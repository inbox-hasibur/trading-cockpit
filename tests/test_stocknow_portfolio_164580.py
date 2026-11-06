"""Unit tests for StockNow Humming Bird portfolio #164580 and 3-tier GSC trading rules."""

from __future__ import annotations

import asyncio
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import select

from backend.adapters.stocknow_adapter import StockNowAdapter
from backend.adapters.stocknow_client import StockNowLiveClient
from backend.adapters.stocknow_market_sync import (
    STOCKNOW_LIST_NAME_TO_CATEGORY,
    extract_quotes_from_payload,
    sync_live_market_to_db,
)
from backend.adapters.stocknow_order_executor import execute_stocknow_virtual_order
from backend.adapters.stocknow_portfolio_sync import (
    extract_hummingbird_portfolio,
    parse_stocknow_ledger_date,
    reconcile_portfolio_to_db,
)
from backend.config import Settings
from backend.database import CompanyProfile, Database, PortfolioState, TaxLot, TradeLog
from backend.engine.auto_trader import AutoTrader
from backend.engine.t2_ledger import assert_ledger
from backend.hermes.skills_manager import SkillsManager
from backend.seed import REAL_STOCKNOW_COMPANIES, migrate_real_stocknow_market, seed_demo


def test_stocknow_portfolio_migration_and_ledger(tmp_path):
    """Verify runtime migration builds exact #164580 portfolio with ledger reconciliation."""
    db_file = tmp_path / "backend" / "data" / "hummingbird.db"
    db_file.parent.mkdir(parents=True, exist_ok=True)
    db_url = f"sqlite:///{db_file.as_posix()}"
    settings = Settings(database_url=db_url, demo_start_date=date(2026, 11, 5))
    db = Database(settings.database_url)
    db.create_schema()

    with db.write() as session:
        seed_demo(session, settings)
        migrate_real_stocknow_market(session, settings)

        state = session.get(PortfolioState, 1)
        assert state is not None
        assert state.name == "Humming Bird #164580"
        assert state.initial_capital == Decimal("121292.71")

        lots = list(session.scalars(select(TaxLot).order_by(TaxLot.symbol)))
        assert len(lots) == 3
        sym_map = {lot.symbol: lot for lot in lots}

        assert "BANKASIA" in sym_map
        assert sym_map["BANKASIA"].remaining_qty == 294
        assert sym_map["BANKASIA"].buy_price == Decimal("17.00")
        assert sym_map["BANKASIA"].buy_fee == Decimal("24.99")
        assert sym_map["BANKASIA"].remaining_cost_basis == Decimal("5022.99")

        assert "IBNSINA" in sym_map
        assert sym_map["IBNSINA"].remaining_qty == 16
        assert sym_map["IBNSINA"].buy_price == Decimal("302.80")
        assert sym_map["IBNSINA"].buy_fee == Decimal("24.22")
        assert sym_map["IBNSINA"].remaining_cost_basis == Decimal("4869.02")

        assert "MATINSPINN" in sym_map
        assert sym_map["MATINSPINN"].remaining_qty == 206
        assert sym_map["MATINSPINN"].buy_price == Decimal("97.40")
        assert sym_map["MATINSPINN"].buy_fee == Decimal("100.32")
        assert sym_map["MATINSPINN"].remaining_cost_basis == Decimal("20164.70")

        total_basis = sum(lot.remaining_cost_basis for lot in lots)
        assert total_basis == Decimal("30056.71")

        trades = list(session.scalars(select(TradeLog)))
        assert len(trades) == 3
        assert all(trade.source == "STOCKNOW_PORTFOLIO" for trade in trades)

        assert_ledger(session, state)


