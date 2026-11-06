"""DSE Market-Hours Auto-Scheduler (10:00 AM – 2:30 PM Sun–Thu).

Periodic async background loop that monitors DSE market trading windows,
pulls live quotes via StockNow, evaluates AutoTrader cycles, and broadcasts SSE updates.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, time
import logging
from typing import Any

from backend.adapters.stocknow_client import StockNowLiveClient
from backend.adapters.stocknow_market_sync import (
    extract_quotes_from_stocknow,
    sync_live_market_to_db,
)
from backend.config import DHAKA, Settings
from backend.database import Database, portfolio_state
from backend.engine.auto_trader import AutoTrader
from backend.engine.t2_ledger import TradingCalendar
from backend.portfolio import build_snapshot

logger = logging.getLogger("hummingbird.scheduler")

_active_scheduler: DSEMarketScheduler | None = None


def get_active_scheduler() -> DSEMarketScheduler | None:
    """Returns the globally active scheduler singleton instance if registered."""
    return _active_scheduler


def is_dse_market_open(
    now_dhaka: datetime | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    """Evaluates whether DSE is currently open for trading in Asia/Dhaka time."""
    cfg = settings or Settings()
    if now_dhaka is None:
        now_dhaka = datetime.now(DHAKA)
    elif now_dhaka.tzinfo is None:
        now_dhaka = now_dhaka.replace(tzinfo=DHAKA)
    else:
        now_dhaka = now_dhaka.astimezone(DHAKA)

    calendar = TradingCalendar(holidays=cfg.holidays, anchor=cfg.bucket_anchor)
    cur_date = now_dhaka.date()
    cur_time = now_dhaka.time()

    is_trading_day = calendar.is_session(cur_date)
    is_time_window = cfg.market_open <= cur_time <= cfg.market_close
    is_open = is_trading_day and is_time_window

    if not is_trading_day:
        weekday_name = cur_date.strftime("%A")
        if cur_date in cfg.holidays:
            reason = f"DSE holiday ({cur_date.isoformat()})"
        elif cur_date.weekday() in {4, 5}:
            reason = f"Weekend ({weekday_name})"
        else:
            reason = f"Non-trading day ({weekday_name})"
    elif cur_time < cfg.market_open:
        reason = f"Pre-market (opens at {cfg.market_open.strftime('%H:%M')})"
    elif cur_time > cfg.market_close:
        reason = f"Post-market (closed at {cfg.market_close.strftime('%H:%M')})"
    else:
        reason = "Market is open for live trading"

    window_str = f"{cfg.market_open.strftime('%H:%M')}-{cfg.market_close.strftime('%H:%M')}"
    return {
        "is_open": is_open,
        "is_trading_day": is_trading_day,
        "dhaka_time": now_dhaka.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "window": window_str,
        "reason": reason,
    }


class DSEMarketScheduler:
    """Async background scheduler enforcing DSE market hours and periodic trading cycles."""

    def __init__(
        self,
        database: Database,
        settings: Settings,
        broadcaster: Any = None,
        client: StockNowLiveClient | None = None,
        trader: AutoTrader | None = None,
    ):
        global _active_scheduler
        self.database = database
        self.settings = settings
        self.broadcaster = broadcaster
        self.client = client
        self.trader = trader or AutoTrader(database, settings)
        self.running: bool = False
        self._task: asyncio.Task | None = None
        self.tick_count: int = 0
        self.last_tick_at: str | None = None
        self.last_skip_reason: str | None = None
        self.last_error: str | None = None
        _active_scheduler = self
        if client and not hasattr(client, "scheduler"):
            client.scheduler = self  # type: ignore[attr-defined]

    def get_status(self) -> dict[str, Any]:
        """Returns scheduler operational status, telemetry, and DSE market gate."""
        with self.database.read() as session:
            state = portfolio_state(session)
            auto_enabled = getattr(state, "automation_enabled", True)
            paused = getattr(state, "paused", False)
            poll_sec = getattr(state, "polling_interval_sec", 120)

        gate = is_dse_market_open(settings=self.settings)
        return {
            "running": self.running,
            "tick_count": self.tick_count,
            "last_tick_at": self.last_tick_at,
            "last_skip_reason": self.last_skip_reason,
            "last_error": self.last_error,
            "polling_interval_sec": poll_sec,
            "automation_enabled": auto_enabled,
            "paused": paused,
            "market": gate,
        }

    async def run_scheduled_tick(self, force: bool = False) -> dict[str, Any]:
        """Executes a single scheduler tick, enforcing gate & automation state unless force=True."""
        with self.database.read() as session:
            state = portfolio_state(session)
            auto_enabled = getattr(state, "automation_enabled", True)
            paused = getattr(state, "paused", False)

        gate = is_dse_market_open(settings=self.settings)
        if not force:
            if not gate["is_open"]:
                self.last_skip_reason = f"Market closed: {gate['reason']}"
                return {"status": "SKIPPED", "reason": self.last_skip_reason, "market": gate}
            if not auto_enabled:
                self.last_skip_reason = "Automation disabled by operator"
                return {"status": "SKIPPED", "reason": self.last_skip_reason, "market": gate}
            if paused:
                self.last_skip_reason = "Engine paused by operator"
                return {"status": "SKIPPED", "reason": self.last_skip_reason, "market": gate}

        synced_count = 0
        if self.client:
            try:
                quotes = await extract_quotes_from_stocknow(self.client)
                if quotes:
                    sync_res = sync_live_market_to_db(self.database, quotes)
                    synced_count = sync_res.get("synced_count", 0)
            except Exception as exc:
                logger.warning("Scheduler market quote sync error: %s", exc)

        cycle_res = None
        try:
            cycle_res = self.trader.run_cycle()
            if self.broadcaster:
                self.broadcaster.publish("cycle", cycle_res)
        except Exception as exc:
            self.last_error = str(exc)
            logger.info("Scheduler cycle execution notice: %s", exc)

        # Hermes OS Autonomous Cron Jobs evaluation
        cron_results = []
        try:
            from backend.hermes_os.cron_manager import CronManager
            with self.database.write() as session:
                cron_results = CronManager.check_and_execute_due_jobs(
                    session=session,
                    settings=self.settings,
                    client=self.stocknow_client,
                )
                if cron_results:
                    logger.info("Hermes OS executed %d scheduled cron job(s) in tick.", len(cron_results))
        except Exception as exc:
            logger.debug("Hermes OS cron scheduler check notice: %s", exc)

        self.tick_count += 1
        now_dse = datetime.now(DHAKA)
        self.last_tick_at = now_dse.strftime("%Y-%m-%d %H:%M:%S %Z")
        self.last_skip_reason = None

        if self.broadcaster:
            try:
                snap = build_snapshot(self.database, self.settings)
                self.broadcaster.publish("snapshot", snap)
            except Exception as exc:
                logger.debug("Broadcaster snapshot ignored: %s", exc)

        return {
            "status": "EXECUTED",
            "tick_count": self.tick_count,
            "last_tick_at": self.last_tick_at,
            "synced_quotes": synced_count,
            "cycle_result": cycle_res,
            "market": gate,
        }

    def run_scheduled_tick_sync(self, force: bool = False, session: Any = None) -> dict[str, Any]:
        """Synchronous version of tick execution (e.g. for Hermes chat turn)."""
        if session is not None:
            state = portfolio_state(session)
            auto_enabled = getattr(state, "automation_enabled", True)
            paused = getattr(state, "paused", False)
        else:
            with self.database.read() as db_session:
                state = portfolio_state(db_session)
                auto_enabled = getattr(state, "automation_enabled", True)
                paused = getattr(state, "paused", False)

        gate = is_dse_market_open(settings=self.settings)
        if not force:
            if not gate["is_open"]:
                self.last_skip_reason = f"Market closed: {gate['reason']}"
                return {"status": "SKIPPED", "reason": self.last_skip_reason, "market": gate}
            if not auto_enabled:
                self.last_skip_reason = "Automation disabled by operator"
                return {"status": "SKIPPED", "reason": self.last_skip_reason, "market": gate}
            if paused:
                self.last_skip_reason = "Engine paused by operator"
                return {"status": "SKIPPED", "reason": self.last_skip_reason, "market": gate}

        cycle_res = None
        try:
            cycle_res = self.trader.run_cycle(session=session)
            if self.broadcaster:
                self.broadcaster.publish("cycle", cycle_res)
        except Exception as exc:
            self.last_error = str(exc)
            logger.info("Scheduler cycle execution notice: %s", exc)

        # Hermes OS Autonomous Cron Jobs evaluation
        cron_results = []
        try:
            from backend.hermes_os.cron_manager import CronManager
            with self.database.write() as session:
                cron_results = CronManager.check_and_execute_due_jobs(
                    session=session,
                    settings=self.settings,
                    client=self.stocknow_client,
                )
                if cron_results:
                    logger.info("Hermes OS executed %d scheduled cron job(s) in tick.", len(cron_results))
        except Exception as exc:
            logger.debug("Hermes OS cron scheduler check notice: %s", exc)

        self.tick_count += 1
        now_dse = datetime.now(DHAKA)
        self.last_tick_at = now_dse.strftime("%Y-%m-%d %H:%M:%S %Z")
        self.last_skip_reason = None

        if self.broadcaster and session is None:
            try:
                snap = build_snapshot(self.database, self.settings)
                self.broadcaster.publish("snapshot", snap)
            except Exception as exc:
                logger.debug("Broadcaster snapshot ignored: %s", exc)

        return {
            "status": "EXECUTED",
            "tick_count": self.tick_count,
            "last_tick_at": self.last_tick_at,
            "synced_quotes": 0,
            "cycle_result": cycle_res,
            "market": gate,
        }

    def start(self) -> dict[str, Any]:
        """Starts background periodic polling loop."""
        if self.running:
            return {"status": "ALREADY_RUNNING", **self.get_status()}
        self.running = True
        try:
            loop = asyncio.get_running_loop()
            self._task = loop.create_task(self._loop())
        except RuntimeError:
            pass
        return {"status": "STARTED", **self.get_status()}

    def stop_sync(self) -> dict[str, Any]:
        """Stops background periodic polling loop gracefully (sync)."""
        if not self.running and not self._task:
            return {"status": "NOT_RUNNING", **self.get_status()}
        self.running = False
        if self._task and not self._task.done():
            self._task.cancel()
            self._task = None
        return {"status": "STOPPED", **self.get_status()}

    async def stop(self) -> dict[str, Any]:
        """Stops background periodic polling loop gracefully."""
        return self.stop_sync()

    async def _loop(self) -> None:
        """Background periodic execution loop respecting configured polling interval."""
        logger.info("DSEMarketScheduler loop started.")
        while self.running:
            try:
                with self.database.read() as session:
                    state = portfolio_state(session)
                    poll_sec = getattr(state, "polling_interval_sec", 120) or 120
                    interval = max(5, min(poll_sec, 3600))
                await self.run_scheduled_tick(force=False)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                self.last_error = str(exc)
                logger.error("DSEMarketScheduler tick error: %s", exc)

            try:
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
        logger.info("DSEMarketScheduler loop stopped.")
