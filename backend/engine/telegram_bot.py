"""Telegram notification dispatcher and interactive command daemon.

Supports:
- Outbound alert dispatcher (Markdown formatted, silent failure on network issues).
- Interactive command processor:
  - /kill : Engages global kill switch mid-cycle.
  - /resume : Disarms kill switch and resets circuit breaker.
  - /status : Reports active portfolio, cash, positions, automation state, risk caps.
  - /off : Turns master automation OFF.
  - /on : Turns master automation ON (verifies preflight & breaker).
  - /reset : Resets tripped circuit breaker.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx

from backend.config import Settings
from backend.database import Database, KernelAuditLog, portfolio_state

logger = logging.getLogger(__name__)


async def send_telegram_alert(
    text: str,
    settings: Settings | None = None,
    parse_mode: str = "Markdown",
) -> bool:
    """Dispatches a message to the configured Telegram chat."""
    token = getattr(settings, "telegram_bot_token", None) or os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = getattr(settings, "telegram_chat_id", None) or os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.post(url, json=payload)
            return resp.status_code == 200
    except Exception as exc:
        logger.warning("Telegram notification failed: %s", exc)
        return False


def send_telegram_alert_sync(
    text: str,
    settings: Settings | None = None,
    parse_mode: str = "Markdown",
) -> bool:
    """Synchronous wrapper for sending Telegram alerts."""
    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, send_telegram_alert(text, settings, parse_mode)).result()
        return loop.run_until_complete(send_telegram_alert(text, settings, parse_mode))
    except RuntimeError:
        return asyncio.run(send_telegram_alert(text, settings, parse_mode))
    except Exception as exc:
        logger.warning("Telegram sync alert failed: %s", exc)
        return False


def handle_telegram_command(command: str, db: Database, settings: Settings) -> str:
    """Executes a text command received from Telegram operator and returns response text."""
    cmd = command.strip().lower()
    parts = cmd.split()
    base_cmd = parts[0] if parts else ""

    if base_cmd in ("/kill", "kill"):
        with db.write() as session:
            state = portfolio_state(session)
            state.kill_switch_active = True
            session.add(KernelAuditLog(
                endpoint="/telegram/kill",
                action="KILL_SWITCH_ENGAGED",
                symbol=None,
                payload={"source": "telegram"},
                result={"kill_switch_active": True},
                session_on=state.clock_date,
                trading_mode=state.trading_mode,
            ))
        return "🛑 *KILL SWITCH ENGAGED*\nAll order execution is now strictly blocked across AutoTrader and Hermes."

    if base_cmd in ("/resume", "resume"):
        with db.write() as session:
            state = portfolio_state(session)
            state.kill_switch_active = False
            state.circuit_breaker_tripped = False
            state.consecutive_failure_count = 0
            state.circuit_breaker_reason = None
            session.add(KernelAuditLog(
                endpoint="/telegram/resume",
                action="KILL_SWITCH_DISARMED",
                symbol=None,
                payload={"source": "telegram"},
                result={"kill_switch_active": False, "circuit_breaker_tripped": False},
                session_on=state.clock_date,
                trading_mode=state.trading_mode,
            ))
        return "✅ *OPERATIONS RESUMED*\nKill switch disarmed and circuit breaker reset. Automation can now operate normally."

    if base_cmd in ("/reset", "reset"):
        with db.write() as session:
            state = portfolio_state(session)
            state.circuit_breaker_tripped = False
            state.consecutive_failure_count = 0
            state.circuit_breaker_reason = None
            session.add(KernelAuditLog(
                endpoint="/telegram/reset",
                action="CIRCUIT_BREAKER_RESET",
                symbol=None,
                payload={"source": "telegram"},
                result={"circuit_breaker_tripped": False},
                session_on=state.clock_date,
                trading_mode=state.trading_mode,
            ))
        return "✅ *CIRCUIT BREAKER RESET*\nConsecutive failure count cleared. Automation can now be safely re-enabled."

    if base_cmd in ("/off", "off"):
        with db.write() as session:
            state = portfolio_state(session)
            state.automation_enabled = False
            state.paused = True
        return "⏸ *AUTOMATION TURNED OFF*\nMaster automation is now OFF (Preview mode active for manual cycles)."

    if base_cmd in ("/on", "on"):
        with db.write() as session:
            state = portfolio_state(session)
            if state.circuit_breaker_tripped:
                return (
                    f"⚠️ *CANNOT ENABLE AUTOMATION*\n"
                    f"Circuit breaker is tripped: {state.circuit_breaker_reason}\n"
                    f"Send /reset first to clear the circuit breaker."
                )
            state.automation_enabled = True
            state.paused = False
        return "▶️ *AUTOMATION TURNED ON*\nMaster automation is now ON."

    if base_cmd in ("/status", "status"):
        with db.read() as session:
            state = portfolio_state(session)
            auto_str = "🟢 ON" if state.automation_enabled else "⚪️ OFF"
            kill_str = "🚨 ACTIVE (BLOCKED)" if state.kill_switch_active else "🟢 Inactive"
            breaker_str = f"🚨 TRIPPED ({state.circuit_breaker_reason})" if state.circuit_breaker_tripped else "🟢 Normal"
            mode_str = getattr(state, "trading_mode", "LIVE_HOURS")
            ingest_str = getattr(state, "ingestion_mode", "BACKGROUND_POLLING")
            session_str = state.clock_date.isoformat() if hasattr(state.clock_date, "isoformat") else str(state.clock_date)
            return (
                f"📊 *Humming Bird Cockpit Status*\n"
                f"• *Session Date:* {session_str}\n"
                f"• *Automation:* {auto_str}\n"
                f"• *Run Mode:* {ingest_str}\n"
                f"• *Trading Mode:* {mode_str}\n"
                f"• *Kill Switch:* {kill_str}\n"
                f"• *Circuit Breaker:* {breaker_str}\n"
                f"• *Daily Budget:* ৳{float(getattr(state, 'daily_budget_bdt', 4000)):.2f}\n"
                f"• *Max Order:* ৳{float(getattr(state, 'max_order_bdt', 20000) or 20000):.2f}\n"
                f"• *Startup Health:* {getattr(state, 'startup_health_status', 'READY')}"
            )

    return (
        "🤖 *Humming Bird Bot Commands*\n"
        "• `/status` - Check current Cockpit status & caps\n"
        "• `/kill` - Emergency halt: stop all trading immediately\n"
        "• `/resume` - Disarm kill switch and reset circuit breaker\n"
        "• `/reset` - Clear tripped circuit breaker\n"
        "• `/on` - Enable master automation\n"
        "• `/off` - Disable master automation"
    )


class TelegramBotDaemon:
    """Long-polling daemon listening for operator Telegram commands."""

    def __init__(self, db: Database, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self._running = False
        self._task: asyncio.Task | None = None
        self._last_update_id = 0

    def start(self) -> None:
        token = getattr(self.settings, "telegram_bot_token", None) or os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        if not token:
            logger.debug("TelegramBotDaemon not started: No TELEGRAM_BOT_TOKEN configured.")
            return
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("TelegramBotDaemon started long polling.")

    def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
        logger.info("TelegramBotDaemon stopped.")

    async def _poll_loop(self) -> None:
        token = getattr(self.settings, "telegram_bot_token", None) or os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        allowed_chat_id = getattr(self.settings, "telegram_chat_id", None) or os.getenv("TELEGRAM_CHAT_ID", "").strip()
        url = f"https://api.telegram.org/bot{token}/getUpdates"

        while self._running:
            try:
                params: dict[str, Any] = {"timeout": 10, "offset": self._last_update_id + 1}
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(url, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        for update in data.get("result", []):
                            update_id = update.get("update_id", 0)
                            if update_id > self._last_update_id:
                                self._last_update_id = update_id

                            msg = update.get("message", {})
                            text = msg.get("text", "")
                            chat = msg.get("chat", {})
                            chat_id = str(chat.get("id", ""))

                            # If allowed_chat_id is specified, ignore unauthorized chats
                            if allowed_chat_id and chat_id != allowed_chat_id:
                                logger.warning("Ignored Telegram message from unauthorized chat_id: %s", chat_id)
                                continue

                            if text.startswith("/"):
                                reply = handle_telegram_command(text, self.db, self.settings)
                                await send_telegram_alert(reply, self.settings)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.debug("Telegram polling transient error: %s", exc)
                await asyncio.sleep(5.0)

