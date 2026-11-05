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
from backend.adapters.stocknow_order_executor import (
    clear_idempotency_cache,
    execute_stocknow_virtual_order,
)
from backend.config import Settings
from backend.database import Database, PortfolioState, TaxLot, TradeLog, portfolio_state
from backend.engine.t2_ledger import assert_ledger
from backend.hermes.agent_loop import CheckpointManager
from backend.hermes.skills_manager import SkillsManager
from backend.hermes.tools_dispatcher import (
    detect_intent_and_tool,
    dispatch_tool,
    format_tool_response,
)
from backend.main import create_app
from backend.seed import seed_demo


@pytest.fixture(autouse=True)
def reset_cache():
    clear_idempotency_cache()
    yield
    clear_idempotency_cache()


@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "test_stocknow_order.db"
    db_url = f"sqlite:///{db_file.as_posix()}"
    settings = Settings(database_url=db_url)
    db = Database(db_url)
    db.create_schema()
    with db.write() as session:
        seed_demo(session, settings)
    return db, settings


def test_execute_stocknow_virtual_order_paper_and_idempotency():
    """Verify virtual order execution and idempotency deduplication."""
    # 1. Normal execution
    receipt = asyncio.run(execute_stocknow_virtual_order(
        symbol="GP",
        side="BUY",
        quantity=10,
        price=Decimal("260.00"),
        portfolio_id="Humming Bird",
        idempotency_key="CYCLE_001_GP_BUY",
        dry_run=True,
    ))
    assert receipt["success"] is True
    assert receipt["status"] == "ACKNOWLEDGED"
    assert receipt["execution_mode"] == "PAPER_VERIFIED"
    assert receipt["symbol"] == "GP"
    assert receipt["side"] == "BUY"
    assert receipt["quantity"] == 10
    assert receipt["price"] == 260.0
    assert receipt["idempotency_key"] == "CYCLE_001_GP_BUY"
    assert "order_id" in receipt

    # 2. Duplicate order with same idempotency_key
    dup_receipt = asyncio.run(execute_stocknow_virtual_order(
        symbol="GP",
        side="BUY",
        quantity=10,
        price=Decimal("260.00"),
        idempotency_key="CYCLE_001_GP_BUY",
    ))
    assert dup_receipt["duplicate"] is True
    assert dup_receipt["status"] == "ALREADY_EXECUTED"
    assert dup_receipt["order_id"] == receipt["order_id"]


def test_execute_stocknow_virtual_order_live_dom():
    """Verify live DOM execution path when active browser page is attached."""
    mock_page = AsyncMock()
    mock_page.is_closed = MagicMock(return_value=False)
    mock_page.query_selector = AsyncMock(return_value=MagicMock())
    mock_page.fill = AsyncMock()
    mock_page.click = AsyncMock()

    mock_client = MagicMock()
    mock_client.page = mock_page

    receipt = asyncio.run(execute_stocknow_virtual_order(
        client=mock_client,
        symbol="BANKASIA",
        side="BUY",
        quantity=50,
        price=Decimal("20.00"),
        dry_run=False,
    ))
    assert receipt["success"] is True
    assert receipt["status"] == "ACKNOWLEDGED"
    assert receipt["execution_mode"] == "STOCKNOW_LIVE_DOM"
    assert receipt["symbol"] == "BANKASIA"
    mock_page.fill.assert_any_call("#order-symbol, input[name='symbol'], input[placeholder*='Symbol']", "BANKASIA")
    mock_page.click.assert_called()


def test_stocknow_adapter_order_delegation():
    """Verify StockNowAdapter.execute_order() updates status telemetry."""
    adapter = StockNowAdapter()
    receipt = asyncio.run(adapter.execute_order(
        symbol="SQURPHARMA",
        side="BUY",
        quantity=5,
        price=Decimal("210.00"),
        dry_run=True,
    ))
    assert receipt["status"] == "ACKNOWLEDGED"
    status = adapter.get_adapter_status()
    assert status["last_order_receipt"] is not None
    assert status["last_order_receipt"]["symbol"] == "SQURPHARMA"


