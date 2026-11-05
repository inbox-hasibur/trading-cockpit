"""Atomic, manual DEMO cycles. No LLM, scheduler, or external order submission."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.adapters.stocknow_adapter import StockNowAdapter
from backend.config import Settings
from backend.database import (
    AutomationCycle,
    CompanyProfile,
    CustomRule,
    CycleRequestKey,
    Database,
    DecisionLog,
    TaxLot,
    TradeLog,
    portfolio_state,
)
from backend.engine.agent_actions import check_canary_theses
from backend.engine.money import HUNDRED, ZERO, decimal, money, price, purchase_amount, whole_shares
from backend.engine.sequential_seller import SellState, plan_sale
from backend.engine.signals import BLOCK_ALL_TRADING, assess_company
from backend.engine.t2_ledger import TradingCalendar, assert_ledger, bucket_balances


class AutomationPaused(ValueError):
    pass


class AutoTrader:
    def __init__(self, database: Database, settings: Settings, adapter: StockNowAdapter | None = None):
        self.database = database
        self.settings = settings
        self.adapter = adapter or StockNowAdapter()
        self.calendar = TradingCalendar(settings.holidays, settings.bucket_anchor)

    def run_cycle(self, request_id: str | None = None, session: Session | None = None) -> dict:
        if session is not None:
            return self._run_cycle_internal(session, request_id)
        with self.database.write() as session_ctx:
            return self._run_cycle_internal(session_ctx, request_id)

    def _run_cycle_internal(self, session: Session, request_id: str | None = None) -> dict:
        state = portfolio_state(session)
        if request_id:
            saved_request = session.get(CycleRequestKey, request_id)
            if saved_request:
                saved = session.get(AutomationCycle, saved_request.cycle_id)
                return {**saved.result, "duplicate": True, "status": "DEDUPLICATED"}
        signal_key = f"{state.clock_date}:{state.revision}:{state.rules_revision}"
        existing = session.scalar(
            select(AutomationCycle).where(AutomationCycle.signal_key == signal_key)
        )
        if existing:
            if request_id:
                session.add(CycleRequestKey(request_id=request_id, cycle_id=existing.id))
            return {**existing.result, "duplicate": True, "status": "DEDUPLICATED"}
        if state.paused:
            raise AutomationPaused("Automation is paused. Resume it before running a paper cycle.")
        if not self.calendar.is_session(state.clock_date):
            raise ValueError("The simulated date is not a trading session.")

        cycle = AutomationCycle(
            id=str(uuid4()),
            request_id=request_id,
            signal_key=signal_key,
            session_on=state.clock_date,
            market_revision=state.revision,
            rules_revision=state.rules_revision,
        )
        session.add(cycle)
        session.flush()
        if request_id:
            session.add(CycleRequestKey(request_id=request_id, cycle_id=cycle.id))

        decisions: list[dict] = []
        trades: list[dict] = []

        def record(symbol: str, action: str, reason: str, quantity: int = 0, lot_id=None):
            session.add(DecisionLog(
                cycle_id=cycle.id, symbol=symbol, action=action, reason=reason,
                quantity=quantity, lot_id=lot_id,
            ))
            decisions.append({
                "symbol": symbol, "action": action, "reason": reason,
                "quantity": quantity, "lot_id": lot_id,
            })

        companies = list(session.scalars(select(CompanyProfile).order_by(CompanyProfile.symbol)))
        rules = {rule.symbol: rule for rule in session.scalars(select(CustomRule))}
        assessments = {}
        for company in companies:
            rule = rules[company.symbol]
            analysis, quote = assess_company(
                company, rule, self.settings, state.clock_date, self.adapter
            )
            assessments[company.symbol] = (analysis, quote)
            if analysis.signal == "CRASH_QUARANTINE" and not company.quarantined:
                company.quarantined = True
                company.quarantine_reason = analysis.reason
            record(company.symbol, analysis.signal, analysis.reason)

        sold_symbols: set[str] = set()
        lots = list(session.scalars(
            select(TaxLot).where(TaxLot.remaining_qty > 0).order_by(TaxLot.id)
        ))
        for lot in lots:
            rule = rules[lot.symbol]
            analysis, quote = assessments[lot.symbol]
            if not rule.enabled:
                record(lot.symbol, "AUTOMATION_DISABLED", "Company automation is disabled.", lot_id=lot.id)
                continue
            if quote is None or analysis.signal in BLOCK_ALL_TRADING:
                record(lot.symbol, "WAIT_VALID_QUOTE", "Invalid/stale data blocks exits too.", lot_id=lot.id)
                continue
            if lot.last_sale_revision == state.revision:
                record(lot.symbol, "WAIT_NEW_QUOTE", "One sale per lot per market snapshot.", lot_id=lot.id)
                continue
            plan = plan_sale(
                SellState(
                    remaining_qty=lot.remaining_qty,
                    remaining_basis=lot.remaining_cost_basis,
                    matures_on=lot.matures_on,
                    cycle_base_qty=lot.cycle_base_qty,
                    peak_price=lot.peak_price,
                    next_tier=lot.next_tier,
                    phase=lot.phase,
                    recovery_anchor=lot.recovery_anchor,
                ),
                current_price=quote.unit_price,
                as_of=state.clock_date,
                sell_fee_rate=self.settings.sell_fee_rate,
                tiers=tuple(decimal(value) for value in rule.profit_tiers),
                slices=tuple(decimal(value) for value in rule.tier_slices),
                pullback_pct=rule.pullback_pct,
            )
            lot.remaining_qty = plan.state.remaining_qty
            lot.remaining_cost_basis = plan.state.remaining_basis
            lot.peak_price = plan.state.peak_price
            lot.next_tier = plan.state.next_tier
            lot.cycle_base_qty = plan.state.cycle_base_qty
            lot.phase = plan.state.phase
            lot.recovery_anchor = plan.state.recovery_anchor
            record(lot.symbol, plan.action, plan.reason, plan.quantity, lot.id)
            if plan.quantity:
                fill_price = self.adapter.paper_fill(quote, plan.quantity)
                lot.last_sale_revision = state.revision
                company = next(company for company in companies if company.symbol == lot.symbol)
                trade = TradeLog(
                    trade_key=f"SELL:{cycle.id}:{lot.id}:{plan.action}",
                    cycle_id=cycle.id, lot_id=lot.id, symbol=lot.symbol, side="SELL",
                    quantity=plan.quantity, price=fill_price,
                    gross_amount=money(plan.quantity * fill_price),
                    fee=plan.fee, net_cash_change=plan.proceeds, realized_pnl=plan.realized_pnl,
                    bucket=lot.bucket, trade_on=state.clock_date,
                    settles_on=self.calendar.add_sessions(state.clock_date, company.settlement_days),
                    reason=plan.reason,
                )
                session.add(trade)
                session.flush()
                trades.append(self._trade_result(trade, plan.action))
                sold_symbols.add(lot.symbol)

        balances = bucket_balances(session, state)
        active_name = self.calendar.bucket_for(state.clock_date)
        active = balances[active_name]
        for company in companies:
            rule = rules[company.symbol]
            analysis, quote = assessments[company.symbol]
            if not rule.enabled or rule.buy_allocation_pct <= ZERO:
                record(company.symbol, "BUY_DISABLED", "New buying is disabled for this company.")
                continue
            if company.quarantined or analysis.signal == "CRASH_QUARANTINE":
                record(company.symbol, "BUY_BLOCKED", "Sticky crash quarantine blocks new buys.")
                continue
            if analysis.signal != "BUY_ZONE" or quote is None:
                continue
            if company.symbol in sold_symbols:
                record(company.symbol, "WAIT_NO_CHURN", "Do not rebuy a symbol sold in this cycle.")
                continue
            buy_key = f"BUY:{company.symbol}:{state.clock_date}"
            already_bought = session.scalar(select(TradeLog.id).where(
                TradeLog.symbol == company.symbol,
                TradeLog.side == "BUY",
                TradeLog.trade_on == state.clock_date,
            ))
            if already_bought:
                record(company.symbol, "WAIT_DAILY_BUY", "Already bought this symbol in this session.")
                continue
            open_basis = sum(session.scalars(select(TaxLot.remaining_cost_basis).where(
                TaxLot.symbol == company.symbol, TaxLot.remaining_qty > 0,
            )), ZERO)
            exposure_cap = money(state.initial_capital * rule.buy_allocation_pct / HUNDRED)
            headroom = max(ZERO, exposure_cap - open_basis)
            daily_headroom = max(ZERO, active.initial_cash - active.today_buy_spend)
            budget = min(active.available_cash, headroom, daily_headroom)
            quantity = whole_shares(budget / (quote.unit_price * (1 + self.settings.buy_fee_rate)))
            while quantity > 0:
                cost, fee = purchase_amount(quantity, quote.unit_price, self.settings.buy_fee_rate)
                if cost <= budget:
                    break
                quantity -= 1
            if quantity <= 0 or money(quantity * quote.unit_price) < self.settings.min_buy_notional:
                record(company.symbol, "WAIT_BUDGET", "Exposure/cash/minimum-notional limit blocks a new buy.")
                continue
            fill_price = self.adapter.paper_fill(quote, quantity)
            lot = TaxLot(
                symbol=company.symbol, bucket=active_name,
                acquired_on=state.clock_date,
                matures_on=self.calendar.add_sessions(state.clock_date, company.settlement_days),
                original_qty=quantity, remaining_qty=quantity, buy_price=fill_price,
                buy_fee=fee, original_cost_basis=cost, remaining_cost_basis=cost,
                cycle_base_qty=quantity, peak_price=fill_price,
            )
            session.add(lot)
            session.flush()
            trade = TradeLog(
                trade_key=buy_key, cycle_id=cycle.id, lot_id=lot.id,
                symbol=company.symbol, side="BUY", quantity=quantity, price=fill_price,
                gross_amount=money(quantity * fill_price), fee=fee,
                net_cash_change=-cost, realized_pnl=ZERO, bucket=active_name,
                trade_on=state.clock_date, settles_on=lot.matures_on,
                reason=f"{analysis.reason} Within company exposure and bucket cash limits.",
            )
            session.add(trade)
            session.flush()
            active.available_cash -= cost
            active.today_buy_spend += cost
            record(company.symbol, "BUY", trade.reason, quantity, lot.id)
            trades.append(self._trade_result(trade, "BUY"))

        session.flush()
        check_canary_theses(session, state)
        assert_ledger(session, state)
        cycle.result = {
            "id": cycle.id, "date": state.clock_date.isoformat(),
            "revision": state.revision, "rules_revision": state.rules_revision,
            "status": "COMPLETED", "duplicate": False, "source": "DEMO_PAPER",
            "trades": trades, "decisions": decisions,
            "buy_count": sum(trade["side"] == "BUY" for trade in trades),
            "sell_count": sum(trade["side"] == "SELL" for trade in trades),
        }
        return cycle.result

    @staticmethod
    def _trade_result(trade: TradeLog, action: str) -> dict:
        return {
            "id": trade.id, "symbol": trade.symbol, "side": trade.side,
            "quantity": trade.quantity, "price": float(trade.price),
            "fee": float(trade.fee), "realized_pnl": float(trade.realized_pnl),
            "action": action, "lot_id": trade.lot_id,
        }

    def advance_demo(self, scenario: str) -> dict:
        if scenario not in {"NORMAL", "RALLY", "PULLBACK", "CRASH", "RECOVERY"}:
            raise ValueError("Unknown demo scenario.")
        with self.database.write() as session:
            state = portfolio_state(session)
            state.clock_date = self.calendar.add_sessions(state.clock_date, 1)
            state.revision += 1
            companies = list(session.scalars(select(CompanyProfile).order_by(CompanyProfile.symbol)))
            for index, company in enumerate(companies):
                multiplier = {
                    "NORMAL": Decimal("1.008") if (state.revision + index) % 2 else Decimal("0.992"),
                    "RALLY": Decimal("1.04"),
                    "PULLBACK": Decimal("0.96"),
                    "CRASH": Decimal("0.78"),
                    "RECOVERY": Decimal("1.03"),
                }[scenario]
                next_price = price(max(Decimal("0.01"), company.last_price * multiplier))
                if scenario == "RECOVERY":
                    anchors = list(session.scalars(select(TaxLot.recovery_anchor).where(
                        TaxLot.symbol == company.symbol,
                        TaxLot.remaining_qty > 0,
                        TaxLot.recovery_anchor.is_not(None),
                    )))
                    if anchors:
                        next_price = max(next_price, price(max(anchors) * Decimal("1.005")))
                company.last_price = next_price
                company.quote_on = state.clock_date
                company.source = "DEMO_SCENARIO"
                company.price_history = (company.price_history + [
                    {"date": state.clock_date.isoformat(), "close": str(next_price)}
                ])[-15:]
            session.flush()
            check_canary_theses(session, state)
            assert_ledger(session, state)
            return {
                "date": state.clock_date.isoformat(), "revision": state.revision,
                "scenario": scenario, "source": "DEMO_SCENARIO", "executed_trades": False,
            }
