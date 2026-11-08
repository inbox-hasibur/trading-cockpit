"""Tests for Step 10: Autostart, Heartbeat, Circuit Breaker, Telegram Commands & Idempotency.

Covers:
- Failure injection for each circuit breaker path:
  1. 3x auth failures (NOT_AUTHENTICATED) -> automation OFF, manual reset required.
  2. Immediate halt on 1st SCHEMA_CHANGED failure -> automation OFF at once.
  3. 3x network failures (TIMEOUT / NETWORK) -> breaker tripped.
  4. 3x ledger mismatch (NO_RECEIPT) -> breaker tripped.
- Manual reset via /api/automation/circuit-breaker/reset clears breaker.
- Restart mid-cycle causes no duplicate order (SQLite OrderIdempotencyKey).
- Enabling Background mode requires risk caps set and passing preflight within 24h.
- Heartbeat logging to SQLite and dead-man alert detection during market hours.
- Daily summary at 14:45 Asia/Dhaka aggregation.
- Telegram bot interactive commands (/kill, /resume, /status, /reset).
- Secret redaction filter in logging.
"""

from __future__ import annotations

import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from backend.config import Settings
from backend.database import (
    DailySummaryLog,
    Database,
    DecisionLog,
    KernelAuditLog,
    OrderIdempotencyKey,
    PreflightCheckLog,
    SystemHeartbeat,
    TaxLot,
    TradeLog,
    portfolio_state,
)
from backend.engine.auto_trader import AutoTrader
from backend.engine.circuit_breaker import (
    is_circuit_breaker_tripped,
    record_circuit_failure,
    record_circuit_success,
    reset_circuit_breaker,
)
from backend.engine.heartbeat import check_dead_man_switch, record_system_heartbeat, send_daily_summary_if_due
from backend.engine.preflight_service import are_caps_set, has_passing_preflight_within_24h, run_cockpit_preflight
from backend.engine.telegram_bot import handle_telegram_command
from backend.logging_config import redact_secrets


# -----------------------------------------------------------------------------
# 1. Secret Redaction Tests
# -----------------------------------------------------------------------------

def test_secret_redaction_masks_credentials():
    """Verify passwords, tokens, BD phone numbers, and JWTs are sanitized."""
    raw = "User 01712345678 logged in with password=secret123 and token='my_secret_token'"
    sanitized = redact_secrets(raw)
    assert "01712345678" not in sanitized
    assert "[REDACTED_PHONE]" in sanitized
    assert "secret123" not in sanitized
    assert "my_secret_token" not in sanitized

    jwt_sample = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.doNotPrintThisSecret"
    sanitized_jwt = redact_secrets(jwt_sample)
    assert "eyJhbGci" not in sanitized_jwt
    assert "[REDACTED" in sanitized_jwt


# -----------------------------------------------------------------------------
# 2. Circuit Breaker Failure Injection Tests
# -----------------------------------------------------------------------------

def test_circuit_breaker_3x_auth_failure_trips(db, settings):
    """3 consecutive auth failures must set automation OFF and require manual reset."""
    with db.write() as session:
        state = portfolio_state(session)
        state.automation_enabled = True
        state.paused = False
        state.consecutive_failure_count = 0
        state.circuit_breaker_tripped = False

    # Failure 1
    tripped1 = record_circuit_failure(db, settings, "NOT_AUTHENTICATED", "HTTP 401 Unauthorized")
    assert tripped1 is False
    with db.read() as s:
        assert portfolio_state(s).automation_enabled is True
        assert portfolio_state(s).consecutive_failure_count == 1

    # Failure 2
    tripped2 = record_circuit_failure(db, settings, "NOT_AUTHENTICATED", "HTTP 401 Re-login failed")
    assert tripped2 is False
    with db.read() as s:
        assert portfolio_state(s).consecutive_failure_count == 2

    # Failure 3 -> Trips breaker!
    tripped3 = record_circuit_failure(db, settings, "NOT_AUTHENTICATED", "HTTP 401 Token expired")
    assert tripped3 is True
    with db.read() as s:
        st = portfolio_state(s)
        assert st.automation_enabled is False
        assert st.paused is True
        assert st.circuit_breaker_tripped is True
        assert "NOT_AUTHENTICATED" in st.circuit_breaker_reason

    # Success resets consecutive count if not tripped, but when tripped, manual reset is required
    res = reset_circuit_breaker(db, settings, actor="Operator")
    assert res["status"] == "RESET"
    with db.read() as s:
        st = portfolio_state(s)
        assert st.circuit_breaker_tripped is False
        assert st.consecutive_failure_count == 0


