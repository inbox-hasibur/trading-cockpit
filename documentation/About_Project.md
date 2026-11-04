# 🐦 Project Humming Bird — About the Project

> **Repository:** `trading-cockpit`  
> **Current Stage:** Version 0.1 (Sprint 1 Core MVP — Paper & StockNow Automation Foundation)  
> **Target Market:** Dhaka Stock Exchange (DSE), Bangladesh  
> **Primary Execution Target (Phase 1):** `stocknow.com.bd` (Virtual Portfolio: **"Humming Bird"**)

---

## 1. Executive Vision

**Project Humming Bird** is an incremental, modular, agentic stock-trading and portfolio management cockpit engineered specifically for the **Bangladesh Stock Market (DSE)**. 

Unlike Western markets, the DSE lacks public retail trading APIs, enforces a **T+2 settlement lock**, and charges a **~1.00% round-trip brokerage fee**. Human retail traders frequently lose money due to emotional panic-selling, buying into fundamentally broken "falling-knife" stocks, or selling winning positions too early and regretting missed rallies.

Humming Bird solves this by replicating the intuition of a disciplined human trader through a deterministic, curve-aware rule engine—starting on **StockNow's virtual portfolio** and scaling version-by-version into **company-specific statistical/ML models** and **live brokerage portals** (such as LankaBangla TradeXpress and Shanta EasyTrade).

### Core Philosophy (In Banglish)
> *"Normal curve-er low-te kena, abnormal crash-e na kena (company vanish ba internal problem thakte pare). Profit hole shob ekbare sell na kore dhape dhape (+ hole kichu, aro ++ hole aro kichu) sell kora, jate afsos na korte hoy. Ar upor theke drop korle baki share-er half (50%) sell kore profit lock kora, ebong baki half (50%) long-term recovery-r jonno rekhe dewa—pore abar + hole same rule! Loss-e kokhono panic sell na kora."*

---

## 2. DSE Market Mechanics & System Constraints

| Parameter | DSE Rule / Constraint | Humming Bird Engineering Solution |
| :--- | :--- | :--- |
| **Timezone & Calendar** | `Asia/Dhaka` (UTC+6). Trading days: **Sunday – Thursday** (Friday & Saturday closed). | Working-session calendar engine that skips weekends and configured DSE holidays. |
| **Trading Hours** | **10:00 AM – 2:30 PM** BD Time. | Automated scheduler and tick engine scoped to active DSE market hours (with a manual/demo clock override for off-hours testing). |
| **Settlement Lock** | **T+2 Working Sessions**. Shares bought on Day $T$ cannot be sold until Day $T+2$. | **3-Bucket Rolling Capital Pipeline (Buckets A, B, C)** so matured inventory becomes available for sale on a rolling daily basis. |
| **Brokerage Hurdle** | **~1.00% Total Fee** (~0.5% on Buy + ~0.5% on Sell). | Exact decimal cost-basis math: break-even requires $\ge 1.005\%$ gross price gain. All profit tiers evaluate **True Net Profit %** after deducting both buy and sell fees. |
| **API Availability** | No official retail REST API for DSE order execution. | **Modular Adapter Architecture** using Async **Playwright** (Persistent Context + Network/XHR Interception + DOM Automation) instead of brittle legacy Selenium. |

---

## 3. Core Algorithmic Methodology ("Staggered Rolling No-Loss Engine")

### 3.1 Human-Like Curve Reading (`curve_analyzer.py`)
Instead of blind indicators, the agent inspects the recent **7 to 30 trading sessions' price curve** to understand a stock's natural oscillation rhythm:
- **Normal Oscillation & `BUY_ZONE`:** Identifies the support floor (recent normal lows) and resistance ceiling (recent normal highs). Triggers a buy signal only when the price dips into the lower band of a **healthy, normal curve** and offers sufficient upside margin above the 1% fee hurdle.
- **`MID_RANGE` / `HOLD_WAIT`:** When price is oscillating in the middle of its normal curve, the agent waits patiently.

