"""Extraction and T+2 ledger reconciliation for StockNow virtual portfolio."""

from __future__ import annotations

import logging
import os
import re
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import Settings, get_allowed_portfolios, get_portfolio_name
from backend.database import CompanyProfile, CustomRule, Database, DecisionLog, PortfolioState, TaxLot, TradeLog
from backend.engine.money import decimal, money, price, purchase_amount
from backend.engine.t2_ledger import BUCKETS, TradingCalendar, assert_ledger, bucket_balances

logger = logging.getLogger(__name__)


def parse_stocknow_ledger_date(date_str: str) -> str:
    """Parse StockNow DD/MM/YY date string into YYYY-MM-DD ISO date."""
    if not date_str:
        return ""
    clean = str(date_str).strip()
    m = re.match(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})$", clean)
    if m:
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if year < 100:
            year += 2000
        return f"{year:04d}-{month:02d}-{day:02d}"
    try:
        dt = datetime.strptime(clean, "%d/%m/%y")
        return dt.date().isoformat()
    except Exception:
        pass
    try:
        dt = datetime.fromisoformat(clean)
        return dt.date().isoformat()
    except Exception:
        pass
    return clean


def _match_portfolio_name(name: str) -> bool:
    return "hummingbird" in (name or "").strip().lower().replace(" ", "").replace("_", "").replace("-", "")


def _find_portfolio_dict(data: Any) -> dict[str, Any] | None:
    if isinstance(data, dict):
        if _match_portfolio_name(data.get("name") or data.get("portfolio_name") or ""):
            return data
        for key in ("portfolios", "data", "items", "results"):
            sub = data.get(key)
            if isinstance(sub, list):
                found = _find_portfolio_dict(sub)
                if found:
                    return found
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and _match_portfolio_name(item.get("name") or item.get("portfolio_name") or ""):
                return item
        if len(data) == 1 and isinstance(data[0], dict):
            return data[0]
    return None


def extract_hummingbird_portfolio(
    client: Any | None = None,
    injected_portfolio: dict[str, Any] | list[Any] | None = None,
) -> dict[str, Any]:
    """Locate and extract 'Humming Bird' virtual portfolio from client or payload."""
    raw_p = _find_portfolio_dict(injected_portfolio) if injected_portfolio is not None else None
    if not raw_p and isinstance(injected_portfolio, dict):
        raw_p = injected_portfolio
    source = "INJECTED" if raw_p else "CAPTURED_ENDPOINT"

    if not raw_p and client is not None and getattr(client, "captured_endpoints", None):
        for _ep, ep_data in client.captured_endpoints.items():
            found = _find_portfolio_dict(ep_data.get("data"))
            if found:
                raw_p = found
                break

    if not raw_p:
        raise ValueError("Could not locate virtual portfolio 'Humming Bird' in StockNow session.")

    p_id = str(raw_p.get("portfolio_id") or raw_p.get("id") or "164580")
    p_name = str(raw_p.get("portfolio_name") or raw_p.get("name") or "Humming Bird")
    cash_val = (
        raw_p.get("cash_amount")
        if raw_p.get("cash_amount") is not None
        else (raw_p.get("cash_balance") or raw_p.get("cash") or raw_p.get("available_cash", 0))
    )

    raw_holdings = (
        raw_p.get("scrips")
        or raw_p.get("holdings")
        or raw_p.get("stocks")
        or raw_p.get("items")
        or []
    )
    raw_ledger = raw_p.get("ledger") or raw_p.get("transactions") or []
    buy_date_map: dict[str, str] = {}
    for entry in raw_ledger:
        if isinstance(entry, dict):
            entry_type = str(entry.get("type") or entry.get("side") or entry.get("action") or "").upper()
            if "BUY" in entry_type or not entry_type:
                sym_raw = str(entry.get("symbol") or entry.get("description") or entry.get("code") or "").upper().strip()
                date_val = entry.get("date") or entry.get("trade_on") or entry.get("trade_date") or entry.get("created_at")
                if sym_raw and date_val:
                    d_iso = parse_stocknow_ledger_date(str(date_val))
                    if d_iso and sym_raw not in buy_date_map:
                        buy_date_map[sym_raw] = d_iso

    holdings: list[dict[str, Any]] = []
    for h in raw_holdings:
        if not isinstance(h, dict):
            continue
        sym = str(h.get("symbol") or h.get("ticker") or h.get("code") or h.get("instrument_id") or "").strip().upper()
        qty = int(h.get("quantity") or h.get("qty") or h.get("shares") or h.get("no_of_shares") or 0)
        avg = decimal(h.get("avg_cost") or h.get("average_cost") or h.get("buy_price") or h.get("buying_price") or h.get("rate") or 0)
        raw_acq = str(h.get("acquired_date") or h.get("date") or h.get("buy_date") or h.get("buying_date") or "")
        acq_date = parse_stocknow_ledger_date(raw_acq) if raw_acq else buy_date_map.get(sym)

        if sym and qty > 0 and avg > Decimal("0"):
            holdings.append({
                "symbol": sym, "quantity": qty, "avg_cost": avg,
                "acquired_date": acq_date,
                "bucket": h.get("bucket"), "name": h.get("name") or sym, "sector": h.get("sector") or "OTHER",
            })

    return {
        "portfolio_id": p_id, "portfolio_name": p_name,
        "cash_balance": decimal(cash_val), "holdings": holdings, "source": source,
    }


