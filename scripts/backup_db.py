"""Database backup utility for Humming Bird SQLite database (hummingbird.db).

Creates an atomic, timestamped copy of hummingbird.db in backend/data/backups/
using SQLite's online backup API, preserving WAL transactions and page locks.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sqlite3
import sys

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))


def get_default_db_path() -> Path:
    """Returns absolute path to hummingbird.db."""
    return WORKSPACE_ROOT / "backend" / "data" / "hummingbird.db"


def get_default_backup_dir() -> Path:
    """Returns absolute path to backups directory."""
    return WORKSPACE_ROOT / "backend" / "data" / "backups"


def backup_database(
    db_path: Path | None = None,
    backup_dir: Path | None = None,
    verbose: bool = False,
) -> Path:
    """Creates a verified timestamped backup of the SQLite database.

    Args:
        db_path: Path to source hummingbird.db (default: backend/data/hummingbird.db).
        backup_dir: Destination directory (default: backend/data/backups).
        verbose: Print progress details.

    Returns:
        Path to the newly created and verified backup file.
    """
    src_path = (db_path or get_default_db_path()).resolve()
    if not src_path.exists():
        raise FileNotFoundError(f"Source database not found: {src_path}")

    dst_dir = (backup_dir or get_default_backup_dir()).resolve()
    dst_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = dst_dir / f"hummingbird_{timestamp}.db"

    # Use SQLite online backup API to safely copy database across WAL checkpoints
    src_conn = sqlite3.connect(str(src_path), timeout=15.0)
    dst_conn = sqlite3.connect(str(backup_path), timeout=15.0)

    try:
        src_conn.backup(dst_conn)
        if verbose:
            print(f"[Backup] SQLite online backup completed from {src_path.name}")
    finally:
        dst_conn.close()
        src_conn.close()

    # Verify backup integrity
    verify_conn = sqlite3.connect(str(backup_path), timeout=15.0)
    try:
        cur = verify_conn.execute("PRAGMA integrity_check;")
        row = cur.fetchone()
        if not row or row[0] != "ok":
            if backup_path.exists():
                backup_path.unlink()
            raise RuntimeError(f"Backup integrity check failed: {row}")
    finally:
        verify_conn.close()

    # Automatically prune older backups to newest 5 (never pruning pre_restore)
    prune_backups(dst_dir, keep_count=5)

    return backup_path


def prune_backups(backup_dir: Path | None = None, keep_count: int = 5) -> list[Path]:
    """Prunes older hummingbird_*.db backups in backup_dir, keeping the newest keep_count.
    Never prunes files inside pre_restore or other subdirectories.
    """
    b_dir = (backup_dir or get_default_backup_dir()).resolve()
    if not b_dir.exists():
        return []

    # Only look for top-level files matching hummingbird_*.db directly in b_dir
    backups = sorted(
        [p for p in b_dir.glob("hummingbird_*.db") if p.is_file()],
        key=lambda p: (p.name, p.stat().st_mtime),
        reverse=True,
    )

    pruned = []
    if len(backups) > keep_count:
        to_delete = backups[keep_count:]
        for p in to_delete:
            try:
                # Also delete associated shm/wal if present
                shm = p.parent / f"{p.name}-shm"
                wal = p.parent / f"{p.name}-wal"
                if shm.exists():
                    shm.unlink()
                if wal.exists():
                    wal.unlink()
                p.unlink()
                pruned.append(p)
            except Exception:
                pass
    return pruned


def main() -> int:
    parser = argparse.ArgumentParser(description="Backup hummingbird.db to timestamped copy.")
    parser.add_argument("--db", type=Path, default=None, help="Custom path to hummingbird.db")
    parser.add_argument("--dir", type=Path, default=None, help="Custom destination backup directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    try:
        backup_file = backup_database(args.db, args.dir, verbose=args.verbose)
        size_bytes = backup_file.stat().st_size
        print(f"SUCCESS: Database backed up to {backup_file.name} ({size_bytes:,} bytes)")
        print(f"Path: {backup_file}")
        return 0
    except Exception as exc:
        print(f"ERROR: Backup failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
