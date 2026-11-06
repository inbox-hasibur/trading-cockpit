"""Unit tests for Hermes OS Step 3: Natural Language Cron Scheduler and Skills/State API."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.config import DHAKA, Settings
from backend.database import Database, HermesCronJob, PortfolioState
from backend.hermes_os.cron_manager import (
    CronManager,
    is_cron_due,
    parse_natural_schedule,
)


def test_natural_schedule_parser_bangla():
    instruction = "Protidin sokal 10 tay StockNow sync kore L1 list check koro"
    parsed = parse_natural_schedule(instruction)
    assert parsed["schedule_expr"] == "0 10 * * 0-4"
    assert parsed["action_type"] == "SYNC_MARKET"
    assert parsed["params"].get("category") == "GSC_L1"
    assert "Market Hours" in parsed["name"] or "Market" in parsed["name"]


def test_natural_schedule_parser_banglish_interval():
    instruction = "Every 5 minutes during market hours sync portfolio and check canary theses"
    parsed = parse_natural_schedule(instruction)
    assert parsed["schedule_expr"] == "*/5 10-14 * * 0-4"
    assert parsed["action_type"] == "CHECK_CANARY"
    assert parsed["params"].get("sync_portfolio") is True


def test_natural_schedule_parser_english_curve():
    instruction = "Every day at 11:30 am inspect curve for BANKASIA"
    parsed = parse_natural_schedule(instruction)
    assert parsed["schedule_expr"] == "30 11 * * 0-4"
    assert parsed["action_type"] == "INSPECT_CURVE"
    assert parsed["params"].get("symbol") == "BANKASIA"


def test_natural_schedule_parser_all_dse_shares():
    instruction = "Protidin dupur 12 tay all dse shares sync koro"
    parsed = parse_natural_schedule(instruction)
    assert parsed["schedule_expr"] == "0 12 * * 0-4"
    assert parsed["action_type"] == "SYNC_ALL_SHARES"


def test_is_cron_due_matching():
    # 0 10 * * 0-4 -> 10:00 AM on Sunday (0) through Thursday (4)
    sunday_10am = datetime(2026, 11, 8, 10, 0, tzinfo=DHAKA)  # 2026-11-08 is Sunday
    assert is_cron_due("0 10 * * 0-4", sunday_10am) is True

    sunday_1001am = datetime(2026, 11, 8, 10, 1, tzinfo=DHAKA)
    assert is_cron_due("0 10 * * 0-4", sunday_1001am) is False

    friday_10am = datetime(2026, 11, 6, 10, 0, tzinfo=DHAKA)
    assert is_cron_due("0 10 * * 0-4", friday_10am) is False

    # Interval */5 10-14 * * 0-4
    t_1005 = datetime(2026, 11, 8, 10, 5, tzinfo=DHAKA)
    assert is_cron_due("*/5 10-14 * * 0-4", t_1005) is True

    t_1007 = datetime(2026, 11, 8, 10, 7, tzinfo=DHAKA)
    assert is_cron_due("*/5 10-14 * * 0-4", t_1007) is False


def test_cron_manager_crud(tmp_path):
    db_path = tmp_path / "test_cron.db"
    db = Database(f"sqlite:///{db_path.as_posix()}")
    db.create_schema()

    with db.write() as session:
        job = CronManager.schedule_task(
            session=session,
            instruction="Protidin sokal 10 tay sync koro",
        )
        assert job.id is not None
        assert job.schedule_expr == "0 10 * * 0-4"
        assert job.enabled is True

        # List
        jobs = CronManager.list_jobs(session)
        assert len(jobs) == 1
        assert jobs[0]["id"] == job.id

        # Toggle
        toggled = CronManager.toggle_job(session, job.id)
        assert toggled["enabled"] is False

        # Delete
        deleted = CronManager.delete_job(session, job.id)
        assert deleted is True

        # Verify empty
        assert len(CronManager.list_jobs(session)) == 0

    db.engine.dispose()


def test_hermes_crons_and_state_api(client):
    # 1. Test create cron via POST /api/hermes/crons
    res = client.post("/api/hermes/crons", json={
        "natural_instruction": "Every 5 minutes during market hours sync portfolio and check canary theses",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    job_id = data["cron"]["id"]
    assert data["cron"]["schedule_expr"] == "*/5 10-14 * * 0-4"

    # 2. Test list crons via GET /api/hermes/crons
    res = client.get("/api/hermes/crons")
    assert res.status_code == 200
    crons_data = res.json()
    assert crons_data["total"] >= 1
    assert any(c["id"] == job_id for c in crons_data["crons"])

    # 3. Test toggle cron via POST /api/hermes/crons/{id}/toggle
    res = client.post(f"/api/hermes/crons/{job_id}/toggle", json={})
    assert res.status_code == 200
    assert res.json()["job"]["enabled"] is False

    # 4. Test state endpoint via GET /api/hermes/state
    res = client.get("/api/hermes/state")
    assert res.status_code == 200
    state_data = res.json()
    assert "user_md" in state_data
    assert "memory_md" in state_data
    assert "skills" in state_data
    assert "crons" in state_data
    assert "active_model" in state_data

    # 5. Test delete cron via DELETE /api/hermes/crons/{id}
    res = client.delete(f"/api/hermes/crons/{job_id}")
    assert res.status_code == 200
    assert res.json()["deleted_id"] == job_id

    # Verify deletion
    res = client.get("/api/hermes/crons")
    assert all(c["id"] != job_id for c in res.json()["crons"])
