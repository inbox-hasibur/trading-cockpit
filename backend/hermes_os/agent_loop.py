"""Hermes OS Core Agent Loop.

Vendored and adapted from NousResearch/hermes-agent conversation & ReAct loop mechanics.
Orchestrates:
1. Agent-curated memory injection (USER.md + MEMORY.md)
2. On-demand skill loading via SkillLoader
3. FTS5 session search recall
4. Automatic context compression (>50% -> 20%)
5. Provider-agnostic model routing (OpenRouter / Google Gemini / Local)
6. Zero-secret safety enforcement via SecretGuard
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from backend.hermes.secret_guard import SecretGuard, redact_secrets
from backend.hermes_os.config import HermesConfig, ensure_hermes_state_dir, load_hermes_config
from backend.hermes_os.memory_curator import MemoryCurator
from backend.hermes_os.skill_loader import SkillLoader

logger = logging.getLogger(__name__)


class HermesOSAgentLoop:
    """Core autonomous agent loop implementing NousResearch Hermes Agent mechanics."""

    def __init__(
        self,
        hermes_dir: Path | str | None = None,
        db_path: Path | str | None = None,
    ):
        self.home_dir = ensure_hermes_state_dir(hermes_dir)
        self.config: HermesConfig = load_hermes_config(self.home_dir)
        self.curator = MemoryCurator(self.home_dir, db_path=db_path)
        self.skill_loader = SkillLoader(self.home_dir)

    def prepare_turn_messages(
        self,
        user_message: str,
        history: list[dict[str, Any]] | None = None,
        conversation_id: str | None = None,
        base_system_prompt: str | None = None,
    ) -> list[dict[str, Any]]:
        """Assembles prompt context: Base System Prompt + USER.md + MEMORY.md + Matched Skills + FTS Recall."""
        clean_user_msg = redact_secrets(user_message.strip())

        # 1. Base Prompt + Curated Memory
        base_prompt = base_system_prompt or (
            "You are Hermes, an autonomous Agentic Share Assistant and Portfolio Co-Pilot for the Bangladesh Stock Market (DSE).\n"
            "You manage execution on StockNow virtual portfolio ('Humming Bird') with strict discipline and capital preservation."
        )

        memory_context = self.curator.format_system_context()

        # 2. Match relevant skills on demand
        matched_skills = self.skill_loader.match_skills(clean_user_msg)
        skills_prompt = self.skill_loader.format_matched_skills_prompt(matched_skills)

        # 3. Retrieve FTS5 session memory recall if relevant
        fts_recall_block = ""
        recall_results = self.curator.session_search(clean_user_msg, limit=3)
        if recall_results:
            recall_lines = [
                f"  - [{r['created_at'][:10]}] ({r['role'].upper()}): {r['content'][:150]}"
                for r in recall_results
            ]
            fts_recall_block = "[FTS5 HISTORICAL RECALL]\n" + "\n".join(recall_lines) + "\n\n"

        full_system_prompt = f"{base_prompt}\n\n{memory_context}\n{skills_prompt}{fts_recall_block}".strip()

        messages: list[dict[str, Any]] = [{"role": "system", "content": full_system_prompt}]

        # 4. Append history
        if history:
            for turn in history:
                role = str(turn.get("role", "user")).lower()
                content = redact_secrets(str(turn.get("content", "")))
                if content:
                    messages.append({"role": role, "content": content})

        # 5. Append latest user message
        messages.append({"role": "user", "content": clean_user_msg})

        # 6. Check context fill and compress if > 50%
        compressed_messages, was_compressed = self.curator.check_and_compress_context(
            messages, max_tokens=self.config.max_context_tokens
        )
        if was_compressed:
            logger.info("Hermes OS compressed context before dispatching to model.")

        return compressed_messages

    def post_turn(
        self,
        conversation_id: str,
        user_message: str,
        assistant_reply: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Post-turn processing: indexes turns into SQLite FTS5 and curates USER.md and MEMORY.md."""
        clean_user = redact_secrets(user_message.strip())
        clean_assistant = redact_secrets(assistant_reply.strip())

        # Index both turns in FTS5
        symbol_hint = context.get("symbol") if context else None
        self.curator.index_message(conversation_id, "user", clean_user, symbol=symbol_hint)
        self.curator.index_message(conversation_id, "assistant", clean_assistant, symbol=symbol_hint)

        # Auto-curate learned preferences and market theses
        user_curation = self.curator.curate_turn("user", clean_user, context=context)
        assistant_curation = self.curator.curate_turn("assistant", clean_assistant, context=context)

        all_patches = user_curation.get("patches", []) + assistant_curation.get("patches", [])
        return {
            "user_updated": user_curation.get("user_updated") or assistant_curation.get("user_updated"),
            "memory_updated": user_curation.get("memory_updated") or assistant_curation.get("memory_updated"),
            "patches": all_patches,
        }
