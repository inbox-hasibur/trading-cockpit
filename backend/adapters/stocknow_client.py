"""Persistent Playwright browser session, auto-login helper, and XHR network sniffer.

Operates in two modes:
- ONSCREEN_LIVE: Headed persistent Chromium side-by-side with Cockpit.
- BACKGROUND_POLLING: Headless persistent Chromium with background polling.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

from backend.hermes.secret_guard import SecretGuard, redact_secrets

logger = logging.getLogger("hummingbird.stocknow")

DEFAULT_PROFILE_DIR = Path.home() / ".hummingbird_stocknow_profile"


def get_safe_profile_dir(custom_path: Path | str | None = None) -> Path:
    """Resolve an isolated Playwright profile directory outside OneDrive.

    OneDrive cloud sync locks LevelDB, session cookies, and SQLite databases used by Chromium,
    causing browser crashes and profile corruption. This helper guarantees an isolated,
    cloud-sync-safe location.
    """
    if custom_path is not None:
        target = Path(custom_path).expanduser().resolve()
        if "onedrive" in str(target).lower():
            logger.warning(
                "Profile path '%s' is located inside a OneDrive folder. "
                "Redirecting to default safe directory '%s' to prevent lock contention.",
                target,
                DEFAULT_PROFILE_DIR,
            )
            return DEFAULT_PROFILE_DIR
        return target
    return DEFAULT_PROFILE_DIR


def mask_phone(phone: str) -> str:
    """Mask phone number for safe display and logging without revealing identity."""
    cleaned = "".join(ch for ch in str(phone) if ch.isdigit())
    if len(cleaned) >= 6:
        return f"{cleaned[:3]}***{cleaned[-3:]}"
    if cleaned:
        return f"{cleaned[:2]}***"
    return ""


class StockNowLiveClient:
    """Persistent Playwright browser controller, auto-login assistant & XHR network sniffer."""

    def __init__(
        self,
        profile_directory: Path | str | None = None,
        ingestion_mode: str = "BACKGROUND_POLLING",
        base_url: str = "https://stocknow.com.bd",
    ):
        self.profile_directory = get_safe_profile_dir(profile_directory)
        self.ingestion_mode = ingestion_mode
        self.base_url = base_url.rstrip("/")
        self.playwright: Any | None = None
        self.context: Any | None = None
        self.page: Any | None = None
        self.state: str = "BROWSER_NOT_STARTED"
        self.last_sync_at: str | None = None
        self.last_error: str | None = None
        self.captured_endpoints: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def _handle_response(self, response: Any) -> None:
        """Passively capture JSON responses from stocknow.com.bd."""
        try:
            url = getattr(response, "url", "")
            if not url or not ("stocknow.com.bd" in url or "/api/" in url):
                return
            headers = getattr(response, "headers", {})
            content_type = headers.get("content-type", "").lower()
            if "application/json" not in content_type:
                return
            status = getattr(response, "status", 0)
            if status >= 400:
                return

            try:
                data = await response.json()
            except Exception:
                return

            parsed = urlparse(url)
            endpoint_key = parsed.path or url
            now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
            self.captured_endpoints[endpoint_key] = {
                "url": url,
                "status": status,
                "data": data,
                "content_type": content_type,
                "captured_at": now_iso,
            }
            self.last_sync_at = now_iso
        except Exception as exc:
            logger.debug("Network sniffer response parsing ignored: %s", exc)

    async def launch(self, mode: str | None = None) -> dict[str, Any]:
        """Launch or attach persistent Chromium session."""
        async with self._lock:
            if mode:
                self.ingestion_mode = mode
            if self.context is not None:
                is_closed = getattr(self.context, "is_closed", None)
                if callable(is_closed) and not is_closed():
                    return self.get_status()

            self.state = "STARTING"
            self.last_error = None
            try:
                from playwright.async_api import async_playwright
            except ImportError:
                self.state = "ERROR"
                self.last_error = "Playwright is not installed in the current Python environment."
                return self.get_status()

            try:
                self.profile_directory.mkdir(parents=True, exist_ok=True)
                is_headless = self.ingestion_mode != "ONSCREEN_LIVE"

                self.playwright = await async_playwright().start()
                self.context = await self.playwright.chromium.launch_persistent_context(
                    str(self.profile_directory),
                    headless=is_headless,
                    timezone_id="Asia/Dhaka",
                    locale="en-US",
                    viewport={"width": 1280, "height": 800},
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                    ],
                    accept_downloads=False,
                )
                pages = self.context.pages
                self.page = pages[0] if pages else await self.context.new_page()

                # Attach XHR/JSON sniffer
                self.page.on("response", lambda res: asyncio.create_task(self._handle_response(res)))

                self.state = "READY"
                self.last_sync_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
                return self.get_status()
            except Exception as exc:
                self.state = "ERROR"
                self.last_error = str(exc)
                logger.error("Failed to launch Playwright persistent browser: %s", redact_secrets(str(exc)))
                return self.get_status()

    async def close(self) -> dict[str, Any]:
        """Close browser context and stop Playwright cleanly."""
        async with self._lock:
            if self.page:
                try:
                    await self.page.close()
                except Exception:
                    pass
                self.page = None

            if self.context:
                try:
                    await self.context.close()
                except Exception:
                    pass
                self.context = None

            if self.playwright:
                try:
                    await self.playwright.stop()
                except Exception:
                    pass
                self.playwright = None

            self.state = "CLOSED"
            return self.get_status()

    async def ensure_authenticated(self, phone: str = "", password: str = "") -> dict[str, Any]:
        """Inspect authentication state on stocknow.com.bd, filling credentials if needed.

        Guarantees that credentials are never leaked in logs or error messages.
        """
        if self.context is None or self.page is None:
            launch_res = await self.launch()
            if self.state == "ERROR" or self.page is None:
                return {
                    "authenticated": False,
                    "state": self.state,
                    "reason": self.last_error or "Browser session could not be started.",
                    "phone_masked": mask_phone(phone),
                }

        masked = mask_phone(phone)
        try:
            current_url = getattr(self.page, "url", "")
            if not current_url or "stocknow.com.bd" not in current_url:
                await self.page.goto(self.base_url, timeout=20000, wait_until="domcontentloaded")

            # Check if user is already logged in
            is_logged_in = False
            for selector in [
                'a[href*="logout"]',
                'button:has-text("Logout")',
                'button:has-text("লগআউট")',
                '.user-profile',
                '.account-menu',
                'a[href*="/portfolio"]',
            ]:
                try:
                    el = await self.page.query_selector(selector)
                    if el:
                        is_logged_in = True
                        break
                except Exception:
                    pass

            if is_logged_in:
                self.state = "READY"
                return {
                    "authenticated": True,
                    "state": "READY",
                    "message": "Persistent session is authenticated.",
                    "phone_masked": masked,
                }

            # If not logged in, look for phone/password inputs
            phone_input = None
            for sel in [
                'input[type="tel"]',
                'input[name*="phone"]',
                'input[name*="mobile"]',
                'input[name*="username"]',
                'input[placeholder*="Phone"]',
                'input[placeholder*="Mobile"]',
                'input[placeholder*="01"]',
            ]:
                try:
                    phone_input = await self.page.query_selector(sel)
                    if phone_input:
                        break
                except Exception:
                    pass

            # Open login form if not open
            if not phone_input:
                for login_btn_sel in [
                    'a[href*="login"]',
                    'button:has-text("Login")',
                    'button:has-text("লগইন")',
                    'a:has-text("Login")',
                ]:
                    try:
                        login_btn = await self.page.query_selector(login_btn_sel)
                        if login_btn:
                            await login_btn.click()
                            await self.page.wait_for_timeout(1000)
                            break
                    except Exception:
                        pass

                for sel in [
                    'input[type="tel"]',
                    'input[name*="phone"]',
                    'input[name*="mobile"]',
                    'input[name*="username"]',
                    'input[placeholder*="Phone"]',
                    'input[placeholder*="Mobile"]',
                    'input[placeholder*="01"]',
                ]:
                    try:
                        phone_input = await self.page.query_selector(sel)
                        if phone_input:
                            break
                    except Exception:
                        pass

            password_input = None
            for sel in ['input[type="password"]', 'input[name*="password"]']:
                try:
                    password_input = await self.page.query_selector(sel)
                    if password_input:
                        break
                except Exception:
                    pass

            if phone and password and phone_input and password_input:
                await phone_input.fill(phone)
                await password_input.fill(password)

                for sub_sel in [
                    'button[type="submit"]',
                    'button:has-text("Login")',
                    'button:has-text("Sign In")',
                    'button:has-text("লগইন")',
                ]:
                    try:
                        sub = await self.page.query_selector(sub_sel)
                        if sub:
                            await sub.click()
                            break
                    except Exception:
                        pass

                await self.page.wait_for_timeout(2500)

                for selector in [
                    'a[href*="logout"]',
                    'button:has-text("Logout")',
                    'button:has-text("লগআউট")',
                    '.user-profile',
                    'a[href*="/portfolio"]',
                ]:
                    try:
                        el = await self.page.query_selector(selector)
                        if el:
                            self.state = "READY"
                            return {
                                "authenticated": True,
                                "state": "READY",
                                "message": "Login credentials submitted and authenticated.",
                                "phone_masked": masked,
                            }
                    except Exception:
                        pass

                self.state = "AUTH_REQUIRED"
                return {
                    "authenticated": False,
                    "state": "AUTH_REQUIRED",
                    "message": "Credentials submitted. Awaiting OTP or manual login confirmation.",
                    "phone_masked": masked,
                }

            self.state = "AUTH_REQUIRED"
            return {
                "authenticated": False,
                "state": "AUTH_REQUIRED",
                "message": "Login form detected. Operator can complete login in the persistent window.",
                "phone_masked": masked,
            }
        except Exception as exc:
            self.state = "ERROR"
            self.last_error = str(exc)
            logger.warning("ensure_authenticated encountered error: %s", redact_secrets(str(exc)))
            return {
                "authenticated": False,
                "state": "ERROR",
                "reason": redact_secrets(str(exc)),
                "phone_masked": masked,
            }

    def get_status(self) -> dict[str, Any]:
        """Return structured telemetry for live session status endpoint."""
        is_connected = (
            self.context is not None
            and not (hasattr(self.context, "is_closed") and self.context.is_closed())
        )
        return {
            "connected": is_connected,
            "state": self.state if is_connected else ("CLOSED" if self.state == "CLOSED" else "BROWSER_NOT_STARTED"),
            "mode": self.ingestion_mode,
            "profile_path": str(self.profile_directory),
            "is_onedrive_safe": "onedrive" not in str(self.profile_directory).lower(),
            "captured_endpoints_count": len(self.captured_endpoints),
            "captured_endpoints": sorted(list(self.captured_endpoints.keys())),
            "last_sync_at": self.last_sync_at,
            "last_error": self.last_error,
        }
