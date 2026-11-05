"""StockNow live browser session and network telemetry endpoints."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict

from backend.adapters.stocknow_client import StockNowLiveClient
from backend.config import Settings


class StockNowSessionActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["launch", "check_auth", "close"]
    mode: Literal["ONSCREEN_LIVE", "BACKGROUND_POLLING"] | None = None


def build_stocknow_router(
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

    return router
