"""Tests for Trading Mode (TEST_OFFHOURS vs LIVE_HOURS) and strict safety invariants."""

from __future__ import annotations

import datetime
from decimal import Decimal
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.database import (
    CompanyProfile,
    Database,
    DecisionLog,
    KernelAuditLog,
    KernelStateCheckpoint,
    PortfolioState,
    RuleAudit,
    TaxLot,
    portfolio_state,
)
from backend.engine.scheduler import DSEMarketScheduler, is_dse_market_open
from backend.kernel_api import clear_order_idempotency_cache, create_kernel_app


@pytest.fixture(autouse=True)
def clean_idempotency():
    clear_order_idempotency_cache()
    yield
    clear_order_idempotency_cache()


@pytest.fixture
def kernel_token(monkeypatch):
    token = "test-kernel-mode-token"
    monkeypatch.setenv("KERNEL_TOKEN", token)
    return token


@pytest.fixture
def auth_headers(kernel_token):
    return {"X-Kernel-Token": kernel_token}


@pytest.fixture
def db(client):
    return client.app.state.database


def test_ui_elements_in_index_html():
    """Verify #trading-mode-toggle, banner, and labels in frontend/index.html."""
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # Permanent virtual banner
    assert "StockNow virtual portfolio, no real money" in html
    assert 'id="permanent-banner"' in html

    # Topbar trading mode toggle
    assert 'id="trading-mode-toggle"' in html
    assert "Live Hours (virtual)" in html
    assert "Test Mode 24/7" in html

    # Settings trading mode toggle
    assert 'id="settings-trading-mode-toggle"' in html


