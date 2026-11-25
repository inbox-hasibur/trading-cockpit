"""Deterministic Real-Data Market Decision Advisor (Checkpoint 2).

Evaluates GSC / GSC_L1 / GSC_L2 watchlist and held lots strictly from:
1) Passive real-time TradeXpress quotes (LTP, Bid/Offer, Min/Max, A/B/Z, PUBLIC/SPOT)
2) Verified 7-30 day DSE daily historical candles (never synthetic/fake curves).
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from backend.adapters.base import to_tradexpress_symbol
from backend.adapters.tradexpress.passive_feed import TradeXpressPassiveFeed, get_global_passive_feed
from backend.config import Settings
from backend.database import CompanyProfile, CustomRule, TaxLot, portfolio_state
from backend.engine.curve_analyzer import analyze_curve
from backend.engine.money import HUNDRED, ZERO, decimal
from backend.engine.t2_ledger import bucket_balances


def _tier_label(cat: str) -> str:
    if cat == "GSC_L1":
        return "L1 Safe"
    if cat == "GSC_L2":
        return "L2 Risky"
    return "GSC Watch"


def _clamp_limit(val: Decimal, min_limit: Decimal | None, max_limit: Decimal | None) -> Decimal:
    out = val
    if min_limit is not None and min_limit > ZERO and out < min_limit:
        out = min_limit
    if max_limit is not None and max_limit > ZERO and out > max_limit:
        out = max_limit
    return out


def analyze_market_decisions(
    session: Session,
    settings: Settings,
    passive_feed: TradeXpressPassiveFeed | None = None,
) -> dict[str, Any]:
    """Produces deterministic BUY / SELL / WAIT / BLOCKED / NO_HISTORY decision table."""
    feed = passive_feed or get_global_passive_feed()
    state = portfolio_state(session)
    as_of = state.clock_date
    today_str = as_of.isoformat()

    buy_fee = decimal(getattr(settings, "buy_fee_rate", Decimal("0.004")) or Decimal("0.004"))
    sell_fee = decimal(getattr(settings, "sell_fee_rate", Decimal("0.004")) or Decimal("0.004"))

    acct = feed.get_account_summary() if feed else None
    real_h9210_bp = float(acct.buying_power if (acct and acct.buying_power > ZERO) else (acct.cash_balance if acct else ZERO))

    active_pid = "H9210_SHADOW" if getattr(state, "mode", "") == "SHADOW" else None
    balances = bucket_balances(session, state, portfolio_id=active_pid)
    shadow_bp = float(sum((b.available_cash for b in balances.values()), ZERO))

    lots_q = select(TaxLot).where(TaxLot.remaining_qty > 0).order_by(TaxLot.acquired_on)
    if active_pid:
        lots_q = lots_q.where(TaxLot.portfolio_id == active_pid)
    lots = list(session.scalars(lots_q))
    held_by_sym: dict[str, list[TaxLot]] = {}
    for lot in lots:
        held_by_sym.setdefault(lot.symbol, []).append(lot)

    held_syms = set(held_by_sym.keys())
    stmt = (
        select(CompanyProfile)
        .where(
            or_(
                CompanyProfile.watchlist_category.in_(("GSC", "GSC_L1", "GSC_L2")),
                CompanyProfile.favorite.is_(True),
                CompanyProfile.symbol.in_(held_syms) if held_syms else False,
            )
        )
        .order_by(CompanyProfile.symbol)
    )
    companies = list(session.scalars(stmt).all())
    rules = {r.symbol: r for r in session.scalars(select(CustomRule)).all()}
    passive_quotes = feed.get_all_quotes() if feed else {}

    buy_candidates: list[dict[str, Any]] = []
    sell_candidates: list[dict[str, Any]] = []
    watch_or_hold: list[dict[str, Any]] = []
    blocked_or_missing: list[dict[str, Any]] = []

    live_quotes_count = 0
    verified_curves_count = 0

    for cp in companies:
        sym = cp.symbol
        cat = (getattr(cp, "watchlist_category", "GSC") or "GSC").upper()
        tier = _tier_label(cat)
        rule = rules.get(sym)

        live_q = passive_quotes.get(sym)
        if live_q and getattr(live_q, "ltp", ZERO) > ZERO:
            live_quotes_count += 1

        ltp = live_q.ltp if (live_q and live_q.ltp > ZERO) else (cp.last_price or ZERO)
        bid = live_q.bid if (live_q and live_q.bid > ZERO) else (getattr(cp, "bid", ZERO) or ZERO)
        offer = live_q.offer if (live_q and live_q.offer > ZERO) else (getattr(cp, "offer", ZERO) or ZERO)
        bid_qty = int(live_q.bid_qty if live_q else (getattr(cp, "bid_qty", 0) or 0))
        offer_qty = int(live_q.offer_qty if live_q else (getattr(cp, "offer_qty", 0) or 0))
        pct_chg = float(live_q.pct_change) if (live_q and live_q.pct_change is not None) else 0.0
        min_lim = (live_q.min_limit if live_q and live_q.min_limit else getattr(cp, "min_limit", None))
        max_lim = (live_q.max_limit if live_q and live_q.max_limit else getattr(cp, "max_limit", None))

        sym_cat = (
            (live_q.symbol_category if live_q and live_q.symbol_category not in ("", "N/A") else None)
            or getattr(cp, "symbol_category", "A")
            or "A"
        ).upper()
        sett_type = (
            (live_q.settlement_type if live_q and live_q.settlement_type not in ("", "N/A") else None)
            or getattr(cp, "settlement_type", "PUBLIC")
            or "PUBLIC"
        ).upper()

        history = list(cp.price_history or [])
        if ltp > ZERO and history and history[-1].get("date") == today_str:
            history[-1] = {**history[-1], "close": f"{ltp:.2f}"}
        elif ltp > ZERO and history and history[-1].get("date", "") < today_str:
            history.append({"date": today_str, "close": f"{ltp:.2f}"})

        history_days = len(history)
        history_verified = history_days >= 7
        if history_verified:
            verified_curves_count += 1

        sym_lots = held_by_sym.get(sym, [])
        held_qty = sum(l.remaining_qty for l in sym_lots)
        mature_qty = sum(l.remaining_qty for l in sym_lots if l.matures_on <= as_of)
        total_cost_basis = sum((l.remaining_cost_basis for l in sym_lots), ZERO)
        avg_buy = (total_cost_basis / held_qty) if held_qty > 0 else ZERO

        support_val = 0.0
        resist_val = 0.0
        curve_signal = "NO_HISTORY"
        curve_reason = "Real 7–30d history not synced yet."

        if history_verified and ltp > ZERO:
            buy_frac = getattr(rule, "buy_zone_fraction", None) or Decimal("0.35")
            crash_d = getattr(rule, "crash_daily_pct", None) or Decimal("8")
            crash_dd = getattr(rule, "crash_drawdown_pct", None) or Decimal("15")
            # Analyze using the latest bar date so real fetched candles up to yesterday/today always evaluate cleanly
            latest_bar_date = as_of
            try:
                latest_bar_date = datetime.strptime(history[-1]["date"], "%Y-%m-%d").date()
            except Exception:
                pass
            analysis = analyze_curve(
                history,
                as_of=latest_bar_date,
                buy_fee_rate=buy_fee,
                sell_fee_rate=sell_fee,
                buy_zone_fraction=decimal(buy_frac),
                crash_daily_pct=decimal(crash_d),
                crash_drawdown_pct=decimal(crash_dd),
            )
            curve_signal = analysis.signal
            curve_reason = analysis.reason
            support_val = float(analysis.low)
            resist_val = float(analysis.high)
        elif ltp <= ZERO:
            curve_signal = "WAIT_SOD"
            curve_reason = "LTP is 0.00 (SOD / market closed)."

        # Suggested limit & upside math
        entry_ref = offer if offer > ZERO else ltp
        entry_limit = _clamp_limit(entry_ref, min_lim, max_lim) if entry_ref > ZERO else ZERO
        exit_ref = bid if bid > ZERO else ltp
        exit_limit = _clamp_limit(exit_ref, min_lim, max_lim) if exit_ref > ZERO else ZERO

        est_net_upside_pct = 0.0
        if entry_limit > ZERO and resist_val > 0:
            resist_dec = decimal(resist_val)
            net_up = (resist_dec * (Decimal("1") - sell_fee) / (entry_limit * (Decimal("1") + buy_fee)) - Decimal("1")) * HUNDRED
            est_net_upside_pct = round(float(net_up), 2)

        breakeven_price = (avg_buy * (Decimal("1") + buy_fee) / (Decimal("1") - sell_fee)) if avg_buy > ZERO else ZERO

        affordable_h9210 = int(Decimal(str(real_h9210_bp)) // (entry_limit * (Decimal("1") + buy_fee))) if entry_limit > ZERO and real_h9210_bp > 0 else 0
        affordable_shadow = int(Decimal(str(shadow_bp)) // (entry_limit * (Decimal("1") + buy_fee))) if entry_limit > ZERO and shadow_bp > 0 else 0

        # Action classification
        action = "WATCH_ONLY"
        suggested_limit = float(entry_limit)
        reason = curve_reason

        if sym_cat == "Z" or sett_type == "SPOT":
            action = "BLOCKED"
            reason = f"BLOCKED: {sym_cat}-category / {sett_type} settlement excluded by DSE safety filter."
        elif cp.quarantined or curve_signal == "CRASH_QUARANTINE":
            action = "BLOCKED"
            reason = f"BLOCKED: Crash quarantine active ({curve_reason})."
        elif not history_verified:
            action = "NO_HISTORY"
            reason = f"NO_HISTORY: {history_days}d candles cached (need >= 7 real days; click Sync 30d Curves)."
        elif ltp <= ZERO:
            action = "HOLD_WAIT"
            reason = "SOD / LTP 0.00 — waiting for live TradeXpress quote."
        elif held_qty > 0:
            suggested_limit = float(exit_limit)
            if mature_qty > 0 and exit_limit > breakeven_price and (curve_signal == "SELL_ZONE" or (exit_limit / breakeven_price - Decimal("1")) * HUNDRED >= Decimal("1.5")):
                action = "SELL_CANDIDATE"
                net_gain_pct = float((exit_limit * (Decimal("1") - sell_fee) / (avg_buy * (Decimal("1") + buy_fee)) - Decimal("1")) * HUNDRED)
                reason = f"Mature {mature_qty} sh net +{net_gain_pct:.2f}% @ ৳{exit_limit:.2f} bid (above ৳{breakeven_price:.2f} breakeven)."
            elif mature_qty == 0:
                action = "HOLD_WAIT"
                reason = f"Holding {held_qty} sh (T+2 locked); waiting for settlement maturity."
            else:
                action = "HOLD_WAIT"
                reason = f"No-Loss Hold: ৳{exit_limit:.2f} below breakeven ৳{breakeven_price:.2f} or mid-range."
        elif cat in ("GSC_L1", "GSC_L2") and curve_signal == "BUY_ZONE" and est_net_upside_pct >= 1.5:
            action = "BUY_CANDIDATE"
            reason = f"{tier} · Real {history_days}d dip near ৳{support_val:.2f} support, +{est_net_upside_pct:.2f}% net upside to ৳{resist_val:.2f} resistance."
        elif cat == "GSC":
            action = "WATCH_ONLY"
            reason = f"GSC Observation pool ({curve_signal}); promote to L1/L2 before buying."
        else:
            action = "HOLD_WAIT"
            reason = f"{tier} · {curve_signal} (wait for lower range near ৳{support_val:.2f} support)."

        row = {
            "symbol": sym,
            "tradexpress_symbol": to_tradexpress_symbol(sym),
            "tier": tier,
            "watchlist_category": cat,
            "category": sym_cat,
            "settlement_type": sett_type,
            "history_days": history_days,
            "history_verified": history_verified,
            "ltp": float(ltp),
            "pct_chg": round(pct_chg, 2),
            "bid": float(bid),
            "bid_qty": bid_qty,
            "offer": float(offer),
            "offer_qty": offer_qty,
            "support": round(support_val, 2),
            "resistance": round(resist_val, 2),
            "curve_signal": curve_signal,
            "action": action,
            "suggested_limit_price": round(suggested_limit, 2),
            "est_net_upside_pct": est_net_upside_pct,
            "affordable_qty_h9210": affordable_h9210,
            "affordable_qty_shadow": affordable_shadow,
            "held_qty": held_qty,
            "mature_qty": mature_qty,
            "reason": reason,
        }

        if action == "BUY_CANDIDATE":
            buy_candidates.append(row)
        elif action == "SELL_CANDIDATE":
            sell_candidates.append(row)
        elif action in ("BLOCKED", "NO_HISTORY"):
            blocked_or_missing.append(row)
        else:
            watch_or_hold.append(row)

    buy_candidates.sort(
        key=lambda r: (0 if r["watchlist_category"] == "GSC_L1" else 1, -r["est_net_upside_pct"], r["symbol"])
    )
    sell_candidates.sort(key=lambda r: (-r["est_net_upside_pct"], r["symbol"]))

    all_decisions = buy_candidates + sell_candidates + watch_or_hold + blocked_or_missing

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "buy_candidates": buy_candidates,
        "sell_candidates": sell_candidates,
        "watch_or_hold": watch_or_hold,
        "blocked_or_missing": blocked_or_missing,
        "all_decisions": all_decisions,
        "data_truth_summary": {
            "total_evaluated": len(all_decisions),
            "live_quotes_count": live_quotes_count,
            "verified_curves_count": verified_curves_count,
            "real_h9210_bp": round(real_h9210_bp, 2),
            "shadow_bp": round(shadow_bp, 2),
            "buy_ideas_count": len(buy_candidates),
            "sell_ideas_count": len(sell_candidates),
        },
    }
