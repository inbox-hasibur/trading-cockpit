# 🗺️ Codebase AST Map & System Architecture Radar

> Auto-generated via `scripts/generate_code_map.py` (Zero-dependency stdlib AST inspection) on **2026-11-10 03:50:01 UTC**.
> **Excluded Paths:** `vendor/`, `node_modules/`, `.venv/`, `venv/`, `.git/`, `__pycache__/`, `backend/data/`, `.pytest_cache/`, `dist/`, `build/`, `scratch/`
> **Pinned Vendor Commit (`vendor/hermes-agent`):** `b777adb7918713e5786cc9d95ad5b854074f2cb6`

---

## 1. Repository Topology & File Metrics

| Extension / Type | File Count | Total Lines of Code | Description |
| :--- | :--- | :--- | :--- |
| `.py` | 82 | 23,709 | Python Core Kernel, Engine, Tests & Plugins |
| `.css` | 2 | 9,568 | Custom Dark / Light / Terminal Design System |
| `.json` | 13 | 5,659 | Fixtures & Configuration |
| `.js` | 3 | 5,452 | Vanilla ES6+ Reactive Terminal Controller & UI |
| `.md` | 11 | 4,034 | Architecture & Strategy Documentation |
| `.html` | 1 | 1,103 | Single Page Application DOM Structure |
| `.ps1` | 2 | 199 | Windows PowerShell Automation |
| `.yaml` | 1 | 32 | Manifest & Plugin Configuration |
| `.toml` | 1 | 13 | PyProject Configuration |
| `.txt` | 2 | 11 | Dependency Specifications |
| `.sh` | 1 | 9 | Shell Scripts |
| `.bat` | 1 | 8 | Batch Launchers |
| *other* | 9 | 43,383 | Other Configuration, Assets & Dotfiles |
| **TOTAL** | **129** | **93,180** | *Entire Humming Bird Repository* |

## 2. Internal Dependency & Import Graph

Shows intra-repo module dependencies within `backend/`, `plugins/`, and `scripts/`:

| Module File | Imported Internal Dependencies |
| :--- | :--- |
| [`backend/__init__.py`](/backend/__init__.py) | *Independent Core Module* |
| [`backend/adapters/__init__.py`](/backend/adapters/__init__.py) | `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.adapters.stocknow_client.StockNowLiveClient`, `backend.adapters.stocknow_client.get_safe_profile_dir`, `backend.adapters.stocknow_market_sync.extract_quotes_from_payload`, `backend.adapters.stocknow_market_sync.extract_quotes_from_stocknow`, `backend.adapters.stocknow_market_sync.sync_live_market_to_db` |
| [`backend/adapters/stocknow_adapter.py`](/backend/adapters/stocknow_adapter.py) | `backend.adapters.stocknow_client.get_safe_profile_dir`, `backend.adapters.stocknow_executor.get_stocknow_executor`, `backend.database.CompanyProfile`, `backend.engine.money.ZERO`, `backend.engine.money.decimal` |
| [`backend/adapters/stocknow_api.py`](/backend/adapters/stocknow_api.py) | `backend.adapters.stocknow_write_guard.StockNowWriteGuardError`, `backend.adapters.stocknow_write_guard.verify_test_portfolio_post_guard` |
| [`backend/adapters/stocknow_client.py`](/backend/adapters/stocknow_client.py) | `backend.secret_guard.SecretGuard`, `backend.secret_guard.redact_secrets` |
| [`backend/adapters/stocknow_executor.py`](/backend/adapters/stocknow_executor.py) | `backend.adapters.stocknow_api.NotAuthenticatedError`, `backend.adapters.stocknow_api.RateLimitedError`, `backend.adapters.stocknow_api.SchemaChangedError`, `backend.adapters.stocknow_api.StockNowAPI`, `backend.adapters.stocknow_write_guard.StockNowWriteGuardError`, `backend.adapters.stocknow_write_guard.verify_test_portfolio_post_guard`, `backend.database.DecisionLog`, `backend.database.KernelAuditLog` |
| [`backend/adapters/stocknow_market_sync.py`](/backend/adapters/stocknow_market_sync.py) | `backend.adapters.stocknow_api.StockNowAPI`, `backend.adapters.stocknow_client.StockNowLiveClient`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.portfolio_state`, `backend.engine.money.ZERO`, `backend.engine.money.decimal`, `backend.portfolio.COMPANY_FUNDAMENTALS`, `backend.portfolio.DEFAULT_FUNDAMENTALS` |
| [`backend/adapters/stocknow_portfolio_sync.py`](/backend/adapters/stocknow_portfolio_sync.py) | `backend.adapters.stocknow_api.SchemaChangedError`, `backend.adapters.stocknow_api.StockNowAPI`, `backend.adapters.stocknow_client.StockNowLiveClient`, `backend.config.Settings`, `backend.config.get_allowed_portfolios`, `backend.config.get_portfolio_name`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.DecisionLog`, `backend.database.PortfolioState`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.engine.checkpoint.CheckpointManager`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.price`, `backend.engine.money.purchase_amount`, `backend.engine.t2_ledger.BUCKETS`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.assert_ledger`, `backend.engine.t2_ledger.bucket_balances` |
| [`backend/adapters/stocknow_write_guard.py`](/backend/adapters/stocknow_write_guard.py) | `backend.config.test_portfolio_configured` |
| [`backend/config.py`](/backend/config.py) | *Independent Core Module* |
| [`backend/database.py`](/backend/database.py) | `backend.config.utc_now_iso` |
| [`backend/engine/__init__.py`](/backend/engine/__init__.py) | *Independent Core Module* |
| [`backend/engine/agent_actions.py`](/backend/engine/agent_actions.py) | `backend.config.Settings`, `backend.config.get_active_target_portfolio`, `backend.database.CanaryThesis`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.DecisionLog`, `backend.database.PortfolioState`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.engine.money.ZERO`, `backend.engine.money.allocated_basis`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.price`, `backend.engine.money.purchase_amount`, `backend.engine.money.sale_amount`, `backend.engine.money.whole_shares`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.assert_ledger`, `backend.engine.t2_ledger.bucket_balances` |
| [`backend/engine/auto_trader.py`](/backend/engine/auto_trader.py) | `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.config.Settings`, `backend.config.get_active_target_portfolio`, `backend.config.get_allowed_portfolios`, `backend.database.AutomationCycle`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.CycleRequestKey`, `backend.database.Database`, `backend.database.DecisionLog`, `backend.database.OrderIdempotencyKey`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.database.portfolio_state`, `backend.engine.agent_actions.check_canary_theses`, `backend.engine.circuit_breaker.record_circuit_failure`, `backend.engine.circuit_breaker.record_circuit_success`, `backend.engine.money.HUNDRED`, `backend.engine.money.ZERO`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.price`, `backend.engine.money.purchase_amount`, `backend.engine.money.whole_shares`, `backend.engine.scheduler.is_dse_market_open`, `backend.engine.sequential_seller.SellState`, `backend.engine.sequential_seller.plan_sale`, `backend.engine.signals.BLOCK_ALL_TRADING`, `backend.engine.signals.assess_company`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.assert_ledger`, `backend.engine.t2_ledger.bucket_balances`, `backend.engine.trading_lock.acquire_trading_lock` |
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
| [`backend/kernel_api.py`](/backend/kernel_api.py) | `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.adapters.stocknow_api.StockNowError`, `backend.adapters.stocknow_executor.NoReceiptExecutionError`, `backend.adapters.stocknow_executor.StockNowExecutionError`, `backend.adapters.stocknow_executor.notify_order_failure`, `backend.adapters.stocknow_market_sync.extract_quotes_from_stocknow`, `backend.adapters.stocknow_market_sync.fetch_stocknow_live_market_data`, `backend.adapters.stocknow_market_sync.get_or_fetch_all_dse_shares`, `backend.adapters.stocknow_market_sync.sync_live_market_to_db`, `backend.adapters.stocknow_portfolio_sync.extract_hummingbird_portfolio`, `backend.adapters.stocknow_portfolio_sync.reconcile_portfolio_to_db`, `backend.adapters.stocknow_portfolio_sync.sync_stocknow_portfolio_via_api`, `backend.config.Settings`, `backend.config.get_active_target_portfolio`, `backend.config.get_allowed_portfolios`, `backend.config.get_portfolio_name`, `backend.config.test_portfolio_configured`, `backend.database.CanaryThesis`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.DecisionLog`, `backend.database.KernelAuditLog`, `backend.database.OrderIdempotencyKey`, `backend.database.PortfolioState`, `backend.database.RuleAudit`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.database.portfolio_state`, `backend.engine.agent_actions.check_canary_theses`, `backend.engine.agent_actions.emergency_quarantine_and_canary`, `backend.engine.agent_actions.execute_agentic_buy`, `backend.engine.agent_actions.execute_agentic_sell`, `backend.engine.agent_actions.restore_quarantine`, `backend.engine.auto_trader.AutoTrader`, `backend.engine.checkpoint.CheckpointManager`, `backend.engine.circuit_breaker.reset_circuit_breaker`, `backend.engine.curve_analyzer.analyze_curve`, `backend.engine.money.ZERO`, `backend.engine.money.allocated_basis`, `backend.engine.money.purchase_amount`, `backend.engine.money.sale_amount`, `backend.engine.preflight_service.are_caps_set`, `backend.engine.preflight_service.has_passing_preflight_within_24h`, `backend.engine.preflight_service.run_cockpit_preflight`, `backend.engine.price_guard.check_price_sanity`, `backend.engine.price_guard.get_market_quote`, `backend.engine.scheduler.get_active_scheduler`, `backend.engine.scheduler.is_dse_market_open`, `backend.engine.t2_ledger.assert_ledger`, `backend.engine.t2_ledger.bucket_balances`, `backend.engine.trading_lock.acquire_trading_lock`, `backend.portfolio.snapshot_from_session`, `backend.seed.seed_demo` |
| [`backend/logging_config.py`](/backend/logging_config.py) | *Independent Core Module* |
| [`backend/main.py`](/backend/main.py) | `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.adapters.stocknow_client.StockNowLiveClient`, `backend.adapters.stocknow_market_sync.extract_quotes_from_stocknow`, `backend.adapters.stocknow_market_sync.fetch_stocknow_live_market_data`, `backend.adapters.stocknow_market_sync.sync_live_market_to_db`, `backend.config.ROOT`, `backend.config.Settings`, `backend.config.VERSION`, `backend.config.get_active_target_portfolio`, `backend.config.get_allowed_portfolios`, `backend.config.get_portfolio_name`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.DecisionLog`, `backend.database.KernelAuditLog`, `backend.database.RuleAudit`, `backend.database.TradeLog`, `backend.database.portfolio_state`, `backend.engine.auto_trader.AutoTrader`, `backend.engine.auto_trader.AutomationPaused`, `backend.engine.checkpoint.CheckpointManager`, `backend.engine.circuit_breaker.reset_circuit_breaker`, `backend.engine.heartbeat.check_dead_man_switch`, `backend.engine.heartbeat.record_system_heartbeat`, `backend.engine.heartbeat.send_daily_summary_if_due`, `backend.engine.money.ZERO`, `backend.engine.preflight_service.are_caps_set`, `backend.engine.preflight_service.has_passing_preflight_within_24h`, `backend.engine.preflight_service.run_cockpit_preflight`, `backend.engine.scheduler.DSEMarketScheduler`, `backend.engine.scheduler.get_active_scheduler`, `backend.engine.telegram_bot.TelegramBotDaemon`, `backend.engine.trading_lock.acquire_trading_lock`, `backend.hermes_bridge.build_hermes_bridge_router`, `backend.kernel_api.CapsUpdateRequest`, `backend.kernel_api.build_kernel_router`, `backend.logging_config.setup_logging`, `backend.market_map.build_market_map_payload`, `backend.portfolio.build_snapshot`, `backend.portfolio.rule_view`, `backend.routes_auth_settings.KeysSettingsRequest`, `backend.routes_auth_settings.LoginRequest`, `backend.routes_auth_settings.build_auth_settings_router`, `backend.routes_hermes.CreateThreadRequest`, `backend.routes_hermes.build_hermes_router`, `backend.routes_stocknow.build_stocknow_router`, `backend.seed.migrate_real_stocknow_market`, `backend.seed.seed_demo` |
| [`backend/market_map.py`](/backend/market_map.py) | *Independent Core Module* |
| [`backend/portfolio.py`](/backend/portfolio.py) | `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.adapters.stocknow_market_sync._ALL_DSE_SHARES_CACHE`, `backend.config.DHAKA`, `backend.config.Settings`, `backend.config.VERSION`, `backend.config.get_active_target_portfolio`, `backend.config.get_allowed_portfolios`, `backend.config.get_portfolio_name`, `backend.database.AutomationCycle`, `backend.database.CanaryThesis`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.DecisionLog`, `backend.database.KernelStateCheckpoint`, `backend.database.RuleAudit`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.database.portfolio_state`, `backend.engine.money.HUNDRED`, `backend.engine.money.ZERO`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.sale_amount`, `backend.engine.signals.assess_company`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.bucket_balances`, `backend.hermes_bridge.read_hermes_state`, `backend.market_map.build_market_map_payload` |
| [`backend/routes_auth_settings.py`](/backend/routes_auth_settings.py) | `backend.config.DHAKA`, `backend.config.Settings`, `backend.database.Database`, `backend.database.portfolio_state`, `backend.engine.checkpoint.CheckpointManager` |
| [`backend/routes_hermes.py`](/backend/routes_hermes.py) | `backend.config.Settings`, `backend.database.Database`, `backend.database.KernelStateCheckpoint`, `backend.database.RuleAudit`, `backend.engine.checkpoint.CheckpointManager`, `backend.hermes_bridge.get_hermes_cmd`, `backend.hermes_bridge.get_hermes_dir`, `backend.hermes_bridge.read_hermes_state`, `backend.portfolio.portfolio_state` |
| [`backend/routes_stocknow.py`](/backend/routes_stocknow.py) | `backend.adapters.stocknow_api.StockNowError`, `backend.adapters.stocknow_client.StockNowLiveClient`, `backend.adapters.stocknow_market_sync.extract_quotes_from_stocknow`, `backend.adapters.stocknow_market_sync.fetch_stocknow_live_market_data`, `backend.adapters.stocknow_market_sync.get_or_fetch_all_dse_shares`, `backend.adapters.stocknow_market_sync.sync_live_market_to_db`, `backend.adapters.stocknow_portfolio_sync.extract_hummingbird_portfolio`, `backend.adapters.stocknow_portfolio_sync.extract_hummingbird_portfolio_from_browser`, `backend.adapters.stocknow_portfolio_sync.reconcile_portfolio_to_db`, `backend.adapters.stocknow_portfolio_sync.sync_stocknow_portfolio_via_api`, `backend.config.Settings`, `backend.config.get_active_target_portfolio`, `backend.database.CompanyProfile`, `backend.database.Database`, `backend.database.PortfolioState`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.engine.scheduler.DSEMarketScheduler`, `backend.engine.scheduler.get_active_scheduler`, `backend.kernel_api.OrderRequest`, `backend.kernel_api.post_order`, `backend.portfolio.build_snapshot` |
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

### 📄 [`backend/config.py`](/backend/config.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `Settings` | `L26–L138` | `object` | — | 5 |


**Methods in `Settings`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `operator_phone` | `L57–L58` | `(self...)` | `str` | — | — |
| `stocknow_mobile` | `L61–L62` | `(self...)` | `str` | — | — |
| `stocknow_password` | `L65–L66` | `(self...)` | `str` | — | — |
| `__post_init__` | `L68–L92` | `(self...)` | `None` | — | `Decimal`, `ValueError`, `any`, `is_finite` |
| `from_env` | `L95–L138` | `(cls...)` | `Settings` | — | `Decimal`, `cls`, `float`, `fromisoformat` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `utc_now_iso` | `L21–L22` | `(...)` | `str` | — | `isoformat`, `now` |
| `get_allowed_portfolios` | `L141–L158` | `(settings: Settings | None=None...)` | `tuple[str, ...]` | Returns the allowlist of authorized StockNow portfolio IDs: [LIVE, TEST]. | `append`, `from_env`, `getenv`, `strip` |
| `get_active_target_portfolio` | `L161–L177` | `(trading_mode: str, settings: Settin...)` | `str | None` | Returns the active portfolio ID based on current trading mode: | `from_env`, `getenv`, `strip` |
| `get_portfolio_name` | `L180–L198` | `(portfolio_id: str, settings: Settin...)` | `str` | Returns human-readable portfolio name for a given portfolio ID. | `getattr`, `getenv`, `str`, `strip` |
| `test_portfolio_configured` | `L201–L207` | `(settings: Settings | None=None...)` | `bool` | Returns True when a portfolio id is configured for testing (can be same as live). | `bool`, `getenv`, `strip` |


---

### 📄 [`backend/database.py`](/backend/database.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `Base` | `L38–L39` | `DeclarativeBase` | — | 0 |
| `PortfolioState` | `L42–L69` | `Base` | — | 0 |
| `CompanyProfile` | `L72–L85` | `Base` | — | 0 |
| `CustomRule` | `L88–L99` | `Base` | — | 0 |
| `TaxLot` | `L102–L129` | `Base` | — | 0 |
| `AutomationCycle` | `L132–L141` | `Base` | — | 0 |
| `TradeLog` | `L144–L171` | `Base` | — | 0 |
| `CanaryThesis` | `L174–L186` | `Base` | — | 0 |
| `KernelStateCheckpoint` | `L189–L199` | `Base` | — | 0 |
| `CycleRequestKey` | `L202–L205` | `Base` | — | 0 |
| `DecisionLog` | `L208–L218` | `Base` | — | 0 |
| `RuleAudit` | `L221–L229` | `Base` | — | 0 |
| `KernelAuditLog` | `L232–L243` | `Base` | — | 0 |
| `OrderIdempotencyKey` | `L246–L254` | `Base` | — | 0 |
| `ChatBudget` | `L257–L260` | `Base` | — | 0 |
| `SystemHeartbeat` | `L263–L273` | `Base` | — | 0 |
| `PreflightCheckLog` | `L276–L284` | `Base` | — | 0 |
| `DailySummaryLog` | `L287–L302` | `Base` | — | 0 |
| `Database` | `L305–L454` | `object` | — | 5 |


**Methods in `Database`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L306–L326` | `(self, url: str...)` | — | — | `Path`, `RLock`, `ValueError`, `create_engine` |
| `configure_sqlite` | `L319–L324` | `(connection: Any, _record: Any...)` | `None` | — | `close`, `cursor`, `execute`, `listens_for` |
| `create_schema` | `L328–L433` | `(self...)` | `None` | — | `commit`, `connect`, `create_all`, `execute` |
| `read` | `L436–L443` | `(self...)` | — | — | `execute`, `rollback`, `sessions`, `text` |
| `write` | `L446–L454` | `(self...)` | — | — | `commit`, `execute`, `rollback`, `sessions` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `portfolio_state` | `L457–L461` | `(session: Session...)` | `PortfolioState` | — | `RuntimeError`, `get` |


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
| `AutomationPaused` | `L38–L39` | `ValueError` | — | 0 |
| `CycleResult` | `L42–L47` | `dict` | Dictionary subclass that equals [] when trades are empty, ensuring backward compatibility with tests asserting trades == []. | 1 |
| `AutoTrader` | `L50–L748` | `object` | — | 8 |