### 3.2 The "Falling Knife" & Company Vanish Guard (`CRASH_QUARANTINE`)
A cheap price is dangerous if the company itself is collapsing.
- If a stock breaks below its normal oscillation curve with an **abnormal single-day plunge or multi-day free-fall**, the agent assumes potential fundamental trouble, scam, or delisting/vanishing risk.
- The stock is immediately flagged as **`CRASH_QUARANTINE`**, and **all new buying is strictly blocked** until the curve stabilizes and is reviewed.

### 3.3 Sector Intelligence & 3-Tier Watchlist Classification
Not all DSE companies behave the same way. Humming Bird groups stocks into three structured tiers:

1. **Big Giant Stable Companies (GSC):**
   - Historically established market leaders with solid fundamentals, decades of operational history, and strong institutional backing (e.g., `GP`, `SQURPHARMA`, `BATBC`, top tier banks like `BANKASIA`).
   - *Key Concept:* Promisable to survive long-term regardless of short-term market cycles. Even if currently in a dip or recovering from a loss, the existential risk of vanishing overnight is virtually non-existent.
2. **GSC Upper Trends L1 (Longer-Term Macro Comeback Wave):**
   - Subset of GSC companies that are in an established upward recovery trend after a prolonged bottom.
   - *Key Concept:* Filters out daily erratic market noise (where a stock fluctuates red one day and green the next). Focuses on smooth multi-week/multi-month curves showing clear comeback momentum.
3. **GSC Upper Trends L2 (Short-Term Fluctuation / Momentum Swing Scalp):**
   - High-turnover swing opportunities capitalizing on short-term price oscillation waves.
   - *Key Concept:* Trades the transition from red to green (e.g. slight dip turning green -> enter quickly, take profit when greener -> swing scalp). Dynamic list with agile exit thresholds.
4. **Custom Per-Company Capital Allocation (`Buy %`):**
   - The user assigns exact capital allocation percentages (e.g., `GP: 25%`, `SQURPHARMA: 25%`, `BANKASIA: 20%`) directly from the Cockpit UI or by instructing Hermes.

### 3.4 Three-Bucket Rolling T+2 Pipeline (`t2_ledger.py`)
To avoid sitting idle during the 2-day DSE settlement lock, starting capital (e.g., `15,000 BDT` test fund, scalable from `5k` to `1 Lakh+` via compounding) is divided into three rolling buckets:
- **Bucket A, Bucket B, Bucket C** (e.g., `5,000 BDT` each).
- Each working day rotates the active buying bucket while previously purchased buckets advance through $T+0 \rightarrow T+1 \rightarrow T+2 \text{ (Matured)}$.
- Every purchase is tracked as an independent **Tax Lot** with exact acquisition cost, buy fee, maturity date, and high-water mark.

### 3.5 Sequential "No-Regret" Selling & 50/50 Pullback Split (`sequential_seller.py`)
Once a Tax Lot reaches **T+2 Maturity**, the selling brain takes over:

1. **Strict No-Loss Rule:**
   - If a matured lot's current net return (after 1% fees) is negative (`< 0%`), the agent **NEVER panic-sells**. It holds the lot until the price curve recovers into net profit.
2. **Tiered Sequential Profit Booking (Zero Regret):**
   - Selling 100% of a stock at the first small profit causes regret (`afsos`) if the stock rallies further.
   - Instead, Humming Bird sells sequentially in slices of the cycle's starting quantity:
     - **Tier 1 (`+1.5%` Net Profit):** Sell **25%** of shares to lock initial gain.
     - **Tier 2 (`+3.5%` Net Profit):** Sell another **25%** of shares as the curve rises (`++`).
     - **Tier 3 (`+6.0%` Net Profit):** Sell another **25%** of shares, leaving a **25% runner** for massive rallies.
