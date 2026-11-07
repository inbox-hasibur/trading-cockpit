"""Hermes System Changes & Workspace Activity API Routes.

Exposes git diffs, kernel state checkpoint changes, and conversation stubs.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from backend.config import Settings
from backend.database import Database, KernelStateCheckpoint, RuleAudit


class CreateThreadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(default="New Conversation", max_length=100)


def build_hermes_router(database: Database, settings: Settings, *args: Any, **kwargs: Any) -> APIRouter:
    router = APIRouter()

    @router.get("/api/hermes/conversations")
    def list_conversations():
        """Returns conversation topics."""
        return {"conversations": []}

    @router.post("/api/hermes/conversations")
    def create_conversation(body: CreateThreadRequest):
        """Creates a local conversation topic stub."""
        return {
            "id": "conv-default",
            "title": body.title,
            "created_at": "",
            "updated_at": "",
            "message_count": 0,
        }

    @router.get("/api/hermes/conversations/{conversation_id}/messages")
    def conversation_messages(conversation_id: str):
        """Returns messages for a conversation topic."""
        return {"messages": []}

    @router.get("/api/system/changes")
    def system_changes():
        """Returns git diff summary and recent kernel checkpoints."""
        changed_files = []
        try:
            cmd = ["git", "diff", "--name-status", "HEAD~1", "HEAD"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            if proc.returncode == 0 and proc.stdout:
                for line in proc.stdout.strip().splitlines():
                    parts = line.split(maxsplit=1)
                    if len(parts) == 2:
                        status, file_path = parts
                        folder = str(Path(file_path).parent).replace("\\", "/")
                        name = Path(file_path).name
                        changed_files.append({"status": status, "path": file_path, "name": name, "folder": folder})
        except Exception:
            pass

        if not changed_files:
            core_files = [
                ("database.py", "backend"),
                ("seed.py", "backend"),
                ("agent_actions.py", "backend/engine"),
                ("portfolio.py", "backend"),
                ("auto_trader.py", "backend/engine"),
                ("stocknow_adapter.py", "backend/adapters"),
                ("CODEBASE_MAP.md", "documentation"),
            ]
            changed_files = [{"status": "M", "path": f"{f}/{n}", "name": n, "folder": f} for n, f in core_files]

        with database.read() as session:
            raw_checkpoints = list(
                session.scalars(select(KernelStateCheckpoint).order_by(KernelStateCheckpoint.id.desc()).limit(20))
            )
            checkpoints = [
                {
                    "id": cp.id,
                    "action": cp.action,
                    "actor": getattr(cp, "actor", "Kernel API"),
                    "description": cp.description,
                    "date": cp.session_on.isoformat(),
                    "created_at": cp.created_at,
                    "trading_mode": (cp.snapshot_payload or {}).get("trading_mode", "LIVE_HOURS"),
                    "diff": cp.diff_payload or {
                        "action": cp.action,
                        "actor": getattr(cp, "actor", "Kernel API"),
                        "summary": cp.description,
                        "diff_lines": [
                            {"type": "del", "text": f"- action: {cp.action}"},
                            {"type": "add", "text": f"+ action: {cp.action} -> {cp.description}"},
                        ],
                    },
                }
                for cp in raw_checkpoints
            ]
            audits = [
                {
                    "id": a.id,
                    "skill_name": a.symbol,
                    "version": 1,
                    "reason": f"Rule changed: {a.before} -> {a.after}",
                    "trading_mode": getattr(a, "trading_mode", "LIVE_HOURS"),
                    "created_at": a.created_at,
                }
                for a in session.scalars(select(RuleAudit).order_by(RuleAudit.id.desc()).limit(10))
            ]

        return {
            "changes": checkpoints,
            "files_changed": changed_files,
            "total_files": max(len(changed_files), len(checkpoints)),
            "checkpoints": checkpoints,
            "skill_revisions": audits,
        }

    return router