**Methods in `CycleResult`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__eq__` | `L44–L47` | `(self, other...)` | — | — | `__eq__`, `get`, `isinstance`, `super` |


**Methods in `AutoTrader`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L51–L55` | `(self, database: Database, settings:...)` | — | — | `StockNowAdapter`, `TradingCalendar` |
| `run_cycle` | `L57–L67` | `(self, request_id: str | None=None, ...)` | `dict` | — | `_run_cycle_internal`, `acquire_trading_lock`, `write` |
| `_dispatch_order` | `L69–L100` | `(self, symbol: str, side: str, quant...)` | `dict | None` | — | `Decimal`, `ThreadPoolExecutor`, `execute_order`, `get_running_loop` |
| `_run_cycle_internal` | `L102–L700` | `(self, session: Session, request_id:...)` | `dict` | — | `AutomationCycle`, `CycleRequestKey`, `CycleResult`, `Decimal` |
| `record` | `L310–L326` | `(symbol: str, action: str, reason: s...)` | — | — | `DecisionLog`, `add`, `append`, `startswith` |
| `buy_priority` | `L489–L495` | `(comp: CompanyProfile...)` | `tuple[int, str]` | — | `getattr` |
| `_trade_result` | `L703–L709` | `(trade: TradeLog, action: str...)` | `dict` | — | `float` |
| `advance_demo` | `L711–L748` | `(self, scenario: str...)` | `dict` | — | `Decimal`, `ValueError`, `add_sessions`, `assert_ledger` |


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
| `DSEMarketScheduler` | `L81–L320` | `object` | Async background scheduler enforcing DSE market hours and periodic trading cycles. | 8 |


