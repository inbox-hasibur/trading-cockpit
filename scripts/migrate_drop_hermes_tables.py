"""Migration to backup old Hermes* tables and drop them from SQLite.

Dumps all rows from hermes_* tables to backend/data/hermes_tables_backup.json,
then drops the tables so the database retains only the trading kernel.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def run_migration(db_path: Path | str | None = None, backup_path: Path | str | None = None) -> dict:
    if db_path is None:
        db_path = Path(__file__).resolve().parent.parent / "backend" / "data" / "hummingbird.db"
    else:
        db_path = Path(db_path)

    if not db_path.exists():
        return {"status": "skipped", "reason": f"Database file not found at {db_path}"}

    if backup_path is None:
        backup_path = db_path.parent / "hermes_tables_backup.json"
    else:
        backup_path = Path(backup_path)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'hermes_%'")
    tables = [row["name"] for row in cur.fetchall()]

    if not tables:
        conn.close()
        return {"status": "noop", "message": "No hermes_* tables found."}

    backup_data: dict[str, list[dict]] = {}
    table_counts: dict[str, int] = {}

    for t in tables:
        cur.execute(f"SELECT * FROM {t}")
        rows = [dict(r) for r in cur.fetchall()]
        backup_data[t] = rows
        table_counts[t] = len(rows)

    export_payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "database": str(db_path),
        "table_counts": table_counts,
        "tables": backup_data,
    }

    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(json.dumps(export_payload, indent=2, default=str), encoding="utf-8")

    # Drop all hermes_* tables
    for t in tables:
        cur.execute(f"DROP TABLE IF EXISTS {t}")
    conn.commit()
    conn.close()

    return {
        "status": "success",
        "backup_path": str(backup_path),
        "dropped_tables": tables,
        "table_counts": table_counts,
    }


if __name__ == "__main__":
    result = run_migration()
    print(json.dumps(result, indent=2))
