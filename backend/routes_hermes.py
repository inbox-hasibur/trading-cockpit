"""Hermes Copilot & System Changes API Routes.

Decomposed from backend/main.py for modularity and clean routing.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from backend.chat import ChatRequest, ChatService
from backend.config import Settings
from backend.database import Database, HermesSkillRevision, HermesStateCheckpoint, portfolio_state


class CreateThreadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(default="New Conversation", max_length=100)


def build_hermes_router(database: Database, settings: Settings, chat: ChatService, broadcaster: Any) -> APIRouter:
    router = APIRouter()

    @router.post("/api/chat")
    async def chat_route(body: ChatRequest):
        res = await chat.respond(body)
        if res.get("agentic_action"):
            broadcaster.publish("agentic_action", res)
        return res

    @router.get("/api/hermes/conversations")
    def list_conversations():
        from backend.hermes.memory import HermesMemory
        with database.read() as session:
            memory = HermesMemory(session)
            return {"conversations": memory.list_threads()}

    @router.post("/api/hermes/conversations")
    def create_conversation(body: CreateThreadRequest):
        from backend.hermes.memory import HermesMemory
        with database.write() as session:
            memory = HermesMemory(session)
            thread = memory.get_or_create_thread(title=body.title)
            return {
                "id": thread.id,
                "title": thread.title,
                "created_at": thread.created_at,
                "updated_at": thread.updated_at,
                "message_count": 0,
            }

    @router.get("/api/hermes/conversations/{conversation_id}/messages")
    def conversation_messages(conversation_id: str):
        from backend.hermes.memory import HermesMemory
        with database.read() as session:
            memory = HermesMemory(session)
            return {"messages": memory.get_thread_messages(conversation_id)}

    @router.get("/api/system/changes")
    def system_changes():
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
                ("agent_loop.py", "backend/hermes"),
                ("stocknow_adapter.py", "backend/adapters"),
                ("CODEBASE_MAP.md", "documentation"),
            ]
            changed_files = [{"status": "M", "path": f"{f}/{n}", "name": n, "folder": f} for n, f in core_files]

        with database.read() as session:
            raw_checkpoints = list(session.scalars(select(HermesStateCheckpoint).order_by(HermesStateCheckpoint.id.desc()).limit(20)))
            checkpoints = [{
                "id": cp.id,
                "action": cp.action,
                "actor": getattr(cp, "actor", "Hermes Agent"),
                "description": cp.description,
                "date": cp.session_on.isoformat(),
                "created_at": cp.created_at,
                "diff": cp.diff_payload or {
                    "action": cp.action,
                    "actor": getattr(cp, "actor", "Hermes Agent"),
                    "summary": cp.description,
                    "diff_lines": [
                        {"type": "del", "text": f"- action: {cp.action}"},
                        {"type": "add", "text": f"+ action: {cp.action} -> {cp.description}"},
                    ],
                },
            } for cp in raw_checkpoints]
            skill_revs = [{
                "id": sr.id,
                "skill_name": sr.skill_name,
                "version": sr.version,
                "reason": sr.reason,
                "created_at": sr.created_at,
            } for sr in session.scalars(select(HermesSkillRevision).order_by(HermesSkillRevision.id.desc()).limit(10))]

        return {
            "changes": checkpoints,
            "files_changed": changed_files,
            "total_files": max(len(changed_files), len(checkpoints)),
            "checkpoints": checkpoints,
            "skill_revisions": skill_revs,
        }

    @router.get("/api/hermes/models")
    def hermes_models():
        with database.read() as session:
            state = portfolio_state(session)
            active = getattr(state, "active_model", settings.openrouter_model)
        available = [
            {"id": "xiaomi/mimo-v2.6-pro", "name": "Xiaomi MiMo-v2.6-Pro (Primary Brain)", "tier": 1},
            {"id": "xiaomi/mimo-v2.6-flash", "name": "Xiaomi MiMo-v2.6-Flash (Ultra Fast)", "tier": 1},
            {"id": "deepseek/deepseek-chat", "name": "DeepSeek V3 / 4.1 Flash (Deep Reasoning)", "tier": 1},
            {"id": "deepseek/deepseek-r1", "name": "DeepSeek R1 (Reasoning / Math)", "tier": 1},
            {"id": "meta-llama/llama-3.3-70b-instruct", "name": "Llama 3.3 70B (High Precision)", "tier": 1},
            {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet (Elite Quant)", "tier": 1},
            {"id": "google/gemini-3.1-flash-lite", "name": "Google Gemini 3.1 Flash-Lite (Fastest ~1.5s)", "tier": 2},
            {"id": "google/gemini-3.5-flash", "name": "Google Gemini 3.5 Flash (Balanced Analysis)", "tier": 2},
            {"id": "google/gemini-3.8-flash", "name": "Google Gemini 3.8 Flash (Latest Preview)", "tier": 2},
            {"id": "google/gemini-3.7-flash", "name": "Google Gemini 3.7 Flash (Hybrid Reasoning)", "tier": 2},
            {"id": "local-quant-brain", "name": "Local Deterministic Quant Brain ($0 Offline)", "tier": 3},
        ]
        if active and not any(m["id"] == active for m in available):
            available.insert(0, {"id": active, "name": f"{active} (Active)", "tier": 1})
        if settings.openrouter_model and not any(m["id"] == settings.openrouter_model for m in available):
            available.insert(1, {"id": settings.openrouter_model, "name": f"{settings.openrouter_model} (Configured)", "tier": 1})
        has_gemini = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or getattr(settings, "gemini_api_key", ""))
        is_direct_gemini = active.startswith("google/") or active.startswith("gemini")
        fallback_chain = [
            {"tier": 1, "name": "Primary Brain", "target": active, "status": "ACTIVE" if (settings.openrouter_api_key or (is_direct_gemini and has_gemini)) else "STANDBY"},
            {"tier": 2, "name": "1st Fallback", "target": "google/gemini-3.1-flash-lite", "status": "READY" if has_gemini else "OFFLINE"},
            {"tier": 3, "name": "2nd Fallback", "target": "Local Deterministic Quant Brain", "status": "ALWAYS AVAILABLE"},
        ]
        return {
            "active_model": active,
            "models": available,
            "fallback_chain": fallback_chain,
        }

    @router.post("/api/hermes/model")
    def set_hermes_model(payload: dict):
        new_model = str(payload.get("model", "")).strip()
        if not new_model:
            raise HTTPException(422, "Model id cannot be empty.")
        from backend.hermes.agent_loop import CheckpointManager
        with database.write() as session:
            state = portfolio_state(session)
            old_model = getattr(state, "active_model", settings.openrouter_model)
            state.active_model = new_model
            diff_payload = {
                "action": "UPDATE_MODEL",
                "actor": "Operator",
                "summary": f"Switched AI brain model to {new_model}",
                "before": {"active_model": old_model},
                "after": {"active_model": new_model},
                "diff_lines": [
                    {"type": "del", "text": f"- active_model: {old_model}"},
                    {"type": "add", "text": f"+ active_model: {new_model}"},
                ],
            }
            CheckpointManager.create_checkpoint(
                session,
                state,
                action="UPDATE_MODEL",
                description=f"Hermes AI Brain switched to {new_model}",
                diff_payload=diff_payload,
                actor="Operator",
            )
        broadcaster.publish("automation_config", {"active_model": new_model})
        return {
            "status": "ok",
            "active_model": new_model,
            "message": f"Hermes brain model successfully switched to {new_model}",
        }

    @router.post("/api/hermes/rollback")
    def rollback_checkpoint():
        from backend.hermes.agent_loop import CheckpointManager
        with database.write() as session:
            state = portfolio_state(session)
            result = CheckpointManager.rollback_last(session, state)
            broadcaster.publish("rollback", result)
            return result

    @router.get("/api/hermes/crons")
    def get_hermes_crons():
        from backend.hermes_os.cron_manager import CronManager
        with database.read() as session:
            jobs = CronManager.list_jobs(session)
            return {"crons": jobs, "total": len(jobs)}

    @router.post("/api/hermes/crons")
    def create_hermes_cron(payload: dict):
        from backend.hermes_os.cron_manager import CronManager
        instruction = payload.get("natural_instruction") or payload.get("instruction")
        name = payload.get("name")
        schedule_expr = payload.get("schedule_expr")
        action_type = payload.get("action_type")
        params = payload.get("params") or {}
        with database.write() as session:
            job = CronManager.schedule_task(
                session=session,
                instruction=instruction,
                schedule_expr=schedule_expr,
                name=name,
                action_type=action_type,
                params=params,
            )
            return {
                "status": "ok",
                "cron": {
                    "id": job.id,
                    "name": job.name,
                    "schedule_expr": job.schedule_expr,
                    "action_type": job.action_type,
                    "natural_instruction": job.natural_instruction,
                    "enabled": job.enabled,
                    "created_at": job.created_at,
                },
            }

    @router.delete("/api/hermes/crons/{job_id}")
    def delete_hermes_cron(job_id: str):
        from backend.hermes_os.cron_manager import CronManager
        with database.write() as session:
            ok = CronManager.delete_job(session, job_id)
            if not ok:
                raise HTTPException(404, f"Cron job '{job_id}' not found.")
            return {"status": "ok", "deleted_id": job_id}

    @router.post("/api/hermes/crons/{job_id}/toggle")
    def toggle_hermes_cron(job_id: str, payload: dict | None = None):
        from backend.hermes_os.cron_manager import CronManager
        enabled = payload.get("enabled") if payload else None
        with database.write() as session:
            toggled = CronManager.toggle_job(session, job_id, enabled=enabled)
            if not toggled:
                raise HTTPException(404, f"Cron job '{job_id}' not found.")
            return {"status": "ok", "job": toggled}

    @router.get("/api/hermes/state")
    def get_hermes_state():
        from backend.hermes_os.config import get_hermes_home
        from backend.hermes_os.cron_manager import CronManager
        from backend.hermes_os.skill_loader import SkillLoader
        home_dir = get_hermes_home()
        user_md_path = home_dir / "USER.md"
        memory_md_path = home_dir / "MEMORY.md"

        user_md_text = user_md_path.read_text(encoding="utf-8") if user_md_path.exists() else ""
        memory_md_text = memory_md_path.read_text(encoding="utf-8") if memory_md_path.exists() else ""

        loader = SkillLoader(home_dir)
        skills = [
            {
                "name": s.name,
                "filename": s.filename,
                "version": s.version,
                "description": s.description,
                "triggers": s.triggers,
                "tags": s.tags,
                "pitfalls": s.pitfalls,
                "steps": s.steps,
                "is_auto_learned": "auto-learned" in s.tags or s.filename.startswith("SKILL_auto_"),
            }
            for s in loader.list_skills()
        ]

        with database.read() as session:
            state = portfolio_state(session)
            active_model = getattr(state, "active_model", settings.openrouter_model)
            crons = CronManager.list_jobs(session)

        return {
            "user_md": user_md_text,
            "memory_md": memory_md_text,
            "skills": skills,
            "crons": crons,
            "active_model": active_model,
        }

    return router
