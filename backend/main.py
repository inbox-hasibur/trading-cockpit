"""One-process local cockpit. Start with: uvicorn backend.main:app --host 127.0.0.1."""

from __future__ import annotations

import asyncio
import hmac
import json
from contextlib import asynccontextmanager
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, StrictBool
from sqlalchemy import select
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.adapters.stocknow_adapter import StockNowAdapter
from backend.chat import ChatRequest, ChatService
from backend.config import ROOT, VERSION, Settings
from backend.database import CustomRule, Database, RuleAudit, portfolio_state
from backend.engine.auto_trader import AutomationPaused, AutoTrader
from backend.engine.money import ZERO
from backend.market_map import build_market_map_payload
from backend.portfolio import build_snapshot, rule_view
from backend.seed import seed_demo


class PauseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    paused: StrictBool


class AutomationConfigRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    automation_enabled: StrictBool
    ingestion_mode: Literal["BACKGROUND_POLLING", "ONSCREEN_LIVE", "SIDE_BY_SIDE_LIVE"]
    polling_interval_sec: int = Field(default=120, ge=30, le=300)


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


class CreateThreadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(default="New Conversation", max_length=100)


class AdvanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario: Literal["NORMAL", "RALLY", "PULLBACK", "CRASH", "RECOVERY"] = "NORMAL"


class AllocationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    buy_allocation_pct: Decimal = Field(ge=0, le=100, max_digits=5, decimal_places=2)
    enabled: StrictBool


