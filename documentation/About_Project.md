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
Not all DSE companies behave the same way. Humming Bird groups stocks into three structured tiers based on the operator's real StockNow workflow:

1. **Big Giant Stable Companies (GSC — Master Observation Pool):**
   - Historically established market leaders with solid fundamentals, decades of operational history, and strong institutional backing (`ACI`, `BANKASIA`, `DHAKABANK`, `FUWANGCER`, `IFIC`, `NPOLYMER`, `PRIMEBANK`, `PUBALIBANK`, `SPCERAMICS`).
   - *Key Concept:* Long-term survival stability, NOT that the stock is currently on a profit curve. Being in `GSC` means the risk of vanishing overnight is virtually non-existent.
   - *Trading Rule:* Hermes continuously monitors and analyzes all `GSC` companies to learn their curve character, but `AutoTrader` **skips auto-buying** from base `GSC` (`WAIT_OBSERVATION_ONLY`) unless the stock is promoted to `GSC_L1` or `GSC_L2`.
2. **GSC Upper Trends L1 (GSC_L1 — Primary Active Trading List):**
   - GSC companies that were previously in a downward curve and are now visibly turning upward on their genuine company recovery curve (`BANKASIA`, `MATINSPINN`).
   - *Key Concept:* Filters out 1-day market noise (red today, green tomorrow). Focuses on genuine multi-week/multi-month comeback recovery waves.
   - *Trading Rule:* Given **Priority #1** by `AutoTrader` when allocating available buying capital.
3. **GSC Upper Trends L2 (GSC_L2 — Secondary Active Trading List / Fluctuation Scalp):**
   - GSC companies whose macro curve is not yet fully stable, but are turning green in short-term fluctuation (`DHAKABANK`).
   - *Key Concept:* Traded like HFT/swing scalps: enter as green momentum starts and sell while still green to profit from short-term market oscillation waves.
   - *Trading Rule:* Given **Priority #2** by `AutoTrader` when evaluating buy candidates.
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
3. **Hermes: Official Nous Research Runtime Integration (`plugins/humming_bird/`):**
   - **Official Skill Architecture (`plugins/humming_bird/skills/<skill>/SKILL.md`):**
     - Versioned skill documents stored in official Hermes layout: `canary_90_10/SKILL.md`, `gsc_tiers/SKILL.md`, `sequential_no_regret/SKILL.md`, `stocknow_dse_quirks/SKILL.md`.
     - *On-Demand Registration:* Registered into Hermes runtime via `ctx.register_skill()`, matching user intents with minimal prompt overhead.
     - *Autonomous Learning:* Hermes natively learns procedural skills through its built-in runtime as trading patterns and canary outcomes confirm.
   - **Persistent Memory Architecture (`memories/USER.md` & `memories/MEMORY.md`):**
     - *Operator Directives (`USER.md`):* Operator risk posture (Strict No-Loss), trading hours, and capital allocations stored in Hermes' native user profile.
     - *Long-Term Working Memory (`MEMORY.md` & SQLite FTS5):* Curated facts, company alerts, and historical canary outcomes indexed for fast contextual retrieval across sessions.
   - **State Checkpoints & 1-Click Rollback (`/rollback`):**
     - Before executing mutating actions (quarantine, tier change, allocation update), the kernel creates atomic checkpoints (`KernelStateCheckpoint`).
     - The operator can command `/rollback` in chat or click the **"Rollback (/rollback)"** button in the Cockpit to instantly restore previous state.
   - **Context Compression & Script-Gated Cron Jobs:**
     - Older conversation turns are automatically compressed by Hermes context compression.
     - Scheduled cron jobs run with `--script check_dse_market_open.py`, emitting `wakeAgent: false` on weekends and off-hours to avoid waking the LLM.
   - **User Thesis Intake & Emergency Intervention:**
     - When you alert Hermes of critical news (e.g., *"আজকে এই কোম্পানির অনেক বড় ক্ষতি হয়ে গেছে, ১ মাসের মাথায় দেউলিয়া হয়ে যাবে"*):
       1. **Instant Crash Quarantine:** Hermes puts the stock under quarantine immediately, blocking all future purchases.
       2. **Emergency 90% Profit Lock:** If the stock is currently in profit, Hermes sells 90% of shares immediately to lock profits before catastrophe strikes.
       3. **10% Canary Observation Holding:** Hermes keeps 10% shares as a "canary probe" to verify if the hypothesis actually plays out in reality.
       4. **Proactive Follow-up & Feedback Loop:** Over future market sessions and months, Hermes continuously tracks the stock. If it crashes, Hermes reports back and records observations in persistent memory! If resilient, Hermes reports safety to restore.
   - **Permissioned Control & Direct Orders:** Command Hermes in natural Bangla, Banglish, or English to change allocations (*"GP-er buy % 25% kore dao"*), move tiers (`hb_set_tier`), execute buys/sells (`hb_place_order`), or pause/resume automation (`hb_automation_set`).

4. **Zero-Secret Isolation & Hardened Profile Boundary (`backend/secret_guard.py` & Hermes Profile):**
   - **Profile Toolset Hardening:** The dedicated `hummingbird` profile explicitly disables `terminal`, `file`, `code_execution`, and `browser` toolsets (`agent.disabled_toolsets` and `platform_toolsets`). Hermes physically lacks `read_file`, `write_file`, and `terminal` tools, enforcing a hard architectural boundary where the agent cannot inspect workspace `.env`, database files, or shell commands.
   - **Manual Approvals:** Configured with `approvals.mode: manual` to fail closed against any unapproved actions.
   - **Token Scrubbing (`backend/secret_guard.py`):** In-kernel regex utility that automatically scrubs patterns matching `sk-or-v1-*`, `sk-*`, `Bearer *`, or passwords before text is logged or stored.
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
   - **Theme Switcher (Dark / Light):** High-contrast daylight mode for daytime readability and sleek dark slate default with clean card borders and contrast.
   - **Continuous Smooth Spline Curves:** Pure continuous cubic bezier spline curves without static point dots, paired with continuous pixel-level hover crosshairs and subtle Buy/Sell execution markers.
   - **DSE Live Market Clock & Countdown:** Topbar live telemetry showing session state (`🟢 DSE OPEN` vs `🔴 DSE CLOSED`) with real-time countdown to next session opening or market close.

