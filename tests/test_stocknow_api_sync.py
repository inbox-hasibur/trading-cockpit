"""Tests for StockNow REST API synchronization.

Verifies:
1. Sync Live Prices: GET /instruments for all DSE shares with timestamp, source="STOCKNOW_API",
   and last_updated; no defaults for missing prices; show LAST CLOSE when market is closed.
2. Favorites: GET /user/lists for Giant Stable Companies, GSC Upper Trends L1, L2 mapped to
   GSC, GSC_L1, GSC_L2 with priority L1 > L2 > GSC.
3. History: fetch 7 to 15 session candles per watched symbol so curves stop showing INVALID DATA;
   if missing show NO DATA with a reason.
4. Portfolio Sync: GET /portfolios/{id}/show and ledger for active portfolio, reconcile into SQLite,
   show diff. Cockpit holdings equal StockNow (cash 129,200, BANKASIA 138, IBNSINA 16).
   A failed or unauthenticated sync never writes zero holdings or default cash.
5. Browser DOM Sync: stays only as an Onscreen cross-check; log API vs DOM mismatches as warnings.
"""

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from backend.adapters.stocknow_api import (
    NotAuthenticatedError,
    SchemaChangedError,
    StockNowAPI,
)
from backend.adapters.stocknow_market_sync import (
    fetch_stocknow_live_market_data,
    get_or_fetch_all_dse_shares,
    sync_live_market_to_db,
)
from backend.adapters.stocknow_portfolio_sync import (
    extract_hummingbird_portfolio,
    reconcile_portfolio_to_db,
    sync_stocknow_portfolio_via_api,
)
from backend.config import Settings
from backend.database import CompanyProfile, Database, PortfolioState, TaxLot, TradeLog, portfolio_state
from backend.engine.curve_analyzer import analyze_curve
from backend.engine.signals import assess_company
from backend.seed import seed_demo

FIXTURES_DIR = Path("tests/fixtures/stocknow")


