#!/usr/bin/env python3
"""100% Read-Only Passive CDP Inspector for LankaBangla TradeXpress 2.0.

Attaches to the operator's already-logged-in TradeXpress browser session via Chrome
DevTools Protocol (CDP) port 9222. Passively sniffs WebSocket frames and captures
a read-only DOM snapshot without triggering any clicks, typing, page reloads, or
active HTTP requests.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.secret_guard import SecretGuard


async def run_passive_probe(cdp_url: str, duration: int, output_path: Path) -> dict:
    """Connect to existing browser over CDP and passively sniff TradeXpress."""
    from playwright.async_api import async_playwright

    print(f"[CDP Probe] Connecting to Chrome DevTools Protocol at {cdp_url}...")
    
    async with async_playwright() as pw:
        try:
            browser = await pw.chromium.connect_over_cdp(cdp_url)
        except Exception as exc:
            print(
                f"[CDP Probe] ERROR: Could not connect to Chrome DevTools Protocol at {cdp_url}.\n"
                f"  Details: {exc}\n\n"
                "To enable CDP, launch Google Chrome / Edge with remote debugging:\n"
                "  chrome.exe --remote-debugging-port=9222 --user-data-dir=\"<path_to_profile>\"\n"
                "Then manually log in to https://itrade.lbsbd.com and re-run this probe."
            )
            return {"error": "CDP_CONNECTION_FAILED", "detail": str(exc)}

        # Scan open pages across all contexts
        target_page = None
        open_urls = []
        for context in browser.contexts:
            for page in context.pages:
                url = page.url
                open_urls.append(url)
                if "itrade.lbsbd.com" in url.lower():
                    target_page = page
                    break
            if target_page:
                break

        if not target_page:
            print(
                f"[CDP Probe] Connected to CDP ({len(open_urls)} tab(s) detected), but NO active tab "
                "matching 'itrade.lbsbd.com' was found.\n"
                f"  Open URLs: {open_urls}\n"
                "Please navigate and log in to https://itrade.lbsbd.com in the debugging browser window."
            )
            return {
                "error": "TRADEXPRESS_TAB_NOT_FOUND",
                "open_tabs_count": len(open_urls),
                "open_urls": [SecretGuard.redact_secrets(u) for u in open_urls],
            }

        print(f"[CDP Probe] Found active TradeXpress tab: {SecretGuard.redact_secrets(target_page.url)}")
        print(f"[CDP Probe] Listening passively to WebSocket frames for {duration} seconds (0 active requests)...")

        ws_frames: list[dict] = []

        # 1. Attach Playwright native WebSocket listener
        def on_web_socket(ws):
            ws_url = SecretGuard.redact_secrets(ws.url)

            def on_frame_received(payload):
                try:
                    ts = datetime.now(ZoneInfo("Asia/Dhaka")).isoformat()
                    is_binary = isinstance(payload, bytes)
                    if is_binary:
                        preview = base64.b64encode(payload[:120]).decode("ascii")
                        frame_type = "binary"
                    else:
                        preview = SecretGuard.redact_secrets(str(payload)[:500])
                        frame_type = "text"
                    ws_frames.append({
                        "source": "playwright_ws",
                        "ws_url": ws_url,
                        "timestamp": ts,
                        "frame_type": frame_type,
                        "length": len(payload),
                        "preview": preview,
                    })
                except Exception:
                    pass

            ws.on("framereceived", on_frame_received)

        target_page.on("websocket", on_web_socket)

        # 2. Attach CDP session to capture frames on ALREADY-connected WebSockets
        try:
            cdp_session = await target_page.context.new_cdp_session(target_page)
            await cdp_session.send("Network.enable")

            def on_cdp_ws_frame(params: dict):
                try:
                    ts = datetime.now(ZoneInfo("Asia/Dhaka")).isoformat()
                    response = params.get("response", {})
                    payload_data = response.get("payloadData", "")
                    opcode = response.get("opcode", 1)  # 1=text, 2=binary
                    frame_type = "binary" if opcode == 2 else "text"
                    redacted_preview = SecretGuard.redact_secrets(str(payload_data)[:500])
                    ws_frames.append({
                        "source": "cdp_network",
                        "request_id": params.get("requestId", ""),
                        "timestamp": ts,
                        "frame_type": frame_type,
                        "length": len(payload_data),
                        "preview": redacted_preview,
                    })
                except Exception:
                    pass

            cdp_session.on("Network.webSocketFrameReceived", on_cdp_ws_frame)
        except Exception as cdp_err:
            print(f"[CDP Probe] Note: Direct CDP Network session attachment skipped ({cdp_err}). Using Playwright listener.")

        # 3. Capture ONE read-only DOM snapshot (zero clicks, zero typing)
        print("[CDP Probe] Capturing read-only DOM snapshot...")
        dom_snapshot: dict = {}
        try:
            dom_snapshot = await target_page.evaluate(
                """() => {
                    const snap = {
                        title: document.title || '',
                        marketWatchHeaders: [],
                        first5Rows: [],
                        watchlistTabs: [],
                        newOrderControls: [],
                        s2BadgeDetails: []
                    };

                    // Headers
                    const headers = document.querySelectorAll('th, [role="columnheader"]');
                    headers.forEach(h => {
                        const txt = (h.innerText || '').trim();
                        if (txt && !snap.marketWatchHeaders.includes(txt)) {
                            snap.marketWatchHeaders.push(txt);
                        }
                    });

                    // First 5 table / grid rows
                    const rows = document.querySelectorAll('tbody tr, [role="row"]');
                    let count = 0;
                    for (const r of rows) {
                        const txt = (r.innerText || '').replace(/\\s+/g, ' ').trim();
                        if (txt && count < 5) {
                            snap.first5Rows.push(txt);
                            count++;
                        }
                    }

                    // Watchlist Tabs
                    const tabs = document.querySelectorAll('[role="tab"], .nav-tabs li, .tab-btn');
                    tabs.forEach(t => {
                        const txt = (t.innerText || '').trim();
                        if (txt && !snap.watchlistTabs.includes(txt)) {
                            snap.watchlistTabs.push(txt);
                        }
                    });

                    // New Order Form Controls (read-only attribute inspection)
                    const controls = document.querySelectorAll(
                        'input, select, button, [role="tab"], [role="switch"]'
                    );
                    controls.forEach(c => {
                        const tag = c.tagName.toLowerCase();
                        const role = c.getAttribute('role') || '';
                        const name = c.getAttribute('name') || '';
                        const placeholder = c.getAttribute('placeholder') || '';
                        const text = (c.innerText || '').trim();
                        const type = c.getAttribute('type') || '';
                        if (placeholder || name || text) {
                            snap.newOrderControls.push({
                                tag, role, type, name, placeholder, text: text.slice(0, 50)
                            });
                        }
                    });

                    // S2 Badge & Tooltip
                    const s2Elements = Array.from(document.querySelectorAll('*')).filter(el => {
                        return (el.innerText || '').trim() === 'S2' || (el.className && String(el.className).includes('s2'));
                    });
                    s2Elements.slice(0, 5).forEach(el => {
                        snap.s2BadgeDetails.push({
                            tagName: el.tagName.toLowerCase(),
                            text: (el.innerText || '').trim(),
                            title: el.getAttribute('title') || '',
                            tooltip: el.getAttribute('data-tooltip') || el.getAttribute('aria-label') || '',
                            className: String(el.className || '')
                        });
                    });

                    return snap;
                }"""
            )
        except Exception as dom_err:
            dom_snapshot = {"error": f"DOM snapshot evaluation failed: {dom_err}"}

        # 4. Passive observation sleep
        await asyncio.sleep(duration)

        result = {
            "probe_completed_at": datetime.now(ZoneInfo("Asia/Dhaka")).isoformat(),
            "target_url": SecretGuard.redact_secrets(target_page.url),
            "target_title": dom_snapshot.get("title", ""),
            "duration_seconds": duration,
            "websocket_frames_captured_count": len(ws_frames),
            "websocket_frames": ws_frames[:200],  # Bound payload size
            "dom_snapshot": {
                "market_watch_headers": dom_snapshot.get("marketWatchHeaders", []),
                "first_5_rows": [SecretGuard.redact_secrets(r) for r in dom_snapshot.get("first5Rows", [])],
                "watchlist_tabs": dom_snapshot.get("watchlistTabs", []),
                "new_order_controls_count": len(dom_snapshot.get("newOrderControls", [])),
                "new_order_controls_sample": dom_snapshot.get("newOrderControls", [])[:30],
                "s2_badge_details": dom_snapshot.get("s2BadgeDetails", []),
            },
        }

        # Save to output path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(
            f"[CDP Probe] Finished. Captured {len(ws_frames)} WebSocket frame(s).\n"
            f"[CDP Probe] Output written to {output_path.resolve()}"
        )
        return result


def main():
    parser = argparse.ArgumentParser(
        description="100% Read-Only Passive CDP Inspector for LankaBangla TradeXpress 2.0"
    )
    parser.add_argument(
        "--cdp-url",
        default="http://127.0.0.1:9222",
        help="Chrome DevTools Protocol endpoint (default: http://127.0.0.1:9222)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="Passive observation duration in seconds (default: 30)",
    )
    parser.add_argument(
        "--output",
        default=str(REPO_ROOT / "scratch" / "tradexpress_passive_probe.json"),
        help="Output JSON file path (default: scratch/tradexpress_passive_probe.json)",
    )
    args = parser.parse_args()

    output_path = Path(args.output).resolve()
    asyncio.run(run_passive_probe(cdp_url=args.cdp_url, duration=args.duration, output_path=output_path))


if __name__ == "__main__":
    main()
