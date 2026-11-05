"""Authentication & Live Telemetry Settings API Routes.

Decomposed from backend/main.py for modularity and clean routing.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from backend.config import DHAKA, Settings
from backend.database import ChatBudget, Database, HermesSessionMemory, portfolio_state


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str
    password: str


class KeysSettingsRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    openrouter_key: str | None = None
    gemini_key: str | None = None
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    daily_call_limit: int | None = None


# Session token tracker for local auth
active_sessions: set[str] = set()


def build_auth_settings_router(database: Database, settings: Settings, broadcaster: Any) -> APIRouter:
    router = APIRouter()

    @router.post("/api/auth/login")
    def login(body: LoginRequest):
        if body.username == settings.operator_username and body.password == settings.operator_password:
            token = f"hb-sess-{uuid4().hex}"
            active_sessions.add(token)
            return {
                "status": "ok",
                "token": token,
                "user": {
                    "username": settings.operator_username,
                    "name": settings.operator_name,
                    "portfolio": settings.operator_portfolio,
                    "authenticated": True,
                },
            }
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    @router.post("/api/auth/logout")
    def logout(request: Request):
        auth_hdr = request.headers.get("Authorization", "")
        token = auth_hdr.replace("Bearer ", "").strip()
        active_sessions.discard(token)
        return {"status": "ok", "authenticated": False}

    @router.get("/api/auth/session")
    def auth_session(request: Request):
        auth_hdr = request.headers.get("Authorization", "")
        token = auth_hdr.replace("Bearer ", "").strip()
        is_authenticated = bool(token and token in active_sessions) or not settings.cockpit_api_token
        return {
            "authenticated": is_authenticated,
            "user": {
                "username": settings.operator_username,
                "name": settings.operator_name,
                "portfolio": settings.operator_portfolio,
                "session_active": is_authenticated,
            },
        }

    @router.get("/api/settings/keys")
    def get_api_keys():
        def mask_single(s: str) -> str:
            if not s:
                return ""
            if len(s) <= 8:
                return "****"
            return f"{s[:4]}...{s[-4:]}"

        def mask(s: str) -> str:
            if not s:
                return ""
            parts = [k.strip() for k in s.replace("\n", ",").replace(";", ",").split(",") if k.strip()]
            if len(parts) > 1:
                return f"{', '.join(mask_single(p) for p in parts)} ({len(parts)} keys active)"
            return mask_single(parts[0]) if parts else ""

        with database.read() as session:
            state = portfolio_state(session)
            active_model = getattr(state, "active_model", settings.openrouter_model)
            day = datetime.now(DHAKA).date()
            budget = session.get(ChatBudget, day)
            used_calls = budget.calls if budget else 0
            total_turns = len(list(session.scalars(select(HermesSessionMemory))))

        gemini_val = os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip() or settings.gemini_api_key

        return {
            "openrouter_key_masked": mask(settings.openrouter_api_key),
            "openrouter_configured": bool(settings.openrouter_api_key),
            "gemini_key_masked": mask(gemini_val),
            "gemini_configured": bool(gemini_val),
            "telegram_bot_token_masked": mask(settings.telegram_bot_token),
            "telegram_chat_id_masked": mask(settings.telegram_chat_id),
            "daily_call_limit": settings.chat_daily_call_limit,
            "daily_calls_used": used_calls,
            "calls_remaining": max(0, settings.chat_daily_call_limit - used_calls),
            "active_model": active_model,
            "total_chat_turns": total_turns,
            "guardrail_status": "ZERO-SECRET-READ ACTIVE",
            "linked_portfolio": settings.operator_portfolio,
        }

    @router.post("/api/settings/keys")
    def update_api_keys(body: KeysSettingsRequest):
        from backend.hermes.agent_loop import CheckpointManager
        updated_fields = []
        if body.openrouter_key is not None:
            clean_val = body.openrouter_key.strip()
            object.__setattr__(settings, "openrouter_api_key", clean_val)
            os.environ["OPENROUTER_API_KEY"] = clean_val
            updated_fields.append("OpenRouter API Key")
        if body.gemini_key is not None:
            clean_val = body.gemini_key.strip()
            object.__setattr__(settings, "gemini_api_key", clean_val)
            os.environ["GEMINI_API_KEY"] = clean_val
            updated_fields.append("Google Gemini API Key")
        if body.telegram_bot_token is not None:
            clean_val = body.telegram_bot_token.strip()
            object.__setattr__(settings, "telegram_bot_token", clean_val)
            os.environ["TELEGRAM_BOT_TOKEN"] = clean_val
            updated_fields.append("Telegram Bot Token")
        if body.telegram_chat_id is not None:
            clean_val = body.telegram_chat_id.strip()
            object.__setattr__(settings, "telegram_chat_id", clean_val)
            os.environ["TELEGRAM_CHAT_ID"] = clean_val
            updated_fields.append("Telegram Chat ID")
        if body.daily_call_limit is not None and 1 <= body.daily_call_limit <= 1000:
            object.__setattr__(settings, "chat_daily_call_limit", body.daily_call_limit)
            updated_fields.append(f"Daily Call Limit ({body.daily_call_limit})")

        with database.write() as session:
            state = portfolio_state(session)
            summary = f"Updated API keys & quotas: {', '.join(updated_fields)}" if updated_fields else "API keys verified"
            diff_payload = {
                "action": "UPDATE_API_KEYS",
                "actor": "Operator",
                "summary": summary,
                "diff_lines": [{"type": "add", "text": f"+ {f}"} for f in updated_fields],
            }
            CheckpointManager.create_checkpoint(
                session, state, action="UPDATE_API_KEYS",
                description=summary, diff_payload=diff_payload, actor="Operator",
            )

        broadcaster.publish("automation_config", {"keys_updated": True})
        return {
            "status": "ok",
            "message": f"Successfully updated: {', '.join(updated_fields)}" if updated_fields else "No changes",
            "updated_fields": updated_fields,
        }

    return router
