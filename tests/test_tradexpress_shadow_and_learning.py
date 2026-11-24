"""Comprehensive Test Suite for Sprint 5A: TradeXpress Passive Feed, Shadow Simulator & Self-Learning."""

from __future__ import annotations

import time
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.adapters.base import MarketQuote, PortfolioHolding, from_tradexpress_symbol, to_tradexpress_symbol
from backend.adapters.tradexpress.passive_feed import (
    AccountSummary,
    TradeXpressPassiveFeed,
    get_feed_health_and_guidance,
    ingest_passive_snapshot,
    parse_account_summary_dict,
    parse_ember_market_watch_rows,
    parse_ember_portfolio_rows,
)
from backend.adapters.tradexpress.shadow_simulator import TradeXpressShadowSimulator
from backend.config import Settings
from backend.database import (
    CompanyProfile,
    CustomRule,
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
from backend.engine.t2_ledger import assert_ledger
from backend.main import create_app
from backend.seed import seed_demo


@pytest.fixture
def test_db_and_settings(tmp_path):
    """Provides an isolated test database with seeded demo state."""
    db_file = tmp_path / "test_sprint5a.db"
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


def test_ember_quote_and_portfolio_parsers():
    """Validates parsing of Ember.js dataObj rows and symbol normalization."""
    raw_mw = [
        {
            "dataObj": {
                "sDes": "BANKASIA`PB",
                "ltp": 18.40,
                "chg": 0.50,
                "pctChg": 2.79,
                "vol": 500000,
                "open": 18.00,
                "high": 18.50,
                "low": 17.90,
                "bbp": 18.30,
                "bbq": 15000,
                "bap": 18.40,
                "baq": 20000,
                "minLimit": 16.50,
                "maxLimit": 20.00,
                "dispSettType": "PUBLIC",
                "dispSymCat": "A",
                "dltt": "13:33:36",
                "wk52": False,
                "jumpUp": False,
            }
        },
        {
            "dataObj": {
                "sDes": "ASIATICLAB'PB",
                "ltp": 35.50,
                "dispSettType": "SPOT",
                "dispSymCat": "A",
            }
        },
        {
            "dataObj": {
                "sDes": "OFFHOURS`PB",
                "ltp": 10.00,
                "dispSettType": "N/A",
                "dispSymCat": "N/A",
            }
        },
    ]

    existing_profiles = {
        "OFFHOURS": {"settlement_type": "PUBLIC", "symbol_category": "B"}
    }
    quotes = parse_ember_market_watch_rows(raw_mw, existing_profiles=existing_profiles)
    assert len(quotes) == 3

    q1 = quotes[0]
    assert q1.symbol == "BANKASIA"
    assert q1.ltp == Decimal("18.4")
    assert q1.bid == Decimal("18.3")
    assert q1.offer == Decimal("18.4")
    assert q1.settlement_type == "PUBLIC"
    assert q1.symbol_category == "A"
    assert q1.last_trade_time == "13:33:36"

    q2 = quotes[1]
    assert q2.symbol == "ASIATICLAB"
    assert q2.settlement_type == "SPOT"

    q3 = quotes[2]
    assert q3.symbol == "OFFHOURS"
    # Preserves cached fallback when off-hours sends N/A
    assert q3.settlement_type == "PUBLIC"
    assert q3.symbol_category == "B"

    # Test portfolio rows parsing
    raw_pf = [
        {
            "dataObj": {
                "symbolInfo": {"dSym": "BANKASIA`PB"},
                "profLossQty": 100,
                "avaiQtyDSE": 100,
                "penHolding": 0,
                "pendBuy": 0,
                "pendSell": 0,
                "avgCst": 17.97,
                "mktPrice": 18.40,
            }
        }
    ]
    holdings = parse_ember_portfolio_rows(raw_pf)
    assert len(holdings) == 1
    h = holdings[0]
    assert h.symbol == "BANKASIA"
    assert h.total_qty == 100
    assert h.available_dse_qty == 100
    assert h.avg_cost == Decimal("17.97")


def test_feed_health_and_operator_guidance():
    """Validates operator guidance generation for missing/stale tabs vs fresh tabs."""
    now = 1000.0
    stale_tabs = {
        "market_watch": now - 200.0,  # Stale (> 120s)
        "gsc": now - 30.0,            # Fresh
    }
    health = get_feed_health_and_guidance(stale_tabs, cdp_connected=False, now_utc=now)
    assert not health["cdp_connected"]
    assert not health["is_healthy"]
    instructions = health["operator_instructions"]
    assert any("CDP connection offline" in i for i in instructions)
    assert any("Click 'Market Watch'" in i for i in instructions)
    assert any("Click 'L1' tab" in i for i in instructions)
    assert any("Click 'Portfolio' tab" in i for i in instructions)
    assert any("Click 'Account Summary' sub-tab" in i for i in instructions)

    # Fresh state
    fresh_tabs = {
        "market_watch": now - 10.0,
        "gsc": now - 20.0,
        "l1": now - 15.0,
        "portfolio": now - 30.0,
        "account_summary": now - 40.0,
    }
    healthy_guidance = get_feed_health_and_guidance(fresh_tabs, cdp_connected=True, now_utc=now)
    assert healthy_guidance["cdp_connected"]
    assert healthy_guidance["is_healthy"]
    assert "All TradeXpress passive data feeds are fresh and active." in healthy_guidance["operator_instructions"][0]


def test_shadow_simulator_limit_buy_and_queue(test_db_and_settings):
    """Validates realistic immediate fill vs resting queued limit buy in ShadowSimulator."""
    db, settings = test_db_and_settings
    feed = TradeXpressPassiveFeed(db)
    simulator = TradeXpressShadowSimulator(db, settings, feed=feed)

    # Ingest quote where Offer = 18.40, qty = 500
    quote = MarketQuote(
        symbol="BANKASIA",
        ltp=Decimal("18.40"),
        change=Decimal("0.50"),
        pct_change=Decimal("2.79"),
        volume=100000,
        open_price=Decimal("18.00"),
        high=Decimal("18.50"),
        low=Decimal("17.90"),
        bid=Decimal("18.30"),
        bid_qty=1000,
        offer=Decimal("18.40"),
        offer_qty=500,
        min_limit=Decimal("16.50"),
        max_limit=Decimal("20.00"),
        settlement_type="PUBLIC",
        symbol_category="A",
        hit_52w_high=False,
        hit_upper_circuit=False,
        last_trade_time="13:30:00",
    )
    feed.update_quotes([quote])

    # 1. Immediate fill: Limit 18.50 >= Offer 18.40 for 100 shares
    fill_res = simulator.submit_shadow_order(
        symbol="BANKASIA",
        side="BUY",
        quantity=100,
        limit_price=Decimal("18.50"),
        confirm=True,
        portfolio_id="H9210_SHADOW",
    )
    assert fill_res["status"] == "FILLED"
    assert fill_res["avg_fill_price"] == 18.40  # Filled at best offer
    assert fill_res["quantity"] == 100

    with db.read() as session:
        state = portfolio_state(session)
        assert_ledger(session, state, portfolio_id="H9210_SHADOW")
        lots = list(session.scalars(select(TaxLot).where(TaxLot.symbol == "BANKASIA", TaxLot.portfolio_id == "H9210_SHADOW")))
        assert len(lots) >= 1
        assert any(l.remaining_qty == 100 and l.buy_price == Decimal("18.40") for l in lots)

    # 2. Resting Queued order: Limit 18.20 < Offer 18.40
    queued_res = simulator.submit_shadow_order(
        symbol="BANKASIA",
        side="BUY",
        quantity=50,
        limit_price=Decimal("18.20"),
        confirm=True,
        portfolio_id="H9210_SHADOW",
    )
    assert queued_res["status"] == "QUEUED"
    order_ref = queued_res["order_ref"]

    # Verify order is resting in shadow_orders table
    with db.read() as session:
        order = session.scalar(select(ShadowOrder).where(ShadowOrder.order_ref == order_ref))
        assert order is not None
        assert order.status == "QUEUED"
        assert order.pending_qty == 50

    # 3. Market depth updates: Offer drops to 18.20 -> Reconcile queue fills order
    quote_updated = MarketQuote(
        symbol="BANKASIA",
        ltp=Decimal("18.20"),
        change=Decimal("0.30"),
        pct_change=Decimal("1.67"),
        volume=120000,
        open_price=Decimal("18.00"),
        high=Decimal("18.50"),
        low=Decimal("17.90"),
        bid=Decimal("18.10"),
        bid_qty=1000,
        offer=Decimal("18.20"),
        offer_qty=500,
        min_limit=Decimal("16.50"),
        max_limit=Decimal("20.00"),
        settlement_type="PUBLIC",
        symbol_category="A",
    )
    feed.update_quotes([quote_updated])

    with db.write() as session:
        reconciled = simulator.reconcile_queued_orders(session, feed.get_all_quotes(), session_phase="CONTINUOUS")
        assert len(reconciled) == 1
        assert reconciled[0]["status"] == "FILLED"
        assert reconciled[0]["avg_fill_price"] == 18.20

    # 4. Session close: remaining queued orders expire
    simulator.submit_shadow_order(
        symbol="BANKASIA",
        side="BUY",
        quantity=20,
        limit_price=Decimal("17.00"),
        confirm=True,
        portfolio_id="H9210_SHADOW",
    )
    with db.write() as session:
        expired = simulator.reconcile_queued_orders(session, feed.get_all_quotes(), session_phase="CLOSED")
        assert len(expired) >= 1
        assert expired[0]["status"] == "EXPIRED"


def test_shadow_simulator_sell_strict_no_loss_and_unsettled_sales(test_db_and_settings):
    """Validates strict no-loss hold, realistic fees, and immediate Unsettled Sales credit on sell fill."""
    db, settings = test_db_and_settings
    feed = TradeXpressPassiveFeed(db)
    simulator = TradeXpressShadowSimulator(db, settings, feed=feed)

    # Ingest initial quote @ 17.50
    init_quote = MarketQuote(
        symbol="BANKASIA",
        ltp=Decimal("17.50"),
        change=Decimal("0"),
        pct_change=Decimal("0"),
        volume=50000,
        open_price=Decimal("17.50"),
        high=Decimal("17.50"),
        low=Decimal("17.50"),
        bid=Decimal("17.40"),
        bid_qty=1000,
        offer=Decimal("17.50"),
        offer_qty=500,
        min_limit=Decimal("16.00"),
        max_limit=Decimal("20.00"),
        settlement_type="PUBLIC",
        symbol_category="A",
    )
    feed.update_quotes([init_quote])

    # Buy 100 shares via simulator so TaxLot and TradeLog are created in the ledger
    buy_res = simulator.submit_shadow_order(
        symbol="BANKASIA",
        side="BUY",
        quantity=100,
        limit_price=Decimal("17.50"),
        confirm=True,
        portfolio_id="H9210_SHADOW",
    )
    assert buy_res["status"] == "FILLED"

    # Make lot mature for T+2 test
    with db.write() as session:
        state = portfolio_state(session)
        lot = session.scalar(
            select(TaxLot).where(
                TaxLot.symbol == "BANKASIA",
                TaxLot.portfolio_id == "H9210_SHADOW",
            ).order_by(TaxLot.id.desc())
        )
        lot.matures_on = state.clock_date
        session.flush()

    # 1. Attempt sell at 17.00 (loss after fee) -> Rejected by Strict No-Loss Guard
    loss_res = simulator.submit_shadow_order(
        symbol="BANKASIA",
        side="SELL",
        quantity=50,
        limit_price=Decimal("17.00"),
        confirm=True,
        portfolio_id="H9210_SHADOW",
    )
    assert loss_res["status"] == "REJECTED"
    assert any("Strict No-Loss Guard" in err for err in loss_res["errors"])

    # 2. Ingest Bid = 18.50 -> Profitable sell execution
    quote = MarketQuote(
        symbol="BANKASIA",
        ltp=Decimal("18.50"),
        change=Decimal("0.60"),
        pct_change=Decimal("3.35"),
        volume=200000,
        open_price=Decimal("18.00"),
        high=Decimal("18.50"),
        low=Decimal("17.90"),
        bid=Decimal("18.50"),
        bid_qty=500,
        offer=Decimal("18.60"),
        offer_qty=500,
        min_limit=Decimal("16.50"),
        max_limit=Decimal("20.00"),
        settlement_type="PUBLIC",
        symbol_category="A",
    )
    feed.update_quotes([quote])

    sell_res = simulator.submit_shadow_order(
        symbol="BANKASIA",
        side="SELL",
        quantity=50,
        limit_price=Decimal("18.50"),
        confirm=True,
        portfolio_id="H9210_SHADOW",
    )
    assert sell_res["status"] == "FILLED"
    assert sell_res["quantity"] == 50
    assert sell_res["avg_fill_price"] == 18.50
    assert sell_res["realized_pnl"] > 0
    assert sell_res["unsettled_sales_bdt"] > 0

    with db.read() as session:
        state = portfolio_state(session)
        assert_ledger(session, state, portfolio_id="H9210_SHADOW")
        assert state.unsettled_sales_bdt > ZERO
        # Check TradeLearningLog was captured
        logs = list(session.scalars(select(TradeLearningLog).where(TradeLearningLog.symbol == "BANKASIA", TradeLearningLog.side == "SELL")))
        assert len(logs) >= 1
        assert logs[0].outcome_type == "SELL_PROFIT"
        assert logs[0].net_pnl_pct > ZERO


def test_shadow_simulator_preflight_invariants(test_db_and_settings):
    """Verifies preflight rejections of SPOT settlement, Z category, and out-of-circuit prices."""
    db, settings = test_db_and_settings
    feed = TradeXpressPassiveFeed(db)
    simulator = TradeXpressShadowSimulator(db, settings, feed=feed)

    # 1. SPOT settlement stock rejection
    spot_quote = MarketQuote(
        symbol="ASIATICLAB",
        ltp=Decimal("35.00"),
        change=Decimal("0"),
        pct_change=Decimal("0"),
        volume=1000,
        open_price=Decimal("35.00"),
        high=Decimal("35.00"),
        low=Decimal("35.00"),
        bid=Decimal("35.00"),
        bid_qty=100,
        offer=Decimal("35.00"),
        offer_qty=100,
        min_limit=Decimal("30.00"),
        max_limit=Decimal("40.00"),
        settlement_type="SPOT",
        symbol_category="A",
    )
    feed.update_quotes([spot_quote])
    res_spot = simulator.submit_shadow_order(
        symbol="ASIATICLAB",
        side="BUY",
        quantity=10,
        limit_price=Decimal("35.00"),
        confirm=True,
    )
    assert res_spot["status"] == "REJECTED"
    assert any("SPOT settlement rejected" in e for e in res_spot["errors"])

    # 2. Z category rejection
    z_quote = MarketQuote(
        symbol="JUNKZ",
        ltp=Decimal("10.00"),
        change=Decimal("0"),
        pct_change=Decimal("0"),
        volume=1000,
        open_price=Decimal("10.00"),
        high=Decimal("10.00"),
        low=Decimal("10.00"),
        bid=Decimal("10.00"),
        bid_qty=100,
        offer=Decimal("10.00"),
        offer_qty=100,
        min_limit=Decimal("8.00"),
        max_limit=Decimal("12.00"),
        settlement_type="PUBLIC",
        symbol_category="Z",
    )
    feed.update_quotes([z_quote])
    res_z = simulator.submit_shadow_order(
        symbol="JUNKZ",
        side="BUY",
        quantity=10,
        limit_price=Decimal("10.00"),
        confirm=True,
    )
    assert res_z["status"] == "REJECTED"
    assert any("Category 'Z' rejected" in e for e in res_z["errors"])


def test_autotrader_l1_l2_risk_split_and_exclusions(test_db_and_settings):
    """Verifies AutoTrader enforces 15% cap on L2, excludes Z/SPOT/Upper Circuit, and uses faster scalp tiers."""
    db, settings = test_db_and_settings

    with db.write() as session:
        state = portfolio_state(session)
        state.trading_mode = "TEST_OFFHOURS"

        # Create Z category company
        session.add(
            CompanyProfile(
                symbol="ZCORP",
                name="Z Corporation",
                sector="Junk",
                favorite=True,
                settlement_days=2,
                last_price=Decimal("20.00"),
                price_history=[{"date": state.clock_date.isoformat(), "close": "20.00", "open": "20.00", "high": "20.00", "low": "20.00", "volume": "100"}],
                quote_on=state.clock_date,
                symbol_category="Z",
                settlement_type="PUBLIC",
                watchlist_category="GSC_L1",
            )
        )
        session.add(CustomRule(symbol="ZCORP", enabled=True, buy_allocation_pct=Decimal("20")))

        # Create Upper Circuit locked company
        session.add(
            CompanyProfile(
                symbol="UPPERLOCK",
                name="Locked Stock",
                sector="Tech",
                favorite=True,
                settlement_days=2,
                last_price=Decimal("50.00"),
                price_history=[{"date": state.clock_date.isoformat(), "close": "50.00", "open": "50.00", "high": "50.00", "low": "50.00", "volume": "100"}],
                quote_on=state.clock_date,
                symbol_category="A",
                settlement_type="PUBLIC",
                hit_upper_circuit=True,
                watchlist_category="GSC_L1",
            )
        )
        session.add(CustomRule(symbol="UPPERLOCK", enabled=True, buy_allocation_pct=Decimal("20")))

        # Create GSC_L2 company with 25% requested allocation (should cap at 15%)
        session.add(
            CompanyProfile(
                symbol="L2SCALP",
                name="Scalp Candidate",
                sector="Bank",
                favorite=True,
                settlement_days=2,
                last_price=Decimal("10.00"),
                price_history=[{"date": state.clock_date.isoformat(), "close": "10.00", "open": "10.00", "high": "10.00", "low": "10.00", "volume": "100"}],
                quote_on=state.clock_date,
                symbol_category="A",
                settlement_type="PUBLIC",
                watchlist_category="GSC_L2",
            )
        )
        session.add(CustomRule(symbol="L2SCALP", enabled=True, buy_allocation_pct=Decimal("25")))
        session.flush()

    autotrader = AutoTrader(db, settings)
    result = autotrader.run_cycle(dry_run=True)

    decisions = {d["symbol"]: d["action"] for d in result.get("decisions", [])}
    assert decisions.get("ZCORP") == "SKIP_Z_CATEGORY"
    assert decisions.get("UPPERLOCK") == "SKIP_UPPER_CIRCUIT_LOCKED"


def test_tradexpress_routes_and_learning_api(test_db_and_settings):
    """Tests FastAPI /api/tradexpress/* endpoints and Hermes learning review route."""
    db, settings = test_db_and_settings
    app = create_app(database=db, settings=settings)
    with TestClient(app, base_url="http://localhost") as client:
        # 1. GET /api/tradexpress/status
        res_status = client.get("/api/tradexpress/status")
        assert res_status.status_code == 200
        status_data = res_status.json()
        assert "status" in status_data
        assert "guidance" in status_data
        assert "execution_venue" in status_data

        # 2. POST /api/tradexpress/passive-ingest
        snapshot = {
            "tab": "gsc",
            "cdp_connected": True,
            "market_watch_rows": [
                {
                    "dataObj": {
                        "sDes": "BANKASIA`PB",
                        "ltp": 18.40,
                        "chg": 0.50,
                        "pctChg": 2.79,
                        "vol": 500000,
                        "open": 18.00,
                        "high": 18.50,
                        "low": 17.90,
                        "bbp": 18.30,
                        "bbq": 15000,
                        "bap": 18.40,
                        "baq": 20000,
                        "minLimit": 16.50,
                        "maxLimit": 20.00,
                        "dispSettType": "PUBLIC",
                        "dispSymCat": "A",
                    }
                }
            ],
            "account_summary": {
                "cash_balance": 188.00,
                "available_cash_balance": 353.60,
                "unsettled_sales": 165.60,
                "buying_power": 353.60,
            },
        }
        res_ingest = client.post("/api/tradexpress/passive-ingest", json=snapshot)
        assert res_ingest.status_code == 200
        ingest_data = res_ingest.json()
        assert ingest_data["status"] == "INGESTED"
        assert ingest_data["quotes_updated"] >= 1
        assert ingest_data["summary_updated"] is True

        # 3. POST /api/tradexpress/shadow-order (Step 1 preview)
        res_preview = client.post(
            "/api/tradexpress/shadow-order",
            json={
                "symbol": "BANKASIA",
                "side": "BUY",
                "quantity": 10,
                "price": 18.40,
                "confirm": False,
            },
        )
        assert res_preview.status_code == 200
        preview_data = res_preview.json()
        assert preview_data["step"] == 1
        assert preview_data["status"] == "PREVIEW"
        assert preview_data["order_value"] == 184.0

        # 4. POST /api/tradexpress/shadow-order (Step 2 confirm fill)
        res_exec = client.post(
            "/api/tradexpress/shadow-order",
            json={
                "symbol": "BANKASIA",
                "side": "BUY",
                "quantity": 10,
                "price": 18.40,
                "confirm": True,
            },
        )
        assert res_exec.status_code == 200
        exec_data = res_exec.json()
        assert exec_data["status"] == "FILLED"
        assert exec_data["avg_fill_price"] == 18.40

        # 5. GET /api/tradexpress/orders
        res_orders = client.get("/api/tradexpress/orders")
        assert res_orders.status_code == 200
        orders = res_orders.json()
        assert len(orders) >= 1

        # 6. GET /api/tradexpress/learning
        res_learn = client.get("/api/tradexpress/learning")
        assert res_learn.status_code == 200
        learn_data = res_learn.json()
        assert "total_records" in learn_data
        assert "win_rate_pct" in learn_data
        assert len(learn_data["recent_logs"]) >= 1


def test_post_shadow_reset_clean_and_mirror(test_db_and_settings):
    """Verifies POST /api/tradexpress/shadow/reset with CLEAN_DUMMY and MIRROR_H9210."""
    db, settings = test_db_and_settings
    app = create_app(settings)
    client = TestClient(app, base_url="http://127.0.0.1:8000")

    # 1. Ingest passive snapshot with buying power
    ingest_res = client.post(
        "/api/tradexpress/passive-ingest",
        json={
            "source": "EDGE_EXTENSION_PASSIVE",
            "dse_status": "Trading",
            "tab": "Dhaka Stock Exchange",
            "market_watch_rows": [
                {"sDes": "BANKASIA", "ltp": "19.20", "chg": "0.80", "pctChg": "4.35", "vol": "50000"}
            ],
            "account_summary": {
                "customer_number": "H9210",
                "cash_balance": 353.00,
                "buying_power": 353.00,
            },
        },
    )
    assert ingest_res.status_code == 200

    # 2. Reset with CLEAN_DUMMY 50,000
    res_clean = client.post(
        "/api/tradexpress/shadow/reset",
        json={"mode": "CLEAN_DUMMY", "capital": 50000.00},
    )
    assert res_clean.status_code == 200
    clean_data = res_clean.json()
    assert clean_data["ok"] is True
    assert clean_data["status"] in ("RESET_OK", "RESET_SUCCESS")
    assert clean_data["portfolio_id"] == "H9210_SHADOW"
    assert clean_data["initial_capital"] == 50000.00
    assert clean_data["circuit_breaker_reset"] is True

    # 3. Reset with MIRROR_H9210
    res_mirror = client.post(
        "/api/tradexpress/shadow/reset",
        json={"mode": "MIRROR_H9210"},
    )
    assert res_mirror.status_code == 200
    mirror_data = res_mirror.json()
    assert mirror_data["ok"] is True
    assert mirror_data["status"] in ("RESET_OK", "RESET_SUCCESS")
    assert mirror_data["initial_capital"] == 353.00

