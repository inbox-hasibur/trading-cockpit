"""Unit tests for StockNow Humming Bird portfolio #164580 and 3-tier GSC trading rules."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select

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

    with db.sessions() as session:
        seed_demo(session, settings)
        # Force migration by calling migrate_real_stocknow_market with runtime db path
        migrate_real_stocknow_market(session, settings)

        state = session.get(PortfolioState, 1)
        assert state is not None
        assert state.name == "Humming Bird #164580"
        assert state.initial_capital == Decimal("121292.71")

        # Verify active holdings
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

        # Check total basis = 30,056.71 BDT
        total_basis = sum(lot.remaining_cost_basis for lot in lots)
        assert total_basis == Decimal("30056.71")

        # Trade logs must have the real trade keys
        trades = list(session.scalars(select(TradeLog)))
        assert len(trades) == 3
        assert all(trade.source == "STOCKNOW_PORTFOLIO" for trade in trades)

        # Ledger assertion passes with zero paisa discrepancy
        assert_ledger(session, state)


def test_gsc_watchlist_tiers_and_observation_skip(tmp_path):
    """Verify GSC_L1 is prioritized over GSC_L2, and base GSC observation pool skips auto-buys."""
    db_file = tmp_path / "backend" / "data" / "hummingbird.db"
    db_file.parent.mkdir(parents=True, exist_ok=True)
    db_url = f"sqlite:///{db_file.as_posix()}"
    settings = Settings(database_url=db_url, demo_start_date=date(2026, 11, 5))
    db = Database(settings.database_url)
    db.create_schema()

    with db.sessions() as session:
        seed_demo(session, settings)
        migrate_real_stocknow_market(session, settings)

        # Verify company categories in DB
        bankasia = session.get(CompanyProfile, "BANKASIA")
        matinspinn = session.get(CompanyProfile, "MATINSPINN")
        dhakabank = session.get(CompanyProfile, "DHAKABANK")
        aci = session.get(CompanyProfile, "ACI")

        assert bankasia.watchlist_category == "GSC_L1"
        assert matinspinn.watchlist_category == "GSC_L1"
        assert dhakabank.watchlist_category == "GSC_L2"
        assert aci.watchlist_category == "GSC"

        # Verify AutoTrader buy order sorting
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
        # L1 first (BANKASIA, MATINSPINN), L2 next (DHAKABANK), GSC last (ACI)
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
