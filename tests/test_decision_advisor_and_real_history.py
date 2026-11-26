"""Offline unit & route tests for Sprint 6A: Real 30d DSE History + Decision Advisor."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
import pytest

from backend.adapters.tradexpress.history_provider import (
    DHAKA_TZ,
    parse_daily_history_candles,
    sync_watchlist_real_history,
)
from backend.adapters.tradexpress.passive_feed import MarketQuote, TradeXpressPassiveFeed, get_global_passive_feed
from backend.config import Settings
from backend.database import CompanyProfile, CustomRule, Database, portfolio_state
from backend.engine.decision_advisor import analyze_market_decisions
from backend.main import create_app
from backend.seed import seed_demo


@pytest.fixture
def isolated_db_settings(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KERNEL_TOKEN", "test-kernel-token")
    db_file = tmp_path / "test_s6a.db"
    settings = Settings(
        database_url=f"sqlite:///{db_file.as_posix()}",
        initial_capital=Decimal("15000.00"),
        demo_start_date=date(2026, 11, 24),
        buy_fee_rate=Decimal("0.004"),
        sell_fee_rate=Decimal("0.004"),
    )
    db = Database(settings.database_url)
    db.create_schema()
    with db.write() as session:
        seed_demo(session, settings)
        st = portfolio_state(session)
        st.mode = "SHADOW"
        st.execution_venue = "SHADOW_DUMMY"
        st.initial_capital = Decimal("0.00")
    feed = get_global_passive_feed(db)
    feed.database = db
    return db, settings, feed


def test_parse_daily_history_candles_sorted_and_filtered():
    """Parses [ts, o, h, l, c, v] into sorted Asia/Dhaka dates and drops close <= 0."""
    ts_day1 = int(datetime(2026, 11, 10, 14, 0, tzinfo=DHAKA_TZ).timestamp())
    ts_day2 = int(datetime(2026, 11, 11, 14, 0, tzinfo=DHAKA_TZ).timestamp())
    ts_bad = int(datetime(2026, 11, 12, 14, 0, tzinfo=DHAKA_TZ).timestamp())

    raw = [
        [ts_day2, 18.0, 18.5, 17.8, 18.4, 20000],
        [ts_day1, 17.5, 18.1, 17.4, 17.9, 15000],
        [ts_bad, 0.0, 0.0, 0.0, 0.0, 0],
    ]
    bars = parse_daily_history_candles(raw, sessions=30)
    assert len(bars) == 2
    assert bars[0]["date"] == "2026-11-10"
    assert bars[0]["close"] == "17.90"
    assert bars[1]["date"] == "2026-11-11"
    assert bars[1]["close"] == "18.40"


def test_parse_stocknow_6_parallel_arrays_and_reject_short_sync(isolated_db_settings):
    """Verifies StockNow's real 6-array format [O,H,L,C,V,T] parses cleanly & <7 bars fails sync."""
    db, settings, feed = isolated_db_settings
    ts_base = int(datetime(2026, 11, 1, 14, 0, tzinfo=DHAKA_TZ).timestamp())
    n = 12
    opens = [328.0 + i * 0.1 for i in range(n)]
    highs = [331.0 + i * 0.1 for i in range(n)]
    lows = [327.0 + i * 0.1 for i in range(n)]
    closes = [329.0 + i * 0.1 for i in range(n)]
    volumes = [12000 + i * 100 for i in range(n)]
    timestamps = [ts_base + i * 86400 for i in range(n)]

    bars = parse_daily_history_candles([opens, highs, lows, closes, volumes, timestamps], sessions=30)
    assert len(bars) == 12
    assert bars[0]["close"] == "329.00"
    assert bars[-1]["close"] == f"{closes[-1]:.2f}"

    # Verify sync_watchlist_real_history NEVER counts <7 bars in synced_count
    import asyncio

    with patch("backend.adapters.tradexpress.history_provider.fetch_real_daily_history", new=AsyncMock(return_value=bars[:2])):
        res = asyncio.run(sync_watchlist_real_history(db, symbols=["BANKASIA"], sessions=30, feed=feed, pace_seconds=0))
        assert res["synced_count"] == 0
        assert any("BANKASIA" in f for f in res["failed_symbols"])


