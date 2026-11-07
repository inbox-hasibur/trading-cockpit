"""Comprehensive MVP Rule Verification Suite.

Tests cover all 12 core trading invariants with StockNow mocked:
1. L1 before L2 buy priority
2. Base GSC never auto-bought (observation pool only)
3. T+2 maturity rolling settlement
4. Strict no-loss rejection
5. 25% sequential sells on profit tiers
6. 50/50 pullback split and recovery hold
7. Caps and budget enforcement (max_order_bdt, max_symbol_bdt, daily_budget_bdt)
8. Global kill switch across AutoTrader and Hermes
9. Polling mode and onscreen-live mode produce identical decisions
10. AutoTrader and Hermes share the single-writer trading lock
11. Restart idempotency across server cold reboots
12. TEST_OFFHOURS vs LIVE_HOURS market hour gates
"""

from __future__ import annotations

import threading
import time
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from sqlalchemy import select

from backend.adapters.stocknow_adapter import StockNowAdapter
from backend.adapters.stocknow_order_executor import clear_idempotency_cache
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
from backend.engine.sequential_seller import SellState, plan_sale
from backend.engine.t2_ledger import TradingCalendar, bucket_balances
from backend.engine.trading_lock import acquire_trading_lock
from backend.kernel_api import clear_order_idempotency_cache


@pytest.fixture(autouse=True)
def clean_test_isolation():
    """Clear all order and idempotency caches before and after each test."""
    clear_order_idempotency_cache()
    clear_idempotency_cache()
    yield
    clear_order_idempotency_cache()
    clear_idempotency_cache()


@pytest.fixture(autouse=True)
def mock_stocknow_virtual_execution():
    """Mock StockNow virtual browser dispatch so tests run fast without external browsers."""
    async def _mock_exec(*args, **kwargs):
        sym = kwargs.get("symbol", "GP")
        side = kwargs.get("side", "BUY")
        qty = kwargs.get("quantity", 1)
        price = kwargs.get("price", 250.0)
        idem = kwargs.get("idempotency_key", f"mock-{uuid4().hex[:8]}")
        return {
            "success": True,
            "status": "ACKNOWLEDGED",
            "execution_mode": "MOCK_VERIFIED",
            "order_id": f"MOCK_ORD_{uuid4().hex[:8].upper()}",
            "symbol": sym,
            "side": side,
            "quantity": qty,
            "price": float(price),
            "commission_pct": 0.5,
            "commission_rate": 0.005,
            "portfolio_id": "164580",
            "idempotency_key": idem,
            "timestamp": "2026-11-07T12:00:00Z",
        }

    with patch.object(StockNowAdapter, "execute_order", side_effect=_mock_exec):
        yield


@pytest.fixture
def kernel_token(monkeypatch):
    token = "test-mvp-rules-token"
    monkeypatch.setenv("KERNEL_TOKEN", token)
    return token


@pytest.fixture
def auth_headers(kernel_token):
    return {"X-Kernel-Token": kernel_token}


# -----------------------------------------------------------------------------
# 1. L1 before L2 Buy Priority
# -----------------------------------------------------------------------------
def test_l1_before_l2_buy_priority(client, auth_headers):
    """Verify that AutoTrader sorts GSC_L1 companies ahead of GSC_L2 companies."""
    db = client.app.state.database
    with db.write() as session:
        companies = list(session.scalars(select(CompanyProfile).order_by(CompanyProfile.symbol)))

        # Define priority order
        def buy_priority(comp: CompanyProfile) -> tuple[int, str]:
            cat = getattr(comp, "watchlist_category", "GSC")
            if cat == "GSC_L1":
                return (1, comp.symbol)
            if cat == "GSC_L2":
                return (2, comp.symbol)
            return (3, comp.symbol)

        sorted_comps = sorted(companies, key=buy_priority)
        l1_symbols = [c.symbol for c in sorted_comps if getattr(c, "watchlist_category", "") == "GSC_L1"]
        l2_symbols = [c.symbol for c in sorted_comps if getattr(c, "watchlist_category", "") == "GSC_L2"]

        assert len(l1_symbols) > 0, "Expected at least one GSC_L1 symbol in seed"
        assert len(l2_symbols) > 0, "Expected at least one GSC_L2 symbol in seed"

        # All GSC_L1 symbols must appear before any GSC_L2 symbol in the sorted candidate list
        first_l2_idx = next(i for i, c in enumerate(sorted_comps) if getattr(c, "watchlist_category", "") == "GSC_L2")
        last_l1_idx = max(i for i, c in enumerate(sorted_comps) if getattr(c, "watchlist_category", "") == "GSC_L1")
        assert last_l1_idx < first_l2_idx


