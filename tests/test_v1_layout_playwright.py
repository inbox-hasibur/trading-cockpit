"""Playwright layout and visual verification for TradeXpress Cockpit V1.

Asserts 1440x900 bounding boxes, 2-column grid layout, zero 64px crush,
interactive Hermes sidebar dock, tab switching, and screenshots.
"""

from decimal import Decimal
from pathlib import Path
import socket
import threading
import time
import urllib.request
import pytest
from playwright.sync_api import sync_playwright

from backend.config import Settings
from backend.database import Database
from backend.main import create_app
from backend.seed import seed_demo


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def cockpit_server(tmp_path_factory):
    """Ensure a live cockpit server is available, either existing or ephemeral."""
    try:
        urllib.request.urlopen("http://127.0.0.1:8000/api/portfolio", timeout=0.8)
        yield "http://127.0.0.1:8000"
        return
    except Exception:
        pass

    import uvicorn
    tmp_dir = tmp_path_factory.mktemp("playwright_db")
    db_file = tmp_dir / "test_cockpit_playwright.db"
    settings = Settings(
        database_url=f"sqlite:///{db_file.resolve()}",
        initial_capital=Decimal("100000.00"),
    )
    db = Database(settings.database_url)
    db.create_schema()
    with db.write() as session:
        seed_demo(session, settings)

    app = create_app(settings)
    port = find_free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    time.sleep(1.2)
    base_url = f"http://127.0.0.1:{port}"
    yield base_url
    server.should_exit = True


def test_tradexpress_v1_layout_and_interactions(cockpit_server):
    """Full visual and bounding box verification of TradeXpress 2.0 3-pane layout in Playwright."""
    base_url = cockpit_server
    js_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        page.on("pageerror", lambda err: js_errors.append(f"PageError: {err}"))
        page.on("console", lambda msg: js_errors.append(f"ConsoleError: {msg.text}") if msg.type == "error" else None)

        page.goto(f"{base_url}/", wait_until="networkidle")
        page.wait_for_selector("#tx-trade-workspace", state="visible", timeout=6000)
        page.wait_for_selector("#watchlist-body tr[data-symbol]", state="visible", timeout=8000)
        time.sleep(0.3)

        # 1. Bounding Boxes in Dark Theme
        workspace_box = page.locator(".tx-workspace").bounding_box()
        sidebar_box = page.locator("#hermes-sidebar").bounding_box()
        mw_box = page.locator("#tx-market-watch").bounding_box()
        ticket_box = page.locator("#tx-order-ticket").bounding_box()
        monitor_box = page.locator("#tx-monitor-panel").bounding_box()

        assert workspace_box is not None and sidebar_box is not None
        assert mw_box is not None and ticket_box is not None and monitor_box is not None

        # .workspace: width >= 900px, left <= 5px (zero 64px crush)
        assert workspace_box["width"] >= 900, f"Workspace width too small: {workspace_box['width']}"
        assert workspace_box["x"] <= 5, f"Workspace left offset too large: {workspace_box['x']}"

        # #hermes-sidebar: width 300..440px, left >= 900px
        assert 300 <= sidebar_box["width"] <= 440, f"Sidebar width out of range: {sidebar_box['width']}"
        assert sidebar_box["x"] >= 900, f"Sidebar x offset too small: {sidebar_box['x']}"

        # 3-Pane heights & widths
        assert mw_box["width"] >= 850, f"Market watch width too small: {mw_box['width']}"
        assert mw_box["height"] >= 250, f"Market watch height too small: {mw_box['height']}"

        assert ticket_box["width"] >= 400, f"Order ticket width too small: {ticket_box['width']}"
        assert ticket_box["height"] >= 220, f"Order ticket height too small: {ticket_box['height']}"

        assert monitor_box["width"] >= 400, f"Monitor panel width too small: {monitor_box['width']}"
        assert monitor_box["height"] >= 220, f"Monitor panel height too small: {monitor_box['height']}"

        # Relative position: ticket is strictly to the left of monitor panel
        ticket_right = ticket_box["x"] + ticket_box["width"]
        assert ticket_right <= monitor_box["x"] + 12, f"Ticket ({ticket_right}) overlaps monitor ({monitor_box['x']})"

        # Watchlist table rows and sparklines
        rows = page.locator("#watchlist-body tr")
        assert rows.count() >= 1, "No market watch rows rendered"
        sparklines = page.locator("#watchlist-body svg")
        assert sparklines.count() >= 1, "No inline sparkline SVGs rendered"

        # Capture Dark Mode Screenshot
        Path("scratch").mkdir(exist_ok=True)
        page.screenshot(path="scratch/verify_v1_dark.png")

        # 2. Interactive Hermes Sidebar Tabs
        page.click("#tab-hermes-conversations")
        page.wait_for_selector("#pane-hermes-conversations", state="visible")
        assert page.locator("#pane-hermes-chat").is_hidden()

        page.click("#tab-hermes-changes")
        page.wait_for_selector("#pane-hermes-changes", state="visible")

        page.click("#tab-hermes-skills")
        page.wait_for_selector("#pane-hermes-skills", state="visible")

        page.click("#tab-hermes-chat")
        page.wait_for_selector("#pane-hermes-chat", state="visible")

        # 3. Collapse & Restore Hermes Sidebar
        page.click("#hermes-collapse-btn")
        time.sleep(0.3)
        expanded_ws = page.locator(".tx-workspace").bounding_box()
        assert expanded_ws["width"] >= 1400, f"Workspace did not expand when sidebar collapsed: {expanded_ws['width']}"

        page.click("#floating-hermes-open")
        time.sleep(0.3)
        restored_sidebar = page.locator("#hermes-sidebar").bounding_box()
        assert restored_sidebar["width"] >= 300, f"Sidebar failed to restore: {restored_sidebar['width']}"

        # 4. Top Navigation View Switching (zero overlap)
        views_to_test = [
            ("tx-nav-heatmap", "view-heatmap-wrap"),
            ("tx-nav-rules", "view-rules-wrap"),
            ("tx-nav-ledger", "view-ledger-wrap"),
            ("tx-nav-learning", "tx-learning-view"),
            ("tx-nav-settings", "view-settings"),
            ("tx-nav-trade", "view-dashboard"),
        ]
        for nav_id, wrap_id in views_to_test:
            page.click(f"#{nav_id}")
            time.sleep(0.25)
            assert page.locator(f"#{wrap_id}").is_visible(), f"View #{wrap_id} not visible after clicking #{nav_id}"

        # 5. Order Ticket Row Selection & Step-2 Confirmation Modal
        first_row = page.locator("#watchlist-body tr").first
        first_row.click()
        time.sleep(0.3)
        sym_val = page.locator("#tx-ticket-sym").inner_text()
        assert sym_val != "", "Order ticket symbol was not populated on row click"

        page.click("#tx-order-submit-btn")
        time.sleep(0.4)
        modal_open = page.evaluate("() => document.getElementById('tx-confirm-order-modal')?.open || false")
        assert modal_open, "Confirm Order modal did not open"

        page.click("#tx-confirm-cancel-btn")
        time.sleep(0.3)
        modal_closed = page.evaluate("() => !(document.getElementById('tx-confirm-order-modal')?.open || false)")
        assert modal_closed, "Confirm Order modal did not close on cancel"

        # 6. Light Theme Switcher & Screenshot
        page.click("#theme-toggle-btn")
        time.sleep(0.35)
        page.screenshot(path="scratch/verify_v1_light.png")

        # 7. Zero JS Console Errors
        assert len(js_errors) == 0, f"Encountered uncaught JS errors: {js_errors}"

        browser.close()