def load_fixture(name: str) -> Any:
    with open(FIXTURES_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def memory_db():
    db = Database("sqlite:///:memory:")
    db.create_schema()
    return db


@pytest.fixture
def seeded_db(memory_db, settings):
    with memory_db.write() as session:
        seed_demo(session, settings)
    return memory_db


# -----------------------------------------------------------------------------
# 1. Sync Live Prices
# -----------------------------------------------------------------------------

@pytest.mark.anyio
async def test_sync_live_prices_schema_and_no_defaults():
    """Live prices from GET /instruments fill All DSE Shares with required metadata and no defaults."""
    inst_fixture = load_fixture("instruments.json")
    user_lists_fixture = load_fixture("user_lists.json")
    history_fixture = load_fixture("history_candles.json")

    # Add an instrument with zero prices to test "no defaults for missing prices"
    inst_fixture["NOPRICE"] = {
        "code": "NOPRICE",
        "name": "No Price Ltd",
        "ltp": 0,
        "close": 0,
        "ycp": 0,
        "updated_at": "2026-11-05 14:00:00",
    }
    # Add an instrument with closed market (ltp is 0 or None, but close/ycp exist)
    inst_fixture["CLOSEDCO"] = {
        "code": "CLOSEDCO",
        "name": "Closed Co Ltd",
        "ltp": 0,
        "close": 55.5,
        "ycp": 54.0,
        "updated_at": "2026-11-05 14:00:00",
    }

    # Add CLOSEDCO to user_lists to check its quote parsing
    user_lists_fixture[0]["items"].append({"code": "CLOSEDCO"})
    user_lists_fixture[0]["items"].append({"code": "NOPRICE"})

    injected_history = {
        "BANKASIA": history_fixture,
        "CLOSEDCO": history_fixture,
    }

    quotes = await fetch_stocknow_live_market_data(
        injected_instruments=inst_fixture,
        injected_lists=user_lists_fixture,
        injected_history=injected_history,
        as_of_date=date(2026, 11, 5),
    )

    # 1. Verify NOPRICE was omitted (no defaults invented)
    quote_syms = {q["symbol"] for q in quotes}
    assert "NOPRICE" not in quote_syms, "Instruments without valid market prices must be skipped"

    # 2. Verify CLOSEDCO shows LAST_CLOSE
    closed_q = next(q for q in quotes if q["symbol"] == "CLOSEDCO")
    assert closed_q["price_type"] == "LAST_CLOSE"
    assert closed_q["last_price"] == Decimal("55.5")
    assert closed_q["source"] == "STOCKNOW_API"
    assert closed_q["last_updated"] == "2026-11-05 14:00:00"

    # 3. Verify BANKASIA has source="STOCKNOW_API" and valid LTP
    bank_q = next(q for q in quotes if q["symbol"] == "BANKASIA")
    assert bank_q["source"] == "STOCKNOW_API"
    assert bank_q["last_price"] == Decimal("17.5")

    # 4. Verify catalog via get_or_fetch_all_dse_shares
    all_shares = await get_or_fetch_all_dse_shares()
    assert all_shares["source"] == "STOCKNOW_API"
    assert "timestamp" in all_shares
    assert "last_updated" in all_shares
    assert all_shares["total"] >= 10
    # Every share in catalog has required fields
    for s in all_shares["shares"]:
        assert "symbol" in s
        assert "ltp" in s
        assert "sparkline" in s


# -----------------------------------------------------------------------------
# 2. Favorites Mapping & Precedence
# -----------------------------------------------------------------------------

@pytest.mark.anyio
async def test_favorites_mapping_and_precedence():
    """GET /user/lists maps to GSC, GSC_L1, GSC_L2 with priority L1 > L2 > GSC."""
    inst_fixture = load_fixture("instruments.json")
    history_fixture = load_fixture("history_candles.json")

    # Construct lists with overlap to test priority using symbols in instruments.json
    lists_payload = [
        {
            "id": 1,
            "name": "Giant Stable Companies",
            "items": [{"code": "ACI"}, {"code": "BANKASIA"}, {"code": "BRACBANK"}],
        },
        {
            "id": 2,
            "name": "GSC Upper Trends L2",
            "items": [{"code": "BRACBANK"}],
        },
        {
            "id": 3,
            "name": "GSC Upper Trends L1",
            "items": [{"code": "BANKASIA"}],
        },
    ]

    hist_map = {
        "ACI": history_fixture,
        "BANKASIA": history_fixture,
        "BRACBANK": history_fixture,
    }

    quotes = await fetch_stocknow_live_market_data(
        injected_instruments=inst_fixture,
        injected_lists=lists_payload,
        injected_history=hist_map,
        as_of_date=date(2026, 11, 5),
    )

    by_sym = {q["symbol"]: q for q in quotes}

    # ACI: only in Giant Stable Companies -> GSC
    assert by_sym["ACI"]["watchlist_category"] == "GSC"
    # BRACBANK: in GSC and GSC_L2 -> GSC_L2
    assert by_sym["BRACBANK"]["watchlist_category"] == "GSC_L2"
    # BANKASIA: in GSC and GSC_L1 -> GSC_L1 (highest priority)
    assert by_sym["BANKASIA"]["watchlist_category"] == "GSC_L1"


# -----------------------------------------------------------------------------
# 3. History Candles & No "INVALID DATA"
# -----------------------------------------------------------------------------

@pytest.mark.anyio
async def test_history_candles_no_invalid_data_and_missing_no_data():
    """Candle curves evaluate cleanly; missing candles report NO DATA."""
    history_fixture = load_fixture("history_candles.json")
    inst_fixture = load_fixture("instruments.json")
    lists_payload = [
        {
            "id": 1,
            "name": "Giant Stable Companies",
            "items": [{"code": "BANKASIA"}, {"code": "ACI"}],
        }
    ]

    # BANKASIA has real candles; ACI has empty candles
    hist_map = {
        "BANKASIA": history_fixture,
        "ACI": [],
    }

    quotes = await fetch_stocknow_live_market_data(
        injected_instruments=inst_fixture,
        injected_lists=lists_payload,
        injected_history=hist_map,
        as_of_date=date(2026, 11, 5),
    )

    by_sym = {q["symbol"]: q for q in quotes}

    # 1. BANKASIA has 15 candles, unique ascending dates
    bank_hist = by_sym["BANKASIA"]["history"]
    assert 7 <= len(bank_hist) <= 15
    dates = [h["date"] for h in bank_hist]
    assert len(dates) == len(set(dates)), "Candle dates must be strictly unique"
    assert dates == sorted(dates), "Candle dates must be strictly ascending"

    # Analyze curve with real candles: must NOT be INVALID_DATA
    analysis = analyze_curve(bank_hist, as_of=date.fromisoformat(dates[-1]))
    assert analysis.signal != "INVALID_DATA", f"Curve analysis returned unexpected INVALID_DATA: {analysis.reason}"
    assert analysis.signal in ("BUY_ZONE", "SELL_ZONE", "MID_RANGE", "CRASH_QUARANTINE")

    # 2. ACI has no candles -> history_status reports reason
    assert by_sym["ACI"]["history"] == []
    assert "No historical candle data" in by_sym["ACI"]["history_status"]

    # Curve analysis on empty history returns NO_DATA with reason
    empty_analysis = analyze_curve([], as_of=date(2026, 11, 5))
    assert empty_analysis.signal == "NO_DATA"
    assert "No historical candle data" in empty_analysis.reason


# -----------------------------------------------------------------------------
# 4. Portfolio Sync & Holdings Reconcile for #164580
# -----------------------------------------------------------------------------

@pytest.mark.anyio
async def test_portfolio_sync_reconcile_and_diff(seeded_db, settings):
    """Reconciling #164580 sets cash to 129,200, BANKASIA 138, IBNSINA 16, and reports diff."""
    show_fixture = load_fixture("portfolio_show.json")
    ledger_fixture = load_fixture("portfolio_ledger.json")

    # Verify extraction from raw StockNow API payload
    extracted = extract_hummingbird_portfolio(
        injected_portfolio=dict(show_fixture, ledger=ledger_fixture["ledger"]),
    )
    assert extracted["portfolio_id"] == "164580"
    assert extracted["cash_balance"] == Decimal("129200")
    assert len(extracted["holdings"]) == 2

    holdings_dict = {h["symbol"]: h for h in extracted["holdings"]}
    assert holdings_dict["BANKASIA"]["quantity"] == 138
    assert holdings_dict["BANKASIA"]["avg_cost"] == Decimal("17")
    assert holdings_dict["IBNSINA"]["quantity"] == 16
    assert holdings_dict["IBNSINA"]["avg_cost"] == Decimal("302.8")

    # Reconcile into SQLite DB
    res = reconcile_portfolio_to_db(seeded_db, settings, extracted)

    assert res["success"] is True
    assert res["cash_balance"] == 129200.0
    assert "diff" in res

    diff = res["diff"]
    assert "old_cash" in diff
    assert diff["new_cash"] == 129200.0
    assert "cash_diff" in diff
    assert "holdings_diff" in diff
    assert "BANKASIA" in diff["holdings_diff"]
    assert diff["holdings_diff"]["BANKASIA"]["stocknow_qty"] == 138

    # Query SQLite database to confirm exact holdings
    with seeded_db.read() as session:
        lots = session.scalars(select(TaxLot).filter(TaxLot.portfolio_id == "164580")).all()
        lots_by_sym = {l.symbol: l for l in lots}
        assert set(lots_by_sym.keys()) == {"BANKASIA", "IBNSINA"}
        assert lots_by_sym["BANKASIA"].remaining_qty == 138
        assert lots_by_sym["BANKASIA"].buy_price == Decimal("17.00")
        assert lots_by_sym["IBNSINA"].remaining_qty == 16
        assert lots_by_sym["IBNSINA"].buy_price == Decimal("302.80")

        st = portfolio_state(session)
        from backend.engine.t2_ledger import bucket_balances
        balances = bucket_balances(session, st, portfolio_id="164580")
        total_cash = sum((b.available_cash for b in balances.values()), Decimal("0"))
        assert total_cash == Decimal("129200.00")


# -----------------------------------------------------------------------------
# 5. Failed / Unauthenticated Sync Never Wipes Holdings or Sets Default Cash
# -----------------------------------------------------------------------------

@pytest.mark.anyio
async def test_unauthenticated_sync_preserves_holdings_and_cash(seeded_db, settings):
    """An unauthenticated or failed API call raises an error and leaves SQLite untouched."""
    # First, record current state of seeded DB
    with seeded_db.read() as session:
        pre_lots = session.scalars(select(TaxLot)).all()
        pre_lots_count = len(pre_lots)
        pre_lots_symbols = {l.symbol for l in pre_lots}
        pre_state = portfolio_state(session)
        from backend.engine.t2_ledger import bucket_balances
        pre_cash = sum((b.available_cash for b in bucket_balances(session, pre_state).values()), Decimal("0"))

    assert pre_lots_count > 0, "Pre-condition: database has seeded holdings"

    # Mock StockNowAPI to simulate 401 unauthenticated
    mock_api = MagicMock()
    mock_api.get_portfolio = AsyncMock(side_effect=NotAuthenticatedError("Session expired"))

    with pytest.raises(NotAuthenticatedError):
        await sync_stocknow_portfolio_via_api("164580", api_client=mock_api, settings=settings)

    # Mock StockNowAPI to simulate schema changed / empty response
    mock_api_empty = MagicMock()
    mock_api_empty.get_portfolio = AsyncMock(return_value={})  # Missing "id"

    with pytest.raises(SchemaChangedError):
        await sync_stocknow_portfolio_via_api("164580", api_client=mock_api_empty, settings=settings)

    # Verify SQLite database was NOT modified at all
    with seeded_db.read() as session:
        post_lots = session.scalars(select(TaxLot)).all()
        post_lots_symbols = {l.symbol for l in post_lots}
        post_state = portfolio_state(session)
        post_cash = sum((b.available_cash for b in bucket_balances(session, post_state).values()), Decimal("0"))

        assert len(post_lots) == pre_lots_count
        assert post_lots_symbols == pre_lots_symbols
        assert post_cash == pre_cash, "Cash must never revert to default or zero on failed sync"


# -----------------------------------------------------------------------------
# 6. Browser DOM Sync Cross-Check
# -----------------------------------------------------------------------------

@pytest.mark.anyio
async def test_browser_dom_sync_cross_check_warning(caplog):
    """DOM sync serves only as cross-check; mismatches log warning without altering authoritative API data."""
    show_fixture = load_fixture("portfolio_show.json")
    ledger_fixture = load_fixture("portfolio_ledger.json")

    mock_client = MagicMock()
    mock_client.page = MagicMock()
    mock_client.page.is_closed = MagicMock(return_value=False)

    # Browser DOM returns different cash and holdings (e.g. stale tab)
    dom_stale_data = {
        "portfolio_id": "164580",
        "cash_balance": Decimal("100000"),  # mismatch: API has 129200
        "holdings": [{"symbol": "BANKASIA", "quantity": 100, "avg_cost": Decimal("17")}],
    }

    with patch(
        "backend.adapters.stocknow_portfolio_sync.extract_hummingbird_portfolio_from_browser",
        new=AsyncMock(return_value=dom_stale_data),
    ), caplog.at_level("WARNING"):
        result = await sync_stocknow_portfolio_via_api(
            portfolio_id="164580",
            live_client=mock_client,
            injected_portfolio=show_fixture,
            injected_ledger=ledger_fixture,
        )

    # Authoritative API data remains unchanged
    assert result["cash_balance"] == Decimal("129200")
    assert any(h["symbol"] == "IBNSINA" for h in result["holdings"])

    # Warnings were logged for both cash and holdings mismatches
    warnings = [r.message for r in caplog.records if r.levelname == "WARNING"]
    assert any("cash mismatch" in w for w in warnings)
    assert any("holdings mismatch" in w for w in warnings)


# -----------------------------------------------------------------------------
# 7. Endpoint Integration (POST /k/sync)
# -----------------------------------------------------------------------------

def test_kernel_sync_endpoints(client, monkeypatch):
    """POST /k/sync successfully coordinates portfolio, favorites and all_shares."""
    token = "test-kernel-token-xyz"
    monkeypatch.setenv("KERNEL_TOKEN", token)
    headers = {"X-Kernel-Token": token}

    show_fixture = load_fixture("portfolio_show.json")
    ledger_fixture = load_fixture("portfolio_ledger.json")

    # 1. Sync Portfolio with payload
    combined = dict(show_fixture, ledger=ledger_fixture["ledger"])
    res = client.post("/k/sync", json={"target": "portfolio", "payload": combined}, headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["target"] == "portfolio"
    assert data["result"]["success"] is True
    assert data["result"]["cash_balance"] == 129200.0

    # 2. Sync all_shares
    res_all = client.post("/k/sync", json={"target": "all_shares"}, headers=headers)
    assert res_all.status_code == 200
    data_all = res_all.json()
    assert data_all["target"] == "all_shares"
    assert data_all["result"]["source"] == "STOCKNOW_API"
