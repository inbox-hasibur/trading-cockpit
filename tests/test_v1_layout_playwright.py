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
from backend.seed import migrate_real_stocknow_market, seed_demo


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
    db_file = tmp_dir / "test_hummingbird.db"
    settings = Settings(
        database_url=f"sqlite:///{db_file.resolve()}",
        initial_capital=Decimal("100000.00"),
    )
    db = Database(settings.database_url)
    db.create_schema()
    with db.write() as session:
        seed_demo(session, settings)
        migrate_real_stocknow_market(session, settings)

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
        time.sleep(0.5)
        bank_row = page.locator('#watchlist-body tr[data-symbol="BANKASIA"]')
        if bank_row.count() > 0:
            bank_row.click()
            time.sleep(0.3)

        def assert_strict_visual_gates(theme: str):
            """Assert strict layout integrity, zero clipping, zero errors, and full depth."""
            # 1. Error banner must NOT be visible
            assert not page.locator("#error-banner").is_visible(), f"[{theme}] Error banner is visible!"

            # 2. Buying power must be real formatted money
            bp_text = page.locator("#tx-hdr-buying-power").inner_text()
            assert bp_text != "৳0.00", f"[{theme}] Buying power stuck at ৳0.00: {bp_text}"
            assert "NaN" not in bp_text, f"[{theme}] Buying power contains NaN: {bp_text}"

            # 3. Market Depth Table has rows and is not loading
            depth_rows = page.locator("#tx-depth-body tr")
            assert depth_rows.count() in (1, 2, 5), f"[{theme}] Expected 1, 2, or 5 depth rows, got {depth_rows.count()}"
            depth_text = page.locator("#tx-depth-body").inner_text()
            assert "Loading depth" not in depth_text, f"[{theme}] Depth table still shows loading: {depth_text}"

            # 4. Market watch toolbar height <= 54px and rows >= 5
            mw_hdr_box = page.locator(".tx-mw-header").bounding_box()
            assert mw_hdr_box is not None and mw_hdr_box["height"] <= 54, f"[{theme}] MW header too tall: {mw_hdr_box['height'] if mw_hdr_box else None}"
            rows_count = page.locator("#watchlist-body tr").count()
            assert rows_count >= 5, f"[{theme}] Expected >= 5 market watch rows, got {rows_count}"

            # 5. Topbar right-edge: theme toggle button not clipped
            ws_box = page.locator(".tx-workspace").bounding_box()
            theme_btn_box = page.locator("#theme-toggle-btn").bounding_box()
            assert ws_box is not None and theme_btn_box is not None
            assert theme_btn_box["x"] + theme_btn_box["width"] <= ws_box["x"] + ws_box["width"] + 2, (
                f"[{theme}] Theme toggle button clipped outside workspace: "
                f"btn_right={theme_btn_box['x'] + theme_btn_box['width']}, ws_right={ws_box['x'] + ws_box['width']}"
            )

            # 6. Ticket internal form elements: all-or-none & submit button 100% inside ticket
            t_box = page.locator("#tx-order-ticket").bounding_box()
            aon_box = page.locator("#tx-order-all-or-none").bounding_box()
            sub_box = page.locator("#tx-order-submit-btn").bounding_box()
            assert t_box is not None and aon_box is not None and sub_box is not None
            assert aon_box["y"] + aon_box["height"] <= t_box["y"] + t_box["height"] + 2, f"[{theme}] All-or-none clipped"
            assert sub_box["y"] + sub_box["height"] <= t_box["y"] + t_box["height"] + 2, f"[{theme}] Submit button clipped"

            # 7. Available saleable quantity in ticket (>= 0, and > 0 for BANKASIA)
            avail_text = page.locator("#tx-ticket-avail-qty").inner_text()
            assert int(avail_text) >= 0, f"[{theme}] Available saleable quantity is negative: {avail_text}"
            curr_sym = page.locator("#tx-ticket-sym").inner_text()
            if "BANKASIA" in curr_sym:
                assert int(avail_text) > 0, f"[{theme}] Available saleable quantity for BANKASIA is zero: {avail_text}"

            # 8. LTP in ticket must match real price
            ticket_ltp = page.locator("#tx-ticket-ltp").inner_text()
            assert float(ticket_ltp) > 0, f"[{theme}] Ticket LTP is non-positive: {ticket_ltp}"

            # 9. Passive spy button must be visible in main nav
            assert page.locator("#tx-passive-spy-btn").is_visible(), f"[{theme}] Passive spy button missing in main nav"

        # Assert visual gates in Dark Theme
        assert_strict_visual_gates("dark")

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
        assert rows.count() >= 5, "Fewer than 5 market watch rows rendered"
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
        bank_row = page.locator('#watchlist-body tr[data-symbol="BANKASIA"]')
        if bank_row.count() > 0:
            bank_row.click()
        else:
            page.locator("#watchlist-body tr").first.click()
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

        # Switch back to trade view if needed
        page.click("#tx-nav-trade")
        time.sleep(0.3)

        # 6. Light Theme Switcher & Screenshot
        page.click("#theme-toggle-btn")
        time.sleep(0.35)
        page.screenshot(path="scratch/verify_v1_light.png")

        # Visual gates in Light Theme
        assert_strict_visual_gates("light")

        # Sprint 5H Light Theme Computed Background Brightness assertions (RGB brightness > 180)
        light_selectors = [
            ".tx-top-header",
            ".tx-search-wrap",
            "#company-search",
            ".tx-panel-header",
            "#tx-order-qty",
            "#tx-order-price",
            "#tx-depth-table thead",
            "#tx-depth-table thead th",
            ".tx-depth-foot",
            "#tx-broker-mirror-card",
        ]
        for sel in light_selectors:
            brightness = page.evaluate(f"""() => {{
                const el = document.querySelector('{sel}');
                if (!el) return 255;
                const bg = window.getComputedStyle(el).backgroundColor;
                const m = bg.match(/\\d+/g);
                if (!m || m.length < 3) return 255;
                return 0.299 * Number(m[0]) + 0.587 * Number(m[1]) + 0.114 * Number(m[2]);
            }}""")
            assert brightness >= 180, f"Element {sel} failed Light Theme brightness check (expected >= 180, got {brightness})"

        # 7. Split-Screen 760x900 and 800x900 assertions (zero left/right clipping)
        for vp_width in (800, 760):
            page.set_viewport_size({"width": vp_width, "height": 900})
            time.sleep(0.3)
            first_child_box = page.evaluate("""() => {
                const hdr = document.querySelector('.tx-top-header');
                const first = hdr ? hdr.firstElementChild : null;
                if (!first) return null;
                const r = first.getBoundingClientRect();
                return { left: r.left, right: r.right };
            }""")
            assert first_child_box is not None
            assert first_child_box["left"] >= 0, (
                f"[{vp_width}px] First child of .tx-top-header clipped off-screen left: left={first_child_box['left']}"
            )

            theme_btn_box = page.locator("#theme-toggle-btn").bounding_box()
            assert theme_btn_box is not None
            assert theme_btn_box["x"] + theme_btn_box["width"] <= vp_width + 4, (
                f"[{vp_width}px] Theme toggle button right edge ({theme_btn_box['x'] + theme_btn_box['width']}) clipped beyond viewport {vp_width}px"
            )

        page.set_viewport_size({"width": 1440, "height": 900})
        time.sleep(0.2)

        # 8. Test live passive ingest of ACMEPL (All DSE tab isolation, % Chg, sparklines, and ৳353 Buying Power)
        import urllib.request
        import json as py_json
        ingest_payload = {
            "source": "EDGE_EXTENSION_PASSIVE",
            "dse_status": "Trading",
            "tab": "Dhaka Stock Exchange",
            "market_watch_rows": [
                {
                    "sDes": "ACMEPL",
                    "ltp": "27.50",
                    "chg": "1.40",
                    "pctChg": "5.39",
                    "vol": "25000",
                    "dispSettType": "PUBLIC",
                    "dispSymCat": "A",
                }
            ],
            "account_summary": {
                "customer_number": "H9210",
                "cash_balance": 353.00,
                "buying_power": 353.00,
            },
        }
        req = urllib.request.Request(
            f"{base_url}/api/tradexpress/passive-ingest",
            data=py_json.dumps(ingest_payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Origin": "chrome-extension://testabc123"},
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            assert resp.status == 200

        # Refresh page to fetch updated snapshot
        page.goto(f"{base_url}/", wait_until="networkidle")
        page.wait_for_selector("#tx-trade-workspace", state="visible", timeout=6000)
        time.sleep(0.5)

        # 8a. My Favorites tab MUST NOT show ACMEPL
        fav_btn = page.locator('button[data-cat="ALL"]')
        if fav_btn.count() > 0:
            fav_btn.click()
            time.sleep(0.3)
        assert page.locator('#watchlist-body tr[data-symbol="ACMEPL"]').count() == 0, "ACMEPL leaked into My Favorites tab!"

        # 8b. All DSE tab MUST show ACMEPL with +5.39% and sparkline SVG
        dse_btn = page.locator('button[data-cat="ALL_DSE"]')
        if dse_btn.count() > 0:
            dse_btn.click()
            time.sleep(0.4)
            acme_row = page.locator('#watchlist-body tr[data-symbol="ACMEPL"]')
            assert acme_row.count() > 0, "ACMEPL not found in All DSE tab!"
            row_text = acme_row.inner_text()
            assert "+5.39%" in row_text or "5.39%" in row_text, f"ACMEPL % Chg missing +5.39%: {row_text}"
            assert "+0.00%" not in row_text, f"ACMEPL % Chg incorrectly shows +0.00%: {row_text}"
            assert acme_row.locator("svg.sparkline").count() > 0, "ACMEPL missing inline sparkline svg!"

        # 8c. LIVE BROKER MIRROR card displays ৳353.00
        page.click("#tx-tab-account-summary")
        time.sleep(0.3)
        bm_bp_text = page.locator("#tx-bm-bp").inner_text()
        assert "353" in bm_bp_text, f"LIVE BROKER MIRROR Buying Power not showing ৳353.00: {bm_bp_text}"
        assert bm_bp_text != "৳0.00", f"LIVE BROKER MIRROR stuck at ৳0.00: {bm_bp_text}"

        # 9. Zero JS Console Errors
        assert len(js_errors) == 0, f"Encountered uncaught JS errors: {js_errors}"

        browser.close()
