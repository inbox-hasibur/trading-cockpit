"""Hermes Agentic Actions Engine.

Allows the AI orchestrator to execute real portfolio interventions:
- Emergency Quarantine + 90% Profit Lock / 10% Canary Holding
- Quarantine Restoration
- Explicit Buy / Sell Orders
- Tracking & Feedback on user-stated market theses
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import Settings
from backend.database import CanaryThesis, CompanyProfile, CustomRule, DecisionLog, PortfolioState, TaxLot, TradeLog
from backend.engine.money import ZERO, allocated_basis, decimal, money, price, purchase_amount, sale_amount, whole_shares
from backend.engine.t2_ledger import TradingCalendar, assert_ledger, bucket_balances


def emergency_quarantine_and_canary(
    session: Session,
    state: PortfolioState,
    settings: Settings,
    symbol: str,
    thesis_text: str,
) -> dict:
    calendar = TradingCalendar(settings.holidays, settings.bucket_anchor)
    company = session.get(CompanyProfile, symbol.upper())
    if company is None:
        raise ValueError(f"Company {symbol} not found in watchlist.")

    company.quarantined = True
    company.quarantine_reason = f"Hermes Agentic Quarantine: {thesis_text}"

    # Check open lots
    lots = list(session.scalars(
        select(TaxLot).where(TaxLot.symbol == company.symbol, TaxLot.remaining_qty > 0).order_by(TaxLot.id)
    ))
    total_shares = sum(lot.remaining_qty for lot in lots)
    total_basis = sum(lot.remaining_cost_basis for lot in lots)
    current_price = company.last_price

    sold_qty = 0
    canary_qty = total_shares
    realized_pnl = ZERO
    total_net_proceeds = ZERO

    # If holding shares and they are in profit, liquidate 90% to lock gains, keep 10% canary
    if total_shares > 0:
        net_val, _fee = sale_amount(total_shares, current_price, settings.sell_fee_rate)
        in_profit = net_val > total_basis

        if in_profit:
            canary_qty = max(1, int(round(total_shares * Decimal("0.10")))) if total_shares >= 2 else 1
            shares_to_sell = total_shares - canary_qty
            remaining_to_sell = shares_to_sell

            for lot in lots:
                if remaining_to_sell <= 0:
                    break
                sell_slice = min(lot.remaining_qty, remaining_to_sell)
                if sell_slice <= 0:
                    continue

                proceeds, fee = sale_amount(sell_slice, current_price, settings.sell_fee_rate)
                cost_slice = allocated_basis(lot.remaining_cost_basis, lot.remaining_qty, sell_slice)
                lot_pnl = max(ZERO, proceeds - cost_slice)

                lot.remaining_qty -= sell_slice
                lot.remaining_cost_basis -= cost_slice
                remaining_to_sell -= sell_slice
                sold_qty += sell_slice
                realized_pnl += lot_pnl
                total_net_proceeds += proceeds

                trade = TradeLog(
                    trade_key=f"EMERGENCY_SELL:{cycle_key(state)}:{lot.id}:{uuid4().hex[:6]}",
                    cycle_id=None,
                    lot_id=lot.id,
                    symbol=company.symbol,
                    side="SELL",
                    quantity=sell_slice,
                    price=current_price,
                    gross_amount=money(sell_slice * current_price),
                    fee=fee,
                    net_cash_change=proceeds,
                    realized_pnl=lot_pnl,
                    bucket=lot.bucket,
                    trade_on=state.clock_date,
                    settles_on=calendar.add_sessions(state.clock_date, company.settlement_days),
                    reason=f"HERMES AGENTIC EMERGENCY EXIT (90% profit locked, 10% canary kept): {thesis_text}",
                    source="HERMES_AGENTIC",
                )
                session.add(trade)

    thesis = CanaryThesis(
        symbol=company.symbol,
        thesis=thesis_text,
        created_on=state.clock_date,
        entry_price=current_price,
        canary_qty=canary_qty,
        last_price_observed=current_price,
        status="OBSERVING",
        notes=(
            f"Exit {sold_qty} shares with ৳{realized_pnl:,.2f} profit. "
            f"Observing {canary_qty} canary shares for thesis confirmation."
            if sold_qty > 0
            else f"Quarantined. Holding {canary_qty} shares (Strict No-Loss Guard; no panic sell at loss)."
        ),
    )
    session.add(thesis)
    state.rules_revision += 1
    session.flush()
    assert_ledger(session, state)

    return {
        "symbol": company.symbol,
        "action": "QUARANTINE_AND_CANARY_EXIT",
        "quarantined": True,
        "sold_qty": sold_qty,
        "canary_qty": canary_qty,
        "realized_pnl": float(realized_pnl),
        "thesis_id": thesis.id,
        "thesis": thesis_text,
    }


def restore_quarantine(
    session: Session,
    state: PortfolioState,
    symbol: str,
    reason: str = "Restored by user/agent review",
) -> dict:
    company = session.get(CompanyProfile, symbol.upper())
    if company is None:
        raise ValueError(f"Company {symbol} not found.")

    company.quarantined = False
    company.quarantine_reason = ""

    theses = list(session.scalars(
        select(CanaryThesis).where(CanaryThesis.symbol == company.symbol, CanaryThesis.status == "OBSERVING")
    ))
    for t in theses:
        t.status = "RESOLVED"
        t.notes += f" | {reason}"

    state.rules_revision += 1
    session.flush()

    return {
        "symbol": company.symbol,
        "action": "RESTORED",
        "quarantined": False,
        "resolved_theses_count": len(theses),
    }


def check_canary_theses(session: Session, state: PortfolioState) -> list[dict]:
    theses = list(session.scalars(
        select(CanaryThesis).where(CanaryThesis.status == "OBSERVING")
    ))
    updates = []
    for t in theses:
        company = session.get(CompanyProfile, t.symbol)
        if not company:
            continue
        t.observations_count += 1
        t.last_price_observed = company.last_price
        drop_pct = (t.entry_price - company.last_price) / t.entry_price * Decimal("100")

        if drop_pct >= Decimal("8"):
            t.status = "CONFIRMED_LOSS"
            t.notes = (
                f"Thesis confirmed: price plunged {float(drop_pct):.1f}% "
                f"from ৳{t.entry_price} to ৳{company.last_price}. 90% capital safely protected!"
            )
            updates.append({"symbol": t.symbol, "status": t.status, "message": t.notes})
        elif t.observations_count >= 3 and drop_pct <= Decimal("-2"):
            # Price actually gained or held strongly
            t.status = "FALSE_ALARM_STABLE"
            t.notes = (
                f"Thesis reviewed: observed over {t.observations_count} sessions. "
                f"Price has risen/held at ৳{company.last_price}. Company is healthy."
            )
            updates.append({"symbol": t.symbol, "status": t.status, "message": t.notes})
    if updates:
        session.flush()
    return updates


def execute_agentic_buy(
    session: Session,
    state: PortfolioState,
    settings: Settings,
    symbol: str,
    requested_qty: int | None = None,
) -> dict:
    calendar = TradingCalendar(settings.holidays, settings.bucket_anchor)
    company = session.get(CompanyProfile, symbol.upper())
    if company is None:
        raise ValueError(f"Company {symbol} not found.")
    if company.quarantined:
        raise ValueError(f"Cannot buy {symbol}: Company is under Crash Quarantine.")

    balances = bucket_balances(session, state)
    active_name = calendar.bucket_for(state.clock_date)
    active = balances[active_name]

    if active.available_cash < settings.min_buy_notional:
        raise ValueError(f"Insufficient active bucket ({active_name}) cash for purchase.")

    unit_price = company.last_price
    if requested_qty:
        quantity = requested_qty
        cost, fee = purchase_amount(quantity, unit_price, settings.buy_fee_rate)
        if cost > active.available_cash:
            raise ValueError(f"Requested {quantity} shares cost ৳{cost:,.2f}, exceeds cash ৳{active.available_cash:,.2f}.")
    else:
        # Default smart sizing
        budget = min(active.available_cash, money(state.initial_capital * Decimal("0.10")))
        quantity = whole_shares(budget / (unit_price * (1 + settings.buy_fee_rate)))
        cost, fee = purchase_amount(quantity, unit_price, settings.buy_fee_rate)

    if quantity <= 0:
        raise ValueError("Budget too small to buy a whole share.")

    lot = TaxLot(
        symbol=company.symbol,
        bucket=active_name,
        acquired_on=state.clock_date,
        matures_on=calendar.add_sessions(state.clock_date, company.settlement_days),
        original_qty=quantity,
        remaining_qty=quantity,
        buy_price=unit_price,
        buy_fee=fee,
        original_cost_basis=cost,
        remaining_cost_basis=cost,
        cycle_base_qty=quantity,
        peak_price=unit_price,
    )
    session.add(lot)
    session.flush()

    trade = TradeLog(
        trade_key=f"AGENT_BUY:{cycle_key(state)}:{lot.id}:{uuid4().hex[:6]}",
        cycle_id=None,
        lot_id=lot.id,
        symbol=company.symbol,
        side="BUY",
        quantity=quantity,
        price=unit_price,
        gross_amount=money(quantity * unit_price),
        fee=fee,
        net_cash_change=-cost,
        realized_pnl=ZERO,
        bucket=active_name,
        trade_on=state.clock_date,
        settles_on=lot.matures_on,
        reason=f"Hermes Agentic buy execution requested by user/assistant.",
        source="HERMES_AGENTIC",
    )
    session.add(trade)
    session.flush()
    assert_ledger(session, state)

    return {
        "symbol": company.symbol,
        "side": "BUY",
        "quantity": quantity,
        "price": float(unit_price),
        "cost": float(cost),
        "bucket": active_name,
    }


def execute_agentic_sell(
    session: Session,
    state: PortfolioState,
    settings: Settings,
    symbol: str,
    requested_qty: int,
) -> dict:
    if requested_qty <= 0:
        raise ValueError(f"Requested sell quantity must be positive, got {requested_qty}.")
    calendar = TradingCalendar(settings.holidays, settings.bucket_anchor)
    company = session.get(CompanyProfile, symbol.upper())
    if company is None:
        raise ValueError(f"Company {symbol} not found.")

    mature_lots = list(session.scalars(
        select(TaxLot)
        .where(
            TaxLot.symbol == company.symbol,
            TaxLot.remaining_qty > 0,
            TaxLot.matures_on <= state.clock_date,
        )
        .order_by(TaxLot.id)
    ))
    mature_qty = sum(lot.remaining_qty for lot in mature_lots)
    if mature_qty <= 0:
        immature_lots = list(session.scalars(
            select(TaxLot).where(TaxLot.symbol == company.symbol, TaxLot.remaining_qty > 0)
        ))
        if immature_lots:
            earliest = min(lot.matures_on for lot in immature_lots)
            raise ValueError(f"Cannot sell {company.symbol}: shares are settlement-locked until {earliest.isoformat()} (T+2 lock).")
        raise ValueError(f"Cannot sell {company.symbol}: no open shares held.")

    if requested_qty > mature_qty:
        raise ValueError(f"Cannot sell {requested_qty} shares of {company.symbol}: only {mature_qty} mature shares available.")

    unit_price = company.last_price

    # Verify no net-loss exit across mature lots to be sold
    remaining = requested_qty
    for lot in mature_lots:
        if remaining <= 0:
            break
        sell_slice = min(lot.remaining_qty, remaining)
        proceeds, _fee = sale_amount(sell_slice, unit_price, settings.sell_fee_rate)
        cost_slice = allocated_basis(lot.remaining_cost_basis, lot.remaining_qty, sell_slice)
        if proceeds < cost_slice:
            net_ret = (proceeds / cost_slice - 1) * Decimal("100")
            raise ValueError(
                f"Cannot sell {company.symbol} at ৳{unit_price}: net return is {float(net_ret):.2f}% (net loss). Strict No-Loss policy holds."
            )
        remaining -= sell_slice

    remaining = requested_qty
    total_proceeds = ZERO
    total_pnl = ZERO
    for lot in mature_lots:
        if remaining <= 0:
            break
        sell_slice = min(lot.remaining_qty, remaining)
        proceeds, fee = sale_amount(sell_slice, unit_price, settings.sell_fee_rate)
        cost_slice = allocated_basis(lot.remaining_cost_basis, lot.remaining_qty, sell_slice)
        lot_pnl = max(ZERO, proceeds - cost_slice)

        lot.remaining_qty -= sell_slice
        lot.remaining_cost_basis -= cost_slice
        remaining -= sell_slice
        total_proceeds += proceeds
        total_pnl += lot_pnl

        trade = TradeLog(
            trade_key=f"AGENT_SELL:{cycle_key(state)}:{lot.id}:{uuid4().hex[:6]}",
            cycle_id=None,
            lot_id=lot.id,
            symbol=company.symbol,
            side="SELL",
            quantity=sell_slice,
            price=unit_price,
            gross_amount=money(sell_slice * unit_price),
            fee=fee,
            net_cash_change=proceeds,
            realized_pnl=lot_pnl,
            bucket=lot.bucket,
            trade_on=state.clock_date,
            settles_on=calendar.add_sessions(state.clock_date, company.settlement_days),
            reason=f"Hermes Agentic sell execution requested by user/assistant.",
            source="HERMES_AGENTIC",
        )
        session.add(trade)

    session.flush()
    assert_ledger(session, state)

    return {
        "symbol": company.symbol,
        "side": "SELL",
        "quantity": requested_qty,
        "price": float(unit_price),
        "proceeds": float(total_proceeds),
        "realized_pnl": float(total_pnl),
    }


def cycle_key(state: PortfolioState) -> str:
    return f"{state.clock_date}:{state.revision}:{state.rules_revision}"

