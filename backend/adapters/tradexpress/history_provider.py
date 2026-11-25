"""Real 30-day DSE daily historical candle provider.

Fetches verified historical daily OHLCV candles from StockNow's public,
unauthenticated read-only history API (separate host from LankaBangla,
robots.txt Allow: /, zero login/cookies) and supports passive TradeXpress
/web/chart payload extraction. Never fabricates fake/synthetic candles.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from decimal import Decimal
import logging
from typing import Any
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy import or_, select
from sqlalchemy.orm.attributes import flag_modified

from backend.adapters.base import from_tradexpress_symbol
from backend.database import CompanyProfile, Database, portfolio_state
from backend.engine.money import ZERO, decimal

logger = logging.getLogger("hummingbird.tradexpress.history")
DHAKA_TZ = ZoneInfo("Asia/Dhaka")
STOCKNOW_PUBLIC_HISTORY_URL = "https://stocknow.com.bd/api/v1/instruments/{symbol}/history?data2=true&resolution=1D&skip=0"


def parse_daily_history_candles(raw_payload: Any, sessions: int = 30) -> list[dict[str, Any]]:
    """Parses StockNow or TradeXpress OHLCV candle arrays/dicts into sorted daily bars.

    Drops any bar with close <= 0. Returns [] cleanly if payload is invalid or empty.
    """
    rows: list[Any] = []
    if isinstance(raw_payload, list):
        rows = raw_payload
    elif isinstance(raw_payload, dict):
        for key in ("data", "history", "candles", "bars", "results", "s"):
            val = raw_payload.get(key)
            if isinstance(val, list):
                rows = val
                break
        if not rows and isinstance(raw_payload.get("t"), list) and isinstance(raw_payload.get("c"), list):
            # TradingView UDF columnar format {t: [...], o: [...], h: [...], l: [...], c: [...], v: [...]}
            ts_list = raw_payload.get("t") or []
            o_list = raw_payload.get("o") or []
            h_list = raw_payload.get("h") or []
            l_list = raw_payload.get("l") or []
            c_list = raw_payload.get("c") or []
            v_list = raw_payload.get("v") or []
            for idx, ts_val in enumerate(ts_list):
                rows.append([
                    ts_val,
                    o_list[idx] if idx < len(o_list) else c_list[idx],
                    h_list[idx] if idx < len(h_list) else c_list[idx],
                    l_list[idx] if idx < len(l_list) else c_list[idx],
                    c_list[idx] if idx < len(c_list) else 0,
                    v_list[idx] if idx < len(v_list) else 0,
                ])

    by_date: dict[str, dict[str, Any]] = {}
    for item in rows:
        try:
            if isinstance(item, (list, tuple)) and len(item) >= 5:
                ts_raw, o_raw, h_raw, l_raw, c_raw = item[0], item[1], item[2], item[3], item[4]
                v_raw = item[5] if len(item) > 5 else 0
            elif isinstance(item, dict):
                ts_raw = item.get("date") or item.get("time") or item.get("t") or item.get("timestamp")
                c_raw = item.get("close") if item.get("close") is not None else item.get("c")
                o_raw = item.get("open") if item.get("open") is not None else item.get("o", c_raw)
                h_raw = item.get("high") if item.get("high") is not None else item.get("h", c_raw)
                l_raw = item.get("low") if item.get("low") is not None else item.get("l", c_raw)
                v_raw = item.get("volume") if item.get("volume") is not None else item.get("v", 0)
            else:
                continue

            close_val = decimal(c_raw)
            if not close_val.is_finite() or close_val <= ZERO:
                continue

            if isinstance(ts_raw, (int, float)):
                epoch = float(ts_raw)
                if epoch > 1e12:
                    epoch /= 1000.0
                date_str = datetime.fromtimestamp(epoch, tz=DHAKA_TZ).date().isoformat()
            else:
                ts_str = str(ts_raw or "").strip()
                if not ts_str:
                    continue
                if ts_str.isdigit():
                    epoch = float(ts_str)
                    if epoch > 1e12:
                        epoch /= 1000.0
                    date_str = datetime.fromtimestamp(epoch, tz=DHAKA_TZ).date().isoformat()
                else:
                    date_str = ts_str[:10]
                    # Validate ISO date format
                    datetime.strptime(date_str, "%Y-%m-%d")

            open_val = decimal(o_raw) if o_raw is not None else close_val
            high_val = decimal(h_raw) if h_raw is not None else close_val
            low_val = decimal(l_raw) if l_raw is not None else close_val
            if open_val <= ZERO:
                open_val = close_val
            if high_val <= ZERO:
                high_val = max(open_val, close_val)
            if low_val <= ZERO:
                low_val = min(open_val, close_val)

            try:
                vol_int = int(float(v_raw or 0))
            except (TypeError, ValueError):
                vol_int = 0

            by_date[date_str] = {
                "date": date_str,
                "open": f"{open_val:.2f}",
                "high": f"{high_val:.2f}",
                "low": f"{low_val:.2f}",
                "close": f"{close_val:.2f}",
                "volume": max(0, vol_int),
            }
        except Exception:
            continue

    sorted_bars = [by_date[d] for d in sorted(by_date.keys())]
    if sessions and sessions > 0:
        return sorted_bars[-sessions:]
    return sorted_bars


def parse_tradexpress_chart_payload(payload: Any) -> tuple[str | None, list[dict[str, Any]]]:
    """Extracts (symbol, daily_bars) from a passive TradeXpress /web/chart payload."""
    if not isinstance(payload, dict):
        return None, []
    raw_sym = (
        payload.get("symbol")
        or payload.get("sym")
        or payload.get("sDes")
        or payload.get("instrument")
        or ""
    )
    clean_sym = from_tradexpress_symbol(str(raw_sym)) if raw_sym else ""
    bars = parse_daily_history_candles(payload, sessions=30)
    if not clean_sym or not bars:
        return None, []
    return clean_sym, bars


async def fetch_real_daily_history(
    symbol: str,
    sessions: int = 30,
    client: httpx.AsyncClient | None = None,
) -> list[dict[str, Any]]:
    """Fetches real 1D DSE candles from StockNow's public unauthenticated history API."""
    clean_symbol = from_tradexpress_symbol(symbol)
    if not clean_symbol:
        return []
    url = STOCKNOW_PUBLIC_HISTORY_URL.format(symbol=clean_symbol)
    headers = {
        "User-Agent": "HummingBird-Cockpit/1.0 (Real DSE Curve Sync)",
        "Accept": "application/json",
    }
    try:
        if client is not None:
            resp = await client.get(url, headers=headers, timeout=10.0)
        else:
            async with httpx.AsyncClient(timeout=10.0) as local_client:
                resp = await local_client.get(url, headers=headers)
        if resp.status_code != 200:
            logger.warning("Real history HTTP %s for %s", resp.status_code, clean_symbol)
            return []
        return parse_daily_history_candles(resp.json(), sessions=sessions)
    except Exception as exc:
        logger.warning("Failed fetching real history for %s: %s", clean_symbol, exc)
        return []


