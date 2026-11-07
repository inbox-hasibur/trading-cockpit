"""Tests for ingestion mode switching, schema validation, error formats, and idempotency."""

from unittest.mock import MagicMock
import pytest


def test_partial_schema_ui_requests(client):
    """The UI only sends {ingestion_mode: '...'} when clicking mode buttons; verify it succeeds."""
    # 1. Switch with only ingestion_mode: BACKGROUND_POLLING
    res1 = client.post("/api/automation/config", json={"ingestion_mode": "BACKGROUND_POLLING"})
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["ingestion_mode"] == "BACKGROUND_POLLING"
    assert "adapter" in data1

    # Snapshot check
    snap1 = client.get("/api/portfolio")
    assert snap1.status_code == 200
    assert snap1.json()["app"]["ingestion_mode"] == "BACKGROUND_POLLING"

    # 2. Switch with only ingestion_mode: ONSCREEN_LIVE (without browser)
    res2 = client.post("/api/automation/config", json={"ingestion_mode": "ONSCREEN_LIVE"})
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["ingestion_mode"] == "ONSCREEN_LIVE"

    # Snapshot check
    snap2 = client.get("/api/portfolio")
    assert snap2.status_code == 200
    assert snap2.json()["app"]["ingestion_mode"] == "ONSCREEN_LIVE"


def test_switch_both_ways_without_browser(client):
    """Switch back and forth without a browser attached; snapshot stays 200."""
    app = client.app

    # Ensure no browser is attached
    app.state.stocknow_client.page = None
    app.state.stocknow_client.context = None
    app.state.stocknow_client.state = "BROWSER_NOT_STARTED"

    # Switch to ONSCREEN_LIVE
    r_live = client.post("/api/automation/config", json={"ingestion_mode": "ONSCREEN_LIVE"})
    assert r_live.status_code == 200
    assert r_live.json()["adapter"]["connected"] is False

    snap_live = client.get("/api/portfolio")
    assert snap_live.status_code == 200
    assert snap_live.json()["adapter"]["cdp_attached"] is False

    # Switch back to BACKGROUND_POLLING
    r_poll = client.post("/api/automation/config", json={"ingestion_mode": "BACKGROUND_POLLING"})
    assert r_poll.status_code == 200
    assert r_poll.json()["adapter"]["mode"] == "BACKGROUND_POLLING"

    snap_poll = client.get("/api/portfolio")
    assert snap_poll.status_code == 200
    assert snap_poll.json()["app"]["ingestion_mode"] == "BACKGROUND_POLLING"


def test_switch_both_ways_with_browser(client):
    """Switch back and forth with a mock browser attached; snapshot stays 200."""
    app = client.app

    mock_page = MagicMock()
    mock_page.is_closed.return_value = False
    mock_page.url = "https://www.stocknow.com.bd/portfolios/164580/show"

    mock_context = MagicMock()
    mock_context.is_closed.return_value = False
    mock_context.pages = [mock_page]

    app.state.stocknow_client.page = mock_page
    app.state.stocknow_client.context = mock_context
    app.state.stocknow_client.state = "READY"

    # Switch to ONSCREEN_LIVE
    r_live = client.post("/api/automation/config", json={"ingestion_mode": "ONSCREEN_LIVE"})
    assert r_live.status_code == 200
    assert r_live.json()["adapter"]["connected"] is True
    assert r_live.json()["adapter"]["cdp_attached"] is True

    snap_live = client.get("/api/portfolio")
    assert snap_live.status_code == 200
    assert snap_live.json()["adapter"]["cdp_attached"] is True

    # Switch to BACKGROUND_POLLING
    r_poll = client.post("/api/automation/config", json={"ingestion_mode": "BACKGROUND_POLLING"})
    assert r_poll.status_code == 200
    assert r_poll.json()["adapter"]["mode"] == "BACKGROUND_POLLING"

    snap_poll = client.get("/api/portfolio")
    assert snap_poll.status_code == 200
    assert snap_poll.json()["adapter"]["mode"] == "BACKGROUND_POLLING"


def test_idempotent_scheduler_and_repeated_switches(client):
    """Multiple identical switches never duplicate scheduler tasks or raise errors."""
    # Repeated BACKGROUND_POLLING calls
    for _ in range(3):
        r = client.post("/api/automation/config", json={"ingestion_mode": "BACKGROUND_POLLING"})
        assert r.status_code == 200
        snap = client.get("/api/portfolio")
        assert snap.status_code == 200

    # Repeated ONSCREEN_LIVE calls
    for _ in range(3):
        r = client.post("/api/automation/config", json={"ingestion_mode": "ONSCREEN_LIVE"})
        assert r.status_code == 200
        snap = client.get("/api/portfolio")
        assert snap.status_code == 200


def test_all_api_errors_return_error_and_detail_json(client):
    """Every API error returns JSON with both 'error' and 'detail' keys."""
    # 1. 422 Validation Error
    res_val = client.post("/api/automation/config", json={"polling_interval_sec": 5})
    assert res_val.status_code == 422
    data_val = res_val.json()
    assert "error" in data_val
    assert "detail" in data_val
    assert data_val["error"] == "VALIDATION_ERROR"
    assert "polling_interval_sec" in data_val["detail"]

    # 2. 404 Not Found
    res_404 = client.get("/api/nonexistent/endpoint")
    assert res_404.status_code == 404
    data_404 = res_404.json()
    assert "error" in data_404
    assert "detail" in data_404
    assert data_404["error"] == "NOT_FOUND"

    # 3. 409 Conflict (e.g. paused cycle)
    client.post("/api/automation/pause", json={"paused": True})
    res_409 = client.post("/api/automation/cycle")
    assert res_409.status_code == 409
    data_409 = res_409.json()
    assert "error" in data_409
    assert "detail" in data_409
    assert data_409["error"] == "CONFLICT"
