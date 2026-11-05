# 🐦 Project Humming Bird — Product Backlog & Sprint Roadmap

> **Current Active Release:** `v0.01` (Sprint 1 Core MVP inside the `v0.1` track)  
> **Core Strategy Mandate:** All versions preserve and refine the core **Human-Like Curve Buying + Crash/Vanish Quarantine + 3-Bucket T+2 Pipeline + Sequential "No-Regret" Profit Scaling + 50/50 Pullback Split + Strict No-Loss Hold** methodology.

---

## 🚀 Version 0.1 — Core MVP & StockNow Virtual Portfolio Automation

### ✅ Sprint 1 (Current — v0.01): Core Trading Automation Engine & Working Cockpit

#### 1. Documentation & Architecture Foundation
- [x] `About_Project.md`: Full vision, DSE mechanics (Sun–Thu 10:00–14:30, T+2 lock, 1% fee math), 3-bucket pipeline, sequential no-regret selling, 50/50 pullback recovery, 3-tier watchlist framework (GSC, GSC_L1, GSC_L2), Hermes Agentic Co-pilot philosophy (10% canary probe, thesis memory), DSE vs StockNow real-time analysis, system architecture, and $0/ultra-cheap deployment plan.
- [x] `Backlog.md`: Incremental sprint-by-sprint roadmap from `v0.1` (`StockNow`) to `v0.2` (Company Models) and `v0.3` (Live Brokers).
- [x] `README.md`: Quick-start commands, environment setup, architecture layout, and test instructions.

#### 2. Core Quantitative & Automation Backend (`backend/`)
- [x] **FastAPI + SQLAlchemy + SQLite Ledger:** Transactional database storing company profiles, tax lots, trade history, custom rules, canary theses, and cycle audit logs.
- [x] **Human-Like Curve Reader (`curve_analyzer.py`):**
  - Analyzes recent 7–15 session price curves to detect normal oscillation support (`BUY_ZONE`), mid-curve (`MID_RANGE`), and resistance (`SELL_ZONE`).
  - Verifies sufficient upside room above the ~1.00% round-trip brokerage fee hurdle before signaling a buy.
  - **Falling-Knife / Vanish Guard (`CRASH_QUARANTINE`):** Automatically blocks buying on any stock experiencing an abnormal single-day plunge or multi-day crash (protecting capital from troubled or vanishing companies).
- [x] **3-Tier Watchlist Framework & Sector Profiling:**
  - **Big Giant Stable Companies (GSC):** Blue-chip foundational anchors (`GP`, `SQURPHARMA`, `BANKASIA`, `EXIM1STMF`).
  - **GSC Upper Trends L1:** Established macro comeback curves after previous slumps, ignoring daily 1-day noise.
  - **GSC Upper Trends L2:** Short-term momentum swing / scalp opportunities capturing green spikes from red dips.
  - Configurable per-company `Buy %` capital allocation and enable/disable toggles.
- [x] **3-Bucket Rolling T+2 Pipeline (`t2_ledger.py`):**
  - Splits starting capital (`15,000 BDT` test fund) into **Bucket A, Bucket B, and Bucket C** (`5,000 BDT` each).
  - Tracks Bangladesh working sessions (Sunday–Thursday, skipping Friday/Saturday and holidays) so lots transition cleanly through `T+0 -> T+1 -> T+2 (Matured)`.
  - Separates available settled cash from unsettled sale receivables.
- [x] **Sequential "No-Regret" Seller & 50/50 Pullback Engine (`sequential_seller.py`):**
  - **Strict No-Loss Rule:** Never sells a matured lot at a net loss (`< 0%` after 1% fees).
  - **Sequential Profit Tiers:** Sells **25%** of the cycle's starting shares at Tier 1 (`+1.5%` net), another **25%** at Tier 2 (`+3.5%` net), and another **25%** at Tier 3 (`+6.0%` net), keeping a runner so we never regret missing a bigger rally.
  - **50/50 Pullback Split & Recovery:** Tracks each lot's High-Water Mark (peak price). If price drops significantly (default `>= 3%` from peak) while still net profitable, sells **50%** of remaining shares immediately to lock profit and holds the other **50%** in `RECOVERY_HOLD` until the next upward wave.
