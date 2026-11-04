"""Shared, read-only assessment used by the cockpit and the orchestrator."""

from dataclasses import replace
from datetime import date

from backend.adapters.stocknow_adapter import DemoQuote, QuoteError, StockNowAdapter
from backend.config import Settings
from backend.database import CompanyProfile, CustomRule
from backend.engine.curve_analyzer import CurveAnalysis, analyze_curve
from backend.engine.money import decimal

BLOCK_ALL_TRADING = {"INVALID_DATA", "STALE_DATA", "WAIT_DATA"}


def assess_company(
    company: CompanyProfile,
    rule: CustomRule,
    settings: Settings,
    as_of: date,
    adapter: StockNowAdapter,
) -> tuple[CurveAnalysis, DemoQuote | None]:
    try:
        quote = adapter.quote(company, as_of)
    except QuoteError as exc:
        return CurveAnalysis("INVALID_DATA", str(exc)), None
    analysis = analyze_curve(
        quote.history,
        as_of=as_of,
        buy_fee_rate=settings.buy_fee_rate,
        sell_fee_rate=settings.sell_fee_rate,
        buy_zone_fraction=rule.buy_zone_fraction,
        crash_daily_pct=rule.crash_daily_pct,
        crash_drawdown_pct=rule.crash_drawdown_pct,
        min_net_upside_pct=decimal(rule.profit_tiers[0]),
    )
    if company.quarantined and analysis.signal not in BLOCK_ALL_TRADING:
        analysis = replace(
            analysis,
            signal="CRASH_QUARANTINE",
            reason=company.quarantine_reason or "Persisted quarantine; review required before buys.",
        )
    return analysis, quote
