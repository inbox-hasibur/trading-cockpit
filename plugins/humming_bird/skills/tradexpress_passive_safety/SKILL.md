---
name: tradexpress_passive_safety
description: "Non-negotiable passive-only security, two-stage graduation gate, and DSE schedule for LankaBangla TradeXpress."
version: 1.0.0
author: Humming Bird
license: MIT
metadata:
  hermes:
    tags: [tradexpress, security, anti_ban, passive_sniffing, cdp, dse_schedule, shadow_dummy, trade_gate]
---

# LankaBangla TradeXpress Passive-Only Security & Operational Boundaries

## 1. Operating Context & Risk Posture
LankaBangla Securities TradeXpress 2.0 (`https://itrade.lbsbd.com`) and iBroker (`https://ibroker.lbsbd.com/Home`) are real-money institutional execution portals. Account `H9210` enforces single-session authentication and automated locks after 3–5 consecutive login failures. To guarantee zero-ban operation and 100% account safety, the trading system operates under strict architectural constraints.

---

## 2. Non-Negotiable Operational Rules

### Rule 1: 100% Passive Network Sniffing Only
- **Zero Active Polling or Scraping:** Live market data from `https://itrade.lbsbd.com` is captured **strictly passively** from the operator's manually logged-in browser session via a local Chrome DevTools Protocol (`CDP`) WebSocket listener (`connect_over_cdp("http://127.0.0.1:9222")`).
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
     1. `New Order - <SYMBOL>'PB`: Verify parameters, read available Buying Power and order depth, and click `Buy @ <price>`.
     2. `Confirm Order <SYMBOL>'PB`: Read back and verify all parameters in the confirmation modal before clicking the green `Confirm Order` button to dispatch to the DSE engine.
   - **Preflight Enforcements:**
     - Settlement: Strictly `PUBLIC` (NEVER `SPOT`).
     - Category: Strictly `A` or vetted `B` (NEVER `Z`).
     - Order Type: Strictly `Limit` (NEVER `Market`).
     - Time In Force: Strictly `DAY` (expires at 02:10 PM; NEVER `GTC`).
     - Flags: `All or None` unchecked (`false`), `Disclosed Qty` / `Min Fill` blank.
     - Profit Hurdle: Net return calculation strictly incorporates round-trip Commission + 15% VAT.

---

### Rule 3: Verified DSE Market Schedule (Asia/Dhaka, Sun–Thu)
Every trading action and schedule must adhere to the official DSE timetable:
- **Continuous Trading:** `10:00 AM – 02:00 PM` (Regular order matching and algorithmic execution).
- **Post-Closing Session:** `02:00 PM – 02:10 PM` (Orders match **strictly at the exact closing price / last LTP**; all deviating limit orders fail or stay unfulfilled).
- **Market Close:** `02:10 PM` (Exchange closed; all DAY orders expire; EOD clearing begins).

---

### Rule 4: Self-Learning Boundary & Immutable Kernel Invariants
Hermes continuously observes market patterns, trade outcomes, and operator manual overrides, updating `memories/MEMORY.md` and proposing skill, allocation, or watchlist adjustments. However:
- **Immutable Invariants:** Hermes may **NEVER** override, bypass, or propose weakening hard kernel safety invariants:
  - **Strict No-Loss Hold:** Never sell matured shares at a net loss (< 0% after round-trip fees).
  - **T+2 Settlement Lock:** 3-bucket rolling capital structure (Buckets A, B, C).
  - **Hard Exchange Filters:** Strict prohibition on `Z`-category and `SPOT` settlement stocks.
  - **Passive-Only Rule:** Strict prohibition on active HTTP scraping, reloading, or automated login on LankaBangla portals.
  - **Risk Caps & Kill Switch:** Kernel order limits, symbol caps, daily budgets, and global emergency kill switch.
