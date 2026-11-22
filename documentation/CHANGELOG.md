# Changelog

All notable changes to the Project Humming Bird (Trading Cockpit) repository will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v1.0.0-dev] - Unreleased (Trading Cockpit V1 Branch - Sprints 4A, 4B, 4C, 5A, 5B)

### Added
- **Trading Cockpit V1 UI Terminal (`frontend/index.html`, `frontend/styles.css`, `frontend/theme_light_hermes.css`, `frontend/tradexpress_ui.js`):** Exact 3-pane TradeXpress 2.0 replica layout with viewport-locked app shell, top header telemetry strip (`CLIENT A/C: H9210 (Shadow)`, `BUYING POWER`, `GAIN / LOSS`, market clock widget, and mode switch).
- **13-Column Market Watch Grid (`frontend/app.js`):** Comprehensive table displaying `Symbol`, `Curve (7–15d)`, `LTP ৳`, `% Chg`, `Bid / Qty` (emerald tint), `Offer / Qty` (rose tint), `Cat / Signal`, `Day` (hold-day indicator), `Matured / Qty`, `Bought Avg`, `Bought Total`, `Sell Total`, and `Net Profit`. Supports instant symbol selection on click, plus filters for hiding Z/SPOT stocks and filtering held-only positions.
- **TradeXpress Order Ticket & 5-Level Depth (`frontend/tradexpress_ui.js`):** Buy/Sell segmented toggle, live 5-level Bid/Offer depth table with click-to-populate limit price and quantity, quick quantity steppers (25%, 50%, 100%), and real-time order value and estimated fee preview.
- **2-Step Limit Confirmation Modal (`#tx-confirm-order-modal`):** Mandatory step-2 confirmation modal with side-themed color banners (Green for BUY, Red for SELL), comprehensive fee breakdown, and explicit execution approval.
- **4-Pane Monitor Panel:** Sub-tabs for `Order List` (with cancelation action for queued shadow orders), `Portfolio` (with Quick-Sell `↓` shortcuts), `Account Summary` (with interactive SVG Asset Allocation Donut chart), and `Order Search`.
- **Secondary Workspace Navigation (`#tx-main-nav`):** Instant switching between `Trade`, `Heat Map`, `Auto Rules & T+2`, `Ledger`, `Learning`, and `Settings` without page reloads.
- **Enriched Portfolio Snapshot Microstructure (`backend/portfolio.py`):** Injected additive microstructure fields (`bid`, `bid_qty`, `offer`, `offer_qty`, `min_limit`, `max_limit`, `settlement_type`, `symbol_category`, `tradexpress_symbol`) and position telemetry (`avg_bought_price`, `bought_total`, `sell_total_net`, `net_profit_bdt`, `net_profit_pct`, `hold_day_label`) alongside top-level `buying_power_bdt` and `unsettled_sales_bdt`.
- **New Test Suite (`tests/test_tradexpress_ui_v1.py`):** Full automated verification of HTML structure, enriched snapshot payload, 2-step limit order preview -> commit flow, and shadow order cancellation.
- **TradeXpress Passive Feed Bridge (`backend/adapters/tradexpress/passive_feed.py`):** Pure Ember DOM table parsers (`parse_ember_market_watch_rows`, `parse_ember_portfolio_rows`, `parse_account_summary_dict`) and passive snapshot ingestion updating SQLite company profiles, Level-2 depth, and organic 30-day price history bars with zero active network traffic.
- **Operator Ingestion Guidance (`get_feed_health_and_guidance`):** Real-time feed health evaluator diagnosing stale or missing tabs and generating clear step-by-step UI clicking instructions for the operator.
- **Realistic `SHADOW_DUMMY` Order-Book Simulator (`backend/adapters/tradexpress/shadow_simulator.py`):** Realistic limit order simulator matching against live passively sniffed exchange Bid/Offer depth. Supports immediate fills, resting queued orders (`ShadowOrder`), post-fill `reconcile_queued_orders` on price drops, and automatic expiry at session close (`14:10`).
- **T+2 Shadow Settlement & Buying Power Balance:** Tracks T+2 settlement maturity, enforces strict no-loss rules, immediately credits gross sell proceeds to `unsettled_sales_bdt` & Buying Power, and records atomic `KernelStateCheckpoint` snapshots before state mutations.
- **L1 / L2 Strategy & Hard Exchange Safety (`backend/engine/auto_trader.py`):** Enforces hard exclusions on `Z`-category instruments, `SPOT` settlement stocks, and upper-circuit locked equities. Caps `GSC_L2` exposure to `<= 15%` with tighter profit-taking scalp tiers (`+1.5%`, `+2.5%`, `+4.0%`).
- **Trade Learning & Reflection Engine (`backend/database.py`):** SQLite persistence in `trade_learning_logs` table (`TradeLearningLog`) recording every trade execution, outcome, and skipped candidate.
- **TradeXpress Fast-Path & Learning API Routes (`backend/routes_tradexpress.py`, `backend/kernel_api.py`):** Endpoints for passive snapshot ingestion, shadow order placement (2-step preview and fill), queued order querying, and feed status/learning reviews (`GET /k/feed-status`, `GET /k/learning/summary`).
- **New Hermes Agentic Tools (`hb_feed_status`, `hb_learning_review`):** Expanded registered toolset from 22 to 24 tools across `plugins/humming_bird/`.
- **Archive Branch Setup:** Archived StockNow virtual automation baseline permanently to branch `stocknow-automation`. Active development transitioned to branch `trading-cockpit-v1`.
- **Master TradeXpress 2.0 & iBroker Context Blueprint (`documentation/TRADEXPRESS_CONTEXT.md`):** Complete site map, Ember.js DOM hierarchy, dual WebSockets (`streaming-api` and `wsqs`), and operational protocols.
- **First Real Live DSE Trade Milestones (Client Code `H9210`):**
  - First Live Buy: `Buy BANKASIA`PB : 9 @ 17.90 : Filled` at `14:01:35` (Post-Closing session).
  - First Live Sell (Round-Trip Milestone): `Sell BANKASIA`PB : 9 @ 18.40 : Filled` at `13:33:36` (Continuous session, Order Value: `165.60 BDT`).
