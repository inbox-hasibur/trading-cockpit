"""One-process local cockpit. Start with: uvicorn backend.main:app --host 127.0.0.1."""

from __future__ import annotations

import asyncio
import hmac
import json
import logging
import os
import sys

from backend.logging_config import setup_logging
setup_logging()

import httpx

if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass
from contextlib import asynccontextmanager
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, StrictBool
from sqlalchemy import select
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.adapters.stocknow_adapter import StockNowAdapter
from backend.adapters.stocknow_client import StockNowLiveClient
from backend.adapters.stocknow_market_sync import extract_quotes_from_stocknow, sync_live_market_to_db
from backend.config import (
    ROOT,
    VERSION,
    Settings,
    get_active_target_portfolio,
    get_allowed_portfolios,
    get_portfolio_name,
)
from backend.database import CustomRule, Database, DecisionLog, KernelAuditLog, RuleAudit, TradeLog, portfolio_state
from backend.engine.auto_trader import AutomationPaused, AutoTrader
from backend.engine.scheduler import DSEMarketScheduler, get_active_scheduler
from backend.engine.money import ZERO
from backend.engine.trading_lock import acquire_trading_lock
from backend.market_map import build_market_map_payload
from backend.portfolio import build_snapshot, rule_view
from backend.routes_auth_settings import (
    KeysSettingsRequest,
    LoginRequest,
    build_auth_settings_router,
)
from backend.hermes_bridge import build_hermes_bridge_router
from backend.kernel_api import CapsUpdateRequest
from backend.routes_hermes import CreateThreadRequest, build_hermes_router
from backend.routes_stocknow import build_stocknow_router
from backend.seed import migrate_real_stocknow_market, seed_demo

logger = logging.getLogger("hummingbird.api")


class PauseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    paused: StrictBool


class AutomationConfigRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    automation_enabled: bool | None = None
    paused: bool | None = None
    ingestion_mode: Literal["BACKGROUND_POLLING", "ONSCREEN_LIVE", "SIDE_BY_SIDE_LIVE", "BACKGROUND_24_7", "BACKGROUND 24/7"] | None = None
    polling_interval_sec: int | None = Field(default=None, ge=30, le=3600)
    trading_mode: Literal["TEST_OFFHOURS", "LIVE_HOURS"] | None = None


class HandoffRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_mode: Literal["BACKGROUND_POLLING", "ONSCREEN_LIVE", "BACKGROUND_24_7", "BACKGROUND 24/7"]
    reason: str | None = None


class KillRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    active: bool = True
    reason: str | None = None


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


