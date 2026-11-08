"""Production Circuit Breaker Service for Humming Bird DSE Trading Cockpit.

Invariants:
- Tracks consecutive failures across four categories:
  1. Auth (NOT_AUTHENTICATED / 401)
  2. Schema (SCHEMA_CHANGED / unexpected structure)
  3. Network (NETWORK / TIMEOUT / HTTP 5xx)
  4. Ledger mismatch (NO_RECEIPT / drift / ledger reconciliation mismatch)
- 3 consecutive failures -> trips circuit breaker:
  - Turns automation OFF (automation_enabled=False, paused=True)
  - Dispatches Telegram alert
  - Requires manual re-enable (blocks auto or operator enable until explicit reset)
- Special Rule: SCHEMA_CHANGED trips breaker IMMEDIATELY on first occurrence (halts trading at once)
- Successful order/cycle clears consecutive failure count to 0.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.config import Settings
from backend.database import Database, DecisionLog, KernelAuditLog, portfolio_state
from backend.engine.telegram_bot import send_telegram_alert, send_telegram_alert_sync

logger = logging.getLogger(__name__)


def record_circuit_failure(
    db: Database,
    settings: Settings,
    failure_type: str,
    detail: str,
    broadcaster: Any = None,
) -> bool:
    """Record an operational failure and trip the circuit breaker if thresholds are met.

    Returns True if circuit breaker is tripped, False otherwise.
    """
    f_type = failure_type.strip().upper()
    is_schema_divergence = f_type in ("SCHEMA_CHANGED", "SCHEMA")

    with db.write() as session:
        state = portfolio_state(session)
        state.consecutive_failure_count += 1
        count = state.consecutive_failure_count
        mode_val = getattr(state, "trading_mode", "LIVE_HOURS")

        # SCHEMA_CHANGED halts immediately on 1st occurrence
        if is_schema_divergence or count >= 3:
            state.circuit_breaker_tripped = True
            state.automation_enabled = False
            state.paused = True

            if is_schema_divergence:
                reason = f"SCHEMA_CHANGED: Immediate automation halt due to unexpected schema divergence: {detail}"
                action = "SCHEMA_CHANGED"
            else:
                reason = f"CIRCUIT_BREAKER: Automation tripped after {count} consecutive failures ({failure_type}): {detail}"
                action = "CIRCUIT_BREAKER_TRIPPED"

            state.circuit_breaker_reason = reason

            session.add(DecisionLog(
                cycle_id=None,
                symbol="SYSTEM",
                action=action,
                quantity=0,
                reason=reason,
                trading_mode=mode_val,
            ))

            session.add(KernelAuditLog(
                endpoint="/engine/circuit-breaker",
                action=action,
                symbol=None,
                payload={"failure_type": failure_type, "detail": detail, "consecutive_count": count},
                result={"circuit_breaker_tripped": True, "reason": reason},
                session_on=state.clock_date,
                trading_mode=mode_val,
            ))

            # UI Broadcast
            if broadcaster and hasattr(broadcaster, "publish"):
                broadcaster.publish("circuit_breaker_tripped", {
                    "reason": reason,
                    "failure_type": failure_type,
                    "consecutive_count": count,
                })

            # Telegram Alert
            if is_schema_divergence:
                tg_msg = (
                    "🚨 *IMMEDIATE HALT: Schema Changed*\n"
                    "Automation halted immediately to protect capital.\n"
                    f"*Detail:* {detail}\n"
                    "Manual inspection and /reset required."
                )
            else:
                tg_msg = (
                    "🚨 *Circuit Breaker Tripped*\n"
                    f"Automation turned OFF after {count} consecutive failures.\n"
                    f"*Failure Type:* `{failure_type}`\n"
                    f"*Detail:* {detail}\n"
                    "Manual re-enable required via Cockpit or /resume."
                )

            try:
                send_telegram_alert_sync(tg_msg, settings)
            except Exception as tg_err:
                logger.warning("Failed to dispatch circuit breaker Telegram alert: %s", tg_err)

            logger.error("Circuit breaker TRIPPED! Reason: %s", reason)
            return True

        logger.warning(
            "Circuit failure recorded: type=%s, count=%d/3, detail=%s",
            failure_type,
            count,
            detail,
        )
        return False


def record_circuit_success(db: Database) -> None:
    """Resets consecutive failure count on successful execution/cycle."""
    with db.write() as session:
        state = portfolio_state(session)
        if state.consecutive_failure_count > 0:
            state.consecutive_failure_count = 0


def reset_circuit_breaker(
    db: Database,
    settings: Settings | None = None,
    actor: str = "Operator",
    broadcaster: Any = None,
) -> dict[str, Any]:
    """Manually resets the tripped circuit breaker."""
    with db.write() as session:
        state = portfolio_state(session)
        was_tripped = state.circuit_breaker_tripped
        state.circuit_breaker_tripped = False
        state.consecutive_failure_count = 0
        state.circuit_breaker_reason = None

        session.add(KernelAuditLog(
            endpoint="/api/automation/circuit-breaker/reset",
            action="RESET_CIRCUIT_BREAKER",
            symbol=None,
            payload={"actor": actor, "was_tripped": was_tripped},
            result={"circuit_breaker_tripped": False},
            session_on=state.clock_date,
            trading_mode=state.trading_mode,
        ))

    if broadcaster and hasattr(broadcaster, "publish"):
        broadcaster.publish("circuit_breaker_reset", {
            "actor": actor,
            "status": "RESET",
        })

    if settings:
        tg_msg = f"✅ *Circuit Breaker Reset*\nReset by {actor}. Automation may now be safely resumed."
        try:
            send_telegram_alert_sync(tg_msg, settings)
        except Exception as tg_err:
            logger.warning("Telegram reset alert notice: %s", tg_err)

    return {
        "status": "RESET",
        "circuit_breaker_tripped": False,
        "consecutive_failure_count": 0,
        "message": "Circuit breaker successfully reset.",
    }


def is_circuit_breaker_tripped(db: Database) -> tuple[bool, str | None]:
    """Checks whether the circuit breaker is currently tripped."""
    with db.read() as session:
        state = portfolio_state(session)
        return bool(state.circuit_breaker_tripped), state.circuit_breaker_reason
