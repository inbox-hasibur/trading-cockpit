"""Unit tests for Sprint 2 Step 2.3: 'Humming Bird' Virtual Portfolio Sync & Ledger Reconciliation."""

from __future__ import annotations

import asyncio
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.adapters.stocknow_client import StockNowLiveClient
from backend.adapters.stocknow_portfolio_sync import (
    extract_hummingbird_portfolio,
    reconcile_portfolio_to_db,
)
from backend.config import Settings
from backend.database import Database, PortfolioState, TaxLot, TradeLog, portfolio_state
from backend.engine.t2_ledger import assert_ledger, bucket_balances
from backend.hermes.agent_loop import CheckpointManager
from backend.hermes.skills_manager import SkillsManager
from backend.hermes.tools_dispatcher import (
    detect_intent_and_tool,
    dispatch_tool,
    format_tool_response,
)
from backend.main import create_app
from backend.seed import seed_demo


@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "test_stocknow_portfolio_sync.db"
    db_url = f"sqlite:///{db_file.as_posix()}"
    settings = Settings(database_url=db_url)
    db = Database(db_url)
    db.create_schema()
    with db.write() as session:
        seed_demo(session, settings)
    return db, settings


def test_extract_hummingbird_portfolio_direct_and_list():
    """Verify extraction handles direct dict, list of portfolios, and nested items."""
    # 1. Direct dict
    payload_direct = {
        "id": "hb_001",
        "name": "Humming Bird",
        "cash_balance": 4892.92,
        "holdings": [
            {"symbol": "BANKASIA", "quantity": 50, "avg_cost": 20.0, "acquired_date": "2026-11-04"},
            {"symbol": "GP", "quantity": 10, "avg_cost": 260.0, "acquired_date": "2026-11-02"},
        ],
    }
    res = extract_hummingbird_portfolio(injected_portfolio=payload_direct)
    assert res["portfolio_id"] == "hb_001"
    assert res["portfolio_name"] == "Humming Bird"
    assert res["cash_balance"] == Decimal("4892.92")
    assert len(res["holdings"]) == 2
    assert res["holdings"][0]["symbol"] == "BANKASIA"
    assert res["holdings"][0]["quantity"] == 50
    assert res["holdings"][0]["avg_cost"] == Decimal("20.0")

    # 2. List of portfolios with matching name
    payload_list = {
        "portfolios": [
            {"id": "p_99", "name": "Growth Speculation", "cash": 1000},
            {
                "id": "p_102",
                "portfolio_name": "Humming Bird",
                "cash": 3500.50,
                "stocks": [{"ticker": "SQURPHARMA", "shares": 25, "rate": 210.0}],
            },
        ]
    }
    res_list = extract_hummingbird_portfolio(injected_portfolio=payload_list)
    assert res_list["portfolio_id"] == "p_102"
    assert res_list["cash_balance"] == Decimal("3500.50")
    assert len(res_list["holdings"]) == 1
    assert res_list["holdings"][0]["symbol"] == "SQURPHARMA"
    assert res_list["holdings"][0]["quantity"] == 25
    assert res_list["holdings"][0]["avg_cost"] == Decimal("210.0")


def test_extract_hummingbird_portfolio_from_sniffer():
    """Verify extraction finds portfolio in client.captured_endpoints."""
    client = StockNowLiveClient()
    client.captured_endpoints["/api/user/virtual-portfolios"] = {
        "url": "https://stocknow.com.bd/api/user/virtual-portfolios",
        "status": 200,
        "data": [
            {
                "id": "hb_virtual_77",
                "name": "Humming Bird",
                "available_cash": 6200.0,
                "holdings": [
                    {"symbol": "BANKASIA", "qty": 40, "average_cost": 19.50},
                ],
            }
        ],
    }
    res = extract_hummingbird_portfolio(client=client)
    assert res["portfolio_id"] == "hb_virtual_77"
    assert res["cash_balance"] == Decimal("6200.0")
    assert len(res["holdings"]) == 1
    assert res["holdings"][0]["symbol"] == "BANKASIA"


def test_reconcile_portfolio_to_db_and_assert_ledger(test_db):
    """Verify holdings and cash balance reconcile into SQLite and assert_ledger passes 100%."""
    db, settings = test_db

    portfolio_data = {
        "portfolio_id": "hb_sync_101",
        "portfolio_name": "Humming Bird",
        "cash_balance": Decimal("5000.00"),
        "holdings": [
            {"symbol": "BANKASIA", "quantity": 50, "avg_cost": Decimal("20.00"), "acquired_date": "2026-11-04"},
            {"symbol": "SQURPHARMA", "quantity": 15, "avg_cost": Decimal("210.00"), "acquired_date": "2026-11-02"},
            {"symbol": "GP", "quantity": 8, "avg_cost": Decimal("265.00"), "acquired_date": "2026-11-01"},
        ],
    }

    # Execute reconciliation
    res = reconcile_portfolio_to_db(db, settings, portfolio_data)
    assert res["success"] is True
    assert res["synced_holdings_count"] == 3
    assert "checkpoint_id" in res

    # Verify ledger integrity
    with db.read() as session:
        state = portfolio_state(session)
        assert_ledger(session, state)

        lots = session.scalars(select(TaxLot)).all()
        assert len(lots) == 3
        symbols = {lot.symbol for lot in lots}
        assert symbols == {"BANKASIA", "SQURPHARMA", "GP"}

        # Verify buckets are rotating/assigned valid BUCKETS
        for lot in lots:
            assert lot.bucket in ("A", "B", "C")
            assert lot.original_qty == lot.remaining_qty
            assert lot.remaining_cost_basis > Decimal("0")

        # Verify trades created
        trades = session.scalars(select(TradeLog)).all()
        assert len(trades) == 3
        for t in trades:
            assert t.side == "BUY"
            assert t.source == "STOCKNOW_SYNC"
            assert t.net_cash_change < Decimal("0")


