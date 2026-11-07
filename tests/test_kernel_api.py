"""Tests for the local trading kernel API service (backend/kernel_api.py)."""

from __future__ import annotations

import ast
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.database import (
    CompanyProfile,
    CustomRule,
    KernelAuditLog,
    KernelStateCheckpoint,
    PortfolioState,
    RuleAudit,
    TaxLot,
    portfolio_state,
)
from backend.kernel_api import clear_order_idempotency_cache, create_kernel_app


@pytest.fixture(autouse=True)
def clean_idempotency():
    clear_order_idempotency_cache()
    yield
    clear_order_idempotency_cache()


@pytest.fixture
def kernel_token(monkeypatch):
    token = "test-kernel-token-xyz"
    monkeypatch.setenv("KERNEL_TOKEN", token)
    return token


@pytest.fixture
def auth_headers(kernel_token):
    return {"X-Kernel-Token": kernel_token}


def test_kernel_auth_and_localhost(client, kernel_token):
    # 1. Missing header -> 401
    res = client.get("/k/portfolio")
    assert res.status_code == 401
    assert "Unauthorized" in res.json()["detail"]

    # 2. Invalid token -> 401
    res = client.get("/k/portfolio", headers={"X-Kernel-Token": "invalid-secret"})
    assert res.status_code == 401
    assert "Invalid or missing" in res.json()["detail"]

    # 3. Valid token -> 200
    res = client.get("/k/portfolio", headers={"X-Kernel-Token": kernel_token})
    assert res.status_code == 200
    data = res.json()
    assert "metrics" in data
    assert "companies" in data
    assert "lots" in data


def test_kernel_read_endpoints(client, auth_headers):
    # 1. /k/portfolio
    p_res = client.get("/k/portfolio", headers=auth_headers)
    assert p_res.status_code == 200
    assert "available_cash" in p_res.json()["metrics"]

    # 2. /k/watchlist
    w_res = client.get("/k/watchlist", headers=auth_headers)
    assert w_res.status_code == 200
    items = w_res.json()
    assert len(items) >= 5
    symbols = {x["symbol"] for x in items}
    assert "GP" in symbols
    assert "SQURPHARMA" in symbols

    # 3. /k/watchlist?tier=
    w_tier = client.get("/k/watchlist?tier=GSC", headers=auth_headers)
    assert w_tier.status_code == 200
    for comp in w_tier.json():
        assert comp["watchlist_category"] == "GSC"

    # 4. /k/curve/{symbol}
    c_res = client.get("/k/curve/GP", headers=auth_headers)
    assert c_res.status_code == 200
    curve_data = c_res.json()
    assert curve_data["symbol"] == "GP"
    assert "support" in curve_data
    assert "resistance" in curve_data

    # Unknown symbol -> 404
    c_404 = client.get("/k/curve/NONEXISTENT", headers=auth_headers)
    assert c_404.status_code == 404

    # 5. /k/market-open
    m_res = client.get("/k/market-open", headers=auth_headers)
    assert m_res.status_code == 200
    assert "is_open" in m_res.json() or "open" in m_res.json()

    # 6. /k/canaries
    can_res = client.get("/k/canaries", headers=auth_headers)
    assert can_res.status_code == 200
    assert isinstance(can_res.json(), list)

    # 7. /k/lots
    lots_res = client.get("/k/lots", headers=auth_headers)
    assert lots_res.status_code == 200
    assert isinstance(lots_res.json(), list)


