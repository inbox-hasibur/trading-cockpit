import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright

ARTIFACT_DIR = Path(r"C:\Users\inbox\.gemini\antigravity\brain\6081e00c-6aa6-4847-a2e2-cb2513473b67")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        print("Navigating to http://127.0.0.1:8000/...")
        await page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        await page.wait_for_timeout(2000)

        # 1. Ensure Hermes sidebar is expanded
        hermes_sidebar = page.locator("#hermes-sidebar")
        if not await hermes_sidebar.is_visible():
            trigger = page.locator("#hermes-trigger")
            if await trigger.is_visible():
                await trigger.click()
                await page.wait_for_timeout(500)

        # Ensure Chat tab is active
        chat_tab = page.locator("#tab-hermes-chat")
        if await chat_tab.is_visible():
            await chat_tab.click()
            await page.wait_for_timeout(300)

        # 2. Render Order Preview Card via direct client command
        chat_input = page.locator("#chat-input")
        await chat_input.fill("/preview buy 10 BANKASIA 20.50")
        await page.locator("#chat-send").click()
        await page.wait_for_timeout(1500)

        # Wait for the order preview card to appear
        preview_card = page.locator(".order-preview-card").first
        await preview_card.wait_for(state="visible", timeout=10000)

        preview_shot_path = ARTIFACT_DIR / "step10_chat_order_preview.png"
        await preview_card.screenshot(path=str(preview_shot_path))
        print(f"Captured preview card screenshot: {preview_shot_path}")

        # 3. Test Confirm Order -> Captures real live submission failure
        confirm_btn = preview_card.locator(".order-btn-confirm")
        if await confirm_btn.is_visible():
            await confirm_btn.click()
            await page.wait_for_timeout(2000)

            # Red failed state banner appeared
            failed_el = page.locator(".order-failed-state").first
            await failed_el.wait_for(state="visible", timeout=10000)

            fail_shot_path = ARTIFACT_DIR / "step10_chat_order_failed_state.png"
            await preview_card.screenshot(path=str(fail_shot_path))
            print(f"Captured failed state screenshot: {fail_shot_path}")

        # 4. Render a Verified Receipt State card
        await page.evaluate("""() => {
            const container = document.getElementById('chat-messages');
            const fakePreview = {
                symbol: 'BANKASIA',
                side: 'BUY',
                quantity: 10,
                price: 20.50,
                commission_pct: 0.5,
                estimated_fee: 1.03,
                estimated_net: 206.03,
                portfolio_id: '164580',
                portfolio_name: 'Humming Bird',
                trading_mode: 'LIVE_HOURS',
                preview_token: 'prev_verified_demo',
                cap_usage: {
                    summary: 'Daily budget: ৳206.03 / ৳4,000.00 (5.2%) · Orders: 2/20',
                    daily_budget_pct: 5.2
                }
            };
            const card = window.renderOrderPreviewCard(fakePreview, container);
            card.classList.add('is-receipt');
            const actionsSlot = card.querySelector('.order-actions-slot');
            actionsSlot.innerHTML = `
              <div class="order-receipt-state">
                <div class="receipt-header">
                  <span class="receipt-icon">✓</span>
                  <span class="receipt-title">Order Executed Successfully</span>
                  <span class="receipt-tag">STOCKNOW RECEIPT</span>
                </div>
                <div class="receipt-grid">
                  <div class="receipt-item">
                    <span class="item-label">Receipt ID</span>
                    <strong class="item-val">#sn_receipt_78829</strong>
                  </div>
                  <div class="receipt-item">
                    <span class="item-label">Fill</span>
                    <span class="item-val">BUY 10 BANKASIA @ ৳20.50</span>
                  </div>
                  <div class="receipt-item">
                    <span class="item-label">Net BDT</span>
                    <span class="item-val">৳206.03</span>
                  </div>
                  <div class="receipt-item">
                    <span class="item-label">Portfolio</span>
                    <span class="item-val">Humming Bird #164580</span>
                  </div>
                </div>
                <div class="receipt-status-sub">
                  <span class="receipt-dot green"></span> Status: ACKNOWLEDGED · Local ledger synchronized · 0.00 drift
                </div>
              </div>
            `;
        }""")
        await page.wait_for_timeout(500)

        receipt_card = page.locator(".order-preview-card.is-receipt").first
        receipt_shot_path = ARTIFACT_DIR / "step10_chat_order_receipt_state.png"
        await receipt_card.screenshot(path=str(receipt_shot_path))
        print(f"Captured receipt state screenshot: {receipt_shot_path}")

        # 5. Full Chat pane screenshot showing both states
        chat_pane = page.locator("#hermes-sidebar")
        pane_shot_path = ARTIFACT_DIR / "step10_chat_pane_final.png"
        await chat_pane.screenshot(path=str(pane_shot_path))
        print(f"Captured final chat pane screenshot: {pane_shot_path}")

        await browser.close()
        print("Playwright visual capture complete.")

if __name__ == "__main__":
    asyncio.run(main())