**Methods in `DSEMarketScheduler`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L84–L106` | `(self, database: Database, settings:...)` | — | — | `AutoTrader`, `hasattr` |
| `get_status` | `L108–L129` | `(self...)` | `dict[str, Any]` | Returns scheduler operational status, telemetry, and DSE market gate. | `getattr`, `is_dse_market_open`, `portfolio_state`, `read` |
| `run_scheduled_tick` | `L131–L215` | `(self, force: bool=False...)` | `dict[str, Any]` | Executes a single scheduler tick, enforcing gate & automation state unless force=True. | `DecisionLog`, `add`, `build_snapshot`, `debug` |
| `run_scheduled_tick_sync` | `L217–L269` | `(self, force: bool=False, session: A...)` | `dict[str, Any]` | Synchronous version of tick execution (e.g. for Hermes chat turn). | `build_snapshot`, `debug`, `getattr`, `info` |
| `start` | `L271–L284` | `(self...)` | `dict[str, Any]` | Starts background periodic polling loop idempotently. | `_loop`, `cancel`, `create_task`, `done` |
| `stop_sync` | `L286–L294` | `(self...)` | `dict[str, Any]` | Stops background periodic polling loop gracefully (sync). | `cancel`, `done`, `get_status` |
| `stop` | `L296–L298` | `(self...)` | `dict[str, Any]` | Stops background periodic polling loop gracefully. | `stop_sync` |
| `_loop` | `L300–L320` | `(self...)` | `None` | Background periodic execution loop respecting configured polling interval. | `error`, `getattr`, `info`, `max` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `get_active_scheduler` | `L30–L32` | `(...)` | `DSEMarketScheduler | None` | Returns the globally active scheduler singleton instance if registered. | — |
| `is_dse_market_open` | `L35–L78` | `(now_dhaka: datetime | None=None, se...)` | `dict[str, Any]` | Evaluates whether DSE is currently open for trading in Asia/Dhaka time. | `Settings`, `TradingCalendar`, `astimezone`, `date` |


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
| `build_kernel_router` | `L1874–L1884` | `(database: Database, settings: Setti...)` | `APIRouter` | Builds the configured kernel router for inclusion in main app. | — |
| `create_kernel_app` | `L1887–L1910` | `(database: Database | None=None, set...)` | `FastAPI` | Creates a standalone FastAPI service for the trading kernel binding 127.0.0.1. | `Database`, `FastAPI`, `Settings`, `create_schema` |


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
| `DevStaticFiles` | `L783–L789` | `StaticFiles` | — | 1 |


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
| `get_response` | `L784–L789` | `(self, path: str, scope...)` | — | — | `get_response`, `super` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `create_app` | `L126–L803` | `(settings: Settings | None=None...)` | `FastAPI` | — | `AutoTrader`, `DSEMarketScheduler`, `Database`, `DevStaticFiles` |
| `lifespan` | `L135–L181` | `(_app: FastAPI...)` | — | — | `TelegramBotDaemon`, `_heartbeat_worker`, `cancel`, `close` |
| `_heartbeat_worker` | `L150–L160` | `(...)` | — | — | `check_dead_man_switch`, `debug`, `record_system_heartbeat`, `send_daily_summary_if_due` |
| `validation_exception_handler` | `L196–L207` | `(_req: Request, exc: RequestValidati...)` | — | — | `JSONResponse`, `append`, `errors`, `exception_handler` |
| `http_exception_handler` | `L210–L230` | `(_req: Request, exc: StarletteHTTPEx...)` | — | — | `JSONResponse`, `exception_handler`, `get`, `getattr` |
| `unhandled_exception_handler` | `L233–L238` | `(_req: Request, exc: Exception...)` | — | — | `JSONResponse`, `exception`, `exception_handler`, `str` |
| `local_security` | `L241–L279` | `(request: Request, call_next...)` | — | — | `JSONResponse`, `call_next`, `compare_digest`, `encode` |
| `health` | `L282–L314` | `(...)` | — | — | `AsyncClient`, `bool`, `get`, `get_status` |
| `portfolio` | `L317–L318` | `(...)` | — | — | `build_snapshot`, `get` |
| `cycle` | `L321–L358` | `(idempotency_key: Annotated[UUID | N...)` | — | — | `HTTPException`, `Header`, `build_snapshot`, `extract_quotes_from_stocknow` |
| `quick_kill` | `L361–L393` | `(body: KillRequest | None=None...)` | — | — | `DecisionLog`, `add`, `build_snapshot`, `create_checkpoint` |
| `automation_handoff` | `L396–L450` | `(body: HandoffRequest...)` | — | — | `HTTPException`, `acquire_trading_lock`, `are_caps_set`, `build_snapshot` |
| `pause` | `L453–L460` | `(body: PauseRequest...)` | — | — | `portfolio_state`, `post`, `publish`, `write` |
| `automation_config` | `L463–L551` | `(body: AutomationConfigRequest...)` | — | — | `HTTPException`, `StockNowAdapter`, `_bg_onscreen_attach`, `are_caps_set` |
| `_bg_onscreen_attach` | `L518–L530` | `(...)` | — | — | `ensure_authenticated`, `extract_quotes_from_stocknow`, `getattr`, `launch` |
| `reset_circuit_breaker_endpoint` | `L554–L556` | `(...)` | — | — | `post`, `reset_circuit_breaker` |
| `get_circuit_breaker_status` | `L559–L568` | `(...)` | — | — | `bool`, `get`, `getattr`, `int` |
| `run_preflight_endpoint` | `L571–L573` | `(...)` | — | — | `post`, `run_cockpit_preflight` |
| `get_preflight_status` | `L576–L581` | `(...)` | — | — | `are_caps_set`, `get`, `has_passing_preflight_within_24h` |
| `get_caps_public` | `L584–L613` | `(...)` | — | — | `Decimal`, `abs`, `all`, `bool` |
| `set_caps_public` | `L616–L701` | `(body: CapsUpdateRequest...)` | — | — | `Decimal`, `HTTPException`, `KernelAuditLog`, `add` |
| `advance` | `L704–L715` | `(body: AdvanceRequest...)` | — | — | `Decimal`, `advance_demo`, `build_market_map_payload`, `get` |
| `market_map_endpoint` | `L718–L719` | `(...)` | — | — | `build_market_map_payload`, `get` |
| `allocation` | `L722–L745` | `(symbol: str, body: AllocationReques...)` | — | — | `HTTPException`, `RuleAudit`, `add`, `get` |
| `event_stream` | `L756–L781` | `(request: Request...)` | — | — | `StreamingResponse`, `generator`, `get`, `subscribe` |
| `generator` | `L759–L771` | `(...)` | — | — | `dumps`, `get`, `is_disconnected`, `unsubscribe` |
| `cockpit` | `L792–L800` | `(...)` | — | — | `FileResponse`, `get` |


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
| `generate_extended_history` | `L237–L289` | `(history: list[dict[str, str]], fund...)` | `dict[str, list[dict[str, Any]]]` | Generates 7d, 1m, 6m, 1y series for TradingView-style deep trend views. | `add_sessions`, `append`, `cos`, `float` |
| `rule_view` | `L292–L302` | `(rule: CustomRule...)` | `dict` | — | `decimal`, `float` |
| `trade_view` | `L305–L334` | `(trade: TradeLog...)` | `dict` | — | `float`, `getattr`, `isoformat` |
| `period_totals` | `L337–L352` | `(trades: list[TradeLog], start: date...)` | `dict` | — | `float`, `isoformat`, `len`, `sum` |
| `build_snapshot` | `L355–L357` | `(database: Database, settings: Setti...)` | `dict` | — | `read`, `snapshot_from_session` |
| `snapshot_from_session` | `L360–L689` | `(session: Session, settings: Setting...)` | `dict` | — | `Decimal`, `StockNowAdapter`, `TradingCalendar`, `abs` |
| `normalized_watchlist` | `L692–L711` | `(companies: list[dict]...)` | `list[dict]` | Equal-weight normalized PRICE index, explicitly not portfolio performance. | `any`, `append`, `decimal`, `float` |


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
| `register` | `L83–L121` | `(ctx...)` | `None` | Register Humming Bird trading kernel tools and lifecycle hooks with Hermes. | `Path`, `exists`, `get`, `is_file` |


---

### 📄 [`plugins/humming_bird/hooks.py`](/plugins/humming_bird/hooks.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `check_dse_trading_hours` | `L13–L41` | `(dt: datetime | None=None...)` | `tuple[bool, str]` | Check if time falls within DSE trading hours (Sun-Thu 10:00 to 14:30 Asia/Dhaka). | `ZoneInfo`, `astimezone`, `now`, `replace` |
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
| `parse_css_design` | `L376–L483` | `(styles_file: Path, light_file: Path...)` | — | — | `append`, `exists`, `get`, `group` |
| `scan_file` | `L429–L478` | `(css_text: str, filename: str...)` | — | — | `any`, `append`, `escape`, `get` |
| `parse_frontend` | `L486–L577` | `(repo_root: Path=REPO_ROOT...)` | — | Index frontend HTML IDs, JS functions, API invocations, and CSS stylesheets. | `add`, `any`, `append`, `compile` |
| `parse_plugin_tools` | `L580–L615` | `(repo_root: Path=REPO_ROOT...)` | `list[dict[str, Any]]` | Parse tools registered in plugins/humming_bird/tools.py using AST. | `append`, `exists`, `get_docstring`, `getattr` |
| `generate_markdown` | `L618–L833` | `(repo_root: Path=REPO_ROOT, output_f...)` | — | — | `append`, `collect_file_metrics`, `discover_files`, `get` |


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
| `run_preflight` | `L361–L415` | `(verbose: bool=False...)` | `tuple[list[CheckResult], bool]` | Runs all preflight checks and returns (results, all_passed). | `Database`, `Settings`, `all`, `check_and_create_db_backup` |
| `print_table` | `L418–L443` | `(checks: list[CheckResult], all_pass...)` | `None` | Formats and prints GO / NO-GO table. | `enumerate`, `len`, `print`, `sum` |
| `main` | `L446–L454` | `(...)` | `int` | — | `ArgumentParser`, `add_argument`, `parse_args`, `print_table` |


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

## 4. Database Schema X-Ray (`backend/database.py`)

SQLAlchemy ORM Entities backing the deterministic ledger and state store:

| Model Entity | Line Range | Base | Purpose & Managed Ledger State |
| :--- | :--- | :--- | :--- |
| `PortfolioState` | `L42–L69` | `Base` | Durable transactional entity |
| `CompanyProfile` | `L72–L85` | `Base` | Durable transactional entity |
| `CustomRule` | `L88–L99` | `Base` | Durable transactional entity |
| `TaxLot` | `L102–L129` | `Base` | Durable transactional entity |
| `AutomationCycle` | `L132–L141` | `Base` | Durable transactional entity |
| `TradeLog` | `L144–L171` | `Base` | Durable transactional entity |
| `CanaryThesis` | `L174–L186` | `Base` | Durable transactional entity |
| `KernelStateCheckpoint` | `L189–L199` | `Base` | Durable transactional entity |
| `CycleRequestKey` | `L202–L205` | `Base` | Durable transactional entity |
| `DecisionLog` | `L208–L218` | `Base` | Durable transactional entity |
| `RuleAudit` | `L221–L229` | `Base` | Durable transactional entity |
| `KernelAuditLog` | `L232–L243` | `Base` | Durable transactional entity |
| `OrderIdempotencyKey` | `L246–L254` | `Base` | Durable transactional entity |
| `ChatBudget` | `L257–L260` | `Base` | Durable transactional entity |
| `SystemHeartbeat` | `L263–L273` | `Base` | Durable transactional entity |
| `PreflightCheckLog` | `L276–L284` | `Base` | Durable transactional entity |
| `DailySummaryLog` | `L287–L302` | `Base` | Durable transactional entity |

---

## 5. FastAPI Route Registry (All Sub-Routers & Endpoints)

| Method | Route Path | Module File | Line | Handler Function | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | [`backend/main.py`](/backend/main.py#L282) | `L282` | `health()` | Route endpoint |
| `GET` | `/api/portfolio` | [`backend/main.py`](/backend/main.py#L317) | `L317` | `portfolio()` | Route endpoint |
| `POST` | `/api/automation/cycle` | [`backend/main.py`](/backend/main.py#L321) | `L321` | `cycle()` | Route endpoint |
| `POST` | `/api/automation/kill` | [`backend/main.py`](/backend/main.py#L361) | `L361` | `quick_kill()` | Route endpoint |
| `POST` | `/api/automation/handoff` | [`backend/main.py`](/backend/main.py#L396) | `L396` | `automation_handoff()` | Route endpoint |
| `POST` | `/api/automation/pause` | [`backend/main.py`](/backend/main.py#L453) | `L453` | `pause()` | Route endpoint |
| `POST` | `/api/automation/config` | [`backend/main.py`](/backend/main.py#L463) | `L463` | `automation_config()` | Route endpoint |
| `POST` | `/api/automation/circuit-breaker/reset` | [`backend/main.py`](/backend/main.py#L554) | `L554` | `reset_circuit_breaker_endpoint()` | Route endpoint |
| `GET` | `/api/automation/circuit-breaker/status` | [`backend/main.py`](/backend/main.py#L559) | `L559` | `get_circuit_breaker_status()` | Route endpoint |
| `POST` | `/api/automation/preflight` | [`backend/main.py`](/backend/main.py#L571) | `L571` | `run_preflight_endpoint()` | Route endpoint |
| `GET` | `/api/automation/preflight/status` | [`backend/main.py`](/backend/main.py#L576) | `L576` | `get_preflight_status()` | Route endpoint |
| `GET` | `/api/caps` | [`backend/main.py`](/backend/main.py#L584) | `L584` | `get_caps_public()` | Route endpoint |
| `POST` | `/api/caps` | [`backend/main.py`](/backend/main.py#L616) | `L616` | `set_caps_public()` | Route endpoint |
| `POST` | `/api/demo/advance` | [`backend/main.py`](/backend/main.py#L704) | `L704` | `advance()` | Route endpoint |
| `GET` | `/api/market/map` | [`backend/main.py`](/backend/main.py#L718) | `L718` | `market_map_endpoint()` | Route endpoint |
| `PATCH` | `/api/companies/{symbol}/allocation` | [`backend/main.py`](/backend/main.py#L722) | `L722` | `allocation()` | Route endpoint |
| `GET` | `/api/stream` | [`backend/main.py`](/backend/main.py#L756) | `L756` | `event_stream()` | Route endpoint |
| `GET` | `/` | [`backend/main.py`](/backend/main.py#L792) | `L792` | `cockpit()` | Route endpoint |
| `GET` | `/api/hermes/conversations` | [`backend/routes_hermes.py`](/backend/routes_hermes.py#L103) | `L103` | `list_conversations()` | Returns conversation topics. |
| `POST` | `/api/hermes/conversations` | [`backend/routes_hermes.py`](/backend/routes_hermes.py#L108) | `L108` | `create_conversation()` | Creates a local conversation topic stub. |
| `GET` | `/api/hermes/conversations/{conversation_id}/messages` | [`backend/routes_hermes.py`](/backend/routes_hermes.py#L119) | `L119` | `conversation_messages()` | Returns messages for a conversation topic. |
| `GET` | `/api/system/changes` | [`backend/routes_hermes.py`](/backend/routes_hermes.py#L124) | `L124` | `system_changes()` | Returns git diff summary and recent kernel checkpoints. |
| `GET` | `/api/hermes/models` | [`backend/routes_hermes.py`](/backend/routes_hermes.py#L199) | `L199` | `get_hermes_models()` | Returns available models, active model, and provider from Hermes state. |
| `POST` | `/api/hermes/model` | [`backend/routes_hermes.py`](/backend/routes_hermes.py#L213) | `L213` | `switch_hermes_model()` | Switches active model and provider in Hermes profile and updates local state. |
| `POST` | `/api/auth/login` | [`backend/routes_auth_settings.py`](/backend/routes_auth_settings.py#L44) | `L44` | `login()` | Route endpoint |
| `POST` | `/api/auth/logout` | [`backend/routes_auth_settings.py`](/backend/routes_auth_settings.py#L61) | `L61` | `logout()` | Route endpoint |
| `GET` | `/api/auth/session` | [`backend/routes_auth_settings.py`](/backend/routes_auth_settings.py#L68) | `L68` | `auth_session()` | Route endpoint |
| `GET` | `/api/settings/keys` | [`backend/routes_auth_settings.py`](/backend/routes_auth_settings.py#L83) | `L83` | `get_api_keys()` | Route endpoint |
| `POST` | `/api/settings/keys` | [`backend/routes_auth_settings.py`](/backend/routes_auth_settings.py#L125) | `L125` | `update_api_keys()` | Route endpoint |
| `GET` | `/api/stocknow/status` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L99) | `L99` | `get_stocknow_status()` | Route endpoint |
| `GET` | `/api/stocknow/page` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L103) | `L103` | `get_stocknow_page()` | Route endpoint |
| `POST` | `/api/stocknow/session` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L117) | `L117` | `post_stocknow_session()` | Route endpoint |
| `POST` | `/api/stocknow/sync-market` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L176) | `L176` | `post_stocknow_sync_market()` | Route endpoint |
| `GET` | `/api/stocknow/all-shares` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L191) | `L191` | `get_all_dse_shares()` | Returns the full 470+ DSE shares catalog with live LTP, +/- %, and sparkline curves. |
| `GET` | `/api/stocknow/history/{symbol}` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L196) | `L196` | `get_stocknow_symbol_history()` | Returns real 400-candle daily history for any DSE company directly from StockNow. |
| `POST` | `/api/stocknow/sync-portfolio` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L212) | `L212` | `post_stocknow_sync_portfolio()` | Route endpoint |
| `POST` | `/api/stocknow/execute-order` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L250) | `L250` | `post_stocknow_execute_order()` | Route endpoint |
| `GET` | `/api/stocknow/scheduler` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L288) | `L288` | `get_stocknow_scheduler()` | Route endpoint |
| `POST` | `/api/stocknow/scheduler` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L292) | `L292` | `post_stocknow_scheduler()` | Route endpoint |
| `GET` | `/k/portfolio` | [`backend/kernel_api.py`](/backend/kernel_api.py#L151) | `L151` | `get_portfolio()` | Returns full portfolio snapshot with holdings, cash, and rolling buckets. |
| `GET` | `/k/watchlist` | [`backend/kernel_api.py`](/backend/kernel_api.py#L162) | `L162` | `get_watchlist()` | Returns watchlist companies, optionally filtered by tier. |
| `GET` | `/k/curve/{symbol}` | [`backend/kernel_api.py`](/backend/kernel_api.py#L192) | `L192` | `get_curve()` | Returns price curve analysis, support floor, resistance ceiling, and sparkline points. |
| `GET` | `/k/market-open` | [`backend/kernel_api.py`](/backend/kernel_api.py#L228) | `L228` | `get_market_open()` | Returns real DSE trading hours and session status in Asia/Dhaka time. |
| `GET` | `/k/canaries` | [`backend/kernel_api.py`](/backend/kernel_api.py#L234) | `L234` | `get_canaries()` | Returns active and past 10% canary probe theses. |
| `GET` | `/k/lots` | [`backend/kernel_api.py`](/backend/kernel_api.py#L256) | `L256` | `get_lots()` | Returns T+2 rolling tax lots with maturity status. |
| `POST` | `/k/tier` | [`backend/kernel_api.py`](/backend/kernel_api.py#L298) | `L298` | `post_tier()` | Updates a company's watchlist tier (GSC, GSC_L1, GSC_L2). |
| `POST` | `/k/allocation` | [`backend/kernel_api.py`](/backend/kernel_api.py#L359) | `L359` | `post_allocation()` | Updates buying allocation percentage for a company rule. |
| `POST` | `/k/quarantine` | [`backend/kernel_api.py`](/backend/kernel_api.py#L428) | `L428` | `post_quarantine()` | Places stock in 90% profit-lock + 10% canary quarantine, or restores it. |
| `POST` | `/k/canary/evaluate` | [`backend/kernel_api.py`](/backend/kernel_api.py#L483) | `L483` | `post_canary_evaluate()` | Evaluates observing canary probe theses against recent price movements. |
| `POST` | `/k/sync` | [`backend/kernel_api.py`](/backend/kernel_api.py#L526) | `L526` | `post_sync()` | Syncs market prices, all-shares board, or virtual portfolio holdings. |
| `POST` | `/k/order` | [`backend/kernel_api.py`](/backend/kernel_api.py#L733) | `L733` | `post_order()` | Submits a virtual BUY or SELL order enforcing T+2 maturity, strict no-loss, and 0.5% fees. |
| `POST` | `/k/rollback` | [`backend/kernel_api.py`](/backend/kernel_api.py#L1244) | `L1244` | `post_rollback()` | Rolls back the last state checkpoint atomically. |
| `GET` | `/k/mode` | [`backend/kernel_api.py`](/backend/kernel_api.py#L1283) | `L1283` | `get_trading_mode()` | Returns current trading mode (TEST_OFFHOURS or LIVE_HOURS). |
| `POST` | `/k/mode` | [`backend/kernel_api.py`](/backend/kernel_api.py#L1295) | `L1295` | `post_trading_mode()` | Sets trading mode to TEST_OFFHOURS or LIVE_HOURS with snapshot and audit log. |
| `GET` | `/k/automation` | [`backend/kernel_api.py`](/backend/kernel_api.py#L1349) | `L1349` | `get_automation_config()` | Returns master buy/sell automation switch, paused state, ingestion mode, and polling interval. |
| `POST` | `/k/automation` | [`backend/kernel_api.py`](/backend/kernel_api.py#L1362) | `L1362` | `post_automation_config()` | Updates master automation switch, paused state, ingestion mode, or polling interval with snapshot & audit. |
| `POST` | `/k/automation/handoff` | [`backend/kernel_api.py`](/backend/kernel_api.py#L1450) | `L1450` | `post_automation_handoff()` | Single-writer run mode handoff: finishes current cycle under lock, then switches mode. |
| `POST` | `/k/automation/circuit-breaker/reset` | [`backend/kernel_api.py`](/backend/kernel_api.py#L1506) | `L1506` | `post_reset_circuit_breaker()` | Manually resets the tripped circuit breaker and clears consecutive failure count. |
| `POST` | `/k/automation/preflight` | [`backend/kernel_api.py`](/backend/kernel_api.py#L1516) | `L1516` | `post_run_preflight()` | Executes the preflight check suite and returns the readiness audit. |
| `GET` | `/k/scheduler` | [`backend/kernel_api.py`](/backend/kernel_api.py#L1530) | `L1530` | `get_scheduler_status()` | Returns current scheduler operational status and telemetry. |
| `POST` | `/k/scheduler` | [`backend/kernel_api.py`](/backend/kernel_api.py#L1545) | `L1545` | `post_scheduler_control()` | Controls background market scheduler (start, stop, status). |
| `POST` | `/k/cycle` | [`backend/kernel_api.py`](/backend/kernel_api.py#L1604) | `L1604` | `post_run_cycle()` | Executes an automation trading cycle via AutoTrader under the single-writer trading lock. |
| `POST` | `/k/stocknow/session` | [`backend/kernel_api.py`](/backend/kernel_api.py#L1654) | `L1654` | `post_stocknow_session()` | Controls live StockNow session (launch, status, login, logout). |
| `GET` | `/k/caps` | [`backend/kernel_api.py`](/backend/kernel_api.py#L1742) | `L1742` | `get_caps()` | Fetch current risk limits, kill switch status, and today's usage scoped by active portfolio. |
| `POST` | `/k/caps` | [`backend/kernel_api.py`](/backend/kernel_api.py#L1779) | `L1779` | `set_caps()` | Update risk limits in the kernel. May only lower limits by itself; raising a limit requires confirmation. |

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
| `.app-shell` | [`frontend/styles.css`](/frontend/styles.css#L242) | `L242` | `grid` | `64px minmax(0, 1fr) var(--hermes-width)` | — | — | — |
| `.nav-rail` | [`frontend/styles.css`](/frontend/styles.css#L255) | `L255` | `flex` | — | — | `var(--nav-bg)` | — |
| `.workspace` | [`frontend/styles.css`](/frontend/styles.css#L356) | `L356` | — | — | `relative` | — | — |
| `.topbar` | [`frontend/styles.css`](/frontend/styles.css#L380) | `L380` | `flex` | — | `sticky` | `rgba(10, 16, 24, 0.88)` | `nowrap` |
| `.topbar-right` | [`frontend/styles.css`](/frontend/styles.css#L416) | `L416` | `flex` | — | — | — | `nowrap` |
| `.topbar` | [`frontend/styles.css`](/frontend/styles.css#L426) | `L426` | `flex` | — | — | — | `nowrap` |
| `.topbar` | [`frontend/styles.css`](/frontend/styles.css#L435) | `L435` | — | — | — | — | — |
| `.topbar` | [`frontend/styles.css`](/frontend/styles.css#L796) | `L796` | — | — | — | — | — |
| `.engine-controls` | [`frontend/styles.css`](/frontend/styles.css#L962) | `L962` | `flex` | — | — | — | — |
| `.session-bar` | [`frontend/styles.css`](/frontend/styles.css#L998) | `L998` | `flex` | — | — | `#0e161f` | `wrap` |
| `.metric-card` | [`frontend/styles.css`](/frontend/styles.css#L1054) | `L1054` | — | — | — | `var(--panel)` | — |
| `.skills-drawer` | [`frontend/styles.css`](/frontend/styles.css#L2724) | `L2724` | — | — | — | `var(--panel)` | — |
| `.model-dropup-menu` | [`frontend/styles.css`](/frontend/styles.css#L4657) | `L4657` | — | — | `absolute` | `var(--panel, #111a24)` | — |
| `.session-bar` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L69) | `L69` | — | — | — | `#ffffff` | — |
| `.metric-card` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L95) | `L95` | — | — | — | `#ffffff` | — |
| `.nav-rail` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L499) | `L499` | — | — | — | `#f8fafc !important` | — |
| `.chat-messages` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L557) | `L557` | — | — | — | `#ffffff !important` | — |
| `.diff-card` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L596) | `L596` | — | — | — | `#ffffff !important` | — |
| `.nav-rail` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L809) | `L809` | — | — | — | `#ccfbf1 !important` | — |
| `.topbar` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L871) | `L871` | — | — | — | `rgba(226, 232, 240, 0.92)` | — |
| `#hermes-resizer` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L958) | `L958` | — | — | `absolute` | `transparent` | — |
| `.app-shell` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L999) | `L999` | — | — | — | — | — |
| `.chat-messages` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L1108) | `L1108` | — | — | — | — | — |
| `.diff-card` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L1598) | `L1598` | — | — | — | `var(--panel)` | — |
| `.model-dropup-menu` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L1733) | `L1733` | — | — | `absolute` | `var(--panel, #111a24)` | — |
| `.model-dropup-menu` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L1750) | `L1750` | — | — | — | `#ffffff` | — |
| `.workspace` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L1873) | `L1873` | — | — | — | — | — |
| `.skills-drawer` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L2225) | `L2225` | — | — | — | `#ffffff !important` | — |
| `.skills-drawer` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L2976) | `L2976` | — | — | — | `var(--panel)` | — |