- [x] **Deterministic Auto-Trader Orchestrator (`auto_trader.py`):**
  - Atomic execution cycle (`Run Automation Cycle`), duplicate-trade prevention, exposure caps, and pause/resume switch.
- [x] **StockNow Adapter Foundation (`stocknow_adapter.py`):**
  - Pre-seeded with realistic DSE fixtures (`BANKASIA`, `EXIM1STMF`, `SQURPHARMA`, `BXPHARMA`, `GP`) and T+0/T+1/T+2 lots for instant testing, plus Playwright persistent-context hooks ready for Sprint 2.
  - Interactive demo clock & scenario controls (rally, pullback, crash, recovery, next working session).
- [x] **Real-Time Reactive Streaming (`/api/stream` SSE):**
  - Instant server-sent events pushed to frontend on every trade, cycle, scenario advance, or chat intervention without page reloads.

#### 3. Cockpit Dashboard & True Hermes Agentic Architecture (`backend/hermes/`)
- [x] **Zero-Secret-Read & `.env` Isolation Guardrails (`secret_guard.py`):**
  - Enforces runtime security boundary: Hermes cannot read `.env`, `.env.*`, `auth.json`, `cookies*`, `browser_profile/`, or `.db` files.
  - Automatically scrubs `sk-or-v1-*`, `sk-*`, `Bearer *`, and token patterns before memory storage or external API calls.
  - Added `.opencodeignore`, `.cursorignore`, and `.agentignore` to protect credentials from coding assistant indexing.
- [x] **Self-Improving Procedural Memory — Skills Engine (`skills_manager.py`):**
  - Versioned markdown skills in `backend/hermes/skills/`: `SKILL_gsc_tiers.md`, `SKILL_canary_90_10.md`, `SKILL_sequential_no_regret.md`, `SKILL_stocknow_dse_quirks.md`.
  - On-demand matching matches only relevant skills by tag/keywords into the agent prompt.
  - Self-patching tool (`learn_or_patch_skill`) updates `SKILL_*.md` files upon user instruction or confirmed canary thesis outcome.
- [x] **Three-Layer Memory System (`memory.py`):**
  - **Layer 1:** Operator Profile & Core Directives (Hasibur, Strict No-Loss posture, T+2 calendar).
  - **Layer 2:** Searchable Session History with cross-turn search across SQLite transcripts.
  - **Layer 3:** Durable Company Facts & Canary Probe Memory per stock.
- [x] **State Checkpoints & 1-Click Rollback (`/rollback`):**
  - Checkpoint manager saves state snapshots before mutations.
  - Operator can type `/rollback` in chat or click the Rollback button in Cockpit UI to restore state cleanly.
- [x] **Turn-based Agent Loop & Context Compression (`agent_loop.py`):**
  - Structured turn orchestration with automatic older-turn summarization.
  - Full toolset: `report_company_threat`, `evaluate_canary_theses`, `restore_quarantined_company`, `set_watchlist_tier`, `update_company_allocation`, `execute_manual_order`, `learn_or_patch_skill`, `rollback_last_checkpoint`.