async def extract_hummingbird_portfolio_from_browser(client: Any) -> dict[str, Any]:
    """Scrapes /portfolios/{id}/show and /portfolios/{id}/ledger from live Playwright session."""
    from backend.adapters.stocknow_client import StockNowLiveClient
    if isinstance(client, StockNowLiveClient) and hasattr(client, "_run_in_proactor"):
        return await client._run_in_proactor(_extract_hummingbird_portfolio_from_browser_impl(client))
    return await _extract_hummingbird_portfolio_from_browser_impl(client)


async def _extract_hummingbird_portfolio_from_browser_impl(client: Any) -> dict[str, Any]:
    p_id = str(getattr(client, "bound_portfolio_id", None) or os.getenv("STOCKNOW_LIVE_PORTFOLIO_ID", "164580"))
    page = getattr(client, "page", None)
    if not page:
        raise RuntimeError("No active Playwright page in StockNowLiveClient.")

    # 1. Scrape /show
    show_url = f"https://www.stocknow.com.bd/portfolios/{p_id}/show"
    try:
        await page.goto(show_url, timeout=15000, wait_until="domcontentloaded")
        await page.wait_for_timeout(1000)
    except Exception as exc:
        logger.debug("Navigation to %s: %s", show_url, exc)

    show_data = await page.evaluate(r"""() => {
        const fullText = document.body ? document.body.innerText : "";
        let cash = 0.0;
        const cashM = fullText.match(/Cash[\s\S]{0,25}?([0-9,]{4,})/i);
        if (cashM) cash = parseFloat(cashM[1].replace(/,/g, ''));

        const holdings = [];
        const seen = new Set();

        // 1. Match from full text lines
        const re = /([A-Z0-9]{3,12})\s*[\r\n]+\s*(\d+)\s*@\s*([0-9.]+)\s*[\r\n]+\s*([0-9.]+)/g;
        let m;
        while ((m = re.exec(fullText)) !== null) {
            const sym = m[1].toUpperCase();
            if (!seen.has(sym) && !["TOTAL", "CASH", "LTP", "SHOW", "EDIT", "BUY", "SELL"].includes(sym)) {
                seen.add(sym);
                holdings.push({
                    symbol: sym,
                    quantity: parseInt(m[2], 10),
                    avg_cost: parseFloat(m[3]),
                    ltp: parseFloat(m[4]),
                    name: sym,
                });
            }
        }

        // 2. Also fallback to rows if fullText regex didn't catch
        if (holdings.length === 0) {
            const rows = document.querySelectorAll("tr, div[class*='row']");
            for (const r of rows) {
                const txt = r.innerText || "";
                const parts = txt.split(/[\t\n]+/).map(s => s.trim()).filter(Boolean);
                if (parts.length < 3) continue;
                let sym = null;
                let qty = 0;
                let buyPrice = 0;
                for (const p of parts) {
                    if (!sym && /^[A-Z0-9]{3,12}$/.test(p) && !["TOTAL", "CASH", "LTP", "SHOW", "EDIT", "BUY", "SELL"].includes(p)) {
                        sym = p;
                    }
                    const qtyAt = p.match(/(\d+)\s*@\s*([0-9.]+)/);
                    if (qtyAt) {
                        qty = parseInt(qtyAt[1], 10);
                        buyPrice = parseFloat(qtyAt[2]);
                    }
                }
                if (sym && qty > 0 && buyPrice > 0 && !seen.has(sym)) {
                    seen.add(sym);
                    holdings.push({
                        symbol: sym,
                        quantity: qty,
                        avg_cost: buyPrice,
                        name: sym,
                    });
                }
            }
        }
        return { cash: cash, holdings: holdings };
    }""")

    # 2. Scrape /ledger
    ledger_url = f"https://www.stocknow.com.bd/portfolios/{p_id}/ledger"
    try:
        await page.goto(ledger_url, timeout=15000, wait_until="domcontentloaded")
        await page.wait_for_timeout(1000)
        ledger_data = await page.evaluate(r"""() => {
            const rows = document.querySelectorAll("tr");
            const entries = [];
            for (const r of rows) {
                const cells = Array.from(r.querySelectorAll("td, th")).map(c => (c.innerText || "").trim());
                if (cells.length >= 4) entries.push(cells);
            }
            return entries;
        }""")
    except Exception as led_err:
        logger.debug("Ledger page scrape error: %s", led_err)
        ledger_data = []

    buy_date_map: dict[str, str] = {}
    for row in ledger_data:
        row_str = " ".join(row).upper()
        if "BUY" in row_str:
            for item in row:
                d_str = parse_stocknow_ledger_date(item)
                if re.match(r"^\d{4}-\d{2}-\d{2}$", d_str):
                    for sym in ("BANKASIA", "IBNSINA", "MATINSPINN"):
                        if sym in row_str and sym not in buy_date_map:
                            buy_date_map[sym] = d_str

    holdings = []
    for h in show_data.get("holdings", []):
        sym = h["symbol"]
        acq_date = buy_date_map.get(sym, "2026-11-02")
        holdings.append({
            "symbol": sym,
            "quantity": h["quantity"],
            "avg_cost": decimal(str(h["avg_cost"])),
            "acquired_date": acq_date,
            "name": sym,
            "sector": "OTHER",
        })

    return {
        "portfolio_id": p_id,
        "portfolio_name": get_portfolio_name(p_id),
        "cash_balance": decimal(str(show_data.get("cash", 0.0))),
        "holdings": holdings,
        "source": "STOCKNOW_LIVE_DOM",
    }


