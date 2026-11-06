"""Live DSE Quote & 7-30 Day Curve Sync Engine for StockNow.

Extracts live quotes and historical price curves from StockNowLiveClient
(via XHR sniffer cache or active Playwright DOM) and synchronizes them
into SQLite CompanyProfile records.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any
import httpx

from backend.database import CompanyProfile, Database, portfolio_state
from backend.engine.money import ZERO, decimal

logger = logging.getLogger("hummingbird.stocknow_sync")

STOCKNOW_LIST_NAME_TO_CATEGORY: dict[str, str] = {
    "Giant Stable Companies": "GSC",
    "GSC Upper Trends L1": "GSC_L1",
    "GSC Upper Trends L2": "GSC_L2",
    "giant stable companies": "GSC",
    "gsc upper trends l1": "GSC_L1",
    "gsc upper trends l2": "GSC_L2",
}


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


def _extract_fundamentals_from_dict(item: dict[str, Any]) -> dict[str, Any]:
    f: dict[str, Any] = {}
    if "fundamentals" in item and isinstance(item["fundamentals"], dict):
        return dict(item["fundamentals"])
    pe = item.get("pe") or item.get("pe_ratio") or item.get("pe_ttm") or item.get("p_e")
    if pe is not None:
        try:
            f["pe_ratio"] = float(str(pe).replace(",", "").strip())
        except (ValueError, TypeError):
            pass
    eps = item.get("eps") or item.get("eps_ttm")
    if eps is not None:
        try:
            f["eps"] = float(str(eps).replace(",", "").strip())
        except (ValueError, TypeError):
            pass
    nav = item.get("nav") or item.get("navps")
    if nav is not None:
        try:
            f["nav"] = float(str(nav).replace(",", "").strip())
        except (ValueError, TypeError):
            pass
    mcap = item.get("market_cap") or item.get("market_cap_cr") or item.get("mcap")
    if mcap is not None:
        try:
            f["market_cap_cr"] = float(str(mcap).replace(",", "").strip())
        except (ValueError, TypeError):
            pass
    paid = item.get("paid_up_capital") or item.get("paid_up_capital_cr") or item.get("paid_up")
    if paid is not None:
        try:
            f["paid_up_capital_cr"] = float(str(paid).replace(",", "").strip())
        except (ValueError, TypeError):
            pass
    div = item.get("dividend_yield") or item.get("div_yield")
    if div is not None:
        try:
            f["dividend_yield"] = float(str(div).replace("%", "").replace(",", "").strip())
        except (ValueError, TypeError):
            pass
    h52 = item.get("high_52w") or item.get("52w_high") or item.get("high52")
    if h52 is not None:
        try:
            f["high_52w"] = float(str(h52).replace(",", "").strip())
        except (ValueError, TypeError):
            pass
    l52 = item.get("low_52w") or item.get("52w_low") or item.get("low52")
    if l52 is not None:
        try:
            f["low_52w"] = float(str(l52).replace(",", "").strip())
        except (ValueError, TypeError):
            pass
    cat = item.get("category") or item.get("market_category")
    if cat is not None and isinstance(cat, str):
        f["category"] = cat.strip().upper()
    year = item.get("listing_year") or item.get("year")
    if year is not None:
        try:
            f["listing_year"] = int(str(year).strip())
        except (ValueError, TypeError):
            pass
    return f


def extract_quotes_from_payload(payload: Any, as_of_date: date | None = None) -> list[dict[str, Any]]:
    """Extract and normalize quotes from an arbitrary JSON payload."""
    as_of = as_of_date or date.today()
    items: list[Any] = []

    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        if isinstance(payload.get("watchlist"), list):
            items = payload["watchlist"]
            active_sym = payload.get("active_symbol")
            active_funds = payload.get("fundamentals") or {}
            for it in items:
                if isinstance(it, dict) and active_sym and it.get("symbol", "").upper() == active_sym:
                    it["fundamentals"] = active_funds
        else:
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
        funds = _extract_fundamentals_from_dict(item)

        quote_dict: dict[str, Any] = {
            "symbol": symbol,
            "last_price": last_price,
            "ycp": ycp,
            "change_pct": change_pct,
            "history": history,
            "as_of_date": as_of,
            "source": "STOCKNOW_LIVE",
        }
        if funds:
            quote_dict["fundamentals"] = funds
        cat = item.get("category") or (funds.get("category") if funds else None)
        if cat:
            quote_dict["category"] = str(cat).strip().upper()

        # Handle 3-list watchlist category mapping
        w_cat = item.get("watchlist_category")
        if not w_cat and str(cat) in ("GSC", "GSC_L1", "GSC_L2"):
            w_cat = str(cat)
        if not w_cat and item.get("list_name") in STOCKNOW_LIST_NAME_TO_CATEGORY:
            w_cat = STOCKNOW_LIST_NAME_TO_CATEGORY[item["list_name"]]
        if w_cat:
            quote_dict["watchlist_category"] = w_cat

        extracted.append(quote_dict)

    return extracted


_ALL_DSE_SHARES_CACHE: list[dict[str, Any]] = []
_ALL_DSE_SHARES_UPDATED_AT: str | None = None
_SECTOR_MAP_CACHE: dict[int, str] = {}


async def fetch_stocknow_live_market_data(client: Any = None) -> list[dict[str, Any]]:
    """Fetches real-time market data directly from stocknow.com.bd API.

    1. Fetches all DSE instruments (473 stocks) and sector definitions.
    2. Builds and caches the All DSE Shares catalog with LTP, +/- %, and sparklines.
    3. Resolves user favorite lists (GSC, GSC_L1, GSC_L2) from browser session if available.
    4. Concurrently pulls real multi-session candlestick curves for favorite companies.
    5. Returns normalized quote objects ready for SQLite database synchronization.
    """
    global _ALL_DSE_SHARES_CACHE, _ALL_DSE_SHARES_UPDATED_AT, _SECTOR_MAP_CACHE

    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    user_lists = None

    # Step 1: Check if live client has active page and auth token
    page = getattr(client, "page", None)
    if page is not None and not (hasattr(page, "is_closed") and page.is_closed()):
        try:
            lists_res = await page.evaluate("""async () => {
                try {
                    const token = localStorage.getItem('access_token');
                    if (!token) return null;
                    const r = await fetch('https://stocknow.com.bd/api/v1/user/lists', {
                        headers: { 'Authorization': 'Bearer ' + token }
                    });
                    if (r.ok) return await r.json();
                } catch (e) {}
                return null;
            }""")
            if isinstance(lists_res, list) and len(lists_res) > 0:
                user_lists = lists_res
        except Exception as exc:
            logger.debug("Failed evaluating user/lists from browser: %s", exc)

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    async with httpx.AsyncClient(headers=headers, timeout=20.0) as http:
        # Step 2: Fetch all instruments and sectors
        try:
            r_inst, r_sec = await asyncio.gather(
                http.get("https://stocknow.com.bd/api/v1/instruments"),
                http.get("https://stocknow.com.bd/api/v1/sectors"),
                return_exceptions=True
            )
            raw_inst = r_inst.json() if not isinstance(r_inst, Exception) and getattr(r_inst, "status_code", 0) == 200 else {}
            raw_sec = r_sec.json() if not isinstance(r_sec, Exception) and getattr(r_sec, "status_code", 0) == 200 else {}
        except Exception as net_exc:
            logger.warning("Failed fetching instruments/sectors: %s", net_exc)
            raw_inst, raw_sec = {}, {}

        if raw_sec and isinstance(raw_sec, dict):
            for k, v in raw_sec.items():
                try:
                    _SECTOR_MAP_CACHE[int(k)] = v.get("name", "Other")
                except Exception:
                    pass

        # Step 3: Format All DSE Shares catalog
        formatted_shares = []
        if raw_inst and isinstance(raw_inst, dict):
            for code, item in raw_inst.items():
                if not isinstance(item, dict):
                    continue
                ltp = float(item.get("close") or item.get("ycp") or 0.0)
                ycp = float(item.get("ycp") or ltp)
                chg = round(ltp - ycp, 2)
                chg_pct = round(((ltp - ycp) / ycp) * 100, 2) if ycp > 0 else 0.0

                spk_raw = [
                    item.get("365d"), item.get("180d"), item.get("90d"),
                    item.get("30d"), item.get("15d"), item.get("7d"), ltp
                ]
                sparkline = [float(p) for p in spk_raw if p is not None and float(p) > 0]
                if len(sparkline) < 2:
                    sparkline = [ycp, ltp] if ycp > 0 and ltp > 0 else [ltp, ltp]

                formatted_shares.append({
                    "symbol": code.strip().upper(),
                    "name": item.get("name") or code,
                    "sector": _SECTOR_MAP_CACHE.get(item.get("sector_id"), "Other"),
                    "category": (item.get("category") or "A").strip().upper(),
                    "ltp": ltp,
                    "ycp": ycp,
                    "change": chg,
                    "change_pct": chg_pct,
                    "volume": int(item.get("volume") or 0),
                    "value_cr": round(float(item.get("value") or 0.0), 2),
                    "trades": int(item.get("trades") or 0),
                    "high": float(item.get("high") or ltp),
                    "low": float(item.get("low") or ltp),
                    "sparkline": sparkline,
                })

            _ALL_DSE_SHARES_CACHE = sorted(formatted_shares, key=lambda s: s["value_cr"], reverse=True)
            _ALL_DSE_SHARES_UPDATED_AT = now_iso

        # Step 4: Resolve Favorite Lists
        fav_categories: dict[str, str] = {}
        if user_lists:
            for l in user_lists:
                name = l.get("name", "")
                cat_code = STOCKNOW_LIST_NAME_TO_CATEGORY.get(name, "GSC")
                for it in l.get("items", []):
                    c = it.get("code")
                    if c:
                        sym_u = c.strip().upper()
                        if sym_u not in fav_categories or cat_code in ("GSC_L1", "GSC_L2"):
                            fav_categories[sym_u] = cat_code
        else:
            # Verified default 3 favorite lists
            for s in ['ACI', 'BANKASIA', 'DHAKABANK', 'FUWANGCER', 'IFIC', 'NPOLYMER', 'PRIMEBANK', 'PUBALIBANK', 'SPCERAMICS', 'IBNSINA']:
                fav_categories[s] = "GSC"
            for s in ['BANKASIA', 'MATINSPINN']:
                fav_categories[s] = "GSC_L1"
            for s in ['DHAKABANK']:
                fav_categories[s] = "GSC_L2"

        # Step 5: Concurrently pull real 30-session history for all favorite symbols
        symbols_to_pull = list(fav_categories.keys())

        async def fetch_hist(sym: str) -> tuple[str, list[dict[str, str]]]:
            url = f"https://stocknow.com.bd/api/v1/instruments/{sym}/history?data2=true&resolution=1D&skip=0"
            try:
                r = await http.get(url, timeout=10.0)
                if r.status_code == 200:
                    d = r.json()
                    if isinstance(d, list) and len(d) >= 6 and len(d[3]) > 0:
                        closes = d[3][-30:]
                        ts_list = d[5][-30:]
                        points = [
                            {"date": datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat(), "close": str(c)}
                            for c, ts in zip(closes, ts_list)
                        ]
                        return sym, points
            except Exception as e:
                logger.debug("Failed fetching history for %s: %s", sym, e)
            return sym, []

        hist_tuples = await asyncio.gather(*[fetch_hist(s) for s in symbols_to_pull])
        hist_map = dict(hist_tuples)

        # Step 6: Construct normalized quotes
        today = date.today()
        quotes: list[dict[str, Any]] = []
        for sym, cat_code in fav_categories.items():
            inst_data = raw_inst.get(sym, {})
            ltp_f = float(inst_data.get("close") or inst_data.get("ycp") or 0.0)
            if ltp_f <= 0:
                continue
            ycp_f = float(inst_data.get("ycp") or ltp_f)
            chg_pct = round(((ltp_f - ycp_f) / ycp_f) * 100, 2) if ycp_f > 0 else 0.0

            history = hist_map.get(sym, [])
            if not history:
                spk_raw = [inst_data.get("30d"), inst_data.get("15d"), inst_data.get("7d"), ltp_f]
                history = [{"date": today.isoformat(), "close": str(p)} for p in spk_raw if p and float(p) > 0]

            quote_dict = {
                "symbol": sym,
                "name": inst_data.get("name") or sym,
                "sector": _SECTOR_MAP_CACHE.get(inst_data.get("sector_id"), "OTHER"),
                "category": (inst_data.get("category") or "A").strip().upper(),
                "watchlist_category": cat_code,
                "last_price": Decimal(str(ltp_f)),
                "ycp": Decimal(str(ycp_f)),
                "change_pct": Decimal(str(chg_pct)),
                "history": history,
                "as_of_date": today,
                "source": "STOCKNOW_LIVE",
            }
            quotes.append(quote_dict)

        return quotes


async def get_or_fetch_all_dse_shares(client: Any = None) -> dict[str, Any]:
    """Returns cached All DSE Shares catalog, populating it if not yet loaded."""
    global _ALL_DSE_SHARES_CACHE, _ALL_DSE_SHARES_UPDATED_AT
    if not _ALL_DSE_SHARES_CACHE:
        try:
            await fetch_stocknow_live_market_data(client=client)
        except Exception as exc:
            logger.warning("Auto-fetch all DSE shares failed: %s", exc)
    return {
        "total": len(_ALL_DSE_SHARES_CACHE),
        "updated_at": _ALL_DSE_SHARES_UPDATED_AT or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "shares": _ALL_DSE_SHARES_CACHE,
    }


async def extract_quotes_from_stocknow(client: Any, injected_payload: Any = None) -> list[dict[str, Any]]:
    """Extracts live DSE ticker quotes from sniffer cache, page DOM or injected payload."""
    from backend.adapters.stocknow_client import StockNowLiveClient
    if isinstance(client, StockNowLiveClient) and hasattr(client, "_run_in_proactor"):
        return await client._run_in_proactor(_extract_quotes_from_stocknow_impl(client, injected_payload))
    return await _extract_quotes_from_stocknow_impl(client, injected_payload)


async def _extract_quotes_from_stocknow_impl(client: Any, injected_payload: Any = None) -> list[dict[str, Any]]:
    if injected_payload is not None:
        return extract_quotes_from_payload(injected_payload)

    # 1. Primary path: real-time StockNow API engine with real 30-session curves & all shares
    try:
        quotes = await fetch_stocknow_live_market_data(client=client)
        if quotes:
            logger.info("Extracted %d live quotes via StockNow API engine", len(quotes))
            return quotes
    except Exception as exc:
        logger.warning("fetch_stocknow_live_market_data failed, trying sniffer fallbacks: %s", exc)

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
            current_url = getattr(page, "url", "")
            if "favorites" not in current_url:
                try:
                    await page.goto("https://www.stocknow.com.bd/favorites", timeout=15000, wait_until="domcontentloaded")
                    await page.wait_for_timeout(1000)
                except Exception as nav_exc:
                    logger.debug("Navigation to favorites: %s", nav_exc)
            dom_data = await page.evaluate(r"""() => {
                const results = [];
                const win = window;
                if (win.__NEXT_DATA__ && win.__NEXT_DATA__.props) {
                    return win.__NEXT_DATA__.props;
                }

                // 1. Scrape center panel active symbol & fundamentals
                let activeSym = null;
                try {
                    const params = new URLSearchParams(win.location ? win.location.search : "");
                    if (params.get("symbol")) activeSym = params.get("symbol").toUpperCase();
                } catch(e) {}

                const fullText = document.body ? document.body.innerText : "";
                const funds = {};

                const peMatch = fullText.match(/P\/E\\s*(?:\\(TTM\\))?[:\\s]+([0-9.]+)/i);
                if (peMatch) funds.pe_ratio = parseFloat(peMatch[1]);

                const epsMatch = fullText.match(/EPS\\s*(?:\\(TTM\\))?[:\\s]+([0-9.-]+)/i);
                if (epsMatch) funds.eps = parseFloat(epsMatch[1]);

                const navMatch = fullText.match(/NAV(?:PS)?[:\\s]+([0-9.]+)/i);
                if (navMatch) funds.nav = parseFloat(navMatch[1]);

                const mcapMatch = fullText.match(/Market\\s*Cap[:\\s]+([0-9.,]+)\\s*(?:cr|crore)?/i);
                if (mcapMatch) funds.market_cap_cr = parseFloat(mcapMatch[1].replace(/,/g, ''));

                const paidMatch = fullText.match(/Paid[- ]?up\\s*Cap(?:ital)?[:\\s]+([0-9.,]+)\\s*(?:cr|crore)?/i);
                if (paidMatch) funds.paid_up_capital_cr = parseFloat(paidMatch[1].replace(/,/g, ''));

                const divMatch = fullText.match(/Div(?:idend)?\\s*Yield[:\\s]+([0-9.]+)%/i);
                if (divMatch) funds.dividend_yield = parseFloat(divMatch[1]);

                const h52Match = fullText.match(/52W\\s*H(?:igh)?[:\\s]+(?:৳|Tk\\.?)?\\s*([0-9.]+)/i);
                if (h52Match) funds.high_52w = parseFloat(h52Match[1]);

                const l52Match = fullText.match(/52W\\s*L(?:ow)?[:\\s]+(?:৳|Tk\\.?)?\\s*([0-9.]+)/i);
                if (l52Match) funds.low_52w = parseFloat(l52Match[1]);

                const range52Match = fullText.match(/52W\\s*Range[:\\s]+(?:৳|Tk\\.?)?\\s*([0-9.]+)\\s*[—–-]\\s*(?:৳|Tk\\.?)?\\s*([0-9.]+)/i);
                if (range52Match) {
                    funds.low_52w = parseFloat(range52Match[1]);
                    funds.high_52w = parseFloat(range52Match[2]);
                }

                const catMatch = fullText.match(/Category\\s*([A-Z])/i);
                if (catMatch) funds.category = catMatch[1].toUpperCase();

                const yearMatch = fullText.match(/Listing\\s*Year[:\\s]+([12][0-9]{3})/i);
                if (yearMatch) funds.listing_year = parseInt(yearMatch[1], 10);

                let currentListName = null;
                const candidates = Array.from(document.querySelectorAll("select, div, button, span, [class*='list'], [class*='dropdown']"));
                for (const el of candidates) {
                    const txt = (el.innerText || el.value || "").trim();
                    if (txt.includes("GSC Upper Trends L1")) { currentListName = "GSC_L1"; break; }
                    if (txt.includes("GSC Upper Trends L2")) { currentListName = "GSC_L2"; break; }
                    if (txt.includes("Giant Stable Companies")) { currentListName = "GSC"; break; }
                }

                // 2. Scrape right-hand watchlist rows
                const rows = document.querySelectorAll("tr, div[class*='row'], div[class*='item']");
                const seen = new Set();
                for (const r of rows) {
                    const text = r.innerText || "";
                    const parts = text.split(/[\\t\\n]+/).map(s => s.trim()).filter(Boolean);
                    if (parts.length < 2) continue;

                    let sym = null;
                    let ltp = null;
                    let changePct = null;
                    let cat = null;

                    for (const p of parts) {
                        if (!sym && /^[A-Z0-9]{2,12}$/.test(p) && !["BUY", "SELL", "LTP", "YCP", "HIGH", "LOW", "VOL", "CLOSE", "CHANGE"].includes(p)) {
                            sym = p;
                        }
                        if (/^\\[?([ABZN])\\]?$/.test(p)) {
                            cat = p.replace(/[\\[\\]]/g, '');
                        }
                        const val = parseFloat(p.replace(/,/g, ''));
                        if (!isNaN(val) && val > 0 && val < 50000) {
                            if (ltp === null && p.includes('.')) {
                                ltp = val;
                            }
                        }
                        if (p.includes('%')) {
                            const cp = parseFloat(p.replace(/[%+,\\s]/g, ''));
                            if (!isNaN(cp)) {
                                changePct = (p.includes('-') ? -1 : 1) * Math.abs(cp);
                            }
                        }
                    }

                    if (sym && ltp !== null && !seen.has(sym)) {
                        seen.add(sym);
                        const item = { symbol: sym, ltp: ltp, change_pct: changePct, category: cat };
                        if (currentListName) {
                            item.watchlist_category = currentListName;
                        }
                        if (activeSym && sym === activeSym && Object.keys(funds).length > 0) {
                            item.fundamentals = funds;
                        }
                        results.push(item);
                    }
                }

                // 3. Fallback for active symbol if not in table
                if (activeSym && !seen.has(activeSym)) {
                    const ltpMatch = fullText.match(/(?:LTP|Price|Last)[:\\s]+(?:৳|Tk\\.?)?\\s*([0-9.]+)/i);
                    if (ltpMatch) {
                        results.push({
                            symbol: activeSym,
                            ltp: parseFloat(ltpMatch[1]),
                            fundamentals: funds,
                        });
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
        last_price = q["last_price"]

        if company is None:
            # Auto-create company profile from live market feed
            from backend.database import CustomRule
            company = CompanyProfile(
                symbol=symbol,
                name=q.get("name") or f"{symbol} · StockNow",
                sector=q.get("sector") or "DSE",
                watchlist_category=q.get("watchlist_category") or q.get("category", "GSC"),
                settlement_days=2,
                last_price=last_price,
                price_history=[{"date": (q.get("as_of_date") or as_of).isoformat(), "close": str(last_price)}],
                quote_on=q.get("as_of_date") or as_of,
                source="STOCKNOW_LIVE",
            )
            session.add(company)
            session.flush()
            rule = session.get(CustomRule, symbol)
            if rule is None:
                session.add(CustomRule(symbol=symbol, buy_allocation_pct=ZERO))

        if q.get("name") and (company.name.endswith(" · StockNow") or not company.name):
            company.name = q["name"]
        if q.get("sector") and company.sector in ("DSE", "OTHER", "Other"):
            company.sector = q["sector"]

        company.last_price = last_price
        company.quote_on = q.get("as_of_date") or as_of
        company.source = "STOCKNOW_LIVE"

        target_cat = q.get("watchlist_category") or (q.get("category") if q.get("category") in ("GSC", "GSC_L1", "GSC_L2") else None)
        if target_cat:
            company.watchlist_category = target_cat

        # Update in-memory fundamentals if provided
        if q.get("fundamentals"):
            try:
                from backend.portfolio import COMPANY_FUNDAMENTALS, DEFAULT_FUNDAMENTALS
                base_f = dict(COMPANY_FUNDAMENTALS.get(symbol, DEFAULT_FUNDAMENTALS))
                base_f.update(q["fundamentals"])
                COMPANY_FUNDAMENTALS[symbol] = base_f
            except Exception as f_exc:
                logger.debug("Failed updating fundamentals for %s: %s", symbol, f_exc)

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