- [x] **Zero-Build Dark-Mode Web Cockpit (`http://127.0.0.1:8000`):**
  - **Financial Telemetry:** Cash available, unsettled receivables, gross market value, net liquidation equity, realized & unrealized net P/L, and total brokerage fees paid.
  - **Period Accounting:** Today, Weekly, Monthly, and Yearly realized gain and total Buy/Sell volume turnover.
  - **T+2 Bucket & Tax-Lot Inspector:** Visual breakdown of Buckets A/B/C, locked vs. matured shares, current profit tier, and recovery anchor state.
  - **3-Tier Watchlist Filtering & Pulse Cards:** Filter by All, Big Giant Stable (GSC), Upper Trends L1, or Upper Trends L2 with live SVG curve sparklines.
  - **Canary Theses Observation Board:** Real-time visibility into user-reported threats tracked by Hermes with 10% canary probes.
  - **Hermes Skills & Memory Drawer:** Inspect active procedural skills, version patch counts, durable company facts, and recent checkpoints.
  - **1-Click Rollback Toolbar Button:** Instant undo directly from the sidebar.
  - **DSE Market Map Treemap Visualizer (Finviz Style):** Full DSE sector treemap matching real market breadth, squarified tiles sized by turnover (cr), color-coded by performance (Green/Red/Blue) with Finviz scale, glowing high-move borders, and one-click drilldown into individual sectors (`< Back`).
  - **Top Sectors By Gainer Stacked Bar Chart:** Pure SVG stacked bar chart with vertical sector labels on the X-axis showing Up, Down, and Unchanged counts per sector with hover tooltips and interactive treemap sync.
  - **TradingView-Style Interactive Crosshairs & Hover Tooltips:** Vertical and horizontal guidelines, session date, rebased index/% change, and circular Buy (`B`, green) & Sell (`S`, red) trade execution markers plotted on charts.
  - **Individual Company Deep-Trend View (Modal):** Multi-timeframe trend curves (**7D**, **1M**, **6M**, **1Y**) with horizontal Support Floor (green dashed) & Resistance Ceiling (red dashed) lines, shaded Buy Zone band, and an 8-card fundamental company profile (P/E, EPS, NAV, Market Cap, Dividend Yield, Paid-up Capital, 52-Week Range, Category).
  - **"What-If" Profit Simulator Slider:** Real-time calculator allowing traders to slide target price up/down and compute simulated gross exit value, 1% DSE brokerage fee, and net pocket cash profit in BDT.
  - **Theme Switcher (Dark / Light):** High-contrast daylight mode for daytime readability and sleek dark slate default with clean card borders and contrast.
  - **Continuous Smooth Spline Curves:** Pure continuous cubic bezier spline curves without static point dots, paired with continuous pixel-level hover crosshairs and subtle Buy/Sell execution markers.
  - **Master Automation Controller & Dual Ingestion Mode (`Background Polling` vs `Onscreen Live Mode`):**
    - Database schema & persistence: `automation_enabled`, `ingestion_mode`, `polling_interval_sec` in `PortfolioState`.
    - API endpoint: `POST /api/automation/config` with real-time SSE broadcast.
    - Two-way segmented slider switch in the sticky topbar and dedicated settings page: Master toggle (`AUTOMATION ON` vs `AUTOMATION OFF / PAUSED`), Dual Ingestion Mode toggle (Method A: Background Polling vs Method B: Onscreen Live Mode), and polling cadence slider.
    - Hermes agentic tool `set_automation_config` with `/rollback` checkpointing and natural Bangla/Banglish command support (*"Switch to onscreen live mode"*, *"Background polling 60s koro"*, *"Turn off buy sell automation"*).
  - **Unified Continuous Dashboard, ScrollSpy & Dedicated Settings Page:**
    - 4 scrollable dashboard sections on the single main page (`#overview`, `#watchlist`, `#rules`, `#ledger`) with ScrollSpy left nav sync, plus 5th dedicated separate `#settings` page.
    - **Sticky Top Navbar:** Locked mission-critical navigation with live DSE market clock & countdown, two-way ingestion mode toggle, master engine controls, and theme switcher, allowing all dashboard sections to slide cleanly underneath.
    - **Fixed Viewport Lock Architecture (Sticky Hermes & Nav Rail):**
      - Locked outer viewport (`height: 100vh; overflow: hidden;`) with middle `.workspace` scrolling independently (`height: 100vh; overflow-y: auto;`). Left nav rail and right Hermes assistant stay 100% viewport-fixed at all times, never scrolling off screen.
  - **Continuous Smooth Curves Without Point Dots:**
    - Eliminated static dots along the price curve in `renderMainChart()` and `renderDeepTrendChart()`.
    - Implemented continuous pixel-level hover interpolation so crosshairs glide smoothly with pixel precision without discrete session hopping.
  - **Rebuilt Hermes `[Changes]` Tab as System & Rule Diff Review:**
    - Replaced raw git files list with visual GitHub/IDE-style structured Before vs. After diff cards (`.diff-card`) featuring red deleted lines (`[-] Previous`) and green added lines (`[+] Updated`), actor badges, timestamps, and 1-click `/rollback`.
  - **3-Tier AI Brain Switcher (`/model`) in Hermes Header & Settings:**
    - **Tier 1:** User-selected OpenRouter model (e.g. `xiaomi/mimo-v2-flash`, `deepseek/deepseek-chat`, `meta-llama/llama-3.3-70b-instruct`, `anthropic/claude-3.5-sonnet`, `google/gemini-2.0-flash-001`). Switchable via `/model <name>` in chat or UI dropdown picker in header & settings.
    - **Tier 2:** 1st Fallback — Free Google Gemini API (`google/gemini-2.5-flash`).
    - **Tier 3:** 2nd Fallback — Deterministic Local Quant Brain ($0 offline).
    - API endpoints: `GET /api/hermes/models` and `POST /api/hermes/model`.
  - **Settings Page Overhaul & Telemetry Pipeline Controls:**
    - Interactive Method A (Background HTTP Polling) vs Method B (Onscreen Live Mode CDP) selector tiles with status pills, smooth polling interval slider (30s to 300s), and quick preset cadence pills (30s Hyper, 60s Fast, 120s Standard, 180s Relaxed).
    - API Keys & Live Telemetry credential manager with masked inputs (`sk-or-v1-...`, Gemini key, Telegram Bot token & chat ID), toggleable password visibility eyes, and quota usage tracking.
    - Market Clearing & Settlement rules card (0.50% buy, 0.50% sell, +1.005% gross hurdle) and T+2 rolling bucket explanation.
    - Technical clutter migration: Relocated SSE realtime status, paper mode badges, and session API token triggers from the sticky topbar into Settings.
  - **Hermes Copilot Viewport Grid Synchronization & UX Polish:**
    - Synchronized bi-directional sidebar width adjustment (280px–640px) resizing the `.app-shell` 3rd column track via CSS variable `--hermes-width`, completely resolving off-screen rightward overflow or clipping while persisting in `localStorage`.
    - Custom upward-opening model drop-up menu (`.model-dropup-menu`) opening smoothly above the chat composer with active model checkmarks.
    - Restored compact horizontal pill quick-prompt buttons (`Portfolio status ↗`, `Alert bankruptcy threat ⚡`, `Restore company ↺`) with subtle borders and teal hover accents.
    - Sub-pixel centered chat send button with zero browser padding offset.
    - Decluttered trader interface by removing repetitive "AGENTIC" badges and visual dot artifacts across Hermes.
  - **Developer Productivity & Instant Local Reload:**
    - Disabled aggressive static asset browser caching (`Cache-Control: no-cache, no-store, must-revalidate`) in `DevStaticFiles` and root cockpit endpoint so frontend UI changes reflect immediately upon browser refresh (`F5`) without clearing browser cache.
  - **Exhaustive Light Mode Daylight Uniformity:**
    - Eliminated all hardcoded dark background artifacts across watchlist tables, position inspectors, DSE market map containers, stacked bar charts, modals, settings, and diff review cards, featuring 50% lighter pastel treemap tiles and dark legible text contrast.
