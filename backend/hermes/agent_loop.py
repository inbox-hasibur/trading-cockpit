"""Hermes Agent Loop, Toolset Orchestration & State Checkpoints.

Implements the Nous Research-style agent turn loop:
System Prompt + Layer 1 Profile + Matched Skills + Layer 3 Facts ->
Agent Tool Execution -> State Checkpointing -> Automatic Context Compression ->
Re-injection & Response.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import DHAKA, Settings
from backend.database import (
    CanaryThesis,
    ChatBudget,
    CompanyProfile,
    CustomRule,
    Database,
    HermesSkillRevision,
    HermesStateCheckpoint,
    PortfolioState,
    RuleAudit,
    TaxLot,
    TradeLog,
    portfolio_state,
)
from backend.engine.agent_actions import (
    check_canary_theses,
    emergency_quarantine_and_canary,
    execute_agentic_buy,
    restore_quarantine,
)
from backend.engine.money import ZERO, decimal, money, price, purchase_amount, sale_amount
from backend.engine.t2_ledger import TradingCalendar, assert_ledger, bucket_balances
from backend.hermes.memory import HermesMemory
from backend.hermes.secret_guard import SecretGuard, redact_secrets
from backend.hermes.skills_manager import SkillsManager
from backend.portfolio import build_snapshot

logger = logging.getLogger(__name__)
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

BASE_AGENT_PROMPT = """You are Hermes, an autonomous, self-improving Agentic Share Assistant and Portfolio Co-Pilot for the Bangladesh Stock Market (DSE).
You manage portfolio execution on StockNow virtual portfolio ("Humming Bird") with strict discipline, human-like curve intelligence, and zero emotional panic.
All current quotes and ledger lots are in SYNTHETIC DEMO mode.

