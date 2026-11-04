"""Explainable range heuristics, not predictions or a solvency assessment."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from statistics import median
from typing import Any

from backend.engine.money import HUNDRED, ZERO, decimal


@dataclass(frozen=True)
class CurveAnalysis:
    signal: str
    reason: str
    low: Decimal = ZERO
    high: Decimal = ZERO
    range_position: Decimal = ZERO
    day_change_pct: Decimal = ZERO
    window_change_pct: Decimal = ZERO
    drawdown_pct: Decimal = ZERO
    typical_daily_move_pct: Decimal = ZERO
    net_upside_to_range_high_pct: Decimal = ZERO

    def to_dict(self) -> dict[str, Any]:
        return {
            field: float(value) if isinstance(value, Decimal) else value
            for field, value in self.__dict__.items()
        }


def analyze_curve(
    history: list[dict[str, str]],
    *,
    as_of: date,
    buy_fee_rate: Decimal = Decimal("0.005"),
    sell_fee_rate: Decimal = Decimal("0.005"),
    buy_zone_fraction: Decimal = Decimal("0.35"),
    crash_daily_pct: Decimal = Decimal("8"),
    crash_drawdown_pct: Decimal = Decimal("15"),
    min_net_upside_pct: Decimal = Decimal("1.5"),
) -> CurveAnalysis:
    if len(history) < 7:
        return CurveAnalysis("WAIT_DATA", "At least seven session closes are required.")
    try:
        window = history[-15:]
        dates = [date.fromisoformat(point["date"]) for point in window]
        closes = [decimal(point["close"]) for point in window]
        if any(not close.is_finite() or close <= ZERO for close in closes):
            raise ValueError("Nonpositive or nonfinite close.")
        if any(earlier >= later for earlier, later in zip(dates, dates[1:])):
            raise ValueError("Dates must be unique and strictly increasing.")
        if dates[-1] > as_of:
            raise ValueError("A future observation cannot be used.")
    except (KeyError, TypeError, ValueError, InvalidOperation):
        return CurveAnalysis("INVALID_DATA", "Invalid prices/dates; new buys and sells are blocked.")
    if dates[-1] < as_of:
        return CurveAnalysis("STALE_DATA", "No quote for the current simulated session; trading blocked.")

    current, previous = closes[-1], closes[-2]
    low, high = min(closes[:-1]), max(closes[:-1])
    day_change = (current / previous - 1) * HUNDRED
    drawdown = max(ZERO, (1 - current / high) * HUNDRED)
    prior_moves = [abs((b / a - 1) * HUNDRED) for a, b in zip(closes[:-2], closes[1:-1])]
    typical_move = median(prior_moves)
    position = (current - low) / (high - low) if high > low else ZERO
    position = min(Decimal(1), max(ZERO, position))
    net_upside = (
        high * (1 - sell_fee_rate) / (current * (1 + buy_fee_rate)) - 1
    ) * HUNDRED
    metrics = {
        "low": low,
        "high": high,
        "range_position": position,
        "day_change_pct": day_change,
        "window_change_pct": (current / closes[0] - 1) * HUNDRED,
        "drawdown_pct": drawdown,
        "typical_daily_move_pct": typical_move,
        "net_upside_to_range_high_pct": net_upside,
    }
    # The relative guard supplements, never weakens, the absolute safety limits.
    unusual_decline = max(Decimal("5"), typical_move * 4)
    if -day_change >= crash_daily_pct or -day_change >= unusual_decline:
        return CurveAnalysis(
            "CRASH_QUARANTINE",
            f"Abnormal {abs(day_change):.2f}% session decline; block buys and require review.",
            **metrics,
        )
    if drawdown >= crash_drawdown_pct:
        return CurveAnalysis(
            "CRASH_QUARANTINE",
            f"{drawdown:.2f}% below the recent high; block buys, not a diagnosis of insolvency.",
            **metrics,
        )
    if high == low:
        return CurveAnalysis("WAIT_RANGE", "No demonstrated oscillation range.", **metrics)
    if position <= buy_zone_fraction:
        if net_upside < min_net_upside_pct:
            return CurveAnalysis(
                "WAIT_FEE_ROOM",
                f"Range rebound leaves only {net_upside:.2f}% estimated net room after fees.",
                **metrics,
            )
        return CurveAnalysis(
            "BUY_ZONE",
            f"Healthy low-range pattern; {net_upside:.2f}% estimated net room, not a forecast.",
            **metrics,
        )
    if position >= Decimal("0.8"):
        return CurveAnalysis(
            "SELL_ZONE", "Upper normal range; only the matured net-profit seller may exit.", **metrics
        )
    return CurveAnalysis("MID_RANGE", "Inside the normal range; wait for a better entry.", **metrics)