- [x] **AST Codebase X-Ray & Architecture Radar (`scripts/generate_code_map.py` -> `documentation/CODEBASE_MAP.md`):**
  - Zero-dependency stdlib script scanning Python AST, class methods, FastAPI routes, DOM elements, and code health radar.
- [x] **Repository Documentation Reorganization:**
  - All architecture specs maintained in `documentation/` (`About_Project.md`, `Backlog.md`, `CODEBASE_MAP.md`), keeping only `README.md` at repo root.
- [x] **Complete Automated Test Suite (28/28 passing):**
  - Engine tests, settlement calendars, fee basis math, sequential seller tiers, local chat, OpenRouter mock, agentic emergency quarantine & canary exits, watchlist categories, SSE streams, cockpit smoke tests, SecretGuard isolation, on-demand skill loading & self-patching, 3-layer memory, state checkpoint `/rollback`, DSE Market Map `/api/market/map` payload & visualizer tests, company fundamentals/extended history deep trend tests, dual-mode automation controller API tests, Hermes conversation threads & messages, system changes diff endpoint, and AI brain model switcher tests.

---

### 🔌 Sprint 2 (Active): Live `stocknow.com.bd` Virtual Portfolio Automation ("Humming Bird")

- [x] **Step 2.1: Persistent Playwright Session, Auto-Login & Network Sniffer:**
  - Launch Chromium with a persistent local profile (`Path.home() / ".hummingbird_stocknow_profile"`) outside OneDrive to prevent sync locks.
  - Dual-mode browser lifecycle (`ONSCREEN_LIVE` headed vs `BACKGROUND_POLLING` headless).
  - Passive XHR/JSON response sniffer (`page.on("response", ...)`) capturing DSE market telemetry and portfolio payloads without spam.
  - Zero-secret auto-login helper (`ensure_authenticated`) with masked phone display and `SecretGuard` protection.
  - REST endpoints (`GET /api/stocknow/status`, `POST /api/stocknow/session`) with real-time SSE broadcasts.