9. **Master Automation Controller & Ingestion Pipeline:**
   - **Dual Ingestion Mode Architecture:**
     - **Method A (`BACKGROUND_POLLING`):** Lightweight periodic data polling (configurable 30s to 300s, default 120s) with interval pill selector and range slider. Ideal for low-resource VPS, battery saving, or stealth operation.
     - **Method B (`ONSCREEN_LIVE`):** Headed, persistent Playwright browser context running alongside the operator on desktop (Onscreen Live Mode), allowing live DOM/CDP telemetry inspection and immediate event triggers.
   - **Hermes Chat Orchestration:** Operator can command in chat (*"Switch to onscreen live mode"*, *"Background polling 60s koro"*, *"Turn off buy sell automation"*), with automatic state checkpointing for 1-click `/rollback`.

10. **Unified Continuous Dashboard, ScrollSpy & Dedicated Settings Page:**
    - **4 Scrollable Dashboard Sections + 5th Separate Settings View:**
      1. `#overview`: Financial telemetry, rebased Watchlist pulse curve, 3-Bucket rolling capital, and Decision stream.
      2. `#watchlist`: Multi-tier company watchlist, Position inspector with maturity lots, DSE Market Map Treemap with Finviz heat scale, and Top Sectors by Gainer chart.
      3. `#rules`: Strategy Rules, "What-If" profit simulator, custom buy cap form, sequential profit tiers (+1.5%, +3.5%, +6.0%), 50/50 pullback setting, and Canary Theses observation board.
      4. `#ledger`: Accounting periods (Overall, Today, Week, Month, Year) and full FIFO tax lot execution table.
      5. `#settings`: Dedicated page for Master Buy/Sell automation switch, Method A vs Method B ingestion pipeline, polling cadence slider, read-only Hermes AI Brain card, fee structure & settlement rules, and notification credentials.
    - **ScrollSpy Left Nav Rail Sync:** Seamlessly tracks operator scrolling across `#overview`, `#watchlist`, `#rules`, and `#ledger` in the main workspace and dynamically highlights the active section icon.
    - **Sticky Top Navbar:** Locked mission-critical navigation with live DSE market clock & countdown, two-way ingestion mode toggle, master engine controls, and theme switcher, allowing all dashboard sections to slide cleanly underneath.
    - **Fixed Viewport Lock Architecture:** Locked outer viewport (`height: 100vh; overflow: hidden;`) with middle `.workspace` scrolling independently (`height: 100vh; overflow-y: auto;`). Left nav rail and right Hermes assistant stay 100% viewport-fixed at all times, never scrolling off screen.
    - **Continuous Smooth Curves Without Point Dots:** Pure continuous cubic bezier curves without static session dots, paired with continuous pixel-level hover interpolation so crosshairs glide smoothly with pixel precision.
    - **Rebuilt Hermes `[Changes]` Tab as System & Rule Diff Review:** Visual GitHub/IDE-style structured Before vs. After diff cards (`.diff-card`) featuring red deleted lines (`[-] Previous`) and green added lines (`[+] Updated`), actor badges, timestamps, and 1-click `/rollback`.
    - **Settings Page Complete Overhaul:**
      - *Telemetry Ingestion Pipeline Card:* Interactive Method A (Background HTTP Polling) vs Method B (Onscreen Live Mode CDP) selector tiles with status pills, smooth polling interval slider (30s to 300s), and quick preset cadence pills (30s Hyper, 60s Fast, 120s Standard, 180s Relaxed).
      - *System Notifications & Telegram Bot Card:* Masked credential form for Telegram Bot Token & Chat ID with toggleable password visibility and one-click save.
      - *Market Clearing & Settlement Rules Card:* Fee structure (0.50% buy, 0.50% sell, +1.005% gross hurdle) and T+2 settlement rolling bucket explanation.
      - *System & Security Card:* Consolidated technical badges (Realtime SSE status, Demo/Paper mode indicator, and optional session API tokens).
    - **Read-Only Hermes AI Brain Card:**
      - Live telemetry synchronized from `~/.hermes/profiles/hummingbird` via `GET /api/hermes/bridge/state`.
      - Displays Primary Inference Model (e.g. `gemini-3.1-flash-lite`, `mimo-v2.6-pro`), configured fallback provider chain from `config.yaml` (`fallback_providers`), and the exact provider/model that served the last conversation turn.
      - Models, fallbacks, and API keys are managed exclusively through Hermes native CLI (`hermes model`, `hermes fallback add`, `config.yaml`).
    - **Exhaustive Light Mode Daylight Uniformity:** Complete elimination of hardcoded dark background artifacts across tables, cards, canvases, settings, and sidebars, featuring 50% lighter pastel treemap tiles and dark legible text contrast.
    - **Developer Productivity & Instant Local Reload:** Disabled aggressive static asset browser caching (`Cache-Control: no-cache, no-store, must-revalidate`) in `DevStaticFiles` and root cockpit endpoint so frontend UI changes reflect immediately upon browser refresh (`F5`) without cache clearing.

11. **Hermes IDE Resizable Sidebar, Topics & Antigravity History:**
    - **Synchronized Viewport-Grid Resizing (`col-resize`):** Smooth, bi-directional width adjustment (280px–640px) dynamically resizing the `.app-shell` 3rd column track via CSS variable `--hermes-width`, completely eliminating off-screen rightward overflow or clipping while persisting dimensions in `localStorage`.
    - **Custom Upward-Opening Model Drop-up Menu:** Bottom status bar model selector opens upward smoothly above the chat composer with zero overflow clipping, active model checkmarks, and instant OpenRouter switching.
    - **Restored Compact Pill Quick-Prompts:** Clean, horizontal inline quick prompts (`Portfolio status ↗`, `Alert bankruptcy threat ⚡`, `Restore company ↺`) with subtle borders and teal hover accents.
    - **Sub-Pixel Centered Chat Send Button:** Reset default browser button padding and aligned send icon to the absolute geometric center.
    - **Decluttered Trader Interface:** Stripped repetitive, redundant "AGENTIC" status badges and visual dot artifacts across Hermes for a focused, institutional-grade terminal aesthetic.
    - **Minimize / Collapse Mode:** One-click minimize button with a floating reopen pill (`✦ Hermes`) for maximum dashboard screen real estate.
    - **Multi-Conversation Topic Manager (`+ New Conversation`):** Human strategy & topic separator (`HermesConversationThread`), enabling distinct conversation threads while Hermes retains unified cross-topic memory and self-improving procedural skills.
    - **High-Performance Snapshot Engine:** Precomputed $O(N)$ calendar date slices in `portfolio.py`, eliminating the 145,000+ date increment loop and resolving page load delays.
    - **AST Codebase X-Ray Radar (`CODEBASE_MAP.md`):** Zero-dependency AST scanner (`scripts/generate_code_map.py`) that indexes all classes, methods, FastAPI routes, DOM elements, and code health radar.