async def sync_watchlist_real_history(
    db: Database,
    symbols: list[str] | None = None,
    sessions: int = 30,
    feed: Any = None,
    pace_seconds: float = 0.25,
) -> dict[str, Any]:
    """Syncs real 30-day DSE daily candles for watchlist symbols (never fabricates data)."""
    if feed is None:
        from backend.adapters.tradexpress.passive_feed import get_global_passive_feed

        feed = get_global_passive_feed(db)

    target_symbols: list[str] = []
    if symbols:
        seen: set[str] = set()
        for raw_s in symbols:
            clean = from_tradexpress_symbol(str(raw_s))
            if clean and clean not in seen:
                seen.add(clean)
                target_symbols.append(clean)
    else:
        with db.read() as session:
            stmt = (
                select(CompanyProfile.symbol)
                .where(
                    or_(
                        CompanyProfile.favorite.is_(True),
                        CompanyProfile.watchlist_category.in_(("GSC", "GSC_L1", "GSC_L2")),
                    )
                )
                .order_by(CompanyProfile.symbol)
            )
            target_symbols = list(session.scalars(stmt).all())

    target_symbols = target_symbols[:40]
    synced_symbols: list[str] = []
    failed_symbols: list[str] = []
    fetched_map: dict[str, list[dict[str, Any]]] = {}

    async with httpx.AsyncClient(timeout=10.0) as client:
        for idx, sym in enumerate(target_symbols):
            bars = await fetch_real_daily_history(sym, sessions=sessions, client=client)
            if bars:
                fetched_map[sym] = bars
                synced_symbols.append(sym)
            else:
                failed_symbols.append(sym)
            if pace_seconds > 0 and idx < len(target_symbols) - 1:
                await asyncio.sleep(pace_seconds)

    if fetched_map:
        with db.write() as session:
            state = portfolio_state(session)
            today_str = state.clock_date.isoformat()
            for sym, bars in fetched_map.items():
                cp = session.get(CompanyProfile, sym)
                if cp is None:
                    continue
                merged_bars = list(bars)
                live_quote = feed.get_cached_quote(sym) if feed else None
                if live_quote and getattr(live_quote, "ltp", ZERO) > ZERO:
                    ltp = live_quote.ltp
                    today_bar = {
                        "date": today_str,
                        "open": f"{(live_quote.open_price if live_quote.open_price > ZERO else ltp):.2f}",
                        "high": f"{(live_quote.high if live_quote.high > ZERO else ltp):.2f}",
                        "low": f"{(live_quote.low if live_quote.low > ZERO else ltp):.2f}",
                        "close": f"{ltp:.2f}",
                        "volume": int(getattr(live_quote, "volume", 0) or 0),
                    }
                    if merged_bars and merged_bars[-1].get("date") == today_str:
                        merged_bars[-1] = today_bar
                    elif not merged_bars or merged_bars[-1].get("date", "") < today_str:
                        merged_bars.append(today_bar)
                    cp.last_price = ltp

                cp.price_history = merged_bars[-sessions:]
                flag_modified(cp, "price_history")
                cp.source = "TRADEXPRESS_LIVE_CURVE"
                try:
                    latest_dt = datetime.strptime(cp.price_history[-1]["date"], "%Y-%m-%d").date()
                    cp.quote_on = latest_dt
                except Exception:
                    cp.quote_on = state.clock_date
            session.flush()

    return {
        "ok": True,
        "total_requested": len(target_symbols),
        "synced_count": len(synced_symbols),
        "failed_symbols": failed_symbols,
        "symbols_updated": synced_symbols,
    }
