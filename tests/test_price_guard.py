"""Tests for price guard sanity check and order rejection."""

from uuid import uuid4
import pytest
from sqlalchemy import select

from backend.database import DecisionLog, KernelAuditLog
from backend.engine.price_guard import (
    check_price_sanity,
    clear_market_quotes,
    set_market_quote,
)


@pytest.fixture(autouse=True)
def clean_market_quotes():
    clear_market_quotes()
    yield
    clear_market_quotes()


@pytest.fixture
def kernel_token(monkeypatch):
    token = "test-kernel-token-xyz"
    monkeypatch.setenv("KERNEL_TOKEN", token)
    return token


@pytest.fixture
def auth_headers(kernel_token):
    return {"X-Kernel-Token": kernel_token}


def test_check_price_sanity_unit():
    """Unit tests for check_price_sanity logic."""
    # 1. Price within 1.5%
    ok, reason = check_price_sanity(price=101.0, ltp=100.0, max_pct=1.5)
    assert ok is True
    assert reason == "OK"

    # Exactly 1.5%
    ok, reason = check_price_sanity(price=101.5, ltp=100.0, max_pct=1.5)
    assert ok is True

    # 2. Price 3% off
    ok, reason = check_price_sanity(price=103.0, ltp=100.0, max_pct=1.5)
    assert ok is False
    assert reason == "PRICE_OUT_OF_RANGE"

    # Price 3% below
    ok, reason = check_price_sanity(price=97.0, ltp=100.0, max_pct=1.5)
    assert ok is False
    assert reason == "PRICE_OUT_OF_RANGE"

    # 3. Price outside day range (even if within 1.5% of LTP)
    ok, reason = check_price_sanity(price=101.2, ltp=100.0, day_low=99.0, day_high=101.0, max_pct=1.5)
    assert ok is False
    assert reason == "PRICE_OUT_OF_RANGE"

    ok, reason = check_price_sanity(price=98.5, ltp=100.0, day_low=99.0, day_high=101.0, max_pct=1.5)
    assert ok is False
    assert reason == "PRICE_OUT_OF_RANGE"

    # Price inside day range
    ok, reason = check_price_sanity(price=100.5, ltp=100.0, day_low=99.0, day_high=101.0, max_pct=1.5)
    assert ok is True
    assert reason == "OK"

    # 4. Missing LTP gives NO_QUOTE
    ok, reason = check_price_sanity(price=100.0, ltp=None)
    assert ok is False
    assert reason == "NO_QUOTE"

    ok, reason = check_price_sanity(price=100.0, ltp=0)
    assert ok is False
    assert reason == "NO_QUOTE"


def test_price_within_one_point_five_percent_order(client, auth_headers):
    """Orders with price within 1.5% of LTP are accepted."""
    client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)
    set_market_quote("GP", ltp=250.0, day_low=245.0, day_high=255.0, close=250.0)

    res = client.post("/k/order", json={
        "idempotency_key": str(uuid4()),
        "symbol": "GP",
        "side": "BUY",
        "quantity": 2,
        "price": 252.0,  # 0.8% deviation <= 1.5%
        "dry_run": True,
    }, headers=auth_headers)

    assert res.status_code == 200
    assert res.json()["symbol"] == "GP"
    assert res.json()["price"] == 252.0


def test_price_three_percent_off_order_rejection(client, auth_headers, db):
    """Orders differing by 3% from LTP are rejected with PRICE_OUT_OF_RANGE."""
    client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)
    set_market_quote("GP", ltp=250.0, day_low=240.0, day_high=260.0, close=250.0)

    res = client.post("/k/order", json={
        "idempotency_key": str(uuid4()),
        "symbol": "GP",
        "side": "BUY",
        "quantity": 2,
        "price": 258.0,  # 3.2% deviation > 1.5%
        "dry_run": True,
    }, headers=auth_headers)

    assert res.status_code == 422
    assert "PRICE_OUT_OF_RANGE" in res.json()["detail"]

    # Verify decision log & audit
    with db.read() as session:
        dec = session.scalar(
            select(DecisionLog)
            .where(DecisionLog.symbol == "GP", DecisionLog.action == "REJECT_PRICE_OUT_OF_RANGE")
            .order_by(DecisionLog.id.desc())
        )
        assert dec is not None
        assert "PRICE_OUT_OF_RANGE" in dec.reason

        audit = session.scalar(
            select(KernelAuditLog)
            .where(KernelAuditLog.symbol == "GP", KernelAuditLog.action == "REJECT_PRICE_OUT_OF_RANGE")
            .order_by(KernelAuditLog.id.desc())
        )
        assert audit is not None


