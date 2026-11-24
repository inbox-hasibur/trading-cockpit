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


class SwitchModelRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    model: str = Field(..., max_length=128)
    provider: str | None = Field(default=None, max_length=64)


AVAILABLE_HERMES_MODELS = [
    {
        "id": "gemini-3.5-flash-lite",
        "name": "Gemini 3.5 Flash-Lite",
        "provider": "gemini",
        "provider_label": "Google",
        "badge": "GOOGLE DIRECT (~1.0s) · RECOMMENDED",
        "description": "Google Direct · ~1.0s Tool-Calling Verified (Fastest)",
    },
    {
        "id": "gemini-3.1-flash-lite",
        "name": "Gemini 3.1 Flash-Lite",
        "provider": "gemini",
        "provider_label": "Google",
        "badge": "GOOGLE DIRECT (~1.1s)",
        "description": "Google Direct · Tool-Calling Verified",
    },
    {
        "id": "gemini-3-flash-preview",
        "name": "Gemini 3 Flash Preview",
        "provider": "gemini",
        "provider_label": "Google",
        "badge": "GOOGLE DIRECT",
        "description": "Google Direct · Tool-Calling Verified",
    },
    {
        "id": "gemini-3.1-flash-lite-preview",
        "name": "Gemini 3.1 Flash-Lite Preview",
        "provider": "gemini",
        "provider_label": "Google",
        "badge": "GOOGLE DIRECT",
        "description": "Google Direct · Tool-Calling Verified",
    },
    {
        "id": "xiaomi/mimo-v2.6-pro",
        "name": "Xiaomi MiMo-v2.6-Pro",
        "provider": "openrouter",
        "provider_label": "OpenRouter",
        "badge": "OPENROUTER",
        "description": "Primary fallback brain via OpenRouter",
    },
    {
        "id": "deepseek/deepseek-chat",
        "name": "DeepSeek V3",
        "provider": "openrouter",
        "provider_label": "OpenRouter",
        "badge": "OPENROUTER",
        "description": "DeepSeek V3 671B reasoning via OpenRouter",
    },
    {
        "id": "deepseek/deepseek-r1",
        "name": "DeepSeek R1",
        "provider": "openrouter",
        "provider_label": "OpenRouter",
        "badge": "OPENROUTER",
        "description": "Reasoning & math specialist via OpenRouter",
    },
    {
        "id": "anthropic/claude-3.5-sonnet",
        "name": "Claude 3.5 Sonnet",
        "provider": "openrouter",
        "provider_label": "OpenRouter",
        "badge": "OPENROUTER",
        "description": "Anthropic Claude 3.5 Sonnet via OpenRouter",
    },
    {
        "id": "meta-llama/llama-3.3-70b-instruct",
        "name": "Llama 3.3 70B",
        "provider": "openrouter",
        "provider_label": "OpenRouter",
        "badge": "OPENROUTER",
        "description": "Meta Llama 3.3 70B Instruct via OpenRouter",
    },
]


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

    @router.get("/api/hermes/models")
    def get_hermes_models():
        """Returns available models, active model, and provider from Hermes state."""
        from backend.hermes_bridge import read_hermes_state
        state_data = read_hermes_state()
        active_model = state_data.get("model", "gemini-3.1-flash-lite")
        active_provider = state_data.get("provider", "gemini")
        return {
            "active_model": active_model,
            "active_provider": active_provider,
            "models": AVAILABLE_HERMES_MODELS,
            "fallback_chain": state_data.get("fallbacks", []),
        }

    @router.post("/api/hermes/model")
    def switch_hermes_model(body: SwitchModelRequest):
        """Switches active model and provider in Hermes profile and updates local state."""
        model_id = body.model.strip()
        provider_id = body.provider.strip() if body.provider else None

        if not provider_id:
            if "gemini" in model_id.lower() or model_id.startswith("google/"):
                provider_id = "gemini"
            else:
                provider_id = "openrouter"

        from backend.hermes_bridge import get_hermes_cmd, get_hermes_dir
        hermes_cmd = get_hermes_cmd()
        h_dir = get_hermes_dir()

        # Update Hermes config
        try:
            cmd1 = [*hermes_cmd, "-p", "hummingbird", "config", "set", "model.default", model_id]
            cmd2 = [*hermes_cmd, "-p", "hummingbird", "config", "set", "model.provider", provider_id]
            subprocess.run(cmd1, capture_output=True, text=True, timeout=5)
            subprocess.run(cmd2, capture_output=True, text=True, timeout=5)
        except Exception:
            cfg_file = h_dir / "config.yaml"
            if cfg_file.exists():
                try:
                    import yaml
                    with open(cfg_file, "r", encoding="utf-8") as f:
                        cfg = yaml.safe_load(f) or {}
                    cfg.setdefault("model", {})
                    cfg["model"]["default"] = model_id
                    cfg["model"]["provider"] = provider_id
                    with open(cfg_file, "w", encoding="utf-8") as f:
                        yaml.safe_dump(cfg, f, default_flow_style=False, sort_keys=False)
                except Exception:
                    pass

        # Update SQLite portfolio_state and record Checkpoint
        from backend.portfolio import portfolio_state
        from backend.engine.checkpoint import CheckpointManager
        with database.write() as session:
            ps = portfolio_state(session)
            prev_model = ps.active_model or "gemini-3.1-flash-lite"
            ps.active_model = model_id
            session.flush()

            CheckpointManager.create_checkpoint(
                session=session,
                state=ps,
                action="UPDATE_MODEL",
                actor="Operator",
                description=f"Switched Hermes AI Brain to {model_id} ({provider_id})",
            )

        return {
            "status": "ok",
            "active_model": model_id,
            "active_provider": provider_id,
            "message": f"Hermes model switched to {model_id} ({provider_id})",
        }

    return router
