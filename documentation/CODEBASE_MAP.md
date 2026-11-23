# 🗺️ Codebase AST Knowledge Graph & Architecture Radar

> Auto-generated via `scripts/generate_code_map.py` (Zero-dependency stdlib AST inspection) on **2026-11-23 14:52:21 UTC**.
> **Core Strategy Invariants:**
> - **Strict No-Loss Guarantee:** Never sell at net loss (< 0% net P/L after round-trip 1.00% fees).
> - **Sequential No-Regret Selling:** 25% / 25% / 25% profit tiers (+1.5%, +3.5%, +6.0% net) + 25% runner.
> - **50/50 Pullback Split & Recovery Hold:** 50% profit lock on >= 3% pullback from peak; 50% recovery hold.
> - **3-Bucket Rolling Capital:** Sunday–Thursday DSE sessions partitioned into Buckets A, B, and C (T+2 rolling maturity).
> - **Crash Quarantine & 90/10 Canary Split:** Emergency quarantine on falling-knives; 90% profit exit, 10% observation probe. Hold if unrealized loss.
> - **TradeXpress 2-Touchpoint Hard Broker Firewall:** Passive CDP sniffing only on port 9222 (read-only, zero active requests); explicit 2-step limit confirmation. Zero automated login, zero credential handling, zero scraping.
> - **Verified DSE Market Schedule:** Continuous `10:00–14:00`, Post-Closing exact LTP only `14:00–14:10`, Market Close `14:10 Asia/Dhaka`.
> **Excluded Paths:** `vendor/`, `node_modules/`, `.venv/`, `venv/`, `.git/`, `__pycache__/`, `backend/data/`, `.pytest_cache/`, `dist/`, `build/`, `scratch/`
> **Pinned Vendor Commit (`vendor/hermes-agent`):** `b777adb7918713e5786cc9d95ad5b854074f2cb6`

---

## 1. Repository Topology, Automated ASCII File Tree & Extension Metrics

### 1.1 Automated Repository Directory Tree

```text
trading-cockpit/
├── backend/
│   ├── adapters/
│   │   ├── tradexpress/
│   │   │   ├── __init__.py
│   │   │   ├── cdp_daemon.py
│   │   │   ├── passive_feed.py
│   │   │   └── shadow_simulator.py
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── stocknow_adapter.py
│   │   ├── stocknow_api.py
│   │   ├── stocknow_client.py
│   │   ├── stocknow_executor.py
│   │   ├── stocknow_market_sync.py
│   │   ├── stocknow_portfolio_sync.py
│   │   └── stocknow_write_guard.py
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── agent_actions.py
│   │   ├── auto_trader.py
│   │   ├── checkpoint.py
│   │   ├── circuit_breaker.py
│   │   ├── curve_analyzer.py
│   │   ├── heartbeat.py
│   │   ├── money.py
│   │   ├── preflight_service.py
│   │   ├── price_guard.py
│   │   ├── scheduler.py
│   │   ├── sequential_seller.py
│   │   ├── signals.py
│   │   ├── t2_ledger.py
│   │   ├── telegram_bot.py
│   │   └── trading_lock.py
│   ├── .env.example
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── hermes_bridge.py
│   ├── kernel_api.py
│   ├── logging_config.py
│   ├── main.py
│   ├── market_map.py
│   ├── portfolio.py
│   ├── requirements-dev.txt
│   ├── requirements.txt
│   ├── routes_auth_settings.py
│   ├── routes_hermes.py
│   ├── routes_stocknow.py
│   ├── routes_tradexpress.py
│   ├── secret_guard.py
│   └── seed.py
├── documentation/
│   ├── About_Project.md
│   ├── Backlog.md
│   ├── CHANGELOG.md
│   ├── CODEBASE_MAP.md
│   ├── STOCKNOW_SITE_MAP.md
│   └── TRADEXPRESS_CONTEXT.md
├── extension/
│   └── tradexpress_mirror/
│       ├── background.js
│       ├── content.js
│       ├── manifest.json
│       ├── popup.html
│       └── popup.js
├── frontend/
│   ├── app.js
│   ├── charts.js
│   ├── favicon.svg
│   ├── hermes_ui.js
│   ├── index.html
│   ├── styles.css
│   ├── theme_light_hermes.css
│   └── tradexpress_ui.js
├── plugins/
│   └── humming_bird/
│       ├── skills/
│       │   ├── canary_90_10/
│       │   │   └── SKILL.md
│       │   ├── gsc_tiers/
│       │   │   └── SKILL.md
│       │   ├── sequential_no_regret/
│       │   │   └── SKILL.md
│       │   ├── stocknow_dse_quirks/
│       │   │   └── SKILL.md
│       │   └── tradexpress_passive_safety/
│       │       └── SKILL.md
│       ├── __init__.py
│       ├── hooks.py
│       ├── plugin.yaml
│       ├── schemas.py
│       └── tools.py
├── scripts/
│   ├── backup_db.py
│   ├── check_dse_market_open.py
│   ├── check_heartbeat.py
│   ├── generate_code_map.py
│   ├── inspect_tradexpress_passive.py
│   ├── install_autostart.ps1
│   ├── install_plugin.ps1
│   ├── open_tradexpress_browser.bat
│   ├── preflight.py
│   ├── restore_db.py
│   ├── verify_chat_card.py
│   └── verify_step10_ui.py
├── tests/
│   ├── fixtures/
│   │   └── stocknow/
│   │       ├── har/
│   │       │   ├── stocknow_exploration.har
│   │       │   └── stocknow_write_contract.har
│   │       ├── config.json
│   │       ├── exploration_meta.json
│   │       ├── history_candles.json
│   │       ├── instruments.json
│   │       ├── portfolio_ledger.json
│   │       ├── portfolio_show.json
│   │       ├── portfolios.json
│   │       ├── sectors.json
│   │       ├── user.json
│   │       ├── user_lists.json
│   │       ├── write_contract_ledger.json
│   │       └── write_contract_results.json
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_chat_order_preview_card.py
│   ├── test_code_map.py
│   ├── test_engine.py
│   ├── test_hermes_skills_origin.py
│   ├── test_humming_bird_plugin.py
│   ├── test_ingestion_switch.py
│   ├── test_kernel_api.py
│   ├── test_kernel_caps.py
│   ├── test_mvp_rules.py
│   ├── test_order_path.py
│   ├── test_portfolio_badge_and_watchlist.py
│   ├── test_portfolio_config.py
│   ├── test_preflight_and_backups.py
│   ├── test_price_guard.py
│   ├── test_reliability_and_safety.py
│   ├── test_run_modes_decisions.py
│   ├── test_secret_guard.py
│   ├── test_stocknow_api.py
│   ├── test_stocknow_api_sync.py
│   ├── test_stocknow_executor.py
│   ├── test_stocknow_portfolio_164580.py
│   ├── test_stocknow_step2_1.py
│   ├── test_stocknow_step2_2.py
│   ├── test_stocknow_step2_3.py
│   ├── test_stocknow_step2_4.py
│   ├── test_stocknow_step2_5.py
│   ├── test_stocknow_write_guard.py
│   ├── test_test_portfolio_guard.py
│   ├── test_tradexpress_cdp_daemon.py
│   ├── test_tradexpress_extension_mirror.py
│   ├── test_tradexpress_foundation.py
│   ├── test_tradexpress_shadow_and_learning.py
│   ├── test_tradexpress_ui_v1.py
│   ├── test_trading_mode.py
│   └── test_v1_layout_playwright.py
├── .agentignore
├── .cursorignore
├── .env.example
├── .gitignore
├── .opencodeignore
├── AGENTS.md
├── package.json
├── pyproject.toml
├── README.md
├── run.bat
├── run.py
└── run.sh
```

### 1.2 File Count & Lines of Code Breakdown

| Extension / Type | File Count | Total Lines of Code | Description |
| :--- | :--- | :--- | :--- |
| `.py` | 95 | 29,287 | Python Core Kernel, Engine, Tests & Plugins |
| `.css` | 2 | 10,892 | Custom Dark / Light / Terminal Design System |
| `.js` | 7 | 7,039 | Vanilla ES6+ Reactive Terminal Controller & UI |
| `.md` | 13 | 5,726 | Architecture & Strategy Documentation |
| `.json` | 14 | 5,688 | Fixtures & Configuration |
| `.html` | 2 | 1,659 | Single Page Application DOM Structure |
| `.ps1` | 2 | 199 | Windows PowerShell Automation |
| `.bat` | 2 | 73 | Batch Launchers |
| `.yaml` | 1 | 34 | Manifest & Plugin Configuration |
| `.toml` | 1 | 13 | PyProject Configuration |
| `.txt` | 2 | 11 | Dependency Specifications |
| `.sh` | 1 | 9 | Shell Scripts |
| *other* | 9 | 43,383 | Other Configuration, Assets & Dotfiles |
| **TOTAL** | **151** | **104,013** | *Entire Humming Bird Repository* |

---

## 2. Reverse Dependency & Blast-Radius Radar

### 2.1 Module Blast-Radius Risk Radar (Impact Analysis)

| Module File | Direct Dependents | Dependents Count | Blast Radius Risk Level | Direct Consumers (Who Imports This) |
| :--- | :--- | :--- | :--- | :--- |
| [`backend/database.py`](/backend/database.py) | 27 | 27 | **CRITICAL** | `backend/adapters/stocknow_adapter.py`, `backend/adapters/stocknow_executor.py`, `backend/adapters/stocknow_market_sync.py`, `backend/adapters/stocknow_portfolio_sync.py`, `backend/adapters/tradexpress/cdp_daemon.py`, `backend/adapters/tradexpress/passive_feed.py`, `backend/adapters/tradexpress/shadow_simulator.py`, `backend/engine/agent_actions.py`, `backend/engine/auto_trader.py`, `backend/engine/checkpoint.py`, `backend/engine/circuit_breaker.py`, `backend/engine/heartbeat.py`, `backend/engine/preflight_service.py`, `backend/engine/scheduler.py`, `backend/engine/signals.py`, `backend/engine/t2_ledger.py`, `backend/engine/telegram_bot.py`, `backend/kernel_api.py`, `backend/main.py`, `backend/portfolio.py`, `backend/routes_auth_settings.py`, `backend/routes_hermes.py`, `backend/routes_stocknow.py`, `backend/routes_tradexpress.py`, `backend/seed.py`, `scripts/check_heartbeat.py`, `scripts/preflight.py` |
| [`backend/config.py`](/backend/config.py) | 25 | 25 | **CRITICAL** | `backend/adapters/stocknow_portfolio_sync.py`, `backend/adapters/stocknow_write_guard.py`, `backend/adapters/tradexpress/cdp_daemon.py`, `backend/adapters/tradexpress/passive_feed.py`, `backend/adapters/tradexpress/shadow_simulator.py`, `backend/database.py`, `backend/engine/agent_actions.py`, `backend/engine/auto_trader.py`, `backend/engine/circuit_breaker.py`, `backend/engine/heartbeat.py`, `backend/engine/preflight_service.py`, `backend/engine/scheduler.py`, `backend/engine/signals.py`, `backend/engine/t2_ledger.py`, `backend/engine/telegram_bot.py`, `backend/kernel_api.py`, `backend/main.py`, `backend/portfolio.py`, `backend/routes_auth_settings.py`, `backend/routes_hermes.py`, `backend/routes_stocknow.py`, `backend/routes_tradexpress.py`, `backend/seed.py`, `scripts/check_heartbeat.py`, `scripts/preflight.py` |
| [`backend/engine/money.py`](/backend/engine/money.py) | 17 | 17 | **CRITICAL** | `backend/adapters/stocknow_adapter.py`, `backend/adapters/stocknow_market_sync.py`, `backend/adapters/stocknow_portfolio_sync.py`, `backend/adapters/tradexpress/passive_feed.py`, `backend/adapters/tradexpress/shadow_simulator.py`, `backend/engine/agent_actions.py`, `backend/engine/auto_trader.py`, `backend/engine/checkpoint.py`, `backend/engine/curve_analyzer.py`, `backend/engine/sequential_seller.py`, `backend/engine/signals.py`, `backend/engine/t2_ledger.py`, `backend/kernel_api.py`, `backend/main.py`, `backend/portfolio.py`, `backend/routes_tradexpress.py`, `backend/seed.py` |
| [`backend/engine/t2_ledger.py`](/backend/engine/t2_ledger.py) | 11 | 11 | **CRITICAL** | `backend/adapters/stocknow_portfolio_sync.py`, `backend/adapters/tradexpress/shadow_simulator.py`, `backend/engine/agent_actions.py`, `backend/engine/auto_trader.py`, `backend/engine/checkpoint.py`, `backend/engine/heartbeat.py`, `backend/engine/scheduler.py`, `backend/kernel_api.py`, `backend/portfolio.py`, `backend/seed.py`, `scripts/preflight.py` |
| [`backend/adapters/stocknow_client.py`](/backend/adapters/stocknow_client.py) | 8 | 8 | **CRITICAL** | `backend/adapters/__init__.py`, `backend/adapters/stocknow_adapter.py`, `backend/adapters/stocknow_market_sync.py`, `backend/adapters/stocknow_portfolio_sync.py`, `backend/engine/scheduler.py`, `backend/main.py`, `backend/routes_stocknow.py`, `scripts/preflight.py` |
| [`backend/adapters/stocknow_market_sync.py`](/backend/adapters/stocknow_market_sync.py) | 7 | 7 | **HIGH** | `backend/adapters/__init__.py`, `backend/engine/price_guard.py`, `backend/engine/scheduler.py`, `backend/kernel_api.py`, `backend/main.py`, `backend/portfolio.py`, `backend/routes_stocknow.py` |
| [`backend/portfolio.py`](/backend/portfolio.py) | 7 | 7 | **HIGH** | `backend/adapters/stocknow_market_sync.py`, `backend/engine/scheduler.py`, `backend/kernel_api.py`, `backend/main.py`, `backend/routes_hermes.py`, `backend/routes_stocknow.py`, `backend/routes_tradexpress.py` |
| [`backend/adapters/stocknow_adapter.py`](/backend/adapters/stocknow_adapter.py) | 6 | 6 | **HIGH** | `backend/adapters/__init__.py`, `backend/engine/auto_trader.py`, `backend/engine/signals.py`, `backend/kernel_api.py`, `backend/main.py`, `backend/portfolio.py` |
| [`backend/engine/checkpoint.py`](/backend/engine/checkpoint.py) | 6 | 6 | **HIGH** | `backend/adapters/stocknow_portfolio_sync.py`, `backend/adapters/tradexpress/shadow_simulator.py`, `backend/kernel_api.py`, `backend/main.py`, `backend/routes_auth_settings.py`, `backend/routes_hermes.py` |
| [`backend/adapters/stocknow_api.py`](/backend/adapters/stocknow_api.py) | 5 | 5 | **HIGH** | `backend/adapters/stocknow_executor.py`, `backend/adapters/stocknow_market_sync.py`, `backend/adapters/stocknow_portfolio_sync.py`, `backend/kernel_api.py`, `backend/routes_stocknow.py` |
| [`backend/adapters/tradexpress/passive_feed.py`](/backend/adapters/tradexpress/passive_feed.py) | 5 | 5 | **HIGH** | `backend/adapters/tradexpress/cdp_daemon.py`, `backend/adapters/tradexpress/shadow_simulator.py`, `backend/engine/auto_trader.py`, `backend/kernel_api.py`, `backend/routes_tradexpress.py` |
| [`backend/engine/scheduler.py`](/backend/engine/scheduler.py) | 5 | 5 | **HIGH** | `backend/engine/auto_trader.py`, `backend/engine/heartbeat.py`, `backend/kernel_api.py`, `backend/main.py`, `backend/routes_stocknow.py` |
| [`backend/hermes_bridge.py`](/backend/hermes_bridge.py) | 4 | 4 | MEDIUM | `backend/main.py`, `backend/portfolio.py`, `backend/routes_hermes.py`, `scripts/preflight.py` |
| [`backend/adapters/base.py`](/backend/adapters/base.py) | 3 | 3 | MEDIUM | `backend/adapters/tradexpress/passive_feed.py`, `backend/adapters/tradexpress/shadow_simulator.py`, `backend/portfolio.py` |
| [`backend/adapters/tradexpress/cdp_daemon.py`](/backend/adapters/tradexpress/cdp_daemon.py) | 3 | 3 | MEDIUM | `backend/kernel_api.py`, `backend/main.py`, `backend/routes_tradexpress.py` |
| [`backend/adapters/tradexpress/shadow_simulator.py`](/backend/adapters/tradexpress/shadow_simulator.py) | 3 | 3 | MEDIUM | `backend/adapters/tradexpress/cdp_daemon.py`, `backend/engine/auto_trader.py`, `backend/routes_tradexpress.py` |
| [`backend/engine/auto_trader.py`](/backend/engine/auto_trader.py) | 3 | 3 | MEDIUM | `backend/engine/scheduler.py`, `backend/kernel_api.py`, `backend/main.py` |
| [`backend/engine/circuit_breaker.py`](/backend/engine/circuit_breaker.py) | 3 | 3 | MEDIUM | `backend/engine/auto_trader.py`, `backend/kernel_api.py`, `backend/main.py` |
| [`backend/engine/telegram_bot.py`](/backend/engine/telegram_bot.py) | 3 | 3 | MEDIUM | `backend/engine/circuit_breaker.py`, `backend/engine/heartbeat.py`, `backend/main.py` |
| [`backend/engine/trading_lock.py`](/backend/engine/trading_lock.py) | 3 | 3 | MEDIUM | `backend/engine/auto_trader.py`, `backend/kernel_api.py`, `backend/main.py` |
| [`backend/secret_guard.py`](/backend/secret_guard.py) | 3 | 3 | MEDIUM | `backend/adapters/stocknow_client.py`, `backend/adapters/tradexpress/cdp_daemon.py`, `scripts/inspect_tradexpress_passive.py` |
| [`backend/adapters/stocknow_executor.py`](/backend/adapters/stocknow_executor.py) | 2 | 2 | MEDIUM | `backend/adapters/stocknow_adapter.py`, `backend/kernel_api.py` |
| [`backend/adapters/stocknow_portfolio_sync.py`](/backend/adapters/stocknow_portfolio_sync.py) | 2 | 2 | MEDIUM | `backend/kernel_api.py`, `backend/routes_stocknow.py` |
| [`backend/adapters/stocknow_write_guard.py`](/backend/adapters/stocknow_write_guard.py) | 2 | 2 | MEDIUM | `backend/adapters/stocknow_api.py`, `backend/adapters/stocknow_executor.py` |
| [`backend/engine/agent_actions.py`](/backend/engine/agent_actions.py) | 2 | 2 | MEDIUM | `backend/engine/auto_trader.py`, `backend/kernel_api.py` |
| [`backend/engine/curve_analyzer.py`](/backend/engine/curve_analyzer.py) | 2 | 2 | MEDIUM | `backend/engine/signals.py`, `backend/kernel_api.py` |
| [`backend/engine/heartbeat.py`](/backend/engine/heartbeat.py) | 2 | 2 | MEDIUM | `backend/main.py`, `scripts/check_heartbeat.py` |
| [`backend/engine/preflight_service.py`](/backend/engine/preflight_service.py) | 2 | 2 | MEDIUM | `backend/kernel_api.py`, `backend/main.py` |
| [`backend/engine/signals.py`](/backend/engine/signals.py) | 2 | 2 | MEDIUM | `backend/engine/auto_trader.py`, `backend/portfolio.py` |
| [`backend/kernel_api.py`](/backend/kernel_api.py) | 2 | 2 | MEDIUM | `backend/main.py`, `backend/routes_stocknow.py` |
| [`backend/market_map.py`](/backend/market_map.py) | 2 | 2 | MEDIUM | `backend/main.py`, `backend/portfolio.py` |
| [`backend/seed.py`](/backend/seed.py) | 2 | 2 | MEDIUM | `backend/kernel_api.py`, `backend/main.py` |
| [`scripts/backup_db.py`](/scripts/backup_db.py) | 2 | 2 | MEDIUM | `scripts/preflight.py`, `scripts/restore_db.py` |
| [`backend/engine/price_guard.py`](/backend/engine/price_guard.py) | 1 | 1 | LOW | `backend/kernel_api.py` |
| [`backend/engine/sequential_seller.py`](/backend/engine/sequential_seller.py) | 1 | 1 | LOW | `backend/engine/auto_trader.py` |
| [`backend/logging_config.py`](/backend/logging_config.py) | 1 | 1 | LOW | `backend/main.py` |
| [`backend/routes_auth_settings.py`](/backend/routes_auth_settings.py) | 1 | 1 | LOW | `backend/main.py` |
| [`backend/routes_hermes.py`](/backend/routes_hermes.py) | 1 | 1 | LOW | `backend/main.py` |
| [`backend/routes_stocknow.py`](/backend/routes_stocknow.py) | 1 | 1 | LOW | `backend/main.py` |
| [`backend/routes_tradexpress.py`](/backend/routes_tradexpress.py) | 1 | 1 | LOW | `backend/main.py` |
| [`plugins/humming_bird/tools.py`](/plugins/humming_bird/tools.py) | 1 | 1 | LOW | `plugins/humming_bird/hooks.py` |
| [`scripts/preflight.py`](/scripts/preflight.py) | 1 | 1 | LOW | `backend/engine/preflight_service.py` |
| [`backend/__init__.py`](/backend/__init__.py) | 0 | 0 | LEAF | *Leaf / Entrypoint* |
| [`backend/adapters/__init__.py`](/backend/adapters/__init__.py) | 0 | 0 | LEAF | *Leaf / Entrypoint* |
| [`backend/adapters/tradexpress/__init__.py`](/backend/adapters/tradexpress/__init__.py) | 0 | 0 | LEAF | *Leaf / Entrypoint* |
| [`backend/engine/__init__.py`](/backend/engine/__init__.py) | 0 | 0 | LEAF | *Leaf / Entrypoint* |
| [`backend/main.py`](/backend/main.py) | 0 | 0 | LEAF | *Leaf / Entrypoint* |
| [`plugins/humming_bird/__init__.py`](/plugins/humming_bird/__init__.py) | 0 | 0 | LEAF | *Leaf / Entrypoint* |
| [`plugins/humming_bird/hooks.py`](/plugins/humming_bird/hooks.py) | 0 | 0 | LEAF | *Leaf / Entrypoint* |
| [`plugins/humming_bird/schemas.py`](/plugins/humming_bird/schemas.py) | 0 | 0 | LEAF | *Leaf / Entrypoint* |
| [`scripts/check_dse_market_open.py`](/scripts/check_dse_market_open.py) | 0 | 0 | LEAF | *Leaf / Entrypoint* |
| [`scripts/check_heartbeat.py`](/scripts/check_heartbeat.py) | 0 | 0 | LEAF | *Leaf / Entrypoint* |
| [`scripts/generate_code_map.py`](/scripts/generate_code_map.py) | 0 | 0 | LEAF | *Leaf / Entrypoint* |
| [`scripts/inspect_tradexpress_passive.py`](/scripts/inspect_tradexpress_passive.py) | 0 | 0 | LEAF | *Leaf / Entrypoint* |
| [`scripts/restore_db.py`](/scripts/restore_db.py) | 0 | 0 | LEAF | *Leaf / Entrypoint* |
| [`scripts/verify_chat_card.py`](/scripts/verify_chat_card.py) | 0 | 0 | LEAF | *Leaf / Entrypoint* |
| [`scripts/verify_step10_ui.py`](/scripts/verify_step10_ui.py) | 0 | 0 | LEAF | *Leaf / Entrypoint* |


### 2.2 Internal Forward Import Dependency Graph

Shows intra-repo module dependencies within `backend/`, `plugins/`, and `scripts/`:

| Module File | Imported Internal Dependencies |
| :--- | :--- |
| [`backend/__init__.py`](/backend/__init__.py) | *Independent Core Module* |
| [`backend/adapters/__init__.py`](/backend/adapters/__init__.py) | `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.adapters.stocknow_client.StockNowLiveClient`, `backend.adapters.stocknow_client.get_safe_profile_dir`, `backend.adapters.stocknow_market_sync.extract_quotes_from_payload`, `backend.adapters.stocknow_market_sync.extract_quotes_from_stocknow`, `backend.adapters.stocknow_market_sync.sync_live_market_to_db` |
| [`backend/adapters/base.py`](/backend/adapters/base.py) | *Independent Core Module* |
| [`backend/adapters/stocknow_adapter.py`](/backend/adapters/stocknow_adapter.py) | `backend.adapters.stocknow_client.get_safe_profile_dir`, `backend.adapters.stocknow_executor.get_stocknow_executor`, `backend.database.CompanyProfile`, `backend.engine.money.ZERO`, `backend.engine.money.decimal` |
| [`backend/adapters/stocknow_api.py`](/backend/adapters/stocknow_api.py) | `backend.adapters.stocknow_write_guard.StockNowWriteGuardError`, `backend.adapters.stocknow_write_guard.verify_test_portfolio_post_guard` |
| [`backend/adapters/stocknow_client.py`](/backend/adapters/stocknow_client.py) | `backend.secret_guard.SecretGuard`, `backend.secret_guard.redact_secrets` |
| [`backend/adapters/stocknow_executor.py`](/backend/adapters/stocknow_executor.py) | `backend.adapters.stocknow_api.NotAuthenticatedError`, `backend.adapters.stocknow_api.RateLimitedError`, `backend.adapters.stocknow_api.SchemaChangedError`, `backend.adapters.stocknow_api.StockNowAPI`, `backend.adapters.stocknow_write_guard.StockNowWriteGuardError`, `backend.adapters.stocknow_write_guard.verify_test_portfolio_post_guard`, `backend.database.DecisionLog`, `backend.database.KernelAuditLog` |
| [`backend/adapters/stocknow_market_sync.py`](/backend/adapters/stocknow_market_sync.py) | `backend.adapters.stocknow_api.StockNowAPI`, `backend.adapters.stocknow_client.StockNowLiveClient`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.portfolio_state`, `backend.engine.money.ZERO`, `backend.engine.money.decimal`, `backend.portfolio.COMPANY_FUNDAMENTALS`, `backend.portfolio.DEFAULT_FUNDAMENTALS` |
| [`backend/adapters/stocknow_portfolio_sync.py`](/backend/adapters/stocknow_portfolio_sync.py) | `backend.adapters.stocknow_api.SchemaChangedError`, `backend.adapters.stocknow_api.StockNowAPI`, `backend.adapters.stocknow_client.StockNowLiveClient`, `backend.config.Settings`, `backend.config.get_allowed_portfolios`, `backend.config.get_portfolio_name`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.DecisionLog`, `backend.database.PortfolioState`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.engine.checkpoint.CheckpointManager`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.price`, `backend.engine.money.purchase_amount`, `backend.engine.t2_ledger.BUCKETS`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.assert_ledger`, `backend.engine.t2_ledger.bucket_balances` |
| [`backend/adapters/stocknow_write_guard.py`](/backend/adapters/stocknow_write_guard.py) | `backend.config.test_portfolio_configured` |
| [`backend/adapters/tradexpress/__init__.py`](/backend/adapters/tradexpress/__init__.py) | *Independent Core Module* |
| [`backend/adapters/tradexpress/cdp_daemon.py`](/backend/adapters/tradexpress/cdp_daemon.py) | `backend.adapters.tradexpress.passive_feed.TradeXpressPassiveFeed`, `backend.adapters.tradexpress.passive_feed.get_global_passive_feed`, `backend.adapters.tradexpress.passive_feed.ingest_passive_snapshot`, `backend.adapters.tradexpress.shadow_simulator.TradeXpressShadowSimulator`, `backend.config.Settings`, `backend.config.utc_now_iso`, `backend.database.Database`, `backend.secret_guard.SecretGuard` |
| [`backend/adapters/tradexpress/passive_feed.py`](/backend/adapters/tradexpress/passive_feed.py) | `backend.adapters.base.MarketFeedAdapter`, `backend.adapters.base.MarketQuote`, `backend.adapters.base.PortfolioHolding`, `backend.adapters.base.from_tradexpress_symbol`, `backend.adapters.base.to_tradexpress_symbol`, `backend.config.Settings`, `backend.config.utc_now_iso`, `backend.database.CompanyProfile`, `backend.database.Database`, `backend.database.PortfolioState`, `backend.database.portfolio_state`, `backend.engine.money.ZERO`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.price` |
| [`backend/adapters/tradexpress/shadow_simulator.py`](/backend/adapters/tradexpress/shadow_simulator.py) | `backend.adapters.base.BrokerOrderExecutor`, `backend.adapters.base.MarketQuote`, `backend.adapters.base.from_tradexpress_symbol`, `backend.adapters.base.to_tradexpress_symbol`, `backend.adapters.base.validate_tradexpress_order_safety`, `backend.adapters.tradexpress.passive_feed.TradeXpressPassiveFeed`, `backend.adapters.tradexpress.passive_feed.get_global_passive_feed`, `backend.config.Settings`, `backend.config.utc_now_iso`, `backend.database.CompanyProfile`, `backend.database.Database`, `backend.database.KernelStateCheckpoint`, `backend.database.PortfolioState`, `backend.database.ShadowOrder`, `backend.database.TaxLot`, `backend.database.TradeLearningLog`, `backend.database.TradeLog`, `backend.database.portfolio_state`, `backend.engine.checkpoint.CheckpointManager`, `backend.engine.money.ZERO`, `backend.engine.money.allocated_basis`, `backend.engine.money.calculate_broker_fee_breakdown`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.price`, `backend.engine.money.whole_shares`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.assert_ledger`, `backend.engine.t2_ledger.bucket_balances` |
| [`backend/config.py`](/backend/config.py) | *Independent Core Module* |
| [`backend/database.py`](/backend/database.py) | `backend.config.utc_now_iso` |
| [`backend/engine/__init__.py`](/backend/engine/__init__.py) | *Independent Core Module* |
| [`backend/engine/agent_actions.py`](/backend/engine/agent_actions.py) | `backend.config.Settings`, `backend.config.get_active_target_portfolio`, `backend.database.CanaryThesis`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.DecisionLog`, `backend.database.PortfolioState`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.engine.money.ZERO`, `backend.engine.money.allocated_basis`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.price`, `backend.engine.money.purchase_amount`, `backend.engine.money.sale_amount`, `backend.engine.money.whole_shares`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.assert_ledger`, `backend.engine.t2_ledger.bucket_balances` |
| [`backend/engine/auto_trader.py`](/backend/engine/auto_trader.py) | `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.adapters.tradexpress.passive_feed.get_global_passive_feed`, `backend.adapters.tradexpress.shadow_simulator.TradeXpressShadowSimulator`, `backend.config.Settings`, `backend.config.get_active_target_portfolio`, `backend.config.get_allowed_portfolios`, `backend.database.AutomationCycle`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.CycleRequestKey`, `backend.database.Database`, `backend.database.DecisionLog`, `backend.database.OrderIdempotencyKey`, `backend.database.TaxLot`, `backend.database.TradeLearningLog`, `backend.database.TradeLog`, `backend.database.portfolio_state`, `backend.engine.agent_actions.check_canary_theses`, `backend.engine.circuit_breaker.record_circuit_failure`, `backend.engine.circuit_breaker.record_circuit_success`, `backend.engine.money.HUNDRED`, `backend.engine.money.ZERO`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.price`, `backend.engine.money.purchase_amount`, `backend.engine.money.whole_shares`, `backend.engine.scheduler.is_dse_market_open`, `backend.engine.sequential_seller.SellState`, `backend.engine.sequential_seller.plan_sale`, `backend.engine.signals.BLOCK_ALL_TRADING`, `backend.engine.signals.assess_company`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.assert_ledger`, `backend.engine.t2_ledger.bucket_balances`, `backend.engine.trading_lock.acquire_trading_lock` |
| [`backend/engine/checkpoint.py`](/backend/engine/checkpoint.py) | `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.KernelStateCheckpoint`, `backend.database.PortfolioState`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.engine.money.decimal`, `backend.engine.t2_ledger.assert_ledger` |
| [`backend/engine/circuit_breaker.py`](/backend/engine/circuit_breaker.py) | `backend.config.Settings`, `backend.database.Database`, `backend.database.DecisionLog`, `backend.database.KernelAuditLog`, `backend.database.portfolio_state`, `backend.engine.telegram_bot.send_telegram_alert`, `backend.engine.telegram_bot.send_telegram_alert_sync` |
| [`backend/engine/curve_analyzer.py`](/backend/engine/curve_analyzer.py) | `backend.engine.money.HUNDRED`, `backend.engine.money.ZERO`, `backend.engine.money.decimal` |
| [`backend/engine/heartbeat.py`](/backend/engine/heartbeat.py) | `backend.config.Settings`, `backend.config.utc_now_iso`, `backend.database.DailySummaryLog`, `backend.database.Database`, `backend.database.DecisionLog`, `backend.database.KernelAuditLog`, `backend.database.SystemHeartbeat`, `backend.database.TradeLog`, `backend.database.portfolio_state`, `backend.engine.scheduler.DHAKA`, `backend.engine.scheduler.is_dse_market_open`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.telegram_bot.send_telegram_alert`, `backend.engine.telegram_bot.send_telegram_alert_sync` |
| [`backend/engine/money.py`](/backend/engine/money.py) | *Independent Core Module* |
| [`backend/engine/preflight_service.py`](/backend/engine/preflight_service.py) | `backend.config.Settings`, `backend.config.utc_now_iso`, `backend.database.Database`, `backend.database.PreflightCheckLog`, `backend.database.portfolio_state`, `scripts.preflight.run_preflight` |
| [`backend/engine/price_guard.py`](/backend/engine/price_guard.py) | `backend.adapters.stocknow_market_sync._ALL_DSE_SHARES_CACHE` |
| [`backend/engine/scheduler.py`](/backend/engine/scheduler.py) | `backend.adapters.stocknow_client.StockNowLiveClient`, `backend.adapters.stocknow_market_sync.extract_quotes_from_stocknow`, `backend.adapters.stocknow_market_sync.fetch_stocknow_live_market_data`, `backend.adapters.stocknow_market_sync.sync_live_market_to_db`, `backend.config.DHAKA`, `backend.config.Settings`, `backend.database.Database`, `backend.database.DecisionLog`, `backend.database.portfolio_state`, `backend.engine.auto_trader.AutoTrader`, `backend.engine.t2_ledger.TradingCalendar`, `backend.portfolio.build_snapshot` |
| [`backend/engine/sequential_seller.py`](/backend/engine/sequential_seller.py) | `backend.engine.money.HUNDRED`, `backend.engine.money.ZERO`, `backend.engine.money.allocated_basis`, `backend.engine.money.sale_amount`, `backend.engine.money.whole_shares` |
| [`backend/engine/signals.py`](/backend/engine/signals.py) | `backend.adapters.stocknow_adapter.DemoQuote`, `backend.adapters.stocknow_adapter.QuoteError`, `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.config.Settings`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.engine.curve_analyzer.CurveAnalysis`, `backend.engine.curve_analyzer.analyze_curve`, `backend.engine.money.decimal` |
| [`backend/engine/t2_ledger.py`](/backend/engine/t2_ledger.py) | `backend.config.get_active_target_portfolio`, `backend.database.PortfolioState`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.engine.money.CENT`, `backend.engine.money.ZERO`, `backend.engine.money.money` |
| [`backend/engine/telegram_bot.py`](/backend/engine/telegram_bot.py) | `backend.config.Settings`, `backend.database.Database`, `backend.database.KernelAuditLog`, `backend.database.portfolio_state` |
| [`backend/engine/trading_lock.py`](/backend/engine/trading_lock.py) | *Independent Core Module* |
| [`backend/hermes_bridge.py`](/backend/hermes_bridge.py) | *Independent Core Module* |
| [`backend/kernel_api.py`](/backend/kernel_api.py) | `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.adapters.stocknow_api.StockNowError`, `backend.adapters.stocknow_executor.NoReceiptExecutionError`, `backend.adapters.stocknow_executor.StockNowExecutionError`, `backend.adapters.stocknow_executor.notify_order_failure`, `backend.adapters.stocknow_market_sync.extract_quotes_from_stocknow`, `backend.adapters.stocknow_market_sync.fetch_stocknow_live_market_data`, `backend.adapters.stocknow_market_sync.get_or_fetch_all_dse_shares`, `backend.adapters.stocknow_market_sync.sync_live_market_to_db`, `backend.adapters.stocknow_portfolio_sync.extract_hummingbird_portfolio`, `backend.adapters.stocknow_portfolio_sync.reconcile_portfolio_to_db`, `backend.adapters.stocknow_portfolio_sync.sync_stocknow_portfolio_via_api`, `backend.adapters.tradexpress.cdp_daemon.get_global_passive_daemon`, `backend.adapters.tradexpress.passive_feed.get_global_passive_feed`, `backend.config.Settings`, `backend.config.get_active_target_portfolio`, `backend.config.get_allowed_portfolios`, `backend.config.get_portfolio_name`, `backend.config.test_portfolio_configured`, `backend.database.CanaryThesis`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.DecisionLog`, `backend.database.KernelAuditLog`, `backend.database.OrderIdempotencyKey`, `backend.database.PortfolioState`, `backend.database.RuleAudit`, `backend.database.TaxLot`, `backend.database.TradeLearningLog`, `backend.database.TradeLog`, `backend.database.portfolio_state`, `backend.engine.agent_actions.check_canary_theses`, `backend.engine.agent_actions.emergency_quarantine_and_canary`, `backend.engine.agent_actions.execute_agentic_buy`, `backend.engine.agent_actions.execute_agentic_sell`, `backend.engine.agent_actions.restore_quarantine`, `backend.engine.auto_trader.AutoTrader`, `backend.engine.checkpoint.CheckpointManager`, `backend.engine.circuit_breaker.reset_circuit_breaker`, `backend.engine.curve_analyzer.analyze_curve`, `backend.engine.money.ZERO`, `backend.engine.money.allocated_basis`, `backend.engine.money.purchase_amount`, `backend.engine.money.sale_amount`, `backend.engine.preflight_service.are_caps_set`, `backend.engine.preflight_service.has_passing_preflight_within_24h`, `backend.engine.preflight_service.run_cockpit_preflight`, `backend.engine.price_guard.check_price_sanity`, `backend.engine.price_guard.get_market_quote`, `backend.engine.scheduler.get_active_scheduler`, `backend.engine.scheduler.is_dse_market_open`, `backend.engine.t2_ledger.assert_ledger`, `backend.engine.t2_ledger.bucket_balances`, `backend.engine.trading_lock.acquire_trading_lock`, `backend.portfolio.snapshot_from_session`, `backend.seed.seed_demo` |
| [`backend/logging_config.py`](/backend/logging_config.py) | *Independent Core Module* |
| [`backend/main.py`](/backend/main.py) | `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.adapters.stocknow_client.StockNowLiveClient`, `backend.adapters.stocknow_market_sync.extract_quotes_from_stocknow`, `backend.adapters.stocknow_market_sync.fetch_stocknow_live_market_data`, `backend.adapters.stocknow_market_sync.sync_live_market_to_db`, `backend.adapters.tradexpress.cdp_daemon.get_global_passive_daemon`, `backend.config.ROOT`, `backend.config.Settings`, `backend.config.VERSION`, `backend.config.get_active_target_portfolio`, `backend.config.get_allowed_portfolios`, `backend.config.get_portfolio_name`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.DecisionLog`, `backend.database.KernelAuditLog`, `backend.database.RuleAudit`, `backend.database.TradeLog`, `backend.database.portfolio_state`, `backend.engine.auto_trader.AutoTrader`, `backend.engine.auto_trader.AutomationPaused`, `backend.engine.checkpoint.CheckpointManager`, `backend.engine.circuit_breaker.reset_circuit_breaker`, `backend.engine.heartbeat.check_dead_man_switch`, `backend.engine.heartbeat.record_system_heartbeat`, `backend.engine.heartbeat.send_daily_summary_if_due`, `backend.engine.money.ZERO`, `backend.engine.preflight_service.are_caps_set`, `backend.engine.preflight_service.has_passing_preflight_within_24h`, `backend.engine.preflight_service.run_cockpit_preflight`, `backend.engine.scheduler.DSEMarketScheduler`, `backend.engine.scheduler.get_active_scheduler`, `backend.engine.telegram_bot.TelegramBotDaemon`, `backend.engine.trading_lock.acquire_trading_lock`, `backend.hermes_bridge.build_hermes_bridge_router`, `backend.kernel_api.CapsUpdateRequest`, `backend.kernel_api.build_kernel_router`, `backend.logging_config.setup_logging`, `backend.market_map.build_market_map_payload`, `backend.portfolio.build_snapshot`, `backend.portfolio.rule_view`, `backend.routes_auth_settings.KeysSettingsRequest`, `backend.routes_auth_settings.LoginRequest`, `backend.routes_auth_settings.build_auth_settings_router`, `backend.routes_hermes.CreateThreadRequest`, `backend.routes_hermes.build_hermes_router`, `backend.routes_stocknow.build_stocknow_router`, `backend.routes_tradexpress.build_tradexpress_router`, `backend.seed.migrate_real_stocknow_market`, `backend.seed.seed_demo` |
| [`backend/market_map.py`](/backend/market_map.py) | *Independent Core Module* |
| [`backend/portfolio.py`](/backend/portfolio.py) | `backend.adapters.base.to_tradexpress_symbol`, `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.adapters.stocknow_market_sync._ALL_DSE_SHARES_CACHE`, `backend.config.DHAKA`, `backend.config.Settings`, `backend.config.VERSION`, `backend.config.get_active_target_portfolio`, `backend.config.get_allowed_portfolios`, `backend.config.get_portfolio_name`, `backend.database.AutomationCycle`, `backend.database.CanaryThesis`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.DecisionLog`, `backend.database.KernelStateCheckpoint`, `backend.database.RuleAudit`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.database.portfolio_state`, `backend.engine.money.HUNDRED`, `backend.engine.money.ZERO`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.sale_amount`, `backend.engine.signals.assess_company`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.bucket_balances`, `backend.hermes_bridge.read_hermes_state`, `backend.market_map.build_market_map_payload` |
| [`backend/routes_auth_settings.py`](/backend/routes_auth_settings.py) | `backend.config.DHAKA`, `backend.config.Settings`, `backend.database.Database`, `backend.database.portfolio_state`, `backend.engine.checkpoint.CheckpointManager` |
| [`backend/routes_hermes.py`](/backend/routes_hermes.py) | `backend.config.Settings`, `backend.database.Database`, `backend.database.KernelStateCheckpoint`, `backend.database.RuleAudit`, `backend.engine.checkpoint.CheckpointManager`, `backend.hermes_bridge.get_hermes_cmd`, `backend.hermes_bridge.get_hermes_dir`, `backend.hermes_bridge.read_hermes_state`, `backend.portfolio.portfolio_state` |
| [`backend/routes_stocknow.py`](/backend/routes_stocknow.py) | `backend.adapters.stocknow_api.StockNowError`, `backend.adapters.stocknow_client.StockNowLiveClient`, `backend.adapters.stocknow_market_sync.extract_quotes_from_stocknow`, `backend.adapters.stocknow_market_sync.fetch_stocknow_live_market_data`, `backend.adapters.stocknow_market_sync.get_or_fetch_all_dse_shares`, `backend.adapters.stocknow_market_sync.sync_live_market_to_db`, `backend.adapters.stocknow_portfolio_sync.extract_hummingbird_portfolio`, `backend.adapters.stocknow_portfolio_sync.extract_hummingbird_portfolio_from_browser`, `backend.adapters.stocknow_portfolio_sync.reconcile_portfolio_to_db`, `backend.adapters.stocknow_portfolio_sync.sync_stocknow_portfolio_via_api`, `backend.config.Settings`, `backend.config.get_active_target_portfolio`, `backend.database.CompanyProfile`, `backend.database.Database`, `backend.database.PortfolioState`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.engine.scheduler.DSEMarketScheduler`, `backend.engine.scheduler.get_active_scheduler`, `backend.kernel_api.OrderRequest`, `backend.kernel_api.post_order`, `backend.portfolio.build_snapshot` |
| [`backend/routes_tradexpress.py`](/backend/routes_tradexpress.py) | `backend.adapters.tradexpress.cdp_daemon.get_global_passive_daemon`, `backend.adapters.tradexpress.passive_feed.get_feed_health_and_guidance`, `backend.adapters.tradexpress.passive_feed.get_global_passive_feed`, `backend.adapters.tradexpress.passive_feed.ingest_passive_snapshot`, `backend.adapters.tradexpress.shadow_simulator.TradeXpressShadowSimulator`, `backend.config.Settings`, `backend.database.Database`, `backend.database.PortfolioState`, `backend.database.TradeLearningLog`, `backend.database.portfolio_state`, `backend.engine.money.ZERO`, `backend.engine.money.decimal`, `backend.portfolio.build_snapshot` |
| [`backend/secret_guard.py`](/backend/secret_guard.py) | *Independent Core Module* |
| [`backend/seed.py`](/backend/seed.py) | `backend.config.DHAKA`, `backend.config.Settings`, `backend.config.utc_now_iso`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.DecisionLog`, `backend.database.PortfolioState`, `backend.database.PreflightCheckLog`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.price`, `backend.engine.money.purchase_amount`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.assert_ledger`, `backend.engine.t2_ledger.bucket_balances` |
| [`plugins/humming_bird/__init__.py`](/plugins/humming_bird/__init__.py) | *Independent Core Module* |
| [`plugins/humming_bird/hooks.py`](/plugins/humming_bird/hooks.py) | `plugins.humming_bird.tools._kernel_get` |
| [`plugins/humming_bird/schemas.py`](/plugins/humming_bird/schemas.py) | *Independent Core Module* |
| [`plugins/humming_bird/tools.py`](/plugins/humming_bird/tools.py) | *Independent Core Module* |
| [`scripts/backup_db.py`](/scripts/backup_db.py) | *Independent Core Module* |
| [`scripts/check_dse_market_open.py`](/scripts/check_dse_market_open.py) | *Independent Core Module* |
| [`scripts/check_heartbeat.py`](/scripts/check_heartbeat.py) | `backend.config.DEFAULT_DATABASE_URL`, `backend.config.Settings`, `backend.database.Database`, `backend.engine.heartbeat.check_dead_man_switch`, `backend.engine.heartbeat.record_system_heartbeat` |
| [`scripts/generate_code_map.py`](/scripts/generate_code_map.py) | *Independent Core Module* |
| [`scripts/inspect_tradexpress_passive.py`](/scripts/inspect_tradexpress_passive.py) | `backend.secret_guard.SecretGuard` |
| [`scripts/preflight.py`](/scripts/preflight.py) | `backend.adapters.stocknow_client.get_safe_profile_dir`, `backend.config.DEFAULT_DATABASE_URL`, `backend.config.Settings`, `backend.config.test_portfolio_configured`, `backend.database.Database`, `backend.database.PortfolioState`, `backend.database.TaxLot`, `backend.engine.t2_ledger.assert_ledger`, `backend.engine.t2_ledger.bucket_balances`, `backend.hermes_bridge.get_hermes_dir`, `backend.hermes_bridge.read_hermes_state`, `plugins.humming_bird._TOOLS`, `scripts.backup_db.backup_database`, `scripts.backup_db.get_default_backup_dir`, `scripts.backup_db.get_default_db_path` |
| [`scripts/restore_db.py`](/scripts/restore_db.py) | `scripts.backup_db.backup_database`, `scripts.backup_db.get_default_backup_dir`, `scripts.backup_db.get_default_db_path` |
| [`scripts/verify_chat_card.py`](/scripts/verify_chat_card.py) | *Independent Core Module* |
| [`scripts/verify_step10_ui.py`](/scripts/verify_step10_ui.py) | *Independent Core Module* |

---

## 3. Python AST X-Ray & Class/Function Registry

### 📄 [`backend/__init__.py`](/backend/__init__.py)

---

### 📄 [`backend/adapters/__init__.py`](/backend/adapters/__init__.py)

---

### 📄 [`backend/adapters/base.py`](/backend/adapters/base.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `OrderBookLevel` | `L18–L20` | `object` | — | 0 |
| `MarketQuote` | `L24–L44` | `object` | — | 0 |
| `PortfolioHolding` | `L48–L56` | `object` | — | 0 |
| `MarketFeedAdapter` | `L59–L70` | `ABC` | Abstract base interface for real-time market quote feeds. | 2 |
| `BrokerOrderExecutor` | `L73–L87` | `ABC` | Abstract base interface for executing orders against a brokerage. | 1 |


**Methods in `MarketFeedAdapter`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `get_quote` | `L63–L65` | `(self, symbol: str...)` | `MarketQuote | None` | Fetch current quote for a single symbol. | — |
| `get_quotes` | `L68–L70` | `(self, symbols: list[str]...)` | `dict[str, MarketQuote]` | Fetch current quotes for multiple symbols. | — |


**Methods in `BrokerOrderExecutor`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `execute_order` | `L77–L87` | `(self, symbol: str, side: str, quant...)` | `dict[str, Any]` | Execute or simulate order placement. | — |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `to_tradexpress_symbol` | `L90–L97` | `(symbol: str, board: str='PB'...)` | `str` | Normalize internal symbol to TradeXpress backtick board format (e.g. BANKASIA`PB). | `lstrip`, `strip`, `sub`, `upper` |
| `from_tradexpress_symbol` | `L100–L106` | `(raw_symbol: str...)` | `str` | Normalize raw TradeXpress symbol by stripping backtick or apostrophe board suffix. | `strip`, `sub`, `upper` |
| `validate_tradexpress_order_safety` | `L109–L201` | `(*, symbol: str, side: str, quantity...)` | `tuple[bool, list[str]]` | Strict preflight safety validation for TradeXpress order execution. | `Decimal`, `append`, `len`, `strip` |


---

### 📄 [`backend/adapters/stocknow_adapter.py`](/backend/adapters/stocknow_adapter.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `QuoteError` | `L15–L16` | `ValueError` | — | 0 |
| `LiveIntegrationNotImplemented` | `L19–L20` | `RuntimeError` | — | 0 |
| `DemoQuote` | `L24–L29` | `object` | — | 0 |
| `StockNowAdapter` | `L32–L164` | `object` | Sprint 1's explicitly synthetic data/paper-fill boundary. | 6 |
| `StockNowBrowserSession` | `L167–L193` | `object` | Opt-in persistent browser foundation, not a login or order implementation. | 2 |


