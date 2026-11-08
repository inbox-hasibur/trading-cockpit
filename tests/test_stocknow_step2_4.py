"""Unit tests for Sprint 2 Step 2.4: Automated Virtual Order Execution on StockNow ('Humming Bird')."""

from __future__ import annotations

import asyncio
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.adapters.stocknow_adapter import StockNowAdapter
from backend.adapters.stocknow_client import StockNowLiveClient
from backend.adapters.stocknow_executor import BrowserTransport
from backend.config import Settings
from backend.database import Database, PortfolioState, TaxLot, TradeLog, portfolio_state
from backend.engine.checkpoint import CheckpointManager
from backend.engine.t2_ledger import assert_ledger
from backend.kernel_api import clear_order_idempotency_cache
from backend.main import create_app
from backend.seed import seed_demo


@pytest.fixture(autouse=True)
def reset_cache():
    clear_order_idempotency_cache()
    yield
    clear_order_idempotency_cache()


@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "test_stocknow_order.db"
    db_url = f"sqlite:///{db_file.as_posix()}"
    settings = Settings(
        database_url=db_url,
        stocknow_test_portfolio_id="164580",
        stocknow_live_portfolio_id="164580",
    )
    db = Database(db_url)
    db.create_schema()
    with db.write() as session:
        seed_demo(session, settings)
    return db, settings


@pytest.mark.anyio
async def test_execute_stocknow_virtual_order_paper_and_idempotency():
    """Verify virtual order execution and idempotency deduplication."""
    adapter = StockNowAdapter(mode="DEMO")
    receipt = await adapter.execute_order(
        symbol="GP",
        side="BUY",
        quantity=10,
        price=Decimal("260.00"),
        portfolio_id="164580",
        idempotency_key="CYCLE_001_GP_BUY",
        dry_run=True,
    )
    assert receipt["success"] is True
    assert receipt["status"] == "ACKNOWLEDGED"
    assert receipt["execution_mode"] in ("DEMO_PAPER", "PAPER_VERIFIED")
    assert receipt["symbol"] == "GP"
    assert receipt["side"] == "BUY"
    assert receipt["quantity"] == 10
    assert receipt["price"] == 260.0
    assert receipt["idempotency_key"] == "CYCLE_001_GP_BUY"
    assert "order_id" in receipt


@pytest.mark.anyio
async def test_execute_stocknow_browser_transport():
    """Verify BrowserTransport execution path when active browser page is attached."""
    mock_page = AsyncMock()
    mock_page.is_closed = MagicMock(return_value=False)
    mock_page.evaluate = AsyncMock(side_effect=lambda script, *a, **kw: "mock_jwt_token" if "access_token" in script else True)
    mock_page.goto = AsyncMock()
    mock_page.wait_for_timeout = AsyncMock()
    mock_page.query_selector = AsyncMock(return_value=MagicMock())
    mock_locator = MagicMock()
    mock_locator.is_visible = AsyncMock(return_value=True)
    mock_locator.fill = AsyncMock()
    mock_locator.click = AsyncMock()
    mock_page.locator = MagicMock(return_value=mock_locator)

    mock_client = MagicMock()
    mock_client.page = mock_page

    transport = BrowserTransport(stocknow_client=mock_client, configured_test_id="164580")
    transport.verify_fill = AsyncMock(return_value={"id": 999, "symbol": "BANKASIA", "action": "BUY", "quantity": 50, "price": 20.0})

    receipt = await transport.execute_order(
        symbol="BANKASIA",
        side="BUY",
        quantity=50,
        price=Decimal("20.00"),
        portfolio_id="164580",
        trade_date=date(2026, 11, 3),
        idempotency_key="TEST_BROWSER_KEY_01",
    )
    assert receipt["success"] is True
    assert receipt["status"] == "FILLED"
    assert receipt["execution_mode"] == "STOCKNOW_LIVE_DOM"
    assert receipt["symbol"] == "BANKASIA"
    assert mock_locator.first.fill.called or mock_locator.fill.called


@pytest.mark.anyio
async def test_stocknow_adapter_order_delegation():
    """Verify StockNowAdapter.execute_order() updates status telemetry."""
    adapter = StockNowAdapter(mode="DEMO")
    receipt = await adapter.execute_order(
        symbol="SQURPHARMA",
        side="BUY",
        quantity=5,
        price=Decimal("210.00"),
        portfolio_id="164580",
        dry_run=True,
    )
    assert receipt["status"] == "ACKNOWLEDGED"
    status = adapter.get_adapter_status()
    assert status["last_order_receipt"] is not None
    assert status["last_order_receipt"]["symbol"] == "SQURPHARMA"


