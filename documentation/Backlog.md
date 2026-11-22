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

#### 3. Cockpit Dashboard & Official Hermes Agentic Architecture
- [x] **Zero-Secret Isolation & Hardened Profile Boundary (`backend/secret_guard.py` & Hermes Profile):**
  - Architectural boundary: the dedicated `hummingbird` Hermes profile explicitly disables `terminal`, `file`, `code_execution`, and `browser` toolsets (`agent.disabled_toolsets`). The agent physically lacks `read_file` and `terminal` tools and cannot read `.env`, database, or filesystem artifacts.
  - Set `approvals.mode: manual` for fail-closed command execution.
  - In-kernel regex utility (`backend/secret_guard.py`) scrubs credentials from adapter logs and telemetry.
  - Added `.opencodeignore`, `.cursorignore`, and `.agentignore` to protect credentials from coding assistant indexing.
- [x] **Standalone Trading Kernel Service (`backend/kernel_api.py`):**
  - Standalone FastAPI router bound strictly to `127.0.0.1` and protected by `X-Kernel-Token`.
  - Zero imports from agent code; strictly deterministic execution of portfolio reads, tier modifications, and order placement.
  - Enforces T+2 maturity, strict no-loss hurdle (>= +1.005% gross profit after 1.00% round trip commission), and portfolio #164580 binding.
  - Snapshot before write via `KernelStateCheckpoint` with structured `KernelAuditLog` entries.
- [x] **Official Humming Bird Hermes Plugin (`plugins/humming_bird/`):**
  - Official plugin format (`plugin.yaml`, `__init__.py` with `register(ctx)`, `schemas.py`, `tools.py`).
  - Read tools: `hb_portfolio`, `hb_watchlist`, `hb_inspect_curve`, `hb_market_open`, `hb_canaries`, `hb_lots`.
  - Write tools: `hb_set_tier`, `hb_set_allocation`, `hb_quarantine_canary`, `hb_restore_quarantine`, `hb_sync`, `hb_place_order` (dry_run default, confirmation required, market hours hook), `hb_rollback_last`.
  - Official procedural skills in `plugins/humming_bird/skills/`: `canary_90_10`, `gsc_tiers`, `sequential_no_regret`, `stocknow_dse_quirks`.
- [x] **Real Hermes SSE Streaming Bridge (`backend/hermes_bridge.py`):**
  - Proxies chat requests directly to Hermes Gateway API server (`/v1/chat/completions`) with zero CLI subprocess fallback.
  - Real-time tool-call cards rendered in chat with tool names, input arguments, running/done status badges, and collapsible execution output.
- [x] **Real Hermes Native Cron & Memory:**
  - Scheduled autonomous tasks run via Hermes' native cron engine (`~/.hermes/cron/jobs.json`) with timezone `Asia/Dhaka` and DSE market hours check.
  - Long-term operator directives and notes managed natively in Hermes' `USER.md` and `MEMORY.md`.
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
  - **Master Automation Controller & Run Modes (`Background` vs `Onscreen`):**
    - Database schema & persistence: `automation_enabled`, `ingestion_mode`, `polling_interval_sec` in `PortfolioState`.
    - API endpoint: `POST /api/automation/config` with real-time SSE broadcast.
    - Two-way segmented slider switch in the sticky topbar and dedicated settings page: Master toggle (`AUTOMATION ON` vs `AUTOMATION OFF / PAUSED`), Run Mode switch (`Background` vs `Onscreen`), and polling cadence slider (active in Background mode).
    - Hermes agentic tool `set_automation_config` with `/rollback` checkpointing and natural Bangla/Banglish command support (*"Switch to onscreen mode"*, *"Background polling 60s koro"*, *"Turn off buy sell automation"*).
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
  - **Real Hermes Agent Integration & Streaming SSE Bridge (`backend/hermes_bridge.py`):**
    - Official Nous Research `hermes-agent` integrated as the standalone brain, keeping the local repo dedicated strictly to trading kernel and Cockpit UI.
    - Thin SSE streaming bridge (`backend/hermes_bridge.py`) proxying chat to Hermes Gateway API server (`/v1/chat/completions`) with granular streaming events, tool cards, and `/api/hermes/bridge/state`.
    - Real-time tool-call cards rendered in chat with tool names, input arguments, running/done status badges, and collapsible execution output.
    - Active model read directly from Hermes' native configuration (`~/.hermes/config.yaml`).
  - **Humming Bird Plugin & Trading Kernel API (`plugins/humming_bird/` & `backend/kernel_api.py`):**
    - Official plugin format (`plugin.yaml`, `__init__.py` with `register(ctx)`, `schemas.py`, `tools.py`).
    - Read tools (`hb_portfolio`, `hb_watchlist`, `hb_inspect_curve`, `hb_market_open`, `hb_canaries`, `hb_lots`) and Write tools (`hb_set_tier`, `hb_set_allocation`, `hb_quarantine_canary`, `hb_restore_quarantine`, `hb_sync`, `hb_place_order`, `hb_rollback_last`).
    - Clean localhost-only (`127.0.0.1`) Trading Kernel API with `X-Kernel-Token` security, `KernelStateCheckpoint` snapshots, and `KernelAuditLog` tracking before mutations.
    - Procedural skills migrated to official format under `plugins/humming_bird/skills/<name>/SKILL.md` (`canary_90_10`, `gsc_tiers`, `sequential_no_regret`, `stocknow_dse_quirks`).
  - **Native Hermes Cron Scheduler (`~/.hermes/cron/jobs.json`):**
    - Recurring autonomous jobs scheduled with timezone `Asia/Dhaka`: morning favorites sync (`0 10 * * 0-4`), market-hours portfolio & canary check (`*/5 10-14 * * 0-4`), and midday all-shares sync (`0 12 * * 0-4`).
    - Every prompt performs pre-execution market hour verification via `hb_market_open` to cleanly stop on weekends and holidays.
    - Cockpit Skills drawer surfaces live Hermes skills, `USER.md` / `MEMORY.md` previews, and interactive Pause / Resume / Delete buttons executing Hermes cron commands.
  - **All DSE Shares Live Market Board:**
    - Live sync and scraping of the full 470+ DSE shares catalog (`/api/stocknow/all-shares`).
    - Dedicated "All DSE Shares" tab in `#watchlist` with instant search, category badges, LTP, +/- %, and sparkline price curves.
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
  - Engine tests, settlement calendars, fee basis math, sequential seller tiers, local chat, OpenRouter mock, agentic emergency quarantine & canary exits, watchlist categories, SSE streams, cockpit smoke tests, SecretGuard isolation, official Hermes plugin skills, persistent memory, state checkpoint `/rollback`, DSE Market Map `/api/market/map` payload & visualizer tests, company fundamentals/extended history deep trend tests, dual-mode automation controller API tests, system changes diff endpoint, and read-only Hermes AI brain state tests.

