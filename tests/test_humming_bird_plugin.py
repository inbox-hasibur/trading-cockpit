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
    HB_AUTOMATION_GET_SCHEMA,
    HB_AUTOMATION_SET_SCHEMA,
    HB_CANARIES_SCHEMA,
    HB_INSPECT_CURVE_SCHEMA,
    HB_LOTS_SCHEMA,
    HB_MARKET_OPEN_SCHEMA,
    HB_PLACE_ORDER_SCHEMA,
    HB_PORTFOLIO_SCHEMA,
    HB_QUARANTINE_CANARY_SCHEMA,
    HB_RESTORE_QUARANTINE_SCHEMA,
    HB_ROLLBACK_LAST_SCHEMA,
    HB_RUN_CYCLE_SCHEMA,
    HB_SCHEDULER_SCHEMA,
    HB_SET_ALLOCATION_SCHEMA,
    HB_SET_TIER_SCHEMA,
    HB_STOCKNOW_SESSION_SCHEMA,
    HB_SYNC_SCHEMA,
    HB_WATCHLIST_SCHEMA,
    HB_MODE_GET_SCHEMA,
    HB_MODE_SET_SCHEMA,
    HB_FEED_STATUS_SCHEMA,
    HB_LEARNING_REVIEW_SCHEMA,
)
from plugins.humming_bird.tools import (
    _kernel_get,
    _kernel_post,
    hb_automation_get,
    hb_automation_set,
    hb_canaries,
    hb_caps_get,
    hb_caps_set,
    hb_feed_status,
    hb_inspect_curve,
    hb_learning_review,
    hb_lots,
    hb_market_open,
    hb_mode_get,
    hb_mode_set,
    hb_place_order,
    hb_portfolio,
    hb_quarantine_canary,
    hb_restore_quarantine,
    hb_rollback_last,
    hb_run_cycle,
    hb_scheduler,
    hb_set_allocation,
    hb_set_tier,
    hb_stocknow_session,
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
    "hb_automation_get",
    "hb_automation_set",
    "hb_scheduler",
    "hb_run_cycle",
    "hb_stocknow_session",
    "hb_mode_get",
    "hb_mode_set",
    "hb_caps_get",
    "hb_caps_set",
    "hb_feed_status",
    "hb_learning_review",
    "hb_analyze_market",
]


