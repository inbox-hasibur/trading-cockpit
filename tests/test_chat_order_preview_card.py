"""Tests for Requirement 10: Hermes Order Preview Card and Execution Lifecycle.

Validates that:
1. hb_place_order / /k/order dry_run returns preview with symbol, side, qty, price,
   0.5% fee, mode, portfolio, cap usage breakdown, and preview token.
2. Confirming with preview_token and operator_confirmed=True executes order and records receipt.
3. Failed live submission leaves local ledger completely unchanged (checkpoint rollback).
4. Order preview card contract conforms to chat rendering requirements.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from backend.adapters.stocknow_executor import StockNowExecutionError
from backend.database import CompanyProfile, TaxLot, TradeLog
from backend.engine.price_guard import clear_market_quotes, set_market_quote
from backend.kernel_api import clear_order_idempotency_cache


@pytest.fixture(autouse=True)
def clean_cache():
    clear_order_idempotency_cache()
    clear_market_quotes()
    yield
    clear_order_idempotency_cache()
    clear_market_quotes()


@pytest.fixture
def kernel_token(monkeypatch):
    token = "test-kernel-token-xyz"
    monkeypatch.setenv("KERNEL_TOKEN", token)
    return token


@pytest.fixture
def auth_headers(kernel_token):
    return {"X-Kernel-Token": kernel_token}


def test_order_preview_contains_caps_and_financials(client, db, auth_headers):
    """Dry run preview contains symbol, side, qty, price, 0.5% fee, mode, portfolio, and cap usage."""
    set_market_quote("BANKASIA", ltp=20.5, day_low=20.0, day_high=21.0, close=20.5)
    payload = {
        "idempotency_key": "preview-bankasia-001",
        "symbol": "BANKASIA",
        "side": "BUY",
        "quantity": 10,
        "price": 20.5,
        "dry_run": True,
        "portfolio_id": "164580",
    }

    with patch("backend.kernel_api.is_dse_market_open", return_value={"is_open": True, "reason": "Trading session"}):
        res = client.post("/k/order", json=payload, headers=auth_headers)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["dry_run"] is True
    assert data["status"] == "VALIDATED"
    assert data["symbol"] == "BANKASIA"
    assert data["side"] == "BUY"
    assert data["quantity"] == 10
    assert data["price"] == 20.5
    assert data["commission_pct"] == 0.5
    assert "estimated_fee" in data
    assert "estimated_net" in data
    assert data["portfolio_id"] == "164580"
    assert "portfolio_name" in data
    assert "trading_mode" in data
    assert data["preview_token"].startswith("prev_")

    # Cap usage validation
    cap = data.get("cap_usage")
    assert cap is not None
    assert cap["side"] == "BUY"
    assert "today_orders" in cap
    assert "max_orders" in cap
    assert "summary" in cap
    assert "daily_budget_spent" in cap
    assert "daily_budget_limit" in cap
    assert "daily_budget_pct" in cap
    assert "Daily budget" in cap["summary"]


def test_order_preview_sell_cap_usage(client, db, auth_headers):
    """Dry run SELL preview contains mature share usage and strict no-loss validation."""
    set_market_quote("BANKASIA", ltp=25.0, day_low=24.0, day_high=26.0, close=25.0)
    with db.write() as session:
        for lot in session.query(TaxLot).filter(TaxLot.symbol == "BANKASIA").all():
            lot.matures_on = date(2026, 10, 1)

    payload = {
        "idempotency_key": "preview-sell-001",
        "symbol": "BANKASIA",
        "side": "SELL",
        "quantity": 5,
        "price": 25.0,  # Profitable price > cost basis
        "dry_run": True,
        "portfolio_id": "164580",
    }

    with patch("backend.kernel_api.is_dse_market_open", return_value={"is_open": True, "reason": "Trading session"}):
        res = client.post("/k/order", json=payload, headers=auth_headers)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["dry_run"] is True
    assert data["side"] == "SELL"
    cap = data["cap_usage"]
    assert cap["side"] == "SELL"
    assert "mature_shares_available" in cap
    assert cap["shares_to_sell"] == 5
    assert "Selling 5 of" in cap["summary"]


def test_order_confirmation_success(client, db, auth_headers):
    """Confirming preview token executes order and records verified receipt."""
    set_market_quote("BANKASIA", ltp=20.5, day_low=20.0, day_high=21.0, close=20.5)
    with db.write() as session:
        comp = session.get(CompanyProfile, "BANKASIA")
        if comp:
            comp.source = "STOCKNOW"

    # 1. Obtain preview
    with patch("backend.kernel_api.is_dse_market_open", return_value={"is_open": True, "reason": "Trading session"}):
        prev_res = client.post("/k/order", json={
            "idempotency_key": "step1-prev-01",
            "symbol": "BANKASIA",
            "side": "BUY",
            "quantity": 10,
            "price": 20.5,
            "dry_run": True,
            "portfolio_id": "164580",
        }, headers=auth_headers)
    assert prev_res.status_code == 200, prev_res.text
    token = prev_res.json()["preview_token"]

    mock_receipt = {
        "success": True,
        "status": "ACKNOWLEDGED",
        "execution_mode": "BACKGROUND_POLLING",
        "receipt_id": "sn_receipt_12345",
        "order_id": "ord_998877",
        "symbol": "BANKASIA",
        "side": "BUY",
        "quantity": 10,
        "price": 20.5,
        "commission_pct": 0.5,
        "portfolio_id": "164580",
        "timestamp": "2026-11-08T10:30:00Z",
    }

    # 2. Confirm order with preview token
    with patch("backend.kernel_api.is_dse_market_open", return_value={"is_open": True, "reason": "Trading session"}), \
         patch("backend.adapters.stocknow_adapter.StockNowAdapter.execute_order", new_callable=AsyncMock) as mock_exec, \
         patch("backend.kernel_api._compute_order_reconcile_and_drift", return_value={"drift_bdt": 0.0, "status": "SYNCHRONIZED"}):
        mock_exec.return_value = mock_receipt

        confirm_res = client.post("/k/order", json={
            "idempotency_key": "step2-confirm-01",
            "symbol": "BANKASIA",
            "side": "BUY",
            "quantity": 10,
            "price": 20.5,
            "dry_run": False,
            "operator_confirmed": True,
            "preview_token": token,
            "portfolio_id": "164580",
        }, headers=auth_headers)

    assert confirm_res.status_code == 200, confirm_res.text
    res_data = confirm_res.json()
    assert res_data["dry_run"] is False
    assert res_data["stocknow_receipt"]["status"] == "ACKNOWLEDGED"
    assert res_data["stocknow_receipt"]["order_id"] == "ord_998877"

    # Verify local ledger updated
    with db.read() as session:
        last_trade = session.query(TradeLog).order_by(TradeLog.id.desc()).first()
        assert last_trade.symbol == "BANKASIA"
        assert last_trade.side == "BUY"
        assert last_trade.quantity == 10
        assert last_trade.source == "STOCKNOW_RECEIPT"


def test_order_failure_leaves_ledger_unchanged(client, db, auth_headers):
    """Failed live submission rolls back checkpoint with no ledger change."""
    set_market_quote("BANKASIA", ltp=20.5, day_low=20.0, day_high=21.0, close=20.5)
    # Initial ledger count
    with db.read() as session:
        initial_trades_count = session.query(TradeLog).count()
        initial_lots_count = session.query(TaxLot).count()

    # 1. Obtain preview
    with patch("backend.kernel_api.is_dse_market_open", return_value={"is_open": True, "reason": "Trading session"}):
        prev_res = client.post("/k/order", json={
            "idempotency_key": "fail-test-prev",
            "symbol": "BANKASIA",
            "side": "BUY",
            "quantity": 10,
            "price": 20.5,
            "dry_run": True,
            "portfolio_id": "164580",
        }, headers=auth_headers)
    token = prev_res.json()["preview_token"]

    # 2. Simulate broker submission failure
    with patch("backend.kernel_api.is_dse_market_open", return_value={"is_open": True, "reason": "Trading session"}), \
         patch("backend.adapters.stocknow_adapter.StockNowAdapter.execute_order", new_callable=AsyncMock) as mock_exec:
        mock_exec.side_effect = StockNowExecutionError("SCHEMA_CHANGED", "StockNow buy form input missing")

        confirm_res = client.post("/k/order", json={
            "idempotency_key": "fail-test-confirm",
            "symbol": "BANKASIA",
            "side": "BUY",
            "quantity": 10,
            "price": 20.5,
            "dry_run": False,
            "operator_confirmed": True,
            "preview_token": token,
            "portfolio_id": "164580",
        }, headers=auth_headers)

    assert confirm_res.status_code == 422
    err_body = confirm_res.json()
    assert err_body["error"] == "SCHEMA_CHANGED"
    assert "StockNow buy form input missing" in err_body["detail"]

    # 3. Assert NO LEDGER CHANGE occurred
    with db.read() as session:
        final_trades_count = session.query(TradeLog).count()
        final_lots_count = session.query(TaxLot).count()
        assert final_trades_count == initial_trades_count, "Ledger must have zero new trades on failure"
        assert final_lots_count == initial_lots_count, "Tax lots must be restored to checkpoint on failure"
