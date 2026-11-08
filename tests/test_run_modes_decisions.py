"""Tests for Run Modes (Background 24/7 vs Onscreen Live), Master Automation OFF/ON,
Single-Writer Handoff, Labeled Preview, and Decision Stream Skip Reasons.
"""

from __future__ import annotations

import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.adapters.stocknow_executor import StockNowExecutor, get_stocknow_executor
from backend.database import (
    AutomationCycle,
    CompanyProfile,
    Database,
    DecisionLog,
    KernelAuditLog,
    PortfolioState,
    TaxLot,
    TradeLog,
    portfolio_state,
)
from backend.engine.auto_trader import AutoTrader
from backend.engine.scheduler import DSEMarketScheduler, is_dse_market_open


@pytest.fixture
def db(client):
    return client.app.state.database


@pytest.fixture
def auth_headers(monkeypatch):
    token = "test-run-modes-token"
    monkeypatch.setenv("KERNEL_TOKEN", token)
    return {"X-Kernel-Token": token}


def test_topbar_and_settings_dom_elements():
    """Verify Master toggle chip, emergency Kill button, handoff buttons and Run cycle now."""
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # Master automation chip & emergency kill
    assert 'id="topbar-master-toggle"' in html
    assert 'id="topbar-kill-btn"' in html
    assert "Auto ON" in html or "topbar-master-label" in html

    # Run cycle now button
    assert 'id="run-cycle"' in html
    assert "Run cycle now" in html

    # Run modes and handoff buttons
    assert "Background 24/7" in html
    assert "Onscreen Live" in html
    assert 'id="topbar-handoff-btn"' in html
    assert 'id="settings-handoff-btn"' in html


def test_master_automation_toggle(client, db):
    """Verify master automation toggle turns automation ON/OFF via /api/automation/config."""
    # 1. Turn OFF
    res_off = client.post("/api/automation/config", json={"automation_enabled": False})
    assert res_off.status_code == 200
    assert res_off.json()["automation_enabled"] is False
    assert res_off.json()["paused"] is True

    snap_off = client.get("/api/portfolio").json()
    assert snap_off["app"]["automation_enabled"] is False
    assert snap_off["app"]["paused"] is True

    # 2. Turn ON
    res_on = client.post("/api/automation/config", json={"automation_enabled": True})
    assert res_on.status_code == 200
    assert res_on.json()["automation_enabled"] is True
    assert res_on.json()["paused"] is False

    snap_on = client.get("/api/portfolio").json()
    assert snap_on["app"]["automation_enabled"] is True
    assert snap_on["app"]["paused"] is False


def test_emergency_kill_switch_api(client, db):
    """Verify emergency kill switch engages and disarms with DecisionLog entries."""
    # 1. Engage kill switch
    res_kill = client.post("/api/automation/kill", json={"active": True, "reason": "Emergency operator kill"})
    assert res_kill.status_code == 200
    assert res_kill.json()["kill_switch_active"] is True
    assert res_kill.json()["status"] == "KILLED"

    with db.read() as session:
        state = portfolio_state(session)
        assert state.kill_switch_active is True
        latest_dec = session.execute(
            select(DecisionLog).where(DecisionLog.action == "KILL_SWITCH").order_by(DecisionLog.id.desc())
        ).scalars().first()
        assert latest_dec is not None
        assert "Global kill switch" in latest_dec.reason

    # Verify orders are blocked when kill switch is active
    snap = client.get("/api/portfolio").json()
    assert snap["app"]["kill_switch_active"] is True

    # 2. Disarm kill switch
    res_disarm = client.post("/api/automation/kill", json={"active": False, "reason": "Operator resume"})
    assert res_disarm.status_code == 200
    assert res_disarm.json()["kill_switch_active"] is False
    assert res_disarm.json()["status"] == "ACTIVE"

    with db.read() as session:
        state = portfolio_state(session)
        assert state.kill_switch_active is False


