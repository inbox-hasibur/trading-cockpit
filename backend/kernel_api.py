"""Humming Bird Trading Kernel API Service.

Exposes clean, deterministic local endpoints for the trading kernel, completely
independent of any agent or LLM code. Binds only to localhost (127.0.0.1).
"""

from __future__ import annotations

import logging
import os
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from backend.adapters.stocknow_market_sync import (
    extract_quotes_from_stocknow,
    get_or_fetch_all_dse_shares,
    sync_live_market_to_db,
)
from backend.adapters.stocknow_portfolio_sync import reconcile_portfolio_to_db
from backend.config import Settings
from backend.database import (
    CanaryThesis,
    CompanyProfile,
    CustomRule,
    Database,
    KernelAuditLog,
    PortfolioState,
    RuleAudit,
    TaxLot,
    portfolio_state,
)
from backend.engine.agent_actions import (
    check_canary_theses,
    emergency_quarantine_and_canary,
    execute_agentic_buy,
    execute_agentic_sell,
    restore_quarantine,
)
from backend.engine.checkpoint import CheckpointManager
from backend.engine.curve_analyzer import analyze_curve
from backend.engine.money import ZERO, allocated_basis, purchase_amount, sale_amount
from backend.engine.scheduler import is_dse_market_open
from backend.portfolio import snapshot_from_session

logger = logging.getLogger(__name__)

# Global cache for idempotency keys
_EXECUTED_ORDER_KEYS: dict[str, dict[str, Any]] = {}


def clear_order_idempotency_cache() -> None:
    """Clear order idempotency cache (for tests)."""
    _EXECUTED_ORDER_KEYS.clear()


def verify_kernel_auth(
    request: Request,
    x_kernel_token: str | None = Header(None, alias="X-Kernel-Token"),
) -> None:
    """Enforces 127.0.0.1 localhost binding and X-Kernel-Token authentication."""
    # 1. Localhost bind check
    client_host = request.client.host if request.client else "127.0.0.1"
    if client_host not in ("127.0.0.1", "localhost", "testclient", "::1"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Kernel API binds to 127.0.0.1 only.",
        )

    # 2. X-Kernel-Token check
    expected = os.getenv("KERNEL_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: KERNEL_TOKEN is not configured.",
        )
    if not x_kernel_token or x_kernel_token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid or missing X-Kernel-Token header.",
        )


def get_db(request: Request) -> Database:
    """Extract database from app state or fallback to default."""
    if hasattr(request.app.state, "database"):
        return request.app.state.database
    settings = get_settings(request)
    return Database(settings.database_url)


def get_settings(request: Request) -> Settings:
    """Extract settings from app state or fallback to default."""
    if hasattr(request.app.state, "settings"):
        return request.app.state.settings
    return Settings()


def get_stocknow_client(request: Request) -> Any | None:
    """Extract live StockNow Playwright client if attached."""
    return getattr(request.app.state, "stocknow_client", None)


router = APIRouter(prefix="/k", dependencies=[Depends(verify_kernel_auth)])


