from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal as D

import pytest

from backend.engine.curve_analyzer import analyze_curve
from backend.engine.money import allocated_basis, purchase_amount, sale_amount
from backend.engine.sequential_seller import SellState, plan_sale
from backend.engine.t2_ledger import TradingCalendar


def test_settlement_skips_weekend_and_holiday():
    thursday = date(2026, 11, 5)
    calendar = TradingCalendar(holidays=frozenset({date(2026, 11, 8)}))
    assert calendar.add_sessions(thursday, 2) == date(2026, 11, 10)
    assert calendar.add_sessions(date(2026, 11, 10), -2) == thursday
    assert len({calendar.bucket_for(calendar.add_sessions(thursday, i)) for i in range(3)}) == 3


def history(values):
    start = date(2026, 1, 1)
    return [{"date": (start + timedelta(days=i)).isoformat(), "close": str(v)}
            for i, v in enumerate(values)]


def test_curve_crash_and_invalid_data():
    sample = history([100, 102, 101, 103, 102, 101, 70])
    assert analyze_curve(sample, as_of=date(2026, 1, 7)).signal == "CRASH_QUARANTINE"
    sample[-1]["close"] = "NaN"
    assert analyze_curve(sample, as_of=date(2026, 1, 7)).signal == "INVALID_DATA"
    assert analyze_curve(sample[:3], as_of=date(2026, 1, 7)).signal == "WAIT_DATA"


def test_fees_and_basis_allocation():
    cost, fee = purchase_amount(100, D("100"), D("0.005"))
    proceeds, sell_fee = sale_amount(100, D("101"), D("0.005"))
    assert (cost, fee, proceeds, sell_fee) == (D("10050"), D("50"), D("10049.50"), D("50.50"))
    assert proceeds < cost  # A 1% price rise is not net break-even.
    basis = D("10.01")
    first = allocated_basis(basis, 3, 1)
    assert first + allocated_basis(basis - first, 2, 2) == basis


def test_tiers_and_recovery_hold():
    today = date(2026, 11, 3)
    state = SellState(100, D("10050"), today, 100, D("100"))
    locked = plan_sale(replace(state, matures_on=today + timedelta(days=1)),
                       current_price=D("110"), as_of=today)
    assert locked.action == "SETTLEMENT_LOCK"
    assert plan_sale(state, current_price=D("101"), as_of=today).action == "NO_LOSS_HOLD"
    first = plan_sale(state, current_price=D("104"), as_of=today)
    assert (first.action, first.quantity) == ("SELL_TIER_1", 25)
    second = plan_sale(first.state, current_price=D("107"), as_of=today)
    assert (second.action, second.quantity) == ("SELL_TIER_2", 25)
    split = plan_sale(second.state, current_price=D("103"), as_of=today)
    assert (split.action, split.quantity, split.state.remaining_qty) == ("PULLBACK_SPLIT", 25, 25)
    held = plan_sale(split.state, current_price=D("103"), as_of=today)
    assert held.action == "RECOVERY_HOLD" and held.quantity == 0
    recovered = plan_sale(held.state, current_price=D("108"), as_of=today)
    assert recovered.action == "SELL_TIER_1" and recovered.quantity == 6


def test_odd_share_and_invalid_rules():
    state = SellState(1, D("100"), date(2026, 1, 1), 1, D("120"))
    assert plan_sale(state, current_price=D("110"), as_of=date(2026, 1, 2)).action == "HOLD_ODD_SHARE"
    with pytest.raises(ValueError):
        plan_sale(state, current_price=D("110"), as_of=date(2026, 1, 2), pullback_pct=D("0"))