def create_app(settings: Settings | None = None, database: Database | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    database = database or Database(settings.database_url)
    stocknow_client = StockNowLiveClient(ingestion_mode="BACKGROUND_POLLING")
    trader = AutoTrader(database, settings)
    broadcaster = EventBroadcaster()
    scheduler = DSEMarketScheduler(database, settings, broadcaster, stocknow_client, trader)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        database.create_schema()
        with database.write() as session:
            seed_demo(session, settings)
            migrate_real_stocknow_market(session, settings)
            state = portfolio_state(session)
            state.startup_health_status = "READY"
            state.startup_health_passed = True

        from backend.engine.heartbeat import record_system_heartbeat, check_dead_man_switch, send_daily_summary_if_due
        from backend.engine.telegram_bot import TelegramBotDaemon

        record_system_heartbeat(database, settings)

        hb_task = None
        async def _heartbeat_worker():
            while True:
                try:
                    await asyncio.sleep(60.0)
                    record_system_heartbeat(database, settings)
                    check_dead_man_switch(database, settings)
                    send_daily_summary_if_due(database, settings)
                except asyncio.CancelledError:
                    break
                except Exception as hb_err:
                    logger.debug("Heartbeat worker tick noticed: %s", hb_err)

        hb_task = asyncio.create_task(_heartbeat_worker())

        tg_daemon = TelegramBotDaemon(database, settings)
        tg_daemon.start()

        try:
            yield
        finally:
            if hb_task and not hb_task.done():
                hb_task.cancel()
            tg_daemon.stop()
            try:
                from backend.adapters.tradexpress.cdp_daemon import get_global_passive_daemon
                await get_global_passive_daemon(database, settings, broadcaster).stop()
            except Exception:
                pass
            database.engine.dispose()
            try:
                await scheduler.stop()
            except Exception:
                pass
            try:
                await stocknow_client.close()
            except Exception:
                pass

    app = FastAPI(
        title="Humming Bird · Paper Trading Cockpit", version=VERSION,
        description="Demo-only deterministic trading rules. No live feed or external orders.",
        lifespan=lifespan, redoc_url=None,
    )
    app.state.database = database
    app.state.settings = settings
    app.state.trader = trader
    app.state.stocknow_client = stocknow_client
    app.state.scheduler = scheduler
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.trusted_hosts))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_req: Request, exc: RequestValidationError):
        errors = []
        for err in exc.errors():
            loc = [str(x) for x in err.get("loc", []) if str(x) not in ("body",)]
            field_name = ".".join(loc) if loc else "body"
            msg = err.get("msg", "Invalid value")
            errors.append(f"{field_name}: {msg}" if field_name else msg)
        detail_msg = "; ".join(errors) if errors else "Validation error"
        return JSONResponse(
            status_code=422,
            content={"error": "VALIDATION_ERROR", "detail": detail_msg},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_req: Request, exc: StarletteHTTPException):
        error_names = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            422: "UNPROCESSABLE_ENTITY",
            500: "INTERNAL_SERVER_ERROR",
        }
        err_code = error_names.get(exc.status_code, "HTTP_ERROR")
        if isinstance(exc.detail, dict):
            err_code = exc.detail.get("error", err_code)
            detail = str(exc.detail.get("detail", exc.detail.get("message", exc.detail)))
        else:
            detail = str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": err_code, "detail": detail},
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_req: Request, exc: Exception):
        logger.exception("Unhandled error on %s: %s", _req.url.path, exc)
        return JSONResponse(
            status_code=500,
            content={"error": "INTERNAL_SERVER_ERROR", "detail": str(exc) or "Internal server error"},
        )

    @app.middleware("http")
    async def local_security(request: Request, call_next):
        is_api = request.url.path.startswith("/api/")
        origin = request.headers.get("origin")
        expected_origin = str(request.base_url).rstrip("/")
        client_host = request.client.host if request.client else "127.0.0.1"
        is_loopback = client_host in ("127.0.0.1", "::1", "localhost", "testclient")
        is_extension_passive_ingest = (
            request.url.path == "/api/tradexpress/passive-ingest"
            and is_loopback
            and (
                not origin
                or origin.lower().startswith("chrome-extension://")
                or origin.lower().startswith("extension://")
                or origin.lower().rstrip("/") == expected_origin.lower()
            )
        )

        if is_api and request.url.path != "/api/health":
            if request.method == "OPTIONS" and is_extension_passive_ingest:
                res = JSONResponse({"status": "ok"}, status_code=200)
                if origin:
                    res.headers["Access-Control-Allow-Origin"] = origin
                    res.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
                    res.headers["Access-Control-Allow-Headers"] = "*"
                return res

            if not is_extension_passive_ingest:
                if (
                    origin and origin.lower().rstrip("/") != expected_origin.lower()
                ) or request.headers.get("sec-fetch-site") == "cross-site":
                    return JSONResponse({"error": "FORBIDDEN", "detail": "Cross-origin API access is not allowed."}, status_code=403)
            if settings.cockpit_api_token:
                supplied = request.headers.get("authorization", "")
                expected = f"Bearer {settings.cockpit_api_token}"
                if not hmac.compare_digest(supplied.encode(), expected.encode()):
                    return JSONResponse(
                        {"error": "UNAUTHORIZED", "detail": "A valid cockpit API token is required."}, status_code=401,
                        headers={"WWW-Authenticate": "Bearer"},
                    )
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["X-Frame-Options"] = "DENY"
        if is_api and origin and (origin.lower().startswith("chrome-extension://") or origin.lower().startswith("extension://")):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
        # The cockpit is entirely local. FastAPI's optional Swagger page loads
        # its standard CDN assets and needs a separate, documentation-only CSP.
        if request.url.path.startswith("/docs"):
            policy = (
                "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://fastapi.tiangolo.com; "
                "connect-src 'self' http://127.0.0.1:* http://localhost:* ws://127.0.0.1:* ws://localhost:*; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
            )
        else:
            policy = (
                "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
                "connect-src 'self' http://127.0.0.1:* http://localhost:* ws://127.0.0.1:* ws://localhost:*; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
            )
        response.headers["Content-Security-Policy"] = policy
        if is_api:
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/api/health")
    async def health():
        gateway_url = os.environ.get("HERMES_GATEWAY_URL", "http://127.0.0.1:8642")
        gateway_online = False
        try:
            async with httpx.AsyncClient(timeout=0.6) as client:
                res = await client.get(f"{gateway_url}/health")
                gateway_online = (res.status_code == 200)
        except Exception:
            gateway_online = False

        kernel_token = getattr(settings, "kernel_token", None) or os.getenv("KERNEL_TOKEN", "")
        sn_status = stocknow_client.get_status() if stocknow_client else {}

        return {
            "status": "ok",
            "version": VERSION,
            "mode": getattr(settings, "trading_mode", "DEMO"),
            "data_source": "SYNTHETIC",
            "gateway": {
                "status": "online" if gateway_online else "offline",
                "url": gateway_url,
            },
            "kernel": {
                "status": "online",
                "token_configured": bool(kernel_token),
            },
            "stocknow": {
                "state": sn_status.get("state", "BROWSER_NOT_STARTED"),
                "connected": sn_status.get("connected", False),
                "mode": sn_status.get("mode", "UNKNOWN"),
                "bound_portfolio_id": sn_status.get("bound_portfolio_id"),
            },
        }

    @app.get("/api/portfolio")
    def portfolio():
        return build_snapshot(database, settings, live_client=stocknow_client)

    @app.post("/api/automation/cycle")
    async def cycle(
        idempotency_key: Annotated[UUID | None, Header(alias="Idempotency-Key")] = None,
        require_active: bool = False,
    ):
        with database.read() as session:
            state = portfolio_state(session)
            mode = getattr(state, "ingestion_mode", "BACKGROUND_POLLING")
            auto_enabled = getattr(state, "automation_enabled", not getattr(state, "paused", False))

        if require_active and not auto_enabled:
            raise HTTPException(status_code=409, detail="Cycle blocked: automation is paused.")

        # Sync latest quotes from live page or API before cycle if active
        if mode == "ONSCREEN_LIVE" and stocknow_client and stocknow_client.state == "READY" and stocknow_client.page:
            try:
                quotes = await extract_quotes_from_stocknow(stocknow_client)
                if quotes:
                    sync_live_market_to_db(database, quotes)
            except Exception as exc:
                logger.warning("Pre-cycle live quote sync skipped: %s", exc)
        elif mode in ("BACKGROUND_POLLING", "BACKGROUND_24_7", "BACKGROUND 24/7"):
            api_client = getattr(app.state, "stocknow_api", None)
            if api_client and getattr(api_client, "is_authenticated", False):
                try:
                    from backend.adapters.stocknow_market_sync import fetch_stocknow_live_market_data
                    quotes = await fetch_stocknow_live_market_data(client=stocknow_client, api_client=api_client)
                    if quotes:
                        sync_live_market_to_db(database, quotes)
                except Exception as exc:
                    logger.warning("Pre-cycle background quote sync skipped: %s", exc)

        # Automation OFF runs labeled PREVIEW (decisions only); ON submits subject to mode, caps and checks
        dry_run = not auto_enabled
        result = trader.run_cycle(str(idempotency_key) if idempotency_key else None, dry_run=dry_run)
        broadcaster.publish("cycle", result)
        snapshot = build_snapshot(database, settings, live_client=stocknow_client)
        broadcaster.publish("snapshot", snapshot)
        return result

    @app.post("/api/automation/kill")
    def quick_kill(body: KillRequest | None = None):
        from backend.engine.checkpoint import CheckpointManager
        is_active = True if body is None else body.active
        reason_txt = (body.reason if body and body.reason else "") or (
            "Emergency Kill Switch Engaged by Operator" if is_active else "Emergency Kill Switch Disarmed by Operator"
        )
        with database.write() as session:
            state = portfolio_state(session)
            state.kill_switch_active = is_active
            cp = CheckpointManager.create_checkpoint(
                session=session,
                state=state,
                action="KILL_SWITCH_ENGAGED" if is_active else "KILL_SWITCH_DISARMED",
                description=reason_txt,
                actor="Operator",
            )
            session.add(DecisionLog(
                cycle_id=None,
                symbol="SYSTEM",
                action="KILL_SWITCH" if is_active else "KILL_SWITCH_DISARM",
                quantity=0,
                reason=f"KILL_SWITCH: Global kill switch {'engaged' if is_active else 'disarmed'} ({reason_txt}). Orders {'blocked' if is_active else 'unblocked'}.",
                trading_mode=getattr(state, "trading_mode", "LIVE_HOURS"),
            ))
            res = {
                "kill_switch_active": is_active,
                "status": "KILLED" if is_active else "ACTIVE",
                "checkpoint_id": cp.id,
            }
            broadcaster.publish("caps_updated", res)
            snap = build_snapshot(database, settings, live_client=stocknow_client)
            broadcaster.publish("snapshot", snap)
            return res

    @app.post("/api/automation/handoff")
    async def automation_handoff(body: HandoffRequest):
        target = "BACKGROUND_POLLING" if body.target_mode in ("BACKGROUND_24_7", "BACKGROUND 24/7") else body.target_mode
        if target == "BACKGROUND_POLLING":
            from backend.engine.preflight_service import are_caps_set, has_passing_preflight_within_24h
            if not are_caps_set(database) or not has_passing_preflight_within_24h(database):
                raise HTTPException(
                    status_code=422,
                    detail="Enabling Background mode requires risk caps set and a passing preflight check within the last 24 hours.",
                )

        # Single writer: finish current cycle under the trading lock before switching
        with acquire_trading_lock():
            with database.write() as session:
                state = portfolio_state(session)
                old_mode = state.ingestion_mode
                state.ingestion_mode = target
                target_enabled = state.automation_enabled
                target_paused = state.paused

            sched = getattr(app.state, "scheduler", None) or get_active_scheduler()
            if target == "BACKGROUND_POLLING":
                # Background 24/7: away from PC, headless ApiTransport, unattended
                if sched and target_enabled and not target_paused:
                    sched.start()
                if stocknow_client:
                    stocknow_client.ingestion_mode = "BACKGROUND_POLLING"
                    try:
                        if stocknow_client.state == "READY":
                            await stocknow_client.close()
                    except Exception as exc:
                        logger.debug("Closing headed browser on handoff notice: %s", exc)
            elif target == "ONSCREEN_LIVE":
                # Onscreen Live: at the PC, headed browser visible, browser transport
                if sched:
                    sched.stop_sync()
                if stocknow_client:
                    stocknow_client.ingestion_mode = "ONSCREEN_LIVE"
                    try:
                        await stocknow_client.launch(mode="ONSCREEN_LIVE")
                        phone = getattr(settings, "operator_phone", settings.operator_username)
                        password = settings.operator_password
                        if phone and password:
                            await stocknow_client.ensure_authenticated(phone, password)
                    except Exception as exc:
                        logger.warning("Launching headed browser on handoff notice: %s", exc)

        snap = build_snapshot(database, settings, live_client=stocknow_client)
        broadcaster.publish("snapshot", snap)
        return {
            "status": "HANDOFF_COMPLETE",
            "old_mode": old_mode,
            "active_mode": target,
            "automation_enabled": target_enabled,
            "snapshot": snap,
        }

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
    async def automation_config(body: AutomationConfigRequest):
        # 1. Circuit Breaker Check when enabling automation
        if body.automation_enabled is True or body.paused is False:
            with database.read() as session:
                st = portfolio_state(session)
                if getattr(st, "circuit_breaker_tripped", False):
                    raise HTTPException(
                        status_code=422,
                        detail=f"Circuit breaker is tripped: {st.circuit_breaker_reason}. Reset breaker first via /api/automation/circuit-breaker/reset.",
                    )

        # 2. Preflight Check when enabling or switching to Background mode
        with database.read() as session:
            curr_state = portfolio_state(session)
            curr_mode = curr_state.ingestion_mode
            curr_enabled = curr_state.automation_enabled
        target_mode_candidate = body.ingestion_mode or curr_mode
        target_enabled_candidate = body.automation_enabled if body.automation_enabled is not None else (not body.paused if body.paused is not None else curr_enabled)
        if target_mode_candidate == "BACKGROUND_POLLING" and target_enabled_candidate:
            from backend.engine.preflight_service import are_caps_set, has_passing_preflight_within_24h
            if not are_caps_set(database) or not has_passing_preflight_within_24h(database):
                raise HTTPException(
                    status_code=422,
                    detail="Enabling Background mode requires risk caps set and a passing preflight check within the last 24 hours.",
                )

        with database.write() as session:
            state = portfolio_state(session)
            if body.automation_enabled is not None:
                state.automation_enabled = body.automation_enabled
                state.paused = not body.automation_enabled
            elif body.paused is not None:
                state.paused = body.paused
                state.automation_enabled = not body.paused
            if body.ingestion_mode is not None:
                state.ingestion_mode = body.ingestion_mode
            if body.polling_interval_sec is not None:
                state.polling_interval_sec = body.polling_interval_sec
            if body.trading_mode is not None:
                state.trading_mode = body.trading_mode
            target_mode = state.ingestion_mode
            target_enabled = state.automation_enabled
            target_paused = state.paused

        # Idempotent background scheduler synchronization
        sched = getattr(app.state, "scheduler", None) or get_active_scheduler()
        if sched:
            if not target_enabled or target_paused:
                sched.stop_sync()
            elif target_mode == "BACKGROUND_POLLING":
                sched.start()

        # Ingestion mode switch handling (non-blocking, safe with or without browser attached)
        if target_mode == "ONSCREEN_LIVE":
            if stocknow_client:
                async def _bg_onscreen_attach():
                    try:
                        if stocknow_client.state != "READY":
                            await stocknow_client.launch(mode="ONSCREEN_LIVE")
                        phone = getattr(settings, "operator_phone", settings.operator_username)
                        password = settings.operator_password
                        if phone and password and stocknow_client.state == "READY":
                            await stocknow_client.ensure_authenticated(phone, password)
                        quotes = await extract_quotes_from_stocknow(stocknow_client)
                        if quotes:
                            sync_live_market_to_db(database, quotes)
                    except Exception as exc:
                        logger.warning("Onscreen live mode background attach noticed: %s", exc)

                asyncio.create_task(_bg_onscreen_attach())
        elif target_mode == "BACKGROUND_POLLING":
            if stocknow_client:
                stocknow_client.ingestion_mode = "BACKGROUND_POLLING"

        with database.read() as session:
            state = portfolio_state(session)
            adapter = StockNowAdapter()
            adapter_status = adapter.get_adapter_status(state.ingestion_mode, state.polling_interval_sec, stocknow_client)
            res = {
                "automation_enabled": state.automation_enabled,
                "paused": state.paused,
                "ingestion_mode": state.ingestion_mode,
                "polling_interval_sec": state.polling_interval_sec,
                "trading_mode": getattr(state, "trading_mode", "LIVE_HOURS"),
                "adapter": adapter_status,
                "mode": "DEMO",
            }
            broadcaster.publish("automation_config", res)
            return res

    @app.post("/api/automation/circuit-breaker/reset")
    def reset_circuit_breaker_endpoint():
        from backend.engine.circuit_breaker import reset_circuit_breaker
        return reset_circuit_breaker(database, settings, actor="Operator", broadcaster=broadcaster)

    @app.get("/api/automation/circuit-breaker/status")
    def get_circuit_breaker_status():
        with database.read() as session:
            st = portfolio_state(session)
            return {
                "circuit_breaker_tripped": bool(getattr(st, "circuit_breaker_tripped", False)),
                "circuit_breaker_reason": getattr(st, "circuit_breaker_reason", None),
                "consecutive_failure_count": int(getattr(st, "consecutive_failure_count", 0)),
                "startup_health_status": getattr(st, "startup_health_status", "READY"),
                "startup_health_passed": bool(getattr(st, "startup_health_passed", True)),
            }

    @app.post("/api/automation/preflight")
    def run_preflight_endpoint():
        from backend.engine.preflight_service import run_cockpit_preflight
        return run_cockpit_preflight(database, settings, actor="Operator")

    @app.get("/api/automation/preflight/status")
    def get_preflight_status():
        from backend.engine.preflight_service import are_caps_set, has_passing_preflight_within_24h
        return {
            "caps_set": are_caps_set(database),
            "has_passing_preflight_24h": has_passing_preflight_within_24h(database),
        }

    @app.get("/api/caps")
    def get_caps_public():
        with database.read() as session:
            state = portfolio_state(session)
            active_pid = get_active_target_portfolio(getattr(state, "trading_mode", "LIVE_HOURS"), settings) or settings.stocknow_live_portfolio_id
            today_buys_spend = sum(
                (abs(t.net_cash_change) for t in session.scalars(
                    select(TradeLog).where(
                        TradeLog.trade_on == state.clock_date,
                        TradeLog.side == "BUY",
                        TradeLog.portfolio_id == active_pid,
                    )
                )),
                ZERO,
            )
            today_orders_count = len(session.scalars(select(TradeLog.id).where(
                TradeLog.trade_on == state.clock_date,
                TradeLog.portfolio_id == active_pid,
            )).all())
            return {
                "max_order_bdt": float(state.max_order_bdt) if getattr(state, "max_order_bdt", None) is not None else None,
                "max_symbol_bdt": float(state.max_symbol_bdt) if getattr(state, "max_symbol_bdt", None) is not None else None,
                "daily_budget_bdt": float(getattr(state, "daily_budget_bdt", Decimal("4000.00"))),
                "max_orders_per_day": int(getattr(state, "max_orders_per_day", 20)),
                "kill_switch_active": bool(getattr(state, "kill_switch_active", False)),
                "today_buy_spend_bdt": float(today_buys_spend),
                "today_orders_count": int(today_orders_count),
                "trading_mode": getattr(state, "trading_mode", "LIVE_HOURS"),
                "portfolio_id": active_pid,
                "portfolio_name": get_portfolio_name(active_pid, settings),
            }

    @app.post("/api/caps")
    def set_caps_public(body: CapsUpdateRequest):
        from backend.engine.checkpoint import CheckpointManager
        with database.write() as session:
            state = portfolio_state(session)
            current_max_order = getattr(state, "max_order_bdt", None)
            current_max_symbol = getattr(state, "max_symbol_bdt", None)
            current_daily_budget = getattr(state, "daily_budget_bdt", Decimal("4000.00"))
            current_max_orders = getattr(state, "max_orders_per_day", 20)
            current_kill_switch = getattr(state, "kill_switch_active", False)

            raising = False
            if body.max_order_bdt is not None:
                new_mo = Decimal(str(body.max_order_bdt))
                if current_max_order is not None and new_mo > current_max_order:
                    raising = True
            if body.max_symbol_bdt is not None:
                new_ms = Decimal(str(body.max_symbol_bdt))
                if current_max_symbol is not None and new_ms > current_max_symbol:
                    raising = True
            if body.daily_budget_bdt is not None:
                new_db = Decimal(str(body.daily_budget_bdt))
                if new_db > current_daily_budget:
                    raising = True
            if body.max_orders_per_day is not None:
                if body.max_orders_per_day > current_max_orders:
                    raising = True
            if body.kill_switch_active is not None:
                if current_kill_switch and not body.kill_switch_active:
                    raising = True

            if raising and not body.confirm:
                raise HTTPException(
                    status_code=422,
                    detail="Raising risk limits requires operator confirmation in the cockpit (confirm=true).",
                )

            cp = CheckpointManager.create_checkpoint(
                session=session,
                state=state,
                action="SET_CAPS",
                description=f"Update risk caps (confirm={body.confirm})",
                actor="Operator",
            )

            if body.max_order_bdt is not None:
                state.max_order_bdt = Decimal(str(body.max_order_bdt))
            if body.max_symbol_bdt is not None:
                state.max_symbol_bdt = Decimal(str(body.max_symbol_bdt))
            if body.daily_budget_bdt is not None:
                state.daily_budget_bdt = Decimal(str(body.daily_budget_bdt))
            if body.max_orders_per_day is not None:
                state.max_orders_per_day = int(body.max_orders_per_day)
            if body.kill_switch_active is not None:
                state.kill_switch_active = bool(body.kill_switch_active)

            state.rules_revision += 1

            session.add(KernelAuditLog(
                endpoint="/api/caps",
                action="SET_CAPS",
                symbol=None,
                payload=body.model_dump(mode="json"),
                result={
                    "status": "ok",
                    "max_order_bdt": str(state.max_order_bdt) if state.max_order_bdt is not None else None,
                    "max_symbol_bdt": str(state.max_symbol_bdt) if state.max_symbol_bdt is not None else None,
                    "daily_budget_bdt": str(state.daily_budget_bdt),
                    "max_orders_per_day": state.max_orders_per_day,
                    "kill_switch_active": state.kill_switch_active,
                },
                checkpoint_id=cp.id,
                session_on=state.clock_date,
                trading_mode=state.trading_mode,
            ))

            res = {
                "status": "ok",
                "checkpoint_id": cp.id,
                "max_order_bdt": float(state.max_order_bdt) if state.max_order_bdt is not None else None,
                "max_symbol_bdt": float(state.max_symbol_bdt) if state.max_symbol_bdt is not None else None,
                "daily_budget_bdt": float(state.daily_budget_bdt),
                "max_orders_per_day": int(state.max_orders_per_day),
                "kill_switch_active": bool(state.kill_switch_active),
            }
            broadcaster.publish("caps_updated", res)
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

    app.include_router(build_hermes_router(database, settings, broadcaster))
    app.include_router(build_hermes_bridge_router(database, settings, broadcaster))
    app.include_router(build_auth_settings_router(database, settings, broadcaster))
    app.include_router(build_stocknow_router(database, settings, broadcaster, stocknow_client, scheduler=scheduler))
    from backend.routes_tradexpress import build_tradexpress_router
    app.include_router(build_tradexpress_router(database, settings, broadcaster))
    from backend.kernel_api import build_kernel_router
    app.state.broadcaster = broadcaster
    app.include_router(build_kernel_router(database, settings, stocknow_client, broadcaster))

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

    class DevStaticFiles(StaticFiles):
        async def get_response(self, path: str, scope):
            response = await super().get_response(path, scope)
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response

    @app.get("/", include_in_schema=False)
    def cockpit():
        return FileResponse(
            ROOT / "frontend/index.html",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    app.mount("/assets", DevStaticFiles(directory=ROOT / "frontend", check_dir=False), name="assets")
    return app


app = create_app()
