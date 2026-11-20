"""DSE Market Open Gating Script for Hermes Cron Jobs.

Executed by Hermes cron scheduler prior to agent wake-up.
Emits JSON with {"wakeAgent": true} when DSE trading session is open,
or {"wakeAgent": false} when market is closed (off-hours, weekends, or holidays).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

DHAKA_TZ = ZoneInfo("Asia/Dhaka")

# DSE trading days: Sunday (6) through Thursday (3)
# In Python datetime.weekday(): Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6
DSE_WORKDAYS = {6, 0, 1, 2, 3}


def check_kernel_market_open() -> tuple[bool, str]:
    """Attempts to verify market status via local kernel API if reachable."""
    kernel_url = os.environ.get("KERNEL_URL", "http://127.0.0.1:8000")
    kernel_token = os.environ.get("KERNEL_TOKEN", "")
    url = f"{kernel_url.rstrip('/')}/k/market-open"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Hermes-Cron/1.0"})
        if kernel_token:
            req.add_header("X-Kernel-Token", kernel_token)
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                is_open = bool(data.get("is_open", False))
                reason = data.get("reason", "Kernel check completed")
                return is_open, f"Kernel verified: {reason}"
    except Exception:
        pass
    return False, "Kernel unreachable"


def is_dse_time_open(now: datetime) -> tuple[bool, str]:
    """Pure calendar and hours check against Dhaka time."""
    weekday = now.weekday()
    if weekday not in DSE_WORKDAYS:
        day_name = now.strftime("%A")
        return False, f"Today is {day_name} (DSE weekend; trading is Sun-Thu)"

    t = now.time()
    # DSE trading session: 10:00 AM to 02:10 PM (14:10)
    open_time = datetime.strptime("10:00:00", "%H:%M:%S").time()
    close_time = datetime.strptime("14:10:00", "%H:%M:%S").time()

    if not (open_time <= t <= close_time):
        return False, f"Current Dhaka time {now.strftime('%H:%M:%S')} is outside trading hours (10:00-14:10)"

    return True, "Within regular DSE trading hours"


def main():
    now = datetime.now(DHAKA_TZ)
    time_open, time_reason = is_dse_time_open(now)

    # If within regular trading hours, also consult kernel API if available
    kernel_open, kernel_reason = check_kernel_market_open()
    if kernel_reason.startswith("Kernel verified"):
        is_open = kernel_open
        reason = kernel_reason
    else:
        is_open = time_open
        reason = time_reason

    output = {
        "wakeAgent": is_open,
        "market_open": is_open,
        "dhaka_time": now.isoformat(),
        "reason": reason,
    }

    # Print JSON line for Hermes cron parser
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()