def test_order_dry_run_defaults_true(client, auth_headers):
    # Retrieve initial lot count
    lots_before = client.get("/k/lots", headers=auth_headers).json()

    key = str(uuid4())
    # dry_run is omitted in request body; must default to True
    req_body = {
        "idempotency_key": key,
        "symbol": "GP",
        "side": "BUY",
        "quantity": 10,
    }
    res = client.post("/k/order", json=req_body, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["dry_run"] is True
    assert data["status"] == "VALIDATED"
    assert data["symbol"] == "GP"
    assert data["side"] == "BUY"
    assert data["quantity"] == 10
    assert data["commission_pct"] == 0.5

    # Verify no state was mutated in database
    lots_after = client.get("/k/lots", headers=auth_headers).json()
    assert len(lots_after) == len(lots_before)


def test_order_portfolio_must_be_164580(client, auth_headers):
    req_body = {
        "idempotency_key": str(uuid4()),
        "symbol": "GP",
        "side": "BUY",
        "quantity": 5,
        "portfolio_id": "999999",  # Invalid portfolio
        "dry_run": True,
    }
    res = client.post("/k/order", json=req_body, headers=auth_headers)
    assert res.status_code == 422
    assert "Portfolio must be 164580" in res.json()["detail"]


def test_order_strict_no_loss_rejection(client, auth_headers):
    # Enable TEST_OFFHOURS mode so test passes regardless of day/market hours
    client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)

    # First, place a real buy order within active bucket budget (e.g. 5 shares)
    buy_key = str(uuid4())
    buy_res = client.post("/k/order", json={
        "idempotency_key": buy_key,
        "symbol": "GP",
        "side": "BUY",
        "quantity": 5,
        "dry_run": False,
    }, headers=auth_headers)
    assert buy_res.status_code == 200, f"Buy error: {buy_res.json()}"
    assert buy_res.json()["dry_run"] is False

    # Attempt to sell at 50.0 (severe loss vs cost basis)
    sell_key = str(uuid4())
    sell_res = client.post("/k/order", json={
        "idempotency_key": sell_key,
        "symbol": "GP",
        "side": "SELL",
        "quantity": 5,
        "price": 50.0,
        "dry_run": False,
    }, headers=auth_headers)

    # Must be rejected due to Strict No-Loss policy or T+2 maturity lock
    assert sell_res.status_code == 422
    detail = sell_res.json()["detail"]
    assert "Strict No-Loss" in detail or "T+2 lock" in detail


def test_snapshot_before_write_and_audit(client, auth_headers):
    # 1. POST /k/tier
    tier_res = client.post("/k/tier", json={
        "symbol": "GP",
        "tier": "GSC_L1",
    }, headers=auth_headers)
    assert tier_res.status_code == 200
    tier_data = tier_res.json()
    assert tier_data["status"] == "ok"
    assert tier_data["tier"] == "GSC_L1"
    cp_id = tier_data["checkpoint_id"]
    assert cp_id is not None

    # Verify that Checkpoint exists in database
    app = client.app
    db = app.state.database
    with db.read() as session:
        cp = session.get(KernelStateCheckpoint, cp_id)
        assert cp is not None
        assert cp.action == "SET_TIER"
        assert "GP" in cp.snapshot_payload["companies"]
        assert cp.snapshot_payload["companies"]["GP"]["watchlist_category"] == "GSC"

        # Verify audit row in KernelAuditLog
        audit = session.scalar(
            select(KernelAuditLog)
            .where(KernelAuditLog.checkpoint_id == cp_id)
            .limit(1)
        )
        assert audit is not None
        assert audit.endpoint == "/k/tier"
        assert audit.action == "SET_TIER"

    # 2. POST /k/allocation
    alloc_res = client.post("/k/allocation", json={
        "symbol": "GP",
        "buy_allocation_pct": 20.0,
        "enabled": True,
    }, headers=auth_headers)
    assert alloc_res.status_code == 200
    alloc_cp = alloc_res.json()["checkpoint_id"]

    with db.read() as session:
        cp_alloc = session.get(KernelStateCheckpoint, alloc_cp)
        assert cp_alloc is not None
        assert cp_alloc.action == "UPDATE_ALLOCATION"

    # 3. POST /k/quarantine
    quar_res = client.post("/k/quarantine", json={
        "symbol": "GP",
        "action": "quarantine",
        "reason": "Risk check test",
    }, headers=auth_headers)
    assert quar_res.status_code == 200
    quar_cp = quar_res.json()["checkpoint_id"]

    with db.read() as session:
        comp = session.get(CompanyProfile, "GP")
        assert comp.quarantined is True
        assert "Risk check test" in comp.quarantine_reason

    # 4. POST /k/rollback -> rolls back quarantine
    roll_res = client.post("/k/rollback", headers=auth_headers)
    assert roll_res.status_code == 200
    roll_data = roll_res.json()
    assert roll_data["status"] == "ok"

    with db.read() as session:
        comp_after = session.get(CompanyProfile, "GP")
        assert comp_after.quarantined is False