def test_passive_broker_order_list_ingest_and_route(isolated_db_settings):
    """Verifies passive broker_order_list is stored and surfaced in GET /api/tradexpress/orders."""
    db, settings, feed = isolated_db_settings
    app = create_app(settings)
    client = TestClient(app, base_url="http://127.0.0.1:8000")

    resp = client.post(
        "/api/tradexpress/passive-ingest",
        json={
            "source": "EDGE_EXTENSION_PASSIVE",
            "tab": "order_list",
            "broker_order_list": [
                {
                    "symbol": "BANKASIA`PB",
                    "orderId": "ORD-9210-1",
                    "cashAccount": "H9210",
                    "status": "Filled",
                    "side": "SELL",
                    "quantity": 9,
                    "price": 18.40,
                    "filledQty": 9,
                    "pendingQty": 0,
                    "avgPrice": 18.40,
                    "orderValue": 165.60,
                }
            ],
        },
        headers={"Origin": "chrome-extension://testabc123"},
    )
    assert resp.status_code == 200

    orders_resp = client.get("/api/tradexpress/orders")
    assert orders_resp.status_code == 200
    orders = orders_resp.json()
    assert any(o.get("source") == "BROKER H9210" and o.get("symbol") == "BANKASIA" for o in orders)


def test_decision_advisor_zero_dummy_buy_and_blocked(isolated_db_settings):
    """Verifies NO_HISTORY (<7 bars), BUY_CANDIDATE (real 15d dip on L1), and BLOCKED (Z/SPOT)."""
    db, settings, feed = isolated_db_settings

    # Build 15 real daily candles ending in a clean dip near support (17.00 -> 19.00 -> 17.20)
    real_15d = [
        {"date": f"2026-11-{i + 1:02d}", "open": "18.50", "high": "19.00", "low": "17.00", "close": f"{18.80 if i < 12 else 17.20:.2f}", "volume": 10000}
        for i in range(15)
    ]

    with db.write() as session:
        # 1. BANKASIA: GSC_L1, PUBLIC, Cat A, 15 real candles -> BUY_CANDIDATE
        cp_bank = session.get(CompanyProfile, "BANKASIA")
        cp_bank.watchlist_category = "GSC_L1"
        cp_bank.favorite = True
        cp_bank.settlement_type = "PUBLIC"
        cp_bank.symbol_category = "A"
        cp_bank.last_price = Decimal("17.20")
        cp_bank.offer = Decimal("17.20")
        cp_bank.bid = Decimal("17.10")
        cp_bank.price_history = real_15d

        # 2. GP: GSC_L1, < 7 candles -> NO_HISTORY (never BUY_CANDIDATE!)
        cp_gp = session.get(CompanyProfile, "GP")
        cp_gp.watchlist_category = "GSC_L1"
        cp_gp.favorite = True
        cp_gp.last_price = Decimal("275.00")
        cp_gp.price_history = real_15d[-3:]

        # 3. Z-category stock -> BLOCKED
        cp_z = CompanyProfile(
            symbol="ZTEST",
            name="Z Test",
            sector="TEST",
            watchlist_category="GSC_L2",
            favorite=True,
            settlement_days=2,
            settlement_type="PUBLIC",
            symbol_category="Z",
            last_price=Decimal("10.00"),
            price_history=real_15d,
            quote_on=date(2026, 11, 24),
            source="TRADEXPRESS_LIVE_CURVE",
        )
        session.add(cp_z)
        session.add(CustomRule(symbol="ZTEST", enabled=True, buy_allocation_pct=Decimal("5.0")))

    # Passive ingest H9210 real buying power 353.00 -> should auto-initialize initial_capital from 0.00!
    from backend.adapters.tradexpress.passive_feed import ingest_passive_snapshot

    ingest_passive_snapshot(
        db,
        {
            "source": "EDGE_EXTENSION_PASSIVE",
            "dse_status": "Trading",
            "tab": "L1",
            "market_watch_rows": [
                {"sDes": "BANKASIA", "ltp": "17.20", "bid": "17.10", "offer": "17.20", "pctChg": "-1.15", "dispSettType": "PUBLIC", "dispSymCat": "A"}
            ],
            "account_summary": {"customer_number": "H9210", "buying_power": 353.00, "cash_balance": 353.00},
        },
        feed=feed,
    )

    with db.read() as session:
        st = portfolio_state(session)
        assert st.initial_capital == Decimal("353.00")

        res = analyze_market_decisions(session, settings, passive_feed=feed)

    buy_syms = {r["symbol"]: r for r in res["buy_candidates"]}
    assert "BANKASIA" in buy_syms
    bank = buy_syms["BANKASIA"]
    assert bank["suggested_limit_price"] == pytest.approx(17.20, 0.01)
    assert bank["est_net_upside_pct"] > 1.5
    # 353 / (17.20 * 1.004) = 20 shares
    assert bank["affordable_qty_h9210"] == 20

    # GP with < 7 candles must be in blocked_or_missing as NO_HISTORY
    missing_syms = {r["symbol"]: r for r in res["blocked_or_missing"]}
    assert "GP" in missing_syms
    assert missing_syms["GP"]["action"] == "NO_HISTORY"
    assert "ZTEST" in missing_syms
    assert missing_syms["ZTEST"]["action"] == "BLOCKED"


