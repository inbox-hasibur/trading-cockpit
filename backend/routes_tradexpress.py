"""TradeXpress and Self-Learning Local API Routes.

Exposes endpoints for passive data ingestion, tab freshness inspection,
shadow order book operations (Step 1 preview -> Step 2 dispatch), and learning logs.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select

from backend.adapters.tradexpress.passive_feed import (
    get_feed_health_and_guidance,
    get_global_passive_feed,
    ingest_passive_snapshot,
)
from backend.adapters.tradexpress.shadow_simulator import TradeXpressShadowSimulator
from backend.config import Settings
from backend.database import Database, PortfolioState, TradeLearningLog, portfolio_state
from backend.engine.money import ZERO, decimal

logger = logging.getLogger("hummingbird.tradexpress.routes")


class BridgeControlRequest(BaseModel):
    action: str = Field("status", description="attach, detach, or status")
    cdp_url: str = Field("http://127.0.0.1:9222", description="Chrome DevTools Protocol endpoint")


class ShadowOrderRequest(BaseModel):
    symbol: str = Field(..., description="DSE stock symbol (e.g. BANKASIA or BANKASIA`PB)")
    side: str = Field(..., description="BUY or SELL")
    quantity: int = Field(..., gt=0, description="Number of shares")
    price: float = Field(..., gt=0, description="Limit price")
    order_type: str = Field("LIMIT", description="Must be LIMIT")
    tif: str = Field("DAY", description="Must be DAY")
    confirm: bool = Field(False, description="False for Step 1 preview, True for Step 2 execution")
    actor: str = Field("OPERATOR_MANUAL", description="Order initiator: OPERATOR_MANUAL, HERMES, or AUTOTRADER")
    reason: str = Field("", description="Optional justification or strategy tag")
    portfolio_id: str = Field("H9210_SHADOW", description="Target portfolio identifier")
    allow_offhours_ltp_fill: bool = Field(True, description="Permit test fills using LTP during off-hours")


def build_tradexpress_router(
    database: Database,
    settings: Settings,
    broadcaster: Any = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/tradexpress", tags=["TradeXpress"])

    @router.get("/status")
    def get_tradexpress_status():
        """Returns passive feed connection status, tab freshness, and operator guidance."""
        from backend.adapters.tradexpress.cdp_daemon import get_global_passive_daemon

        feed = get_global_passive_feed(database)
        guidance = feed.get_health_and_guidance()
        with database.read() as session:
            state = portfolio_state(session)
            venue = getattr(state, "execution_venue", "SHADOW_DUMMY")
            unsettled = float(getattr(state, "unsettled_sales_bdt", ZERO) or ZERO)

        acct = feed.get_account_summary()
        daemon = get_global_passive_daemon(database, settings, broadcaster=broadcaster)
        daemon_status = daemon.get_status()
        telem = feed.get_telemetry()
        is_connected = bool(guidance.get("bridge_connected") or telem.get("bridge_connected") or daemon_status.get("cdp_connected"))

        return {
            "status": "ONLINE" if (guidance.get("is_healthy") or is_connected) else "ATTENTION_REQUIRED",
            "cdp_connected": guidance.get("cdp_connected") or daemon_status.get("cdp_connected"),
            "bridge_connected": is_connected,
            "bridge_source": telem.get("bridge_source", "OFFLINE"),
            "dse_status": telem.get("dse_status", "UNKNOWN"),
            "active_tab": telem.get("active_tab", "none"),
            "last_ingest_utc": telem.get("last_ingest_utc", ""),
            "total_ingests_count": telem.get("total_ingests_count", 0),
            "execution_venue": venue,
            "buying_power": float(acct.buying_power),
            "unsettled_sales_bdt": unsettled,
            "guidance": guidance,
            "account_summary": acct.to_dict(),
            "daemon": daemon_status,
            "net_tap": feed.get_net_tap_summary(),
        }

    @router.post("/bridge")
    async def post_bridge_control(req: BridgeControlRequest):
        """Controls passive CDP spy daemon: attach, detach, or status."""
        from backend.adapters.tradexpress.cdp_daemon import get_global_passive_daemon

        daemon = get_global_passive_daemon(database, settings, broadcaster=broadcaster)
        action = (req.action or "status").strip().lower()
        if action == "attach":
            status_data = await daemon.start(cdp_url=req.cdp_url)
        elif action == "detach":
            status_data = await daemon.stop()
        elif action == "status":
            status_data = daemon.get_status()
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown bridge action: {action}. Expected attach, detach, or status.",
            )
        return {"status": "SUCCESS", "action": action, "daemon": status_data}

    @router.post("/passive-ingest")
    def post_passive_ingest(payload: dict[str, Any], request: Request):
        """Ingests passively sniffed WebSocket / DOM snapshot and reconciles order queue."""
        x_source = request.headers.get("X-Hummingbird-Source") or payload.get("source") or "MANUAL_INGEST"
        feed = get_global_passive_feed(database)
        result = ingest_passive_snapshot(
            database,
            payload,
            feed=feed,
            broadcaster=broadcaster,
            bridge_source=x_source,
        )

        # Run shadow queue order reconciliation
        phase = payload.get("session_phase", "CONTINUOUS")
        with database.write() as session:
            simulator = TradeXpressShadowSimulator(database, settings, feed=feed)
            reconciled = simulator.reconcile_queued_orders(session, feed.get_all_quotes(), session_phase=phase)
            result["reconciled_orders"] = reconciled

        # Immediately publish live SSE "portfolio" update so http://127.0.0.1:8000 updates in real time with zero reload!
        if broadcaster:
            try:
                from backend.portfolio import build_snapshot
                snap = build_snapshot(database, settings)
                broadcaster.publish("portfolio", snap)
            except Exception as b_err:
                logger.debug("Failed publishing live SSE portfolio update after passive ingest: %s", b_err)

        return result

    @router.post("/passive-net-tap")
    def post_passive_net_tap(payload: dict[str, Any], request: Request):
        """Ingests a batch of passive WebSocket / XHR / Fetch network tap events."""
        events = payload.get("events") if isinstance(payload.get("events"), list) else (
            [payload] if payload.get("type") else []
        )
        feed = get_global_passive_feed(database)
        summary = feed.record_net_tap_events(events)
        return {
            "status": "INGESTED",
            "count": len(events),
            "summary": summary,
        }

    @router.get("/net-tap/summary")
    def get_net_tap_summary():
        """Returns in-memory network tap telemetry, seen channels, endpoints, and recent events."""
        feed = get_global_passive_feed(database)
        return feed.get_net_tap_summary()

    @router.get("/orders")
    def list_orders(
        status: str | None = None,
        portfolio_id: str = "H9210_SHADOW",
        limit: int = 50,
    ):
        """Lists simulated shadow orders mirroring TradeXpress Order List."""
        simulator = TradeXpressShadowSimulator(database, settings)
        return simulator.get_orders(portfolio_id=portfolio_id, status=status, limit=limit)

    @router.post("/shadow-order")
    def submit_shadow_order(req: ShadowOrderRequest):
        """Submits 2-step limit order into shadow simulator (confirm=False preview, True commit)."""
        simulator = TradeXpressShadowSimulator(database, settings)
        return simulator.submit_shadow_order(
            symbol=req.symbol,
            side=req.side,
            quantity=req.quantity,
            limit_price=decimal(req.price),
            order_type=req.order_type,
            tif=req.tif,
            confirm=req.confirm,
            actor=req.actor,
            reason=req.reason,
            portfolio_id=req.portfolio_id,
            allow_offhours_ltp_fill=req.allow_offhours_ltp_fill,
        )

    @router.post("/shadow-order/{order_ref}/cancel")
    def cancel_shadow_order(order_ref: str):
        """Cancels a resting QUEUED shadow order."""
        simulator = TradeXpressShadowSimulator(database, settings)
        res = simulator.cancel_order(order_ref)
        if res.get("status") == "ERROR":
            raise HTTPException(status_code=400, detail=res.get("message"))
        return res

    @router.get("/learning")
    def get_learning_logs(tier: str | None = None, limit: int = 50):
        """Returns recent TradeLearningLog records and aggregated win-rate telemetry."""
        with database.read() as session:
            q = select(TradeLearningLog)
            if tier:
                clean_tier = tier.strip().upper()
                if clean_tier in ("L1", "GSC_L1"):
                    q = q.where(TradeLearningLog.tier.in_(["L1", "GSC_L1"]))
                elif clean_tier in ("L2", "GSC_L2"):
                    q = q.where(TradeLearningLog.tier.in_(["L2", "GSC_L2"]))
                else:
                    q = q.where(TradeLearningLog.tier == clean_tier)

            q = q.order_by(TradeLearningLog.id.desc()).limit(limit)
            logs = list(session.scalars(q))

            buys = [l for l in logs if l.side == "BUY" and l.outcome_type == "BUY_FILL"]
            sells = [l for l in logs if l.side == "SELL"]
            profitable_sells = [s for s in sells if (s.net_pnl_pct or ZERO) > ZERO]
            win_rate = (len(profitable_sells) / len(sells) * 100) if sells else 100.0
            avg_pnl = (float(sum((s.net_pnl_pct or ZERO for s in sells), ZERO)) / len(sells)) if sells else 0.0

            return {
                "total_records": len(logs),
                "buys_count": len(buys),
                "sells_count": len(sells),
                "win_rate_pct": round(win_rate, 2),
                "avg_net_pnl_pct": round(avg_pnl, 2),
                "recent_logs": [
                    {
                        "id": l.id,
                        "symbol": l.symbol,
                        "tier": l.tier,
                        "side": l.side,
                        "outcome_type": l.outcome_type,
                        "entry_price": float(l.entry_price),
                        "exit_price": float(l.exit_price) if l.exit_price is not None else None,
                        "net_pnl_pct": float(l.net_pnl_pct) if l.net_pnl_pct is not None else None,
                        "actor": l.actor,
                        "lesson_summary": l.lesson_summary,
                        "session_on": l.session_on.isoformat() if l.session_on else "",
                        "created_at": l.created_at,
                    }
                    for l in logs
                ],
            }

    return router