**Methods in `StockNowAdapter`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L35–L37` | `(self, mode: str='DEMO'...)` | — | — | — |
| `quote` | `L39–L56` | `(self, company: CompanyProfile, as_o...)` | `DemoQuote` | — | `DemoQuote`, `QuoteError`, `decimal`, `is_finite` |
| `paper_fill` | `L58–L61` | `(self, quote: DemoQuote, quantity: i...)` | `Decimal` | — | `ValueError`, `startswith` |
| `read_virtual_portfolio` | `L63–L64` | `(self...)` | — | — | `LiveIntegrationNotImplemented` |
| `execute_order` | `L66–L127` | `(self, symbol: str, side: str, quant...)` | `dict` | — | `Decimal`, `execute_order`, `float`, `get_stocknow_executor` |
| `get_adapter_status` | `L129–L164` | `(self, ingestion_mode: str='BACKGROU...)` | `dict` | — | `get`, `get_safe_profile_dir`, `get_status`, `getattr` |


**Methods in `StockNowBrowserSession`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L175–L176` | `(self, profile_directory: Path...)` | — | — | — |
| `open` | `L179–L193` | `(self...)` | — | — | `async_playwright`, `close`, `launch_persistent_context`, `mkdir` |


---

### 📄 [`backend/adapters/stocknow_api.py`](/backend/adapters/stocknow_api.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `StockNowError` | `L28–L30` | `Exception` | Base exception for StockNow API errors. | 0 |
| `NotAuthenticatedError` | `L33–L35` | `StockNowError` | Raised on missing credentials, failed login, or persistent 401. | 0 |
| `RateLimitedError` | `L38–L40` | `StockNowError` | Raised on 429 Too Many Requests. | 0 |
| `SchemaChangedError` | `L43–L45` | `StockNowError` | Raised when an API response misses expected fields. Must stop trading. | 0 |
| `NetworkError` | `L48–L50` | `StockNowError` | Raised on transport failures, DNS errors, or timeouts after retries. | 0 |
| `_RateLimiter` | `L60–L76` | `object` | Async token bucket / interval limiter ensuring max 1 req/sec per host. | 2 |
| `StockNowAPI` | `L79–L608` | `object` | Async HTTP client for StockNow REST endpoints. | 16 |


**Methods in `_RateLimiter`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L63–L66` | `(self, interval: float=1.0...)` | `None` | — | `Lock`, `float`, `max` |
| `acquire` | `L68–L76` | `(self...)` | `None` | — | `get_event_loop`, `sleep`, `time` |


**Methods in `StockNowAPI`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L82–L116` | `(self, base_url: str='https://stockn...)` | `None` | — | `AsyncClient`, `_RateLimiter`, `rstrip` |
| `__aenter__` | `L118–L119` | `(self...)` | `StockNowAPI` | — | — |
| `__aexit__` | `L121–L122` | `(self, exc_type: Any, exc_val: Any, ...)` | `None` | — | `aclose` |
| `aclose` | `L124–L128` | `(self...)` | `None` | Close underlying HTTP client and wipe token from memory. | `aclose` |
| `login` | `L134–L195` | `(self...)` | `str` | Authenticate using credentials from environment (or constructor). | `NetworkError`, `NotAuthenticatedError`, `RateLimitedError`, `SchemaChangedError` |
| `logout` | `L197–L214` | `(self...)` | `None` | Terminate active session on server and clear token from memory. | `acquire`, `post`, `warning` |
| `ensure_authenticated` | `L216–L221` | `(self...)` | `str` | Ensure a valid, non-expired in-memory JWT token exists. | `login`, `time` |
| `_request` | `L227–L339` | `(self, method: str, path: str, *, pa...)` | `Any` | — | `NetworkError`, `NotAuthenticatedError`, `RateLimitedError`, `SchemaChangedError` |
| `_check_ledger_for_trade` | `L341–L380` | `(self, portfolio_id: str | int, expe...)` | `dict[str, Any] | None` | Read ledger to verify if an unconfirmed mutation was executed on the server. | `get`, `get_ledger`, `info`, `int` |
| `get_instruments` | `L386–L415` | `(self...)` | `dict[str, Any]` | Fetch complete DSE instruments catalog. | `SchemaChangedError`, `_request`, `any`, `isinstance` |
| `get_lists` | `L417–L432` | `(self...)` | `list[dict[str, Any]]` | Fetch operator watchlists (GSC, L1, L2). Validates expected schema. | `SchemaChangedError`, `_request`, `get`, `isinstance` |
| `get_history` | `L434–L471` | `(self, symbol: str, sessions: int=15...)` | `list[list[Any]]` | Fetch daily OHLCV candles for symbol sliced to requested sessions count. | `SchemaChangedError`, `_request`, `all`, `append` |
| `get_portfolio` | `L473–L490` | `(self, id: str | int...)` | `dict[str, Any]` | Fetch portfolio holdings and cash balance. Validates expected schema. | `SchemaChangedError`, `_request`, `isinstance`, `keys` |
| `get_ledger` | `L492–L510` | `(self, id: str | int...)` | `dict[str, Any]` | Fetch portfolio ledger transactions. Validates expected schema. | `SchemaChangedError`, `_request`, `get`, `isinstance` |
| `buy` | `L516–L561` | `(self, id: str | int, items: list[di...)` | `dict[str, Any]` | Execute Buy orders on StockNow portfolio. | `SchemaChangedError`, `ValueError`, `_request`, `float` |
| `sell` | `L563–L608` | `(self, id: str | int, items: list[di...)` | `dict[str, Any]` | Execute Sell orders on StockNow portfolio. | `SchemaChangedError`, `ValueError`, `_request`, `float` |


---

### 📄 [`backend/adapters/stocknow_client.py`](/backend/adapters/stocknow_client.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `StockNowLiveClient` | `L81–L606` | `object` | Persistent Playwright browser controller, auto-login assistant & XHR network sniffer. | 14 |


**Methods in `StockNowLiveClient`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L84–L112` | `(self, profile_directory: Path | str...)` | — | — | `Thread`, `_create_proactor_loop`, `get_safe_profile_dir`, `rstrip` |
| `_run_worker_loop` | `L114–L119` | `(self...)` | `None` | — | `debug`, `format_exception_str`, `run_forever`, `set_event_loop` |
| `_run_in_proactor` | `L121–L144` | `(self, coro: Any...)` | `Any` | Run a coroutine inside the dedicated proactor event loop thread. | `Thread`, `_create_proactor_loop`, `get_running_loop`, `hasattr` |
| `_handle_response` | `L146–L177` | `(self, response: Any...)` | `None` | Passively capture JSON responses from stocknow.com.bd. | `debug`, `format_exception_str`, `get`, `getattr` |
| `launch` | `L179–L181` | `(self, mode: str | None=None...)` | `dict[str, Any]` | Launch or attach persistent Chromium session on dedicated Proactor thread. | `_launch_internal`, `_run_in_proactor` |
| `_launch_internal` | `L183–L264` | `(self, mode: str | None=None...)` | `dict[str, Any]` | — | `RuntimeError`, `_handle_response`, `async_playwright`, `callable` |
| `close` | `L266–L268` | `(self...)` | `dict[str, Any]` | Close browser context and stop Playwright cleanly. | `_close_internal`, `_run_in_proactor` |
| `_close_internal` | `L270–L293` | `(self...)` | `dict[str, Any]` | — | `close`, `get_status`, `stop` |
| `ensure_authenticated` | `L295–L300` | `(self, phone: str='', password: str=...)` | `dict[str, Any]` | Inspect authentication state on stocknow.com.bd, filling credentials if needed. | `_ensure_authenticated_internal`, `_run_in_proactor` |
| `_ensure_authenticated_internal` | `L302–L490` | `(self, phone: str='', password: str=...)` | `dict[str, Any]` | — | `_discover_portfolio_internal`, `check`, `click`, `debug` |
| `logout` | `L492–L506` | `(self...)` | `dict[str, Any]` | Log out of StockNow session in Playwright browser and clear tokens. | `bool`, `evaluate`, `getattr`, `goto` |
| `discover_portfolio` | `L508–L510` | `(self...)` | `dict[str, Any]` | Discover 'Humming Bird' portfolio stats and ID from /portfolios. | `_discover_portfolio_internal`, `_run_in_proactor` |
| `_discover_portfolio_internal` | `L512–L577` | `(self...)` | `dict[str, Any]` | — | `debug`, `evaluate`, `format_exception_str`, `get` |
| `get_status` | `L579–L606` | `(self...)` | `dict[str, Any]` | Return structured telemetry for live session status endpoint. | `hasattr`, `is_closed`, `keys`, `len` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `format_exception_str` | `L34–L37` | `(e: Exception | BaseException...)` | `str` | Format exception to guarantee non-empty diagnostic message. | `repr`, `str`, `strip`, `type` |
| `_create_proactor_loop` | `L40–L47` | `(...)` | `asyncio.AbstractEventLoop` | Create a new ProactorEventLoop on Windows or standard event loop on POSIX. | `WindowsProactorEventLoopPolicy`, `getattr`, `new_event_loop` |
| `get_safe_profile_dir` | `L50–L68` | `(custom_path: Path | str | None=None...)` | `Path` | Resolve an isolated Playwright profile directory outside OneDrive. | `Path`, `expanduser`, `lower`, `resolve` |
| `mask_phone` | `L71–L78` | `(phone: str...)` | `str` | Mask phone number for safe display and logging without revealing identity. | `isdigit`, `join`, `len`, `str` |


---

### 📄 [`backend/adapters/stocknow_executor.py`](/backend/adapters/stocknow_executor.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `StockNowExecutionError` | `L43–L50` | `Exception` | Base error for all StockNow execution failures. | 1 |
| `NotAuthenticatedExecutionError` | `L53–L55` | `StockNowExecutionError` | — | 1 |
| `SelectorMissingExecutionError` | `L58–L60` | `StockNowExecutionError` | — | 1 |
| `SchemaChangedExecutionError` | `L63–L65` | `StockNowExecutionError` | — | 1 |
| `TimeoutExecutionError` | `L68–L70` | `StockNowExecutionError` | — | 1 |
| `NoReceiptExecutionError` | `L73–L75` | `StockNowExecutionError` | — | 1 |
| `StockNowExecutor` | `L154–L198` | `ABC` | Abstract contract for StockNow order execution and ledger verification. | 5 |
| `ApiTransport` | `L205–L375` | `StockNowExecutor` | Executes orders via direct StockNow REST API (httpx async). | 6 |
| `BrowserTransport` | `L382–L635` | `StockNowExecutor` | Executes orders via live Playwright browser session. | 8 |
| `DemoPaperExecutor` | `L642–L698` | `StockNowExecutor` | Explicit DEMO paper fill. Only invoked when data source is strictly DEMO. | 5 |


**Methods in `StockNowExecutionError`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L46–L50` | `(self, error_code: str, message: str...)` | `None` | — | `__init__`, `super` |


**Methods in `NotAuthenticatedExecutionError`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L54–L55` | `(self, message: str='User not authen...)` | `None` | — | `__init__`, `super` |


**Methods in `SelectorMissingExecutionError`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L59–L60` | `(self, message: str='Expected DOM se...)` | `None` | — | `__init__`, `super` |


**Methods in `SchemaChangedExecutionError`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L64–L65` | `(self, message: str='StockNow respon...)` | `None` | — | `__init__`, `super` |


**Methods in `TimeoutExecutionError`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L69–L70` | `(self, message: str='StockNow order ...)` | `None` | — | `__init__`, `super` |


**Methods in `NoReceiptExecutionError`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L74–L75` | `(self, message: str='Order execution...)` | `None` | — | `__init__`, `super` |


**Methods in `StockNowExecutor`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `execute_order` | `L158–L170` | `(self, symbol: str, side: str, quant...)` | `dict[str, Any]` | Execute buy/sell order, verify fill in ledger, and return receipt. | `Decimal` |
| `get_ledger` | `L173–L175` | `(self, portfolio_id: str | int...)` | `dict[str, Any]` | Fetch portfolio ledger. | — |
| `verify_fill` | `L178–L188` | `(self, portfolio_id: str | int, trad...)` | `dict[str, Any] | None` | Verify if a trade matching date, side, symbol, qty, price exists in the ledger. | — |
| `logout` | `L191–L193` | `(self...)` | `dict[str, Any]` | Log out of the session. | — |
| `is_authenticated` | `L196–L198` | `(self...)` | `bool` | Check if transport currently has an active authenticated session. | — |


**Methods in `ApiTransport`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L208–L211` | `(self, api_client: Any | None=None, ...)` | `None` | — | `StockNowAPI` |
| `is_authenticated` | `L213–L221` | `(self...)` | `bool` | — | `bool`, `ensure_authenticated`, `getattr` |
| `get_ledger` | `L223–L232` | `(self, portfolio_id: str | int...)` | `dict[str, Any]` | — | `NotAuthenticatedExecutionError`, `SchemaChangedExecutionError`, `StockNowExecutionError`, `get_ledger` |
| `verify_fill` | `L234–L253` | `(self, portfolio_id: str | int, trad...)` | `dict[str, Any] | None` | — | `get`, `get_ledger`, `match_ledger_entry`, `warning` |
| `execute_order` | `L255–L370` | `(self, symbol: str, side: str, quant...)` | `dict[str, Any]` | — | `Decimal`, `NoReceiptExecutionError`, `NotAuthenticatedExecutionError`, `SchemaChangedExecutionError` |
| `logout` | `L372–L375` | `(self...)` | `dict[str, Any]` | Terminate active session on server and wipe in-memory token. | `logout` |


**Methods in `BrowserTransport`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L385–L387` | `(self, stocknow_client: Any, configu...)` | `None` | — | — |
| `_ensure_dialog_handler` | `L389–L416` | `(self, page: Any...)` | `None` | Register dialog handler: accepts ONLY StockNow logout confirm and logs other dialogs. | `getattr`, `hasattr`, `on` |
| `_on_dialog` | `L395–L413` | `(dialog: Any...)` | `None` | — | `accept`, `any`, `dismiss`, `hasattr` |
| `is_authenticated` | `L418–L429` | `(self...)` | `bool` | — | `bool`, `evaluate`, `getattr` |
| `get_ledger` | `L431–L454` | `(self, portfolio_id: str | int...)` | `dict[str, Any]` | — | `NotAuthenticatedExecutionError`, `StockNowExecutionError`, `evaluate`, `get` |
| `verify_fill` | `L456–L475` | `(self, portfolio_id: str | int, trad...)` | `dict[str, Any] | None` | — | `get`, `get_ledger`, `match_ledger_entry`, `warning` |
| `execute_order` | `L477–L629` | `(self, symbol: str, side: str, quant...)` | `dict[str, Any]` | — | `Decimal`, `NoReceiptExecutionError`, `NotAuthenticatedExecutionError`, `SelectorMissingExecutionError` |
| `logout` | `L631–L635` | `(self...)` | `dict[str, Any]` | Log out of StockNow session in browser. | `hasattr`, `logout` |


**Methods in `DemoPaperExecutor`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `is_authenticated` | `L645–L646` | `(self...)` | `bool` | — | — |
| `get_ledger` | `L648–L649` | `(self, portfolio_id: str | int...)` | `dict[str, Any]` | — | — |
| `verify_fill` | `L651–L667` | `(self, portfolio_id: str | int, trad...)` | `dict[str, Any] | None` | — | `float`, `int`, `str`, `time` |
| `execute_order` | `L669–L695` | `(self, symbol: str, side: str, quant...)` | `dict[str, Any]` | — | `Decimal`, `float`, `hasattr`, `isoformat` |
| `logout` | `L697–L698` | `(self...)` | `dict[str, Any]` | — | — |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `match_ledger_entry` | `L90–L147` | `(entry: dict[str, Any], trade_date: ...)` | `bool` | Verify if a ledger row strictly matches trade date, side, symbol, qty, price. | `abs`, `float`, `get`, `hasattr` |
| `get_stocknow_executor` | `L705–L737` | `(mode: str, stocknow_client: Any | N...)` | `StockNowExecutor` | Factory selecting the concrete transport based on the active run mode. | `ApiTransport`, `BrowserTransport`, `DemoPaperExecutor`, `NotAuthenticatedExecutionError` |
| `notify_order_failure` | `L744–L831` | `(session: Any, state: Any, settings:...)` | `None` | Record failure in DB audit, broadcast UI toast, and dispatch Telegram alert. | `AsyncClient`, `DecisionLog`, `KernelAuditLog`, `add` |


---

### 📄 [`backend/adapters/stocknow_market_sync.py`](/backend/adapters/stocknow_market_sync.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `_parse_positive_decimal` | `L32–L41` | `(val: Any...)` | `Decimal | None` | — | `decimal`, `is_finite`, `replace`, `str` |
| `_normalize_history_series` | `L44–L59` | `(raw_history: Any, fallback_price: D...)` | `list[dict[str, str]]` | Normalize 7-30 session curve observations into [{"date": "YYYY-MM-DD", "close": "XX.XX"}]. | `_parse_positive_decimal`, `append`, `get`, `isinstance` |
| `_extract_fundamentals_from_dict` | `L62–L123` | `(item: dict[str, Any]...)` | `dict[str, Any]` | — | `dict`, `float`, `get`, `int` |
| `extract_quotes_from_payload` | `L126–L213` | `(payload: Any, as_of_date: date | No...)` | `list[dict[str, Any]]` | Extract and normalize quotes from an arbitrary JSON payload. | `_extract_fundamentals_from_dict`, `_normalize_history_series`, `_parse_positive_decimal`, `append` |
| `fetch_stocknow_live_market_data` | `L221–L498` | `(client: Any=None, api_client: Any |...)` | `list[dict[str, Any]]` | Fetches real-time market data directly from stocknow.com.bd API. | `Decimal`, `StockNowAPI`, `_request`, `append` |
| `fetch_sym_history` | `L389–L440` | `(sym: str...)` | `tuple[str, list[dict[str, str]], str]` | — | `add`, `all`, `append`, `date` |
| `get_or_fetch_all_dse_shares` | `L501–L517` | `(client: Any=None, api_client: Any=N...)` | `dict[str, Any]` | Returns cached All DSE Shares catalog, populating it if not yet loaded. | `fetch_stocknow_live_market_data`, `isoformat`, `len`, `now` |
| `extract_quotes_from_stocknow` | `L521–L526` | `(client: Any, injected_payload: Any=...)` | `list[dict[str, Any]]` | Extracts live DSE ticker quotes from sniffer cache, page DOM or injected payload. | `_extract_quotes_from_stocknow_impl`, `_run_in_proactor`, `hasattr`, `isinstance` |
| `_extract_quotes_from_stocknow_impl` | `L529–L691` | `(client: Any, injected_payload: Any=...)` | `list[dict[str, Any]]` | — | `debug`, `evaluate`, `extract_quotes_from_payload`, `fetch_stocknow_live_market_data` |
| `_sync_in_session` | `L694–L796` | `(session: Any, quotes: list[dict[str...)` | `dict[str, Any]` | — | `CompanyProfile`, `CustomRule`, `add`, `append` |
| `sync_live_market_to_db` | `L799–L808` | `(target: Database | Any, quotes: lis...)` | `dict[str, Any]` | Synchronizes extracted live quotes into SQLite CompanyProfile records. | `_sync_in_session`, `hasattr`, `write` |


---

### 📄 [`backend/adapters/stocknow_portfolio_sync.py`](/backend/adapters/stocknow_portfolio_sync.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `parse_stocknow_ledger_date` | `L23–L44` | `(date_str: str...)` | `str` | Parse StockNow DD/MM/YY date string into YYYY-MM-DD ISO date. | `date`, `fromisoformat`, `group`, `int` |
| `_match_portfolio_name` | `L47–L48` | `(name: str...)` | `bool` | — | `lower`, `replace`, `strip` |
| `_find_portfolio_dict` | `L51–L67` | `(data: Any...)` | `dict[str, Any] | None` | — | `_find_portfolio_dict`, `_match_portfolio_name`, `get`, `isinstance` |
| `extract_hummingbird_portfolio` | `L70–L138` | `(client: Any | None=None, injected_p...)` | `dict[str, Any]` | Locate and extract 'Humming Bird' virtual portfolio from client or payload. | `Decimal`, `ValueError`, `_find_portfolio_dict`, `append` |
| `extract_hummingbird_portfolio_from_browser` | `L141–L146` | `(client: Any...)` | `dict[str, Any]` | Scrapes /portfolios/{id}/show and /portfolios/{id}/ledger from live Playwright session. | `_extract_hummingbird_portfolio_from_browser_impl`, `_run_in_proactor`, `hasattr`, `isinstance` |
| `_extract_hummingbird_portfolio_from_browser_impl` | `L149–L271` | `(client: Any...)` | `dict[str, Any]` | — | `RuntimeError`, `append`, `debug`, `decimal` |
| `_execute_reconciliation` | `L274–L443` | `(session: Session, settings: Setting...)` | `dict[str, Any]` | — | `CompanyProfile`, `CustomRule`, `Decimal`, `RuntimeError` |
| `reconcile_portfolio_to_db` | `L446–L453` | `(target: Database | Session, setting...)` | `dict[str, Any]` | Reconcile virtual portfolio holdings and cash balance into SQLite ledger. | `_execute_reconciliation`, `isinstance`, `write` |
| `sync_stocknow_portfolio_via_api` | `L456–L532` | `(portfolio_id: str | int, api_client...)` | `dict[str, Any]` | Sync target portfolio via StockNow REST API (GET /portfolios/{id} & ledger). | `SchemaChangedError`, `StockNowAPI`, `abs`, `dict` |


---

### 📄 [`backend/adapters/stocknow_write_guard.py`](/backend/adapters/stocknow_write_guard.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `StockNowWriteGuardError` | `L13–L17` | `PermissionError` | Raised when a POST operation attempts to target an unauthorized or non-test portfolio. | 1 |


**Methods in `StockNowWriteGuardError`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L15–L17` | `(self, message: str='TEST_PORTFOLIO_...)` | `None` | — | `__init__`, `super` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `verify_test_portfolio_post_guard` | `L20–L80` | `(target_portfolio_id: str | int | No...)` | `str` | Enforce strict hard guard: refuses any POST unless portfolio_id equals the test id. | `StockNowWriteGuardError`, `getenv`, `str`, `strip` |


---

### 📄 [`backend/adapters/tradexpress/__init__.py`](/backend/adapters/tradexpress/__init__.py)

---

### 📄 [`backend/adapters/tradexpress/cdp_daemon.py`](/backend/adapters/tradexpress/cdp_daemon.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `TradeXpressPassiveDaemon` | `L155–L393` | `object` | Continuous read-only CDP spy daemon observing TradeXpress 2.0 via DevTools Protocol. | 8 |


**Methods in `TradeXpressPassiveDaemon`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L158–L186` | `(self, database: Database, settings:...)` | `None` | — | `get_global_passive_feed` |
| `get_status` | `L188–L201` | `(self...)` | `dict[str, Any]` | Returns comprehensive telemetry dictionary for UI and API clients. | `redact_secrets` |
| `start` | `L203–L214` | `(self, cdp_url: str='http://127.0.0....)` | `dict[str, Any]` | Idempotently starts the continuous passive spy background task. | `_run_loop`, `create_task`, `done`, `get_status` |
| `stop` | `L216–L250` | `(self...)` | `dict[str, Any]` | Idempotently stops background spy loop and safely disconnects CDP client. | `cancel`, `close`, `debug`, `done` |
| `_run_loop` | `L252–L393` | `(self, cdp_url: str...)` | `None` | Main resilient observation loop. Auto-reconnects on browser restarts. | `TradeXpressShadowSimulator`, `async_playwright`, `close`, `connect_over_cdp` |
| `on_web_socket` | `L315–L320` | `(ws: Any...)` | `None` | — | `on` |
| `on_frame_received` | `L316–L318` | `(_payload: Any...)` | `None` | — | `update_tab_timestamp` |
| `on_response` | `L325–L328` | `(res: Any...)` | `None` | — | `lower` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `get_global_passive_daemon` | `L399–L414` | `(database: Database, settings: Setti...)` | `TradeXpressPassiveDaemon` | Singleton getter for the global TradeXpress passive CDP spy daemon. | `TradeXpressPassiveDaemon` |


---

### 📄 [`backend/adapters/tradexpress/passive_feed.py`](/backend/adapters/tradexpress/passive_feed.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `AccountSummary` | `L35–L59` | `object` | Live account balance telemetry from TradeXpress Account Summary tab. | 1 |
| `TradeXpressPassiveFeed` | `L281–L420` | `MarketFeedAdapter` | Thread-safe in-memory cache and feed adapter for TradeXpress passive market data. | 15 |


**Methods in `AccountSummary`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `to_dict` | `L48–L59` | `(self...)` | `dict[str, Any]` | — | `float` |


**Methods in `TradeXpressPassiveFeed`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L284–L297` | `(self, database: Database | None=Non...)` | `None` | — | `AccountSummary`, `RLock` |
| `set_cdp_connected` | `L299–L301` | `(self, connected: bool...)` | `None` | — | — |
| `update_ingest_telemetry` | `L303–L319` | `(self, source: str, dse_status: str=...)` | `None` | — | `time`, `utc_now_iso` |
| `is_bridge_connected` | `L321–L326` | `(self, now_utc: float | None=None...)` | `bool` | — | `time` |
| `get_telemetry` | `L328–L337` | `(self...)` | `dict[str, Any]` | — | `is_bridge_connected` |
| `update_tab_timestamp` | `L339–L341` | `(self, tab: str, timestamp: float | ...)` | `None` | — | `lower`, `time` |
| `update_quotes` | `L343–L346` | `(self, quotes: list[MarketQuote]...)` | `None` | — | — |
| `update_holdings` | `L348–L351` | `(self, holdings: list[PortfolioHoldi...)` | `None` | — | — |
| `update_account_summary` | `L353–L355` | `(self, summary: AccountSummary...)` | `None` | — | — |
| `get_account_summary` | `L357–L359` | `(self...)` | `AccountSummary` | — | — |
| `get_all_holdings` | `L361–L363` | `(self...)` | `dict[str, PortfolioHolding]` | — | `dict` |
| `get_all_quotes` | `L365–L367` | `(self...)` | `dict[str, MarketQuote]` | — | `dict` |
| `get_quote` | `L369–L402` | `(self, symbol: str...)` | `MarketQuote | None` | — | `Decimal`, `MarketQuote`, `from_tradexpress_symbol`, `get` |
| `get_quotes` | `L404–L410` | `(self, symbols: list[str]...)` | `dict[str, MarketQuote]` | — | `get_quote` |
| `get_health_and_guidance` | `L412–L420` | `(self, now_utc: float | None=None...)` | `dict[str, Any]` | — | `get_feed_health_and_guidance`, `is_bridge_connected` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `parse_ember_market_watch_rows` | `L62–L158` | `(rows: list[dict[str, Any]], existin...)` | `list[MarketQuote]` | Pure parser mapping Ember.js dataObj rows to MarketQuote instances. | `MarketQuote`, `append`, `bool`, `decimal` |
| `parse_ember_portfolio_rows` | `L161–L191` | `(rows: list[dict[str, Any]]...)` | `list[PortfolioHolding]` | Pure parser mapping Ember.js portfolio rows to PortfolioHolding instances. | `PortfolioHolding`, `append`, `decimal`, `from_tradexpress_symbol` |
| `parse_account_summary_dict` | `L194–L214` | `(data: dict[str, Any]...)` | `AccountSummary` | Parses raw Account Summary payload into an AccountSummary dataclass. | `AccountSummary`, `decimal`, `get`, `str` |
| `get_feed_health_and_guidance` | `L217–L278` | `(tab_timestamps: dict[str, float], c...)` | `dict[str, Any]` | Evaluates freshness of CDP/extension connection & each tab, generating operator guidance. | `all`, `append`, `get`, `round` |
| `get_global_passive_feed` | `L426–L433` | `(database: Database | None=None...)` | `TradeXpressPassiveFeed` | Singleton getter for the global passive market feed adapter. | `TradeXpressPassiveFeed` |
| `ingest_passive_snapshot` | `L436–L645` | `(db: Database, snapshot_payload: dic...)` | `dict[str, Any]` | Ingests passively sniffed snapshot payload into SQLite and in-memory feed. | `CompanyProfile`, `add`, `append`, `bool` |


---

### 📄 [`backend/adapters/tradexpress/shadow_simulator.py`](/backend/adapters/tradexpress/shadow_simulator.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `TradeXpressShadowSimulator` | `L61–L868` | `BrokerOrderExecutor` | Realistic limit order simulator executing against passive Level-2 order depth. | 9 |


**Methods in `TradeXpressShadowSimulator`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L64–L73` | `(self, database: Database, settings:...)` | `None` | — | `TradingCalendar`, `get_global_passive_feed` |
| `validate_order` | `L75–L120` | `(self, session: Session, *, symbol: ...)` | `tuple[bool, list[str]]` | Validates order against TradeXpress and DSE safety invariants. | `from_tradexpress_symbol`, `get`, `get_all_quotes`, `getattr` |
| `execute_order` | `L122–L139` | `(self, symbol: str, side: str, quant...)` | `dict[str, Any]` | BrokerOrderExecutor interface entry point. | `submit_shadow_order` |
| `submit_shadow_order` | `L141–L225` | `(self, *, symbol: str, side: str, qu...)` | `dict[str, Any]` | Submits an order into the shadow simulator with 2-step verification support. | `_execute_shadow_order_in_session`, `calculate_broker_fee_breakdown`, `float`, `from_tradexpress_symbol` |
| `_execute_shadow_order_in_session` | `L227–L465` | `(self, session: Session, clean_symbo...)` | `dict[str, Any]` | — | `Decimal`, `ShadowOrder`, `TradeLearningLog`, `_process_fill` |
| `_process_fill` | `L467–L736` | `(self, session: Session, state: Port...)` | `dict[str, Any]` | Executes fill accounting, tax lot adjustments, and trade logs. | `Decimal`, `ShadowOrder`, `TaxLot`, `TradeLearningLog` |
| `reconcile_queued_orders` | `L738–L813` | `(self, session: Session, quotes: dic...)` | `list[dict[str, Any]]` | Evaluates pending QUEUED orders against fresh quote depth and expires at session close. | `_process_fill`, `append`, `create_checkpoint`, `flush` |
| `cancel_order` | `L815–L831` | `(self, order_ref: str...)` | `dict[str, Any]` | Cancels a resting QUEUED shadow order. | `flush`, `scalar`, `select`, `where` |
| `get_orders` | `L833–L868` | `(self, portfolio_id: str='H9210_SHAD...)` | `list[dict[str, Any]]` | Retrieves shadow orders for cockpit display (mirroring TradeXpress Order List). | `desc`, `float`, `isoformat`, `limit` |


---

### 📄 [`backend/config.py`](/backend/config.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `Settings` | `L26–L144` | `object` | — | 5 |


**Methods in `Settings`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `operator_phone` | `L60–L61` | `(self...)` | `str` | — | — |
| `stocknow_mobile` | `L64–L65` | `(self...)` | `str` | — | — |
| `stocknow_password` | `L68–L69` | `(self...)` | `str` | — | — |
| `__post_init__` | `L71–L95` | `(self...)` | `None` | — | `Decimal`, `ValueError`, `any`, `is_finite` |
| `from_env` | `L98–L144` | `(cls...)` | `Settings` | — | `Decimal`, `cls`, `float`, `fromisoformat` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `utc_now_iso` | `L21–L22` | `(...)` | `str` | — | `isoformat`, `now` |
| `get_allowed_portfolios` | `L147–L164` | `(settings: Settings | None=None...)` | `tuple[str, ...]` | Returns the allowlist of authorized StockNow portfolio IDs: [LIVE, TEST]. | `append`, `from_env`, `getenv`, `strip` |
| `get_active_target_portfolio` | `L167–L183` | `(trading_mode: str, settings: Settin...)` | `str | None` | Returns the active portfolio ID based on current trading mode: | `from_env`, `getenv`, `strip` |
| `get_portfolio_name` | `L186–L204` | `(portfolio_id: str, settings: Settin...)` | `str` | Returns human-readable portfolio name for a given portfolio ID. | `getattr`, `getenv`, `str`, `strip` |
| `test_portfolio_configured` | `L207–L213` | `(settings: Settings | None=None...)` | `bool` | Returns True when a portfolio id is configured for testing (can be same as live). | `bool`, `getenv`, `strip` |


---

### 📄 [`backend/database.py`](/backend/database.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `Base` | `L38–L39` | `DeclarativeBase` | — | 0 |
| `PortfolioState` | `L42–L71` | `Base` | — | 0 |
| `CompanyProfile` | `L74–L98` | `Base` | — | 0 |
| `CustomRule` | `L101–L112` | `Base` | — | 0 |
| `TaxLot` | `L115–L142` | `Base` | — | 0 |
| `AutomationCycle` | `L145–L154` | `Base` | — | 0 |
| `TradeLog` | `L157–L184` | `Base` | — | 0 |
| `CanaryThesis` | `L187–L199` | `Base` | — | 0 |
| `KernelStateCheckpoint` | `L202–L212` | `Base` | — | 0 |
| `CycleRequestKey` | `L215–L218` | `Base` | — | 0 |
| `DecisionLog` | `L221–L231` | `Base` | — | 0 |
| `RuleAudit` | `L234–L242` | `Base` | — | 0 |
| `KernelAuditLog` | `L245–L256` | `Base` | — | 0 |
| `OrderIdempotencyKey` | `L259–L267` | `Base` | — | 0 |
| `ShadowOrder` | `L270–L291` | `Base` | — | 0 |
| `TradeLearningLog` | `L294–L313` | `Base` | — | 0 |
| `ChatBudget` | `L316–L319` | `Base` | — | 0 |
| `SystemHeartbeat` | `L322–L332` | `Base` | — | 0 |
| `PreflightCheckLog` | `L335–L343` | `Base` | — | 0 |
| `DailySummaryLog` | `L346–L361` | `Base` | — | 0 |
| `Database` | `L364–L544` | `object` | — | 5 |


**Methods in `Database`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L365–L385` | `(self, url: str...)` | — | — | `Path`, `RLock`, `ValueError`, `create_engine` |
| `configure_sqlite` | `L378–L383` | `(connection: Any, _record: Any...)` | `None` | — | `close`, `cursor`, `execute`, `listens_for` |
| `create_schema` | `L387–L523` | `(self...)` | `None` | — | `commit`, `connect`, `create_all`, `execute` |
| `read` | `L526–L533` | `(self...)` | — | — | `execute`, `rollback`, `sessions`, `text` |
| `write` | `L536–L544` | `(self...)` | — | — | `commit`, `execute`, `rollback`, `sessions` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `portfolio_state` | `L547–L551` | `(session: Session...)` | `PortfolioState` | — | `RuntimeError`, `get` |


---

### 📄 [`backend/engine/__init__.py`](/backend/engine/__init__.py)

---

### 📄 [`backend/engine/agent_actions.py`](/backend/engine/agent_actions.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `emergency_quarantine_and_canary` | `L25–L136` | `(session: Session, state: PortfolioS...)` | `dict` | — | `CanaryThesis`, `Decimal`, `TradeLog`, `TradingCalendar` |
| `restore_quarantine` | `L139–L167` | `(session: Session, state: PortfolioS...)` | `dict` | — | `ValueError`, `flush`, `get`, `len` |
| `check_canary_theses` | `L170–L200` | `(session: Session, state: PortfolioS...)` | `list[dict]` | — | `Decimal`, `append`, `float`, `flush` |
| `execute_agentic_buy` | `L203–L295` | `(session: Session, state: PortfolioS...)` | `dict` | — | `Decimal`, `TaxLot`, `TradeLog`, `TradingCalendar` |
| `execute_agentic_sell` | `L298–L408` | `(session: Session, state: PortfolioS...)` | `dict` | — | `Decimal`, `TradeLog`, `TradingCalendar`, `ValueError` |
| `cycle_key` | `L411–L412` | `(state: PortfolioState...)` | `str` | — | — |


---

### 📄 [`backend/engine/auto_trader.py`](/backend/engine/auto_trader.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `AutomationPaused` | `L39–L40` | `ValueError` | — | 0 |
| `CycleResult` | `L43–L48` | `dict` | Dictionary subclass that equals [] when trades are empty, ensuring backward compatibility with tests asserting trades == []. | 1 |
| `AutoTrader` | `L51–L885` | `object` | — | 8 |


**Methods in `CycleResult`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__eq__` | `L45–L48` | `(self, other...)` | — | — | `__eq__`, `get`, `isinstance`, `super` |


**Methods in `AutoTrader`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L52–L56` | `(self, database: Database, settings:...)` | — | — | `StockNowAdapter`, `TradingCalendar` |
| `run_cycle` | `L58–L68` | `(self, request_id: str | None=None, ...)` | `dict` | — | `_run_cycle_internal`, `acquire_trading_lock`, `write` |
| `_dispatch_order` | `L70–L141` | `(self, symbol: str, side: str, quant...)` | `dict | None` | — | `Decimal`, `ThreadPoolExecutor`, `TradeXpressShadowSimulator`, `execute_order` |
| `_run_cycle_internal` | `L143–L837` | `(self, session: Session, request_id:...)` | `dict` | — | `AutomationCycle`, `CycleRequestKey`, `CycleResult`, `Decimal` |
| `record` | `L351–L367` | `(symbol: str, action: str, reason: s...)` | — | — | `DecisionLog`, `add`, `append`, `startswith` |
| `buy_priority` | `L554–L560` | `(comp: CompanyProfile...)` | `tuple[int, str]` | — | `getattr` |
| `_trade_result` | `L840–L846` | `(trade: TradeLog, action: str...)` | `dict` | — | `float` |
| `advance_demo` | `L848–L885` | `(self, scenario: str...)` | `dict` | — | `Decimal`, `ValueError`, `add_sessions`, `assert_ledger` |


---

### 📄 [`backend/engine/checkpoint.py`](/backend/engine/checkpoint.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `CheckpointManager` | `L25–L198` | `object` | Manages transactional state checkpoints and atomic rollback restoration. | 2 |


**Methods in `CheckpointManager`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `create_checkpoint` | `L29–L86` | `(session: Session, state: PortfolioS...)` | `KernelStateCheckpoint` | — | `KernelStateCheckpoint`, `add`, `flush`, `get` |
| `rollback_last` | `L89–L198` | `(session: Session, state: PortfolioS...)` | `dict[str, Any]` | — | `TaxLot`, `TradeLog`, `ValueError`, `add` |


---

### 📄 [`backend/engine/circuit_breaker.py`](/backend/engine/circuit_breaker.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `record_circuit_failure` | `L29–L122` | `(db: Database, settings: Settings, f...)` | `bool` | Record an operational failure and trip the circuit breaker if thresholds are met. | `DecisionLog`, `KernelAuditLog`, `add`, `error` |
| `record_circuit_success` | `L125–L130` | `(db: Database...)` | `None` | Resets consecutive failure count on successful execution/cycle. | `portfolio_state`, `write` |
| `reset_circuit_breaker` | `L133–L175` | `(db: Database, settings: Settings | ...)` | `dict[str, Any]` | Manually resets the tripped circuit breaker. | `KernelAuditLog`, `add`, `hasattr`, `portfolio_state` |
| `is_circuit_breaker_tripped` | `L178–L182` | `(db: Database...)` | `tuple[bool, str | None]` | Checks whether the circuit breaker is currently tripped. | `bool`, `portfolio_state`, `read` |


---

### 📄 [`backend/engine/curve_analyzer.py`](/backend/engine/curve_analyzer.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `CurveAnalysis` | `L15–L31` | `object` | — | 1 |


**Methods in `CurveAnalysis`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `to_dict` | `L27–L31` | `(self...)` | `dict[str, Any]` | — | `float`, `isinstance`, `items` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `analyze_curve` | `L34–L117` | `(history: list[dict[str, str]], *, a...)` | `CurveAnalysis` | — | `CurveAnalysis`, `Decimal`, `ValueError`, `abs` |


---

### 📄 [`backend/engine/heartbeat.py`](/backend/engine/heartbeat.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `record_system_heartbeat` | `L37–L62` | `(db: Database, settings: Settings | ...)` | `SystemHeartbeat` | Records a single 1-minute system heartbeat to SQLite and prunes entries older than 7 days. | `SystemHeartbeat`, `add`, `delete`, `execute` |
| `check_dead_man_switch` | `L65–L120` | `(db: Database, settings: Settings, n...)` | `bool` | Checks if the heartbeat is stale (>120s) during DSE market hours. | `desc`, `fromisoformat`, `is_dse_market_open`, `limit` |
| `send_daily_summary_if_due` | `L123–L234` | `(db: Database, settings: Settings, n...)` | `bool` | Generates and sends the 14:45 Asia/Dhaka daily session summary to Telegram and logs to SQLite. | `DailySummaryLog`, `Decimal`, `TradingCalendar`, `abs` |


---

### 📄 [`backend/engine/money.py`](/backend/engine/money.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `decimal` | `L11–L12` | `(value: object...)` | `Decimal` | — | `Decimal`, `isinstance`, `str` |
| `money` | `L15–L16` | `(value: Decimal...)` | `Decimal` | — | `quantize` |
| `price` | `L19–L20` | `(value: Decimal...)` | `Decimal` | — | `quantize` |
| `whole_shares` | `L23–L24` | `(value: Decimal...)` | `int` | — | `int`, `to_integral_value` |
| `purchase_amount` | `L27–L30` | `(quantity: int, unit_price: Decimal,...)` | `tuple[Decimal, Decimal]` | — | `money` |
| `sale_amount` | `L33–L36` | `(quantity: int, unit_price: Decimal,...)` | `tuple[Decimal, Decimal]` | — | `money` |
| `allocated_basis` | `L39–L44` | `(remaining_basis: Decimal, remaining...)` | `Decimal` | — | `ValueError`, `money` |
| `calculate_broker_fee_breakdown` | `L47–L68` | `(gross_amount: Decimal, *, commissio...)` | `dict[str, Decimal]` | Calculate exact gross, broker commission, VAT on commission, and exchange fees. | `Decimal`, `money`, `quantize` |
| `round_trip_breakeven_price` | `L71–L85` | `(buy_price: Decimal, *, buy_fee_rate...)` | `Decimal` | Computes exact minimum gross sell price required for net_profit >= 0 after both fees. | `Decimal`, `ValueError`, `money` |


---

### 📄 [`backend/engine/preflight_service.py`](/backend/engine/preflight_service.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `are_caps_set` | `L23–L40` | `(db: Database...)` | `bool` | Check whether all risk caps are configured and greater than zero. | `getattr`, `portfolio_state`, `read` |
| `has_passing_preflight_within_24h` | `L43–L57` | `(db: Database...)` | `bool` | Verifies if a passing preflight check was logged within the last 24 hours. | `desc`, `isoformat`, `limit`, `now` |
| `record_preflight_result` | `L60–L91` | `(db: Database, all_passed: bool, che...)` | `dict[str, Any]` | Records a preflight verification result into the preflight_check_logs table. | `PreflightCheckLog`, `add`, `flush`, `get` |
| `run_cockpit_preflight` | `L94–L119` | `(db: Database, settings: Settings, a...)` | `dict[str, Any]` | Executes the preflight check suite and persists the audit log. | `are_caps_set`, `bool`, `portfolio_state`, `read` |


---

### 📄 [`backend/engine/price_guard.py`](/backend/engine/price_guard.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `set_market_quote` | `L12–L25` | `(symbol: str, ltp: float | Decimal |...)` | `None` | Explicitly register an in-memory market quote for tests or runtime hooks. | `float`, `strip`, `upper` |
| `get_market_quote` | `L28–L55` | `(symbol: str, comp: Any=None...)` | `dict[str, Any] | None` | Retrieves cached live market quote for symbol. | `float`, `get`, `getattr`, `startswith` |
| `clear_market_quotes` | `L58–L60` | `(...)` | `None` | Clears in-memory market quotes registry. | `clear` |
| `check_price_sanity` | `L63–L121` | `(price: float | Decimal | int | str ...)` | `tuple[bool, str]` | Validates order price against market LTP and day range. | `abs`, `float` |


---

### 📄 [`backend/engine/scheduler.py`](/backend/engine/scheduler.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `DSEMarketScheduler` | `L91–L330` | `object` | Async background scheduler enforcing DSE market hours and periodic trading cycles. | 8 |


**Methods in `DSEMarketScheduler`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L94–L116` | `(self, database: Database, settings:...)` | — | — | `AutoTrader`, `hasattr` |
| `get_status` | `L118–L139` | `(self...)` | `dict[str, Any]` | Returns scheduler operational status, telemetry, and DSE market gate. | `getattr`, `is_dse_market_open`, `portfolio_state`, `read` |
| `run_scheduled_tick` | `L141–L225` | `(self, force: bool=False...)` | `dict[str, Any]` | Executes a single scheduler tick, enforcing gate & automation state unless force=True. | `DecisionLog`, `add`, `build_snapshot`, `debug` |
| `run_scheduled_tick_sync` | `L227–L279` | `(self, force: bool=False, session: A...)` | `dict[str, Any]` | Synchronous version of tick execution (e.g. for Hermes chat turn). | `build_snapshot`, `debug`, `getattr`, `info` |
| `start` | `L281–L294` | `(self...)` | `dict[str, Any]` | Starts background periodic polling loop idempotently. | `_loop`, `cancel`, `create_task`, `done` |
| `stop_sync` | `L296–L304` | `(self...)` | `dict[str, Any]` | Stops background periodic polling loop gracefully (sync). | `cancel`, `done`, `get_status` |
| `stop` | `L306–L308` | `(self...)` | `dict[str, Any]` | Stops background periodic polling loop gracefully. | `stop_sync` |
| `_loop` | `L310–L330` | `(self...)` | `None` | Background periodic execution loop respecting configured polling interval. | `error`, `getattr`, `info`, `max` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `get_active_scheduler` | `L30–L32` | `(...)` | `DSEMarketScheduler | None` | Returns the globally active scheduler singleton instance if registered. | — |
| `is_dse_market_open` | `L35–L88` | `(now_dhaka: datetime | None=None, se...)` | `dict[str, Any]` | Evaluates whether DSE is currently open for trading in Asia/Dhaka time. | `Settings`, `TradingCalendar`, `astimezone`, `date` |


---

### 📄 [`backend/engine/sequential_seller.py`](/backend/engine/sequential_seller.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `SellState` | `L13–L21` | `object` | — | 0 |
| `SellPlan` | `L25–L34` | `object` | — | 0 |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `plan_sale` | `L37–L141` | `(state: SellState, *, current_price:...)` | `SellPlan` | — | `Decimal`, `SellPlan`, `ValueError`, `allocated_basis` |


---

### 📄 [`backend/engine/signals.py`](/backend/engine/signals.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `assess_company` | `L15–L45` | `(company: CompanyProfile, rule: Cust...)` | `tuple[CurveAnalysis, DemoQuote | None]` | — | `CurveAnalysis`, `analyze_curve`, `decimal`, `lower` |


---

### 📄 [`backend/engine/t2_ledger.py`](/backend/engine/t2_ledger.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `TradingCalendar` | `L19–L51` | `object` | — | 5 |
| `BucketBalance` | `L55–L63` | `object` | — | 0 |


**Methods in `TradingCalendar`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `is_session` | `L23–L24` | `(self, day: date...)` | `bool` | — | `weekday` |
| `on_or_before` | `L26–L29` | `(self, day: date...)` | `date` | — | `is_session`, `timedelta` |
| `add_sessions` | `L31–L37` | `(self, day: date, count: int...)` | `date` | — | `abs`, `is_session`, `range`, `timedelta` |
| `session_distance` | `L39–L46` | `(self, start: date, end: date...)` | `int` | — | `int`, `is_session`, `session_distance`, `timedelta` |
| `bucket_for` | `L48–L51` | `(self, day: date...)` | `str` | — | `ValueError`, `is_session`, `session_distance` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `bucket_balances` | `L66–L111` | `(session: Session, state: PortfolioS...)` | `dict[str, BucketBalance]` | — | `BucketBalance`, `RuntimeError`, `all`, `distinct` |
| `assert_ledger` | `L114–L134` | `(session: Session, state: PortfolioS...)` | `None` | Book assets must equal initial capital plus realized P/L, to the paisa. | `RuntimeError`, `all`, `bucket_balances`, `distinct` |


---

### 📄 [`backend/engine/telegram_bot.py`](/backend/engine/telegram_bot.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `TelegramBotDaemon` | `L186–L247` | `object` | Long-polling daemon listening for operator Telegram commands. | 4 |


**Methods in `TelegramBotDaemon`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L189–L194` | `(self, db: Database, settings: Setti...)` | `None` | — | — |
| `start` | `L196–L205` | `(self...)` | `None` | — | `_poll_loop`, `create_task`, `debug`, `getattr` |
| `stop` | `L207–L211` | `(self...)` | `None` | — | `cancel`, `done`, `info` |
| `_poll_loop` | `L213–L247` | `(self...)` | `None` | — | `AsyncClient`, `debug`, `get`, `getattr` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `send_telegram_alert` | `L29–L54` | `(text: str, settings: Settings | Non...)` | `bool` | Dispatches a message to the configured Telegram chat. | `AsyncClient`, `getattr`, `getenv`, `post` |
| `send_telegram_alert_sync` | `L57–L74` | `(text: str, settings: Settings | Non...)` | `bool` | Synchronous wrapper for sending Telegram alerts. | `ThreadPoolExecutor`, `get_running_loop`, `is_running`, `result` |
| `handle_telegram_command` | `L77–L183` | `(command: str, db: Database, setting...)` | `str` | Executes a text command received from Telegram operator and returns response text. | `KernelAuditLog`, `add`, `float`, `getattr` |


---

### 📄 [`backend/engine/trading_lock.py`](/backend/engine/trading_lock.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `acquire_trading_lock` | `L21–L30` | `(timeout: float=30.0...)` | `Generator[None, None, None]` | Acquires the single-writer trading lock with timeout protection. | `RuntimeError`, `acquire`, `error`, `release` |


---

### 📄 [`backend/hermes_bridge.py`](/backend/hermes_bridge.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `BridgeChatRequest` | `L76–L79` | `BaseModel` | — | 0 |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `get_hermes_dir` | `L28–L47` | `(profile: str='hummingbird'...)` | `Path` | Returns the Hermes profile directory (hummingbird profile if available, else hermes home). | `Path`, `exists`, `get`, `home` |
| `get_hermes_bin` | `L50–L60` | `(...)` | `str` | Returns path to the hermes executable, preferring vendor/hermes-agent editable in .venv. | `Path`, `exists`, `get`, `str` |
| `get_hermes_cmd` | `L63–L73` | `(...)` | `list[str]` | Returns command arguments for Hermes CLI, preferring python -m to bypass Windows AppControl (WinError 4551). | `exists`, `get_hermes_bin`, `run`, `str` |
| `stream_hermes_chat` | `L82–L148` | `(message: str, session_id: Optional[...)` | `AsyncGenerator[str, None]` | Streams SSE events from running Hermes gateway API server. | `AsyncClient`, `aiter_lines`, `append`, `aread` |
| `read_hermes_state` | `L151–L316` | `(...)` | `dict[str, Any]` | Reads skills, memory (USER.md / MEMORY.md), active model, and cron jobs from Hermes. | `Path`, `_extract_skill_meta`, `_get_bundled_skill_names`, `any` |
| `_extract_skill_meta` | `L319–L336` | `(path: Path...)` | `dict[str, Any]` | Extracts frontmatter metadata from a SKILL.md file. | `get`, `isinstance`, `len`, `read_text` |
| `_get_bundled_skill_names` | `L339–L375` | `(skills_root: Path | None=None...)` | `set[str]` | Resolves names of bundled Hermes skills via hidden manifest or vendor directory. | `add`, `append`, `exists`, `get_hermes_dir` |
| `run_hermes_cron_cmd` | `L378–L389` | `(*args: str...)` | `dict[str, Any]` | Runs a hermes cron sub-command synchronously on the hummingbird profile. | `get_hermes_cmd`, `run`, `str`, `strip` |
| `build_hermes_bridge_router` | `L392–L439` | `(database: Any=None, settings: Any=N...)` | `APIRouter` | Builds and returns the Hermes bridge router. | `APIRouter` |
| `bridge_chat` | `L397–L407` | `(body: BridgeChatRequest...)` | — | Streaming chat endpoint proxying to running Hermes. | `StreamingResponse`, `post`, `stream_hermes_chat` |
| `bridge_state` | `L411–L413` | `(...)` | — | Returns active model, skills, memory preview, and cron jobs directly from Hermes. | `get`, `read_hermes_state` |
| `bridge_cron_pause` | `L416–L421` | `(job_id: str...)` | — | Pauses a scheduled Hermes cron job. | `HTTPException`, `get`, `post`, `run_hermes_cron_cmd` |
| `bridge_cron_resume` | `L424–L429` | `(job_id: str...)` | — | Resumes a paused Hermes cron job. | `HTTPException`, `get`, `post`, `run_hermes_cron_cmd` |
| `bridge_cron_delete` | `L432–L437` | `(job_id: str...)` | — | Deletes a scheduled Hermes cron job. | `HTTPException`, `delete`, `get`, `run_hermes_cron_cmd` |


---

### 📄 [`backend/kernel_api.py`](/backend/kernel_api.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `SetTierRequest` | `L292–L294` | `BaseModel` | — | 0 |
| `SetAllocationRequest` | `L352–L355` | `BaseModel` | — | 0 |
| `QuarantineRequest` | `L421–L424` | `BaseModel` | — | 0 |
| `SyncRequest` | `L520–L522` | `BaseModel` | — | 0 |
| `OrderRequest` | `L712–L729` | `BaseModel` | — | 1 |
| `SetTradingModeRequest` | `L1277–L1279` | `BaseModel` | — | 0 |
| `SetAutomationConfigRequest` | `L1341–L1345` | `BaseModel` | — | 0 |
| `KernelHandoffRequest` | `L1445–L1446` | `BaseModel` | — | 0 |
| `SchedulerActionRequest` | `L1525–L1526` | `BaseModel` | — | 0 |
| `RunCycleRequest` | `L1598–L1600` | `BaseModel` | — | 0 |
| `StockNowSessionActionRequest` | `L1648–L1650` | `BaseModel` | — | 0 |
| `CapsUpdateRequest` | `L1732–L1738` | `BaseModel` | — | 0 |


**Methods in `OrderRequest`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `handle_confirm_alias` | `L725–L729` | `(cls, data: Any...)` | `Any` | — | `isinstance`, `model_validator` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `get_broadcaster` | `L74–L78` | `(request: Request | None=None...)` | `Any` | Resolve global or request broadcaster instance. | `hasattr` |
| `clear_order_idempotency_cache` | `L81–L84` | `(...)` | `None` | Clear order idempotency cache and preview tokens (for tests). | `clear` |
| `verify_kernel_auth` | `L87–L114` | `(request: Request, x_kernel_token: s...)` | `None` | Enforces 127.0.0.1 localhost binding and X-Kernel-Token / Bearer authentication. | `HTTPException`, `Header`, `getenv`, `replace` |
| `get_db` | `L117–L122` | `(request: Request...)` | `Database` | Extract database from app state or fallback to default. | `Database`, `get_settings`, `hasattr` |
| `get_settings` | `L125–L129` | `(request: Request...)` | `Settings` | Extract settings from app state or fallback to default. | `from_env`, `hasattr` |
| `get_stocknow_client` | `L132–L139` | `(request: Request...)` | `Any | None` | Extract live StockNow Playwright client if attached. | `get_active_scheduler`, `getattr`, `hasattr` |
| `get_portfolio` | `L151–L158` | `(request: Request, db: Database=Depe...)` | `dict[str, Any]` | Returns full portfolio snapshot with holdings, cash, and rolling buckets. | `Depends`, `get`, `read`, `snapshot_from_session` |
| `get_watchlist` | `L162–L188` | `(tier: str | None=Query(None, descri...)` | `list[dict[str, Any]]` | Returns watchlist companies, optionally filtered by tier. | `Depends`, `Query`, `append`, `float` |
| `get_curve` | `L192–L224` | `(symbol: str, db: Database=Depends(g...)` | `dict[str, Any]` | Returns price curve analysis, support floor, resistance ceiling, and sparkline points. | `Depends`, `HTTPException`, `analyze_curve`, `float` |
| `get_market_open` | `L228–L230` | `(settings: Settings=Depends(get_sett...)` | `dict[str, Any]` | Returns real DSE trading hours and session status in Asia/Dhaka time. | `Depends`, `get`, `is_dse_market_open` |
| `get_canaries` | `L234–L252` | `(db: Database=Depends(get_db)...)` | `list[dict[str, Any]]` | Returns active and past 10% canary probe theses. | `Depends`, `desc`, `float`, `get` |
| `get_lots` | `L256–L284` | `(symbol: str | None=Query(None, desc...)` | `list[dict[str, Any]]` | Returns T+2 rolling tax lots with maturity status. | `Depends`, `Query`, `float`, `get` |
| `post_tier` | `L298–L349` | `(body: SetTierRequest, db: Database=...)` | `dict[str, Any]` | Updates a company's watchlist tier (GSC, GSC_L1, GSC_L2). | `Depends`, `HTTPException`, `KernelAuditLog`, `RuleAudit` |
| `post_allocation` | `L359–L418` | `(body: SetAllocationRequest, db: Dat...)` | `dict[str, Any]` | Updates buying allocation percentage for a company rule. | `Depends`, `HTTPException`, `KernelAuditLog`, `RuleAudit` |
| `post_quarantine` | `L428–L479` | `(body: QuarantineRequest, db: Databa...)` | `dict[str, Any]` | Places stock in 90% profit-lock + 10% canary quarantine, or restores it. | `Depends`, `HTTPException`, `KernelAuditLog`, `add` |
| `post_canary_evaluate` | `L483–L517` | `(db: Database=Depends(get_db)...)` | `dict[str, Any]` | Evaluates observing canary probe theses against recent price movements. | `Depends`, `KernelAuditLog`, `add`, `check_canary_theses` |
| `post_sync` | `L526–L617` | `(body: SyncRequest, db: Database=Dep...)` | `dict[str, Any]` | Syncs market prices, all-shares board, or virtual portfolio holdings. | `Depends`, `HTTPException`, `KernelAuditLog`, `add` |
| `_compute_order_reconcile_and_drift` | `L620–L680` | `(session: Any, state: PortfolioState...)` | `dict[str, Any]` | Verifies local ledger integrity and compares holdings with StockNow to detect drift. | `abs`, `assert_ledger`, `bool`, `bucket_balances` |
| `_record_order_rejection` | `L683–L709` | `(session: Any, state: PortfolioState...)` | `None` | Records DecisionLog and KernelAuditLog for any rejected order. | `DecisionLog`, `KernelAuditLog`, `add`, `commit` |
| `post_order` | `L733–L1240` | `(body: OrderRequest, request: Reques...)` | `dict[str, Any]` | Submits a virtual BUY or SELL order enforcing T+2 maturity, strict no-loss, and 0.5% fees. | `Decimal`, `Depends`, `HTTPException`, `KernelAuditLog` |
| `post_rollback` | `L1244–L1269` | `(db: Database=Depends(get_db)...)` | `dict[str, Any]` | Rolls back the last state checkpoint atomically. | `Depends`, `HTTPException`, `KernelAuditLog`, `add` |
| `get_trading_mode` | `L1283–L1291` | `(db: Database=Depends(get_db)...)` | `dict[str, Any]` | Returns current trading mode (TEST_OFFHOURS or LIVE_HOURS). | `Depends`, `get`, `getattr`, `portfolio_state` |
| `post_trading_mode` | `L1295–L1338` | `(body: SetTradingModeRequest, db: Da...)` | `dict[str, Any]` | Sets trading mode to TEST_OFFHOURS or LIVE_HOURS with snapshot and audit log. | `Depends`, `HTTPException`, `KernelAuditLog`, `add` |
| `get_automation_config` | `L1349–L1358` | `(db: Database=Depends(get_db)...)` | `dict[str, Any]` | Returns master buy/sell automation switch, paused state, ingestion mode, and polling interval. | `Depends`, `bool`, `get`, `getattr` |
| `post_automation_config` | `L1362–L1442` | `(body: SetAutomationConfigRequest, d...)` | `dict[str, Any]` | Updates master automation switch, paused state, ingestion mode, or polling interval with snapshot & audit. | `Depends`, `HTTPException`, `KernelAuditLog`, `add` |
| `post_automation_handoff` | `L1450–L1502` | `(body: KernelHandoffRequest, db: Dat...)` | `dict[str, Any]` | Single-writer run mode handoff: finishes current cycle under lock, then switches mode. | `Depends`, `HTTPException`, `KernelAuditLog`, `acquire_trading_lock` |
| `post_reset_circuit_breaker` | `L1506–L1512` | `(db: Database=Depends(get_db), setti...)` | `dict[str, Any]` | Manually resets the tripped circuit breaker and clears consecutive failure count. | `Depends`, `post`, `reset_circuit_breaker` |
| `post_run_preflight` | `L1516–L1522` | `(db: Database=Depends(get_db), setti...)` | `dict[str, Any]` | Executes the preflight check suite and returns the readiness audit. | `Depends`, `post`, `run_cockpit_preflight` |
| `get_scheduler_status` | `L1530–L1541` | `(settings: Settings=Depends(get_sett...)` | `dict[str, Any]` | Returns current scheduler operational status and telemetry. | `Depends`, `get`, `get_active_scheduler`, `get_status` |
| `post_scheduler_control` | `L1545–L1595` | `(body: SchedulerActionRequest, db: D...)` | `dict[str, Any]` | Controls background market scheduler (start, stop, status). | `Depends`, `KernelAuditLog`, `add`, `create_checkpoint` |
| `post_run_cycle` | `L1604–L1645` | `(body: RunCycleRequest, db: Database...)` | `dict[str, Any]` | Executes an automation trading cycle via AutoTrader under the single-writer trading lock. | `AutoTrader`, `Depends`, `KernelAuditLog`, `acquire_trading_lock` |
| `post_stocknow_session` | `L1654–L1729` | `(body: StockNowSessionActionRequest,...)` | `dict[str, Any]` | Controls live StockNow session (launch, status, login, logout). | `Depends`, `KernelAuditLog`, `add`, `create_checkpoint` |
| `get_caps` | `L1742–L1775` | `(db: Database=Depends(get_db), setti...)` | `dict[str, Any]` | Fetch current risk limits, kill switch status, and today's usage scoped by active portfolio. | `Decimal`, `Depends`, `abs`, `all` |
| `set_caps` | `L1779–L1866` | `(body: CapsUpdateRequest, db: Databa...)` | `dict[str, Any]` | Update risk limits in the kernel. May only lower limits by itself; raising a limit requires confirmation. | `Decimal`, `Depends`, `HTTPException`, `KernelAuditLog` |
| `get_feed_status` | `L1870–L1900` | `(request: Request, db: Database=Depe...)` | — | Returns TradeXpress passive feed status, daemon metrics, and operator guidance for Hermes. | `Depends`, `float`, `get`, `get_account_summary` |
| `get_learning_summary` | `L1904–L1953` | `(tier: str | None=Query(None, descri...)` | — | Returns TradeLearningLog review metrics, win rate, and recent logs for Hermes self-learning. | `Depends`, `Query`, `desc`, `float` |
| `build_kernel_router` | `L1961–L1971` | `(database: Database, settings: Setti...)` | `APIRouter` | Builds the configured kernel router for inclusion in main app. | — |
| `create_kernel_app` | `L1974–L1997` | `(database: Database | None=None, set...)` | `FastAPI` | Creates a standalone FastAPI service for the trading kernel binding 127.0.0.1. | `Database`, `FastAPI`, `Settings`, `create_schema` |


---

### 📄 [`backend/logging_config.py`](/backend/logging_config.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `SecretRedactingFilter` | `L54–L68` | `logging.Filter` | Logging filter that scrubs sensitive credentials from log records. | 1 |


**Methods in `SecretRedactingFilter`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `filter` | `L57–L68` | `(self, record: logging.LogRecord...)` | `bool` | — | `isinstance`, `items`, `redact_secrets`, `str` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `redact_secrets` | `L34–L51` | `(text: str...)` | `str` | Sanitize secrets, phones, tokens and credentials from string. | `isinstance`, `str`, `sub` |
| `setup_logging` | `L71–L120` | `(log_dir: Path | str | None=None, lo...)` | `logging.Logger` | Configure rotating file and console logging with secret redaction. | `Formatter`, `Path`, `RotatingFileHandler`, `SecretRedactingFilter` |


---

### 📄 [`backend/main.py`](/backend/main.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `PauseRequest` | `L69–L71` | `BaseModel` | — | 0 |
| `AutomationConfigRequest` | `L74–L80` | `BaseModel` | — | 0 |
| `HandoffRequest` | `L83–L86` | `BaseModel` | — | 0 |
| `KillRequest` | `L89–L92` | `BaseModel` | — | 0 |
| `AdvanceRequest` | `L95–L97` | `BaseModel` | — | 0 |
| `AllocationRequest` | `L100–L103` | `BaseModel` | — | 0 |
| `EventBroadcaster` | `L106–L123` | `object` | — | 4 |
| `DevStaticFiles` | `L816–L822` | `StaticFiles` | — | 1 |


**Methods in `EventBroadcaster`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L107–L108` | `(self...)` | — | — | `set` |
| `subscribe` | `L110–L113` | `(self...)` | `asyncio.Queue` | — | `Queue`, `add` |
| `unsubscribe` | `L115–L116` | `(self, queue: asyncio.Queue...)` | — | — | `discard` |
| `publish` | `L118–L123` | `(self, event_type: str, data: dict...)` | — | — | `list`, `put_nowait` |


**Methods in `DevStaticFiles`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `get_response` | `L817–L822` | `(self, path: str, scope...)` | — | — | `get_response`, `super` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `create_app` | `L126–L836` | `(settings: Settings | None=None, dat...)` | `FastAPI` | — | `AutoTrader`, `DSEMarketScheduler`, `Database`, `DevStaticFiles` |
| `lifespan` | `L135–L186` | `(_app: FastAPI...)` | — | — | `TelegramBotDaemon`, `_heartbeat_worker`, `cancel`, `close` |
| `_heartbeat_worker` | `L150–L160` | `(...)` | — | — | `check_dead_man_switch`, `debug`, `record_system_heartbeat`, `send_daily_summary_if_due` |
| `validation_exception_handler` | `L201–L212` | `(_req: Request, exc: RequestValidati...)` | — | — | `JSONResponse`, `append`, `errors`, `exception_handler` |
| `http_exception_handler` | `L215–L235` | `(_req: Request, exc: StarletteHTTPEx...)` | — | — | `JSONResponse`, `exception_handler`, `get`, `getattr` |
| `unhandled_exception_handler` | `L238–L243` | `(_req: Request, exc: Exception...)` | — | — | `JSONResponse`, `exception`, `exception_handler`, `str` |
| `local_security` | `L246–L310` | `(request: Request, call_next...)` | — | — | `JSONResponse`, `call_next`, `compare_digest`, `encode` |
| `health` | `L313–L345` | `(...)` | — | — | `AsyncClient`, `bool`, `get`, `get_status` |
| `portfolio` | `L348–L349` | `(...)` | — | — | `build_snapshot`, `get` |
| `cycle` | `L352–L389` | `(idempotency_key: Annotated[UUID | N...)` | — | — | `HTTPException`, `Header`, `build_snapshot`, `extract_quotes_from_stocknow` |
| `quick_kill` | `L392–L424` | `(body: KillRequest | None=None...)` | — | — | `DecisionLog`, `add`, `build_snapshot`, `create_checkpoint` |
| `automation_handoff` | `L427–L481` | `(body: HandoffRequest...)` | — | — | `HTTPException`, `acquire_trading_lock`, `are_caps_set`, `build_snapshot` |
| `pause` | `L484–L491` | `(body: PauseRequest...)` | — | — | `portfolio_state`, `post`, `publish`, `write` |
| `automation_config` | `L494–L582` | `(body: AutomationConfigRequest...)` | — | — | `HTTPException`, `StockNowAdapter`, `_bg_onscreen_attach`, `are_caps_set` |
| `_bg_onscreen_attach` | `L549–L561` | `(...)` | — | — | `ensure_authenticated`, `extract_quotes_from_stocknow`, `getattr`, `launch` |
| `reset_circuit_breaker_endpoint` | `L585–L587` | `(...)` | — | — | `post`, `reset_circuit_breaker` |
| `get_circuit_breaker_status` | `L590–L599` | `(...)` | — | — | `bool`, `get`, `getattr`, `int` |
| `run_preflight_endpoint` | `L602–L604` | `(...)` | — | — | `post`, `run_cockpit_preflight` |
| `get_preflight_status` | `L607–L612` | `(...)` | — | — | `are_caps_set`, `get`, `has_passing_preflight_within_24h` |
| `get_caps_public` | `L615–L644` | `(...)` | — | — | `Decimal`, `abs`, `all`, `bool` |
| `set_caps_public` | `L647–L732` | `(body: CapsUpdateRequest...)` | — | — | `Decimal`, `HTTPException`, `KernelAuditLog`, `add` |
| `advance` | `L735–L746` | `(body: AdvanceRequest...)` | — | — | `Decimal`, `advance_demo`, `build_market_map_payload`, `get` |
| `market_map_endpoint` | `L749–L750` | `(...)` | — | — | `build_market_map_payload`, `get` |
| `allocation` | `L753–L776` | `(symbol: str, body: AllocationReques...)` | — | — | `HTTPException`, `RuleAudit`, `add`, `get` |
| `event_stream` | `L789–L814` | `(request: Request...)` | — | — | `StreamingResponse`, `generator`, `get`, `subscribe` |
| `generator` | `L792–L804` | `(...)` | — | — | `dumps`, `get`, `is_disconnected`, `unsubscribe` |
| `cockpit` | `L825–L833` | `(...)` | — | — | `FileResponse`, `get` |


---

### 📄 [`backend/market_map.py`](/backend/market_map.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `build_market_map_payload` | `L208–L279` | `(scenario_bias: Decimal=Decimal('0')...)` | `dict[str, Any]` | Builds hierarchical treemap data and sector gainer stats for the visualizer. | `Decimal`, `append`, `float`, `items` |


---

### 📄 [`backend/portfolio.py`](/backend/portfolio.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `generate_extended_history` | `L238–L290` | `(history: list[dict[str, str]], fund...)` | `dict[str, list[dict[str, Any]]]` | Generates 7d, 1m, 6m, 1y series for TradingView-style deep trend views. | `add_sessions`, `append`, `cos`, `float` |
| `rule_view` | `L293–L303` | `(rule: CustomRule...)` | `dict` | — | `decimal`, `float` |
| `trade_view` | `L306–L335` | `(trade: TradeLog...)` | `dict` | — | `float`, `getattr`, `isoformat` |
| `period_totals` | `L338–L353` | `(trades: list[TradeLog], start: date...)` | `dict` | — | `float`, `isoformat`, `len`, `sum` |
| `build_snapshot` | `L356–L358` | `(database: Database, settings: Setti...)` | `dict` | — | `read`, `snapshot_from_session` |
| `snapshot_from_session` | `L361–L734` | `(session: Session, settings: Setting...)` | `dict` | — | `Decimal`, `StockNowAdapter`, `TradingCalendar`, `abs` |
| `normalized_watchlist` | `L737–L756` | `(companies: list[dict]...)` | `list[dict]` | Equal-weight normalized PRICE index, explicitly not portfolio performance. | `any`, `append`, `decimal`, `float` |


---

### 📄 [`backend/routes_auth_settings.py`](/backend/routes_auth_settings.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `LoginRequest` | `L21–L24` | `BaseModel` | — | 0 |
| `KeysSettingsRequest` | `L27–L33` | `BaseModel` | — | 0 |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `build_auth_settings_router` | `L40–L173` | `(database: Database, settings: Setti...)` | `APIRouter` | — | `APIRouter` |
| `login` | `L44–L58` | `(body: LoginRequest...)` | — | — | `HTTPException`, `add`, `post`, `uuid4` |
| `logout` | `L61–L65` | `(request: Request...)` | — | — | `discard`, `get`, `post`, `replace` |
| `auth_session` | `L68–L80` | `(request: Request...)` | — | — | `bool`, `get`, `replace`, `strip` |
| `get_api_keys` | `L83–L122` | `(...)` | — | — | `bool`, `get`, `getattr`, `getenv` |
| `mask_single` | `L84–L89` | `(s: str...)` | `str` | — | `len` |
| `mask` | `L91–L97` | `(s: str...)` | `str` | — | `join`, `len`, `mask_single`, `replace` |
| `update_api_keys` | `L125–L171` | `(body: KeysSettingsRequest...)` | — | — | `__setattr__`, `append`, `create_checkpoint`, `join` |


---

### 📄 [`backend/routes_hermes.py`](/backend/routes_hermes.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `CreateThreadRequest` | `L20–L22` | `BaseModel` | — | 0 |
| `SwitchModelRequest` | `L25–L28` | `BaseModel` | — | 0 |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `build_hermes_router` | `L99–L273` | `(database: Database, settings: Setti...)` | `APIRouter` | — | `APIRouter` |
| `list_conversations` | `L103–L105` | `(...)` | — | Returns conversation topics. | `get` |
| `create_conversation` | `L108–L116` | `(body: CreateThreadRequest...)` | — | Creates a local conversation topic stub. | `post` |
| `conversation_messages` | `L119–L121` | `(conversation_id: str...)` | — | Returns messages for a conversation topic. | `get` |
| `system_changes` | `L124–L196` | `(...)` | — | Returns git diff summary and recent kernel checkpoints. | `Path`, `append`, `desc`, `get` |
| `get_hermes_models` | `L199–L210` | `(...)` | — | Returns available models, active model, and provider from Hermes state. | `get`, `read_hermes_state` |
| `switch_hermes_model` | `L213–L271` | `(body: SwitchModelRequest...)` | — | Switches active model and provider in Hermes profile and updates local state. | `create_checkpoint`, `exists`, `flush`, `get_hermes_cmd` |


---

### 📄 [`backend/routes_stocknow.py`](/backend/routes_stocknow.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `StockNowSessionActionRequest` | `L36–L39` | `BaseModel` | — | 0 |
| `StockNowMarketSyncRequest` | `L42–L44` | `BaseModel` | — | 0 |
| `StockNowPortfolioSyncRequest` | `L47–L49` | `BaseModel` | — | 0 |
| `StockNowExecuteOrderRequest` | `L52–L71` | `BaseModel` | — | 1 |
| `StockNowSchedulerActionRequest` | `L74–L77` | `BaseModel` | — | 0 |


**Methods in `StockNowExecuteOrderRequest`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `handle_confirm_alias` | `L67–L71` | `(cls, data: Any...)` | `Any` | — | `bool`, `get`, `isinstance`, `model_validator` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `build_stocknow_router` | `L80–L302` | `(database: Database, settings: Setti...)` | `APIRouter` | — | `APIRouter`, `DSEMarketScheduler`, `StockNowLiveClient`, `get_active_scheduler` |
| `get_stocknow_status` | `L99–L100` | `(...)` | — | — | `get`, `get_status` |
| `get_stocknow_page` | `L103–L114` | `(...)` | — | — | `_get_info`, `_run_in_proactor`, `get`, `getattr` |
| `_get_info` | `L106–L111` | `(...)` | — | — | `evaluate`, `getattr`, `hasattr`, `title` |
| `post_stocknow_session` | `L117–L173` | `(body: StockNowSessionActionRequest...)` | — | — | `HTTPException`, `_background_auth`, `close`, `create_task` |
| `_background_auth` | `L134–L141` | `(...)` | — | — | `ensure_authenticated`, `get_status`, `publish`, `warning` |
| `post_stocknow_sync_market` | `L176–L188` | `(body: StockNowMarketSyncRequest | N...)` | — | — | `build_snapshot`, `extract_quotes_from_stocknow`, `fetch_stocknow_live_market_data`, `post` |
| `get_all_dse_shares` | `L191–L193` | `(...)` | — | Returns the full 470+ DSE shares catalog with live LTP, +/- %, and sparkline curves. | `get`, `get_or_fetch_all_dse_shares` |
| `get_stocknow_symbol_history` | `L196–L209` | `(symbol: str...)` | — | Returns real 400-candle daily history for any DSE company directly from StockNow. | `AsyncClient`, `HTTPException`, `get`, `json` |
| `post_stocknow_sync_portfolio` | `L212–L247` | `(body: StockNowPortfolioSyncRequest ...)` | — | — | `HTTPException`, `build_snapshot`, `error`, `extract_hummingbird_portfolio` |
| `post_stocknow_execute_order` | `L250–L285` | `(body: StockNowExecuteOrderRequest, ...)` | — | — | `OrderRequest`, `build_snapshot`, `get`, `post` |
| `get_stocknow_scheduler` | `L288–L289` | `(...)` | — | — | `get`, `get_status` |
| `post_stocknow_scheduler` | `L292–L300` | `(body: StockNowSchedulerActionReques...)` | — | — | `HTTPException`, `post`, `run_scheduled_tick`, `start` |


---

### 📄 [`backend/routes_tradexpress.py`](/backend/routes_tradexpress.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `BridgeControlRequest` | `L29–L31` | `BaseModel` | — | 0 |
| `ShadowOrderRequest` | `L34–L45` | `BaseModel` | — | 0 |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `build_tradexpress_router` | `L48–L226` | `(database: Database, settings: Setti...)` | `APIRouter` | — | `APIRouter` |
| `get_tradexpress_status` | `L56–L88` | `(...)` | — | Returns passive feed connection status, tab freshness, and operator guidance. | `bool`, `float`, `get`, `get_account_summary` |
| `post_bridge_control` | `L91–L108` | `(req: BridgeControlRequest...)` | — | Controls passive CDP spy daemon: attach, detach, or status. | `HTTPException`, `get_global_passive_daemon`, `get_status`, `lower` |
| `post_passive_ingest` | `L111–L139` | `(payload: dict[str, Any], request: R...)` | — | Ingests passively sniffed WebSocket / DOM snapshot and reconciles order queue. | `TradeXpressShadowSimulator`, `build_snapshot`, `debug`, `get` |
| `list_orders` | `L142–L149` | `(status: str | None=None, portfolio_...)` | — | Lists simulated shadow orders mirroring TradeXpress Order List. | `TradeXpressShadowSimulator`, `get`, `get_orders` |
| `submit_shadow_order` | `L152–L167` | `(req: ShadowOrderRequest...)` | — | Submits 2-step limit order into shadow simulator (confirm=False preview, True commit). | `TradeXpressShadowSimulator`, `decimal`, `post`, `submit_shadow_order` |
| `cancel_shadow_order` | `L170–L176` | `(order_ref: str...)` | — | Cancels a resting QUEUED shadow order. | `HTTPException`, `TradeXpressShadowSimulator`, `cancel_order`, `get` |
| `get_learning_logs` | `L179–L224` | `(tier: str | None=None, limit: int=5...)` | — | Returns recent TradeLearningLog records and aggregated win-rate telemetry. | `desc`, `float`, `get`, `in_` |


---

### 📄 [`backend/secret_guard.py`](/backend/secret_guard.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `SecurityViolation` | `L14–L16` | `PermissionError` | Raised when an operation attempts to inspect sensitive credentials or isolated files. | 0 |
| `SecretGuard` | `L40–L63` | `object` | — | 2 |


**Methods in `SecretGuard`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `assert_safe_path` | `L42–L50` | `(target: str | Path...)` | `Path` | — | `Path`, `SecurityViolation`, `replace`, `resolve` |
| `redact_secrets` | `L53–L63` | `(text: str, custom_tokens: list[str]...)` | `str` | — | `len`, `replace`, `str`, `sub` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `redact_secrets` | `L66–L67` | `(text: str, custom_tokens: list[str]...)` | `str` | — | `redact_secrets` |


---

### 📄 [`backend/seed.py`](/backend/seed.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `seed_demo` | `L35–L139` | `(session: Session, settings: Setting...)` | `None` | — | `CompanyProfile`, `CustomRule`, `Decimal`, `PortfolioState` |
| `migrate_real_stocknow_market` | `L159–L306` | `(session: Session, settings: Setting...)` | `None` | Migrates existing SQLite database on boot to real StockNow #164580 portfolio and watchlist. | `CompanyProfile`, `CustomRule`, `Decimal`, `TaxLot` |


---

### 📄 [`plugins/humming_bird/__init__.py`](/plugins/humming_bird/__init__.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `register` | `L89–L127` | `(ctx...)` | `None` | Register Humming Bird trading kernel tools and lifecycle hooks with Hermes. | `Path`, `exists`, `get`, `is_file` |


---

### 📄 [`plugins/humming_bird/hooks.py`](/plugins/humming_bird/hooks.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `check_dse_trading_hours` | `L13–L41` | `(dt: datetime | None=None...)` | `tuple[bool, str]` | Check if time falls within DSE trading hours (Sun-Thu 10:00 to 14:10 Asia/Dhaka). | `ZoneInfo`, `astimezone`, `now`, `replace` |
| `on_pre_tool_call` | `L44–L92` | `(tool_name: str, args: dict[str, Any...)` | `dict[str, Any] | None` | Pre-tool-call lifecycle hook. | `_kernel_get`, `check_dse_trading_hours`, `get`, `getenv` |


---

### 📄 [`plugins/humming_bird/schemas.py`](/plugins/humming_bird/schemas.py)

---

### 📄 [`plugins/humming_bird/tools.py`](/plugins/humming_bird/tools.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `_kernel_get` | `L17–L50` | `(endpoint: str, params: dict[str, An...)` | `str` | Perform authenticated GET request to local Humming Bird kernel API. | `Request`, `decode`, `dumps`, `get` |
| `_kernel_post` | `L53–L85` | `(endpoint: str, data: dict[str, Any]...)` | `str` | Perform authenticated POST request to local Humming Bird kernel API. | `Request`, `decode`, `dumps`, `encode` |
| `hb_portfolio` | `L90–L124` | `(args: dict[str, Any] | None=None, *...)` | `str` | Fetch current portfolio state from kernel API. | `_kernel_get`, `append`, `dumps`, `get` |
| `hb_watchlist` | `L127–L133` | `(args: dict[str, Any] | None=None, *...)` | `str` | Fetch watchlist filtered optionally by tier from kernel API. | `_kernel_get`, `dict`, `get`, `update` |
| `hb_inspect_curve` | `L136–L144` | `(args: dict[str, Any] | None=None, *...)` | `str` | Inspect price curve and support/resistance analysis for a symbol. | `_kernel_get`, `dict`, `dumps`, `get` |
| `hb_market_open` | `L147–L149` | `(args: dict[str, Any] | None=None, *...)` | `str` | Check if DSE market is currently open. | `_kernel_get` |
| `hb_canaries` | `L152–L154` | `(args: dict[str, Any] | None=None, *...)` | `str` | Retrieve active canary theses from kernel API. | `_kernel_get` |
| `hb_lots` | `L157–L163` | `(args: dict[str, Any] | None=None, *...)` | `str` | Fetch tax lots and T+2 maturity status. | `_kernel_get`, `dict`, `get`, `str` |
| `hb_set_tier` | `L168–L179` | `(args: dict[str, Any] | None=None, *...)` | `str` | Set watchlist tier for a company. | `_kernel_post`, `dict`, `dumps`, `get` |
| `hb_set_allocation` | `L182–L205` | `(args: dict[str, Any] | None=None, *...)` | `str` | Set buy allocation percentage for a symbol. | `_kernel_post`, `bool`, `dict`, `dumps` |
| `hb_quarantine_canary` | `L208–L221` | `(args: dict[str, Any] | None=None, *...)` | `str` | Trigger emergency crash quarantine (90% liquidation, 10% canary probe). | `_kernel_post`, `dict`, `dumps`, `get` |
| `hb_restore_quarantine` | `L224–L237` | `(args: dict[str, Any] | None=None, *...)` | `str` | Restore a company from crash quarantine back into active status. | `_kernel_post`, `dict`, `dumps`, `get` |
| `hb_sync` | `L240–L248` | `(args: dict[str, Any] | None=None, *...)` | `str` | Trigger sync with StockNow market data. | `_kernel_post`, `dict`, `dumps`, `get` |
| `_get_allowed_portfolios` | `L251–L254` | `(...)` | `tuple[str, ...]` | — | `getenv`, `strip` |
| `hb_place_order` | `L257–L336` | `(args: dict[str, Any] | None=None, *...)` | `str` | Submit virtual BUY or SELL order enforcing constraints and authorization. | `_get_allowed_portfolios`, `_kernel_post`, `bool`, `dict` |
| `hb_rollback_last` | `L339–L341` | `(args: dict[str, Any] | None=None, *...)` | `str` | Roll back the last state checkpoint atomically. | `_kernel_post` |
| `hb_automation_get` | `L344–L346` | `(args: dict[str, Any] | None=None, *...)` | `str` | Fetch current automation settings from the trading kernel. | `_kernel_get` |
| `hb_automation_set` | `L349–L378` | `(args: dict[str, Any] | None=None, *...)` | `str` | Configure trading automation switches, ingestion mode, or polling cadence. | `_kernel_post`, `dict`, `dumps`, `int` |
| `hb_scheduler` | `L381–L390` | `(args: dict[str, Any] | None=None, *...)` | `str` | Control or inspect the market scheduler background loop. | `_kernel_post`, `dict`, `dumps`, `get` |
| `hb_run_cycle` | `L393–L406` | `(args: dict[str, Any] | None=None, *...)` | `str` | Trigger an immediate AutoTrader cycle. | `_kernel_post`, `dict`, `get`, `isinstance` |
| `hb_stocknow_session` | `L409–L422` | `(args: dict[str, Any] | None=None, *...)` | `str` | Manage live Playwright session for StockNow integration. | `_kernel_post`, `dict`, `dumps`, `get` |
| `hb_mode_get` | `L425–L427` | `(args: dict[str, Any] | None=None, *...)` | `str` | Get active trading mode from kernel. | `_kernel_get` |
| `hb_mode_set` | `L430–L446` | `(args: dict[str, Any] | None=None, *...)` | `str` | Set trading mode in kernel (TEST_OFFHOURS or LIVE_HOURS). | `_kernel_post`, `bool`, `dict`, `dumps` |
| `hb_caps_get` | `L449–L451` | `(args: dict[str, Any] | None=None, *...)` | `str` | Get active risk caps and daily limits from kernel. | `_kernel_get` |
| `hb_caps_set` | `L454–L491` | `(args: dict[str, Any] | None=None, *...)` | `str` | Set or lower risk limits in kernel. Raising a limit requires confirm=true. | `_kernel_post`, `bool`, `dict`, `dumps` |
| `hb_feed_status` | `L494–L496` | `(args: dict[str, Any] | None=None, *...)` | `str` | Check TradeXpress passive feed freshness and get step-by-step operator tab guidance. | `_kernel_get` |
| `hb_learning_review` | `L499–L511` | `(args: dict[str, Any] | None=None, *...)` | `str` | Review trade learning logs, win rates by tier (L1 vs L2), slippage, and post-market reflection metrics. | `_kernel_get`, `dict`, `int`, `str` |


---

### 📄 [`scripts/backup_db.py`](/scripts/backup_db.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `get_default_db_path` | `L20–L22` | `(...)` | `Path` | Returns absolute path to hummingbird.db. | — |
| `get_default_backup_dir` | `L25–L27` | `(...)` | `Path` | Returns absolute path to backups directory. | — |
| `backup_database` | `L30–L82` | `(db_path: Path | None=None, backup_d...)` | `Path` | Creates a verified timestamped backup of the SQLite database. | `FileNotFoundError`, `RuntimeError`, `backup`, `close` |
| `prune_backups` | `L85–L116` | `(backup_dir: Path | None=None, keep_...)` | `list[Path]` | Prunes older hummingbird_*.db backups in backup_dir, keeping the newest keep_count. | `append`, `exists`, `get_default_backup_dir`, `glob` |
| `main` | `L119–L134` | `(...)` | `int` | — | `ArgumentParser`, `add_argument`, `backup_database`, `parse_args` |


---

### 📄 [`scripts/check_dse_market_open.py`](/scripts/check_dse_market_open.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `check_kernel_market_open` | `L24–L42` | `(...)` | `tuple[bool, str]` | Attempts to verify market status via local kernel API if reachable. | `Request`, `add_header`, `bool`, `decode` |
| `is_dse_time_open` | `L45–L60` | `(now: datetime...)` | `tuple[bool, str]` | Pure calendar and hours check against Dhaka time. | `strftime`, `strptime`, `time`, `weekday` |
| `main` | `L63–L85` | `(...)` | — | — | `check_kernel_market_open`, `dumps`, `exit`, `is_dse_time_open` |


---

### 📄 [`scripts/check_heartbeat.py`](/scripts/check_heartbeat.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `main` | `L22–L41` | `(...)` | `None` | — | `ArgumentParser`, `Database`, `Settings`, `add_argument` |


---

### 📄 [`scripts/generate_code_map.py`](/scripts/generate_code_map.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `AstVisitor` | `L216–L311` | `ast.NodeVisitor` | — | 9 |


**Methods in `AstVisitor`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L217–L224` | `(self, filepath: Path, code_lines: l...)` | — | — | — |
| `visit_Import` | `L226–L229` | `(self, node: ast.Import...)` | — | — | `append`, `generic_visit` |
| `visit_ImportFrom` | `L231–L235` | `(self, node: ast.ImportFrom...)` | — | — | `append`, `generic_visit` |
| `visit_ClassDef` | `L237–L252` | `(self, node: ast.ClassDef...)` | — | — | `append`, `generic_visit`, `get_docstring`, `getattr` |
| `visit_FunctionDef` | `L254–L255` | `(self, node: ast.FunctionDef...)` | — | — | `_record_func` |
| `visit_AsyncFunctionDef` | `L257–L258` | `(self, node: ast.AsyncFunctionDef...)` | — | — | `_record_func` |
| `_record_func` | `L260–L287` | `(self, node: ast.FunctionDef | ast.A...)` | — | — | `_compute_depth`, `append`, `generic_visit`, `get_docstring` |
| `visit_Call` | `L289–L298` | `(self, node: ast.Call...)` | — | — | `add`, `generic_visit`, `isinstance` |
| `_compute_depth` | `L300–L311` | `(self, node: ast.AST, current_depth:...)` | `int` | — | `_compute_depth`, `isinstance`, `iter_child_nodes` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `is_excluded` | `L80–L112` | `(path: Path | str, repo_root: Path=R...)` | `bool` | Check if a path should be excluded based on directory rules. | `Path`, `as_posix`, `is_absolute`, `len` |
| `get_pinned_vendor_commit` | `L115–L145` | `(repo_root: Path=REPO_ROOT...)` | `str` | Retrieve pinned submodule commit for vendor/hermes-agent from git. | `len`, `run`, `str`, `strip` |
| `discover_files` | `L148–L184` | `(repo_root: Path=REPO_ROOT...)` | `list[Path]` | Discover files using git ls-files + untracked non-ignored files, | `Path`, `append`, `is_excluded`, `is_file` |
| `collect_file_metrics` | `L187–L213` | `(discovered_files: list[Path], repo_...)` | — | Collect file counts and LOC grouped by extension, grouping long-tail as 'other'. | `append`, `defaultdict`, `is_file`, `len` |
| `parse_python_files` | `L314–L332` | `(discovered_files: list[Path], repo_...)` | `dict[str, AstVisitor]` | Parse all discovered Python files in backend/, plugins/, scripts/ using AST. | `AstVisitor`, `as_posix`, `lower`, `parse` |
| `parse_fastapi_routes` | `L335–L373` | `(router_paths: list[Path], repo_root...)` | — | Parse route handlers from FastAPI router modules. | `append`, `as_posix`, `exists`, `get_docstring` |
| `parse_css_design` | `L376–L486` | `(styles_file: Path, light_file: Path...)` | — | — | `append`, `exists`, `get`, `group` |
| `scan_file` | `L432–L481` | `(css_text: str, filename: str...)` | — | — | `any`, `append`, `escape`, `get` |
| `parse_frontend` | `L489–L580` | `(repo_root: Path=REPO_ROOT...)` | — | Index frontend HTML IDs, JS functions, API invocations, and CSS stylesheets. | `add`, `any`, `append`, `compile` |
| `parse_frontend_dom_audit` | `L583–L613` | `(repo_root: Path=REPO_ROOT...)` | `dict[str, Any]` | Audit JS DOM bindings against index.html IDs to detect orphan queries. | `add`, `exists`, `findall`, `finditer` |
| `parse_plugin_tools` | `L616–L651` | `(repo_root: Path=REPO_ROOT...)` | `list[dict[str, Any]]` | Parse tools registered in plugins/humming_bird/tools.py using AST. | `append`, `exists`, `get_docstring`, `getattr` |
| `generate_ascii_tree` | `L654–L679` | `(discovered_files: list[Path], repo_...)` | `str` | Generate a clean ASCII directory tree from discovered files. | `_format`, `join`, `relative_to`, `setdefault` |
| `_format` | `L666–L676` | `(d: dict[str, Any], prefix: str=''...)` | — | — | `_format`, `append`, `enumerate`, `keys` |
| `compute_blast_radius` | `L682–L711` | `(parsed_py: dict[str, AstVisitor]...)` | `dict[str, dict[str, Any]]` | Compute reverse dependencies and blast-radius risk levels for each module. | `add`, `items`, `len`, `list` |
| `parse_sqlalchemy_schema` | `L714–L757` | `(repo_root: Path=REPO_ROOT...)` | `list[dict[str, Any]]` | Parse SQLAlchemy ORM entities in backend/database.py. | `append`, `exists`, `get_docstring`, `getattr` |
| `parse_pydantic_contracts` | `L760–L794` | `(discovered_files: list[Path], repo_...)` | `list[dict[str, Any]]` | Parse all Pydantic models across backend/ and plugins/. | `any`, `append`, `as_posix`, `endswith` |
| `parse_hermes_skills_graph` | `L797–L851` | `(repo_root: Path=REPO_ROOT...)` | `list[dict[str, Any]]` | Map Hermes tools in plugins/humming_bird/tools.py to kernel routes and procedural skills. | `append`, `exists`, `get`, `get_docstring` |
| `parse_environment_registry` | `L854–L872` | `(repo_root: Path=REPO_ROOT...)` | `list[dict[str, str]]` | Extract environment variables and configuration properties across the repository. | — |
| `generate_markdown` | `L875–L1160` | `(repo_root: Path=REPO_ROOT, output_f...)` | — | — | `append`, `collect_file_metrics`, `compute_blast_radius`, `discover_files` |


---

### 📄 [`scripts/inspect_tradexpress_passive.py`](/scripts/inspect_tradexpress_passive.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `run_passive_probe` | `L29–L292` | `(cdp_url: str, duration: int, output...)` | `dict` | Connect to existing browser over CDP and passively sniff TradeXpress. | `ZoneInfo`, `append`, `async_playwright`, `connect_over_cdp` |
| `on_web_socket` | `L83–L107` | `(ws...)` | — | — | `on`, `redact_secrets` |
| `on_frame_received` | `L86–L105` | `(payload...)` | — | — | `ZoneInfo`, `append`, `b64encode`, `decode` |
| `on_cdp_ws_frame` | `L116–L133` | `(params: dict...)` | — | — | `ZoneInfo`, `append`, `get`, `isoformat` |
| `main` | `L295–L318` | `(...)` | — | — | `ArgumentParser`, `Path`, `add_argument`, `parse_args` |


---

### 📄 [`scripts/preflight.py`](/scripts/preflight.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `CheckResult` | `L41–L44` | `NamedTuple` | — | 0 |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `check_gateway` | `L47–L64` | `(url: str='http://127.0.0.1:8642'...)` | `CheckResult` | Verifies Hermes Gateway HTTP service on port 8642. | `CheckResult`, `Request`, `get`, `rstrip` |
| `check_model_and_fallback` | `L67–L92` | `(...)` | `CheckResult` | Verifies primary inference model and fallback chain in Hermes configuration. | `CheckResult`, `get`, `join`, `read_hermes_state` |
| `check_plugin_tools` | `L95–L124` | `(...)` | `CheckResult` | Verifies humming_bird plugin registration and expected tool count. | `CheckResult`, `exists`, `get`, `get_hermes_dir` |
| `check_kernel_token` | `L127–L146` | `(...)` | `CheckResult` | Verifies KERNEL_TOKEN authorization configuration. | `CheckResult`, `exists`, `get`, `len` |
| `check_stocknow_session` | `L149–L217` | `(db: Database...)` | `CheckResult` | Verifies StockNow session state, credentials, and profile binding. | `CheckResult`, `Request`, `bool`, `close` |
| `check_portfolio_drift` | `L220–L253` | `(db: Database...)` | `CheckResult` | Verifies that book assets match initial capital with exact 0.00 paisa drift. | `CheckResult`, `Decimal`, `abs`, `assert_ledger` |
| `check_trading_mode` | `L256–L278` | `(db: Database...)` | `CheckResult` | Verifies trading mode configuration. | `CheckResult`, `get`, `getattr`, `read` |
| `check_caps_set` | `L281–L310` | `(db: Database...)` | `CheckResult` | Verifies kernel risk caps and kill switch configuration. | `CheckResult`, `get`, `read` |
| `check_automation_state` | `L313–L329` | `(db: Database...)` | `CheckResult` | Verifies master automation switch, ingestion mode, and scheduler settings. | `CheckResult`, `get`, `read` |
| `check_and_create_db_backup` | `L332–L343` | `(db_path: Path...)` | `CheckResult` | Takes a fresh verified backup of hummingbird.db and confirms backup integrity. | `CheckResult`, `backup_database`, `stat` |
| `check_test_portfolio_configured` | `L346–L358` | `(...)` | `CheckResult` | Verifies that test portfolio is configured and distinct from live portfolio. | `CheckResult`, `test_portfolio_configured` |
| `run_preflight` | `L361–L416` | `(verbose: bool=False...)` | `tuple[list[CheckResult], bool]` | Runs all preflight checks and returns (results, all_passed). | `Database`, `Settings`, `all`, `check_and_create_db_backup` |
| `print_table` | `L419–L444` | `(checks: list[CheckResult], all_pass...)` | `None` | Formats and prints GO / NO-GO table. | `enumerate`, `len`, `print`, `sum` |
| `main` | `L447–L455` | `(...)` | `int` | — | `ArgumentParser`, `add_argument`, `parse_args`, `print_table` |


---

### 📄 [`scripts/restore_db.py`](/scripts/restore_db.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `find_latest_backup` | `L21–L31` | `(backup_dir: Path | None=None...)` | `Path` | Finds the most recent hummingbird_*.db backup file. | `FileNotFoundError`, `exists`, `get_default_backup_dir`, `glob` |
| `restore_database` | `L34–L121` | `(backup_file: Path | str | None=None...)` | `Path` | Restores database from specified or latest backup file. | `FileNotFoundError`, `Path`, `RuntimeError`, `backup` |
| `main` | `L124–L144` | `(...)` | `int` | — | `ArgumentParser`, `add_argument`, `get_default_db_path`, `parse_args` |


---

### 📄 [`scripts/verify_chat_card.py`](/scripts/verify_chat_card.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `main` | `L8–L128` | `(...)` | — | — | `async_playwright`, `click`, `close`, `evaluate` |


---

### 📄 [`scripts/verify_step10_ui.py`](/scripts/verify_step10_ui.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `run` | `L9–L44` | `(...)` | — | — | `async_playwright`, `close`, `count`, `goto` |


---

## 4. Full SQLAlchemy Database Schema X-Ray (`backend/database.py`)

SQLAlchemy ORM Entities backing the deterministic ledger and state store:


### Table `portfolio_state` (Model `PortfolioState`)

- **File & Lines:** [`backend/database.py#L42`](/backend/database.py#L42-L71)
- **Purpose:** Managed transactional state

| Column Name | ORM Mapped Type | Constraints / Defaults / SQL Type |
| :--- | :--- | :--- |
| `id` | `Mapped[int]` | primary_key=True, default=1 |
| `name` | `Mapped[str]` | String(80), default='Humming Bird' |
| `mode` | `Mapped[str]` | String(16), default='DEMO' |
| `initial_capital` | `Mapped[Decimal]` | MONEY |
| `clock_date` | `Mapped[date]` | Date |
| `revision` | `Mapped[int]` | Integer, default=1 |
| `rules_revision` | `Mapped[int]` | Integer, default=1 |
| `paused` | `Mapped[bool]` | Boolean, default=False |
| `automation_enabled` | `Mapped[bool]` | Boolean, default=True |
| `ingestion_mode` | `Mapped[str]` | String(32), default='BACKGROUND_POLLING' |
| `polling_interval_sec` | `Mapped[int]` | Integer, default=120 |
| `active_model` | `Mapped[str]` | String(64), default='xiaomi/mimo-v2-flash' |
| `trading_mode` | `Mapped[str]` | String(32), default='LIVE_HOURS' |
| `max_order_bdt` | `Mapped[Decimal | None]` | MONEY, nullable=True, default=Decimal('20000.00') |
| `max_symbol_bdt` | `Mapped[Decimal | None]` | MONEY, nullable=True, default=Decimal('50000.00') |
| `daily_budget_bdt` | `Mapped[Decimal]` | MONEY, default=Decimal('4000.00') |
| `max_orders_per_day` | `Mapped[int]` | Integer, default=20 |
| `kill_switch_active` | `Mapped[bool]` | Boolean, default=False |
| `consecutive_failure_count` | `Mapped[int]` | Integer, default=0 |
| `circuit_breaker_tripped` | `Mapped[bool]` | Boolean, default=False |
| `circuit_breaker_reason` | `Mapped[str | None]` | String(255), nullable=True, default=None |
| `startup_health_passed` | `Mapped[bool]` | Boolean, default=True |
| `startup_health_status` | `Mapped[str]` | String(32), default='READY' |
| `calendar_holidays` | `Mapped[list[str]]` | JSON, default=list |
| `bucket_anchor` | `Mapped[date]` | Date |
| `execution_venue` | `Mapped[str]` | String(32), default='SHADOW_DUMMY' |
| `unsettled_sales_bdt` | `Mapped[Decimal]` | MONEY, default=Decimal('0.00') |
| `created_at` | `Mapped[str]` | String(40), default=utc_now_iso |


### Table `company_profiles` (Model `CompanyProfile`)

- **File & Lines:** [`backend/database.py#L74`](/backend/database.py#L74-L98)
- **Purpose:** Managed transactional state

| Column Name | ORM Mapped Type | Constraints / Defaults / SQL Type |
| :--- | :--- | :--- |
| `symbol` | `Mapped[str]` | String(32), primary_key=True |
| `name` | `Mapped[str]` | String(100) |
| `sector` | `Mapped[str]` | String(32) |
| `favorite` | `Mapped[bool]` | Boolean, default=True |
| `settlement_days` | `Mapped[int]` | Integer, default=2 |
| `last_price` | `Mapped[Decimal]` | PRICE |
| `price_history` | `Mapped[list[dict[str, str]]]` | JSON |
| `quote_on` | `Mapped[date]` | Date |
| `source` | `Mapped[str]` | String(32), default='DEMO_SEED' |
| `watchlist_category` | `Mapped[str]` | String(32), default='GSC' |
| `quarantined` | `Mapped[bool]` | Boolean, default=False |
| `quarantine_reason` | `Mapped[str]` | String(500), default='' |
| `bid` | `Mapped[Decimal]` | PRICE, default=Decimal('0.0') |
| `bid_qty` | `Mapped[int]` | Integer, default=0 |
| `offer` | `Mapped[Decimal]` | PRICE, default=Decimal('0.0') |
| `offer_qty` | `Mapped[int]` | Integer, default=0 |
| `min_limit` | `Mapped[Decimal | None]` | PRICE, nullable=True, default=None |
| `max_limit` | `Mapped[Decimal | None]` | PRICE, nullable=True, default=None |
| `settlement_type` | `Mapped[str]` | String(16), default='PUBLIC' |
| `symbol_category` | `Mapped[str]` | String(8), default='A' |
| `hit_52w_high` | `Mapped[bool]` | Boolean, default=False |
| `hit_upper_circuit` | `Mapped[bool]` | Boolean, default=False |
| `last_trade_time` | `Mapped[str]` | String(32), default='' |


### Table `custom_rules` (Model `CustomRule`)

- **File & Lines:** [`backend/database.py#L101`](/backend/database.py#L101-L112)
- **Purpose:** Managed transactional state

| Column Name | ORM Mapped Type | Constraints / Defaults / SQL Type |
| :--- | :--- | :--- |
| `symbol` | `Mapped[str]` | ForeignKey('company_profiles.symbol'), primary_key=True |
| `enabled` | `Mapped[bool]` | Boolean, default=True |
| `buy_allocation_pct` | `Mapped[Decimal]` | PERCENT |
| `profit_tiers` | `Mapped[list[str]]` | JSON, default=lambda: ['1.5', '3.5', '6.0'] |
| `tier_slices` | `Mapped[list[str]]` | JSON, default=lambda: ['25', '25', '25'] |
| `pullback_pct` | `Mapped[Decimal]` | PERCENT, default=Decimal('3') |
| `buy_zone_fraction` | `Mapped[Decimal]` | PERCENT, default=Decimal('0.35') |
| `crash_daily_pct` | `Mapped[Decimal]` | PERCENT, default=Decimal('8') |
| `crash_drawdown_pct` | `Mapped[Decimal]` | PERCENT, default=Decimal('15') |


### Table `tax_lots` (Model `TaxLot`)

- **File & Lines:** [`backend/database.py#L115`](/backend/database.py#L115-L142)
- **Purpose:** Managed transactional state

| Column Name | ORM Mapped Type | Constraints / Defaults / SQL Type |
| :--- | :--- | :--- |
| `id` | `Mapped[int]` | primary_key=True |
| `symbol` | `Mapped[str]` | ForeignKey('company_profiles.symbol') |
| `bucket` | `Mapped[str]` | String(1) |
| `acquired_on` | `Mapped[date]` | Date |
| `matures_on` | `Mapped[date]` | Date |
| `original_qty` | `Mapped[int]` | Integer |
| `remaining_qty` | `Mapped[int]` | Integer |
| `buy_price` | `Mapped[Decimal]` | PRICE |
| `buy_fee` | `Mapped[Decimal]` | MONEY |
| `original_cost_basis` | `Mapped[Decimal]` | MONEY |
| `remaining_cost_basis` | `Mapped[Decimal]` | MONEY |
| `cycle_base_qty` | `Mapped[int]` | Integer |
| `next_tier` | `Mapped[int]` | Integer, default=0 |
| `last_sale_revision` | `Mapped[int]` | Integer, default=0 |
| `peak_price` | `Mapped[Decimal]` | PRICE |
| `phase` | `Mapped[str]` | String(24), default='ACTIVE' |
| `recovery_anchor` | `Mapped[Decimal | None]` | PRICE, nullable=True |
| `portfolio_id` | `Mapped[str]` | String(32), default='164580' |


### Table `automation_cycles` (Model `AutomationCycle`)

- **File & Lines:** [`backend/database.py#L145`](/backend/database.py#L145-L154)
- **Purpose:** Managed transactional state

| Column Name | ORM Mapped Type | Constraints / Defaults / SQL Type |
| :--- | :--- | :--- |
| `id` | `Mapped[str]` | String(36), primary_key=True |
| `request_id` | `Mapped[str | None]` | String(36), unique=True, nullable=True |
| `signal_key` | `Mapped[str]` | String(100), unique=True |
| `session_on` | `Mapped[date]` | Date |
| `market_revision` | `Mapped[int]` | Integer |
| `rules_revision` | `Mapped[int]` | Integer |
| `result` | `Mapped[dict[str, Any]]` | JSON, default=dict |
| `created_at` | `Mapped[str]` | String(40), default=utc_now_iso |


### Table `trade_logs` (Model `TradeLog`)

- **File & Lines:** [`backend/database.py#L157`](/backend/database.py#L157-L184)
- **Purpose:** Managed transactional state

| Column Name | ORM Mapped Type | Constraints / Defaults / SQL Type |
| :--- | :--- | :--- |
| `id` | `Mapped[int]` | primary_key=True |
| `trade_key` | `Mapped[str]` | String(160), unique=True |
| `cycle_id` | `Mapped[str | None]` | ForeignKey('automation_cycles.id'), nullable=True |
| `lot_id` | `Mapped[int]` | ForeignKey('tax_lots.id') |
| `symbol` | `Mapped[str]` | ForeignKey('company_profiles.symbol') |
| `side` | `Mapped[str]` | String(4) |
| `quantity` | `Mapped[int]` | Integer |
| `price` | `Mapped[Decimal]` | PRICE |
| `gross_amount` | `Mapped[Decimal]` | MONEY |
| `fee` | `Mapped[Decimal]` | MONEY |
| `net_cash_change` | `Mapped[Decimal]` | MONEY |
| `realized_pnl` | `Mapped[Decimal]` | MONEY, default=Decimal('0') |
| `bucket` | `Mapped[str]` | String(1) |
| `trade_on` | `Mapped[date]` | Date |
| `settles_on` | `Mapped[date]` | Date |
| `reason` | `Mapped[str]` | String(500) |
| `source` | `Mapped[str]` | String(32), default='DEMO_PAPER' |
| `portfolio_id` | `Mapped[str]` | String(32), default='164580' |
| `created_at` | `Mapped[str]` | String(40), default=utc_now_iso |


### Table `canary_theses` (Model `CanaryThesis`)

- **File & Lines:** [`backend/database.py#L187`](/backend/database.py#L187-L199)
- **Purpose:** Managed transactional state

| Column Name | ORM Mapped Type | Constraints / Defaults / SQL Type |
| :--- | :--- | :--- |
| `id` | `Mapped[int]` | primary_key=True |
| `symbol` | `Mapped[str]` | ForeignKey('company_profiles.symbol'), index=True |
| `thesis` | `Mapped[str]` | String(500) |
| `created_on` | `Mapped[date]` | Date |
| `entry_price` | `Mapped[Decimal]` | PRICE |
| `canary_qty` | `Mapped[int]` | Integer, default=0 |
| `status` | `Mapped[str]` | String(32), default='OBSERVING' |
| `observations_count` | `Mapped[int]` | Integer, default=0 |
| `last_price_observed` | `Mapped[Decimal]` | PRICE |
| `notes` | `Mapped[str]` | String(500), default='' |
| `created_at` | `Mapped[str]` | String(40), default=utc_now_iso |


### Table `kernel_state_checkpoints` (Model `KernelStateCheckpoint`)

- **File & Lines:** [`backend/database.py#L202`](/backend/database.py#L202-L212)
- **Purpose:** Managed transactional state

| Column Name | ORM Mapped Type | Constraints / Defaults / SQL Type |
| :--- | :--- | :--- |
| `id` | `Mapped[str]` | String(36), primary_key=True |
| `action` | `Mapped[str]` | String(64) |
| `description` | `Mapped[str]` | String(500) |
| `snapshot_payload` | `Mapped[dict[str, Any]]` | JSON |
| `diff_payload` | `Mapped[dict[str, Any] | None]` | JSON, nullable=True |
| `actor` | `Mapped[str]` | String(32), default='Kernel API' |
| `session_on` | `Mapped[date]` | Date |
| `reverted` | `Mapped[bool]` | Boolean, default=False |
| `created_at` | `Mapped[str]` | String(40), default=utc_now_iso |


### Table `cycle_request_keys` (Model `CycleRequestKey`)

- **File & Lines:** [`backend/database.py#L215`](/backend/database.py#L215-L218)
- **Purpose:** Managed transactional state

| Column Name | ORM Mapped Type | Constraints / Defaults / SQL Type |
| :--- | :--- | :--- |
| `request_id` | `Mapped[str]` | String(36), primary_key=True |
| `cycle_id` | `Mapped[str]` | ForeignKey('automation_cycles.id') |


### Table `decision_logs` (Model `DecisionLog`)

- **File & Lines:** [`backend/database.py#L221`](/backend/database.py#L221-L231)
- **Purpose:** Managed transactional state

| Column Name | ORM Mapped Type | Constraints / Defaults / SQL Type |
| :--- | :--- | :--- |
| `id` | `Mapped[int]` | primary_key=True |
| `cycle_id` | `Mapped[str | None]` | ForeignKey('automation_cycles.id'), nullable=True, index=True, default=None |
| `symbol` | `Mapped[str]` | String(40), index=True |
| `lot_id` | `Mapped[int | None]` | ForeignKey('tax_lots.id'), nullable=True |
| `action` | `Mapped[str]` | String(40) |
| `quantity` | `Mapped[int]` | Integer, default=0 |
| `reason` | `Mapped[str]` | String(600) |
| `trading_mode` | `Mapped[str]` | String(32), default='LIVE_HOURS' |
| `created_at` | `Mapped[str]` | String(40), default=utc_now_iso |


### Table `rule_audit` (Model `RuleAudit`)

- **File & Lines:** [`backend/database.py#L234`](/backend/database.py#L234-L242)
- **Purpose:** Managed transactional state

| Column Name | ORM Mapped Type | Constraints / Defaults / SQL Type |
| :--- | :--- | :--- |
| `id` | `Mapped[int]` | primary_key=True |
| `symbol` | `Mapped[str]` | ForeignKey('company_profiles.symbol') |
| `before` | `Mapped[dict[str, Any]]` | JSON |
| `after` | `Mapped[dict[str, Any]]` | JSON |
| `session_on` | `Mapped[date]` | Date |
| `trading_mode` | `Mapped[str]` | String(32), default='LIVE_HOURS' |
| `created_at` | `Mapped[str]` | String(40), default=utc_now_iso |


### Table `kernel_audit_logs` (Model `KernelAuditLog`)

- **File & Lines:** [`backend/database.py#L245`](/backend/database.py#L245-L256)
- **Purpose:** Managed transactional state

| Column Name | ORM Mapped Type | Constraints / Defaults / SQL Type |
| :--- | :--- | :--- |
| `id` | `Mapped[int]` | primary_key=True |
| `endpoint` | `Mapped[str]` | String(80) |
| `action` | `Mapped[str]` | String(80) |
| `symbol` | `Mapped[str | None]` | String(20), nullable=True |
| `payload` | `Mapped[dict[str, Any]]` | JSON |
| `result` | `Mapped[dict[str, Any]]` | JSON |
| `checkpoint_id` | `Mapped[str | None]` | String(64), nullable=True |
| `session_on` | `Mapped[date]` | Date |
| `trading_mode` | `Mapped[str]` | String(32), default='LIVE_HOURS' |
| `created_at` | `Mapped[str]` | String(40), default=utc_now_iso |


### Table `order_idempotency_keys` (Model `OrderIdempotencyKey`)

- **File & Lines:** [`backend/database.py#L259`](/backend/database.py#L259-L267)
- **Purpose:** Managed transactional state

| Column Name | ORM Mapped Type | Constraints / Defaults / SQL Type |
| :--- | :--- | :--- |
| `idempotency_key` | `Mapped[str]` | String(128), primary_key=True |
| `symbol` | `Mapped[str]` | String(32) |
| `side` | `Mapped[str]` | String(10) |
| `quantity` | `Mapped[int]` | Integer |
| `price` | `Mapped[Decimal]` | PRICE |
| `response_payload` | `Mapped[dict[str, Any]]` | JSON |
| `created_at` | `Mapped[str]` | String(40), default=utc_now_iso |


### Table `shadow_orders` (Model `ShadowOrder`)

- **File & Lines:** [`backend/database.py#L270`](/backend/database.py#L270-L291)
- **Purpose:** Managed transactional state

| Column Name | ORM Mapped Type | Constraints / Defaults / SQL Type |
| :--- | :--- | :--- |
| `id` | `Mapped[int]` | primary_key=True, autoincrement=True |
| `order_ref` | `Mapped[str]` | String(64), unique=True, index=True |
| `symbol` | `Mapped[str]` | String(32), index=True |
| `side` | `Mapped[str]` | String(4) |
| `order_type` | `Mapped[str]` | String(16), default='LIMIT' |
| `tif` | `Mapped[str]` | String(8), default='DAY' |
| `quantity` | `Mapped[int]` | Integer |
| `filled_qty` | `Mapped[int]` | Integer, default=0 |
| `pending_qty` | `Mapped[int]` | Integer |
| `limit_price` | `Mapped[Decimal]` | PRICE |
| `avg_fill_price` | `Mapped[Decimal]` | PRICE, default=Decimal('0.0') |
| `order_value` | `Mapped[Decimal]` | MONEY |
| `estimated_fee` | `Mapped[Decimal]` | MONEY |
| `status` | `Mapped[str]` | String(24), default='QUEUED' |
| `actor` | `Mapped[str]` | String(32), default='AUTOTRADER' |
| `reason` | `Mapped[str]` | String(500), default='' |
| `session_on` | `Mapped[date]` | Date |
| `portfolio_id` | `Mapped[str]` | String(32), default='H9210_SHADOW' |
| `created_at` | `Mapped[str]` | String(40), default=utc_now_iso |
| `updated_at` | `Mapped[str]` | String(40), default=utc_now_iso |


### Table `trade_learning_logs` (Model `TradeLearningLog`)

- **File & Lines:** [`backend/database.py#L294`](/backend/database.py#L294-L313)
- **Purpose:** Managed transactional state

| Column Name | ORM Mapped Type | Constraints / Defaults / SQL Type |
| :--- | :--- | :--- |
| `id` | `Mapped[int]` | primary_key=True, autoincrement=True |
| `symbol` | `Mapped[str]` | String(32), index=True |
| `tier` | `Mapped[str]` | String(16), default='L1' |
| `side` | `Mapped[str]` | String(8) |
| `outcome_type` | `Mapped[str]` | String(24) |
| `entry_price` | `Mapped[Decimal]` | PRICE |
| `exit_price` | `Mapped[Decimal | None]` | PRICE, nullable=True, default=None |
| `net_pnl_pct` | `Mapped[Decimal | None]` | PERCENT, nullable=True, default=None |
| `bid_offer_spread_pct` | `Mapped[Decimal | None]` | PERCENT, nullable=True, default=None |
| `support_distance_pct` | `Mapped[Decimal | None]` | PERCENT, nullable=True, default=None |
| `hit_52w_high` | `Mapped[bool]` | Boolean, default=False |
| `hold_sessions` | `Mapped[int]` | Integer, default=0 |
| `actor` | `Mapped[str]` | String(32), default='AUTOTRADER' |
| `operator_override` | `Mapped[bool]` | Boolean, default=False |
| `context_json` | `Mapped[dict[str, Any]]` | JSON, default=dict |
| `lesson_summary` | `Mapped[str]` | String(600), default='' |
| `session_on` | `Mapped[date]` | Date |
| `created_at` | `Mapped[str]` | String(40), default=utc_now_iso |


### Table `chat_budget` (Model `ChatBudget`)

- **File & Lines:** [`backend/database.py#L316`](/backend/database.py#L316-L319)
- **Purpose:** Managed transactional state

| Column Name | ORM Mapped Type | Constraints / Defaults / SQL Type |
| :--- | :--- | :--- |
| `day` | `Mapped[date]` | Date, primary_key=True |
| `calls` | `Mapped[int]` | Integer, default=0 |


### Table `system_heartbeats` (Model `SystemHeartbeat`)

- **File & Lines:** [`backend/database.py#L322`](/backend/database.py#L322-L332)
- **Purpose:** Managed transactional state

| Column Name | ORM Mapped Type | Constraints / Defaults / SQL Type |
| :--- | :--- | :--- |
| `id` | `Mapped[int]` | primary_key=True |
| `status` | `Mapped[str]` | String(32), default='OK' |
| `ingestion_mode` | `Mapped[str]` | String(32), default='BACKGROUND_POLLING' |
| `trading_mode` | `Mapped[str]` | String(32), default='LIVE_HOURS' |
| `automation_enabled` | `Mapped[bool]` | Boolean, default=True |
| `kill_switch_active` | `Mapped[bool]` | Boolean, default=False |
| `circuit_breaker_tripped` | `Mapped[bool]` | Boolean, default=False |
| `details` | `Mapped[dict[str, Any]]` | JSON, default=dict |
| `created_at` | `Mapped[str]` | String(40), default=utc_now_iso, index=True |


### Table `preflight_check_logs` (Model `PreflightCheckLog`)

- **File & Lines:** [`backend/database.py#L335`](/backend/database.py#L335-L343)
- **Purpose:** Managed transactional state

| Column Name | ORM Mapped Type | Constraints / Defaults / SQL Type |
| :--- | :--- | :--- |
| `id` | `Mapped[int]` | primary_key=True |
| `status` | `Mapped[str]` | String(20) |
| `passed_count` | `Mapped[int]` | Integer |
| `total_count` | `Mapped[int]` | Integer |
| `checks` | `Mapped[list[dict[str, Any]]]` | JSON |
| `actor` | `Mapped[str]` | String(40), default='System' |
| `created_at` | `Mapped[str]` | String(40), default=utc_now_iso, index=True |


### Table `daily_summary_logs` (Model `DailySummaryLog`)

- **File & Lines:** [`backend/database.py#L346`](/backend/database.py#L346-L361)
- **Purpose:** Managed transactional state

| Column Name | ORM Mapped Type | Constraints / Defaults / SQL Type |
| :--- | :--- | :--- |
| `id` | `Mapped[int]` | primary_key=True |
| `session_date` | `Mapped[date]` | Date, index=True |
| `orders_count` | `Mapped[int]` | Integer, default=0 |
| `buys_count` | `Mapped[int]` | Integer, default=0 |
| `sells_count` | `Mapped[int]` | Integer, default=0 |
| `buy_spend_bdt` | `Mapped[Decimal]` | MONEY, default=ZERO |
| `sell_proceeds_bdt` | `Mapped[Decimal]` | MONEY, default=ZERO |
| `skips_count` | `Mapped[int]` | Integer, default=0 |
| `skips_breakdown` | `Mapped[dict[str, Any]]` | JSON, default=dict |
| `drift_bdt` | `Mapped[Decimal]` | MONEY, default=ZERO |
| `errors_count` | `Mapped[int]` | Integer, default=0 |
| `errors_summary` | `Mapped[list[str]]` | JSON, default=list |
| `telegram_sent` | `Mapped[bool]` | Boolean, default=False |
| `created_at` | `Mapped[str]` | String(40), default=utc_now_iso |


---

## 5. Pydantic Model Contract Registry

Indexed **30** Pydantic contract and request/response models across `backend/` and `plugins/`:


| Model Class | Defined In | Line | Category | Fields Count | Key Fields | Docstring / Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `BridgeChatRequest` | [`backend/hermes_bridge.py`](/backend/hermes_bridge.py#L76) | `L76` | Request Model | 2 | `message`: str, `session_id`: Optional[str] | Request Model |
| `SetTierRequest` | [`backend/kernel_api.py`](/backend/kernel_api.py#L292) | `L292` | Request Model | 2 | `symbol`: str, `tier`: str | Request Model |
| `SetAllocationRequest` | [`backend/kernel_api.py`](/backend/kernel_api.py#L352) | `L352` | Request Model | 3 | `symbol`: str, `buy_allocation_pct`: Decimal, `enabled`: bool | Request Model |
| `QuarantineRequest` | [`backend/kernel_api.py`](/backend/kernel_api.py#L421) | `L421` | Request Model | 3 | `symbol`: str, `action`: str, `reason`: str | Request Model |
| `SyncRequest` | [`backend/kernel_api.py`](/backend/kernel_api.py#L520) | `L520` | Request Model | 2 | `target`: str, `payload`: dict[str, Any] \| list[Any] \| None | Request Model |
| `OrderRequest` | [`backend/kernel_api.py`](/backend/kernel_api.py#L712) | `L712` | Request Model | 9 | `idempotency_key`: str, `symbol`: str, `side`: str... | Request Model |
| `SetTradingModeRequest` | [`backend/kernel_api.py`](/backend/kernel_api.py#L1277) | `L1277` | Request Model | 2 | `trading_mode`: Literal['TEST_OFFHOURS', 'LIVE_HOURS'], `confirm`: bool | Request Model |
| `SetAutomationConfigRequest` | [`backend/kernel_api.py`](/backend/kernel_api.py#L1341) | `L1341` | Request Model | 4 | `automation_enabled`: bool \| None, `paused`: bool \| None, `ingestion_mode`: str \| None... | Request Model |
| `KernelHandoffRequest` | [`backend/kernel_api.py`](/backend/kernel_api.py#L1445) | `L1445` | Request Model | 1 | `target_mode`: str | Request Model |
| `SchedulerActionRequest` | [`backend/kernel_api.py`](/backend/kernel_api.py#L1525) | `L1525` | Request Model | 1 | `action`: str | Request Model |
| `RunCycleRequest` | [`backend/kernel_api.py`](/backend/kernel_api.py#L1598) | `L1598` | Request Model | 2 | `dry_run`: bool, `idempotency_key`: str \| None | Request Model |
| `StockNowSessionActionRequest` | [`backend/kernel_api.py`](/backend/kernel_api.py#L1648) | `L1648` | Request Model | 2 | `action`: str, `mode`: str \| None | Request Model |
| `CapsUpdateRequest` | [`backend/kernel_api.py`](/backend/kernel_api.py#L1732) | `L1732` | Request Model | 6 | `max_order_bdt`: Decimal \| float \| None, `max_symbol_bdt`: Decimal \| float \| None, `daily_budget_bdt`: Decimal \| float \| None... | Request Model |
| `PauseRequest` | [`backend/main.py`](/backend/main.py#L69) | `L69` | Request Model | 1 | `paused`: StrictBool | Request Model |
| `AutomationConfigRequest` | [`backend/main.py`](/backend/main.py#L74) | `L74` | Request Model | 5 | `automation_enabled`: bool \| None, `paused`: bool \| None, `ingestion_mode`: Literal['BACKGROUND_POLLING', 'ONSCREEN_LIVE', 'SIDE_BY_SIDE_LIVE', 'BACKGROUND_24_7', 'BACKGROUND 24/7'] \| None... | Request Model |
| `HandoffRequest` | [`backend/main.py`](/backend/main.py#L83) | `L83` | Request Model | 2 | `target_mode`: Literal['BACKGROUND_POLLING', 'ONSCREEN_LIVE', 'BACKGROUND_24_7', 'BACKGROUND 24/7'], `reason`: str \| None | Request Model |
| `KillRequest` | [`backend/main.py`](/backend/main.py#L89) | `L89` | Request Model | 2 | `active`: bool, `reason`: str \| None | Request Model |
| `AdvanceRequest` | [`backend/main.py`](/backend/main.py#L95) | `L95` | Request Model | 1 | `scenario`: Literal['NORMAL', 'RALLY', 'PULLBACK', 'CRASH', 'RECOVERY'] | Request Model |
| `AllocationRequest` | [`backend/main.py`](/backend/main.py#L100) | `L100` | Request Model | 2 | `buy_allocation_pct`: Decimal, `enabled`: StrictBool | Request Model |
| `LoginRequest` | [`backend/routes_auth_settings.py`](/backend/routes_auth_settings.py#L21) | `L21` | Request Model | 2 | `username`: str, `password`: str | Request Model |
| `KeysSettingsRequest` | [`backend/routes_auth_settings.py`](/backend/routes_auth_settings.py#L27) | `L27` | Request Model | 5 | `openrouter_key`: str \| None, `gemini_key`: str \| None, `telegram_bot_token`: str \| None... | Request Model |
| `CreateThreadRequest` | [`backend/routes_hermes.py`](/backend/routes_hermes.py#L20) | `L20` | Request Model | 1 | `title`: str | Request Model |
| `SwitchModelRequest` | [`backend/routes_hermes.py`](/backend/routes_hermes.py#L25) | `L25` | Request Model | 2 | `model`: str, `provider`: str \| None | Request Model |
| `StockNowSessionActionRequest` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L36) | `L36` | Request Model | 2 | `action`: Literal['launch', 'check_auth', 'close'], `mode`: Literal['ONSCREEN_LIVE', 'BACKGROUND_POLLING'] \| None | Request Model |
| `StockNowMarketSyncRequest` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L42) | `L42` | Request Model | 1 | `payload`: Any \| None | Request Model |
| `StockNowPortfolioSyncRequest` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L47) | `L47` | Request Model | 1 | `injected_portfolio`: Any \| None | Request Model |
| `StockNowExecuteOrderRequest` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L52) | `L52` | Request Model | 10 | `symbol`: str, `side`: Literal['BUY', 'SELL', 'buy', 'sell'], `quantity`: int... | Request Model |
| `StockNowSchedulerActionRequest` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L74) | `L74` | Request Model | 2 | `action`: Literal['start', 'stop', 'tick_now'], `force`: bool | Request Model |
| `BridgeControlRequest` | [`backend/routes_tradexpress.py`](/backend/routes_tradexpress.py#L29) | `L29` | Request Model | 2 | `action`: str, `cdp_url`: str | Request Model |
| `ShadowOrderRequest` | [`backend/routes_tradexpress.py`](/backend/routes_tradexpress.py#L34) | `L34` | Request Model | 11 | `symbol`: str, `side`: str, `quantity`: int... | Request Model |

---

## 6. Frontend DOM, JS Controller, CSS Design & UI Tool Integration

### 6.1 Theme Color & Layout Tokens Table (`:root` Dark vs Light Mode)

| CSS Custom Property | Category | Dark Mode (`:root`) | Light Mode (`[data-theme="light"]`) |
| :--- | :--- | :--- | :--- |
| `--amber` | Color | `#fbbf24` | `#b45309` |
| `--amber-bg` | Surface / Background | `rgba(251, 191, 36, 0.15)` | `#fef3c7` |
| `--bg` | Surface / Background | `#0a1018` | `#e2e8f0` |
| `--blue` | Color | `#8dacf0` | `#1d4ed8` |
| `--brand` | Color | `#5de4c7` | `#0f766e` |
| `--brand-bg` | Surface / Background | `#15362f` | `#ccfbf1` |
| `--buy` | Color | `#60a5fa` | `#1d4ed8` |
| `--buy-bg` | Surface / Background | `rgba(96, 165, 250, 0.15)` | `#dbeafe` |
| `--chart-crosshair` | Color | `#5de4c7` | `#0d9488` |
| `--chart-grid` | Border / Divider | `#1c2837` | `#cbd5e1` |
| `--dim` | Typography | `#8393a6` | `#334155` |
| `--font-mono` | Color | `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Noto Sans Bengali", "Nirmala UI", "Vrinda", monospace` | `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Noto Sans Bengali", "Nirmala UI", "Vrinda", monospace` |
| `--font-sans` | Color | `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans Bengali", "Nirmala UI", "Vrinda", sans-serif` | `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans Bengali", "Nirmala UI", "Vrinda", sans-serif` |
| `--fs-lg` | Color | `14px` | `14px` |
| `--fs-md` | Color | `13px` | `13px` |
| `--fs-sm` | Color | `12px` | `12px` |
| `--fs-xs` | Color | `11px` | `11px` |
| `--glow-down` | Glow / Shadow | `rgba(239, 68, 68, 0.35)` | `rgba(220, 38, 38, 0.25)` |
| `--glow-up` | Glow / Shadow | `rgba(34, 197, 94, 0.35)` | `rgba(13, 148, 136, 0.25)` |
| `--green` | Color | `#34d399` | `#15803d` |
| `--green-bg` | Surface / Background | `rgba(52, 211, 153, 0.15)` | `#dcfce7` |
| `--line` | Border / Divider | `#202c39` | `#cbd5e1` |
| `--modal-bg` | Surface / Background | `rgba(10, 16, 24, 0.88)` | `rgba(15, 23, 42, 0.65)` |
| `--modal-border` | Border / Divider | `#233547` | `#cbd5e1` |
| `--modal-panel` | Surface / Background | `#111a24` | `#ffffff` |
| `--muted` | Typography | `#9aabbd` | `#1e293b` |
| `--nav-bg` | Surface / Background | `#0d141d` | `#f8fafc` |
| `--panel` | Surface / Background | `#101822` | `#ffffff` |
| `--panel-hover` | Surface / Background | `#141f2b` | `#f8fafc` |
| `--radius` | Shape / Radius | `10px` | `10px` |
| `--red` | Color | `#f87171` | `#dc2626` |
| `--red-bg` | Surface / Background | `rgba(248, 113, 113, 0.15)` | `#fee2e2` |
| `--sell` | Color | `#fbbf24` | `#b45309` |
| `--sell-bg` | Surface / Background | `rgba(251, 191, 36, 0.15)` | `#fef3c7` |
| `--sim-bg` | Surface / Background | `#14202d` | `#f8fafc` |
| `--sim-border` | Border / Divider | `#233446` | `#cbd5e1` |
| `--soft-line` | Border / Divider | `#1a2531` | `#e2e8f0` |
| `--teal` | Color | `#5de4c7` | `#0f766e` |
| `--teal-bg` | Surface / Background | `#15362f` | `#ccfbf1` |
| `--text` | Typography | `#e5edf5` | `#050811` |
| `--tile-neutral` | Color | `#334155` | `#cbd5e1` |


### 6.2 Component CSS Selector Map

| Component Selector | Stylesheet File | Line | Display | Grid / Layout | Position | Background / Color | Flex Wrap |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `.app-shell` | [`frontend/styles.css`](/frontend/styles.css#L242) | `L242` | `grid` | `minmax(0, 1fr) var(--hermes-width, 380px) !important` | — | — | — |
| `.nav-rail` | [`frontend/styles.css`](/frontend/styles.css#L262) | `L262` | `none !important` | — | — | — | — |
| `.nav-rail` | [`frontend/styles.css`](/frontend/styles.css#L269) | `L269` | `flex` | — | — | `var(--nav-bg)` | — |
| `.workspace` | [`frontend/styles.css`](/frontend/styles.css#L370) | `L370` | — | — | `relative` | — | — |
| `.topbar` | [`frontend/styles.css`](/frontend/styles.css#L394) | `L394` | `flex` | — | `sticky` | `rgba(10, 16, 24, 0.88)` | `nowrap` |
| `.topbar-right` | [`frontend/styles.css`](/frontend/styles.css#L430) | `L430` | `flex` | — | — | — | `nowrap` |
| `.topbar` | [`frontend/styles.css`](/frontend/styles.css#L440) | `L440` | `flex` | — | — | — | `nowrap` |
| `.topbar` | [`frontend/styles.css`](/frontend/styles.css#L449) | `L449` | — | — | — | — | — |
| `.topbar` | [`frontend/styles.css`](/frontend/styles.css#L810) | `L810` | — | — | — | — | — |
| `.engine-controls` | [`frontend/styles.css`](/frontend/styles.css#L976) | `L976` | `flex` | — | — | — | — |
| `.session-bar` | [`frontend/styles.css`](/frontend/styles.css#L1012) | `L1012` | `flex` | — | — | `#0e161f` | `wrap` |
| `.metric-card` | [`frontend/styles.css`](/frontend/styles.css#L1068) | `L1068` | — | — | — | `var(--panel)` | — |
| `.skills-drawer` | [`frontend/styles.css`](/frontend/styles.css#L2738) | `L2738` | — | — | — | `var(--panel)` | — |
| `.model-dropup-menu` | [`frontend/styles.css`](/frontend/styles.css#L4671) | `L4671` | — | — | `absolute` | `var(--panel, #111a24)` | — |
| `.tx-topbar` | [`frontend/styles.css`](/frontend/styles.css#L6581) | `L6581` | `flex` | — | — | `#0d1522` | — |
| `.tx-bottom-split` | [`frontend/styles.css`](/frontend/styles.css#L6808) | `L6808` | `flex` | — | — | — | — |
| `.tx-top-header` | [`frontend/styles.css`](/frontend/styles.css#L6827) | `L6827` | `flex !important` | — | `relative !important` | `#0a0f18 !important` | `nowrap !important` |
| `.tx-topbar` | [`frontend/styles.css`](/frontend/styles.css#L6828) | `L6828` | `flex !important` | — | `relative !important` | `#0a0f18 !important` | `nowrap !important` |
| `.tx-topbar` | [`frontend/styles.css`](/frontend/styles.css#L6916) | `L6916` | — | — | — | — | — |
| `.tx-mw-header` | [`frontend/styles.css`](/frontend/styles.css#L6925) | `L6925` | `flex` | — | — | `#0a0f18` | `nowrap` |
| `.tx-ticket-strip` | [`frontend/styles.css`](/frontend/styles.css#L7167) | `L7167` | `flex` | — | — | `#0d1522` | — |
| `.tx-depth-pane` | [`frontend/styles.css`](/frontend/styles.css#L7379) | `L7379` | `flex` | — | — | `#090e17` | — |
| `#tx-confirm-order-modal` | [`frontend/styles.css`](/frontend/styles.css#L7581) | `L7581` | — | — | — | `#0f172a` | — |
| `.session-bar` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L69) | `L69` | — | — | — | `#ffffff` | — |
| `.metric-card` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L95) | `L95` | — | — | — | `#ffffff` | — |
| `.nav-rail` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L499) | `L499` | — | — | — | `#f8fafc !important` | — |
| `.chat-messages` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L557) | `L557` | — | — | — | `#ffffff !important` | — |
| `.diff-card` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L596) | `L596` | — | — | — | `#ffffff !important` | — |
| `.nav-rail` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L809) | `L809` | — | — | — | `#ccfbf1 !important` | — |
| `.topbar` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L872) | `L872` | — | — | — | `rgba(226, 232, 240, 0.92)` | — |
| `#hermes-resizer` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L959) | `L959` | — | — | `absolute` | `transparent` | — |
| `.app-shell` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L1000) | `L1000` | — | — | — | — | — |
| `.chat-messages` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L1109) | `L1109` | — | — | — | — | — |
| `.diff-card` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L1599) | `L1599` | — | — | — | `var(--panel)` | — |
| `.model-dropup-menu` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L1734) | `L1734` | — | — | `absolute` | `var(--panel, #111a24)` | — |
| `.model-dropup-menu` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L1751) | `L1751` | — | — | — | `#ffffff` | — |
| `.workspace` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L1874) | `L1874` | — | — | — | — | — |
| `.skills-drawer` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L2226) | `L2226` | — | — | — | `#ffffff !important` | — |
| `.skills-drawer` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L2977) | `L2977` | — | — | — | `var(--panel)` | — |
| `.tx-topbar` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L3027) | `L3027` | — | — | — | `#ffffff` | — |
| `.tx-mw-header` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L3071) | `L3071` | — | — | — | `#f8fafc` | — |
| `.tx-depth-pane` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L3137) | `L3137` | — | — | — | `#ffffff` | — |
| `#tx-confirm-order-modal` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L3146) | `L3146` | — | — | — | `#ffffff` | — |


### 6.3 DOM Identifiers Index (`frontend/index.html`)

Complete catalog of all **434** distinct element IDs in `frontend/index.html` for UI element location:

| DOM Element ID (`id="..."`) | HTML Tag | Line Number |
| :--- | :--- | :--- |
| `#nav-system-control` | `<a>` | [`frontend/index.html#L31`](/frontend/index.html#L31) |
| `#user-avatar-btn` | `<button>` | [`frontend/index.html#L33`](/frontend/index.html#L33) |
| `#tx-top-header` | `<header>` | [`frontend/index.html#L40`](/frontend/index.html#L40) |
| `#portfolio-header-badge` | `<span>` | [`frontend/index.html#L46`](/frontend/index.html#L46) |
| `#portfolio-header-badge-dot` | `<span>` | [`frontend/index.html#L47`](/frontend/index.html#L47) |
| `#portfolio-header-badge-text` | `<span>` | [`frontend/index.html#L48`](/frontend/index.html#L48) |
| `#tx-hdr-buying-power` | `<span>` | [`frontend/index.html#L60`](/frontend/index.html#L60) |
| `#tx-hdr-gain-loss` | `<span>` | [`frontend/index.html#L64`](/frontend/index.html#L64) |
| `#topbar-clock-widget` | `<button>` | [`frontend/index.html#L68`](/frontend/index.html#L68) |
| `#market-status-dot` | `<span>` | [`frontend/index.html#L69`](/frontend/index.html#L69) |
| `#market-status-text` | `<span>` | [`frontend/index.html#L70`](/frontend/index.html#L70) |
| `#market-countdown-text` | `<span>` | [`frontend/index.html#L72`](/frontend/index.html#L72) |
| `#topbar-tmode-badge` | `<span>` | [`frontend/index.html#L73`](/frontend/index.html#L73) |
| `#topbar-run-mode-switch` | `<div>` | [`frontend/index.html#L78`](/frontend/index.html#L78) |
| `#topbar-mode-btn-background` | `<button>` | [`frontend/index.html#L79`](/frontend/index.html#L79) |
| `#topbar-mode-btn-onscreen` | `<button>` | [`frontend/index.html#L80`](/frontend/index.html#L80) |
| `#topbar-switching-state` | `<span>` | [`frontend/index.html#L82`](/frontend/index.html#L82) |
| `#topbar-automation-control` | `<div>` | [`frontend/index.html#L86`](/frontend/index.html#L86) |
| `#topbar-automation-toggle-input` | `<input>` | [`frontend/index.html#L89`](/frontend/index.html#L89) |
| `#topbar-automation-state` | `<span>` | [`frontend/index.html#L92`](/frontend/index.html#L92) |
| `#run-cycle` | `<button>` | [`frontend/index.html#L96`](/frontend/index.html#L96) |
| `#run-label` | `<span>` | [`frontend/index.html#L96`](/frontend/index.html#L96) |
| `#theme-toggle-btn` | `<button>` | [`frontend/index.html#L99`](/frontend/index.html#L99) |
| `#theme-name` | `<span>` | [`frontend/index.html#L100`](/frontend/index.html#L100) |
| `#tx-main-nav` | `<nav>` | [`frontend/index.html#L105`](/frontend/index.html#L105) |
| `#tx-nav-trade` | `<button>` | [`frontend/index.html#L106`](/frontend/index.html#L106) |
| `#tx-nav-heatmap` | `<button>` | [`frontend/index.html#L107`](/frontend/index.html#L107) |
| `#tx-nav-rules` | `<button>` | [`frontend/index.html#L108`](/frontend/index.html#L108) |
| `#tx-nav-ledger` | `<button>` | [`frontend/index.html#L109`](/frontend/index.html#L109) |
| `#tx-nav-learning` | `<button>` | [`frontend/index.html#L110`](/frontend/index.html#L110) |
| `#tx-nav-settings` | `<button>` | [`frontend/index.html#L111`](/frontend/index.html#L111) |
| `#tx-passive-spy-btn` | `<button>` | [`frontend/index.html#L112`](/frontend/index.html#L112) |
| `#topbar-kill-btn` | `<button>` | [`frontend/index.html#L116`](/frontend/index.html#L116) |
| `#topbar-handoff-btn` | `<button>` | [`frontend/index.html#L117`](/frontend/index.html#L117) |
| `#topbar-handoff-label` | `<span>` | [`frontend/index.html#L118`](/frontend/index.html#L118) |
| `#topbar-kill-label` | `<span>` | [`frontend/index.html#L119`](/frontend/index.html#L119) |
| `#topbar-status-text` | `<span>` | [`frontend/index.html#L120`](/frontend/index.html#L120) |
| `#topbar-master-toggle` | `<div>` | [`frontend/index.html#L121`](/frontend/index.html#L121) |
| `#topbar-overflow-btn` | `<button>` | [`frontend/index.html#L122`](/frontend/index.html#L122) |
| `#topbar-overflow-menu` | `<div>` | [`frontend/index.html#L123`](/frontend/index.html#L123) |
| `#trading-mode-toggle` | `<div>` | [`frontend/index.html#L124`](/frontend/index.html#L124) |
| `#header-mode-slider` | `<div>` | [`frontend/index.html#L125`](/frontend/index.html#L125) |
| `#topbar-master-label` | `<span>` | [`frontend/index.html#L126`](/frontend/index.html#L126) |
| `#footer-mode-tag` | `<div>` | [`frontend/index.html#L127`](/frontend/index.html#L127) |
| `#bucket-stack` | `<div>` | [`frontend/index.html#L128`](/frontend/index.html#L128) |
| `#holdings-settled-cash` | `<span>` | [`frontend/index.html#L129`](/frontend/index.html#L129) |
| `#holdings-buy-cost` | `<span>` | [`frontend/index.html#L130`](/frontend/index.html#L130) |
| `#holdings-sell-value` | `<span>` | [`frontend/index.html#L131`](/frontend/index.html#L131) |
| `#holdings-unrealized-gain` | `<span>` | [`frontend/index.html#L132`](/frontend/index.html#L132) |
| `#watchlist-source-label` | `<span>` | [`frontend/index.html#L133`](/frontend/index.html#L133) |
| `#overflow-mode-live` | `<button>` | [`frontend/index.html#L134`](/frontend/index.html#L134) |
| `#overflow-mode-polling` | `<button>` | [`frontend/index.html#L135`](/frontend/index.html#L135) |
| `#overflow-tmode-live` | `<button>` | [`frontend/index.html#L136`](/frontend/index.html#L136) |
| `#overflow-tmode-test` | `<button>` | [`frontend/index.html#L137`](/frontend/index.html#L137) |
| `#hdr-mode-live` | `<button>` | [`frontend/index.html#L138`](/frontend/index.html#L138) |
| `#hdr-mode-polling` | `<button>` | [`frontend/index.html#L139`](/frontend/index.html#L139) |
| `#hdr-tmode-dot` | `<span>` | [`frontend/index.html#L140`](/frontend/index.html#L140) |
| `#hdr-tmode-label` | `<span>` | [`frontend/index.html#L141`](/frontend/index.html#L141) |
| `#hdr-tmode-live` | `<button>` | [`frontend/index.html#L142`](/frontend/index.html#L142) |
| `#hdr-tmode-pill` | `<div>` | [`frontend/index.html#L143`](/frontend/index.html#L143) |
| `#hdr-tmode-test` | `<button>` | [`frontend/index.html#L144`](/frontend/index.html#L144) |
| `#pause-button` | `<button>` | [`frontend/index.html#L145`](/frontend/index.html#L145) |
| `#rollback-button` | `<button>` | [`frontend/index.html#L146`](/frontend/index.html#L146) |
| `#settings-handoff-btn` | `<button>` | [`frontend/index.html#L147`](/frontend/index.html#L147) |
| `#settings-handoff-label` | `<span>` | [`frontend/index.html#L148`](/frontend/index.html#L148) |
| `#skills-drawer` | `<div>` | [`frontend/index.html#L149`](/frontend/index.html#L149) |
| `#skills-toggle` | `<button>` | [`frontend/index.html#L150`](/frontend/index.html#L150) |
| `#close-skills` | `<button>` | [`frontend/index.html#L151`](/frontend/index.html#L151) |
| `#adapter-dot` | `<span>` | [`frontend/index.html#L152`](/frontend/index.html#L152) |
| `#adapter-status-text` | `<span>` | [`frontend/index.html#L153`](/frontend/index.html#L153) |
| `#daily-limit-slider` | `<input>` | [`frontend/index.html#L154`](/frontend/index.html#L154) |
| `#key-daily-limit` | `<span>` | [`frontend/index.html#L155`](/frontend/index.html#L155) |
| `#save-keys-btn` | `<button>` | [`frontend/index.html#L156`](/frontend/index.html#L156) |
| `#hermes-model-btn` | `<button>` | [`frontend/index.html#L157`](/frontend/index.html#L157) |
| `#hermes-bottom-model-btn` | `<button>` | [`frontend/index.html#L158`](/frontend/index.html#L158) |
| `#hermes-model-display` | `<span>` | [`frontend/index.html#L159`](/frontend/index.html#L159) |
| `#hermes-resize-handle` | `<div>` | [`frontend/index.html#L160`](/frontend/index.html#L160) |
| `#skills-count` | `<span>` | [`frontend/index.html#L161`](/frontend/index.html#L161) |
| `#lock-cockpit-btn` | `<button>` | [`frontend/index.html#L162`](/frontend/index.html#L162) |
| `#login-form` | `<form>` | [`frontend/index.html#L163`](/frontend/index.html#L163) |
| `#login-username` | `<input>` | [`frontend/index.html#L164`](/frontend/index.html#L164) |
| `#login-password` | `<input>` | [`frontend/index.html#L165`](/frontend/index.html#L165) |
| `#login-error-msg` | `<span>` | [`frontend/index.html#L166`](/frontend/index.html#L166) |
| `#login-autofill-btn` | `<button>` | [`frontend/index.html#L167`](/frontend/index.html#L167) |
| `#op-backdrop` | `<div>` | [`frontend/index.html#L169`](/frontend/index.html#L169) |
| `#error-banner` | `<div>` | [`frontend/index.html#L172`](/frontend/index.html#L172) |
| `#error-text` | `<span>` | [`frontend/index.html#L172`](/frontend/index.html#L172) |
| `#dismiss-error` | `<button>` | [`frontend/index.html#L172`](/frontend/index.html#L172) |
| `#view-dashboard` | `<div>` | [`frontend/index.html#L174`](/frontend/index.html#L174) |
| `#tx-trade-workspace` | `<div>` | [`frontend/index.html#L175`](/frontend/index.html#L175) |
| `#tx-market-watch` | `<section>` | [`frontend/index.html#L177`](/frontend/index.html#L177) |
| `#category-tabs` | `<div>` | [`frontend/index.html#L181`](/frontend/index.html#L181) |
| `#cat-all-count` | `<span>` | [`frontend/index.html#L182`](/frontend/index.html#L182) |
| `#cat-gsc-count` | `<span>` | [`frontend/index.html#L183`](/frontend/index.html#L183) |
| `#cat-l1-count` | `<span>` | [`frontend/index.html#L184`](/frontend/index.html#L184) |
| `#cat-l2-count` | `<span>` | [`frontend/index.html#L185`](/frontend/index.html#L185) |
| `#cat-dse-count` | `<span>` | [`frontend/index.html#L186`](/frontend/index.html#L186) |
| `#company-search` | `<input>` | [`frontend/index.html#L192`](/frontend/index.html#L192) |
| `#filter-hide-z-spot` | `<input>` | [`frontend/index.html#L195`](/frontend/index.html#L195) |
| `#filter-held-only` | `<input>` | [`frontend/index.html#L198`](/frontend/index.html#L198) |
| `#company-count` | `<span>` | [`frontend/index.html#L200`](/frontend/index.html#L200) |
| `#watchlist` | `<table>` | [`frontend/index.html#L206`](/frontend/index.html#L206) |
| `#watchlist-thead` | `<thead>` | [`frontend/index.html#L207`](/frontend/index.html#L207) |
| `#col-curve-signal` | `<th>` | [`frontend/index.html#L215`](/frontend/index.html#L215) |
| `#col-held-mature` | `<th>` | [`frontend/index.html#L217`](/frontend/index.html#L217) |
| `#col-buy-cap` | `<th>` | [`frontend/index.html#L221`](/frontend/index.html#L221) |
| `#watchlist-body` | `<tbody>` | [`frontend/index.html#L224`](/frontend/index.html#L224) |
| `#watchlist-pagination` | `<div>` | [`frontend/index.html#L229`](/frontend/index.html#L229) |
| `#watchlist-prev-page` | `<button>` | [`frontend/index.html#L230`](/frontend/index.html#L230) |
| `#watchlist-page-info` | `<span>` | [`frontend/index.html#L231`](/frontend/index.html#L231) |
| `#watchlist-next-page` | `<button>` | [`frontend/index.html#L232`](/frontend/index.html#L232) |
| `#tx-order-ticket` | `<section>` | [`frontend/index.html#L239`](/frontend/index.html#L239) |
| `#tx-ticket-header-title` | `<h2>` | [`frontend/index.html#L241`](/frontend/index.html#L241) |
| `#tx-order-side-toggle` | `<div>` | [`frontend/index.html#L246`](/frontend/index.html#L246) |
| `#tx-side-buy-btn` | `<button>` | [`frontend/index.html#L247`](/frontend/index.html#L247) |
| `#tx-side-sell-btn` | `<button>` | [`frontend/index.html#L248`](/frontend/index.html#L248) |
| `#tx-ticket-bp` | `<strong>` | [`frontend/index.html#L251`](/frontend/index.html#L251) |
| `#tx-ticket-avail-qty` | `<strong>` | [`frontend/index.html#L252`](/frontend/index.html#L252) |
| `#tx-ticket-gainloss` | `<span>` | [`frontend/index.html#L253`](/frontend/index.html#L253) |
| `#tx-ticket-symbol-info` | `<div>` | [`frontend/index.html#L258`](/frontend/index.html#L258) |
| `#tx-ticket-cat` | `<span>` | [`frontend/index.html#L259`](/frontend/index.html#L259) |
| `#tx-ticket-sym` | `<strong>` | [`frontend/index.html#L259`](/frontend/index.html#L259) |
| `#tx-ticket-ltp` | `<strong>` | [`frontend/index.html#L261`](/frontend/index.html#L261) |
| `#tx-ticket-chgpct` | `<span>` | [`frontend/index.html#L261`](/frontend/index.html#L261) |
| `#tx-ticket-minmax` | `<span>` | [`frontend/index.html#L262`](/frontend/index.html#L262) |
| `#tx-ticket-bidoffer` | `<span>` | [`frontend/index.html#L263`](/frontend/index.html#L263) |
| `#tx-ticket-lowhigh` | `<span>` | [`frontend/index.html#L264`](/frontend/index.html#L264) |
| `#tx-order-type` | `<select>` | [`frontend/index.html#L275`](/frontend/index.html#L275) |
| `#tx-order-qty` | `<input>` | [`frontend/index.html#L279`](/frontend/index.html#L279) |
| `#tx-order-price` | `<input>` | [`frontend/index.html#L284`](/frontend/index.html#L284) |
| `#tx-price-up` | `<button>` | [`frontend/index.html#L286`](/frontend/index.html#L286) |
| `#tx-price-down` | `<button>` | [`frontend/index.html#L287`](/frontend/index.html#L287) |
| `#tx-order-tif` | `<select>` | [`frontend/index.html#L297`](/frontend/index.html#L297) |
| `#tx-order-disclosed-qty` | `<input>` | [`frontend/index.html#L301`](/frontend/index.html#L301) |
| `#tx-order-min-fill` | `<input>` | [`frontend/index.html#L305`](/frontend/index.html#L305) |
| `#tx-order-all-or-none` | `<input>` | [`frontend/index.html#L312`](/frontend/index.html#L312) |
| `#tx-depth-table` | `<table>` | [`frontend/index.html#L325`](/frontend/index.html#L325) |
| `#tx-depth-body` | `<tbody>` | [`frontend/index.html#L334`](/frontend/index.html#L334) |
| `#tx-order-submit-btn` | `<button>` | [`frontend/index.html#L345`](/frontend/index.html#L345) |
| `#tx-order-reset-btn` | `<button>` | [`frontend/index.html#L346`](/frontend/index.html#L346) |
| `#tx-ticket-order-val` | `<strong>` | [`frontend/index.html#L349`](/frontend/index.html#L349) |
| `#tx-ticket-fee` | `<strong>` | [`frontend/index.html#L350`](/frontend/index.html#L350) |
| `#tx-ticket-net-val` | `<strong>` | [`frontend/index.html#L351`](/frontend/index.html#L351) |
| `#tx-monitor-panel` | `<section>` | [`frontend/index.html#L357`](/frontend/index.html#L357) |
| `#tx-tab-order-list` | `<button>` | [`frontend/index.html#L360`](/frontend/index.html#L360) |
| `#tx-order-count` | `<span>` | [`frontend/index.html#L360`](/frontend/index.html#L360) |
| `#tx-tab-portfolio` | `<button>` | [`frontend/index.html#L361`](/frontend/index.html#L361) |
| `#tx-tab-account-summary` | `<button>` | [`frontend/index.html#L362`](/frontend/index.html#L362) |
| `#tx-tab-order-search` | `<button>` | [`frontend/index.html#L363`](/frontend/index.html#L363) |
| `#tx-pane-order-list` | `<div>` | [`frontend/index.html#L369`](/frontend/index.html#L369) |
| `#tx-orders-table` | `<table>` | [`frontend/index.html#L371`](/frontend/index.html#L371) |
| `#tx-orders-body` | `<tbody>` | [`frontend/index.html#L387`](/frontend/index.html#L387) |
| `#tx-pane-portfolio` | `<div>` | [`frontend/index.html#L395`](/frontend/index.html#L395) |
| `#tx-portfolio-table` | `<table>` | [`frontend/index.html#L397`](/frontend/index.html#L397) |
| `#active-holdings-body` | `<tbody>` | [`frontend/index.html#L412`](/frontend/index.html#L412) |
| `#active-holdings-foot` | `<tfoot>` | [`frontend/index.html#L415`](/frontend/index.html#L415) |
| `#tx-pane-account-summary` | `<div>` | [`frontend/index.html#L421`](/frontend/index.html#L421) |
| `#tx-acc-settled-cash` | `<span>` | [`frontend/index.html#L427`](/frontend/index.html#L427) |
| `#tx-acc-buying-power` | `<strong>` | [`frontend/index.html#L428`](/frontend/index.html#L428) |
| `#tx-acc-blocked` | `<span>` | [`frontend/index.html#L429`](/frontend/index.html#L429) |
| `#tx-acc-unsettled-sales` | `<strong>` | [`frontend/index.html#L430`](/frontend/index.html#L430) |
| `#tx-acc-realized-pnl` | `<span>` | [`frontend/index.html#L431`](/frontend/index.html#L431) |
| `#tx-acc-unrealized-pnl` | `<span>` | [`frontend/index.html#L432`](/frontend/index.html#L432) |
| `#tx-account-donut` | `<div>` | [`frontend/index.html#L436`](/frontend/index.html#L436) |
| `#tx-pane-order-search` | `<div>` | [`frontend/index.html#L443`](/frontend/index.html#L443) |
| `#tx-search-sym` | `<input>` | [`frontend/index.html#L445`](/frontend/index.html#L445) |
| `#tx-search-side` | `<select>` | [`frontend/index.html#L446`](/frontend/index.html#L446) |
| `#tx-search-status` | `<select>` | [`frontend/index.html#L451`](/frontend/index.html#L451) |
| `#tx-search-orders-body` | `<tbody>` | [`frontend/index.html#L468`](/frontend/index.html#L468) |
| `#view-heatmap-wrap` | `<div>` | [`frontend/index.html#L481`](/frontend/index.html#L481) |
| `#market-map` | `<section>` | [`frontend/index.html#L482`](/frontend/index.html#L482) |
| `#treemap-sector-select` | `<select>` | [`frontend/index.html#L489`](/frontend/index.html#L489) |
| `#treemap-back-btn` | `<button>` | [`frontend/index.html#L499`](/frontend/index.html#L499) |
| `#treemap-active-view` | `<span>` | [`frontend/index.html#L502`](/frontend/index.html#L502) |
| `#treemap-turnover-badge` | `<span>` | [`frontend/index.html#L503`](/frontend/index.html#L503) |
| `#treemap-container` | `<div>` | [`frontend/index.html#L508`](/frontend/index.html#L508) |
| `#treemap-tooltip` | `<div>` | [`frontend/index.html#L511`](/frontend/index.html#L511) |
| `#sector-gainer-chart-wrap` | `<div>` | [`frontend/index.html#L530`](/frontend/index.html#L530) |
| `#sector-gainer-chart` | `<svg>` | [`frontend/index.html#L531`](/frontend/index.html#L531) |
| `#view-rules-wrap` | `<div>` | [`frontend/index.html#L539`](/frontend/index.html#L539) |
| `#rules` | `<section>` | [`frontend/index.html#L540`](/frontend/index.html#L540) |
| `#what-if-card` | `<article>` | [`frontend/index.html#L549`](/frontend/index.html#L549) |
| `#sim-symbol-badge` | `<span>` | [`frontend/index.html#L555`](/frontend/index.html#L555) |
| `#what-if-target-price` | `<strong>` | [`frontend/index.html#L559`](/frontend/index.html#L559) |
| `#what-if-target-pct` | `<span>` | [`frontend/index.html#L560`](/frontend/index.html#L560) |
| `#what-if-slider` | `<input>` | [`frontend/index.html#L563`](/frontend/index.html#L563) |
| `#what-if-gross` | `<strong>` | [`frontend/index.html#L572`](/frontend/index.html#L572) |
| `#what-if-fee` | `<strong>` | [`frontend/index.html#L573`](/frontend/index.html#L573) |
| `#what-if-net-pnl` | `<strong>` | [`frontend/index.html#L574`](/frontend/index.html#L574) |
| `#what-if-return-pct` | `<strong>` | [`frontend/index.html#L575`](/frontend/index.html#L575) |
| `#profit-tiers` | `<div>` | [`frontend/index.html#L587`](/frontend/index.html#L587) |
| `#pullback-setting` | `<span>` | [`frontend/index.html#L587`](/frontend/index.html#L587) |
| `#allocation-form` | `<form>` | [`frontend/index.html#L588`](/frontend/index.html#L588) |
| `#buy-allocation` | `<input>` | [`frontend/index.html#L592`](/frontend/index.html#L592) |
| `#company-enabled` | `<input>` | [`frontend/index.html#L598`](/frontend/index.html#L598) |
| `#save-allocation` | `<button>` | [`frontend/index.html#L603`](/frontend/index.html#L603) |
| `#canary-section` | `<section>` | [`frontend/index.html#L609`](/frontend/index.html#L609) |
| `#canary-count` | `<span>` | [`frontend/index.html#L610`](/frontend/index.html#L610) |
| `#canary-feed` | `<div>` | [`frontend/index.html#L611`](/frontend/index.html#L611) |
| `#decision-panel` | `<section>` | [`frontend/index.html#L615`](/frontend/index.html#L615) |
| `#decision-count` | `<span>` | [`frontend/index.html#L617`](/frontend/index.html#L617) |
| `#cycle-badge` | `<span>` | [`frontend/index.html#L625`](/frontend/index.html#L625) |
| `#decision-feed` | `<div>` | [`frontend/index.html#L627`](/frontend/index.html#L627) |
| `#view-ledger-wrap` | `<div>` | [`frontend/index.html#L641`](/frontend/index.html#L641) |
| `#ledger` | `<section>` | [`frontend/index.html#L642`](/frontend/index.html#L642) |
| `#period-pnl` | `<strong>` | [`frontend/index.html#L651`](/frontend/index.html#L651) |
| `#period-buy` | `<strong>` | [`frontend/index.html#L651`](/frontend/index.html#L651) |
| `#period-sell` | `<strong>` | [`frontend/index.html#L651`](/frontend/index.html#L651) |
| `#period-trades` | `<strong>` | [`frontend/index.html#L651`](/frontend/index.html#L651) |
| `#trades-body` | `<tbody>` | [`frontend/index.html#L652`](/frontend/index.html#L652) |
| `#ledger-range` | `<span>` | [`frontend/index.html#L653`](/frontend/index.html#L653) |
| `#tx-learning-view` | `<div>` | [`frontend/index.html#L659`](/frontend/index.html#L659) |
| `#tx-learn-total` | `<div>` | [`frontend/index.html#L666`](/frontend/index.html#L666) |
| `#tx-learn-win-rate` | `<div>` | [`frontend/index.html#L671`](/frontend/index.html#L671) |
| `#tx-learn-buys` | `<div>` | [`frontend/index.html#L676`](/frontend/index.html#L676) |
| `#tx-learn-sells` | `<div>` | [`frontend/index.html#L681`](/frontend/index.html#L681) |
| `#tx-learn-avg-pnl` | `<div>` | [`frontend/index.html#L686`](/frontend/index.html#L686) |
| `#tx-learn-table` | `<table>` | [`frontend/index.html#L696`](/frontend/index.html#L696) |
| `#tx-learn-body` | `<tbody>` | [`frontend/index.html#L711`](/frontend/index.html#L711) |
| `#view-settings` | `<div>` | [`frontend/index.html#L719`](/frontend/index.html#L719) |
| `#system-control` | `<div>` | [`frontend/index.html#L724`](/frontend/index.html#L724) |
| `#automation-settings-card` | `<article>` | [`frontend/index.html#L726`](/frontend/index.html#L726) |
| `#circuit-state` | `<span>` | [`frontend/index.html#L739`](/frontend/index.html#L739) |
| `#master-automation-toggle-input` | `<input>` | [`frontend/index.html#L743`](/frontend/index.html#L743) |
| `#master-automation-status-text` | `<span>` | [`frontend/index.html#L746`](/frontend/index.html#L746) |
| `#master-automation-toggle` | `<button>` | [`frontend/index.html#L749`](/frontend/index.html#L749) |
| `#current-mode-pill` | `<span>` | [`frontend/index.html#L758`](/frontend/index.html#L758) |
| `#ingestion-mode-switch` | `<div>` | [`frontend/index.html#L760`](/frontend/index.html#L760) |
| `#mode-btn-polling` | `<button>` | [`frontend/index.html#L761`](/frontend/index.html#L761) |
| `#mode-btn-live` | `<button>` | [`frontend/index.html#L771`](/frontend/index.html#L771) |
| `#settings-runmode-status-line` | `<div>` | [`frontend/index.html#L782`](/frontend/index.html#L782) |
| `#settings-active-mode-text` | `<span>` | [`frontend/index.html#L783`](/frontend/index.html#L783) |
| `#settings-pending-handoff-state` | `<span>` | [`frontend/index.html#L784`](/frontend/index.html#L784) |
| `#settings-trading-mode-wrap` | `<div>` | [`frontend/index.html#L788`](/frontend/index.html#L788) |
| `#settings-trading-mode-pill` | `<span>` | [`frontend/index.html#L794`](/frontend/index.html#L794) |
| `#settings-trading-mode-toggle` | `<div>` | [`frontend/index.html#L796`](/frontend/index.html#L796) |
| `#settings-tmode-live` | `<button>` | [`frontend/index.html#L797`](/frontend/index.html#L797) |
| `#settings-tmode-test` | `<button>` | [`frontend/index.html#L807`](/frontend/index.html#L807) |
| `#polling-interval-wrap` | `<div>` | [`frontend/index.html#L820`](/frontend/index.html#L820) |
| `#polling-interval-display` | `<strong>` | [`frontend/index.html#L826`](/frontend/index.html#L826) |
| `#polling-range-slider` | `<input>` | [`frontend/index.html#L829`](/frontend/index.html#L829) |
| `#polling-interval-pills` | `<div>` | [`frontend/index.html#L838`](/frontend/index.html#L838) |
| `#polling-disabled-hint` | `<div>` | [`frontend/index.html#L844`](/frontend/index.html#L844) |
| `#tx-feed-status-card` | `<article>` | [`frontend/index.html#L849`](/frontend/index.html#L849) |
| `#tx-feed-cdp-badge` | `<span>` | [`frontend/index.html#L851`](/frontend/index.html#L851) |
| `#tx-feed-health-badge` | `<span>` | [`frontend/index.html#L852`](/frontend/index.html#L852) |
| `#tx-bridge-attach-btn` | `<button>` | [`frontend/index.html#L858`](/frontend/index.html#L858) |
| `#tx-bridge-detach-btn` | `<button>` | [`frontend/index.html#L859`](/frontend/index.html#L859) |
| `#tx-extension-setup-hint` | `<div>` | [`frontend/index.html#L861`](/frontend/index.html#L861) |
| `#tx-feed-bridge-stats` | `<div>` | [`frontend/index.html#L869`](/frontend/index.html#L869) |
| `#tx-feed-tabs-status` | `<div>` | [`frontend/index.html#L871`](/frontend/index.html#L871) |
| `#tx-feed-guidance-list` | `<ul>` | [`frontend/index.html#L877`](/frontend/index.html#L877) |
| `#stocknow-connection-card` | `<article>` | [`frontend/index.html#L884`](/frontend/index.html#L884) |
| `#stocknow-api-status` | `<strong>` | [`frontend/index.html#L894`](/frontend/index.html#L894) |
| `#stocknow-browser-status` | `<strong>` | [`frontend/index.html#L898`](/frontend/index.html#L898) |
| `#stocknow-prices-synced` | `<strong>` | [`frontend/index.html#L902`](/frontend/index.html#L902) |
| `#stocknow-portfolio-synced` | `<strong>` | [`frontend/index.html#L906`](/frontend/index.html#L906) |
| `#stocknow-active-portfolio` | `<strong>` | [`frontend/index.html#L910`](/frontend/index.html#L910) |
| `#btn-stocknow-launch` | `<button>` | [`frontend/index.html#L915`](/frontend/index.html#L915) |
| `#btn-stocknow-auth` | `<button>` | [`frontend/index.html#L916`](/frontend/index.html#L916) |
| `#btn-stocknow-sync` | `<button>` | [`frontend/index.html#L917`](/frontend/index.html#L917) |
| `#btn-stocknow-logout` | `<button>` | [`frontend/index.html#L918`](/frontend/index.html#L918) |
| `#btn-stocknow-sync-portfolio` | `<button>` | [`frontend/index.html#L920`](/frontend/index.html#L920) |
| `#risk-caps-card` | `<article>` | [`frontend/index.html#L925`](/frontend/index.html#L925) |
| `#risk-caps-form` | `<form>` | [`frontend/index.html#L932`](/frontend/index.html#L932) |
| `#caps-kill-switch` | `<input>` | [`frontend/index.html#L940`](/frontend/index.html#L940) |
| `#caps-kill-switch-status` | `<span>` | [`frontend/index.html#L941`](/frontend/index.html#L941) |
| `#caps-max-order` | `<input>` | [`frontend/index.html#L949`](/frontend/index.html#L949) |
| `#caps-max-symbol` | `<input>` | [`frontend/index.html#L953`](/frontend/index.html#L953) |
| `#caps-daily-budget` | `<input>` | [`frontend/index.html#L957`](/frontend/index.html#L957) |
| `#caps-max-orders` | `<input>` | [`frontend/index.html#L961`](/frontend/index.html#L961) |
| `#btn-save-caps` | `<button>` | [`frontend/index.html#L966`](/frontend/index.html#L966) |
| `#caps-save-status` | `<span>` | [`frontend/index.html#L969`](/frontend/index.html#L969) |
| `#hermes-brain-card` | `<article>` | [`frontend/index.html#L975`](/frontend/index.html#L975) |
| `#brain-primary-model` | `<strong>` | [`frontend/index.html#L987`](/frontend/index.html#L987) |
| `#brain-primary-provider` | `<span>` | [`frontend/index.html#L988`](/frontend/index.html#L988) |
| `#brain-profile-tag` | `<span>` | [`frontend/index.html#L988`](/frontend/index.html#L988) |
| `#brain-primary-status` | `<span>` | [`frontend/index.html#L990`](/frontend/index.html#L990) |
| `#brain-fallbacks-list` | `<div>` | [`frontend/index.html#L997`](/frontend/index.html#L997) |
| `#brain-fallbacks-empty` | `<div>` | [`frontend/index.html#L998`](/frontend/index.html#L998) |
| `#brain-last-turn-provider` | `<strong>` | [`frontend/index.html#L1009`](/frontend/index.html#L1009) |
| `#brain-last-turn-model` | `<span>` | [`frontend/index.html#L1010`](/frontend/index.html#L1010) |
| `#brain-last-turn-time` | `<span>` | [`frontend/index.html#L1012`](/frontend/index.html#L1012) |
| `#advanced-settings-card` | `<details>` | [`frontend/index.html#L1022`](/frontend/index.html#L1022) |
| `#api-keys-card` | `<div>` | [`frontend/index.html#L1033`](/frontend/index.html#L1033) |
| `#api-keys-form` | `<form>` | [`frontend/index.html#L1039`](/frontend/index.html#L1039) |
| `#key-telegram-token` | `<input>` | [`frontend/index.html#L1044`](/frontend/index.html#L1044) |
| `#key-telegram-chat` | `<input>` | [`frontend/index.html#L1051`](/frontend/index.html#L1051) |
| `#btn-save-api-keys` | `<button>` | [`frontend/index.html#L1055`](/frontend/index.html#L1055) |
| `#keys-save-status` | `<span>` | [`frontend/index.html#L1058`](/frontend/index.html#L1058) |
| `#fees-card` | `<div>` | [`frontend/index.html#L1064`](/frontend/index.html#L1064) |
| `#bridge-ctrl-card` | `<div>` | [`frontend/index.html#L1080`](/frontend/index.html#L1080) |
| `#adp-mode-text` | `<strong>` | [`frontend/index.html#L1087`](/frontend/index.html#L1087) |
| `#sse-status-badge` | `<span>` | [`frontend/index.html#L1093`](/frontend/index.html#L1093) |
| `#live-dot` | `<span>` | [`frontend/index.html#L1093`](/frontend/index.html#L1093) |
| `#source-badge` | `<span>` | [`frontend/index.html#L1094`](/frontend/index.html#L1094) |
| `#token-button` | `<button>` | [`frontend/index.html#L1095`](/frontend/index.html#L1095) |
| `#overview` | `<div>` | [`frontend/index.html#L1106`](/frontend/index.html#L1106) |
| `#demo-date` | `<div>` | [`frontend/index.html#L1107`](/frontend/index.html#L1107) |
| `#engine-state` | `<div>` | [`frontend/index.html#L1108`](/frontend/index.html#L1108) |
| `#snapshot-label` | `<div>` | [`frontend/index.html#L1109`](/frontend/index.html#L1109) |
| `#overview-sys-link` | `<a>` | [`frontend/index.html#L1110`](/frontend/index.html#L1110) |
| `#overview-sys-dot` | `<span>` | [`frontend/index.html#L1110`](/frontend/index.html#L1110) |
| `#overview-sys-text` | `<span>` | [`frontend/index.html#L1110`](/frontend/index.html#L1110) |
| `#scenario` | `<select>` | [`frontend/index.html#L1111`](/frontend/index.html#L1111) |
| `#next-session` | `<button>` | [`frontend/index.html#L1112`](/frontend/index.html#L1112) |
| `#metric-equity` | `<div>` | [`frontend/index.html#L1113`](/frontend/index.html#L1113) |
| `#metric-total-gain` | `<div>` | [`frontend/index.html#L1113`](/frontend/index.html#L1113) |
| `#metric-cash` | `<div>` | [`frontend/index.html#L1114`](/frontend/index.html#L1114) |
| `#metric-unsettled` | `<div>` | [`frontend/index.html#L1114`](/frontend/index.html#L1114) |
| `#metric-realized` | `<div>` | [`frontend/index.html#L1115`](/frontend/index.html#L1115) |
| `#metric-unrealized` | `<div>` | [`frontend/index.html#L1115`](/frontend/index.html#L1115) |
| `#equity-sparkline` | `<div>` | [`frontend/index.html#L1116`](/frontend/index.html#L1116) |
| `#mature-shares` | `<span>` | [`frontend/index.html#L1117`](/frontend/index.html#L1117) |
| `#locked-shares` | `<span>` | [`frontend/index.html#L1117`](/frontend/index.html#L1117) |
| `#quarantined-count` | `<span>` | [`frontend/index.html#L1117`](/frontend/index.html#L1117) |
| `#fees-paid` | `<span>` | [`frontend/index.html#L1117`](/frontend/index.html#L1117) |
| `#ledger-status` | `<span>` | [`frontend/index.html#L1117`](/frontend/index.html#L1117) |
| `#index-value` | `<div>` | [`frontend/index.html#L1118`](/frontend/index.html#L1118) |
| `#index-change` | `<div>` | [`frontend/index.html#L1118`](/frontend/index.html#L1118) |
| `#pulse-support-val` | `<div>` | [`frontend/index.html#L1119`](/frontend/index.html#L1119) |
| `#pulse-resistance-val` | `<div>` | [`frontend/index.html#L1119`](/frontend/index.html#L1119) |
| `#curve-sessions` | `<div>` | [`frontend/index.html#L1120`](/frontend/index.html#L1120) |
| `#main-chart` | `<div>` | [`frontend/index.html#L1121`](/frontend/index.html#L1121) |
| `#main-chart-tooltip` | `<div>` | [`frontend/index.html#L1121`](/frontend/index.html#L1121) |
| `#execution` | `<div>` | [`frontend/index.html#L1123`](/frontend/index.html#L1123) |
| `#inspector-symbol` | `<h2>` | [`frontend/index.html#L1124`](/frontend/index.html#L1124) |
| `#open-deep-trend` | `<button>` | [`frontend/index.html#L1124`](/frontend/index.html#L1124) |
| `#inspector-sector` | `<span>` | [`frontend/index.html#L1125`](/frontend/index.html#L1125) |
| `#inspector-basis` | `<strong>` | [`frontend/index.html#L1125`](/frontend/index.html#L1125) |
| `#inspector-pnl` | `<strong>` | [`frontend/index.html#L1125`](/frontend/index.html#L1125) |
| `#inspector-return` | `<strong>` | [`frontend/index.html#L1125`](/frontend/index.html#L1125) |
| `#inspector-reason` | `<p>` | [`frontend/index.html#L1126`](/frontend/index.html#L1126) |
| `#lots-body` | `<tbody>` | [`frontend/index.html#L1126`](/frontend/index.html#L1126) |
| `#hermes-sidebar` | `<aside>` | [`frontend/index.html#L1130`](/frontend/index.html#L1130) |
| `#hermes-resizer` | `<div>` | [`frontend/index.html#L1131`](/frontend/index.html#L1131) |
| `#hermes-collapse-btn` | `<button>` | [`frontend/index.html#L1138`](/frontend/index.html#L1138) |
| `#active-conv-title` | `<span>` | [`frontend/index.html#L1144`](/frontend/index.html#L1144) |
| `#tab-hermes-chat` | `<button>` | [`frontend/index.html#L1149`](/frontend/index.html#L1149) |
| `#tab-hermes-conversations` | `<button>` | [`frontend/index.html#L1150`](/frontend/index.html#L1150) |
| `#conversations-badge` | `<span>` | [`frontend/index.html#L1150`](/frontend/index.html#L1150) |
| `#tab-hermes-changes` | `<button>` | [`frontend/index.html#L1151`](/frontend/index.html#L1151) |
| `#changes-badge` | `<span>` | [`frontend/index.html#L1151`](/frontend/index.html#L1151) |
| `#tab-hermes-skills` | `<button>` | [`frontend/index.html#L1152`](/frontend/index.html#L1152) |
| `#skills-badge` | `<span>` | [`frontend/index.html#L1152`](/frontend/index.html#L1152) |
| `#pane-hermes-chat` | `<div>` | [`frontend/index.html#L1156`](/frontend/index.html#L1156) |
| `#chat-messages` | `<div>` | [`frontend/index.html#L1157`](/frontend/index.html#L1157) |
| `#hermes-welcome-message` | `<article>` | [`frontend/index.html#L1158`](/frontend/index.html#L1158) |
| `#chat-safety-note` | `<div>` | [`frontend/index.html#L1163`](/frontend/index.html#L1163) |
| `#welcome-chips-slot` | `<div>` | [`frontend/index.html#L1164`](/frontend/index.html#L1164) |
| `#bottom-chips-slot` | `<div>` | [`frontend/index.html#L1169`](/frontend/index.html#L1169) |
| `#chat-quick-prompts` | `<div>` | [`frontend/index.html#L1170`](/frontend/index.html#L1170) |
| `#chip-passive-sync-guide` | `<button>` | [`frontend/index.html#L1171`](/frontend/index.html#L1171) |
| `#hermes-model-trigger` | `<button>` | [`frontend/index.html#L1180`](/frontend/index.html#L1180) |
| `#provider-prefix-label` | `<span>` | [`frontend/index.html#L1181`](/frontend/index.html#L1181) |
| `#hermes-active-model-name` | `<strong>` | [`frontend/index.html#L1182`](/frontend/index.html#L1182) |
| `#model-dropup-menu` | `<div>` | [`frontend/index.html#L1185`](/frontend/index.html#L1185) |
| `#model-dropdown-list` | `<div>` | [`frontend/index.html#L1187`](/frontend/index.html#L1187) |
| `#chat-form` | `<form>` | [`frontend/index.html#L1193`](/frontend/index.html#L1193) |
| `#chat-input` | `<textarea>` | [`frontend/index.html#L1195`](/frontend/index.html#L1195) |
| `#chat-send` | `<button>` | [`frontend/index.html#L1198`](/frontend/index.html#L1198) |
| `#chat-footer-note` | `<p>` | [`frontend/index.html#L1203`](/frontend/index.html#L1203) |
| `#pane-hermes-conversations` | `<div>` | [`frontend/index.html#L1208`](/frontend/index.html#L1208) |
| `#new-conversation-btn` | `<button>` | [`frontend/index.html#L1210`](/frontend/index.html#L1210) |
| `#conversations-list` | `<div>` | [`frontend/index.html#L1215`](/frontend/index.html#L1215) |
| `#pane-hermes-changes` | `<div>` | [`frontend/index.html#L1221`](/frontend/index.html#L1221) |
| `#changes-badge-count` | `<span>` | [`frontend/index.html#L1225`](/frontend/index.html#L1225) |
| `#rollback-pane-btn` | `<button>` | [`frontend/index.html#L1228`](/frontend/index.html#L1228) |
| `#refresh-changes-btn` | `<button>` | [`frontend/index.html#L1231`](/frontend/index.html#L1231) |
| `#changes-diff-list` | `<div>` | [`frontend/index.html#L1235`](/frontend/index.html#L1235) |
| `#files-changed-list` | `<div>` | [`frontend/index.html#L1239`](/frontend/index.html#L1239) |
| `#changes-checkpoints-list` | `<div>` | [`frontend/index.html#L1240`](/frontend/index.html#L1240) |
| `#pane-hermes-skills` | `<div>` | [`frontend/index.html#L1244`](/frontend/index.html#L1244) |
| `#rollback-skills-btn` | `<button>` | [`frontend/index.html#L1247`](/frontend/index.html#L1247) |
| `#skills-list` | `<div>` | [`frontend/index.html#L1254`](/frontend/index.html#L1254) |
| `#btn-add-cron` | `<button>` | [`frontend/index.html#L1259`](/frontend/index.html#L1259) |
| `#crons-list` | `<div>` | [`frontend/index.html#L1261`](/frontend/index.html#L1261) |
| `#hermes-memory-preview` | `<div>` | [`frontend/index.html#L1267`](/frontend/index.html#L1267) |
| `#user-md-preview` | `<div>` | [`frontend/index.html#L1272`](/frontend/index.html#L1272) |
| `#memory-md-preview` | `<div>` | [`frontend/index.html#L1278`](/frontend/index.html#L1278) |
| `#durable-facts-list` | `<div>` | [`frontend/index.html#L1284`](/frontend/index.html#L1284) |
| `#checkpoints-list` | `<div>` | [`frontend/index.html#L1288`](/frontend/index.html#L1288) |
| `#floating-hermes-open` | `<button>` | [`frontend/index.html#L1295`](/frontend/index.html#L1295) |
| `#tx-confirm-order-modal` | `<dialog>` | [`frontend/index.html#L1302`](/frontend/index.html#L1302) |
| `#tx-confirm-banner` | `<div>` | [`frontend/index.html#L1304`](/frontend/index.html#L1304) |
| `#tx-confirm-banner-title` | `<h3>` | [`frontend/index.html#L1305`](/frontend/index.html#L1305) |
| `#tx-confirm-subtitle` | `<div>` | [`frontend/index.html#L1307`](/frontend/index.html#L1307) |
| `#tx-confirm-side` | `<strong>` | [`frontend/index.html#L1312`](/frontend/index.html#L1312) |
| `#tx-confirm-price` | `<strong>` | [`frontend/index.html#L1316`](/frontend/index.html#L1316) |
| `#tx-confirm-qty` | `<strong>` | [`frontend/index.html#L1317`](/frontend/index.html#L1317) |
| `#tx-confirm-fee` | `<strong>` | [`frontend/index.html#L1318`](/frontend/index.html#L1318) |
| `#tx-confirm-order-val` | `<strong>` | [`frontend/index.html#L1321`](/frontend/index.html#L1321) |
| `#tx-confirm-net-val` | `<strong>` | [`frontend/index.html#L1322`](/frontend/index.html#L1322) |
| `#tx-confirm-submit-btn` | `<button>` | [`frontend/index.html#L1326`](/frontend/index.html#L1326) |
| `#tx-confirm-cancel-btn` | `<button>` | [`frontend/index.html#L1327`](/frontend/index.html#L1327) |
| `#deep-trend-modal` | `<dialog>` | [`frontend/index.html#L1332`](/frontend/index.html#L1332) |
| `#modal-backdrop` | `<div>` | [`frontend/index.html#L1333`](/frontend/index.html#L1333) |
| `#modal-company-sector` | `<span>` | [`frontend/index.html#L1337`](/frontend/index.html#L1337) |
| `#modal-company-category` | `<span>` | [`frontend/index.html#L1337`](/frontend/index.html#L1337) |
| `#modal-company-title` | `<h2>` | [`frontend/index.html#L1338`](/frontend/index.html#L1338) |
| `#modal-company-sub` | `<span>` | [`frontend/index.html#L1338`](/frontend/index.html#L1338) |
| `#modal-price` | `<span>` | [`frontend/index.html#L1340`](/frontend/index.html#L1340) |
| `#modal-change` | `<span>` | [`frontend/index.html#L1341`](/frontend/index.html#L1341) |
| `#modal-signal-tag` | `<span>` | [`frontend/index.html#L1342`](/frontend/index.html#L1342) |
| `#deep-timeframe-tabs` | `<div>` | [`frontend/index.html#L1346`](/frontend/index.html#L1346) |
| `#modal-close-btn` | `<button>` | [`frontend/index.html#L1352`](/frontend/index.html#L1352) |
| `#deep-support-val` | `<strong>` | [`frontend/index.html#L1368`](/frontend/index.html#L1368) |
| `#deep-resistance-val` | `<strong>` | [`frontend/index.html#L1369`](/frontend/index.html#L1369) |
| `#deep-chart-container` | `<div>` | [`frontend/index.html#L1372`](/frontend/index.html#L1372) |
| `#deep-trend-chart-mount` | `<div>` | [`frontend/index.html#L1373`](/frontend/index.html#L1373) |
| `#deep-chart-tooltip` | `<div>` | [`frontend/index.html#L1374`](/frontend/index.html#L1374) |
| `#fundamentals-grid` | `<div>` | [`frontend/index.html#L1387`](/frontend/index.html#L1387) |
| `#fund-pe` | `<strong>` | [`frontend/index.html#L1388`](/frontend/index.html#L1388) |
| `#fund-eps` | `<strong>` | [`frontend/index.html#L1389`](/frontend/index.html#L1389) |
| `#fund-nav` | `<strong>` | [`frontend/index.html#L1390`](/frontend/index.html#L1390) |
| `#fund-mcap` | `<strong>` | [`frontend/index.html#L1391`](/frontend/index.html#L1391) |
| `#fund-div` | `<strong>` | [`frontend/index.html#L1392`](/frontend/index.html#L1392) |
| `#fund-paidup` | `<strong>` | [`frontend/index.html#L1393`](/frontend/index.html#L1393) |
| `#fund-52w` | `<strong>` | [`frontend/index.html#L1394`](/frontend/index.html#L1394) |
| `#fund-cat` | `<strong>` | [`frontend/index.html#L1395`](/frontend/index.html#L1395) |
| `#modal-sim-name` | `<span>` | [`frontend/index.html#L1405`](/frontend/index.html#L1405) |
| `#modal-sim-target-price` | `<strong>` | [`frontend/index.html#L1410`](/frontend/index.html#L1410) |
| `#modal-sim-target-pct` | `<span>` | [`frontend/index.html#L1411`](/frontend/index.html#L1411) |
| `#modal-sim-slider` | `<input>` | [`frontend/index.html#L1414`](/frontend/index.html#L1414) |
| `#modal-sim-gross` | `<strong>` | [`frontend/index.html#L1423`](/frontend/index.html#L1423) |
| `#modal-sim-fee` | `<strong>` | [`frontend/index.html#L1424`](/frontend/index.html#L1424) |
| `#modal-sim-net-pnl` | `<strong>` | [`frontend/index.html#L1425`](/frontend/index.html#L1425) |
| `#modal-sim-return-pct` | `<strong>` | [`frontend/index.html#L1426`](/frontend/index.html#L1426) |
| `#operator-modal` | `<dialog>` | [`frontend/index.html#L1435`](/frontend/index.html#L1435) |
| `#op-title` | `<h2>` | [`frontend/index.html#L1438`](/frontend/index.html#L1438) |
| `#op-close-btn` | `<button>` | [`frontend/index.html#L1439`](/frontend/index.html#L1439) |
| `#login-gate-overlay` | `<dialog>` | [`frontend/index.html#L1448`](/frontend/index.html#L1448) |
| `#login-title` | `<h2>` | [`frontend/index.html#L1452`](/frontend/index.html#L1452) |
| `#toast` | `<div>` | [`frontend/index.html#L1458`](/frontend/index.html#L1458) |


### 6.4 JavaScript Controllers & UI Functions (`frontend/app.js`, `charts.js`, `hermes_ui.js`)

Complete index of all **143** JavaScript controller and rendering functions:

| Function | Module File | Line | Role / Category |
| :--- | :--- | :--- | :--- |
| `$()` | [`frontend/app.js`](/frontend/app.js#L11) | `L11` | UI Controller |
| `formatTimestamp()` | [`frontend/app.js`](/frontend/app.js#L18) | `L18` | Formatter / Utility |
| `element()` | [`frontend/app.js`](/frontend/app.js#L60) | `L60` | UI Controller |
| `svgElement()` | [`frontend/app.js`](/frontend/app.js#L67) | `L67` | UI Controller |
| `currency()` | [`frontend/app.js`](/frontend/app.js#L73) | `L73` | UI Controller |
| `percentage()` | [`frontend/app.js`](/frontend/app.js#L80) | `L80` | UI Controller |
| `sessionDate()` | [`frontend/app.js`](/frontend/app.js#L85) | `L85` | UI Controller |
| `setText()` | [`frontend/app.js`](/frontend/app.js#L89) | `L89` | DOM Updater / State Sync |
| `setPnl()` | [`frontend/app.js`](/frontend/app.js#L94) | `L94` | DOM Updater / State Sync |
| `tone()` | [`frontend/app.js`](/frontend/app.js#L102) | `L102` | UI Controller |
| `badge()` | [`frontend/app.js`](/frontend/app.js#L112) | `L112` | UI Controller |
| `notify()` | [`frontend/app.js`](/frontend/app.js#L140) | `L140` | UI Controller |
| `showError()` | [`frontend/app.js`](/frontend/app.js#L159) | `L159` | UI Controller |
| `api()` | [`frontend/app.js`](/frontend/app.js#L166) | `L166` | API Client / Ingestion |
| `updateControls()` | [`frontend/app.js`](/frontend/app.js#L203) | `L203` | DOM Updater / State Sync |
| `refresh()` | [`frontend/app.js`](/frontend/app.js#L249) | `L249` | UI Controller |
| `mutate()` | [`frontend/app.js`](/frontend/app.js#L265) | `L265` | UI Controller |
| `isLiveSource()` | [`frontend/app.js`](/frontend/app.js#L274) | `L274` | UI Controller |
| `renderPortfolioHeaderBadge()` | [`frontend/app.js`](/frontend/app.js#L286) | `L286` | DOM Renderer |
| `renderSnapshot()` | [`frontend/app.js`](/frontend/app.js#L350) | `L350` | DOM Renderer |
| `renderEquitySparkline()` | [`frontend/app.js`](/frontend/app.js#L431) | `L431` | DOM Renderer |
| `renderActiveHoldings()` | [`frontend/app.js`](/frontend/app.js#L445) | `L445` | DOM Renderer |
| `renderBuckets()` | [`frontend/app.js`](/frontend/app.js#L644) | `L644` | DOM Renderer |
| `cell()` | [`frontend/app.js`](/frontend/app.js#L677) | `L677` | UI Controller |
| `selectCompany()` | [`frontend/app.js`](/frontend/app.js#L679) | `L679` | Event Handler / State Transition |
| `formatCompactNumber()` | [`frontend/app.js`](/frontend/app.js#L686) | `L686` | Formatter / Utility |
| `renderWatchlist()` | [`frontend/app.js`](/frontend/app.js#L694) | `L694` | DOM Renderer |
| `renderCanaryTheses()` | [`frontend/app.js`](/frontend/app.js#L1022) | `L1022` | DOM Renderer |
| `renderInspector()` | [`frontend/app.js`](/frontend/app.js#L1056) | `L1056` | DOM Renderer |
| `isBuyDecision()` | [`frontend/app.js`](/frontend/app.js#L1095) | `L1095` | UI Controller |
| `isSellDecision()` | [`frontend/app.js`](/frontend/app.js#L1101) | `L1101` | UI Controller |
| `isLockDecision()` | [`frontend/app.js`](/frontend/app.js#L1107) | `L1107` | UI Controller |
| `isBlockedDecision()` | [`frontend/app.js`](/frontend/app.js#L1124) | `L1124` | UI Controller |
| `renderDecisions()` | [`frontend/app.js`](/frontend/app.js#L1147) | `L1147` | DOM Renderer |
| `renderLedger()` | [`frontend/app.js`](/frontend/app.js#L1235) | `L1235` | DOM Renderer |
| `initMarketMapResizeObserver()` | [`frontend/app.js`](/frontend/app.js#L1425) | `L1425` | UI Controller |
| `initTheme()` | [`frontend/app.js`](/frontend/app.js#L1451) | `L1451` | UI Controller |
| `setTheme()` | [`frontend/app.js`](/frontend/app.js#L1457) | `L1457` | DOM Updater / State Sync |
| `toggleTheme()` | [`frontend/app.js`](/frontend/app.js#L1468) | `L1468` | Event Handler / State Transition |
| `tickMarketClock()` | [`frontend/app.js`](/frontend/app.js#L1474) | `L1474` | UI Controller |
| `tickClock()` | [`frontend/app.js`](/frontend/app.js#L1556) | `L1556` | UI Controller |
| `renderAutomationControlBar()` | [`frontend/app.js`](/frontend/app.js#L1565) | `L1565` | DOM Renderer |
| `setAutomationConfig()` | [`frontend/app.js`](/frontend/app.js#L1906) | `L1906` | DOM Updater / State Sync |
| `setHandoffPendingState()` | [`frontend/app.js`](/frontend/app.js#L2029) | `L2029` | DOM Updater / State Sync |
| `executeRunModeHandoff()` | [`frontend/app.js`](/frontend/app.js#L2047) | `L2047` | UI Controller |
| `executeHandoff()` | [`frontend/app.js`](/frontend/app.js#L2072) | `L2072` | UI Controller |
| `switchToLiveHours()` | [`frontend/app.js`](/frontend/app.js#L2173) | `L2173` | Event Handler / State Transition |
| `switchToTestMode()` | [`frontend/app.js`](/frontend/app.js#L2182) | `L2182` | Event Handler / State Transition |
| `initRealtimeStream()` | [`frontend/app.js`](/frontend/app.js#L2234) | `L2234` | UI Controller |
| `switchView()` | [`frontend/app.js`](/frontend/app.js#L2260) | `L2260` | Event Handler / State Transition |
| `initViewRouter()` | [`frontend/app.js`](/frontend/app.js#L2318) | `L2318` | UI Controller |
| `initScrollSpy()` | [`frontend/app.js`](/frontend/app.js#L2355) | `L2355` | UI Controller |
| `updateActiveNav()` | [`frontend/app.js`](/frontend/app.js#L2368) | `L2368` | DOM Updater / State Sync |
| `smoothCurvePath()` | [`frontend/charts.js`](/frontend/charts.js#L8) | `L8` | Canvas / Chart Geometry |
| `getBezierPointAtContinuousIndex()` | [`frontend/charts.js`](/frontend/charts.js#L31) | `L31` | Canvas / Chart Geometry |
| `renderMainChart()` | [`frontend/charts.js`](/frontend/charts.js#L63) | `L63` | DOM Renderer |
| `x()` | [`frontend/charts.js`](/frontend/charts.js#L95) | `L95` | UI Controller |
| `y()` | [`frontend/charts.js`](/frontend/charts.js#L96) | `L96` | UI Controller |
| `sparkline()` | [`frontend/charts.js`](/frontend/charts.js#L352) | `L352` | Canvas / Chart Geometry |
| `squarify()` | [`frontend/charts.js`](/frontend/charts.js#L368) | `L368` | Canvas / Chart Geometry |
| `layoutRow()` | [`frontend/charts.js`](/frontend/charts.js#L378) | `L378` | UI Controller |
| `worst()` | [`frontend/charts.js`](/frontend/charts.js#L425) | `L425` | UI Controller |
| `showTreemapTooltip()` | [`frontend/charts.js`](/frontend/charts.js#L462) | `L462` | Canvas / Chart Geometry |
| `hideTreemapTooltip()` | [`frontend/charts.js`](/frontend/charts.js#L475) | `L475` | Canvas / Chart Geometry |
| `renderMarketMap()` | [`frontend/charts.js`](/frontend/charts.js#L480) | `L480` | DOM Renderer |
| `renderTopSectorsChart()` | [`frontend/charts.js`](/frontend/charts.js#L659) | `L659` | DOM Renderer |
| `renderGainerChart()` | [`frontend/charts.js`](/frontend/charts.js#L819) | `L819` | DOM Renderer |
| `updateWhatIfSimulator()` | [`frontend/charts.js`](/frontend/charts.js#L824) | `L824` | DOM Updater / State Sync |
| `updateModalSimulator()` | [`frontend/charts.js`](/frontend/charts.js#L868) | `L868` | DOM Updater / State Sync |
| `openDeepTrendModal()` | [`frontend/charts.js`](/frontend/charts.js#L907) | `L907` | UI Controller |
| `closeDeepTrendModal()` | [`frontend/charts.js`](/frontend/charts.js#L1016) | `L1016` | UI Controller |
| `renderDeepTrendChart()` | [`frontend/charts.js`](/frontend/charts.js#L1026) | `L1026` | DOM Renderer |
| `x()` | [`frontend/charts.js`](/frontend/charts.js#L1054) | `L1054` | UI Controller |
| `y()` | [`frontend/charts.js`](/frontend/charts.js#L1055) | `L1055` | UI Controller |
| `initCharts()` | [`frontend/charts.js`](/frontend/charts.js#L1310) | `L1310` | Canvas / Chart Geometry |
| `renderHermesSkills()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L8) | `L8` | DOM Renderer |
| `createCard()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L23) | `L23` | UI Controller |
| `loadHermesOSState()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L79) | `L79` | API Client / Ingestion |
| `renderSkillCardHtml()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L117) | `L117` | DOM Renderer |
| `renderHermesBrainCard()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L180) | `L180` | DOM Renderer |
| `renderHermesCronJobs()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L230) | `L230` | DOM Renderer |
| `formatChatMarkdown()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L298) | `L298` | Formatter / Utility |
| `syncQuickPromptsPlacement()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L339) | `L339` | Event Handler / State Transition |
| `addMessage()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L359) | `L359` | Hermes Copilot / Chat UI |
| `isOrderPreview()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L380) | `L380` | Hermes Copilot / Chat UI |
| `renderOrderPreviewCard()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L390) | `L390` | DOM Renderer |
| `sendChat()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L609) | `L609` | Hermes Copilot / Chat UI |
| `initHermesSidebar()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L844) | `L844` | Hermes Copilot / Chat UI |
| `applyWidth()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L852) | `L852` | UI Controller |
| `onMouseMove()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L886) | `L886` | UI Controller |
| `onMouseUp()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L892) | `L892` | UI Controller |
| `loadConversations()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L989) | `L989` | API Client / Ingestion |
| `switchConversation()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L1023) | `L1023` | Event Handler / State Transition |
| `createNewConversation()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L1052) | `L1052` | UI Controller |
| `formatRelativeTime()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L1079) | `L1079` | Formatter / Utility |
| `escapeHtml()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L1093) | `L1093` | UI Controller |
| `executeRollback()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L1103) | `L1103` | UI Controller |
| `loadHermesModels()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L1154) | `L1154` | API Client / Ingestion |
| `switchHermesModel()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L1193) | `L1193` | Hermes Copilot / Chat UI |
| `loadRiskCapsSettings()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L1217) | `L1217` | API Client / Ingestion |
| `saveRiskCapsSettings()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L1251) | `L1251` | DOM Updater / State Sync |
| `loadApiKeysSettings()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L1318) | `L1318` | API Client / Ingestion |
| `saveApiKeysSettings()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L1343) | `L1343` | API Client / Ingestion |
| `checkAuthSession()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L1382) | `L1382` | UI Controller |
| `openOperatorProfile()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L1400) | `L1400` | UI Controller |
| `closeOperatorProfile()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L1405) | `L1405` | UI Controller |
| `handleOperatorLogin()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L1410) | `L1410` | Event Handler / State Transition |
| `handleOperatorLogout()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L1439) | `L1439` | Event Handler / State Transition |
| `markKeysDirty()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L1449) | `L1449` | UI Controller |
| `initAuthAndSettings()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L1459) | `L1459` | DOM Updater / State Sync |
| `loadSystemChanges()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L1557) | `L1557` | API Client / Ingestion |
| `initHermesChatListeners()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L1646) | `L1646` | Hermes Copilot / Chat UI |
| `setStockNowBusy()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L1692) | `L1692` | DOM Updater / State Sync |
| `updateSourceBadgeToLive()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L1697) | `L1697` | DOM Updater / State Sync |
| `runBridgeAction()` | [`frontend/hermes_ui.js`](/frontend/hermes_ui.js#L1705) | `L1705` | UI Controller |
| `toTradeXpressSymbol()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L24) | `L24` | UI Controller |
| `cleanSymbol()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L30) | `L30` | UI Controller |
| `calcBrokerFee()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L35) | `L35` | UI Controller |
| `formatMoney()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L41) | `L41` | Formatter / Utility |
| `formatPct()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L46) | `L46` | Formatter / Utility |
| `switchNavView()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L53) | `L53` | Event Handler / State Transition |
| `switchMonPane()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L96) | `L96` | Event Handler / State Transition |
| `updateOrderTicketCalculations()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L120) | `L120` | DOM Updater / State Sync |
| `selectSymbolForTicket()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L148) | `L148` | Event Handler / State Transition |
| `setOrderSide()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L223) | `L223` | DOM Updater / State Sync |
| `quickSell()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L235) | `L235` | UI Controller |
| `renderMarketDepthTable()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L251) | `L251` | DOM Renderer |
| `submitOrderPreview()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L291) | `L291` | Hermes Copilot / Chat UI |
| `openConfirmModal()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L330) | `L330` | UI Controller |
| `executeConfirmedOrder()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L366) | `L366` | UI Controller |
| `loadOrders()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L411) | `L411` | API Client / Ingestion |
| `renderOrdersTable()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L423) | `L423` | DOM Renderer |
| `cancelOrder()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L465) | `L465` | UI Controller |
| `loadLearningSummary()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L484) | `L484` | API Client / Ingestion |
| `renderLearningView()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L496) | `L496` | DOM Renderer |
| `loadFeedStatus()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L534) | `L534` | API Client / Ingestion |
| `controlBridge()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L546) | `L546` | UI Controller |
| `renderFeedStatusCard()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L565) | `L565` | DOM Renderer |
| `renderAccountDonut()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L645) | `L645` | DOM Renderer |
| `updateFromSnapshot()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L691) | `L691` | DOM Updater / State Sync |
| `setText()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L740) | `L740` | DOM Updater / State Sync |
| `showToast()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L745) | `L745` | UI Controller |
| `init()` | [`frontend/tradexpress_ui.js`](/frontend/tradexpress_ui.js#L763) | `L763` | UI Controller |


### 6.5 Hermes Agent Plugin Tool Registry (`plugins/humming_bird/tools.py`)

Complete catalog of all **24** registered Hermes tools powering chat commands and UI interactions:

| Tool Name | Category | Line Range | Purpose / Description |
| :--- | :--- | :--- | :--- |
| `hb_portfolio` | Read Tool | [`plugins/humming_bird/tools.py#L90`](/plugins/humming_bird/tools.py#L90-L124) | Fetch current portfolio state from kernel API. |
| `hb_watchlist` | Read Tool | [`plugins/humming_bird/tools.py#L127`](/plugins/humming_bird/tools.py#L127-L133) | Fetch watchlist filtered optionally by tier from kernel API. |
| `hb_inspect_curve` | Read Tool | [`plugins/humming_bird/tools.py#L136`](/plugins/humming_bird/tools.py#L136-L144) | Inspect price curve and support/resistance analysis for a symbol. |
| `hb_market_open` | Read Tool | [`plugins/humming_bird/tools.py#L147`](/plugins/humming_bird/tools.py#L147-L149) | Check if DSE market is currently open. |
| `hb_canaries` | Read Tool | [`plugins/humming_bird/tools.py#L152`](/plugins/humming_bird/tools.py#L152-L154) | Retrieve active canary theses from kernel API. |
| `hb_lots` | Read Tool | [`plugins/humming_bird/tools.py#L157`](/plugins/humming_bird/tools.py#L157-L163) | Fetch tax lots and T+2 maturity status. |
| `hb_set_tier` | Write / Order Tool | [`plugins/humming_bird/tools.py#L168`](/plugins/humming_bird/tools.py#L168-L179) | Set watchlist tier for a company. |
| `hb_set_allocation` | Write / Order Tool | [`plugins/humming_bird/tools.py#L182`](/plugins/humming_bird/tools.py#L182-L205) | Set buy allocation percentage for a symbol. |
| `hb_quarantine_canary` | Write / Order Tool | [`plugins/humming_bird/tools.py#L208`](/plugins/humming_bird/tools.py#L208-L221) | Trigger emergency crash quarantine (90% liquidation, 10% canary probe). |
| `hb_restore_quarantine` | Write / Order Tool | [`plugins/humming_bird/tools.py#L224`](/plugins/humming_bird/tools.py#L224-L237) | Restore a company from crash quarantine back into active status. |
| `hb_sync` | Broker Session & Sync Tool | [`plugins/humming_bird/tools.py#L240`](/plugins/humming_bird/tools.py#L240-L248) | Trigger sync with StockNow market data. |
| `hb_place_order` | Write / Order Tool | [`plugins/humming_bird/tools.py#L257`](/plugins/humming_bird/tools.py#L257-L336) | Submit virtual BUY or SELL order enforcing constraints and authorization. |
| `hb_rollback_last` | Write / Order Tool | [`plugins/humming_bird/tools.py#L339`](/plugins/humming_bird/tools.py#L339-L341) | Roll back the last state checkpoint atomically. |
| `hb_automation_get` | Engine / Automation Tool | [`plugins/humming_bird/tools.py#L344`](/plugins/humming_bird/tools.py#L344-L346) | Fetch current automation settings from the trading kernel. |
| `hb_automation_set` | Engine / Automation Tool | [`plugins/humming_bird/tools.py#L349`](/plugins/humming_bird/tools.py#L349-L378) | Configure trading automation switches, ingestion mode, or polling cadence. |
| `hb_scheduler` | Engine / Automation Tool | [`plugins/humming_bird/tools.py#L381`](/plugins/humming_bird/tools.py#L381-L390) | Control or inspect the market scheduler background loop. |
| `hb_run_cycle` | Engine / Automation Tool | [`plugins/humming_bird/tools.py#L393`](/plugins/humming_bird/tools.py#L393-L406) | Trigger an immediate AutoTrader cycle. |
| `hb_stocknow_session` | Broker Session & Sync Tool | [`plugins/humming_bird/tools.py#L409`](/plugins/humming_bird/tools.py#L409-L422) | Manage live Playwright session for StockNow integration. |
| `hb_mode_get` | Mode & Risk Caps Tool | [`plugins/humming_bird/tools.py#L425`](/plugins/humming_bird/tools.py#L425-L427) | Get active trading mode from kernel. |
| `hb_mode_set` | Mode & Risk Caps Tool | [`plugins/humming_bird/tools.py#L430`](/plugins/humming_bird/tools.py#L430-L446) | Set trading mode in kernel (TEST_OFFHOURS or LIVE_HOURS). |
| `hb_caps_get` | Mode & Risk Caps Tool | [`plugins/humming_bird/tools.py#L449`](/plugins/humming_bird/tools.py#L449-L451) | Get active risk caps and daily limits from kernel. |
| `hb_caps_set` | Mode & Risk Caps Tool | [`plugins/humming_bird/tools.py#L454`](/plugins/humming_bird/tools.py#L454-L491) | Set or lower risk limits in kernel. Raising a limit requires confirm=true. |
| `hb_feed_status` | Read Tool | [`plugins/humming_bird/tools.py#L494`](/plugins/humming_bird/tools.py#L494-L496) | Check TradeXpress passive feed freshness and get step-by-step operator tab guidance. |
| `hb_learning_review` | Read Tool | [`plugins/humming_bird/tools.py#L499`](/plugins/humming_bird/tools.py#L499-L511) | Review trade learning logs, win rates by tier (L1 vs L2), slippage, and post-market reflection metrics. |


### 6.6 Frontend Stylesheets (`frontend/*.css`)

| Stylesheet File | Lines | Purpose |
| :--- | :--- | :--- |
| `styles.css` | 7714 | Core design tokens, layout & widgets |
| `theme_light_hermes.css` | 3178 | Daylight overrides & Hermes IDE sidebar |


### 6.7 Frontend API Contract Invocations (`frontend/*.js`)

| Endpoint Invocated | Direction | Purpose |
| :--- | :--- | :--- |
| `/api/auth/login` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/auth/logout` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/auth/session` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/automation/config` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/automation/cycle` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/automation/handoff` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/automation/kill` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/automation/pause` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/caps` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/demo/advance` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/hermes/bridge/state` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/hermes/conversations` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/hermes/model` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/hermes/models` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/hermes/rollback` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/portfolio` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/settings/keys` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/stocknow/all-shares` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/stocknow/execute-order` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/stocknow/session` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/stocknow/sync-market` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/stocknow/sync-portfolio` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/system/changes` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/k/order` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |


### 6.8 Frontend DOM ↔ JS Binding & Orphan ID Health Audit

Automated verification of dynamic DOM queries (`$(...)` and `getElementById(...)`) against `frontend/index.html`:


- **Total JS Element Queries:** 286

- **Total HTML Declared IDs:** 434

- **Matched Dynamic Bindings:** 286 (100% resolution)

- **Orphan Critical IDs:** 0


| Status | Query ID | Queried In | Resolution |
| :--- | :--- | :--- | :--- |
| :white_check_mark: Clean | *All queried DOM elements exist in `index.html`* | `frontend/*.js` | Cleanly bound without null references |

---

## 7. Hermes Tool ↔ Kernel Route ↔ Skills Graph & Environment Variable Registry

### 7.1 Hermes Plugin Tool ↔ Kernel Endpoint ↔ Skills Matrix (`plugins/humming_bird/tools.py`)

Mapping all **24** Hermes agent tools to their deterministic kernel API endpoints and procedural skill references:


| Tool Name | Kernel Endpoint | Associated Skill | Skill Purpose | Tool Description |
| :--- | :--- | :--- | :--- | :--- |
| `hb_automation_get` | `/k/automation` | `tradexpress_passive_safety` | Automation & Polling Cadence | Fetch current automation settings from the trading kernel. |
| `hb_automation_set` | `/k/automation` | `tradexpress_passive_safety` | Master Automation Switch | Configure trading automation switches, ingestion mode, or polling cadence. |
| `hb_canaries` | `/k/canaries` | `canary_90_10` | Canary Theses & Solvency Monitoring | Retrieve active canary theses from kernel API. |
| `hb_caps_get` | `/k/caps` | `tradexpress_passive_safety` | Risk Caps & Daily Budget Inspection | Get active risk caps and daily limits from kernel. |
| `hb_caps_set` | `/k/caps` | `tradexpress_passive_safety` | Autonomous Lowering / Operator Raising | Set or lower risk limits in kernel. Raising a limit requires confirm=true. |
| `hb_feed_status` | `/k/feed-status` | `tradexpress_passive_safety` | Trading Operations | Check TradeXpress passive feed freshness and get step-by-step operator tab guidance. |
| `hb_inspect_curve` | *Internal / Engine* | `gsc_tiers` | 7-30 Session Curve Trend & Zones | Inspect price curve and support/resistance analysis for a symbol. |
| `hb_learning_review` | `/k/learning/summary` | `tradexpress_passive_safety` | Trading Operations | Review trade learning logs, win rates by tier (L1 vs L2), slippage, and post-market reflection metrics. |
| `hb_lots` | `/k/lots` | `sequential_no_regret` | 3-Bucket Rolling Lots & Runner Scaling | Fetch tax lots and T+2 maturity status. |
| `hb_market_open` | `/k/market-open` | `stocknow_dse_quirks` | DSE Schedule Gate (10:00–14:10) | Check if DSE market is currently open. |
| `hb_mode_get` | `/k/mode` | `tradexpress_passive_safety` | Trading Mode Inspection | Get active trading mode from kernel. |
| `hb_mode_set` | `/k/mode` | `tradexpress_passive_safety` | LIVE_HOURS vs TEST_OFFHOURS Toggle | Set trading mode in kernel (TEST_OFFHOURS or LIVE_HOURS). |
| `hb_place_order` | `/k/order` | `sequential_no_regret` | 2-Step Order Confirmation & Strict No-Loss | Submit virtual BUY or SELL order enforcing constraints and authorization. |
| `hb_portfolio` | `/k/portfolio` | `sequential_no_regret` | Portfolio Valuation & T+2 State | Fetch current portfolio state from kernel API. |
| `hb_quarantine_canary` | `/k/quarantine` | `canary_90_10` | 90/10 Emergency Split & Crash Quarantine | Trigger emergency crash quarantine (90% liquidation, 10% canary probe). |
| `hb_restore_quarantine` | `/k/quarantine` | `canary_90_10` | Quarantine Recovery & Re-listing | Restore a company from crash quarantine back into active status. |
| `hb_rollback_last` | `/k/rollback` | `sequential_no_regret` | Atomic State Rollback Checkpoint | Roll back the last state checkpoint atomically. |
| `hb_run_cycle` | `/k/cycle` | `stocknow_dse_quirks` | Deterministic AutoTrader Cycle | Trigger an immediate AutoTrader cycle. |
| `hb_scheduler` | `/k/scheduler` | `tradexpress_passive_safety` | Trading Operations | Control or inspect the market scheduler background loop. |
| `hb_set_allocation` | `/k/allocation` | `gsc_tiers` | Per-Symbol Capital Allocation % | Set buy allocation percentage for a symbol. |
| `hb_set_tier` | `/k/tier` | `gsc_tiers` | Watchlist Tier Allocation & Promotion | Set watchlist tier for a company. |
| `hb_stocknow_session` | `/k/stocknow/session` | `stocknow_dse_quirks` | Broker Session & Auth Status | Manage live Playwright session for StockNow integration. |
| `hb_sync` | `/k/sync` | `stocknow_dse_quirks` | Portfolio, Favorites & Market Sync | Trigger sync with StockNow market data. |
| `hb_watchlist` | `/k/watchlist` | `gsc_tiers` | GSC Master, L1 Turnaround, L2 Scalp Tiers | Fetch watchlist filtered optionally by tier from kernel API. |


### 7.2 Repository Environment Variables & Configuration Registry

Complete catalog of environment variables, default settings, and operational scopes across the system:


| Environment Variable | Default Value | Required | Operational Scope | Architectural Purpose |
| :--- | :--- | :--- | :--- | :--- |
| `KERNEL_TOKEN` | `(random uuid)` | Yes | Kernel API Auth | X-Kernel-Token secret protecting standalone trading kernel |
| `DATABASE_URL` | `sqlite:///backend/data/hummingbird.db` | No | Persistence | SQLite database path (WAL mode enforced) |
| `OPERATOR_USERNAME` | `hasib` | No | Cockpit Auth | Cockpit web dashboard operator username |
| `OPERATOR_PASSWORD` | `admin123` | No | Cockpit Auth | Cockpit web dashboard operator password |
| `COCKPIT_API_TOKEN` | `` | No | Cockpit Auth | Optional bearer token for external API invocations |
| `HERMES_GATEWAY_URL` | `http://127.0.0.1:8642` | No | Hermes Bridge | Nous Research Hermes Agent Gateway HTTP/SSE endpoint |
| `HERMES_PROFILE` | `hummingbird` | No | Hermes Bridge | Hermes profile name enforcing zero-secret tool isolation |
| `STOCKNOW_LIVE_PORTFOLIO_ID` | `164580` | No | StockNow Broker | LankaBangla Securities target portfolio identifier |
| `STOCKNOW_TEST_PORTFOLIO_ID` | `164580` | No | StockNow Broker | Test portfolio identifier for write safety validation |
| `STOCKNOW_USERNAME` | `` | Conditional | StockNow Broker | Operator phone/login for StockNow API re-auth |
| `STOCKNOW_PASSWORD` | `` | Conditional | StockNow Broker | Operator password for StockNow API re-auth |
| `TRADEXPRESS_CDP_URL` | `http://127.0.0.1:9222` | No | TradeXpress CDP | Chrome DevTools Protocol port for passive sniffing |
| `PRICE_MAX_DEVIATION_PCT` | `1.5` | No | Risk Caps | Maximum allowed price deviation % from LTP for sanity guard |
| `TELEGRAM_BOT_TOKEN` | `` | No | Alerts & Notifications | Telegram bot API token for push trade alerts and dead-man switch |
| `TELEGRAM_CHAT_ID` | `` | No | Alerts & Notifications | Telegram chat ID for trade notifications and daily summaries |


### 7.3 Code Health & Complexity Radar

Functions requiring architectural attention (> 70 lines or nesting depth >= 4):


| File | Function / Method | Length (Lines) | Max Nesting Depth | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| `backend/adapters/base.py` | `validate_tradexpress_order_safety` | 93 | 4 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_adapter.py` | `quote` | 18 | 4 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_api.py` | `login` | 62 | 4 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_api.py` | `_request` | 113 | 5 | Decompose into sub-functions |
| `backend/adapters/stocknow_api.py` | `_check_ledger_for_trade` | 40 | 4 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_client.py` | `_launch_internal` | 82 | 6 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_client.py` | `_ensure_authenticated_internal` | 189 | 7 | Decompose into sub-functions |
| `backend/adapters/stocknow_client.py` | `_discover_portfolio_internal` | 66 | 5 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_executor.py` | `match_ledger_entry` | 58 | 4 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_executor.py` | `notify_order_failure` | 88 | 4 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_executor.py` | `execute_order` | 116 | 3 | Decompose into sub-functions |
| `backend/adapters/stocknow_executor.py` | `_ensure_dialog_handler` | 28 | 5 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_executor.py` | `_on_dialog` | 19 | 4 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_executor.py` | `execute_order` | 153 | 3 | Decompose into sub-functions |
| `backend/adapters/stocknow_market_sync.py` | `_normalize_history_series` | 16 | 6 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_market_sync.py` | `extract_quotes_from_payload` | 88 | 6 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_market_sync.py` | `fetch_stocknow_live_market_data` | 278 | 6 | Decompose into sub-functions |
| `backend/adapters/stocknow_market_sync.py` | `fetch_sym_history` | 52 | 4 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_market_sync.py` | `_extract_quotes_from_stocknow_impl` | 163 | 5 | Decompose into sub-functions |
| `backend/adapters/stocknow_market_sync.py` | `_sync_in_session` | 103 | 5 | Decompose into sub-functions |
| `backend/adapters/stocknow_portfolio_sync.py` | `_find_portfolio_dict` | 17 | 5 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_portfolio_sync.py` | `extract_hummingbird_portfolio` | 69 | 6 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_portfolio_sync.py` | `_extract_hummingbird_portfolio_from_browser_impl` | 123 | 7 | Decompose into sub-functions |
| `backend/adapters/stocknow_portfolio_sync.py` | `_execute_reconciliation` | 170 | 3 | Decompose into sub-functions |
| `backend/adapters/stocknow_portfolio_sync.py` | `sync_stocknow_portfolio_via_api` | 77 | 5 | Acceptable; well-scoped logic |
| `backend/adapters/tradexpress/cdp_daemon.py` | `_run_loop` | 142 | 6 | Decompose into sub-functions |
| `backend/adapters/tradexpress/passive_feed.py` | `parse_ember_market_watch_rows` | 97 | 4 | Acceptable; well-scoped logic |
| `backend/adapters/tradexpress/passive_feed.py` | `get_feed_health_and_guidance` | 62 | 8 | Acceptable; well-scoped logic |
| `backend/adapters/tradexpress/passive_feed.py` | `ingest_passive_snapshot` | 210 | 7 | Decompose into sub-functions |
| `backend/adapters/tradexpress/passive_feed.py` | `get_quote` | 34 | 4 | Acceptable; well-scoped logic |
| `backend/adapters/tradexpress/shadow_simulator.py` | `submit_shadow_order` | 85 | 2 | Acceptable; well-scoped logic |
| `backend/adapters/tradexpress/shadow_simulator.py` | `_execute_shadow_order_in_session` | 239 | 6 | Decompose into sub-functions |
| `backend/adapters/tradexpress/shadow_simulator.py` | `_process_fill` | 270 | 5 | Decompose into sub-functions |
| `backend/adapters/tradexpress/shadow_simulator.py` | `reconcile_queued_orders` | 76 | 5 | Acceptable; well-scoped logic |
| `backend/config.py` | `get_allowed_portfolios` | 18 | 4 | Acceptable; well-scoped logic |
| `backend/config.py` | `get_active_target_portfolio` | 17 | 4 | Acceptable; well-scoped logic |
| `backend/database.py` | `create_schema` | 137 | 4 | Decompose into sub-functions |
| `backend/engine/agent_actions.py` | `emergency_quarantine_and_canary` | 112 | 5 | Decompose into sub-functions |
| `backend/engine/agent_actions.py` | `check_canary_theses` | 31 | 4 | Acceptable; well-scoped logic |
| `backend/engine/agent_actions.py` | `execute_agentic_buy` | 93 | 3 | Acceptable; well-scoped logic |
| `backend/engine/agent_actions.py` | `execute_agentic_sell` | 111 | 3 | Decompose into sub-functions |
| `backend/engine/auto_trader.py` | `_dispatch_order` | 72 | 6 | Acceptable; well-scoped logic |
| `backend/engine/auto_trader.py` | `_run_cycle_internal` | 695 | 7 | Decompose into sub-functions |
| `backend/engine/auto_trader.py` | `advance_demo` | 38 | 5 | Acceptable; well-scoped logic |
| `backend/engine/checkpoint.py` | `rollback_last` | 110 | 3 | Decompose into sub-functions |
| `backend/engine/circuit_breaker.py` | `record_circuit_failure` | 94 | 4 | Acceptable; well-scoped logic |
| `backend/engine/curve_analyzer.py` | `analyze_curve` | 84 | 3 | Acceptable; well-scoped logic |
| `backend/engine/heartbeat.py` | `check_dead_man_switch` | 56 | 4 | Acceptable; well-scoped logic |
| `backend/engine/heartbeat.py` | `send_daily_summary_if_due` | 112 | 4 | Decompose into sub-functions |
| `backend/engine/price_guard.py` | `get_market_quote` | 28 | 4 | Acceptable; well-scoped logic |
| `backend/engine/price_guard.py` | `check_price_sanity` | 59 | 5 | Acceptable; well-scoped logic |
| `backend/engine/scheduler.py` | `is_dse_market_open` | 54 | 5 | Acceptable; well-scoped logic |
| `backend/engine/scheduler.py` | `run_scheduled_tick` | 85 | 6 | Acceptable; well-scoped logic |
| `backend/engine/scheduler.py` | `_loop` | 21 | 4 | Acceptable; well-scoped logic |
| `backend/engine/sequential_seller.py` | `plan_sale` | 105 | 3 | Decompose into sub-functions |
| `backend/engine/t2_ledger.py` | `bucket_balances` | 46 | 4 | Acceptable; well-scoped logic |
| `backend/engine/t2_ledger.py` | `assert_ledger` | 21 | 4 | Acceptable; well-scoped logic |
| `backend/engine/telegram_bot.py` | `send_telegram_alert_sync` | 18 | 4 | Acceptable; well-scoped logic |
| `backend/engine/telegram_bot.py` | `handle_telegram_command` | 107 | 4 | Decompose into sub-functions |
| `backend/engine/telegram_bot.py` | `_poll_loop` | 35 | 6 | Acceptable; well-scoped logic |
| `backend/hermes_bridge.py` | `stream_hermes_chat` | 67 | 5 | Acceptable; well-scoped logic |
| `backend/hermes_bridge.py` | `read_hermes_state` | 166 | 6 | Decompose into sub-functions |
| `backend/hermes_bridge.py` | `_extract_skill_meta` | 18 | 5 | Acceptable; well-scoped logic |
| `backend/hermes_bridge.py` | `_get_bundled_skill_names` | 37 | 7 | Acceptable; well-scoped logic |
| `backend/kernel_api.py` | `post_quarantine` | 52 | 4 | Acceptable; well-scoped logic |
| `backend/kernel_api.py` | `post_sync` | 92 | 7 | Acceptable; well-scoped logic |
| `backend/kernel_api.py` | `_compute_order_reconcile_and_drift` | 61 | 4 | Acceptable; well-scoped logic |
| `backend/kernel_api.py` | `post_order` | 508 | 8 | Decompose into sub-functions |
| `backend/kernel_api.py` | `post_automation_config` | 81 | 4 | Acceptable; well-scoped logic |
| `backend/kernel_api.py` | `post_automation_handoff` | 53 | 6 | Acceptable; well-scoped logic |
| `backend/kernel_api.py` | `post_scheduler_control` | 51 | 5 | Acceptable; well-scoped logic |
| `backend/kernel_api.py` | `post_stocknow_session` | 76 | 6 | Acceptable; well-scoped logic |
| `backend/kernel_api.py` | `set_caps` | 88 | 4 | Acceptable; well-scoped logic |
| `backend/kernel_api.py` | `get_learning_summary` | 50 | 5 | Acceptable; well-scoped logic |
| `backend/logging_config.py` | `setup_logging` | 50 | 4 | Acceptable; well-scoped logic |
| `backend/logging_config.py` | `filter` | 12 | 4 | Acceptable; well-scoped logic |
| `backend/main.py` | `create_app` | 711 | 7 | Decompose into sub-functions |
| `backend/main.py` | `local_security` | 65 | 4 | Acceptable; well-scoped logic |
| `backend/main.py` | `cycle` | 38 | 6 | Acceptable; well-scoped logic |
| `backend/main.py` | `automation_handoff` | 55 | 7 | Acceptable; well-scoped logic |
| `backend/main.py` | `automation_config` | 89 | 5 | Acceptable; well-scoped logic |
| `backend/main.py` | `set_caps_public` | 86 | 4 | Acceptable; well-scoped logic |
| `backend/main.py` | `event_stream` | 26 | 4 | Acceptable; well-scoped logic |
| `backend/main.py` | `generator` | 13 | 4 | Acceptable; well-scoped logic |
| `backend/market_map.py` | `build_market_map_payload` | 72 | 5 | Acceptable; well-scoped logic |
| `backend/portfolio.py` | `snapshot_from_session` | 374 | 5 | Decompose into sub-functions |
| `backend/portfolio.py` | `normalized_watchlist` | 20 | 4 | Acceptable; well-scoped logic |
| `backend/routes_auth_settings.py` | `build_auth_settings_router` | 134 | 2 | Decompose into sub-functions |
| `backend/routes_hermes.py` | `build_hermes_router` | 175 | 5 | Decompose into sub-functions |
| `backend/routes_hermes.py` | `system_changes` | 73 | 5 | Acceptable; well-scoped logic |
| `backend/routes_hermes.py` | `switch_hermes_model` | 59 | 5 | Acceptable; well-scoped logic |
| `backend/routes_stocknow.py` | `build_stocknow_router` | 223 | 6 | Decompose into sub-functions |
| `backend/routes_stocknow.py` | `post_stocknow_session` | 57 | 6 | Acceptable; well-scoped logic |
| `backend/routes_stocknow.py` | `post_stocknow_scheduler` | 9 | 4 | Acceptable; well-scoped logic |
| `backend/routes_tradexpress.py` | `build_tradexpress_router` | 179 | 5 | Decompose into sub-functions |
| `backend/routes_tradexpress.py` | `post_bridge_control` | 18 | 4 | Acceptable; well-scoped logic |
| `backend/routes_tradexpress.py` | `get_learning_logs` | 46 | 5 | Acceptable; well-scoped logic |
| `backend/secret_guard.py` | `redact_secrets` | 11 | 4 | Acceptable; well-scoped logic |
| `backend/seed.py` | `seed_demo` | 105 | 3 | Decompose into sub-functions |
| `backend/seed.py` | `migrate_real_stocknow_market` | 148 | 7 | Decompose into sub-functions |
| `plugins/humming_bird/__init__.py` | `register` | 39 | 9 | Acceptable; well-scoped logic |
| `plugins/humming_bird/tools.py` | `hb_portfolio` | 35 | 4 | Acceptable; well-scoped logic |
| `plugins/humming_bird/tools.py` | `hb_place_order` | 80 | 3 | Acceptable; well-scoped logic |
| `scripts/backup_db.py` | `backup_database` | 53 | 4 | Acceptable; well-scoped logic |
| `scripts/backup_db.py` | `prune_backups` | 32 | 5 | Acceptable; well-scoped logic |
| `scripts/check_dse_market_open.py` | `check_kernel_market_open` | 19 | 4 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `discover_files` | 37 | 5 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `parse_fastapi_routes` | 39 | 10 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `parse_css_design` | 111 | 8 | Decompose into sub-functions |
| `scripts/generate_code_map.py` | `scan_file` | 50 | 8 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `parse_frontend` | 92 | 11 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `parse_plugin_tools` | 36 | 7 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `compute_blast_radius` | 30 | 6 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `parse_sqlalchemy_schema` | 44 | 9 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `parse_pydantic_contracts` | 35 | 8 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `parse_hermes_skills_graph` | 55 | 7 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `generate_markdown` | 286 | 6 | Decompose into sub-functions |
| `scripts/generate_code_map.py` | `visit_Call` | 10 | 4 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `_compute_depth` | 12 | 4 | Acceptable; well-scoped logic |
| `scripts/inspect_tradexpress_passive.py` | `run_passive_probe` | 264 | 4 | Decompose into sub-functions |
| `scripts/preflight.py` | `check_gateway` | 18 | 5 | Acceptable; well-scoped logic |
| `scripts/preflight.py` | `check_kernel_token` | 20 | 5 | Acceptable; well-scoped logic |
| `scripts/preflight.py` | `check_stocknow_session` | 69 | 5 | Acceptable; well-scoped logic |
| `scripts/preflight.py` | `check_portfolio_drift` | 34 | 4 | Acceptable; well-scoped logic |
| `scripts/preflight.py` | `check_trading_mode` | 23 | 4 | Acceptable; well-scoped logic |
| `scripts/restore_db.py` | `restore_database` | 88 | 4 | Acceptable; well-scoped logic |
| `scripts/verify_chat_card.py` | `main` | 121 | 3 | Decompose into sub-functions |


> **Knowledge Graph Summary:** 57 Python modules inspected, 67 FastAPI endpoints registered, 19 SQLAlchemy tables mapped, 30 Pydantic contracts indexed, 24 Hermes tools bound to skills, 143 JS functions mapped, 434 DOM IDs indexed, 104,013 total LOC indexed across 151 repository files.