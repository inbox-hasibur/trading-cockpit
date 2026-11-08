"""Script to capture verification screenshots for step 10: portfolio badge, watchlist signals, footer, ledger tags."""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

ARTIFACTS_DIR = Path(r"C:\Users\inbox\.gemini\antigravity\brain\6081e00c-6aa6-4847-a2e2-cb2513473b67")

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        await page.goto("http://127.0.0.1:8000")
        await page.wait_for_selector(".page-heading", timeout=15000)
        await page.wait_for_timeout(2000)

        # 1. Capture Overview with Portfolio Header Badge
        header_el = page.locator(".page-heading").first
        await header_el.screenshot(path=str(ARTIFACTS_DIR / "step10_header_badge.png"))

        # 2. Capture Full Overview Dashboard
        await page.screenshot(path=str(ARTIFACTS_DIR / "step10_overview_full.png"))

        # 3. Capture Watchlist with Curves, Signals, and Retry links
        watchlist_el = page.locator(".watchlist-panel")
        if await watchlist_el.count() > 0:
            await watchlist_el.screenshot(path=str(ARTIFACTS_DIR / "step10_watchlist_panel.png"))

        # 4. Scroll and capture Trade Ledger table with STOCKNOW RECEIPT and PAPER FILL tags
        ledger_el = page.locator("#ledger")
        if await ledger_el.count() > 0:
            await ledger_el.scroll_into_view_if_needed()
            await page.wait_for_timeout(1000)
            await ledger_el.screenshot(path=str(ARTIFACTS_DIR / "step10_ledger_panel.png"))

        # 5. Capture Footer
        footer_el = page.locator("footer.workspace-footer")
        if await footer_el.count() > 0:
            await footer_el.screenshot(path=str(ARTIFACTS_DIR / "step10_footer.png"))

        await browser.close()
        print("Screenshots captured successfully.")

if __name__ == "__main__":
    asyncio.run(run())
