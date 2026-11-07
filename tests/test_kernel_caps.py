"""Tests for enforced kernel risk limits and safety caps across AutoTrader and Hermes."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlalchemy import select

from backend.database import (
    CompanyProfile,
    CustomRule,
    DecisionLog,
    KernelAuditLog,
    PortfolioState,
    TaxLot,
    TradeLog,
    portfolio_state,
)
from backend.engine.auto_trader import AutoTrader
from backend.kernel_api import clear_order_idempotency_cache
from plugins.humming_bird.tools import hb_caps_get, hb_caps_set


@pytest.fixture(autouse=True)
def clean_idempotency():
    clear_order_idempotency_cache()
    yield
    clear_order_idempotency_cache()


@pytest.fixture
def kernel_token(monkeypatch):
    token = "test-kernel-caps-token"
    monkeypatch.setenv("KERNEL_TOKEN", token)
    return token


@pytest.fixture
def auth_headers(kernel_token):
    return {"X-Kernel-Token": kernel_token}


def test_per_order_cap(client, auth_headers):
    """Test that individual orders exceeding max_order_bdt are rejected and logged."""
    client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)

    # 1. Set max_order_bdt to 5,000 (lowering from 20,000: confirm not needed)
    res_cap = client.post("/k/caps", json={"max_order_bdt": 5000.0}, headers=auth_headers)
    assert res_cap.status_code == 200
    assert res_cap.json()["max_order_bdt"] == 5000.0

    # 2. Place an order for 25 shares of GP @ 250 BDT = 6,250 BDT (exceeds 5,000)
    key_reject = f"ord-rej-{uuid4().hex[:8]}"
    res_reject = client.post("/k/order", json={
        "idempotency_key": key_reject,
        "symbol": "GP",
        "side": "BUY",
        "quantity": 25,
        "dry_run": False,
        "operator_confirmed": True,
    }, headers=auth_headers)

    assert res_reject.status_code == 422
    assert "exceeds max order cap" in res_reject.json()["detail"]

    # Verify DecisionLog and KernelAuditLog record the rejection
    db = client.app.state.database
    with db.read() as session:
        d_log = session.scalar(
            select(DecisionLog)
            .where(DecisionLog.symbol == "GP", DecisionLog.action == "REJECT_MAX_ORDER_CAP")
            .order_by(DecisionLog.id.desc())
            .limit(1)
        )
        assert d_log is not None
        assert "exceeds max order cap" in d_log.reason

        a_log = session.scalar(
            select(KernelAuditLog)
            .where(KernelAuditLog.action == "REJECT_MAX_ORDER_CAP")
            .order_by(KernelAuditLog.id.desc())
            .limit(1)
        )
        assert a_log is not None

    # 3. Place an order for 5 shares of GP @ 250 BDT = ~1,256 BDT (within 5,000 and within cash) -> succeeds
    key_pass = f"ord-pass-{uuid4().hex[:8]}"
    res_pass = client.post("/k/order", json={
        "idempotency_key": key_pass,
        "symbol": "GP",
        "side": "BUY",
        "quantity": 5,
        "dry_run": False,
        "operator_confirmed": True,
    }, headers=auth_headers)
    assert res_pass.status_code == 200
    assert res_pass.json()["dry_run"] is False


def test_per_symbol_cap(client, auth_headers):
    """Test that orders pushing a symbol's exposure over max_symbol_bdt are rejected."""
    client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)

    # GP starts with ~1929.60 BDT open cost basis in demo seed.
    # 1. Set max_symbol_bdt to 3,000 BDT
    res_cap = client.post("/k/caps", json={"max_symbol_bdt": 3000.0}, headers=auth_headers)
    assert res_cap.status_code == 200

    # 2. First buy: 4 shares of GP @ 250 BDT = 1,000 BDT (total exposure: 1929.60 + 1000 = 2929.60 <= 3000) -> succeeds
    res_buy1 = client.post("/k/order", json={
        "idempotency_key": f"buy1-{uuid4().hex[:8]}",
        "symbol": "GP",
        "side": "BUY",
        "quantity": 4,
        "dry_run": False,
        "operator_confirmed": True,
    }, headers=auth_headers)
    assert res_buy1.status_code == 200

    # 3. Second buy: 2 more shares of GP @ 250 BDT = 500 BDT (total exposure would be 3,429.60 > 3,000)
    res_buy2 = client.post("/k/order", json={
        "idempotency_key": f"buy2-{uuid4().hex[:8]}",
        "symbol": "GP",
        "side": "BUY",
        "quantity": 2,
        "dry_run": False,
        "operator_confirmed": True,
    }, headers=auth_headers)

    assert res_buy2.status_code == 422
    assert "exceeds max symbol cap" in res_buy2.json()["detail"]

    # Verify DecisionLog recorded
    db = client.app.state.database
    with db.read() as session:
        d_log = session.scalar(
            select(DecisionLog)
            .where(DecisionLog.symbol == "GP", DecisionLog.action == "REJECT_MAX_SYMBOL_CAP")
            .order_by(DecisionLog.id.desc())
            .limit(1)
        )
        assert d_log is not None


