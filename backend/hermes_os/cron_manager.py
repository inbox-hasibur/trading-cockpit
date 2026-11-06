"""Hermes OS Natural-Language Cron Scheduler & Watchdog Manager.

Provides:
1. Natural language schedule parser supporting Bangla, Banglish, and English instructions:
   - "Protidin sokal 10 tay StockNow sync kore L1 list check koro" -> 0 10 * * 0-4
   - "Every 5 minutes during market hours sync portfolio and check canary theses" -> */5 10-14 * * 0-4
2. Persistent SQLite-backed HermesCronJob storage in backend/database.py.
3. Execution dispatcher integrated with DSEMarketScheduler and Humming Bird toolsets.
4. API and Tool bindings for natural operator scheduling, list, pause, and delete.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import DHAKA, Settings, utc_now_iso
from backend.database import HermesCronJob, PortfolioState
from backend.hermes.secret_guard import redact_secrets

logger = logging.getLogger("hermes.cron")


def parse_natural_schedule(instruction: str) -> dict[str, Any]:
    """Parses natural Bangla, Banglish, or English scheduling instructions into structured cron attributes."""
    clean = redact_secrets(instruction.strip())
    lower = clean.lower()

    # 1. Action Type & Parameter Extraction
    action_type = "SYNC_MARKET"
    params: dict[str, Any] = {}

    sym_match = re.search(r"\b([A-Z0-9]{3,12})\b", clean)
    if "canary" in lower or "theses" in lower or "probe" in lower:
        action_type = "CHECK_CANARY"
        if "portfolio" in lower:
            params["sync_portfolio"] = True
    elif "all dse" in lower or "all share" in lower or "all_shares" in lower or "price board" in lower:
        action_type = "SYNC_ALL_SHARES"
    elif "portfolio" in lower or "holdings" in lower or "ledger" in lower:
        action_type = "SYNC_PORTFOLIO"
    elif "curve" in lower or "support" in lower or "floor" in lower or "drawdown" in lower:
        action_type = "INSPECT_CURVE"
        if sym_match and sym_match.group(1).upper() not in {"DSE", "L1", "L2", "GSC", "ALL", "SYNC"}:
            params["symbol"] = sym_match.group(1).upper()

    # Watchlist category hints
    if "l1" in lower or "gsc_l1" in lower:
        params["category"] = "GSC_L1"
    elif "l2" in lower or "gsc_l2" in lower:
        params["category"] = "GSC_L2"
    elif "gsc" in lower:
        params["category"] = "GSC"

    # Human-readable title
    action_labels = {
        "SYNC_MARKET": "Market Sync",
        "SYNC_ALL_SHARES": "All DSE Shares Sync",
        "SYNC_PORTFOLIO": "Portfolio Sync",
        "CHECK_CANARY": "Canary Theses Check",
        "INSPECT_CURVE": f"Curve Inspection {params.get('symbol', '')}".strip(),
    }
    action_label = action_labels.get(action_type, "Autonomous Task")

    # 2. Timing & Cron Expression Extraction
    schedule_expr = "0 10 * * 0-4"  # Default: 10:00 AM on DSE trading days (Sun-Thu)

    # A. Interval: "every N minutes" / "proti N minite"
    m_min = re.search(r"(?:every|proti|each)\s*(\d+)?\s*(?:minute|min|minit|m|minite)", lower)
    if m_min:
        n = int(m_min.group(1)) if m_min.group(1) else 5
        if "market hour" in lower or "market e" in lower or "trading" in lower or "dse" in lower:
            schedule_expr = f"*/{n} 10-14 * * 0-4"
            name = f"Every {n}-min Market Hours {action_label}"
        else:
            schedule_expr = f"*/{n} * * * *"
            name = f"Every {n}-min {action_label}"
        return {
            "name": name,
            "schedule_expr": schedule_expr,
            "action_type": action_type,
            "params": params,
            "natural_instruction": clean,
        }

    # B. Daily at specific time: "sokal 10 tay", "at 10:15 am", "protidin 10 am"
    m_time = re.search(r"(?:sokal|morning|dupur|at|tay|e|bikel)?\s*(\d{1,2})(?::(\d{2}))?\s*(?:ta|tay|am|pm)?", lower)
    m_daily = re.search(r"(?:protidin|every\s*day|daily|sokal|proti\s*din|at)\s*.*?(\d{1,2})(?::(\d{2}))?\s*(?:ta|tay|am|pm)?", lower)
    chosen_match = m_daily or m_time
    if chosen_match:
        try:
            hr = int(chosen_match.group(1))
            mn = int(chosen_match.group(2)) if chosen_match.group(2) else 0
            if "pm" in lower and hr < 12:
                hr += 12
            if hr <= 23 and mn <= 59:
                schedule_expr = f"{mn} {hr} * * 0-4"
                name = f"Daily {hr:02d}:{mn:02d} {action_label}"
                return {
                    "name": name,
                    "schedule_expr": schedule_expr,
                    "action_type": action_type,
                    "params": params,
                    "natural_instruction": clean,
                }
        except Exception:
            pass

    name = f"Scheduled {action_label}"
    return {
        "name": name,
        "schedule_expr": schedule_expr,
        "action_type": action_type,
        "params": params,
        "natural_instruction": clean,
    }


def match_cron_field(pattern: str, val: int) -> bool:
    """Matches an integer value against a single cron field pattern."""
    pat = pattern.strip()
    if pat == "*":
        return True
    if pat.startswith("*/"):
        try:
            step = int(pat[2:])
            return (val % step) == 0
        except ValueError:
            return False
    if "-" in pat:
        try:
            start_s, end_s = pat.split("-", 1)
            return int(start_s) <= val <= int(end_s)
        except ValueError:
            return False
    if "," in pat:
        try:
            allowed = [int(p) for p in pat.split(",")]
            return val in allowed
        except ValueError:
            return False
    try:
        return int(pat) == val
    except ValueError:
        return False


def is_cron_due(schedule_expr: str, now_dt: datetime) -> bool:
    """Evaluates if a 5-field cron expression matches the given datetime in Asia/Dhaka time."""
    parts = schedule_expr.strip().split()
    if len(parts) != 5:
        # If expression is a raw interval in seconds
        return False

    min_pat, hr_pat, dom_pat, mon_pat, dow_pat = parts
    minute = now_dt.minute
    hour = now_dt.hour
    day = now_dt.day
    month = now_dt.month
    # Python weekday: Mon=0 .. Sun=6. Standard Cron: Sun=0, Mon=1 .. Thu=4, Fri=5, Sat=6.
    # Convert Python weekday to Cron: (weekday + 1) % 7 -> Sun=0, Mon=1, ..., Thu=4, Fri=5, Sat=6
    cron_dow = (now_dt.weekday() + 1) % 7

    return (
        match_cron_field(min_pat, minute)
        and match_cron_field(hr_pat, hour)
        and match_cron_field(dom_pat, day)
        and match_cron_field(mon_pat, month)
        and match_cron_field(dow_pat, cron_dow)
    )


class CronManager:
    """Persistent SQLite-backed cron manager with execution dispatch."""

    @staticmethod
    def schedule_task(
        session: Session,
        name: str | None = None,
        schedule_expr: str | None = None,
        action_type: str | None = None,
        params: dict[str, Any] | None = None,
        natural_instruction: str | None = None,
        instruction: str | None = None,
    ) -> HermesCronJob:
        """Schedules a new recurring autonomous cron job."""
        raw_instruction = natural_instruction or instruction
        if raw_instruction and (not schedule_expr or not action_type):
            parsed = parse_natural_schedule(raw_instruction)
            name = name or parsed["name"]
            schedule_expr = schedule_expr or parsed["schedule_expr"]
            action_type = action_type or parsed["action_type"]
            params = params if params is not None else parsed.get("params", {})
            natural_instruction = raw_instruction
        else:
            name = name or "Autonomous Hermes Task"
            schedule_expr = schedule_expr or "0 10 * * 0-4"
            action_type = (action_type or "SYNC_MARKET").upper()
            params = params or {}

        job_id = f"cron_{uuid4().hex[:10]}"
        job = HermesCronJob(
            id=job_id,
            name=name[:120],
            schedule_expr=schedule_expr[:64],
            natural_instruction=(natural_instruction or "")[:500],
            action_type=action_type[:64],
            params=params,
            enabled=True,
            last_status="PENDING",
            created_at=utc_now_iso(),
        )
        session.add(job)
        session.flush()
        logger.info("Hermes OS scheduled cron job '%s' (%s, %s)", job.name, job.schedule_expr, job.action_type)
        return job

    @staticmethod
    def list_jobs(session: Session) -> list[dict[str, Any]]:
        """Returns all scheduled cron jobs as dictionaries."""
        jobs = list(session.scalars(select(HermesCronJob).order_by(HermesCronJob.created_at.desc())))
        return [
            {
                "id": j.id,
                "name": j.name,
                "schedule_expr": j.schedule_expr,
                "natural_instruction": j.natural_instruction,
                "action_type": j.action_type,
                "params": j.params or {},
                "enabled": j.enabled,
                "last_run_at": j.last_run_at,
                "last_status": j.last_status,
                "last_result": j.last_result,
                "created_at": j.created_at,
            }
            for j in jobs
        ]

    @staticmethod
    def delete_job(session: Session, job_id: str) -> bool:
        """Deletes a cron job by id."""
        job = session.get(HermesCronJob, job_id)
        if not job:
            return False
        session.delete(job)
        session.flush()
        logger.info("Hermes OS deleted cron job '%s'", job_id)
        return True

    @staticmethod
    def toggle_job(session: Session, job_id: str, enabled: bool | None = None) -> dict[str, Any] | None:
        """Toggles or sets the enabled state of a cron job."""
        job = session.get(HermesCronJob, job_id)
        if not job:
            return None
        job.enabled = not job.enabled if enabled is None else bool(enabled)
        session.flush()
        logger.info("Hermes OS set cron job '%s' enabled=%s", job_id, job.enabled)
        return {
            "id": job.id,
            "name": job.name,
            "enabled": job.enabled,
        }

    @staticmethod
    def execute_job(
        job: HermesCronJob,
        session: Session,
        settings: Settings,
        client: Any | None = None,
    ) -> dict[str, Any]:
        """Executes the specific action defined by the cron job."""
        from backend.hermes_os.toolsets import default_registry, ToolContext
        state = session.get(PortfolioState, 1)
        if not state:
            return {"status": "ERROR", "error": "PortfolioState missing"}

        ctx = ToolContext(
            session=session,
            state=state,
            settings=settings,
            stocknow_client=client,
        )

        res: dict[str, Any] = {}
        now_iso = utc_now_iso()
        try:
            if job.action_type in ("SYNC_MARKET", "SYNC_FAVORITES"):
                res = default_registry.execute("sync_favorites_3_lists", job.params or {}, ctx)
            elif job.action_type == "SYNC_PORTFOLIO":
                res = default_registry.execute("sync_portfolio_164580", job.params or {}, ctx)
            elif job.action_type in ("CHECK_CANARY", "CANARY_CHECK"):
                res = default_registry.execute("evaluate_canary_outcomes", job.params or {}, ctx)
            elif job.action_type == "SYNC_ALL_SHARES":
                res = default_registry.execute("sync_all_dse_shares", job.params or {}, ctx)
            elif job.action_type == "INSPECT_CURVE":
                sym = (job.params or {}).get("symbol", "BANKASIA")
                res = default_registry.execute("inspect_curve_and_support", {"symbol": sym}, ctx)
            else:
                res = {"status": "SUCCESS", "message": f"Autonomous execution for {job.action_type}"}

            job.last_run_at = now_iso
            job.last_status = "SUCCESS"
            job.last_result = str(res)[:990]
        except Exception as exc:
            job.last_run_at = now_iso
            job.last_status = "FAILED"
            job.last_result = f"Error: {exc}"[:990]
            res = {"status": "FAILED", "error": str(exc)}

        session.flush()
        return res

    @classmethod
    def check_and_execute_due_jobs(
        cls,
        session: Session,
        settings: Settings,
        client: Any | None = None,
        now_dt: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Finds all active cron jobs due at now_dt (Asia/Dhaka) and executes them."""
        dt = now_dt or datetime.now(DHAKA)
        due_jobs = list(session.scalars(select(HermesCronJob).where(HermesCronJob.enabled == True)))
        results = []

        cur_minute_str = dt.strftime("%Y-%m-%d %H:%M")
        for job in due_jobs:
            # Prevent double execution within the exact same minute
            if job.last_run_at and job.last_run_at.startswith(cur_minute_str):
                continue

            if is_cron_due(job.schedule_expr, dt):
                logger.info("Executing scheduled cron job: '%s' (%s)", job.name, job.action_type)
                exec_res = cls.execute_job(job, session, settings, client=client)
                results.append({"job_id": job.id, "name": job.name, "result": exec_res})

        return results
