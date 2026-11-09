"""Humming Bird Trading Kernel API Service.

Exposes clean, deterministic local endpoints for the trading kernel, completely
independent of any agent or LLM code. Binds only to localhost (127.0.0.1).
"""

from __future__ import annotations

import logging
import os
import time
from decimal import Decimal
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select

from backend.adapters.stocknow_market_sync import (
    extract_quotes_from_stocknow,
    get_or_fetch_all_dse_shares,
    sync_live_market_to_db,
)
from backend.adapters.stocknow_portfolio_sync import reconcile_portfolio_to_db
from backend.config import (
    Settings,
    get_active_target_portfolio,
    get_allowed_portfolios,
    get_portfolio_name,
    test_portfolio_configured,
)
from backend.database import (
    CanaryThesis,
    CompanyProfile,
    CustomRule,
    Database,
    DecisionLog,
    KernelAuditLog,
    OrderIdempotencyKey,
    PortfolioState,
    RuleAudit,
    TaxLot,
    TradeLog,
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
from backend.engine.auto_trader import AutoTrader
from backend.engine.scheduler import get_active_scheduler, is_dse_market_open
from backend.engine.price_guard import check_price_sanity, get_market_quote
from backend.engine.trading_lock import acquire_trading_lock
from backend.portfolio import snapshot_from_session

logger = logging.getLogger(__name__)

# Global cache for idempotency keys (in-memory fast-path; SQLite is source of truth)
_EXECUTED_ORDER_KEYS: dict[str, dict[str, Any]] = {}

# Preview tokens store for two-step confirmation (with 5-minute TTL)
_ORDER_PREVIEW_TOKENS: dict[str, dict[str, Any]] = {}

_KERNEL_BROADCASTER: Any | None = None


def get_broadcaster(request: Request | None = None) -> Any:
    """Resolve global or request broadcaster instance."""
    if request and hasattr(request, "app") and hasattr(request.app.state, "broadcaster"):
        return request.app.state.broadcaster
    return _KERNEL_BROADCASTER


def clear_order_idempotency_cache() -> None:
    """Clear order idempotency cache and preview tokens (for tests)."""
    _EXECUTED_ORDER_KEYS.clear()
    _ORDER_PREVIEW_TOKENS.clear()


def verify_kernel_auth(
    request: Request,
    x_kernel_token: str | None = Header(None, alias="X-Kernel-Token"),
    authorization: str | None = Header(None, alias="Authorization"),
) -> None:
    """Enforces 127.0.0.1 localhost binding and X-Kernel-Token / Bearer authentication."""
    # 1. Localhost bind check
    client_host = request.client.host if request.client else "127.0.0.1"
    if client_host not in ("127.0.0.1", "localhost", "testclient", "::1"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Kernel API binds to 127.0.0.1 only.",
        )

    # 2. X-Kernel-Token / Authorization check
    expected = os.getenv("KERNEL_TOKEN")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: KERNEL_TOKEN is not configured.",
        )
    bearer = authorization.replace("Bearer ", "").strip() if authorization and authorization.startswith("Bearer ") else None
    token = x_kernel_token or bearer
    if not token or token != expected:
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
    return Settings.from_env()


def get_stocknow_client(request: Request) -> Any | None:
    """Extract live StockNow Playwright client if attached."""
    client = getattr(request.app.state, "stocknow_client", None)
    if not client:
        sched = get_active_scheduler()
        if sched and hasattr(sched, "client"):
            client = sched.client
    return client


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
            target_pid = get_active_target_portfolio(getattr(state, "trading_mode", "LIVE_HOURS"), settings) or settings.stocknow_live_portfolio_id
            if act == "restore":
                res = restore_quarantine(session, state, sym, reason=body.reason)
            else:
                res = emergency_quarantine_and_canary(session, state, settings, sym, thesis_text=body.reason, portfolio_id=target_pid)
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
        if target in ("favorites", "market", "live_prices", "quotes"):
            quotes = body.payload
            if quotes is None:
                from backend.adapters.stocknow_market_sync import fetch_stocknow_live_market_data
                quotes = await fetch_stocknow_live_market_data(client=stocknow_client, as_of_date=state.clock_date)
            if quotes:
                sync_live_market_to_db(session, quotes, session_date=state.clock_date)
            res: Any = {"synced_quotes": len(quotes) if quotes else 0}

        elif target == "portfolio":
            trading_mode = getattr(state, "trading_mode", "LIVE_HOURS")
            active_pid = get_active_target_portfolio(trading_mode, settings)
            if trading_mode == "TEST_OFFHOURS" and not active_pid:
                raise HTTPException(
                    status_code=422,
                    detail="Sync rejected in Test Mode: STOCKNOW_TEST_PORTFOLIO_ID is not configured. Set STOCKNOW_TEST_PORTFOLIO_ID in .env or switch to LIVE_HOURS.",
                )
            target_pid = active_pid or settings.stocknow_live_portfolio_id
            if isinstance(body.payload, dict) and body.payload.get("portfolio_id"):
                provided_pid = str(body.payload["portfolio_id"]).strip()
                if provided_pid != target_pid:
                    raise HTTPException(
                        status_code=422,
                        detail=f"Cannot sync portfolio '{provided_pid}' in {trading_mode} mode. Active target portfolio is '{target_pid}'.",
                    )
            if body.payload:
                p_data = body.payload
                if isinstance(p_data, dict) and ("scrips" in p_data or "cash_amount" in p_data or "holdings" not in p_data):
                    from backend.adapters.stocknow_portfolio_sync import extract_hummingbird_portfolio
                    p_data = extract_hummingbird_portfolio(injected_portfolio=p_data)
                elif isinstance(p_data, dict) and not p_data.get("portfolio_id"):
                    p_data["portfolio_id"] = target_pid
            else:
                from backend.adapters.stocknow_portfolio_sync import sync_stocknow_portfolio_via_api
                from backend.adapters.stocknow_api import StockNowError
                try:
                    p_data = await sync_stocknow_portfolio_via_api(
                        portfolio_id=target_pid,
                        live_client=stocknow_client,
                        settings=settings,
                    )
                except StockNowError as sne:
                    logger.error("StockNow API sync failed: %s", sne)
                    raise HTTPException(status_code=422, detail={"error": sne.error_code, "detail": str(sne)})
                except Exception as exc:
                    logger.error("StockNow API sync unexpected error: %s", exc)
                    raise HTTPException(status_code=422, detail={"error": "SYNC_FAILED", "detail": str(exc)})
            res = reconcile_portfolio_to_db(session, settings, p_data, checkpoint_mgr=CheckpointManager)

        elif target in ("all_shares", "instruments", "shares"):
            from backend.adapters.stocknow_market_sync import get_or_fetch_all_dse_shares
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


