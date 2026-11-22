"""Realistic Order-Book Queue Simulator for TradeXpress SHADOW_DUMMY Execution.

Simulates exchange execution against live passively sniffed Bid/Offer queues and Level-2 depth.
Runs 100% locally with ZERO real BDT capital risk, enforcing T+2 settlement maturity,
Strict No-Loss hold, realistic ~0.40% broker fee + VAT accounting, and 2-step limit confirmation.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.adapters.base import (
    BrokerOrderExecutor,
    MarketQuote,
    from_tradexpress_symbol,
    to_tradexpress_symbol,
    validate_tradexpress_order_safety,
)
from backend.adapters.tradexpress.passive_feed import (
    TradeXpressPassiveFeed,
    get_global_passive_feed,
)
from backend.config import Settings, utc_now_iso
from backend.database import (
    CompanyProfile,
    Database,
    KernelStateCheckpoint,
    PortfolioState,
    ShadowOrder,
    TaxLot,
    TradeLearningLog,
    TradeLog,
    portfolio_state,
)
from backend.engine.checkpoint import CheckpointManager
from backend.engine.money import (
    ZERO,
    allocated_basis,
    calculate_broker_fee_breakdown,
    decimal,
    money,
    price,
    whole_shares,
)
from backend.engine.t2_ledger import TradingCalendar, assert_ledger, bucket_balances

logger = logging.getLogger("hummingbird.tradexpress.shadow_simulator")

# LankaBangla TradeXpress default effective fee (~0.40% commission + 15% VAT on commission)
DEFAULT_TRADEXPRESS_COMMISSION_RATE = Decimal("0.004")
DEFAULT_VAT_RATE = Decimal("0.15")


class TradeXpressShadowSimulator(BrokerOrderExecutor):
    """Realistic limit order simulator executing against passive Level-2 order depth."""

    def __init__(
        self,
        database: Database,
        settings: Settings,
        feed: TradeXpressPassiveFeed | None = None,
    ) -> None:
        self.database = database
        self.settings = settings
        self.feed = feed or get_global_passive_feed(database)
        self.calendar = TradingCalendar(settings.holidays, settings.bucket_anchor)

    def validate_order(
        self,
        session: Session,
        *,
        symbol: str,
        side: str,
        quantity: int,
        limit_price: Decimal,
        order_type: str = "LIMIT",
        tif: str = "DAY",
        all_or_none: bool = False,
        session_phase: str = "CONTINUOUS",
        allow_offhours_na: bool = True,
    ) -> tuple[bool, list[str]]:
        """Validates order against TradeXpress and DSE safety invariants."""
        clean_symbol = from_tradexpress_symbol(symbol)
        company = session.get(CompanyProfile, clean_symbol)

        quote = self.feed.get_all_quotes().get(clean_symbol)
        sett_type = quote.settlement_type if quote else (getattr(company, "settlement_type", "PUBLIC") if company else "PUBLIC")
        sym_cat = quote.symbol_category if quote else (getattr(company, "symbol_category", "A") if company else "A")
        min_lim = quote.min_limit if quote else (getattr(company, "min_limit", None) if company else None)
        max_lim = quote.max_limit if quote else (getattr(company, "max_limit", None) if company else None)
        ltp = quote.ltp if quote else (company.last_price if company else None)

        cached_sett = getattr(company, "settlement_type", "PUBLIC") if company else "PUBLIC"
        cached_cat = getattr(company, "symbol_category", "A") if company else "A"

        return validate_tradexpress_order_safety(
            symbol=clean_symbol,
            side=side,
            quantity=quantity,
            price=limit_price,
            order_type=order_type,
            tif=tif,
            all_or_none=all_or_none,
            settlement_type=sett_type,
            symbol_category=sym_cat,
            min_limit=min_lim,
            max_limit=max_lim,
            ltp=ltp,
            session_phase=session_phase,
            allow_offhours_na=allow_offhours_na,
            cached_settlement_type=cached_sett,
            cached_symbol_category=cached_cat,
        )

    async def execute_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        price: Decimal,
        order_type: str = "LIMIT",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """BrokerOrderExecutor interface entry point."""
        return self.submit_shadow_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            limit_price=price,
            order_type=order_type,
            **kwargs,
        )

    def submit_shadow_order(
        self,
        *,
        symbol: str,
        side: str,
        quantity: int,
        limit_price: Decimal,
        order_type: str = "LIMIT",
        tif: str = "DAY",
        confirm: bool = True,
        actor: str = "AUTOTRADER",
        reason: str = "",
        portfolio_id: str = "H9210_SHADOW",
        allow_offhours_ltp_fill: bool = True,
        session_phase: str = "CONTINUOUS",
        session: Session | None = None,
        record_tax_lot: bool = True,
    ) -> dict[str, Any]:
        """Submits an order into the shadow simulator with 2-step verification support."""
        clean_symbol = from_tradexpress_symbol(symbol)
        side_norm = side.strip().upper()
        gross = money(quantity * limit_price)
        fee_info = calculate_broker_fee_breakdown(
            gross,
            commission_rate=DEFAULT_TRADEXPRESS_COMMISSION_RATE,
            vat_rate=DEFAULT_VAT_RATE,
        )
        estimated_fee = fee_info["total_fee"]
        net_val = gross + estimated_fee if side_norm == "BUY" else gross - estimated_fee

        # Step 1: Preview Ticket (if confirm=False, mirrors Step 1 input read-back)
        if not confirm:
            return {
                "step": 1,
                "status": "PREVIEW",
                "symbol": clean_symbol,
                "tradexpress_symbol": to_tradexpress_symbol(clean_symbol),
                "side": side_norm,
                "quantity": quantity,
                "limit_price": float(limit_price),
                "order_value": float(gross),
                "commission": float(fee_info["commission"]),
                "vat": float(fee_info["vat"]),
                "estimated_fee": float(estimated_fee),
                "net_value": float(net_val),
                "order_type": order_type,
                "tif": tif,
                "portfolio_id": portfolio_id,
                "message": "Order preview verified. Dispatch with confirm=true to submit.",
            }

        # Step 2: Confirmation & Execution
        if session is not None:
            return self._execute_shadow_order_in_session(
                session=session,
                clean_symbol=clean_symbol,
                side_norm=side_norm,
                quantity=quantity,
                limit_price=limit_price,
                order_type=order_type,
                tif=tif,
                actor=actor,
                reason=reason,
                portfolio_id=portfolio_id,
                allow_offhours_ltp_fill=allow_offhours_ltp_fill,
                session_phase=session_phase,
                record_tax_lot=record_tax_lot,
            )

        with self.database.write() as write_session:
            return self._execute_shadow_order_in_session(
                session=write_session,
                clean_symbol=clean_symbol,
                side_norm=side_norm,
                quantity=quantity,
                limit_price=limit_price,
                order_type=order_type,
                tif=tif,
                actor=actor,
                reason=reason,
                portfolio_id=portfolio_id,
                allow_offhours_ltp_fill=allow_offhours_ltp_fill,
                session_phase=session_phase,
                record_tax_lot=record_tax_lot,
            )

    def _execute_shadow_order_in_session(
        self,
        session: Session,
        clean_symbol: str,
        side_norm: str,
        quantity: int,
        limit_price: Decimal,
        order_type: str,
        tif: str,
        actor: str,
        reason: str,
        portfolio_id: str,
        allow_offhours_ltp_fill: bool,
        session_phase: str,
        record_tax_lot: bool,
    ) -> dict[str, Any]:
        state = portfolio_state(session)
        today = state.clock_date
        order_ref = f"SHADOW-{uuid4().hex[:10].upper()}"
        gross = money(quantity * limit_price)
        fee_info = calculate_broker_fee_breakdown(
            gross,
            commission_rate=DEFAULT_TRADEXPRESS_COMMISSION_RATE,
            vat_rate=DEFAULT_VAT_RATE,
        )
        estimated_fee = fee_info["total_fee"]

        # Preflight validation
        is_valid, errors = self.validate_order(
            session,
            symbol=clean_symbol,
            side=side_norm,
            quantity=quantity,
            limit_price=limit_price,
            order_type=order_type,
            tif=tif,
            session_phase=session_phase,
            allow_offhours_na=True,
        )
        if not is_valid:
            error_msg = "; ".join(errors)
            logger.warning("Shadow order rejected preflight: %s", error_msg)
            rejection = ShadowOrder(
                order_ref=order_ref,
                symbol=clean_symbol,
                side=side_norm,
                order_type=order_type,
                tif=tif,
                quantity=quantity,
                filled_qty=0,
                pending_qty=quantity,
                limit_price=limit_price,
                avg_fill_price=ZERO,
                order_value=gross,
                estimated_fee=estimated_fee,
                status="REJECTED",
                actor=actor,
                reason=error_msg,
                session_on=today,
                portfolio_id=portfolio_id,
            )
            session.add(rejection)
            # Record to TradeLearningLog as SKIP
            company = session.get(CompanyProfile, clean_symbol)
            tier = getattr(company, "watchlist_category", "GSC") if company else "GSC"
            session.add(
                TradeLearningLog(
                    symbol=clean_symbol,
                    tier=tier,
                    side=side_norm,
                    outcome_type="SKIP",
                    entry_price=limit_price,
                    actor=actor,
                    lesson_summary=f"Preflight rejection: {error_msg}",
                    session_on=today,
                )
            )
            session.flush()
            return {
                "status": "REJECTED",
                "order_ref": order_ref,
                "errors": errors,
                "message": f"Preflight check rejected: {error_msg}",
            }

        # Check queue depth & matching
        quote = self.feed.get_all_quotes().get(clean_symbol)
        can_fill_immediately = False
        fill_price = limit_price

        if side_norm == "BUY":
            # Check cash budget in active bucket (if record_tax_lot is requested)
            if record_tax_lot:
                balances = bucket_balances(session, state, portfolio_id=portfolio_id)
                active_bucket = self.calendar.bucket_for(today)
                avail_cash = balances[active_bucket].available_cash
                if avail_cash < gross + estimated_fee:
                    return {
                        "status": "REJECTED",
                        "order_ref": order_ref,
                        "errors": [
                            f"Insufficient available cash in bucket {active_bucket} (needs ৳{gross + estimated_fee:.2f}, has ৳{avail_cash:.2f})"
                        ],
                    }

            if quote:
                if quote.offer > ZERO and quote.offer <= limit_price and quote.offer_qty >= quantity:
                    can_fill_immediately = True
                    fill_price = min(limit_price, quote.offer)
                elif quote.offer == ZERO and allow_offhours_ltp_fill and quote.ltp <= limit_price:
                    can_fill_immediately = True
                    fill_price = limit_price
            elif allow_offhours_ltp_fill:
                can_fill_immediately = True
                fill_price = limit_price

        elif side_norm == "SELL":
            # Verify mature T+2 shares and strict no-loss (if record_tax_lot is requested)
            if record_tax_lot:
                mature_lots = list(
                    session.scalars(
                        select(TaxLot)
                        .where(
                            TaxLot.symbol == clean_symbol,
                            TaxLot.remaining_qty > 0,
                            TaxLot.portfolio_id == portfolio_id,
                            TaxLot.matures_on <= today,
                        )
                        .order_by(TaxLot.id)
                    )
                )
                mature_qty = sum(l.remaining_qty for l in mature_lots)
                if mature_qty < quantity:
                    return {
                        "status": "REJECTED",
                        "order_ref": order_ref,
                        "errors": [
                            f"Cannot sell {quantity} shares of {clean_symbol}: only {mature_qty} mature T+2 shares available."
                        ],
                    }

                # Strict No-Loss check
                test_gross = money(quantity * limit_price)
                test_fee_info = calculate_broker_fee_breakdown(
                    test_gross,
                    commission_rate=DEFAULT_TRADEXPRESS_COMMISSION_RATE,
                    vat_rate=DEFAULT_VAT_RATE,
                )
                net_sale_val = test_gross - test_fee_info["total_fee"]

                rem_test = quantity
                req_cost_basis = ZERO
                for l in mature_lots:
                    if rem_test <= 0:
                        break
                    s_qty = min(l.remaining_qty, rem_test)
                    req_cost_basis += allocated_basis(l.remaining_cost_basis, l.remaining_qty, s_qty)
                    rem_test -= s_qty

                if net_sale_val < req_cost_basis:
                    net_loss_pct = (net_sale_val / req_cost_basis - 1) * Decimal("100")
                    return {
                        "status": "REJECTED",
                        "order_ref": order_ref,
                        "errors": [
                            f"Strict No-Loss Guard: Net return {net_loss_pct:.2f}% is negative after 1% round-trip fees."
                        ],
                    }

            if quote:
                if quote.bid > ZERO and quote.bid >= limit_price and quote.bid_qty >= quantity:
                    can_fill_immediately = True
                    fill_price = max(limit_price, quote.bid)
                elif quote.bid == ZERO and allow_offhours_ltp_fill and quote.ltp >= limit_price:
                    can_fill_immediately = True
                    fill_price = limit_price
            elif allow_offhours_ltp_fill:
                can_fill_immediately = True
                fill_price = limit_price

        # If matching queue is not available immediately, store order as QUEUED
        if not can_fill_immediately:
            queued_order = ShadowOrder(
                order_ref=order_ref,
                symbol=clean_symbol,
                side=side_norm,
                order_type=order_type,
                tif=tif,
                quantity=quantity,
                filled_qty=0,
                pending_qty=quantity,
                limit_price=limit_price,
                avg_fill_price=ZERO,
                order_value=gross,
                estimated_fee=estimated_fee,
                status="QUEUED",
                actor=actor,
                reason=reason or "Resting in simulated order queue",
                session_on=today,
                portfolio_id=portfolio_id,
            )
            session.add(queued_order)
            session.flush()
            return {
                "status": "QUEUED",
                "order_ref": order_ref,
                "symbol": clean_symbol,
                "side": side_norm,
                "quantity": quantity,
                "limit_price": float(limit_price),
                "pending_qty": quantity,
                "message": f"Order {order_ref} queued in simulated book (awaiting matching depth).",
            }

        # Immediate Fill: Take atomic state checkpoint before state mutation
        CheckpointManager.create_checkpoint(
            session=session,
            state=state,
            action=f"SHADOW_{side_norm}_{clean_symbol}",
            description=f"Shadow {side_norm} fill of {quantity} {clean_symbol} @ {fill_price}",
            actor=actor,
        )

        # Process Fill
        fill_result = self._process_fill(
            session=session,
            state=state,
            order_ref=order_ref,
            symbol=clean_symbol,
            side=side_norm,
            quantity=quantity,
            fill_price=fill_price,
            actor=actor,
            reason=reason,
            portfolio_id=portfolio_id,
            record_tax_lot=record_tax_lot,
        )
        session.flush()
        return fill_result

    def _process_fill(
        self,
        session: Session,
        state: PortfolioState,
        order_ref: str,
        symbol: str,
        side: str,
        quantity: int,
        fill_price: Decimal,
        actor: str,
        reason: str,
        portfolio_id: str,
        record_tax_lot: bool = True,
    ) -> dict[str, Any]:
        """Executes fill accounting, tax lot adjustments, and trade logs."""
        today = state.clock_date
        active_bucket = self.calendar.bucket_for(today)
        company = session.get(CompanyProfile, symbol)
        tier = getattr(company, "watchlist_category", "GSC") if company else "GSC"
        settlement_days = getattr(company, "settlement_days", 2) if company else 2
        matures_on = self.calendar.add_sessions(today, settlement_days)

        gross = money(quantity * fill_price)
        fee_info = calculate_broker_fee_breakdown(
            gross,
            commission_rate=DEFAULT_TRADEXPRESS_COMMISSION_RATE,
            vat_rate=DEFAULT_VAT_RATE,
        )
        total_fee = fee_info["total_fee"]

        if side == "BUY":
            total_cost = gross + total_fee
            if record_tax_lot:
                lot = TaxLot(
                    symbol=symbol,
                    bucket=active_bucket,
                    acquired_on=today,
                    matures_on=matures_on,
                    original_qty=quantity,
                    remaining_qty=quantity,
                    buy_price=fill_price,
                    buy_fee=total_fee,
                    original_cost_basis=total_cost,
                    remaining_cost_basis=total_cost,
                    cycle_base_qty=quantity,
                    peak_price=fill_price,
                    portfolio_id=portfolio_id,
                )
                session.add(lot)
                session.flush()

                trade = TradeLog(
                    portfolio_id=portfolio_id,
                    trade_key=f"SHADOW_BUY:{order_ref}",
                    cycle_id=None,
                    lot_id=lot.id,
                    symbol=symbol,
                    side="BUY",
                    quantity=quantity,
                    price=fill_price,
                    gross_amount=gross,
                    fee=total_fee,
                    net_cash_change=-total_cost,
                    realized_pnl=ZERO,
                    bucket=active_bucket,
                    trade_on=today,
                    settles_on=matures_on,
                    reason=reason or f"Shadow Buy filled @ ৳{fill_price}",
                    source="SHADOW_DUMMY",
                )
                session.add(trade)

            existing_order = session.scalar(
                select(ShadowOrder).where(ShadowOrder.order_ref == order_ref)
            )
            if existing_order is not None:
                existing_order.filled_qty = quantity
                existing_order.pending_qty = 0
                existing_order.avg_fill_price = fill_price
                existing_order.order_value = gross
                existing_order.estimated_fee = total_fee
                existing_order.status = "FILLED"
                existing_order.reason = reason or "Filled"
            else:
                order_record = ShadowOrder(
                    order_ref=order_ref,
                    symbol=symbol,
                    side="BUY",
                    order_type="LIMIT",
                    tif="DAY",
                    quantity=quantity,
                    filled_qty=quantity,
                    pending_qty=0,
                    limit_price=fill_price,
                    avg_fill_price=fill_price,
                    order_value=gross,
                    estimated_fee=total_fee,
                    status="FILLED",
                    actor=actor,
                    reason=reason or "Immediate fill",
                    session_on=today,
                    portfolio_id=portfolio_id,
                )
                session.add(order_record)

            # Record in TradeLearningLog
            session.add(
                TradeLearningLog(
                    symbol=symbol,
                    tier=tier,
                    side="BUY",
                    outcome_type="BUY_FILL",
                    entry_price=fill_price,
                    actor=actor,
                    lesson_summary=f"Buy filled {quantity} sh @ ৳{fill_price:.2f}",
                    session_on=today,
                )
            )

            if record_tax_lot:
                state.rules_revision += 1
                assert_ledger(session, state, portfolio_id=portfolio_id)

            return {
                "status": "FILLED",
                "order_ref": order_ref,
                "symbol": symbol,
                "side": "BUY",
                "quantity": quantity,
                "avg_fill_price": float(fill_price),
                "order_value": float(gross),
                "fee": float(total_fee),
                "net_value": float(total_cost),
                "message": f"Buy filled: {quantity} {symbol} @ ৳{fill_price:.2f}",
            }

        else:  # SELL
            net_proceeds = gross - total_fee
            mature_lots = list(
                session.scalars(
                    select(TaxLot)
                    .where(
                        TaxLot.symbol == symbol,
                        TaxLot.remaining_qty > 0,
                        TaxLot.portfolio_id == portfolio_id,
                        TaxLot.matures_on <= today,
                    )
                    .order_by(TaxLot.id)
                )
            )

            remaining_to_sell = quantity
            total_realized_pnl = ZERO
            total_cost_basis_sold = ZERO

            if record_tax_lot:
                for l in mature_lots:
                    if remaining_to_sell <= 0:
                        break
                    s_qty = min(l.remaining_qty, remaining_to_sell)
                    cost_slice = allocated_basis(l.remaining_cost_basis, l.remaining_qty, s_qty)
                    lot_net_proceeds = money(net_proceeds * s_qty / quantity)
                    lot_fee = money(total_fee * s_qty / quantity)
                    lot_pnl = max(ZERO, lot_net_proceeds - cost_slice)

                    l.remaining_qty -= s_qty
                    l.remaining_cost_basis -= cost_slice
                    remaining_to_sell -= s_qty
                    total_realized_pnl += lot_pnl
                    total_cost_basis_sold += cost_slice

                    trade = TradeLog(
                        portfolio_id=portfolio_id,
                        trade_key=f"SHADOW_SELL:{order_ref}:{l.id}",
                        cycle_id=None,
                        lot_id=l.id,
                        symbol=symbol,
                        side="SELL",
                        quantity=s_qty,
                        price=fill_price,
                        gross_amount=money(s_qty * fill_price),
                        fee=lot_fee,
                        net_cash_change=lot_net_proceeds,
                        realized_pnl=lot_pnl,
                        bucket=l.bucket,
                        trade_on=today,
                        settles_on=matures_on,
                        reason=reason or f"Shadow Sell filled @ ৳{fill_price}",
                        source="SHADOW_DUMMY",
                    )
                    session.add(trade)

                # Credit gross sales to unsettled_sales_bdt (immediate Buying Power credit!)
                current_unsettled = getattr(state, "unsettled_sales_bdt", ZERO) or ZERO
                state.unsettled_sales_bdt = current_unsettled + gross

            existing_order = session.scalar(
                select(ShadowOrder).where(ShadowOrder.order_ref == order_ref)
            )
            if existing_order is not None:
                existing_order.filled_qty = quantity
                existing_order.pending_qty = 0
                existing_order.avg_fill_price = fill_price
                existing_order.order_value = gross
                existing_order.estimated_fee = total_fee
                existing_order.status = "FILLED"
                existing_order.reason = reason or "Filled"
            else:
                order_record = ShadowOrder(
                    order_ref=order_ref,
                    symbol=symbol,
                    side="SELL",
                    order_type="LIMIT",
                    tif="DAY",
                    quantity=quantity,
                    filled_qty=quantity,
                    pending_qty=0,
                    limit_price=fill_price,
                    avg_fill_price=fill_price,
                    order_value=gross,
                    estimated_fee=total_fee,
                    status="FILLED",
                    actor=actor,
                    reason=reason or "Immediate fill",
                    session_on=today,
                    portfolio_id=portfolio_id,
                )
                session.add(order_record)

            net_pnl_pct = (
                (net_proceeds / total_cost_basis_sold - 1) * Decimal("100")
                if total_cost_basis_sold > ZERO
                else ZERO
            )

            # Record in TradeLearningLog
            session.add(
                TradeLearningLog(
                    symbol=symbol,
                    tier=tier,
                    side="SELL",
                    outcome_type="SELL_PROFIT",
                    entry_price=money(total_cost_basis_sold / quantity) if quantity > 0 else fill_price,
                    exit_price=fill_price,
                    net_pnl_pct=net_pnl_pct,
                    actor=actor,
                    lesson_summary=f"Sell filled {quantity} sh @ ৳{fill_price:.2f} (net return: {net_pnl_pct:.2f}%)",
                    session_on=today,
                )
            )

            if record_tax_lot:
                state.rules_revision += 1
                assert_ledger(session, state, portfolio_id=portfolio_id)

            return {
                "status": "FILLED",
                "order_ref": order_ref,
                "symbol": symbol,
                "side": "SELL",
                "quantity": quantity,
                "avg_fill_price": float(fill_price),
                "order_value": float(gross),
                "fee": float(total_fee),
                "net_value": float(net_proceeds),
                "realized_pnl": float(total_realized_pnl),
                "net_pnl_pct": float(net_pnl_pct),
                "unsettled_sales_bdt": float(getattr(state, "unsettled_sales_bdt", ZERO) or ZERO),
                "message": f"Sell filled: {quantity} {symbol} @ ৳{fill_price:.2f} (+৳{total_realized_pnl:.2f})",
            }

    def reconcile_queued_orders(
        self,
        session: Session,
        quotes: dict[str, MarketQuote] | None = None,
        session_phase: str = "CONTINUOUS",
    ) -> list[dict[str, Any]]:
        """Evaluates pending QUEUED orders against fresh quote depth and expires at session close."""
        state = portfolio_state(session)
        queued_orders = list(
            session.scalars(
                select(ShadowOrder)
                .where(ShadowOrder.status == "QUEUED")
                .order_by(ShadowOrder.id)
            )
        )
        if not queued_orders:
            return []

        # If market closed, expire all resting DAY orders
        if session_phase.upper() == "CLOSED":
            results = []
            for order in queued_orders:
                order.status = "EXPIRED"
                order.reason = "Expired at session close (14:10)"
                results.append({"order_ref": order.order_ref, "status": "EXPIRED"})
            session.flush()
            return results

        fresh_quotes = quotes or self.feed.get_all_quotes()
        filled_results = []

        for order in queued_orders:
            q = fresh_quotes.get(order.symbol)
            if not q:
                continue

            can_fill = False
            f_price = order.limit_price

            if order.side == "BUY":
                if q.offer > ZERO and q.offer <= order.limit_price and q.offer_qty >= order.pending_qty:
                    can_fill = True
                    f_price = min(order.limit_price, q.offer)
            elif order.side == "SELL":
                if q.bid > ZERO and q.bid >= order.limit_price and q.bid_qty >= order.pending_qty:
                    can_fill = True
                    f_price = max(order.limit_price, q.bid)

            if can_fill:
                CheckpointManager.create_checkpoint(
                    session=session,
                    state=state,
                    action=f"RECONCILE_{order.side}_{order.symbol}",
                    description=f"Fill queued shadow {order.side} {order.order_ref}",
                    actor="RECONCILER",
                )
                fill_res = self._process_fill(
                    session=session,
                    state=state,
                    order_ref=order.order_ref,
                    symbol=order.symbol,
                    side=order.side,
                    quantity=order.pending_qty,
                    fill_price=f_price,
                    actor=order.actor,
                    reason="Queue depth matched",
                    portfolio_id=order.portfolio_id,
                )
                order.status = "FILLED"
                order.filled_qty = order.quantity
                order.pending_qty = 0
                order.avg_fill_price = f_price
                filled_results.append(fill_res)

        session.flush()
        return filled_results

    def cancel_order(self, order_ref: str) -> dict[str, Any]:
        """Cancels a resting QUEUED shadow order."""
        with self.database.write() as session:
            order = session.scalar(
                select(ShadowOrder).where(ShadowOrder.order_ref == order_ref)
            )
            if not order:
                return {"status": "ERROR", "message": f"Order {order_ref} not found."}
            if order.status != "QUEUED":
                return {
                    "status": "ERROR",
                    "message": f"Order {order_ref} is {order.status}, cannot cancel.",
                }
            order.status = "CANCELLED"
            order.reason = "Cancelled by operator"
            session.flush()
            return {"status": "CANCELLED", "order_ref": order_ref}

    def get_orders(
        self,
        portfolio_id: str = "H9210_SHADOW",
        status: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Retrieves shadow orders for cockpit display (mirroring TradeXpress Order List)."""
        with self.database.read() as session:
            q = select(ShadowOrder).where(ShadowOrder.portfolio_id == portfolio_id)
            if status:
                q = q.where(ShadowOrder.status == status.upper())
            q = q.order_by(ShadowOrder.id.desc()).limit(limit)
            orders = list(session.scalars(q))
            return [
                {
                    "id": o.id,
                    "order_ref": o.order_ref,
                    "symbol": o.symbol,
                    "side": o.side,
                    "order_type": o.order_type,
                    "tif": o.tif,
                    "quantity": o.quantity,
                    "filled_qty": o.filled_qty,
                    "pending_qty": o.pending_qty,
                    "limit_price": float(o.limit_price),
                    "avg_fill_price": float(o.avg_fill_price),
                    "order_value": float(o.order_value),
                    "estimated_fee": float(o.estimated_fee),
                    "status": o.status,
                    "actor": o.actor,
                    "reason": o.reason,
                    "session_on": o.session_on.isoformat() if o.session_on else "",
                    "created_at": o.created_at,
                }
                for o in orders
            ]