### 6.3 DOM Identifiers Index (`frontend/index.html`)

Complete catalog of all **301** distinct element IDs in `frontend/index.html` for UI element location:

| DOM Element ID (`id="..."`) | HTML Tag | Line Number |
| :--- | :--- | :--- |
| `#nav-system-control` | `<a>` | [`frontend/index.html#L28`](/frontend/index.html#L28) |
| `#user-avatar-btn` | `<button>` | [`frontend/index.html#L30`](/frontend/index.html#L30) |
| `#topbar-clock-widget` | `<button>` | [`frontend/index.html#L38`](/frontend/index.html#L38) |
| `#market-status-dot` | `<span>` | [`frontend/index.html#L39`](/frontend/index.html#L39) |
| `#market-status-text` | `<span>` | [`frontend/index.html#L40`](/frontend/index.html#L40) |
| `#market-countdown-text` | `<span>` | [`frontend/index.html#L42`](/frontend/index.html#L42) |
| `#topbar-tmode-badge` | `<span>` | [`frontend/index.html#L43`](/frontend/index.html#L43) |
| `#topbar-run-mode-switch` | `<div>` | [`frontend/index.html#L48`](/frontend/index.html#L48) |
| `#topbar-mode-btn-background` | `<button>` | [`frontend/index.html#L49`](/frontend/index.html#L49) |
| `#topbar-mode-btn-onscreen` | `<button>` | [`frontend/index.html#L50`](/frontend/index.html#L50) |
| `#topbar-switching-state` | `<span>` | [`frontend/index.html#L52`](/frontend/index.html#L52) |
| `#topbar-automation-control` | `<div>` | [`frontend/index.html#L56`](/frontend/index.html#L56) |
| `#topbar-automation-toggle-input` | `<input>` | [`frontend/index.html#L59`](/frontend/index.html#L59) |
| `#topbar-automation-state` | `<span>` | [`frontend/index.html#L62`](/frontend/index.html#L62) |
| `#run-cycle` | `<button>` | [`frontend/index.html#L66`](/frontend/index.html#L66) |
| `#run-label` | `<span>` | [`frontend/index.html#L66`](/frontend/index.html#L66) |
| `#theme-toggle-btn` | `<button>` | [`frontend/index.html#L69`](/frontend/index.html#L69) |
| `#theme-name` | `<span>` | [`frontend/index.html#L70`](/frontend/index.html#L70) |
| `#topbar-kill-btn` | `<button>` | [`frontend/index.html#L77`](/frontend/index.html#L77) |
| `#topbar-handoff-btn` | `<button>` | [`frontend/index.html#L78`](/frontend/index.html#L78) |
| `#trading-mode-toggle` | `<div>` | [`frontend/index.html#L79`](/frontend/index.html#L79) |
| `#header-mode-slider` | `<div>` | [`frontend/index.html#L80`](/frontend/index.html#L80) |
| `#topbar-master-label` | `<span>` | [`frontend/index.html#L81`](/frontend/index.html#L81) |
| `#error-banner` | `<div>` | [`frontend/index.html#L84`](/frontend/index.html#L84) |
| `#error-text` | `<span>` | [`frontend/index.html#L84`](/frontend/index.html#L84) |
| `#dismiss-error` | `<button>` | [`frontend/index.html#L84`](/frontend/index.html#L84) |
| `#view-dashboard` | `<div>` | [`frontend/index.html#L87`](/frontend/index.html#L87) |
| `#overview` | `<section>` | [`frontend/index.html#L88`](/frontend/index.html#L88) |
| `#portfolio-header-badge` | `<span>` | [`frontend/index.html#L95`](/frontend/index.html#L95) |
| `#portfolio-header-badge-dot` | `<span>` | [`frontend/index.html#L96`](/frontend/index.html#L96) |
| `#portfolio-header-badge-text` | `<span>` | [`frontend/index.html#L97`](/frontend/index.html#L97) |
| `#demo-date` | `<strong>` | [`frontend/index.html#L109`](/frontend/index.html#L109) |
| `#engine-state` | `<span>` | [`frontend/index.html#L111`](/frontend/index.html#L111) |
| `#snapshot-label` | `<span>` | [`frontend/index.html#L112`](/frontend/index.html#L112) |
| `#overview-sys-link` | `<a>` | [`frontend/index.html#L113`](/frontend/index.html#L113) |
| `#overview-sys-dot` | `<span>` | [`frontend/index.html#L114`](/frontend/index.html#L114) |
| `#overview-sys-text` | `<span>` | [`frontend/index.html#L115`](/frontend/index.html#L115) |
| `#scenario` | `<select>` | [`frontend/index.html#L119`](/frontend/index.html#L119) |
| `#next-session` | `<button>` | [`frontend/index.html#L119`](/frontend/index.html#L119) |
| `#equity-sparkline` | `<div>` | [`frontend/index.html#L126`](/frontend/index.html#L126) |
| `#metric-equity` | `<div>` | [`frontend/index.html#L128`](/frontend/index.html#L128) |
| `#metric-total-gain` | `<span>` | [`frontend/index.html#L129`](/frontend/index.html#L129) |
| `#metric-cash` | `<div>` | [`frontend/index.html#L131`](/frontend/index.html#L131) |
| `#metric-unsettled` | `<span>` | [`frontend/index.html#L131`](/frontend/index.html#L131) |
| `#metric-realized` | `<div>` | [`frontend/index.html#L132`](/frontend/index.html#L132) |
| `#metric-unrealized` | `<div>` | [`frontend/index.html#L133`](/frontend/index.html#L133) |
| `#active-holdings-card` | `<article>` | [`frontend/index.html#L137`](/frontend/index.html#L137) |
| `#holdings-settled-cash` | `<strong>` | [`frontend/index.html#L144`](/frontend/index.html#L144) |
| `#holdings-buy-cost` | `<strong>` | [`frontend/index.html#L145`](/frontend/index.html#L145) |
| `#holdings-sell-value` | `<strong>` | [`frontend/index.html#L146`](/frontend/index.html#L146) |
| `#holdings-unrealized-gain` | `<strong>` | [`frontend/index.html#L147`](/frontend/index.html#L147) |
| `#active-holdings-body` | `<tbody>` | [`frontend/index.html#L164`](/frontend/index.html#L164) |
| `#active-holdings-foot` | `<tfoot>` | [`frontend/index.html#L165`](/frontend/index.html#L165) |
| `#mature-shares` | `<strong>` | [`frontend/index.html#L170`](/frontend/index.html#L170) |
| `#locked-shares` | `<strong>` | [`frontend/index.html#L170`](/frontend/index.html#L170) |
| `#quarantined-count` | `<strong>` | [`frontend/index.html#L170`](/frontend/index.html#L170) |
| `#fees-paid` | `<strong>` | [`frontend/index.html#L170`](/frontend/index.html#L170) |
| `#ledger-status` | `<span>` | [`frontend/index.html#L170`](/frontend/index.html#L170) |
| `#curve-sessions` | `<span>` | [`frontend/index.html#L174`](/frontend/index.html#L174) |
| `#index-value` | `<strong>` | [`frontend/index.html#L175`](/frontend/index.html#L175) |
| `#index-change` | `<span>` | [`frontend/index.html#L175`](/frontend/index.html#L175) |
| `#pulse-support-val` | `<strong>` | [`frontend/index.html#L185`](/frontend/index.html#L185) |
| `#pulse-resistance-val` | `<strong>` | [`frontend/index.html#L186`](/frontend/index.html#L186) |
| `#main-chart` | `<div>` | [`frontend/index.html#L190`](/frontend/index.html#L190) |
| `#main-chart-tooltip` | `<div>` | [`frontend/index.html#L191`](/frontend/index.html#L191) |
| `#bucket-stack` | `<div>` | [`frontend/index.html#L195`](/frontend/index.html#L195) |
| `#cycle-badge` | `<span>` | [`frontend/index.html#L209`](/frontend/index.html#L209) |
| `#decision-feed` | `<div>` | [`frontend/index.html#L211`](/frontend/index.html#L211) |
| `#watchlist-header` | `<div>` | [`frontend/index.html#L215`](/frontend/index.html#L215) |
| `#watchlist` | `<section>` | [`frontend/index.html#L221`](/frontend/index.html#L221) |
| `#company-count` | `<span>` | [`frontend/index.html#L223`](/frontend/index.html#L223) |
| `#watchlist-source-label` | `<span>` | [`frontend/index.html#L223`](/frontend/index.html#L223) |
| `#category-tabs` | `<div>` | [`frontend/index.html#L224`](/frontend/index.html#L224) |
| `#cat-all-count` | `<span>` | [`frontend/index.html#L225`](/frontend/index.html#L225) |
| `#cat-gsc-count` | `<span>` | [`frontend/index.html#L226`](/frontend/index.html#L226) |
| `#cat-l1-count` | `<span>` | [`frontend/index.html#L227`](/frontend/index.html#L227) |
| `#cat-l2-count` | `<span>` | [`frontend/index.html#L228`](/frontend/index.html#L228) |
| `#cat-dse-count` | `<span>` | [`frontend/index.html#L229`](/frontend/index.html#L229) |
| `#company-search` | `<input>` | [`frontend/index.html#L231`](/frontend/index.html#L231) |
| `#watchlist-thead` | `<thead>` | [`frontend/index.html#L233`](/frontend/index.html#L233) |
| `#col-curve-signal` | `<th>` | [`frontend/index.html#L233`](/frontend/index.html#L233) |
| `#col-held-mature` | `<th>` | [`frontend/index.html#L233`](/frontend/index.html#L233) |
| `#col-buy-cap` | `<th>` | [`frontend/index.html#L233`](/frontend/index.html#L233) |
| `#watchlist-body` | `<tbody>` | [`frontend/index.html#L233`](/frontend/index.html#L233) |
| `#watchlist-pagination` | `<div>` | [`frontend/index.html#L234`](/frontend/index.html#L234) |
| `#watchlist-prev-page` | `<button>` | [`frontend/index.html#L235`](/frontend/index.html#L235) |
| `#watchlist-page-info` | `<span>` | [`frontend/index.html#L236`](/frontend/index.html#L236) |
| `#watchlist-next-page` | `<button>` | [`frontend/index.html#L237`](/frontend/index.html#L237) |
| `#execution` | `<section>` | [`frontend/index.html#L243`](/frontend/index.html#L243) |
| `#inspector-symbol` | `<h2>` | [`frontend/index.html#L245`](/frontend/index.html#L245) |
| `#open-deep-trend` | `<button>` | [`frontend/index.html#L247`](/frontend/index.html#L247) |
| `#inspector-sector` | `<span>` | [`frontend/index.html#L250`](/frontend/index.html#L250) |
| `#inspector-basis` | `<strong>` | [`frontend/index.html#L253`](/frontend/index.html#L253) |
| `#inspector-pnl` | `<strong>` | [`frontend/index.html#L253`](/frontend/index.html#L253) |
| `#inspector-return` | `<strong>` | [`frontend/index.html#L253`](/frontend/index.html#L253) |
| `#inspector-reason` | `<p>` | [`frontend/index.html#L254`](/frontend/index.html#L254) |
| `#lots-body` | `<tbody>` | [`frontend/index.html#L255`](/frontend/index.html#L255) |
| `#market-map` | `<section>` | [`frontend/index.html#L259`](/frontend/index.html#L259) |
| `#treemap-sector-select` | `<select>` | [`frontend/index.html#L266`](/frontend/index.html#L266) |
| `#treemap-back-btn` | `<button>` | [`frontend/index.html#L276`](/frontend/index.html#L276) |
| `#treemap-active-view` | `<span>` | [`frontend/index.html#L279`](/frontend/index.html#L279) |
| `#treemap-turnover-badge` | `<span>` | [`frontend/index.html#L280`](/frontend/index.html#L280) |
| `#treemap-container` | `<div>` | [`frontend/index.html#L285`](/frontend/index.html#L285) |
| `#treemap-tooltip` | `<div>` | [`frontend/index.html#L288`](/frontend/index.html#L288) |
| `#sector-gainer-chart-wrap` | `<div>` | [`frontend/index.html#L307`](/frontend/index.html#L307) |
| `#sector-gainer-chart` | `<svg>` | [`frontend/index.html#L308`](/frontend/index.html#L308) |
| `#rules` | `<section>` | [`frontend/index.html#L314`](/frontend/index.html#L314) |
| `#what-if-card` | `<article>` | [`frontend/index.html#L323`](/frontend/index.html#L323) |
| `#sim-symbol-badge` | `<span>` | [`frontend/index.html#L329`](/frontend/index.html#L329) |
| `#what-if-target-price` | `<strong>` | [`frontend/index.html#L333`](/frontend/index.html#L333) |
| `#what-if-target-pct` | `<span>` | [`frontend/index.html#L334`](/frontend/index.html#L334) |
| `#what-if-slider` | `<input>` | [`frontend/index.html#L337`](/frontend/index.html#L337) |
| `#what-if-gross` | `<strong>` | [`frontend/index.html#L346`](/frontend/index.html#L346) |
| `#what-if-fee` | `<strong>` | [`frontend/index.html#L347`](/frontend/index.html#L347) |
| `#what-if-net-pnl` | `<strong>` | [`frontend/index.html#L348`](/frontend/index.html#L348) |
| `#what-if-return-pct` | `<strong>` | [`frontend/index.html#L349`](/frontend/index.html#L349) |
| `#profit-tiers` | `<div>` | [`frontend/index.html#L361`](/frontend/index.html#L361) |
| `#pullback-setting` | `<span>` | [`frontend/index.html#L361`](/frontend/index.html#L361) |
| `#allocation-form` | `<form>` | [`frontend/index.html#L362`](/frontend/index.html#L362) |
| `#buy-allocation` | `<input>` | [`frontend/index.html#L366`](/frontend/index.html#L366) |
| `#company-enabled` | `<input>` | [`frontend/index.html#L372`](/frontend/index.html#L372) |
| `#save-allocation` | `<button>` | [`frontend/index.html#L377`](/frontend/index.html#L377) |
| `#canary-section` | `<section>` | [`frontend/index.html#L383`](/frontend/index.html#L383) |
| `#canary-count` | `<span>` | [`frontend/index.html#L384`](/frontend/index.html#L384) |
| `#canary-feed` | `<div>` | [`frontend/index.html#L385`](/frontend/index.html#L385) |
| `#ledger` | `<section>` | [`frontend/index.html#L390`](/frontend/index.html#L390) |
| `#period-pnl` | `<strong>` | [`frontend/index.html#L399`](/frontend/index.html#L399) |
| `#period-buy` | `<strong>` | [`frontend/index.html#L399`](/frontend/index.html#L399) |
| `#period-sell` | `<strong>` | [`frontend/index.html#L399`](/frontend/index.html#L399) |
| `#period-trades` | `<strong>` | [`frontend/index.html#L399`](/frontend/index.html#L399) |
| `#trades-body` | `<tbody>` | [`frontend/index.html#L400`](/frontend/index.html#L400) |
| `#ledger-range` | `<span>` | [`frontend/index.html#L401`](/frontend/index.html#L401) |
| `#view-settings` | `<div>` | [`frontend/index.html#L407`](/frontend/index.html#L407) |
| `#system-control` | `<div>` | [`frontend/index.html#L412`](/frontend/index.html#L412) |
| `#automation-settings-card` | `<article>` | [`frontend/index.html#L414`](/frontend/index.html#L414) |
| `#circuit-state` | `<span>` | [`frontend/index.html#L427`](/frontend/index.html#L427) |
| `#master-automation-toggle-input` | `<input>` | [`frontend/index.html#L431`](/frontend/index.html#L431) |
| `#master-automation-status-text` | `<span>` | [`frontend/index.html#L434`](/frontend/index.html#L434) |
| `#master-automation-toggle` | `<button>` | [`frontend/index.html#L437`](/frontend/index.html#L437) |
| `#current-mode-pill` | `<span>` | [`frontend/index.html#L446`](/frontend/index.html#L446) |
| `#ingestion-mode-switch` | `<div>` | [`frontend/index.html#L448`](/frontend/index.html#L448) |
| `#mode-btn-polling` | `<button>` | [`frontend/index.html#L449`](/frontend/index.html#L449) |
| `#mode-btn-live` | `<button>` | [`frontend/index.html#L459`](/frontend/index.html#L459) |
| `#settings-runmode-status-line` | `<div>` | [`frontend/index.html#L470`](/frontend/index.html#L470) |
| `#settings-active-mode-text` | `<span>` | [`frontend/index.html#L471`](/frontend/index.html#L471) |
| `#settings-pending-handoff-state` | `<span>` | [`frontend/index.html#L472`](/frontend/index.html#L472) |
| `#settings-trading-mode-wrap` | `<div>` | [`frontend/index.html#L476`](/frontend/index.html#L476) |
| `#settings-trading-mode-pill` | `<span>` | [`frontend/index.html#L482`](/frontend/index.html#L482) |
| `#settings-trading-mode-toggle` | `<div>` | [`frontend/index.html#L484`](/frontend/index.html#L484) |
| `#settings-tmode-live` | `<button>` | [`frontend/index.html#L485`](/frontend/index.html#L485) |
| `#settings-tmode-test` | `<button>` | [`frontend/index.html#L495`](/frontend/index.html#L495) |
| `#polling-interval-wrap` | `<div>` | [`frontend/index.html#L508`](/frontend/index.html#L508) |
| `#polling-interval-display` | `<strong>` | [`frontend/index.html#L514`](/frontend/index.html#L514) |
| `#polling-range-slider` | `<input>` | [`frontend/index.html#L517`](/frontend/index.html#L517) |
| `#polling-interval-pills` | `<div>` | [`frontend/index.html#L526`](/frontend/index.html#L526) |
| `#polling-disabled-hint` | `<div>` | [`frontend/index.html#L532`](/frontend/index.html#L532) |
| `#stocknow-connection-card` | `<article>` | [`frontend/index.html#L537`](/frontend/index.html#L537) |
| `#stocknow-api-status` | `<strong>` | [`frontend/index.html#L547`](/frontend/index.html#L547) |
| `#stocknow-browser-status` | `<strong>` | [`frontend/index.html#L551`](/frontend/index.html#L551) |
| `#stocknow-prices-synced` | `<strong>` | [`frontend/index.html#L555`](/frontend/index.html#L555) |
| `#stocknow-portfolio-synced` | `<strong>` | [`frontend/index.html#L559`](/frontend/index.html#L559) |
| `#stocknow-active-portfolio` | `<strong>` | [`frontend/index.html#L563`](/frontend/index.html#L563) |
| `#btn-stocknow-launch` | `<button>` | [`frontend/index.html#L568`](/frontend/index.html#L568) |
| `#btn-stocknow-auth` | `<button>` | [`frontend/index.html#L569`](/frontend/index.html#L569) |
| `#btn-stocknow-sync` | `<button>` | [`frontend/index.html#L570`](/frontend/index.html#L570) |
| `#btn-stocknow-logout` | `<button>` | [`frontend/index.html#L571`](/frontend/index.html#L571) |
| `#btn-stocknow-sync-portfolio` | `<button>` | [`frontend/index.html#L573`](/frontend/index.html#L573) |
| `#risk-caps-card` | `<article>` | [`frontend/index.html#L578`](/frontend/index.html#L578) |
| `#risk-caps-form` | `<form>` | [`frontend/index.html#L585`](/frontend/index.html#L585) |
| `#caps-kill-switch` | `<input>` | [`frontend/index.html#L593`](/frontend/index.html#L593) |
| `#caps-kill-switch-status` | `<span>` | [`frontend/index.html#L594`](/frontend/index.html#L594) |
| `#caps-max-order` | `<input>` | [`frontend/index.html#L602`](/frontend/index.html#L602) |
| `#caps-max-symbol` | `<input>` | [`frontend/index.html#L606`](/frontend/index.html#L606) |
| `#caps-daily-budget` | `<input>` | [`frontend/index.html#L610`](/frontend/index.html#L610) |
| `#caps-max-orders` | `<input>` | [`frontend/index.html#L614`](/frontend/index.html#L614) |
| `#btn-save-caps` | `<button>` | [`frontend/index.html#L619`](/frontend/index.html#L619) |
| `#caps-save-status` | `<span>` | [`frontend/index.html#L622`](/frontend/index.html#L622) |
| `#hermes-brain-card` | `<article>` | [`frontend/index.html#L628`](/frontend/index.html#L628) |
| `#brain-primary-model` | `<strong>` | [`frontend/index.html#L640`](/frontend/index.html#L640) |
| `#brain-primary-provider` | `<span>` | [`frontend/index.html#L641`](/frontend/index.html#L641) |
| `#brain-profile-tag` | `<span>` | [`frontend/index.html#L641`](/frontend/index.html#L641) |
| `#brain-primary-status` | `<span>` | [`frontend/index.html#L643`](/frontend/index.html#L643) |
| `#brain-fallbacks-list` | `<div>` | [`frontend/index.html#L650`](/frontend/index.html#L650) |
| `#brain-fallbacks-empty` | `<div>` | [`frontend/index.html#L651`](/frontend/index.html#L651) |
| `#brain-last-turn-provider` | `<strong>` | [`frontend/index.html#L662`](/frontend/index.html#L662) |
| `#brain-last-turn-model` | `<span>` | [`frontend/index.html#L663`](/frontend/index.html#L663) |
| `#brain-last-turn-time` | `<span>` | [`frontend/index.html#L665`](/frontend/index.html#L665) |
| `#advanced-settings-card` | `<details>` | [`frontend/index.html#L675`](/frontend/index.html#L675) |
| `#api-keys-card` | `<div>` | [`frontend/index.html#L686`](/frontend/index.html#L686) |
| `#api-keys-form` | `<form>` | [`frontend/index.html#L692`](/frontend/index.html#L692) |
| `#key-telegram-token` | `<input>` | [`frontend/index.html#L697`](/frontend/index.html#L697) |
| `#key-telegram-chat` | `<input>` | [`frontend/index.html#L704`](/frontend/index.html#L704) |
| `#btn-save-api-keys` | `<button>` | [`frontend/index.html#L708`](/frontend/index.html#L708) |
| `#keys-save-status` | `<span>` | [`frontend/index.html#L711`](/frontend/index.html#L711) |
| `#fees-card` | `<div>` | [`frontend/index.html#L717`](/frontend/index.html#L717) |
| `#bridge-ctrl-card` | `<div>` | [`frontend/index.html#L733`](/frontend/index.html#L733) |
| `#adp-mode-text` | `<strong>` | [`frontend/index.html#L740`](/frontend/index.html#L740) |
| `#sse-status-badge` | `<span>` | [`frontend/index.html#L746`](/frontend/index.html#L746) |
| `#live-dot` | `<span>` | [`frontend/index.html#L746`](/frontend/index.html#L746) |
| `#source-badge` | `<span>` | [`frontend/index.html#L747`](/frontend/index.html#L747) |
| `#token-button` | `<button>` | [`frontend/index.html#L748`](/frontend/index.html#L748) |
| `#footer-mode-tag` | `<span>` | [`frontend/index.html#L757`](/frontend/index.html#L757) |
| `#footer-synthetic-desc` | `<p>` | [`frontend/index.html#L757`](/frontend/index.html#L757) |
| `#dhaka-clock` | `<span>` | [`frontend/index.html#L757`](/frontend/index.html#L757) |
| `#hermes-sidebar` | `<aside>` | [`frontend/index.html#L760`](/frontend/index.html#L760) |
| `#hermes-resizer` | `<div>` | [`frontend/index.html#L761`](/frontend/index.html#L761) |
| `#hermes-collapse-btn` | `<button>` | [`frontend/index.html#L768`](/frontend/index.html#L768) |
| `#active-conv-title` | `<span>` | [`frontend/index.html#L774`](/frontend/index.html#L774) |
| `#tab-hermes-chat` | `<button>` | [`frontend/index.html#L779`](/frontend/index.html#L779) |
| `#tab-hermes-conversations` | `<button>` | [`frontend/index.html#L780`](/frontend/index.html#L780) |
| `#conversations-badge` | `<span>` | [`frontend/index.html#L780`](/frontend/index.html#L780) |
| `#tab-hermes-changes` | `<button>` | [`frontend/index.html#L781`](/frontend/index.html#L781) |
| `#changes-badge` | `<span>` | [`frontend/index.html#L781`](/frontend/index.html#L781) |
| `#tab-hermes-skills` | `<button>` | [`frontend/index.html#L782`](/frontend/index.html#L782) |
| `#skills-badge` | `<span>` | [`frontend/index.html#L782`](/frontend/index.html#L782) |
| `#pane-hermes-chat` | `<div>` | [`frontend/index.html#L786`](/frontend/index.html#L786) |
| `#chat-messages` | `<div>` | [`frontend/index.html#L787`](/frontend/index.html#L787) |
| `#hermes-welcome-message` | `<article>` | [`frontend/index.html#L788`](/frontend/index.html#L788) |
| `#chat-safety-note` | `<div>` | [`frontend/index.html#L793`](/frontend/index.html#L793) |
| `#welcome-chips-slot` | `<div>` | [`frontend/index.html#L794`](/frontend/index.html#L794) |
| `#bottom-chips-slot` | `<div>` | [`frontend/index.html#L799`](/frontend/index.html#L799) |
| `#chat-quick-prompts` | `<div>` | [`frontend/index.html#L800`](/frontend/index.html#L800) |
| `#hermes-model-trigger` | `<button>` | [`frontend/index.html#L809`](/frontend/index.html#L809) |
| `#provider-prefix-label` | `<span>` | [`frontend/index.html#L810`](/frontend/index.html#L810) |
| `#hermes-active-model-name` | `<strong>` | [`frontend/index.html#L811`](/frontend/index.html#L811) |
| `#model-dropup-menu` | `<div>` | [`frontend/index.html#L814`](/frontend/index.html#L814) |
| `#model-dropdown-list` | `<div>` | [`frontend/index.html#L816`](/frontend/index.html#L816) |
| `#chat-form` | `<form>` | [`frontend/index.html#L822`](/frontend/index.html#L822) |
| `#chat-input` | `<textarea>` | [`frontend/index.html#L824`](/frontend/index.html#L824) |
| `#chat-send` | `<button>` | [`frontend/index.html#L827`](/frontend/index.html#L827) |
| `#chat-footer-note` | `<p>` | [`frontend/index.html#L832`](/frontend/index.html#L832) |
| `#pane-hermes-conversations` | `<div>` | [`frontend/index.html#L837`](/frontend/index.html#L837) |
| `#new-conversation-btn` | `<button>` | [`frontend/index.html#L839`](/frontend/index.html#L839) |
| `#conversations-list` | `<div>` | [`frontend/index.html#L844`](/frontend/index.html#L844) |
| `#pane-hermes-changes` | `<div>` | [`frontend/index.html#L850`](/frontend/index.html#L850) |
| `#changes-badge-count` | `<span>` | [`frontend/index.html#L854`](/frontend/index.html#L854) |
| `#rollback-pane-btn` | `<button>` | [`frontend/index.html#L857`](/frontend/index.html#L857) |
| `#refresh-changes-btn` | `<button>` | [`frontend/index.html#L860`](/frontend/index.html#L860) |
| `#changes-diff-list` | `<div>` | [`frontend/index.html#L864`](/frontend/index.html#L864) |
| `#files-changed-list` | `<div>` | [`frontend/index.html#L868`](/frontend/index.html#L868) |
| `#changes-checkpoints-list` | `<div>` | [`frontend/index.html#L869`](/frontend/index.html#L869) |
| `#pane-hermes-skills` | `<div>` | [`frontend/index.html#L873`](/frontend/index.html#L873) |
| `#rollback-skills-btn` | `<button>` | [`frontend/index.html#L876`](/frontend/index.html#L876) |
| `#skills-list` | `<div>` | [`frontend/index.html#L883`](/frontend/index.html#L883) |
| `#btn-add-cron` | `<button>` | [`frontend/index.html#L888`](/frontend/index.html#L888) |
| `#crons-list` | `<div>` | [`frontend/index.html#L890`](/frontend/index.html#L890) |
| `#hermes-memory-preview` | `<div>` | [`frontend/index.html#L896`](/frontend/index.html#L896) |
| `#user-md-preview` | `<div>` | [`frontend/index.html#L901`](/frontend/index.html#L901) |
| `#memory-md-preview` | `<div>` | [`frontend/index.html#L907`](/frontend/index.html#L907) |
| `#durable-facts-list` | `<div>` | [`frontend/index.html#L913`](/frontend/index.html#L913) |
| `#checkpoints-list` | `<div>` | [`frontend/index.html#L917`](/frontend/index.html#L917) |
| `#floating-hermes-open` | `<button>` | [`frontend/index.html#L924`](/frontend/index.html#L924) |
| `#deep-trend-modal` | `<dialog>` | [`frontend/index.html#L928`](/frontend/index.html#L928) |
| `#modal-backdrop` | `<div>` | [`frontend/index.html#L929`](/frontend/index.html#L929) |
| `#modal-company-sector` | `<span>` | [`frontend/index.html#L933`](/frontend/index.html#L933) |
| `#modal-company-category` | `<span>` | [`frontend/index.html#L933`](/frontend/index.html#L933) |
| `#modal-company-title` | `<h2>` | [`frontend/index.html#L934`](/frontend/index.html#L934) |
| `#modal-company-sub` | `<span>` | [`frontend/index.html#L934`](/frontend/index.html#L934) |
| `#modal-price` | `<span>` | [`frontend/index.html#L936`](/frontend/index.html#L936) |
| `#modal-change` | `<span>` | [`frontend/index.html#L937`](/frontend/index.html#L937) |
| `#modal-signal-tag` | `<span>` | [`frontend/index.html#L938`](/frontend/index.html#L938) |
| `#deep-timeframe-tabs` | `<div>` | [`frontend/index.html#L942`](/frontend/index.html#L942) |
| `#modal-close-btn` | `<button>` | [`frontend/index.html#L948`](/frontend/index.html#L948) |
| `#deep-support-val` | `<strong>` | [`frontend/index.html#L964`](/frontend/index.html#L964) |
| `#deep-resistance-val` | `<strong>` | [`frontend/index.html#L965`](/frontend/index.html#L965) |
| `#deep-chart-container` | `<div>` | [`frontend/index.html#L968`](/frontend/index.html#L968) |
| `#deep-trend-chart-mount` | `<div>` | [`frontend/index.html#L969`](/frontend/index.html#L969) |
| `#deep-chart-tooltip` | `<div>` | [`frontend/index.html#L970`](/frontend/index.html#L970) |
| `#fundamentals-grid` | `<div>` | [`frontend/index.html#L983`](/frontend/index.html#L983) |
| `#fund-pe` | `<strong>` | [`frontend/index.html#L984`](/frontend/index.html#L984) |
| `#fund-eps` | `<strong>` | [`frontend/index.html#L985`](/frontend/index.html#L985) |
| `#fund-nav` | `<strong>` | [`frontend/index.html#L986`](/frontend/index.html#L986) |
| `#fund-mcap` | `<strong>` | [`frontend/index.html#L987`](/frontend/index.html#L987) |
| `#fund-div` | `<strong>` | [`frontend/index.html#L988`](/frontend/index.html#L988) |
| `#fund-paidup` | `<strong>` | [`frontend/index.html#L989`](/frontend/index.html#L989) |
| `#fund-52w` | `<strong>` | [`frontend/index.html#L990`](/frontend/index.html#L990) |
| `#fund-cat` | `<strong>` | [`frontend/index.html#L991`](/frontend/index.html#L991) |
| `#modal-sim-name` | `<span>` | [`frontend/index.html#L1001`](/frontend/index.html#L1001) |
| `#modal-sim-target-price` | `<strong>` | [`frontend/index.html#L1006`](/frontend/index.html#L1006) |
| `#modal-sim-target-pct` | `<span>` | [`frontend/index.html#L1007`](/frontend/index.html#L1007) |
| `#modal-sim-slider` | `<input>` | [`frontend/index.html#L1010`](/frontend/index.html#L1010) |
| `#modal-sim-gross` | `<strong>` | [`frontend/index.html#L1019`](/frontend/index.html#L1019) |
| `#modal-sim-fee` | `<strong>` | [`frontend/index.html#L1020`](/frontend/index.html#L1020) |
| `#modal-sim-net-pnl` | `<strong>` | [`frontend/index.html#L1021`](/frontend/index.html#L1021) |
| `#modal-sim-return-pct` | `<strong>` | [`frontend/index.html#L1022`](/frontend/index.html#L1022) |
| `#operator-modal` | `<dialog>` | [`frontend/index.html#L1031`](/frontend/index.html#L1031) |
| `#op-title` | `<h2>` | [`frontend/index.html#L1036`](/frontend/index.html#L1036) |
| `#op-close-btn` | `<button>` | [`frontend/index.html#L1038`](/frontend/index.html#L1038) |
| `#op-name` | `<strong>` | [`frontend/index.html#L1044`](/frontend/index.html#L1044) |
| `#op-username` | `<span>` | [`frontend/index.html#L1045`](/frontend/index.html#L1045) |
| `#op-portfolio` | `<span>` | [`frontend/index.html#L1046`](/frontend/index.html#L1046) |
| `#lock-cockpit-btn` | `<button>` | [`frontend/index.html#L1064`](/frontend/index.html#L1064) |
| `#login-gate-overlay` | `<dialog>` | [`frontend/index.html#L1073`](/frontend/index.html#L1073) |
| `#login-title` | `<h2>` | [`frontend/index.html#L1077`](/frontend/index.html#L1077) |
| `#login-form` | `<form>` | [`frontend/index.html#L1080`](/frontend/index.html#L1080) |
| `#login-username` | `<input>` | [`frontend/index.html#L1083`](/frontend/index.html#L1083) |
| `#login-password` | `<input>` | [`frontend/index.html#L1087`](/frontend/index.html#L1087) |
| `#login-error-msg` | `<div>` | [`frontend/index.html#L1089`](/frontend/index.html#L1089) |
| `#login-submit-btn` | `<button>` | [`frontend/index.html#L1091`](/frontend/index.html#L1091) |
| `#login-autofill-btn` | `<button>` | [`frontend/index.html#L1092`](/frontend/index.html#L1092) |
| `#toast` | `<div>` | [`frontend/index.html#L1101`](/frontend/index.html#L1101) |


### 6.4 JavaScript Controllers & UI Functions (`frontend/app.js`, `charts.js`, `hermes_ui.js`)

Complete index of all **115** JavaScript controller and rendering functions:

| Function | Module File | Line | Role / Category |
| :--- | :--- | :--- | :--- |
| `$()` | [`frontend/app.js`](/frontend/app.js#L11) | `L11` | UI Controller |
| `formatTimestamp()` | [`frontend/app.js`](/frontend/app.js#L18) | `L18` | Formatter / Utility |
| `element()` | [`frontend/app.js`](/frontend/app.js#L59) | `L59` | UI Controller |
| `svgElement()` | [`frontend/app.js`](/frontend/app.js#L66) | `L66` | UI Controller |
| `currency()` | [`frontend/app.js`](/frontend/app.js#L72) | `L72` | UI Controller |
| `percentage()` | [`frontend/app.js`](/frontend/app.js#L79) | `L79` | UI Controller |
| `sessionDate()` | [`frontend/app.js`](/frontend/app.js#L84) | `L84` | UI Controller |
| `setText()` | [`frontend/app.js`](/frontend/app.js#L88) | `L88` | DOM Updater / State Sync |
| `setPnl()` | [`frontend/app.js`](/frontend/app.js#L93) | `L93` | DOM Updater / State Sync |
| `tone()` | [`frontend/app.js`](/frontend/app.js#L101) | `L101` | UI Controller |
| `badge()` | [`frontend/app.js`](/frontend/app.js#L111) | `L111` | UI Controller |
| `notify()` | [`frontend/app.js`](/frontend/app.js#L139) | `L139` | UI Controller |
| `showError()` | [`frontend/app.js`](/frontend/app.js#L158) | `L158` | UI Controller |
| `api()` | [`frontend/app.js`](/frontend/app.js#L165) | `L165` | API Client / Ingestion |
| `updateControls()` | [`frontend/app.js`](/frontend/app.js#L202) | `L202` | DOM Updater / State Sync |
| `refresh()` | [`frontend/app.js`](/frontend/app.js#L242) | `L242` | UI Controller |
| `mutate()` | [`frontend/app.js`](/frontend/app.js#L258) | `L258` | UI Controller |
| `isLiveSource()` | [`frontend/app.js`](/frontend/app.js#L267) | `L267` | UI Controller |
| `renderPortfolioHeaderBadge()` | [`frontend/app.js`](/frontend/app.js#L279) | `L279` | DOM Renderer |
| `renderSnapshot()` | [`frontend/app.js`](/frontend/app.js#L343) | `L343` | DOM Renderer |
| `renderEquitySparkline()` | [`frontend/app.js`](/frontend/app.js#L416) | `L416` | DOM Renderer |
| `renderActiveHoldings()` | [`frontend/app.js`](/frontend/app.js#L430) | `L430` | DOM Renderer |
| `renderBuckets()` | [`frontend/app.js`](/frontend/app.js#L613) | `L613` | DOM Renderer |
| `cell()` | [`frontend/app.js`](/frontend/app.js#L645) | `L645` | UI Controller |
| `selectCompany()` | [`frontend/app.js`](/frontend/app.js#L647) | `L647` | Event Handler / State Transition |
| `formatCompactNumber()` | [`frontend/app.js`](/frontend/app.js#L654) | `L654` | Formatter / Utility |
| `renderWatchlist()` | [`frontend/app.js`](/frontend/app.js#L662) | `L662` | DOM Renderer |
| `renderCanaryTheses()` | [`frontend/app.js`](/frontend/app.js#L919) | `L919` | DOM Renderer |
| `renderInspector()` | [`frontend/app.js`](/frontend/app.js#L953) | `L953` | DOM Renderer |
| `isBuyDecision()` | [`frontend/app.js`](/frontend/app.js#L988) | `L988` | UI Controller |
| `isSellDecision()` | [`frontend/app.js`](/frontend/app.js#L994) | `L994` | UI Controller |
| `isLockDecision()` | [`frontend/app.js`](/frontend/app.js#L1000) | `L1000` | UI Controller |
| `isBlockedDecision()` | [`frontend/app.js`](/frontend/app.js#L1017) | `L1017` | UI Controller |
| `renderDecisions()` | [`frontend/app.js`](/frontend/app.js#L1040) | `L1040` | DOM Renderer |
| `renderLedger()` | [`frontend/app.js`](/frontend/app.js#L1126) | `L1126` | DOM Renderer |
| `initMarketMapResizeObserver()` | [`frontend/app.js`](/frontend/app.js#L1303) | `L1303` | UI Controller |
| `initTheme()` | [`frontend/app.js`](/frontend/app.js#L1329) | `L1329` | UI Controller |
| `setTheme()` | [`frontend/app.js`](/frontend/app.js#L1335) | `L1335` | DOM Updater / State Sync |
| `toggleTheme()` | [`frontend/app.js`](/frontend/app.js#L1346) | `L1346` | Event Handler / State Transition |
| `tickMarketClock()` | [`frontend/app.js`](/frontend/app.js#L1352) | `L1352` | UI Controller |
| `tickClock()` | [`frontend/app.js`](/frontend/app.js#L1434) | `L1434` | UI Controller |
| `renderAutomationControlBar()` | [`frontend/app.js`](/frontend/app.js#L1443) | `L1443` | DOM Renderer |
| `setAutomationConfig()` | [`frontend/app.js`](/frontend/app.js#L1784) | `L1784` | DOM Updater / State Sync |
| `setHandoffPendingState()` | [`frontend/app.js`](/frontend/app.js#L1907) | `L1907` | DOM Updater / State Sync |
| `executeRunModeHandoff()` | [`frontend/app.js`](/frontend/app.js#L1925) | `L1925` | UI Controller |
| `executeHandoff()` | [`frontend/app.js`](/frontend/app.js#L1950) | `L1950` | UI Controller |
| `switchToLiveHours()` | [`frontend/app.js`](/frontend/app.js#L2051) | `L2051` | Event Handler / State Transition |
| `switchToTestMode()` | [`frontend/app.js`](/frontend/app.js#L2060) | `L2060` | Event Handler / State Transition |
| `initRealtimeStream()` | [`frontend/app.js`](/frontend/app.js#L2112) | `L2112` | UI Controller |
| `switchView()` | [`frontend/app.js`](/frontend/app.js#L2138) | `L2138` | Event Handler / State Transition |
| `initViewRouter()` | [`frontend/app.js`](/frontend/app.js#L2196) | `L2196` | UI Controller |
| `initScrollSpy()` | [`frontend/app.js`](/frontend/app.js#L2233) | `L2233` | UI Controller |
| `updateActiveNav()` | [`frontend/app.js`](/frontend/app.js#L2246) | `L2246` | DOM Updater / State Sync |
| `smoothCurvePath()` | [`frontend/charts.js`](/frontend/charts.js#L8) | `L8` | Canvas / Chart Geometry |
| `getBezierPointAtContinuousIndex()` | [`frontend/charts.js`](/frontend/charts.js#L31) | `L31` | Canvas / Chart Geometry |
| `renderMainChart()` | [`frontend/charts.js`](/frontend/charts.js#L63) | `L63` | DOM Renderer |
| `x()` | [`frontend/charts.js`](/frontend/charts.js#L93) | `L93` | UI Controller |
| `y()` | [`frontend/charts.js`](/frontend/charts.js#L94) | `L94` | UI Controller |
| `sparkline()` | [`frontend/charts.js`](/frontend/charts.js#L350) | `L350` | Canvas / Chart Geometry |
| `squarify()` | [`frontend/charts.js`](/frontend/charts.js#L366) | `L366` | Canvas / Chart Geometry |
| `layoutRow()` | [`frontend/charts.js`](/frontend/charts.js#L376) | `L376` | UI Controller |
| `worst()` | [`frontend/charts.js`](/frontend/charts.js#L423) | `L423` | UI Controller |
| `showTreemapTooltip()` | [`frontend/charts.js`](/frontend/charts.js#L460) | `L460` | Canvas / Chart Geometry |
| `hideTreemapTooltip()` | [`frontend/charts.js`](/frontend/charts.js#L473) | `L473` | Canvas / Chart Geometry |
| `renderMarketMap()` | [`frontend/charts.js`](/frontend/charts.js#L478) | `L478` | DOM Renderer |
| `renderTopSectorsChart()` | [`frontend/charts.js`](/frontend/charts.js#L657) | `L657` | DOM Renderer |
| `renderGainerChart()` | [`frontend/charts.js`](/frontend/charts.js#L817) | `L817` | DOM Renderer |
| `updateWhatIfSimulator()` | [`frontend/charts.js`](/frontend/charts.js#L822) | `L822` | DOM Updater / State Sync |
| `updateModalSimulator()` | [`frontend/charts.js`](/frontend/charts.js#L866) | `L866` | DOM Updater / State Sync |
| `openDeepTrendModal()` | [`frontend/charts.js`](/frontend/charts.js#L905) | `L905` | UI Controller |
| `closeDeepTrendModal()` | [`frontend/charts.js`](/frontend/charts.js#L1014) | `L1014` | UI Controller |
| `renderDeepTrendChart()` | [`frontend/charts.js`](/frontend/charts.js#L1024) | `L1024` | DOM Renderer |
| `x()` | [`frontend/charts.js`](/frontend/charts.js#L1052) | `L1052` | UI Controller |
| `y()` | [`frontend/charts.js`](/frontend/charts.js#L1053) | `L1053` | UI Controller |
| `initCharts()` | [`frontend/charts.js`](/frontend/charts.js#L1308) | `L1308` | Canvas / Chart Geometry |
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


### 6.5 Hermes Agent Plugin Tool Registry (`plugins/humming_bird/tools.py`)

Complete catalog of all **22** registered Hermes tools powering chat commands and UI interactions:

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


### 6.6 Frontend Stylesheets (`frontend/*.css`)

| Stylesheet File | Lines | Purpose |
| :--- | :--- | :--- |
| `styles.css` | 6550 | Core design tokens, layout & widgets |
| `theme_light_hermes.css` | 3018 | Daylight overrides & Hermes IDE sidebar |


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

---

## 7. Code Health & Complexity Radar

Functions requiring architectural attention (> 70 lines or nesting depth >= 4):


| File | Function / Method | Length (Lines) | Max Nesting Depth | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
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
| `backend/config.py` | `get_allowed_portfolios` | 18 | 4 | Acceptable; well-scoped logic |
| `backend/config.py` | `get_active_target_portfolio` | 17 | 4 | Acceptable; well-scoped logic |
| `backend/database.py` | `create_schema` | 106 | 4 | Decompose into sub-functions |
| `backend/engine/agent_actions.py` | `emergency_quarantine_and_canary` | 112 | 5 | Decompose into sub-functions |
| `backend/engine/agent_actions.py` | `check_canary_theses` | 31 | 4 | Acceptable; well-scoped logic |
| `backend/engine/agent_actions.py` | `execute_agentic_buy` | 93 | 3 | Acceptable; well-scoped logic |
| `backend/engine/agent_actions.py` | `execute_agentic_sell` | 111 | 3 | Decompose into sub-functions |
| `backend/engine/auto_trader.py` | `_dispatch_order` | 32 | 5 | Acceptable; well-scoped logic |
| `backend/engine/auto_trader.py` | `_run_cycle_internal` | 599 | 7 | Decompose into sub-functions |
| `backend/engine/auto_trader.py` | `advance_demo` | 38 | 5 | Acceptable; well-scoped logic |
| `backend/engine/checkpoint.py` | `rollback_last` | 110 | 3 | Decompose into sub-functions |
| `backend/engine/circuit_breaker.py` | `record_circuit_failure` | 94 | 4 | Acceptable; well-scoped logic |
| `backend/engine/curve_analyzer.py` | `analyze_curve` | 84 | 3 | Acceptable; well-scoped logic |
| `backend/engine/heartbeat.py` | `check_dead_man_switch` | 56 | 4 | Acceptable; well-scoped logic |
| `backend/engine/heartbeat.py` | `send_daily_summary_if_due` | 112 | 4 | Decompose into sub-functions |
| `backend/engine/price_guard.py` | `get_market_quote` | 28 | 4 | Acceptable; well-scoped logic |
| `backend/engine/price_guard.py` | `check_price_sanity` | 59 | 5 | Acceptable; well-scoped logic |
| `backend/engine/scheduler.py` | `is_dse_market_open` | 44 | 4 | Acceptable; well-scoped logic |
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
| `backend/logging_config.py` | `setup_logging` | 50 | 4 | Acceptable; well-scoped logic |
| `backend/logging_config.py` | `filter` | 12 | 4 | Acceptable; well-scoped logic |
| `backend/main.py` | `create_app` | 678 | 7 | Decompose into sub-functions |
| `backend/main.py` | `local_security` | 39 | 4 | Acceptable; well-scoped logic |
| `backend/main.py` | `cycle` | 38 | 6 | Acceptable; well-scoped logic |
| `backend/main.py` | `automation_handoff` | 55 | 7 | Acceptable; well-scoped logic |
| `backend/main.py` | `automation_config` | 89 | 5 | Acceptable; well-scoped logic |
| `backend/main.py` | `set_caps_public` | 86 | 4 | Acceptable; well-scoped logic |
| `backend/main.py` | `event_stream` | 26 | 4 | Acceptable; well-scoped logic |
| `backend/main.py` | `generator` | 13 | 4 | Acceptable; well-scoped logic |
| `backend/market_map.py` | `build_market_map_payload` | 72 | 5 | Acceptable; well-scoped logic |
| `backend/portfolio.py` | `snapshot_from_session` | 330 | 5 | Decompose into sub-functions |
| `backend/portfolio.py` | `normalized_watchlist` | 20 | 4 | Acceptable; well-scoped logic |
| `backend/routes_auth_settings.py` | `build_auth_settings_router` | 134 | 2 | Decompose into sub-functions |
| `backend/routes_hermes.py` | `build_hermes_router` | 175 | 5 | Decompose into sub-functions |
| `backend/routes_hermes.py` | `system_changes` | 73 | 5 | Acceptable; well-scoped logic |
| `backend/routes_hermes.py` | `switch_hermes_model` | 59 | 5 | Acceptable; well-scoped logic |
| `backend/routes_stocknow.py` | `build_stocknow_router` | 223 | 6 | Decompose into sub-functions |
| `backend/routes_stocknow.py` | `post_stocknow_session` | 57 | 6 | Acceptable; well-scoped logic |
| `backend/routes_stocknow.py` | `post_stocknow_scheduler` | 9 | 4 | Acceptable; well-scoped logic |
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
| `scripts/generate_code_map.py` | `parse_css_design` | 108 | 8 | Decompose into sub-functions |
| `scripts/generate_code_map.py` | `scan_file` | 50 | 8 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `parse_frontend` | 92 | 11 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `parse_plugin_tools` | 36 | 7 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `generate_markdown` | 216 | 6 | Decompose into sub-functions |
| `scripts/generate_code_map.py` | `visit_Call` | 10 | 4 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `_compute_depth` | 12 | 4 | Acceptable; well-scoped logic |
| `scripts/preflight.py` | `check_gateway` | 18 | 5 | Acceptable; well-scoped logic |
| `scripts/preflight.py` | `check_kernel_token` | 20 | 5 | Acceptable; well-scoped logic |
| `scripts/preflight.py` | `check_stocknow_session` | 69 | 5 | Acceptable; well-scoped logic |
| `scripts/preflight.py` | `check_portfolio_drift` | 34 | 4 | Acceptable; well-scoped logic |
| `scripts/preflight.py` | `check_trading_mode` | 23 | 4 | Acceptable; well-scoped logic |
| `scripts/restore_db.py` | `restore_database` | 88 | 4 | Acceptable; well-scoped logic |
| `scripts/verify_chat_card.py` | `main` | 121 | 3 | Decompose into sub-functions |


> **Audit Summary:** 50 Python modules inspected, 65 FastAPI endpoints registered, 115 JS functions mapped, 301 DOM IDs indexed, 22 Hermes tools registered, 93,180 total LOC indexed across 129 repository files.