- [x] **Step 2.2: Live DSE Quote & 7–30 Day Curve Sync Engine:**
  - Modular sync engine (`backend/adapters/stocknow_market_sync.py`) extracting quotes and historical curves from sniffer cache or active DOM.
  - SQLite database sync (`sync_live_market_to_db`) updating `CompanyProfile` rows, reconciling curve observations, and activating `"STOCKNOW_LIVE"` source tag.
  - REST endpoint `POST /api/stocknow/sync-market` with SSE portfolio refresh broadcast.
  - Hermes agentic tool `control_stocknow_session` with natural language Bangla/English command execution (*"Launch StockNow browser"*, *"StockNow login check koro"*, *"Sync live market prices"*).
  - UI action buttons in `#settings` StockNow Bridge card (`Launch Live Browser`, `Check / Auto-Login`, `Sync Live Prices`).
- [x] **Step 2.3: "Humming Bird" Virtual Portfolio & Holdings Sync:**
  - Automatically bind to the operator's **"Humming Bird"** virtual portfolio on StockNow (`extract_hummingbird_portfolio`).
  - Sync virtual cash balance, holdings, buy prices, and transaction history into the local SQLite T+2 ledger with rotating bucket assignment (`reconcile_portfolio_to_db`).
  - Active selling tier preservation (`next_tier`, `peak_price`, `phase`, `recovery_anchor`, `cycle_base_qty`) across sync cycles.
  - State checkpointing with full 1-click `/rollback` restoration of previous tax lots and trades.
  - Zero-drift paisa-level ledger balancing guaranteeing `assert_ledger` 100% compliance.
  - API endpoint `POST /api/stocknow/sync-portfolio` with real-time SSE snapshot broadcast.
  - Hermes agentic tool dispatch with Bangla/English natural commands (*"Sync Humming Bird portfolio"*, *"Humming Bird portfolio sync koro"*).
  - UI control button in `#settings` StockNow Bridge card (`Sync "Humming Bird" Portfolio`).
