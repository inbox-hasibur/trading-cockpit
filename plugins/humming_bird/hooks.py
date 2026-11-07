"""Hooks for Humming Bird Hermes Plugin."""

from __future__ import annotations

import logging
import os
from datetime import datetime, time
from typing import Any

logger = logging.getLogger(__name__)


def check_dse_trading_hours(dt: datetime | None = None) -> tuple[bool, str]:
    """Check if time falls within DSE trading hours (Sun-Thu 10:00 to 14:30 Asia/Dhaka)."""
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Asia/Dhaka")
    except Exception:
        from datetime import timedelta, timezone
        tz = timezone(timedelta(hours=6))

    if dt is None:
        dt = datetime.now(tz)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    else:
        dt = dt.astimezone(tz)

    # DSE trading days: Sunday (6), Monday (0), Tuesday (1), Wednesday (2), Thursday (3)
    if dt.weekday() in (4, 5):
        day_name = dt.strftime("%A")
        return False, f"Today is {day_name} (DSE weekend). Trading sessions run Sunday through Thursday."

    current_time = dt.time()
    open_time = time(10, 0)
    close_time = time(14, 30)

    if not (open_time <= current_time <= close_time):
        return False, f"Current Dhaka time {dt.strftime('%H:%M')} is outside trading hours (10:00 to 14:30 Asia/Dhaka)."

    return True, "DSE market is open."


def on_pre_tool_call(tool_name: str, args: dict[str, Any] | None = None, **kwargs) -> dict[str, Any] | None:
    """Pre-tool-call lifecycle hook.

    Enforces DSE market hours and Hermes approval gates for orders.
    """
    if tool_name != "hb_place_order":
        return None

    args = args or {}
    dry_run = args.get("dry_run", True)
    if isinstance(dry_run, str):
        dry_run = dry_run.lower() in ("true", "1", "yes")

    # Check trading mode from kernel if available (TEST_OFFHOURS bypasses market hours gate)
    is_test_offhours = False
    try:
        from plugins.humming_bird.tools import _kernel_get
        import json as _json
        mode_res = _json.loads(_kernel_get("/k/mode"))
        if mode_res.get("trading_mode") == "TEST_OFFHOURS":
            is_test_offhours = True
    except Exception:
        pass

    bypass = is_test_offhours or (os.getenv("HB_BYPASS_MARKET_HOURS", "").lower() in ("true", "1", "yes"))
    allow_dry_run_off_hours = os.getenv("ALLOW_OFF_HOURS_DRY_RUN", "true").lower() in ("true", "1", "yes")

    is_open, reason = check_dse_trading_hours()
    if not is_open and not bypass:
        # Block real orders off-hours; also block dry-run if off-hours dry runs are disabled
        if not dry_run or not allow_dry_run_off_hours:
            return {
                "action": "block",
                "message": f"Order blocked: DSE market is closed ({reason}). Orders are strictly limited to Sun-Thu 10:00 to 14:30 Asia/Dhaka in LIVE_HOURS mode.",
            }

    # If real submit (dry_run=False), invoke Hermes built-in approval gate
    if not dry_run:
        symbol = args.get("symbol", "UNKNOWN")
        side = args.get("side", "ORDER")
        qty = args.get("quantity", "")
        return {
            "action": "approve",
            "message": f"Execute real live DSE order: {side} {qty} {symbol} on portfolio 164580 (dry_run=false).",
            "rule_key": f"dse_live_order:{symbol}",
        }

    return None

