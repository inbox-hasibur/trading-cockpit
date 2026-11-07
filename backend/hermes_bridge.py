"""Thin HTTP/SSE bridge to the running official Nous Research Hermes Agent.

Proxies streaming chat turns and inspection endpoints directly to the Hermes runtime
with no business logic.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, AsyncGenerator, Optional

import httpx
import yaml
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("hermes.bridge")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


def get_hermes_dir(profile: str = "hummingbird") -> Path:
    """Returns the Hermes profile directory (hummingbird profile if available, else hermes home)."""
    target_profile = os.environ.get("HERMES_PROFILE") or profile
    if "HERMES_HOME" in os.environ:
        home_path = Path(os.environ["HERMES_HOME"])
        prof_path = home_path / "profiles" / target_profile
        if prof_path.exists():
            return prof_path
        if home_path.name == target_profile:
            return home_path
        return home_path
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app:
        hb_profile = Path(local_app) / "hermes" / "profiles" / target_profile
        if hb_profile.exists():
            return hb_profile
        base = Path(local_app) / "hermes"
        if base.exists():
            return base
    return Path.home() / ".hermes"


def get_hermes_bin() -> str:
    """Returns path to the hermes executable, preferring vendor/hermes-agent editable in .venv."""
    venv_exe = WORKSPACE_ROOT / ".venv" / "Scripts" / ("hermes.exe" if os.name == "nt" else "hermes")
    if venv_exe.exists():
        return str(venv_exe)
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app:
        bin_exe = Path(local_app) / "hermes" / "bin" / ("hermes.exe" if os.name == "nt" else "hermes")
        if bin_exe.exists():
            return str(bin_exe)
    return "hermes"


class BridgeChatRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = None


async def stream_hermes_chat(message: str, session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
    """Streams SSE events from running Hermes gateway API server."""
    gateway_url = os.environ.get("HERMES_GATEWAY_URL", "http://127.0.0.1:8642")
    api_key = os.environ.get("API_SERVER_KEY") or "hb-hermes-local-key-2026"

    # Check Hermes Gateway API Server (/v1/chat/completions)
    gateway_connected = False
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            health = await client.get(f"{gateway_url}/health")
            if health.status_code == 200:
                gateway_connected = True
    except Exception:
        gateway_connected = False

    if not gateway_connected:
        error_msg = "Hermes is starting or stopped (Gateway offline at http://127.0.0.1:8642)."
        yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"
        return

    # Stream turns through Gateway API
    try:
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        payload = {
            "model": "hermes",
            "messages": [{"role": "user", "content": message}],
            "stream": True,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", f"{gateway_url}/v1/chat/completions", json=payload, headers=headers) as resp:
                if resp.status_code != 200:
                    err_body = await resp.aread()
                    err_msg = err_body.decode("utf-8", errors="replace")
                    yield f"data: {json.dumps({'type': 'error', 'error': f'Gateway error ({resp.status_code}): {err_msg}'})}\n\n"
                    return

                full_reply = []
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    chunk_str = line[6:].strip()
                    if chunk_str == "[DONE]":
                        break
                    try:
                        parsed = json.loads(chunk_str)
                        delta = parsed.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            full_reply.append(content)
                            yield f"data: {json.dumps({'type': 'text', 'text': content})}\n\n"
                    except Exception:
                        continue
                yield f"data: {json.dumps({'type': 'done', 'text': ''.join(full_reply)})}\n\n"
    except Exception as exc:
        logger.error("Hermes gateway stream failed: %s", exc)
        yield f"data: {json.dumps({'type': 'error', 'error': f'Hermes is starting or stopped ({exc})'})}\n\n"


def read_hermes_state() -> dict[str, Any]:
    """Reads skills, memory (USER.md / MEMORY.md), active model, and cron jobs from Hermes."""
    h_dir = get_hermes_dir()

    # 1. Config, Active Model & Fallbacks
    cfg_path = h_dir / "config.yaml"
    model_name = "gemini-3.1-flash-lite"
    provider_name = "gemini"
    fallbacks: list[dict[str, Any]] = []
    if cfg_path.exists():
        try:
            cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
            model_cfg = cfg.get("model", {})
            if isinstance(model_cfg, dict):
                model_name = model_cfg.get("default", model_name)
                provider_name = model_cfg.get("provider", provider_name)
            elif isinstance(model_cfg, str):
                model_name = model_cfg
                provider_name = "custom"

            # Hermes fallback provider chain
            raw_fbs = cfg.get("fallback_providers") or cfg.get("fallback_model") or []
            if isinstance(raw_fbs, dict):
                raw_fbs = [raw_fbs]
            if isinstance(raw_fbs, list):
                for fb in raw_fbs:
                    if isinstance(fb, dict):
                        fallbacks.append({
                            "provider": fb.get("provider", "unknown"),
                            "model": fb.get("model") or fb.get("default", "unknown"),
                            "base_url": fb.get("base_url"),
                        })
        except Exception as exc:
            logger.debug("Hermes config read notice: %s", exc)

    # 1b. Last turn execution info from session_model_usage
    last_turn = {
        "provider": provider_name,
        "model": model_name,
        "timestamp": None,
    }
    state_db_path = h_dir / "state.db"
    if not state_db_path.exists():
        local_app = os.environ.get("LOCALAPPDATA")
        if local_app:
            state_db_path = Path(local_app) / "hermes" / "state.db"
    if state_db_path.exists():
        try:
            import sqlite3
            from datetime import datetime, timezone
            conn = sqlite3.connect(state_db_path)
            row = conn.execute(
                "SELECT model, billing_provider, last_seen FROM session_model_usage "
                "WHERE model IS NOT NULL AND model != '' "
                "ORDER BY last_seen DESC LIMIT 1"
            ).fetchone()
            if row:
                last_turn["model"] = row[0]
                last_turn["provider"] = row[1] or provider_name
                if row[2]:
                    last_turn["timestamp"] = datetime.fromtimestamp(row[2], timezone.utc).isoformat()
            conn.close()
        except Exception as exc:
            logger.debug("Hermes session_model_usage query notice: %s", exc)

    # 2. Memories (USER.md & MEMORY.md)
    user_md_path = h_dir / "memories" / "USER.md"
    memory_md_path = h_dir / "memories" / "MEMORY.md"
    user_md = user_md_path.read_text(encoding="utf-8") if user_md_path.exists() else ""
    memory_md = memory_md_path.read_text(encoding="utf-8") if memory_md_path.exists() else ""
    if not user_md and h_dir.parent.name == "profiles":
        root_user = h_dir.parent.parent / "memories" / "USER.md"
        if root_user.exists():
            user_md = root_user.read_text(encoding="utf-8")
    if not memory_md and h_dir.parent.name == "profiles":
        root_mem = h_dir.parent.parent / "memories" / "MEMORY.md"
        if root_mem.exists():
            memory_md = root_mem.read_text(encoding="utf-8")

    # 3. Scheduled Cron Jobs
    jobs_file = h_dir / "cron" / "jobs.json"
    crons = []
    if jobs_file.exists():
        try:
            jobs_data = json.loads(jobs_file.read_text(encoding="utf-8"))
            raw_jobs = jobs_data.get("jobs", [])
            for j in raw_jobs:
                crons.append({
                    "id": j.get("id"),
                    "name": j.get("name") or j.get("id"),
                    "schedule_expr": j.get("schedule_display") or j.get("schedule", {}).get("display", ""),
                    "state": j.get("state", "scheduled"),
                    "enabled": bool(j.get("enabled", True)),
                    "last_status": j.get("last_status"),
                    "last_run": j.get("last_run_at"),
                    "next_run": j.get("next_run_at"),
                    "prompt": j.get("prompt"),
                    "timezone": j.get("timezone", "Asia/Dhaka"),
                })
        except Exception as exc:
            logger.debug("Hermes cron read notice: %s", exc)

    # 4. Skills (Plugin skills & Local Hermes skills)
    skills = []
    # (a) Humming Bird plugin skills
    plugin_skills_dir = WORKSPACE_ROOT / "plugins" / "humming_bird" / "skills"
    if plugin_skills_dir.exists():
        for s_dir in sorted(plugin_skills_dir.iterdir()):
            sk_file = s_dir / "SKILL.md"
            if sk_file.is_file():
                meta = _extract_skill_meta(sk_file)
                skills.append({
                    "name": s_dir.name,
                    "title": meta.get("name", s_dir.name),
                    "description": meta.get("description", ""),
                    "version": meta.get("version", "1.0.0"),
                    "tags": meta.get("tags", []),
                    "source": "humming_bird plugin",
                    "is_auto_learned": False,
                })

    # (b) Hermes skills (profile skills + hermes home skills)
    search_skill_dirs = [h_dir / "skills"]
    if h_dir.parent.name == "profiles" and (h_dir.parent.parent / "skills").exists():
        search_skill_dirs.append(h_dir.parent.parent / "skills")

    for s_root in search_skill_dirs:
        if not s_root.exists():
            continue
        for sk_file in s_root.rglob("SKILL.md"):
            # Avoid repeating plugin skills, hub bundle dirs, or locks
            if ".hub" in sk_file.parts or "plugins" in sk_file.parts or ".locks" in sk_file.parts:
                continue
            name = sk_file.parent.name
            if any(s["name"] == name for s in skills):
                continue
            meta = _extract_skill_meta(sk_file)
            skills.append({
                "name": name,
                "title": meta.get("name", name),
                "description": meta.get("description", ""),
                "version": meta.get("version", "1.0.0"),
                "tags": meta.get("tags", []),
                "source": "profile skill" if s_root == h_dir / "skills" else "hermes skill",
                "is_auto_learned": True,
            })

    return {
        "model": model_name,
        "provider": provider_name,
        "primary_model": model_name,
        "primary_provider": provider_name,
        "fallbacks": fallbacks,
        "last_turn": last_turn,
        "skills": skills,
        "user_md": user_md,
        "memory_md": memory_md,
        "crons": crons,
        "profile": h_dir.name,
    }


def _extract_skill_meta(path: Path) -> dict[str, Any]:
    """Extracts frontmatter metadata from a SKILL.md file."""
    meta: dict[str, Any] = {"tags": []}
    try:
        content = path.read_text(encoding="utf-8")
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                raw_yaml = yaml.safe_load(parts[1]) or {}
                if isinstance(raw_yaml, dict):
                    meta["name"] = raw_yaml.get("name", path.parent.name)
                    meta["description"] = raw_yaml.get("description", "")
                    meta["version"] = str(raw_yaml.get("version", "1.0.0"))
                    hermes_meta = raw_yaml.get("metadata", {}).get("hermes", {})
                    meta["tags"] = hermes_meta.get("tags", [])
    except Exception:
        pass
    return meta


def run_hermes_cron_cmd(*args: str) -> dict[str, Any]:
    """Runs a hermes cron sub-command synchronously on the hummingbird profile."""
    bin_exe = get_hermes_bin()
    cmd = [bin_exe, "-p", "hummingbird", "cron", *args]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return {
            "success": proc.returncode == 0,
            "output": proc.stdout.strip(),
            "error": proc.stderr.strip() if proc.returncode != 0 else None,
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def build_hermes_bridge_router(database: Any = None, settings: Any = None, broadcaster: Any = None) -> APIRouter:
    """Builds and returns the Hermes bridge router."""
    router = APIRouter(tags=["hermes-bridge"])

    @router.post("/api/hermes/bridge/chat")
    async def bridge_chat(body: BridgeChatRequest):
        """Streaming chat endpoint proxying to running Hermes."""
        return StreamingResponse(
            stream_hermes_chat(body.message, session_id=body.session_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @router.get("/api/hermes/bridge/state")
    @router.get("/api/hermes/state")
    def bridge_state():
        """Returns active model, skills, memory preview, and cron jobs directly from Hermes."""
        return read_hermes_state()

    @router.post("/api/hermes/bridge/cron/{job_id}/pause")
    def bridge_cron_pause(job_id: str):
        """Pauses a scheduled Hermes cron job."""
        res = run_hermes_cron_cmd("pause", job_id)
        if not res.get("success"):
            raise HTTPException(400, res.get("error") or "Failed to pause cron job.")
        return {"status": "ok", "message": res.get("output")}

    @router.post("/api/hermes/bridge/cron/{job_id}/resume")
    def bridge_cron_resume(job_id: str):
        """Resumes a paused Hermes cron job."""
        res = run_hermes_cron_cmd("resume", job_id)
        if not res.get("success"):
            raise HTTPException(400, res.get("error") or "Failed to resume cron job.")
        return {"status": "ok", "message": res.get("output")}

    @router.delete("/api/hermes/bridge/cron/{job_id}")
    def bridge_cron_delete(job_id: str):
        """Deletes a scheduled Hermes cron job."""
        res = run_hermes_cron_cmd("remove", job_id)
        if not res.get("success"):
            raise HTTPException(400, res.get("error") or "Failed to delete cron job.")
        return {"status": "ok", "message": res.get("output")}

    return router