---

### 🔌 Sprint 2 (Completed): Live `stocknow.com.bd` Virtual Portfolio Automation ("Humming Bird")

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
  - UI action buttons in `#settings` StockNow Bridge card (`Launch Live Browser`, `Check / Auto-Login`, `Sync Live Prices`).
- [x] **Step 2.3: "Humming Bird" Virtual Portfolio & Holdings Sync:**
  - Automatically bind to the operator's **"Humming Bird"** virtual portfolio on StockNow (`extract_hummingbird_portfolio`).
  - Sync virtual cash balance, holdings, buy prices, and transaction history into the local SQLite T+2 ledger with rotating bucket assignment (`reconcile_portfolio_to_db`).
  - Active selling tier preservation (`next_tier`, `peak_price`, `phase`, `recovery_anchor`, `cycle_base_qty`) across sync cycles.
  - State checkpointing with full 1-click `/rollback` restoration of previous tax lots and trades.
  - Zero-drift paisa-level ledger balancing guaranteeing `assert_ledger` 100% compliance.
  - API endpoint `POST /api/stocknow/sync-portfolio` with real-time SSE snapshot broadcast.
  - UI control button in `#settings` StockNow Bridge card (`Sync "Humming Bird" Portfolio`).
- [x] **Step 2.4: Automated Virtual Order Execution on StockNow ("Humming Bird"):**
  - Dedicated virtual order executor (`stocknow_executor.py`) supporting live browser DOM automation and direct API execution.
  - Idempotency deduplication preventing accidental double-fills across retry loops or rapid commands.
  - Updated `StockNowAdapter.execute_order()` delegating to virtual order execution and exposing `last_order_receipt`.
  - REST endpoint `POST /api/stocknow/execute-order` with CheckpointManager state snapshot for 1-click `/rollback`.
  - Strict enforcement of T+2 maturity lock and 1% fee math (blocking immature and net-loss sells under Strict No-Loss policy).
- [x] **Step 2.4.1: Real Hermes Agent Migration & Architecture Clean-Up:**
  - Replaced imitation agent loop, memory, and custom skill engines with the official Nous Research Hermes runtime.
  - Implemented streaming SSE bridge in `backend/hermes_bridge.py` and Humming Bird plugin in `plugins/humming_bird/`.
  - Exposed local trading engine as deterministic `backend/kernel_api.py` with `X-Kernel-Token` authentication and atomic `KernelStateCheckpoint` snapshots.
  - Dropped legacy `hermes_*` tables with automated backup export, purged imitation code (`backend/hermes/`, `backend/hermes_os/`), and retained all core kernel invariants.

- [x] **Step 2.5: DSE Market-Hours Auto-Scheduler (10:00 AM – 2:30 PM Sun–Thu):**
  - Automated background loop running Sunday–Thursday from **10:00 AM to 2:30 PM (`Asia/Dhaka`)** respecting configured polling intervals (`30s`–`300s`).
  - DSE market hours gate (`is_dse_market_open`) evaluating Asia/Dhaka time, trading days, weekends (Friday/Saturday), and configured DSE holidays.
  - Background async scheduler (`DSEMarketScheduler`) syncing live market quotes from StockNow, executing AutoTrader paper cycle, updating telemetry, and broadcasting SSE snapshots.
  - API endpoints: `GET /api/stocknow/scheduler`, `POST /api/stocknow/scheduler` (`start`, `stop`, `tick_now` with `force`).

