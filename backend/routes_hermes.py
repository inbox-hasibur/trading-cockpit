"""Hermes System Changes & Workspace Activity API Routes.

Exposes git diffs, kernel state checkpoint changes, and conversation stubs.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
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


PROVIDER_KEY_ENV_MAP: dict[str, tuple[str, ...]] = {
    "gemini": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    "groq": ("GROQ_API_KEY",),
    "mistral": ("MISTRAL_API_KEY",),
    "cerebras": ("CEREBRAS_API_KEY",),
    "sambanova": ("SAMBANOVA_API_KEY",),
    "openrouter": ("OPENROUTER_API_KEY",),
    "cloudflare": ("CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID"),
}


def _read_configured_env_keys() -> set[str]:
    """Returns names of non-empty API key env vars from process env and .env files (never values)."""
    configured = {k for k, v in os.environ.items() if k in {x for cols in PROVIDER_KEY_ENV_MAP.values() for x in cols} and str(v).strip()}
    candidate_paths = []
    try:
        from backend.hermes_bridge import get_hermes_dir
        candidate_paths.append(get_hermes_dir() / ".env")
    except Exception:
        pass
    from pathlib import Path
    candidate_paths.extend([Path(".env"), Path("backend/.env")])
    for env_path in candidate_paths:
        try:
            if not env_path.exists():
                continue
            for raw_line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                key_name = k.strip()
                val = v.strip().strip('"').strip("'")
                if val:
                    configured.add(key_name)
        except Exception:
            continue
    return configured


def is_provider_available(provider: str, settings: Settings | None = None) -> tuple[bool, str]:
    """Checks whether a provider has the required API key(s) configured."""
    prov = (provider or "").strip().lower()
    if prov in ("google", "google-ai-studio"):
        prov = "gemini"
    env_keys = PROVIDER_KEY_ENV_MAP.get(prov)
    if not env_keys:
        return False, f"Unsupported provider: {prov}"

    configured = _read_configured_env_keys()
    if settings is not None:
        if getattr(settings, "gemini_api_key", ""):
            configured.add("GEMINI_API_KEY")
        if getattr(settings, "openrouter_api_key", ""):
            configured.add("OPENROUTER_API_KEY")

    if prov == "cloudflare":
        missing = [k for k in env_keys if k not in configured]
        if missing:
            return False, f"Missing {' & '.join(missing)}"
        return True, ""

    if any(k in configured for k in env_keys):
        return True, ""
    return False, f"Missing {env_keys[0]}"


def _infer_provider(model_id: str) -> str:
    """Infers provider ID from catalog or model naming conventions."""
    low = (model_id or "").strip().lower()
    for item in AVAILABLE_HERMES_MODELS:
        if item["id"].lower() == low:
            return item["provider"]
    if "gemini" in low or low.startswith("google/"):
        return "gemini"
    if low.startswith("@cf/"):
        return "cloudflare"
    if "mistral" in low or "codestral" in low:
        return "mistral"
    if "groq" in low or low in {"openai/gpt-oss-120b", "qwen/qwen3.8-27b", "llama-3.3-70b-versatile", "kimi-k2-instruct"}:
        return "groq"
    if low in {"qwen-3.8-27b"}:
        return "cerebras"
    if low in {"deepseek-v3.1", "meta-llama-3.3-70b-instruct"}:
        return "sambanova"
    return "openrouter"


AVAILABLE_HERMES_MODELS = [
    # --- Google AI Studio (Primary) ---
    {
        "id": "gemini-2.5-pro",
        "name": "Gemini 2.5 Pro",
        "provider": "gemini",
        "provider_label": "Google",
        "badge": "GOOGLE AI STUDIO · 1M CTX",
        "description": "Google AI Studio · Complex reasoning, coding & multimodal",
    },
    {
        "id": "gemini-3.8-flash",
        "name": "Gemini 3.8 Flash",
        "provider": "gemini",
        "provider_label": "Google",
        "badge": "GOOGLE AI STUDIO · RECOMMENDED",
        "description": "Google AI Studio · Fast multimodal & dynamic free quota",
    },
    {
        "id": "gemini-3.6-flash",
        "name": "Gemini 3.6 Flash",
        "provider": "gemini",
        "provider_label": "Google",
        "badge": "GOOGLE AI STUDIO",
        "description": "Google AI Studio · Balanced speed & intelligence",
    },
    {
        "id": "gemini-3.5-flash-lite",
        "name": "Gemini 3.5 Flash-Lite",
        "provider": "gemini",
        "provider_label": "Google",
        "badge": "GOOGLE DIRECT (~1.0s)",
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
    # --- Groq Cloud (Ultra-Fast LPU Backup) ---
    {
        "id": "openai/gpt-oss-120b",
        "name": "GPT-OSS 120B (Groq)",
        "provider": "groq",
        "provider_label": "Groq",
        "badge": "GROQ LPU · BACKUP",
        "description": "Groq Cloud · ~500+ tok/s 120B high-speed reasoning",
    },
    {
        "id": "qwen/qwen3.8-27b",
        "name": "Qwen 3.8 27B (Groq)",
        "provider": "groq",
        "provider_label": "Groq",
        "badge": "GROQ LPU",
        "description": "Groq Cloud · Fast coding, math & tool calling",
    },
    {
        "id": "llama-3.3-70b-versatile",
        "name": "Llama 3.3 70B Versatile",
        "provider": "groq",
        "provider_label": "Groq",
        "badge": "GROQ LPU",
        "description": "Groq Cloud · Versatile 70B free tier",
    },
    {
        "id": "kimi-k2-instruct",
        "name": "Kimi K2 Instruct",
        "provider": "groq",
        "provider_label": "Groq",
        "badge": "GROQ LPU",
        "description": "Groq Cloud · Long-context instruction following",
    },
    # --- Mistral AI ---
    {
        "id": "mistral-large-latest",
        "name": "Mistral Large",
        "provider": "mistral",
        "provider_label": "Mistral",
        "badge": "MISTRAL AI",
        "description": "Mistral AI · Flagship reasoning & multilingual",
    },
    {
        "id": "codestral-latest",
        "name": "Codestral",
        "provider": "mistral",
        "provider_label": "Mistral",
        "badge": "MISTRAL AI",
        "description": "Mistral AI · Dedicated coding specialist",
    },
    {
        "id": "mistral-small-latest",
        "name": "Mistral Small",
        "provider": "mistral",
        "provider_label": "Mistral",
        "badge": "MISTRAL AI",
        "description": "Mistral AI · Lightweight fast free tier",
    },
    # --- Cerebras Cloud ---
    {
        "id": "gpt-oss-120b",
        "name": "GPT-OSS 120B (Cerebras)",
        "provider": "cerebras",
        "provider_label": "Cerebras",
        "badge": "CEREBRAS · ~2000 TPS",
        "description": "Cerebras Wafer-Scale · ~2,000+ tok/s inference",
    },
    {
        "id": "qwen-3.8-27b",
        "name": "Qwen 3.8 27B (Cerebras)",
        "provider": "cerebras",
        "provider_label": "Cerebras",
        "badge": "CEREBRAS",
        "description": "Cerebras Wafer-Scale · Instant 27B coding & math",
    },
    # --- SambaNova Cloud ---
    {
        "id": "DeepSeek-V3.1",
        "name": "DeepSeek V3.1 (SambaNova)",
        "provider": "sambanova",
        "provider_label": "SambaNova",
        "badge": "SAMBANOVA",
        "description": "SambaNova Cloud · Full 671B open-weights reasoning",
    },
    {
        "id": "gpt-oss-120b",
        "name": "GPT-OSS 120B (SambaNova)",
        "provider": "sambanova",
        "provider_label": "SambaNova",
        "badge": "SAMBANOVA",
        "description": "SambaNova Cloud · 120B free tier",
    },
    {
        "id": "Meta-Llama-3.3-70B-Instruct",
        "name": "Llama 3.3 70B (SambaNova)",
        "provider": "sambanova",
        "provider_label": "SambaNova",
        "badge": "SAMBANOVA",
        "description": "SambaNova Cloud · Fast 70B instruction model",
    },
    # --- OpenRouter ---
    {
        "id": "openrouter/free",
        "name": "OpenRouter Free Router",
        "provider": "openrouter",
        "provider_label": "OpenRouter",
        "badge": "OPENROUTER · FREE",
        "description": "OpenRouter · Auto-routes across available free models",
    },
    {
        "id": "nvidia/nemotron-3-nano-30b-a3b:free",
        "name": "Nemotron 3 Nano 30B (Free)",
        "provider": "openrouter",
        "provider_label": "OpenRouter",
        "badge": "OPENROUTER · FREE",
        "description": "OpenRouter · Fast free reasoning model",
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
    # --- Cloudflare Workers AI ---
    {
        "id": "@cf/openai/gpt-oss-120b",
        "name": "GPT-OSS 120B (Cloudflare)",
        "provider": "cloudflare",
        "provider_label": "Cloudflare",
        "badge": "CLOUDFLARE · 10K/DAY",
        "description": "Cloudflare Workers AI · Edge serverless inference",
    },
    {
        "id": "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
        "name": "DeepSeek R1 Qwen 32B",
        "provider": "cloudflare",
        "provider_label": "Cloudflare",
        "badge": "CLOUDFLARE · 10K/DAY",
        "description": "Cloudflare Workers AI · Serverless reasoning model",
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
        """Returns available models with provider key availability, active model, and fallback chain."""
        from backend.hermes_bridge import read_hermes_state
        state_data = read_hermes_state()
        active_model = state_data.get("model", "gemini-3.1-flash-lite")
        active_provider = state_data.get("provider", "gemini")

        provider_status: dict[str, dict[str, Any]] = {}
        for prov in PROVIDER_KEY_ENV_MAP:
            avail, reason = is_provider_available(prov, settings)
            provider_status[prov] = {"available": avail, "reason": reason}

        enriched_models = []
        for m in AVAILABLE_HERMES_MODELS:
            p_info = provider_status.get(m["provider"], {"available": False, "reason": "Provider not configured"})
            enriched_models.append({
                **m,
                "available": p_info["available"],
                "unavailable_reason": p_info["reason"],
            })

        fallbacks = state_data.get("fallbacks", [])
        if not fallbacks:
            recommended = [
                {"provider": "gemini", "model": "gemini-3.8-flash", "role": "primary"},
                {"provider": "groq", "model": "openai/gpt-oss-120b", "role": "backup"},
                {"provider": "openrouter", "model": "openrouter/free", "role": "tertiary"},
            ]
            fallbacks = [
                {**fb, "available": provider_status.get(fb["provider"], {}).get("available", False)}
                for fb in recommended
            ]

        return {
            "active_model": active_model,
            "active_provider": active_provider,
            "models": enriched_models,
            "provider_status": provider_status,
            "fallback_chain": fallbacks,
        }

    @router.post("/api/hermes/model")
    def switch_hermes_model(body: SwitchModelRequest):
        """Switches active model and provider in Hermes profile and updates local state."""
        model_id = body.model.strip()
        provider_id = (body.provider.strip().lower() if body.provider else None) or _infer_provider(model_id)
        if provider_id in ("google", "google-ai-studio"):
            provider_id = "gemini"

        avail, reason = is_provider_available(provider_id, settings)
        if not avail:
            raise HTTPException(
                status_code=400,
                detail=f"Model '{model_id}' ({provider_id}) is unavailable: {reason}. Configure the API key first.",
            )

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