def test_daily_budget_exhaustion(client, auth_headers):
    """Test that buying orders are strictly capped at daily_budget_bdt."""
    client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)

    # Demo seed starts with 879.38 BDT buy spend today.
    # 1. Set daily_budget_bdt to 3,000 BDT
    res_cap = client.post("/k/caps", json={"daily_budget_bdt": 3000.0}, headers=auth_headers)
    assert res_cap.status_code == 200

    # 2. Buy 5 shares of GP @ 250 BDT = ~1,256.25 BDT (total spend ~2,135.63 <= 3,000) -> succeeds
    res_buy1 = client.post("/k/order", json={
        "idempotency_key": f"bdg1-{uuid4().hex[:8]}",
        "symbol": "GP",
        "side": "BUY",
        "quantity": 5,
        "dry_run": False,
        "operator_confirmed": True,
    }, headers=auth_headers)
    assert res_buy1.status_code == 200

    # 3. Attempt to buy 5 more shares of GP @ 250 BDT = ~1,256 BDT (total spend ~3,391 > 3,000) -> rejected
    res_buy2 = client.post("/k/order", json={
        "idempotency_key": f"bdg2-{uuid4().hex[:8]}",
        "symbol": "GP",
        "side": "BUY",
        "quantity": 5,
        "dry_run": False,
        "operator_confirmed": True,
    }, headers=auth_headers)

    assert res_buy2.status_code == 422
    assert "exceeding daily budget cap" in res_buy2.json()["detail"]

    # Verify DecisionLog
    db = client.app.state.database
    with db.read() as session:
        d_log = session.scalar(
            select(DecisionLog)
            .where(DecisionLog.symbol == "GP", DecisionLog.action == "REJECT_DAILY_BUDGET_EXHAUSTED")
            .order_by(DecisionLog.id.desc())
            .limit(1)
        )
        assert d_log is not None


def test_kill_switch_mid_cycle(client, auth_headers):
    """Test global kill switch halts orders in kernel and mid-cycle in AutoTrader."""
    client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)

    # 1. Activate kill switch (defensive: confirm not needed)
    res_ks = client.post("/k/caps", json={"kill_switch_active": True}, headers=auth_headers)
    assert res_ks.status_code == 200
    assert res_ks.json()["kill_switch_active"] is True

    # 2. Attempt order via kernel API -> rejected
    res_ord = client.post("/k/order", json={
        "idempotency_key": f"ks-{uuid4().hex[:8]}",
        "symbol": "GP",
        "side": "BUY",
        "quantity": 2,
        "dry_run": False,
        "operator_confirmed": True,
    }, headers=auth_headers)
    assert res_ord.status_code == 422
    assert "Global kill switch is active" in res_ord.json()["detail"]

    # 3. Run AutoTrader cycle with kill switch active -> halts mid-cycle without trades
    db = client.app.state.database
    settings = client.app.state.settings
    trader = AutoTrader(database=db, settings=settings)

    trades = trader.run_cycle()
    assert trades == []

    # Verify DecisionLog recorded KILL_SWITCH_ACTIVE
    with db.read() as session:
        ks_log = session.scalar(
            select(DecisionLog)
            .where(DecisionLog.action == "KILL_SWITCH_ACTIVE")
            .limit(1)
        )
        assert ks_log is not None
        assert "kill switch is active" in ks_log.reason.lower()


