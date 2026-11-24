# LankaBangla Securities TradeXpress 2.0 & iBroker Context, Master Site Map & Execution Blueprint

> [!CAUTION]
> **2-Touchpoint Hard Broker Firewall Rule (CRITICAL ZERO-BAN INVARIANT)**  
> Strictly **TWO** interaction touchpoints are permitted with `itrade.lbsbd.com`:  
> 1. **Passive Sniffing Touchpoint:** Passive network and read-only DOM text inspection over local Chrome DevTools Protocol (`connect_over_cdp("http://127.0.0.1:9222")`) listening ONLY to incoming browser WebSocket frames (`page.on("websocket")`) from the operator's manually logged-in session. Zero active requests, zero HTTP scraping, zero polling, zero reload.  
> 2. **Explicit 2-Step Execution Touchpoint:** Permitted ONLY in Stage 2 (`TRADEXPRESS_LIVE`) mode with mandatory operator confirmation: Step 1 (`New Order` input) -> Step 2 (`Confirm Order` read-back verification) -> Final dispatch.  
> **LOCAL-ONLY COCKPIT MANDATE:** All AI, Hermes agent reasoning, signal analysis, paper simulation, and learning run 100% locally in our cockpit. NEVER automate login, credential entry, password submission, or active HTTP requests on `itrade.lbsbd.com` or `ibroker.lbsbd.com`. 3–5 failures lock account `H9210`.

> **Verification Context & Real Live Execution Milestones:**  
> Verified live on LankaBangla TradeXpress 2.0 (`https://itrade.lbsbd.com`) and iBroker (`https://ibroker.lbsbd.com/Home`) on Wednesday, November 18, 2026 and Sunday, November 22, 2026.  
> **First Live Real DSE Buy Executed & Filled:**  
> `Buy BANKASIA`PB : 9 @ 17.90 : Filled` at `14:01:35` (Post-Closing Session)  
> **First Live Real DSE Sell Executed & Filled (Round-Trip Milestone):**  
> `Sell BANKASIA`PB : 9 @ 18.40 : Filled` at `13:33:36` (Continuous Session, Order Value: `165.60 BDT`; `Order List` confirmed `Filled | Sell | 9 | 18.40 | 165.60`)  
> **Client Code / Cash A/C:** `H9210` · **Market:** DSE Main Public (`PUBLIC`) · **Settlement:** T+2  
> **Zero Secrets Policy:** All session tokens, IDs, hashes, and secrets in this document are strictly `<REDACTED>`.

---

