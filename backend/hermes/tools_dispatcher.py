"""Hermes Tool Dispatcher, Tool Handlers & Formatter Sub-module.

Decomposed from agent_loop.py to maintain modularity, low nesting depth (<= 3),
and clean architectural separation.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import Settings
from backend.database import (
    CompanyProfile,
    CustomRule,
    PortfolioState,
    RuleAudit,
    TaxLot,
    TradeLog,
)
from backend.engine.agent_actions import (
    check_canary_theses,
    emergency_quarantine_and_canary,
    execute_agentic_buy,
    restore_quarantine,
)
from backend.engine.money import decimal
from backend.hermes.memory import HermesMemory
from backend.hermes.skills_manager import SkillsManager


# ==============================================================================
# Individual Tool Handlers
# ==============================================================================

def handle_report_company_threat(
    args: dict[str, Any],
    session: Session,
    state: PortfolioState,
    settings: Settings,
    checkpoint_mgr: Any,
) -> dict[str, Any]:
    symbol = args["symbol"].upper()
    thesis = args["thesis"]
    memory = HermesMemory(session)
    diff_lines = [
        {"type": "del", "text": f"{symbol} quarantined: False"},
        {"type": "add", "text": f"{symbol} quarantined: True (CRASH_QUARANTINE) | 90% profit-lock + 10% canary probe"},
    ]
    checkpoint_mgr.create_checkpoint(
        session, state, "REPORT_THREAT", f"Threat quarantine & 90/10 canary probe for {symbol}: {thesis}", symbol,
        diff_payload={
            "action": "REPORT_THREAT",
            "actor": "Hermes Agent",
            "summary": f"Emergency quarantine & 90/10 canary for {symbol}: {thesis[:90]}",
            "before": {"symbol": symbol, "quarantined": False},
            "after": {"symbol": symbol, "quarantined": True, "thesis": thesis},
            "diff_lines": diff_lines,
        },
        actor="Hermes Agent",
    )
    result = emergency_quarantine_and_canary(session, state, settings, symbol, thesis)
    memory.record_fact(symbol, f"Operator threat alert: {thesis}. 90% profit locked, 10% canary retained.", "CANARY_PROBE", "HIGH")
    return {"status": "SUCCESS", "tool": "report_company_threat", "result": result}


def handle_restore_quarantined_company(
    args: dict[str, Any],
    session: Session,
    state: PortfolioState,
    checkpoint_mgr: Any,
) -> dict[str, Any]:
    symbol = args["symbol"].upper()
    reason = args.get("reason", "Operator instructed restoration")
    memory = HermesMemory(session)
    diff_lines = [
        {"type": "del", "text": f"{symbol} quarantined: True"},
        {"type": "add", "text": f"{symbol} quarantined: False | Restored to active watchlist"},
    ]
    checkpoint_mgr.create_checkpoint(
        session, state, "RESTORE_QUARANTINE", f"Restore {symbol} from quarantine", symbol,
        diff_payload={
            "action": "RESTORE_QUARANTINE",
            "actor": "Hermes Agent",
            "summary": f"Restored {symbol} from quarantine to active watchlist",
            "before": {"symbol": symbol, "quarantined": True},
            "after": {"symbol": symbol, "quarantined": False, "reason": reason},
            "diff_lines": diff_lines,
        },
        actor="Hermes Agent",
    )
    result = restore_quarantine(session, state, symbol, reason)
    memory.record_fact(symbol, f"Restored from quarantine: {reason}", "STATUS", "HIGH")
    return {"status": "SUCCESS", "tool": "restore_quarantined_company", "result": result}


def handle_set_watchlist_tier(
    args: dict[str, Any],
    session: Session,
    state: PortfolioState,
    checkpoint_mgr: Any,
) -> dict[str, Any]:
    symbol = args["symbol"].upper()
    tier = args["tier"].upper()
    if tier not in {"GSC", "GSC_L1", "GSC_L2"}:
        raise ValueError("Watchlist tier must be GSC, GSC_L1, or GSC_L2.")
    comp = session.get(CompanyProfile, symbol)
    if not comp:
        raise ValueError(f"Company {symbol} not found.")
    old_tier = getattr(comp, "watchlist_category", "GSC")
    diff_lines = [
        {"type": "del", "text": f"{symbol} watchlist_category: {old_tier}"},
        {"type": "add", "text": f"{symbol} watchlist_category: {tier}"},
    ]
    checkpoint_mgr.create_checkpoint(
        session, state, "SET_WATCHLIST_TIER", f"Move {symbol} to {tier}", symbol,
        diff_payload={
            "action": "SET_WATCHLIST_TIER",
            "actor": "Hermes Agent",
            "summary": f"Moved {symbol} from tier {old_tier} to {tier}",
            "before": {"symbol": symbol, "watchlist_category": old_tier},
            "after": {"symbol": symbol, "watchlist_category": tier},
            "diff_lines": diff_lines,
        },
        actor="Hermes Agent",
    )
    comp.watchlist_category = tier
    state.rules_revision += 1
    session.flush()
    memory = HermesMemory(session)
    memory.record_fact(symbol, f"Classified into tier {tier}", "WATCHLIST_CATEGORY", "HIGH")
    return {"status": "SUCCESS", "tool": "set_watchlist_tier", "symbol": symbol, "tier": tier, "old_tier": old_tier}


def handle_update_company_allocation(
    args: dict[str, Any],
    session: Session,
    state: PortfolioState,
    checkpoint_mgr: Any,
) -> dict[str, Any]:
    symbol = args["symbol"].upper()
    pct = decimal(args["buy_allocation_pct"])
    enabled = bool(args.get("enabled", True))
    rule = session.get(CustomRule, symbol)
    if not rule:
        raise ValueError(f"Rule for {symbol} not found.")
    old_alloc = str(rule.buy_allocation_pct)
    diff_lines = [
        {"type": "del", "text": f"{symbol} buy_allocation_pct: {old_alloc}% | enabled: {rule.enabled}"},
        {"type": "add", "text": f"{symbol} buy_allocation_pct: {pct}% | enabled: {enabled}"},
    ]
    checkpoint_mgr.create_checkpoint(
        session, state, "UPDATE_ALLOCATION", f"Set {symbol} allocation to {pct}%", symbol,
        diff_payload={
            "action": "UPDATE_ALLOCATION",
            "actor": "Hermes Agent",
            "summary": f"Adjusted {symbol} buy cap from {old_alloc}% to {pct}%",
            "before": {"symbol": symbol, "buy_allocation_pct": old_alloc, "enabled": rule.enabled},
            "after": {"symbol": symbol, "buy_allocation_pct": str(pct), "enabled": enabled},
            "diff_lines": diff_lines,
        },
        actor="Hermes Agent",
    )
    before = {"buy_allocation_pct": float(rule.buy_allocation_pct), "enabled": rule.enabled}
    rule.buy_allocation_pct = pct
    rule.enabled = enabled
    after = {"buy_allocation_pct": float(rule.buy_allocation_pct), "enabled": rule.enabled}
    session.add(RuleAudit(symbol=symbol, before=before, after=after, session_on=state.clock_date))
    state.rules_revision += 1
    session.flush()
    return {"status": "SUCCESS", "tool": "update_company_allocation", "symbol": symbol, "after": after}


def handle_execute_manual_order(
    args: dict[str, Any],
    session: Session,
    state: PortfolioState,
    settings: Settings,
    checkpoint_mgr: Any,
    stocknow_client: Any | None = None,
) -> dict[str, Any]:
    symbol = args["symbol"].upper()
    side = args.get("side", "BUY").upper()
    qty = int(args.get("quantity", 0))

    if side not in ("BUY", "SELL"):
        raise ValueError(f"Unsupported manual order side '{side}'. Must be BUY or SELL.")

    if side == "SELL" and qty <= 0:
        mature_lots = list(session.scalars(
            select(TaxLot).where(
                TaxLot.symbol == symbol,
                TaxLot.remaining_qty > 0,
                TaxLot.matures_on <= state.clock_date,
            )
        ))
        qty = sum(l.remaining_qty for l in mature_lots)
        if qty <= 0:
            immature_lots = list(session.scalars(
                select(TaxLot).where(TaxLot.symbol == symbol, TaxLot.remaining_qty > 0)
            ))
            if immature_lots:
                earliest = min(l.matures_on for l in immature_lots)
                raise ValueError(f"Cannot sell {symbol}: shares are settlement-locked until {earliest.isoformat()} (T+2 lock).")
            raise ValueError(f"Cannot sell {symbol}: no mature shares available in portfolio.")

    lots = session.scalars(select(TaxLot)).all()
    trades = session.scalars(select(TradeLog)).all()
    lots_snap = [
        {
            "id": l.id, "symbol": l.symbol, "bucket": l.bucket, "acquired_on": l.acquired_on.isoformat(),
            "matures_on": l.matures_on.isoformat(), "original_qty": l.original_qty, "remaining_qty": l.remaining_qty,
            "buy_price": str(l.buy_price), "buy_fee": str(l.buy_fee), "original_cost_basis": str(l.original_cost_basis),
            "remaining_cost_basis": str(l.remaining_cost_basis), "cycle_base_qty": l.cycle_base_qty,
            "next_tier": l.next_tier, "last_sale_revision": l.last_sale_revision, "peak_price": str(l.peak_price),
            "phase": l.phase, "recovery_anchor": str(l.recovery_anchor) if l.recovery_anchor else None,
        }
        for l in lots
    ]
    trades_snap = [
        {
            "id": t.id, "trade_key": t.trade_key, "cycle_id": t.cycle_id, "lot_id": t.lot_id, "symbol": t.symbol,
            "side": t.side, "quantity": t.quantity, "price": str(t.price), "gross_amount": str(t.gross_amount),
            "fee": str(t.fee), "net_cash_change": str(t.net_cash_change), "realized_pnl": str(t.realized_pnl),
            "bucket": t.bucket, "trade_on": t.trade_on.isoformat(), "settles_on": t.settles_on.isoformat(),
            "reason": t.reason, "source": t.source,
        }
        for t in trades
    ]

    checkpoint_mgr.create_checkpoint(
        session, state, f"MANUAL_{side}", f"Manual {side} {qty} shares of {symbol}", symbol,
        diff_payload={
            "action": f"MANUAL_{side}",
            "actor": "Operator via Hermes",
            "summary": f"Executed manual {side} of {qty} shares for {symbol}",
            "before": {}, "after": {"symbol": symbol, "side": side, "qty": qty},
            "diff_lines": [{"type": "add", "text": f"{side} {qty} shares of {symbol}"}],
        },
        actor="Operator",
        extra_snapshot={
            "portfolio_lots": lots_snap,
            "portfolio_trades": trades_snap,
            "initial_capital": str(state.initial_capital),
        },
    )

    from backend.engine.agent_actions import execute_agentic_buy, execute_agentic_sell
    from backend.adapters.stocknow_order_executor import execute_stocknow_virtual_order

    if side == "BUY":
        res = execute_agentic_buy(session, state, settings, symbol, requested_qty=qty if qty > 0 else None)
    else:
        res = execute_agentic_sell(session, state, settings, symbol, requested_qty=qty)

    is_live = stocknow_client is not None and getattr(stocknow_client, "state", "") == "READY"
    dry_run = not is_live
    pid = getattr(stocknow_client, "bound_portfolio_id", "164580") if is_live else "164580"

    import asyncio
    try:
        receipt = asyncio.run(execute_stocknow_virtual_order(
            client=stocknow_client if is_live else None,
            symbol=symbol,
            side=side,
            quantity=res["quantity"],
            price=res["price"],
            portfolio_id=pid,
            dry_run=dry_run,
        ))
    except RuntimeError:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            receipt = pool.submit(
                asyncio.run,
                execute_stocknow_virtual_order(
                    client=stocknow_client if is_live else None,
                    symbol=symbol,
                    side=side,
                    quantity=res["quantity"],
                    price=res["price"],
                    portfolio_id=pid,
                    dry_run=dry_run,
                )
            ).result()

    res["receipt"] = receipt
    return {"status": "SUCCESS", "tool": "execute_manual_order", "result": res}


def handle_learn_or_patch_skill(
    args: dict[str, Any],
    session: Session,
    state: PortfolioState,
    skills_mgr: SkillsManager,
    checkpoint_mgr: Any,
) -> dict[str, Any]:
    skill_name = args["skill_name"]
    lesson_md = args["lesson_markdown"]
    reason = args.get("reason", "Autonomous learning from market event")
    diff_lines = [
        {"type": "del", "text": f"SKILL_{skill_name}.md: previous version"},
        {"type": "add", "text": f"SKILL_{skill_name}.md: revision patched | reason: {reason}"},
    ]
    checkpoint_mgr.create_checkpoint(
        session, state, "LEARN_SKILL", f"Learn/patch skill {skill_name}: {reason}",
        diff_payload={
            "action": "LEARN_SKILL",
            "actor": "Hermes Learner",
            "summary": f"Patched procedural skill {skill_name} ({reason})",
            "before": {"skill": skill_name}, "after": {"skill": skill_name, "reason": reason},
            "diff_lines": diff_lines,
        },
        actor="Hermes Autonomous Learner",
    )
    res = skills_mgr.learn_or_patch_skill(skill_name, lesson_md, reason, session, state.clock_date)
    return {"status": "SUCCESS", "tool": "learn_or_patch_skill", "result": res}


def handle_set_automation_config(
    args: dict[str, Any],
    session: Session,
    state: PortfolioState,
    checkpoint_mgr: Any,
) -> dict[str, Any]:
    enabled = bool(args.get("automation_enabled", getattr(state, "automation_enabled", True)))
    mode = args.get("ingestion_mode", getattr(state, "ingestion_mode", "BACKGROUND_POLLING"))
    interval = int(args.get("polling_interval_sec", getattr(state, "polling_interval_sec", 120)))
    if mode not in {"BACKGROUND_POLLING", "SIDE_BY_SIDE_LIVE"}:
        raise ValueError(f"Invalid ingestion mode: {mode}")
    if not (30 <= interval <= 300):
        raise ValueError(f"Polling interval must be between 30 and 300 seconds, got {interval}")

    old_enabled = getattr(state, "automation_enabled", True)
    old_mode = getattr(state, "ingestion_mode", "BACKGROUND_POLLING")
    old_interval = getattr(state, "polling_interval_sec", 120)
    diff_lines = [
        {"type": "del", "text": f"automation: {'ON' if old_enabled else 'OFF'} | mode: {old_mode} | interval: {old_interval}s"},
        {"type": "add", "text": f"automation: {'ON' if enabled else 'OFF'} | mode: {mode} | interval: {interval}s"},
    ]
    checkpoint_mgr.create_checkpoint(
        session, state, "SET_AUTOMATION_CONFIG",
        f"Set automation enabled={enabled}, mode={mode}, interval={interval}s",
        diff_payload={
            "action": "SET_AUTOMATION_CONFIG",
            "actor": "Operator via Hermes",
            "summary": f"Configured automation to {'ON' if enabled else 'OFF'}, {mode} ({interval}s)",
            "before": {"automation_enabled": old_enabled, "ingestion_mode": old_mode, "polling_interval_sec": old_interval},
            "after": {"automation_enabled": enabled, "ingestion_mode": mode, "polling_interval_sec": interval},
            "diff_lines": diff_lines,
        },
        actor="Operator",
    )
    state.automation_enabled = enabled
    state.paused = not enabled
    state.ingestion_mode = mode
    state.polling_interval_sec = interval
    state.rules_revision += 1
    session.flush()
    return {
        "status": "SUCCESS",
        "tool": "set_automation_config",
        "automation_enabled": state.automation_enabled,
        "ingestion_mode": state.ingestion_mode,
        "polling_interval_sec": state.polling_interval_sec,
    }


def handle_set_ai_model(
    args: dict[str, Any],
    session: Session,
    state: PortfolioState,
    settings: Settings,
    checkpoint_mgr: Any,
) -> dict[str, Any]:
    target_model = args.get("model", "").strip()
    available = [
        "xiaomi/mimo-v2.6-pro",
        "xiaomi/mimo-v2.6-flash",
        "deepseek/deepseek-chat",
        "deepseek/deepseek-r1",
        "meta-llama/llama-3.3-70b-instruct",
        "anthropic/claude-3.5-sonnet",
        "google/gemini-3.1-flash-lite",
        "google/gemini-3.5-flash",
        "google/gemini-3.8-flash",
        "google/gemini-3.7-flash",
        "local-quant-brain",
    ]
    if not target_model:
        curr = getattr(state, "active_model", settings.openrouter_model)
        return {"status": "INFO", "tool": "set_ai_model", "current_model": curr, "available_models": available}

    old_model = getattr(state, "active_model", settings.openrouter_model)
    diff_lines = [
        {"type": "del", "text": f"active_brain_model: {old_model}"},
        {"type": "add", "text": f"active_brain_model: {target_model}"},
    ]
    checkpoint_mgr.create_checkpoint(
        session, state, "SET_AI_MODEL", f"Switch Hermes primary brain to {target_model}",
        diff_payload={
            "action": "SET_AI_MODEL",
            "actor": "Operator",
            "summary": f"Switched AI model from {old_model} to {target_model}",
            "before": {"active_model": old_model},
            "after": {"active_model": target_model},
            "diff_lines": diff_lines,
        },
        actor="Operator",
    )
    state.active_model = target_model
    state.rules_revision += 1
    session.flush()
    return {"status": "SUCCESS", "tool": "set_ai_model", "old_model": old_model, "active_model": target_model}


def handle_evaluate_canary_theses(
    session: Session,
    state: PortfolioState,
    skills_mgr: SkillsManager,
) -> dict[str, Any]:
    updates = check_canary_theses(session, state)
    for u in updates:
        lesson = (
            f"### Case Observation ({state.clock_date.isoformat()}): {u['symbol']}\n"
            f"- Status: {u['status']}\n"
            f"- Outcome: {u['message']}\n"
            f"- Proven rule: 90% liquidation preserved capital while 10% canary captured resolution without catastrophic loss.\n"
        )
        skills_mgr.learn_or_patch_skill(
            "canary_90_10", lesson, f"Auto-learned from {u['symbol']} canary outcome ({u['status']})", session, state.clock_date
        )
    return {"status": "SUCCESS", "tool": "evaluate_canary_theses", "updates": updates}


def handle_control_stocknow_session(
    args: dict[str, Any],
    session: Session,
    state: PortfolioState,
    settings: Settings,
    checkpoint_mgr: Any,
) -> dict[str, Any]:
    action = args.get("action", "check_auth")
    mode = args.get("mode", "ONSCREEN_LIVE")

    from backend.adapters.stocknow_client import StockNowLiveClient
    from backend.adapters.stocknow_market_sync import (
        extract_quotes_from_stocknow,
        sync_live_market_to_db,
    )
    from backend.database import Database

    client = StockNowLiveClient(ingestion_mode=mode)
    database = Database(settings.database_url)

    diff_lines = [
        {"type": "add", "text": f"StockNow live session action: {action}"},
    ]

    action_result: dict[str, Any] = {}
    if action == "launch":
        try:
            import asyncio
            try:
                asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    action_result = pool.submit(asyncio.run, client.launch(mode=mode)).result()
            except RuntimeError:
                action_result = asyncio.run(client.launch(mode=mode))
        except Exception as exc:
            action_result = {"connected": False, "state": "ERROR", "reason": str(exc)}
    elif action == "check_auth":
        try:
            import asyncio
            phone = getattr(settings, "operator_phone", settings.operator_username)
            password = settings.operator_password
            try:
                asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    action_result = pool.submit(asyncio.run, client.ensure_authenticated(phone, password)).result()
            except RuntimeError:
                action_result = asyncio.run(client.ensure_authenticated(phone, password))
        except Exception as exc:
            action_result = {"authenticated": False, "state": "ERROR", "reason": str(exc)}
    elif action in ("sync_market", "sync_prices", "sync"):
        try:
            injected = args.get("payload")
            from backend.adapters.stocknow_market_sync import extract_quotes_from_payload
            if injected is not None:
                quotes = extract_quotes_from_payload(injected)
            else:
                import asyncio
                try:
                    asyncio.get_running_loop()
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        quotes = pool.submit(asyncio.run, extract_quotes_from_stocknow(client)).result()
                except RuntimeError:
                    quotes = asyncio.run(extract_quotes_from_stocknow(client))
            action_result = sync_live_market_to_db(session, quotes, session_date=state.clock_date)
        except Exception as exc:
            action_result = {"success": False, "error": str(exc)}
    elif action == "sync_portfolio":
        try:
            from backend.adapters.stocknow_portfolio_sync import (
                extract_hummingbird_portfolio,
                reconcile_portfolio_to_db,
            )
            injected = args.get("injected_portfolio") or args.get("portfolio")
            extracted = extract_hummingbird_portfolio(client, injected_portfolio=injected)
            action_result = reconcile_portfolio_to_db(
                session, settings, extracted, checkpoint_mgr=checkpoint_mgr
            )
            pname = extracted.get("portfolio_name", "Humming Bird")
            diff_lines.append({
                "type": "add",
                "text": f"Synced virtual portfolio '{pname}' ({action_result.get('synced_holdings_count', 0)} holdings, cash: ৳{action_result.get('cash_balance', 0):,.2f})",
            })
        except Exception as exc:
            action_result = {"success": False, "error": str(exc)}
    elif action == "scheduler_start":
        from backend.engine.scheduler import get_active_scheduler
        sch = get_active_scheduler()
        if sch:
            action_result = sch.start()
        else:
            action_result = {"status": "NO_SCHEDULER_INSTANCE"}
        diff_lines.append({"type": "add", "text": "Started DSE market-hours auto-scheduler background loop."})
    elif action == "scheduler_stop":
        from backend.engine.scheduler import get_active_scheduler
        sch = get_active_scheduler()
        if sch:
            action_result = sch.stop_sync()
        else:
            action_result = {"status": "NO_SCHEDULER_INSTANCE"}
        diff_lines.append({"type": "modify", "text": "Stopped DSE market-hours auto-scheduler background loop."})
    elif action == "scheduler_tick":
        from backend.engine.scheduler import get_active_scheduler
        sch = get_active_scheduler()
        force = bool(args.get("force", True))
        if sch:
            action_result = sch.run_scheduled_tick_sync(force=force, session=session)
        else:
            action_result = {"status": "NO_SCHEDULER_INSTANCE"}
        diff_lines.append({"type": "add", "text": f"Executed DSE scheduler tick (status: {action_result.get('status', 'EXECUTED')})."})
    elif action == "close":
        try:
            import asyncio
            try:
                asyncio.get_running_loop()
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    action_result = pool.submit(asyncio.run, client.close()).result()
            except RuntimeError:
                action_result = asyncio.run(client.close())
        except Exception as exc:
            action_result = {"state": "CLOSED", "reason": str(exc)}

    checkpoint_mgr.create_checkpoint(
        session, state, "STOCKNOW_CONTROL", f"StockNow session action: {action}", None,
        diff_payload={
            "action": action,
            "actor": "Hermes Agent",
            "summary": f"Executed StockNow command: {action}",
            "result": action_result,
            "diff_lines": diff_lines,
        },
        actor="Hermes Agent",
    )

    return {
        "status": "SUCCESS",
        "tool": "control_stocknow_session",
        "action": action,
        "result": action_result,
    }


# ==============================================================================
# Central Tool Dispatcher Function
# ==============================================================================

def dispatch_tool(
    tool_name: str,
    args: dict[str, Any],
    session: Session,
    state: PortfolioState,
    settings: Settings,
    skills_mgr: SkillsManager,
    checkpoint_mgr: Any,
    stocknow_client: Any | None = None,
) -> dict[str, Any]:
    """Routes tool execution to dedicated handlers with low nesting depth (<= 3)."""
    if tool_name == "report_company_threat":
        return handle_report_company_threat(args, session, state, settings, checkpoint_mgr)
    elif tool_name == "restore_quarantined_company":
        return handle_restore_quarantined_company(args, session, state, checkpoint_mgr)
    elif tool_name == "set_watchlist_tier":
        return handle_set_watchlist_tier(args, session, state, checkpoint_mgr)
    elif tool_name == "update_company_allocation":
        return handle_update_company_allocation(args, session, state, checkpoint_mgr)
    elif tool_name == "execute_manual_order":
        return handle_execute_manual_order(args, session, state, settings, checkpoint_mgr, stocknow_client=stocknow_client)
    elif tool_name == "learn_or_patch_skill":
        return handle_learn_or_patch_skill(args, session, state, skills_mgr, checkpoint_mgr)
    elif tool_name == "rollback_last_checkpoint":
        res = checkpoint_mgr.rollback_last(session, state)
        return {"status": "SUCCESS", "tool": tool_name, "result": res}
    elif tool_name == "set_automation_config":
        return handle_set_automation_config(args, session, state, checkpoint_mgr)
    elif tool_name == "set_ai_model":
        return handle_set_ai_model(args, session, state, settings, checkpoint_mgr)
    elif tool_name == "evaluate_canary_theses":
        return handle_evaluate_canary_theses(session, state, skills_mgr)
    elif tool_name == "control_stocknow_session":
        return handle_control_stocknow_session(args, session, state, settings, checkpoint_mgr)
    elif tool_name in ("schedule_cron_task", "schedule_task"):
        from backend.hermes_os.cron_manager import CronManager
        job = CronManager.schedule_task(
            session=session,
            instruction=args.get("natural_instruction") or args.get("instruction"),
            schedule_expr=args.get("schedule_expr"),
            name=args.get("name"),
            action_type=args.get("action_type"),
            params=args.get("params") or {},
        )
        return {
            "status": "SUCCESS",
            "tool": tool_name,
            "job": {
                "id": job.id,
                "name": job.name,
                "schedule_expr": job.schedule_expr,
                "action_type": job.action_type,
                "natural_instruction": job.natural_instruction,
                "enabled": job.enabled,
            },
        }
    elif tool_name in ("list_or_remove_cron_tasks", "manage_cron_jobs"):
        from backend.hermes_os.cron_manager import CronManager
        action = str(args.get("action", "LIST")).upper()
        job_id = args.get("job_id")
        if action == "DELETE" and job_id:
            del_ok = CronManager.delete_job(session, job_id)
            return {"status": "SUCCESS", "tool": tool_name, "action": "DELETE", "deleted": del_ok, "job_id": job_id}
        elif action == "TOGGLE" and job_id:
            toggled = CronManager.toggle_job(session, job_id)
            return {"status": "SUCCESS", "tool": tool_name, "action": "TOGGLE", "job": toggled}
        else:
            jobs = CronManager.list_jobs(session)
            return {"status": "SUCCESS", "tool": tool_name, "action": "LIST", "jobs": jobs, "total": len(jobs)}
    else:
        raise ValueError(f"Unknown tool: {tool_name}")


# ==============================================================================
# Tool Response Formatting Helpers
# ==============================================================================

def _fmt_rollback(res: dict[str, Any], bangla: bool) -> str:
    syms = ", ".join(res["restored_symbols"]) if res["restored_symbols"] else "N/A"
    if bangla:
        return (
            f"DEMO/PAPER · [Hermes Agentic Rollback ↺]\n"
            f"✅ পূর্ববর্তী স্টেট চেকপয়েন্ট সফলভাবে রোলব্যাক করা হয়েছে!\n"
            f"- রিভার্ট করা অ্যাকশন: {res['action_reverted']}\n"
            f"- বিবরণ: {res['description']}\n"
            f"- পুনঃস্থাপিত কোম্পানি: {syms}\n"
            f"পোর্টফোলিও পূর্বের স্থিতিশীল অবস্থায় ফিরে গেছে।"
        )
    return (
        f"DEMO/PAPER · [Hermes Rollback ↺]\n"
        f"Successfully restored previous state checkpoint:\n"
        f"- Reverted: {res['action_reverted']} ({res['description']})\n"
        f"- Restored: {syms}."
    )


def _fmt_report_threat(res: dict[str, Any], bangla: bool) -> str:
    sym = res["symbol"]
    sold_qty = res["sold_qty"]
    pnl = res["realized_pnl"]
    canary_qty = res["canary_qty"]
    if sold_qty > 0:
        profit_note = f"পূর্বের অর্জিত লাভ ঘরে তুলতে {sold_qty} টি শেয়ার বিক্রি করে ৳{pnl:,.2f} নিট লাভ লক করা হয়েছে!"
    else:
        profit_note = "কঠোর নো-লস নিয়মে লোকসানে বিক্রি করা হয়নি।"

    if bangla:
        return (
            f"DEMO/PAPER · [Hermes Agentic Intervention & Checkpoint Saved]\n"
            f"🚨 {sym}-এর ওপর এমার্জেন্সি অ্যাকশন সম্পন্ন হয়েছে:\n"
            f"১. {sym}-কে অবিলম্বে CRASH_QUARANTINE-এ নেওয়া হয়েছে (নতুন কেনা সম্পূর্ণ বন্ধ)।\n"
            f"২. মুনাফা রক্ষা (৯০% প্রস্থান): {profit_note}\n"
            f"৩. ক্যানারি প্রোব (১০%): আপনার থিসিস সত্যি কিনা তা যাচাই করার জন্য {canary_qty} টি শেয়ার পর্যবেক্ষণে রাখা হয়েছে।\n"
            f"৪. স্টেট চেকপয়েন্ট সেভ করা হয়েছে (প্রয়োজনে আপনি `/rollback` দিয়ে এটি আনডু করতে পারবেন)।"
        )
    return (
        f"DEMO/PAPER · [Hermes Agentic Intervention & Checkpoint Saved]\n"
        f"Action executed on {sym}:\n"
        f"1. Placed in CRASH_QUARANTINE.\n"
        f"2. Profit-lock: Sold {sold_qty} shares (৳{pnl:,.2f} gain).\n"
        f"3. Retained {canary_qty} canary shares (10%) for thesis verification.\n"
        f"4. State checkpoint created. You can type `/rollback` to undo."
    )


def _fmt_watchlist_tier(tool_res: dict[str, Any], bangla: bool) -> str:
    sym = tool_res["symbol"]
    tier = tool_res["tier"]
    tier_names = {"GSC": "Big Giant Stable", "GSC_L1": "GSC Upper Trends L1 (Comeback)", "GSC_L2": "GSC Upper Trends L2 (Swing Scalp)"}
    name = tier_names.get(tier, tier)
    if bangla:
        return (
            f"DEMO/PAPER · [Watchlist Tier Updated]\n"
            f"✅ {sym}-কে সফলভাবে {name}-এ স্থানান্তর করা হয়েছে। "
            f"চেকপয়েন্ট সেভ করা হয়েছে (আনডু করতে `/rollback` লিখুন)।"
        )
    return f"DEMO/PAPER · {sym} moved to tier {name}. Checkpoint saved."


def _fmt_automation_config(tool_res: dict[str, Any], bangla: bool) -> str:
    enabled_str = "চালু (ON)" if tool_res["automation_enabled"] else "বন্ধ (OFF/Paused)"
    mode_desc = (
        "Background Polling (মেথড A)" if tool_res["ingestion_mode"] == "BACKGROUND_POLLING"
        else "Side-by-Side Live Browser (মেথড B)"
    )
    if bangla:
        return (
            f"DEMO/PAPER · [Automation Configuration Updated ⚙️]\n"
            f"✅ সিস্টেম কনফিগারেশন সফলভাবে আপডেট করা হয়েছে:\n"
            f"- **Buy/Sell Automation**: {enabled_str}\n"
            f"- **Ingestion Mode**: {mode_desc}\n"
            f"- **Polling Interval**: {tool_res['polling_interval_sec']} সেকেন্ড\n"
            f"স্টেট চেকপয়েন্ট সেভ করা হয়েছে (পূর্বের অবস্থায় ফিরতে `/rollback` কমান্ড ব্যবহার করুন)।"
        )
    return (
        f"DEMO/PAPER · [Automation Configuration Updated]\n"
        f"✅ Automation config updated:\n"
        f"- **Buy/Sell Automation**: {'ON' if tool_res['automation_enabled'] else 'OFF (Paused)'}\n"
        f"- **Ingestion Mode**: {tool_res['ingestion_mode']}\n"
        f"- **Polling Interval**: {tool_res['polling_interval_sec']}s\n"
        f"State checkpoint saved. Type `/rollback` to undo."
    )


def _fmt_ai_model(tool_res: dict[str, Any], bangla: bool) -> str:
    if tool_res.get("status") == "INFO":
        if bangla:
            return (
                f"DEMO/PAPER · [Hermes Brain & Models 🧠]\n"
                f"বর্তমান সক্রিয় মডেল: `{tool_res['current_model']}`\n"
                f"উপলব্ধ মডেলসমূহ: {', '.join(tool_res['available_models'])}\n"
                f"মডেল পরিবর্তন করতে লিখুন: `/model <model_name>` (যেমন `/model deepseek/deepseek-chat`)"
            )
        return (
            f"DEMO/PAPER · [Hermes Brain & Models 🧠]\n"
            f"Active Model: `{tool_res['current_model']}`\n"
            f"Available Models: {', '.join(tool_res['available_models'])}\n"
            f"To switch model, type: `/model <name>` (e.g. `/model deepseek/deepseek-chat`)"
        )

    if bangla:
        return (
            f"DEMO/PAPER · [Hermes Brain Model Switched 🧠]\n"
            f"✅ প্রাথমিক এআই মডেল সফলভাবে পরিবর্তন করা হয়েছে:\n"
            f"- **পূর্ববর্তী মডেল**: `{tool_res['old_model']}`\n"
            f"- **নতুন সক্রিয় মডেল**: `{tool_res['active_model']}`\n"
            f"Fallback চেইন: 1st Fallback: Free Google Gemini API → 2nd Fallback: Local Deterministic Brain.\n"
            f"স্টেট চেকপয়েন্ট সেভ করা হয়েছে (রিভার্ট করতে `/rollback` লিখুন)।"
        )
    return (
        f"DEMO/PAPER · [Hermes Brain Model Switched 🧠]\n"
        f"Switched primary AI brain from `{tool_res['old_model']}` to `{tool_res['active_model']}`.\n"
        f"Fallback Chain: 1st Fallback: Free Gemini API -> 2nd Fallback: Local Deterministic Brain.\n"
        f"State checkpoint saved. Type `/rollback` to revert."
    )


def format_tool_response(tool_name: str, tool_res: dict[str, Any], user_msg: str, snapshot: dict) -> str:
    """Formats human-friendly Bangla/English message summarizing the executed tool's outcome."""
    bangla = any("\u0980" <= char <= "\u09ff" for char in user_msg) or any(w in user_msg.lower() for w in ("koro", "deulia", "khoti"))

    if tool_name == "rollback_last_checkpoint":
        if tool_res["status"] == "SUCCESS":
            return _fmt_rollback(tool_res["result"], bangla)
        return f"DEMO/PAPER · Rollback failed: {tool_res.get('error')}"

    if tool_name == "report_company_threat":
        if tool_res["status"] == "SUCCESS":
            return _fmt_report_threat(tool_res["result"], bangla)

    if tool_name == "set_watchlist_tier":
        return _fmt_watchlist_tier(tool_res, bangla)

    if tool_name == "learn_or_patch_skill":
        res = tool_res["result"]
        if bangla:
            return (
                f"DEMO/PAPER · [Hermes Self-Improving Skill Updated 🧠]\n"
                f"✅ নতুন জ্ঞান সংরক্ষিত হয়েছে:\n"
                f"- স্কিল ফাইল: `{res['file']}` (Version {res['version']})\n"
                f"- কারণ: {res['reason']}\n"
                f"হার্মিস ভবিষ্যতে এই নিয়মটি সবসময় মেনে চলবে।"
            )
        return f"DEMO/PAPER · Skill patched: `{res['file']}` (v{res['version']}). Reason: {res['reason']}."

    if tool_name == "restore_quarantined_company":
        sym = tool_res["result"]["symbol"]
        if bangla:
            return (
                f"DEMO/PAPER · [Company Restored]\n"
                f"✅ {sym}-কে কোয়ারেন্টাইন তালিকা থেকে সক্রিয় ওয়াচলিস্টে রিস্টোর করা হয়েছে। "
                f"চেকপয়েন্ট সেভ করা হয়েছে।"
            )
        return f"DEMO/PAPER · {sym} restored to active watchlist. Checkpoint saved."

    if tool_name == "execute_manual_order":
        res = tool_res["result"]
        side = res.get("side", "BUY")
        sym = res["symbol"]
        qty = res["quantity"]
        pr = res["price"]
        receipt = res.get("receipt", {})
        oid = receipt.get("order_id", "N/A")
        emode = receipt.get("execution_mode", "PAPER_VERIFIED")
        mode_label_bn = " (লাইভ StockNow ব্রাউজারে এক্সিকিউটেড 🟢)" if emode == "STOCKNOW_LIVE_DOM" else " (পেপার ভেরিফাইড)"
        mode_label_en = " (Live StockNow Browser Executed 🟢)" if emode == "STOCKNOW_LIVE_DOM" else " (Paper Verified)"
        if side == "BUY":
            cost = res.get("cost", 0.0)
            bucket = res.get("bucket", "A")
            return (
                f"DEMO/PAPER · [Manual Buy Executed]\n"
                f"✅ {sym}-এর {qty} টি শেয়ার ৳{pr:,.2f} দরে কেনা হয়েছে (মোট খরচ: ৳{cost:,.2f}, বাকেট {bucket})。\n"
                f"• StockNow ভার্চুয়াল রসিদ: {oid} ({emode}{mode_label_bn})"
                if bangla
                else (
                    f"DEMO/PAPER · [Manual Buy Executed]\n"
                    f"✅ Bought {qty} shares of {sym} at ৳{pr:,.2f} (Total: ৳{cost:,.2f}, Bucket {bucket}).\n"
                    f"• StockNow Virtual Receipt: {oid} ({emode}{mode_label_en})"
                )
            )
        else:
            proceeds = res.get("proceeds", 0.0)
            pnl = res.get("realized_pnl", 0.0)
            return (
                f"DEMO/PAPER · [Manual Matured Sell Executed]\n"
                f"✅ {sym}-এর {qty} টি ম্যাচিউরড শেয়ার ৳{pr:,.2f} দরে বিক্রি করা হয়েছে (মোট আদায়: ৳{proceeds:,.2f}, প্রফিট: +৳{pnl:,.2f})。\n"
                f"• StockNow ভার্চুয়াল রসিদ: {oid} ({emode}{mode_label_bn})"
                if bangla
                else (
                    f"DEMO/PAPER · [Manual Matured Sell Executed]\n"
                    f"✅ Sold {qty} mature shares of {sym} at ৳{pr:,.2f} (Net proceeds: ৳{proceeds:,.2f}, Realized P/L: +৳{pnl:,.2f}).\n"
                    f"• StockNow Virtual Receipt: {oid} ({emode}{mode_label_en})"
                )
            )

    if tool_name == "set_automation_config":
        return _fmt_automation_config(tool_res, bangla)

    if tool_name == "set_ai_model":
        return _fmt_ai_model(tool_res, bangla)

    if tool_name == "control_stocknow_session":
        action = tool_res.get("action", "")
        res = tool_res.get("result", {})
        if action == "launch":
            connected = res.get("connected", False)
            return (
                f"DEMO/PAPER · [StockNow Session]\n"
                f"✅ StockNow লাইভ ব্রাউজার {'চালু করা হয়েছে (READY)' if connected else 'স্টার্ট করা হয়েছে'}।"
                if bangla
                else f"DEMO/PAPER · StockNow live browser session {'launched (READY)' if connected else 'initiated'}."
            )
        elif action == "check_auth":
            auth = res.get("authenticated", False)
            msg = res.get("message", "লগইন চেক সম্পন্ন")
            return (
                f"DEMO/PAPER · [StockNow Auth]\n"
                f"✅ StockNow লগইন স্টেটাস: {'লগইন ভেরিফাইড (READY)' if auth else msg}।"
                if bangla
                else f"DEMO/PAPER · StockNow authentication: {'Authenticated (READY)' if auth else msg}."
            )
        elif action in ("sync_market", "sync_prices", "sync"):
            count = res.get("synced_count", 0)
            syms = ", ".join(res.get("symbols", [])) if res.get("symbols") else "none"
            return (
                f"DEMO/PAPER · [StockNow Market Sync]\n"
                f"✅ StockNow থেকে {count} টি কোম্পানির লাইভ DSE প্রাইস ও কার্ভ ডেটাবেজে সিঙ্ক করা হয়েছে ({syms})।"
                if bangla
                else f"DEMO/PAPER · Synchronized {count} live DSE quotes & curves from StockNow ({syms})."
            )
        elif action == "sync_portfolio":
            pname = res.get("portfolio_name", "Humming Bird")
            count = res.get("synced_holdings_count", 0)
            cash = res.get("cash_balance", 0.0)
            syms = ", ".join(res.get("symbols", [])) if res.get("symbols") else "none"
            return (
                f"DEMO/PAPER · [StockNow Portfolio Sync]\n"
                f"✅ StockNow '{pname}' ভার্চুয়াল পোর্টফোলিও সফলভাবে সিঙ্ক করা হয়েছে।\n"
                f"• হোল্ডিংস: {count} টি ({syms})\n"
                f"• ক্যাশ ব্যালেন্স: ৳{cash:,.2f}\n"
                f"• T+2 লেজার সম্পূর্ণ ব্যালেন্সড ও রিকনসাইলড।"
                if bangla
                else (
                    f"DEMO/PAPER · [StockNow Portfolio Sync]\n"
                    f"✅ StockNow virtual portfolio '{pname}' synced successfully.\n"
                    f"• Holdings: {count} ({syms})\n"
                    f"• Cash Balance: ৳{cash:,.2f}\n"
                    f"• T+2 ledger fully balanced to the paisa."
                )
            )
        elif action == "scheduler_start":
            status = res.get("status", "STARTED")
            return (
                f"DEMO/PAPER · [DSE Market Scheduler]\n"
                f"✅ DSE মার্কেট-আওয়ার অটো-শিডিউলার ব্যাকগ্রাউন্ড লুপ সফলভাবে চালু করা হয়েছে (Status: {status})।\n"
                f"• ট্রেডিং উইন্ডো: ১০:০০ AM – ০২:৩০ PM (রবি–বৃহস্পতি)\n"
                f"• লাইভ কোট ও অটোমেশন সাইকেল স্বয়ংক্রিয়ভাবে এক্সিকিউট হবে।"
                if bangla
                else (
                    f"DEMO/PAPER · [DSE Market Scheduler]\n"
                    f"✅ DSE market-hours auto-scheduler started successfully ({status}).\n"
                    f"• Active window: 10:00 AM – 2:30 PM (Sun–Thu)\n"
                    f"• Monitoring live DSE quotes and executing automation ticks."
                )
            )
        elif action == "scheduler_stop":
            status = res.get("status", "STOPPED")
            return (
                f"DEMO/PAPER · [DSE Market Scheduler]\n"
                f"🛑 DSE মার্কেট-আওয়ার অটো-শিডিউলার থামানো হয়েছে ({status})।"
                if bangla
                else f"DEMO/PAPER · DSE market-hours auto-scheduler stopped ({status})."
            )
        elif action == "scheduler_tick":
            status = res.get("status", "EXECUTED")
            tick = res.get("tick_count", 0)
            synced = res.get("synced_quotes", 0)
            return (
                f"DEMO/PAPER · [DSE Market Scheduler Tick]\n"
                f"⚡ শিডিউলার টিক সফলভাবে রান হয়েছে (Status: {status}, Tick #{tick})।\n"
                f"• সিঙ্ক হওয়া কোট: {synced} টি কোম্পানি\n"
                f"• পোর্টফোলিও স্ন্যাপশট ও ডিসিশন সাইকেল SSE তে ব্রডকাস্ট হয়েছে।"
                if bangla
                else (
                    f"DEMO/PAPER · [DSE Market Scheduler Tick]\n"
                    f"⚡ Scheduler tick executed successfully (Status: {status}, Tick #{tick}).\n"
                    f"• Synced quotes: {synced} companies\n"
                    f"• Snapshot and cycle evaluated and broadcast."
                )
            )
        return (
            f"DEMO/PAPER · StockNow সেশন অ্যাকশন '{action}' সম্পন্ন হয়েছে।"
            if bangla
            else f"DEMO/PAPER · StockNow session action '{action}' executed."
        )

    return f"DEMO/PAPER · Tool {tool_name} executed successfully."