- [x] **Step 2.6: Comprehensive UI/UX Polish & Bug Fix Pass (B1 - B11, Readability, Theming & Per-Screen Polish):**
  - **Critical Bug Fixes (B1 - B11):**
    - Corrected fee accounting discrepancy in What-If simulator and lot inspector to include exit broker fee.
    - Resolved double JSON stringification on model switcher.
    - Integrated read-only Hermes Brain card fed by `/api/hermes/bridge/state` reflecting native Hermes config.
    - Added accurate provider/model metadata display synchronized live from Hermes bridge state.
    - Verified multi-session drop wording and accurate support level comparison logic in Hermes analysis summaries.
    - Re-aligned Overview price curve with dedicated right gutter padding for resistance/support labels and single-row legend.
    - Fixed Treemap small tile label clipping with `ResizeObserver` and neutral slate 0% unchanged heat token.
    - Standardized Telegram placeholders and clarified immediate auto-save vs. manual API key save states.
  - **Readability & Typography:**
    - Upgraded dark mode contrast tokens (`--dim` to `#8393a6`, `--muted` to `#9aabbd`) to pass WCAG AA.
    - Enforced `:root` type scale (`--fs-xs: 11px`, `--fs-sm: 12px`, `--fs-md: 13px`, `--fs-lg: 14px`) and eliminated all sub-11px visible text.
    - Applied `font-variant-numeric: tabular-nums` across all numeric metrics, tables, and clock displays.
    - Enforced Overview metric cards typography hierarchy with 30px Net Liquidation Equity hero number.
  - **Semantic Color System:**
    - Defined semantic tokens for profit/loss (`--green`, `--red`), brand accent (`--brand`), warnings (`--amber`), and order sides (`--buy` blue, `--sell` amber) across both Dark and Light themes.
    - Enforced strict color mapping where green and red exclusively convey financial direction (P/L, day change, sparklines).
  - **Per-Screen Refinements:**
    - Topbar grouped layout with compact mode slider below 1280px, overflow menu below 1100px, next-session DSE scheduler tooltips, and left nav rail tooltips.
    - Overview rolling capital progress bars and decision stream hierarchy.
    - Watchlist left/right text/numeric alignment, sticky header, and 3-column Position Inspector grid.
    - Strategy rules visible +1.005% round-trip breakeven marker, Buy Cap `%` suffix input with toggle switch, and subtle trade ledger zebra striping.
    - Settings equal-height cards, 12px/20px spacing hierarchy, Method B polling interval disabled state with helper text, and StockNow Bridge spinner feedback.
    - Hermes chat empty-state quick action chips placement under intro, responsive composer return, line-height 1.5, high-contrast tab counters, and interactive model trigger caret.
    - Added 7-session Net Liquidation Equity sparkline and client-side Decision stream filter chips (All, Buys, Sells, Blocked, Locks).

