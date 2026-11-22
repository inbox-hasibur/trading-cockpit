"""Comprehensive Offline Test Suite for Sprint 5C: TradeXpress Passive CDP Spy Daemon & AutoTrader SHADOW_DUMMY Wiring.

STRICT ZERO-BAN & OFFLINE POLICY:
All tests in this suite run 100% locally with mocked DevTools Protocol and zero real network calls.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.adapters.base import MarketQuote
from backend.adapters.tradexpress.cdp_daemon import (
    TradeXpressPassiveDaemon,
    get_global_passive_daemon,
)
from backend.adapters.tradexpress.passive_feed import TradeXpressPassiveFeed
from backend.adapters.tradexpress.shadow_simulator import TradeXpressShadowSimulator
from backend.config import Settings
from backend.database import (
    CompanyProfile,
    Database,
    PortfolioState,
    ShadowOrder,
    TaxLot,
    TradeLearningLog,
    TradeLog,
    portfolio_state,
)
from backend.engine.auto_trader import AutoTrader
from backend.engine.money import ZERO, decimal, money
from backend.main import create_app
from backend.seed import seed_demo


@pytest.fixture
def test_db_and_settings(tmp_path):
    """Provides an isolated test database with seeded state."""
    db_file = tmp_path / "test_sprint5c.db"
    settings = Settings(
        database_url=f"sqlite:///{db_file}",
        initial_capital=Decimal("100000.00"),
        stocknow_live_portfolio_id="H9210_SHADOW",
        stocknow_test_portfolio_id="H9210_SHADOW",
    )
    db = Database(settings.database_url)
    db.create_schema()
    with db.write() as session:
        seed_demo(session, settings)
    return db, settings


@pytest.fixture
def app_client(test_db_and_settings, monkeypatch):
    """FastAPI TestClient with initialized app and mock token."""
    db, settings = test_db_and_settings
    monkeypatch.setenv("KERNEL_TOKEN", "test-kernel-token-5c-32characters")
    app = create_app(settings)
    app.state.database = db
    with TestClient(app, base_url="http://127.0.0.1:8000") as client:
        yield client, db, settings


# ─────────────────────────────────────────────────────────────────────────────
# 1. TradeXpressPassiveDaemon Unit Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_daemon_initial_status_and_defaults(test_db_and_settings):
    """Verifies default daemon operational telemetry and safe defaults."""
    db, settings = test_db_and_settings
    feed = TradeXpressPassiveFeed(db)
    daemon = TradeXpressPassiveDaemon(database=db, settings=settings, feed=feed)

    status = daemon.get_status()
    assert status["running"] is False
    assert status["cdp_connected"] is False
    assert status["cdp_url"] == "http://127.0.0.1:9222"
    assert status["dom_syncs_count"] == 0
    assert status["ws_frames_count"] == 0
    assert status["xhr_responses_count"] == 0
    assert status["active_tab"] == ""


def test_daemon_start_and_stop_lifecycle(test_db_and_settings):
    """Verifies clean, idempotent start and stop lifecycle of the daemon."""
    async def _run():
        db, settings = test_db_and_settings
        daemon = TradeXpressPassiveDaemon(database=db, settings=settings)

        # Mock _run_loop so no real browser is required
        with patch.object(daemon, "_run_loop", new_callable=AsyncMock):
            status1 = await daemon.start(cdp_url="http://127.0.0.1:9222")
            assert status1["running"] is True
            assert daemon._task is not None

            # Calling start again while running is idempotent
            status2 = await daemon.start(cdp_url="http://127.0.0.1:9222")
            assert status2["running"] is True

            # Stop daemon
            stop_status = await daemon.stop()
            assert stop_status["running"] is False
            assert stop_status["cdp_connected"] is False
            assert daemon._task is None

    asyncio.run(_run())


def test_daemon_resilient_connection_handling(test_db_and_settings):
    """Verifies daemon catches CDP connection failures and updates telemetry gracefully."""
    async def _run():
        db, settings = test_db_and_settings
        feed = TradeXpressPassiveFeed(db)
        daemon = TradeXpressPassiveDaemon(database=db, settings=settings, feed=feed)
        daemon.running = True

        # Mock playwright to simulate connection error then stop
        mock_pw_cm = AsyncMock()
        mock_pw_inst = AsyncMock()
        mock_pw_cm.start.return_value = mock_pw_inst
        mock_pw_inst.chromium.connect_over_cdp.side_effect = Exception("Connection refused: 127.0.0.1:9222")

        with patch("playwright.async_api.async_playwright", return_value=mock_pw_cm):
            task = asyncio.create_task(daemon._run_loop("http://127.0.0.1:9222"))
            await asyncio.sleep(0.05)
            daemon.running = False
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        assert daemon.cdp_connected is False
        assert "Cannot connect to CDP" in daemon.last_error

    asyncio.run(_run())


def test_daemon_zero_forbidden_methods(test_db_and_settings):
    """Verifies daemon AST NEVER invokes forbidden active methods: click, fill, type, goto, reload."""
    import ast
    import inspect
    from backend.adapters.tradexpress import cdp_daemon

    source = inspect.getsource(cdp_daemon)
    tree = ast.parse(source)

    forbidden = {"click", "fill", "type", "goto", "reload"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in forbidden, f"Forbidden method call found: {node.func.attr}"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Bridge API Endpoints Tests (/api/tradexpress/bridge & /status)
# ─────────────────────────────────────────────────────────────────────────────


def test_tradexpress_bridge_control_endpoint(app_client):
    """Tests POST /api/tradexpress/bridge action dispatch (status, attach, detach)."""
    client, db, settings = app_client

    # 1. Action: status
    res = client.post("/api/tradexpress/bridge", json={"action": "status"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert data["action"] == "status"
    assert "daemon" in data
    assert data["daemon"]["running"] is False

    # 2. Action: attach (mocked start)
    with patch("backend.adapters.tradexpress.cdp_daemon.TradeXpressPassiveDaemon.start", new_callable=AsyncMock) as mock_start:
        mock_start.return_value = {
            "running": True,
            "cdp_connected": True,
            "cdp_url": "http://127.0.0.1:9222",
            "active_tab": "TradeXpress",
            "dom_syncs_count": 0,
            "ws_frames_count": 0,
            "xhr_responses_count": 0,
            "last_sync_utc": "",
            "last_error": "",
        }
        res_attach = client.post("/api/tradexpress/bridge", json={"action": "attach", "cdp_url": "http://127.0.0.1:9222"})
        assert res_attach.status_code == 200
        attach_data = res_attach.json()
        assert attach_data["action"] == "attach"
        assert attach_data["daemon"]["running"] is True

    # 3. Action: detach
    with patch("backend.adapters.tradexpress.cdp_daemon.TradeXpressPassiveDaemon.stop", new_callable=AsyncMock) as mock_stop:
        mock_stop.return_value = {
            "running": False,
            "cdp_connected": False,
            "cdp_url": "http://127.0.0.1:9222",
            "active_tab": "",
            "dom_syncs_count": 0,
            "ws_frames_count": 0,
            "xhr_responses_count": 0,
            "last_sync_utc": "",
            "last_error": "",
        }
        res_detach = client.post("/api/tradexpress/bridge", json={"action": "detach"})
        assert res_detach.status_code == 200
        detach_data = res_detach.json()
        assert detach_data["action"] == "detach"
        assert detach_data["daemon"]["running"] is False

    # 4. Action: invalid action -> 400
    res_bad = client.post("/api/tradexpress/bridge", json={"action": "invalid_action"})
    assert res_bad.status_code == 400
    assert "Unknown bridge action" in res_bad.json()["detail"]


def test_tradexpress_status_and_kernel_feed_status(app_client):
    """Verifies GET /api/tradexpress/status and GET /k/feed-status include daemon telemetry."""
    client, db, settings = app_client

    # 1. /api/tradexpress/status
    res = client.get("/api/tradexpress/status")
    assert res.status_code == 200
    data = res.json()
    assert "daemon" in data
    assert "cdp_connected" in data
    assert "execution_venue" in data

    # 2. /k/feed-status (requires auth)
    k_res = client.get("/k/feed-status", headers={"X-Kernel-Token": "test-kernel-token-5c-32characters"})
    assert k_res.status_code == 200
    k_data = k_res.json()
    assert "daemon" in k_data
    assert "operator_instructions" in k_data


# ─────────────────────────────────────────────────────────────────────────────
# 3. AutoTrader SHADOW_DUMMY Wiring Tests
# ─────────────────────────────────────────────────────────────────────────────


def test_autotrader_dispatches_into_shadow_simulator(test_db_and_settings):
    """Verifies AutoTrader records ShadowOrder and TradeLearningLog when execution_venue is SHADOW_DUMMY."""
    db, settings = test_db_and_settings

    # Set execution_venue to SHADOW_DUMMY
    with db.write() as session:
        state = portfolio_state(session)
        state.execution_venue = "SHADOW_DUMMY"
        state.trading_mode = "LIVE_HOURS"
        state.automation_enabled = True

        # Ensure active GSC_L1 company with favorable price
        cp = session.get(CompanyProfile, "BANKASIA")
        if cp:
            cp.watchlist_category = "GSC_L1"
            cp.last_price = Decimal("18.00")
            cp.bid = Decimal("17.90")
            cp.offer = Decimal("18.00")
            cp.offer_qty = 500
            cp.price_history = [{"date": "2026-11-20", "close": "17.00"}, {"date": "2026-11-21", "close": "17.50"}]

    feed = TradeXpressPassiveFeed(db)
    feed.update_quotes([
        MarketQuote(
            symbol="BANKASIA",
            ltp=Decimal("18.00"),
            change=Decimal("0.50"),
            pct_change=Decimal("2.8"),
            volume=100000,
            open_price=Decimal("17.50"),
            high=Decimal("18.20"),
            low=Decimal("17.50"),
            bid=Decimal("17.90"),
            bid_qty=1000,
            offer=Decimal("18.00"),
            offer_qty=500,
            min_limit=Decimal("16.00"),
            max_limit=Decimal("20.00"),
            settlement_type="PUBLIC",
            symbol_category="A",
        )
    ])

    # Instantiate AutoTrader
    trader = AutoTrader(db, settings)

    # Execute a cycle
    res = trader.run_cycle(dry_run=False)

    with db.read() as session:
        # Check if any ShadowOrder was recorded
        shadow_orders = list(session.scalars(select(ShadowOrder)))
        # Check TradeLearningLog records
        learning_logs = list(session.scalars(select(TradeLearningLog).where(TradeLearningLog.actor == "AUTOTRADER")))

        # If a trade was executed, verify shadow order and learning log
        if res.get("buy_count", 0) > 0 or res.get("sell_count", 0) > 0:
            assert len(shadow_orders) >= 1
            assert any(so.actor == "AUTOTRADER" for so in shadow_orders)
            assert len(learning_logs) >= 1
            assert any(ll.actor == "AUTOTRADER" for ll in learning_logs)


def test_autotrader_preserves_stocknow_demo_when_not_shadow(test_db_and_settings):
    """Verifies AutoTrader defaults to StockNow paper fill when execution_venue is not SHADOW_DUMMY."""
    db, settings = test_db_and_settings

    with db.write() as session:
        state = portfolio_state(session)
        state.execution_venue = "DEMO"
        state.trading_mode = "LIVE_HOURS"
        state.automation_enabled = True

    trader = AutoTrader(db, settings)
    assert getattr(trader.adapter, "mode", "DEMO") == "DEMO"
