"""Hermes OS Structured Toolsets for Humming Bird DSE Execution.

Wires Humming Bird quantitative intelligence & StockNow browser tools into
three structured Hermes OS toolsets with automatic CheckpointManager snapshots
prior to any state mutation:

1. stocknow_browser_toolset:
   - launch_browser
   - login_stocknow
   - sync_favorites_3_lists
   - sync_all_dse_shares
   - sync_portfolio_164580
   - execute_live_order (BUY/SELL with 0.5% brokerage commission)

2. quant_strategy_toolset:
   - inspect_curve_and_support
   - trigger_canary_90_10_quarantine
   - evaluate_canary_outcomes
   - restore_quarantine
   - set_watchlist_tier (GSC, GSC_L1, GSC_L2)
   - update_buy_allocation

3. memory_and_skill_toolset:
   - curate_memory_md
   - curate_user_md
   - session_search_fts5
   - create_or_patch_skill
   - rollback_checkpoint
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import Settings
from backend.database import (
    CanaryThesis,
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
    execute_agentic_sell,
    restore_quarantine as core_restore_quarantine,
)
from backend.engine.money import decimal, money, price
from backend.hermes.agent_loop import CheckpointManager
from backend.hermes.memory import HermesMemory
from backend.hermes.secret_guard import redact_secrets
from backend.hermes_os.memory_curator import MemoryCurator
from backend.hermes_os.skill_learner import SkillLearner

logger = logging.getLogger(__name__)


def _run_coroutine_sync(coro: Any) -> Any:
    """Safely runs an async coroutine synchronously from sync tool handlers."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result(timeout=45)
    return asyncio.run(coro)


@dataclass
class ToolContext:
    """Execution context injected into every tool handler."""
    session: Session
    state: PortfolioState
    settings: Settings
    stocknow_client: Any | None = None
    checkpoint_mgr: Any = CheckpointManager
    curator: MemoryCurator | None = None
    learner: SkillLearner | None = None


@dataclass
class ToolDefinition:
    """Metadata and execution handler for a Hermes OS tool."""
    name: str
    description: str
    toolset: str
    parameters: dict[str, Any]
    handler: Callable[[dict[str, Any], ToolContext], dict[str, Any]]


# ==============================================================================
# Toolset 1: StockNow Browser Toolset
# ==============================================================================

