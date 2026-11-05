"""Live DSE Quote & 7-30 Day Curve Sync Engine for StockNow.

Extracts live quotes and historical price curves from StockNowLiveClient
(via XHR sniffer cache or active Playwright DOM) and synchronizes them
into SQLite CompanyProfile records.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from backend.database import CompanyProfile, Database, portfolio_state
from backend.engine.money import ZERO, decimal

logger = logging.getLogger("hummingbird.stocknow_sync")


def _parse_positive_decimal(val: Any) -> Decimal | None:
    if val is None:
        return None
    try:
        d = decimal(str(val).replace(",", "").strip())
        if d.is_finite() and d > ZERO:
            return d
    except (InvalidOperation, ValueError, TypeError):
        pass
    return None


def _normalize_history_series(raw_history: Any, fallback_price: Decimal, as_of_date: date) -> list[dict[str, str]]:
    """Normalize 7-30 session curve observations into [{"date": "YYYY-MM-DD", "close": "XX.XX"}]."""
    result: list[dict[str, str]] = []
    if isinstance(raw_history, list):
        for item in raw_history:
            if isinstance(item, dict):
                d_str = str(item.get("date") or item.get("trade_on") or item.get("d") or "")
                c_val = _parse_positive_decimal(item.get("close") or item.get("ltp") or item.get("c") or item.get("price"))
                if d_str and c_val:
                    result.append({"date": d_str, "close": str(c_val)})
            elif isinstance(item, (int, float, str, Decimal)):
                c_val = _parse_positive_decimal(item)
                if c_val:
                    result.append({"date": as_of_date.isoformat(), "close": str(c_val)})

    return result[-30:]


def extract_quotes_from_payload(payload: Any, as_of_date: date | None = None) -> list[dict[str, Any]]:
    """Extract and normalize quotes from an arbitrary JSON payload."""
    as_of = as_of_date or date.today()
    items: list[Any] = []

    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        for key in ("instruments", "data", "quotes", "prices", "items", "rows"):
            if isinstance(payload.get(key), list):
                items = payload[key]
                break
        if not items and ("symbol" in payload or "trading_code" in payload):
            items = [payload]

    extracted: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        sym = (
            item.get("symbol")
            or item.get("trading_code")
            or item.get("code")
            or item.get("ticker")
        )
        if not sym or not isinstance(sym, str):
            continue
        symbol = sym.strip().upper()

        price_val = (
            item.get("ltp")
            or item.get("close")
            or item.get("last_price")
            or item.get("price")
            or item.get("last")
        )
        last_price = _parse_positive_decimal(price_val)
        if not last_price:
            continue

        ycp = _parse_positive_decimal(item.get("ycp") or item.get("prev_close") or item.get("previous_close"))
        raw_change = item.get("change_pct") or item.get("change") or item.get("pChange")
        change_pct = None
        if raw_change is not None:
            try:
                change_pct = decimal(str(raw_change).replace("%", "").strip())
            except Exception:
                pass

        raw_hist = item.get("history") or item.get("series") or item.get("chart") or item.get("price_history")
        history = _normalize_history_series(raw_hist, last_price, as_of)

        extracted.append({
            "symbol": symbol,
            "last_price": last_price,
            "ycp": ycp,
            "change_pct": change_pct,
            "history": history,
            "as_of_date": as_of,
            "source": "STOCKNOW_LIVE",
        })

    return extracted


async def extract_quotes_from_stocknow(client: Any, injected_payload: Any = None) -> list[dict[str, Any]]:
    """Extracts live DSE ticker quotes from sniffer cache, page DOM or injected payload."""
    if injected_payload is not None:
        return extract_quotes_from_payload(injected_payload)

    captured = getattr(client, "captured_endpoints", {})
    if captured:
        for ep, ep_data in captured.items():
            data = ep_data.get("data")
            quotes = extract_quotes_from_payload(data)
            if quotes:
                logger.info("Extracted %d quotes from captured endpoint '%s'", len(quotes), ep)
                return quotes

    page = getattr(client, "page", None)
    if page is not None:
        try:
            dom_data = await page.evaluate("""() => {
                const results = [];
                const win = window;
                if (win.__NEXT_DATA__ && win.__NEXT_DATA__.props) {
                    return win.__NEXT_DATA__.props;
                }
                const rows = document.querySelectorAll("tr, div[class*='row']");
                for (const r of rows) {
                    const text = r.innerText || "";
                    const parts = text.split(/[\\t\\n]+/);
                    if (parts.length >= 2) {
                        const sym = parts[0].trim().toUpperCase();
                        const p = parseFloat(parts[1].replace(/,/g, ''));
                        if (sym.length >= 2 && sym.length <= 12 && !isNaN(p) && p > 0) {
                            results.push({ symbol: sym, ltp: p });
                        }
                    }
                }
                return results;
            }""")
            quotes = extract_quotes_from_payload(dom_data)
            if quotes:
                logger.info("Extracted %d quotes directly from StockNow live page DOM", len(quotes))
                return quotes
        except Exception as exc:
            logger.debug("Page DOM extraction ignored: %s", exc)

    return []


def _sync_in_session(
    session: Any,
    quotes: list[dict[str, Any]],
    session_date: date | None = None,
) -> dict[str, Any]:
    if not quotes:
        return {
            "success": True,
            "synced_count": 0,
            "symbols": [],
            "skipped_count": 0,
            "synced_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }

    synced_symbols: list[str] = []
    skipped_count = 0

    state = portfolio_state(session)
    as_of = session_date or state.clock_date or date.today()

    for q in quotes:
        symbol = q["symbol"].upper()
        company = session.get(CompanyProfile, symbol)
        if company is None:
            skipped_count += 1
            continue

        last_price = q["last_price"]
        company.last_price = last_price
        company.quote_on = q.get("as_of_date") or as_of
        company.source = "STOCKNOW_LIVE"

        provided_hist = q.get("history")
        if provided_hist and len(provided_hist) >= 2:
            hist = list(provided_hist)
            date_str = company.quote_on.isoformat()
            price_str = str(last_price)
            if hist[-1].get("date") != date_str or decimal(hist[-1].get("close")) != last_price:
                hist.append({"date": date_str, "close": price_str})
            company.price_history = hist[-30:]
        else:
            hist = list(company.price_history or [])
            date_str = company.quote_on.isoformat()
            price_str = str(last_price)
            if hist and hist[-1].get("date") == date_str:
                hist[-1] = {"date": date_str, "close": price_str}
            else:
                hist.append({"date": date_str, "close": price_str})
            company.price_history = hist[-30:]

        synced_symbols.append(symbol)

    if synced_symbols:
        state.revision += 1

    return {
        "success": True,
        "synced_count": len(synced_symbols),
        "symbols": synced_symbols,
        "skipped_count": skipped_count,
        "synced_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def sync_live_market_to_db(
    target: Database | Any,
    quotes: list[dict[str, Any]],
    session_date: date | None = None,
) -> dict[str, Any]:
    """Synchronizes extracted live quotes into SQLite CompanyProfile records."""
    if hasattr(target, "write"):
        with target.write() as session:
            return _sync_in_session(session, quotes, session_date)
    return _sync_in_session(target, quotes, session_date)