## Table of Contents
1. [Domains & Purpose Split](#1-domains--purpose-split)
2. [Tech Stack & Dual WebSocket Architecture](#2-tech-stack--dual-websocket-architecture)
3. [CRITICAL Symbol Format Discovery: The Backtick (`PB)](#3-critical-symbol-format-discovery-the-backtick-pb)
4. [Auth, Single-Session & Zero-Ban Security Rules](#4-auth-single-session--zero-ban-security-rules)
5. [Verified DSE Market Schedule (10:00–14:10 Asia/Dhaka)](#5-verified-dse-market-schedule-10001410-asiadhaka)
6. [Verified Navigation & Workspace Topology (#tradeOrderTab)](#6-verified-navigation--workspace-topology-tradeordertab)
7. [Exact 2-Step Order Execution Flow](#7-exact-2-step-order-execution-flow)
8. [Fill Verification & Cash Ledger Behavior](#8-fill-verification--cash-ledger-behavior)
9. [Verified Operational Tips, Tricks & Gotchas](#9-verified-operational-tips-tricks--gotchas)
10. [Passive Playwright Adapter Architecture](#10-passive-playwright-adapter-architecture)
11. [Operational Risk Checklist](#11-operational-risk-checklist)

---

## 1. Domains & Purpose Split

LankaBangla Securities operates two distinct web platforms with complementary roles:

```text
+---------------------------------------------------------------------------------------------------+
|                                  LankaBangla Securities Ecosystem                                 |
+-----------------------------------------------------------------+---------------------------------+
|   https://itrade.lbsbd.com (TradeXpress 2.0 / NetPlus HTML5)   |   https://ibroker.lbsbd.com     |
+-----------------------------------------------------------------+---------------------------------+
| - Real-time DirectFN NetPlus HTML5 Single Page Application (SPA)| - Classic ASP.NET Web App       |
| - Bi-directional Dual WebSocket (wss://) market feed            | - Fund Deposit / Withdrawal     |
| - Live execution terminal (Order Placement & Confirmations)     | - Detailed Ledger Statements    |
| - Market Watch (All DSE + Custom Watchlists: GSC, L1, L2)      | - Portfolio Live Valuation      |
| - Level-2 Bid/Offer Order Book Depth & Intraday Tickers         |   (Total Qty, Saleable Qty,     |
| - Real-time Order List (Filled, Open, Pending, Cancelled)       |    AVG Cost, Net Realized Gain) |
| - Dynamic Buying Power (BDT) calculation                        | - Single Sign-On (SSO) Portal   |
+-----------------------------------------------------------------+---------------------------------+
```

### 1.1 `https://itrade.lbsbd.com` (TradeXpress 2.0)
- **Engine:** DirectFN NetPlus HTML5 Single Page Application (Ember.js based).
- **Protocols:**
  - `HTTPS` for initial SPA bundles, static scripts, and periodic XHR catalog queries.
  - `WSS` dual WebSockets for live OMS execution commands and real-time quote depth.
- **Role:** Fast, sub-second execution engine. Primary target for Humming Bird passive sniffing and automated 2-step limit execution.

### 1.2 `https://ibroker.lbsbd.com/Home` (iBroker)
- **Engine:** ASP.NET Server-rendered Web Forms / MVC.
- **Role:** Clearing, back-office ledger, banking transfers (BEFTN, NPSB, bKash, Nagad), capital gain tax reports, and EOD portfolio reconciliation.
- **Key Table (`Portfolio Live`):**
  - Columns: `Company Name`, `Total Qty`, `Saleable Qty` (matured T+2 lots), `AVG Price (Cost Basis)`, `LTP`, `Total Cost`, `Market Value`, `Unrealized Gain / (Loss)`.
  - Used by Humming Bird for daily settlement audit and EOD ledger reconciliation.

---

## 2. Tech Stack & Dual WebSocket Architecture

TradeXpress 2.0 is built on **Ember.js** (`ember-view`, `ember-table`, with bundle scripts like `universal-app-*.js`, `ua-price-*.js`, `ua-trade-*.js`, `ua-chart-*.js`, and `ua-widgets-*.js`).

### 2.1 Dual WebSockets (The 2 Header Status Dots)
In the top-right header, TradeXpress displays two connectivity status dots:
1. **Trade / OMS Socket (Left Dot):**
   - URL: `wss://itrade.lbsbd.com/streaming-api`
   - Framing: JSON message envelope:
     ```json
     {
       "HED": {
         "msgTyp": 1,
         "channel": 30,
         "commVer": "DFNUAWEB_XX_LBSLNTP_X_1.000.05.3",
         "sesnId": "<REDACTED>",
         "ver": "1.0"
       },
       "DAT": { ... }
     }
     ```
   - Message Types:
     - `msgTyp: 1` — Session authentication & heartbeat.
     - `msgTyp: 6` — Customer account & portfolio telemetry.
     - `msgTyp: 31` / `200` — Order placement, cancellation, confirmation responses.
     - `msgTyp: 1006` — Live execution / fill receipt notifications.
2. **Price Feed Socket (Right Dot):**
   - URL: `wss://itrade.lbsbd.com/wsqs`
   - Framing: DirectFN proprietary binary and text streaming feed.
   - Authentication: Session bound via initial SSO token (`SSOTOK=<REDACTED>`).
   - Role: Continuous ticker updates, Best Bid / Best Offer (BBP/BAP), market depth, and index ticks.

### 2.2 Passive Browser XHR Endpoints (NEVER Call Directly; Observe Passively Only)
During active sessions, TradeXpress periodically exchanges XHR queries to populate metadata:
- `/web/price?...&RT=306&SRC=DSE&MOD=WL:...` — Custom Watchlist definitions (`GSC`, `L1`, etc.).
- `/web/price?...&RT=308&SRC=XCHG...` — Exchange market status and turnover summary.
- `/web/price?...&RT=301...` — Full symbol catalog metadata.
- `/web/price?...&RT=52&E=DSE&S=DSE~0~<SYMBOL>%60PB...` — Periodic single-symbol price validation.
- `/web/chart?...&RT=37&E=DSE&S=<SYMBOL>...` — Historical OHLCV candle chart data.

---

## 3. CRITICAL Symbol Format Discovery: The Backtick (`PB)

> [!CAUTION]
> **TradeXpress Symbol Syntax: Backtick (`` ` `` / URL `%60`), NOT Apostrophe (`'`)**  
> On TradeXpress, securities traded on the DSE Public Market use a **BACKTICK**:
> - Real TradeXpress Symbol: ``BANKASIA`PB`` (URL encoded as `BANKASIA%60PB`)
> - Real TradeXpress Symbol: ``MATINSPINN`PB``, ``PRIMEBANK`PB``, ``GP`PB``
> - Incorrect (Will fail in DOM inputs): `BANKASIA'PB`

### Defensive Normalization Contract
The Humming Bird normalization layer (`backend/adapters/base.py`) enforces:
1. `to_tradexpress_symbol("BANKASIA")` $\rightarrow$ ``BANKASIA`PB`` (always emits backtick).
2. `from_tradexpress_symbol(...)` defensively accepts both ``BANKASIA`PB`` and `BANKASIA'PB`, returning clean upper-case `"BANKASIA"`.

---

## 4. Auth, Single-Session & Zero-Ban Security Rules

> [!CAUTION]
> **Strict Anti-Ban & Single-Session Policy**  
> LankaBangla enforces hardware session locks and strict rate-limiting on authentication endpoints. Failure to follow these rules will lock operator account `H9210`.

### 4.1 Manual Login Only (Operator Gateway)
- **Rule:** The bot **NEVER** attempts automated credential submission or password brute-forcing on `itrade.lbsbd.com`.
- **Workflow:**
  1. Operator opens the dedicated browser window at `09:55 AM Asia/Dhaka`.
  2. Operator manually enters User ID (`H9210`), Password, and completes OTP.
  3. Once authenticated and the Market Watch grid loads, the Humming Bird Playwright adapter attaches passively over CDP (`connect_over_cdp("http://127.0.0.1:9222")`).
- **Account Lock Threshold:** 3–5 consecutive failed login attempts result in an immediate automated account freeze requiring phone support and signed documentation.

### 4.2 Single-Session Enforcement
- LankaBangla permits strictly **ONE** active session per trading account.
- If a secondary browser, mobile app, or headless script logs in with `H9210`, the primary session is instantly invalidated.

### 4.3 100% Passive Data Ingestion
- **Zero Active Polling:** The adapter **NEVER** sends periodic HTTP polling loops (`GET /quotes`, `POST /market`) to TradeXpress servers.
- **WebSocket Sniffing:** Data is captured passively by attaching a listener to the browser's native WebSocket connection:
  ```python
  page.on("websocket", handle_tradexpress_ws_frame)
  ```
- **DOM State Reading:** Real-time values (`Buying Power`, `Order Status`, `LTP`) are extracted directly from rendered Ember.js DOM nodes.

---

## 5. Verified DSE Market Schedule (10:00–14:10 Asia/Dhaka)

The official DSE trading timetable operates Sunday through Thursday (`Asia/Dhaka` / UTC+6):

| Session Phase | Time Window | Allowable Order Types | Verified Behavior & Constraints |
|:---|:---|:---|:---|
| **Pre-Market** | `09:45:00 – 09:59:59` | Ingestion / Preflight | Order accumulation; no matching occurs. Humming Bird runs preflight audits. |
| **CONTINUOUS** | `10:00:00 – 13:59:59` | Buy, Sell (Limit Orders) | Real-time continuous order matching based on price-time priority. Primary algorithmic execution window. |
| **POST_CLOSING** | `14:00:00 – 14:10:00` | Closing Price Orders Only | **Critical DSE Rule:** Orders match strictly at the official closing price (last LTP). Orders above or below closing price fail. |
| **CLOSED** | `14:10:01 – 09:44:59` | Read-only | Exchange closed. EOD back-office clearing and trade settlement reconciliation. |

---

## 6. Verified Navigation & Workspace Topology (`#tradeOrderTab`)

TradeXpress organizes the trading workspace under `#tradeOrderTab`:

```text
+---------------------------------------------------------------------------------------------------+
| Top Nav: Market | Trade | Quote | Top Stocks | Heat Map | News | Chart | Daily Client Position    |
+---------------------------------------------------------------------------------------------------+
| TOP WIDGET: Market Watch Container (#watchListContainer-8-1-1-2-cached, [container-id="watchList"])|
| - Header Tabs: Dhaka Stock Exchange | My Favorites | GSC (15 verified symbols) | L1                |
| - Filter Input: input.search-query[placeholder="Filter"]                                          |
| - Toolbar: Board (Main), Asset (All/Equity/...), Sector (All Sectors), Market (Public Board)       |
| - Virtualized Ember Table: .ember-table-left-table-block | .ember-table-right-table-block           |
| - Visible Badges: 52Wk High (span.wk52-up-icon i.icon-high-low-52) | Jump-Up (i.icon-jump-up)     |
+-------------------------------------------------+-------------------------------------------------+
| BOTTOM-LEFT: Order Ticket                       | BOTTOM-RIGHT: Portfolio & Order List Monitor    |
| (#order-ticket-landscape-id,                    | (#portfolioContainer-8-1-2-3,                   |
|  [container-id="orderTicket"])                  |  [container-id="portfolio"])                    |
| - Header: New Order - <SYMBOL>`PB (DSE)         | - Tabs: Order List | Portfolio | Account        |
| - Side: #orderSideToggleSwitch8-1-1-1           |         Summary | Order Search                  |
| - Telemetry: Buying Power, Avail Qty, Gain/Loss | - Portfolio Grid with T+2 Maturity Attributes:   |
| - Inputs: Symbol, Quantity, Price, TIF (DAY)    |   * avaiQtyDSE: Matured T+2 Saleable Qty!       |
| - Submit: button.btn-buy / button.btn-sell      |   * penHolding: Unmatured T+0/T+1 Qty!          |
| - Step 2 Modal: #confirmationPopup-8-1-1-1      |   * avgCst: Real Average Cost Basis             |
+-------------------------------------------------+-------------------------------------------------+
```

### 6.1 Top Widget: Market Watch Grid (`[container-id="watchList"]`)
- **Container ID:** `#watchListContainer-8-1-1-2-cached`
- **Tabs Selector:** `#widget-header-8-1-1-2-cached a[role="tab"]`
  - Tabs: `Dhaka Stock Exchange`, `My Favorites`, `GSC`, `L1`.
  - **15 Verified GSC Symbols:** `MATINSPINN`, `PRIMEBANK`, `NPOLYMER`, `PUBALIBANK`, `IBNSINA`, `BANKASIA`, `DHAKABANK`, `ACI`, `SPCERAMICS`, `GP`, `SQURPHARMA`, `BEXIMCO`, `ROBI`, `FUWANGCER`, `IFIC`.
- **Virtualized Ember Table (`#table-8-1-1-2-cached`):**
  - TradeXpress uses Ember Table virtualization (`lazy-list-container`). Only ~19 rows exist in DOM at any instant.
  - Because `GSC` has 15 symbols, **all 15 GSC symbols fit in DOM without scrolling**.
  - Split into:
    - `.ember-table-left-table-block`: Symbol name (`.symbol-fore-color`) and status badges.
    - `.ember-table-right-table-block`: Numerical data cells.
- **Verified Badges:**
  - `span.wk52-up-icon i.icon-high-low-52` $\rightarrow$ `title="Today's High Reached 52Wk High"` (visual glyph looks like `52`, NOT `S2`!).
  - `i.icon-jump-up` $\rightarrow$ `title="Last Trade Price Reached Max Value"` (upper circuit ceiling hit).
- **Verified Stable Cell Attributes (`cell-id`):**
  - `cell-id="dataObj.sDes"` — Symbol Description (e.g. ``BANKASIA`PB``)
  - `cell-id="dataObj.ltp"` — Last Traded Price
  - `cell-id="dataObj.ltq"` — Last Traded Quantity
  - `cell-id="dataObj.chg"` — Absolute Price Change
  - `cell-id="dataObj.pctChg"` — Percentage Price Change
  - `cell-id="dataObj.vol"` — Cumulative Volume
  - `cell-id="dataObj.bbp"` — Best Bid Price
  - `cell-id="dataObj.bbq"` — Best Bid Quantity
  - `cell-id="dataObj.bap"` — Best Offer/Ask Price
  - `cell-id="dataObj.baq"` — Best Offer/Ask Quantity
  - `cell-id="dataObj.trades"` — Number of Trades
  - `cell-id="dataObj.ltd"` — Last Trade Date (DD-MM-YYYY)
  - `cell-id="dataObj.dltt"` — Last Trade Time (HH:MM:SS)
  - `cell-id="dataObj.open"` — Session Open Price
  - `cell-id="dataObj.high"` — Session High Price
  - `cell-id="dataObj.low"` — Session Low Price
  - `cell-id="dataObj.dispSettType"` — Settlement Type (`PUBLIC` live / `N/A` off-hours)
  - `cell-id="dataObj.dispSymCat"` — Symbol Category (`A`, `B`, `Z` live / `N/A` off-hours)

### 6.2 Bottom-Left Widget: Order Ticket (`[container-id="orderTicket"]`)
- **Container ID:** `#order-ticket-landscape-id`
- **Header:** `#widget-header-8-1-1-1` (`New Order - <SYMBOL>`PB (DSE)`)
- **Side Toggle:** `#orderSideToggleSwitch8-1-1-1` (`input[name="buy-sell-switch"]`)
- **Telemetry Display (`#order-top-panel-8-1-1-1`):**
  - Buying Power: `[data-id="bp-short"] .holding-trade-bp`
  - Available Quantity: `[data-id="available-quantity"] .holding-trade`
  - Gain/Loss: `[data-id="gain-loss"]`
- **Price & Limit Information (`#order-symbol-info`):**
  - Symbol Search Input: `#searchField-8-1-1-1`
  - Pending Order Indicator: `[data-id="order-price-info-level-5"]`
  - Min / Max Circuit Limits: `[data-id="order-price-info-level-4"]`
  - Top Bid / Offer Summary: `[data-id="order-price-info-level-3"]`
  - Session Low / High: `[data-id="order-price-info-level-2"]`
- **Parameter Inputs:**
  - Quantity: `#qtyField-8-1-1-1`
  - Price: `#orderPriceId-8-1-1-1`
  - Disclosed Qty: `#orderDisQtyId-8-1-1-1` (leave blank)
  - Min Fill: `#orderMinQtyId-8-1-1-1` (leave blank)
  - Time in Force (TIF): `button.btn-order-tif` (must be `DAY`)
  - All-or-None: `input[name="allOrNone"]` (must be unchecked / false)
- **Action Buttons (`#executeComp-8-1-1-1`):**
  - Submit Button: `button.btn-buy` (or `button.btn-sell`). Note: Dynamic button ID contains price (e.g. `Buy @ 17.90-8-1-1-1`), so select by class `.btn-buy` inside `#executeComp-8-1-1-1`!
  - Reset Button: `#reset-8-1-1-1`
  - Step 2 Confirmation Modal: `#confirmationPopup-8-1-1-1`

### 6.3 Bottom-Right Widget: Portfolio & Order Monitor (`[container-id="portfolio"]`)
- **Container ID:** `#portfolioContainer-8-1-2-3`
- **Tab Selectors:**
  - `a[container-tab-id="orderList"]` — Active and filled orders
  - `a[container-tab-id="portfolio"]` — Live holding balances
  - `a[container-tab-id="accountSummary"]` — Cash & purchasing power overview
  - `a[container-tab-id="orderSearch"]` — Historical order lookup
- **Verified Portfolio Grid `cell-id` Attributes:**
  - `symbolInfo.dSym` — Security Symbol
  - `profLossQty` — Total Holding Quantity
  - `pendSell` — Pending Sell Quantity
  - `pendBuy` — Pending Buy Quantity
  - `avaiQtyDSE` — **Matured T+2 Saleable Quantity** (Native T+2 maturity tracking!)
  - `avaiQtyCSE` — Available on Chittagong Stock Exchange
  - `penHolding` — **Unmatured T+0/T+1 Quantity**
  - `mktPrice` — Current Market Price
  - `avgCst` — Average Cost Basis
  - `costVal` — Total Acquisition Cost Value
  - `mktVal` — Current Market Value
  - `gainLoss` — Absolute Unrealized Gain / Loss
  - `gainLossPer` — Percentage Unrealized Gain / Loss
  - `portPer` — Percentage of Total Portfolio

---

## 7. Exact 2-Step Order Execution Flow

> [!IMPORTANT]
> **Two-Step Broker Commitment**  
> TradeXpress 2.0 enforces an explicit two-panel verification flow. Clicking `Buy` or `Sell` in the input panel **DOES NOT** transmit the order to the exchange. It transitions the UI into a confirmation review state.

```mermaid
flowchart TD
    A["Operator / Hermes Triggers Order"] --> B["Step 1: 'New Order - SYMBOL`PB' Panel"]
    B --> C["Verify Side: Buy / Sell Toggle"]
    C --> D["Read Live Buying Power (BDT) & Order Book Depth"]
    D --> E["Enter Quantity & Price"]
    E --> F["Inspect Calculated Order Value, Comm + VAT, Net Value"]
    F --> G["Click Submit Button: button.btn-buy"]
    G --> H["Step 2: Confirmation Modal #confirmationPopup-8-1-1-1"]
    H --> I{"Verify Overlay Fields"}
    I -->|"Match Verified"| J["Click Green 'Confirm Order' Button"]
    I -->|"Discrepancy / Drift"| K["Click 'Cancel' & Abort"]
    J --> L["Dispatched to DSE Order Engine"]
    L --> M["Top Banner: 'Buy SYMBOL`PB : Qty @ Price : Filled'"]
    M --> N["Order List Table Updated with Order ID & Status"]
```

### 7.1 Step 1: Input Panel & Floating Sell Popup
1. **Side Selection:**
   - Buy: Green `Buy` button / toggle.
   - Sell: Click sell button on position or toggle red `Sell`. Opens floating Order Ticket (`New Order - <SYMBOL>`PB (DSE)`).
2. **Purchasing Power & Holding Metrics:**
   - For Buys: Verify `Order Value <= Buying Power`.
   - For Sells: Displays top holding row: `Holding | Buy Pending | Sell Pending` directly above parameters. Verify `Quantity <= Saleable Qty (Holding)`.
3. **Parameter Entry:** Fill `#qtyField-8-1-1-1` (Quantity) and `#orderPriceId-8-1-1-1` (Limit Price).
4. **Calculated Value Summary:** Directly below inputs: `Order Value | Commission | VAT | Net Value`.
   - **Intraday Fee Display Quirk:** Note that both the order ticket and confirmation modal display `Commission: 0.00` and `VAT: 0.00` intraday (`Net Value == Order Value`). Real clearing fees are deducted at EOD.
5. **Submit:** Click `button.btn-buy` (for Buy) or `button.btn-sell` (for Sell) inside `#executeComp-8-1-1-1`.

### 7.2 Step 2: Confirmation Modal (Green for Buy, Red/Crimson for Sell)
1. **Target:** `#confirmationPopup-8-1-1-1`.
2. **Visual Differentiation & Subtitle:**
   - Subtitle header: Shows company full name, exchange, and board, e.g. `BANK ASIA PLC. | DSE | Main`.
   - Buy Modal: Header/accent is green/blue, confirm button is green `button.btn-confirm` / `Confirm Order`.
   - Sell Modal: Header/accent is red/crimson, confirm button is red `button.btn-confirm` / `Confirm Order`.
3. **Read-back Verification Grid:**
   - Row 1: `Side | Order Type | TIF` (e.g. `SELL | LIMIT | DAY`)
   - Row 2: `Price | Quantity | Commission (0.00)`
   - Row 3: `VAT (0.00) | Order Value | Net Value`
4. **Action:**
   - If all parameters match engine intent 100%, click `button.btn-confirm` (or button labeled `Confirm Order` — green for Buy, red for Sell).
   - If any discrepancy is detected, click `button:has-text("Cancel")` (or `Cancel`) and abort immediately.

---

## 8. Fill Verification & Cash Ledger Behavior

### 8.1 Top Notification Toast
- Immediate Fill:
  ```text
  Buy BANKASIA`PB : 9 @ 17.90 : Filled
  Sell BANKASIA`PB : 9 @ 18.40 : Filled
  ```
- Resting Limit Order:
  ```text
  Buy BANKASIA`PB : 9 @ 17.90 : Queued / New
  ```

### 8.2 Real-time Buying Power & Back-Office Ledger Mechanics
- **Immediate Gross Deduction on Buy:**
  TradeXpress deducts the **exact gross order value** upfront from active `Buying Power`:
  $$\text{Buying Power}_{\text{after}} = \text{Buying Power}_{\text{before}} - (\text{Quantity} \times \text{Price})$$
- **Immediate Gross Credit on Sell (Unsettled Sales Immediate Credit):**
  When a sell order fills (e.g. `Sell BANKASIA`PB 9 @ 18.40 = 165.60 BDT`), gross sales proceeds **immediately credit** to active `Buying Power`:
  $$\text{Buying Power}_{\text{after}} = \text{Buying Power}_{\text{before}} + (\text{Quantity} \times \text{Price})$$
  Confirmed live on `22-11-2026`: Buying Power increased immediately from `188.00 BDT -> 353.60 BDT` upon fill, allowing instant intraday re-investment before T+2 rolling settlement maturity.
- **CRITICAL Intraday Commission Display Quirk & Broker Fee Breakdown:**
  - **Intraday UI Quirk:** Both the Order Ticket (`New Order`) and Step 2 Confirmation modal show `Commission: 0.00` and `VAT: 0.00` (`Net Value == Order Value`).
  - **Actual Broker Clearing Fee:** Real LankaBangla effective fee is **`~0.40%` per side** (`0.64 BDT` verified on `161.10 BDT` buy -> `Cost Value: 161.74`, `Avg. Cost: 17.97`), debited during EOD back-office clearing.
  - **Local Kernel Mandate:** Local Humming Bird kernel MUST compute the `~0.40%` fee independently and strictly enforces its conservative **`0.50%` per side (`1.00%` round trip)** net profit hurdle, guaranteeing zero-loss even with broker fee variations.

### 8.3 Account Summary Tab Mechanics (`a[container-tab-id="accountSummary"]`)
The `Account Summary` sub-tab inside `#portfolioContainer-8-1-2-3` provides direct visibility into verified balance fields:
- `Customer Number`: Client Code `H9210`.
- `Cash Balance`: Settled ledger cash balance (`188.00 BDT`).
- `Available Cash Balance`: Real-time trading purchasing power (`353.60 BDT`).
- `Blocked Amount`: Active order reserves (`0.00 BDT`).
- `Cash Available For Withdrawal`: Matured funds eligible for BEFTN/NPSB.
- `Unsettled Sales`: Unmatured T+1/T+2 sales proceeds (`165.60 BDT`).
- `Payable Amount`: Pending broker clearing charges (`0.00 BDT`).
- **Live Invariant Verified:** Unsettled sales are immediately added to `Available Cash Balance / Buying Power`, permitting seamless intraday redeployment.

### 8.4 Inactive & SPOT Instrument Protections
- **SPOT Settlement Stocks:** Attempting to place an order for a SPOT instrument (e.g. `ASIATICLAB`PB) displays a system error modal:
  ```text
  Order cannot be placed for SPOT instrument
  ```
- **Halted / Inactive Stocks (`N/A` / `LTP = 0.00`):** Attempting to trade halted securities (e.g. `ATCSLGF`PB with `LTP = 0.00` or `Status: N/A`) is rejected.
- **Preflight Filter Invariant:** The trading engine must verify `Settlement Type == 'PUBLIC'`, `Category != 'Z'`, and `LTP > 0.00` before generating order tickets.

### 8.5 Sprint 5G DOM Extraction Patterns (Account Summary & 5-Level Depth)
- **Resilient Label-Based Account Summary Parsing:** Rather than hardcoded table indices, `content.js` matches row labels across `#portfolioContainer-8-1-2-3` using case-insensitive regex patterns:
  - `Customer Number` -> client code `H9210`
  - `Cash Balance` -> settled ledger cash (`353.00 BDT`)
  - `Available Cash Balance` / `Available Cash` -> real-time trading power
  - `Blocked Amount` -> reserved capital
  - `Cash Available For Withdrawal` -> withdrawable balance
  - `Unsettled Sales` -> unmatured sales proceeds
  - `Payable Amount` -> clearing payable
- **Order Ticket Header Buying Power Fallback:** Order ticket header and `#order-ticket-landscape-id` top panel display `Buying Power: ৳353.00` even before the Account Summary tab is clicked. `content.js` scrapes this fallback so `LIVE BROKER MIRROR (H9210)` never displays `৳0.00`.
- **Real 5-Level Bid/Offer Depth Parsing:** Targets the depth table inside `#order-ticket-landscape-id` containing `Bid` and `Offer` column headers, extracting up to 5 non-empty rows with numeric quantities and prices.

---

## 9. Verified Operational Tips, Tricks & Gotchas

1. **Manual Login Only:**
   The human operator logs in manually at `09:55 AM`. Bot never enters credentials or solves captchas.
2. **Chrome / Edge v136+ CDP Security Rule:**
   Modern Chromium explicitly ignores `--remote-debugging-port=9222` on default user profiles to prevent credential hijacking. To open CDP, always specify an explicit, non-default directory:
   ```cmd
   msedge.exe --remote-debugging-port=9222 --user-data-dir="%LOCALAPPDATA%\Microsoft\Edge\TradeXpressDebug"
   ```
3. **Never Force-Kill While Logged In:**
   Never run `Stop-Process -Force` or kill the browser process while logged into TradeXpress. Doing so leaves the session hanging on the server and blocks re-login. Always click `Log out` cleanly first.
4. **Midnight OMS Maintenance Window (23:45–01:00 Asia/Dhaka):**
   Every night (and Thursday night into Friday weekend), DirectFN takes the OMS gateway offline for clearing. The top banner displays `Trade Disconnected. Retrying..` and login attempts fail with `Authentication timed out. Please Retry...`. **This is normal server maintenance, NOT an account lock.** Do NOT retry repeatedly during maintenance.
5. **Off-Hours / Weekend Field Behavior:**
   When DSE is closed or over weekends, TradeXpress displays `Buying Power: 0.00` and `dispSettType` / `dispSymCat` display `"N/A"`. Testing engines must handle `"N/A"` gracefully via cached metadata rather than throwing exceptions.
6. **Ember Table Virtualization:**
   Only ~19 rows are mounted in `#table-8-1-1-2-cached` at any time. For full market scans, never rely on scrolling the table; rely exclusively on passive sniffing of `wss://itrade.lbsbd.com/wsqs` and `/web/price` payloads.

---

## 10. Passive Playwright Adapter Architecture

```mermaid
classDiagram
    class TradeXpressLiveClient {
        +Path profile_directory
        +BrowserContext context
        +Page page
        +str cash_account_no
        +connect_cdp(endpoint_url)
        +attach_session(profile_dir)
        +get_status() dict
        +read_buying_power() Decimal
        +read_matured_lots() list
        +execute_order_twostep(symbol, side, qty, price) dict
    }

    class TradeXpressWebSocketSniffer {
        +on_oms_message(frame)
        +on_price_message(frame)
        +parse_market_depth(payload)
        +parse_fill_notification(payload)
        +update_shared_memory()
    }

    class TradeXpressExecutor {
        +validate_preflight(order)
        +step1_enter_parameters(page, order)
        +step2_verify_and_confirm(page, order)
        +await_fill_receipt(page, timeout)
    }

    TradeXpressLiveClient --> TradeXpressWebSocketSniffer : attaches to
    TradeXpressLiveClient --> TradeXpressExecutor : delegates order to
```

### 10.1 Edge / Chrome Extension Passive Mirror (`extension/tradexpress_mirror/`)
- **Zero-Dependency Manifest V3 Extension:** Runs as a 100% read-only passive content script on `https://itrade.lbsbd.com/*` and background service worker reporting strictly to `http://127.0.0.1:8000/api/tradexpress/passive-ingest`.
- **Zero-Ban Anti-Bot Guarantees:** Strictly forbidden from clicking, typing/filling, mutating DOM, reloading/navigating, reading credentials/cookies, or communicating with any non-localhost URL.
- **Ember Virtual Table Top-Alignment (`style.top`):** Maps `.ember-table-left-table-block .ember-table-table-row` to `.ember-table-right-table-block .ember-table-table-row` by matching `row.style.top` to prevent virtual scroll row-shifting.
- **Off-Hours 0.00 Cash Guard:** When `dse_status` is `Close`/`CLOSED` and incoming `account_summary` has `buying_power == 0` and `cash_balance == 0`, preserves cached positive buying power & cash balance while continuing to ingest quotes and portfolio rows.
- **Instant SSE Push:** Every ingested snapshot triggers an atomic shadow order queue reconciliation and an instant SSE `"portfolio"` push so the local terminal updates in real time with zero reload.

### 10.2 Full Passive WebSocket & XHR Network Tap (`network_tap.js`)
- **MAIN World Passive Tap:** Injected at `document_start` into the webpage's `MAIN` execution world. Intercepts `window.WebSocket`, `XMLHttpRequest.prototype`, and `window.fetch` using non-intrusive transparent wrappers wrapped in `try/catch`.
- **Zero Secrets Redaction Protocol:** Strips or masks `sesnId`, `SSOTOK`, `token`, `password`, `Authorization`, and cookies before sending. URLs matching login/auth/password/sso/otp are NEVER recorded with request bodies (`[AUTH_REDACTED]`).
- **SOD (Start of Day) Phase Protection:**
  - Between ~09:00 and 09:59 Asia/Dhaka, TradeXpress resets quotes (`LTP`, `Bid`, `Offer`, `Vol`) to `0.00`.
  - When incoming `q.ltp <= ZERO` and existing `CompanyProfile.last_price > ZERO`, the engine preserves positive price and refuses to append `0.00` candle bars to `price_history`.
  - Portfolio snapshot generator marks SOD symbols as `WAIT_SOD` (`"Waiting for market open (LTP 0.00 / SOD phase)..."`), suppressing `QuoteError` while rendering `" — (SOD reset)"` in support position labels.
- **Unseen Symbol Auto-Rule Provisioning:**
  - Full market ingestion of previously unseen symbols (e.g., `1JANATAMF`) automatically provisions a default disabled `CustomRule(symbol=..., enabled=False, buy_allocation_pct=0.00)`.
  - Portfolio snapshot and AutoTrader enforce defensive `rules.get(symbol)` lookups with fallback to default disabled `CustomRule`, eliminating `KeyError` crashes permanently.
- **Verified Real DSE T+2 Settlement Milestone (Nov 24, 2026 09:18 AM):**
  - Nov 22 Sell (`165.60 BDT` gross) matured and settled at SOD Nov 24:
  - Account summary updated: `Cash Balance: 353.00 BDT`, `Unsettled Sales: 0.00 BDT`.
  - Verified back-office net fee: `0.60 BDT` (approx `0.36%` total brokerage + exchange fee).

---

## 11. Operational Risk Checklist

- [x] **Verified:** DSE Public Market symbols use backtick (`` `PB ``), e.g. ``BANKASIA`PB``.
- [x] **Verified:** 2 status dots correspond to `streaming-api` (OMS) and `wsqs` (Price Feed).
- [x] **Verified:** `avaiQtyDSE` provides exact matured T+2 saleable shares natively in TradeXpress.
- [x] **Verified:** Badge `icon-high-low-52` indicates 52-week high; `icon-jump-up` indicates upper circuit limit.
- [x] **Verified:** Two-step confirmation (`button.btn-buy` -> `#confirmationPopup-8-1-1-1`) is mandatory.
- [x] **Verified:** Real live sell round trip executed: `Sell BANKASIA`PB : 9 @ 18.40 : Filled` at `13:33:36` (Order Value: 165.60 BDT).
- [x] **Verified:** Intraday commission display quirk (`0.00` intraday; real fee is `~0.40%` settled at EOD; Humming Bird 0.50% hurdle enforced).
- [x] **Verified:** Gross sell proceeds immediately credited to active Buying Power upon fill.
- [x] **Verified:** SPOT instrument protection modal (`Order cannot be placed for SPOT instrument` on `ASIATICLAB`PB).
- [x] **Verified:** 2-Touchpoint Hard Broker Firewall rule enforced in documentation and agent guidelines.
- [x] **Verified:** Midnight maintenance window (`23:45–01:00`) causes `Authentication timed out`.
- [x] **Verified (Sprint 5):** Live-Data Dummy Mirror Simulator (`SHADOW_DUMMY` mode) and 100% Read-Only Passive Extension Mirror (`extension/tradexpress_mirror/`).
- [ ] **Pending (Sprint 6):** Automated 2-step execution harness with live order verification.
