"""Three-Layer Memory System for Hermes Agent.

Layer 1: Persistent Operator Profile & Core Directives
Layer 2: Searchable Session History (Transcripts & Cross-Turn Recall)
Layer 3: Durable Facts & Canary Thesis Memory per Company
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from backend.database import (
    CanaryThesis,
    CompanyProfile,
    HermesConversationThread,
    HermesDurableFact,
    HermesSessionMemory,
    HermesUserProfile,
)
from backend.hermes.secret_guard import redact_secrets

logger = logging.getLogger(__name__)


class HermesMemory:
    def __init__(self, session: Session, curator: Any | None = None):
        self.session = session
        self._curator = curator

    @property
    def curator(self):
        if self._curator is None:
            try:
                from backend.hermes_os.memory_curator import MemoryCurator
                self._curator = MemoryCurator()
            except Exception as e:
                logger.debug("Could not initialize MemoryCurator: %s", e)
                return None
        return self._curator

    # -------------------------------------------------------------
    # Layer 1: Operator Profile & Core Directives
    # -------------------------------------------------------------
    def get_user_profile(self) -> dict[str, Any]:
        profile = self.session.get(HermesUserProfile, 1)
        if profile is None:
            profile = HermesUserProfile(
                id=1,
                operator_name="Hasibur",
                language_preference="Bangla, Banglish, English",
                risk_posture="Strict No-Loss / Capital Preservation",
                custom_directives=[
                    "Never panic-sell at a net loss (< 0% after 1% round-trip fees).",
                    "On severe danger/bankruptcy news, immediately quarantine, lock 90% profit, and retain 10% canary probe.",
                    "Enforce T+2 rolling capital buckets (Buckets A, B, C) for DSE.",
                    "Classify watchlist into GSC (Big Giant Stable), GSC_L1 (Comeback), and GSC_L2 (Swing Scalp).",
                ],
            )
            self.session.add(profile)
            self.session.flush()

        return {
            "operator_name": profile.operator_name,
            "language_preference": profile.language_preference,
            "risk_posture": profile.risk_posture,
            "directives": profile.custom_directives,
        }

    def format_layer_1_prompt(self) -> str:
        prof = self.get_user_profile()
        directives_str = "\n".join(f"- {d}" for d in prof["directives"])
        base_layer1 = (
            f"[LAYER 1 MEMORY: OPERATOR DIRECTIVES & POSTURE]\n"
            f"Operator: {prof['operator_name']}\n"
            f"Language: {prof['language_preference']}\n"
            f"Risk Posture: {prof['risk_posture']}\n"
            f"Core Rules:\n{directives_str}\n"
        )
        if self.curator:
            try:
                user_md = self.curator.read_user_md().strip()
                if user_md:
                    return f"{base_layer1}\n[AGENT-CURATED OPERATOR PROFILE (USER.md)]\n{user_md}\n"
            except Exception as e:
                logger.debug("Failed to read USER.md: %s", e)
        return base_layer1

    # -------------------------------------------------------------
    # Layer 2: Searchable Session History & Conversation Threads
    # -------------------------------------------------------------
    def get_or_create_thread(self, conversation_id: str | None = None, title: str | None = None) -> HermesConversationThread:
        if conversation_id:
            thread = self.session.get(HermesConversationThread, conversation_id)
            if thread:
                return thread
        new_id = conversation_id or str(uuid4())
        thread = HermesConversationThread(
            id=new_id,
            title=(title or "General Strategy").strip()[:100],
        )
        self.session.add(thread)
        self.session.flush()
        return thread

    def list_threads(self) -> list[dict[str, Any]]:
        threads = list(self.session.scalars(
            select(HermesConversationThread).order_by(HermesConversationThread.updated_at.desc()).limit(30)
        ))
        if not threads:
            default_t = self.get_or_create_thread(title="General Trading Strategy")
            threads = [default_t]
        result = []
        for t in threads:
            msg_count = self.session.scalar(
                select(func.count(HermesSessionMemory.id)).where(HermesSessionMemory.conversation_id == t.id)
            ) or 0
            result.append({
                "id": t.id,
                "title": t.title,
                "message_count": msg_count,
                "created_at": t.created_at,
                "updated_at": t.updated_at,
            })
        return result

    def get_thread_messages(self, conversation_id: str, limit: int = 50) -> list[dict[str, Any]]:
        msgs = list(self.session.scalars(
            select(HermesSessionMemory)
            .where(HermesSessionMemory.conversation_id == conversation_id)
            .order_by(HermesSessionMemory.id.asc())
            .limit(limit)
        ))
        return [{
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "date": m.session_date.isoformat(),
            "action": m.action_taken,
            "created_at": m.created_at,
        } for m in msgs]

    def record_turn(
        self,
        session_date: date,
        role: str,
        content: str,
        symbol_mentioned: str | None = None,
        action_taken: str | None = None,
        conversation_id: str | None = None,
    ) -> None:
        clean_content = redact_secrets(content.strip())[:4000]
        if conversation_id:
            thread = self.session.get(HermesConversationThread, conversation_id)
            if thread:
                from backend.config import utc_now_iso
                thread.updated_at = utc_now_iso()
                if role == "user" and thread.title in {"New Conversation", "General Strategy"}:
                    thread.title = clean_content[:45] + ("…" if len(clean_content) > 45 else "")
            else:
                self.get_or_create_thread(conversation_id, title=clean_content[:45])
        mem = HermesSessionMemory(
            conversation_id=conversation_id,
            session_date=session_date,
            role=role,
            content=clean_content,
            symbol_mentioned=symbol_mentioned,
            action_taken=action_taken,
        )
        self.session.add(mem)
        self.session.flush()

        if self.curator:
            try:
                self.curator.index_message(
                    conversation_id=conversation_id or "default",
                    role=role,
                    content=clean_content,
                    symbol=symbol_mentioned,
                )
                self.curator.curate_turn(
                    role=role,
                    message=clean_content,
                    context={"symbol": symbol_mentioned, "action": action_taken},
                )
            except Exception as exc:
                logger.debug("Curator indexing/curation error: %s", exc)

    def search_sessions(self, query: str, limit: int = 4) -> list[dict[str, Any]]:
        text_query = query.strip()
        if not text_query:
            return []

        # 1. Try SQLite FTS5 search via MemoryCurator first
        if self.curator:
            try:
                fts_hits = self.curator.session_search(text_query, limit=limit)
                if fts_hits:
                    return [
                        {
                            "date": (h.get("created_at") or "")[:10] or "2026-11-06",
                            "role": h.get("role", "user"),
                            "content": (h.get("content") or "")[:300],
                            "symbol": h.get("symbol"),
                            "action": None,
                        }
                        for h in fts_hits
                    ]
            except Exception as exc:
                logger.debug("Curator FTS5 search error: %s", exc)

        # 2. Fallback to token matching over DB rows
        text_query_lower = text_query.lower()
        tokens = [token for token in text_query_lower.split() if len(token) >= 3]
        if not tokens:
            tokens = [text_query_lower]

        results = []
        stmt = (
            select(HermesSessionMemory)
            .order_by(HermesSessionMemory.id.desc())
            .limit(30)
        )
        records = list(self.session.scalars(stmt))
        for r in records:
            content_lower = r.content.lower()
            if any(t in content_lower for t in tokens) or (r.symbol_mentioned and r.symbol_mentioned.lower() in text_query_lower):
                results.append({
                    "date": r.session_date.isoformat(),
                    "role": r.role,
                    "content": r.content[:300],
                    "symbol": r.symbol_mentioned,
                    "action": r.action_taken,
                })
                if len(results) >= limit:
                    break
        return results

    # -------------------------------------------------------------
    # Layer 3: Durable Facts & Canary Thesis Memory
    # -------------------------------------------------------------
    def record_fact(
        self,
        symbol: str,
        fact: str,
        category: str = "FUNDAMENTAL",
        confidence: str = "HIGH",
    ) -> HermesDurableFact:
        clean_fact = redact_secrets(fact.strip())[:1000]
        fact_obj = HermesDurableFact(
            symbol=symbol.upper(),
            category=category,
            fact=clean_fact,
            confidence=confidence,
            active=True,
        )
        self.session.add(fact_obj)
        self.session.flush()
        return fact_obj

    def recall_facts_for_symbol(self, symbol: str) -> list[dict[str, Any]]:
        facts = list(self.session.scalars(
            select(HermesDurableFact)
            .where(HermesDurableFact.symbol == symbol.upper(), HermesDurableFact.active == True)
            .order_by(HermesDurableFact.id.desc())
            .limit(5)
        ))
        canary = list(self.session.scalars(
            select(CanaryThesis)
            .where(CanaryThesis.symbol == symbol.upper())
            .order_by(CanaryThesis.id.desc())
            .limit(3)
        ))
        recalled = []
        for f in facts:
            recalled.append({"type": "DURABLE_FACT", "fact": f.fact, "category": f.category, "confidence": f.confidence})
        for c in canary:
            recalled.append({
                "type": "CANARY_THESIS",
                "thesis": c.thesis,
                "status": c.status,
                "entry_price": float(c.entry_price),
                "notes": c.notes,
            })
        return recalled

    def format_layer_3_prompt(self, symbols: list[str]) -> str:
        sections = []
        for sym in symbols:
            items = self.recall_facts_for_symbol(sym)
            if items:
                lines = []
                for it in items:
                    if it["type"] == "DURABLE_FACT":
                        lines.append(f"  - [{it['category']}] {it['fact']} (Confidence: {it['confidence']})")
                    else:
                        lines.append(f"  - [CANARY {it['status']}] Thesis: {it['thesis']} | Notes: {it['notes']}")
                sections.append(f"Durable Knowledge for {sym}:\n" + "\n".join(lines))

        memory_notes = ""
        if self.curator:
            try:
                mem_md = self.curator.read_memory_md().strip()
                if mem_md:
                    memory_notes = f"\n[AGENT-CURATED WORKING MEMORY (MEMORY.md)]\n{mem_md}\n"
            except Exception as exc:
                logger.debug("Failed reading MEMORY.md: %s", exc)

        if not sections and not memory_notes:
            return ""

        body = "\n\n".join(sections) if sections else ""
        header = "[LAYER 3 MEMORY: DURABLE COMPANY FACTS & CANARY PROBES]\n" if sections else ""
        return f"{header}{body}{memory_notes}"

