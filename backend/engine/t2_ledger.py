"""Working-session settlement and conservative, fully funded rolling buckets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import PortfolioState, TaxLot, TradeLog
from backend.engine.money import CENT, ZERO, money

BUCKETS = ("A", "B", "C")


@dataclass(frozen=True)
class TradingCalendar:
    holidays: frozenset[date] = frozenset()
    anchor: date = date(2024, 1, 7)

    def is_session(self, day: date) -> bool:
        return day.weekday() not in {4, 5} and day not in self.holidays

    def on_or_before(self, day: date) -> date:
        while not self.is_session(day):
            day -= timedelta(days=1)
        return day

    def add_sessions(self, day: date, count: int) -> date:
        direction = 1 if count >= 0 else -1
        for _ in range(abs(count)):
            day += timedelta(days=direction)
            while not self.is_session(day):
                day += timedelta(days=direction)
        return day

    def session_distance(self, start: date, end: date) -> int:
        if end < start:
            return -self.session_distance(end, start)
        count = 0
        while start < end:
            start += timedelta(days=1)
            count += int(self.is_session(start))
        return count

    def bucket_for(self, day: date) -> str:
        if not self.is_session(day):
            raise ValueError("A non-trading date has no active buy bucket.")
        return BUCKETS[self.session_distance(self.anchor, day) % 3]


@dataclass
class BucketBalance:
    name: str
    initial_cash: Decimal
    available_cash: Decimal
    unsettled_proceeds: Decimal = ZERO
    open_cost_basis: Decimal = ZERO
    mature_shares: int = 0
    locked_shares: int = 0
    today_buy_spend: Decimal = ZERO


def bucket_balances(session: Session, state: PortfolioState) -> dict[str, BucketBalance]:
    base = (state.initial_capital / 3).quantize(CENT, rounding="ROUND_DOWN")
    allocations = {"A": base, "B": base, "C": state.initial_capital - 2 * base}
    balances = {
        name: BucketBalance(name=name, initial_cash=value, available_cash=value)
        for name, value in allocations.items()
    }
    trades = session.scalars(select(TradeLog).where(TradeLog.trade_on <= state.clock_date))
    for trade in trades:
        bucket = balances[trade.bucket]
        if trade.side == "BUY":
            bucket.available_cash += trade.net_cash_change  # Negative, including buy fee.
            if trade.trade_on == state.clock_date:
                bucket.today_buy_spend -= trade.net_cash_change
        elif trade.settles_on <= state.clock_date:
            bucket.available_cash += trade.net_cash_change
        else:
            bucket.unsettled_proceeds += trade.net_cash_change
    lots = session.scalars(select(TaxLot).where(TaxLot.remaining_qty > 0))
    for lot in lots:
        bucket = balances[lot.bucket]
        bucket.open_cost_basis += lot.remaining_cost_basis
        if lot.matures_on <= state.clock_date:
            bucket.mature_shares += lot.remaining_qty
        else:
            bucket.locked_shares += lot.remaining_qty
    for bucket in balances.values():
        bucket.available_cash = money(bucket.available_cash)
        if bucket.available_cash < ZERO:
            raise RuntimeError(f"Ledger invariant violated: negative cash in bucket {bucket.name}.")
    return balances


def assert_ledger(session: Session, state: PortfolioState) -> None:
    """Book assets must equal initial capital plus realized P/L, to the paisa."""
    balances = bucket_balances(session, state)
    book_assets = sum(
        (b.available_cash + b.unsettled_proceeds + b.open_cost_basis for b in balances.values()), ZERO
    )
    realized = sum(
        session.scalars(select(TradeLog.realized_pnl).where(TradeLog.trade_on <= state.clock_date)),
        ZERO,
    )
    if money(book_assets) != money(state.initial_capital + realized):
        raise RuntimeError("Ledger invariant violated: cash, lots and realized P/L do not reconcile.")
