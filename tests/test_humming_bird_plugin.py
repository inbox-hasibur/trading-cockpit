"""Tests for Humming Bird Hermes Plugin (READ & WRITE Tools + Hooks)."""

import json
import urllib.error
from datetime import datetime
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest
import yaml

from plugins.humming_bird import _TOOLS, register
from plugins.humming_bird.hooks import check_dse_trading_hours, on_pre_tool_call
from plugins.humming_bird.schemas import (
    HB_CANARIES_SCHEMA,
    HB_INSPECT_CURVE_SCHEMA,
    HB_LOTS_SCHEMA,
    HB_MARKET_OPEN_SCHEMA,
    HB_PLACE_ORDER_SCHEMA,
    HB_PORTFOLIO_SCHEMA,
    HB_QUARANTINE_CANARY_SCHEMA,
    HB_RESTORE_QUARANTINE_SCHEMA,
    HB_ROLLBACK_LAST_SCHEMA,
    HB_SET_ALLOCATION_SCHEMA,
    HB_SET_TIER_SCHEMA,
    HB_SYNC_SCHEMA,
    HB_WATCHLIST_SCHEMA,
)
from plugins.humming_bird.tools import (
    _kernel_get,
    _kernel_post,
    hb_canaries,
    hb_inspect_curve,
    hb_lots,
    hb_market_open,
    hb_place_order,
    hb_portfolio,
    hb_quarantine_canary,
    hb_restore_quarantine,
    hb_rollback_last,
    hb_set_allocation,
    hb_set_tier,
    hb_sync,
    hb_watchlist,
)

ALL_EXPECTED_TOOLS = [
    "hb_portfolio",
    "hb_watchlist",
    "hb_inspect_curve",
    "hb_market_open",
    "hb_canaries",
    "hb_lots",
    "hb_set_tier",
    "hb_set_allocation",
    "hb_quarantine_canary",
    "hb_restore_quarantine",
    "hb_sync",
    "hb_place_order",
    "hb_rollback_last",
]