def _compute_order_reconcile_and_drift(
    session: Any,
    state: PortfolioState,
    live_client: Any | None,
    symbol: str,
    portfolio_id: str | None = None,
) -> dict[str, Any]:
    """Verifies local ledger integrity and compares holdings with StockNow to detect drift."""
    from backend.engine.t2_ledger import assert_ledger, bucket_balances
    book_reconciled = True
    try:
        assert_ledger(session, state, portfolio_id=portfolio_id)
    except Exception as exc:
        logger.warning("Local ledger assert warning: %s", exc)
        book_reconciled = False

    balances = bucket_balances(session, state, portfolio_id=portfolio_id)
    local_cash = sum((b.available_cash for b in balances.values()), ZERO)

    lot_q = select(TaxLot).where(TaxLot.remaining_qty > 0)
    if portfolio_id:
        lot_q = lot_q.where(TaxLot.portfolio_id == str(portfolio_id))
    local_lots = list(session.scalars(lot_q))
    local_holdings: dict[str, int] = {}
    for lot in local_lots:
        local_holdings[lot.symbol] = local_holdings.get(lot.symbol, 0) + lot.remaining_qty

    stocknow_holdings: dict[str, int] = {}
    stocknow_cash: float | None = None

    if hasattr(live_client, "mock_holdings"):
        stocknow_holdings = dict(live_client.mock_holdings)
        stocknow_cash = getattr(live_client, "mock_cash", float(local_cash))
    elif live_client and getattr(live_client, "last_reconciled_portfolio", None):
        sn_p = live_client.last_reconciled_portfolio
        for h in sn_p.get("holdings", []):
            stocknow_holdings[h["symbol"]] = stocknow_holdings.get(h["symbol"], 0) + h["quantity"]
        stocknow_cash = float(sn_p.get("cash_balance", 0))

    holdings_drift: dict[str, dict[str, int]] = {}
    if stocknow_holdings:
        all_syms = set(local_holdings.keys()) | set(stocknow_holdings.keys())
        for s in all_syms:
            loc_q = local_holdings.get(s, 0)
            sn_q = stocknow_holdings.get(s, 0)
            if loc_q != sn_q:
                holdings_drift[s] = {"local_qty": loc_q, "stocknow_qty": sn_q, "diff": loc_q - sn_q}

    cash_drift = None
    if stocknow_cash is not None:
        cash_drift = round(float(local_cash) - stocknow_cash, 2)

    has_drift = bool(holdings_drift) or (cash_drift is not None and abs(cash_drift) > 1.0)

    return {
        "book_reconciled": book_reconciled,
        "has_drift": has_drift,
        "holdings_drift": holdings_drift,
        "cash_drift": cash_drift,
        "local_symbol_shares": local_holdings.get(symbol, 0),
    }


def _record_order_rejection(
    session: Any,
    state: PortfolioState,
    symbol: str,
    action: str,
    reason: str,
    trading_mode: str,
    payload: dict[str, Any],
) -> None:
    """Records DecisionLog and KernelAuditLog for any rejected order."""
    session.add(DecisionLog(
        cycle_id=None,
        symbol=symbol,
        action=f"REJECT_{action}",
        reason=reason,
        trading_mode=trading_mode,
    ))
    session.add(KernelAuditLog(
        endpoint="/k/order",
        action=f"REJECT_{action}",
        symbol=symbol,
        payload=payload,
        result={"status": "REJECTED", "reason": reason},
        session_on=state.clock_date,
        trading_mode=trading_mode,
    ))
    session.commit()