3. **The Pullback 50/50 Split & Recovery Rule:**
   - The agent continuously tracks the **High-Water Mark (peak price)** of every profitable matured lot.
   - If the price starts dropping significantly from its peak (e.g., $\ge 3\%$ pullback from peak) while **still in net profit**:
     - Immediately **sell HALF (50%) of the remaining shares** to secure profit before it evaporates.
     - **Hold the remaining HALF (50%)** in `RECOVERY_HOLD` for long-term recovery.
     - Once the stock recovers back above its anchor/profit wave later on, the exact same sequential selling rule restarts automatically!

---

## 4. The Humming Bird Cockpit & Hermes Agentic Share Assistant

The web interface is designed as a **Real-Time Reactive Agentic Trading Cockpit** for the Bangladesh Share Market:

1. **Financial Telemetry & Accounting Header:**
   - **Total Portfolio Value & Net Revenue/Gain:** Live breakdown across **Today, Weekly, Monthly, and Yearly** horizons.
   - **Trading Volume Metrics:** Total Buy and Total Sell turnover per **Day, Week, and Year**.
   - **BO Account & Brokerage Tracker:** Displays available settled cash, unsettled T+2 cash/shares, BO status, and cumulative 1% brokerage commissions paid.
2. **Three-Tier Watchlist Pulse Cards & Real-Time Filtering:**
   - Tabs for **All**, **Big Giant Stable (GSC)**, **GSC Upper Trends L1**, and **GSC Upper Trends L2**.
   - Displays each tracked company's DSE/StockNow price, last 7 days `+/-` performance, mini curve sparkline, brain state (`BUY_ZONE`, `MID_RANGE`, `SEQUENTIAL_SELL`, `RECOVERY_HOLD`, `CRASH_QUARANTINE`), and custom `Buy %` sliders.
3. **Hermes: True Self-Improving Agent Architecture (Nous Research Style):**
   - **Self-Improving Procedural Memory (`SKILL_*.md`):**
     - Versioned skill documents stored in `backend/hermes/skills/`: `SKILL_gsc_tiers.md`, `SKILL_canary_90_10.md`, `SKILL_sequential_no_regret.md`, `SKILL_stocknow_dse_quirks.md`.
     - *On-Demand Injection:* Matches relevant skills based on query/market event tags, minimizing prompt tokens.
     - *Self-Improvement (`learn_or_patch_skill`):* When the operator teaches a rule or when a 10% canary thesis confirms, Hermes patches or creates skill files and audits revisions in SQLite!
   - **Three-Layer Memory System (`backend/hermes/memory.py`):**
     - *Layer 1 (Operator Profile):* Hasibur's core directives, risk posture (Strict No-Loss), and strategy principles injected every turn.
     - *Layer 2 (Searchable Sessions):* Full transcript memory with cross-turn search so Hermes recalls past conversations.
     - *Layer 3 (Durable Facts & Canary Probes):* Company-specific knowledge (fundamental alerts, historical canary results) recalled whenever that stock is discussed.
   - **State Checkpoints & 1-Click Rollback (`/rollback`):**
     - Before executing any mutating action (quarantine, tier change, allocation update, skill patch), Hermes creates a state checkpoint in SQLite.
     - The operator can command `/rollback` in chat or click the **"Rollback (/rollback)"** button in the Cockpit to instantly restore previous state.
   - **Context Compression:** Older conversation turns are automatically summarized to keep token costs tiny.
   - **User Thesis Intake & Emergency Intervention:**
     - When you alert Hermes of critical news (e.g., *"আজকে এই কোম্পানির অনেক বড় ক্ষতি হয়ে গেছে, ১ মাসের মাথায় দেউলিয়া হয়ে যাবে"*):
       1. **Instant Crash Quarantine:** Hermes puts the stock under quarantine immediately, blocking all future purchases.
       2. **Emergency 90% Profit Lock:** If the stock is currently in profit, Hermes sells 90% of shares immediately to lock profits before catastrophe strikes.
       3. **10% Canary Observation Holding:** Hermes keeps 10% shares as a "canary probe" to verify if the hypothesis actually plays out in reality.
       4. **Proactive Follow-up & Feedback Loop:** Over future market sessions and months, Hermes continuously tracks the stock. If it crashes, Hermes reports back and auto-updates procedural skills! If resilient, Hermes reports safety to restore.
   - **Permissioned Control & Direct Orders:** Command Hermes in natural Bangla, Banglish, or English to change allocations (*"GP-er buy % 25% kore dao"*), move tiers (`set_watchlist_tier`), execute buys/sells, or pause/resume automation.

