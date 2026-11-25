"""Tests for preflight verification suite, database backup, and database restore scripts."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path
import sqlite3
import subprocess
import sys
from unittest.mock import MagicMock, patch

import pytest

from backend.config import Settings
from backend.database import Database, PortfolioState
from backend.seed import seed_demo
from scripts.backup_db import backup_database, get_default_backup_dir, get_default_db_path
from scripts.preflight import (
    CheckResult,
    check_automation_state,
    check_caps_set,
    check_gateway,
    check_kernel_token,
    check_model_and_fallback,
    check_plugin_tools,
    check_portfolio_drift,
    check_stocknow_session,
    check_trading_mode,
    run_preflight,
)
from scripts.restore_db import find_latest_backup, restore_database


def test_backup_and_restore_database(tmp_path: Path):
    """Verify backup_database creates a verified copy and restore_database recovers it cleanly."""
    db_file = tmp_path / "data" / "hummingbird.db"
    db_file.parent.mkdir(parents=True, exist_ok=True)
    backup_dir = tmp_path / "data" / "backups"

    # Initialize a test database
    db_url = f"sqlite:///{db_file.as_posix()}"
    settings = Settings(database_url=db_url, demo_start_date=date(2026, 11, 4))
    db = Database(settings.database_url)
    db.create_schema()
    with db.write() as session:
        seed_demo(session, settings)
        state = session.get(PortfolioState, 1)
        state.name = "Pre-Backup Test State"

    # Take verified backup
    backup_path = backup_database(db_path=db_file, backup_dir=backup_dir)
    assert backup_path.exists()
    assert backup_path.name.startswith("hummingbird_")
    assert backup_path.name.endswith(".db")

    # Verify backup integrity directly
    conn = sqlite3.connect(str(backup_path))
    res = conn.execute("PRAGMA integrity_check;").fetchone()
    conn.close()
    assert res == ("ok",)

    # Mutate source database
    with db.write() as session:
        state = session.get(PortfolioState, 1)
        state.name = "Mutated State After Backup"

    # Close any open connections so files are unlocked on Windows
    db.engine.dispose()

    # Restore from backup
    restored = restore_database(backup_file=backup_path, target_db=db_file, create_safety_backup=False)
    assert restored == backup_path

    # Verify restored state
    with db.read() as session:
        state = session.get(PortfolioState, 1)
        assert state.name == "Pre-Backup Test State"


def test_find_latest_backup(tmp_path: Path):
    """Verify find_latest_backup returns the most recent backup."""
    b_dir = tmp_path / "backups"
    b_dir.mkdir(parents=True, exist_ok=True)

    b1 = b_dir / "hummingbird_20261107_100000.db"
    b2 = b_dir / "hummingbird_20261107_120000.db"
    b1.write_text("fake db 1")
    b2.write_text("fake db 2")

    latest = find_latest_backup(b_dir)
    assert latest == b2


def test_check_gateway_online_and_offline():
    """Verify check_gateway correctly distinguishes online vs offline states."""
    # Offline state
    off_res = check_gateway("http://127.0.0.1:59999")
    assert off_res.is_go is False
    assert "Offline" in off_res.details

    # Mocked online state
    with patch("urllib.request.urlopen") as mock_open:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__.return_value = mock_resp
        mock_open.return_value = mock_resp

        on_res = check_gateway("http://127.0.0.1:8642")
        assert on_res.is_go is True
        assert "Online" in on_res.details


def test_check_model_and_fallback():
    """Verify check_model_and_fallback verifies primary and fallback presence."""
    with patch("scripts.preflight.read_hermes_state") as mock_state:
        # Both present
        mock_state.return_value = {
            "primary_model": "gemini-3.1-flash-lite",
            "primary_provider": "gemini",
            "fallbacks": [{"model": "xiaomi/mimo-v2.6-pro", "provider": "openrouter"}],
        }
        res = check_model_and_fallback()
        assert res.is_go is True
        assert "gemini-3.1-flash-lite" in res.details
        assert "mimo-v2.6-pro" in res.details

        # Missing fallback
        mock_state.return_value = {
            "primary_model": "gemini-3.1-flash-lite",
            "primary_provider": "gemini",
            "fallbacks": [],
        }
        res_nofallback = check_model_and_fallback()
        assert res_nofallback.is_go is False
        assert "Fallback chain empty" in res_nofallback.details


def test_check_plugin_tools_count():
    """Verify check_plugin_tools validates the 25 tools registered in humming_bird."""
    res = check_plugin_tools()
    assert res.is_go is True
    assert "25 tools registered" in res.details


def test_check_kernel_token_logic(monkeypatch: pytest.MonkeyPatch):
    """Verify check_kernel_token verifies token presence."""
    monkeypatch.setenv("KERNEL_TOKEN", "hb-test-token-value-2026")
    res = check_kernel_token()
    assert res.is_go is True
    assert "Configured" in res.details

    monkeypatch.delenv("KERNEL_TOKEN", raising=False)
    with patch("dotenv.load_dotenv"), patch.object(Path, "exists", return_value=False):
        res_empty = check_kernel_token()
        assert res_empty.is_go is False


def test_check_portfolio_drift_zero(tmp_path: Path):
    """Verify check_portfolio_drift confirms exact 0.00 paisa drift on reconciled database."""
    db_file = tmp_path / "drift.db"
    db_url = f"sqlite:///{db_file.as_posix()}"
    settings = Settings(database_url=db_url, demo_start_date=date(2026, 11, 4))
    db = Database(settings.database_url)
    db.create_schema()
    with db.write() as session:
        seed_demo(session, settings)

    res = check_portfolio_drift(db)
    assert res.is_go is True
    assert "0.00 BDT" in res.details


def test_check_trading_mode_validations(tmp_path: Path):
    """Verify check_trading_mode validates LIVE_HOURS and TEST_OFFHOURS."""
    db_file = tmp_path / "mode.db"
    db_url = f"sqlite:///{db_file.as_posix()}"
    settings = Settings(database_url=db_url, demo_start_date=date(2026, 11, 4))
    db = Database(settings.database_url)
    db.create_schema()

    with db.write() as session:
        seed_demo(session, settings)
        state = session.get(PortfolioState, 1)
        state.trading_mode = "LIVE_HOURS"

    res_live = check_trading_mode(db)
    assert res_live.is_go is True
    assert "LIVE_HOURS" in res_live.details

    with db.write() as session:
        state = session.get(PortfolioState, 1)
        state.trading_mode = "TEST_OFFHOURS"

    res_test = check_trading_mode(db)
    assert res_test.is_go is True
    assert "TEST_OFFHOURS" in res_test.details


def test_check_caps_set_validations(tmp_path: Path):
    """Verify check_caps_set validates risk caps and kill switch configuration."""
    db_file = tmp_path / "caps.db"
    db_url = f"sqlite:///{db_file.as_posix()}"
    settings = Settings(database_url=db_url, demo_start_date=date(2026, 11, 4))
    db = Database(settings.database_url)
    db.create_schema()

    with db.write() as session:
        seed_demo(session, settings)
        state = session.get(PortfolioState, 1)
        state.max_order_bdt = Decimal("20000.00")
        state.max_symbol_bdt = Decimal("50000.00")
        state.daily_budget_bdt = Decimal("4000.00")
        state.max_orders_per_day = 20
        state.kill_switch_active = False

    res = check_caps_set(db)
    assert res.is_go is True
    assert "20,000" in res.details
    assert "KillSwitch: OFF" in res.details


def test_check_automation_state_validations(tmp_path: Path):
    """Verify check_automation_state inspects automation master switch and ingestion mode."""
    db_file = tmp_path / "auto.db"
    db_url = f"sqlite:///{db_file.as_posix()}"
    settings = Settings(database_url=db_url, demo_start_date=date(2026, 11, 4))
    db = Database(settings.database_url)
    db.create_schema()

    with db.write() as session:
        seed_demo(session, settings)
        state = session.get(PortfolioState, 1)
        state.automation_enabled = True
        state.paused = False
        state.ingestion_mode = "ONSCREEN_LIVE"
        state.polling_interval_sec = 60

    res = check_automation_state(db)
    assert res.is_go is True
    assert "Master Buy/Sell: ON" in res.details
    assert "ONSCREEN_LIVE" in res.details