def test_single_writer_handoff(client, auth_headers, db):
    """Verify single-writer handoff between Background 24/7 and Onscreen Live."""
    app = client.app
    if app.state.stocknow_client:
        app.state.stocknow_client.launch = AsyncMock(return_value={"status": "READY", "mode": "ONSCREEN_LIVE"})
        app.state.stocknow_client.close = AsyncMock(return_value={"status": "CLOSED"})
        app.state.stocknow_client.ensure_authenticated = AsyncMock(return_value={"status": "AUTHENTICATED"})

    # 1. Handoff to Background 24/7
    res_bg = client.post("/api/automation/handoff", json={"target_mode": "BACKGROUND_24_7"})
    assert res_bg.status_code == 200
    assert res_bg.json()["status"] == "HANDOFF_COMPLETE"
    assert res_bg.json()["active_mode"] == "BACKGROUND_POLLING"

    with db.read() as session:
        state = portfolio_state(session)
        assert state.ingestion_mode == "BACKGROUND_POLLING"

    # 2. Handoff to Onscreen Live
    res_live = client.post("/api/automation/handoff", json={"target_mode": "ONSCREEN_LIVE"})
    assert res_live.status_code == 200
    assert res_live.json()["status"] == "HANDOFF_COMPLETE"
    assert res_live.json()["active_mode"] == "ONSCREEN_LIVE"

    with db.read() as session:
        state = portfolio_state(session)
        assert state.ingestion_mode == "ONSCREEN_LIVE"

    # 3. Kernel API handoff endpoint
    k_res = client.post("/k/automation/handoff", json={"target_mode": "BACKGROUND_24_7"}, headers=auth_headers)
    assert k_res.status_code == 200
    assert k_res.json()["status"] == "HANDOFF_COMPLETE"
    assert k_res.json()["active_mode"] == "BACKGROUND_POLLING"


def test_preview_mode_when_master_automation_off(client, db):
    """When master automation is OFF, running a cycle executes a labeled PREVIEW.
    Zero orders are submitted, no ledger or tax lots are modified, and decisions are labeled MASTER_OFF."""
    # Ensure master automation is OFF
    client.post("/api/automation/config", json={"automation_enabled": False})

    # Record baseline ledger/tax lot state
    with db.read() as session:
        initial_trades = session.execute(select(TradeLog)).scalars().all()
        initial_lots = session.execute(select(TaxLot)).scalars().all()
        initial_trades_count = len(initial_trades)
        initial_lots_count = len(initial_lots)

    # Run cycle now
    res = client.post("/api/automation/cycle")
    assert res.status_code == 200
    data = res.json()

    assert data["is_preview"] is True
    assert data["status"] == "PREVIEW"

    # Verify zero trades executed in database
    with db.read() as session:
        post_trades = session.execute(select(TradeLog)).scalars().all()
        post_lots = session.execute(select(TaxLot)).scalars().all()
        assert len(post_trades) == initial_trades_count
        assert len(post_lots) == initial_lots_count

        # Check that decisions logged for this preview cycle carry MASTER_OFF reason tag
        cycle_id = data.get("cycle_id") or data.get("id")
        decisions = session.execute(
            select(DecisionLog).where(DecisionLog.cycle_id == cycle_id)
        ).scalars().all()
        for dec in decisions:
            if "PREVIEW" in dec.action:
                assert "MASTER_OFF" in dec.reason