def test_plugin_yaml_manifest():
    """Manifest declares proper metadata, 25 tools, and pre_tool_call hook."""
    with open("plugins/humming_bird/plugin.yaml", "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    assert manifest["name"] == "humming_bird"
    assert manifest["version"] == "0.2.0"
    assert "KERNEL_URL" in manifest["requires_env"]
    assert "KERNEL_TOKEN" in manifest["requires_env"]
    assert manifest["provides_tools"] == ALL_EXPECTED_TOOLS
    assert manifest["provides_hooks"] == ["pre_tool_call"]


def test_plugin_registration():
    """register(ctx) registers all 25 tools and the pre_tool_call hook."""
    ctx = MagicMock()
    register(ctx)

    assert ctx.register_tool.call_count == 25
    registered_names = [call.kwargs["name"] for call in ctx.register_tool.call_args_list]
    for name in ALL_EXPECTED_TOOLS:
        assert name in registered_names

    for call in ctx.register_tool.call_args_list:
        assert call.kwargs["toolset"] == "humming_bird"
        assert isinstance(call.kwargs["schema"], dict)
        assert callable(call.kwargs["handler"])

    # Hook registration check
    ctx.register_hook.assert_called_once_with("pre_tool_call", on_pre_tool_call)


def test_skills_registration():
    """register(ctx) discovers and registers all 5 procedural skills."""
    ctx = MagicMock()
    register(ctx)
    registered_skills = [call.kwargs["name"] for call in ctx.register_skill.call_args_list]
    expected_skills = [
        "canary_90_10",
        "gsc_tiers",
        "sequential_no_regret",
        "stocknow_dse_quirks",
        "tradexpress_passive_safety",
    ]
    for skill in expected_skills:
        assert skill in registered_skills


def test_schemas_structure():
    """All 25 schemas conform to JSON Schema parameter specifications."""
    from plugins.humming_bird import _TOOLS
    assert len(_TOOLS) == 25
    for name, schema, handler in _TOOLS:
        assert "name" in schema
        assert "description" in schema
        assert "parameters" in schema
        params = schema["parameters"]
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
    with patch("plugins.humming_bird.hooks.check_dse_trading_hours", return_value=(False, "Weekend")), \
         patch("plugins.humming_bird.tools._kernel_get", return_value='{"trading_mode": "LIVE_HOURS"}'):
        res_blocked = on_pre_tool_call("hb_place_order", {"symbol": "BANKASIA", "side": "BUY", "quantity": 10, "dry_run": False})
        assert res_blocked is not None
        assert res_blocked["action"] == "block"
        assert "Order blocked" in res_blocked["message"]

    # When inside market hours, real submit triggers Hermes built-in approval gate
    with patch("plugins.humming_bird.hooks.check_dse_trading_hours", return_value=(True, "Open")), \
         patch("plugins.humming_bird.tools._kernel_get", return_value='{"trading_mode": "LIVE_HOURS"}'):
        res_approved = on_pre_tool_call("hb_place_order", {"symbol": "BANKASIA", "side": "BUY", "quantity": 10, "dry_run": False})
        assert res_approved is not None
        assert res_approved["action"] == "approve"
        assert "dse_live_order:BANKASIA" in res_approved["rule_key"]


@patch("urllib.request.urlopen")
def test_hb_automation_tools(mock_urlopen):
    """hb_automation_get and hb_automation_set interface with kernel."""
    fake_response = MagicMock()
    fake_payload = {
        "status": "ok",
        "automation_enabled": True,
        "paused": False,
        "ingestion_mode": "mock",
        "poll_interval_seconds": 15,
    }
    fake_response.read.return_value = json.dumps(fake_payload).encode("utf-8")
    fake_response.__enter__.return_value = fake_response
    mock_urlopen.return_value = fake_response

    # Test GET
    get_res = hb_automation_get()
    get_data = json.loads(get_res)
    assert get_data["status"] == "ok"
    assert get_data["automation_enabled"] is True

    # Test SET
    fake_payload["automation_enabled"] = False
    fake_response.read.return_value = json.dumps(fake_payload).encode("utf-8")
    set_res = hb_automation_set({"automation_enabled": False, "reason": "Operator request"})
    set_data = json.loads(set_res)
    assert set_data["status"] == "ok"
    assert set_data["automation_enabled"] is False


@patch("urllib.request.urlopen")
def test_hb_scheduler_tool(mock_urlopen):
    """hb_scheduler validates action and invokes kernel."""
    fake_response = MagicMock()
    fake_payload = {"status": "ok", "action": "status", "scheduler_running": True}
    fake_response.read.return_value = json.dumps(fake_payload).encode("utf-8")
    fake_response.__enter__.return_value = fake_response
    mock_urlopen.return_value = fake_response

    res = hb_scheduler({"action": "status"})
    assert json.loads(res)["status"] == "ok"

    # Validation error for invalid action
    err_res = hb_scheduler({"action": "restart"})
    assert "error" in json.loads(err_res)


@patch("urllib.request.urlopen")
def test_hb_run_cycle_tool(mock_urlopen):
    """hb_run_cycle enforces dry_run default and accepts explicit mode."""
    fake_response = MagicMock()
    fake_payload = {"status": "ok", "dry_run": True, "executed": True}
    fake_response.read.return_value = json.dumps(fake_payload).encode("utf-8")
    fake_response.__enter__.return_value = fake_response
    mock_urlopen.return_value = fake_response

    res = hb_run_cycle()
    assert json.loads(res)["dry_run"] is True


@patch("urllib.request.urlopen")
def test_hb_stocknow_session_tool(mock_urlopen):
    """hb_stocknow_session invokes browser session actions."""
    fake_response = MagicMock()
    fake_payload = {"status": "ok", "action": "status", "session": "idle"}
    fake_response.read.return_value = json.dumps(fake_payload).encode("utf-8")
    fake_response.__enter__.return_value = fake_response
    mock_urlopen.return_value = fake_response

    res = hb_stocknow_session({"action": "status"})
    assert json.loads(res)["action"] == "status"


@patch("urllib.request.urlopen")
def test_hb_mode_tools(mock_urlopen):
    """hb_mode_get returns mode; hb_mode_set requires confirm=True for TEST_OFFHOURS."""
    fake_response = MagicMock()
    fake_payload = {"status": "ok", "trading_mode": "LIVE_HOURS"}
    fake_response.read.return_value = json.dumps(fake_payload).encode("utf-8")
    fake_response.__enter__.return_value = fake_response
    mock_urlopen.return_value = fake_response

    # hb_mode_get
    res = hb_mode_get()
    assert json.loads(res)["trading_mode"] == "LIVE_HOURS"

    # hb_mode_set to TEST_OFFHOURS without confirm -> blocked with error
    err_res = hb_mode_set({"trading_mode": "TEST_OFFHOURS"})
    assert "error" in json.loads(err_res)
    assert "operator confirmation" in json.loads(err_res)["error"]

    # hb_mode_set to TEST_OFFHOURS with confirm=True -> passes
    fake_payload = {"status": "ok", "trading_mode": "TEST_OFFHOURS"}
    fake_response.read.return_value = json.dumps(fake_payload).encode("utf-8")
    success_res = hb_mode_set({"trading_mode": "TEST_OFFHOURS", "confirm": True})
    assert json.loads(success_res)["trading_mode"] == "TEST_OFFHOURS"

    # hb_mode_set to LIVE_HOURS without confirm -> allowed
    fake_payload = {"status": "ok", "trading_mode": "LIVE_HOURS"}
    fake_response.read.return_value = json.dumps(fake_payload).encode("utf-8")
    live_res = hb_mode_set({"trading_mode": "LIVE_HOURS"})
    assert json.loads(live_res)["trading_mode"] == "LIVE_HOURS"


    err_res = hb_stocknow_session({"action": "destroy"})
    assert "error" in json.loads(err_res)


@patch("urllib.request.urlopen")
def test_hb_feed_status_and_learning_review(mock_urlopen):
    """hb_feed_status and hb_learning_review query kernel endpoints cleanly."""
    fake_response = MagicMock()
    fake_payload = {
        "status": "ONLINE",
        "cdp_connected": True,
        "operator_instructions": ["All TradeXpress passive data feeds are fresh and active. No action needed."],
    }
    fake_response.read.return_value = json.dumps(fake_payload).encode("utf-8")
    fake_response.__enter__.return_value = fake_response
    mock_urlopen.return_value = fake_response

    status_res = hb_feed_status()
    assert json.loads(status_res)["status"] == "ONLINE"

    fake_learning = {
        "total_records": 10,
        "win_rate_pct": 100.0,
        "recent_logs": [],
    }
    fake_response.read.return_value = json.dumps(fake_learning).encode("utf-8")
    learn_res = hb_learning_review({"tier": "L1", "limit": 10})
    assert json.loads(learn_res)["win_rate_pct"] == 100.0