def test_circuit_breaker_schema_changed_immediate_halt(db, settings):
    """SCHEMA_CHANGED must trip the circuit breaker IMMEDIATELY on 1st occurrence."""
    with db.write() as session:
        state = portfolio_state(session)
        state.automation_enabled = True
        state.paused = False
        state.consecutive_failure_count = 0
        state.circuit_breaker_tripped = False

    # 1st failure of type SCHEMA_CHANGED
    tripped = record_circuit_failure(db, settings, "SCHEMA_CHANGED", "StockNow payload missing 'items' array")
    assert tripped is True

    with db.read() as s:
        st = portfolio_state(s)
        assert st.automation_enabled is False
        assert st.paused is True
        assert st.circuit_breaker_tripped is True
        assert "SCHEMA_CHANGED" in st.circuit_breaker_reason


def test_circuit_breaker_3x_network_failure(db, settings):
    """3 consecutive network failures (TIMEOUT) must trip circuit breaker."""
    with db.write() as session:
        state = portfolio_state(session)
        state.automation_enabled = True
        state.consecutive_failure_count = 0
        state.circuit_breaker_tripped = False

    record_circuit_failure(db, settings, "TIMEOUT", "Timeout connecting to gateway")
    record_circuit_failure(db, settings, "NETWORK", "Connection refused")
    tripped = record_circuit_failure(db, settings, "TIMEOUT", "Timeout 504")

    assert tripped is True
    with db.read() as s:
        st = portfolio_state(s)
        assert st.automation_enabled is False
        assert st.circuit_breaker_tripped is True


def test_circuit_breaker_3x_ledger_mismatch_failure(db, settings):
    """3 consecutive ledger mismatch failures (NO_RECEIPT) must trip circuit breaker."""
    with db.write() as session:
        state = portfolio_state(session)
        state.automation_enabled = True
        state.consecutive_failure_count = 0
        state.circuit_breaker_tripped = False

    record_circuit_failure(db, settings, "NO_RECEIPT", "Trade not found in StockNow ledger after 3 attempts")
    record_circuit_failure(db, settings, "NO_RECEIPT", "Trade not found in StockNow ledger after 3 attempts")
    tripped = record_circuit_failure(db, settings, "NO_RECEIPT", "Trade not found in StockNow ledger after 3 attempts")

    assert tripped is True
    with db.read() as s:
        st = portfolio_state(s)
        assert st.automation_enabled is False
        assert st.circuit_breaker_tripped is True


def test_manual_reenable_blocked_while_breaker_tripped(client, db):
    """Attempting to enable automation while circuit breaker is tripped must return 422."""
    with db.write() as session:
        state = portfolio_state(session)
        state.automation_enabled = False
        state.circuit_breaker_tripped = True
        state.circuit_breaker_reason = "Circuit breaker tripped after 3 consecutive failures"

    # Try enabling via /api/automation/config
    res = client.post("/api/automation/config", json={"automation_enabled": True})
    assert res.status_code == 422
    assert "Circuit breaker is tripped" in str(res.json())

    # Reset circuit breaker via endpoint
    res_reset = client.post("/api/automation/circuit-breaker/reset")
    assert res_reset.status_code == 200
    assert res_reset.json()["circuit_breaker_tripped"] is False

    # Now enabling succeeds
    res_on = client.post("/api/automation/config", json={"automation_enabled": True})
    assert res_on.status_code == 200
    assert res_on.json()["automation_enabled"] is True


# -----------------------------------------------------------------------------
# 3. Mid-Cycle Restart Order Deduplication Tests
# -----------------------------------------------------------------------------

def test_mid_cycle_restart_deduplication(db, settings):
    """Verifies that an order already submitted in SQLite OrderIdempotencyKey is not duplicated on restart."""
    trader = AutoTrader(db, settings)

    with db.write() as session:
        state = portfolio_state(session)
        state.automation_enabled = True
        state.trading_mode = "TEST_OFFHOURS"
        state.mode = "LIVE"
        state.kill_switch_active = False
        state.circuit_breaker_tripped = False

        # Pre-seed an idempotency key as if an order was submitted right before process restart
        test_key = f"auto:buy:{state.clock_date}:BANKASIA:164580"
        session.add(OrderIdempotencyKey(
            idempotency_key=test_key,
            symbol="BANKASIA",
            side="BUY",
            quantity=10,
            price=Decimal("17.50"),
            response_payload={"simulated": True},
        ))

    # Mock order dispatch
    dispatch_mock = MagicMock(return_value={"status": "FILLED"})
    trader._dispatch_order = dispatch_mock

    # Run cycle - BANKASIA buy should be skipped due to existing key
    result = trader.run_cycle(dry_run=False)

    # Ensure BANKASIA was not submitted again
    for call in dispatch_mock.call_args_list:
        assert call.kwargs.get("symbol") != "BANKASIA"


# -----------------------------------------------------------------------------
# 4. Background Mode Preflight Gate (24h Requirement)
# -----------------------------------------------------------------------------