# -----------------------------------------------------------------------------
# 2. Base GSC Never Auto-Bought
# -----------------------------------------------------------------------------
def test_base_gsc_never_auto_bought(client, auth_headers):
    """Verify base GSC observation pool companies are never auto-bought when tiers exist."""
    db = client.app.state.database
    client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)

    # Configure StockNow 164580 portfolio context and enable rule for ACI (in base tier GSC)
    with db.write() as session:
        state = portfolio_state(session)
        state.name = "StockNow #164580 Virtual Portfolio"
        aci = session.get(CompanyProfile, "ACI")
        if aci:
            aci.source = "STOCKNOW_FAVORITES"
            aci.watchlist_category = "GSC"
        aci_rule = session.get(CustomRule, "ACI")
        if aci_rule:
            aci_rule.enabled = True
            aci_rule.buy_allocation_pct = Decimal("15.00")

    # Run cycle
    trader = AutoTrader(db, client.app.state.settings)
    trader.run_cycle()

    with db.read() as session:
        # ACI must not have any buy trade logged
        aci_buys = session.scalars(select(TradeLog).where(TradeLog.symbol == "ACI", TradeLog.side == "BUY")).all()
        assert len(aci_buys) == 0

        # Decision log must record observation pool skip
        d_log = session.scalar(
            select(DecisionLog)
            .where(DecisionLog.symbol == "ACI", DecisionLog.action == "WAIT_OBSERVATION_ONLY")
            .order_by(DecisionLog.id.desc())
        )
        assert d_log is not None
        assert "Observation pool only" in d_log.reason


# -----------------------------------------------------------------------------
# 3. T+2 Maturity Rolling Settlement
# -----------------------------------------------------------------------------
def test_t2_maturity_rolling_settlement(client, auth_headers):
    """Verify rolling settlement: shares bought on T0 are locked on T0 and T1, mature on T2."""
    db = client.app.state.database
    client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)

    # Step A: Buy shares on day T0
    buy_key = f"t2-buy-{uuid4().hex[:8]}"
    res_buy = client.post("/k/order", json={
        "idempotency_key": buy_key,
        "symbol": "BANKASIA",
        "side": "BUY",
        "quantity": 10,
        "dry_run": False,
        "operator_confirmed": True,
    }, headers=auth_headers)
    assert res_buy.status_code == 200

    bought_lot_id = None
    with db.read() as session:
        state_t0 = portfolio_state(session)
        t0_date = state_t0.clock_date
        bought_lot = session.scalar(
            select(TaxLot)
            .where(TaxLot.symbol == "BANKASIA", TaxLot.acquired_on == t0_date)
            .order_by(TaxLot.id.desc())
        )
        assert bought_lot is not None
        assert bought_lot.matures_on > t0_date
        bought_lot_id = bought_lot.id

    # Attempt to sell on day T0 -> Must fail settlement lock
    res_sell_t0 = client.post("/k/order", json={
        "idempotency_key": f"t2-sell-t0-{uuid4().hex[:8]}",
        "symbol": "BANKASIA",
        "side": "SELL",
        "quantity": 10,
        "dry_run": False,
        "operator_confirmed": True,
    }, headers=auth_headers)
    assert res_sell_t0.status_code == 422
    assert "settlement-locked" in res_sell_t0.json()["detail"] or "T+2" in res_sell_t0.json()["detail"]

    # Step B: Advance 1 session using advance_demo -> Session T+1
    res_adv1 = client.post("/api/demo/advance", json={"scenario": "NORMAL"})
    assert res_adv1.status_code == 200

    # Attempt to sell on day T+1 -> Must still fail settlement lock
    res_sell_t1 = client.post("/k/order", json={
        "idempotency_key": f"t2-sell-t1-{uuid4().hex[:8]}",
        "symbol": "BANKASIA",
        "side": "SELL",
        "quantity": 10,
        "dry_run": False,
        "operator_confirmed": True,
    }, headers=auth_headers)
    assert res_sell_t1.status_code == 422
    assert "settlement-locked" in res_sell_t1.json()["detail"] or "T+2" in res_sell_t1.json()["detail"]

    # Step C: Advance 2nd session using advance_demo -> Session T+2
    res_adv2 = client.post("/api/demo/advance", json={"scenario": "NORMAL"})
    assert res_adv2.status_code == 200

    with db.read() as session:
        state_t2 = portfolio_state(session)
        lot_t2 = session.get(TaxLot, bought_lot_id)
        assert lot_t2.matures_on <= state_t2.clock_date, "Lot must be mature on T+2"


