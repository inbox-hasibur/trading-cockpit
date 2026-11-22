"""Continuous Read-Only Passive CDP Spy Daemon for LankaBangla TradeXpress 2.0.

ZERO-BAN & PASSIVE-ONLY MANDATE:
This daemon NEVER clicks, types, submits credentials, calls page.goto(), calls page.reload(),
or sends outgoing HTTP requests to LankaBangla servers. It connects via Chrome DevTools Protocol
to the operator's already-logged-in browser, passively listens to WebSocket frames and XHR/fetch
responses, and periodically extracts read-only DOM snapshots.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from typing import Any

from backend.adapters.tradexpress.passive_feed import (
    TradeXpressPassiveFeed,
    get_global_passive_feed,
    ingest_passive_snapshot,
)
from backend.adapters.tradexpress.shadow_simulator import TradeXpressShadowSimulator
from backend.config import Settings, utc_now_iso
from backend.database import Database
from backend.secret_guard import SecretGuard

logger = logging.getLogger("hummingbird.tradexpress.cdp_daemon")

EXTRACT_READONLY_DOM_SCRIPT = """() => {
    const data = {
        title: document.title || '',
        market_watch_rows: [],
        portfolio_rows: [],
        account_summary: {},
        session_phase: 'CONTINUOUS',
        tab: 'market_watch'
    };

    try {
        // 1. Extract Market Watch Rows (Ember cell-id="dataObj.*")
        const rowElements = document.querySelectorAll(
            '#table-8-1-1-2-cached .lazy-list-container > div, [container-id="watchList"] tbody tr'
        );
        for (const r of rowElements) {
            const symEl = r.querySelector('[cell-id="dataObj.sDes"], .symbol-fore-color');
            if (!symEl) continue;
            const sym = (symEl.innerText || '').trim();
            if (!sym) continue;

            const ltpEl = r.querySelector('[cell-id="dataObj.ltp"]');
            const chgEl = r.querySelector('[cell-id="dataObj.chg"]');
            const pctChgEl = r.querySelector('[cell-id="dataObj.pctChg"]');
            const volEl = r.querySelector('[cell-id="dataObj.vol"]');
            const bbpEl = r.querySelector('[cell-id="dataObj.bbp"]');
            const bbqEl = r.querySelector('[cell-id="dataObj.bbq"]');
            const bapEl = r.querySelector('[cell-id="dataObj.bap"]');
            const baqEl = r.querySelector('[cell-id="dataObj.baq"]');
            const openEl = r.querySelector('[cell-id="dataObj.open"]');
            const highEl = r.querySelector('[cell-id="dataObj.high"]');
            const lowEl = r.querySelector('[cell-id="dataObj.low"]');
            const settEl = r.querySelector('[cell-id="dataObj.dispSettType"]');
            const catEl = r.querySelector('[cell-id="dataObj.dispSymCat"]');
            const dlttEl = r.querySelector('[cell-id="dataObj.dltt"]');
            const wk52El = r.querySelector('.wk52-up-icon, .icon-high-low-52');
            const jumpEl = r.querySelector('.icon-jump-up');

            data.market_watch_rows.push({
                sDes: sym,
                ltp: ltpEl ? (ltpEl.innerText || '').trim().replace(/,/g, '') : '',
                chg: chgEl ? (chgEl.innerText || '').trim().replace(/,/g, '') : '',
                pctChg: pctChgEl ? (pctChgEl.innerText || '').trim().replace(/%/g, '').trim() : '',
                vol: volEl ? (volEl.innerText || '').trim().replace(/,/g, '') : '',
                bbp: bbpEl ? (bbpEl.innerText || '').trim().replace(/,/g, '') : '',
                bbq: bbqEl ? (bbqEl.innerText || '').trim().replace(/,/g, '') : '',
                bap: bapEl ? (bapEl.innerText || '').trim().replace(/,/g, '') : '',
                baq: baqEl ? (baqEl.innerText || '').trim().replace(/,/g, '') : '',
                open: openEl ? (openEl.innerText || '').trim().replace(/,/g, '') : '',
                high: highEl ? (highEl.innerText || '').trim().replace(/,/g, '') : '',
                low: lowEl ? (lowEl.innerText || '').trim().replace(/,/g, '') : '',
                dispSettType: settEl ? (settEl.innerText || '').trim() : 'PUBLIC',
                dispSymCat: catEl ? (catEl.innerText || '').trim() : 'A',
                dltt: dlttEl ? (dlttEl.innerText || '').trim() : '',
                wk52: !!wk52El,
                jumpUp: !!jumpEl
            });
        }

        // 2. Extract Portfolio Rows
        const portElements = document.querySelectorAll(
            '#portfolioContainer-8-1-2-3 tbody tr, [container-tab-id="portfolio"] tbody tr'
        );
        for (const pr of portElements) {
            const symEl = pr.querySelector('[cell-id="symbolInfo.dSym"]');
            if (!symEl) continue;
            const sym = (symEl.innerText || '').trim();
            if (!sym) continue;

            const totalEl = pr.querySelector('[cell-id="profLossQty"]');
            const availEl = pr.querySelector('[cell-id="avaiQtyDSE"]');
            const penEl = pr.querySelector('[cell-id="penHolding"]');
            const avgCostEl = pr.querySelector('[cell-id="avgCst"]');
            const ltpEl = pr.querySelector('[cell-id="ltp"]');

            data.portfolio_rows.push({
                symbol: sym,
                total_qty: totalEl ? (totalEl.innerText || '').trim().replace(/,/g, '') : '',
                available_qty: availEl ? (availEl.innerText || '').trim().replace(/,/g, '') : '',
                pending_qty: penEl ? (penEl.innerText || '').trim().replace(/,/g, '') : '',
                average_cost: avgCostEl ? (avgCostEl.innerText || '').trim().replace(/,/g, '') : '',
                market_price: ltpEl ? (ltpEl.innerText || '').trim().replace(/,/g, '') : ''
            });
        }

        // 3. Extract Account Summary Telemetry
        const allText = document.body ? document.body.innerText : '';
        const parseMoneyPattern = (label) => {
            const regex = new RegExp(label + '[:\\\\s\\\\t]+([0-9,]+(?:\\\\.[0-9]{1,2})?)', 'i');
            const m = allText.match(regex);
            return m ? parseFloat(m[1].replace(/,/g, '')) : 0.0;
        };

        const cash = parseMoneyPattern('(?:Cash Balance|Available Cash)');
        const buyingPower = parseMoneyPattern('(?:Buying Power|Purchasing Power)');
        const unsettled = parseMoneyPattern('(?:Unsettled Sales|Unsettled Amount)');
        const blocked = parseMoneyPattern('(?:Blocked Amount|Blocked Cash)');

        if (cash > 0 || buyingPower > 0 || unsettled > 0) {
            data.account_summary = {
                cash_balance: cash,
                available_cash_balance: cash,
                buying_power: buyingPower > 0 ? buyingPower : cash + unsettled,
                unsettled_sales: unsettled,
                blocked_amount: blocked
            };
        }

        // Detect current visible tab
        const activeTabEl = document.querySelector('[role="tab"].active, .nav-tabs .active a, [aria-selected="true"]');
        if (activeTabEl) {
            const tabTxt = (activeTabEl.innerText || '').toLowerCase();
            if (tabTxt.includes('order')) data.tab = 'order_status';
            else if (tabTxt.includes('port')) data.tab = 'portfolio';
            else if (tabTxt.includes('account')) data.tab = 'account_summary';
            else if (tabTxt.includes('watch') || tabTxt.includes('market')) data.tab = 'market_watch';
        }
    } catch (err) {
        data.error = String(err);
    }

    return data;
};"""


class TradeXpressPassiveDaemon:
    """Continuous read-only CDP spy daemon observing TradeXpress 2.0 via DevTools Protocol."""

    def __init__(
        self,
        database: Database,
        settings: Settings,
        broadcaster: Any = None,
        feed: TradeXpressPassiveFeed | None = None,
    ) -> None:
        self.database = database
        self.settings = settings
        self.broadcaster = broadcaster
        self.feed = feed or get_global_passive_feed(database)

        # Operational telemetry
        self.running: bool = False
        self.cdp_connected: bool = False
        self.cdp_url: str = "http://127.0.0.1:9222"
        self.attached_url: str = ""
        self.active_tab: str = ""
        self.dom_syncs_count: int = 0
        self.ws_frames_count: int = 0
        self.xhr_responses_count: int = 0
        self.last_sync_utc: str = ""
        self.last_error: str = ""

        # Internal task & Playwright handle references
        self._task: asyncio.Task | None = None
        self._last_payload_hash: str = ""
        self._playwright_instance: Any | None = None
        self._browser_instance: Any | None = None

    def get_status(self) -> dict[str, Any]:
        """Returns comprehensive telemetry dictionary for UI and API clients."""
        return {
            "running": self.running,
            "cdp_connected": self.cdp_connected,
            "cdp_url": SecretGuard.redact_secrets(self.cdp_url),
            "attached_url": SecretGuard.redact_secrets(self.attached_url),
            "active_tab": self.active_tab,
            "dom_syncs_count": self.dom_syncs_count,
            "ws_frames_count": self.ws_frames_count,
            "xhr_responses_count": self.xhr_responses_count,
            "last_sync_utc": self.last_sync_utc,
            "last_error": self.last_error,
        }

    async def start(self, cdp_url: str = "http://127.0.0.1:9222") -> dict[str, Any]:
        """Idempotently starts the continuous passive spy background task."""
        if self.running and self._task and not self._task.done():
            logger.info("TradeXpress passive daemon is already running on %s", self.cdp_url)
            return self.get_status()

        self.cdp_url = cdp_url.strip() or "http://127.0.0.1:9222"
        self.running = True
        self.last_error = ""
        self._task = asyncio.create_task(self._run_loop(self.cdp_url))
        logger.info("Started TradeXpress passive daemon task against %s", self.cdp_url)
        return self.get_status()

    async def stop(self) -> dict[str, Any]:
        """Idempotently stops background spy loop and safely disconnects CDP client."""
        logger.info("Stopping TradeXpress passive daemon...")
        self.running = False

        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):
                pass
            self._task = None

        if self._browser_instance is not None:
            try:
                # In Playwright, browser.close() on a connect_over_cdp connection
                # only closes the DevTools WebSocket, leaving the user's browser intact.
                await self._browser_instance.close()
            except Exception as exc:
                logger.debug("Browser client detach notice: %s", exc)
            self._browser_instance = None

        if self._playwright_instance is not None:
            try:
                await self._playwright_instance.stop()
            except Exception as exc:
                logger.debug("Playwright stop notice: %s", exc)
            self._playwright_instance = None

        self.cdp_connected = False
        self.feed.set_cdp_connected(False)
        self.attached_url = ""
        self.active_tab = ""
        logger.info("TradeXpress passive daemon stopped successfully.")
        return self.get_status()

    async def _run_loop(self, cdp_url: str) -> None:
        """Main resilient observation loop. Auto-reconnects on browser restarts."""
        from playwright.async_api import async_playwright

        while self.running:
            try:
                self._playwright_instance = await async_playwright().start()
                try:
                    self._browser_instance = await self._playwright_instance.chromium.connect_over_cdp(
                        cdp_url, timeout=5000
                    )
                except Exception as conn_err:
                    self.cdp_connected = False
                    self.feed.set_cdp_connected(False)
                    self.last_error = f"Cannot connect to CDP at {cdp_url}: {conn_err}"
                    logger.debug("CDP connection failed: %s (retrying in 5s)", conn_err)
                    if self._playwright_instance:
                        await self._playwright_instance.stop()
                        self._playwright_instance = None
                    await asyncio.sleep(5.0)
                    continue

                self.cdp_connected = True
                self.feed.set_cdp_connected(True)
                self.last_error = ""

                # Locate LankaBangla tab
                target_page = None
                for context in self._browser_instance.contexts:
                    for page in context.pages:
                        url = page.url.lower()
                        if "itrade.lbsbd.com" in url or "ibroker.lbsbd.com" in url:
                            target_page = page
                            break
                    if target_page:
                        break

                if not target_page:
                    self.last_error = "Connected to CDP, but no active 'itrade.lbsbd.com' tab found."
                    self.attached_url = ""
                    self.active_tab = ""
                    logger.debug(self.last_error)
                    await asyncio.sleep(3.0)
                    if self._browser_instance:
                        await self._browser_instance.close()
                        self._browser_instance = None
                    if self._playwright_instance:
                        await self._playwright_instance.stop()
                        self._playwright_instance = None
                    continue

                self.attached_url = target_page.url
                try:
                    self.active_tab = await target_page.title()
                except Exception:
                    self.active_tab = "LankaBangla TradeXpress"

                logger.info(
                    "Passive CDP attached to TradeXpress tab: %s",
                    SecretGuard.redact_secrets(self.attached_url),
                )

                # Attach passive WebSocket sniffer
                def on_web_socket(ws: Any) -> None:
                    def on_frame_received(_payload: Any) -> None:
                        self.ws_frames_count += 1
                        self.feed.update_tab_timestamp("market_watch")

                    ws.on("framereceived", on_frame_received)

                target_page.on("websocket", on_web_socket)

                # Attach passive XHR/Fetch response sniffer
                def on_response(res: Any) -> None:
                    url = res.url.lower()
                    if "/web/price" in url or "/web/chart" in url or "/web/portfolio" in url:
                        self.xhr_responses_count += 1

                target_page.on("response", on_response)

                # Passive periodic extraction loop
                while self.running:
                    if target_page.is_closed():
                        logger.warning("Observed TradeXpress tab was closed by operator.")
                        break

                    try:
                        extracted = await target_page.evaluate(EXTRACT_READONLY_DOM_SCRIPT)
                    except Exception as eval_err:
                        self.last_error = f"DOM evaluate error: {eval_err}"
                        logger.debug(self.last_error)
                        await asyncio.sleep(2.0)
                        continue

                    # Ingest if payload content changed
                    h = hashlib.sha256(json.dumps(extracted, sort_keys=True).encode()).hexdigest()
                    if h != self._last_payload_hash:
                        self._last_payload_hash = h
                        self.dom_syncs_count += 1
                        self.last_sync_utc = utc_now_iso()

                        extracted["cdp_connected"] = True
                        ingest_passive_snapshot(
                            self.database,
                            extracted,
                            feed=self.feed,
                            broadcaster=self.broadcaster,
                        )

                        # Reconcile any resting queued limit orders against new depth
                        phase = extracted.get("session_phase", "CONTINUOUS")
                        with self.database.write() as session:
                            simulator = TradeXpressShadowSimulator(
                                self.database, self.settings, feed=self.feed
                            )
                            simulator.reconcile_queued_orders(
                                session, self.feed.get_all_quotes(), session_phase=phase
                            )

                    await asyncio.sleep(2.5)

            except asyncio.CancelledError:
                break
            except Exception as loop_err:
                self.cdp_connected = False
                self.feed.set_cdp_connected(False)
                self.last_error = f"Daemon loop error: {loop_err}"
                logger.warning("Passive daemon loop caught error: %s (restarting loop in 5s)", loop_err)
                await asyncio.sleep(5.0)
            finally:
                if self._browser_instance:
                    try:
                        await self._browser_instance.close()
                    except Exception:
                        pass
                    self._browser_instance = None
                if self._playwright_instance:
                    try:
                        await self._playwright_instance.stop()
                    except Exception:
                        pass
                    self._playwright_instance = None


_GLOBAL_PASSIVE_DAEMON: TradeXpressPassiveDaemon | None = None


def get_global_passive_daemon(
    database: Database,
    settings: Settings,
    broadcaster: Any = None,
) -> TradeXpressPassiveDaemon:
    """Singleton getter for the global TradeXpress passive CDP spy daemon."""
    global _GLOBAL_PASSIVE_DAEMON
    if _GLOBAL_PASSIVE_DAEMON is None:
        _GLOBAL_PASSIVE_DAEMON = TradeXpressPassiveDaemon(
            database=database,
            settings=settings,
            broadcaster=broadcaster,
        )
    elif database and not _GLOBAL_PASSIVE_DAEMON.database:
        _GLOBAL_PASSIVE_DAEMON.database = database
    return _GLOBAL_PASSIVE_DAEMON
