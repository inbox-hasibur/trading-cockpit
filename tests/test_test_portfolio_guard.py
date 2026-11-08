"""Tests for test portfolio configuration guard."""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.config import test_portfolio_configured as check_configured
from backend.main import create_app


def test_ids_equal_gives_false(monkeypatch):
    """test_portfolio_configured returns False when test ID equals live ID."""
    monkeypatch.setenv("STOCKNOW_LIVE_PORTFOLIO_ID", "164580")
    monkeypatch.setenv("STOCKNOW_TEST_PORTFOLIO_ID", "164580")
    assert check_configured() is False


def test_test_id_empty_gives_false(monkeypatch):
    """test_portfolio_configured returns False when test ID is empty."""
    monkeypatch.setenv("STOCKNOW_LIVE_PORTFOLIO_ID", "164580")
    monkeypatch.setenv("STOCKNOW_TEST_PORTFOLIO_ID", "")
    assert check_configured() is False


def test_two_different_ids_give_true(monkeypatch):
    """test_portfolio_configured returns True when test ID and live ID are distinct."""
    monkeypatch.setenv("STOCKNOW_LIVE_PORTFOLIO_ID", "164580")
    monkeypatch.setenv("STOCKNOW_TEST_PORTFOLIO_ID", "164580_test")
    assert check_configured() is True


def test_post_order_test_offhours_equal_ids_returns_test_portfolio_not_configured(tmp_path, monkeypatch):
    """post_order in TEST_OFFHOURS with equal test and live IDs rejects with TEST_PORTFOLIO_NOT_CONFIGURED and makes no StockNow call."""
    monkeypatch.setenv("STOCKNOW_LIVE_PORTFOLIO_ID", "164580")
    monkeypatch.setenv("STOCKNOW_TEST_PORTFOLIO_ID", "164580")
    token = "test-kernel-token-guard"
    monkeypatch.setenv("KERNEL_TOKEN", token)
    headers = {"X-Kernel-Token": token}

    db_file = tmp_path / "test_equal_ids.db"
    settings = Settings(
        database_url=f"sqlite:///{db_file.as_posix()}",
        stocknow_live_portfolio_id="164580",
        stocknow_test_portfolio_id="164580",
        cockpit_api_token=token,
    )
    app = create_app(settings)
    with TestClient(app, base_url="http://localhost") as client:
        # Switch mode to TEST_OFFHOURS
        mode_res = client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=headers)
        assert mode_res.status_code == 200

        with patch("backend.adapters.stocknow_executor.StockNowExecutor.execute_order") as mock_exec, \
             patch("backend.adapters.stocknow_api.StockNowAPI.buy") as mock_buy, \
             patch("backend.adapters.stocknow_api.StockNowAPI.sell") as mock_sell:
            res = client.post("/k/order", json={
                "idempotency_key": str(uuid4()),
                "symbol": "GP",
                "side": "BUY",
                "quantity": 10,
                "dry_run": False,
                "operator_confirmed": True,
            }, headers=headers)

            assert res.status_code == 422
            assert "TEST_PORTFOLIO_NOT_CONFIGURED" in res.json()["detail"]
            mock_exec.assert_not_called()
            mock_buy.assert_not_called()
            mock_sell.assert_not_called()