# ─────────────────────────────────────────────────────────────────────────────
# READ ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/portfolio")
def get_portfolio(
    request: Request,
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Returns full portfolio snapshot with holdings, cash, and rolling buckets."""
    with db.read() as session:
        return snapshot_from_session(session, settings)


@router.get("/watchlist")
def get_watchlist(
    tier: str | None = Query(None, description="Optional tier filter (e.g. GSC, GSC_L1, GSC_L2)"),
    db: Database = Depends(get_db),
) -> list[dict[str, Any]]:
    """Returns watchlist companies, optionally filtered by tier."""
    with db.read() as session:
        query = select(CompanyProfile).order_by(CompanyProfile.symbol)
        if tier:
            query = query.where(func.upper(CompanyProfile.watchlist_category) == tier.strip().upper())
        companies = list(session.scalars(query))
        result = []
        for c in companies:
            closes = [float(p["close"]) for p in (c.price_history or []) if isinstance(p, dict) and "close" in p]
            sup = min(closes) if closes else float(c.last_price)
            res = max(closes) if closes else float(c.last_price)
            result.append({
                "symbol": c.symbol,
                "name": c.name,
                "sector": c.sector,
                "watchlist_category": c.watchlist_category,
                "last_price": float(c.last_price),
                "support": sup,
                "resistance": res,
                "quarantined": c.quarantined,
                "quarantine_reason": c.quarantine_reason,
            })
        return result


@router.get("/curve/{symbol}")
def get_curve(
    symbol: str,
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Returns price curve analysis, support floor, resistance ceiling, and sparkline points."""
    sym = symbol.strip().upper()
    with db.read() as session:
        comp = session.get(CompanyProfile, sym)
        if not comp:
            raise HTTPException(status_code=404, detail=f"Company '{sym}' not found in database.")
        state = portfolio_state(session)
        history = comp.price_history or []
        closes = [float(p["close"]) for p in history if isinstance(p, dict) and "close" in p]
        sup = min(closes) if closes else float(comp.last_price)
        res = max(closes) if closes else float(comp.last_price)
        analysis = None
        if history:
            analysis = analyze_curve(
                history,
                as_of=state.clock_date,
                buy_fee_rate=settings.buy_fee_rate,
                sell_fee_rate=settings.sell_fee_rate,
            )
        return {
            "symbol": comp.symbol,
            "last_price": float(comp.last_price),
            "support": sup,
            "resistance": res,
            "watchlist_category": comp.watchlist_category,
            "analysis": analysis.to_dict() if analysis else None,
            "history_points": len(history),
        }


@router.get("/market-open")
def get_market_open(settings: Settings = Depends(get_settings)) -> dict[str, Any]:
    """Returns real DSE trading hours and session status in Asia/Dhaka time."""
    return is_dse_market_open(settings=settings)


@router.get("/canaries")
def get_canaries(db: Database = Depends(get_db)) -> list[dict[str, Any]]:
    """Returns active and past 10% canary probe theses."""
    with db.read() as session:
        theses = list(session.scalars(select(CanaryThesis).order_by(CanaryThesis.id.desc())))
        return [
            {
                "id": t.id,
                "symbol": t.symbol,
                "thesis": t.thesis,
                "created_on": t.created_on.isoformat(),
                "entry_price": float(t.entry_price),
                "canary_qty": t.canary_qty,
                "status": t.status,
                "observations_count": t.observations_count,
                "last_price_observed": float(t.last_price_observed),
                "notes": t.notes,
            }
            for t in theses
        ]


@router.get("/lots")
def get_lots(
    symbol: str | None = Query(None, description="Optional symbol filter"),
    db: Database = Depends(get_db),
) -> list[dict[str, Any]]:
    """Returns T+2 rolling tax lots with maturity status."""
    with db.read() as session:
        state = portfolio_state(session)
        query = select(TaxLot).order_by(TaxLot.id)
        if symbol:
            query = query.where(TaxLot.symbol == symbol.strip().upper())
        lots = list(session.scalars(query))
        return [
            {
                "id": lot.id,
                "symbol": lot.symbol,
                "bucket": lot.bucket,
                "acquired_on": lot.acquired_on.isoformat(),
                "matures_on": lot.matures_on.isoformat(),
                "is_mature": lot.matures_on <= state.clock_date,
                "original_qty": lot.original_qty,
                "remaining_qty": lot.remaining_qty,
                "buy_price": float(lot.buy_price),
                "buy_fee": float(lot.buy_fee),
                "remaining_cost_basis": float(lot.remaining_cost_basis),
                "phase": lot.phase,
                "peak_price": float(lot.peak_price),
            }
            for lot in lots
        ]


# ─────────────────────────────────────────────────────────────────────────────
# WRITE ENDPOINTS (Every write snapshots first and writes an audit row)
# ─────────────────────────────────────────────────────────────────────────────


class SetTierRequest(BaseModel):
    symbol: str
    tier: str


@router.post("/tier")
def post_tier(
    body: SetTierRequest,
    db: Database = Depends(get_db),
) -> dict[str, Any]:
    """Updates a company's watchlist tier (GSC, GSC_L1, GSC_L2)."""
    sym = body.symbol.strip().upper()
    target_tier = body.tier.strip().upper()
    with db.write() as session:
        state = portfolio_state(session)
        comp = session.get(CompanyProfile, sym)
        if not comp:
            raise HTTPException(status_code=404, detail=f"Company '{sym}' not found.")
        old_tier = comp.watchlist_category

        # 1. Snapshot state first
        cp = CheckpointManager.create_checkpoint(
            session=session,
            state=state,
            action="SET_TIER",
            description=f"Update {sym} tier {old_tier} -> {target_tier}",
            symbol=sym,
            actor="Kernel API",
        )

        # 2. Mutate state
        comp.watchlist_category = target_tier
        state.rules_revision += 1

        # 3. Write audit rows
        session.add(RuleAudit(
            symbol=sym,
            before={"watchlist_category": old_tier},
            after={"watchlist_category": target_tier},
            session_on=state.clock_date,
        ))
        session.add(KernelAuditLog(
            endpoint="/k/tier",
            action="SET_TIER",
            symbol=sym,
            payload=body.model_dump(),
            result={"old_tier": old_tier, "tier": target_tier},
            checkpoint_id=cp.id,
            session_on=state.clock_date,
        ))

        return {
            "status": "ok",
            "symbol": sym,
            "old_tier": old_tier,
            "tier": target_tier,
            "checkpoint_id": cp.id,
        }


class SetAllocationRequest(BaseModel):
    symbol: str
    buy_allocation_pct: Decimal = Field(ge=0, le=100)
    enabled: bool = True


@router.post("/allocation")
def post_allocation(
    body: SetAllocationRequest,
    db: Database = Depends(get_db),
) -> dict[str, Any]:
    """Updates buying allocation percentage for a company rule."""
    sym = body.symbol.strip().upper()
    with db.write() as session:
        state = portfolio_state(session)
        rule = session.get(CustomRule, sym)
        if not rule:
            raise HTTPException(status_code=404, detail=f"Custom rule for '{sym}' not found.")

        other_allocations = sum(
            session.scalars(select(CustomRule.buy_allocation_pct).where(CustomRule.symbol != sym)),
            ZERO,
        )
        if other_allocations + body.buy_allocation_pct > 100:
            raise HTTPException(status_code=422, detail="Combined company allocations cannot exceed 100%.")

        before = {"buy_allocation_pct": str(rule.buy_allocation_pct), "enabled": rule.enabled}

        # 1. Snapshot state first
        cp = CheckpointManager.create_checkpoint(
            session=session,
            state=state,
            action="UPDATE_ALLOCATION",
            description=f"Update allocation for {sym} to {body.buy_allocation_pct}%",
            symbol=sym,
            actor="Kernel API",
        )

        # 2. Mutate state
        rule.buy_allocation_pct = body.buy_allocation_pct
        rule.enabled = body.enabled
        after = {"buy_allocation_pct": str(rule.buy_allocation_pct), "enabled": rule.enabled}
        state.rules_revision += 1

        # 3. Write audit rows
        session.add(RuleAudit(
            symbol=sym,
            before=before,
            after=after,
            session_on=state.clock_date,
        ))
        session.add(KernelAuditLog(
            endpoint="/k/allocation",
            action="UPDATE_ALLOCATION",
            symbol=sym,
            payload={"symbol": sym, "buy_allocation_pct": str(body.buy_allocation_pct), "enabled": body.enabled},
            result=after,
            checkpoint_id=cp.id,
            session_on=state.clock_date,
        ))

        return {
            "status": "ok",
            "symbol": sym,
            "rule": after,
            "checkpoint_id": cp.id,
        }


class QuarantineRequest(BaseModel):
    symbol: str
    action: str = "quarantine"  # "quarantine" or "restore"
    reason: str = "Kernel API quarantine trigger"


@router.post("/quarantine")
def post_quarantine(
    body: QuarantineRequest,
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Places stock in 90% profit-lock + 10% canary quarantine, or restores it."""
    sym = body.symbol.strip().upper()
    act = body.action.strip().lower()
    with db.write() as session:
        state = portfolio_state(session)
        comp = session.get(CompanyProfile, sym)
        if not comp:
            raise HTTPException(status_code=404, detail=f"Company '{sym}' not found.")

        # 1. Snapshot state first
        cp = CheckpointManager.create_checkpoint(
            session=session,
            state=state,
            action=act.upper(),
            description=f"{act.capitalize()} {sym}: {body.reason}",
            symbol=sym,
            actor="Kernel API",
        )

        # 2. Mutate state via existing engine action
        try:
            if act == "restore":
                res = restore_quarantine(session, state, sym, reason=body.reason)
            else:
                res = emergency_quarantine_and_canary(session, state, settings, sym, thesis_text=body.reason)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        # 3. Write audit row
        session.add(KernelAuditLog(
            endpoint="/k/quarantine",
            action=act.upper(),
            symbol=sym,
            payload=body.model_dump(),
            result=res,
            checkpoint_id=cp.id,
            session_on=state.clock_date,
        ))

        return {
            "status": "ok",
            "symbol": sym,
            "action": act,
            "result": res,
            "checkpoint_id": cp.id,
        }


@router.post("/canary/evaluate")
def post_canary_evaluate(
    db: Database = Depends(get_db),
) -> dict[str, Any]:
    """Evaluates observing canary probe theses against recent price movements."""
    with db.write() as session:
        state = portfolio_state(session)

        # 1. Snapshot state first
        cp = CheckpointManager.create_checkpoint(
            session=session,
            state=state,
            action="CANARY_EVALUATE",
            description="Evaluate active canary theses",
            actor="Kernel API",
        )

        # 2. Mutate state via existing engine action
        updates = check_canary_theses(session, state)

        # 3. Write audit row
        session.add(KernelAuditLog(
            endpoint="/k/canary/evaluate",
            action="CANARY_EVALUATE",
            symbol=None,
            payload={},
            result={"updates": updates},
            checkpoint_id=cp.id,
            session_on=state.clock_date,
        ))

        return {
            "status": "ok",
            "updates": updates,
            "checkpoint_id": cp.id,
        }


class SyncRequest(BaseModel):
    target: str = Field(..., pattern="^(portfolio|favorites|all_shares)$")
    payload: dict[str, Any] | list[Any] | None = None


@router.post("/sync")
async def post_sync(
    body: SyncRequest,
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
    stocknow_client: Any | None = Depends(get_stocknow_client),
) -> dict[str, Any]:
    """Syncs market prices, all-shares board, or virtual portfolio holdings."""
    target = body.target.strip().lower()
    with db.write() as session:
        state = portfolio_state(session)

        # 1. Snapshot state first
        cp = CheckpointManager.create_checkpoint(
            session=session,
            state=state,
            action=f"SYNC_{target.upper()}",
            description=f"Kernel sync target={target}",
            actor="Kernel API",
        )

        # 2. Run existing sync routines
        if target == "favorites":
            quotes = body.payload
            if quotes is None and stocknow_client is not None:
                quotes = await extract_quotes_from_stocknow(stocknow_client)
            if quotes:
                sync_live_market_to_db(db, quotes)
            res: Any = {"synced_quotes": len(quotes) if quotes else 0}

        elif target == "portfolio":
            p_data = body.payload or {"portfolio_id": "164580"}
            res = reconcile_portfolio_to_db(session, settings, p_data, checkpoint_mgr=CheckpointManager)

        elif target == "all_shares":
            res = await get_or_fetch_all_dse_shares(stocknow_client)

        # 3. Write audit row
        res_for_log = res if isinstance(res, dict) else {"count": len(res) if hasattr(res, "__len__") else 0}
        session.add(KernelAuditLog(
            endpoint="/k/sync",
            action=f"SYNC_{target.upper()}",
            symbol=None,
            payload={"target": target, "has_payload": body.payload is not None},
            result=res_for_log,
            checkpoint_id=cp.id,
            session_on=state.clock_date,
        ))

        return {
            "status": "ok",
            "target": target,
            "result": res,
            "checkpoint_id": cp.id,
        }


class OrderRequest(BaseModel):
    idempotency_key: str = Field(..., min_length=1)
    symbol: str
    side: str = Field(..., pattern="^(BUY|SELL|buy|sell)$")
    quantity: int = Field(..., gt=0)
    price: Decimal | None = None
    portfolio_id: str = "164580"
    dry_run: bool = True  # dry_run defaults true


@router.post("/order")
def post_order(
    body: OrderRequest,
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Submits a virtual BUY or SELL order enforcing T+2 maturity, strict no-loss, and 0.5% fees."""
    # 1. Enforce portfolio must be 164580
    if str(body.portfolio_id).strip() != "164580":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Portfolio must be 164580.",
        )

    # 2. Idempotency deduplication check
    if body.idempotency_key in _EXECUTED_ORDER_KEYS:
        cached = dict(_EXECUTED_ORDER_KEYS[body.idempotency_key])
        cached["duplicate"] = True
        cached["status"] = "ALREADY_EXECUTED"
        return cached

    sym = body.symbol.strip().upper()
    side = body.side.strip().upper()
    commission_rate = Decimal("0.005")  # 0.5% commission strictly enforced

    # Pre-validation & execution
    with db.write() as session:
        state = portfolio_state(session)
        comp = session.get(CompanyProfile, sym)
        if not comp:
            raise HTTPException(status_code=404, detail=f"Company '{sym}' not found in database.")

        unit_price = body.price if body.price is not None and body.price > ZERO else comp.last_price
        if unit_price <= ZERO:
            raise HTTPException(status_code=422, detail=f"Invalid unit price '{unit_price}'.")

        # Pre-validate BUY
        if side == "BUY":
            if comp.quarantined:
                raise HTTPException(status_code=422, detail=f"Cannot buy {sym}: Company is under Crash Quarantine.")
            cost, fee = purchase_amount(body.quantity, unit_price, commission_rate)

        # Pre-validate SELL (enforces T+2 maturity and strict no-loss)
        if side == "SELL":
            mature_lots = list(session.scalars(
                select(TaxLot)
                .where(
                    TaxLot.symbol == sym,
                    TaxLot.remaining_qty > 0,
                    TaxLot.matures_on <= state.clock_date,
                )
                .order_by(TaxLot.id)
            ))
            mature_qty = sum(lot.remaining_qty for lot in mature_lots)
            if mature_qty <= 0:
                immature_lots = list(session.scalars(
                    select(TaxLot).where(TaxLot.symbol == sym, TaxLot.remaining_qty > 0)
                ))
                if immature_lots:
                    earliest = min(lot.matures_on for lot in immature_lots)
                    raise HTTPException(
                        status_code=422,
                        detail=f"Cannot sell {sym}: shares are settlement-locked until {earliest.isoformat()} (T+2 lock).",
                    )
                raise HTTPException(status_code=422, detail=f"Cannot sell {sym}: no open shares held.")

            if body.quantity > mature_qty:
                raise HTTPException(
                    status_code=422,
                    detail=f"Cannot sell {body.quantity} shares of {sym}: only {mature_qty} mature shares available.",
                )

            # Strict no-loss verification across mature lots to be sold
            remaining = body.quantity
            total_proceeds = ZERO
            total_basis = ZERO
            for lot in mature_lots:
                if remaining <= 0:
                    break
                sell_slice = min(lot.remaining_qty, remaining)
                proceeds, _fee = sale_amount(sell_slice, unit_price, commission_rate)
                cost_slice = allocated_basis(lot.remaining_cost_basis, lot.remaining_qty, sell_slice)
                if proceeds < cost_slice:
                    net_ret = (proceeds / cost_slice - 1) * Decimal("100")
                    raise HTTPException(
                        status_code=422,
                        detail=f"Cannot sell {sym} at ৳{unit_price}: net return is {float(net_ret):.2f}% (net loss). Strict No-Loss policy holds.",
                    )
                total_proceeds += proceeds
                total_basis += cost_slice
                remaining -= sell_slice

        # Handle dry_run default
        if body.dry_run:
            fee_est = float(fee) if side == "BUY" else float(body.quantity * unit_price * commission_rate)
            net_est = float(cost) if side == "BUY" else float(total_proceeds)
            return {
                "dry_run": True,
                "status": "VALIDATED",
                "idempotency_key": body.idempotency_key,
                "portfolio_id": "164580",
                "symbol": sym,
                "side": side,
                "quantity": body.quantity,
                "price": float(unit_price),
                "commission_pct": 0.5,
                "estimated_fee": fee_est,
                "estimated_net": net_est,
                "note": "Dry run execution validated all constraints (T+2 maturity, strict no-loss, 0.5% fee). No state mutated.",
            }

        # dry_run is False -> Snapshot first, then mutate state
        cp = CheckpointManager.create_checkpoint(
            session=session,
            state=state,
            action=f"ORDER_{side}",
            description=f"Execute {side} {body.quantity} {sym} @ {unit_price}",
            symbol=sym,
            actor="Kernel API",
        )

        try:
            if side == "BUY":
                order_res = execute_agentic_buy(session, state, settings, sym, requested_qty=body.quantity)
            else:
                order_res = execute_agentic_sell(session, state, settings, sym, requested_qty=body.quantity)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=str(exc))

        # Record idempotency
        _EXECUTED_ORDER_KEYS[body.idempotency_key] = order_res

        # Write audit row
        session.add(KernelAuditLog(
            endpoint="/k/order",
            action=f"ORDER_{side}",
            symbol=sym,
            payload=body.model_dump(mode="json"),
            result=order_res,
            checkpoint_id=cp.id,
            session_on=state.clock_date,
        ))

        return {
            **order_res,
            "dry_run": False,
            "checkpoint_id": cp.id,
            "idempotency_key": body.idempotency_key,
            "portfolio_id": "164580",
        }