12. **Sprint 2: StockNow Live Adapter & Real-Time Sync Engine:**
    - **Step 2.1 (Persistent Playwright Session & Auto-Login):**
      - Launches Chromium with persistent profile in `~/.hummingbird_stocknow_profile` (strictly outside OneDrive to avoid cloud sync LevelDB locks).
      - Zero-secret auto-login helper (`ensure_authenticated`) with masked phone display and `SecretGuard` protection.
      - Passive XHR/JSON sniffer capturing all background market API responses without additional network overhead.
    - **Step 2.2 (Live DSE Quote & 7–30 Day Curve Sync):**
      - Dedicated sync engine (`stocknow_market_sync.py`) extracting quotes and historical curves from sniffer cache or active DOM.
      - Synchronizes live prices into SQLite `CompanyProfile` records, reconciling curve observations and updating `source="STOCKNOW_LIVE"`.
      - REST API endpoint `POST /api/stocknow/sync-market` broadcasting realtime portfolio updates via SSE.
      - Hermes conversational tool `control_stocknow_session` (*"Launch StockNow browser"*, *"StockNow login check koro"*, *"Sync live market prices"*).
      - 1-Click UI controls in Settings (`Launch Live Browser`, `Check / Auto-Login`, `Sync Live Prices`).
    - **Step 2.3 ("Humming Bird" Virtual Portfolio & Holdings Sync):**
      - Dedicated portfolio extractor and reconciler (`stocknow_portfolio_sync.py`) locating the **"Humming Bird"** virtual portfolio.
      - Synchronizes virtual cash balance and holdings into SQLite `TaxLot` and `TradeLog` records with rotating bucket assignment (`A`, `B`, `C`).
      - Preserves active sequential selling tier progression (`next_tier`, `peak_price`, `phase`, `recovery_anchor`, `cycle_base_qty`) during portfolio sync.
      - CheckpointManager state snapshot enabling complete 1-click `/rollback` restoration.
      - Zero-drift paisa-level ledger balancing guaranteeing `assert_ledger` 100% compliance.
      - REST endpoint `POST /api/stocknow/sync-portfolio` broadcasting real-time snapshot via SSE.
      - Hermes conversational command (*"Sync Humming Bird portfolio"*, *"Humming Bird portfolio sync koro"*).
      - 1-Click UI action button in Settings (`Sync "Humming Bird" Portfolio`).
    - **Step 2.4 (Automated Virtual Order Execution on StockNow "Humming Bird"):**
      - Dedicated order executor (`stocknow_executor.py`) supporting live browser DOM automation (`BrowserTransport`) and direct async HTTP API (`ApiTransport`).
      - Idempotency deduplication preventing duplicate trade executions on retries.
      - Delegated `StockNowAdapter.execute_order()` tracking `last_order_receipt` in telemetry status.
      - REST API endpoint `POST /api/stocknow/execute-order` with CheckpointManager state snapshot for 1-click `/rollback`.
      - Strict T+2 maturity lock and 1% fee math enforcement (rejecting immature and net-loss sells under Strict No-Loss policy).
      - Hermes conversational Buy and Matured Sell execution (*"Buy 10 GP"*, *"GP 10 ta share kine felo"*, *"Sell 5 SQURPHARMA"*) attaching StockNow virtual receipts.
    - **Step 2.5 (DSE Market-Hours Auto-Scheduler 10:00 AM – 2:30 PM Sun–Thu):**
      - Dedicated async background scheduler (`backend/engine/scheduler.py`, `DSEMarketScheduler`).
      - DSE market hours gate (`is_dse_market_open`) enforcing trading windows strictly Sunday–Thursday 10:00 AM – 2:30 PM (`Asia/Dhaka`), pausing on weekends and official DSE holidays.
      - Live quote sync from StockNow, execution of AutoTrader paper cycle, and SSE real-time broadcast.
      - API endpoints: `GET /api/stocknow/scheduler`, `POST /api/stocknow/scheduler` (`start`, `stop`, `tick_now`).
      - Hermes conversational commands (*"Start DSE scheduler"*, *"Stop scheduler"*, *"Run scheduler tick now"*).
    - **Step 2.7 (Real StockNow Portfolio #164580 & 3-Tier Watchlist Implementation):**
      - Replaced dummy fixtures with the operator's real StockNow "Humming Bird" portfolio (`#164580`) in the runtime database.
      - Settled Cash: `91,236.00 BDT`, Open Basis: `30,056.71 BDT`, Total Book Assets: `121,292.71 BDT` reconciled to exact 0.00 paisa drift.
      - Active matured holdings: `BANKASIA` (294 @ 17.09 cost), `IBNSINA` (16 @ 304.31 cost), and `MATINSPINN` (206 @ 97.89 cost).
      - Dedicated "Humming Bird Active Holdings (StockNow #164580)" card in `#overview` with live summary pills, detailed holdings table, net return percentages, and summary totals row.
      - AutoTrader buy ordering prioritizes `GSC_L1` #1, `GSC_L2` #2, and skips base `GSC` observation pool (`WAIT_OBSERVATION_ONLY`).
      - Encoded operator domain knowledge into Hermes skill `SKILL_gsc_tiers.md` (v1.1.0).
    - **Step 2.8 (Live Playwright Automation for /login, /favorites, /show, /ledger, /buy & /sell):**
      - Exact login flow: `https://www.stocknow.com.bd/login?nextUrl=/portfolios` automatically authenticating with operator credentials loaded securely from environment variables (`STOCKNOW_MOBILE`, `STOCKNOW_PASSWORD`), and "Remember mobile and password" checkbox.
      - Dynamic portfolio discovery: scrapes `/portfolios` to locate "Humming Bird", extracts summary telemetry (`Balance`, `Sell Value`, `Gain/Loss Today`, `Unrealized Gain/Loss`), and binds `bound_portfolio_id = "164580"`.
      - 3-list favorites extraction: maps dropdown options ("Giant Stable Companies" -> `GSC`, "GSC Upper Trends L1" -> `GSC_L1`, "GSC Upper Trends L2" -> `GSC_L2`) and syncs live quotes, change %, volume, and fundamentals to SQLite.
      - Holdings (`/show`) and transaction ledger (`/ledger`) scraper: parses `DD/MM/YY` dates (e.g. `02/11/26` -> `2026-11-02`) so T+2 maturity aligns with real purchase dates.
      - Order execution forms (`/buy` and `/sell`): automated field selection under Item 1 with `0.5%` commission, clearing auto-filled quantities on SELL to submit precise slice sizes.
      - Active Holdings quick actions: 1-click 25% slice sell on profitable matured holdings (`BANKASIA`, `MATINSPINN`) and locked `No-Loss Hold Guard` on underwater holdings (`IBNSINA`).
      - AutoTrader integration: dispatches every automated Buy and Sequential Tier Sell through `adapter.execute_order` with `0.5%` commission.
    - **Step 2.9 (Steps 1–10 Production Architecture & Autonomous Resiliency Foundation):**
      - **Target Portfolio Configuration (Step 1):** Configurable `STOCKNOW_LIVE_PORTFOLIO_ID=164580` and `STOCKNOW_TEST_PORTFOLIO_ID` with hard allowlist enforcement, isolated SQLite ledgers, tax lots, and independent daily budgets.
      - **Write Contract Specification (Step 2):** HAR inspection of StockNow virtual broker write APIs (`/buy`, `/sell`), documented in `STOCKNOW_SITE_MAP.md` with hard test-only write guards.
      - **Async StockNowAPI Transport (Step 3):** High-performance `httpx.AsyncClient` adapter (`stocknow_api.py`) with memory-only token storage, margin-based auto-relogin, ETag caching, and typed schema errors.
      - **Unified Executor & Dual Transports (Step 4):** `StockNowExecutor` dynamically selecting `ApiTransport` (Background) or `BrowserTransport` (Onscreen), zero fallback to paper, checkpoint state rollbacks, and explicit trade date T+2 calculations.
      - **Direct API Market Sync (Step 5):** Direct API sync for `/instruments`, `/user/lists`, 7–15 session candles, and portfolio reconciliation, with DOM sync retained as an Onscreen cross-check.
      - **Single-Writer Master Switch & Run Modes (Step 6):** Master `ON / OFF` control, separate Emergency Kill switch, run modes `Onscreen Live` vs `Background 24/7` with `Go Background` / `Go Onscreen` handoffs, and labeled `PREVIEW` execution when OFF.
      - **Autonomous Reliability & Safety (Step 7):** Windows Task Scheduler autostart (`scripts/install_autostart.ps1`), SQLite minute heartbeat, Telegram dead-man alerts & daily summary (14:45), 3-failure circuit breaker, and rotating secret-free logs.
      - **UI Alignment & 4 Balanced Settings Cards (Step 8):** Clean labels `Live Hours` and `Test Mode`, topbar unified status chip, 4 balanced cards in Settings (Automation, StockNow Connection, Safety Caps, Hermes Brain) plus collapsed Advanced card.
      - **Portfolio Header Badge & Watchlist Status (Step 9):** `LIVE STOCKNOW <name> #<id>` badge with drift warning, watchlist status pills (`LIVE`, `LAST CLOSE`, `STALE`, `NO DATA`) with direct retry link, and ledger tags (`STOCKNOW RECEIPT` vs `PAPER FILL`).
      - **Hermes Chat Order Preview Card (Step 10):** Interactive chat cards rendered on `hb_place_order` previews displaying symbol, side badge, quantity, price, 0.5% fee, mode, portfolio, and cap usage breakdown with Confirm / Cancel buttons (zero typed parameters), verified receipt state, and red `live submission failed: <reason>` with guaranteed no ledger change.

---

## 5. System Architecture & Tech Stack

```text
+-------------------------------------------------------------------------------------------------------+
|                                    HUMMING BIRD OPERATOR TERMINAL                                     |
|  [Left Nav Rail]      [Multi-View Workspace Containers]                   [Hermes IDE Copilot]        |
|  - 1: #overview       - View 1: Overview (Telemetry, Pulse, Buckets, Strm)- Sticky Viewport (100vh)   |
|  - 2: #watchlist      - View 2: Watchlist & DSE Market Treemap Heatmap    - Model Badge (Hermes state)|
|  - 3: #rules          - View 3: Strategy Rules, What-If & Canary Theses   - [💬 Chat] Tool-Call Cards |
|  - 4: #ledger         - View 4: Trade Ledger & FIFO Tax Lots              - [📂 Topics] Strategy Tabs |
|  - 5: #settings       - View 5: Dedicated Settings & Automation Controls  - [⚡ Changes] Diff Review  |
|                       - Independent Scrolling Workspace (100vh)           - [🧠 Skills] Hermes Native |
+---------------------------------------------------+---------------------------------------------------+
                                                    | HTTP REST / SSE Stream (/api/stream)
                                                    v
+-------------------------------------------------------------------------------------------------------+
|                                  FASTAPI QUANT & AUTOMATION BACKEND                                   |
|                                                                                                       |
|  +-------------------------+  +--------------------------+  +--------------------------------------+  |
|  |     CurveAnalyzer       |  |     SequentialSeller     |  |          T2Ledger (A/B/C)            |  |
|  | - 7-30d Range Reader    |  | - 1.00% Net Fee Math     |  | - Sunday-Thursday Working Calendar   |  |
|  | - Sector Classification |  | - 25% Tiered Profit Lock |  | - T+0 -> T+1 -> T+2 Maturity Engine  |  |
|  | - Crash/Vanish Guard    |  | - 50/50 Pullback Split   |  | - Tax-Lot Cost Basis & Settlement    |  |
|  +------------+------------+  +------------+-------------+  +-------------------+------------------+  |
|               \                            |                                    /                     |
|                v                           v                                   v                      |
|  +-------------------------------------------------------------------------------------------------+  |
|  |                              AutoTrader Deterministic Orchestrator                              |  |
|  |             - Atomic Evaluation Cycles  - Idempotency Locks  - Duplicate Trade Guards           |  |
|  +-------------------+---------------------------------------------------------+-------------------+  |
|                      |                                                         |                      |
|                      v                                                         v                      |
|  +---------------------------------------+             +-------------------------------------------+  |
|  |     OFFICIAL HERMES INTELLIGENCE      |             |       MODULAR DATA & ADAPTER LAYER        |  |
|  | - Nous Hermes Agent (~/.hermes)       |             | - Dual Ingestion Pipeline:                |  |
|  | - Humming Bird Plugin (22 Tools)      |             |   * Method A: Background HTTP Polling     |  |
|  | - Procedural Skills (4 SKILL.md)      |             |   * Method B: Playwright Headed CDP Live  |  |
|  | - Real Hermes Cron (Asia/Dhaka)       |             | - StockNowAdapter (DSE Fixtures & Sync)   |  |
|  | - SSE Chat Bridge & Kernel API        |             | - Broadcaster (SSE Realtime Stream)       |  |
|  +-------------------+-------------------+             +---------------------+---------------------+  |
+----------------------|-------------------------------------------------------|------------------------+
                       |                                                       |
                       v                                                       v
+-------------------------------------------------------------------------------------------------------+
|                                 SQLITE TRANSACTIONAL LEDGER (WAL MODE)                                 |
|  - PortfolioState & Automation Config     - CustomRule & CompanyProfile     - TaxLots (T0, T1, T2)   |
|  - TradeLog & Financial Ledgers           - CanaryThesis Observation Theses - KernelStateCheckpoints |
|  - KernelAuditLogs & RuleAudits           - SingleWriterTradingLock         - DecisionLogs           |
+-------------------------------------------------------------------------------------------------------+
```

---

## 6. Official Hermes Runtime Integration & Streaming SSE Bridge

Humming Bird uses the official **Nous Research Hermes Agent** (`hermes-agent`) as its autonomous intelligence layer, keeping the local repository dedicated strictly to the trading kernel, StockNow adapters, and Cockpit UI.

### Integration Path & SSE Chat Bridge (`backend/hermes_bridge.py`)
- **Gateway Server & Streaming SSE:** The Cockpit connects via `backend/hermes_bridge.py` directly to the running Hermes Gateway API server (`http://127.0.0.1:8642/v1/chat/completions`) streaming over standard OpenAI-compatible SSE. If the gateway server is offline, the bridge returns a clear error instructing the operator to start it. `--yolo` and `--in` have been removed to preserve profile security boundaries.
- **Granular Streaming Events:** Emits standard Server-Sent Events (`tool_use`, `tool_result`, `text`, `done`, `error`) directly to the web UI.
- **Tool-Call Inspection Cards:** The Cockpit chat interface dynamically renders interactive collapsible cards showing the tool name, JSON input arguments, running/done status badge, and execution output.
- **Provider & Model Configuration:** Model selection and API keys are managed exclusively in Hermes' native runtime configuration (`~/.hermes/config.yaml`), completely isolated from repository source code. The active model (`gemini-3.1-flash-lite`, `mimo-v2.6-pro`, etc.) is read dynamically by `GET /api/hermes/bridge/state` and displayed in the sidebar badge.

---

## 7. Humming Bird Plugin & Trading Kernel API (`plugins/humming_bird/` & `backend/kernel_api.py`)

Trading logic and market execution are exposed to Hermes via an official standalone plugin and an isolated local kernel service.

### Humming Bird Plugin (`plugins/humming_bird/`)
Following the official Hermes Agent plugin architecture (`plugin.yaml`, `__init__.py` with `register(ctx)`, `tools.py`, `schemas.py`):
1. **Read-Only Tools:**
   - `hb_portfolio`: Returns cash, gross equity, net liquidation value, unrealized P/L, and holding summaries.
   - `hb_watchlist`: Inspects companies filtered by tier (`GSC`, `GSC_L1`, `GSC_L2`).
   - `hb_inspect_curve`: Calculates 7–30 day trend slope, support levels, resistance, and swing bounds.
   - `hb_market_open`: Checks DSE market hours, holidays, and trading day status.
   - `hb_canaries`: Returns active 90/10 canary probe theses and price observations.
   - `hb_lots`: Inspects individual tax lots across settlement buckets (A, B, C) and T+2 maturity.
2. **Write & Order Tools:**
   - `hb_set_tier`: Promotes or demotes symbols between `GSC`, `GSC_L1`, and `GSC_L2`.
   - `hb_set_allocation`: Updates per-symbol buy allocation percentages (capped at 100% total).
   - `hb_quarantine_canary`: Initiates 90/10 emergency profit lock with canary probe on insolvency threats.
   - `hb_restore_quarantine`: Releases a stock from quarantine back into active watchlist rotation.
   - `hb_sync`: Synchronizes live market prices, favorites, or portfolio #164580 holdings from StockNow.
   - `hb_place_order`: Places virtual orders with `dry_run=true` by default, requiring explicit operator confirmation, and validating market hours gates.
   - `hb_rollback_last`: Reverts the last state checkpoint atomically.
3. **Engine & Automation Control Tools:**
   - `hb_automation_get`: Inspects master buy/sell switch, ingestion mode (`BACKGROUND_POLLING`, `ONSCREEN_LIVE`), and polling interval.
   - `hb_automation_set`: Updates automation switches, polling cadence, and ingestion pipeline parameters.
   - `hb_scheduler`: Starts, stops, or inspects status of the background evaluation cycle scheduler.
   - `hb_run_cycle`: Triggers an immediate deterministic evaluation cycle (`dry_run=true` by default).
   - `hb_stocknow_session`: Manages persistent Playwright browser session (`launch`, `status`, `login`).
4. **Trading Mode & Risk Caps Tools:**
   - `hb_mode_get`: Inspects active trading mode (`LIVE_HOURS` vs `TEST_OFFHOURS`).
   - `hb_mode_set`: Switches trading mode with operator confirmation guard.
   - `hb_caps_get`: Fetches current risk caps, daily budget, and kill switch status.
   - `hb_caps_set`: Lowers caps autonomously; raising limits requires operator confirmation in Cockpit UI.
5. **Official Procedural Skills (`plugins/humming_bird/skills/`):**
   - Encoded as `<name>/SKILL.md` with official `agentskills` YAML frontmatter and registered via `ctx.register_skill`:
     - `canary_90_10`: Emergency threat response and 90/10 split execution.
     - `gsc_tiers`: 3-tier GSC watchlist rules and turnaround priority.
     - `sequential_no_regret`: Multi-tier profit locking, 50/50 pullback split, and T+2 rolling ledger.
     - `stocknow_dse_quirks`: Virtual portfolio #164580 constraints, latency nuances, and market session rules.

### Deterministic Trading Kernel API (`backend/kernel_api.py`)
- **Isolation:** Bound strictly to `127.0.0.1` and protected by `X-Kernel-Token` matching `KERNEL_TOKEN` from the environment.
- **Zero Agent Imports:** Contains no LLM, agent, prompt, or external network code.
- **Audit & Atomic Checkpoints:** Every state mutation takes a `KernelStateCheckpoint` snapshot and writes a structured `KernelAuditLog` entry before modifying state.
- **Strict Invariants:** Enforces T+2 maturity, strict no-loss (>= +1.005% gross hurdle after round-trip 1% commission), single-writer lock, and target portfolio #164580 constraint.

### Unified Supervisor & Launcher (`run.py`)
- **One-Command Orchestration:** Starts Hermes Gateway daemon (`127.0.0.1:8642`) with profile `hummingbird`, waits for HTTP 200 on `/health`, and launches FastAPI Uvicorn on `127.0.0.1:8000`. Wrappers `run.bat`, `run.sh`, and `package.json` delegate to `run.py`.
- **Environment & Profile Protection:** Resolves Windows `HERMES_HOME` path bug and enforces profile isolation.
- **Process Supervision:** Restarts Hermes Gateway up to 3 times on unexpected process exit; cleanly terminates child processes on `Ctrl+C` (SIGINT/SIGTERM).

### Dual Trading Modes (`LIVE_HOURS` vs `TEST_OFFHOURS`)
- **`LIVE_HOURS` (Default):** Strictly enforces Sunday-Thursday 10:00–14:30 Asia/Dhaka trading gate in plugin pre-tool hooks, kernel `post_order`, and scheduler ticks.
- **`TEST_OFFHOURS`:** Bypasses *only* the market hours gate for continuous off-hours end-to-end integration testing. T+2 maturity, no-loss hurdle, fees, risk caps, and single-writer concurrency locks remain 100% enforced.
- **Operator Safety Guard:** Switching to `LIVE_HOURS` or `TEST_OFFHOURS` requires explicit operator confirmation via `#trading-mode-toggle` in the UI or `hb_mode_set`.

### Enforced Risk Limits & Kernel Caps
- **Database-Enforced Constraints:** Stored in SQLite (`portfolio_state`): `max_order_bdt` (e.g. 20,000 BDT), `max_symbol_bdt` (e.g. 50,000 BDT), `daily_budget_bdt` (default 4,000 BDT), `max_orders_per_day` (20), and a global `kill_switch_active`.
- **Single-Writer Concurrency Lock:** AutoTrader evaluation cycles and Hermes order execution share an exclusive transactional lock (`SingleWriterTradingLock`).
- **Autonomous vs Operator Boundaries:** Hermes may lower caps autonomously; raising limits requires cockpit operator confirmation. Rejected orders record structured `DecisionLog` and `KernelAuditLog` entries. Advisory rules taught in chat remain non-binding until applied via `hb_caps_set` or `hb_set_allocation`.

### Verified Order Execution Path & Reconciled Drift
- **End-to-End Execution Pipeline:**
  1. Acquire single-writer trading lock (`/k/order`).
  2. Take atomic state checkpoint (`KernelStateCheckpoint`).
  3. Run preflight verification (T+2, no-loss hurdle, risk caps, daily budget, market hours gate).
  4. Call `StockNowAdapter.execute_order` on live browser session (or mock adapter in dry run).
  5. Verify execution fill by inspecting the StockNow ledger receipt.
  6. Update local SQLite transactional ledger *only* after receipt matches.
  7. On any fill failure or timeout, automatically roll back to the state checkpoint.
- **Zero-Drift Ledger Reassurance:** Verifies local ledger integrity (`assert_ledger`) against broker portfolio, confirming exact 0.00 paisa drift.

### Preflight Verification & Backup Suite (`scripts/preflight.py`, `scripts/backup_db.py`, `scripts/restore_db.py`)
- **10-Point Readiness Audit (`scripts/preflight.py`):**
  1. Hermes Gateway Up (HTTP 200 on `127.0.0.1:8642`)
  2. Primary Model & Fallback chain present
  3. Humming Bird plugin loaded with 22 tools
  4. Kernel Token configured (`KERNEL_TOKEN`)
  5. StockNow session authenticated (Portfolio #164580)
  6. Portfolio drift 0.00 (`assert_ledger` verified)
  7. Trading mode (`LIVE_HOURS` or `TEST_OFFHOURS`)
  8. Risk caps configured (`max_order`, `max_symbol`, `daily_budget`, `kill_switch`)
  9. Automation state valid
  10. Fresh verified SQLite database backup generated
  - Exits with code 0 on `ALL GO`, code 1 on any `NO-GO`.
- **Atomic Database Backup & Restore (`scripts/backup_db.py`, `scripts/restore_db.py`):**
  - Uses SQLite online backup API to take verified, timestamped snapshots of `hummingbird.db`.
  - Clears stale `-wal` and `-shm` artifacts upon restoration and runs `PRAGMA integrity_check`.

---

## 8. Real Hermes Cron Scheduler & Memory Subsystem

Autonomous schedules and long-term memory leverage Hermes' native capabilities rather than custom imitation code:

### Hermes Native Cron (`~/.hermes/cron/jobs.json`)
Scheduled autonomous tasks run via Hermes' native cron engine with timezone `Asia/Dhaka`:
- **10:00 AM Sun–Thu (`0 10 * * 0-4`):** Morning favorites sync and GSC_L1 turnaround list review (`morning_open_sync_l1`).
- **Every 5 min 10:00–14:30 Sun–Thu (`*/5 10-14 * * 0-4`):** Active session portfolio sync and canary thesis evaluation (`market_hours_portfolio_canaries`).
- **12:00 PM Sun–Thu (`0 12 * * 0-4`):** Midday all-shares market quote sync (`midday_all_shares_sync`).
- **Pre-Execution Hours Gate:** Each job prompt begins by calling `hb_market_open` and halts immediately if the DSE market is closed (weekends, holidays).
- **Cockpit Management:** The Cockpit Skills drawer inspects `GET /api/hermes/bridge/state` and allows the operator to Pause, Resume, or Delete scheduled jobs via Hermes CLI commands.

### Memory & Learning Subsystem
- **`USER.md`:** Operator identity (Hasibur Rahman), DSE preferences, Banglish language style, strict no-loss posture, and custom directives managed in Hermes' memory directory.
- **`MEMORY.md`:** Working market observations and thesis notes maintained directly by Hermes.
- **Procedural Learning:** Newly learned rules and methodologies discovered by Hermes are created and evolved directly as official skills under Hermes' native skills directory.

---

## 9. Repository Topology & Project File Tree

The following tree represents the complete, clean directory structure of the Humming Bird repository after migrating to the official Nous Research Hermes Agent and removing all legacy imitation agent modules:

```text
trading-cockpit/
├── .agentignore                             # Coding assistant indexing ignore patterns
├── .cursorignore                            # Cursor IDE indexing ignore patterns
├── .env.example                             # Environment variable template
├── .gitignore                               # Git ignored files & patterns
├── .opencodeignore                          # OpenCode indexing ignore patterns
├── AGENTS.md                                # Operator guidelines, commit conventions & operating rules
├── README.md                                # Project overview, quickstart & setup guide
├── package.json                             # Root tooling metadata
├── pyproject.toml                           # Python project configuration & packaging metadata
├── run.bat                                  # Windows quick-launch script
├── run.py                                   # Unified server launcher script
├── run.sh                                   # Linux/macOS launcher script
│
├── backend/                                 # Deterministic Trading Kernel & FastAPI Server
│   ├── .env.example                         # Backend environment variables template
│   ├── __init__.py                          # Backend package initializer
│   ├── config.py                            # Application configuration & environment loader
│   ├── database.py                          # SQLite schema (WAL mode) & SQLAlchemy ORM models
│   ├── hermes_bridge.py                     # Streaming SSE bridge to official Hermes Gateway API
│   ├── kernel_api.py                        # Standalone local Trading Kernel API (X-Kernel-Token protected)
│   ├── main.py                              # FastAPI entrypoint, middleware & route mounter
│   ├── market_map.py                        # DSE sector tree, market capitalization & categorization
│   ├── portfolio.py                         # Portfolio holdings calculation & valuation engine
│   ├── requirements.txt                     # Production runtime Python dependencies
│   ├── requirements-dev.txt                 # Development & testing Python dependencies
│   ├── routes_auth_settings.py              # Settings, auth tokens & system configuration endpoints
│   ├── routes_hermes.py                     # Hermes chat streaming bridge & bridge state endpoints
│   ├── routes_stocknow.py                   # StockNow ingestion routes, telemetry & market data endpoints
│   ├── secret_guard.py                      # Zero-secret isolation & credential redaction utility
│   ├── seed.py                              # Database seeder for demo fixtures & initial state
│   │
│   ├── adapters/                            # External Exchange & Brokerage Adapters
│   │   ├── __init__.py                      # Adapters package initializer
│   │   ├── stocknow_adapter.py              # High-level StockNow client adapter & state synchronizer
│   │   ├── stocknow_api.py                  # HTTP API client, Background mode (direct async httpx client)
│   │   ├── stocknow_client.py               # Browser session client, Onscreen mode (persistent Playwright browser session)
│   │   ├── stocknow_executor.py             # StockNowExecutor with ApiTransport and BrowserTransport
│   │   ├── stocknow_market_sync.py          # Real-time market prices, indices & quotes sync
│   │   ├── stocknow_portfolio_sync.py       # Portfolio holdings & cash synchronization
│   │   └── stocknow_write_guard.py          # Write guards restricting test portfolio mutations
│   │
│   ├── data/                                # Local persistent database & backup stores
│   │   ├── backups/                         # Atomic SQLite backups & legacy exports
│   │   │   └── legacy/                      # Exported backup rows from dropped legacy Hermes tables
│   │   └── hummingbird.db                   # Primary SQLite database file (WAL mode)
│   │
│   └── engine/                              # Core Quantitative & Deterministic Trading Engine
│       ├── __init__.py                      # Engine package initializer
│       ├── agent_actions.py                 # Deterministic action dispatcher & rule executor
│       ├── auto_trader.py                   # Automated evaluation cycle runner & signal executor
│       ├── checkpoint.py                    # Atomic state snapshot & rollback manager (KernelStateCheckpoint)
│       ├── circuit_breaker.py               # 3-failure circuit breaker with automatic shutoff & manual re-enable
│       ├── curve_analyzer.py                # 7-30 day trend slope, support/resistance, & crash detection
│       ├── heartbeat.py                     # Minute SQLite heartbeat, dead-man alert & daily summary (14:45)
│       ├── money.py                         # Strict decimal brokerage fee math (1.00% round trip)
│       ├── scheduler.py                     # Market calendar engine & session status evaluator
│       ├── sequential_seller.py             # Multi-tier profit locking & 50/50 pullback seller
│       ├── signals.py                       # Quantitative trading signal generators & indicators
│       ├── t2_ledger.py                     # DSE T+2 settlement rolling 3-bucket ledger (A, B, C)
│       ├── telegram_bot.py                  # Telegram daemon for alerts, summaries & remote kill switch
│       └── trading_lock.py                  # Single-writer cross-process trading concurrency lock
│
├── plugins/                                 # Official Hermes Agent Plugins
│   └── humming_bird/                        # Humming Bird Trading Engine Hermes Plugin
│       ├── __init__.py                      # Plugin lifecycle & tool registration (register(ctx))
│       ├── hooks.py                         # Pre-tool execution hooks (DSE market hours enforcement)
│       ├── plugin.yaml                      # Official Hermes plugin manifest & environment declarations
│       ├── schemas.py                       # Type definitions & Pydantic validation schemas
│       ├── tools.py                         # 22 Hermes tools (Read, Write, Modes, Caps, Sync, Orders)
│       └── skills/                          # Official Procedural Skills (agentskills standard)
│           ├── canary_90_10/
│           │   └── SKILL.md                 # 90/10 emergency profit lock & canary observation probe
│           ├── gsc_tiers/
│           │   └── SKILL.md                 # GSC master observation, L1 turnaround, L2 swing rally tiers
│           ├── sequential_no_regret/
│           │   └── SKILL.md                 # Multi-tier profit locking, 50/50 pullback & T+2 capital rolling
│           └── stocknow_dse_quirks/
│               └── SKILL.md                 # Virtual portfolio #164580 constraints & DSE session rules
│
├── frontend/                                # Cockpit Single-Page Interface
│   ├── app.js                               # Reactive state manager, DOM updater & telemetry polling
│   ├── charts.js                            # Canvas chart renderer (trend curves, sparklines, treemap)
│   ├── favicon.svg                          # Humming Bird brand icon
│   ├── hermes_ui.js                         # Hermes SSE chat stream, order preview cards, skills & crons
│   ├── index.html                           # Single-page cockpit dashboard layout & 4 balanced settings cards
│   ├── styles.css                           # Dark theme styling, terminal aesthetic, card layout & design system
│   └── theme_light_hermes.css               # WCAG AA compliant light theme design system
│
├── scripts/                                 # Administrative & Automation Scripts
│   ├── backup_db.py                         # Atomic SQLite database backup utility
│   ├── check_dse_market_open.py             # DSE trading hours & session validator
│   ├── check_heartbeat.py                   # Heartbeat verification & dead-man alert probe
│   ├── generate_code_map.py                 # Zero-dependency AST inspection & Codebase Map generator
│   ├── install_autostart.ps1                # Windows Task Scheduler logon autostart installer with restart
│   ├── install_plugin.ps1                   # Hermes plugin installation & linking script
│   ├── preflight.py                         # Pre-flight environment, auth, ledger & safety check suite
│   ├── restore_db.py                        # Atomic database restore utility
│   └── verify_chat_card.py                  # Playwright visual card renderer & screenshot capture probe
│
├── tests/                                   # Pytest Automated Test Suite (204 Tests)
│   ├── conftest.py                          # Shared test fixtures, mock client & test database setup
│   ├── test_api.py                          # REST API endpoint tests
│   ├── test_chat_order_preview_card.py      # Chat order preview card, execution & failure rollback tests
│   ├── test_engine.py                       # Quantitative engine unit tests (T2 ledger, fee math, curves)
│   ├── test_humming_bird_plugin.py          # Hermes plugin tool handler tests with mock kernel
│   ├── test_ingestion_switch.py             # Ingestion mode toggle & handoff tests
│   ├── test_kernel_api.py                   # Local kernel service endpoint, auth & checkpoint tests
│   ├── test_kernel_caps.py                  # Kernel safety caps, daily budget & operator confirmation tests
│   ├── test_mvp_rules.py                    # Core MVP trading rules, no-loss & 50/50 pullback tests
│   ├── test_order_path.py                   # Two-step order preview token & execution path tests
│   ├── test_portfolio_badge_and_watchlist.py # Portfolio header badge, drift & watchlist status pill tests
│   ├── test_portfolio_config.py             # Target portfolio configuration, allowlist & budget tests
│   ├── test_preflight_and_backups.py        # Preflight verification and backup/restore tests
│   ├── test_reliability_and_safety.py       # Reliability, circuit breaker, heartbeat & dead-man tests
│   ├── test_run_modes_decisions.py          # Onscreen vs Background run modes & decision stream tests
│   ├── test_secret_guard.py                 # Secret isolation & credential redaction tests
│   ├── test_stocknow_api.py                 # Async httpx StockNow API client contract tests
│   ├── test_stocknow_api_sync.py            # API-based market data, list & portfolio sync tests
│   ├── test_stocknow_executor.py            # Transport selection (ApiTransport vs BrowserTransport) tests
│   ├── test_stocknow_portfolio_164580.py    # Portfolio #164580 constraints & skill validation tests
│   ├── test_stocknow_step2_1.py             # StockNow adapter authentication tests
│   ├── test_stocknow_step2_2.py             # StockNow portfolio sync & holdings ingestion tests
│   ├── test_stocknow_step2_3.py             # StockNow order placement & validation tests
│   ├── test_stocknow_step2_4.py             # StockNow market data sync & quotes ingestion tests
│   ├── test_stocknow_step2_5.py             # StockNow scheduler & automated cycle runner tests
│   ├── test_stocknow_write_guard.py         # Hard test-only write contract guards
│   └── test_trading_mode.py                 # Live Hours vs Test Mode operational gate tests
│
└── documentation/                           # System Architecture & Strategy Documentation
    ├── About_Project.md                     # Core architecture, system philosophy & repo topology
    ├── Backlog.md                           # Implementation roadmap, sprint plans & backlog items
    ├── CODEBASE_MAP.md                      # Auto-generated AST map, LOC metrics & endpoint radar
    ├── REAL_HERMES_MIGRATION.md             # Verified Hermes extension points, runtime docs & evidence
    ├── Recent.md                            # Recent change logs, UI polish passes & sprint accomplishments
    ├── STOCKNOW_CURL_AUDIT.md               # Raw curl verification & endpoint response audits
    └── STOCKNOW_SITE_MAP.md                 # StockNow site map, write contracts & sanitized fixtures
```

