---
name: tradexpress_passive_safety
description: "Non-negotiable passive-only security, two-stage graduation gate, and DSE schedule for LankaBangla TradeXpress."
version: 1.1.0
author: Humming Bird
license: MIT
metadata:
  hermes:
    tags: [tradexpress, security, anti_ban, passive_sniffing, cdp, dse_schedule, shadow_dummy, trade_gate, ember_selectors]
---

# LankaBangla TradeXpress Passive-Only Security & Operational Boundaries

## 1. Operating Context & Risk Posture
LankaBangla Securities TradeXpress 2.0 (`https://itrade.lbsbd.com`) and iBroker (`https://ibroker.lbsbd.com/Home`) are real-money institutional execution portals. Account `H9210` enforces single-session authentication and automated locks after 3–5 consecutive login failures. To guarantee zero-ban operation and 100% account safety, the trading system operates under strict architectural constraints.

---

## 2. Non-Negotiable Operational Rules

### Rule 1: 100% Passive Network Sniffing Only
- **Zero Active Polling or Scraping:** Live market data from `https://itrade.lbsbd.com` is captured **strictly passively** from the operator's manually logged-in browser session via a local Chrome DevTools Protocol (`CDP`) WebSocket listener (`connect_over_cdp("http://127.0.0.1:9222")`).
- **Dual WebSocket Awareness:**
  - **Trade / OMS Socket (Left Dot):** `wss://itrade.lbsbd.com/streaming-api` (Order and portfolio events).
  - **Price Feed Socket (Right Dot):** `wss://itrade.lbsbd.com/wsqs` (Live ticker, depth, and index ticks).
- **No Automated Auth:** The operator logs in manually at `09:55 AM Asia/Dhaka`. The bot and Hermes must **NEVER** attempt automated credential submission, password entry, or captcha bypass.
- **Strict Prohibition:** Hermes must **NEVER** suggest, recommend, or trigger active HTTP polling, `fetch()`, `httpx` GET/POST requests, `page.reload()`, or scraping against `itrade.lbsbd.com` or `ibroker.lbsbd.com`.

---

### Rule 2: Two-Stage Graduation Gate
To protect real capital, the system enforces a strict two-stage graduation gate:

1. **Stage 1 (`SHADOW_DUMMY` Mode):**
   - Live passively sniffed TradeXpress quotes and Bid/Offer order-book depth feed our local Humming Bird Dummy Cockpit simulator.
   - All AutoTrader cycles, Hermes actions, and operator manual orders execute **strictly against the local simulator**.
   - **Real BDT Risk:** Exactly 0.00 BDT. Allows full validation of curve reading, execution timing, and self-learning loops on real DSE market feeds.
2. **Stage 2 (`TRADEXPRESS_LIVE` Mode):**
   - Enabled **ONLY** after the operator explicitly graduates the system following verified simulator performance.
   - Requires the mandatory **2-step Limit order confirmation flow**:
     1. `New Order - <SYMBOL>\`PB`: Verify parameters, read available Buying Power and order depth, and click `button.btn-buy`.
     2. `Confirm Order <SYMBOL>\`PB`: Read back and verify all parameters in modal `#confirmationPopup-8-1-1-1` before clicking the green `Confirm Order` button to dispatch to the DSE engine.
   - **Preflight Enforcements:**
     - Settlement: Strictly `PUBLIC` (NEVER `SPOT`).
     - Category: Strictly `A` or vetted `B` (NEVER `Z`).
     - Order Type: Strictly `Limit` (NEVER `Market`).
     - Time In Force: Strictly `DAY` (expires at 02:10 PM; NEVER `GTC`).
     - Flags: `All or None` unchecked (`false`), `Disclosed Qty` / `Min Fill` blank.
     - Profit Hurdle: Net return calculation strictly incorporates round-trip Commission (0.40%) + 15% VAT on commission + exchange charges (~1.02% total).

---

### Rule 3: Verified DSE Market Schedule (Asia/Dhaka, Sun–Thu)
Every trading action and schedule must adhere to the official DSE timetable:
- **Continuous Trading:** `10:00:00 – 13:59:59` (`session_phase = "CONTINUOUS"` — regular continuous matching).
- **Post-Closing Session:** `14:00:00 – 14:10:00` (`session_phase = "POST_CLOSING"` — orders match **strictly at the exact closing price / last LTP**; all deviating limit orders fail or stay unfulfilled).
- **Market Close:** `14:10:01` (`session_phase = "CLOSED"` — exchange closed; all DAY orders expire; EOD clearing begins).

---

### Rule 4: Protocol Quirks & Operational Realities
1. **Symbol Format (Backtick):**
   TradeXpress symbols on DSE Public Board carry a **backtick**, e.g. ``BANKASIA`PB``, ``MATINSPINN`PB`` (NOT `'PB`). The system normalizes internal symbols to `` `PB `` and defensively accepts `'PB`.
2. **Market Watch Badges:**
   - `span.wk52-up-icon i.icon-high-low-52`: Company has reached 52-week high (visual glyph is `52`, not `S2`).
   - `i.icon-jump-up`: LTP reached maximum upper circuit breaker ceiling.
3. **Native T+2 Maturity:**
   TradeXpress exposes real matured shares under `cell-id="avaiQtyDSE"` and unmatured shares under `cell-id="penHolding"`.
4. **Midnight OMS Maintenance Window (23:45–01:00):**
   Between 23:45 and 01:00 Asia/Dhaka, TradeXpress OMS gateway disconnects (`Trade Disconnected. Retrying..`) and login attempts fail with `Authentication timed out. Please Retry...`. Hermes must recognize this as scheduled clearing maintenance, NOT an account lock.

---

### Rule 5: Self-Learning Boundary & Immutable Kernel Invariants
Hermes continuously observes market patterns, trade outcomes, and operator manual overrides, updating `memories/MEMORY.md` and proposing skill, allocation, or watchlist adjustments. However:
- **Immutable Invariants:** Hermes may **NEVER** override, bypass, or propose weakening hard kernel safety invariants:
  - **Strict No-Loss Hold:** Never sell matured shares at a net loss (< 0% after round-trip fees).
  - **T+2 Settlement Lock:** 3-bucket rolling capital structure (Buckets A, B, C).
  - **Hard Exchange Filters:** Strict prohibition on `Z`-category and `SPOT` settlement stocks.
  - **Passive-Only Rule:** Strict prohibition on active HTTP scraping, reloading, or automated login on LankaBangla portals.
  - **Risk Caps & Kill Switch:** Kernel order limits, symbol caps, daily budgets, and global emergency kill switch.