class OrderRequest(BaseModel):
    idempotency_key: str = Field(..., min_length=1)
    symbol: str
    side: str = Field(..., pattern="^(BUY|SELL|buy|sell)$")
    quantity: int = Field(..., gt=0)
    price: Decimal | None = None
    portfolio_id: str | None = None
    dry_run: bool = True  # dry_run defaults true
    operator_confirmed: bool = False
    preview_token: str | None = None

    @model_validator(mode="before")
    @classmethod
    def handle_confirm_alias(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "confirm" in data and "operator_confirmed" not in data:
                data["operator_confirmed"] = data["confirm"]
        return data


@router.post("/order")
async def post_order(
    body: OrderRequest,
    request: Request,
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Submits a virtual BUY or SELL order enforcing T+2 maturity, strict no-loss, and 0.5% fees."""
    sym = body.symbol.strip().upper()
    side = body.side.strip().upper()
    commission_rate = Decimal("0.005")  # 0.5% commission strictly enforced

    # Pre-validation & execution under single-writer trading lock
    with acquire_trading_lock():
        with db.write() as session:
            state = portfolio_state(session)
            trading_mode = getattr(state, "trading_mode", "LIVE_HOURS")
            active_pid = get_active_target_portfolio(trading_mode, settings)

            # Block Test Mode if test portfolio is not configured (Requirement: TEST_PORTFOLIO_NOT_CONFIGURED)
            if trading_mode == "TEST_OFFHOURS" and not test_portfolio_configured(settings):
                reason = "Order execution rejected in Test Mode: TEST_PORTFOLIO_NOT_CONFIGURED. STOCKNOW_TEST_PORTFOLIO_ID is not configured or equals live portfolio. Set STOCKNOW_TEST_PORTFOLIO_ID in .env or switch to LIVE_HOURS."
                _record_order_rejection(session, state, sym, "TEST_PORTFOLIO_NOT_CONFIGURED", reason, trading_mode, body.model_dump(mode="json"))
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=reason,
                )

            # Resolve target portfolio ID
            target_pid = str(body.portfolio_id or active_pid or "").strip()

            # Enforce allowlist (Requirement 1)
            allowed_portfolios = get_allowed_portfolios(settings)
            if target_pid not in allowed_portfolios:
                reason = f"Unauthorized portfolio '{target_pid}'. Allowed portfolios: {list(allowed_portfolios)}."
                _record_order_rejection(session, state, sym, "UNAUTHORIZED_PORTFOLIO", reason, trading_mode, body.model_dump(mode="json"))
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=reason,
                )

            # Enforce mode matching (Requirement 2): Test Mode -> test portfolio only; Live Hours -> 164580 only
            if trading_mode == "TEST_OFFHOURS" and target_pid != active_pid:
                reason = f"Order rejected: Test Mode sends orders only to the configured test portfolio '{active_pid}', but received '{target_pid}'."
                _record_order_rejection(session, state, sym, "PORTFOLIO_MODE_MISMATCH", reason, trading_mode, body.model_dump(mode="json"))
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=reason,
                )
            elif trading_mode == "LIVE_HOURS" and target_pid != settings.stocknow_live_portfolio_id:
                reason = f"Order rejected: LIVE_HOURS mode sends orders only to the live portfolio '{settings.stocknow_live_portfolio_id}', but received '{target_pid}'."
                _record_order_rejection(session, state, sym, "PORTFOLIO_MODE_MISMATCH", reason, trading_mode, body.model_dump(mode="json"))
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=reason,
                )

            # 2. SQLite Idempotency Deduplication Check (persists across server restarts)
            existing_key = session.get(OrderIdempotencyKey, body.idempotency_key)
            if existing_key:
                cached = dict(existing_key.response_payload)
                cached["duplicate"] = True
                cached["status"] = "ALREADY_EXECUTED"
                return cached

            if body.idempotency_key in _EXECUTED_ORDER_KEYS:
                cached = dict(_EXECUTED_ORDER_KEYS[body.idempotency_key])
                cached["duplicate"] = True
                cached["status"] = "ALREADY_EXECUTED"
                return cached

            comp = session.get(CompanyProfile, sym)
            if not comp:
                raise HTTPException(status_code=404, detail=f"Company '{sym}' not found in database.")

            unit_price = body.price if body.price is not None and body.price > ZERO else comp.last_price
            if unit_price <= ZERO:
                raise HTTPException(status_code=422, detail=f"Invalid unit price '{unit_price}'.")

            # 3. Global Kill Switch Check (AutoTrader & Hermes shared)
            if getattr(state, "kill_switch_active", False):
                reason = "Order rejected: Global kill switch is active."
                _record_order_rejection(session, state, sym, "KILL_SWITCH", reason, trading_mode, body.model_dump(mode="json"))
                raise HTTPException(status_code=422, detail=reason)

            # 4. Max Orders Per Day Check (AutoTrader & Hermes shared, scoped by portfolio)
            max_orders = getattr(state, "max_orders_per_day", 20)
            today_orders_count = len(session.scalars(select(TradeLog.id).where(
                TradeLog.trade_on == state.clock_date,
                TradeLog.portfolio_id == target_pid,
            )).all())
            if today_orders_count >= max_orders:
                reason = f"Order rejected: Daily order limit reached ({today_orders_count}/{max_orders} orders executed today for portfolio {target_pid})."
                _record_order_rejection(session, state, sym, "DAILY_ORDER_LIMIT", reason, trading_mode, body.model_dump(mode="json"))
                raise HTTPException(status_code=422, detail=reason)

            # 5. Max Order Gross Cap Check (AutoTrader & Hermes shared)
            max_order_bdt = getattr(state, "max_order_bdt", None)
            order_gross = body.quantity * unit_price
            if max_order_bdt is not None and order_gross > max_order_bdt:
                reason = f"Order rejected: Order amount ৳{float(order_gross):.2f} exceeds max order cap of ৳{float(max_order_bdt):.2f}."
                _record_order_rejection(session, state, sym, "MAX_ORDER_CAP", reason, trading_mode, body.model_dump(mode="json"))
                raise HTTPException(status_code=422, detail=reason)

            # Pre-validate BUY
            if side == "BUY":
                if comp.quarantined:
                    reason = f"Cannot buy {sym}: Company is under Crash Quarantine."
                    _record_order_rejection(session, state, sym, "QUARANTINE", reason, trading_mode, body.model_dump(mode="json"))
                    raise HTTPException(status_code=422, detail=reason)

                cost, fee = purchase_amount(body.quantity, unit_price, commission_rate)

                # 6. Max Symbol Exposure Cap Check (AutoTrader & Hermes shared, scoped by portfolio)
                max_symbol_bdt = getattr(state, "max_symbol_bdt", None)
                open_basis = sum(session.scalars(select(TaxLot.remaining_cost_basis).where(
                    TaxLot.symbol == sym, TaxLot.remaining_qty > 0, TaxLot.portfolio_id == target_pid,
                )), ZERO)
                new_symbol_exposure = open_basis + (body.quantity * unit_price)
                if max_symbol_bdt is not None and new_symbol_exposure > max_symbol_bdt:
                    reason = f"Order rejected: Symbol {sym} total exposure ৳{float(new_symbol_exposure):.2f} exceeds max symbol cap of ৳{float(max_symbol_bdt):.2f}."
                    _record_order_rejection(session, state, sym, "MAX_SYMBOL_CAP", reason, trading_mode, body.model_dump(mode="json"))
                    raise HTTPException(status_code=422, detail=reason)

                # 7. Daily Buy Budget Exhaustion Check (AutoTrader & Hermes shared, scoped by portfolio)
                daily_budget_bdt = getattr(state, "daily_budget_bdt", Decimal("4000.00"))
                today_buys_spend = sum(
                    (abs(t.net_cash_change) for t in session.scalars(
                        select(TradeLog).where(
                            TradeLog.trade_on == state.clock_date,
                            TradeLog.side == "BUY",
                            TradeLog.portfolio_id == target_pid,
                        )
                    )),
                    ZERO,
                )
                if (today_buys_spend + cost) > daily_budget_bdt:
                    reason = f"Order rejected: Daily buy spend would reach ৳{float(today_buys_spend + cost):.2f}, exceeding daily budget cap of ৳{float(daily_budget_bdt):.2f} for portfolio {target_pid}."
                    _record_order_rejection(session, state, sym, "DAILY_BUDGET_EXHAUSTED", reason, trading_mode, body.model_dump(mode="json"))
                    raise HTTPException(status_code=422, detail=reason)

            # Pre-validate SELL (enforces T+2 maturity and strict no-loss, scoped by portfolio)
            if side == "SELL":
                mature_lots = list(session.scalars(
                    select(TaxLot)
                    .where(
                        TaxLot.symbol == sym,
                        TaxLot.remaining_qty > 0,
                        TaxLot.portfolio_id == target_pid,
                        TaxLot.matures_on <= state.clock_date,
                    )
                    .order_by(TaxLot.id)
                ))
                mature_qty = sum(lot.remaining_qty for lot in mature_lots)
                if mature_qty <= 0:
                    immature_lots = list(session.scalars(
                        select(TaxLot).where(TaxLot.symbol == sym, TaxLot.remaining_qty > 0, TaxLot.portfolio_id == target_pid)
                    ))
                    if immature_lots:
                        earliest = min(lot.matures_on for lot in immature_lots)
                        reason = f"Cannot sell {sym}: shares are settlement-locked until {earliest.isoformat()} (T+2 lock)."
                    else:
                        reason = f"Cannot sell {sym}: no open shares held in portfolio {target_pid}."
                    _record_order_rejection(session, state, sym, "SETTLEMENT_LOCK", reason, trading_mode, body.model_dump(mode="json"))
                    raise HTTPException(status_code=422, detail=reason)

                if body.quantity > mature_qty:
                    reason = f"Cannot sell {body.quantity} shares of {sym}: only {mature_qty} mature shares available in portfolio {target_pid}."
                    _record_order_rejection(session, state, sym, "INSUFFICIENT_SHARES", reason, trading_mode, body.model_dump(mode="json"))
                    raise HTTPException(status_code=422, detail=reason)

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
                        reason = f"Cannot sell {sym} at ৳{unit_price}: net return is {float(net_ret):.2f}% (net loss). Strict No-Loss policy holds."
                        _record_order_rejection(session, state, sym, "STRICT_NO_LOSS", reason, trading_mode, body.model_dump(mode="json"))
                        raise HTTPException(status_code=422, detail=reason)
                    total_proceeds += proceeds
                    total_basis += cost_slice
                    remaining -= sell_slice

            # Market hours gate (bypassed only when trading_mode == 'TEST_OFFHOURS')
            if not body.dry_run and trading_mode != "TEST_OFFHOURS":
                market_gate = is_dse_market_open(settings=settings)
                if not market_gate["is_open"]:
                    reason = f"DSE market is closed ({market_gate['reason']}). Orders in LIVE_HOURS mode are strictly limited to Sun-Thu 10:00 to 14:30 Asia/Dhaka."
                    _record_order_rejection(session, state, sym, "MARKET_CLOSED", reason, trading_mode, body.model_dump(mode="json"))
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=reason,
                    )

            # 8. Price Sanity Guard (AutoTrader & Hermes shared, preflight for buy and sell)
            max_dev_pct = getattr(settings, "price_max_deviation_pct", 1.5)
            quote = get_market_quote(sym, comp=comp)
            ltp = quote.get("ltp") if quote else None
            day_low = quote.get("day_low") if quote else None
            day_high = quote.get("day_high") if quote else None

            if ltp is None or float(ltp) <= 0:
                if trading_mode == "LIVE_HOURS":
                    reason = f"Order rejected: No live market quote available for {sym} (NO_QUOTE)."
                    _record_order_rejection(session, state, sym, "NO_QUOTE", reason, trading_mode, body.model_dump(mode="json"))
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=reason,
                    )
                else:
                    # In TEST_OFFHOURS, missing quote uses last close and continues
                    last_close = None
                    if quote and quote.get("close") and float(quote["close"]) > 0:
                        last_close = float(quote["close"])
                    elif comp.price_history:
                        try:
                            last_close = float(comp.price_history[-1].get("close"))
                        except Exception:
                            pass
                    if last_close is None and comp.last_price and float(comp.last_price) > 0:
                        last_close = float(comp.last_price)
                    ltp = last_close

            ok, reason_code = check_price_sanity(
                price=unit_price,
                ltp=ltp,
                day_low=day_low,
                day_high=day_high,
                max_pct=max_dev_pct,
            )
            if not ok:
                if reason_code == "NO_QUOTE":
                    reason = f"Order rejected: No market quote available for {sym} (NO_QUOTE)."
                else:
                    reason = f"Order rejected: Price ৳{float(unit_price):.2f} is out of acceptable market range (PRICE_OUT_OF_RANGE)."
                _record_order_rejection(session, state, sym, reason_code, reason, trading_mode, body.model_dump(mode="json"))
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=reason,
                )

            # Handle dry_run default: generate preview token
            if body.dry_run:
                fee_est = float(fee) if side == "BUY" else float(body.quantity * unit_price * commission_rate)
                net_est = float(cost) if side == "BUY" else float(total_proceeds)
                token = f"prev_{uuid4().hex[:12]}"
                _ORDER_PREVIEW_TOKENS[token] = {
                    "symbol": sym,
                    "side": side,
                    "quantity": body.quantity,
                    "price": float(unit_price),
                    "portfolio_id": target_pid,
                    "created_at": time.time(),
                    "expires_at": time.time() + 300,
                }

                if side == "BUY":
                    daily_limit = float(daily_budget_bdt) if daily_budget_bdt is not None else 4000.0
                    spent_before = float(today_buys_spend)
                    spent_after = float(today_buys_spend + cost)
                    daily_pct = round((spent_after / daily_limit) * 100, 1) if daily_limit > 0 else 0.0
                    cap_usage = {
                        "side": "BUY",
                        "today_orders": today_orders_count,
                        "max_orders": max_orders,
                        "orders_ratio": f"{today_orders_count + 1}/{max_orders}",
                        "order_gross": float(order_gross),
                        "max_order_bdt": float(max_order_bdt) if max_order_bdt is not None else None,
                        "daily_budget_spent": spent_before,
                        "daily_budget_after": spent_after,
                        "daily_budget_limit": daily_limit,
                        "daily_budget_pct": daily_pct,
                        "symbol_exposure": float(new_symbol_exposure),
                        "max_symbol_bdt": float(max_symbol_bdt) if max_symbol_bdt is not None else None,
                        "summary": f"Daily budget: ৳{spent_after:,.2f} / ৳{daily_limit:,.2f} ({daily_pct}%) · Orders: {today_orders_count + 1}/{max_orders}",
                    }
                else:
                    cap_usage = {
                        "side": "SELL",
                        "today_orders": today_orders_count,
                        "max_orders": max_orders,
                        "orders_ratio": f"{today_orders_count + 1}/{max_orders}",
                        "order_gross": float(order_gross),
                        "max_order_bdt": float(max_order_bdt) if max_order_bdt is not None else None,
                        "mature_shares_available": int(mature_qty),
                        "shares_to_sell": int(body.quantity),
                        "summary": f"Orders: {today_orders_count + 1}/{max_orders} · Selling {body.quantity} of {mature_qty} mature shares",
                    }

                return {
                    "dry_run": True,
                    "status": "VALIDATED",
                    "preview_token": token,
                    "idempotency_key": body.idempotency_key,
                    "portfolio_id": target_pid,
                    "portfolio_name": get_portfolio_name(target_pid, settings),
                    "symbol": sym,
                    "side": side,
                    "quantity": body.quantity,
                    "price": float(unit_price),
                    "commission_pct": 0.5,
                    "estimated_fee": fee_est,
                    "estimated_net": net_est,
                    "trading_mode": trading_mode,
                    "cap_usage": cap_usage,
                    "note": "Dry run execution validated all constraints (T+2 maturity, strict no-loss, 0.5% fee). Preview token generated for operator confirmation.",
                }

            # Confirmation enforcement for real execution (dry_run=False)
            if not body.operator_confirmed:
                reason = "Order execution rejected: operator_confirmed must be true. Operator confirmation is required for real virtual order execution."
                _record_order_rejection(session, state, sym, "UNCONFIRMED", reason, trading_mode, body.model_dump(mode="json"))
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=reason,
                )

            if trading_mode == "LIVE_HOURS":
                # In LIVE_HOURS, a valid two-step preview token is strictly required
                if not body.preview_token:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="In LIVE_HOURS mode, real execution requires a two-step preview token from a prior dry_run preview.",
                    )
                token_data = _ORDER_PREVIEW_TOKENS.get(body.preview_token)
                if not token_data or token_data.get("expires_at", 0) < time.time():
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Invalid or expired preview token. Please re-run order preview to obtain a fresh token.",
                    )
                if (
                    token_data["symbol"] != sym
                    or token_data["side"] != side
                    or token_data["quantity"] != body.quantity
                    or (token_data.get("portfolio_id") and token_data["portfolio_id"] != target_pid)
                ):
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Preview token mismatch: order parameters do not match the preview token.",
                    )
                _ORDER_PREVIEW_TOKENS.pop(body.preview_token, None)
            else:
                # In TEST_OFFHOURS, clear imperative command with operator_confirmed=True may execute in one step
                if body.preview_token and body.preview_token in _ORDER_PREVIEW_TOKENS:
                    _ORDER_PREVIEW_TOKENS.pop(body.preview_token, None)

            # Checkpoint BEFORE any external dispatch or local ledger mutation
            existing_lots = session.scalars(select(TaxLot)).all()
            existing_trades = session.scalars(select(TradeLog)).all()
            lots_snap = [{
                "id": l.id, "symbol": l.symbol, "bucket": l.bucket, "acquired_on": l.acquired_on.isoformat(),
                "matures_on": l.matures_on.isoformat(), "original_qty": l.original_qty, "remaining_qty": l.remaining_qty,
                "buy_price": str(l.buy_price), "buy_fee": str(l.buy_fee), "original_cost_basis": str(l.original_cost_basis),
                "remaining_cost_basis": str(l.remaining_cost_basis), "cycle_base_qty": l.cycle_base_qty,
                "next_tier": l.next_tier, "last_sale_revision": l.last_sale_revision, "peak_price": str(l.peak_price),
                "phase": l.phase, "recovery_anchor": str(l.recovery_anchor) if l.recovery_anchor else None,
            } for l in existing_lots]
            trades_snap = [{
                "id": t.id, "trade_key": t.trade_key, "cycle_id": t.cycle_id, "lot_id": t.lot_id, "symbol": t.symbol,
                "side": t.side, "quantity": t.quantity, "price": str(t.price), "gross_amount": str(t.gross_amount),
                "fee": str(t.fee), "net_cash_change": str(t.net_cash_change), "realized_pnl": str(t.realized_pnl),
                "bucket": t.bucket, "trade_on": t.trade_on.isoformat(), "settles_on": t.settles_on.isoformat(),
                "reason": t.reason, "source": t.source,
            } for t in existing_trades]

            cp = CheckpointManager.create_checkpoint(
                session=session,
                state=state,
                action=f"ORDER_{side}",
                description=f"Execute {side} {body.quantity} {sym} @ {unit_price}",
                symbol=sym,
                actor="Kernel API",
                extra_snapshot={
                    "portfolio_lots": lots_snap,
                    "portfolio_trades": trades_snap,
                    "initial_capital": str(state.initial_capital),
                },
            )

            # Call StockNowAdapter.execute_order (delegates to StockNowExecutor transports)
            live_client = get_stocknow_client(request)
            from backend.adapters.stocknow_adapter import StockNowAdapter
            from backend.adapters.stocknow_executor import (
                StockNowExecutionError,
                notify_order_failure,
                NoReceiptExecutionError,
            )
            # Paper fill only when data source is explicitly DEMO
            is_demo_source = getattr(comp, "source", "").startswith("DEMO") or trading_mode == "DEMO"
            adapter = StockNowAdapter(mode="DEMO" if is_demo_source else "LIVE")

            try:
                receipt = await adapter.execute_order(
                    symbol=sym,
                    side=side,
                    quantity=body.quantity,
                    price=unit_price,
                    portfolio_id=target_pid,
                    trade_date=state.clock_date,
                    commission_pct=Decimal("0.5"),
                    idempotency_key=body.idempotency_key,
                    dry_run=False,
                    live_client=live_client,
                    ingestion_mode=getattr(state, "ingestion_mode", "BACKGROUND_POLLING"),
                    settings=settings,
                )
                if not receipt or not receipt.get("success") or receipt.get("status") not in ("ACKNOWLEDGED", "EXECUTED", "FILLED"):
                    raise NoReceiptExecutionError(f"StockNow virtual order rejected or unacknowledged: {receipt.get('status') if receipt else 'NONE'}")

                # Update local ledger ONLY after receipt matches and is verified
                trade_source = "DEMO_PAPER" if is_demo_source else "STOCKNOW_RECEIPT"
                if side == "BUY":
                    order_res = execute_agentic_buy(session, state, settings, sym, requested_qty=body.quantity, portfolio_id=target_pid, trade_date=state.clock_date, source=trade_source)
                else:
                    order_res = execute_agentic_sell(session, state, settings, sym, requested_qty=body.quantity, portfolio_id=target_pid, trade_date=state.clock_date, source=trade_source)

            except StockNowExecutionError as exc:
                logger.error("StockNow execution failure [%s] for %s %s: %s. Rolling back checkpoint %s.", exc.error_code, side, sym, exc.message, cp.id)
                try:
                    CheckpointManager.rollback_last(session, state)
                except Exception as rb_exc:
                    logger.warning("Checkpoint rollback error: %s", rb_exc)
                await notify_order_failure(
                    session=session,
                    state=state,
                    settings=settings,
                    broadcaster=_KERNEL_BROADCASTER,
                    symbol=sym,
                    side=side,
                    quantity=body.quantity,
                    error_code=exc.error_code,
                    detail=exc.message,
                    endpoint="/k/order",
                )
                session.commit()
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={"error": exc.error_code, "detail": exc.message},
                )
            except HTTPException:
                raise
            except Exception as exc:
                logger.error("Order path failure for %s %s: %s. Rolling back checkpoint %s.", side, sym, exc, cp.id)
                try:
                    CheckpointManager.rollback_last(session, state)
                except Exception as rb_exc:
                    logger.warning("Checkpoint rollback error: %s", rb_exc)
                await notify_order_failure(
                    session=session,
                    state=state,
                    settings=settings,
                    broadcaster=_KERNEL_BROADCASTER,
                    symbol=sym,
                    side=side,
                    quantity=body.quantity,
                    error_code="NO_RECEIPT",
                    detail=str(exc),
                    endpoint="/k/order",
                )
                session.commit()
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={"error": "NO_RECEIPT", "detail": str(exc)},
                )

            # Portfolio reconciliation & drift report
            reconcile_report = _compute_order_reconcile_and_drift(session, state, live_client, sym, portfolio_id=target_pid)

            final_res = {
                **order_res,
                "dry_run": False,
                "checkpoint_id": cp.id,
                "idempotency_key": body.idempotency_key,
                "portfolio_id": target_pid,
                "portfolio_name": get_portfolio_name(target_pid, settings),
                "stocknow_receipt": receipt,
                "reconcile": reconcile_report,
                "trading_mode": trading_mode,
            }

            session.add(OrderIdempotencyKey(
                idempotency_key=body.idempotency_key,
                symbol=sym,
                side=side,
                quantity=body.quantity,
                price=unit_price,
                response_payload=final_res,
            ))
            _EXECUTED_ORDER_KEYS[body.idempotency_key] = final_res

            session.add(KernelAuditLog(
                endpoint="/k/order",
                action=f"ORDER_{side}",
                symbol=sym,
                payload=body.model_dump(mode="json"),
                result=final_res,
                checkpoint_id=cp.id,
                session_on=state.clock_date,
                trading_mode=trading_mode,
            ))

            return final_res


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
# AUTOMATION CONTROL & SCHEDULER ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────


class SetTradingModeRequest(BaseModel):
    trading_mode: Literal["TEST_OFFHOURS", "LIVE_HOURS"]
    confirm: bool = False


@router.get("/mode")
def get_trading_mode(db: Database = Depends(get_db)) -> dict[str, Any]:
    """Returns current trading mode (TEST_OFFHOURS or LIVE_HOURS)."""
    with db.read() as session:
        state = portfolio_state(session)
        return {
            "status": "ok",
            "trading_mode": getattr(state, "trading_mode", "LIVE_HOURS"),
            "allowed_modes": ["TEST_OFFHOURS", "LIVE_HOURS"],
        }


@router.post("/mode")
def post_trading_mode(
    body: SetTradingModeRequest,
    db: Database = Depends(get_db),
) -> dict[str, Any]:
    """Sets trading mode to TEST_OFFHOURS or LIVE_HOURS with snapshot and audit log."""
    new_mode = body.trading_mode
    if new_mode == "TEST_OFFHOURS" and not body.confirm:
        raise HTTPException(
            status_code=422,
            detail="Switching to TEST_OFFHOURS bypasses DSE market hours and requires explicit operator confirmation (confirm=true).",
        )

    with db.write() as session:
        state = portfolio_state(session)
        before_mode = getattr(state, "trading_mode", "LIVE_HOURS")

        cp = CheckpointManager.create_checkpoint(
            session=session,
            state=state,
            action="SET_TRADING_MODE",
            description=f"Switch trading mode {before_mode} -> {new_mode}",
            actor="Kernel API",
        )

        state.trading_mode = new_mode

        audit = KernelAuditLog(
            endpoint="/k/mode",
            action="SET_TRADING_MODE",
            symbol=None,
            payload=body.model_dump(),
            result={"status": "SUCCESS", "trading_mode": new_mode, "previous_mode": before_mode},
            checkpoint_id=cp.id,
            session_on=state.clock_date,
            trading_mode=new_mode,
        )
        session.add(audit)

        return {
            "status": "ok",
            "trading_mode": state.trading_mode,
            "previous_mode": before_mode,
            "checkpoint_id": cp.id,
        }


class SetAutomationConfigRequest(BaseModel):
    automation_enabled: bool | None = None
    paused: bool | None = None
    ingestion_mode: str | None = None  # "BACKGROUND_POLLING" or "ONSCREEN_LIVE"
    polling_interval_sec: int | None = Field(None, ge=5, le=3600)


@router.get("/automation")
def get_automation_config(db: Database = Depends(get_db)) -> dict[str, Any]:
    """Returns master buy/sell automation switch, paused state, ingestion mode, and polling interval."""
    with db.read() as session:
        state = portfolio_state(session)
        return {
            "automation_enabled": bool(getattr(state, "automation_enabled", True)),
            "paused": bool(getattr(state, "paused", False)),
            "ingestion_mode": getattr(state, "ingestion_mode", "BACKGROUND_POLLING"),
            "polling_interval_sec": int(getattr(state, "polling_interval_sec", 120)),
        }


@router.post("/automation")
def post_automation_config(
    body: SetAutomationConfigRequest,
    db: Database = Depends(get_db),
) -> dict[str, Any]:
    """Updates master automation switch, paused state, ingestion mode, or polling interval with snapshot & audit."""
    with db.write() as session:
        state = portfolio_state(session)

        # Circuit breaker check when enabling
        if body.automation_enabled is True or body.paused is False:
            if getattr(state, "circuit_breaker_tripped", False):
                raise HTTPException(
                    status_code=422,
                    detail=f"Circuit breaker is tripped: {state.circuit_breaker_reason}. Reset breaker first via /k/automation/circuit-breaker/reset.",
                )

        # Preflight check when enabling or switching to Background mode
        target_mode_candidate = body.ingestion_mode or state.ingestion_mode
        target_enabled_candidate = body.automation_enabled if body.automation_enabled is not None else (not body.paused if body.paused is not None else state.automation_enabled)
        if target_mode_candidate == "BACKGROUND_POLLING" and target_enabled_candidate:
            from backend.engine.preflight_service import are_caps_set, has_passing_preflight_within_24h
            if not are_caps_set(db) or not has_passing_preflight_within_24h(db):
                raise HTTPException(
                    status_code=422,
                    detail="Enabling Background mode requires risk caps set and a passing preflight check within the last 24 hours.",
                )

        # 1. Snapshot state first
        cp = CheckpointManager.create_checkpoint(
            session=session,
            state=state,
            action="SET_AUTOMATION",
            description="Update automation config",
            actor="Kernel API",
        )

        before = {
            "automation_enabled": getattr(state, "automation_enabled", True),
            "paused": getattr(state, "paused", False),
            "ingestion_mode": getattr(state, "ingestion_mode", "BACKGROUND_POLLING"),
            "polling_interval_sec": getattr(state, "polling_interval_sec", 120),
        }

        # 2. Mutate state
        if body.automation_enabled is not None:
            state.automation_enabled = body.automation_enabled
        if body.paused is not None:
            state.paused = body.paused
        if body.ingestion_mode is not None:
            mode = body.ingestion_mode.strip().upper()
            if mode not in ("BACKGROUND_POLLING", "ONSCREEN_LIVE"):
                raise HTTPException(status_code=422, detail=f"Invalid ingestion mode '{body.ingestion_mode}'.")
            state.ingestion_mode = mode
        if body.polling_interval_sec is not None:
            state.polling_interval_sec = body.polling_interval_sec

        state.rules_revision += 1

        after = {
            "automation_enabled": bool(state.automation_enabled),
            "paused": bool(state.paused),
            "ingestion_mode": state.ingestion_mode,
            "polling_interval_sec": state.polling_interval_sec,
        }

        # 3. Write audit log
        session.add(KernelAuditLog(
            endpoint="/k/automation",
            action="SET_AUTOMATION",
            symbol=None,
            payload=body.model_dump(),
            result=after,
            checkpoint_id=cp.id,
            session_on=state.clock_date,
        ))

        return {
            "status": "ok",
            "checkpoint_id": cp.id,
            **after,
        }


class KernelHandoffRequest(BaseModel):
    target_mode: str = Field(..., pattern="^(BACKGROUND_POLLING|ONSCREEN_LIVE|BACKGROUND_24_7|BACKGROUND 24/7)$")


@router.post("/automation/handoff")
def post_automation_handoff(
    body: KernelHandoffRequest,
    db: Database = Depends(get_db),
) -> dict[str, Any]:
    """Single-writer run mode handoff: finishes current cycle under lock, then switches mode."""
    target = "BACKGROUND_POLLING" if body.target_mode in ("BACKGROUND_24_7", "BACKGROUND 24/7") else body.target_mode
    if target == "BACKGROUND_POLLING":
        from backend.engine.preflight_service import are_caps_set, has_passing_preflight_within_24h
        if not are_caps_set(db) or not has_passing_preflight_within_24h(db):
            raise HTTPException(
                status_code=422,
                detail="Enabling Background mode requires risk caps set and a passing preflight check within the last 24 hours.",
            )

    with acquire_trading_lock():
        with db.write() as session:
            state = portfolio_state(session)
            old_mode = state.ingestion_mode
            state.ingestion_mode = target
            state.rules_revision += 1

            sched = get_active_scheduler()
            if target == "BACKGROUND_POLLING":
                if sched and state.automation_enabled and not state.paused:
                    sched.start()
            elif target == "ONSCREEN_LIVE":
                if sched:
                    sched.stop_sync()

            cp = CheckpointManager.create_checkpoint(
                session=session,
                state=state,
                action="HANDOFF_MODE",
                description=f"Handoff from {old_mode} to {target}",
                actor="Kernel API",
            )
            session.add(KernelAuditLog(
                endpoint="/k/automation/handoff",
                action="HANDOFF_MODE",
                symbol=None,
                payload={"target_mode": target, "old_mode": old_mode},
                result={"status": "HANDOFF_COMPLETE", "active_mode": target},
                checkpoint_id=cp.id,
                session_on=state.clock_date,
            ))

            return {
                "status": "HANDOFF_COMPLETE",
                "checkpoint_id": cp.id,
                "old_mode": old_mode,
                "active_mode": target,
                "automation_enabled": state.automation_enabled,
            }


@router.post("/automation/circuit-breaker/reset")
def post_reset_circuit_breaker(
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Manually resets the tripped circuit breaker and clears consecutive failure count."""
    from backend.engine.circuit_breaker import reset_circuit_breaker
    return reset_circuit_breaker(db, settings, actor="Kernel API")


@router.post("/automation/preflight")
def post_run_preflight(
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Executes the preflight check suite and returns the readiness audit."""
    from backend.engine.preflight_service import run_cockpit_preflight
    return run_cockpit_preflight(db, settings, actor="Kernel API")


class SchedulerActionRequest(BaseModel):
    action: str = Field(..., pattern="^(start|stop|status)$")


@router.get("/scheduler")
def get_scheduler_status(
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Returns current scheduler operational status and telemetry."""
    sched = get_active_scheduler()
    if not sched:
        return {
            "running": False,
            "status": "UNAVAILABLE",
            "market": is_dse_market_open(settings=settings),
        }
    return sched.get_status()


@router.post("/scheduler")
def post_scheduler_control(
    body: SchedulerActionRequest,
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Controls background market scheduler (start, stop, status)."""
    action = body.action.strip().lower()
    sched = get_active_scheduler()

    if action == "status":
        if not sched:
            return {"status": "UNAVAILABLE", "running": False, "market": is_dse_market_open(settings=settings)}
        return sched.get_status()

    # Writes snapshot and audit before start/stop
    with db.write() as session:
        state = portfolio_state(session)
        cp = CheckpointManager.create_checkpoint(
            session=session,
            state=state,
            action=f"SCHEDULER_{action.upper()}",
            description=f"Scheduler control: {action}",
            actor="Kernel API",
        )

        result: dict[str, Any]
        if not sched:
            result = {"status": "UNAVAILABLE", "message": "No active scheduler registered"}
        elif action == "start":
            result = sched.start()
        elif action == "stop":
            result = sched.stop_sync()
        else:
            result = {"status": "UNKNOWN_ACTION"}

        session.add(KernelAuditLog(
            endpoint="/k/scheduler",
            action=f"SCHEDULER_{action.upper()}",
            symbol=None,
            payload=body.model_dump(),
            result=result,
            checkpoint_id=cp.id,
            session_on=state.clock_date,
        ))

        return {
            "status": "ok",
            "action": action,
            "checkpoint_id": cp.id,
            "scheduler": result,
        }


class RunCycleRequest(BaseModel):
    dry_run: bool = True
    idempotency_key: str | None = None


@router.post("/cycle")
def post_run_cycle(
    body: RunCycleRequest,
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Executes an automation trading cycle via AutoTrader under the single-writer trading lock."""
    with acquire_trading_lock():
        with db.write() as session:
            state = portfolio_state(session)
            auto_enabled = getattr(state, "automation_enabled", not getattr(state, "paused", False))
            is_dry = body.dry_run if body.dry_run is not None else not auto_enabled

            # 1. Snapshot state first
            cp = CheckpointManager.create_checkpoint(
                session=session,
                state=state,
                action="RUN_CYCLE",
                description=f"Run cycle (dry_run={is_dry})",
                actor="Kernel API",
            )

            # 2. Run AutoTrader cycle
            trader = AutoTrader(db, settings)
            cycle_result = trader.run_cycle(request_id=body.idempotency_key, session=session, dry_run=is_dry)

            # 3. Write audit row
            session.add(KernelAuditLog(
                endpoint="/k/cycle",
                action="RUN_CYCLE",
                symbol=None,
                payload=body.model_dump(),
                result={"cycle_id": cycle_result.get("id"), "trades_count": len(cycle_result.get("trades", []))},
                checkpoint_id=cp.id,
                session_on=state.clock_date,
            ))

            return {
                "status": "ok",
                "checkpoint_id": cp.id,
                "dry_run": is_dry,
                "cycle": cycle_result,
            }


class StockNowSessionActionRequest(BaseModel):
    action: str = Field(..., pattern="^(launch|status|login|logout)$")
    mode: str | None = None


@router.post("/stocknow/session")
async def post_stocknow_session(
    body: StockNowSessionActionRequest,
    request: Request,
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
    stocknow_client: Any | None = Depends(get_stocknow_client),
) -> dict[str, Any]:
    """Controls live StockNow session (launch, status, login, logout)."""
    action = body.action.strip().lower()

    if action == "status":
        if not stocknow_client:
            return {"status": "UNAVAILABLE", "connected": False}
        return stocknow_client.get_status()

    # Write snapshot and audit
    with db.write() as session:
        state = portfolio_state(session)
        cp = CheckpointManager.create_checkpoint(
            session=session,
            state=state,
            action=f"STOCKNOW_{action.upper()}",
            description=f"StockNow session {action}",
            actor="Kernel API",
        )

        res: dict[str, Any]
        if action == "logout":
            browser_res = {"status": "LOGGED_OUT", "transport": "BROWSER"}
            if stocknow_client and hasattr(stocknow_client, "logout"):
                browser_res = await stocknow_client.logout()

            api_res = {"status": "LOGGED_OUT", "transport": "API"}
            api_client = getattr(request.app.state, "stocknow_api", None)
            if api_client and hasattr(api_client, "logout"):
                await api_client.logout()
            res = {"status": "LOGGED_OUT", "browser": browser_res, "api": api_res}
        elif not stocknow_client:
            res = {"status": "MOCK", "action": action, "connected": True, "message": "Simulated StockNow session"}
        elif action == "launch":
            target_mode = body.mode or "ONSCREEN_LIVE"
            res = await stocknow_client.launch(mode=target_mode)
        elif action == "login":
            phone = (
                getattr(settings, "operator_phone", None)
                or settings.operator_username
                or os.getenv("STOCKNOW_MOBILE", "")
                or os.getenv("OPERATOR_USERNAME", "")
            )
            password = (
                settings.operator_password
                or os.getenv("STOCKNOW_PASSWORD", "")
                or os.getenv("OPERATOR_PASSWORD", "")
            )
            res = await stocknow_client.ensure_authenticated(phone, password)
        else:
            res = {"status": "UNKNOWN_ACTION"}

        session.add(KernelAuditLog(
            endpoint="/k/stocknow/session",
            action=f"STOCKNOW_{action.upper()}",
            symbol=None,
            payload=body.model_dump(),
            result=res,
            checkpoint_id=cp.id,
            session_on=state.clock_date,
        ))

        return {
            "status": "ok",
            "action": action,
            "checkpoint_id": cp.id,
            "result": res,
            "browser": res.get("browser"),
            "api": res.get("api"),
        }


class CapsUpdateRequest(BaseModel):
    max_order_bdt: Decimal | float | None = None
    max_symbol_bdt: Decimal | float | None = None
    daily_budget_bdt: Decimal | float | None = None
    max_orders_per_day: int | None = None
    kill_switch_active: bool | None = None
    confirm: bool = False


@router.get("/caps")
def get_caps(
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """Fetch current risk limits, kill switch status, and today's usage scoped by active portfolio."""
    with db.read() as session:
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


@router.post("/caps")
def set_caps(
    body: CapsUpdateRequest,
    db: Database = Depends(get_db),
) -> dict[str, Any]:
    """Update risk limits in the kernel. May only lower limits by itself; raising a limit requires confirmation."""
    with db.write() as session:
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
            # Relaxing kill switch from True to False requires confirmation
            if current_kill_switch and not body.kill_switch_active:
                raising = True

        if raising and not body.confirm:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Raising risk limits requires operator confirmation in the cockpit (confirm=true).",
            )

        cp = CheckpointManager.create_checkpoint(
            session=session,
            state=state,
            action="SET_CAPS",
            description=f"Update risk caps (confirm={body.confirm})",
            actor="Kernel API",
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
            endpoint="/k/caps",
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

        return {
            "status": "ok",
            "checkpoint_id": cp.id,
            "max_order_bdt": float(state.max_order_bdt) if state.max_order_bdt is not None else None,
            "max_symbol_bdt": float(state.max_symbol_bdt) if state.max_symbol_bdt is not None else None,
            "daily_budget_bdt": float(state.daily_budget_bdt),
            "max_orders_per_day": int(state.max_orders_per_day),
            "kill_switch_active": bool(state.kill_switch_active),
        }


# ─────────────────────────────────────────────────────────────────────────────
# STANDALONE LOCAL SERVICE FACTORY
# ─────────────────────────────────────────────────────────────────────────────


def build_kernel_router(
    database: Database,
    settings: Settings,
    stocknow_client: Any | None = None,
    broadcaster: Any | None = None,
) -> APIRouter:
    """Builds the configured kernel router for inclusion in main app."""
    global _KERNEL_BROADCASTER
    if broadcaster is not None:
        _KERNEL_BROADCASTER = broadcaster
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