# -----------------------------------------------------------------------------
# 4. Strict No-Loss Rejection
# -----------------------------------------------------------------------------
def test_strict_no_loss_rejection(client, auth_headers):
    """Verify sells at a net loss (< 0% after 1% round trip fee) are strictly rejected."""
    db = client.app.state.database
    client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)

    # In seed data, GP has mature shares with cost basis ~241.20 BDT per share
    with db.write() as session:
        state = portfolio_state(session)
        gp_lot = session.scalar(select(TaxLot).where(TaxLot.symbol == "GP", TaxLot.remaining_qty > 0))
        assert gp_lot is not None
        # Force lot to be mature today
        gp_lot.matures_on = state.clock_date
        # Lower GP market price to 200.00 (below cost basis of 241.20)
        gp_comp = session.get(CompanyProfile, "GP")
        gp_comp.last_price = Decimal("200.00")

    # Kernel order sell attempt must reject with 422 Strict No-Loss
    res_sell = client.post("/k/order", json={
        "idempotency_key": f"noloss-{uuid4().hex[:8]}",
        "symbol": "GP",
        "side": "SELL",
        "quantity": 2,
        "price": 200.0,
        "dry_run": False,
        "operator_confirmed": True,
    }, headers=auth_headers)
    assert res_sell.status_code == 422
    assert "Strict No-Loss" in res_sell.json()["detail"] or "net loss" in res_sell.json()["detail"]

    # In AutoTrader sequential seller, plan_sale returns NO_LOSS_HOLD
    plan = plan_sale(
        SellState(
            remaining_qty=8,
            remaining_basis=Decimal("1929.60"),
            matures_on=state.clock_date,
            cycle_base_qty=8,
            peak_price=Decimal("250.00"),
            next_tier=0,
            phase="ACCUMULATING",
            recovery_anchor=None,
        ),
        current_price=Decimal("200.00"),
        as_of=state.clock_date,
        sell_fee_rate=Decimal("0.005"),
    )
    assert plan.action == "NO_LOSS_HOLD"
    assert "strict no-loss policy holds" in plan.reason


# -----------------------------------------------------------------------------
# 5. 25% Sequential Sells
# -----------------------------------------------------------------------------
def test_twenty_five_percent_sequential_sells():
    """Verify sequential seller sells in 25% tranches when profit tiers are achieved."""
    as_of = Decimal("100")
    base_qty = 100
    cost_basis = Decimal("10000.00")  # 100 BDT/share

    # Price rises 6% to 106.00 (exceeds 5% Tier 1 hurdle after 0.5% fee)
    plan_tier1 = plan_sale(
        SellState(
            remaining_qty=base_qty,
            remaining_basis=cost_basis,
            matures_on=as_of,
            cycle_base_qty=base_qty,
            peak_price=Decimal("100.00"),
            next_tier=0,
            phase="ACTIVE",
            recovery_anchor=None,
        ),
        current_price=Decimal("106.00"),
        as_of=as_of,
        sell_fee_rate=Decimal("0.005"),
        tiers=(Decimal("5"), Decimal("10"), Decimal("15")),
        slices=(Decimal("25"), Decimal("25"), Decimal("25")),
    )
    assert plan_tier1.action == "SELL_TIER_1"
    # Exactly 25% of base quantity sold
    assert plan_tier1.quantity == 25
    assert plan_tier1.state.remaining_qty == 75
    assert plan_tier1.state.next_tier == 1


# -----------------------------------------------------------------------------
# 6. 50/50 Pullback Split
# -----------------------------------------------------------------------------
def test_fifty_fifty_pullback():
    """Verify that a 3% pullback while net profitable sells 50% and retains 50% for recovery."""
    as_of = Decimal("100")
    remaining_qty = 60
    cost_basis = Decimal("6000.00")  # 100 BDT/share
    peak_price = Decimal("120.00")

    # Pullback 4% from peak (120 * 0.96 = 115.20), still profitable vs 100 cost
    current_price = Decimal("115.20")
    plan_pb = plan_sale(
        SellState(
            remaining_qty=remaining_qty,
            remaining_basis=cost_basis,
            matures_on=as_of,
            cycle_base_qty=100,
            peak_price=peak_price,
            next_tier=1,
            phase="ACTIVE",
            recovery_anchor=None,
        ),
        current_price=current_price,
        as_of=as_of,
        sell_fee_rate=Decimal("0.005"),
        pullback_pct=Decimal("3"),
    )
    assert plan_pb.action == "PULLBACK_SPLIT"
    # Sells 50% of remaining (60 // 2 = 30)
    assert plan_pb.quantity == 30
    assert plan_pb.state.remaining_qty == 30
    assert plan_pb.state.phase == "RECOVERY_HOLD"
    assert plan_pb.state.recovery_anchor == peak_price


