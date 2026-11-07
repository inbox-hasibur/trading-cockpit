"""Tests proving the order execution path (preflight, StockNowAdapter, idempotency, rollback, drift)."""

from __future__ import annotations

import asyncio
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from sqlalchemy import select

from backend.database import (
    CompanyProfile,
    OrderIdempotencyKey,
    PortfolioState,
    TaxLot,
    TradeLog,
)
from backend.kernel_api import (
    _ORDER_PREVIEW_TOKENS,
    clear_order_idempotency_cache,
)


@pytest.fixture(autouse=True)
def clean_idempotency():
    clear_order_idempotency_cache()
    yield
    clear_order_idempotency_cache()


@pytest.fixture
def kernel_token(monkeypatch):
    token = "test-kernel-token-orderpath"
    monkeypatch.setenv("KERNEL_TOKEN", token)
    return token


@pytest.fixture
def auth_headers(kernel_token):
    return {"X-Kernel-Token": kernel_token}


def test_order_path_success(client, auth_headers):
    """Test successful order execution: preflight, StockNow dispatch, verified receipt, ledger update, reconcile drift."""
    # 1. TEST_OFFHOURS direct execution
    client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)

    key1 = f"ord-{uuid4().hex[:8]}"
    req1 = {
        "idempotency_key": key1,
        "symbol": "GP",
        "side": "BUY",
        "quantity": 5,
        "dry_run": False,
        "operator_confirmed": True,
    }

    res1 = client.post("/k/order", json=req1, headers=auth_headers)
    assert res1.status_code == 200, f"Error: {res1.json()}"
    data1 = res1.json()
    assert data1["dry_run"] is False
    assert data1["symbol"] == "GP"
    assert data1["side"] == "BUY"
    assert data1["stocknow_receipt"]["success"] is True
    assert data1["stocknow_receipt"]["status"] in ("ACKNOWLEDGED", "EXECUTED", "FILLED")
    assert "reconcile" in data1
    assert data1["reconcile"]["book_reconciled"] is True

    # Verify SQLite persistence of idempotency key
    app = client.app
    db = app.state.database
    with db.read() as session:
        stored_key = session.get(OrderIdempotencyKey, key1)
        assert stored_key is not None
        assert stored_key.symbol == "GP"
        assert stored_key.side == "BUY"
        assert stored_key.quantity == 5


def test_order_path_live_hours_two_step(client, auth_headers, monkeypatch):
    """Test LIVE_HOURS two-step preview token flow."""
    client.post("/k/mode", json={"trading_mode": "LIVE_HOURS", "confirm": True}, headers=auth_headers)

    # Mock market hours to be open
    monkeypatch.setattr(
        "backend.kernel_api.is_dse_market_open",
        lambda settings: {"is_open": True, "reason": "Trading session open"},
    )

    # Step 1: dry_run=True preview to obtain token
    prev_key = f"prev-{uuid4().hex[:8]}"
    prev_req = {
        "idempotency_key": prev_key,
        "symbol": "GP",
        "side": "BUY",
        "quantity": 3,
        "dry_run": True,
    }
    prev_res = client.post("/k/order", json=prev_req, headers=auth_headers)
    assert prev_res.status_code == 200
    prev_data = prev_res.json()
    assert prev_data["dry_run"] is True
    assert prev_data["status"] == "VALIDATED"
    preview_token = prev_data["preview_token"]
    assert preview_token.startswith("prev_")

    # Step 2: dry_run=False with operator_confirmed=True and preview_token
    exec_key = f"exec-{uuid4().hex[:8]}"
    exec_req = {
        "idempotency_key": exec_key,
        "symbol": "GP",
        "side": "BUY",
        "quantity": 3,
        "dry_run": False,
        "operator_confirmed": True,
        "preview_token": preview_token,
    }
    exec_res = client.post("/k/order", json=exec_req, headers=auth_headers)
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert exec_data["dry_run"] is False
    assert exec_data["stocknow_receipt"]["success"] is True

    # Reusing the consumed token must fail
    reuse_res = client.post("/k/order", json={
        "idempotency_key": f"exec-{uuid4().hex[:8]}",
        "symbol": "GP",
        "side": "BUY",
        "quantity": 3,
        "dry_run": False,
        "operator_confirmed": True,
        "preview_token": preview_token,
    }, headers=auth_headers)
    assert reuse_res.status_code == 422
    assert "Invalid or expired preview token" in reuse_res.json()["detail"]


