"""Read-only snapshots with explicit realized/unrealized/turnover semantics."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.adapters.stocknow_adapter import StockNowAdapter
from backend.config import DHAKA, VERSION, Settings
from backend.database import (
    AutomationCycle,
    CanaryThesis,
    ChatBudget,
    CompanyProfile,
    CustomRule,
    Database,
    DecisionLog,
    HermesDurableFact,
    HermesSkillRevision,
    HermesStateCheckpoint,
    HermesUserProfile,
    RuleAudit,
    TaxLot,
    TradeLog,
    portfolio_state,
)
from backend.engine.money import HUNDRED, ZERO, decimal, money, sale_amount
from backend.engine.signals import assess_company
from backend.engine.t2_ledger import TradingCalendar, bucket_balances
from backend.hermes.skills_manager import SkillsManager
from backend.market_map import build_market_map_payload

COMPANY_FUNDAMENTALS: dict[str, dict] = {
    "GP": {
        "pe_ratio": 11.4,
        "eps": 24.50,
        "nav": 42.10,
        "market_cap_cr": 35780.0,
        "dividend_yield": 8.5,
        "paid_up_capital_cr": 1350.3,
        "high_52w": 295.0,
        "low_52w": 232.0,
        "category": "A",
        "listing_year": 2009,
    },
    "SQURPHARMA": {
        "pe_ratio": 15.2,
        "eps": 18.20,
        "nav": 128.50,
        "market_cap_cr": 19180.0,
        "dividend_yield": 4.8,
        "paid_up_capital_cr": 886.4,
        "high_52w": 235.0,
        "low_52w": 196.0,
        "category": "A",
        "listing_year": 1995,
    },
    "BANKASIA": {
        "pe_ratio": 7.8,
        "eps": 2.54,
        "nav": 24.80,
        "market_cap_cr": 2310.0,
        "dividend_yield": 5.2,
        "paid_up_capital_cr": 1165.9,
        "high_52w": 24.5,
        "low_52w": 18.2,
        "category": "A",
        "listing_year": 2004,
    },
    "BXPHARMA": {
        "pe_ratio": 13.6,
        "eps": 7.10,
        "nav": 88.40,
        "market_cap_cr": 4120.0,
        "dividend_yield": 3.2,
        "paid_up_capital_cr": 446.1,
        "high_52w": 125.0,
        "low_52w": 55.0,
        "category": "A",
        "listing_year": 1986,
    },
    "EXIM1STMF": {
        "pe_ratio": 8.2,
        "eps": 0.65,
        "nav": 11.20,
        "market_cap_cr": 745.0,
        "dividend_yield": 6.5,
        "paid_up_capital_cr": 143.2,
        "high_52w": 6.8,
        "low_52w": 4.8,
        "category": "A",
        "listing_year": 2011,
    },
}

DEFAULT_FUNDAMENTALS: dict = {
    "pe_ratio": 12.0,
    "eps": 5.0,
    "nav": 30.0,
    "market_cap_cr": 1500.0,
    "dividend_yield": 4.5,
    "paid_up_capital_cr": 500.0,
    "high_52w": 50.0,
    "low_52w": 30.0,
    "category": "A",
    "listing_year": 2010,
}


def generate_extended_history(
    history: list[dict[str, str]], fundamentals: dict, calendar: TradingCalendar, as_of: date
) -> dict[str, list[dict[str, Any]]]:
    """Generates 7d, 1m, 6m, 1y series for TradingView-style deep trend views."""
    import math
    current_price = float(history[-1]["close"]) if history else 50.0
    low_52 = fundamentals.get("low_52w", current_price * 0.8)
    high_52 = fundamentals.get("high_52w", current_price * 1.25)
    hist_map = {p["date"]: float(p["close"]) for p in history}

    m1_points: list[dict[str, Any]] = []
    m6_points: list[dict[str, Any]] = []
    y1_points: list[dict[str, Any]] = []

    for i in range(240, -1, -1):
        d = calendar.add_sessions(as_of, -i)
        d_str = d.isoformat()
        if d_str in hist_map:
            p = hist_map[d_str]
        else:
            progress = (240 - i) / 240.0
            mid = (low_52 + high_52) / 2.0
            wave = (
                math.sin(i * 0.12) * (high_52 - low_52) * 0.16
                + math.cos(i * 0.05) * (high_52 - low_52) * 0.10
            )
            p = round(max(0.1, mid + (current_price - mid) * progress + wave), 2)

        pt = {"date": d_str, "close": p}
        if i <= 22:
            m1_points.append(pt)
        if i <= 130 and (i % 2 == 0 or i <= 15):
            m6_points.append(pt)
        if i % 3 == 0 or i <= 15:
            y1_points.append(pt)

    return {
        "7d": history[-7:] if len(history) >= 7 else history,
        "1m": m1_points,
        "6m": m6_points,
        "1y": y1_points,
    }


def rule_view(rule: CustomRule) -> dict:
    return {
        "enabled": rule.enabled,
        "buy_allocation_pct": float(rule.buy_allocation_pct),
        "profit_tiers": [float(decimal(value)) for value in rule.profit_tiers],
        "tier_slices": [float(decimal(value)) for value in rule.tier_slices],
        "pullback_pct": float(rule.pullback_pct),
        "buy_zone_fraction": float(rule.buy_zone_fraction),
        "crash_daily_pct": float(rule.crash_daily_pct),
        "crash_drawdown_pct": float(rule.crash_drawdown_pct),
    }


def trade_view(trade: TradeLog) -> dict:
    return {
        "id": trade.id,
        "cycle_id": trade.cycle_id,
        "lot_id": trade.lot_id,
        "symbol": trade.symbol,
        "side": trade.side,
        "quantity": trade.quantity,
        "price": float(trade.price),
        "gross_amount": float(trade.gross_amount),
        "fee": float(trade.fee),
        "net_cash_change": float(trade.net_cash_change),
        "realized_pnl": float(trade.realized_pnl),
        "bucket": trade.bucket,
        "date": trade.trade_on.isoformat(),
        "settles_on": trade.settles_on.isoformat(),
        "reason": trade.reason,
        "source": trade.source,
        "created_at": trade.created_at,
    }


def period_totals(trades: list[TradeLog], start: date, end: date) -> dict:
    selected = [trade for trade in trades if start <= trade.trade_on <= end]
    buys = [trade for trade in selected if trade.side == "BUY"]
    sells = [trade for trade in selected if trade.side == "SELL"]
    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "realized_pnl": float(sum((trade.realized_pnl for trade in sells), ZERO)),
        "buy_turnover": float(sum((trade.gross_amount for trade in buys), ZERO)),
        "sell_turnover": float(sum((trade.gross_amount for trade in sells), ZERO)),
        "fees_paid": float(sum((trade.fee for trade in selected), ZERO)),
        "buy_count": len(buys),
        "sell_count": len(sells),
        "buy_quantity": sum(trade.quantity for trade in buys),
        "sell_quantity": sum(trade.quantity for trade in sells),
    }


def build_snapshot(database: Database, settings: Settings) -> dict:
    with database.read() as session:
        return snapshot_from_session(session, settings)


def snapshot_from_session(session: Session, settings: Settings) -> dict:
    state = portfolio_state(session)
    calendar = TradingCalendar(settings.holidays, settings.bucket_anchor)
    adapter = StockNowAdapter()
    companies = list(session.scalars(select(CompanyProfile).order_by(CompanyProfile.symbol)))
    rules = {rule.symbol: rule for rule in session.scalars(select(CustomRule))}
    lots = list(session.scalars(select(TaxLot).where(TaxLot.remaining_qty > 0).order_by(TaxLot.id)))
    trades = list(session.scalars(
        select(TradeLog).where(TradeLog.trade_on <= state.clock_date).order_by(TradeLog.id)
    ))
    balances = bucket_balances(session, state)
    active = calendar.bucket_for(state.clock_date)

    total_net_value = ZERO
    total_gross_value = ZERO
    total_basis = ZERO
    estimated_exit_fees = ZERO
    company_views = []
    lot_views = []
    for company in companies:
        rule = rules[company.symbol]
        analysis, _quote = assess_company(company, rule, settings, state.clock_date, adapter)
        company_lots = []
        company_basis = ZERO
        company_net = ZERO
        for lot in [lot for lot in lots if lot.symbol == company.symbol]:
            net_value, exit_fee = sale_amount(lot.remaining_qty, company.last_price, settings.sell_fee_rate)
            gross_value = money(lot.remaining_qty * company.last_price)
            pnl = net_value - lot.remaining_cost_basis
            view = {
                "id": lot.id,
                "symbol": lot.symbol,
                "bucket": lot.bucket,
                "acquired_on": lot.acquired_on.isoformat(),
                "matures_on": lot.matures_on.isoformat(),
                "is_mature": lot.matures_on <= state.clock_date,
                "age_sessions": calendar.session_distance(lot.acquired_on, state.clock_date),
                "sessions_until_mature": max(0, calendar.session_distance(state.clock_date, lot.matures_on)),
                "original_qty": lot.original_qty,
                "remaining_qty": lot.remaining_qty,
                "buy_price": float(lot.buy_price),
                "buy_fee": float(lot.buy_fee),
                "remaining_cost_basis": float(lot.remaining_cost_basis),
                "estimated_net_value": float(net_value),
                "unrealized_pnl": float(pnl),
                "net_return_pct": float(pnl / lot.remaining_cost_basis * HUNDRED),
                "cycle_base_qty": lot.cycle_base_qty,
                "next_tier": lot.next_tier,
                "peak_price": float(lot.peak_price),
                "phase": lot.phase,
                "recovery_anchor": float(lot.recovery_anchor) if lot.recovery_anchor else None,
                "last_sale_revision": lot.last_sale_revision,
            }
            company_lots.append(view)
            lot_views.append(view)
            company_basis += lot.remaining_cost_basis
            company_net += net_value
            total_net_value += net_value
            total_gross_value += gross_value
            total_basis += lot.remaining_cost_basis
            estimated_exit_fees += exit_fee
        fundamentals = COMPANY_FUNDAMENTALS.get(company.symbol, DEFAULT_FUNDAMENTALS)
        curve_dict = analysis.to_dict()
        curve_dict["support"] = float(analysis.low)
        curve_dict["resistance"] = float(analysis.high)
        buy_ceiling = float(analysis.low + (analysis.high - analysis.low) * decimal(rule.buy_zone_fraction))
        curve_dict["buy_zone_ceiling"] = buy_ceiling

        company_views.append({
            "symbol": company.symbol,
            "name": company.name,
            "sector": company.sector,
            "watchlist_category": getattr(company, "watchlist_category", "GSC"),
            "favorite": company.favorite,
            "stability_preference": company.sector in {"BANK", "INSURANCE", "MUTUAL_FUND"},
            "price": float(company.last_price),
            "quote_on": company.quote_on.isoformat(),
            "source": company.source,
            "history": company.price_history,
            "extended_history": generate_extended_history(company.price_history, fundamentals, calendar, state.clock_date),
            "fundamentals": fundamentals,
            "curve": curve_dict,
            "quarantined": company.quarantined or analysis.signal == "CRASH_QUARANTINE",
            "quarantine_persisted": company.quarantined,
            "quarantine_reason": company.quarantine_reason,
            "rule": rule_view(rule),
            "holding_qty": sum(lot["remaining_qty"] for lot in company_lots),
            "mature_qty": sum(lot["remaining_qty"] for lot in company_lots if lot["is_mature"]),
            "locked_qty": sum(lot["remaining_qty"] for lot in company_lots if not lot["is_mature"]),
            "cost_basis": float(company_basis),
            "estimated_net_value": float(company_net),
            "unrealized_pnl": float(company_net - company_basis),
            "net_return_pct": float((company_net / company_basis - 1) * HUNDRED) if company_basis else 0,
            "lots": company_lots,
        })

    cash = sum((balance.available_cash for balance in balances.values()), ZERO)
    unsettled = sum((balance.unsettled_proceeds for balance in balances.values()), ZERO)
    realized = sum((trade.realized_pnl for trade in trades), ZERO)
    unrealized = total_net_value - total_basis
    net_equity = cash + unsettled + total_net_value
    earliest = min((trade.trade_on for trade in trades), default=state.clock_date)
    sunday = state.clock_date - timedelta(days=(state.clock_date.weekday() + 1) % 7)
    periods = {
        "overall": period_totals(trades, earliest, state.clock_date),
        "today": period_totals(trades, state.clock_date, state.clock_date),
        "weekly": period_totals(trades, sunday, state.clock_date),
        "monthly": period_totals(trades, state.clock_date.replace(day=1), state.clock_date),
        "yearly": period_totals(trades, state.clock_date.replace(month=1, day=1), state.clock_date),
    }
    decisions = []
    for decision, cycle in session.execute(
        select(DecisionLog, AutomationCycle)
        .join(AutomationCycle, DecisionLog.cycle_id == AutomationCycle.id)
        .order_by(DecisionLog.id.desc()).limit(50)
    ):
        decisions.append({
            "id": decision.id, "cycle_id": decision.cycle_id,
            "symbol": decision.symbol, "action": decision.action,
            "quantity": decision.quantity, "lot_id": decision.lot_id,
            "reason": decision.reason, "date": cycle.session_on.isoformat(),
            "revision": cycle.market_revision,
        })
    latest = session.scalar(select(AutomationCycle).order_by(
        AutomationCycle.market_revision.desc(), AutomationCycle.rules_revision.desc()
    ).limit(1))
    now = datetime.now(DHAKA)
    budget = session.get(ChatBudget, now.date())
    used_calls = budget.calls if budget else 0
    theses_views = [{
        "id": t.id,
        "symbol": t.symbol,
        "thesis": t.thesis,
        "created_on": t.created_on.isoformat(),
        "entry_price": float(t.entry_price),
        "canary_qty": t.canary_qty,
        "status": t.status,
        "observations_count": t.observations_count,
        "last_price_observed": float(t.last_price_observed),
        "notes": t.notes,
        "created_at": t.created_at,
    } for t in session.scalars(select(CanaryThesis).order_by(CanaryThesis.id.desc()))]

    skills_mgr = SkillsManager()
    active_skills = []
    for s in skills_mgr.list_skills():
        rev_count = session.scalar(
            select(func.count(HermesSkillRevision.id)).where(HermesSkillRevision.skill_name == s.name)
        ) or 0
        active_skills.append({
            "name": s.name,
            "title": s.title,
            "version": s.version,
            "tags": s.tags,
            "revision_count": rev_count,
        })

    recent_checkpoints = [{
        "id": cp.id,
        "action": cp.action,
        "description": cp.description,
        "date": cp.session_on.isoformat(),
        "reverted": cp.reverted,
        "created_at": cp.created_at,
    } for cp in session.scalars(select(HermesStateCheckpoint).order_by(HermesStateCheckpoint.id.desc()).limit(10))]

    durable_facts = [{
        "id": f.id,
        "symbol": f.symbol,
        "category": f.category,
        "fact": f.fact,
        "confidence": f.confidence,
    } for f in session.scalars(select(HermesDurableFact).where(HermesDurableFact.active == True).order_by(HermesDurableFact.id.desc()).limit(15))]

    return {
        "app": {
            "name": state.name, "version": VERSION, "mode": "DEMO", "source": "SYNTHETIC",
            "date": state.clock_date.isoformat(), "revision": state.revision,
            "rules_revision": state.rules_revision, "paused": state.paused,
            "active_bucket": active, "created_at": state.created_at,
        },
        "market_clock": {
            "now": now.isoformat(), "timezone": "Asia/Dhaka",
            "is_working_session": calendar.is_session(now.date()),
            "within_configured_hours": calendar.is_session(now.date())
            and settings.market_open <= now.time().replace(tzinfo=None) < settings.market_close,
            "configured_open": settings.market_open.strftime("%H:%M"),
            "configured_close": settings.market_close.strftime("%H:%M"),
            "schedule_verified": False, "calendar_verified": False,
            "holidays": sorted(day.isoformat() for day in settings.holidays),
        },
        "metrics": {
            "initial_capital": float(state.initial_capital),
            "available_cash": float(cash), "unsettled_proceeds": float(unsettled),
            "open_cost_basis": float(total_basis), "gross_market_value": float(total_gross_value),
            "estimated_exit_fees": float(estimated_exit_fees),
            "gross_equity": float(cash + unsettled + total_gross_value),
            "net_liquidation_equity": float(net_equity),
            "realized_pnl": float(realized), "unrealized_pnl": float(unrealized),
            "total_gain": float(realized + unrealized),
            "total_gain_pct": float((net_equity / state.initial_capital - 1) * HUNDRED),
            "fees_paid": float(sum((trade.fee for trade in trades), ZERO)),
            "mature_shares": sum(lot["remaining_qty"] for lot in lot_views if lot["is_mature"]),
            "locked_shares": sum(lot["remaining_qty"] for lot in lot_views if not lot["is_mature"]),
            "quarantined_count": sum(company["quarantined"] for company in company_views),
            "book_reconciled": money(cash + unsettled + total_basis) == money(state.initial_capital + realized),
            "equity_reconciled": money(net_equity - state.initial_capital) == money(realized + unrealized),
        },
        "periods": periods,
        "companies": company_views,
        "lots": lot_views,
        "buckets": [{
            "name": balance.name, "active": balance.name == active,
            "initial_cash": float(balance.initial_cash),
            "available_cash": float(balance.available_cash),
            "unsettled_proceeds": float(balance.unsettled_proceeds),
            "open_cost_basis": float(balance.open_cost_basis),
            "mature_shares": balance.mature_shares, "locked_shares": balance.locked_shares,
            "today_buy_spend": float(balance.today_buy_spend),
        } for balance in balances.values()],
        "trades": [trade_view(trade) for trade in reversed(trades[-100:])],
        "trade_count": len(trades),
        "decisions": decisions,
        "canary_theses": theses_views,
        "hermes": {
            "skills": active_skills,
            "checkpoints": recent_checkpoints,
            "durable_facts": durable_facts,
        },
        "latest_cycle": latest.result if latest else None,
        "market_map": build_market_map_payload(),
        "rule_audit": [{
            "id": audit.id, "symbol": audit.symbol, "before": audit.before,
            "after": audit.after, "date": audit.session_on.isoformat(), "created_at": audit.created_at,
        } for audit in session.scalars(select(RuleAudit).order_by(RuleAudit.id.desc()).limit(10))],
        "normalized_curve": normalized_watchlist(company_views),
        "fees": {
            "buy_rate": float(settings.buy_fee_rate), "sell_rate": float(settings.sell_fee_rate),
            "exact_unrounded_break_even_pct": float(
                ((1 + settings.buy_fee_rate) / (1 - settings.sell_fee_rate) - 1) * HUNDRED
            ),
        },
        "chat": {
            "provider": "openrouter" if settings.openrouter_api_key else "local",
            "model": settings.openrouter_model if settings.openrouter_api_key else None,
            "read_only": True, "daily_call_limit": settings.chat_daily_call_limit,
            "external_calls_today": used_calls,
            "external_calls_remaining": max(0, settings.chat_daily_call_limit - used_calls),
        },
        "connections": {"stocknow": False, "brokerage": False, "bo_account": False, "telegram": False},
        "notice": "All prices/scenarios/trades are synthetic. No live orders. No guaranteed recovery or returns.",
    }


def normalized_watchlist(companies: list[dict]) -> list[dict]:
    """Equal-weight normalized PRICE index, explicitly not portfolio performance."""
    observations: dict[str, list[Decimal]] = {}
    for company in companies:
        try:
            history = company["history"]
            baseline = decimal(history[0]["close"])
            if baseline <= ZERO or not baseline.is_finite():
                continue
            points = [(point["date"], decimal(point["close"]) / baseline * HUNDRED) for point in history]
            if any(not value.is_finite() or value <= ZERO for _day, value in points):
                continue
            for day, value in points:
                observations.setdefault(day, []).append(value)
        except (KeyError, IndexError, TypeError, ValueError, ArithmeticError):
            continue
    return [
        {"date": day, "value": float(sum(values, ZERO) / len(values))}
        for day, values in sorted(observations.items())
    ]