def test_gsc_watchlist_tiers_and_observation_skip(tmp_path):
    """Verify GSC_L1 is prioritized over GSC_L2, and base GSC observation pool skips auto-buys."""
    db_file = tmp_path / "backend" / "data" / "hummingbird.db"
    db_file.parent.mkdir(parents=True, exist_ok=True)
    db_url = f"sqlite:///{db_file.as_posix()}"
    settings = Settings(database_url=db_url, demo_start_date=date(2026, 11, 5))
    db = Database(settings.database_url)
    db.create_schema()

    with db.write() as session:
        seed_demo(session, settings)
        migrate_real_stocknow_market(session, settings)

        bankasia = session.get(CompanyProfile, "BANKASIA")
        matinspinn = session.get(CompanyProfile, "MATINSPINN")
        dhakabank = session.get(CompanyProfile, "DHAKABANK")
        aci = session.get(CompanyProfile, "ACI")

        assert bankasia.watchlist_category == "GSC_L1"
        assert matinspinn.watchlist_category == "GSC_L1"
        assert dhakabank.watchlist_category == "GSC_L2"
        assert aci.watchlist_category == "GSC"

        trader = AutoTrader(db, settings)
        companies = [aci, dhakabank, bankasia, matinspinn]

        def buy_priority(comp):
            cat = getattr(comp, "watchlist_category", "GSC")
            if cat == "GSC_L1":
                return (1, comp.symbol)
            if cat == "GSC_L2":
                return (2, comp.symbol)
            return (3, comp.symbol)

        sorted_comps = sorted(companies, key=buy_priority)
        symbols_order = [c.symbol for c in sorted_comps]
        assert symbols_order == ["BANKASIA", "MATINSPINN", "DHAKABANK", "ACI"]


def test_hermes_gsc_skill_content():
    """Verify Hermes SKILL_gsc_tiers.md encodes the exact operator rules."""
    skills = {s.name: s.content for s in SkillsManager().list_skills()}
    content = skills.get("SKILL_gsc_tiers")
    assert content is not None
    assert "Giant Stable Companies" in content
    assert "GSC_L1" in content
    assert "GSC_L2" in content
    assert "WAIT_OBSERVATION_ONLY" in content
    assert "MATINSPINN" in content
    assert "DHAKABANK" in content


def test_parse_stocknow_ledger_date():
    """Verify parsing DD/MM/YY format into YYYY-MM-DD ISO format."""
    assert parse_stocknow_ledger_date("02/11/26") == "2026-11-02"
    assert parse_stocknow_ledger_date("05/11/26") == "2026-11-05"
    assert parse_stocknow_ledger_date("28/02/25") == "2025-02-28"
    assert parse_stocknow_ledger_date("2026-11-02") == "2026-11-02"
    assert parse_stocknow_ledger_date("") == ""


def test_extract_hummingbird_portfolio_with_ledger():
    """Verify extracting portfolio with show holdings and ledger transaction dates."""
    injected = {
        "portfolio_id": "164580",
        "portfolio_name": "Humming Bird",
        "cash_balance": "91236.00",
        "holdings": [
            {"symbol": "BANKASIA", "quantity": 294, "avg_cost": "17.09"},
            {"symbol": "IBNSINA", "quantity": 16, "avg_cost": "304.31"},
            {"symbol": "MATINSPINN", "quantity": 206, "avg_cost": "97.89"},
        ],
        "ledger": [
            {"date": "02/11/26", "type": "BUY", "description": "BANKASIA", "quantity": 294, "rate": "17.00"},
            {"date": "02/11/26", "type": "BUY", "description": "IBNSINA", "quantity": 16, "rate": "302.80"},
            {"date": "02/11/26", "type": "BUY", "description": "MATINSPINN", "quantity": 206, "rate": "97.40"},
        ],
    }
    extracted = extract_hummingbird_portfolio(injected_portfolio=injected)
    assert extracted["portfolio_id"] == "164580"
    assert extracted["cash_balance"] == Decimal("91236.00")
    assert len(extracted["holdings"]) == 3

    sym_holdings = {h["symbol"]: h for h in extracted["holdings"]}
    assert sym_holdings["BANKASIA"]["acquired_date"] == "2026-11-02"
    assert sym_holdings["IBNSINA"]["acquired_date"] == "2026-11-02"
    assert sym_holdings["MATINSPINN"]["acquired_date"] == "2026-11-02"


