"""Unit tests for Sprint 2 Step 2.2: Live DSE Quote & 7-30 Day Curve Sync Engine."""

from __future__ import annotations

import asyncio
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.adapters.stocknow_adapter import StockNowAdapter
from backend.adapters.stocknow_client import StockNowLiveClient
from backend.adapters.stocknow_market_sync import (
    extract_quotes_from_payload,
    extract_quotes_from_stocknow,
    sync_live_market_to_db,
)
from backend.config import Settings
from backend.database import CompanyProfile, Database, portfolio_state
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
    db_file = tmp_path / "test_stocknow_sync.db"
    db_url = f"sqlite:///{db_file.as_posix()}"
    settings = Settings(database_url=db_url)
    db = Database(db_url)
    db.create_schema()
    with db.write() as session:
        seed_demo(session, settings)
    return db, settings


def test_extract_quotes_from_payload():
    """Verify robust extraction and normalization of quotes and 7-30 day curves."""
    raw_payload = {
        "instruments": [
            {
                "symbol": "BANKASIA",
                "ltp": "19.80",
                "ycp": "19.50",
                "change_pct": "1.54%",
                "history": [
                    {"date": "2026-11-01", "close": "19.30"},
                    {"date": "2026-11-02", "close": "19.50"},
                    {"date": "2026-11-03", "close": "19.80"},
                ],
            },
            {
                "trading_code": "gp",
                "close": 268.50,
                "prev_close": 265.00,
            },
            # Invalid item (missing symbol or negative price)
            {"symbol": "INVALID", "ltp": "-5.00"},
            {"symbol": "", "ltp": "100.00"},
        ]
    }

    quotes = extract_quotes_from_payload(raw_payload)
    assert len(quotes) == 2

    q1 = next(q for q in quotes if q["symbol"] == "BANKASIA")
    assert q1["last_price"] == Decimal("19.80")
    assert q1["ycp"] == Decimal("19.50")
    assert q1["change_pct"] == Decimal("1.54")
    assert len(q1["history"]) == 3
    assert q1["source"] == "STOCKNOW_LIVE"

    q2 = next(q for q in quotes if q["symbol"] == "GP")
    assert q2["last_price"] == Decimal("268.50")
    assert q2["ycp"] == Decimal("265.00")
    assert q2["source"] == "STOCKNOW_LIVE"


def test_sync_live_market_to_db(test_db):
    """Verify sync_live_market_to_db updates SQLite CompanyProfile rows and reconciles history."""
    db, settings = test_db

    quotes = [
        {
            "symbol": "BANKASIA",
            "last_price": Decimal("20.50"),
            "as_of_date": date(2026, 11, 5),
            "history": [
                {"date": "2026-11-03", "close": "19.50"},
                {"date": "2026-11-04", "close": "19.80"},
                {"date": "2026-11-05", "close": "20.50"},
            ],
            "source": "STOCKNOW_LIVE",
        }
    ]

    res = sync_live_market_to_db(db, quotes, session_date=date(2026, 11, 5))
    assert res["success"] is True
    assert res["synced_count"] == 1
    assert "BANKASIA" in res["symbols"]

    # Verify CompanyProfile row
    with db.read() as session:
        comp = session.get(CompanyProfile, "BANKASIA")
        assert comp is not None
        assert comp.last_price == Decimal("20.50")
        assert comp.source == "STOCKNOW_LIVE"
        assert comp.quote_on == date(2026, 11, 5)
        assert len(comp.price_history) >= 3
        assert comp.price_history[-1]["close"] == "20.50"

        # Check other symbols were safely untouched
        gp = session.get(CompanyProfile, "GP")
        assert gp is not None
        assert gp.source == "DEMO_SEED"

    # Verify StockNowAdapter accepts STOCKNOW_LIVE quote
    adapter = StockNowAdapter()
    with db.read() as session:
        comp = session.get(CompanyProfile, "BANKASIA")
        quote = adapter.quote(comp, comp.quote_on)
        assert quote.source == "STOCKNOW_LIVE"
        fill_price = adapter.paper_fill(quote, 10)
        assert fill_price == Decimal("20.50")


def test_api_stocknow_sync_market(test_db):
    """Verify POST /api/stocknow/sync-market endpoint with injected quote payload."""
    db, settings = test_db
    app = create_app(settings)

    with TestClient(app, base_url="http://localhost") as client:
        payload = {
            "payload": [
                {
                    "symbol": "SQURPHARMA",
                    "ltp": "218.00",
                    "history": [
                        {"date": "2026-11-04", "close": "216.00"},
                        {"date": "2026-11-05", "close": "218.00"},
                    ],
                }
            ]
        }
        res = client.post("/api/stocknow/sync-market", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["result"]["success"] is True
        assert data["result"]["synced_count"] == 1
        assert "SQURPHARMA" in data["result"]["symbols"]
        assert "snapshot" in data

    with db.read() as session:
        comp = session.get(CompanyProfile, "SQURPHARMA")
        assert comp.last_price == Decimal("218.00")
        assert comp.source == "STOCKNOW_LIVE"


def test_hermes_tool_control_stocknow_session(test_db):
    """Verify Hermes intent detection and dispatch for StockNow live commands."""
    db, settings = test_db

    # Intent detection
    cmd1, args1 = detect_intent_and_tool("Launch StockNow browser", {})
    assert cmd1 == "control_stocknow_session"
    assert args1["action"] == "launch"

    cmd2, args2 = detect_intent_and_tool("StockNow login check koro", {})
    assert cmd2 == "control_stocknow_session"
    assert args2["action"] == "check_auth"

    cmd3, args3 = detect_intent_and_tool("Sync live market prices", {})
    assert cmd3 == "control_stocknow_session"
    assert args3["action"] == "sync_market"

    # Tool dispatch with injected sync payload
    skills_mgr = SkillsManager()
    with db.write() as session:
        state = portfolio_state(session)
        dispatch_res = dispatch_tool(
            "control_stocknow_session",
            {
                "action": "sync_market",
                "payload": [{"symbol": "EXIM1STMF", "ltp": "5.40"}],
            },
            session,
            state,
            settings,
            skills_mgr,
            CheckpointManager,
        )
        assert dispatch_res["status"] == "SUCCESS"
        assert dispatch_res["action"] == "sync_market"
        assert dispatch_res["result"]["synced_count"] == 1

        # Formatter output
        formatted_en = format_tool_response("control_stocknow_session", dispatch_res, "Sync live market prices", {})
        assert "Synchronized 1 live DSE quotes" in formatted_en
        assert "EXIM1STMF" in formatted_en

        formatted_bn = format_tool_response("control_stocknow_session", dispatch_res, "live price sync koro", {})
        assert "সিঙ্ক করা হয়েছে" in formatted_bn