- [x] **Step 2.7: Real StockNow Portfolio (#164580) Migration, 3-List GSC Trading Priority & Active Holdings Table:**
  - **Runtime Database Migration to Real StockNow Portfolio (#164580):**
    - Transitioned runtime database from dummy fixtures to operator's real StockNow "Humming Bird" portfolio (`#164580`).
    - Settled cash: `91,236.00 BDT`, open cost basis: `30,056.71 BDT`, total book assets: `121,292.71 BDT` reconciled to exact 0.00 paisa drift (`assert_ledger`).
    - Active matured holdings: `BANKASIA` (294 sh @ 17.09 cost), `IBNSINA` (16 sh @ 304.31 cost), and `MATINSPINN` (206 sh @ 97.89 cost).
    - Preserved legacy test fixture isolation so synthetic tests in `tests/` pass with zero regression.
  - **3-Tier Watchlist Structure & AutoTrader Buy Ordering:**
    - `GSC` (Giant Stable Companies): Master observation pool of surviving giants (`ACI`, `BANKASIA`, `DHAKABANK`, `FUWANGCER`, `IFIC`, `NPOLYMER`, `PRIMEBANK`, `PUBALIBANK`, `SPCERAMICS`). Analyzed and logged for learning, but skipped for auto-buying (`WAIT_OBSERVATION_ONLY`) unless promoted to `GSC_L1` or `GSC_L2`.
    - `GSC_L1` (GSC Upper Trends L1): Genuinely recovering comeback curves (`BANKASIA`, `MATINSPINN`), prioritized #1 for buys.
    - `GSC_L2` (GSC Upper Trends L2): Short-term fluctuation / swing scalps (`DHAKABANK`), prioritized #2 for buys.
  - **Hermes Procedural Skill (`plugins/humming_bird/skills/gsc_tiers/SKILL.md` v1.1.0):**
    - Encoded operator domain knowledge so Hermes always applies the exact 3-list distinctions in advice and execution.
  - **Humming Bird Active Holdings Table in `#overview`:**
    - Dedicated card below top metric grid with live summary pills (Settled Cash, Buy Cost, Sell Value, Unrealized Gain/Loss).
    - Full holdings table with Company, Tier, Qty @ Avg Cost, LTP, Total Cost, Sell Value (Net), Gain/Loss (%), Status/Action, and Total footer row.
  - **Full Test Suite Verification:** 62 passing unit tests covering portfolio migration, ledger reconciliation, tier priority, and Hermes skill matching.

- [x] **Step 2.8: Live Playwright Workflow for /login, /favorites (3 Lists), /show, /ledger, /buy & /sell:**
  - **Login & Auto-Discovery:**
    - Live login automation against `https://www.stocknow.com.bd/login?nextUrl=/portfolios` filling credentials from environment variables (`STOCKNOW_MOBILE`, `STOCKNOW_PASSWORD`), toggling "Remember mobile and password", and clicking Login.
    - Scrapes `/portfolios` to discover "Humming Bird", extracts balance (`91,236`), sell value (`31,637`), today gain/loss (`-200`), unrealized gain/loss (`1,422`), and binds `bound_portfolio_id = "164580"`.
  - **3-List Favorites Sync:**
    - Reads favorites list dropdown on `/favorites`: maps "Giant Stable Companies" -> `GSC`, "GSC Upper Trends L1" -> `GSC_L1`, "GSC Upper Trends L2" -> `GSC_L2`.
    - Updates each company's `watchlist_category` and live quote telemetry in SQLite.
  - **Holdings (/show) & Ledger (/ledger) Scraper:**
    - Parses `/portfolios/164580/show` table for cash `91,236.00` and holding rows (`BANKASIA`, `IBNSINA`, `MATINSPINN`).
    - Parses `/portfolios/164580/ledger` table with `DD/MM/YY` date parsing (`02/11/26` -> `2026-11-02`) so T+2 maturity is computed from real purchase dates.
  - **Order Automation with 0.5% Commission:**
    - Automates `/buy` and `/sell` under Item 1 on `stocknow.com.bd` with default `commission_pct = 0.5%`.
    - Automatically clears auto-filled quantities on `/sell` to submit exact slice sizes (25% sequential slice or 50% pullback split).
    - Wired `AutoTrader._run_cycle_internal()` to dispatch every automated Buy and Sequential Tier Sell through `adapter.execute_order` with 0.5% commission.
    - Wired 1-click 25% slice sell quick action in `#overview` Active Holdings table with locked `No-Loss Hold Guard` on underwater holdings.
  - **Full Verification:** 67 passing unit tests.

- [x] **Step 2.9: Official Nous Research Hermes Agent Migration & Architecture Decoupling:**
  - **Standalone Trading Kernel Service (`backend/kernel_api.py`):**
    - Isolated local REST endpoints (`127.0.0.1`) secured with `X-Kernel-Token`.
    - Zero imports of LLM/agent code; strict enforcement of T+2 maturity, strict no-loss (+1.005% gross hurdle), 0.5% buy/sell commission, and portfolio #164580 constraints.
    - Atomic `KernelStateCheckpoint` snapshots and `KernelAuditLog` entries taken prior to any state mutation.
  - **Official Humming Bird Plugin (`plugins/humming_bird/`):**
    - Standalone plugin package (`plugin.yaml`, `__init__.py`, `schemas.py`, `tools.py`).
    - 6 Read tools: `hb_portfolio`, `hb_watchlist`, `hb_inspect_curve`, `hb_market_open`, `hb_canaries`, `hb_lots`.
    - 7 Write tools: `hb_set_tier`, `hb_set_allocation`, `hb_quarantine_canary`, `hb_restore_quarantine`, `hb_sync`, `hb_place_order` (dry_run default, explicit confirmation required), `hb_rollback_last`.
    - Pre-tool execution hooks (`hooks.py`) enforcing DSE trading session hours (Sun-Thu 10:00-14:30 Asia/Dhaka).
    - 4 official procedural skills in `plugins/humming_bird/skills/`: `canary_90_10`, `gsc_tiers`, `sequential_no_regret`, `stocknow_dse_quirks`.
  - **Official Hermes Runtime & OpenRouter Configuration:**
    - Installed official `hermes-agent` beside the project (`~/.hermes`).
    - Configured OpenRouter provider with tool-calling models (`gemini-3.1-flash-lite`, `mimo-v2.6-pro`) in native Hermes config.
  - **Streaming SSE Chat Bridge (`backend/hermes_bridge.py`):**
    - High-performance bridge streaming events (`tool_use`, `tool_result`, `text`, `done`) to the Cockpit UI via Hermes Gateway API server (`/v1/chat/completions`) with zero CLI subprocess fallback.
    - Live tool-call cards rendered directly in Cockpit chat with inputs, execution badges, and expandable outputs.
  - **Hermes Native Cron & Memory:**
    - Native cron jobs created in `~/.hermes/cron/jobs.json` with timezone `Asia/Dhaka` and pre-execution market hours gate.
    - Operator identity and trading posture persisted in native `USER.md` and `MEMORY.md`.
  - **Imitation Code Removal & Clean Database Migration:**
    - Completely deleted 7,000+ lines of imitation code (`backend/hermes/` and `backend/hermes_os/`).
    - Exported legacy Hermes SQLite tables to `backend/data/hermes_tables_backup.json` and dropped legacy tables.
    - Preserved `SecretGuard` in `backend/secret_guard.py` for adapter credential isolation.
    - Verified full test suite passes (74 passing unit tests).

- [x] **Step 2.10: Hardened Production Runtime, Unified Launcher, Risk Caps, Trading Modes & Preflight Suite:**
  - **Unified Supervisor Launcher (`run.py`):**
    - One-command startup script setting `HERMES_HOME`, initializing Hermes Gateway on `127.0.0.1:8642` with profile `hummingbird`, polling `/health` for liveness, and starting FastAPI Uvicorn on `127.0.0.1:8000`. Thin wrappers `run.bat`, `run.sh`, and `package.json` delegate to `run.py`.
    - Automatic 3-restart crash recovery and clean teardown on `Ctrl+C` (SIGINT/SIGTERM).
  - **Dual Trading Modes (`LIVE_HOURS` vs `TEST_OFFHOURS`):**
    - Database-backed trading mode in `PortfolioState`.
    - `LIVE_HOURS` enforces Asia/Dhaka Sun-Thu 10:00–14:30 market gate across hooks, kernel orders, and scheduler.
    - `TEST_OFFHOURS` bypasses *only* the market hours gate for continuous off-hours end-to-end integration testing while keeping T+2, no-loss, fees, caps, and single-writer concurrency locks 100% active.
    - Added `#trading-mode-toggle` in topbar and Settings; exposed via `hb_mode_get` and `hb_mode_set`.
  - **Enforced Risk Limits & Kernel Caps:**
    - SQLite-backed `max_order_bdt`, `max_symbol_bdt`, `daily_budget_bdt` (default 4000 BDT), `max_orders_per_day` (default 20), and global `kill_switch_active`.
    - Shared single-writer lock (`SingleWriterTradingLock`) guaranteeing AutoTrader and Hermes order paths never run concurrently.
    - Exposed via `/k/caps` endpoints and plugin tools `hb_caps_get` / `hb_caps_set` (autonomous limit lowering, operator confirmation required for raising). Rejections write `DecisionLog` and `KernelAuditLog`.
  - **Verified Order Execution Path & StockNow Integration:**
    - Full execution pipeline: acquire lock -> state checkpoint -> preflight validation -> call `StockNowAdapter.execute_order` on live browser session -> verify fill against StockNow ledger -> commit local ledger update *only* on verified receipt match -> rollback on failure.
    - Two-step confirmation token in `LIVE_HOURS`, dry_run=true default, explicit operator confirmation required.
  - **Preflight Verification & Safe Backup Suite (`scripts/preflight.py`, `scripts/backup_db.py`, `scripts/restore_db.py`):**
    - `scripts/preflight.py`: Prints a 10-point GO / NO-GO readiness audit table covering Gateway up, Primary Model & Fallback chain, 22 plugin tools, `KERNEL_TOKEN`, StockNow session, 0.00 portfolio drift, trading mode, risk caps, automation state, and fresh verified database backup. Exits with code 1 on any NO-GO.
    - `scripts/backup_db.py` & `scripts/restore_db.py`: Atomic timestamped copies of `hummingbird.db` via SQLite online backup API with `PRAGMA integrity_check` verification.
  - **Comprehensive MVP Rules Test Suite (`tests/test_mvp_rules.py`):**
    - 12 comprehensive unit tests covering L1 before L2 priority, base GSC observation guard, T+2 settlement, no-loss hurdle, 25% sequential profit sells, 50/50 pullback split, caps/budget, kill switch, polling vs onscreen-live decision equivalence, single-writer lock sharing, restart idempotency, and trading mode market-hours gating (117 total passing tests).

---

### ✅ Sprint 3: Production Hardening, Dual Transport & UI Refinements (Steps 1–10)

- [x] **Step 1: Configurable Target Portfolios:**
  - `.env` keys `STOCKNOW_LIVE_PORTFOLIO_ID=164580` and `STOCKNOW_TEST_PORTFOLIO_ID` with hard two-member allowlist.
  - Test Mode sends orders/syncs strictly to test portfolio; Live Hours strictly to 164580.
  - Scoped SQLite ledger, lots, cap usage, and daily budget by `portfolio_id`.
- [x] **Step 2: Write Contract Specification & Capture on TEST Portfolio:**
  - Hard guard refusing any POST unless portfolio id equals test id (`test_stocknow_write_guard.py`).
  - Recorded write contract (`/buy`, `/sell`) and error behaviors in `documentation/STOCKNOW_SITE_MAP.md`.
- [x] **Step 3: Direct Async StockNow API Client (`backend/adapters/stocknow_api.py`):**
  - High-performance `httpx.AsyncClient` with in-memory tokens, exp margin re-login, ETag caching, typed error handling.
- [x] **Step 4: StockNow Executor & Dual Transports (`backend/adapters/stocknow_executor.py`):**
  - Dynamic transport selection (`ApiTransport` Background vs `BrowserTransport` Onscreen). Zero paper fallback in live mode.
  - State checkpoints, explicit trade dates, and rollback on broker rejection.
- [x] **Step 5: Direct API Market & Portfolio Sync:**
  - Fast API sync for `/instruments`, `/user/lists`, 7–15 session candles, and portfolio reconciliation diffs.
- [x] **Step 6: Master Automation Switch & Run Modes:**
  - Master OFF/ON switch with separate Emergency Kill switch.
  - Run modes: "Onscreen Live" vs "Background 24/7" with `Go Background` / `Go Onscreen` handoffs.
  - Labeled `PREVIEW` execution when OFF with Decision stream audit logs.
- [x] **Step 7: Autonomous Reliability, Circuit Breaker & Autostart:**
  - Windows Task Scheduler autostart (`scripts/install_autostart.ps1`) with failure restart.
  - SQLite minute heartbeat, Telegram dead-man alerts, 14:45 daily summary, and 3-failure circuit breaker.
- [x] **Step 8: UI Alignment & 4 Balanced Settings Cards:**
  - Standardized terminology "Live Hours" and "Test Mode".
  - Topbar single status chip (e.g. `ON · Background · Live Hours`).
  - 4 balanced cards in Settings (Automation, StockNow Connection, Safety Caps, Hermes Brain) plus collapsed Advanced card.
- [x] **Step 9: Portfolio Header Badge & Watchlist Status:**
  - `#portfolio-header-badge` displaying `LIVE STOCKNOW <name> #<id>` with drift warning.
  - Watchlist status pills (`LIVE`, `LAST CLOSE`, `STALE`, `NO DATA`) with direct retry link.
  - Trade ledger tagged with `STOCKNOW RECEIPT` or `PAPER FILL`.
- [x] **Step 10: Hermes Order Preview Chat Card & Execution Lifecycle:**
  - Chat preview cards for `hb_place_order` with symbol, side badge, qty, price, 0.5% fee, mode, portfolio, and cap usage.
  - Interactive Confirm / Cancel buttons (operator never types parameters).
  - Transition to verified receipt state or red `live submission failed: <reason>` with guaranteed no ledger change.
  - 203 automated test suites passing.
- [x] **Step 11: Documentation Consolidation & Codebase Map Regeneration:**
  - Consolidated `documentation/` to exactly 4 canonical files (`About_Project.md`, `Backlog.md`, `CODEBASE_MAP.md`, `STOCKNOW_SITE_MAP.md`).
  - Fixed `scripts/generate_code_map.py` discovery to exclude submodules (`vendor/hermes-agent`), `node_modules/`, `.venv/`, `backend/data/`, `scratch/`, etc.
  - Suffix-only parsing with long-tail grouping into `*other*`, zero `.png`, exact 10 `.md`, and low-hundreds `.py`.
  - Mapped 108 JS controller functions (`app.js`, `charts.js`, `hermes_ui.js`), 300 HTML element IDs, and all 22 registered `hb_*` plugin tools with line references.
  - 211 automated test suites passing (including `tests/test_code_map.py`).
- [x] **Step 12: Live Reconciliation, Anti-Typo Guard, Native Chrome & MVP Verification:**
  - `Native Google Chrome Launch`: Prioritized user-installed Google Chrome over sandboxed "Chrome for Testing" (`channels_to_try = ["chrome", "msedge", None]`), preserving extensions, logins, and standard web compatibility.
  - `Anti-Typo Price Sanity Guard`: Built `check_price_sanity` enforcing preflight validation blocking orders deviating > 1.5% from market LTP (`PRICE_OUT_OF_RANGE`).
  - `Shared/Single Portfolio ID Support`: Removed strict mismatch constraint between test and live IDs, allowing single-portfolio accounts (`#164580`) to test safely without `TEST_PORTFOLIO_NOT_CONFIGURED` rejections.
  - `SQLite Nullable Decision Log`: Migrated `decision_logs.cycle_id` to nullable and removed invalid `FOREIGN KEY(symbol)` constraints, preventing SQLite `IntegrityError` during manual/Hermes order logging.
  - `Live Quote Sync Reconciliation`: Synced SQLite `state.clock_date` with latest quote date (`quote_on`), ensuring live daily changes (+9.92% for MATINSPINN) match StockNow real-time data instead of defaulting to +0.00%.
  - `Preloaded 475+ DSE Catalog`: Background catalog preloading on boot for instant symbol search, heatmap breadth, and ticker lookup without requiring manual tab interaction.
  - `MVP Verification Tracking`: Established and executed structured end-to-end MVP verification plan in `documentation/MVP_VERIFICATION.md`.

---

### 📋 Open Items & MVP Audit Reconciliation

Reconciliation of all audit findings and architectural items from historical MVP audits and recent sprint passes:

| Item / Finding | Severity | Status | Evidence / Resolution |
| :--- | :---: | :---: | :--- |
| **1. `hb_place_order` disconnect from StockNow virtual execution** | CRITICAL | **FIXED** | Kernel `post_order` calls `StockNowAdapter.execute_order`, which delegates to `StockNowExecutor` (`BrowserTransport` for Onscreen mode, `ApiTransport` for Background mode). Verified by `tests/test_stocknow_executor.py` and `tests/test_chat_order_preview_card.py`. |
| **2. Hermes Gateway API daemon offline on port 8642** | HIGH | **OPEN / OPERATIONAL** | Hermes Gateway (`127.0.0.1:8642`) must be started via unified supervisor `python run.py` (or Windows Task Scheduler logon task `scripts/install_autostart.ps1`). Monitored and verified by `scripts/preflight.py` Check 1. |
| **3. Local ledger mutates before StockNow receipt verification** | HIGH | **FIXED** | Atomic checkpoint taken prior to external order dispatch (`CheckpointManager.create_checkpoint`). Local SQLite `TaxLot` and `TradeLog` records are mutated strictly after fill verification matches the broker receipt (`verify_fill`). On rejection or timeout, state is rolled back automatically (`tests/test_stocknow_executor.py:test_ledger_mismatch_restores_checkpoint`). |
| **4. Kernel `POST /k/order` lacks internal DSE market hours gate** | MEDIUM | **FIXED** | `backend/kernel_api.py:920-930` checks `is_dse_market_open(settings=settings)` in `LIVE_HOURS` mode, rejecting off-hours orders with HTTP 422 `MARKET_CLOSED`. Verified by `tests/test_trading_mode.py`. |
| **5. Unauthenticated StockNow DOM failure silently defaults to Paper mode** | MEDIUM | **FIXED** | Zero paper fallback in live mode. `BrowserTransport` and `ApiTransport` in `backend/adapters/stocknow_executor.py` raise `NotAuthenticatedExecutionError` on missing or expired tokens, triggering checkpoint rollback. Verified by `tests/test_stocknow_executor.py:test_logged_out_order_fails_on_browser_transport`. |
| **6. Stale `--yolo` mention in documentation** | LOW | **FIXED** | All mentions of `--yolo` and subprocess CLI fallback purged from `hermes_bridge.py`, tests, and documentation. |
| **7. Telegram Bot push notifications for trade alerts** | MEDIUM | **OPEN** | Autonomous real-time push alerts on automated Buy, Sequential Tier Sell, 50/50 Pullback Split, or Crash Quarantine events queued for Sprint 4. |
| **8. Multi-Broker Live Adapters (LankaBangla / Shanta)** | MEDIUM | **IN PROGRESS** | Captured live verified site map & execution blueprint in [`documentation/TRADEXPRESS_CONTEXT.md`](TRADEXPRESS_CONTEXT.md) after first real DSE execution (LankaBangla Client `H9210`: `Buy BANKASIA'PB : 9 @ 17.90 : Filled` at `14:01:35`). Passive Playwright adapter architecture drafted for Version 0.3. |

---

### ✅ Sprint 4 (Completed): TradeXpress Passive CDP Sniffer, Decoupled Broker Interface & DSE Schedule Lock

- [x] **Exact GSC / L1 / L2 Definitions Lock:**
  - Updated `plugins/humming_bird/skills/gsc_tiers/SKILL.md` (v1.2.0) with explicit tier profiles:
    - **GSC:** Giant Stable Companies master observation pool (survival guarantee, not current profit; `WAIT_OBSERVATION_ONLY`, no blind auto-buy).
    - **L1 (`GSC_L1`):** Safe primary active buy list (Priority #1), subset of GSC with multi-week upward profitability curves.
    - **L2 (`GSC_L2`):** Risky short-term swing/scalp list (Priority #2), **NOT necessarily GSC** — vetted non-Z Category A/B stocks with early green momentum. Smaller position caps and tighter risk guards.
    - **Hard Exclusions:** Strictly blacklist `Z`-category and `SPOT` settlement stocks.
- [x] **TradeXpress Passive Security Skill (`tradexpress_passive_safety/SKILL.md`):**
  - Enforced 100% passive network sniffing via CDP (`connect_over_cdp("http://127.0.0.1:9222")`).
  - Zero automated login, zero HTTP scraping, zero page reloads on LankaBangla portals.
  - Two-Stage Graduation Gate: Stage 1 (`SHADOW_DUMMY`) with 0 real BDT risk vs Stage 2 (`TRADEXPRESS_LIVE`) with mandatory 2-step Limit confirmation.
  - Verified DSE Schedule: `10:00–14:00` Continuous, `14:00–14:10` Post-Closing exact LTP only, `14:10` Market Close.
  - Self-learning boundary protecting immutable kernel invariants (No-Loss, T+2, Z/SPOT, Daily Caps, Kill Switch).
- [x] **Agent Operating Guidelines (`AGENTS.md`):**
  - Added dedicated TradeXpress Passive-Only & Strategy Lock section for all coding agents.
  - Added 2-Touchpoint Hard Broker Firewall Rule and Changelog hygiene requirement.
- [x] **Read-Only Passive CDP Inspector Script (`scripts/inspect_tradexpress_passive.py`):**
  - Non-intrusive probe attaching to active `itrade.lbsbd.com` tab over CDP (port 9222).
  - Passive WebSocket frame listener (`page.on("websocket")`) with secret redaction (`SecretGuard.redact_secrets`).
  - Read-only DOM snapshot of Market Watch headers, watchlist tabs, order controls, and `S2` badge tooltips.
- [x] **Decoupled Broker Adapter Interface (`backend/adapters/`):**
  - Modular broker abstraction (`BaseBrokerAdapter`, `TradeXpressAdapter`) allowing plug-and-play switching between StockNow virtual and TradeXpress live/shadow.
- [x] **DSE Schedule & Commission Math Realignment:**
  - Aligned market scheduler and pre-tool hooks to official DSE hours (`10:00–14:10 Asia/Dhaka`).
  - Incorporated round-trip Commission + 15% VAT breakdown math (`calculate_broker_fee_breakdown`, `round_trip_breakeven_price`).
- [x] **Strict `PUBLIC` + Category `A`/`B` Order Filter:**
  - `OrderSafetyValidator` enforcing preflight rejection of `SPOT` settlement and `Z`-category instruments, market orders, and circuit violations.
- [x] **Knowledge Graph Generator & Changelog System (`scripts/generate_code_map.py`, `documentation/CHANGELOG.md`):**
  - Enriched `CODEBASE_MAP.md` into 7-section Knowledge Graph with automated ASCII file tree, reverse dependency blast-radius radar, full ORM schema x-ray, Pydantic contracts registry, and Hermes-to-Kernel tool graph.
  - Established project changelog adhering to "Keep a Changelog" standard.

---

### 🧪 Sprint 5A (Active): TradeXpress Passive Feed Bridge, Realistic SHADOW_DUMMY Simulator, L1/L2 Strategy & Hermes TradeReflectionLog

- [ ] **TradeXpress Passive Feed Bridge:**
  - Ingest live passively sniffed TradeXpress quotes and Level-2 Bid/Offer order depth via CDP sniffer into local memory cache and SQLite.
  - Real-time tick updates with zero active polling, zero HTTP requests, and zero page reloads on LankaBangla portals.
- [ ] **Realistic `SHADOW_DUMMY` Mirror Simulator:**
  - Simulate realistic limit order fills against real passively sniffed exchange Level-2 depth with 0 real BDT capital risk.
  - Full T+2 settlement tracking, conservative `0.50%` round-trip commission math, and zero-drift ledger balancing.
- [ ] **L1 / L2 Strategy Pipeline:**
  - Prioritize `GSC_L1` (safe multi-week recovery curves) as Priority #1 and `GSC_L2` (early green swing scalps) as Priority #2.
  - Base `GSC` preserved strictly in observation-only mode (`WAIT_OBSERVATION_ONLY`, no blind buys).
- [ ] **Post-Market Hermes Reflection Loop & `TradeReflectionLog`:**
  - Automated post-14:10 reflection cycle analyzing daily signal performance, execution slippage, and canary theses.
  - Structured storage in SQLite `trade_reflections` table (`TradeReflectionLog`) and self-learning memory updates in `memories/MEMORY.md`.

---

### 🎨 Sprint 5B: Trading Cockpit V1 TradeXpress 3-Pane Redesign, Resizable Hermes Sidebar & Safety Badging

- [ ] **TradeXpress 3-Pane Cockpit Layout:**
  - Professional DSE workstation layout mirroring TradeXpress NetPlus structure:
    - Top/Left: Market Watch, Watchlist Tiers (`GSC`, `L1`, `L2`), and Heatmap.
    - Bottom Left: New Order Entry Ticket with 2-step verification preview.
    - Bottom Right: Order List, Active Portfolio, and Account Summary tabs.
- [ ] **Resizable Hermes Copilot Sidebar:**
  - Interactive draggable/resizable chat sidebar with docked, collapsed, and expanded split states.
  - Conversational order preview cards with 1-click Confirm / Cancel interaction tokens.
- [ ] **Safety Badging & Risk Meter Visualizations:**
  - Prominent visual badges for active mode (`SHADOW_DUMMY` vs `TRADEXPRESS_LIVE`) and 2-Touchpoint Hard Broker Firewall status.
  - Real-time DSE session clock badge (`CONTINUOUS 10:00-14:00`, `POST_CLOSING 14:00-14:10`, `CLOSED`) and daily risk budget gauge meters.

---

### 🏦 Sprint 6: Production Graduation to Live TradeXpress 2-Step Execution & iBroker EOD Audit

- [ ] **Production TradeXpress 2-Step Executor (`TRADEXPRESS_LIVE` Mode):**
  - Operator-permissioned graduation gate enabling live order dispatch to DSE.
  - Automated 2-step execution: `New Order - <SYMBOL>'PB` -> read-back verification -> `Confirm Order` modal click.
  - High-priority fill verification from top toast (`Filled`) and `Order List` table.
- [ ] **iBroker (`ibroker.lbsbd.com`) EOD Reconciliation:**
  - Daily reconciliation sync between iBroker `Portfolio Live` (`Total Qty`, `Saleable Qty`, `AVG Price`, `Unrealized Gain/Loss`) and local SQLite ledger.
- [ ] **Operator Guardrails & Fail-Safe Circuit Breaker:**
  - Enforce per-order and daily BDT budget caps, anti-typo price sanity guard (±1.5% LTP), and instant kill switch.