@router.post("/rollback")
def post_rollback(
    db: Database = Depends(get_db),
) -> dict[str, Any]:
    """Rolls back the last state checkpoint atomically."""
    with db.write() as session:
        state = portfolio_state(session)
        try:
            rollback_res = CheckpointManager.rollback_last(session, state)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        # Write audit row
        session.add(KernelAuditLog(
            endpoint="/k/rollback",
            action="ROLLBACK",
            symbol=None,
            payload={},
            result=rollback_res,
            checkpoint_id=rollback_res.get("checkpoint_id"),
            session_on=state.clock_date,
        ))

        return {
            "status": "ok",
            "rollback": rollback_res,
        }


# ─────────────────────────────────────────────────────────────────────────────
# STANDALONE LOCAL SERVICE FACTORY
# ─────────────────────────────────────────────────────────────────────────────


def build_kernel_router(
    database: Database,
    settings: Settings,
    stocknow_client: Any | None = None,
) -> APIRouter:
    """Builds the configured kernel router for inclusion in main app."""
    return router


def create_kernel_app(
    database: Database | None = None,
    settings: Settings | None = None,
    stocknow_client: Any | None = None,
) -> FastAPI:
    """Creates a standalone FastAPI service for the trading kernel binding 127.0.0.1."""
    from backend.seed import seed_demo

    cfg = settings or Settings()
    db = database or Database(cfg.database_url)
    db.create_schema()
    with db.write() as session:
        seed_demo(session, cfg)

    app = FastAPI(
        title="Humming Bird Trading Kernel",
        description="Clean, deterministic trading engine local service",
        version="1.0.0",
    )
    app.state.database = db
    app.state.settings = cfg
    app.state.stocknow_client = stocknow_client
    app.include_router(router)
    return app