def tool_launch_browser(args: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
    mode = args.get("mode", "ONSCREEN_LIVE")
    from backend.adapters.stocknow_client import StockNowLiveClient
    client = ctx.stocknow_client or StockNowLiveClient(ingestion_mode=mode)
    res = _run_coroutine_sync(client.launch(mode=mode))
    return {"status": "SUCCESS", "tool": "launch_browser", "result": res}


def tool_login_stocknow(args: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
    phone = args.get("phone") or getattr(ctx.settings, "operator_phone", ctx.settings.operator_username)
    password = args.get("password") or ctx.settings.operator_password
    from backend.adapters.stocknow_client import StockNowLiveClient
    client = ctx.stocknow_client or StockNowLiveClient()
    res = _run_coroutine_sync(client.ensure_authenticated(phone, password))
    return {"status": "SUCCESS", "tool": "login_stocknow", "result": res}


def tool_sync_favorites_3_lists(args: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
    from backend.adapters.stocknow_market_sync import (
        extract_quotes_from_payload,
        extract_quotes_from_stocknow,
        sync_live_market_to_db,
    )
    injected = args.get("payload")
    if injected:
        quotes = extract_quotes_from_payload(injected)
    else:
        quotes = _run_coroutine_sync(extract_quotes_from_stocknow(ctx.stocknow_client))

    diff_lines = [
        {"type": "add", "text": f"Synced {len(quotes)} market quotes from 3 Favorite lists (GSC, L1, L2)."}
    ]
    ctx.checkpoint_mgr.create_checkpoint(
        ctx.session, ctx.state, "SYNC_FAVORITES",
        f"Synchronized 3 Favorite lists ({len(quotes)} quotes) with historical curves",
        diff_payload={"action": "SYNC_FAVORITES", "count": len(quotes), "diff_lines": diff_lines},
        actor="Hermes Market Sync",
    )
    sync_res = sync_live_market_to_db(ctx.session, quotes, session_date=ctx.state.clock_date)
    return {"status": "SUCCESS", "tool": "sync_favorites_3_lists", "quotes_count": len(quotes), "sync_result": sync_res}


def tool_sync_all_dse_shares(args: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
    from backend.adapters.stocknow_market_sync import get_or_fetch_all_dse_shares
    shares = _run_coroutine_sync(get_or_fetch_all_dse_shares(client=ctx.stocknow_client))
    return {"status": "SUCCESS", "tool": "sync_all_dse_shares", "total_dse_shares": len(shares), "shares": shares[:50]}


def tool_sync_portfolio_164580(args: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
    from backend.adapters.stocknow_portfolio_sync import (
        extract_hummingbird_portfolio,
        reconcile_portfolio_to_db,
    )
    injected = args.get("injected_portfolio") or args.get("portfolio")
    extracted = extract_hummingbird_portfolio(ctx.stocknow_client, injected_portfolio=injected)
    recon_res = reconcile_portfolio_to_db(ctx.session, ctx.settings, extracted, checkpoint_mgr=ctx.checkpoint_mgr)
    return {"status": "SUCCESS", "tool": "sync_portfolio_164580", "portfolio": extracted.get("portfolio_name"), "result": recon_res}


def tool_execute_live_order(args: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
    symbol = args["symbol"].upper()
    side = args.get("side", "BUY").upper()
    qty = int(args.get("quantity", 0))

    if side not in ("BUY", "SELL"):
        raise ValueError(f"Invalid order side: '{side}'. Must be BUY or SELL.")

    if side == "SELL" and qty <= 0:
        mature_lots = list(ctx.session.scalars(
            select(TaxLot).where(
                TaxLot.symbol == symbol,
                TaxLot.remaining_qty > 0,
                TaxLot.matures_on <= ctx.state.clock_date,
            )
        ))
        qty = sum(l.remaining_qty for l in mature_lots)
        if qty <= 0:
            raise ValueError(f"Zero mature shares available to sell for {symbol} on {ctx.state.clock_date.isoformat()}.")

    # Snapshot before order execution
    diff_lines = [
        {"type": "add", "text": f"Execute live virtual order: {side} {qty} {symbol} (0.5% commission)"}
    ]
    ctx.checkpoint_mgr.create_checkpoint(
        ctx.session, ctx.state, f"ORDER_{side}", f"Live virtual {side} order for {qty} {symbol}", symbol,
        diff_payload={"action": f"ORDER_{side}", "symbol": symbol, "side": side, "quantity": qty, "diff_lines": diff_lines},
        actor="Hermes Execution Engine",
    )

    if side == "BUY":
        order_res = execute_agentic_buy(ctx.session, ctx.state, ctx.settings, symbol, requested_qty=qty if qty > 0 else None)
    else:
        order_res = execute_agentic_sell(ctx.session, ctx.state, ctx.settings, symbol, requested_qty=qty)

    from backend.adapters.stocknow_order_executor import execute_stocknow_virtual_order
    is_live = ctx.stocknow_client is not None and getattr(ctx.stocknow_client, "state", "") == "READY"
    pid = getattr(ctx.stocknow_client, "bound_portfolio_id", "164580") if is_live else "164580"

    receipt = _run_coroutine_sync(execute_stocknow_virtual_order(
        client=ctx.stocknow_client if is_live else None,
        symbol=symbol,
        side=side,
        quantity=order_res["quantity"],
        price=order_res["price"],
        portfolio_id=pid,
        dry_run=not is_live,
    ))

    order_res["receipt"] = receipt
    return {"status": "SUCCESS", "tool": "execute_live_order", "symbol": symbol, "side": side, "result": order_res}


# ==============================================================================
# Toolset 2: Quantitative Strategy Toolset
# ==============================================================================

def tool_inspect_curve_and_support(args: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
    symbol = args["symbol"].upper()
    comp = ctx.session.get(CompanyProfile, symbol)
    if not comp:
        raise ValueError(f"Company {symbol} not found in database.")

    cur_price = float(comp.last_price)
    history = comp.price_history or []
    close_prices = []
    for h in history:
        if isinstance(h, dict) and "close" in h:
            try:
                close_prices.append(float(h["close"]))
            except Exception:
                pass

    if not close_prices:
        close_prices = [cur_price]

    support_floor = min(close_prices)
    resistance_ceiling = max(close_prices)

    # Multi-session drawdown calculation
    multisession_drawdown_pct = ((cur_price - resistance_ceiling) / resistance_ceiling * 100) if resistance_ceiling > 0 else 0.0

    # 1-day change calculation
    prev_close = close_prices[-2] if len(close_prices) >= 2 else cur_price
    change_1d_pct = ((cur_price - prev_close) / prev_close * 100) if prev_close > 0 else 0.0

    # Adhere strictly to Hermes Market Analysis & Support Guidelines:
    # 1. Distinguish multi-session drawdown from 1-day change:
    drawdown_desc = f"{abs(multisession_drawdown_pct):.2f}% drop over {len(close_prices)} sessions (1-day: {change_1d_pct:+.2f}%)"

    # 2. Compare price to support:
    rel_diff = (cur_price - support_floor) / support_floor if support_floor > 0 else 0.0
    if cur_price < support_floor:
        support_status = f"below support (৳{support_floor:,.2f})"
    elif abs(rel_diff) <= 0.002:
        support_status = f"at support (৳{support_floor:,.2f})"
    elif 0 < rel_diff <= 0.01:
        support_status = f"near support (৳{support_floor:,.2f})"
    else:
        support_status = f"above support (৳{support_floor:,.2f})"

    return {
        "status": "SUCCESS",
        "tool": "inspect_curve_and_support",
        "symbol": symbol,
        "current_price": cur_price,
        "support_floor": support_floor,
        "resistance_ceiling": resistance_ceiling,
        "support_status": support_status,
        "drawdown_description": drawdown_desc,
        "multisession_drawdown_pct": round(multisession_drawdown_pct, 2),
        "change_1d_pct": round(change_1d_pct, 2),
        "session_count": len(close_prices),
    }


def tool_trigger_canary_90_10_quarantine(args: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
    symbol = args["symbol"].upper()
    thesis = args.get("thesis", "Operator threat alert or critical breakdown")

    diff_lines = [
        {"type": "del", "text": f"{symbol} quarantined: False"},
        {"type": "add", "text": f"{symbol} quarantined: True (CRASH_QUARANTINE) | 90% profit-lock + 10% canary probe retained"},
    ]
    ctx.checkpoint_mgr.create_checkpoint(
        ctx.session, ctx.state, "CANARY_QUARANTINE",
        f"Quarantine {symbol} with 90% profit-lock & 10% canary probe: {thesis}", symbol,
        diff_payload={"action": "CANARY_QUARANTINE", "symbol": symbol, "thesis": thesis, "diff_lines": diff_lines},
        actor="Hermes Risk Co-Pilot",
    )

    res = emergency_quarantine_and_canary(ctx.session, ctx.state, ctx.settings, symbol, thesis)
    mem = HermesMemory(ctx.session)
    mem.record_fact(symbol, f"Operator threat alert: {thesis}. 90% profit locked, 10% canary probe active.", "CANARY_PROBE", "HIGH")
    if ctx.curator:
        ctx.curator.patch_memory(f"[{ctx.state.clock_date.isoformat()}] {symbol}: Quarantined with 10% canary probe ({thesis})")

    return {"status": "SUCCESS", "tool": "trigger_canary_90_10_quarantine", "result": res}


def tool_evaluate_canary_outcomes(args: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
    symbol_filter = args.get("symbol", "").upper().strip() or None
    updates = check_canary_theses(ctx.session, ctx.state)
    if symbol_filter:
        updates = [u for u in updates if u.get("symbol") == symbol_filter]

    # Closed learning loop on canary outcomes
    learner = ctx.learner or SkillLearner()
    for u in updates:
        sym = u["symbol"]
        status = u["status"]
        lesson_log = [
            f"Observation: {sym} canary status shifted to {status}",
            f"Message: {u['message']}",
            f"Outcome: 90% liquidation preserved capital, 10% probe captured resolution without catastrophic risk",
        ]
        learner.learn_from_execution(
            task_name="Canary 90-10 Defense",
            task_description="Resolving insolvency threats by locking 90% profit and retaining a 10% canary probe",
            execution_log=lesson_log,
            outcome=f"{sym} probe concluded with status {status}",
            session=ctx.session,
        )

    return {"status": "SUCCESS", "tool": "evaluate_canary_outcomes", "evaluated_count": len(updates), "updates": updates}


def tool_restore_quarantine(args: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
    symbol = args["symbol"].upper()
    reason = args.get("reason", "Operator instructed restoration")

    diff_lines = [
        {"type": "del", "text": f"{symbol} quarantined: True"},
        {"type": "add", "text": f"{symbol} quarantined: False | Restored to active trading"},
    ]
    ctx.checkpoint_mgr.create_checkpoint(
        ctx.session, ctx.state, "RESTORE_QUARANTINE", f"Restore {symbol} from quarantine", symbol,
        diff_payload={"action": "RESTORE_QUARANTINE", "symbol": symbol, "reason": reason, "diff_lines": diff_lines},
        actor="Hermes Agent",
    )

    res = core_restore_quarantine(ctx.session, ctx.state, symbol, reason)
    mem = HermesMemory(ctx.session)
    mem.record_fact(symbol, f"Restored from quarantine: {reason}", "STATUS", "HIGH")
    if ctx.curator:
        ctx.curator.patch_memory(f"[{ctx.state.clock_date.isoformat()}] {symbol}: Restored from quarantine ({reason})")

    return {"status": "SUCCESS", "tool": "restore_quarantine", "symbol": symbol, "result": res}


def tool_set_watchlist_tier(args: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
    symbol = args["symbol"].upper()
    tier = args["tier"].upper().strip()
    if tier not in {"GSC", "GSC_L1", "GSC_L2"}:
        raise ValueError(f"Watchlist tier must be GSC, GSC_L1, or GSC_L2, got '{tier}'.")

    comp = ctx.session.get(CompanyProfile, symbol)
    if not comp:
        raise ValueError(f"Company {symbol} not found.")

    old_tier = getattr(comp, "watchlist_category", "GSC")
    diff_lines = [
        {"type": "del", "text": f"{symbol} watchlist_category: {old_tier}"},
        {"type": "add", "text": f"{symbol} watchlist_category: {tier}"},
    ]
    ctx.checkpoint_mgr.create_checkpoint(
        ctx.session, ctx.state, "SET_WATCHLIST_TIER", f"Move {symbol} to {tier}", symbol,
        diff_payload={"action": "SET_WATCHLIST_TIER", "symbol": symbol, "before": old_tier, "after": tier, "diff_lines": diff_lines},
        actor="Hermes Agent",
    )

    comp.watchlist_category = tier
    ctx.state.rules_revision += 1
    ctx.session.flush()

    mem = HermesMemory(ctx.session)
    mem.record_fact(symbol, f"Moved to watchlist tier {tier}", "WATCHLIST_CATEGORY", "HIGH")
    return {"status": "SUCCESS", "tool": "set_watchlist_tier", "symbol": symbol, "tier": tier, "old_tier": old_tier}


def tool_update_buy_allocation(args: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
    symbol = args["symbol"].upper()
    pct = decimal(str(args["buy_allocation_pct"]))
    enabled = bool(args.get("enabled", True))

    rule = ctx.session.get(CustomRule, symbol)
    if not rule:
        rule = CustomRule(symbol=symbol, buy_allocation_pct=pct, enabled=enabled)
        ctx.session.add(rule)
        old_alloc = "0"
    else:
        old_alloc = str(rule.buy_allocation_pct)

    diff_lines = [
        {"type": "del", "text": f"{symbol} buy_allocation_pct: {old_alloc}% | enabled: {getattr(rule, 'enabled', True)}"},
        {"type": "add", "text": f"{symbol} buy_allocation_pct: {pct}% | enabled: {enabled}"},
    ]
    ctx.checkpoint_mgr.create_checkpoint(
        ctx.session, ctx.state, "UPDATE_ALLOCATION", f"Set {symbol} allocation to {pct}%", symbol,
        diff_payload={"action": "UPDATE_ALLOCATION", "symbol": symbol, "before": old_alloc, "after": str(pct), "diff_lines": diff_lines},
        actor="Hermes Agent",
    )

    before = {"buy_allocation_pct": float(old_alloc), "enabled": rule.enabled}
    rule.buy_allocation_pct = pct
    rule.enabled = enabled
    after = {"buy_allocation_pct": float(pct), "enabled": enabled}

    ctx.session.add(RuleAudit(symbol=symbol, before=before, after=after, session_on=ctx.state.clock_date))
    ctx.state.rules_revision += 1
    ctx.session.flush()

    return {"status": "SUCCESS", "tool": "update_buy_allocation", "symbol": symbol, "after": after}


# ==============================================================================
# Toolset 3: Memory and Skill Toolset
# ==============================================================================

def tool_curate_memory_md(args: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
    note = args["note"].strip()
    section = args.get("section", "Distilled Market Notes & Theses")
    curator = ctx.curator or MemoryCurator()
    updated = curator.patch_memory(note, section=section)
    return {"status": "SUCCESS", "tool": "curate_memory_md", "memory_updated": updated, "note": note}


def tool_curate_user_md(args: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
    directive = args["directive"].strip()
    section = args.get("section", "Learned Preferences")
    curator = ctx.curator or MemoryCurator()
    updated = curator.patch_user_profile(directive, section=section)
    return {"status": "SUCCESS", "tool": "curate_user_md", "user_updated": updated, "directive": directive}


def tool_session_search_fts5(args: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
    query = args["query"].strip()
    limit = int(args.get("limit", 5))
    curator = ctx.curator or MemoryCurator()
    hits = curator.session_search(query, limit=limit)
    return {"status": "SUCCESS", "tool": "session_search_fts5", "query": query, "hits_count": len(hits), "hits": hits}


def tool_create_or_patch_skill(args: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
    name = args["name"].strip()
    desc = args.get("description", f"{name} execution methodology").strip()
    triggers = args.get("triggers", [name.lower()])
    content = args["content"].strip()
    pitfalls = args.get("pitfalls", [])
    steps = args.get("steps", [])

    diff_lines = [
        {"type": "add", "text": f"Closed learning loop compiled skill '{name}'"}
    ]
    ctx.checkpoint_mgr.create_checkpoint(
        ctx.session, ctx.state, "LEARN_SKILL", f"Compiled/patched procedural skill {name}",
        diff_payload={"action": "LEARN_SKILL", "skill": name, "diff_lines": diff_lines},
        actor="Hermes Closed Learning Loop",
    )

    learner = ctx.learner or SkillLearner()
    skill = learner.create_or_patch_skill(
        name=name,
        description=desc,
        triggers=triggers,
        content=content,
        pitfalls=pitfalls,
        steps=steps,
        session=ctx.session,
    )
    return {
        "status": "SUCCESS",
        "tool": "create_or_patch_skill",
        "name": skill.name,
        "version": skill.version,
        "file": skill.filename,
    }


def tool_rollback_checkpoint(args: dict[str, Any], ctx: ToolContext) -> dict[str, Any]:
    steps_back = int(args.get("steps_back", 1))
    results = []
    for _ in range(max(1, steps_back)):
        try:
            rb_res = ctx.checkpoint_mgr.rollback_last(ctx.session, ctx.state)
            results.append(rb_res)
        except ValueError as val_err:
            if not results:
                raise val_err
            break

    return {"status": "SUCCESS", "tool": "rollback_checkpoint", "reverted_count": len(results), "rollbacks": results}


# ==============================================================================
# Central Tool Registry
# ==============================================================================

class HermesToolRegistry:
    """Central registry and dispatcher for all Humming Bird DSE toolsets."""

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._register_defaults()

    def register(self, tool_def: ToolDefinition) -> None:
        self._tools[tool_def.name] = tool_def

    def _register_defaults(self) -> None:
        # StockNow Browser Toolset
        self.register(ToolDefinition(
            name="launch_browser",
            description="Launches visible StockNow Chromium browser via Playwright CDP worker thread.",
            toolset="stocknow_browser_toolset",
            parameters={"type": "object", "properties": {"mode": {"type": "string", "enum": ["ONSCREEN_LIVE", "BACKGROUND_POLLING"]}}},
            handler=tool_launch_browser,
        ))
        self.register(ToolDefinition(
            name="login_stocknow",
            description="Ensures operator authentication on StockNow using persistent session cookies or auto-login credentials.",
            toolset="stocknow_browser_toolset",
            parameters={"type": "object", "properties": {"phone": {"type": "string"}, "password": {"type": "string"}}},
            handler=tool_login_stocknow,
        ))
        self.register(ToolDefinition(
            name="sync_favorites_3_lists",
            description="Synchronizes live prices, changes, and historical multi-session curves from the 3 StockNow Favorite lists (GSC, L1, L2).",
            toolset="stocknow_browser_toolset",
            parameters={"type": "object", "properties": {"payload": {"type": "object"}}},
            handler=tool_sync_favorites_3_lists,
        ))
        self.register(ToolDefinition(
            name="sync_all_dse_shares",
            description="Scrapes and synchronizes the entire DSE market board into local memory and cache.",
            toolset="stocknow_browser_toolset",
            parameters={"type": "object", "properties": {"payload": {"type": "object"}}},
            handler=tool_sync_all_dse_shares,
        ))
        self.register(ToolDefinition(
            name="sync_portfolio_164580",
            description="Scrapes virtual portfolio #164580 ('Humming Bird'), reconciles cash and T+2 lots, with automatic rollback checkpoint snapshot.",
            toolset="stocknow_browser_toolset",
            parameters={"type": "object", "properties": {"injected_portfolio": {"type": "object"}}},
            handler=tool_sync_portfolio_164580,
        ))
        self.register(ToolDefinition(
            name="execute_live_order",
            description="Executes a virtual BUY or SELL order on StockNow with 0.5% brokerage commission calculation and rollback checkpoint.",
            toolset="stocknow_browser_toolset",
            parameters={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "side": {"type": "string", "enum": ["BUY", "SELL"]},
                    "quantity": {"type": "integer"},
                    "price": {"type": "number"},
                },
                "required": ["symbol", "side", "quantity"],
            },
            handler=tool_execute_live_order,
        ))

        # Quantitative Strategy Toolset
        self.register(ToolDefinition(
            name="inspect_curve_and_support",
            description="Inspects multi-session drawdown, support floor, and resistance ceiling, distinguishing multi-session drops from 1-day changes.",
            toolset="quant_strategy_toolset",
            parameters={"type": "object", "properties": {"symbol": {"type": "string"}}, "required": ["symbol"]},
            handler=tool_inspect_curve_and_support,
        ))
        self.register(ToolDefinition(
            name="trigger_canary_90_10_quarantine",
            description="Locks in 90% profit and retains a 10% canary probe lot to protect capital upon bankruptcy or danger thesis.",
            toolset="quant_strategy_toolset",
            parameters={"type": "object", "properties": {"symbol": {"type": "string"}, "thesis": {"type": "string"}}, "required": ["symbol"]},
            handler=tool_trigger_canary_90_10_quarantine,
        ))
        self.register(ToolDefinition(
            name="evaluate_canary_outcomes",
            description="Monitors performance of active 10% canary probes and invokes closed learning loop on confirmation or invalidation.",
            toolset="quant_strategy_toolset",
            parameters={"type": "object", "properties": {"symbol": {"type": "string"}}},
            handler=tool_evaluate_canary_outcomes,
        ))
        self.register(ToolDefinition(
            name="restore_quarantine",
            description="Restores a quarantined company back to the active trading watchlist with a state rollback checkpoint.",
            toolset="quant_strategy_toolset",
            parameters={"type": "object", "properties": {"symbol": {"type": "string"}, "reason": {"type": "string"}}, "required": ["symbol"]},
            handler=tool_restore_quarantine,
        ))
        self.register(ToolDefinition(
            name="set_watchlist_tier",
            description="Moves a stock between GSC (Big Giant Stable), GSC_L1 (Comeback Trend), and GSC_L2 (Swing Scalp) with rollback checkpoint.",
            toolset="quant_strategy_toolset",
            parameters={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "tier": {"type": "string", "enum": ["GSC", "GSC_L1", "GSC_L2"]},
                },
                "required": ["symbol", "tier"],
            },
            handler=tool_set_watchlist_tier,
        ))
        self.register(ToolDefinition(
            name="update_buy_allocation",
            description="Updates custom buy allocation cap for a stock with rollback checkpoint and audit logging.",
            toolset="quant_strategy_toolset",
            parameters={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "buy_allocation_pct": {"type": "number"},
                    "enabled": {"type": "boolean"},
                },
                "required": ["symbol", "buy_allocation_pct"],
            },
            handler=tool_update_buy_allocation,
        ))

        # Memory and Skill Toolset
        self.register(ToolDefinition(
            name="curate_memory_md",
            description="Appends a new market thesis or verified trading observation to MEMORY.md scratchpad.",
            toolset="memory_and_skill_toolset",
            parameters={"type": "object", "properties": {"note": {"type": "string"}, "section": {"type": "string"}}, "required": ["note"]},
            handler=tool_curate_memory_md,
        ))
        self.register(ToolDefinition(
            name="curate_user_md",
            description="Appends a new operator preference or trading directive to USER.md profile.",
            toolset="memory_and_skill_toolset",
            parameters={"type": "object", "properties": {"directive": {"type": "string"}, "section": {"type": "string"}}, "required": ["directive"]},
            handler=tool_curate_user_md,
        ))
        self.register(ToolDefinition(
            name="session_search_fts5",
            description="Performs lightning-fast SQLite FTS5 BM25 search across past conversation transcripts.",
            toolset="memory_and_skill_toolset",
            parameters={"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["query"]},
            handler=tool_session_search_fts5,
        ))
        self.register(ToolDefinition(
            name="create_or_patch_skill",
            description="Synthesizes or evolves a procedural SKILL_<name>.md with YAML frontmatter, pitfalls, and execution steps.",
            toolset="memory_and_skill_toolset",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "triggers": {"type": "array", "items": {"type": "string"}},
                    "content": {"type": "string"},
                    "pitfalls": {"type": "array", "items": {"type": "string"}},
                    "steps": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name", "content"],
            },
            handler=tool_create_or_patch_skill,
        ))
        self.register(ToolDefinition(
            name="rollback_checkpoint",
            description="Reverts database state to the last saved CheckpointManager snapshot (/rollback).",
            toolset="memory_and_skill_toolset",
            parameters={"type": "object", "properties": {"steps_back": {"type": "integer"}}},
            handler=tool_rollback_checkpoint,
        ))

    def execute(self, tool_name: str, args: dict[str, Any], context: ToolContext) -> dict[str, Any]:
        """Routes and executes a registered tool within the provided ToolContext."""
        tool_def = self._tools.get(tool_name)
        if not tool_def:
            raise ValueError(f"Tool '{tool_name}' is not registered in Hermes OS toolsets.")
        return tool_def.handler(args, context)

    def get_toolset(self, toolset_name: str) -> list[ToolDefinition]:
        return [t for t in self._tools.values() if t.toolset == toolset_name]

    def list_tools(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def export_schemas(self, toolset_name: str | None = None) -> list[dict[str, Any]]:
        """Exports tools as OpenAI/OpenRouter function declaration dictionaries."""
        tools = self.get_toolset(toolset_name) if toolset_name else self.list_tools()
        schemas = []
        for t in tools:
            schemas.append({
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            })
        return schemas


# Global singleton registry
default_registry = HermesToolRegistry()
