"""No invented StockNow endpoints or selectors, and no silent live-to-demo fallback."""

from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path

from backend.database import CompanyProfile
from backend.engine.money import ZERO, decimal


class QuoteError(ValueError):
    pass


class LiveIntegrationNotImplemented(RuntimeError):
    pass


@dataclass(frozen=True)
class DemoQuote:
    symbol: str
    unit_price: Decimal
    history: list[dict[str, str]]
    as_of: date
    source: str = "DEMO_PAPER"


class StockNowAdapter:
    """Sprint 1's explicitly synthetic data/paper-fill boundary."""

    def __init__(self, mode: str = "DEMO"):
        if mode != "DEMO":
            raise LiveIntegrationNotImplemented("StockNow connection is a gated Sprint 2 feature.")

    def quote(self, company: CompanyProfile, as_of: date) -> DemoQuote:
        if not (company.source.startswith("DEMO_") or company.source == "STOCKNOW_LIVE"):
            raise QuoteError("This adapter only accepts explicitly synthetic data or verified StockNow live quotes.")
        if company.quote_on != as_of:
            raise QuoteError("Quote date does not match the current demo session.")
        if not company.last_price.is_finite() or company.last_price <= ZERO:
            raise QuoteError("Quote is nonpositive or nonfinite.")
        try:
            last = company.price_history[-1]
            if last["date"] != as_of.isoformat() or decimal(last["close"]) != company.last_price:
                raise QuoteError("Quote and final history observation do not reconcile.")
        except (IndexError, KeyError, TypeError, ArithmeticError) as exc:
            raise QuoteError("Quote history is invalid.") from exc
        quote_source = "STOCKNOW_LIVE" if company.source == "STOCKNOW_LIVE" else "DEMO_PAPER"
        return DemoQuote(company.symbol, company.last_price, company.price_history, as_of, source=quote_source)

    def paper_fill(self, quote: DemoQuote, quantity: int) -> Decimal:
        if quantity <= 0 or quote.source not in ("DEMO_PAPER", "STOCKNOW_LIVE"):
            raise ValueError("Only positive paper fills are allowed.")
        return quote.unit_price  # No simulated liquidity/slippage: disclosed in UI/docs.

    async def read_virtual_portfolio(self):
        raise LiveIntegrationNotImplemented("StockNow live DOM/XHR reads are not implemented.")

    async def execute_order(self, *_args, **_kwargs):
        raise LiveIntegrationNotImplemented("No connected virtual or real orders in Sprint 1.")

    def get_adapter_status(
        self,
        ingestion_mode: str = "BACKGROUND_POLLING",
        polling_interval_sec: int = 120,
        live_client: Any | None = None,
    ) -> dict:
        from backend.adapters.stocknow_client import get_safe_profile_dir

        client_status = live_client.get_status() if live_client and hasattr(live_client, "get_status") else {}
        is_connected = client_status.get("connected", False)
        session_state = client_status.get("state", "BROWSER_NOT_STARTED")
        profile_path = client_status.get("profile_path", str(get_safe_profile_dir()))
        captured_endpoints_count = client_status.get("captured_endpoints_count", 0)
        last_sync_at = client_status.get("last_sync_at")

        return {
            "mode": ingestion_mode,
            "polling_interval_sec": polling_interval_sec,
            "connected": is_connected,
            "cdp_attached": is_connected and ingestion_mode == "ONSCREEN_LIVE",
            "ready": True,
            "source": "DEMO_SYNTHETIC" if not is_connected else "STOCKNOW_LIVE",
            "session_state": session_state,
            "profile_path": profile_path,
            "captured_endpoints_count": captured_endpoints_count,
            "last_sync_at": last_sync_at,
            "bound_portfolio_name": client_status.get("bound_portfolio_name"),
            "bound_portfolio_id": client_status.get("bound_portfolio_id"),
            "last_portfolio_sync_at": client_status.get("last_portfolio_sync_at"),
            "description": (
                f"Method A: Periodic background polling every {polling_interval_sec}s."
                if ingestion_mode == "BACKGROUND_POLLING"
                else "Method B: Onscreen Live Mode (Playwright Headed CDP Attached)."
            ),
        }


class StockNowBrowserSession:
    """Opt-in persistent browser foundation, not a login or order implementation.

    Nothing in the web app calls this. It opens a blank browser only when a
    developer explicitly enters the context, after installing Chromium. Sprint 2
    must inspect the actual authorized account and implement reconciliation.
    """

    def __init__(self, profile_directory: Path):
        self.profile_directory = profile_directory

    @asynccontextmanager
    async def open(self):
        from playwright.async_api import async_playwright

        self.profile_directory.mkdir(parents=True, exist_ok=True)
        async with async_playwright() as playwright:
            context = await playwright.chromium.launch_persistent_context(
                str(self.profile_directory),
                headless=False,
                timezone_id="Asia/Dhaka",
                accept_downloads=False,
            )
            try:
                yield context
            finally:
                await context.close()