- **2-Touchpoint Hard Broker Firewall Rule:** Strict operational constraint codified in `AGENTS.md` and `TRADEXPRESS_CONTEXT.md` permitting only passive CDP sniffing (port 9222) and explicit 2-step limit confirmation. Zero automated login, zero credential handling, and zero active scraping.
- **Read-Only Passive CDP Inspector (`scripts/inspect_tradexpress_passive.py`):** Non-intrusive probe attaching to operator's active browser session via Chrome DevTools Protocol to sniff incoming WebSocket frames with automatic secret redaction.
- **Decoupled Broker Adapter Abstraction (`backend/adapters/base.py`):** Abstract interfaces (`MarketFeedAdapter`, `BrokerOrderExecutor`) and data classes (`MarketQuote`, `PortfolioHolding`) providing unified order validation, quote querying, and two-stage execution (`SHADOW_DUMMY` vs `TRADEXPRESS_LIVE`).
- **Broker Fee & Breakdown Math (`backend/engine/money.py`):** Precise arithmetic (`calculate_broker_fee_breakdown`, `round_trip_breakeven_price`) incorporating verified `~0.40%` commission, `15%` VAT on commission, and round-trip breakeven hurdle.
- **TradeXpress Safety Validator (`validate_tradexpress_order_safety` in `backend/adapters/base.py`):** Preflight safety guard blocking `SPOT` settlement stocks, `Z`-category instruments, market orders, non-`DAY` TIF, circuit limit violations, and off-hour/post-closing price discrepancies.
- **Symbol Normalization:** Robust conversion supporting DSE Public Board backtick format (`` `PB ``), e.g. `BANKASIA` -> ``BANKASIA`PB``.
- **Knowledge Graph Generator (`scripts/generate_code_map.py`):** Generates 7 enriched sections in `documentation/CODEBASE_MAP.md` including automated ASCII repository tree, reverse dependency blast-radius radar, full SQLAlchemy schema X-ray, Pydantic contract registry, and Hermes-to-Kernel route call graph.
- **Test Cache Isolation:** Added autouse cache cleaning fixture in `tests/conftest.py` preventing quote and share cache cross-test contamination.

### Changed
- **Verified DSE Market Schedule Realignment:** Aligned market scheduler, hooks, and preflight checks to official DSE trading hours: `10:00–14:10 Asia/Dhaka` (`10:00–13:59` Continuous, `14:00–14:10` Post-Closing exact LTP only, `14:11+` Closed).
- **GSC / L1 / L2 Hierarchy Clarification:** Updated `plugins/humming_bird/skills/gsc_tiers/SKILL.md` (v1.2.0) defining GSC as master observation pool (`WAIT_OBSERVATION_ONLY`), L1 as primary active turnaround buy list, and L2 as non-GSC swing scalp list.
- **Project Documentation Streamlining:** Replaced static 150-line manual file tree in `documentation/About_Project.md` Section 9 with a dynamic pointer to the auto-generated file tree in `documentation/CODEBASE_MAP.md`.

### Fixed
- **Cockpit 2-Column Grid Layout Crush Fix (`frontend/styles.css`, `frontend/theme_light_hermes.css`, `frontend/index.html`):** Resolved 64px left squash by updating `.app-shell` to strictly 2 columns (`minmax(0, 1fr) var(--hermes-width, 380px)`), hiding legacy `.nav-rail`, and moving it to `.test-compat-hidden`.
- **Restored Complete Hermes Sidebar & View Settings (`frontend/index.html`):** Restored all 4 working Hermes tabs (Chat, Topics, Changes, Skills), `#model-dropup-menu`, `<textarea id="chat-input">`, quick prompts, crons, memory preview, and full `#view-settings` cards (automation, passive feed health, trading mode, StockNow connection, risk caps, brain cards).
- **Restored Deep Trend Modal & Secondary Views (`frontend/index.html`):** Restored all 8 fundamental metrics (`#fund-pe` through `#fund-cat`), interactive what-if simulator (`#modal-sim-slider`), `#view-heatmap-wrap`, `#view-rules-wrap`, and `#view-ledger-wrap`.
- **Added Playwright Headless Layout Verification Suite (`tests/test_v1_layout_playwright.py`):** Automated visual viewport bounding-box assertions at 1440x900 verifying workspace width (`1060px`), Hermes dock (`380px`), Market Watch (`1040x381px`), Order Ticket & Monitor Panel (`517x323px`), tab transitions, row selection, and modal lifecycle.
- **Intraday Fee Display Quirk Handling:** Recorded and accommodated TradeXpress UI bug where Order Ticket and Confirmation modal display `Commission: 0.00` and `VAT: 0.00` intraday (real fee ~0.40% settled at EOD back-office clearing; local 0.50% hurdle enforced).
- **Instant Buying Power Credit on Sell:** Documented immediate gross credit of sell proceeds (`165.60 BDT`) into active Buying Power upon execution for intraday re-investment.
- **SPOT Instrument Rejection Modal:** Documented broker error modal (`Order cannot be placed for SPOT instrument`) observed on `ASIATICLAB`PB.
- **Test Suite Sanity Alignments:** Resolved price sanity guard range deviations in `test_chat_order_preview_card.py` and test portfolio fallback configuration in `test_portfolio_config.py`.

---

## [v0.1.0] - 2026-11-15

### Added
- **Core Quantitative Backend & Ledger:**
  - FastAPI web service with SQLite database (WAL mode) and SQLAlchemy ORM models.
  - 3-bucket rolling T+2 pipeline (`t2_ledger.py`) tracking Buckets A, B, and C across Bangladesh trading calendar.
  - Human-like curve analyzer (`curve_analyzer.py`) with support, mid-range, resistance bands, and Crash Quarantine guard.
  - Sequential "no-regret" profit-scaling engine (`sequential_seller.py`) with 25%/25%/25%/25% runner, 50/50 pullback split, and recovery hold.
  - Deterministic auto-trader orchestrator (`auto_trader.py`) with single-writer concurrency lock and atomic state rollback (`KernelStateCheckpoint`).
  - Standalone local Trading Kernel API (`backend/kernel_api.py`) bound to `127.0.0.1` and protected by `X-Kernel-Token`.
  - Zero-secret isolation boundary (`backend/secret_guard.py`) scrubbing credentials from logs and telemetry.
- **Official Nous Research Hermes Agent Integration:**
  - Native Hermes plugin (`plugins/humming_bird/`) with 22 tools and procedural skills (`canary_90_10`, `gsc_tiers`, `sequential_no_regret`, `stocknow_dse_quirks`).
  - Streaming SSE bridge (`backend/hermes_bridge.py`) proxying chat requests to Hermes Gateway API server (`/v1/chat/completions`).
  - Real-time tool-call cards rendered in chat with tool names, input arguments, running/done status badges, and collapsible execution output.
  - Autonomous native cron schedules (`~/.hermes/cron/jobs.json`) with `Asia/Dhaka` timezone.
- **Cockpit Single-Page Interface (`frontend/`):**
  - Dark-mode terminal UI with DSE sector treemap, SVG trend curves, interactive crosshairs, what-if profit calculator, and dark/light theme switcher.
  - ScrollSpy navigation rail, sticky top navbar with live market clock, and dedicated Settings page.
  - 4 balanced Settings cards (API Keys & Tokens, Broker & Ingestion Mode, Market Hours & Trading Mode, Safety Caps & Budget).
  - Hermes chat order preview cards with 2-step confirmation and cap usage telemetry.
- **System Reliability & Automation:**
  - Supervisor launcher script (`run.py`, `run.bat`, `run.sh`).
  - Windows Task Scheduler logon autostart installer (`scripts/install_autostart.ps1`).
  - 10-point readiness audit (`scripts/preflight.py`) and atomic SQLite backup/restore utilities (`scripts/backup_db.py`, `scripts/restore_db.py`).
  - Telegram bot daemon for real-time notifications, daily summaries, and remote kill switch.
  - Automated test suite covering 237 passing tests.