def test_plugin_yaml_manifest():
    """Manifest declares proper metadata, 13 tools, and pre_tool_call hook."""
    with open("plugins/humming_bird/plugin.yaml", "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    assert manifest["name"] == "humming_bird"
    assert manifest["version"] == "0.2.0"
    assert "KERNEL_URL" in manifest["requires_env"]
    assert "KERNEL_TOKEN" in manifest["requires_env"]
    assert manifest["provides_tools"] == ALL_EXPECTED_TOOLS
    assert manifest["provides_hooks"] == ["pre_tool_call"]


def test_plugin_registration():
    """register(ctx) registers all 13 tools and the pre_tool_call hook."""
    ctx = MagicMock()
    register(ctx)

    assert ctx.register_tool.call_count == 13
    registered_names = [call.kwargs["name"] for call in ctx.register_tool.call_args_list]
    for name in ALL_EXPECTED_TOOLS:
        assert name in registered_names

    for call in ctx.register_tool.call_args_list:
        assert call.kwargs["toolset"] == "humming_bird"
        assert isinstance(call.kwargs["schema"], dict)
        assert callable(call.kwargs["handler"])

    # Hook registration check
    ctx.register_hook.assert_called_once_with("pre_tool_call", on_pre_tool_call)


def test_schemas_structure():
    """All 13 schemas conform to JSON Schema parameter specifications."""
    schemas = [
        HB_PORTFOLIO_SCHEMA,
        HB_WATCHLIST_SCHEMA,
        HB_INSPECT_CURVE_SCHEMA,
        HB_MARKET_OPEN_SCHEMA,
        HB_CANARIES_SCHEMA,
        HB_LOTS_SCHEMA,
        HB_SET_TIER_SCHEMA,
        HB_SET_ALLOCATION_SCHEMA,
        HB_QUARANTINE_CANARY_SCHEMA,
        HB_RESTORE_QUARANTINE_SCHEMA,
        HB_SYNC_SCHEMA,
        HB_PLACE_ORDER_SCHEMA,
        HB_ROLLBACK_LAST_SCHEMA,
    ]
    assert len(schemas) == 13
    for s in schemas:
        assert "name" in s
        assert "description" in s
        assert "parameters" in s
        params = s["parameters"]
        assert params["type"] == "object"
        assert "properties" in params


@patch("urllib.request.urlopen")
def test_hb_portfolio_handler(mock_urlopen):
    """hb_portfolio compacts portfolio payload properly."""
    fake_response = MagicMock()
    fake_payload = {
        "metrics": {"available_cash": 50000.0, "gross_equity": 100000.0},
        "companies": [
            {"symbol": "BANKASIA", "holding_qty": 100, "estimated_net_value": 1750.0},
            {"symbol": "ACI", "holding_qty": 0},
        ],
        "canary_theses": [],
        "market_clock": {"is_working_session": True},
        "trade_count": 5,
    }
    fake_response.read.return_value = json.dumps(fake_payload).encode("utf-8")
    fake_response.__enter__.return_value = fake_response
    mock_urlopen.return_value = fake_response

    res = hb_portfolio()
    data = json.loads(res)

    assert "metrics" in data
    assert len(data["holdings"]) == 1
    assert data["holdings"][0]["symbol"] == "BANKASIA"


@patch("urllib.request.urlopen")
def test_hb_set_tier(mock_urlopen):
    """hb_set_tier posts symbol and tier."""
    fake_response = MagicMock()
    fake_payload = {"status": "ok", "symbol": "BANKASIA", "tier": "GSC_L1"}
    fake_response.read.return_value = json.dumps(fake_payload).encode("utf-8")
    fake_response.__enter__.return_value = fake_response
    mock_urlopen.return_value = fake_response

    res = hb_set_tier({"symbol": "bankasia", "tier": "GSC_L1"})
    data = json.loads(res)
    assert data["status"] == "ok"
    assert data["tier"] == "GSC_L1"

    # Validation errors
    assert "error" in json.loads(hb_set_tier({"tier": "GSC"}))
    assert "error" in json.loads(hb_set_tier({"symbol": "BANKASIA"}))


@patch("urllib.request.urlopen")
def test_hb_set_allocation(mock_urlopen):
    """hb_set_allocation validates percentage range."""
    fake_response = MagicMock()
    fake_payload = {"status": "ok", "symbol": "BANKASIA", "buy_allocation_pct": 25.0}
    fake_response.read.return_value = json.dumps(fake_payload).encode("utf-8")
    fake_response.__enter__.return_value = fake_response
    mock_urlopen.return_value = fake_response

    res = hb_set_allocation({"symbol": "bankasia", "buy_allocation_pct": 25.0})
    assert json.loads(res)["status"] == "ok"

    # Invalid range errors
    assert "error" in json.loads(hb_set_allocation({"symbol": "BANKASIA", "buy_allocation_pct": 120}))
    assert "error" in json.loads(hb_set_allocation({"symbol": "BANKASIA", "buy_allocation_pct": -5}))


@patch("urllib.request.urlopen")
def test_hb_quarantine_and_restore(mock_urlopen):
    """hb_quarantine_canary and hb_restore_quarantine trigger 90/10 split and restore."""
    fake_response = MagicMock()
    fake_payload = {"status": "ok", "action": "quarantine", "symbol": "GP"}
    fake_response.read.return_value = json.dumps(fake_payload).encode("utf-8")
    fake_response.__enter__.return_value = fake_response
    mock_urlopen.return_value = fake_response

    q_res = hb_quarantine_canary({"symbol": "gp", "reason": "Severe breakdown"})
    assert json.loads(q_res)["status"] == "ok"

    fake_payload["action"] = "restore"
    fake_response.read.return_value = json.dumps(fake_payload).encode("utf-8")
    r_res = hb_restore_quarantine({"symbol": "gp", "reason": "Recovered support"})
    assert json.loads(r_res)["action"] == "restore"


@patch("urllib.request.urlopen")
def test_hb_sync(mock_urlopen):
    """hb_sync validates targets."""
    fake_response = MagicMock()
    fake_payload = {"status": "ok", "target": "favorites"}
    fake_response.read.return_value = json.dumps(fake_payload).encode("utf-8")
    fake_response.__enter__.return_value = fake_response
    mock_urlopen.return_value = fake_response

    res = hb_sync({"target": "favorites"})
    assert json.loads(res)["status"] == "ok"

    # Invalid target
    assert "error" in json.loads(hb_sync({"target": "invalid_target"}))


@patch("urllib.request.urlopen")
def test_hb_place_order(mock_urlopen):
    """hb_place_order enforces dry_run default, portfolio 164580, and confirmation."""
    fake_response = MagicMock()
    fake_payload = {"dry_run": True, "status": "VALIDATED", "symbol": "BANKASIA", "quantity": 10}
    fake_response.read.return_value = json.dumps(fake_payload).encode("utf-8")
    fake_response.__enter__.return_value = fake_response
    mock_urlopen.return_value = fake_response

    # 1. Default dry_run=True passes without confirmation
    res_dry = hb_place_order({"symbol": "BANKASIA", "side": "BUY", "quantity": 10})
    data_dry = json.loads(res_dry)
    assert data_dry["dry_run"] is True
    assert data_dry["status"] == "VALIDATED"

    # 2. Hard fail if portfolio is not 164580
    res_wrong = hb_place_order({"symbol": "BANKASIA", "side": "BUY", "quantity": 10, "portfolio_id": "999999"})
    data_wrong = json.loads(res_wrong)
    assert "error" in data_wrong
    assert "Hard fail" in data_wrong["error"]

    # 3. Real submit (dry_run=False) requires confirm=True
    res_unconfirmed = hb_place_order({"symbol": "BANKASIA", "side": "BUY", "quantity": 10, "dry_run": False})
    data_unconf = json.loads(res_unconfirmed)
    assert "error" in data_unconf
    assert data_unconf.get("requires_confirmation") is True

    # 4. Real submit with confirm=True executes
    fake_payload["dry_run"] = False
    fake_payload["status"] = "EXECUTED"
    fake_response.read.return_value = json.dumps(fake_payload).encode("utf-8")

    res_confirmed = hb_place_order({"symbol": "BANKASIA", "side": "BUY", "quantity": 10, "dry_run": False, "confirm": True})
    data_conf = json.loads(res_confirmed)
    assert data_conf["dry_run"] is False
    assert data_conf["status"] == "EXECUTED"


@patch("urllib.request.urlopen")
def test_hb_rollback_last(mock_urlopen):
    """hb_rollback_last posts to /k/rollback."""
    fake_response = MagicMock()
    fake_payload = {"status": "ok", "action": "ROLLBACK"}
    fake_response.read.return_value = json.dumps(fake_payload).encode("utf-8")
    fake_response.__enter__.return_value = fake_response
    mock_urlopen.return_value = fake_response

    res = hb_rollback_last()
    assert json.loads(res)["status"] == "ok"


def test_dse_trading_hours_check():
    """check_dse_trading_hours accurately identifies trading sessions."""
    tz = ZoneInfo("Asia/Dhaka")

    # Sunday 11:00 AM (Open)
    sunday_open = datetime(2026, 11, 8, 11, 0, tzinfo=tz)
    is_open, msg = check_dse_trading_hours(sunday_open)
    assert is_open is True

    # Sunday 09:30 AM (Before open)
    sunday_early = datetime(2026, 11, 8, 9, 30, tzinfo=tz)
    is_open, msg = check_dse_trading_hours(sunday_early)
    assert is_open is False
    assert "outside trading hours" in msg

    # Friday 11:00 AM (Weekend)
    friday_mid = datetime(2026, 11, 6, 11, 0, tzinfo=tz)
    is_open, msg = check_dse_trading_hours(friday_mid)
    assert is_open is False
    assert "weekend" in msg


def test_pre_tool_call_hook():
    """on_pre_tool_call blocks real orders off-hours and escalates to approval gate."""
    # Other tools are ignored
    assert on_pre_tool_call("hb_portfolio", {}) is None

    # Block real orders off-hours (e.g. on Saturday)
    saturday_time = datetime(2026, 11, 7, 12, 0, tzinfo=ZoneInfo("Asia/Dhaka"))
    with patch("plugins.humming_bird.hooks.check_dse_trading_hours", return_value=(False, "Weekend")):
        res_blocked = on_pre_tool_call("hb_place_order", {"symbol": "BANKASIA", "side": "BUY", "quantity": 10, "dry_run": False})
        assert res_blocked is not None
        assert res_blocked["action"] == "block"
        assert "Order blocked" in res_blocked["message"]

    # When inside market hours, real submit triggers Hermes built-in approval gate
    with patch("plugins.humming_bird.hooks.check_dse_trading_hours", return_value=(True, "Open")):
        res_approved = on_pre_tool_call("hb_place_order", {"symbol": "BANKASIA", "side": "BUY", "quantity": 10, "dry_run": False})
        assert res_approved is not None
        assert res_approved["action"] == "approve"
        assert "dse_live_order:BANKASIA" in res_approved["rule_key"]