class EventBroadcaster:
    def __init__(self):
        self._subscribers: set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=50)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        self._subscribers.discard(queue)

    def publish(self, event_type: str, data: dict):
        for queue in list(self._subscribers):
            try:
                queue.put_nowait({"event": event_type, "data": data})
            except Exception:
                pass


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    database = Database(settings.database_url)
    trader = AutoTrader(database, settings)
    chat = ChatService(database, settings)
    broadcaster = EventBroadcaster()

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        database.create_schema()
        with database.write() as session:
            seed_demo(session, settings)
        try:
            yield
        finally:
            database.engine.dispose()

    app = FastAPI(
        title="Humming Bird · Paper Trading Cockpit", version=VERSION,
        description="Demo-only deterministic trading rules. No live feed or external orders.",
        lifespan=lifespan, redoc_url=None,
    )
    app.state.database = database
    app.state.settings = settings
    app.state.trader = trader
    app.state.chat = chat
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.trusted_hosts))

    @app.middleware("http")
    async def local_security(request: Request, call_next):
        is_api = request.url.path.startswith("/api/")
        if is_api and request.url.path != "/api/health":
            origin = request.headers.get("origin")
            expected_origin = str(request.base_url).rstrip("/")
            if (
                origin and origin.lower().rstrip("/") != expected_origin.lower()
            ) or request.headers.get("sec-fetch-site") == "cross-site":
                return JSONResponse({"detail": "Cross-origin API access is not allowed."}, status_code=403)
            if settings.cockpit_api_token:
                supplied = request.headers.get("authorization", "")
                expected = f"Bearer {settings.cockpit_api_token}"
                if not hmac.compare_digest(supplied.encode(), expected.encode()):
                    return JSONResponse(
                        {"detail": "A valid cockpit API token is required."}, status_code=401,
                        headers={"WWW-Authenticate": "Bearer"},
                    )
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["X-Frame-Options"] = "DENY"
        # The cockpit is entirely local. FastAPI's optional Swagger page loads
        # its standard CDN assets and needs a separate, documentation-only CSP.
        if request.url.path.startswith("/docs"):
            policy = (
                "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "
                "connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
            )
        else:
            policy = (
                "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
                "connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
            )
        response.headers["Content-Security-Policy"] = policy
        if is_api:
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/api/health")
    def health():
        return {"status": "ok", "version": VERSION, "mode": "DEMO", "data_source": "SYNTHETIC"}

    @app.get("/api/portfolio")
    def portfolio():
        return build_snapshot(database, settings)

    @app.post("/api/automation/cycle")
    def cycle(idempotency_key: Annotated[UUID | None, Header(alias="Idempotency-Key")] = None):
        try:
            result = trader.run_cycle(str(idempotency_key) if idempotency_key else None)
            broadcaster.publish("cycle", result)
            return result
        except AutomationPaused as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/automation/pause")
    def pause(body: PauseRequest):
        with database.write() as session:
            state = portfolio_state(session)
            state.paused = body.paused
            state.automation_enabled = not body.paused
            res = {"paused": state.paused, "automation_enabled": state.automation_enabled, "mode": "DEMO"}
            broadcaster.publish("pause", res)
            return res

    @app.post("/api/automation/config")
    def automation_config(body: AutomationConfigRequest):
        with database.write() as session:
            state = portfolio_state(session)
            state.automation_enabled = body.automation_enabled
            state.paused = not body.automation_enabled
            state.ingestion_mode = body.ingestion_mode
            state.polling_interval_sec = body.polling_interval_sec
            adapter = StockNowAdapter()
            adapter_status = adapter.get_adapter_status(state.ingestion_mode, state.polling_interval_sec)
            res = {
                "automation_enabled": state.automation_enabled,
                "paused": state.paused,
                "ingestion_mode": state.ingestion_mode,
                "polling_interval_sec": state.polling_interval_sec,
                "adapter": adapter_status,
                "mode": "DEMO",
            }
            broadcaster.publish("automation_config", res)
            return res

    @app.post("/api/demo/advance")
    def advance(body: AdvanceRequest):
        res = trader.advance_demo(body.scenario)
        broadcaster.publish("advance", res)
        scenario_bias = {
            "NORMAL": Decimal("0"),
            "RALLY": Decimal("1.5"),
            "PULLBACK": Decimal("-1.2"),
            "CRASH": Decimal("-3.5"),
            "RECOVERY": Decimal("1.8"),
        }.get(body.scenario, Decimal("0"))
        broadcaster.publish("market_map", build_market_map_payload(scenario_bias=scenario_bias))
        return res

    @app.get("/api/market/map")
    def market_map_endpoint():
        return build_market_map_payload()

    @app.patch("/api/companies/{symbol}/allocation")
    def allocation(symbol: str, body: AllocationRequest):
        with database.write() as session:
            state = portfolio_state(session)
            rule = session.get(CustomRule, symbol.upper())
            if rule is None:
                raise HTTPException(status_code=404, detail="Unknown demo company.")
            other_allocations = sum(session.scalars(select(CustomRule.buy_allocation_pct).where(
                CustomRule.symbol != rule.symbol
            )), ZERO)
            if other_allocations + body.buy_allocation_pct > 100:
                raise HTTPException(status_code=422, detail="Combined company allocations cannot exceed 100%.")
            if rule.buy_allocation_pct == body.buy_allocation_pct and rule.enabled == body.enabled:
                return {"symbol": rule.symbol, "rule": rule_view(rule), "changed": False}
            before = rule_view(rule)
            rule.buy_allocation_pct = body.buy_allocation_pct
            rule.enabled = body.enabled
            after = rule_view(rule)
            session.add(RuleAudit(
                symbol=rule.symbol, before=before, after=after, session_on=state.clock_date,
            ))
            state.rules_revision += 1
            res = {"symbol": rule.symbol, "rule": after, "changed": True}
            broadcaster.publish("allocation", res)
            return res

    @app.post("/api/chat")
    async def chat_route(body: ChatRequest):
        res = await chat.respond(body)
        if res.get("agentic_action"):
            broadcaster.publish("agentic_action", res)
        return res

    @app.get("/api/hermes/conversations")
    def list_conversations():
        from backend.hermes.memory import HermesMemory
        with database.read() as session:
            memory = HermesMemory(session)
            return {"conversations": memory.list_threads()}

    @app.post("/api/hermes/conversations")
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

    @app.get("/api/hermes/conversations/{conversation_id}/messages")
    def conversation_messages(conversation_id: str):
        from backend.hermes.memory import HermesMemory
        with database.read() as session:
            memory = HermesMemory(session)
            return {"messages": memory.get_thread_messages(conversation_id)}

    @app.get("/api/system/changes")
    def system_changes():
        import subprocess
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
            from backend.database import HermesSkillRevision, HermesStateCheckpoint
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

    @app.get("/api/hermes/models")
    def hermes_models():
        import os
        from backend.database import portfolio_state
        with database.read() as session:
            state = portfolio_state(session)
            active = getattr(state, "active_model", settings.openrouter_model)
        available = [
            {"id": "xiaomi/mimo-v2-flash", "name": "Xiaomi MiMo-v2-Flash (Ultra Fast / Free)", "tier": 1},
            {"id": "deepseek/deepseek-chat", "name": "DeepSeek V3 (Deep Reasoning)", "tier": 1},
            {"id": "meta-llama/llama-3.3-70b-instruct", "name": "Llama 3.3 70B (High Precision)", "tier": 1},
            {"id": "google/gemini-2.0-flash-001", "name": "Gemini 2.0 Flash (Fast Analysis)", "tier": 1},
            {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet (Elite Quant)", "tier": 1},
            {"id": "google/gemini-2.5-flash", "name": "Google Gemini 2.5 Flash (1st Fallback)", "tier": 2},
            {"id": "local-quant-brain", "name": "Local Deterministic Quant Brain ($0 Offline)", "tier": 3},
        ]
        fallback_chain = [
            {"tier": 1, "name": "Primary Brain", "target": active, "status": "ACTIVE" if settings.openrouter_api_key else "STANDBY"},
            {"tier": 2, "name": "1st Fallback", "target": "google/gemini-2.5-flash", "status": "READY" if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") else "OFFLINE"},
            {"tier": 3, "name": "2nd Fallback", "target": "Local Deterministic Quant Brain", "status": "ALWAYS AVAILABLE"},
        ]
        return {
            "active_model": active,
            "models": available,
            "fallback_chain": fallback_chain,
        }

    @app.post("/api/hermes/model")
    def set_hermes_model(payload: dict):
        new_model = str(payload.get("model", "")).strip()
        if not new_model:
            raise HTTPException(422, "Model id cannot be empty.")
        from backend.database import portfolio_state
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

    @app.post("/api/hermes/rollback")
    def rollback_checkpoint():
        from backend.hermes.agent_loop import CheckpointManager
        with database.write() as session:
            state = portfolio_state(session)
            result = CheckpointManager.rollback_last(session, state)
            broadcaster.publish("rollback", result)
            return result

    active_sessions: set[str] = set()

    @app.post("/api/auth/login")
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

    @app.post("/api/auth/logout")
    def logout(request: Request):
        auth_hdr = request.headers.get("Authorization", "")
        token = auth_hdr.replace("Bearer ", "").strip()
        active_sessions.discard(token)
        return {"status": "ok", "authenticated": False}

    @app.get("/api/auth/session")
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

    @app.get("/api/settings/keys")
    def get_api_keys():
        import os
        from datetime import datetime
        from backend.config import DHAKA
        def mask(s: str) -> str:
            if not s:
                return ""
            if len(s) <= 8:
                return "****"
            return f"{s[:4]}...{s[-4:]}"

        with database.read() as session:
            state = portfolio_state(session)
            active_model = getattr(state, "active_model", settings.openrouter_model)
            from backend.database import ChatBudget, HermesSessionMemory
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

    @app.post("/api/settings/keys")
    def update_api_keys(body: KeysSettingsRequest):
        import os
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

    @app.get("/api/stream")
    async def event_stream(request: Request):
        queue = broadcaster.subscribe()

        async def generator():
            try:
                yield f"event: connected\ndata: {json.dumps({'status': 'connected'})}\n\n"
                while True:
                    if await request.is_disconnected():
                        break
                    try:
                        msg = await asyncio.wait_for(queue.get(), timeout=12.0)
                        yield f"event: {msg['event']}\ndata: {json.dumps(msg['data'])}\n\n"
                    except asyncio.TimeoutError:
                        yield ": heartbeat\n\n"
            finally:
                broadcaster.unsubscribe(queue)

        return StreamingResponse(
            generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @app.get("/", include_in_schema=False)
    def cockpit():
        return FileResponse(ROOT / "frontend/index.html", headers={"Cache-Control": "no-cache"})

    app.mount("/assets", StaticFiles(directory=ROOT / "frontend", check_dir=False), name="assets")
    return app


app = create_app()