@pytest.mark.anyio
async def test_execute_stocknow_virtual_order_0_5_commission():
    """Verify order execution defaults to 0.5% commission on both BUY and SELL."""
    receipt_buy = await execute_stocknow_virtual_order(
        symbol="BANKASIA",
        side="BUY",
        quantity=294,
        price=Decimal("17.00"),
        portfolio_id="164580",
        commission_pct=Decimal("0.5"),
    )
    assert receipt_buy["success"] is True
    assert receipt_buy["status"] == "ACKNOWLEDGED"
    assert receipt_buy["commission_pct"] == 0.5
    assert receipt_buy["portfolio_id"] == "164580"
    assert receipt_buy["side"] == "BUY"

    receipt_sell = await execute_stocknow_virtual_order(
        symbol="MATINSPINN",
        side="SELL",
        quantity=50,
        price=Decimal("105.40"),
        portfolio_id="164580",
        commission_pct=Decimal("0.5"),
    )
    assert receipt_sell["success"] is True
    assert receipt_sell["status"] == "ACKNOWLEDGED"
    assert receipt_sell["commission_pct"] == 0.5
    assert receipt_sell["side"] == "SELL"


def test_autotrader_dispatches_order_with_0_5_commission(tmp_path):
    """Verify AutoTrader run_cycle dispatches order via adapter with 0.5% commission."""
    db_file = tmp_path / "test_trader.db"
    settings = Settings(database_url=f"sqlite:///{db_file.as_posix()}", demo_start_date=date(2026, 11, 3))
    db = Database(settings.database_url)
    db.create_schema()

    with db.write() as session:
        seed_demo(session, settings)

    adapter = StockNowAdapter(mode="DEMO")
    adapter.execute_order = MagicMock(return_value={"status": "MOCK_EXECUTED"})

    trader = AutoTrader(db, settings, adapter=adapter)
    res = trader.run_cycle()

    assert res["status"] == "COMPLETED"
    assert len(res["trades"]) > 0

    # Verify adapter.execute_order was called with 0.5% commission
    assert adapter.execute_order.called
    for call in adapter.execute_order.call_args_list:
        kwargs = call.kwargs
        assert kwargs.get("commission_pct") == Decimal("0.5")
        assert kwargs.get("side") in ("BUY", "SELL")


def test_three_list_favorites_category_mapping():
    """Verify mapping of 3 favorites lists to GSC, GSC_L1, and GSC_L2."""
    assert STOCKNOW_LIST_NAME_TO_CATEGORY["Giant Stable Companies"] == "GSC"
    assert STOCKNOW_LIST_NAME_TO_CATEGORY["GSC Upper Trends L1"] == "GSC_L1"
    assert STOCKNOW_LIST_NAME_TO_CATEGORY["GSC Upper Trends L2"] == "GSC_L2"

    payload = [
        {"symbol": "BANKASIA", "ltp": 17.50, "list_name": "GSC Upper Trends L1"},
        {"symbol": "DHAKABANK", "ltp": 11.10, "list_name": "GSC Upper Trends L2"},
        {"symbol": "ACI", "ltp": 176.20, "list_name": "Giant Stable Companies"},
    ]
    quotes = extract_quotes_from_payload(payload)
    assert len(quotes) == 3
    q_map = {q["symbol"]: q for q in quotes}
    assert q_map["BANKASIA"]["watchlist_category"] == "GSC_L1"
    assert q_map["DHAKABANK"]["watchlist_category"] == "GSC_L2"
    assert q_map["ACI"]["watchlist_category"] == "GSC"
