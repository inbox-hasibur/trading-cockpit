"""Comprehensive unit tests for Hermes OS Step 2:

Closed Learning Loop (Auto-Skill Generation) & Custom DSE Trading Toolsets.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import select

from backend.config import Settings
from backend.database import Base, CompanyProfile, CustomRule, Database, PortfolioState, TaxLot
from backend.engine.money import decimal, price
from backend.hermes_os.agent_loop import HermesOSAgentLoop
from backend.hermes_os.memory_curator import MemoryCurator
from backend.hermes_os.skill_learner import SkillLearner, bump_version
from backend.hermes_os.toolsets import (
    HermesToolRegistry,
    ToolContext,
    default_registry,
)


@pytest.fixture
def test_env(tmp_path: Path):
    """Sets up an isolated database with reconciled seed ledger, Hermes OS state directory, and ToolContext."""
    hermes_home = tmp_path / "hermes_home"
    db_file = tmp_path / "test_hermes_os2.db"
    today = date(2026, 11, 4)

    settings = Settings(
        database_url=f"sqlite:///{db_file.as_posix()}",
        demo_start_date=today,
    )
    db = Database(settings.database_url)
    Base.metadata.create_all(db.engine)

    from backend.seed import seed_demo
    with db.write() as session:
        seed_demo(session, settings)

    curator = MemoryCurator(hermes_dir=hermes_home)
    learner = SkillLearner(skills_dir=hermes_home / "skills", state_dir=hermes_home)

    return {
        "db": db,
        "settings": settings,
        "hermes_home": hermes_home,
        "curator": curator,
        "learner": learner,
    }


def test_bump_version():
    """Verifies semantic minor version incrementing."""
    assert bump_version("1.0.0") == "1.1.0"
    assert bump_version("1.1.0") == "1.2.0"
    assert bump_version("2.5") == "2.6.0"


def test_closed_learning_loop_compilation_and_evolution(test_env):
    """Verifies closed learning loop generates SKILL_<name>.md and evolves upon retry discovery."""
    learner: SkillLearner = test_env["learner"]

    # 1. Initial creation from execution log
    skill1 = learner.learn_from_execution(
        task_name="StockNow Select Quirk",
        task_description="Handling Ionic custom dropdown select elements on stocknow.com.bd",
        execution_log=[
            "Timeout: click on ion-select failed to open alert popover",
            "Retry: clicked inner button.select-native element directly",
            "Success: overlay opened and GSC_L1 category option selected",
        ],
        outcome="Successfully selected category GSC_L1 and triggered market sync",
    )
    assert skill1.version == "1.0.0"
    assert len(skill1.pitfalls) >= 1
    assert any("ion-select failed" in p for p in skill1.pitfalls)
    assert len(skill1.steps) >= 1
    assert skill1.file_path.exists()

    # 2. Re-learning with newly discovered pitfalls increments minor version (1.0.0 -> 1.1.0)
    skill2 = learner.learn_from_execution(
        task_name="StockNow Select Quirk",
        task_description="Handling Ionic custom dropdown select elements on stocknow.com.bd",
        execution_log=[
            "Quirk: shadow DOM button requires dispatchEvent('ionChange')",
            "Success: dispatched synthetic ionChange event and form updated",
        ],
        outcome="Form updated seamlessly with ionChange dispatch",
    )
    assert skill2.version == "1.1.0"
    assert len(skill2.pitfalls) >= 2
    assert any("ionChange" in p for p in skill2.pitfalls)
    # File content on disk contains updated YAML frontmatter
    saved_text = skill2.file_path.read_text(encoding="utf-8")
    assert "version: 1.1.0" in saved_text
    assert "pitfalls:" in saved_text


def test_inspect_curve_and_support(test_env):
    """Verifies quantitative inspection of multi-session drawdown, support floor, and comparison."""
    db: Database = test_env["db"]
    with db.write() as session:
        state = session.get(PortfolioState, 1)
        ctx = ToolContext(
            session=session,
            state=state,
            settings=test_env["settings"],
            curator=test_env["curator"],
            learner=test_env["learner"],
        )
        res = default_registry.execute("inspect_curve_and_support", {"symbol": "BANKASIA"}, ctx)

        assert res["status"] == "SUCCESS"
        assert res["symbol"] == "BANKASIA"
        assert res["support_floor"] == 17.00
        assert res["resistance_ceiling"] == 18.50
        # Price is 17.50, support is 17.00 -> price > support
        assert "above support" in res["support_status"]
        assert "drop over 7 sessions" in res["drawdown_description"]


def test_canary_90_10_quarantine_and_restore(test_env):
    """Verifies emergency quarantine, 90% profit lock + 10% canary probe, and rollback."""
    db: Database = test_env["db"]
    with db.write() as session:
        state = session.get(PortfolioState, 1)
        ctx = ToolContext(
            session=session,
            state=state,
            settings=test_env["settings"],
            curator=test_env["curator"],
            learner=test_env["learner"],
        )

        # 1. Trigger Canary 90/10 Quarantine
        q_res = default_registry.execute(
            "trigger_canary_90_10_quarantine",
            {"symbol": "SQURPHARMA", "thesis": "Insolvency risk and massive factory shutdown"},
            ctx,
        )
        assert q_res["status"] == "SUCCESS"
        comp = session.get(CompanyProfile, "SQURPHARMA")
        assert comp.quarantined is True
        assert "Insolvency risk" in comp.quarantine_reason

        # 2. Check 10% canary probe retained and CanaryThesis record created
        assert q_res["result"]["canary_qty"] == 2
        assert q_res["result"]["sold_qty"] == 18
        from backend.database import CanaryThesis
        thesis_rec = session.scalar(select(CanaryThesis).where(CanaryThesis.symbol == "SQURPHARMA"))
        assert thesis_rec is not None
        assert "Insolvency risk" in thesis_rec.thesis

        # 3. Restore from quarantine
        rest_res = default_registry.execute(
            "restore_quarantine",
            {"symbol": "SQURPHARMA", "reason": "Investigation cleared the factory issue"},
            ctx,
        )
        assert rest_res["status"] == "SUCCESS"
        assert comp.quarantined is False


def test_set_watchlist_tier_and_update_allocation(test_env):
    """Verifies changing watchlist tiers and buy allocation caps with rollback checkpoints."""
    db: Database = test_env["db"]
    with db.write() as session:
        state = session.get(PortfolioState, 1)
        ctx = ToolContext(
            session=session,
            state=state,
            settings=test_env["settings"],
            curator=test_env["curator"],
            learner=test_env["learner"],
        )

        # Set tier to GSC_L2
        t_res = default_registry.execute(
            "set_watchlist_tier",
            {"symbol": "BANKASIA", "tier": "GSC_L2"},
            ctx,
        )
        assert t_res["status"] == "SUCCESS"
        comp = session.get(CompanyProfile, "BANKASIA")
        assert comp.watchlist_category == "GSC_L2"

        # Update buy allocation to 25%
        a_res = default_registry.execute(
            "update_buy_allocation",
            {"symbol": "BANKASIA", "buy_allocation_pct": 25.0},
            ctx,
        )
        assert a_res["status"] == "SUCCESS"
        rule = session.get(CustomRule, "BANKASIA")
        assert rule.buy_allocation_pct == Decimal("25.00")

        # Rollback the allocation change
        rb_res = default_registry.execute("rollback_checkpoint", {"steps_back": 1}, ctx)
        assert rb_res["status"] == "SUCCESS"
        assert rule.buy_allocation_pct == Decimal("10.00")


def test_memory_and_skill_toolset(test_env):
    """Verifies curate_memory_md, curate_user_md, session_search_fts5, and create_or_patch_skill."""
    db: Database = test_env["db"]
    with db.write() as session:
        state = session.get(PortfolioState, 1)
        ctx = ToolContext(
            session=session,
            state=state,
            settings=test_env["settings"],
            curator=test_env["curator"],
            learner=test_env["learner"],
        )

        # 1. Curate MEMORY.md
        m_res = default_registry.execute(
            "curate_memory_md",
            {"note": "BANKASIA support floor tested at ৳17.20 on high turnover"},
            ctx,
        )
        assert m_res["memory_updated"] is True
        mem_text = test_env["curator"].read_memory_md()
        assert "BANKASIA support floor tested" in mem_text

        # 2. Curate USER.md
        u_res = default_registry.execute(
            "curate_user_md",
            {"directive": "Hasibur prioritizes GSC_L1 comeback stocks over high beta speculative issues"},
            ctx,
        )
        assert u_res["user_updated"] is True
        user_text = test_env["curator"].read_user_md()
        assert "GSC_L1 comeback stocks" in user_text

        # 3. FTS5 Search
        test_env["curator"].index_message("c1", "user", "Hasibur asks for BANKASIA curve analysis", symbol="BANKASIA")
        fts_res = default_registry.execute(
            "session_search_fts5",
            {"query": "BANKASIA curve"},
            ctx,
        )
        assert fts_res["hits_count"] >= 1
        assert "BANKASIA" in fts_res["hits"][0]["content"]

        # 4. Create skill via tool
        s_res = default_registry.execute(
            "create_or_patch_skill",
            {
                "name": "Breakout Swing Scalp",
                "description": "Gradual profit-taking rules across multiple resistance tiers",
                "triggers": ["profit-taking", "no-regret", "tiers"],
                "content": "Take 25% profit at Tier 1 (+7%), 50% at Tier 2 (+14%).",
                "pitfalls": ["Do not sell 100% at once", "Do not ignore T+2 settlement cycle"],
                "steps": ["Monitor tier target", "Execute 25% partial sell", "Retain remainder"],
            },
            ctx,
        )
        assert s_res["status"] == "SUCCESS"
        assert s_res["version"] == "1.0.0"


def test_hermes_os_agent_loop_executes_tool(test_env):
    """Verifies HermesOSAgentLoop can dispatch structured tools via execute_tool."""
    db: Database = test_env["db"]
    loop = HermesOSAgentLoop(hermes_dir=test_env["hermes_home"])

    with db.write() as session:
        state = session.get(PortfolioState, 1)
        ctx = ToolContext(
            session=session,
            state=state,
            settings=test_env["settings"],
            curator=loop.curator,
            learner=loop.learner,
        )

        res = loop.execute_tool(
            "inspect_curve_and_support",
            {"symbol": "SQURPHARMA"},
            ctx,
        )
        assert res["status"] == "SUCCESS"
        assert res["symbol"] == "SQURPHARMA"
        assert res["support_floor"] == 202.00


def test_stocknow_browser_toolset_execution(test_env):
    """Verifies stocknow_browser_toolset (sync_favorites_3_lists, sync_portfolio_164580, execute_live_order)."""
    db: Database = test_env["db"]
    with db.write() as session:
        state = session.get(PortfolioState, 1)
        ctx = ToolContext(
            session=session,
            state=state,
            settings=test_env["settings"],
            curator=test_env["curator"],
            learner=test_env["learner"],
        )

        # 1. sync_favorites_3_lists with mock payload
        mock_payload = {
            "quotes": [
                {"symbol": "BANKASIA", "ltp": "17.60", "ycp": "17.50", "category": "GSC_L1"},
                {"symbol": "SQURPHARMA", "ltp": "215.00", "ycp": "214.00", "category": "GSC"},
            ]
        }
        fav_res = default_registry.execute("sync_favorites_3_lists", {"payload": mock_payload}, ctx)
        assert fav_res["status"] == "SUCCESS"
        assert fav_res["quotes_count"] >= 2

        # 2. sync_portfolio_164580 with injected portfolio
        injected = {
            "portfolio_id": "164580",
            "name": "Humming Bird",
            "cash": 107596.0,
            "holdings": [
                {"symbol": "BANKASIA", "quantity": 138, "avg_cost": 17.09},
                {"symbol": "IBNSINA", "quantity": 16, "avg_cost": 304.31},
            ],
        }
        port_res = default_registry.execute("sync_portfolio_164580", {"injected_portfolio": injected}, ctx)
        assert port_res["status"] == "SUCCESS"
        assert port_res["result"]["cash_balance"] == Decimal("107596.00")

        # 3. execute_live_order (BUY)
        buy_res = default_registry.execute(
            "execute_live_order",
            {"symbol": "BANKASIA", "side": "BUY", "quantity": 10},
            ctx,
        )
        assert buy_res["status"] == "SUCCESS"
        assert buy_res["result"]["quantity"] == 10
        assert buy_res["result"]["cost"] > 0
        from backend.database import TradeLog
        trade = session.scalar(select(TradeLog).where(TradeLog.symbol == "BANKASIA", TradeLog.side == "BUY").order_by(TradeLog.id.desc()))
        assert trade is not None
        assert trade.fee > 0  # 0.5% brokerage commission
