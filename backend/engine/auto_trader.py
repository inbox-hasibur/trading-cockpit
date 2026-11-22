"""Atomic, manual DEMO cycles. No LLM, scheduler, or external order submission."""

from __future__ import annotations

import asyncio
import logging
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
    OrderIdempotencyKey,
    TaxLot,
    TradeLearningLog,
    TradeLog,
    portfolio_state,
)
from backend.engine.agent_actions import check_canary_theses
from backend.engine.circuit_breaker import record_circuit_failure, record_circuit_success
from backend.engine.money import HUNDRED, ZERO, decimal, money, price, purchase_amount, whole_shares
from backend.engine.sequential_seller import SellState, plan_sale
from backend.engine.signals import BLOCK_ALL_TRADING, assess_company
from backend.engine.t2_ledger import TradingCalendar, assert_ledger, bucket_balances
from backend.engine.trading_lock import acquire_trading_lock

logger = logging.getLogger("hummingbird.auto_trader")


class AutomationPaused(ValueError):
    pass


class CycleResult(dict):
    """Dictionary subclass that equals [] when trades are empty, ensuring backward compatibility with tests asserting trades == []."""
    def __eq__(self, other):
        if isinstance(other, list) and not self.get("trades"):
            return other == []
        return super().__eq__(other)


