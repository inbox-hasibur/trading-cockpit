"""Tests for configurable target portfolio, allowlist enforcement, and portfolio-scoped ledgers."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.config import Settings
from backend.database import TaxLot, TradeLog, portfolio_state
from backend.main import create_app


@pytest.fixture
def test_settings(tmp_path):
    db_file = tmp_path / "test_portfolios.db"
    return Settings(
        database_url=f"sqlite:///{db_file.as_posix()}",
        stocknow_live_portfolio_id="164580",
        stocknow_test_portfolio_id="164581_test",
        openrouter_api_key="test-key",
    )


@pytest.fixture
def auth_headers(monkeypatch):
    token = "test-kernel-token-portfolio-cfg"
    monkeypatch.setenv("KERNEL_TOKEN", token)
    return {"X-Kernel-Token": token}


def test_mode_never_touches_164580(test_settings, auth_headers):
    """Test Mode executes orders exclusively on the test portfolio and never touches 164580."""
    app = create_app(test_settings)
    with TestClient(app, base_url="http://localhost") as client:
        # Switch to TEST_OFFHOURS
        client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)

        # 1. Sending an order targeting 164580 while in TEST_OFFHOURS is rejected with 422
        bad_res = client.post("/k/order", json={
            "idempotency_key": str(uuid4()),
            "symbol": "GP",
            "side": "BUY",
            "quantity": 2,
            "portfolio_id": "164580",
            "dry_run": False,
            "operator_confirmed": True,
        }, headers=auth_headers)
        assert bad_res.status_code == 422
        assert "Test Mode sends orders only to the configured test portfolio" in bad_res.json()["detail"]

        # 2. Record initial lot count of 164580
        db = app.state.database
        with db.read() as session:
            initial_164580_lots = session.scalars(select(TaxLot).where(TaxLot.portfolio_id == "164580")).all()
            initial_164580_count = len(initial_164580_lots)

        # 3. Place order in TEST_OFFHOURS (defaults to active test portfolio 164581_test)
        buy_res = client.post("/k/order", json={
            "idempotency_key": str(uuid4()),
            "symbol": "GP",
            "side": "BUY",
            "quantity": 2,
            "dry_run": False,
            "operator_confirmed": True,
        }, headers=auth_headers)
        assert buy_res.status_code == 200, f"Order failed: {buy_res.json()}"
        data = buy_res.json()
        assert data["portfolio_id"] == "164581_test"
        assert "(Test)" in data["portfolio_name"]
        assert data["stocknow_receipt"]["portfolio_id"] == "164581_test"

        # 4. Verify 164580 lots were completely untouched
        with db.read() as session:
            lots_164580 = session.scalars(select(TaxLot).where(TaxLot.portfolio_id == "164580")).all()
            assert len(lots_164580) == initial_164580_count

            # Verify trade log has 164581_test
            test_trades = session.scalars(select(TradeLog).where(TradeLog.portfolio_id == "164581_test")).all()
            assert len(test_trades) >= 1
            assert any(t.symbol == "GP" and t.quantity == 2 for t in test_trades)


def test_mode_switch_changes_active_portfolio(test_settings, auth_headers):
    """Switching trading mode updates the active target portfolio and receipt telemetry."""
    app = create_app(test_settings)
    with TestClient(app, base_url="http://localhost") as client:
        # 1. LIVE_HOURS active portfolio
        caps_live = client.get("/k/caps", headers=auth_headers).json()
        assert caps_live["portfolio_id"] == "164580"
        assert "Humming Bird" in caps_live["portfolio_name"]
        assert caps_live["trading_mode"] == "LIVE_HOURS"

        # 2. Switch to TEST_OFFHOURS
        client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)
        caps_test = client.get("/k/caps", headers=auth_headers).json()
        assert caps_test["portfolio_id"] == "164581_test"
        assert "(Test)" in caps_test["portfolio_name"]
        assert caps_test["trading_mode"] == "TEST_OFFHOURS"

        # 3. Dry run receipt reflects test portfolio
        dry_res = client.post("/k/order", json={
            "idempotency_key": str(uuid4()),
            "symbol": "GP",
            "side": "BUY",
            "quantity": 1,
            "dry_run": True,
        }, headers=auth_headers).json()
        assert dry_res["portfolio_id"] == "164581_test"
        assert "(Test)" in dry_res["portfolio_name"]

        # 4. Switch back to LIVE_HOURS
        client.post("/k/mode", json={"trading_mode": "LIVE_HOURS", "confirm": True}, headers=auth_headers)
        caps_reverted = client.get("/k/caps", headers=auth_headers).json()
        assert caps_reverted["portfolio_id"] == "164580"
        assert caps_reverted["trading_mode"] == "LIVE_HOURS"


def test_budgets_are_per_portfolio(test_settings, auth_headers):
    """Buy spend and orders executed in Test Mode do not consume Live Hours budget."""
    app = create_app(test_settings)
    with TestClient(app, base_url="http://localhost") as client:
        # Check initial live spend
        caps_live_init = client.get("/k/caps", headers=auth_headers).json()
        live_init_spend = caps_live_init["today_buy_spend_bdt"]
        live_init_orders = caps_live_init["today_orders_count"]

        # Switch to TEST_OFFHOURS and record test initial spend
        client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)
        caps_test_init = client.get("/k/caps", headers=auth_headers).json()
        test_init_orders = caps_test_init["today_orders_count"]
        test_init_spend = caps_test_init["today_buy_spend_bdt"]

        buy_res = client.post("/k/order", json={
            "idempotency_key": str(uuid4()),
            "symbol": "GP",
            "side": "BUY",
            "quantity": 3,
            "dry_run": False,
            "operator_confirmed": True,
        }, headers=auth_headers)
        assert buy_res.status_code == 200

        caps_test = client.get("/k/caps", headers=auth_headers).json()
        assert caps_test["today_orders_count"] == test_init_orders + 1
        assert caps_test["today_buy_spend_bdt"] > test_init_spend

        # Switch back to LIVE_HOURS: live budget usage remains unchanged!
        client.post("/k/mode", json={"trading_mode": "LIVE_HOURS", "confirm": True}, headers=auth_headers)
        caps_live_after = client.get("/k/caps", headers=auth_headers).json()
        assert caps_live_after["today_buy_spend_bdt"] == live_init_spend
        assert caps_live_after["today_orders_count"] == live_init_orders


def test_missing_test_portfolio_blocks_orders(tmp_path, auth_headers):
    """If Test Mode has no test portfolio ID configured, order execution is blocked with a clear message."""
    db_file = tmp_path / "test_no_test_pid.db"
    settings = Settings(
        database_url=f"sqlite:///{db_file.as_posix()}",
        stocknow_live_portfolio_id="164580",
        stocknow_test_portfolio_id="",  # Empty / unconfigured
    )
    app = create_app(settings)
    with TestClient(app, base_url="http://localhost") as client:
        client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)

        res = client.post("/k/order", json={
            "idempotency_key": str(uuid4()),
            "symbol": "GP",
            "side": "BUY",
            "quantity": 1,
            "dry_run": True,
        }, headers=auth_headers)
        assert res.status_code == 422
        detail = res.json()["detail"]
        assert "STOCKNOW_TEST_PORTFOLIO_ID is not configured" in detail


def test_allowlist_enforcement(test_settings, auth_headers):
    """Orders with portfolio IDs not in the allowlist are rejected."""
    app = create_app(test_settings)
    with TestClient(app, base_url="http://localhost") as client:
        res = client.post("/k/order", json={
            "idempotency_key": str(uuid4()),
            "symbol": "GP",
            "side": "BUY",
            "quantity": 1,
            "portfolio_id": "999999",
            "dry_run": True,
        }, headers=auth_headers)
        assert res.status_code == 422
        assert "Unauthorized portfolio '999999'" in res.json()["detail"]
        assert "164580" in res.json()["detail"]
        assert "164581_test" in res.json()["detail"]