4. **Zero-Secret-Read & `.env` Isolation Security Architecture (`backend/hermes/secret_guard.py`):**
   - **Strict File Isolation:** Hermes prompt builders, skill managers, and tools are blocked by runtime security assertions from reading `.env`, `.env.*`, `auth.json`, `cookies*`, `browser_profile/`, or `.db` files.
   - **Token Scrubbing (`redact_secrets`):** Automatically scrubs any patterns matching `sk-or-v1-*`, `sk-*`, `Bearer *`, or passwords before any text is stored in memory, logged, or sent to OpenRouter.
   - **Agent Ignore Rules:** `.opencodeignore`, `.cursorignore`, and `.agentignore` in repository root prevent AI coding agents from indexing credentials.

5. **Real-Time Reactive UI (Server-Sent Events / SSE):**
   - The Cockpit connects via `/api/stream` (SSE), pushing instantaneous updates to your browser whenever a cycle executes, a price changes, a checkpoint rollback occurs, or Hermes executes an action—**zero manual page reloads required**.

6. **Real-Time Market Data Analysis (DSE vs StockNow):**
   - **DSE Official Site (`dsebd.org`):** Suffers from 1 to 3-minute ticker latency during market peak hours, lacks public JSON endpoints, relies on HTML scraping, and enforces strict IP rate-limiting.
   - **StockNow (`stocknow.com.bd`):** Provides sub-second reactive WebSocket/JSON feeds, rich 7–30 day historical curves, and an integrated virtual portfolio engine ("Humming Bird") ideal for high-fidelity paper trading before deploying real broker capital.

7. **DSE Market Breadth Visualizers (Market Map Treemap & Top Sectors By Gainer):**
   - **DSE Sector Treemap (Finviz-Style Heatmap):** Squarified treemap grouping all Dhaka Stock Exchange sectors (Textile, Insurance, Engineering, Bank, Fuel & Power, Pharmaceuticals, Food & Allied, etc.). Tile area is proportional to turnover (cr) and color-coded with glowing green/red indicators (Green for `+` gainers, Red for `-` losers, Blue for `0.00%` unchanged).
   - **One-Click Sector Drilldown:** Clicking any sector zooms into that sector's full-screen treemap breakdown with a `< Back` button and sector turnover stats.
   - **Top Sectors By Gainer Stacked Bar Chart:** Interactive stacked bar chart with sectors along the X-axis (vertical labels) displaying Up (green), Down (red), and Unchanged (blue/purple) breadth metrics across DSE.

8. **Pro Trader Cockpit Upgrades:**
   - **TradingView-Style Interactive Crosshairs & Hover Tooltips:** Vertical and horizontal tracking guidelines, date/price inspection, and circular Buy (`B`, green) & Sell (`S`, red) trade execution markers plotted directly on price curves.
   - **Individual Company Deep-Trend View (Modal):** Multi-timeframe trend curves (**7D**, **1M**, **6M**, **1Y**) with horizontal Support Floor (dashed green) and Resistance Ceiling (dashed red) lines, shaded Buy Zone band, and an 8-metric fundamental profile card (P/E, EPS, NAV, Market Cap, Dividend Yield, Paid-up Capital, 52-Week Range, Category).
   - **"What-If" Profit Simulator Slider:** Real-time calculator allowing traders to slide target price up/down and compute simulated gross exit value, 1% DSE brokerage fee, and net pocket cash profit in BDT.
   - **Multi-Theme Switcher (Dark / Light / Terminal):** High-contrast daylight mode for daytime readability, dark slate default, and retro Matrix cyberpunk monospace terminal mode.
   - **DSE Live Market Clock & Countdown:** Topbar live telemetry showing session state (`🟢 DSE OPEN` vs `🔴 DSE CLOSED`) with real-time countdown to next session opening or market close.

