"""Agent-Curated Memory & SQLite FTS5 Full-Text Search.

Vendored and customized from NousResearch/hermes-agent.
Manages:
1. USER.md (Operator Profile & Personal Directives)
2. MEMORY.md (Working Context, Theses & Market Memory)
3. SQLite FTS5 Full-Text Search (`hermes_fts`) over session transcripts
4. Context Compression (>50% fill compressed down to 20% target)
Protected with zero-secret isolation via SecretGuard.
"""

from __future__ import annotations

import logging
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.hermes.secret_guard import SecretGuard, redact_secrets
from backend.hermes_os.config import ensure_hermes_state_dir, load_hermes_config

logger = logging.getLogger(__name__)

# Heuristics for detecting operator preferences and rules to curate into USER.md
PREFERENCE_PATTERNS = [
    re.compile(r"(?:amar|my|i)\s+(?:naam|name)\s+(?:is\s+|hoche\s+|holo\s+)?([A-Za-z0-9_\s]{2,40})", re.IGNORECASE),
    re.compile(r"(?:prefer|like|bhalobasi|chai)\s+(?:to\s+|korte\s+)?([A-Za-z0-9_\-\s]{3,60})", re.IGNORECASE),
    re.compile(r"(?:language|bhasha)\s*[:=]?\s*([A-Za-z0-9_\-\s,]{3,40})", re.IGNORECASE),
    re.compile(r"(?:never|kokhono|always|shobshomoy|rule)\s+([A-Za-z0-9_\-\s,৳%]{5,80})", re.IGNORECASE),
    re.compile(r"(?:risk|loss|allocation)\s+([A-Za-z0-9_\-\s,%]{5,80})", re.IGNORECASE),
]

# Heuristics for detecting market facts and trade findings to curate into MEMORY.md
MARKET_FACT_PATTERNS = [
    re.compile(r"\b([A-Z0-9]{3,12})\b.*?(?:quarantine|deulia|crisis|bankruptcy|crash|fall|drop)", re.IGNORECASE),
    re.compile(r"\b([A-Z0-9]{3,12})\b.*?(?:support|resistance|floor|breakout|turnaround)\s*(?:at\s+|৳)?([0-9.]+)?", re.IGNORECASE),
    re.compile(r"\b(?:earnings|dividend|nav|eps|pe\s+ratio)\b.*?\b([A-Z0-9]{3,12})\b", re.IGNORECASE),
    re.compile(r"(?:sold|bought|executed|traded)\s+(\d+)\s+(?:shares\s+of\s+)?([A-Z0-9]{3,12})", re.IGNORECASE),
]