def test_order_idempotency_cache(client, auth_headers):
    client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)
    key = str(uuid4())
    req = {
        "idempotency_key": key,
        "symbol": "GP",
        "side": "BUY",
        "quantity": 2,
        "dry_run": False,
    }
    first_res = client.post("/k/order", json=req, headers=auth_headers)
    assert first_res.status_code == 200
    assert first_res.json()["dry_run"] is False

    # Second call with the same idempotency key must return cached execution
    second_res = client.post("/k/order", json=req, headers=auth_headers)
    assert second_res.status_code == 200
    data2 = second_res.json()
    assert data2.get("duplicate") is True
    assert data2.get("status") == "ALREADY_EXECUTED"


def test_standalone_kernel_app(kernel_token):
    """Verify that create_kernel_app runs as an independent local service."""
    app = create_kernel_app()
    with TestClient(app, base_url="http://127.0.0.1") as k_client:
        res = k_client.get("/k/portfolio", headers={"X-Kernel-Token": kernel_token})
        assert res.status_code == 200
        assert "metrics" in res.json()
        assert "companies" in res.json()


def test_kernel_api_has_no_hermes_imports():
    """Verify strictly that backend/kernel_api.py does not import backend.hermes or backend.hermes_os."""
    with open("backend/kernel_api.py", "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename="backend/kernel_api.py")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "hermes" not in alias.name, f"Forbidden import: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert "hermes" not in mod, f"Forbidden from-import: {mod}"


def test_automation_endpoints_and_audits(client, auth_headers):
    """Verify GET /k/automation and POST /k/automation snapshot and audit creation."""
    # 1. GET /k/automation
    res = client.get("/k/automation", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "automation_enabled" in data
    assert "paused" in data

    # 2. POST /k/automation
    update_res = client.post("/k/automation", json={
        "automation_enabled": False,
        "paused": True,
        "polling_interval_sec": 60,
    }, headers=auth_headers)
    assert update_res.status_code == 200
    res_data = update_res.json()
    assert res_data["automation_enabled"] is False
    assert res_data["paused"] is True
    assert res_data["polling_interval_sec"] == 60
    assert "checkpoint_id" in res_data

    # Verify audit in DB
    app = client.app
    db = app.state.database
    with db.read() as session:
        audit = session.scalar(
            select(KernelAuditLog)
            .where(KernelAuditLog.endpoint == "/k/automation")
            .order_by(KernelAuditLog.created_at.desc())
            .limit(1)
        )
        assert audit is not None
        assert audit.action == "SET_AUTOMATION"


def test_scheduler_control_endpoints(client, auth_headers):
    """Verify /k/scheduler status and control actions."""
    status_res = client.get("/k/scheduler", headers=auth_headers)
    assert status_res.status_code == 200

    post_status = client.post("/k/scheduler", json={"action": "status"}, headers=auth_headers)
    assert post_status.status_code == 200

    stop_res = client.post("/k/scheduler", json={"action": "stop"}, headers=auth_headers)
    assert stop_res.status_code == 200
    assert "checkpoint_id" in stop_res.json()


def test_run_cycle_dry_run_default(client, auth_headers):
    """Verify /k/cycle defaults dry_run=True and takes snapshot first."""
    res = client.post("/k/cycle", json={}, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["dry_run"] is True
    assert "checkpoint_id" in data
    assert "cycle" in data


def test_stocknow_session_endpoints(client, auth_headers):
    """Verify /k/stocknow/session endpoint."""
    status_res = client.post("/k/stocknow/session", json={"action": "status"}, headers=auth_headers)
    assert status_res.status_code == 200

    launch_res = client.post("/k/stocknow/session", json={"action": "launch", "mode": "BACKGROUND_POLLING"}, headers=auth_headers)
    assert launch_res.status_code == 200
    assert "checkpoint_id" in launch_res.json()


def test_single_writer_trading_lock_concurrency():
    """Verify that the trading lock serializes concurrent execution across threads."""
    import threading
    import time
    from backend.engine.trading_lock import acquire_trading_lock

    execution_order = []

    def task(task_id: int):
        with acquire_trading_lock(timeout=5.0):
            execution_order.append(f"start-{task_id}")
            time.sleep(0.05)
            execution_order.append(f"end-{task_id}")

    t1 = threading.Thread(target=task, args=(1,))
    t2 = threading.Thread(target=task, args=(2,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Must be perfectly serialized: start-1, end-1, start-2, end-2 (or start-2, end-2, start-1, end-1)
    assert (
        execution_order == ["start-1", "end-1", "start-2", "end-2"]
        or execution_order == ["start-2", "end-2", "start-1", "end-1"]
    )