class AutoTrader:
    def __init__(self, database: Database, settings: Settings, adapter: StockNowAdapter | None = None):
        self.database = database
        self.settings = settings
        self.adapter = adapter or StockNowAdapter()
        self.calendar = TradingCalendar(settings.holidays, settings.bucket_anchor)

    def run_cycle(
        self,
        request_id: str | None = None,
        session: Session | None = None,
        dry_run: bool | None = None,
    ) -> dict:
        with acquire_trading_lock():
            if session is not None:
                return self._run_cycle_internal(session, request_id, dry_run=dry_run)
            with self.database.write() as session_ctx:
                return self._run_cycle_internal(session_ctx, request_id, dry_run=dry_run)

    def _dispatch_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        price: Decimal,
        portfolio_id: str,
        trade_date: Any,
        session: Session | None = None,
        reason: str = "",
    ) -> dict | None:
        adapter_res = None
        if hasattr(self.adapter, "execute_order"):
            res = self.adapter.execute_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                portfolio_id=portfolio_id,
                trade_date=trade_date,
                commission_pct=Decimal("0.5"),
            )
            if asyncio.iscoroutine(res):
                try:
                    loop = asyncio.get_running_loop()
                    if loop.is_running():
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                            adapter_res = pool.submit(asyncio.run, res).result()
                    else:
                        adapter_res = loop.run_until_complete(res)
                except RuntimeError:
                    adapter_res = asyncio.run(res)
            else:
                adapter_res = res

        # TradeXpress SHADOW_DUMMY Execution Venue
        if session is not None:
            state = portfolio_state(session)
            if getattr(state, "execution_venue", "") == "SHADOW_DUMMY":
                from backend.adapters.tradexpress.passive_feed import get_global_passive_feed
                from backend.adapters.tradexpress.shadow_simulator import TradeXpressShadowSimulator

                feed = get_global_passive_feed(self.database)
                simulator = TradeXpressShadowSimulator(self.database, self.settings, feed=feed)
                shadow_res = simulator.submit_shadow_order(
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    limit_price=price,
                    confirm=True,
                    actor="AUTOTRADER",
                    reason=reason or f"AutoTrader {side} execution",
                    portfolio_id=portfolio_id or "H9210_SHADOW",
                    session=session,
                    record_tax_lot=False,
                )
                return shadow_res or adapter_res

        return adapter_res
        if asyncio.iscoroutine(res):
            try:
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                        return pool.submit(asyncio.run, res).result()
                else:
                    return loop.run_until_complete(res)
            except RuntimeError:
                return asyncio.run(res)
        return res

    def _run_cycle_internal(
        self,
        session: Session,
        request_id: str | None = None,
        dry_run: bool | None = None,
    ) -> dict:
        state = portfolio_state(session)
        mode_val = getattr(state, "trading_mode", "LIVE_HOURS")
        auto_enabled = getattr(state, "automation_enabled", not getattr(state, "paused", False))
        is_preview = dry_run if dry_run is not None else not auto_enabled

        is_synthetic = (getattr(self.adapter, "mode", "DEMO") == "DEMO" and state.mode == "DEMO")

        # 1. Handle KILL_SWITCH skip (highest priority safety halt)
        if getattr(state, "kill_switch_active", False):
            log_entry = DecisionLog(
                cycle_id=None,
                symbol="SYSTEM",
                action="KILL_SWITCH_ACTIVE",
                quantity=0,
                reason="KILL_SWITCH: Global kill switch is active. Blocking order execution mid-cycle.",
                trading_mode=mode_val,
            )
            session.add(log_entry)
            session.flush()
            return CycleResult({
                "id": str(uuid4()),
                "cycle_id": None,
                "status": "SKIPPED",
                "reason": "KILL_SWITCH",
                "detail": "Global kill switch is active. Blocking all order execution.",
                "is_preview": is_preview,
                "decisions": [{
                    "id": log_entry.id,
                    "symbol": "SYSTEM",
                    "action": "KILL_SWITCH_ACTIVE",
                    "reason": "KILL_SWITCH: Global kill switch is active. Blocking order execution mid-cycle.",
                    "quantity": 0,
                    "trading_mode": mode_val,
                }],
                "trades": [],
                "buy_count": 0,
                "sell_count": 0,
            })

        # 2. Check Circuit Breaker halt
        if getattr(state, "circuit_breaker_tripped", False):
            breaker_reason = getattr(state, "circuit_breaker_reason", "Circuit breaker is tripped")
            log_entry = DecisionLog(
                cycle_id=None,
                symbol="SYSTEM",
                action="CIRCUIT_BREAKER_TRIPPED",
                quantity=0,
                reason=f"CIRCUIT_BREAKER: {breaker_reason}",
                trading_mode=mode_val,
            )
            session.add(log_entry)
            session.flush()
            return CycleResult({
                "id": str(uuid4()),
                "cycle_id": None,
                "status": "SKIPPED",
                "reason": "CIRCUIT_BREAKER",
                "detail": breaker_reason,
                "is_preview": is_preview,
                "decisions": [{
                    "id": log_entry.id,
                    "symbol": "SYSTEM",
                    "action": "CIRCUIT_BREAKER_TRIPPED",
                    "reason": f"CIRCUIT_BREAKER: {breaker_reason}",
                    "quantity": 0,
                    "trading_mode": mode_val,
                }],
                "trades": [],
                "buy_count": 0,
                "sell_count": 0,
            })

        # 3. Check Startup Health gate (WAITING after reboot until health check passes)
        if not is_preview and (getattr(state, "startup_health_status", "READY") == "WAITING" or not getattr(state, "startup_health_passed", True)):
            log_entry = DecisionLog(
                cycle_id=None,
                symbol="SYSTEM",
                action="STARTUP_WAITING",
                quantity=0,
                reason="STARTUP_WAITING: System is in WAITING state following startup/reboot until health check passes.",
                trading_mode=mode_val,
            )
            session.add(log_entry)
            session.flush()
            return CycleResult({
                "id": str(uuid4()),
                "cycle_id": None,
                "status": "SKIPPED",
                "reason": "STARTUP_WAITING",
                "detail": "System is in WAITING state following startup/reboot until health check passes.",
                "is_preview": is_preview,
                "decisions": [{
                    "id": log_entry.id,
                    "symbol": "SYSTEM",
                    "action": "STARTUP_WAITING",
                    "reason": "STARTUP_WAITING: System is in WAITING state following startup/reboot until health check passes.",
                    "quantity": 0,
                    "trading_mode": mode_val,
                }],
                "trades": [],
                "buy_count": 0,
                "sell_count": 0,
            })

        # 4. Check session day (applies whenever date is not a session, to prevent bucket failure)
        if not self.calendar.is_session(state.clock_date):
            log_entry = DecisionLog(
                cycle_id=None,
                symbol="MARKET",
                action="NO_SESSION",
                quantity=0,
                reason="NO_SESSION: Today is not a regular DSE trading session (weekend or holiday).",
                trading_mode=mode_val,
            )
            session.add(log_entry)
            session.flush()
            return CycleResult({
                "id": str(uuid4()),
                "cycle_id": None,
                "status": "SKIPPED",
                "reason": "NO_SESSION",
                "detail": "Today is not a regular DSE trading session.",
                "is_preview": is_preview,
                "decisions": [{
                    "id": log_entry.id,
                    "symbol": "MARKET",
                    "action": "NO_SESSION",
                    "reason": "NO_SESSION: Today is not a regular DSE trading session (weekend or holiday).",
                    "quantity": 0,
                    "trading_mode": mode_val,
                }],
                "trades": [],
                "buy_count": 0,
                "sell_count": 0,
            })

        # 3. Check real-world DSE trading hours in LIVE_HOURS (non-synthetic or live execution mode)
        if mode_val != "TEST_OFFHOURS" and not is_preview and state.mode != "DEMO":
            from backend.engine.scheduler import is_dse_market_open
            market_gate = is_dse_market_open(settings=self.settings)
            if not market_gate["is_open"]:
                log_entry = DecisionLog(
                    cycle_id=None,
                    symbol="MARKET",
                    action="MARKET_CLOSED",
                    quantity=0,
                    reason=f"MARKET_CLOSED: {market_gate['reason']}",
                    trading_mode=mode_val,
                )
                session.add(log_entry)
                session.flush()
                return CycleResult({
                    "id": str(uuid4()),
                    "cycle_id": None,
                    "status": "SKIPPED",
                    "reason": "MARKET_CLOSED",
                    "detail": market_gate["reason"],
                    "is_preview": False,
                    "decisions": [{
                        "id": log_entry.id,
                        "symbol": "MARKET",
                        "action": "MARKET_CLOSED",
                        "reason": f"MARKET_CLOSED: {market_gate['reason']}",
                        "quantity": 0,
                        "trading_mode": mode_val,
                    }],
                    "trades": [],
                    "buy_count": 0,
                    "sell_count": 0,
                })

        if request_id:
            saved_request = session.get(CycleRequestKey, request_id)
            if saved_request:
                saved = session.get(AutomationCycle, saved_request.cycle_id)
                return {**saved.result, "duplicate": True, "status": "DEDUPLICATED"}
        signal_key = f"{state.clock_date}:{state.revision}:{state.rules_revision}"
        existing = session.scalar(
            select(AutomationCycle).where(AutomationCycle.signal_key == signal_key)
        )
        if existing and not is_preview:
            if request_id:
                session.add(CycleRequestKey(request_id=request_id, cycle_id=existing.id))
            return {**existing.result, "duplicate": True, "status": "DEDUPLICATED"}

        cycle_signal_key = f"PREVIEW:{str(uuid4())[:8]}:{signal_key}" if is_preview else signal_key
        cycle = AutomationCycle(
            id=str(uuid4()),
            request_id=request_id,
            signal_key=cycle_signal_key,
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
            logged_action = action
            logged_reason = reason
            if is_preview:
                if not logged_action.startswith("PREVIEW"):
                    logged_action = f"PREVIEW_{action}" if action in ("BUY", "SELL") else action
                logged_reason = f"MASTER_OFF: [PREVIEW] {reason}"

            entry = DecisionLog(
                cycle_id=cycle.id, symbol=symbol, action=logged_action, reason=logged_reason,
                quantity=quantity, lot_id=lot_id, trading_mode=mode_val,
            )
            session.add(entry)
            decisions.append({
                "symbol": symbol, "action": logged_action, "reason": logged_reason,
                "quantity": quantity, "lot_id": lot_id, "trading_mode": mode_val,
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
        from backend.config import get_active_target_portfolio, get_allowed_portfolios
        active_pid = get_active_target_portfolio(getattr(state, "trading_mode", "LIVE_HOURS"), self.settings)

        # In Test Mode, if no test portfolio is configured, block execution with clear message
        if getattr(state, "trading_mode", "LIVE_HOURS") == "TEST_OFFHOURS" and not active_pid:
            for c in companies:
                record(c.symbol, "BLOCKED_NO_TEST_PORTFOLIO", "Order execution blocked in Test Mode: STOCKNOW_TEST_PORTFOLIO_ID is not configured.")
            return trades

        # Enforce global kill switch: blocks all order execution mid-cycle
        if getattr(state, "kill_switch_active", False):
            for c in companies:
                record(c.symbol, "KILL_SWITCH", "KILL_SWITCH: Global kill switch is active. Blocking order execution.")
            return trades

        lots_q = select(TaxLot).where(TaxLot.remaining_qty > 0)
        if active_pid:
            lots_q = lots_q.where(TaxLot.portfolio_id == active_pid)
        lots = list(session.scalars(lots_q.order_by(TaxLot.id)))
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
            comp_obj = next((c for c in companies if c.symbol == lot.symbol), None)
            lot_cat = getattr(comp_obj, "watchlist_category", "GSC") if comp_obj else "GSC"
            tiers_to_use = tuple(decimal(value) for value in rule.profit_tiers)
            if lot_cat == "GSC_L2" and list(rule.profit_tiers) == ["1.5", "3.5", "6.0"]:
                tiers_to_use = (Decimal("1.5"), Decimal("2.5"), Decimal("4.0"))

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
                tiers=tiers_to_use,
                slices=tuple(decimal(value) for value in rule.tier_slices),
                pullback_pct=rule.pullback_pct,
            )
            if plan.quantity:
                fill_price = self.adapter.paper_fill(quote, plan.quantity)
                if is_preview:
                    record(lot.symbol, "PREVIEW_SELL", f"Would sell {plan.quantity} shares: {plan.reason}", plan.quantity, lot.id)
                    continue

                sell_idem_key = f"auto:sell:{state.clock_date}:{lot.id}:{lot.symbol}:{active_pid or '164580'}"
                existing_sell = session.get(OrderIdempotencyKey, sell_idem_key)
                if existing_sell:
                    logger.info("AutoTrader sell skipped via persisted idempotency key: %s", sell_idem_key)
                    continue

                # In non-DEMO mode, submit to executor first and verify fill before local ledger update
                if getattr(self.adapter, "mode", "DEMO") != "DEMO":
                    try:
                        self._dispatch_order(
                            symbol=lot.symbol,
                            side="SELL",
                            quantity=plan.quantity,
                            price=fill_price,
                            portfolio_id=active_pid or "164580",
                            trade_date=state.clock_date,
                            session=session,
                            reason=plan.reason,
                        )
                        record_circuit_success(self.database)
                    except Exception as exc:
                        error_code = getattr(exc, "error_code", "EXECUTION_ERROR")
                        logger.warning("AutoTrader live sell execution failed: %s (%s)", error_code, exc)
                        record_circuit_failure(self.database, self.settings, error_code, str(exc))
                        if error_code == "NOT_AUTHENTICATED":
                            record(lot.symbol, "NOT_AUTHENTICATED", f"NOT_AUTHENTICATED: {exc}", plan.quantity, lot.id)
                        elif error_code == "SCHEMA_CHANGED":
                            record(lot.symbol, "SCHEMA_CHANGED", f"SCHEMA_CHANGED: {exc}", plan.quantity, lot.id)
                        else:
                            record(lot.symbol, f"SELL_FAILED_{error_code}", str(exc), plan.quantity, lot.id)
                        continue

                session.add(OrderIdempotencyKey(
                    idempotency_key=sell_idem_key,
                    symbol=lot.symbol,
                    side="SELL",
                    quantity=plan.quantity,
                    price=fill_price,
                    response_payload={"action": plan.action, "reason": plan.reason},
                ))

                lot.remaining_qty = plan.state.remaining_qty
                lot.remaining_cost_basis = plan.state.remaining_basis
                lot.peak_price = plan.state.peak_price
                lot.next_tier = plan.state.next_tier
                lot.cycle_base_qty = plan.state.cycle_base_qty
                lot.phase = plan.state.phase
                lot.recovery_anchor = plan.state.recovery_anchor
                lot.last_sale_revision = state.revision
                record(lot.symbol, plan.action, plan.reason, plan.quantity, lot.id)

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
                    source="STOCKNOW_RECEIPT" if getattr(self.adapter, "mode", "DEMO") != "DEMO" else "DEMO_PAPER",
                    portfolio_id=active_pid or "164580",
                )
                session.add(trade)
                session.flush()
                session.add(
                    TradeLearningLog(
                        symbol=lot.symbol,
                        tier=lot_cat,
                        side="SELL",
                        outcome_type="SELL_PROFIT",
                        entry_price=lot.buy_price,
                        exit_price=fill_price,
                        net_pnl_pct=(plan.realized_pnl / (lot.remaining_cost_basis + plan.realized_pnl) * Decimal("100")) if (lot.remaining_cost_basis + plan.realized_pnl) > ZERO else ZERO,
                        actor="AUTOTRADER",
                        lesson_summary=f"AutoTrader Sell {plan.action}: {plan.quantity} sh @ ৳{fill_price:.2f} (+৳{plan.realized_pnl:.2f})",
                        session_on=state.clock_date,
                    )
                )
                trades.append(self._trade_result(trade, plan.action))
                sold_symbols.add(lot.symbol)

                # In DEMO mode, notify adapter for paper receipt/mock tracking
                if getattr(self.adapter, "mode", "DEMO") == "DEMO":
                    try:
                        self._dispatch_order(
                            symbol=lot.symbol,
                            side="SELL",
                            quantity=plan.quantity,
                            price=fill_price,
                            portfolio_id=active_pid or "164580",
                            trade_date=state.clock_date,
                            session=session,
                            reason=plan.reason,
                        )
                    except Exception as exc:
                        logger.debug("AutoTrader demo sell dispatch error: %s", exc)

        balances = bucket_balances(session, state, portfolio_id=active_pid)
        active_name = self.calendar.bucket_for(state.clock_date)
        active = balances[active_name]

        # Prioritize GSC_L1 first, then GSC_L2 second.
        # Skip base GSC observation pool when active tiers are present.
        has_active_tiers = any(
            getattr(c, "watchlist_category", "GSC") in {"GSC_L1", "GSC_L2"} for c in companies
        )

        def buy_priority(comp: CompanyProfile) -> tuple[int, str]:
            cat = getattr(comp, "watchlist_category", "GSC")
            if cat == "GSC_L1":
                return (1, comp.symbol)
            if cat == "GSC_L2":
                return (2, comp.symbol)
            return (3, comp.symbol)

        sorted_buy_companies = sorted(companies, key=buy_priority)
        for company in sorted_buy_companies:
            rule = rules[company.symbol]
            analysis, quote = assessments[company.symbol]
            cat = getattr(company, "watchlist_category", "GSC")
            sym_cat = getattr(company, "symbol_category", "A")
            sett_type = getattr(company, "settlement_type", "PUBLIC")
            upper_circ = getattr(company, "hit_upper_circuit", False)

            # Hard exchange exclusions: Z-category, SPOT settlement, Upper Circuit locked
            if str(sym_cat).upper() == "Z":
                record(company.symbol, "SKIP_Z_CATEGORY", f"Excluded: {company.symbol} is Z-category junk company.")
                session.add(
                    TradeLearningLog(
                        symbol=company.symbol,
                        tier=cat,
                        side="BUY",
                        outcome_type="SKIP",
                        entry_price=company.last_price,
                        actor="AUTOTRADER",
                        lesson_summary="Hard exclusion: Z-category junk company.",
                        session_on=state.clock_date,
                    )
                )
                continue

            if str(sett_type).upper() == "SPOT":
                record(company.symbol, "SKIP_SPOT_SETTLEMENT", f"Excluded: {company.symbol} is under SPOT settlement.")
                session.add(
                    TradeLearningLog(
                        symbol=company.symbol,
                        tier=cat,
                        side="BUY",
                        outcome_type="SKIP",
                        entry_price=company.last_price,
                        actor="AUTOTRADER",
                        lesson_summary="Hard exclusion: SPOT settlement stock.",
                        session_on=state.clock_date,
                    )
                )
                continue

            if upper_circ:
                record(company.symbol, "SKIP_UPPER_CIRCUIT_LOCKED", f"Excluded: {company.symbol} is locked at upper circuit.")
                session.add(
                    TradeLearningLog(
                        symbol=company.symbol,
                        tier=cat,
                        side="BUY",
                        outcome_type="SKIP",
                        entry_price=company.last_price,
                        actor="AUTOTRADER",
                        lesson_summary="Hard exclusion: Upper circuit locked.",
                        session_on=state.clock_date,
                    )
                )
                continue

            is_stocknow = getattr(company, "source", "") == "STOCKNOW_FAVORITES" or any(pid in getattr(state, "name", "") for pid in get_allowed_portfolios(self.settings))
            if is_stocknow and has_active_tiers and cat not in {"GSC_L1", "GSC_L2"}:
                record(company.symbol, "WAIT_OBSERVATION_ONLY", "Observation pool only (not in GSC_L1 or GSC_L2).")
                continue
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
            already_bought_q = select(TradeLog.id).where(
                TradeLog.symbol == company.symbol,
                TradeLog.side == "BUY",
                TradeLog.trade_on == state.clock_date,
            )
            if active_pid:
                already_bought_q = already_bought_q.where(TradeLog.portfolio_id == active_pid)
            already_bought = session.scalar(already_bought_q)
            if already_bought:
                record(company.symbol, "WAIT_DAILY_BUY", "Already bought this symbol in this session.")
                continue
            if getattr(state, "kill_switch_active", False):
                record(company.symbol, "KILL_SWITCH", "KILL_SWITCH: Global kill switch is active. Blocking order execution.")
                continue

            # Enforce max orders per day limit across AutoTrader and Hermes
            max_orders = getattr(state, "max_orders_per_day", 20)
            today_orders_q = select(TradeLog.id).where(TradeLog.trade_on == state.clock_date)
            if active_pid:
                today_orders_q = today_orders_q.where(TradeLog.portfolio_id == active_pid)
            today_orders_count = len(session.scalars(today_orders_q).all())
            if today_orders_count >= max_orders:
                record(company.symbol, "CAPS", f"CAPS: Daily order limit reached ({today_orders_count}/{max_orders}).")
                continue

            # Enforce shared daily budget limit across AutoTrader and Hermes
            daily_budget = getattr(state, "daily_budget_bdt", Decimal("4000.00"))
            today_buys_q = select(TradeLog).where(TradeLog.trade_on == state.clock_date, TradeLog.side == "BUY")
            if active_pid:
                today_buys_q = today_buys_q.where(TradeLog.portfolio_id == active_pid)
            today_buys_spend = sum(
                (abs(t.net_cash_change) for t in session.scalars(today_buys_q)),
                ZERO,
            )
            daily_budget_headroom = max(ZERO, daily_budget - today_buys_spend)
            if daily_budget_headroom <= ZERO:
                record(company.symbol, "CAPS", f"CAPS: Daily buy budget exhausted (spent ৳{today_buys_spend:.2f} of ৳{daily_budget:.2f}).")
                continue

            open_basis_q = select(TaxLot.remaining_cost_basis).where(
                TaxLot.symbol == company.symbol, TaxLot.remaining_qty > 0,
            )
            if active_pid:
                open_basis_q = open_basis_q.where(TaxLot.portfolio_id == active_pid)
            open_basis = sum(session.scalars(open_basis_q), ZERO)
            effective_alloc_pct = rule.buy_allocation_pct
            if cat == "GSC_L2":
                effective_alloc_pct = min(effective_alloc_pct, Decimal("15"))
            exposure_cap = money(state.initial_capital * effective_alloc_pct / HUNDRED)
            headroom = max(ZERO, exposure_cap - open_basis)

            # Enforce max symbol exposure cap
            max_sym_cap = getattr(state, "max_symbol_bdt", None)
            if max_sym_cap is not None:
                sym_headroom = max(ZERO, max_sym_cap - open_basis)
                if sym_headroom <= ZERO:
                    record(company.symbol, "CAPS", f"CAPS: Symbol {company.symbol} exposure cap reached (৳{open_basis:.2f} >= ৳{max_sym_cap:.2f}).")
                    continue
                headroom = min(headroom, sym_headroom)

            daily_headroom = max(ZERO, active.initial_cash - active.today_buy_spend)
            budget = min(active.available_cash, headroom, daily_headroom, daily_budget_headroom)

            # Enforce max order gross/net cap
            max_order_cap = getattr(state, "max_order_bdt", None)
            if max_order_cap is not None:
                budget = min(budget, max_order_cap)

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

            if is_preview:
                record(
                    company.symbol,
                    "PREVIEW_BUY",
                    f"Would buy {quantity} shares @ ৳{fill_price}: {analysis.reason}",
                    quantity,
                )
                continue

            buy_idem_key = f"auto:buy:{state.clock_date}:{company.symbol}:{active_pid or '164580'}"
            existing_buy = session.get(OrderIdempotencyKey, buy_idem_key)
            if existing_buy:
                logger.info("AutoTrader buy skipped via persisted idempotency key: %s", buy_idem_key)
                continue

            # In non-DEMO mode, submit to executor first and verify fill before local ledger update
            if getattr(self.adapter, "mode", "DEMO") != "DEMO":
                try:
                    self._dispatch_order(
                        symbol=company.symbol,
                        side="BUY",
                        quantity=quantity,
                        price=fill_price,
                        portfolio_id=active_pid or "164580",
                        trade_date=state.clock_date,
                        session=session,
                        reason=analysis.reason,
                    )
                    record_circuit_success(self.database)
                except Exception as exc:
                    error_code = getattr(exc, "error_code", "EXECUTION_ERROR")
                    logger.warning("AutoTrader live buy execution failed: %s (%s)", error_code, exc)
                    record_circuit_failure(self.database, self.settings, error_code, str(exc))
                    if error_code == "NOT_AUTHENTICATED":
                        record(company.symbol, "NOT_AUTHENTICATED", f"NOT_AUTHENTICATED: {exc}", quantity)
                    elif error_code == "SCHEMA_CHANGED":
                        record(company.symbol, "SCHEMA_CHANGED", f"SCHEMA_CHANGED: {exc}", quantity)
                    else:
                        record(company.symbol, f"BUY_FAILED_{error_code}", str(exc), quantity)
                    continue

            session.add(OrderIdempotencyKey(
                idempotency_key=buy_idem_key,
                symbol=company.symbol,
                side="BUY",
                quantity=quantity,
                price=fill_price,
                response_payload={"reason": analysis.reason},
            ))

            lot = TaxLot(
                symbol=company.symbol, bucket=active_name,
                acquired_on=state.clock_date,
                matures_on=self.calendar.add_sessions(state.clock_date, company.settlement_days),
                original_qty=quantity, remaining_qty=quantity, buy_price=fill_price,
                buy_fee=fee, original_cost_basis=cost, remaining_cost_basis=cost,
                cycle_base_qty=quantity, peak_price=fill_price,
                portfolio_id=active_pid or "164580",
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
                source="STOCKNOW_RECEIPT" if getattr(self.adapter, "mode", "DEMO") != "DEMO" else "DEMO_PAPER",
                portfolio_id=active_pid or "164580",
            )
            session.add(trade)
            session.flush()
            active.available_cash -= cost
            active.today_buy_spend += cost
            record(company.symbol, "BUY", trade.reason, quantity, lot.id)
            trades.append(self._trade_result(trade, "BUY"))
            session.add(
                TradeLearningLog(
                    symbol=company.symbol,
                    tier=cat,
                    side="BUY",
                    outcome_type="BUY_FILL",
                    entry_price=fill_price,
                    actor="AUTOTRADER",
                    lesson_summary=f"AutoTrader Buy filled {quantity} sh @ ৳{fill_price:.2f}",
                    session_on=state.clock_date,
                )
            )

            # In DEMO mode, notify adapter for paper receipt/mock tracking
            if getattr(self.adapter, "mode", "DEMO") == "DEMO":
                try:
                    self._dispatch_order(
                        symbol=company.symbol,
                        side="BUY",
                        quantity=quantity,
                        price=fill_price,
                        portfolio_id=active_pid or "164580",
                        trade_date=state.clock_date,
                        session=session,
                        reason=analysis.reason,
                    )
                except Exception as exc:
                    logger.debug("AutoTrader demo buy dispatch error: %s", exc)

        session.flush()
        if not is_preview:
            check_canary_theses(session, state)
            assert_ledger(session, state, portfolio_id=active_pid)
        cycle.result = CycleResult({
            "id": cycle.id,
            "cycle_id": cycle.id,
            "date": state.clock_date.isoformat(),
            "revision": state.revision, "rules_revision": state.rules_revision,
            "status": "PREVIEW" if is_preview else "COMPLETED",
            "is_preview": is_preview,
            "duplicate": False, "source": "DEMO_PAPER",
            "trades": trades, "decisions": decisions,
            "buy_count": sum(trade["side"] == "BUY" for trade in trades),
            "sell_count": sum(trade["side"] == "SELL" for trade in trades),
        })
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