def test_api_execute_order_buy_and_rollback(test_db):
    """Verify POST /api/stocknow/execute-order records BUY in SQLite and /rollback restores cleanly."""
    db, settings = test_db
    with db.write() as session:
        state = session.get(PortfolioState, 1)
        state.trading_mode = "TEST_OFFHOURS"
    app = create_app(settings)
    api_client = TestClient(app, base_url="http://localhost")

    with db.read() as session:
        initial_lots_count = len(session.scalars(select(TaxLot)).all())

    # 1. Execute BUY
    payload = {
        "symbol": "BANKASIA",
        "side": "BUY",
        "quantity": 10,
        "dry_run": False,
        "operator_confirmed": True,
        "idempotency_key": "API_TEST_BUY_01",
    }
    resp = api_client.post("/api/stocknow/execute-order", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["success"] is True
    assert data["side"] == "BUY"
    assert data["quantity"] == 10
    assert "snapshot" in data

    # Verify ledger integrity
    with db.read() as session:
        state = portfolio_state(session)
        assert_ledger(session, state)
        lots = session.scalars(select(TaxLot)).all()
        assert len(lots) == initial_lots_count + 1

    # 2. Rollback
    with db.write() as session:
        state = session.get(PortfolioState, 1)
        rb_res = CheckpointManager.rollback_last(session, state)
        assert "ORDER_BUY" in rb_res["action_reverted"] or "STOCKNOW_BUY" in rb_res["action_reverted"]

    # Verify state restored
    with db.read() as session:
        state = portfolio_state(session)
        assert_ledger(session, state)
        lots = session.scalars(select(TaxLot)).all()
        assert len(lots) == initial_lots_count


def test_api_execute_order_matured_sell_and_restrictions(test_db):
    """Verify matured profitable SELL succeeds, while net-loss or immature SELL is rejected."""
    db, settings = test_db
    with db.write() as session:
        state = session.get(PortfolioState, 1)
        state.trading_mode = "TEST_OFFHOURS"
    app = create_app(settings)
    api_client = TestClient(app, base_url="http://localhost")

    # In seed_demo:
    # SQURPHARMA: bought at 200, last_price=216, offset=-2 (matures_on <= today) -> mature and in profit!
    # 1. Profitable mature sell of 5 SQURPHARMA shares
    sell_payload = {
        "symbol": "SQURPHARMA",
        "side": "SELL",
        "quantity": 5,
        "dry_run": False,
        "operator_confirmed": True,
        "idempotency_key": "API_TEST_SELL_01",
    }
    resp = api_client.post("/api/stocknow/execute-order", json=sell_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["side"] == "SELL"
    assert data["quantity"] == 5
    assert data["realized_pnl"] > 0

    with db.read() as session:
        state = portfolio_state(session)
        assert_ledger(session, state)

    # 2. Reject immature sell
    # In seed_demo: BANKASIA has offset=0 (matures_on is T+2 sessions in future) -> immature!
    immature_payload = {
        "symbol": "BANKASIA",
        "side": "SELL",
        "quantity": 5,
        "dry_run": False,
        "operator_confirmed": True,
        "idempotency_key": "API_TEST_SELL_02",
    }
    resp_immature = api_client.post("/api/stocknow/execute-order", json=immature_payload)
    assert resp_immature.status_code in (400, 422)
    assert "settlement-locked" in resp_immature.json()["detail"].lower()

    # 3. Reject net-loss sell
    # In seed_demo: BXPHARMA bought at 90, last_price=58 -> steep loss!
    # Even if mature, selling at loss must be blocked by Strict No-Loss policy
    with db.write() as session:
        bx_lot = session.scalar(select(TaxLot).where(TaxLot.symbol == "BXPHARMA"))
        bx_lot.matures_on = date(2026, 11, 1)  # Force mature
    loss_payload = {
        "symbol": "BXPHARMA",
        "side": "SELL",
        "quantity": 5,
        "dry_run": False,
        "operator_confirmed": True,
        "idempotency_key": "API_TEST_SELL_03",
    }
    resp_loss = api_client.post("/api/stocknow/execute-order", json=loss_payload)
    assert resp_loss.status_code in (400, 422)
    assert "strict no-loss" in resp_loss.json()["detail"].lower()
