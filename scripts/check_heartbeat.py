"""Watchdog CLI script to check Cockpit heartbeat and trigger dead-man alerts if needed.

Can be run via cron, Task Scheduler, or external monitoring system.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from backend.config import DEFAULT_DATABASE_URL, Settings
from backend.database import Database
from backend.engine.heartbeat import check_dead_man_switch, record_system_heartbeat


def main() -> None:
    parser = argparse.ArgumentParser(description="Check Humming Bird Cockpit heartbeat.")
    parser.add_argument("--record", action="store_true", help="Record a heartbeat tick now")
    args = parser.parse_args()

    settings = Settings(database_url=DEFAULT_DATABASE_URL)
    db = Database(settings.database_url)

    if args.record:
        hb = record_system_heartbeat(db, settings)
        print(f"[OK] Heartbeat recorded at {hb.created_at}")
        return

    triggered = check_dead_man_switch(db, settings)
    if triggered:
        print("[ALERT] Heartbeat is stale during market hours! Dead-man alert dispatched.")
        sys.exit(1)
    else:
        print("[OK] Heartbeat check passed (system healthy or market closed).")
        sys.exit(0)


if __name__ == "__main__":
    main()