def test_tier_preservation_and_rollback(test_db):
    """Verify active selling tier state is preserved on sync, and /rollback cleanly restores previous state."""
    db, settings = test_db

    # 1. Mutate BANKASIA lot to simulate sequential seller tier progression
    with db.write() as session:
        bank_lot = session.scalar(select(TaxLot).where(TaxLot.symbol == "BANKASIA"))
        bank_lot.next_tier = 2
        bank_lot.peak_price = Decimal("24.50")
        bank_lot.phase = "ACTIVE"
        bank_lot.recovery_anchor = Decimal("21.00")
        original_initial_cap = session.get(PortfolioState, 1).initial_capital
        original_lot_count = len(session.scalars(select(TaxLot)).all())

    # 2. Sync portfolio with BANKASIA and a new symbol
    sync_data = {
        "portfolio_id": "hb_tier_test",
        "portfolio_name": "Humming Bird",
        "cash_balance": Decimal("4000.00"),
        "holdings": [
            {"symbol": "BANKASIA", "quantity": 50, "avg_cost": Decimal("20.50"), "acquired_date": "2026-11-04"},
            {"symbol": "EXIM1STMF", "quantity": 100, "avg_cost": Decimal("5.50"), "acquired_date": "2026-11-03"},
        ],
    }
    reconcile_portfolio_to_db(db, settings, sync_data)

    # 3. Verify BANKASIA preserved its tier progression
    with db.read() as session:
        state = portfolio_state(session)
        assert_ledger(session, state)
        new_bank_lot = session.scalar(select(TaxLot).where(TaxLot.symbol == "BANKASIA"))
        assert new_bank_lot.next_tier == 2
        assert new_bank_lot.peak_price == Decimal("24.50")
        assert new_bank_lot.recovery_anchor == Decimal("21.00")

    # 4. Rollback last checkpoint
    with db.write() as session:
        state = session.get(PortfolioState, 1)
        rb_res = CheckpointManager.rollback_last(session, state)
        assert rb_res["action_reverted"] == "PORTFOLIO_SYNC"

    # 5. Verify restored previous state and ledger invariant
    with db.read() as session:
        state = portfolio_state(session)
        assert_ledger(session, state)
        restored_lots = session.scalars(select(TaxLot)).all()
        assert len(restored_lots) == original_lot_count
        assert state.initial_capital == original_initial_cap


def test_hermes_tool_sync_portfolio_bangla_and_english(test_db):
    """Verify natural language commands in Bangla & English dispatch and format portfolio sync."""
    db, settings = test_db
    skills_mgr = SkillsManager()

    # Intent detection
    tool_bn, args_bn = detect_intent_and_tool("Humming Bird portfolio sync koro", {})
    assert tool_bn == "control_stocknow_session"
    assert args_bn["action"] == "sync_portfolio"

    tool_en, args_en = detect_intent_and_tool("Sync Humming Bird portfolio", {})
    assert tool_en == "control_stocknow_session"
    assert args_en["action"] == "sync_portfolio"

    # Dispatch tool with injected portfolio
    injected = {
        "portfolio_id": "hb_hermes_test",
        "portfolio_name": "Humming Bird",
        "cash_balance": 4500.0,
        "holdings": [
            {"symbol": "BANKASIA", "quantity": 50, "avg_cost": 20.0},
            {"symbol": "GP", "quantity": 10, "avg_cost": 260.0},
        ],
    }
    with db.write() as session:
        state = session.get(PortfolioState, 1)
        dispatch_res = dispatch_tool(
            "control_stocknow_session",
            {"action": "sync_portfolio", "injected_portfolio": injected},
            session,
            state,
            settings,
            skills_mgr,
            CheckpointManager,
        )
        assert dispatch_res["status"] == "SUCCESS"
        assert dispatch_res["result"]["synced_holdings_count"] == 2

        formatted_bn = format_tool_response("control_stocknow_session", dispatch_res, "portfolio sync koro", {})
        assert "ভার্চুয়াল পোর্টফোলিও সফলভাবে সিঙ্ক" in formatted_bn
        assert "হোল্ডিংস: 2 টি" in formatted_bn

        formatted_en = format_tool_response("control_stocknow_session", dispatch_res, "sync portfolio", {})
        assert "synced successfully" in formatted_en
        assert "Holdings: 2" in formatted_en


def test_api_post_sync_portfolio(test_db):
    """Verify POST /api/stocknow/sync-portfolio updates status and returns snapshot."""
    db, settings = test_db
    app = create_app(settings)
    api_client = TestClient(app, base_url="http://localhost")

    payload = {
        "injected_portfolio": {
            "id": "hb_api_test",
            "name": "Humming Bird",
            "cash": 4800.0,
            "holdings": [
                {"symbol": "BANKASIA", "qty": 50, "rate": 20.0},
                {"symbol": "SQURPHARMA", "qty": 15, "rate": 210.0},
            ],
        }
    }

    resp = api_client.post("/api/stocknow/sync-portfolio", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"]["success"] is True
    assert data["result"]["synced_holdings_count"] == 2
    assert "snapshot" in data
    assert data["snapshot"]["app"]["name"] == "Humming Bird"

    # Verify client status updated
    status_resp = api_client.get("/api/stocknow/status")
    assert status_resp.status_code == 200
    st = status_resp.json()
    assert st["bound_portfolio_name"] == "Humming Bird"
    assert st["bound_portfolio_id"] == "hb_api_test"
    assert st["last_portfolio_sync_at"] is not None
