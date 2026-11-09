# Trading Cockpit & Hermes MVP Verification Plan

Tracking document for end-to-end verification of the core trading system and Hermes autonomous assistant.

---

## Phase 1: Engine & Market Data Connectivity
- [x] **Test 1.1: Unified Runner Startup**
  - **Description:** Run `npm run dev` (`python run.py`) to launch Hermes Gateway on 127.0.0.1:8642 and Cockpit UI on 127.0.0.1:8000 simultaneously.
  - **Status:** PASSED (2026-11-09)
  - **Proof:**
    - Gateway polling completed with `HEALTHY`.
    - Uvicorn backend started on `http://127.0.0.1:8000`.
    - SSE stream `/api/stream` connected with HTTP 200.
    - Portfolio endpoint `/api/portfolio` returned HTTP 200.
    - Bridge state `/api/hermes/bridge/state` returned HTTP 200.
- [x] **Test 1.2: Live StockNow Data Sync**
  - **Description:** Verify live LTP prices, 470+ All DSE shares catalog, and watchlists (GSC, L1, L2) populate from StockNow feed.
  - **Status:** PASSED (2026-11-09)
  - **Proof:**
    - Live DSE catalog loaded (475 shares).
    - Watchlists synchronized (11 core tier symbols across GSC, GSC_L1, GSC_L2).
    - Day change % verified against live StockNow: MATINSPINN at ৳127.40 (+9.92%), BANKASIA at ৳17.40 (+0.00%), ACI at ৳179.80 (+0.62%), FUWANGCER at ৳11.80 (+2.61%).
    - Fixed SQLite clock_date and StockNow live quote source reconciliation so curve analysis generates accurate day change and signals without demo date mismatch errors.
- [x] **Test 1.3: Adapter Connection Status**
  - **Description:** Check topbar badge displays `LIVE STOCKNOW` with synced time/drift and session cookies are active.
  - **Status:** PASSED (2026-11-09)
  - **Proof:**
    - Topbar shows `LIVE STOCKNOW HUMMING BIRD (STOCKNOW) #164580 (DRIFT 0.00)`.
    - DSE market session countdown accurately reports `DSE CLOSED` with time until opening session.
    - Hermes Portfolio Copilot actively connected and answering in Banglish/English.

---

## Phase 2: Manual Orders & Core Safety Guards
- [ ] **Test 2.1: Manual Buy Preview & Execution**
  - **Description:** Click Buy on any watchlist share. Verify preview card calculations (0.5% commission, cash deduction) and confirmation writes lot to ledger.
- [ ] **Test 2.2: Price Sanity Guard (Anti-Typo)**
  - **Description:** Attempt order with price deviating > 1.5% from LTP or outside day range. Verify backend blocks with `PRICE_OUT_OF_RANGE`.
- [ ] **Test 2.3: T+2 Settlement & Strict No-Loss Block**
  - **Description:** Verify selling T+0 shares is blocked by T+2 lock. Verify selling any share at net loss is blocked by Strict No-Loss policy.

---

## Phase 3: Automation Logic (L1 Dip vs L2 Momentum)
- [ ] **Test 3.1: "Run cycle now" Preview (Dry-Run)**
  - **Description:** Run single cycle with Automation OFF. Verify Decision Stream records L2 momentum rallies and L1 pullback buy/sell signals.
- [ ] **Test 3.2: Automated Order Execution**
  - **Description:** Toggle Automation ON. Verify system executes qualifying orders and writes to decision logs & audit trails.
- [ ] **Test 3.3: 90/10 Canary Split on Emergency**
  - **Description:** Trigger crash quarantine on a holding. Verify 90% profit lock and 10% canary observation retention.

---

## Phase 4: Hermes Assistant (Reporting & Command Execution)
- [ ] **Test 4.1: Natural Reporting in Chat**
  - **Description:** Ask Hermes status queries ("Portfolio status ki?", "GP er obostha ki?"). Verify accurate portfolio and curve summaries.
- [ ] **Test 4.2: Hermes Directed Order with Confirmation**
  - **Description:** Instruct Hermes to buy shares. Verify it renders a two-step preview card and executes only on operator confirmation.
- [ ] **Test 4.3: Dynamic Rule / Cap Adjustment**
  - **Description:** Instruct Hermes to adjust risk caps or strategy parameters (e.g. daily budget, L2 pullback). Verify rule checkpoint creation.

