"""StockNow live browser session and network telemetry endpoints."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from backend.adapters.stocknow_client import StockNowLiveClient
from backend.adapters.stocknow_market_sync import (
    extract_quotes_from_stocknow,
    sync_live_market_to_db,
)
from backend.config import Settings
from backend.database import Database
from backend.portfolio import build_snapshot


class StockNowSessionActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["launch", "check_auth", "close"]
    mode: Literal["ONSCREEN_LIVE", "BACKGROUND_POLLING"] | None = None


class StockNowMarketSyncRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    payload: Any | None = None


def build_stocknow_router(
    database: Database,
    settings: Settings,
    broadcaster: Any,
    client: StockNowLiveClient | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/stocknow", tags=["stocknow"])
    stocknow_client = client or StockNowLiveClient(ingestion_mode="BACKGROUND_POLLING")
    router.stocknow_client = stocknow_client  # type: ignore[attr-defined]

    @router.get("/status")
    def get_stocknow_status():
        return stocknow_client.get_status()

    @router.post("/session")
    async def post_stocknow_session(body: StockNowSessionActionRequest):
        action = body.action
        if action == "launch":
            res = await stocknow_client.launch(mode=body.mode)
            phone = getattr(settings, "operator_phone", settings.operator_username)
            password = settings.operator_password
            if phone and password and stocknow_client.state == "READY":
                auth_res = await stocknow_client.ensure_authenticated(phone, password)
                res["auth"] = auth_res
        elif action == "check_auth":
            phone = getattr(settings, "operator_phone", settings.operator_username)
            password = settings.operator_password
            res = await stocknow_client.ensure_authenticated(phone, password)
        elif action == "close":
            res = await stocknow_client.close()
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported action '{action}'.")

        broadcaster.publish("stocknow_session", res)
        return res

    @router.post("/sync-market")
    async def post_stocknow_sync_market(body: StockNowMarketSyncRequest | None = None):
        injected = body.payload if body is not None else None
        quotes = await extract_quotes_from_stocknow(stocknow_client, injected_payload=injected)
        result = sync_live_market_to_db(database, quotes)
        if result["synced_count"] > 0:
            stocknow_client.last_sync_at = result["synced_at"]
        snapshot = build_snapshot(database, settings)
        payload = {"result": result, "snapshot": snapshot}
        broadcaster.publish("market_sync", payload)
        return payload

    return router
