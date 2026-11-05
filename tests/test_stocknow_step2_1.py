"""Unit tests for Sprint 2 Step 2.1: Persistent Playwright session, auto-login & network sniffer."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.adapters.stocknow_adapter import StockNowAdapter
from backend.adapters.stocknow_client import (
    DEFAULT_PROFILE_DIR,
    StockNowLiveClient,
    get_safe_profile_dir,
    mask_phone,
)
from backend.config import Settings
from backend.main import create_app


def test_onedrive_safe_profile_directory():
    """Verify that default profile is isolated outside OneDrive, and OneDrive paths are redirected."""
    default_dir = get_safe_profile_dir()
    assert default_dir == DEFAULT_PROFILE_DIR
    assert "onedrive" not in str(default_dir).lower()

    # If given a OneDrive-nested path, it must safely redirect to DEFAULT_PROFILE_DIR
    onedrive_path = Path("C:/Users/test/OneDrive/Documents/profile")
    safe_dir = get_safe_profile_dir(onedrive_path)
    assert safe_dir == DEFAULT_PROFILE_DIR

    # A safe external path should be respected
    safe_custom = Path("C:/custom_safe_profile_dir").resolve()
    resolved = get_safe_profile_dir(safe_custom)
    assert resolved == safe_custom


def test_mask_phone():
    """Verify operator phone masking for zero-secret disclosure."""
    assert mask_phone("01882082502") == "018***502"
    assert mask_phone("+8801882082502") == "880***502"
    assert mask_phone("12345") == "12***"
    assert mask_phone("") == ""


def test_stocknow_live_client_initial_state():
    """Verify StockNowLiveClient initial state and status payload schema."""
    client = StockNowLiveClient(ingestion_mode="ONSCREEN_LIVE")
    assert client.ingestion_mode == "ONSCREEN_LIVE"
    assert client.state == "BROWSER_NOT_STARTED"

    status = client.get_status()
    assert status["connected"] is False
    assert status["state"] == "BROWSER_NOT_STARTED"
    assert status["mode"] == "ONSCREEN_LIVE"
    assert status["is_onedrive_safe"] is True
    assert status["captured_endpoints_count"] == 0
    assert status["captured_endpoints"] == []
    assert status["last_sync_at"] is None
    assert status["last_error"] is None


def test_network_sniffer_caching():
    """Verify passive XHR response sniffer captures and caches JSON endpoints."""
    async def run():
        client = StockNowLiveClient()

        # Mock response object from Playwright
        mock_resp = MagicMock()
        mock_resp.url = "https://stocknow.com.bd/api/v1/market/prices?sector=bank"
        mock_resp.status = 200
        mock_resp.headers = {"content-type": "application/json; charset=utf-8"}
        mock_resp.json = AsyncMock(return_value=[{"symbol": "BANKASIA", "ltp": 19.64}])

        await client._handle_response(mock_resp)

        status = client.get_status()
        assert status["captured_endpoints_count"] == 1
        assert "/api/v1/market/prices" in client.captured_endpoints
        cached = client.captured_endpoints["/api/v1/market/prices"]
        assert cached["status"] == 200
        assert cached["data"] == [{"symbol": "BANKASIA", "ltp": 19.64}]
        assert status["last_sync_at"] is not None

        # Foreign or non-JSON response must be ignored
        foreign_resp = MagicMock()
        foreign_resp.url = "https://analytics.google.com/collect"
        foreign_resp.status = 200
        foreign_resp.headers = {"content-type": "application/json"}
        foreign_resp.json = AsyncMock(return_value={})
        await client._handle_response(foreign_resp)
        assert client.get_status()["captured_endpoints_count"] == 1

        # Error status response (e.g. 500) must be ignored
        err_resp = MagicMock()
        err_resp.url = "https://stocknow.com.bd/api/v1/error"
        err_resp.status = 500
        err_resp.headers = {"content-type": "application/json"}
        await client._handle_response(err_resp)
        assert client.get_status()["captured_endpoints_count"] == 1

    asyncio.run(run())


def test_ensure_authenticated_graceful_handling():
    """Verify ensure_authenticated handles launch/auth gracefully and masks phone."""
    async def run():
        client = StockNowLiveClient()
        client.launch = AsyncMock(return_value={"connected": False, "state": "ERROR"})
        client.state = "ERROR"
        client.last_error = "Mock offline browser failure"

        res = await client.ensure_authenticated(phone="01882082502", password="Stocknow#909109")
        assert res["authenticated"] is False
        assert res["state"] == "ERROR"
        assert res["phone_masked"] == "018***502"
        # Ensure password is NOT leaked in response
        assert "Stocknow#909109" not in str(res)

    asyncio.run(run())


def test_stocknow_adapter_telemetry():
    """Verify StockNowAdapter.get_adapter_status includes Sprint 2 telemetry fields."""
    adapter = StockNowAdapter()

    # Without client
    status_default = adapter.get_adapter_status(ingestion_mode="ONSCREEN_LIVE", polling_interval_sec=60)
    assert status_default["mode"] == "ONSCREEN_LIVE"
    assert status_default["polling_interval_sec"] == 60
    assert status_default["session_state"] == "BROWSER_NOT_STARTED"
    assert "profile_path" in status_default
    assert status_default["captured_endpoints_count"] == 0

    # With mocked live client
    mock_client = MagicMock()
    mock_client.get_status.return_value = {
        "connected": True,
        "state": "READY",
        "profile_path": "C:/safe_profile",
        "captured_endpoints_count": 5,
        "last_sync_at": "2026-11-05T14:30:00Z",
    }
    status_live = adapter.get_adapter_status(
        ingestion_mode="ONSCREEN_LIVE",
        polling_interval_sec=120,
        live_client=mock_client,
    )
    assert status_live["connected"] is True
    assert status_live["cdp_attached"] is True
    assert status_live["source"] == "STOCKNOW_LIVE"
    assert status_live["session_state"] == "READY"
    assert status_live["profile_path"] == "C:/safe_profile"
    assert status_live["captured_endpoints_count"] == 5
    assert status_live["last_sync_at"] == "2026-11-05T14:30:00Z"


def test_stocknow_api_endpoints():
    """Verify GET /api/stocknow/status and POST /api/stocknow/session routes."""
    app = create_app()
    with TestClient(app, base_url="http://localhost") as client:
        # GET status
        res = client.get("/api/stocknow/status")
        assert res.status_code == 200
        data = res.json()
        assert "connected" in data
        assert "state" in data
        assert "mode" in data
        assert "is_onedrive_safe" in data
        assert "captured_endpoints_count" in data

        # POST session close
        res_close = client.post("/api/stocknow/session", json={"action": "close"})
        assert res_close.status_code == 200
        data_close = res_close.json()
        assert data_close["state"] == "CLOSED"

        # POST session invalid action
        res_invalid = client.post("/api/stocknow/session", json={"action": "invalid_action"})
        assert res_invalid.status_code == 422