def test_autotrader_and_hermes_share_same_budget(client, auth_headers):
    """Test that AutoTrader and Hermes consume and enforce the exact same shared daily budget."""
    client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)

    # 1. Set daily budget to 3,000 BDT
    client.post("/k/caps", json={"daily_budget_bdt": 3000.0}, headers=auth_headers)

    # 2. Hermes executes a BUY order consuming ~1,256.25 BDT (5 shares of GP @ 250, total spend ~2,135.63 <= 3,000)
    res_h = client.post("/k/order", json={
        "idempotency_key": f"hermes-buy-{uuid4().hex[:8]}",
        "symbol": "GP",
        "side": "BUY",
        "quantity": 5,
        "dry_run": False,
        "operator_confirmed": True,
    }, headers=auth_headers)
    assert res_h.status_code == 200

    # 3. AutoTrader now only has ~487.50 BDT remaining of the shared 3,000 BDT budget
    db = client.app.state.database
    settings = client.app.state.settings
    trader = AutoTrader(database=db, settings=settings)

    # If AutoTrader evaluates buying a stock that costs > 487.50 BDT, it gets blocked by DAILY_BUDGET_EXHAUSTED
    # Or if budget allows smaller shares, it respects the daily_budget_headroom
    with db.write() as session:
        state = portfolio_state(session)
        # Ensure BATBC is in BUY_ZONE with price 500
        comp = session.get(CompanyProfile, "BATBC")
        if comp:
            comp.last_price = Decimal("500.00")
            comp.watchlist_category = "GSC_L1"

    trades = trader.run_cycle()
    # Any buy trade placed by AutoTrader cannot push total buy spend over 3,000
    with db.read() as session:
        state = portfolio_state(session)
        total_buys = sum(
            (abs(t.net_cash_change) for t in session.scalars(
                select(TradeLog).where(TradeLog.trade_on == state.clock_date, TradeLog.side == "BUY")
            )),
            Decimal("0"),
        )
        assert total_buys <= Decimal("3000.00")


def test_caps_raising_requires_confirmation(client, auth_headers):
    """Test that raising a risk limit requires operator confirmation (confirm=true)."""
    # 1. Lower limit to 2,000 -> succeeds without confirmation
    res_low = client.post("/k/caps", json={"daily_budget_bdt": 2000.0, "confirm": False}, headers=auth_headers)
    assert res_low.status_code == 200
    assert res_low.json()["daily_budget_bdt"] == 2000.0

    # 2. Raise limit from 2,000 to 5,000 without confirmation -> rejected with 422
    res_raise_fail = client.post("/k/caps", json={"daily_budget_bdt": 5000.0, "confirm": False}, headers=auth_headers)
    assert res_raise_fail.status_code == 422
    assert "requires operator confirmation" in res_raise_fail.json()["detail"]

    # 3. Raise limit with confirm=true -> succeeds
    res_raise_ok = client.post("/k/caps", json={"daily_budget_bdt": 5000.0, "confirm": True}, headers=auth_headers)
    assert res_raise_ok.status_code == 200
    assert res_raise_ok.json()["daily_budget_bdt"] == 5000.0


def test_plugin_tools_hb_caps(client, auth_headers, monkeypatch):
    """Test that hb_caps_get and hb_caps_set plugin tools function correctly with kernel."""
    import json

    monkeypatch.setenv("KERNEL_BASE_URL", str(client.base_url))
    monkeypatch.setenv("KERNEL_TOKEN", auth_headers["X-Kernel-Token"])

    # 1. hb_caps_get
    with patch("plugins.humming_bird.tools._kernel_get") as mock_get:
        mock_get.return_value = json.dumps({"daily_budget_bdt": 5000.0, "kill_switch_active": False})
        res_get = hb_caps_get()
        data = json.loads(res_get)
        assert data["daily_budget_bdt"] == 5000.0

    # 2. hb_caps_set
    with patch("plugins.humming_bird.tools._kernel_post") as mock_post:
        mock_post.return_value = json.dumps({"status": "ok", "daily_budget_bdt": 3500.0})
        res_set = hb_caps_set(daily_budget_bdt=3500.0)
        data_set = json.loads(res_set)
        assert data_set["status"] == "ok"
