"""Synthetic, capital-backed fixtures. These prices are NOT current market data."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from backend.config import DHAKA, Settings
from backend.database import CompanyProfile, CustomRule, PortfolioState, TaxLot, TradeLog
from backend.engine.money import decimal, money, price, purchase_amount
from backend.engine.t2_ledger import TradingCalendar, bucket_balances

# The crash symbol is an invented test scenario, not an opinion about that issuer.
FIXTURES = (
    ("BANKASIA", "Bank Asia · demo", "BANK", "GSC_L2", "10", [20.6, 21.1, 20.9, 20.2, 21, 20.4, 19.8]),
    ("EXIM1STMF", "EXIM 1st Mutual Fund · demo", "MUTUAL_FUND", "GSC", "15",
     [5.5, 5.65, 5.55, 5.35, 5.6, 5.4, 5.2]),
    ("SQURPHARMA", "Square Pharma · demo", "PHARMA", "GSC_L1", "30", [202, 205, 208, 211, 214, 215, 216]),
    ("BXPHARMA", "Beximco Pharma · crash fixture", "PHARMA", "GSC", "10", [91, 92, 93, 92, 91, 90, 58]),
    ("GP", "Grameenphone · demo", "TELECOM", "GSC", "25", [260, 264, 270, 275, 273, 269, 265]),
)


def seed_demo(session: Session, settings: Settings) -> None:
    existing = session.get(PortfolioState, 1)
    if existing is not None:
        if (
            existing.calendar_holidays != sorted(day.isoformat() for day in settings.holidays)
            or existing.bucket_anchor != settings.bucket_anchor
        ):
            raise ValueError("Calendar differs from the saved demo. Use a new database for that calendar.")
        return
    calendar = TradingCalendar(settings.holidays, settings.bucket_anchor)
    today = calendar.on_or_before(settings.demo_start_date or datetime.now(DHAKA).date())
    state = PortfolioState(
        id=1,
        initial_capital=money(settings.initial_capital),
        clock_date=today,
        calendar_holidays=sorted(day.isoformat() for day in settings.holidays),
        bucket_anchor=settings.bucket_anchor,
    )
    session.add(state)
    for symbol, name, sector, category, allocation, values in FIXTURES:
        history = [
            {"date": calendar.add_sessions(today, index - 6).isoformat(), "close": str(price(decimal(value)))}
            for index, value in enumerate(values)
        ]
        session.add(CompanyProfile(
            symbol=symbol,
            name=name,
            sector=sector,
            watchlist_category=category,
            settlement_days=settings.settlement_days,
            last_price=price(decimal(values[-1])),
            price_history=history,
            quote_on=today,
        ))
    session.flush()
    for symbol, _name, _sector, _category, allocation, _values in FIXTURES:
        session.add(CustomRule(symbol=symbol, buy_allocation_pct=decimal(allocation)))
    session.flush()

    # Keep seed lots fully funded even when a user chooses smaller initial capital.
    scale = settings.initial_capital / Decimal("15000")
    lot_specs = (
        ("BANKASIA", 0, 50, "20", "20"),
        ("EXIM1STMF", -1, 100, "5", "5.2"),
        ("SQURPHARMA", -2, 20, "200", "216"),
        ("BXPHARMA", -2, 10, "90", "93"),
        ("GP", -3, 8, "240", "275"),
    )
    for symbol, offset, base_quantity, buy_at, observed_peak in lot_specs:
        acquired_on = calendar.add_sessions(today, offset)
        quantity = max(1, int(base_quantity * scale))
        cost, fee = purchase_amount(quantity, decimal(buy_at), settings.buy_fee_rate)
        lot = TaxLot(
            symbol=symbol,
            bucket=calendar.bucket_for(acquired_on),
            acquired_on=acquired_on,
            matures_on=calendar.add_sessions(acquired_on, settings.settlement_days),
            original_qty=quantity,
            remaining_qty=quantity,
            buy_price=decimal(buy_at),
            buy_fee=fee,
            original_cost_basis=cost,
            remaining_cost_basis=cost,
            cycle_base_qty=quantity,
            peak_price=decimal(observed_peak),
        )
        session.add(lot)
        session.flush()
        session.add(TradeLog(
            trade_key=f"SEED:{symbol}",
            lot_id=lot.id,
            symbol=symbol,
            side="BUY",
            quantity=quantity,
            price=lot.buy_price,
            gross_amount=money(quantity * lot.buy_price),
            fee=fee,
            net_cash_change=-cost,
            realized_pnl=Decimal("0"),
            bucket=lot.bucket,
            trade_on=acquired_on,
            settles_on=lot.matures_on,
            reason="Synthetic opening holding, funded from its rolling bucket.",
            source="DEMO_SEED",
        ))
    session.flush()
    bucket_balances(session, state)  # Refuse to seed an unfunded ledger.
