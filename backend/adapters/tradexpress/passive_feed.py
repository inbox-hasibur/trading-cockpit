"""Passive Data Ingestion and Telemetry Parser for LankaBangla TradeXpress 2.0.

ZERO-BAN & PASSIVE-ONLY MANDATE:
This module NEVER issues automated logins, HTTP scraping requests, or page reloads.
It strictly ingests passively received WebSocket frames and read-only DOM snapshots
from the operator's manually authenticated browser session via Chrome DevTools Protocol.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from decimal import Decimal
from threading import RLock
from typing import Any

from sqlalchemy import select

from backend.adapters.base import (
    MarketFeedAdapter,
    MarketQuote,
    PortfolioHolding,
    from_tradexpress_symbol,
    to_tradexpress_symbol,
)
from backend.config import Settings, utc_now_iso
from backend.database import CompanyProfile, Database, PortfolioState, portfolio_state
from backend.engine.money import ZERO, decimal, money, price

logger = logging.getLogger("hummingbird.tradexpress.passive_feed")


@dataclass
class AccountSummary:
    """Live account balance telemetry from TradeXpress Account Summary tab."""

    customer_number: str = "H9210"
    cash_balance: Decimal = Decimal("0.00")
    available_cash_balance: Decimal = Decimal("0.00")
    blocked_amount: Decimal = Decimal("0.00")
    cash_available_for_withdrawal: Decimal = Decimal("0.00")
    unsettled_sales: Decimal = Decimal("0.00")
    payable_amount: Decimal = Decimal("0.00")
    buying_power: Decimal = Decimal("0.00")
    last_updated: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "customer_number": self.customer_number,
            "cash_balance": float(self.cash_balance),
            "available_cash_balance": float(self.available_cash_balance),
            "blocked_amount": float(self.blocked_amount),
            "cash_available_for_withdrawal": float(self.cash_available_for_withdrawal),
            "unsettled_sales": float(self.unsettled_sales),
            "payable_amount": float(self.payable_amount),
            "buying_power": float(self.buying_power),
            "last_updated": self.last_updated,
        }


def parse_ember_market_watch_rows(
    rows: list[dict[str, Any]],
    existing_profiles: dict[str, Any] | None = None,
) -> list[MarketQuote]:
    """Pure parser mapping Ember.js dataObj rows to MarketQuote instances.

    Maps verified dataObj fields:
    - sDes: raw symbol (e.g. 'BANKASIA`PB' or 'BANKASIA\'PB')
    - ltp: Last Traded Price
    - chg: Price Change
    - pctChg: Percentage Change
    - vol: Total Traded Volume
    - bbp / bbq: Best Bid Price / Best Bid Quantity
    - bap / baq: Best Ask (Offer) Price / Best Ask Quantity
    - open / high / low: Session Open, High, Low
    - dispSettType: Settlement Type ('PUBLIC', 'SPOT', etc.)
    - dispSymCat: Symbol Category ('A', 'B', 'N', 'Z')
    - dltt: Last Trade Time string (e.g. '14:01:35')
    - wk52: 52-week high flag
    - jumpUp: Upper circuit hit flag
    """
    quotes: list[MarketQuote] = []
    for row in rows:
        d = row.get("dataObj") if isinstance(row.get("dataObj"), dict) else row
        raw_sym = str(d.get("sDes") or d.get("symbol") or d.get("sym") or "").strip()
        if not raw_sym:
            continue
        symbol = from_tradexpress_symbol(raw_sym)
        ltp = decimal(d.get("ltp") or d.get("lastTradedPrice") or d.get("lastPrice") or 0)
        chg = decimal(d.get("chg") or d.get("change") or 0)
        pct_chg = decimal(d.get("pctChg") or d.get("pctChange") or 0)
        vol = int(d.get("vol") or d.get("volume") or 0)
        open_price = decimal(d.get("open") or d.get("openPrice") or ltp)
        high = decimal(d.get("high") or ltp)
        low = decimal(d.get("low") or ltp)
        bid = decimal(d.get("bbp") or d.get("bid") or 0)
        bid_qty = int(d.get("bbq") or d.get("bidQty") or 0)
        offer = decimal(d.get("bap") or d.get("offer") or 0)
        offer_qty = int(d.get("baq") or d.get("offerQty") or 0)
        min_limit = decimal(d["minLimit"]) if d.get("minLimit") is not None else None
        max_limit = decimal(d["maxLimit"]) if d.get("maxLimit") is not None else None

        sett_type = str(d.get("dispSettType") or d.get("settlement_type") or "").strip()
        sym_cat = str(d.get("dispSymCat") or d.get("symbol_category") or "").strip()

        # Preserve last-known settlement_type and symbol_category when off-hours feed sends "N/A"
        if sett_type.upper() in ("N/A", "") and existing_profiles and symbol in existing_profiles:
            cached_sett = getattr(existing_profiles[symbol], "settlement_type", None) or (
                existing_profiles[symbol].get("settlement_type")
                if isinstance(existing_profiles[symbol], dict)
                else None
            )
            if cached_sett and cached_sett.upper() != "N/A":
                sett_type = cached_sett
        if sett_type.upper() in ("N/A", ""):
            sett_type = "PUBLIC"

        if sym_cat.upper() in ("N/A", "") and existing_profiles and symbol in existing_profiles:
            cached_cat = getattr(existing_profiles[symbol], "symbol_category", None) or (
                existing_profiles[symbol].get("symbol_category")
                if isinstance(existing_profiles[symbol], dict)
                else None
            )
            if cached_cat and cached_cat.upper() != "N/A":
                sym_cat = cached_cat
        if sym_cat.upper() in ("N/A", ""):
            sym_cat = "A"

        dltt = str(d.get("dltt") or d.get("last_trade_time") or "")
        wk52 = bool(d.get("wk52") or d.get("hit_52w_high") or False)
        jump_up = bool(d.get("jumpUp") or d.get("hit_upper_circuit") or False)

        quotes.append(
            MarketQuote(
                symbol=symbol,
                ltp=ltp,
                change=chg,
                pct_change=pct_chg,
                volume=vol,
                open_price=open_price,
                high=high,
                low=low,
                bid=bid,
                bid_qty=bid_qty,
                offer=offer,
                offer_qty=offer_qty,
                min_limit=min_limit,
                max_limit=max_limit,
                settlement_type=sett_type,
                symbol_category=sym_cat,
                hit_52w_high=wk52,
                hit_upper_circuit=jump_up,
                last_trade_time=dltt,
                source="TRADEXPRESS_PASSIVE",
            )
        )
    return quotes


def parse_ember_portfolio_rows(rows: list[dict[str, Any]]) -> list[PortfolioHolding]:
    """Pure parser mapping Ember.js portfolio rows to PortfolioHolding instances."""
    holdings: list[PortfolioHolding] = []
    for row in rows:
        d = row.get("dataObj") if isinstance(row.get("dataObj"), dict) else row
        sym_info = d.get("symbolInfo") if isinstance(d.get("symbolInfo"), dict) else {}
        raw_sym = str(sym_info.get("dSym") or d.get("symbol") or d.get("sDes") or "").strip()
        if not raw_sym:
            continue
        symbol = from_tradexpress_symbol(raw_sym)
        total_qty = int(d.get("profLossQty") or d.get("total_qty") or d.get("holding") or 0)
        avai_qty = int(d.get("avaiQtyDSE") or d.get("available_dse_qty") or d.get("saleable_qty") or 0)
        pen_holding = int(d.get("penHolding") or d.get("pending_holding_qty") or 0)
        pend_buy = int(d.get("pendBuy") or d.get("buy_pending_qty") or 0)
        pend_sell = int(d.get("pendSell") or d.get("sell_pending_qty") or 0)
        avg_cost = decimal(d.get("avgCst") or d.get("avg_cost") or 0)
        mkt_price = decimal(d.get("mktPrice") or d.get("market_price") or 0)

        holdings.append(
            PortfolioHolding(
                symbol=symbol,
                total_qty=total_qty,
                available_dse_qty=avai_qty,
                pending_holding_qty=pen_holding,
                buy_pending_qty=pend_buy,
                sell_pending_qty=pend_sell,
                avg_cost=avg_cost,
                market_price=mkt_price,
            )
        )
    return holdings


def parse_account_summary_dict(data: dict[str, Any]) -> AccountSummary:
    """Parses raw Account Summary payload into an AccountSummary dataclass."""
    cash = decimal(data.get("cash_balance") or data.get("cashBalance") or 0)
    avail_cash = decimal(data.get("available_cash_balance") or data.get("availableCashBalance") or cash)
    blocked = decimal(data.get("blocked_amount") or data.get("blockedAmount") or 0)
    avail_with = decimal(data.get("cash_available_for_withdrawal") or data.get("cashAvailableForWithdrawal") or cash)
    unsettled = decimal(data.get("unsettled_sales") or data.get("unsettledSales") or 0)
    payable = decimal(data.get("payable_amount") or data.get("payableAmount") or 0)
    buying_power = decimal(data.get("buying_power") or data.get("buyingPower") or avail_cash)

    return AccountSummary(
        customer_number=str(data.get("customer_number") or data.get("customerNumber") or "H9210"),
        cash_balance=cash,
        available_cash_balance=avail_cash,
        blocked_amount=blocked,
        cash_available_for_withdrawal=avail_with,
        unsettled_sales=unsettled,
        payable_amount=payable,
        buying_power=buying_power,
        last_updated=utc_now_iso(),
    )


def get_feed_health_and_guidance(
    tab_timestamps: dict[str, float],
    cdp_connected: bool,
    now_utc: float | None = None,
    stale_threshold_sec: float = 120.0,
    bridge_connected: bool = False,
    bridge_source: str = "",
) -> dict[str, Any]:
    """Evaluates freshness of CDP/extension connection & each tab, generating operator guidance."""
    now = now_utc if now_utc is not None else time.time()
    tabs_to_check = [
        ("market_watch", "Market Watch"),
        ("gsc", "GSC Tab"),
        ("l1", "L1 Tab"),
        ("portfolio", "Portfolio Tab"),
        ("account_summary", "Account Summary Tab"),
    ]
    freshness: dict[str, dict[str, Any]] = {}
    instructions: list[str] = []

    is_connected = cdp_connected or bridge_connected

    if not is_connected:
        instructions.append(
            "CDP connection offline / Passive feed offline. Launch Edge/Chrome with extension or CDP port 9222 and log in to https://itrade.lbsbd.com."
        )

    for tab_key, tab_label in tabs_to_check:
        ts = tab_timestamps.get(tab_key)
        age = (now - ts) if ts is not None else None
        is_fresh = age is not None and age <= stale_threshold_sec
        freshness[tab_key] = {
            "label": tab_label,
            "last_updated_epoch": ts,
            "age_seconds": round(age, 1) if age is not None else None,
            "is_fresh": is_fresh,
        }
        if not is_fresh:
            if tab_key == "market_watch":
                instructions.append("Click 'Market Watch' in TradeXpress top navigation to stream market overview.")
            elif tab_key == "gsc":
                instructions.append("Click 'GSC' tab in Market Watch to stream Giant Stable Companies quotes.")
            elif tab_key == "l1":
                instructions.append("Click 'L1' tab in Market Watch to stream Trend Recovery candidate quotes.")
            elif tab_key == "portfolio":
                instructions.append("Click 'Portfolio' tab in bottom container to refresh holdings and saleable quantities.")
            elif tab_key == "account_summary":
                instructions.append("Click 'Account Summary' sub-tab inside Portfolio container to update Buying Power and Unsettled Sales.")

    if is_connected and not instructions:
        instructions.append("All TradeXpress passive data feeds are fresh and active. No action needed.")

    is_healthy = is_connected and all(f["is_fresh"] for f in freshness.values())

    return {
        "cdp_connected": cdp_connected,
        "bridge_connected": is_connected,
        "bridge_source": bridge_source,
        "is_healthy": is_healthy,
        "freshness": freshness,
        "operator_instructions": instructions,
    }


class TradeXpressPassiveFeed(MarketFeedAdapter):
    """Thread-safe in-memory cache and feed adapter for TradeXpress passive market data."""

    def __init__(self, database: Database | None = None) -> None:
        self.database = database
        self._quotes: dict[str, MarketQuote] = {}
        self._holdings: dict[str, PortfolioHolding] = {}
        self._account_summary = AccountSummary()
        self._tab_timestamps: dict[str, float] = {}
        self._cdp_connected: bool = False
        self._bridge_source: str = "OFFLINE"
        self._last_ingest_utc: str = ""
        self._last_ingest_epoch: float = 0.0
        self._dse_status: str = "UNKNOWN"
        self._active_tab: str = "none"
        self._total_ingests_count: int = 0
        self._lock = RLock()

    def set_cdp_connected(self, connected: bool) -> None:
        with self._lock:
            self._cdp_connected = connected

    def update_ingest_telemetry(
        self,
        source: str,
        dse_status: str = "",
        active_tab: str = "",
        ingest_epoch: float | None = None,
    ) -> None:
        with self._lock:
            if source:
                self._bridge_source = source
            self._total_ingests_count += 1
            self._last_ingest_epoch = ingest_epoch if ingest_epoch is not None else time.time()
            self._last_ingest_utc = utc_now_iso()
            if dse_status:
                self._dse_status = dse_status
            if active_tab:
                self._active_tab = active_tab

    def is_bridge_connected(self, now_utc: float | None = None) -> bool:
        with self._lock:
            if self._cdp_connected:
                return True
            now = now_utc if now_utc is not None else time.time()
            return self._last_ingest_epoch > 0.0 and (now - self._last_ingest_epoch <= 20.0)

    def get_telemetry(self) -> dict[str, Any]:
        with self._lock:
            return {
                "bridge_source": self._bridge_source,
                "bridge_connected": self.is_bridge_connected(),
                "dse_status": self._dse_status,
                "active_tab": self._active_tab,
                "last_ingest_utc": self._last_ingest_utc,
                "total_ingests_count": self._total_ingests_count,
            }

    def update_tab_timestamp(self, tab: str, timestamp: float | None = None) -> None:
        with self._lock:
            self._tab_timestamps[tab.lower()] = timestamp if timestamp is not None else time.time()

    def update_quotes(self, quotes: list[MarketQuote]) -> None:
        with self._lock:
            for q in quotes:
                self._quotes[q.symbol] = q

    def update_holdings(self, holdings: list[PortfolioHolding]) -> None:
        with self._lock:
            for h in holdings:
                self._holdings[h.symbol] = h

    def update_account_summary(self, summary: AccountSummary) -> None:
        with self._lock:
            self._account_summary = summary

    def get_account_summary(self) -> AccountSummary:
        with self._lock:
            return self._account_summary

    def get_all_holdings(self) -> dict[str, PortfolioHolding]:
        with self._lock:
            return dict(self._holdings)

    def get_all_quotes(self) -> dict[str, MarketQuote]:
        with self._lock:
            return dict(self._quotes)

    async def get_quote(self, symbol: str) -> MarketQuote | None:
        clean = from_tradexpress_symbol(symbol)
        with self._lock:
            if clean in self._quotes:
                return self._quotes[clean]

        # Fallback to database if available
        if self.database:
            with self.database.read() as session:
                cp = session.get(CompanyProfile, clean)
                if cp:
                    return MarketQuote(
                        symbol=cp.symbol,
                        ltp=cp.last_price,
                        change=Decimal("0"),
                        pct_change=Decimal("0"),
                        volume=0,
                        open_price=cp.last_price,
                        high=cp.last_price,
                        low=cp.last_price,
                        bid=getattr(cp, "bid", Decimal("0")),
                        bid_qty=getattr(cp, "bid_qty", 0),
                        offer=getattr(cp, "offer", Decimal("0")),
                        offer_qty=getattr(cp, "offer_qty", 0),
                        min_limit=getattr(cp, "min_limit", None),
                        max_limit=getattr(cp, "max_limit", None),
                        settlement_type=getattr(cp, "settlement_type", "PUBLIC"),
                        symbol_category=getattr(cp, "symbol_category", "A"),
                        hit_52w_high=getattr(cp, "hit_52w_high", False),
                        hit_upper_circuit=getattr(cp, "hit_upper_circuit", False),
                        last_trade_time=getattr(cp, "last_trade_time", ""),
                        source="DATABASE_FALLBACK",
                    )
        return None

    async def get_quotes(self, symbols: list[str]) -> dict[str, MarketQuote]:
        result: dict[str, MarketQuote] = {}
        for s in symbols:
            q = await self.get_quote(s)
            if q:
                result[q.symbol] = q
        return result

    def get_health_and_guidance(self, now_utc: float | None = None) -> dict[str, Any]:
        with self._lock:
            return get_feed_health_and_guidance(
                self._tab_timestamps,
                self._cdp_connected,
                now_utc=now_utc,
                bridge_connected=self.is_bridge_connected(now_utc=now_utc),
                bridge_source=self._bridge_source,
            )


_GLOBAL_PASSIVE_FEED: TradeXpressPassiveFeed | None = None


def get_global_passive_feed(database: Database | None = None) -> TradeXpressPassiveFeed:
    """Singleton getter for the global passive market feed adapter."""
    global _GLOBAL_PASSIVE_FEED
    if _GLOBAL_PASSIVE_FEED is None:
        _GLOBAL_PASSIVE_FEED = TradeXpressPassiveFeed(database=database)
    elif database and not _GLOBAL_PASSIVE_FEED.database:
        _GLOBAL_PASSIVE_FEED.database = database
    return _GLOBAL_PASSIVE_FEED


def ingest_passive_snapshot(
    db: Database,
    snapshot_payload: dict[str, Any],
    feed: TradeXpressPassiveFeed | None = None,
    broadcaster: Any = None,
    bridge_source: str | None = None,
) -> dict[str, Any]:
    """Ingests passively sniffed snapshot payload into SQLite and in-memory feed.

    Builds/updates CompanyProfile microstructure columns and automatically appends
    or updates today's candle bar in price_history so 7-30 day curves build organically.
    """
    active_feed = feed or get_global_passive_feed(db)
    tab = str(snapshot_payload.get("tab") or "").strip().lower()
    if tab:
        active_feed.update_tab_timestamp(tab)

    cdp_conn = snapshot_payload.get("cdp_connected")
    if cdp_conn is not None:
        active_feed.set_cdp_connected(bool(cdp_conn))

    dse_status = str(snapshot_payload.get("dse_status") or "").strip()
    resolved_source = bridge_source or snapshot_payload.get("source") or (
        "EDGE_EXTENSION_PASSIVE"
        if (cdp_conn is None and "source" in snapshot_payload)
        else ("CDP_DAEMON" if cdp_conn else "MANUAL_INGEST")
    )
    active_feed.update_ingest_telemetry(
        source=resolved_source,
        dse_status=dse_status or "UNKNOWN",
        active_tab=tab or "market_watch",
    )

    quotes_updated = 0
    holdings_updated = 0
    summary_updated = False

    # 1. Parse & Ingest Market Watch rows
    mw_rows = snapshot_payload.get("market_watch_rows") or snapshot_payload.get("rows")
    parsed_quotes: list[MarketQuote] = []
    if mw_rows and isinstance(mw_rows, list):
        # Fetch existing company profiles for fallback caching (as pure dicts to prevent DetachedInstanceError)
        existing_profiles: dict[str, dict[str, Any]] = {}
        with db.read() as read_session:
            profiles = list(read_session.scalars(select(CompanyProfile)))
            existing_profiles = {
                p.symbol: {
                    "settlement_type": p.settlement_type,
                    "symbol_category": p.symbol_category,
                }
                for p in profiles
            }

        parsed_quotes = parse_ember_market_watch_rows(mw_rows, existing_profiles)
        active_feed.update_quotes(parsed_quotes)

        with db.write() as session:
            state = portfolio_state(session)
            today_str = state.clock_date.isoformat()

            for q in parsed_quotes:
                cp = session.get(CompanyProfile, q.symbol)
                if cp is None:
                    # Create new company profile if symbol does not exist
                    cp = CompanyProfile(
                        symbol=q.symbol,
                        name=q.symbol,
                        sector="DSE",
                        favorite=True,
                        settlement_days=2,
                        last_price=q.ltp,
                        price_history=[],
                        quote_on=state.clock_date,
                        source="TRADEXPRESS_PASSIVE",
                        watchlist_category="GSC",
                    )
                    session.add(cp)

                # Update live microstructure telemetry
                if q.ltp > ZERO:
                    cp.last_price = q.ltp
                cp.bid = q.bid
                cp.bid_qty = q.bid_qty
                cp.offer = q.offer
                cp.offer_qty = q.offer_qty
                cp.min_limit = q.min_limit
                cp.max_limit = q.max_limit
                if q.settlement_type and q.settlement_type.upper() != "N/A":
                    cp.settlement_type = q.settlement_type
                if q.symbol_category and q.symbol_category.upper() != "N/A":
                    cp.symbol_category = q.symbol_category
                cp.hit_52w_high = q.hit_52w_high
                cp.hit_upper_circuit = q.hit_upper_circuit
                cp.last_trade_time = q.last_trade_time
                cp.source = "TRADEXPRESS_PASSIVE"
                cp.quote_on = state.clock_date

                # Organically maintain closing candle bar in price_history
                candle = {
                    "date": today_str,
                    "close": str(q.ltp),
                    "open": str(q.open_price),
                    "high": str(q.high),
                    "low": str(q.low),
                    "volume": str(q.volume),
                }
                history = list(cp.price_history or [])
                if history and history[-1].get("date") == today_str:
                    history[-1] = candle
                else:
                    history.append(candle)
                cp.price_history = history[-30:]
                quotes_updated += 1

            session.flush()

    # 1.5. Ingest order ticket limits if present
    ot_limits = snapshot_payload.get("order_ticket_limits")
    if ot_limits and isinstance(ot_limits, dict):
        raw_sym = str(ot_limits.get("symbol") or "").strip()
        if raw_sym:
            sym = from_tradexpress_symbol(raw_sym)
            min_l = ot_limits.get("min_limit")
            max_l = ot_limits.get("max_limit")
            min_val = decimal(min_l) if min_l is not None and str(min_l).strip() != "" else None
            max_val = decimal(max_l) if max_l is not None and str(max_l).strip() != "" else None
            if min_val is not None or max_val is not None:
                with db.write() as session:
                    cp = session.get(CompanyProfile, sym)
                    if cp:
                        if min_val is not None and min_val > ZERO:
                            cp.min_limit = min_val
                        if max_val is not None and max_val > ZERO:
                            cp.max_limit = max_val
                        session.flush()

    # 2. Parse & Ingest Portfolio rows
    pf_rows = snapshot_payload.get("portfolio_rows")
    if pf_rows and isinstance(pf_rows, list):
        parsed_holdings = parse_ember_portfolio_rows(pf_rows)
        active_feed.update_holdings(parsed_holdings)
        holdings_updated = len(parsed_holdings)

    # 3. Parse & Ingest Account Summary
    acct_data = snapshot_payload.get("account_summary")
    is_offhours_closed = dse_status.upper() in ("CLOSE", "CLOSED")
    if acct_data and isinstance(acct_data, dict):
        summary = parse_account_summary_dict(acct_data)
        prev_summary = active_feed.get_account_summary()

        # Off-Hours 0.00 Cash Guard:
        # When dse_status is "Close"/"CLOSED" AND incoming account_summary has
        # buying_power == 0 and cash_balance == 0, preserve previously cached
        # positive buying_power / cash_balance instead of overwriting with 0.00!
        if (
            is_offhours_closed
            and summary.cash_balance <= ZERO
            and summary.buying_power <= ZERO
            and (prev_summary.cash_balance > ZERO or prev_summary.buying_power > ZERO)
        ):
            logger.info(
                "Off-Hours 0.00 Cash Guard: Preserving cached cash balances (buying_power=%s)",
                prev_summary.buying_power,
            )
            summary.cash_balance = prev_summary.cash_balance
            summary.available_cash_balance = prev_summary.available_cash_balance
            summary.buying_power = prev_summary.buying_power
            summary.cash_available_for_withdrawal = prev_summary.cash_available_for_withdrawal
            if summary.unsettled_sales <= ZERO and prev_summary.unsettled_sales > ZERO:
                summary.unsettled_sales = prev_summary.unsettled_sales
            if summary.blocked_amount <= ZERO and prev_summary.blocked_amount > ZERO:
                summary.blocked_amount = prev_summary.blocked_amount

        active_feed.update_account_summary(summary)
        summary_updated = True
        with db.write() as session:
            state = portfolio_state(session)
            if summary.unsettled_sales > ZERO or not is_offhours_closed:
                state.unsettled_sales_bdt = summary.unsettled_sales
            session.flush()

    # 4. SSE broadcast if available
    if broadcaster:
        try:
            broadcaster.publish(
                "tradexpress_feed_update",
                {
                    "tab": tab,
                    "quotes_count": quotes_updated,
                    "holdings_count": holdings_updated,
                    "summary_updated": summary_updated,
                    "bridge_source": resolved_source,
                    "dse_status": dse_status,
                    "timestamp": utc_now_iso(),
                },
            )
        except Exception as exc:
            logger.debug("Failed publishing SSE feed update: %s", exc)

    return {
        "status": "INGESTED",
        "tab": tab,
        "quotes_updated": quotes_updated,
        "holdings_updated": holdings_updated,
        "summary_updated": summary_updated,
        "bridge_source": resolved_source,
        "dse_status": dse_status,
        "bridge_connected": active_feed.is_bridge_connected(),
        "guidance": active_feed.get_health_and_guidance(),
    }