def test_price_outside_day_range_order_rejection(client, auth_headers, db):
    """Orders within 1.5% of LTP but outside [day_low, day_high] are rejected with PRICE_OUT_OF_RANGE."""
    client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)
    set_market_quote("GP", ltp=250.0, day_low=248.0, day_high=252.0, close=250.0)

    # 253.0 is 1.2% off LTP (within 1.5%), but exceeds day_high 252.0
    res = client.post("/k/order", json={
        "idempotency_key": str(uuid4()),
        "symbol": "GP",
        "side": "BUY",
        "quantity": 2,
        "price": 253.0,
        "dry_run": True,
    }, headers=auth_headers)

    assert res.status_code == 422
    assert "PRICE_OUT_OF_RANGE" in res.json()["detail"]

    with db.read() as session:
        dec = session.scalar(
            select(DecisionLog)
            .where(DecisionLog.symbol == "GP", DecisionLog.action == "REJECT_PRICE_OUT_OF_RANGE")
            .order_by(DecisionLog.id.desc())
        )
        assert dec is not None


def test_missing_ltp_in_live_hours_mode(client, auth_headers, db):
    """In LIVE_HOURS mode, missing LTP rejects the order with NO_QUOTE."""
    client.post("/k/mode", json={"trading_mode": "LIVE_HOURS", "confirm": True}, headers=auth_headers)
    set_market_quote("GP", ltp=None)

    res = client.post("/k/order", json={
        "idempotency_key": str(uuid4()),
        "symbol": "GP",
        "side": "BUY",
        "quantity": 2,
        "price": 250.0,
        "dry_run": True,
    }, headers=auth_headers)

    assert res.status_code == 422
    assert "NO_QUOTE" in res.json()["detail"]

    with db.read() as session:
        dec = session.scalar(
            select(DecisionLog)
            .where(DecisionLog.symbol == "GP", DecisionLog.action == "REJECT_NO_QUOTE")
            .order_by(DecisionLog.id.desc())
        )
        assert dec is not None
        assert "NO_QUOTE" in dec.reason

        audit = session.scalar(
            select(KernelAuditLog)
            .where(KernelAuditLog.symbol == "GP", KernelAuditLog.action == "REJECT_NO_QUOTE")
            .order_by(KernelAuditLog.id.desc())
        )
        assert audit is not None


def test_missing_ltp_in_test_offhours_mode(client, auth_headers):
    """In TEST_OFFHOURS mode, missing LTP uses last close and continues."""
    client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)
    set_market_quote("GP", ltp=None)

    # 1. Order at last close price (GP seeded last price is 265.0) -> succeeds
    res_ok = client.post("/k/order", json={
        "idempotency_key": str(uuid4()),
        "symbol": "GP",
        "side": "BUY",
        "quantity": 2,
        "price": 265.0,
        "dry_run": True,
    }, headers=auth_headers)
    assert res_ok.status_code == 200, res_ok.json()
    assert res_ok.json()["price"] == 265.0

    # 2. Order 3% off from last close 265.0 (e.g. 275.0 is ~3.8% off) -> rejected by price guard
    res_bad = client.post("/k/order", json={
        "idempotency_key": str(uuid4()),
        "symbol": "GP",
        "side": "BUY",
        "quantity": 2,
        "price": 275.0,  # ~3.8% deviation from last close 265.0
        "dry_run": True,
    }, headers=auth_headers)
    assert res_bad.status_code == 422
    assert "PRICE_OUT_OF_RANGE" in res_bad.json()["detail"]