def test_routes_decisions_sync_history_and_hermes_tool(isolated_db_settings):
    """Verifies /api/tradexpress/decisions, /k/decisions/analyze, /sync-history (mocked HTTP), and hb_analyze_market."""
    db, settings, feed = isolated_db_settings
    app = create_app(settings)
    client = TestClient(app, base_url="http://127.0.0.1:8000")

    ts_base = int(datetime(2026, 11, 1, 14, 0, tzinfo=DHAKA_TZ).timestamp())
    mock_bars = [[ts_base + i * 86400, 18.0, 19.0, 17.5, 18.2 + (i % 3) * 0.1, 12000] for i in range(15)]

    with patch("backend.adapters.tradexpress.history_provider.fetch_real_daily_history", new=AsyncMock(return_value=parse_daily_history_candles(mock_bars))):
        sync_res = client.post("/api/tradexpress/sync-history", json={"symbols": ["BANKASIA"], "sessions": 30})
        assert sync_res.status_code == 200
        sync_data = sync_res.json()
        assert sync_data["ok"] is True
        assert sync_data["synced_count"] == 1

    dec_res = client.get("/api/tradexpress/decisions")
    assert dec_res.status_code == 200
    dec_json = dec_res.json()
    assert "data_truth_summary" in dec_json
    assert "all_decisions" in dec_json

    k_res = client.get("/k/decisions/analyze", headers={"X-Kernel-Token": "test-kernel-token"})
    assert k_res.status_code == 200
    assert "data_truth_summary" in k_res.json()

    # Verify hb_analyze_market tool
    from plugins.humming_bird import _TOOLS
    from plugins.humming_bird.tools import hb_analyze_market

    assert len(_TOOLS) == 25
    with patch("urllib.request.urlopen") as mock_open:
        fake_resp = MagicMock()
        fake_resp.read.return_value = json.dumps(dec_json).encode("utf-8")
        fake_resp.__enter__.return_value = fake_resp
        mock_open.return_value = fake_resp
        tool_out = json.loads(hb_analyze_market())
        assert "data_truth_summary" in tool_out


def test_zero_initial_capital_snapshot_no_division_undefined(isolated_db_settings):
    """Verifies build_snapshot handles initial_capital=0.00 & net_equity=0.00 without DivisionUndefined."""
    db, settings, feed = isolated_db_settings
    from backend.database import TaxLot, TradeLog
    from backend.portfolio import build_snapshot
    from sqlalchemy import delete

    with db.write() as session:
        session.execute(delete(TradeLog))
        session.execute(delete(TaxLot))
        st = portfolio_state(session)
        st.initial_capital = Decimal("0.00")

    snap = build_snapshot(db, settings)
    assert snap["metrics"]["initial_capital"] == 0.0
    assert snap["metrics"]["total_gain_pct"] == 0.0