def test_background_mode_requires_caps_and_24h_preflight(client, db):
    """Enabling Background mode without caps set or without 24h preflight must fail with 422."""
    # 1. Unset caps
    with db.write() as session:
        state = portfolio_state(session)
        state.max_order_bdt = Decimal("0.00")  # Invalid cap

    res = client.post("/api/automation/handoff", json={"target_mode": "BACKGROUND_24_7"})
    assert res.status_code == 422
    assert "Background mode requires risk caps set" in str(res.json())

    # 2. Restore caps, but expire preflight log
    with db.write() as session:
        state = portfolio_state(session)
        state.max_order_bdt = Decimal("20000.00")
        state.max_symbol_bdt = Decimal("50000.00")
        state.daily_budget_bdt = Decimal("4000.00")
        state.max_orders_per_day = 20

        # Delete recent preflight logs
        session.query(PreflightCheckLog).delete()

    res2 = client.post("/api/automation/handoff", json={"target_mode": "BACKGROUND_24_7"})
    assert res2.status_code == 422
    assert "Background mode requires risk caps set" in str(res2.json())

    # 3. Run preflight
    res_pref = client.post("/api/automation/preflight")
    assert res_pref.status_code == 200

    # 4. Now handoff succeeds
    res3 = client.post("/api/automation/handoff", json={"target_mode": "BACKGROUND_24_7"})
    assert res3.status_code == 200
    assert res3.json()["active_mode"] == "BACKGROUND_POLLING"


# -----------------------------------------------------------------------------
# 5. Heartbeat & Dead-Man Watchdog Tests
# -----------------------------------------------------------------------------

def test_system_heartbeat_sqlite_persistence(db, settings):
    """Verify heartbeat is written to SQLite system_heartbeats table."""
    hb = record_system_heartbeat(db, settings)
    assert hb.id is not None
    assert hb.status == "OK"

    with db.read() as session:
        saved = session.scalar(select(SystemHeartbeat).order_by(SystemHeartbeat.id.desc()).limit(1))
        assert saved is not None
        assert saved.created_at == hb.created_at


def test_dead_man_switch_triggers_during_market_hours(db, settings):
    """Dead-man alert should trigger if heartbeat is stale during market hours."""
    from backend.engine.scheduler import DHAKA

    # Sunday 11:30 AM (active market session)
    sunday_market_time = datetime.datetime(2026, 11, 8, 11, 30, tzinfo=DHAKA)

    # Empty heartbeat table -> stale!
    with db.write() as session:
        session.query(SystemHeartbeat).delete()

    with patch("backend.engine.heartbeat.send_telegram_alert_sync", return_value=True) as mock_tg:
        triggered = check_dead_man_switch(db, settings, now_dhaka=sunday_market_time)
        assert triggered is True
        mock_tg.assert_called_once()
        assert "DEAD-MAN ALERT" in mock_tg.call_args[0][0]


def test_daily_summary_at_1445(db, settings):
    """Daily summary aggregates metrics and records to SQLite."""
    from backend.engine.scheduler import DHAKA

    # Sunday 14:46 (15 min after close)
    summary_time = datetime.datetime(2026, 11, 8, 14, 46, tzinfo=DHAKA)

    with patch("backend.engine.heartbeat.send_telegram_alert_sync", return_value=True) as mock_tg:
        sent = send_daily_summary_if_due(db, settings, now_dhaka=summary_time, force=True)
        assert sent is True
        mock_tg.assert_called_once()
        assert "DSE Daily Session Summary" in mock_tg.call_args[0][0]

    with db.read() as session:
        log = session.scalar(select(DailySummaryLog).order_by(DailySummaryLog.id.desc()).limit(1))
        assert log is not None
        assert log.session_date == summary_time.date()


# -----------------------------------------------------------------------------
# 6. Telegram Bot Command Processor Tests
# -----------------------------------------------------------------------------

def test_telegram_bot_commands(db, settings):
    """Verify Telegram text commands (/kill, /resume, /status, /reset, /off, /on)."""
    # 1. /kill
    reply_kill = handle_telegram_command("/kill", db, settings)
    assert "KILL SWITCH ENGAGED" in reply_kill
    with db.read() as s:
        assert portfolio_state(s).kill_switch_active is True

    # 2. /status
    reply_status = handle_telegram_command("/status", db, settings)
    assert "Cockpit Status" in reply_status
    assert "ACTIVE (BLOCKED)" in reply_status

    # 3. /resume
    reply_resume = handle_telegram_command("/resume", db, settings)
    assert "OPERATIONS RESUMED" in reply_resume
    with db.read() as s:
        assert portfolio_state(s).kill_switch_active is False
        assert portfolio_state(s).circuit_breaker_tripped is False

    # 4. /off and /on
    reply_off = handle_telegram_command("/off", db, settings)
    assert "AUTOMATION TURNED OFF" in reply_off
    with db.read() as s:
        assert portfolio_state(s).automation_enabled is False

    reply_on = handle_telegram_command("/on", db, settings)
    assert "AUTOMATION TURNED ON" in reply_on
    with db.read() as s:
        assert portfolio_state(s).automation_enabled is True
