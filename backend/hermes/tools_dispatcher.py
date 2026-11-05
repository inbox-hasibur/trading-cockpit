"""Hermes Tool Dispatcher, Tool Handlers & Formatter Sub-module.

Decomposed from agent_loop.py to maintain modularity, low nesting depth (<= 3),
and clean architectural separation.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from backend.config import Settings
from backend.database import (
    CompanyProfile,
    CustomRule,
    PortfolioState,
    RuleAudit,
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
) -> dict[str, Any]:
    symbol = args["symbol"].upper()
    side = args.get("side", "BUY").upper()
    qty = int(args.get("quantity", 0))
    if side != "BUY":
        raise ValueError("Manual sell execution uses sequential profit-taking engine.")

    checkpoint_mgr.create_checkpoint(
        session, state, "MANUAL_BUY", f"Manual buy {qty} shares of {symbol}", symbol,
        diff_payload={
            "action": "MANUAL_BUY",
            "actor": "Operator via Hermes",
            "summary": f"Executed manual buy of {qty} shares for {symbol}",
            "before": {}, "after": {"symbol": symbol, "qty": qty},
            "diff_lines": [{"type": "add", "text": f"BUY {qty} shares of {symbol}"}],
        },
        actor="Operator",
    )
    res = execute_agentic_buy(session, state, settings, symbol, requested_qty=qty if qty > 0 else None)
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
        "xiaomi/mimo-v2-flash",
        "deepseek/deepseek-chat",
        "xiaomi/mimo-v2-pro",
        "google/gemini-2.5-flash",
        "anthropic/claude-3.5-haiku",
        "meta-llama/llama-3.3-70b-instruct",
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
        return handle_execute_manual_order(args, session, state, settings, checkpoint_mgr)
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
        return (
            f"DEMO/PAPER · [Manual Order Executed]\n"
            f"✅ {res['symbol']}-এর {res['quantity']} টি শেয়ার ৳{res['price']:,.2f} দরে কেনা হয়েছে "
            f"(মোট খরচ: ৳{res['cost']:,.2f}, বাকেট {res['bucket']})।"
        )

    if tool_name == "set_automation_config":
        return _fmt_automation_config(tool_res, bangla)

    if tool_name == "set_ai_model":
        return _fmt_ai_model(tool_res, bangla)

    return f"DEMO/PAPER · Tool {tool_name} executed successfully."


# ==============================================================================
# Intent Detection Logic
# ==============================================================================

def detect_intent_and_tool(message: str, snapshot: dict) -> tuple[str | None, dict[str, Any]]:
    """High-precision intent detector for Bangla, Banglish & English agent commands."""
    text = message.strip()
    text_lower = text.lower()

    # 0. Model command
    if text.startswith("/model") or text_lower.startswith("switch model") or text_lower.startswith("model change"):
        parts = text.split(maxsplit=1)
        target = parts[1].strip() if len(parts) > 1 else ""
        return "set_ai_model", {"model": target}

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
    }
    matched_sym = None
    for sym, aliases in symbol_aliases.items():
        if any(alias in text_lower for alias in aliases):
            matched_sym = sym
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
    buy_words = ("buy koro", "share kino", "explicitly buy", "kine dao", "buy now")
    if matched_sym and any(w in text_lower for w in buy_words):
        digits = "".join(ch for ch in text if ch.isdigit())
        qty = int(digits) if digits else 0
        return "execute_manual_order", {"symbol": matched_sym, "side": "BUY", "quantity": qty}

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