Core Capabilities:
1. Procedural Memory: You follow and self-improve versioned markdown skills (SKILL_*.md).
2. Three-Layer Memory: You recall operator directives (Layer 1), past conversation sessions (Layer 2), and durable company facts (Layer 3).
3. Risk & Quarantine: On user threats/insolvency alerts, you immediately quarantine the stock, lock in 90% profit if in profit, and retain a 10% canary probe to verify the thesis over subsequent sessions.
4. Checkpoints & Rollback: Before any state mutation, a snapshot checkpoint is saved. The operator can command `/rollback` at any time to undo the last mutation.
5. Watchlist Categories: You classify and move stocks between GSC (Big Giant Stable), GSC_L1 (Comeback Trend), and GSC_L2 (Swing Momentum Scalp).
Respond in the operator's language (Bangla, Banglish, or English), clearly, concisely, and action-oriented.
"""


class CheckpointManager:
    @staticmethod
    def create_checkpoint(session: Session, state: PortfolioState, action: str, description: str, symbol: str | None = None) -> HermesStateCheckpoint:
        payload: dict[str, Any] = {
            "action": action,
            "description": description,
            "date": state.clock_date.isoformat(),
            "rules_revision": state.rules_revision,
            "companies": {},
            "rules": {},
        }
        symbols_to_save = [symbol.upper()] if symbol else [c.symbol for c in session.scalars(select(CompanyProfile))]
        for sym in symbols_to_save:
            comp = session.get(CompanyProfile, sym)
            rule = session.get(CustomRule, sym)
            if comp:
                payload["companies"][sym] = {
                    "quarantined": comp.quarantined,
                    "quarantine_reason": comp.quarantine_reason,
                    "watchlist_category": getattr(comp, "watchlist_category", "GSC"),
                    "last_price": str(comp.last_price),
                }
            if rule:
                payload["rules"][sym] = {
                    "buy_allocation_pct": str(rule.buy_allocation_pct),
                    "enabled": rule.enabled,
                }

        cp = HermesStateCheckpoint(
            id=str(uuid4()),
            action=action,
            description=description,
            snapshot_payload=payload,
            session_on=state.clock_date,
            reverted=False,
        )
        session.add(cp)
        session.flush()
        return cp

    @staticmethod
    def rollback_last(session: Session, state: PortfolioState) -> dict[str, Any]:
        cp = session.scalar(
            select(HermesStateCheckpoint)
            .where(HermesStateCheckpoint.reverted == False)
            .order_by(HermesStateCheckpoint.id.desc())
            .limit(1)
        )
        if not cp:
            raise ValueError("No active checkpoint available to rollback.")

        payload = cp.snapshot_payload
        restored_symbols = []
        for sym, data in payload.get("companies", {}).items():
            comp = session.get(CompanyProfile, sym)
            if comp:
                comp.quarantined = data["quarantined"]
                comp.quarantine_reason = data["quarantine_reason"]
                comp.watchlist_category = data.get("watchlist_category", "GSC")
                restored_symbols.append(sym)

        for sym, rdata in payload.get("rules", {}).items():
            rule = session.get(CustomRule, sym)
            if rule:
                rule.buy_allocation_pct = decimal(rdata["buy_allocation_pct"])
                rule.enabled = rdata["enabled"]

        cp.reverted = True
        state.rules_revision += 1
        session.flush()
        return {
            "checkpoint_id": cp.id,
            "action_reverted": cp.action,
            "description": cp.description,
            "restored_symbols": restored_symbols,
        }


class HermesAgentLoop:
    def __init__(self, database: Database, settings: Settings):
        self.database = database
        self.settings = settings
        self.skills_mgr = SkillsManager()
        self.transport: httpx.AsyncBaseTransport | None = None

    def execute_tool(self, tool_name: str, args: dict[str, Any], session: Session, state: PortfolioState) -> dict[str, Any]:
        """Deterministic execution of Hermes Agent tools with automatic checkpointing."""
        memory = HermesMemory(session)
        calendar = TradingCalendar(self.settings.holidays, self.settings.bucket_anchor)

        if tool_name == "report_company_threat":
            symbol = args["symbol"].upper()
            thesis = args["thesis"]
            CheckpointManager.create_checkpoint(
                session, state, "REPORT_THREAT", f"Threat quarantine & 90/10 canary probe for {symbol}: {thesis}", symbol
            )
            result = emergency_quarantine_and_canary(session, state, self.settings, symbol, thesis)
            memory.record_fact(symbol, f"Operator threat alert: {thesis}. 90% profit locked, 10% canary retained.", "CANARY_PROBE", "HIGH")
            return {"status": "SUCCESS", "tool": tool_name, "result": result}

        elif tool_name == "restore_quarantined_company":
            symbol = args["symbol"].upper()
            reason = args.get("reason", "Operator instructed restoration")
            CheckpointManager.create_checkpoint(session, state, "RESTORE_QUARANTINE", f"Restore {symbol} from quarantine", symbol)
            result = restore_quarantine(session, state, symbol, reason)
            memory.record_fact(symbol, f"Restored from quarantine: {reason}", "STATUS", "HIGH")
            return {"status": "SUCCESS", "tool": tool_name, "result": result}

        elif tool_name == "set_watchlist_tier":
            symbol = args["symbol"].upper()
            tier = args["tier"].upper()
            if tier not in {"GSC", "GSC_L1", "GSC_L2"}:
                raise ValueError("Watchlist tier must be GSC, GSC_L1, or GSC_L2.")
            comp = session.get(CompanyProfile, symbol)
            if not comp:
                raise ValueError(f"Company {symbol} not found.")
            CheckpointManager.create_checkpoint(session, state, "SET_WATCHLIST_TIER", f"Move {symbol} to {tier}", symbol)
            comp.watchlist_category = tier
            state.rules_revision += 1
            session.flush()
            memory.record_fact(symbol, f"Classified into tier {tier}", "WATCHLIST_CATEGORY", "HIGH")
            return {"status": "SUCCESS", "tool": tool_name, "symbol": symbol, "tier": tier}

        elif tool_name == "update_company_allocation":
            symbol = args["symbol"].upper()
            pct = decimal(args["buy_allocation_pct"])
            enabled = bool(args.get("enabled", True))
            rule = session.get(CustomRule, symbol)
            if not rule:
                raise ValueError(f"Rule for {symbol} not found.")
            CheckpointManager.create_checkpoint(session, state, "UPDATE_ALLOCATION", f"Set {symbol} allocation to {pct}%", symbol)
            before = {"buy_allocation_pct": float(rule.buy_allocation_pct), "enabled": rule.enabled}
            rule.buy_allocation_pct = pct
            rule.enabled = enabled
            after = {"buy_allocation_pct": float(rule.buy_allocation_pct), "enabled": rule.enabled}
            session.add(RuleAudit(symbol=symbol, before=before, after=after, session_on=state.clock_date))
            state.rules_revision += 1
            session.flush()
            return {"status": "SUCCESS", "tool": tool_name, "symbol": symbol, "after": after}

        elif tool_name == "execute_manual_order":
            symbol = args["symbol"].upper()
            side = args.get("side", "BUY").upper()
            qty = int(args.get("quantity", 0))
            if side == "BUY":
                CheckpointManager.create_checkpoint(session, state, "MANUAL_BUY", f"Manual buy {qty} shares of {symbol}", symbol)
                res = execute_agentic_buy(session, state, self.settings, symbol, requested_qty=qty if qty > 0 else None)
                return {"status": "SUCCESS", "tool": tool_name, "result": res}
            else:
                raise ValueError("Manual sell execution uses sequential profit-taking engine.")

        elif tool_name == "learn_or_patch_skill":
            skill_name = args["skill_name"]
            lesson_md = args["lesson_markdown"]
            reason = args.get("reason", "Autonomous learning from market event")
            res = self.skills_mgr.learn_or_patch_skill(skill_name, lesson_md, reason, session, state.clock_date)
            return {"status": "SUCCESS", "tool": tool_name, "result": res}

        elif tool_name == "rollback_last_checkpoint":
            res = CheckpointManager.rollback_last(session, state)
            return {"status": "SUCCESS", "tool": tool_name, "result": res}

        elif tool_name == "evaluate_canary_theses":
            updates = check_canary_theses(session, state)
            for u in updates:
                # If a canary thesis confirmed, auto-patch the canary skill!
                lesson = (
                    f"### Case Observation ({state.clock_date.isoformat()}): {u['symbol']}\n"
                    f"- Status: {u['status']}\n"
                    f"- Outcome: {u['message']}\n"
                    f"- Proven rule: 90% liquidation preserved capital while 10% canary captured resolution without catastrophic loss.\n"
                )
                self.skills_mgr.learn_or_patch_skill(
                    "canary_90_10", lesson, f"Auto-learned from {u['symbol']} canary outcome ({u['status']})", session, state.clock_date
                )
            return {"status": "SUCCESS", "tool": tool_name, "updates": updates}

        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def compress_history(self, history: list[dict[str, str]], max_turns: int = 6) -> list[dict[str, str]]:
        """Summarizes older conversation turns to keep context window compact & lightweight."""
        if len(history) <= max_turns:
            return history
        older = history[:-max_turns]
        recent = history[-max_turns:]
        summary_points = []
        for turn in older:
            role = turn["role"].capitalize()
            snippet = turn["content"][:80].replace("\n", " ")
            summary_points.append(f"{role}: {snippet}...")
        compressed_brief = f"[Earlier context compressed: {len(older)} turns]\n" + "\n".join(summary_points)
        return [{"role": "assistant", "content": compressed_brief}] + recent

    def detect_intent_and_tool(self, message: str, snapshot: dict) -> tuple[str | None, dict[str, Any]]:
        """High-precision intent detector for Bangla, Banglish & English agent commands."""
        text = message.strip()
        text_lower = text.lower()

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

        return None, {}

    async def run_turn(self, user_message: str, history: list[dict[str, str]]) -> dict[str, Any]:
        """Main turn loop: Layered Memory + Skills Injection + Tool Execution + Context Scrubbing."""
        # Clean user input
        safe_message = redact_secrets(user_message.strip())

        # Load portfolio snapshot
        snapshot = build_snapshot(self.database, self.settings)

        # Detect tool call intent
        tool_name, tool_args = self.detect_intent_and_tool(safe_message, snapshot)
        tool_result = None

        with self.database.write() as session:
            state = portfolio_state(session)
            memory = HermesMemory(session)

            # Record user turn in Layer 2 memory
            memory.record_turn(
                session_date=state.clock_date,
                role="user",
                content=safe_message,
                symbol_mentioned=tool_args.get("symbol"),
            )

            # Execute tool if detected
            if tool_name:
                try:
                    tool_result = self.execute_tool(tool_name, tool_args, session, state)
                    memory.record_turn(
                        session_date=state.clock_date,
                        role="assistant",
                        content=f"Executed tool: {tool_name} with result {tool_result}",
                        symbol_mentioned=tool_args.get("symbol"),
                        action_taken=tool_name,
                    )
                except Exception as exc:
                    tool_result = {"status": "ERROR", "error": str(exc), "tool": tool_name}

        # If tool executed, format a dedicated response
        if tool_result:
            updated_snapshot = build_snapshot(self.database, self.settings)
            reply = self._format_tool_response(tool_name, tool_result, safe_message, updated_snapshot)
            action_map = {
                "report_company_threat": "EMERGENCY_QUARANTINE",
                "restore_quarantined_company": "RESTORE_QUARANTINE",
                "rollback_last_checkpoint": "ROLLBACK",
                "set_watchlist_tier": "SET_WATCHLIST_TIER",
                "learn_or_patch_skill": "LEARN_SKILL",
                "execute_manual_order": "MANUAL_ORDER",
                "update_company_allocation": "UPDATE_ALLOCATION",
            }
            return {
                "reply": reply,
                "provider": "local",
                "model": "hermes-agentic",
                "tool_executed": tool_name,
                "agentic_action": action_map.get(tool_name, tool_name.upper()),
                "tool_result": tool_result,
                "context_date": updated_snapshot["app"]["date"],
                "context_revision": updated_snapshot["app"]["revision"],
                "read_only": False,
            }

        # Otherwise: Assemble full layered prompt for conversational response
        return await self._conversational_inference(safe_message, history, snapshot)

    def _format_tool_response(self, tool_name: str, tool_res: dict[str, Any], user_msg: str, snapshot: dict) -> str:
        bangla = any("\u0980" <= char <= "\u09ff" for char in user_msg) or any(w in user_msg.lower() for w in ("koro", "deulia", "khoti"))

        if tool_name == "rollback_last_checkpoint":
            if tool_res["status"] == "SUCCESS":
                res = tool_res["result"]
                return (
                    f"DEMO/PAPER · [Hermes Agentic Rollback ↺]\n"
                    f"✅ পূর্ববর্তী স্টেট চেকপয়েন্ট সফলভাবে রোলব্যাক করা হয়েছে!\n"
                    f"- রিভার্ট করা অ্যাকশন: {res['action_reverted']}\n"
                    f"- বিবরণ: {res['description']}\n"
                    f"- পুনঃস্থাপিত কোম্পানি: {', '.join(res['restored_symbols']) if res['restored_symbols'] else 'N/A'}\n"
                    f"পোর্টফোলিও পূর্বের স্থিতিশীল অবস্থায় ফিরে গেছে।"
                    if bangla else
                    f"DEMO/PAPER · [Hermes Rollback ↺]\n"
                    f"Successfully restored previous state checkpoint:\n"
                    f"- Reverted: {res['action_reverted']} ({res['description']})\n"
                    f"- Restored: {', '.join(res['restored_symbols']) if res['restored_symbols'] else 'N/A'}."
                )
            else:
                return f"DEMO/PAPER · Rollback failed: {tool_res.get('error')}"

        if tool_name == "report_company_threat":
            if tool_res["status"] == "SUCCESS":
                res = tool_res["result"]
                sym = res["symbol"]
                sold_qty = res["sold_qty"]
                pnl = res["realized_pnl"]
                canary_qty = res["canary_qty"]
                if sold_qty > 0:
                    profit_note = f"পূর্বের অর্জিত লাভ ঘরে তুলতে {sold_qty} টি শেয়ার বিক্রি করে ৳{pnl:,.2f} নিট লাভ লক করা হয়েছে!"
                else:
                    profit_note = "কঠোর নো-লস নিয়মে লোকসানে বিক্রি করা হয়নি।"

                return (
                    f"DEMO/PAPER · [Hermes Agentic Intervention & Checkpoint Saved]\n"
                    f"🚨 {sym}-এর ওপর এমার্জেন্সি অ্যাকশন সম্পন্ন হয়েছে:\n"
                    f"১. {sym}-কে অবিলম্বে CRASH_QUARANTINE-এ নেওয়া হয়েছে (নতুন কেনা সম্পূর্ণ বন্ধ)।\n"
                    f"২. মুনাফা রক্ষা (৯০% প্রস্থান): {profit_note}\n"
                    f"৩. ক্যানারি প্রোব (১০%): আপনার থিসিস সত্যি কিনা তা যাচাই করার জন্য {canary_qty} টি শেয়ার পর্যবেক্ষণে রাখা হয়েছে।\n"
                    f"৪. স্টেট চেকপয়েন্ট সেভ করা হয়েছে (প্রয়োজনে আপনি `/rollback` দিয়ে এটি আনডু করতে পারবেন)।"
                    if bangla else
                    f"DEMO/PAPER · [Hermes Agentic Intervention & Checkpoint Saved]\n"
                    f"Action executed on {sym}:\n"
                    f"1. Placed in CRASH_QUARANTINE.\n"
                    f"2. Profit-lock: Sold {sold_qty} shares (৳{pnl:,.2f} gain).\n"
                    f"3. Retained {canary_qty} canary shares (10%) for thesis verification.\n"
                    f"4. State checkpoint created. You can type `/rollback` to undo."
                )

        if tool_name == "set_watchlist_tier":
            sym = tool_res["symbol"]
            tier = tool_res["tier"]
            tier_names = {"GSC": "Big Giant Stable", "GSC_L1": "GSC Upper Trends L1 (Comeback)", "GSC_L2": "GSC Upper Trends L2 (Swing Scalp)"}
            return (
                f"DEMO/PAPER · [Watchlist Tier Updated]\n"
                f"✅ {sym}-কে সফলভাবে {tier_names.get(tier, tier)}-এ স্থানান্তর করা হয়েছে। "
                f"চেকপয়েন্ট সেভ করা হয়েছে (আনডু করতে `/rollback` লিখুন)।"
                if bangla else
                f"DEMO/PAPER · {sym} moved to tier {tier_names.get(tier, tier)}. Checkpoint saved."
            )

        if tool_name == "learn_or_patch_skill":
            res = tool_res["result"]
            return (
                f"DEMO/PAPER · [Hermes Self-Improving Skill Updated 🧠]\n"
                f"✅ নতুন জ্ঞান সংরক্ষিত হয়েছে:\n"
                f"- স্কিল ফাইল: `{res['file']}` (Version {res['version']})\n"
                f"- কারণ: {res['reason']}\n"
                f"হার্মিস ভবিষ্যতে এই নিয়মটি সবসময় মেনে চলবে।"
                if bangla else
                f"DEMO/PAPER · Skill patched: `{res['file']}` (v{res['version']}). Reason: {res['reason']}."
            )

        if tool_name == "restore_quarantined_company":
            sym = tool_res["result"]["symbol"]
            return (
                f"DEMO/PAPER · [Company Restored]\n"
                f"✅ {sym}-কে কোয়ারেন্টাইন তালিকা থেকে সক্রিয় ওয়াচলিস্টে রিস্টোর করা হয়েছে। "
                f"চেকপয়েন্ট সেভ করা হয়েছে।"
                if bangla else
                f"DEMO/PAPER · {sym} restored to active watchlist. Checkpoint saved."
            )

        if tool_name == "execute_manual_order":
            res = tool_res["result"]
            return (
                f"DEMO/PAPER · [Manual Order Executed]\n"
                f"✅ {res['symbol']}-এর {res['quantity']} টি শেয়ার ৳{res['price']:,.2f} দরে কেনা হয়েছে "
                f"(মোট খরচ: ৳{res['cost']:,.2f}, বাকেট {res['bucket']})।"
            )

        return f"DEMO/PAPER · Tool {tool_name} executed successfully."

    async def _conversational_inference(self, message: str, history: list[dict[str, str]], snapshot: dict) -> dict[str, Any]:
        """Runs conversational response with Layered Memory and Matched SKILL.md injection."""
        with self.database.read() as session:
            memory = HermesMemory(session)
            layer1 = memory.format_layer_1_prompt()

            # Find symbols mentioned for Layer 3 durable facts
            mentioned_symbols = [c["symbol"] for c in snapshot["companies"] if c["symbol"].lower() in message.lower()]
            layer3 = memory.format_layer_3_prompt(mentioned_symbols)

            # Match on-demand skills
            matched_skills = self.skills_mgr.match_skills(message, max_skills=2)
            skills_text = "\n\n".join(f"[ACTIVE SKILL: {s.title} (v{s.version})]\n{s.content}" for s in matched_skills)

        # Layer 2: Compress conversation history
        compressed_history = self.compress_history(history, max_turns=6)

        # Context payload
        clean_snapshot = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":"))
        if len(clean_snapshot) > 30000:
            clean_snapshot = clean_snapshot[:29500] + "...}"

        full_system_prompt = (
            f"{BASE_AGENT_PROMPT}\n\n"
            f"{layer1}\n\n"
            f"{skills_text}\n\n"
            f"{layer3}\n\n"
            f"[CURRENT PORTFOLIO STATE SNAPSHOT (DEMO)]\n{clean_snapshot}\n"
        )
        # Final scrubbing
        full_system_prompt = redact_secrets(full_system_prompt)

        # Check OpenRouter credentials & budget
        if not self.settings.openrouter_api_key:
            return self._local_conversational_fallback(message, snapshot)

        # External OpenRouter call - check and increment budget
        day = datetime.now(DHAKA).date()
        allowed = True
        with self.database.write() as session:
            budget = session.get(ChatBudget, day)
            if budget is None:
                budget = ChatBudget(day=day, calls=0)
                session.add(budget)
            if budget.calls >= self.settings.chat_daily_call_limit:
                allowed = False
            else:
                budget.calls += 1

        if not allowed:
            return self._local_conversational_fallback(message, snapshot, warning="Daily external-call allowance reached; using free local agentic summary.")

        messages = [{"role": "system", "content": full_system_prompt}]
        for turn in compressed_history:
            messages.append({"role": turn["role"], "content": redact_secrets(turn["content"])})
        messages.append({"role": "user", "content": message})

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(25, connect=5), transport=self.transport) as client:
                resp = await client.post(
                    OPENROUTER_URL,
                    headers={
                        "Authorization": f"Bearer {self.settings.openrouter_api_key}",
                        "Content-Type": "application/json",
                        "X-Title": "Humming Bird Trading Cockpit",
                    },
                    json={
                        "model": self.settings.openrouter_model,
                        "messages": messages,
                        "temperature": 0.2,
                        "max_tokens": self.settings.chat_max_output_tokens,
                    },
                )
                resp.raise_for_status()
                reply_text = resp.json()["choices"][0]["message"]["content"]
                clean_reply = redact_secrets(reply_text.strip()[:12000])

                with self.database.write() as session:
                    state = portfolio_state(session)
                    mem = HermesMemory(session)
                    mem.record_turn(session_date=state.clock_date, role="assistant", content=clean_reply)

                return {
                    "reply": clean_reply,
                    "provider": "openrouter",
                    "model": self.settings.openrouter_model,
                    "warning": None,
                    "context_date": snapshot["app"]["date"],
                    "context_revision": snapshot["app"]["revision"],
                    "read_only": False,
                }
        except Exception as exc:
            logger.warning("OpenRouter call failed: %s; falling back to local agent summary.", exc)
            return self._local_conversational_fallback(message, snapshot, warning=f"OpenRouter unavailable ({exc}); local summary used.")

    def _local_conversational_fallback(self, message: str, snapshot: dict, warning: str | None = None) -> dict[str, Any]:
        from backend.chat import local_summary
        reply = local_summary(message, snapshot)
        with self.database.write() as session:
            state = portfolio_state(session)
            mem = HermesMemory(session)
            mem.record_turn(session_date=state.clock_date, role="assistant", content=reply)
        return {
            "reply": reply,
            "provider": "local",
            "model": "hermes-local-quant",
            "warning": warning or "Local summary mode: zero external API cost.",
            "context_date": snapshot["app"]["date"],
            "context_revision": snapshot["app"]["revision"],
            "read_only": False,
        }