def _execute_reconciliation(
    session: Session, settings: Settings, portfolio_data: dict[str, Any], checkpoint_mgr: Any = None
) -> dict[str, Any]:
    state = session.get(PortfolioState, 1)
    if not state:
        raise RuntimeError("Demo database is not initialized.")

    if "holdings" not in portfolio_data and (
        "scrips" in portfolio_data or "cash_amount" in portfolio_data or "id" in portfolio_data
    ):
        portfolio_data = extract_hummingbird_portfolio(injected_portfolio=portfolio_data)

    target_pid = str(portfolio_data.get("portfolio_id") or settings.stocknow_live_portfolio_id)
    allowed = get_allowed_portfolios(settings)
    is_scoped = target_pid in allowed

    if is_scoped:
        existing_lots = session.scalars(select(TaxLot).where(TaxLot.portfolio_id == target_pid)).all()
        existing_trades = session.scalars(select(TradeLog).where(TradeLog.portfolio_id == target_pid)).all()
    else:
        existing_lots = session.scalars(select(TaxLot)).all()
        existing_trades = session.scalars(select(TradeLog)).all()

    old_holdings_map: dict[str, int] = {}
    for l in existing_lots:
        old_holdings_map[l.symbol] = old_holdings_map.get(l.symbol, 0) + l.remaining_qty

    old_balances = bucket_balances(session, state, portfolio_id=target_pid)
    old_cash = sum((b.available_cash for b in old_balances.values()), Decimal("0"))

    lots_snap = [{
        "id": l.id, "symbol": l.symbol, "bucket": l.bucket, "acquired_on": l.acquired_on.isoformat(),
        "matures_on": l.matures_on.isoformat(), "original_qty": l.original_qty, "remaining_qty": l.remaining_qty,
        "buy_price": str(l.buy_price), "buy_fee": str(l.buy_fee), "original_cost_basis": str(l.original_cost_basis),
        "remaining_cost_basis": str(l.remaining_cost_basis), "cycle_base_qty": l.cycle_base_qty,
        "next_tier": l.next_tier, "last_sale_revision": l.last_sale_revision, "peak_price": str(l.peak_price),
        "phase": l.phase, "recovery_anchor": str(l.recovery_anchor) if l.recovery_anchor else None,
    } for l in existing_lots]

    trades_snap = [{
        "id": t.id, "trade_key": t.trade_key, "cycle_id": t.cycle_id, "lot_id": t.lot_id, "symbol": t.symbol,
        "side": t.side, "quantity": t.quantity, "price": str(t.price), "gross_amount": str(t.gross_amount),
        "fee": str(t.fee), "net_cash_change": str(t.net_cash_change), "realized_pnl": str(t.realized_pnl),
        "bucket": t.bucket, "trade_on": t.trade_on.isoformat(), "settles_on": t.settles_on.isoformat(),
        "reason": t.reason, "source": t.source,
    } for t in existing_trades]

    tier_cache = {l.symbol: {
        "next_tier": l.next_tier, "peak_price": l.peak_price, "phase": l.phase,
        "recovery_anchor": l.recovery_anchor, "cycle_base_qty": l.cycle_base_qty,
    } for l in existing_lots}

    if checkpoint_mgr is None:
        from backend.engine.checkpoint import CheckpointManager
        checkpoint_mgr = CheckpointManager

    cp = checkpoint_mgr.create_checkpoint(
        session=session, state=state, action="PORTFOLIO_SYNC",
        description=f"Synchronized virtual portfolio '{portfolio_data.get('portfolio_name') or get_portfolio_name(target_pid, settings)}' from StockNow",
        diff_payload={"portfolio_lots": lots_snap, "portfolio_trades": trades_snap, "initial_capital": str(state.initial_capital)},
        extra_snapshot={"portfolio_lots": lots_snap, "portfolio_trades": trades_snap, "initial_capital": str(state.initial_capital)},
    )

    if is_scoped:
        lot_ids = [l.id for l in existing_lots]
        if lot_ids:
            session.query(DecisionLog).filter(DecisionLog.lot_id.in_(lot_ids)).update({"lot_id": None}, synchronize_session=False)
        session.query(TradeLog).filter(TradeLog.portfolio_id == target_pid).delete()
        session.query(TaxLot).filter(TaxLot.portfolio_id == target_pid).delete()
    else:
        session.query(TradeLog).delete()
        session.query(DecisionLog).update({"lot_id": None})
        session.query(TaxLot).delete()
    session.flush()

    calendar = TradingCalendar(settings.holidays, settings.bucket_anchor)
    today = state.clock_date
    created_lots: list[TaxLot] = []
    bucket_spends: dict[str, Decimal] = {"A": Decimal("0"), "B": Decimal("0"), "C": Decimal("0")}

    for holding in portfolio_data.get("holdings", []):
        sym = holding["symbol"]
        qty = int(holding.get("quantity") or holding.get("shares") or 0)
        avg_cost = Decimal(str(holding["avg_cost"]))
        if not session.get(CompanyProfile, sym):
            session.add(CompanyProfile(
                symbol=sym, name=holding.get("name") or sym, sector=holding.get("sector") or "OTHER",
                watchlist_category="GSC", settlement_days=settings.settlement_days, last_price=price(avg_cost),
                price_history=[{"date": today.isoformat(), "close": str(price(avg_cost))}], quote_on=today, source="STOCKNOW_LIVE",
            ))
        if not session.get(CustomRule, sym):
            session.add(CustomRule(symbol=sym, buy_allocation_pct=Decimal("15")))
        session.flush()

        acq_str = holding.get("acquired_date")
        try:
            acq_date = date.fromisoformat(acq_str) if acq_str else today
        except ValueError:
            acq_date = today
        matures_date = calendar.add_sessions(acq_date, settings.settlement_days)
        bucket = holding.get("bucket") if holding.get("bucket") in BUCKETS else min(bucket_spends, key=bucket_spends.get)

        cost, fee = purchase_amount(qty, avg_cost, settings.buy_fee_rate)
        bucket_spends[bucket] += cost

        prev = tier_cache.get(sym, {})
        lot = TaxLot(
            portfolio_id=target_pid,
            symbol=sym, bucket=bucket, acquired_on=acq_date, matures_on=matures_date,
            original_qty=qty, remaining_qty=qty, buy_price=price(avg_cost), buy_fee=fee,
            original_cost_basis=cost, remaining_cost_basis=cost,
            cycle_base_qty=prev.get("cycle_base_qty", qty), next_tier=prev.get("next_tier", 0),
            peak_price=max(prev.get("peak_price", avg_cost), avg_cost), phase=prev.get("phase", "ACTIVE"),
            recovery_anchor=prev.get("recovery_anchor"),
        )
        session.add(lot)
        session.flush()

        session.add(TradeLog(
            portfolio_id=target_pid,
            trade_key=f"SYNC:{target_pid}:{sym}:{lot.id}",
            cycle_id=None, lot_id=lot.id, symbol=sym, side="BUY", quantity=qty,
            price=price(avg_cost), gross_amount=money(qty * price(avg_cost)), fee=fee,
            net_cash_change=-cost, realized_pnl=Decimal("0"), bucket=bucket,
            trade_on=acq_date, settles_on=matures_date,
            reason=f"Synced from StockNow portfolio '{portfolio_data.get('portfolio_name') or get_portfolio_name(target_pid, settings)}'",
            source="STOCKNOW_SYNC",
        ))
        created_lots.append(lot)

    session.flush()
    total_cost = sum((lot.remaining_cost_basis for lot in created_lots), Decimal("0"))
    cash_bal = Decimal(str(portfolio_data.get("cash_balance") or 0))
    min_required_capital = (max(bucket_spends.values()) if bucket_spends else Decimal("0")) * 3

    state.initial_capital = money(max(cash_bal + total_cost, min_required_capital))
    state.name = portfolio_data.get("portfolio_name") or state.name
    state.revision += 1
    session.flush()
    assert_ledger(session, state, portfolio_id=target_pid)

    new_holdings_map = {h["symbol"]: int(h["quantity"]) for h in portfolio_data.get("holdings", [])}
    all_syms = sorted(set(old_holdings_map.keys()) | set(new_holdings_map.keys()))
    holdings_diff = {
        s: {
            "local_qty": old_holdings_map.get(s, 0),
            "stocknow_qty": new_holdings_map.get(s, 0),
            "diff": new_holdings_map.get(s, 0) - old_holdings_map.get(s, 0),
        }
        for s in all_syms
        if old_holdings_map.get(s, 0) != new_holdings_map.get(s, 0)
    }
    cash_diff = float(cash_bal - old_cash)

    diff_report = {
        "old_cash": float(old_cash),
        "new_cash": float(cash_bal),
        "cash_diff": cash_diff,
        "holdings_diff": holdings_diff,
    }

    return {
        "success": True, "portfolio_id": target_pid,
        "portfolio_name": portfolio_data.get("portfolio_name") or get_portfolio_name(target_pid, settings),
        "synced_holdings_count": len(created_lots), "symbols": [lot.symbol for lot in created_lots],
        "cash_balance": float(cash_bal), "total_holdings_cost": float(total_cost),
        "initial_capital": float(state.initial_capital),
        "synced_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "checkpoint_id": cp.id,
        "diff": diff_report,
    }


