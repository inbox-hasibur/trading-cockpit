"""System Heartbeat, Dead-Man Watchdog, and DSE 14:45 Daily Summary Service.

Invariants:
- Heartbeat every minute to SQLite (system_heartbeats table).
- Dead-man alert dispatched to Telegram if heartbeat ceases during DSE market hours.
- Daily summary at 14:45 Asia/Dhaka aggregating orders, skips, drift, errors to Telegram and SQLite.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
import logging
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import delete, func, select

from backend.config import Settings, utc_now_iso
from backend.database import (
    DailySummaryLog,
    Database,
    DecisionLog,
    KernelAuditLog,
    SystemHeartbeat,
    TradeLog,
    portfolio_state,
)
from backend.engine.scheduler import DHAKA, is_dse_market_open
from backend.engine.telegram_bot import send_telegram_alert, send_telegram_alert_sync

logger = logging.getLogger(__name__)

# State flag to prevent deadman spamming within the same outage
_LAST_DEADMAN_ALERT_TIME: datetime | None = None


def record_system_heartbeat(db: Database, settings: Settings | None = None) -> SystemHeartbeat:
    """Records a single 1-minute system heartbeat to SQLite and prunes entries older than 7 days."""
    with db.write() as session:
        state = portfolio_state(session)
        hb = SystemHeartbeat(
            status="OK",
            ingestion_mode=getattr(state, "ingestion_mode", "BACKGROUND_POLLING"),
            trading_mode=getattr(state, "trading_mode", "LIVE_HOURS"),
            automation_enabled=getattr(state, "automation_enabled", True),
            kill_switch_active=getattr(state, "kill_switch_active", False),
            circuit_breaker_tripped=getattr(state, "circuit_breaker_tripped", False),
            details={
                "clock_date": state.clock_date.isoformat(),
                "revision": state.revision,
                "startup_health_status": getattr(state, "startup_health_status", "READY"),
                "consecutive_failure_count": getattr(state, "consecutive_failure_count", 0),
            },
            created_at=utc_now_iso(),
        )
        session.add(hb)

        # Prune older than 7 days
        cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        session.execute(delete(SystemHeartbeat).where(SystemHeartbeat.created_at < cutoff))
        session.flush()
        return hb


def check_dead_man_switch(
    db: Database,
    settings: Settings,
    now_dhaka: datetime | None = None,
) -> bool:
    """Checks if the heartbeat is stale (>120s) during DSE market hours.

    Dispatches a Telegram dead-man alert if stale. Returns True if alert was triggered.
    """
    global _LAST_DEADMAN_ALERT_TIME
    if now_dhaka is None:
        now_dhaka = datetime.now(DHAKA)

    market_check = is_dse_market_open(now_dhaka=now_dhaka, settings=settings)
    if not market_check["is_open"]:
        return False

    with db.read() as session:
        stmt = select(SystemHeartbeat).order_by(SystemHeartbeat.created_at.desc()).limit(1)
        latest_hb = session.scalar(stmt)

    now_utc = datetime.now(timezone.utc)
    is_stale = False
    last_str = "Never"

    if latest_hb is None:
        is_stale = True
    else:
        last_str = latest_hb.created_at
        try:
            last_dt = datetime.fromisoformat(latest_hb.created_at.replace("Z", "+00:00"))
            elapsed = (now_utc - last_dt).total_seconds()
            if elapsed > 120.0:
                is_stale = True
        except Exception:
            is_stale = True

    if is_stale:
        # Throttle deadman alert to once every 10 minutes
        if _LAST_DEADMAN_ALERT_TIME and (now_utc - _LAST_DEADMAN_ALERT_TIME).total_seconds() < 600:
            return False

        _LAST_DEADMAN_ALERT_TIME = now_utc
        msg = (
            "🚨 *DEAD-MAN ALERT: Cockpit Heartbeat Stopped*\n"
            "The Cockpit has stopped recording heartbeats during live DSE market hours!\n"
            f"*Last Heartbeat:* `{last_str}`\n"
            "*Status:* System may have crashed, frozen, or lost power."
        )
        try:
            send_telegram_alert_sync(msg, settings)
        except Exception as exc:
            logger.warning("Could not dispatch deadman alert: %s", exc)
        return True

    return False


def send_daily_summary_if_due(
    db: Database,
    settings: Settings,
    now_dhaka: datetime | None = None,
    force: bool = False,
) -> bool:
    """Generates and sends the 14:45 Asia/Dhaka daily session summary to Telegram and logs to SQLite.

    Returns True if summary was generated and sent.
    """
    from decimal import Decimal
    from backend.engine.t2_ledger import TradingCalendar

    if now_dhaka is None:
        now_dhaka = datetime.now(DHAKA)

    calendar = TradingCalendar(settings.holidays, settings.bucket_anchor)
    session_date = now_dhaka.date()

    if not force:
        # Check if today is a trading session
        if not calendar.is_session(session_date):
            return False

        # Check if 14:45 Asia/Dhaka has arrived
        target_time = time(14, 45)
        if now_dhaka.time() < target_time:
            return False

    # Check if summary for this date has already been logged
    with db.read() as session:
        existing = session.scalar(
            select(DailySummaryLog).where(DailySummaryLog.session_date == session_date)
        )
        if existing and not force:
            return False

    # Aggregate today's metrics
    with db.read() as session:
        # 1. Orders
        trades = list(session.scalars(select(TradeLog).where(TradeLog.trade_on == session_date)))
        orders_count = len(trades)
        buys = [t for t in trades if t.side == "BUY"]
        sells = [t for t in trades if t.side == "SELL"]
        buys_count = len(buys)
        sells_count = len(sells)
        buy_spend = sum((abs(t.net_cash_change) for t in buys), Decimal("0.00"))
        sell_proceeds = sum((t.net_cash_change for t in sells), Decimal("0.00"))

        # 2. Skips Breakdown from DecisionLog
        date_str = session_date.isoformat()
        decisions = list(session.scalars(
            select(DecisionLog).where(DecisionLog.created_at.like(f"{date_str}%"))
        ))
        skips_breakdown: dict[str, int] = {}
        for d in decisions:
            act = d.action.upper()
            if any(skip_word in act for skip_word in ("SKIP", "WAIT", "BLOCKED", "PREVIEW", "CAPS", "NO_SESSION", "MARKET_CLOSED")):
                skips_breakdown[act] = skips_breakdown.get(act, 0) + 1
        skips_count = sum(skips_breakdown.values())

        # 3. Errors
        error_logs = list(session.scalars(
            select(KernelAuditLog).where(
                KernelAuditLog.session_on == session_date,
                KernelAuditLog.action.like("%FAILED%") | KernelAuditLog.action.like("%ERROR%"),
            )
        ))
        errors_count = len(error_logs)
        errors_summary = [f"{l.action}: {l.payload.get('error_code', '')}" for l in error_logs[:5]]

        drift_bdt = Decimal("0.00")

    # Format Telegram Message
    skips_formatted = ", ".join(f"{k}: {v}" for k, v in list(skips_breakdown.items())[:4]) or "None"
    summary_msg = (
        f"📊 *DSE Daily Session Summary — {session_date.isoformat()}*\n"
        f"• *Orders Executed:* {orders_count} ({buys_count} buys, {sells_count} sells)\n"
        f"• *Capital Flow:* Buy: ৳{buy_spend:.2f} | Sell: ৳{sell_proceeds:.2f}\n"
        f"• *Skips:* {skips_count} ({skips_formatted})\n"
        f"• *Drift:* ৳{drift_bdt:.2f}\n"
        f"• *Errors:* {errors_count}\n"
        "• *Market Status:* Closed (14:45 post-session review complete)"
    )

    tg_sent = False
    try:
        tg_sent = bool(send_telegram_alert_sync(summary_msg, settings))
    except Exception as exc:
        logger.warning("Failed to dispatch daily summary Telegram alert: %s", exc)

    # Persist DailySummaryLog
    with db.write() as session:
        log = DailySummaryLog(
            session_date=session_date,
            orders_count=orders_count,
            buys_count=buys_count,
            sells_count=sells_count,
            buy_spend_bdt=buy_spend,
            sell_proceeds_bdt=sell_proceeds,
            skips_count=skips_count,
            skips_breakdown=skips_breakdown,
            drift_bdt=drift_bdt,
            errors_count=errors_count,
            errors_summary=errors_summary,
            telegram_sent=tg_sent,
            created_at=utc_now_iso(),
        )
        session.add(log)

    logger.info("Daily session summary sent and logged for %s", session_date)
    return True
