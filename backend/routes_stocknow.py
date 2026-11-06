"""StockNow live browser session and network telemetry endpoints."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

logger = logging.getLogger("hummingbird.stocknow_routes")

from backend.adapters.stocknow_client import StockNowLiveClient
from backend.adapters.stocknow_market_sync import (
    extract_quotes_from_stocknow,
    get_or_fetch_all_dse_shares,
    sync_live_market_to_db,
)
from backend.adapters.stocknow_portfolio_sync import (
    extract_hummingbird_portfolio,
    extract_hummingbird_portfolio_from_browser,
    reconcile_portfolio_to_db,
)
from backend.config import Settings
from backend.database import CompanyProfile, Database, PortfolioState, TaxLot, TradeLog
from backend.portfolio import build_snapshot


class StockNowSessionActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["launch", "check_auth", "close"]
    mode: Literal["ONSCREEN_LIVE", "BACKGROUND_POLLING"] | None = None


class StockNowMarketSyncRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    payload: Any | None = None


class StockNowPortfolioSyncRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    injected_portfolio: Any | None = None


class StockNowExecuteOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    symbol: str
    side: Literal["BUY", "SELL"]
    quantity: int
    dry_run: bool = False
    idempotency_key: str | None = None


class StockNowSchedulerActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["start", "stop", "tick_now"]
    force: bool = False


def build_stocknow_router(
    database: Database,
    settings: Settings,
    broadcaster: Any,
    client: StockNowLiveClient | None = None,
    scheduler: Any = None,
) -> APIRouter:
    from backend.engine.scheduler import DSEMarketScheduler, get_active_scheduler

    router = APIRouter(prefix="/api/stocknow", tags=["stocknow"])
    stocknow_client = client or StockNowLiveClient(ingestion_mode="BACKGROUND_POLLING")
    router.stocknow_client = stocknow_client  # type: ignore[attr-defined]

    dse_scheduler = scheduler or get_active_scheduler()
    if dse_scheduler is None:
        dse_scheduler = DSEMarketScheduler(database, settings, broadcaster, stocknow_client)
    router.dse_scheduler = dse_scheduler  # type: ignore[attr-defined]

    @router.get("/status")
    def get_stocknow_status():
        return stocknow_client.get_status()

    @router.get("/page")
    async def get_stocknow_page():
        if not stocknow_client.page or getattr(stocknow_client.page, "is_closed", lambda: True)():
            return {"connected": False, "url": None, "title": None}
        async def _get_info():
            p = stocknow_client.page
            url = getattr(p, "url", "")
            title = await p.title() if hasattr(p, "title") else ""
            text = await p.evaluate("() => document.body ? document.body.innerText.substring(0, 1000) : ''") if hasattr(p, "evaluate") else ""
            return {"connected": True, "url": url, "title": title, "text": text}
        if hasattr(stocknow_client, "_run_in_proactor"):
            return await stocknow_client._run_in_proactor(_get_info())
        return await _get_info()

    @router.post("/session")
    async def post_stocknow_session(body: StockNowSessionActionRequest):
        action = body.action
        if action == "launch":
            target_mode = body.mode or "ONSCREEN_LIVE"
            res = await stocknow_client.launch(mode=target_mode)
            phone = getattr(settings, "operator_phone", None) or settings.operator_username or "01882082502"
            password = settings.operator_password or "Stocknow#909109"
            if stocknow_client.state == "READY":
                async def _background_auth():
                    try:
                        auth_res = await stocknow_client.ensure_authenticated(phone, password)
                        status_payload = stocknow_client.get_status()
                        status_payload["auth"] = auth_res
                        broadcaster.publish("stocknow_session", status_payload)
                    except Exception as err:
                        logger.warning("Background StockNow authentication failed: %s", err)

                asyncio.create_task(_background_auth())

            if not res.get("connected") or res.get("state") == "ERROR":
                res["reason"] = res.get("last_error") or stocknow_client.last_error or "Browser launch failed"
        elif action == "check_auth":
            phone = getattr(settings, "operator_phone", None) or settings.operator_username or "01882082502"
            password = settings.operator_password or "Stocknow#909109"
            res = await stocknow_client.ensure_authenticated(phone, password)
            if not res.get("authenticated") or res.get("state") == "ERROR":
                res["reason"] = res.get("reason") or res.get("message") or "Authentication check failed"
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

    @router.get("/all-shares")
    async def get_all_dse_shares():
        """Returns the full 470+ DSE shares catalog with live LTP, +/- %, and sparkline curves."""
        return await get_or_fetch_all_dse_shares(stocknow_client)

    @router.get("/history/{symbol}")
    async def get_stocknow_symbol_history(symbol: str):
        """Returns real 400-candle daily history for any DSE company directly from StockNow."""
        sym_clean = symbol.strip().upper()
        import httpx
        url = f"https://stocknow.com.bd/api/v1/instruments/{sym_clean}/history?data2=true&resolution=1D&skip=0"
        try:
            async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"}, timeout=12.0) as http:
                res = await http.get(url)
                if res.status_code != 200:
                    raise HTTPException(status_code=res.status_code, detail=f"StockNow history unavailable for {sym_clean}")
                data = res.json()
                return {"symbol": sym_clean, "data": data}
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Failed fetching StockNow history: {exc}")

    @router.post("/sync-portfolio")
    async def post_stocknow_sync_portfolio(body: StockNowPortfolioSyncRequest | None = None):
        injected = body.injected_portfolio if body is not None else None
        extracted = None
        if not injected and stocknow_client.state == "READY":
            try:
                extracted = await extract_hummingbird_portfolio_from_browser(stocknow_client)
            except Exception as exc:
                logger.warning("Browser extraction from live tab failed, falling back: %s", exc)
        if not extracted:
            extracted = extract_hummingbird_portfolio(stocknow_client, injected_portfolio=injected)

        result = reconcile_portfolio_to_db(database, settings, extracted)
        if result.get("success"):
            stocknow_client.bound_portfolio_name = extracted.get("portfolio_name", "Humming Bird")
            stocknow_client.bound_portfolio_id = extracted.get("portfolio_id")
            stocknow_client.last_portfolio_sync_at = result.get("synced_at")

        snapshot = build_snapshot(database, settings)
        payload = {"result": result, "snapshot": snapshot}
        broadcaster.publish("portfolio_sync", payload)
        return payload

    @router.post("/execute-order")
    async def post_stocknow_execute_order(body: StockNowExecuteOrderRequest):
        sym = body.symbol.upper()
        side = body.side.upper()
        qty = body.quantity

        from backend.adapters.stocknow_order_executor import execute_stocknow_virtual_order
        from backend.engine.agent_actions import execute_agentic_buy, execute_agentic_sell
        from backend.hermes.agent_loop import CheckpointManager

        with database.write() as session:
            state = session.get(PortfolioState, 1)
            if not state:
                raise HTTPException(status_code=500, detail="Portfolio state not initialized.")
            comp = session.get(CompanyProfile, sym)
            if not comp:
                raise HTTPException(status_code=404, detail=f"Company {sym} not found in database.")

            lots = session.scalars(select(TaxLot)).all()
            trades = session.scalars(select(TradeLog)).all()
            lots_snap = [
                {
                    "id": l.id, "symbol": l.symbol, "bucket": l.bucket, "acquired_on": l.acquired_on.isoformat(),
                    "matures_on": l.matures_on.isoformat(), "original_qty": l.original_qty, "remaining_qty": l.remaining_qty,
                    "buy_price": str(l.buy_price), "buy_fee": str(l.buy_fee), "original_cost_basis": str(l.original_cost_basis),
                    "remaining_cost_basis": str(l.remaining_cost_basis), "cycle_base_qty": l.cycle_base_qty,
                    "next_tier": l.next_tier, "last_sale_revision": l.last_sale_revision, "peak_price": str(l.peak_price),
                    "phase": l.phase, "recovery_anchor": str(l.recovery_anchor) if l.recovery_anchor else None,
                }
                for l in lots
            ]
            trades_snap = [
                {
                    "id": t.id, "trade_key": t.trade_key, "cycle_id": t.cycle_id, "lot_id": t.lot_id, "symbol": t.symbol,
                    "side": t.side, "quantity": t.quantity, "price": str(t.price), "gross_amount": str(t.gross_amount),
                    "fee": str(t.fee), "net_cash_change": str(t.net_cash_change), "realized_pnl": str(t.realized_pnl),
                    "bucket": t.bucket, "trade_on": t.trade_on.isoformat(), "settles_on": t.settles_on.isoformat(),
                    "reason": t.reason, "source": t.source,
                }
                for t in trades
            ]

            CheckpointManager.create_checkpoint(
                session=session,
                state=state,
                action=f"STOCKNOW_{side}",
                description=f"StockNow virtual {side} of {qty} shares of {sym}",
                symbol=sym,
                extra_snapshot={
                    "portfolio_lots": lots_snap,
                    "portfolio_trades": trades_snap,
                    "initial_capital": str(state.initial_capital),
                },
                actor="StockNow Order Router",
            )

            try:
                if side == "BUY":
                    trade_res = execute_agentic_buy(session, state, settings, sym, requested_qty=qty)
                else:
                    trade_res = execute_agentic_sell(session, state, settings, sym, requested_qty=qty)
            except ValueError as err:
                raise HTTPException(status_code=400, detail=str(err))

            unit_price = comp.last_price

        receipt = await execute_stocknow_virtual_order(
            client=stocknow_client,
            symbol=sym,
            side=side,
            quantity=qty,
            price=unit_price,
            portfolio_id=stocknow_client.bound_portfolio_id or "Humming Bird",
            idempotency_key=body.idempotency_key,
            dry_run=body.dry_run,
        )

        snapshot = build_snapshot(database, settings)
        payload = {"success": True, "receipt": receipt, "trade": trade_res, "snapshot": snapshot}
        broadcaster.publish("order_executed", payload)
        return payload

    @router.get("/scheduler")
    def get_stocknow_scheduler():
        return dse_scheduler.get_status()

    @router.post("/scheduler")
    async def post_stocknow_scheduler(body: StockNowSchedulerActionRequest):
        action = body.action
        if action == "start":
            return dse_scheduler.start()
        elif action == "stop":
            return await dse_scheduler.stop()
        elif action == "tick_now":
            return await dse_scheduler.run_scheduled_tick(force=body.force)
        raise HTTPException(status_code=400, detail=f"Unknown scheduler action: {action}")

    return router