class MemoryCurator:
    """NousResearch-style autonomous memory curator with FTS5 search and disk markdown storage."""

    def __init__(self, hermes_dir: Path | str | None = None, db_path: Path | str | None = None):
        self.home_dir = ensure_hermes_state_dir(hermes_dir)
        self.config = load_hermes_config(self.home_dir)
        self.user_file = self.home_dir / "USER.md"
        self.memory_file = self.home_dir / "MEMORY.md"

        # Assert secret safety on memory files
        SecretGuard.assert_safe_path(self.user_file)
        SecretGuard.assert_safe_path(self.memory_file)

        # SQLite FTS5 database path (internal engine store)
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = self.home_dir / "mnemosyne.db"

        self._init_fts()

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(str(self.db_path), timeout=15.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_fts(self) -> None:
        """Initializes the FTS5 virtual table for lightning-fast transcript recall."""
        with self._connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS hermes_fts USING fts5(
                        conversation_id UNINDEXED,
                        role UNINDEXED,
                        content,
                        symbol,
                        created_at UNINDEXED,
                        tokenize='unicode61 remove_diacritics 2'
                    );
                """)
                conn.commit()
            except sqlite3.OperationalError as exc:
                logger.warning("FTS5 table creation warning (falling back if needed): %s", exc)

    # ------------------------------------------------------------------
    # FTS5 Indexing & Search
    # ------------------------------------------------------------------
    def index_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        symbol: str | None = None,
        created_at: str | None = None,
    ) -> None:
        """Indexes a conversation message into the FTS5 virtual table after zero-secret scrubbing."""
        if not content or not content.strip():
            return

        clean_content = redact_secrets(content.strip())
        now_iso = created_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
        sym = symbol.strip().upper() if symbol else ""

        with self._connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO hermes_fts (conversation_id, role, content, symbol, created_at) VALUES (?, ?, ?, ?, ?)",
                (conversation_id, role, clean_content, sym, now_iso),
            )
            conn.commit()

    def session_search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Performs full-text search across transcripts using SQLite FTS5 with safe fallback."""
        clean_q = query.strip()
        if not clean_q:
            return []

        # Sanitize query for FTS5 (strip special punctuation syntax like ", *, (, ), :, ^)
        terms = re.findall(r"[A-Za-z0-9_]+", clean_q)
        if not terms:
            terms = [clean_q]

        fts_query = " ".join(f'"{t}"*' for t in terms if len(t) >= 2) or clean_q

        with self._connection() as conn:
            cur = conn.cursor()
            try:
                # 1. Primary: FTS5 MATCH with BM25 ranking
                sql = """
                    SELECT conversation_id, role, content, symbol, created_at, bm25(hermes_fts) as rank
                    FROM hermes_fts
                    WHERE hermes_fts MATCH ?
                    ORDER BY rank ASC
                    LIMIT ?
                """
                rows = cur.execute(sql, (fts_query, limit)).fetchall()
                return [
                    {
                        "conversation_id": row["conversation_id"],
                        "role": row["role"],
                        "content": row["content"],
                        "symbol": row["symbol"],
                        "created_at": row["created_at"],
                        "rank": float(row["rank"]),
                    }
                    for row in rows
                ]
            except sqlite3.OperationalError as fts_exc:
                logger.debug("FTS5 match failed (%s), falling back to LIKE query: %s", fts_exc, clean_q)
                # 2. Graceful fallback: Safe LIKE query
                like_term = f"%{clean_q[:30]}%"
                sql = """
                    SELECT conversation_id, role, content, symbol, created_at, 0.0 as rank
                    FROM hermes_fts
                    WHERE content LIKE ? OR symbol LIKE ?
                    ORDER BY rowid DESC
                    LIMIT ?
                """
                rows = cur.execute(sql, (like_term, like_term, limit)).fetchall()
                return [
                    {
                        "conversation_id": row["conversation_id"],
                        "role": row["role"],
                        "content": row["content"],
                        "symbol": row["symbol"],
                        "created_at": row["created_at"],
                        "rank": 0.0,
                    }
                    for row in rows
                ]

    # ------------------------------------------------------------------
    # USER.md Management & Curation
    # ------------------------------------------------------------------
    def read_user_md(self) -> str:
        """Reads USER.md from disk."""
        SecretGuard.assert_safe_path(self.user_file)
        if self.user_file.exists():
            return self.user_file.read_text(encoding="utf-8")
        return ""

    def write_user_md(self, content: str) -> None:
        """Writes scrubbed markdown content to USER.md."""
        SecretGuard.assert_safe_path(self.user_file)
        clean = redact_secrets(content)
        self.user_file.write_text(clean, encoding="utf-8")

    def patch_user_profile(self, preference_statement: str, section: str = "Learned Preferences") -> bool:
        """Appends a new learned rule or preference to USER.md without duplicates."""
        clean_stmt = redact_secrets(preference_statement.strip())
        if not clean_stmt:
            return False

        current = self.read_user_md()
        # Avoid duplicate entries
        if clean_stmt.lower() in current.lower():
            return False

        header = f"## {section}"
        bullet = f"- {clean_stmt}"
        if header in current:
            parts = current.split(header, 1)
            updated = f"{parts[0]}{header}\n{bullet}\n{parts[1].lstrip()}"
        else:
            updated = f"{current.rstrip()}\n\n{header}\n{bullet}\n"

        self.write_user_md(updated)
        logger.info("Hermes MemoryCurator patched USER.md with: '%s'", clean_stmt[:60])
        return True

    # ------------------------------------------------------------------
    # MEMORY.md Management & Curation
    # ------------------------------------------------------------------
    def read_memory_md(self) -> str:
        """Reads MEMORY.md from disk."""
        SecretGuard.assert_safe_path(self.memory_file)
        if self.memory_file.exists():
            return self.memory_file.read_text(encoding="utf-8")
        return ""

    def write_memory_md(self, content: str) -> None:
        """Writes scrubbed markdown content to MEMORY.md."""
        SecretGuard.assert_safe_path(self.memory_file)
        clean = redact_secrets(content)
        self.memory_file.write_text(clean, encoding="utf-8")

    def patch_memory(self, fact_statement: str, section: str = "Distilled Market Notes & Theses") -> bool:
        """Appends a new market note or distilled thesis to MEMORY.md without duplicates."""
        clean_fact = redact_secrets(fact_statement.strip())
        if not clean_fact:
            return False

        current = self.read_memory_md()
        if clean_fact.lower() in current.lower():
            return False

        header = f"## {section}"
        bullet = f"- {clean_fact}"
        if header in current:
            parts = current.split(header, 1)
            updated = f"{parts[0]}{header}\n{bullet}\n{parts[1].lstrip()}"
        else:
            updated = f"{current.rstrip()}\n\n{header}\n{bullet}\n"

        self.write_memory_md(updated)
        logger.info("Hermes MemoryCurator patched MEMORY.md with: '%s'", clean_fact[:60])
        return True

    # ------------------------------------------------------------------
    # Auto-Curation Loop (per Turn)
    # ------------------------------------------------------------------
    def curate_turn(
        self,
        role: str,
        message: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Inspects turn content and automatically curates learned operator preferences into USER.md

        and market theses/facts into MEMORY.md.
        """
        clean_msg = redact_secrets(message)
        patches: list[str] = []
        user_updated = False
        memory_updated = False

        # 1. Detect Operator Preferences / Directives (when user speaks)
        if role == "user":
            for pattern in PREFERENCE_PATTERNS:
                m = pattern.search(clean_msg)
                if m:
                    extracted = m.group(0).strip()
                    if len(extracted) >= 8:
                        if self.patch_user_profile(f"Operator stated: {extracted}"):
                            patches.append(f"USER.md: {extracted}")
                            user_updated = True

        # 2. Detect Market Observations / Theses / Order Results (from user or assistant)
        for pattern in MARKET_FACT_PATTERNS:
            m = pattern.search(clean_msg)
            if m:
                extracted = m.group(0).strip()
                if len(extracted) >= 6:
                    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                    if self.patch_memory(f"[{ts}] {extracted}"):
                        patches.append(f"MEMORY.md: {extracted}")
                        memory_updated = True

        # 3. Check explicit context hints (e.g. executed order or thesis discovery)
        if context:
            if context.get("action") == "QUARANTINE" and context.get("symbol"):
                sym = context["symbol"]
                reason = context.get("reason", "Bankruptcy/crash defense")
                self.patch_memory(f"Active Canary Probe: {sym} quarantined under thesis '{reason}'.")
                memory_updated = True
            elif context.get("action") == "TRADE_EXECUTED":
                sym = context.get("symbol", "")
                side = context.get("side", "")
                qty = context.get("quantity", 0)
                self.patch_memory(f"Trade Execution: {side} {qty} shares of {sym} on StockNow #164580.")
                memory_updated = True

        return {
            "user_updated": user_updated,
            "memory_updated": memory_updated,
            "patches": patches,
        }

    # ------------------------------------------------------------------
    # Context Compression (Threshold > 50% -> Target 20%)
    # ------------------------------------------------------------------
    def check_and_compress_context(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int | None = None,
    ) -> tuple[list[dict[str, Any]], bool]:
        """Calculates context fill.

        If estimated token count exceeds compression threshold (>50%),
        compresses older session turns into distilled bullet points in MEMORY.md and
        condenses message history targeting <=20% fill.
        """
        limit = max_tokens or self.config.max_context_tokens
        threshold = self.config.compression_threshold  # default 0.50
        target_ratio = self.config.compression_target   # default 0.20

        # Estimate tokens (~4 characters per token)
        total_chars = sum(len(str(m.get("content", ""))) for m in messages)
        estimated_tokens = total_chars // 4
        fill_ratio = estimated_tokens / limit if limit > 0 else 0.0

        if fill_ratio <= threshold or len(messages) <= 4:
            return messages, False

        # Context fill exceeds 50%: Compress!
        logger.info(
            "Context fill at %.1f%% (%d tokens / %d limit). Compressing context targeting %.1f%%...",
            fill_ratio * 100, estimated_tokens, limit, target_ratio * 100
        )

        # Retain system prompt (if index 0) and the most recent 4 messages
        system_msg = messages[0] if (messages and messages[0].get("role") == "system") else None
        recent_turns = messages[-4:]

        # Turns to compress: everything between system prompt and recent turns
        start_idx = 1 if system_msg else 0
        end_idx = max(start_idx, len(messages) - 4)
        turns_to_compress = messages[start_idx:end_idx]

        distilled_points: list[str] = []
        for t in turns_to_compress:
            role = t.get("role", "unknown")
            content = str(t.get("content", "")).strip()
            # Distill key actions and statements
            if len(content) > 8:
                summary_line = content[:140].replace("\n", " ") + ("…" if len(content) > 140 else "")
                distilled_points.append(f"{role.upper()}: {summary_line}")

        # Append distilled knowledge into MEMORY.md so it is permanently preserved
        if distilled_points:
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
            summary_block = f"[{ts} Session Compression Summary]\n" + "\n".join(f"  • {p}" for p in distilled_points[:10])
            self.patch_memory(summary_block, section="Distilled Market Notes & Theses")

        # Create a single condensed system turn
        condensed_message = {
            "role": "system",
            "content": f"[HERMES OS COMPRESSED CONTEXT: {len(turns_to_compress)} earlier turns distilled into MEMORY.md]",
        }

        compressed_messages: list[dict[str, Any]] = []
        if system_msg:
            compressed_messages.append(system_msg)
        compressed_messages.append(condensed_message)
        compressed_messages.extend(recent_turns)

        return compressed_messages, True

    # ------------------------------------------------------------------
    # Formatted System Prompt Context
    # ------------------------------------------------------------------
    def format_system_context(self) -> str:
        """Assembles USER.md and MEMORY.md into a structured context block for injection into Hermes prompt."""
        user_text = self.read_user_md().strip()
        memory_text = self.read_memory_md().strip()

        sections = []
        if user_text:
            sections.append(f"[HERMES AGENT: OPERATOR PROFILE (USER.md)]\n{user_text}")
        if memory_text:
            sections.append(f"[HERMES AGENT: WORKING CONTEXT & MARKET MEMORY (MEMORY.md)]\n{memory_text}")

        return "\n\n".join(sections) + "\n"