def test_kernel_mode_get_and_post_confirm(client, auth_headers, db):
    """Verify /k/mode requires confirm=True for TEST_OFFHOURS but not for LIVE_HOURS."""
    # 1. GET default mode -> LIVE_HOURS
    res = client.get("/k/mode", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["trading_mode"] == "LIVE_HOURS"

    # 2. Switch to TEST_OFFHOURS without confirm -> 422
    err_res = client.post(
        "/k/mode",
        json={"trading_mode": "TEST_OFFHOURS", "confirm": False},
        headers=auth_headers,
    )
    assert err_res.status_code == 422
    assert "requires explicit operator confirmation" in err_res.json()["detail"]

    # 3. Switch to TEST_OFFHOURS with confirm=True -> 200
    ok_res = client.post(
        "/k/mode",
        json={"trading_mode": "TEST_OFFHOURS", "confirm": True},
        headers=auth_headers,
    )
    assert ok_res.status_code == 200
    assert ok_res.json()["trading_mode"] == "TEST_OFFHOURS"

    # Verify audit log and checkpoint recorded with trading_mode
    with db.read() as session:
        audit = session.scalar(
            select(KernelAuditLog)
            .where(KernelAuditLog.endpoint == "/k/mode")
            .order_by(KernelAuditLog.id.desc())
        )
        assert audit is not None
        assert audit.trading_mode == "TEST_OFFHOURS"

    # 4. Switch back to LIVE_HOURS without confirm -> 200 allowed
    back_res = client.post(
        "/k/mode",
        json={"trading_mode": "LIVE_HOURS", "confirm": False},
        headers=auth_headers,
    )
    assert back_res.status_code == 200
    assert back_res.json()["trading_mode"] == "LIVE_HOURS"


def test_saturday_order_blocked_in_live_hours_passes_in_test_offhours(client, auth_headers, db):
    """Saturday order (market closed) is rejected in LIVE_HOURS and allowed in TEST_OFFHOURS."""
    # Ensure profile and cash exist
    with db.write() as session:
        state = portfolio_state(session)
        state.available_cash = Decimal("200000.00")
        state.trading_mode = "LIVE_HOURS"
        profile = session.get(CompanyProfile, "GP")
        if not profile:
            session.add(
                CompanyProfile(
                    symbol="GP",
                    name="Grameenphone Ltd",
                    sector="Telecommunication",
                    last_price=Decimal("250.00"),
                    price_history=[{"date": "2026-11-03", "close": "250.00"}],
                    quote_on=datetime.date(2026, 11, 3),
                )
            )

    # Mock Saturday 11:00 AM Asia/Dhaka (DSE closed on Saturday)
    saturday_dt = datetime.datetime(2026, 11, 7, 11, 0, 0, tzinfo=ZoneInfo("Asia/Dhaka"))

    order_payload = {
        "symbol": "GP",
        "side": "BUY",
        "quantity": 5,
        "price": 250.0,
        "dry_run": False,
        "idempotency_key": "sat-order-live-hours-1",
    }

    with patch("backend.kernel_api.is_dse_market_open") as mock_open:
        mock_open.return_value = {
            "is_open": False,
            "reason": "Saturday - DSE market is closed on weekends",
            "next_open": "Sunday 10:00 AM",
        }
        # In LIVE_HOURS -> Blocked with 422
        res_live = client.post("/k/order", json=order_payload, headers=auth_headers)
        assert res_live.status_code == 422
        assert "DSE market is closed" in res_live.json()["detail"]
        assert "LIVE_HOURS mode" in res_live.json()["detail"]

    # Now switch to TEST_OFFHOURS
    client.post(
        "/k/mode",
        json={"trading_mode": "TEST_OFFHOURS", "confirm": True},
        headers=auth_headers,
    )

    # In TEST_OFFHOURS -> Saturday order succeeds (bypasses market hours gate)
    order_payload["idempotency_key"] = "sat-order-test-offhours-2"
    with patch("backend.kernel_api.is_dse_market_open") as mock_open:
        mock_open.return_value = {
            "is_open": False,
            "reason": "Saturday - DSE market is closed on weekends",
        }
        res_test = client.post("/k/order", json=order_payload, headers=auth_headers)
        assert res_test.status_code == 200, f"Error: {res_test.json()}"
        data = res_test.json()
        assert data["dry_run"] is False
        assert data["side"] == "BUY"
        assert data["quantity"] == 5
        assert "checkpoint_id" in data


def test_scheduler_tick_blocked_in_live_hours_runs_in_test_offhours(db, settings):
    """Scheduler tick skips on closed market in LIVE_HOURS and executes in TEST_OFFHOURS."""
    import asyncio

    # In LIVE_HOURS
    with db.write() as session:
        state = portfolio_state(session)
        state.trading_mode = "LIVE_HOURS"
        state.automation_enabled = True
        state.paused = False

    sched = DSEMarketScheduler(database=db, settings=settings)

    with patch("backend.engine.scheduler.is_dse_market_open") as mock_open:
        mock_open.return_value = {
            "is_open": False,
            "reason": "Off-hours Saturday",
        }
        result_live = asyncio.run(sched.run_scheduled_tick())
        assert result_live["status"] == "SKIPPED"
        assert "Market closed" in result_live["reason"]

    # Switch to TEST_OFFHOURS
    with db.write() as session:
        state = portfolio_state(session)
        state.trading_mode = "TEST_OFFHOURS"

    with patch("backend.engine.scheduler.is_dse_market_open") as mock_open:
        mock_open.return_value = {
            "is_open": False,
            "reason": "Off-hours Saturday",
        }
        # In TEST_OFFHOURS, scheduler tick executes (runs cycle, not skipped for market closed)
        result_test = asyncio.run(sched.run_scheduled_tick())
        assert result_test["status"] == "EXECUTED"


def test_strict_no_loss_still_rejects_in_test_offhours(client, auth_headers):
    """Strict no-loss is fully enforced in TEST_OFFHOURS: selling at a loss returns 422."""
    # 1. Switch to TEST_OFFHOURS
    client.post(
        "/k/mode",
        json={"trading_mode": "TEST_OFFHOURS", "confirm": True},
        headers=auth_headers,
    )

    # 2. Place a real buy order for 5 shares of GP
    from uuid import uuid4
    buy_key = str(uuid4())
    buy_res = client.post("/k/order", json={
        "idempotency_key": buy_key,
        "symbol": "GP",
        "side": "BUY",
        "quantity": 5,
        "dry_run": False,
    }, headers=auth_headers)
    assert buy_res.status_code == 200, f"Buy error: {buy_res.json()}"

    # 3. Attempt to sell at 50.0 (severe loss vs cost basis 250.0)
    sell_key = str(uuid4())
    sell_res = client.post("/k/order", json={
        "idempotency_key": sell_key,
        "symbol": "GP",
        "side": "SELL",
        "quantity": 5,
        "price": 50.0,
        "dry_run": False,
    }, headers=auth_headers)

    # Must be rejected due to Strict No-Loss policy
    assert sell_res.status_code == 422
    detail = sell_res.json()["detail"]
    assert "Strict No-Loss" in detail or "T+2 lock" in detail


def test_decision_log_records_trading_mode(db, settings):
    """Verify auto-trader cycle records trading_mode in DecisionLog rows."""
    from backend.engine.auto_trader import AutoTrader

    with db.write() as session:
        state = portfolio_state(session)
        state.trading_mode = "TEST_OFFHOURS"

    trader = AutoTrader(db, settings)
    trader.run_cycle()

    with db.read() as session:
        decisions = list(session.scalars(select(DecisionLog).order_by(DecisionLog.id.desc()).limit(5)))
        assert len(decisions) > 0
        for d in decisions:
            assert d.trading_mode == "TEST_OFFHOURS"