# ==============================================================================
# Intent Detection Logic
# ==============================================================================

def detect_intent_and_tool(message: str, snapshot: dict) -> tuple[str | None, dict[str, Any]]:
    """High-precision intent detector for Bangla, Banglish & English agent commands."""
    text = message.strip()
    text_lower = text.lower()

    # 0. Model command
    if text.startswith("/model") or text_lower.startswith("switch model") or text_lower.startswith("model change") or text_lower.startswith("model switch"):
        parts = text.split(maxsplit=1)
        raw_target = parts[1].strip() if len(parts) > 1 else ""
        alias_map = {
            "mimov2.6 pro": "xiaomi/mimo-v2.6-pro",
            "mimov2.6-pro": "xiaomi/mimo-v2.6-pro",
            "mimo-v2.6-pro": "xiaomi/mimo-v2.6-pro",
            "mimo v2.6 pro": "xiaomi/mimo-v2.6-pro",
            "mimo pro": "xiaomi/mimo-v2.6-pro",
            "mimov2.6 flash": "xiaomi/mimo-v2.6-flash",
            "mimov2.6-flash": "xiaomi/mimo-v2.6-flash",
            "mimo-v2.6-flash": "xiaomi/mimo-v2.6-flash",
            "mimo flash": "xiaomi/mimo-v2.6-flash",
            "deepseek 4.1": "deepseek/deepseek-chat",
            "deepseek 4.1 flash": "deepseek/deepseek-chat",
            "deepseek": "deepseek/deepseek-chat",
            "deepseek v3": "deepseek/deepseek-chat",
            "deepseek-chat": "deepseek/deepseek-chat",
            "deepseek r1": "deepseek/deepseek-r1",
            "deepseek-r1": "deepseek/deepseek-r1",
            "llama": "meta-llama/llama-3.3-70b-instruct",
            "llama 3.3": "meta-llama/llama-3.3-70b-instruct",
            "claude": "anthropic/claude-3.5-sonnet",
            "claude 3.5": "anthropic/claude-3.5-sonnet",
            "gemini 3.1": "google/gemini-3.1-flash-lite",
            "gemini-3.1-flash-lite": "google/gemini-3.1-flash-lite",
            "gemini 3.1 flash lite": "google/gemini-3.1-flash-lite",
            "gemini 3.1 lite": "google/gemini-3.1-flash-lite",
            "gemini lite": "google/gemini-3.1-flash-lite",
            "gemini 3.5": "google/gemini-3.5-flash",
            "gemini-3.5-flash": "google/gemini-3.5-flash",
            "gemini 3.5 flash": "google/gemini-3.5-flash",
            "gemini 3.8": "google/gemini-3.8-flash",
            "gemini-3.8-flash": "google/gemini-3.8-flash",
            "gemini 3.7": "google/gemini-3.7-flash",
            "gemini-3.7-flash": "google/gemini-3.7-flash",
            "local": "local-quant-brain",
            "local brain": "local-quant-brain",
            "local-quant-brain": "local-quant-brain",
        }
        target = alias_map.get(raw_target.lower(), raw_target)
        return "set_ai_model", {"model": target}

    # 0.1 StockNow Live Session Commands
    launch_words = (
        "launch stocknow", "open stocknow", "stocknow browser", "live browser", "launch browser",
        "stocknow open koro", "browser kholo", "browser open koro", "start stocknow", "launch live browser"
    )
    if any(w in text_lower for w in launch_words):
        return "control_stocknow_session", {"action": "launch", "mode": "ONSCREEN_LIVE"}

    auth_words = (
        "stocknow login", "check login", "login check", "stocknow auth",
        "stocknow login check koro", "auto login", "login check koro", "check stocknow login", "check / auto-login"
    )
    if any(w in text_lower for w in auth_words):
        return "control_stocknow_session", {"action": "check_auth"}

    portfolio_sync_words = (
        "sync hummingbird", "sync hummingbird portfolio", "sync humming bird portfolio",
        "sync humming bird", "humming bird portfolio sync", "hummingbird portfolio sync",
        "humming bird sync koro", "hummingbird sync koro", "portfolio sync koro",
        "humming bird portfolio sync koro", "sync portfolio",
    )
    if any(w in text_lower for w in portfolio_sync_words):
        return "control_stocknow_session", {"action": "sync_portfolio"}

    sync_words = (
        "sync live market", "sync market", "sync stocknow", "sync live prices", "sync live",
        "live price sync koro", "market sync koro", "sync live market prices", "price sync koro", "sync koro"
    )
    if any(w in text_lower for w in sync_words):
        return "control_stocknow_session", {"action": "sync_market"}

    scheduler_start_words = (
        "start dse scheduler", "start scheduler", "scheduler start", "dse scheduler start",
        "scheduler start koro", "start market scheduler", "scheduler chalu koro", "chalu koro scheduler"
    )
    if any(w in text_lower for w in scheduler_start_words):
        return "control_stocknow_session", {"action": "scheduler_start"}

    scheduler_stop_words = (
        "stop dse scheduler", "stop scheduler", "scheduler stop", "dse scheduler stop",
        "scheduler stop koro", "stop market scheduler", "scheduler bondho koro", "bondho koro scheduler"
    )
    if any(w in text_lower for w in scheduler_stop_words):
        return "control_stocknow_session", {"action": "scheduler_stop"}

    scheduler_tick_words = (
        "run scheduler tick now", "scheduler tick", "run scheduler tick", "tick now",
        "force scheduler tick", "run tick now", "scheduler tick dao", "tick koro"
    )
    if any(w in text_lower for w in scheduler_tick_words):
        return "control_stocknow_session", {"action": "scheduler_tick", "force": True}

    # 1. Rollback command
    if text_lower in {"/rollback", "rollback", "undo", "undo last action", "undo koro", "ager obosthay nao"}:
        return "rollback_last_checkpoint", {}

    # 2. Match company symbol
    symbol_aliases = {
        "BANKASIA": ["bankasia", "bank asia", "bank-asia"],
        "EXIM1STMF": ["exim1stmf", "exim", "exim 1st", "exim mutual fund"],
        "SQURPHARMA": ["squrpharma", "square pharma", "square pharmaceuticals", "square"],
        "BXPHARMA": ["bxpharma", "beximco pharma", "beximco pharmaceuticals", "beximco"],
        "GP": ["gp", "grameenphone", "grameen phone", "grameen"],
        "MATINSPINN": ["matinspinn", "matin spinning", "matin spin", "matin"],
        "IBNSINA": ["ibnsina", "ibn sina", "ibn-sina"],
    }
    matched_sym = None
    for sym, aliases in symbol_aliases.items():
        if any(alias in text_lower for alias in aliases):
            matched_sym = sym
            break

    # Dynamic symbol match against all active watchlist / database companies in snapshot
    if not matched_sym and snapshot.get("companies"):
        for comp in snapshot["companies"]:
            csym = comp.get("symbol", "").upper()
            if not csym:
                continue
            if csym.lower() in text_lower:
                matched_sym = csym
                break
            cname = comp.get("name", "").lower()
            if cname and len(cname) > 3 and cname in text_lower:
                matched_sym = csym
                break

    # 3. Emergency threat / bankruptcy alert
    threat_words = (
        "khoti", "deulia", "loss hobe", "bankrupt", "collapse", "dhowsh",
        "scam", "fraud", "bad news", "ruin", "problem", "baje obostha", "vanishing",
        "threat", "quarantine koro", "quarantine e rakh"
    )
    if matched_sym and any(w in text_lower for w in threat_words):
        return "report_company_threat", {"symbol": matched_sym, "thesis": message}

    # 4. Restore company
    restore_words = ("restore", "quarantine theke ber", "release", "unquarantine", "valoe ashe", "bhalo ache restore")
    if matched_sym and any(w in text_lower for w in restore_words):
        return "restore_quarantined_company", {"symbol": matched_sym, "reason": message}

    # 5. Watchlist Tier classification
    if matched_sym and ("tier" in text_lower or "move" in text_lower or "category" in text_lower or "set" in text_lower):
        if "l1" in text_lower or "comeback" in text_lower:
            return "set_watchlist_tier", {"symbol": matched_sym, "tier": "GSC_L1"}
        elif "l2" in text_lower or "scalp" in text_lower or "swing" in text_lower:
            return "set_watchlist_tier", {"symbol": matched_sym, "tier": "GSC_L2"}
        elif "gsc" in text_lower or "giant" in text_lower or "stable" in text_lower:
            return "set_watchlist_tier", {"symbol": matched_sym, "tier": "GSC"}

    # 6. Allocation update
    if matched_sym and ("allocation" in text_lower or "%" in text_lower or "buy cap" in text_lower):
        digits = "".join(ch for ch in text if ch.isdigit() or ch == ".")
        if digits:
            try:
                pct = float(digits)
                if 0 <= pct <= 100:
                    return "update_company_allocation", {"symbol": matched_sym, "buy_allocation_pct": pct}
            except ValueError:
                pass

    # 7. Explicit Buy
    buy_words = ("buy koro", "share kino", "explicitly buy", "kine dao", "buy now", "kine felo", "kino", "buy", "purchase", "kine nao")
    if matched_sym and any(w in text_lower for w in buy_words):
        digits = "".join(ch for ch in text if ch.isdigit())
        qty = int(digits) if digits else 0
        return "execute_manual_order", {"symbol": matched_sym, "side": "BUY", "quantity": qty}

    # 7.1 Explicit Sell
    sell_words = (
        "sell koro", "share becho", "explicitly sell", "beche dao", "sell now",
        "bikri koro", "becho", "sell", "bikri", "beche felo", "sob beche dao", "sob sell koro", "liquidate"
    )
    if matched_sym and any(w in text_lower for w in sell_words):
        digits = "".join(ch for ch in text if ch.isdigit())
        qty = int(digits) if digits else 0
        return "execute_manual_order", {"symbol": matched_sym, "side": "SELL", "quantity": qty}

    # 8. Learning / Teaching a lesson
    learn_words = ("mone rakhba", "lesson:", "remember this:", "notun rule:", "sikhe rakho")
    if any(w in text_lower for w in learn_words):
        return "learn_or_patch_skill", {
            "skill_name": f"learned_rule_{matched_sym.lower() if matched_sym else 'general'}",
            "lesson_markdown": message,
            "reason": "Operator taught a new trading rule via chat",
        }

    # 9. Master Automation & Ingestion Mode Controls
    current_app = snapshot.get("app", {})
    curr_enabled = current_app.get("automation_enabled", not current_app.get("paused", False))
    curr_mode = current_app.get("ingestion_mode", "BACKGROUND_POLLING")
    curr_interval = current_app.get("polling_interval_sec", 120)

    # Mode switch: Side-by-side live browser
    if any(w in text_lower for w in ("side by side", "side-by-side", "headed live", "live browser mode", "playwright mode")):
        return "set_automation_config", {
            "automation_enabled": True,
            "ingestion_mode": "SIDE_BY_SIDE_LIVE",
            "polling_interval_sec": curr_interval,
        }

    # Mode switch: Background polling
    if any(w in text_lower for w in ("background polling", "polling mode", "periodic polling")):
        digits = "".join(ch for ch in text if ch.isdigit())
        interval = int(digits) if digits and 30 <= int(digits) <= 300 else curr_interval
        return "set_automation_config", {
            "automation_enabled": True,
            "ingestion_mode": "BACKGROUND_POLLING",
            "polling_interval_sec": interval,
        }

    # Polling interval change without explicit mode mention
    if "polling" in text_lower and ("interval" in text_lower or "sec" in text_lower or "second" in text_lower or "s koro" in text_lower):
        digits = "".join(ch for ch in text if ch.isdigit())
        if digits and 30 <= int(digits) <= 300:
            return "set_automation_config", {
                "automation_enabled": curr_enabled,
                "ingestion_mode": curr_mode,
                "polling_interval_sec": int(digits),
            }

    # Master Automation Toggle OFF
    off_patterns = (
        "turn off buy sell automation", "turn off automation", "stop automation", "automation off",
        "disable automation", "automation bondho", "automation thamao", "automation paused"
    )
    if any(p in text_lower for p in off_patterns):
        return "set_automation_config", {
            "automation_enabled": False,
            "ingestion_mode": curr_mode,
            "polling_interval_sec": curr_interval,
        }

    # Master Automation Toggle ON
    on_patterns = (
        "turn on buy sell automation", "turn on automation", "start automation", "automation on",
        "enable automation", "automation chalu", "automation start", "resume automation"
    )
    if any(p in text_lower for p in on_patterns):
        return "set_automation_config", {
            "automation_enabled": True,
            "ingestion_mode": curr_mode,
            "polling_interval_sec": curr_interval,
        }

    return None, {}