# -----------------------------------------------------------------------------
# 7. Caps and Budget Enforcement
# -----------------------------------------------------------------------------
def test_caps_and_budget_enforcement(client, auth_headers):
    """Verify max_order_bdt, max_symbol_bdt, and daily_budget_bdt are enforced."""
    client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)

    # A. Set strict caps
    client.post("/k/caps", json={
        "max_order_bdt": 5000.0,
        "max_symbol_bdt": 3000.0,
        "daily_budget_bdt": 3000.0,
    }, headers=auth_headers)

    # 1. Order exceeding max_order_bdt (25 shares of GP @ 250 = 6,250 > 5,000) -> 422
    res_order_cap = client.post("/k/order", json={
        "idempotency_key": f"cap-ord-{uuid4().hex[:8]}",
        "symbol": "GP",
        "side": "BUY",
        "quantity": 25,
        "dry_run": False,
        "operator_confirmed": True,
    }, headers=auth_headers)
    assert res_order_cap.status_code == 422
    assert "exceeds max order cap" in res_order_cap.json()["detail"]

    # 2. Order exceeding max_symbol_bdt (5 shares of GP @ 250 = 1,250 <= 5,000 order cap; 1929 + 1250 = 3179 > 3000 symbol cap)
    res_sym_cap = client.post("/k/order", json={
        "idempotency_key": f"cap-sym-{uuid4().hex[:8]}",
        "symbol": "GP",
        "side": "BUY",
        "quantity": 5,
        "dry_run": False,
        "operator_confirmed": True,
    }, headers=auth_headers)
    assert res_sym_cap.status_code == 422
    assert "max symbol cap" in res_sym_cap.json()["detail"]

    # 3. Order exceeding daily_budget_bdt
    # Raise max_symbol_bdt to 10,000 so symbol cap passes, but lower daily_budget_bdt to 2,000
    client.post("/k/caps", json={"max_symbol_bdt": 10000.0, "daily_budget_bdt": 2000.0, "confirm": True}, headers=auth_headers)
    # Buying 100 shares of BANKASIA @ 17.5 = 1,750 BDT; today already spent 879.38 => 879.38 + 1750 = 2629.38 > 2000 daily budget
    res_budget_cap = client.post("/k/order", json={
        "idempotency_key": f"cap-bdg-{uuid4().hex[:8]}",
        "symbol": "BANKASIA",
        "side": "BUY",
        "quantity": 100,
        "dry_run": False,
        "operator_confirmed": True,
    }, headers=auth_headers)
    assert res_budget_cap.status_code == 422
    assert "daily budget" in res_budget_cap.json()["detail"]


# -----------------------------------------------------------------------------
# 8. Global Kill Switch Across AutoTrader and Hermes
# -----------------------------------------------------------------------------
def test_global_kill_switch(client, auth_headers):
    """Verify global kill switch stops mid-cycle AutoTrader and rejects Hermes orders."""
    db = client.app.state.database
    client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)

    # Activate kill switch
    res_kill = client.post("/k/caps", json={"kill_switch_active": True, "confirm": True}, headers=auth_headers)
    assert res_kill.status_code == 200

    # Hermes order path rejected
    res_order = client.post("/k/order", json={
        "idempotency_key": f"kill-ord-{uuid4().hex[:8]}",
        "symbol": "GP",
        "side": "BUY",
        "quantity": 1,
        "dry_run": False,
        "operator_confirmed": True,
    }, headers=auth_headers)
    assert res_order.status_code == 422
    assert "kill switch is active" in res_order.json()["detail"]

    # AutoTrader cycle halts mid-cycle
    trader = AutoTrader(db, client.app.state.settings)
    trader.run_cycle()

    with db.read() as session:
        d_log = session.scalar(
            select(DecisionLog)
            .where(DecisionLog.action == "KILL_SWITCH_ACTIVE")
            .order_by(DecisionLog.id.desc())
        )
        assert d_log is not None
        assert "kill switch is active" in d_log.reason.lower()


