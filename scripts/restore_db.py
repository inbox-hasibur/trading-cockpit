"""Database restore utility for Humming Bird SQLite database (hummingbird.db).

Restores hummingbird.db from a timestamped backup in backend/data/backups/
using SQLite's online backup API, clearing stale WAL/SHM artifacts and verifying integrity.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sqlite3
import sys

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from scripts.backup_db import backup_database, get_default_backup_dir, get_default_db_path


def find_latest_backup(backup_dir: Path | None = None) -> Path:
    """Finds the most recent hummingbird_*.db backup file."""
    b_dir = (backup_dir or get_default_backup_dir()).resolve()
    if not b_dir.exists():
        raise FileNotFoundError(f"Backup directory does not exist: {b_dir}")

    candidates = sorted(b_dir.glob("hummingbird_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No hummingbird_*.db backup files found in {b_dir}")

    return candidates[0]


def restore_database(
    backup_file: Path | str | None = None,
    target_db: Path | None = None,
    create_safety_backup: bool = True,
    verbose: bool = False,
) -> Path:
    """Restores database from specified or latest backup file.

    Args:
        backup_file: Specific backup Path/filename or None for latest.
        target_db: Target destination path (default: backend/data/hummingbird.db).
        create_safety_backup: Take safety backup of existing target DB before restoring.
        verbose: Print progress details.

    Returns:
        Path of the restored backup file.
    """
    target_path = (target_db or get_default_db_path()).resolve()
    backup_dir = get_default_backup_dir()

    if backup_file is None:
        source_backup = find_latest_backup(backup_dir)
    else:
        p = Path(backup_file)
        if p.is_file():
            source_backup = p.resolve()
        elif (backup_dir / p.name).is_file():
            source_backup = (backup_dir / p.name).resolve()
        else:
            raise FileNotFoundError(f"Specified backup file not found: {backup_file}")

    # 1. Verify backup file integrity before any action
    verify_conn = sqlite3.connect(str(source_backup), timeout=15.0)
    try:
        cur = verify_conn.execute("PRAGMA integrity_check;")
        row = cur.fetchone()
        if not row or row[0] != "ok":
            raise RuntimeError(f"Source backup file integrity check failed: {row}")
    finally:
        verify_conn.close()

    # 2. Safety backup of existing database if present
    if create_safety_backup and target_path.exists():
        try:
            safety_file = backup_database(target_path, backup_dir=backup_dir / "pre_restore")
            if verbose:
                print(f"[Restore] Pre-restore safety backup created: {safety_file.name}")
        except Exception as exc:
            if verbose:
                print(f"[Restore Warning] Pre-restore safety backup skipped: {exc}")

    # 3. Clean up existing WAL and SHM journal artifacts to avoid stale page conflicts
    wal_file = target_path.with_name(target_path.name + "-wal")
    shm_file = target_path.with_name(target_path.name + "-shm")
    if wal_file.exists():
        try:
            wal_file.unlink()
        except Exception as e:
            if verbose:
                print(f"[Notice] Could not remove {wal_file.name}: {e}")
    if shm_file.exists():
        try:
            shm_file.unlink()
        except Exception as e:
            if verbose:
                print(f"[Notice] Could not remove {shm_file.name}: {e}")

    # 4. Perform SQLite online restoration
    target_path.parent.mkdir(parents=True, exist_ok=True)
    src_conn = sqlite3.connect(str(source_backup), timeout=15.0)
    dst_conn = sqlite3.connect(str(target_path), timeout=15.0)
    try:
        src_conn.backup(dst_conn)
    finally:
        dst_conn.close()
        src_conn.close()

    # 5. Verify restored database integrity
    chk_conn = sqlite3.connect(str(target_path), timeout=15.0)
    try:
        cur = chk_conn.execute("PRAGMA integrity_check;")
        row = cur.fetchone()
        if not row or row[0] != "ok":
            raise RuntimeError(f"Restored database integrity check failed: {row}")
    finally:
        chk_conn.close()

    return source_backup


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore hummingbird.db from backup.")
    parser.add_argument("backup", nargs="?", default=None, help="Backup file path or filename (default: latest)")
    parser.add_argument("--db", type=Path, default=None, help="Custom target path for hummingbird.db")
    parser.add_argument("--no-safety", action="store_true", help="Skip pre-restore safety backup")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    try:
        restored_from = restore_database(
            backup_file=args.backup,
            target_db=args.db,
            create_safety_backup=not args.no_safety,
            verbose=args.verbose,
        )
        print(f"SUCCESS: Database restored from {restored_from.name}")
        print(f"Target: {args.db or get_default_db_path()}")
        return 0
    except Exception as exc:
        print(f"ERROR: Restore failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