def test_api_execute_order_buy_and_rollback(test_db):
    """Verify POST /api/stocknow/execute-order records BUY in SQLite and /rollback restores cleanly."""
    db, settings = test_db
    app = create_app(settings)
    api_client = TestClient(app, base_url="http://localhost")

    with db.read() as session:
        initial_lots_count = len(session.scalars(select(TaxLot)).all())

    # 1. Execute BUY
    payload = {
        "symbol": "BANKASIA",
        "side": "BUY",
        "quantity": 10,
        "dry_run": True,
        "idempotency_key": "API_TEST_BUY_01",
    }
    resp = api_client.post("/api/stocknow/execute-order", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["trade"]["side"] == "BUY"
    assert data["trade"]["quantity"] == 10
    assert data["receipt"]["status"] == "ACKNOWLEDGED"
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
        assert "STOCKNOW_BUY" in rb_res["action_reverted"]

    # Verify state restored
    with db.read() as session:
        state = portfolio_state(session)
        assert_ledger(session, state)
        lots = session.scalars(select(TaxLot)).all()
        assert len(lots) == initial_lots_count


def test_api_execute_order_matured_sell_and_restrictions(test_db):
    """Verify matured profitable SELL succeeds, while net-loss or immature SELL is rejected."""
    db, settings = test_db
    app = create_app(settings)
    api_client = TestClient(app, base_url="http://localhost")

    # In seed_demo:
    # SQURPHARMA: bought at 200, last_price=216, offset=-2 (matures_on <= today) -> mature and in profit!
    # 1. Profitable mature sell of 5 SQURPHARMA shares
    sell_payload = {
        "symbol": "SQURPHARMA",
        "side": "SELL",
        "quantity": 5,
        "dry_run": True,
        "idempotency_key": "API_TEST_SELL_01",
    }
    resp = api_client.post("/api/stocknow/execute-order", json=sell_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["trade"]["side"] == "SELL"
    assert data["trade"]["quantity"] == 5
    assert data["trade"]["realized_pnl"] > 0
    assert data["receipt"]["status"] == "ACKNOWLEDGED"

    with db.read() as session:
        state = portfolio_state(session)
        assert_ledger(session, state)

    # 2. Reject immature sell
    # In seed_demo: BANKASIA has offset=0 (matures_on is T+2 sessions in future) -> immature!
    immature_payload = {
        "symbol": "BANKASIA",
        "side": "SELL",
        "quantity": 5,
    }
    resp_immature = api_client.post("/api/stocknow/execute-order", json=immature_payload)
    assert resp_immature.status_code == 400
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
    }
    resp_loss = api_client.post("/api/stocknow/execute-order", json=loss_payload)
    assert resp_loss.status_code == 400
    assert "strict no-loss" in resp_loss.json()["detail"].lower()


def test_hermes_tool_execute_manual_order(test_db):
    """Verify Hermes conversational Buy and Matured Sell commands attach StockNow order receipt."""
    db, settings = test_db
    skills_mgr = SkillsManager()

    # 1. Natural Language Intent Detection
    tool_buy, args_buy = detect_intent_and_tool("Buy 10 GP", {})
    assert tool_buy == "execute_manual_order"
    assert args_buy["symbol"] == "GP"
    assert args_buy["side"] == "BUY"
    assert args_buy["quantity"] == 10

    tool_bn, args_bn = detect_intent_and_tool("GP 10 ta share kine felo", {})
    assert tool_bn == "execute_manual_order"
    assert args_bn["symbol"] == "GP"
    assert args_bn["side"] == "BUY"
    assert args_bn["quantity"] == 10

    tool_sell, args_sell = detect_intent_and_tool("Sell 5 SQURPHARMA", {})
    assert tool_sell == "execute_manual_order"
    assert args_sell["symbol"] == "SQURPHARMA"
    assert args_sell["side"] == "SELL"
    assert args_sell["quantity"] == 5

    # 2. Dispatch manual BUY via Hermes
    with db.write() as session:
        state = session.get(PortfolioState, 1)
        res_buy = dispatch_tool(
            "execute_manual_order",
            {"symbol": "BANKASIA", "side": "BUY", "quantity": 10},
            session,
            state,
            settings,
            skills_mgr,
            CheckpointManager,
        )
        assert res_buy["status"] == "SUCCESS"
        assert res_buy["result"]["receipt"]["status"] == "ACKNOWLEDGED"

        fmt_bn = format_tool_response("execute_manual_order", res_buy, "buy koro", {})
        assert "কেনা হয়েছে" in fmt_bn
        assert "StockNow ভার্চুয়াল রসিদ" in fmt_bn

    # 3. Dispatch manual SELL via Hermes (SQURPHARMA is mature and profitable)
    with db.write() as session:
        state = session.get(PortfolioState, 1)
        res_sell = dispatch_tool(
            "execute_manual_order",
            {"symbol": "SQURPHARMA", "side": "SELL", "quantity": 5},
            session,
            state,
            settings,
            skills_mgr,
            CheckpointManager,
        )
        assert res_sell["status"] == "SUCCESS"
        assert res_sell["result"]["side"] == "SELL"
        assert res_sell["result"]["receipt"]["status"] == "ACKNOWLEDGED"

        fmt_en = format_tool_response("execute_manual_order", res_sell, "sell now", {})
        assert "Sold 5 mature shares" in fmt_en
        assert "StockNow Virtual Receipt" in fmt_en