def test_order_path_rejection(client, auth_headers, monkeypatch):
    """Test rejections: unconfirmed, missing token, market closed, strict no-loss."""
    # 1. Unconfirmed rejection (operator_confirmed=False)
    client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)
    res_unconfirmed = client.post("/k/order", json={
        "idempotency_key": f"rej-{uuid4().hex[:8]}",
        "symbol": "GP",
        "side": "BUY",
        "quantity": 2,
        "dry_run": False,
        "operator_confirmed": False,
    }, headers=auth_headers)
    assert res_unconfirmed.status_code == 422
    assert "operator_confirmed must be true" in res_unconfirmed.json()["detail"]

    # 2. In LIVE_HOURS: missing preview token
    client.post("/k/mode", json={"trading_mode": "LIVE_HOURS", "confirm": True}, headers=auth_headers)
    monkeypatch.setattr(
        "backend.kernel_api.is_dse_market_open",
        lambda settings: {"is_open": True, "reason": "Trading session open"},
    )
    res_missing_token = client.post("/k/order", json={
        "idempotency_key": f"rej-{uuid4().hex[:8]}",
        "symbol": "GP",
        "side": "BUY",
        "quantity": 2,
        "dry_run": False,
        "operator_confirmed": True,
    }, headers=auth_headers)
    assert res_missing_token.status_code == 422
    assert "requires a two-step preview token" in res_missing_token.json()["detail"]

    # 3. In LIVE_HOURS: market closed gate
    monkeypatch.setattr(
        "backend.kernel_api.is_dse_market_open",
        lambda settings: {"is_open": False, "reason": "Weekend closed"},
    )
    _ORDER_PREVIEW_TOKENS["dummy_token"] = {
        "symbol": "GP", "side": "BUY", "quantity": 2, "price": 200.0, "expires_at": 9999999999,
    }
    res_market_closed = client.post("/k/order", json={
        "idempotency_key": f"rej-{uuid4().hex[:8]}",
        "symbol": "GP",
        "side": "BUY",
        "quantity": 2,
        "dry_run": False,
        "operator_confirmed": True,
        "preview_token": "dummy_token",
    }, headers=auth_headers)
    assert res_market_closed.status_code == 422
    assert "DSE market is closed" in res_market_closed.json()["detail"]

    # 4. Strict no-loss rejection
    client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)
    # Buy 5 shares first
    client.post("/k/order", json={
        "idempotency_key": f"buy-{uuid4().hex[:8]}",
        "symbol": "GP",
        "side": "BUY",
        "quantity": 5,
        "dry_run": False,
        "operator_confirmed": True,
    }, headers=auth_headers)

    # Try selling at severe loss (price 10.0)
    res_loss = client.post("/k/order", json={
        "idempotency_key": f"sell-{uuid4().hex[:8]}",
        "symbol": "GP",
        "side": "SELL",
        "quantity": 5,
        "price": 10.0,
        "dry_run": False,
        "operator_confirmed": True,
    }, headers=auth_headers)
    assert res_loss.status_code == 422
    assert "Strict No-Loss" in res_loss.json()["detail"] or "T+2 lock" in res_loss.json()["detail"]


def test_order_path_timeout_rollback(client, auth_headers, monkeypatch):
    """Test that a timeout in StockNowAdapter rolls back the checkpoint cleanly."""
    client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)

    app = client.app
    db = app.state.database
    with db.read() as session:
        initial_lots_count = len(session.scalars(select(TaxLot)).all())
        initial_trades_count = len(session.scalars(select(TradeLog)).all())

    # Mock StockNowAdapter.execute_order to raise TimeoutError
    async def mock_timeout(*args, **kwargs):
        raise TimeoutError("StockNow DOM virtual submission timed out after 15s")

    monkeypatch.setattr(
        "backend.adapters.stocknow_adapter.StockNowAdapter.execute_order",
        mock_timeout,
    )

    t_key = f"timeout-{uuid4().hex[:8]}"
    res = client.post("/k/order", json={
        "idempotency_key": t_key,
        "symbol": "GP",
        "side": "BUY",
        "quantity": 4,
        "dry_run": False,
        "operator_confirmed": True,
    }, headers=auth_headers)

    assert res.status_code == 422
    assert "timed out" in res.json()["detail"]

    # Verify atomic rollback: lots and trades count are strictly unchanged
    with db.read() as session:
        final_lots_count = len(session.scalars(select(TaxLot)).all())
        final_trades_count = len(session.scalars(select(TradeLog)).all())
        assert final_lots_count == initial_lots_count
        assert final_trades_count == initial_trades_count


def test_order_path_duplicate_key(client, auth_headers):
    """Test that an identical idempotency key returns the cached response without double execution."""
    client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)

    dup_key = f"dup-{uuid4().hex[:8]}"
    req = {
        "idempotency_key": dup_key,
        "symbol": "GP",
        "side": "BUY",
        "quantity": 2,
        "dry_run": False,
        "operator_confirmed": True,
    }

    # First attempt: succeeds
    res1 = client.post("/k/order", json=req, headers=auth_headers)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1.get("duplicate") is None or data1.get("duplicate") is False

    # Second attempt with same key: returns cached duplicate response
    res2 = client.post("/k/order", json=req, headers=auth_headers)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2.get("duplicate") is True
    assert data2.get("status") == "ALREADY_EXECUTED"


def test_order_path_restart_dedupe(client, auth_headers):
    """Test SQLite persistence across simulated server restarts."""
    client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)

    restart_key = f"restart-{uuid4().hex[:8]}"
    req = {
        "idempotency_key": restart_key,
        "symbol": "GP",
        "side": "BUY",
        "quantity": 2,
        "dry_run": False,
        "operator_confirmed": True,
    }

    res1 = client.post("/k/order", json=req, headers=auth_headers)
    assert res1.status_code == 200

    # Simulate restart by clearing in-memory caches
    clear_order_idempotency_cache()

    # Second execution must be caught by SQLite OrderIdempotencyKey
    res2 = client.post("/k/order", json=req, headers=auth_headers)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2.get("duplicate") is True
    assert data2.get("status") == "ALREADY_EXECUTED"