9. **Master Automation Controller & Dual Ingestion Mode (`Background Polling` vs `Side-by-Side Live`):**
   - **Master Buy/Sell Automation Switch:** A dedicated toggle in the Cockpit header (`AUTOMATION ON` vs `AUTOMATION OFF / PAUSED`). Disables evaluation cycles and protects capital on demand without server restart.
   - **Dual Ingestion Mode Architecture:**
     - **Method A (`BACKGROUND_POLLING`):** Lightweight periodic data polling (configurable 30s to 300s, default 120s) with interval pill selector (`30s`, `60s`, `120s`, `180s`). Ideal for low-resource VPS, battery saving, or stealth operation.
     - **Method B (`SIDE_BY_SIDE_LIVE`):** Headed, persistent Playwright browser context running alongside the operator on desktop, allowing live DOM/CDP telemetry inspection and immediate event triggers.
   - **Hermes Chat Orchestration:** Operator can command in chat (*"Switch to side by side mode"*, *"Background polling 60s koro"*, *"Turn off buy sell automation"*), with automatic state checkpointing for 1-click `/rollback`.
   - **AST Codebase X-Ray Radar (`CODEBASE_MAP.md`):** Zero-dependency AST scanner (`scripts/generate_code_map.py`) that indexes all classes, methods, FastAPI routes, DOM elements, and code complexity metrics.

---

## 5. System Architecture & Tech Stack

```text
+-----------------------------------------------------------------------------------+
|                   HUMMING BIRD WEB COCKPIT (Dark-Mode Terminal)                   |
|  [Telemetry: Today/Wk/Mo/Yr Gain] [T+2 Buckets A/B/C] [7-Day Company Pulse Cards] |
|  [Custom Rules & Buy % Controls]                 [Hermes AI Side-Chat (Bangla/EN)]|
+-----------------------------------------+-----------------------------------------+
                                          | HTTP / REST / WebSockets
                                          v
+-----------------------------------------------------------------------------------+
|                        FASTAPI QUANT & AUTOMATION BACKEND                         |
|                                                                                   |
|  +-----------------------+  +------------------------+  +----------------------+  |
|  |   CurveAnalyzer       |  |   SequentialSeller     |  |   T2Ledger (A/B/C)   |  |
|  | - 7-30d Range Reader  |  | - 1% Fee Exact Math    |  | - Sun-Thu Calendar   |  |
|  | - Sector Rules        |  | - 25% Tiered Scaling   |  | - Tax-Lot Maturity   |  |
|  | - Crash/Vanish Guard  |  | - 50/50 Pullback Split |  | - Exposure Caps      |  |
|  +-----------+-----------+  +------------+-----------+  +-----------+----------+  |
|              \                           |                         /              |
|               v                          v                        v               |
|  +-----------------------------------------------------------------------------+  |
|  |                    AutoTrader Deterministic Orchestrator                    |  |
|  +-------------------+-------------------------------------+-------------------+  |
+----------------------|-------------------------------------|----------------------+
                       |                                     |
                       v                                     v
+---------------------------------------------+   +---------------------------------+
|      MODULAR BROKER ADAPTER LAYER           |   |    SQLITE / SUPABASE LEDGER     |
| - Sprint 1: Paper / StockNow Seed Engine    |   | - CompanyProfile & Custom Rules |
| - Sprint 2: Playwright Persistent Context   |   | - TaxLots (T+0, T+1, T+2)       |
|   & XHR/DOM Sync for `stocknow.com.bd`      |   | - TradeLogs & Audit History     |
| - v0.3: LankaBangla / Shanta Adapters       |   +---------------------------------+
+---------------------------------------------+