- [x] **Step 2.4: Automated Virtual Order Execution on StockNow ("Humming Bird"):**
  - Dedicated virtual order executor (`stocknow_order_executor.py`) supporting live browser DOM automation and paper verified execution.
  - Idempotency deduplication preventing accidental double-fills across retry loops or rapid commands.
  - Updated `StockNowAdapter.execute_order()` delegating to virtual order execution and exposing `last_order_receipt`.
  - REST endpoint `POST /api/stocknow/execute-order` with CheckpointManager state snapshot for 1-click `/rollback`.
  - Strict enforcement of T+2 maturity lock and 1% fee math (blocking immature and net-loss sells under Strict No-Loss policy).
  - Hermes conversational Buy and Matured Sell execution (*"Buy 10 GP"*, *"GP 10 ta share kine felo"*, *"Sell 5 SQURPHARMA"*) with StockNow virtual order receipt confirmation.
- [ ] **Step 2.5: DSE Market-Hours Scheduler:**
  - Automated background loop running Sunday–Thursday from **10:00 AM to 2:30 PM (`Asia/Dhaka`)** with configurable polling intervals.

---

### 🎛️ Sprint 3: Custom Rule Builder UI, Conversational Control & Telegram Bot

- [ ] **Interactive Custom Rule Builder UI:**
  - Visual sliders and inputs per company and per sector: customize Tier 1/2/3 profit percentages, slice percentages (e.g., 20% / 30% / 50%), pullback drop threshold, and per-company `Buy %` limits.
  - Favorite company selector & Quarantine review/release toggle from the Cockpit UI.
- [ ] **Sector Profile Customization:**
  - Dedicated stability settings for `BANK`, `INSURANCE`, and `MUTUAL_FUND` vs. custom renowned stocks.
- [ ] **Telegram Bot Command Center (`telegram_bot.py`):**
  - Real-time push alerts on every automated Buy, Sequential Tier Sell, 50/50 Pullback Split, or Crash Quarantine event.
  - Interactive Telegram commands (`/status`, `/buckets`, `/today`, `/pause`, `/resume`, and natural language Bangla/English chat).
- [ ] **Hermes Agent Action Proposals:**
  - Allow the user to tell the Side-Chat or Telegram Bot (e.g., *"GP-er buy % 25% kore dao"* or *"Ajke bank sector pause rakho"*) with a 1-click confirmation preview.

---

## 🧠 Version 0.2 — Company-Specific Models, Auto-Scanner & Full Cockpit Telemetry

- [ ] **Per-Company Statistical / ML Curve Models:**
  - Train lightweight company-specific models (Support/Resistance bands, Z-score mean reversion, Linear Regression slope) tailored to the historical price character of each renowned DSE company (`BANKASIA`, `BXPHARMA`, `SQURPHARMA`, `GP`, `EXIM1STMF`, etc.).
- [ ] **Automated DSE Curve-Stability Scanner:**
  - Scan DSE stocks to automatically discover and rank companies showing smooth, repeatable, low-crash oscillation curves for watchlist expansion.
- [ ] **Full Cockpit Accounting & BO Telemetry:**
  - Historical daily equity curve snapshots, deposits/withdrawals tracking, dividend adjustments, and BO account annual charge / brokerage commission analytics across Today, Weekly, Monthly, and Yearly views.
- [ ] **Cloud / Always-On Deployment Pack:**
  - Docker + Systemd setup for $0 Oracle Always-Free VM or ultra-cheap Linux VPS deployment.

---

## 🏦 Version 0.3 — Live Brokerage Portal Adapters (LankaBangla / Shanta)

- [ ] **Plug-and-Play Broker Adapter Interface:**
  - Build dedicated Playwright / API adapters for real DSE brokerage portals (e.g., **LankaBangla TradeXpress**, **Shanta EasyTrade**) using the exact same `base_adapter.py` contract.
- [ ] **Live BO Account & Settled Balance Reconciliation:**
  - Sync real BO account balances, mature saleable quantities, and exact broker commission schedules.
- [ ] **Human-in-the-Loop Execution Guardrails:**
  - Optional 1-tap Telegram/Cockpit approval gate before submitting real-money orders, daily max-spend caps, and instant kill-switch.