def test_decision_stream_skip_reasons(client, db):
    """Verify explicit skip reasons are logged into Decision stream:
    - NO_SESSION: Friday or Saturday outside session
    - MARKET_CLOSED: Outside DSE trading window in LIVE_HOURS
    - KILL_SWITCH: Emergency kill switch active
    """
    settings = client.app.state.settings
    trader = AutoTrader(db, settings)

    # 1. Test KILL_SWITCH skip
    with db.write() as session:
        state = portfolio_state(session)
        state.automation_enabled = True
        state.kill_switch_active = True
        state.trading_mode = "LIVE_HOURS"

    res_kill = trader.run_cycle(dry_run=False)
    assert res_kill["status"] == "SKIPPED"
    assert res_kill["reason"] == "KILL_SWITCH"

    with db.read() as session:
        skip_log = session.execute(
            select(DecisionLog).where(DecisionLog.action.like("KILL_SWITCH%")).order_by(DecisionLog.id.desc())
        ).scalars().first()
        assert skip_log is not None
        assert "KILL_SWITCH" in skip_log.reason

    # Reset kill switch
    with db.write() as session:
        state = portfolio_state(session)
        state.kill_switch_active = False

    # 2. Test NO_SESSION skip (e.g. Friday in Dhaka)
    with db.write() as session:
        state = portfolio_state(session)
        state.clock_date = datetime.date(2026, 11, 6)  # Friday (weekend in DSE)
        state.trading_mode = "LIVE_HOURS"

    res_no_session = trader.run_cycle(dry_run=False)
    assert res_no_session["status"] == "SKIPPED"
    assert res_no_session["reason"] == "NO_SESSION"

    with db.read() as session:
        skip_log = session.execute(
            select(DecisionLog).where(DecisionLog.action == "NO_SESSION").order_by(DecisionLog.id.desc())
        ).scalars().first()
        assert skip_log is not None
        assert "NO_SESSION" in skip_log.reason

    # 3. Test MARKET_CLOSED skip (e.g. Tuesday outside DSE hours)
    with db.write() as session:
        state = portfolio_state(session)
        state.clock_date = datetime.date(2026, 11, 3)  # Tuesday (trading day)
        state.mode = "LIVE"

    with patch("backend.engine.scheduler.is_dse_market_open", return_value={"is_open": False, "reason": "Trading closed outside 10:00-14:30"}):
        res_closed = trader.run_cycle(dry_run=False)
        assert res_closed["status"] == "SKIPPED"
        assert res_closed["reason"] == "MARKET_CLOSED"

    with db.read() as session:
        skip_log = session.execute(
            select(DecisionLog).where(DecisionLog.action == "MARKET_CLOSED").order_by(DecisionLog.id.desc())
        ).scalars().first()
        assert skip_log is not None
        assert "MARKET_CLOSED" in skip_log.reason


def test_identical_decisions_in_both_run_modes(client, db):
    """Requirement 5: Both modes ('Onscreen Live' and 'Background 24/7')
    make identical decisions for the same snapshot."""
    settings = client.app.state.settings
    trader = AutoTrader(db, settings)

    # Setup test mode so market hours don't block
    with db.write() as session:
        state = portfolio_state(session)
        state.trading_mode = "TEST_OFFHOURS"
        state.kill_switch_active = False
        state.automation_enabled = True

    # 1. Run evaluation under BACKGROUND_POLLING mode
    with db.write() as session:
        state = portfolio_state(session)
        state.ingestion_mode = "BACKGROUND_POLLING"

    # Dry-run evaluation produces decision list
    res_background = trader.run_cycle(dry_run=True)

    # 2. Run evaluation under ONSCREEN_LIVE mode
    with db.write() as session:
        state = portfolio_state(session)
        state.ingestion_mode = "ONSCREEN_LIVE"

    res_onscreen = trader.run_cycle(dry_run=True)

    # Extract decisions from both runs as serializable tuples
    with db.read() as session:
        decisions_bg = [
            (d.symbol, d.action, d.quantity, d.reason)
            for d in session.execute(
                select(DecisionLog).where(DecisionLog.cycle_id == res_background["cycle_id"]).order_by(DecisionLog.symbol)
            ).scalars().all()
        ]
        decisions_live = [
            (d.symbol, d.action, d.quantity, d.reason)
            for d in session.execute(
                select(DecisionLog).where(DecisionLog.cycle_id == res_onscreen["cycle_id"]).order_by(DecisionLog.symbol)
            ).scalars().all()
        ]

    assert len(decisions_bg) > 0, "Expected non-empty decisions for snapshot"
    assert len(decisions_bg) == len(decisions_live), "Decision count must be identical across run modes"
    assert decisions_bg == decisions_live, "All symbol decisions, actions, quantities & reasons must match 100%"

    assert res_background["buy_count"] == res_onscreen["buy_count"]
    assert res_background["sell_count"] == res_onscreen["sell_count"]