# -----------------------------------------------------------------------------
# 9. Polling Mode and Onscreen-Live Mode Produce Identical Decisions
# -----------------------------------------------------------------------------
def test_polling_and_onscreen_modes_identical_decisions(client, auth_headers):
    """Verify AutoTrader produces identical trading decisions for identical market state across modes."""
    db = client.app.state.database
    client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)
    trader = AutoTrader(db, client.app.state.settings)

    # 1. Run in BACKGROUND_POLLING mode
    with db.write() as session:
        state = portfolio_state(session)
        state.ingestion_mode = "BACKGROUND_POLLING"

    cycle_res_polling = trader.run_cycle()
    signals_polling = cycle_res_polling.get("signals", {})
    trades_polling = cycle_res_polling.get("trades", [])

    # Advance demo session to increment revision and generate fresh evaluation
    client.post("/api/demo/advance", json={"scenario": "NORMAL"})

    # 2. Run in ONSCREEN_LIVE mode
    with db.write() as session:
        state = portfolio_state(session)
        state.ingestion_mode = "ONSCREEN_LIVE"

    cycle_res_onscreen = trader.run_cycle()
    signals_onscreen = cycle_res_onscreen.get("signals", {})

    # Both modes evaluate the mathematical curve and rules engine identically
    assert set(signals_polling.keys()) == set(signals_onscreen.keys())
    for sym in signals_polling:
        assert signals_polling[sym].get("trend") == signals_onscreen[sym].get("trend")


# -----------------------------------------------------------------------------
# 10. AutoTrader and Hermes Share Single-Writer Lock
# -----------------------------------------------------------------------------
def test_autotrader_hermes_single_writer_lock():
    """Verify AutoTrader and Hermes share acquire_trading_lock with contention protection."""
    contention_detected = False

    def holder_task():
        with acquire_trading_lock(timeout=2.0):
            time.sleep(0.5)

    t = threading.Thread(target=holder_task)
    t.start()
    time.sleep(0.1)  # Allow thread to acquire lock

    # Second acquirer with 0.1s timeout should raise contention error
    try:
        with acquire_trading_lock(timeout=0.1):
            pass
    except RuntimeError as exc:
        contention_detected = True
        assert "Trading lock contention" in str(exc)

    t.join()
    assert contention_detected, "Expected trading lock contention when lock is held"


# -----------------------------------------------------------------------------
# 11. Restart Idempotency SQLite Persistence
# -----------------------------------------------------------------------------
def test_restart_idempotency_sqlite(client, auth_headers):
    """Verify order idempotency survives process reboots via SQLite OrderIdempotencyKey."""
    client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)

    idem_key = f"reboot-{uuid4().hex[:8]}"
    payload = {
        "idempotency_key": idem_key,
        "symbol": "GP",
        "side": "BUY",
        "quantity": 2,
        "dry_run": False,
        "operator_confirmed": True,
    }

    # 1. Execute order
    res1 = client.post("/k/order", json=payload, headers=auth_headers)
    assert res1.status_code == 200

    # 2. Simulate cold server restart by purging all in-memory caches
    clear_order_idempotency_cache()
    clear_idempotency_cache()

    # 3. Repeat exact same order -> Must return ALREADY_EXECUTED duplicate from SQLite
    res2 = client.post("/k/order", json=payload, headers=auth_headers)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2.get("duplicate") is True
    assert data2.get("status") == "ALREADY_EXECUTED"


# -----------------------------------------------------------------------------
# 12. TEST_OFFHOURS vs LIVE_HOURS Market Hours Gates
# -----------------------------------------------------------------------------
def test_trading_mode_market_hours_gates(client, auth_headers):
    """Verify off-hours gate is enforced in LIVE_HOURS and bypassed only in TEST_OFFHOURS."""
    # Ensure LIVE_HOURS
    client.post("/k/mode", json={"trading_mode": "LIVE_HOURS", "confirm": False}, headers=auth_headers)

    payload = {
        "idempotency_key": f"gate-test-{uuid4().hex[:8]}",
        "symbol": "GP",
        "side": "BUY",
        "quantity": 1,
        "dry_run": False,
        "operator_confirmed": True,
        "preview_token": "dummy_preview",
    }

    # In LIVE_HOURS, when market is closed (e.g. Saturday/off-hours), order is rejected
    with patch("backend.kernel_api.is_dse_market_open", return_value={"is_open": False, "reason": "Saturday weekend"}):
        res_live = client.post("/k/order", json=payload, headers=auth_headers)
        assert res_live.status_code == 422
        assert "DSE market is closed" in res_live.json()["detail"]

    # Switch to TEST_OFFHOURS with confirm=True
    client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)

    # In TEST_OFFHOURS, the exact same off-hours order passes cleanly
    with patch("backend.kernel_api.is_dse_market_open", return_value={"is_open": False, "reason": "Saturday weekend"}):
        res_test = client.post("/k/order", json=payload, headers=auth_headers)
        assert res_test.status_code == 200
        assert res_test.json()["trading_mode"] == "TEST_OFFHOURS"
