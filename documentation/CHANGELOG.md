# Changelog

All notable changes to the Project Humming Bird (Trading Cockpit) repository will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v0.2.0-dev] - Unreleased (Sprints 4A, 4B, 4C)

### Added
- **Master TradeXpress 2.0 & iBroker Context Blueprint (`documentation/TRADEXPRESS_CONTEXT.md`):** Complete site map, Ember.js DOM hierarchy, dual WebSockets (`streaming-api` and `wsqs`), and operational protocols.
- **First Real Live DSE Trade Milestones (Client Code `H9210`):**
  - First Live Buy: `Buy BANKASIA`PB : 9 @ 17.90 : Filled` at `14:01:35` (Post-Closing session).
  - First Live Sell (Round-Trip Milestone): `Sell BANKASIA`PB : 9 @ 18.40 : Filled` at `13:33:36` (Continuous session, Order Value: `165.60 BDT`).
- **2-Touchpoint Hard Broker Firewall Rule:** Strict operational constraint codified in `AGENTS.md` and `TRADEXPRESS_CONTEXT.md` permitting only passive CDP sniffing (port 9222) and explicit 2-step limit confirmation. Zero automated login, zero credential handling, and zero active scraping.
- **Read-Only Passive CDP Inspector (`scripts/inspect_tradexpress_passive.py`):** Non-intrusive probe attaching to operator's active browser session via Chrome DevTools Protocol to sniff incoming WebSocket frames with automatic secret redaction.
- **Decoupled Broker Adapter Abstraction (`backend/adapters/base_broker.py`, `backend/adapters/tradexpress_adapter.py`):** Abstract base class (`BaseBrokerAdapter`) and TradeXpress implementation providing unified order validation, quote querying, and two-stage execution (`SHADOW_DUMMY` vs `TRADEXPRESS_LIVE`).
- **Broker Fee & Breakdown Math:** Detailed calculations in `tradexpress_adapter.py` (`calculate_broker_fee_breakdown`, `round_trip_breakeven_price`) incorporating `0.40%` commission, `15%` VAT on commission, and exchange fees.
- **TradeXpress Safety Validator (`OrderSafetyValidator`):** In-kernel preflight guard blocking `SPOT` settlement stocks, `Z`-category instruments, market orders, circuit limit violations, and off-hour/post-closing price discrepancies.
- **Symbol Normalization:** Robust conversion supporting DSE Public Board backtick format (`` `PB ``), e.g. `BANKASIA` -> ``BANKASIA`PB``.
- **Knowledge Graph Generator (`scripts/generate_code_map.py`):** Generates 7 enriched sections in `documentation/CODEBASE_MAP.md` including automated ASCII repository tree, reverse dependency blast-radius radar, full SQLAlchemy schema X-ray, Pydantic contract registry, and Hermes-to-Kernel route call graph.
- **Test Cache Isolation:** Added autouse cache cleaning fixture in `tests/conftest.py` preventing quote and share cache cross-test contamination.

### Changed
- **Verified DSE Market Schedule Realignment:** Aligned market scheduler, hooks, and preflight checks to official DSE trading hours: `10:00–14:10 Asia/Dhaka` (`10:00–13:59` Continuous, `14:00–14:10` Post-Closing exact LTP only, `14:11+` Closed).
- **GSC / L1 / L2 Hierarchy Clarification:** Updated `plugins/humming_bird/skills/gsc_tiers/SKILL.md` (v1.2.0) defining GSC as master observation pool (`WAIT_OBSERVATION_ONLY`), L1 as primary active turnaround buy list, and L2 as non-GSC swing scalp list.
- **Project Documentation Streamlining:** Replaced static 150-line manual file tree in `documentation/About_Project.md` Section 9 with a dynamic pointer to the auto-generated file tree in `documentation/CODEBASE_MAP.md`.

### Fixed
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