def reconcile_portfolio_to_db(
    target: Database | Session, settings: Settings, portfolio_data: dict[str, Any], checkpoint_mgr: Any = None
) -> dict[str, Any]:
    """Reconcile virtual portfolio holdings and cash balance into SQLite ledger."""
    if isinstance(target, Session):
        return _execute_reconciliation(target, settings, portfolio_data, checkpoint_mgr)
    with target.write() as session:
        return _execute_reconciliation(session, settings, portfolio_data, checkpoint_mgr)


async def sync_stocknow_portfolio_via_api(
    portfolio_id: str | int,
    api_client: Any | None = None,
    live_client: Any | None = None,
    settings: Settings | None = None,
    injected_portfolio: dict[str, Any] | None = None,
    injected_ledger: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Sync target portfolio via StockNow REST API (GET /portfolios/{id} & ledger).

    Never writes zero holdings or default cash on failure.
    Uses browser DOM sync only as an Onscreen cross-check (logging mismatches as warnings).
    """
    from backend.adapters.stocknow_api import StockNowAPI, SchemaChangedError

    target_pid = str(portfolio_id).strip()
    api = api_client or StockNowAPI()

    # 1. Fetch portfolio show data
    if injected_portfolio is not None:
        raw_show = injected_portfolio
    else:
        try:
            raw_show = await api.get_portfolio(target_pid)
        except Exception as exc:
            logger.error("Portfolio API sync failed for portfolio %s: %s. Aborting without mutating ledger.", target_pid, exc)
            raise

    # 2. Fetch portfolio ledger data
    if injected_ledger is not None:
        raw_ledger = injected_ledger
    else:
        try:
            raw_ledger = await api.get_ledger(target_pid)
        except Exception as exc:
            logger.warning("Portfolio ledger API fetch failed: %s (continuing with show data)", exc)
            raw_ledger = {}

    # 3. Extract portfolio data from API responses
    # A failed or empty payload must never proceed to write zero holdings or default cash!
    if not isinstance(raw_show, dict) or "id" not in raw_show:
        raise SchemaChangedError(f"Invalid portfolio API response for {target_pid}: {raw_show}")

    # Combine ledger into show for buy_date_map if available
    combined = dict(raw_show)
    if raw_ledger and isinstance(raw_ledger, dict) and ("ledger" in raw_ledger or "transactions" in raw_ledger):
        combined["ledger"] = raw_ledger.get("ledger") or raw_ledger.get("transactions")

    extracted = extract_hummingbird_portfolio(
        client=live_client,
        injected_portfolio=combined,
    )

    # 4. Browser DOM Onscreen Cross-Check (Requirement 5)
    if live_client and getattr(live_client, "page", None) and not getattr(live_client.page, "is_closed", lambda: False)():
        try:
            dom_data = await extract_hummingbird_portfolio_from_browser(live_client)
            if dom_data:
                dom_cash = float(dom_data.get("cash_balance", 0))
                dom_holdings = {h["symbol"]: h["quantity"] for h in dom_data.get("holdings", [])}
                api_cash = float(extracted["cash_balance"])
                api_holdings = {h["symbol"]: h["quantity"] for h in extracted["holdings"]}

                if abs(api_cash - dom_cash) > 0.01:
                    logger.warning(
                        "StockNow API vs DOM cross-check cash mismatch: API=৳%.2f vs DOM=৳%.2f (diff=৳%.2f)",
                        api_cash, dom_cash, api_cash - dom_cash,
                    )
                if api_holdings != dom_holdings:
                    logger.warning(
                        "StockNow API vs DOM cross-check holdings mismatch: API=%s vs DOM=%s",
                        api_holdings, dom_holdings,
                    )
        except Exception as dom_err:
            logger.warning("Browser DOM cross-check failed: %s (API data remains authoritative)", dom_err)

    return extracted
