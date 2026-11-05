"""Hermes Agent Loop, Toolset Orchestration & State Checkpoints.

Implements the Nous Research-style agent turn loop:
System Prompt + Layer 1 Profile + Matched Skills + Layer 3 Facts ->
Agent Tool Execution -> State Checkpointing -> Automatic Context Compression ->
Re-injection & Response.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import DHAKA, Settings
from backend.database import (
    ChatBudget,
    CompanyProfile,
    CustomRule,
    Database,
    HermesStateCheckpoint,
    PortfolioState,
    portfolio_state,
)
from backend.engine.money import decimal
from backend.hermes.memory import HermesMemory
from backend.hermes.secret_guard import SecretGuard, redact_secrets
from backend.hermes.skills_manager import SkillsManager
from backend.hermes.tools_dispatcher import (
    detect_intent_and_tool,
    dispatch_tool,
    format_tool_response,
)
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
    def create_checkpoint(
        session: Session,
        state: PortfolioState,
        action: str,
        description: str,
        symbol: str | None = None,
        diff_payload: dict[str, Any] | None = None,
        actor: str = "Hermes Agent",
    ) -> HermesStateCheckpoint:
        payload: dict[str, Any] = {
            "action": action,
            "description": description,
            "date": state.clock_date.isoformat(),
            "rules_revision": state.rules_revision,
            "automation_enabled": getattr(state, "automation_enabled", True),
            "ingestion_mode": getattr(state, "ingestion_mode", "BACKGROUND_POLLING"),
            "polling_interval_sec": getattr(state, "polling_interval_sec", 120),
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
            id=f"{time.time_ns():020d}_{uuid4().hex[:8]}",
            action=action,
            description=description,
            snapshot_payload=payload,
            diff_payload=diff_payload,
            actor=actor,
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

        if "automation_enabled" in payload:
            state.automation_enabled = payload["automation_enabled"]
            state.paused = not state.automation_enabled
        if "ingestion_mode" in payload:
            state.ingestion_mode = payload["ingestion_mode"]
        if "polling_interval_sec" in payload:
            state.polling_interval_sec = payload["polling_interval_sec"]

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
        """Deterministic execution of Hermes Agent tools with automatic checkpointing and rule diff tracking."""
        return dispatch_tool(tool_name, args, session, state, self.settings, self.skills_mgr, CheckpointManager)

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
        return detect_intent_and_tool(message, snapshot)

    async def run_turn(self, user_message: str, history: list[dict[str, str]], conversation_id: str | None = None) -> dict[str, Any]:
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
                conversation_id=conversation_id,
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
                        conversation_id=conversation_id,
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
                "set_automation_config": "SET_AUTOMATION_CONFIG",
                "set_ai_model": "SET_AI_MODEL",
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
                "conversation_id": conversation_id,
                "read_only": False,
            }

        # Otherwise: Assemble full layered prompt for conversational response
        res = await self._conversational_inference(safe_message, history, snapshot, conversation_id=conversation_id)
        res["conversation_id"] = conversation_id
        return res

    def _format_tool_response(self, tool_name: str, tool_res: dict[str, Any], user_msg: str, snapshot: dict) -> str:
        return format_tool_response(tool_name, tool_res, user_msg, snapshot)

    async def _conversational_inference(self, message: str, history: list[dict[str, str]], snapshot: dict, conversation_id: str | None = None) -> dict[str, Any]:
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

        # Tier 1 & Tier 2 budget enforcement
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
            return self._local_conversational_fallback(
                message,
                snapshot,
                warning="Daily external call budget reached. Running offline on Local Deterministic Quant Brain.",
                conversation_id=conversation_id,
            )

        # Tier 1: User-selected OpenRouter model
        target_model = snapshot.get("app", {}).get("active_model") or self.settings.openrouter_model
        messages = [{"role": "system", "content": full_system_prompt}]
        for turn in compressed_history:
            messages.append({"role": turn["role"], "content": redact_secrets(turn["content"])})
        messages.append({"role": "user", "content": message})

        if self.settings.openrouter_api_key:
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
                            "model": target_model,
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
                        mem.record_turn(session_date=state.clock_date, role="assistant", content=clean_reply, conversation_id=conversation_id)

                    return {
                        "reply": clean_reply,
                        "provider": "openrouter",
                        "model": target_model,
                        "warning": None,
                        "context_date": snapshot["app"]["date"],
                        "context_revision": snapshot["app"]["revision"],
                        "conversation_id": conversation_id,
                        "read_only": False,
                    }
            except Exception as exc:
                logger.warning("Tier 1 OpenRouter failed: %s; falling back to Tier 2 Gemini.", exc)

        # Tier 2: 1st Fallback — Free Google Gemini API
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip()
        if gemini_key:
            try:
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
                prompt_text = f"{full_system_prompt}\n\nOperator message: {message}"
                async with httpx.AsyncClient(timeout=httpx.Timeout(20, connect=5), transport=self.transport) as client:
                    resp = await client.post(
                        gemini_url,
                        json={"contents": [{"parts": [{"text": prompt_text}]}]},
                    )
                    resp.raise_for_status()
                    g_reply = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                    clean_reply = redact_secrets(g_reply.strip()[:12000])
                    with self.database.write() as session:
                        state = portfolio_state(session)
                        mem = HermesMemory(session)
                        mem.record_turn(session_date=state.clock_date, role="assistant", content=clean_reply, conversation_id=conversation_id)
                    return {
                        "reply": clean_reply,
                        "provider": "gemini",
                        "model": "google/gemini-2.5-flash",
                        "warning": "Served via 1st Fallback: Free Google Gemini API",
                        "context_date": snapshot["app"]["date"],
                        "context_revision": snapshot["app"]["revision"],
                        "conversation_id": conversation_id,
                        "read_only": False,
                    }
            except Exception as exc:
                logger.warning("Tier 2 Gemini fallback failed: %s; falling back to Tier 3 Local Brain.", exc)

        # Tier 3: 2nd Fallback — Deterministic Local Quant Brain ($0 offline)
        return self._local_conversational_fallback(message, snapshot, conversation_id=conversation_id)

    def _local_conversational_fallback(self, message: str, snapshot: dict, warning: str | None = None, conversation_id: str | None = None) -> dict[str, Any]:
        from backend.chat import local_summary
        reply = local_summary(message, snapshot)
        with self.database.write() as session:
            state = portfolio_state(session)
            mem = HermesMemory(session)
            mem.record_turn(session_date=state.clock_date, role="assistant", content=reply, conversation_id=conversation_id)
        return {
            "reply": reply,
            "provider": "local",
            "model": "hermes-local-quant",
            "warning": warning or "Local summary mode: zero external API cost.",
            "context_date": snapshot["app"]["date"],
            "context_revision": snapshot["app"]["revision"],
            "conversation_id": conversation_id,
            "read_only": False,
        }
