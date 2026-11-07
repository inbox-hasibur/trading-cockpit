# 🗺️ Codebase AST Map & System Architecture Radar

> Auto-generated via `scripts/generate_code_map.py` (Zero-dependency stdlib AST inspection) on **2026-11-07 12:03:35 UTC**.

---

## 1. Repository Topology & File Metrics

| Extension / Type | File Count | Total Lines of Code | Description |
| :--- | :--- | :--- | :--- |
| `.py` | 72 | 13,771 | Python Core Kernel, Engine & Hermes Agent |
| `.png` | 3 | 11,100 | Configuration / Asset |
| `.css` | 2 | 8,429 | Custom Dark / Light / Terminal Design System |
| `.js` | 3 | 4,156 | Vanilla ES6+ Reactive Terminal Controller |
| `.md` | 13 | 3,146 | Architecture & Strategy Documentation |
| `.html` | 1 | 996 | Single Page Application DOM Structure |
| `.ps1` | 2 | 295 | Configuration / Asset |
| `.yaml` | 1 | 30 | Configuration / Asset |
| `.agentignore` | 1 | 12 | Configuration / Asset |
| `.cursorignore` | 1 | 12 | Configuration / Asset |
| `.opencodeignore` | 1 | 12 | Configuration / Asset |
| `.json` | 1 | 12 | Configuration / Asset |
| `.txt` | 2 | 11 | Dependency Specifications |
| `.toml` | 1 | 10 | PyProject Configuration |
| `.sh` | 1 | 9 | Configuration / Asset |
| `.bat` | 1 | 8 | Configuration / Asset |
| `.svg` | 1 | 1 | Configuration / Asset |
| `.db` | 1 | 0 | Configuration / Asset |
| **TOTAL** | **108** | **42,010** | *Entire Humming Bird Repository* |

## 2. Internal Dependency & Import Graph

Shows intra-repo module dependencies within `backend/` and `scripts/`:

| Module File | Imported Internal Dependencies |
| :--- | :--- |
| [`backend/__init__.py`](/backend/__init__.py) | *Independent Core Module* |
| [`backend/adapters/__init__.py`](/backend/adapters/__init__.py) | `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.adapters.stocknow_client.StockNowLiveClient`, `backend.adapters.stocknow_client.get_safe_profile_dir`, `backend.adapters.stocknow_market_sync.extract_quotes_from_payload`, `backend.adapters.stocknow_market_sync.extract_quotes_from_stocknow`, `backend.adapters.stocknow_market_sync.sync_live_market_to_db` |
| [`backend/adapters/stocknow_adapter.py`](/backend/adapters/stocknow_adapter.py) | `backend.adapters.stocknow_client.get_safe_profile_dir`, `backend.adapters.stocknow_order_executor.execute_stocknow_virtual_order`, `backend.database.CompanyProfile`, `backend.engine.money.ZERO`, `backend.engine.money.decimal` |
| [`backend/adapters/stocknow_client.py`](/backend/adapters/stocknow_client.py) | `backend.secret_guard.SecretGuard`, `backend.secret_guard.redact_secrets` |
| [`backend/adapters/stocknow_market_sync.py`](/backend/adapters/stocknow_market_sync.py) | `backend.adapters.stocknow_client.StockNowLiveClient`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.portfolio_state`, `backend.engine.money.ZERO`, `backend.engine.money.decimal`, `backend.portfolio.COMPANY_FUNDAMENTALS`, `backend.portfolio.DEFAULT_FUNDAMENTALS` |
| [`backend/adapters/stocknow_order_executor.py`](/backend/adapters/stocknow_order_executor.py) | `backend.adapters.stocknow_client.StockNowLiveClient` |
| [`backend/adapters/stocknow_portfolio_sync.py`](/backend/adapters/stocknow_portfolio_sync.py) | `backend.adapters.stocknow_client.StockNowLiveClient`, `backend.config.Settings`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.DecisionLog`, `backend.database.PortfolioState`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.engine.checkpoint.CheckpointManager`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.price`, `backend.engine.money.purchase_amount`, `backend.engine.t2_ledger.BUCKETS`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.assert_ledger` |
| [`backend/config.py`](/backend/config.py) | *Independent Core Module* |
| [`backend/database.py`](/backend/database.py) | `backend.config.utc_now_iso` |
| [`backend/engine/__init__.py`](/backend/engine/__init__.py) | *Independent Core Module* |
| [`backend/engine/agent_actions.py`](/backend/engine/agent_actions.py) | `backend.config.Settings`, `backend.database.CanaryThesis`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.DecisionLog`, `backend.database.PortfolioState`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.engine.money.ZERO`, `backend.engine.money.allocated_basis`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.price`, `backend.engine.money.purchase_amount`, `backend.engine.money.sale_amount`, `backend.engine.money.whole_shares`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.assert_ledger`, `backend.engine.t2_ledger.bucket_balances` |
| [`backend/engine/auto_trader.py`](/backend/engine/auto_trader.py) | `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.config.Settings`, `backend.database.AutomationCycle`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.CycleRequestKey`, `backend.database.Database`, `backend.database.DecisionLog`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.database.portfolio_state`, `backend.engine.agent_actions.check_canary_theses`, `backend.engine.money.HUNDRED`, `backend.engine.money.ZERO`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.price`, `backend.engine.money.purchase_amount`, `backend.engine.money.whole_shares`, `backend.engine.sequential_seller.SellState`, `backend.engine.sequential_seller.plan_sale`, `backend.engine.signals.BLOCK_ALL_TRADING`, `backend.engine.signals.assess_company`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.assert_ledger`, `backend.engine.t2_ledger.bucket_balances`, `backend.engine.trading_lock.acquire_trading_lock` |
| [`backend/engine/checkpoint.py`](/backend/engine/checkpoint.py) | `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.KernelStateCheckpoint`, `backend.database.PortfolioState`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.engine.money.decimal`, `backend.engine.t2_ledger.assert_ledger` |
| [`backend/engine/curve_analyzer.py`](/backend/engine/curve_analyzer.py) | `backend.engine.money.HUNDRED`, `backend.engine.money.ZERO`, `backend.engine.money.decimal` |
| [`backend/engine/money.py`](/backend/engine/money.py) | *Independent Core Module* |
| [`backend/engine/scheduler.py`](/backend/engine/scheduler.py) | `backend.adapters.stocknow_client.StockNowLiveClient`, `backend.adapters.stocknow_market_sync.extract_quotes_from_stocknow`, `backend.adapters.stocknow_market_sync.sync_live_market_to_db`, `backend.config.DHAKA`, `backend.config.Settings`, `backend.database.Database`, `backend.database.portfolio_state`, `backend.engine.auto_trader.AutoTrader`, `backend.engine.t2_ledger.TradingCalendar`, `backend.portfolio.build_snapshot` |
| [`backend/engine/sequential_seller.py`](/backend/engine/sequential_seller.py) | `backend.engine.money.HUNDRED`, `backend.engine.money.ZERO`, `backend.engine.money.allocated_basis`, `backend.engine.money.sale_amount`, `backend.engine.money.whole_shares` |
| [`backend/engine/signals.py`](/backend/engine/signals.py) | `backend.adapters.stocknow_adapter.DemoQuote`, `backend.adapters.stocknow_adapter.QuoteError`, `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.config.Settings`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.engine.curve_analyzer.CurveAnalysis`, `backend.engine.curve_analyzer.analyze_curve`, `backend.engine.money.decimal` |
| [`backend/engine/t2_ledger.py`](/backend/engine/t2_ledger.py) | `backend.database.PortfolioState`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.engine.money.CENT`, `backend.engine.money.ZERO`, `backend.engine.money.money` |
| [`backend/engine/trading_lock.py`](/backend/engine/trading_lock.py) | *Independent Core Module* |
| [`backend/hermes_bridge.py`](/backend/hermes_bridge.py) | *Independent Core Module* |
| [`backend/kernel_api.py`](/backend/kernel_api.py) | `backend.adapters.stocknow_market_sync.extract_quotes_from_stocknow`, `backend.adapters.stocknow_market_sync.get_or_fetch_all_dse_shares`, `backend.adapters.stocknow_market_sync.sync_live_market_to_db`, `backend.adapters.stocknow_portfolio_sync.reconcile_portfolio_to_db`, `backend.config.Settings`, `backend.database.CanaryThesis`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.KernelAuditLog`, `backend.database.PortfolioState`, `backend.database.RuleAudit`, `backend.database.TaxLot`, `backend.database.portfolio_state`, `backend.engine.agent_actions.check_canary_theses`, `backend.engine.agent_actions.emergency_quarantine_and_canary`, `backend.engine.agent_actions.execute_agentic_buy`, `backend.engine.agent_actions.execute_agentic_sell`, `backend.engine.agent_actions.restore_quarantine`, `backend.engine.auto_trader.AutoTrader`, `backend.engine.checkpoint.CheckpointManager`, `backend.engine.curve_analyzer.analyze_curve`, `backend.engine.money.ZERO`, `backend.engine.money.allocated_basis`, `backend.engine.money.purchase_amount`, `backend.engine.money.sale_amount`, `backend.engine.scheduler.get_active_scheduler`, `backend.engine.scheduler.is_dse_market_open`, `backend.engine.trading_lock.acquire_trading_lock`, `backend.portfolio.snapshot_from_session`, `backend.seed.seed_demo` |
| [`backend/main.py`](/backend/main.py) | `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.adapters.stocknow_client.StockNowLiveClient`, `backend.adapters.stocknow_market_sync.extract_quotes_from_stocknow`, `backend.adapters.stocknow_market_sync.sync_live_market_to_db`, `backend.config.ROOT`, `backend.config.Settings`, `backend.config.VERSION`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.RuleAudit`, `backend.database.portfolio_state`, `backend.engine.auto_trader.AutoTrader`, `backend.engine.auto_trader.AutomationPaused`, `backend.engine.money.ZERO`, `backend.engine.scheduler.DSEMarketScheduler`, `backend.hermes_bridge.build_hermes_bridge_router`, `backend.kernel_api.build_kernel_router`, `backend.market_map.build_market_map_payload`, `backend.portfolio.build_snapshot`, `backend.portfolio.rule_view`, `backend.routes_auth_settings.KeysSettingsRequest`, `backend.routes_auth_settings.LoginRequest`, `backend.routes_auth_settings.build_auth_settings_router`, `backend.routes_hermes.CreateThreadRequest`, `backend.routes_hermes.build_hermes_router`, `backend.routes_stocknow.build_stocknow_router`, `backend.seed.migrate_real_stocknow_market`, `backend.seed.seed_demo` |
| [`backend/market_map.py`](/backend/market_map.py) | *Independent Core Module* |
| [`backend/portfolio.py`](/backend/portfolio.py) | `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.adapters.stocknow_market_sync._ALL_DSE_SHARES_CACHE`, `backend.config.DHAKA`, `backend.config.Settings`, `backend.config.VERSION`, `backend.database.AutomationCycle`, `backend.database.CanaryThesis`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.DecisionLog`, `backend.database.KernelStateCheckpoint`, `backend.database.RuleAudit`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.database.portfolio_state`, `backend.engine.money.HUNDRED`, `backend.engine.money.ZERO`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.sale_amount`, `backend.engine.signals.assess_company`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.bucket_balances`, `backend.market_map.build_market_map_payload` |
| [`backend/routes_auth_settings.py`](/backend/routes_auth_settings.py) | `backend.config.DHAKA`, `backend.config.Settings`, `backend.database.Database`, `backend.database.portfolio_state`, `backend.engine.checkpoint.CheckpointManager` |
| [`backend/routes_hermes.py`](/backend/routes_hermes.py) | `backend.config.Settings`, `backend.database.Database`, `backend.database.KernelStateCheckpoint`, `backend.database.RuleAudit` |
| [`backend/routes_stocknow.py`](/backend/routes_stocknow.py) | `backend.adapters.stocknow_client.StockNowLiveClient`, `backend.adapters.stocknow_market_sync.extract_quotes_from_stocknow`, `backend.adapters.stocknow_market_sync.get_or_fetch_all_dse_shares`, `backend.adapters.stocknow_market_sync.sync_live_market_to_db`, `backend.adapters.stocknow_order_executor.execute_stocknow_virtual_order`, `backend.adapters.stocknow_portfolio_sync.extract_hummingbird_portfolio`, `backend.adapters.stocknow_portfolio_sync.extract_hummingbird_portfolio_from_browser`, `backend.adapters.stocknow_portfolio_sync.reconcile_portfolio_to_db`, `backend.config.Settings`, `backend.database.CompanyProfile`, `backend.database.Database`, `backend.database.PortfolioState`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.engine.agent_actions.execute_agentic_buy`, `backend.engine.agent_actions.execute_agentic_sell`, `backend.engine.checkpoint.CheckpointManager`, `backend.engine.scheduler.DSEMarketScheduler`, `backend.engine.scheduler.get_active_scheduler`, `backend.portfolio.build_snapshot` |
| [`backend/secret_guard.py`](/backend/secret_guard.py) | *Independent Core Module* |
| [`backend/seed.py`](/backend/seed.py) | `backend.config.DHAKA`, `backend.config.Settings`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.DecisionLog`, `backend.database.PortfolioState`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.price`, `backend.engine.money.purchase_amount`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.assert_ledger`, `backend.engine.t2_ledger.bucket_balances` |
| [`scripts/check_dse_market_open.py`](/scripts/check_dse_market_open.py) | *Independent Core Module* |
| [`scripts/generate_code_map.py`](/scripts/generate_code_map.py) | *Independent Core Module* |
| [`scripts/migrate_drop_hermes_tables.py`](/scripts/migrate_drop_hermes_tables.py) | *Independent Core Module* |

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
| `StockNowAdapter` | `L32–L126` | `object` | Sprint 1's explicitly synthetic data/paper-fill boundary. | 6 |
| `StockNowBrowserSession` | `L129–L155` | `object` | Opt-in persistent browser foundation, not a login or order implementation. | 2 |


**Methods in `StockNowAdapter`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L35–L37` | `(self, mode: str='DEMO'...)` | — | — | — |
| `quote` | `L39–L53` | `(self, company: CompanyProfile, as_o...)` | `DemoQuote` | — | `DemoQuote`, `QuoteError`, `decimal`, `is_finite` |
| `paper_fill` | `L55–L58` | `(self, quote: DemoQuote, quantity: i...)` | `Decimal` | — | `ValueError` |
| `read_virtual_portfolio` | `L60–L61` | `(self...)` | — | — | `LiveIntegrationNotImplemented` |
| `execute_order` | `L63–L89` | `(self, symbol: str, side: str, quant...)` | `dict` | — | `Decimal`, `execute_stocknow_virtual_order` |
| `get_adapter_status` | `L91–L126` | `(self, ingestion_mode: str='BACKGROU...)` | `dict` | — | `get`, `get_safe_profile_dir`, `get_status`, `getattr` |


**Methods in `StockNowBrowserSession`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L137–L138` | `(self, profile_directory: Path...)` | — | — | — |
| `open` | `L141–L155` | `(self...)` | — | — | `async_playwright`, `close`, `launch_persistent_context`, `mkdir` |


---

### 📄 [`backend/adapters/stocknow_client.py`](/backend/adapters/stocknow_client.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `StockNowLiveClient` | `L81–L590` | `object` | Persistent Playwright browser controller, auto-login assistant & XHR network sniffer. | 13 |


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
| `discover_portfolio` | `L492–L494` | `(self...)` | `dict[str, Any]` | Discover 'Humming Bird' portfolio stats and ID from /portfolios. | `_discover_portfolio_internal`, `_run_in_proactor` |
| `_discover_portfolio_internal` | `L496–L561` | `(self...)` | `dict[str, Any]` | — | `debug`, `evaluate`, `format_exception_str`, `get` |
| `get_status` | `L563–L590` | `(self...)` | `dict[str, Any]` | Return structured telemetry for live session status endpoint. | `hasattr`, `is_closed`, `keys`, `len` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `format_exception_str` | `L34–L37` | `(e: Exception | BaseException...)` | `str` | Format exception to guarantee non-empty diagnostic message. | `repr`, `str`, `strip`, `type` |
| `_create_proactor_loop` | `L40–L47` | `(...)` | `asyncio.AbstractEventLoop` | Create a new ProactorEventLoop on Windows or standard event loop on POSIX. | `WindowsProactorEventLoopPolicy`, `getattr`, `new_event_loop` |
| `get_safe_profile_dir` | `L50–L68` | `(custom_path: Path | str | None=None...)` | `Path` | Resolve an isolated Playwright profile directory outside OneDrive. | `Path`, `expanduser`, `lower`, `resolve` |
| `mask_phone` | `L71–L78` | `(phone: str...)` | `str` | Mask phone number for safe display and logging without revealing identity. | `isdigit`, `join`, `len`, `str` |


---

### 📄 [`backend/adapters/stocknow_market_sync.py`](/backend/adapters/stocknow_market_sync.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `_parse_positive_decimal` | `L32–L41` | `(val: Any...)` | `Decimal | None` | — | `decimal`, `is_finite`, `replace`, `str` |
| `_normalize_history_series` | `L44–L59` | `(raw_history: Any, fallback_price: D...)` | `list[dict[str, str]]` | Normalize 7-30 session curve observations into [{"date": "YYYY-MM-DD", "close": "XX.XX"}]. | `_parse_positive_decimal`, `append`, `get`, `isinstance` |
| `_extract_fundamentals_from_dict` | `L62–L123` | `(item: dict[str, Any]...)` | `dict[str, Any]` | — | `dict`, `float`, `get`, `int` |
| `extract_quotes_from_payload` | `L126–L213` | `(payload: Any, as_of_date: date | No...)` | `list[dict[str, Any]]` | Extract and normalize quotes from an arbitrary JSON payload. | `_extract_fundamentals_from_dict`, `_normalize_history_series`, `_parse_positive_decimal`, `append` |
| `fetch_stocknow_live_market_data` | `L221–L392` | `(client: Any=None...)` | `list[dict[str, Any]]` | Fetches real-time market data directly from stocknow.com.bd API. | `AsyncClient`, `Decimal`, `append`, `debug` |
| `fetch_hist` | `L340–L356` | `(sym: str...)` | `tuple[str, list[dict[str, str]]]` | — | `date`, `debug`, `fromtimestamp`, `get` |
| `get_or_fetch_all_dse_shares` | `L395–L407` | `(client: Any=None...)` | `dict[str, Any]` | Returns cached All DSE Shares catalog, populating it if not yet loaded. | `fetch_stocknow_live_market_data`, `isoformat`, `len`, `now` |
| `extract_quotes_from_stocknow` | `L410–L415` | `(client: Any, injected_payload: Any=...)` | `list[dict[str, Any]]` | Extracts live DSE ticker quotes from sniffer cache, page DOM or injected payload. | `_extract_quotes_from_stocknow_impl`, `_run_in_proactor`, `hasattr`, `isinstance` |
| `_extract_quotes_from_stocknow_impl` | `L418–L580` | `(client: Any, injected_payload: Any=...)` | `list[dict[str, Any]]` | — | `debug`, `evaluate`, `extract_quotes_from_payload`, `fetch_stocknow_live_market_data` |
| `_sync_in_session` | `L583–L680` | `(session: Any, quotes: list[dict[str...)` | `dict[str, Any]` | — | `CompanyProfile`, `CustomRule`, `add`, `append` |
| `sync_live_market_to_db` | `L683–L692` | `(target: Database | Any, quotes: lis...)` | `dict[str, Any]` | Synchronizes extracted live quotes into SQLite CompanyProfile records. | `_sync_in_session`, `hasattr`, `write` |


---

### 📄 [`backend/adapters/stocknow_order_executor.py`](/backend/adapters/stocknow_order_executor.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `clear_idempotency_cache` | `L18–L20` | `(...)` | `None` | Clear in-memory deduplication cache (for testing isolation). | `clear` |
| `execute_stocknow_virtual_order` | `L23–L61` | `(client: Any | None=None, symbol: st...)` | `dict[str, Any]` | Execute a virtual transaction for 'Humming Bird' portfolio with idempotency. | `Decimal`, `_execute_stocknow_virtual_order_impl`, `_run_in_proactor`, `hasattr` |
| `_execute_stocknow_virtual_order_impl` | `L64–L283` | `(client: Any | None=None, symbol: st...)` | `dict[str, Any]` | — | `Decimal`, `ValueError`, `_ensure_authenticated_internal`, `click` |


---

### 📄 [`backend/adapters/stocknow_portfolio_sync.py`](/backend/adapters/stocknow_portfolio_sync.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `parse_stocknow_ledger_date` | `L22–L43` | `(date_str: str...)` | `str` | Parse StockNow DD/MM/YY date string into YYYY-MM-DD ISO date. | `date`, `fromisoformat`, `group`, `int` |
| `_match_portfolio_name` | `L46–L47` | `(name: str...)` | `bool` | — | `lower`, `replace`, `strip` |
| `_find_portfolio_dict` | `L50–L66` | `(data: Any...)` | `dict[str, Any] | None` | — | `_find_portfolio_dict`, `_match_portfolio_name`, `get`, `isinstance` |
| `extract_hummingbird_portfolio` | `L69–L127` | `(client: Any | None=None, injected_p...)` | `dict[str, Any]` | Locate and extract 'Humming Bird' virtual portfolio from client or payload. | `Decimal`, `ValueError`, `_find_portfolio_dict`, `append` |
| `extract_hummingbird_portfolio_from_browser` | `L130–L135` | `(client: Any...)` | `dict[str, Any]` | Scrapes /portfolios/{id}/show and /portfolios/{id}/ledger from live Playwright session. | `_extract_hummingbird_portfolio_from_browser_impl`, `_run_in_proactor`, `hasattr`, `isinstance` |
| `_extract_hummingbird_portfolio_from_browser_impl` | `L138–L260` | `(client: Any...)` | `dict[str, Any]` | — | `RuntimeError`, `append`, `debug`, `decimal` |
| `_execute_reconciliation` | `L263–L382` | `(session: Session, settings: Setting...)` | `dict[str, Any]` | — | `CompanyProfile`, `CustomRule`, `Decimal`, `RuntimeError` |
| `reconcile_portfolio_to_db` | `L385–L392` | `(target: Database | Session, setting...)` | `dict[str, Any]` | Reconcile virtual portfolio holdings and cash balance into SQLite ledger. | `_execute_reconciliation`, `isinstance`, `write` |


---

### 📄 [`backend/config.py`](/backend/config.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `Settings` | `L25–L131` | `object` | — | 5 |


**Methods in `Settings`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `operator_phone` | `L53–L54` | `(self...)` | `str` | — | — |
| `stocknow_mobile` | `L57–L58` | `(self...)` | `str` | — | — |
| `stocknow_password` | `L61–L62` | `(self...)` | `str` | — | — |
| `__post_init__` | `L64–L88` | `(self...)` | `None` | — | `Decimal`, `ValueError`, `any`, `is_finite` |
| `from_env` | `L91–L131` | `(cls...)` | `Settings` | — | `Decimal`, `cls`, `fromisoformat`, `frozenset` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `utc_now_iso` | `L20–L21` | `(...)` | `str` | — | `isoformat`, `now` |


---

### 📄 [`backend/database.py`](/backend/database.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `Base` | `L37–L38` | `DeclarativeBase` | — | 0 |
| `PortfolioState` | `L41–L58` | `Base` | — | 0 |
| `CompanyProfile` | `L61–L74` | `Base` | — | 0 |
| `CustomRule` | `L77–L88` | `Base` | — | 0 |
| `TaxLot` | `L91–L116` | `Base` | — | 0 |
| `AutomationCycle` | `L119–L128` | `Base` | — | 0 |
| `TradeLog` | `L131–L156` | `Base` | — | 0 |
| `CanaryThesis` | `L159–L171` | `Base` | — | 0 |
| `KernelStateCheckpoint` | `L174–L184` | `Base` | — | 0 |
| `CycleRequestKey` | `L187–L190` | `Base` | — | 0 |
| `DecisionLog` | `L193–L203` | `Base` | — | 0 |
| `RuleAudit` | `L206–L214` | `Base` | — | 0 |
| `KernelAuditLog` | `L217–L228` | `Base` | — | 0 |
| `ChatBudget` | `L231–L234` | `Base` | — | 0 |
| `Database` | `L237–L328` | `object` | — | 5 |


**Methods in `Database`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L238–L258` | `(self, url: str...)` | — | — | `Path`, `RLock`, `ValueError`, `create_engine` |
| `configure_sqlite` | `L251–L256` | `(connection: Any, _record: Any...)` | `None` | — | `close`, `cursor`, `execute`, `listens_for` |
| `create_schema` | `L260–L307` | `(self...)` | `None` | — | `commit`, `connect`, `create_all`, `execute` |
| `read` | `L310–L317` | `(self...)` | — | — | `execute`, `rollback`, `sessions`, `text` |
| `write` | `L320–L328` | `(self...)` | — | — | `commit`, `execute`, `rollback`, `sessions` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `portfolio_state` | `L331–L335` | `(session: Session...)` | `PortfolioState` | — | `RuntimeError`, `get` |


---

### 📄 [`backend/engine/__init__.py`](/backend/engine/__init__.py)

---

### 📄 [`backend/engine/agent_actions.py`](/backend/engine/agent_actions.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `emergency_quarantine_and_canary` | `L25–L130` | `(session: Session, state: PortfolioS...)` | `dict` | — | `CanaryThesis`, `Decimal`, `TradeLog`, `TradingCalendar` |
| `restore_quarantine` | `L133–L161` | `(session: Session, state: PortfolioS...)` | `dict` | — | `ValueError`, `flush`, `get`, `len` |
| `check_canary_theses` | `L164–L194` | `(session: Session, state: PortfolioS...)` | `list[dict]` | — | `Decimal`, `append`, `float`, `flush` |
| `execute_agentic_buy` | `L197–L279` | `(session: Session, state: PortfolioS...)` | `dict` | — | `Decimal`, `TaxLot`, `TradeLog`, `TradingCalendar` |
| `execute_agentic_sell` | `L282–L382` | `(session: Session, state: PortfolioS...)` | `dict` | — | `Decimal`, `TradeLog`, `TradingCalendar`, `ValueError` |
| `cycle_key` | `L385–L386` | `(state: PortfolioState...)` | `str` | — | — |


---

### 📄 [`backend/engine/auto_trader.py`](/backend/engine/auto_trader.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `AutomationPaused` | `L36–L37` | `ValueError` | — | 0 |
| `AutoTrader` | `L40–L360` | `object` | — | 7 |


**Methods in `AutoTrader`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L41–L45` | `(self, database: Database, settings:...)` | — | — | `StockNowAdapter`, `TradingCalendar` |
| `run_cycle` | `L47–L52` | `(self, request_id: str | None=None, ...)` | `dict` | — | `_run_cycle_internal`, `acquire_trading_lock`, `write` |
| `_run_cycle_internal` | `L54–L312` | `(self, session: Session, request_id:...)` | `dict` | — | `AutomationCycle`, `AutomationPaused`, `CycleRequestKey`, `Decimal` |
| `record` | `L91–L99` | `(symbol: str, action: str, reason: s...)` | — | — | `DecisionLog`, `add`, `append` |
| `buy_priority` | `L204–L210` | `(comp: CompanyProfile...)` | `tuple[int, str]` | — | `getattr` |
| `_trade_result` | `L315–L321` | `(trade: TradeLog, action: str...)` | `dict` | — | `float` |
| `advance_demo` | `L323–L360` | `(self, scenario: str...)` | `dict` | — | `Decimal`, `ValueError`, `add_sessions`, `assert_ledger` |


---

### 📄 [`backend/engine/checkpoint.py`](/backend/engine/checkpoint.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `CheckpointManager` | `L25–L183` | `object` | Manages transactional state checkpoints and atomic rollback restoration. | 2 |


**Methods in `CheckpointManager`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `create_checkpoint` | `L29–L81` | `(session: Session, state: PortfolioS...)` | `KernelStateCheckpoint` | — | `KernelStateCheckpoint`, `add`, `flush`, `get` |
| `rollback_last` | `L84–L183` | `(session: Session, state: PortfolioS...)` | `dict[str, Any]` | — | `TaxLot`, `TradeLog`, `ValueError`, `add` |


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
| `analyze_curve` | `L34–L115` | `(history: list[dict[str, str]], *, a...)` | `CurveAnalysis` | — | `CurveAnalysis`, `Decimal`, `ValueError`, `abs` |


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

### 📄 [`backend/engine/scheduler.py`](/backend/engine/scheduler.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `DSEMarketScheduler` | `L81–L291` | `object` | Async background scheduler enforcing DSE market hours and periodic trading cycles. | 8 |


**Methods in `DSEMarketScheduler`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L84–L106` | `(self, database: Database, settings:...)` | — | — | `AutoTrader`, `hasattr` |
| `get_status` | `L108–L129` | `(self...)` | `dict[str, Any]` | Returns scheduler operational status, telemetry, and DSE market gate. | `getattr`, `is_dse_market_open`, `portfolio_state`, `read` |
| `run_scheduled_tick` | `L131–L189` | `(self, force: bool=False...)` | `dict[str, Any]` | Executes a single scheduler tick, enforcing gate & automation state unless force=True. | `build_snapshot`, `debug`, `extract_quotes_from_stocknow`, `get` |
| `run_scheduled_tick_sync` | `L191–L243` | `(self, force: bool=False, session: A...)` | `dict[str, Any]` | Synchronous version of tick execution (e.g. for Hermes chat turn). | `build_snapshot`, `debug`, `getattr`, `info` |
| `start` | `L245–L255` | `(self...)` | `dict[str, Any]` | Starts background periodic polling loop. | `_loop`, `create_task`, `get_running_loop`, `get_status` |
| `stop_sync` | `L257–L265` | `(self...)` | `dict[str, Any]` | Stops background periodic polling loop gracefully (sync). | `cancel`, `done`, `get_status` |
| `stop` | `L267–L269` | `(self...)` | `dict[str, Any]` | Stops background periodic polling loop gracefully. | `stop_sync` |
| `_loop` | `L271–L291` | `(self...)` | `None` | Background periodic execution loop respecting configured polling interval. | `error`, `getattr`, `info`, `max` |


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
| `assess_company` | `L15–L42` | `(company: CompanyProfile, rule: Cust...)` | `tuple[CurveAnalysis, DemoQuote | None]` | — | `CurveAnalysis`, `analyze_curve`, `decimal`, `quote` |


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
| `bucket_balances` | `L66–L96` | `(session: Session, state: PortfolioS...)` | `dict[str, BucketBalance]` | — | `BucketBalance`, `RuntimeError`, `items`, `money` |
| `assert_ledger` | `L99–L110` | `(session: Session, state: PortfolioS...)` | `None` | Book assets must equal initial capital plus realized P/L, to the paisa. | `RuntimeError`, `bucket_balances`, `money`, `scalars` |


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
| `BridgeChatRequest` | `L53–L56` | `BaseModel` | — | 0 |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `get_hermes_dir` | `L28–L40` | `(...)` | `Path` | Returns the Hermes home directory (hummingbird profile if available, else ~/.hermes). | `Path`, `exists`, `get`, `home` |
| `get_hermes_bin` | `L43–L50` | `(...)` | `str` | Returns path to the hermes executable. | `Path`, `exists`, `get`, `str` |
| `stream_hermes_chat` | `L59–L114` | `(message: str, session_id: Optional[...)` | `AsyncGenerator[str, None]` | Streams SSE events from running Hermes gateway API server. | `AsyncClient`, `aiter_lines`, `append`, `aread` |
| `read_hermes_state` | `L117–L263` | `(...)` | `dict[str, Any]` | Reads skills, memory (USER.md / MEMORY.md), active model, and cron jobs from Hermes. | `Path`, `_extract_skill_meta`, `any`, `append` |
| `_extract_skill_meta` | `L266–L283` | `(path: Path...)` | `dict[str, Any]` | Extracts frontmatter metadata from a SKILL.md file. | `get`, `isinstance`, `len`, `read_text` |
| `run_hermes_cron_cmd` | `L286–L298` | `(*args: str...)` | `dict[str, Any]` | Runs a hermes cron sub-command synchronously on the hummingbird profile. | `get_hermes_bin`, `run`, `str`, `strip` |
| `build_hermes_bridge_router` | `L301–L347` | `(database: Any=None, settings: Any=N...)` | `APIRouter` | Builds and returns the Hermes bridge router. | `APIRouter` |
| `bridge_chat` | `L306–L316` | `(body: BridgeChatRequest...)` | — | Streaming chat endpoint proxying to running Hermes. | `StreamingResponse`, `post`, `stream_hermes_chat` |
| `bridge_state` | `L319–L321` | `(...)` | — | Returns active model, skills, memory preview, and cron jobs directly from Hermes. | `get`, `read_hermes_state` |
| `bridge_cron_pause` | `L324–L329` | `(job_id: str...)` | — | Pauses a scheduled Hermes cron job. | `HTTPException`, `get`, `post`, `run_hermes_cron_cmd` |
| `bridge_cron_resume` | `L332–L337` | `(job_id: str...)` | — | Resumes a paused Hermes cron job. | `HTTPException`, `get`, `post`, `run_hermes_cron_cmd` |
| `bridge_cron_delete` | `L340–L345` | `(job_id: str...)` | — | Deletes a scheduled Hermes cron job. | `HTTPException`, `delete`, `get`, `run_hermes_cron_cmd` |


---

### 📄 [`backend/kernel_api.py`](/backend/kernel_api.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `SetTierRequest` | `L259–L261` | `BaseModel` | — | 0 |
| `SetAllocationRequest` | `L319–L322` | `BaseModel` | — | 0 |
| `QuarantineRequest` | `L388–L391` | `BaseModel` | — | 0 |
| `SyncRequest` | `L486–L488` | `BaseModel` | — | 0 |
| `OrderRequest` | `L548–L555` | `BaseModel` | — | 0 |
| `SetTradingModeRequest` | `L755–L757` | `BaseModel` | — | 0 |
| `SetAutomationConfigRequest` | `L819–L823` | `BaseModel` | — | 0 |
| `SchedulerActionRequest` | `L904–L905` | `BaseModel` | — | 0 |
| `RunCycleRequest` | `L977–L979` | `BaseModel` | — | 0 |
| `StockNowSessionActionRequest` | `L1025–L1027` | `BaseModel` | — | 0 |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `clear_order_idempotency_cache` | `L57–L59` | `(...)` | `None` | Clear order idempotency cache (for tests). | `clear` |
| `verify_kernel_auth` | `L62–L86` | `(request: Request, x_kernel_token: s...)` | `None` | Enforces 127.0.0.1 localhost binding and X-Kernel-Token authentication. | `HTTPException`, `Header`, `getenv` |
| `get_db` | `L89–L94` | `(request: Request...)` | `Database` | Extract database from app state or fallback to default. | `Database`, `get_settings`, `hasattr` |
| `get_settings` | `L97–L101` | `(request: Request...)` | `Settings` | Extract settings from app state or fallback to default. | `Settings`, `hasattr` |
| `get_stocknow_client` | `L104–L106` | `(request: Request...)` | `Any | None` | Extract live StockNow Playwright client if attached. | `getattr` |
| `get_portfolio` | `L118–L125` | `(request: Request, db: Database=Depe...)` | `dict[str, Any]` | Returns full portfolio snapshot with holdings, cash, and rolling buckets. | `Depends`, `get`, `read`, `snapshot_from_session` |
| `get_watchlist` | `L129–L155` | `(tier: str | None=Query(None, descri...)` | `list[dict[str, Any]]` | Returns watchlist companies, optionally filtered by tier. | `Depends`, `Query`, `append`, `float` |
| `get_curve` | `L159–L191` | `(symbol: str, db: Database=Depends(g...)` | `dict[str, Any]` | Returns price curve analysis, support floor, resistance ceiling, and sparkline points. | `Depends`, `HTTPException`, `analyze_curve`, `float` |
| `get_market_open` | `L195–L197` | `(settings: Settings=Depends(get_sett...)` | `dict[str, Any]` | Returns real DSE trading hours and session status in Asia/Dhaka time. | `Depends`, `get`, `is_dse_market_open` |
| `get_canaries` | `L201–L219` | `(db: Database=Depends(get_db)...)` | `list[dict[str, Any]]` | Returns active and past 10% canary probe theses. | `Depends`, `desc`, `float`, `get` |
| `get_lots` | `L223–L251` | `(symbol: str | None=Query(None, desc...)` | `list[dict[str, Any]]` | Returns T+2 rolling tax lots with maturity status. | `Depends`, `Query`, `float`, `get` |
| `post_tier` | `L265–L316` | `(body: SetTierRequest, db: Database=...)` | `dict[str, Any]` | Updates a company's watchlist tier (GSC, GSC_L1, GSC_L2). | `Depends`, `HTTPException`, `KernelAuditLog`, `RuleAudit` |
| `post_allocation` | `L326–L385` | `(body: SetAllocationRequest, db: Dat...)` | `dict[str, Any]` | Updates buying allocation percentage for a company rule. | `Depends`, `HTTPException`, `KernelAuditLog`, `RuleAudit` |
| `post_quarantine` | `L395–L445` | `(body: QuarantineRequest, db: Databa...)` | `dict[str, Any]` | Places stock in 90% profit-lock + 10% canary quarantine, or restores it. | `Depends`, `HTTPException`, `KernelAuditLog`, `add` |
| `post_canary_evaluate` | `L449–L483` | `(db: Database=Depends(get_db)...)` | `dict[str, Any]` | Evaluates observing canary probe theses against recent price movements. | `Depends`, `KernelAuditLog`, `add`, `check_canary_theses` |
| `post_sync` | `L492–L545` | `(body: SyncRequest, db: Database=Dep...)` | `dict[str, Any]` | Syncs market prices, all-shares board, or virtual portfolio holdings. | `Depends`, `KernelAuditLog`, `add`, `create_checkpoint` |
| `post_order` | `L559–L718` | `(body: OrderRequest, db: Database=De...)` | `dict[str, Any]` | Submits a virtual BUY or SELL order enforcing T+2 maturity, strict no-loss, and 0.5% fees. | `Decimal`, `Depends`, `HTTPException`, `KernelAuditLog` |
| `post_rollback` | `L722–L747` | `(db: Database=Depends(get_db)...)` | `dict[str, Any]` | Rolls back the last state checkpoint atomically. | `Depends`, `HTTPException`, `KernelAuditLog`, `add` |
| `get_trading_mode` | `L761–L769` | `(db: Database=Depends(get_db)...)` | `dict[str, Any]` | Returns current trading mode (TEST_OFFHOURS or LIVE_HOURS). | `Depends`, `get`, `getattr`, `portfolio_state` |
| `post_trading_mode` | `L773–L816` | `(body: SetTradingModeRequest, db: Da...)` | `dict[str, Any]` | Sets trading mode to TEST_OFFHOURS or LIVE_HOURS with snapshot and audit log. | `Depends`, `HTTPException`, `KernelAuditLog`, `add` |
| `get_automation_config` | `L827–L836` | `(db: Database=Depends(get_db)...)` | `dict[str, Any]` | Returns master buy/sell automation switch, paused state, ingestion mode, and polling interval. | `Depends`, `bool`, `get`, `getattr` |
| `post_automation_config` | `L840–L901` | `(body: SetAutomationConfigRequest, d...)` | `dict[str, Any]` | Updates master automation switch, paused state, ingestion mode, or polling interval with snapshot & audit. | `Depends`, `HTTPException`, `KernelAuditLog`, `add` |
| `get_scheduler_status` | `L909–L920` | `(settings: Settings=Depends(get_sett...)` | `dict[str, Any]` | Returns current scheduler operational status and telemetry. | `Depends`, `get`, `get_active_scheduler`, `get_status` |
| `post_scheduler_control` | `L924–L974` | `(body: SchedulerActionRequest, db: D...)` | `dict[str, Any]` | Controls background market scheduler (start, stop, status). | `Depends`, `KernelAuditLog`, `add`, `create_checkpoint` |
| `post_run_cycle` | `L983–L1022` | `(body: RunCycleRequest, db: Database...)` | `dict[str, Any]` | Executes an automation trading cycle via AutoTrader under the single-writer trading lock. | `AutoTrader`, `Depends`, `KernelAuditLog`, `acquire_trading_lock` |
| `post_stocknow_session` | `L1031–L1093` | `(body: StockNowSessionActionRequest,...)` | `dict[str, Any]` | Controls live StockNow browser session (launch, status, login). | `Depends`, `KernelAuditLog`, `add`, `create_checkpoint` |
| `build_kernel_router` | `L1101–L1107` | `(database: Database, settings: Setti...)` | `APIRouter` | Builds the configured kernel router for inclusion in main app. | — |
| `create_kernel_app` | `L1110–L1133` | `(database: Database | None=None, set...)` | `FastAPI` | Creates a standalone FastAPI service for the trading kernel binding 127.0.0.1. | `Database`, `FastAPI`, `Settings`, `create_schema` |


---

### 📄 [`backend/main.py`](/backend/main.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `PauseRequest` | `L55–L57` | `BaseModel` | — | 0 |
| `AutomationConfigRequest` | `L60–L65` | `BaseModel` | — | 0 |
| `AdvanceRequest` | `L68–L70` | `BaseModel` | — | 0 |
| `AllocationRequest` | `L73–L76` | `BaseModel` | — | 0 |
| `EventBroadcaster` | `L79–L96` | `object` | — | 4 |
| `DevStaticFiles` | `L365–L371` | `StaticFiles` | — | 1 |


**Methods in `EventBroadcaster`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L80–L81` | `(self...)` | — | — | `set` |
| `subscribe` | `L83–L86` | `(self...)` | `asyncio.Queue` | — | `Queue`, `add` |
| `unsubscribe` | `L88–L89` | `(self, queue: asyncio.Queue...)` | — | — | `discard` |
| `publish` | `L91–L96` | `(self, event_type: str, data: dict...)` | — | — | `list`, `put_nowait` |


**Methods in `DevStaticFiles`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `get_response` | `L366–L371` | `(self, path: str, scope...)` | — | — | `get_response`, `super` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `create_app` | `L99–L385` | `(settings: Settings | None=None...)` | `FastAPI` | — | `AutoTrader`, `DSEMarketScheduler`, `Database`, `DevStaticFiles` |
| `lifespan` | `L108–L124` | `(_app: FastAPI...)` | — | — | `close`, `create_schema`, `dispose`, `migrate_real_stocknow_market` |
| `local_security` | `L139–L177` | `(request: Request, call_next...)` | — | — | `JSONResponse`, `call_next`, `compare_digest`, `encode` |
| `health` | `L180–L212` | `(...)` | — | — | `AsyncClient`, `bool`, `get`, `get_status` |
| `portfolio` | `L215–L216` | `(...)` | — | — | `build_snapshot`, `get` |
| `cycle` | `L219–L233` | `(idempotency_key: Annotated[UUID | N...)` | — | — | `HTTPException`, `Header`, `extract_quotes_from_stocknow`, `post` |
| `pause` | `L236–L243` | `(body: PauseRequest...)` | — | — | `portfolio_state`, `post`, `publish`, `write` |
| `automation_config` | `L246–L284` | `(body: AutomationConfigRequest...)` | — | — | `StockNowAdapter`, `ensure_authenticated`, `extract_quotes_from_stocknow`, `get_adapter_status` |
| `advance` | `L287–L298` | `(body: AdvanceRequest...)` | — | — | `Decimal`, `advance_demo`, `build_market_map_payload`, `get` |
| `market_map_endpoint` | `L301–L302` | `(...)` | — | — | `build_market_map_payload`, `get` |
| `allocation` | `L305–L328` | `(symbol: str, body: AllocationReques...)` | — | — | `HTTPException`, `RuleAudit`, `add`, `get` |
| `event_stream` | `L338–L363` | `(request: Request...)` | — | — | `StreamingResponse`, `generator`, `get`, `subscribe` |
| `generator` | `L341–L353` | `(...)` | — | — | `dumps`, `get`, `is_disconnected`, `unsubscribe` |
| `cockpit` | `L374–L382` | `(...)` | — | — | `FileResponse`, `get` |


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
| `generate_extended_history` | `L230–L282` | `(history: list[dict[str, str]], fund...)` | `dict[str, list[dict[str, Any]]]` | Generates 7d, 1m, 6m, 1y series for TradingView-style deep trend views. | `add_sessions`, `append`, `cos`, `float` |
| `rule_view` | `L285–L295` | `(rule: CustomRule...)` | `dict` | — | `decimal`, `float` |
| `trade_view` | `L298–L317` | `(trade: TradeLog...)` | `dict` | — | `float`, `isoformat` |
| `period_totals` | `L320–L335` | `(trades: list[TradeLog], start: date...)` | `dict` | — | `float`, `isoformat`, `len`, `sum` |
| `build_snapshot` | `L338–L340` | `(database: Database, settings: Setti...)` | `dict` | — | `read`, `snapshot_from_session` |
| `snapshot_from_session` | `L343–L633` | `(session: Session, settings: Setting...)` | `dict` | — | `StockNowAdapter`, `TradingCalendar`, `abs`, `add_sessions` |
| `normalized_watchlist` | `L636–L655` | `(companies: list[dict]...)` | `list[dict]` | Equal-weight normalized PRICE index, explicitly not portfolio performance. | `any`, `append`, `decimal`, `float` |


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


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `build_hermes_router` | `L25–L124` | `(database: Database, settings: Setti...)` | `APIRouter` | — | `APIRouter` |
| `list_conversations` | `L29–L31` | `(...)` | — | Returns conversation topics. | `get` |
| `create_conversation` | `L34–L42` | `(body: CreateThreadRequest...)` | — | Creates a local conversation topic stub. | `post` |
| `conversation_messages` | `L45–L47` | `(conversation_id: str...)` | — | Returns messages for a conversation topic. | `get` |
| `system_changes` | `L50–L122` | `(...)` | — | Returns git diff summary and recent kernel checkpoints. | `Path`, `append`, `desc`, `get` |


---

### 📄 [`backend/routes_stocknow.py`](/backend/routes_stocknow.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `StockNowSessionActionRequest` | `L32–L35` | `BaseModel` | — | 0 |
| `StockNowMarketSyncRequest` | `L38–L40` | `BaseModel` | — | 0 |
| `StockNowPortfolioSyncRequest` | `L43–L45` | `BaseModel` | — | 0 |
| `StockNowExecuteOrderRequest` | `L48–L54` | `BaseModel` | — | 0 |
| `StockNowSchedulerActionRequest` | `L57–L60` | `BaseModel` | — | 0 |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `build_stocknow_router` | `L63–L306` | `(database: Database, settings: Setti...)` | `APIRouter` | — | `APIRouter`, `DSEMarketScheduler`, `StockNowLiveClient`, `get_active_scheduler` |
| `get_stocknow_status` | `L82–L83` | `(...)` | — | — | `get`, `get_status` |
| `get_stocknow_page` | `L86–L97` | `(...)` | — | — | `_get_info`, `_run_in_proactor`, `get`, `getattr` |
| `_get_info` | `L89–L94` | `(...)` | — | — | `evaluate`, `getattr`, `hasattr`, `title` |
| `post_stocknow_session` | `L100–L151` | `(body: StockNowSessionActionRequest...)` | — | — | `HTTPException`, `_background_auth`, `close`, `create_task` |
| `_background_auth` | `L117–L124` | `(...)` | — | — | `ensure_authenticated`, `get_status`, `publish`, `warning` |
| `post_stocknow_sync_market` | `L154–L163` | `(body: StockNowMarketSyncRequest | N...)` | — | — | `build_snapshot`, `extract_quotes_from_stocknow`, `post`, `publish` |
| `get_all_dse_shares` | `L166–L168` | `(...)` | — | Returns the full 470+ DSE shares catalog with live LTP, +/- %, and sparkline curves. | `get`, `get_or_fetch_all_dse_shares` |
| `get_stocknow_symbol_history` | `L171–L184` | `(symbol: str...)` | — | Returns real 400-candle daily history for any DSE company directly from StockNow. | `AsyncClient`, `HTTPException`, `get`, `json` |
| `post_stocknow_sync_portfolio` | `L187–L207` | `(body: StockNowPortfolioSyncRequest ...)` | — | — | `build_snapshot`, `extract_hummingbird_portfolio`, `extract_hummingbird_portfolio_from_browser`, `get` |
| `post_stocknow_execute_order` | `L210–L289` | `(body: StockNowExecuteOrderRequest...)` | — | — | `HTTPException`, `all`, `build_snapshot`, `create_checkpoint` |
| `get_stocknow_scheduler` | `L292–L293` | `(...)` | — | — | `get`, `get_status` |
| `post_stocknow_scheduler` | `L296–L304` | `(body: StockNowSchedulerActionReques...)` | — | — | `HTTPException`, `post`, `run_scheduled_tick`, `start` |


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
| `seed_demo` | `L35–L121` | `(session: Session, settings: Setting...)` | `None` | — | `CompanyProfile`, `CustomRule`, `Decimal`, `PortfolioState` |
| `migrate_real_stocknow_market` | `L141–L288` | `(session: Session, settings: Setting...)` | `None` | Migrates existing SQLite database on boot to real StockNow #164580 portfolio and watchlist. | `CompanyProfile`, `CustomRule`, `Decimal`, `TaxLot` |


---

### 📄 [`scripts/check_dse_market_open.py`](/scripts/check_dse_market_open.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `check_kernel_market_open` | `L24–L42` | `(...)` | `tuple[bool, str]` | Attempts to verify market status via local kernel API if reachable. | `Request`, `add_header`, `bool`, `decode` |
| `is_dse_time_open` | `L45–L60` | `(now: datetime...)` | `tuple[bool, str]` | Pure calendar and hours check against Dhaka time. | `strftime`, `strptime`, `time`, `weekday` |
| `main` | `L63–L85` | `(...)` | — | — | `check_kernel_market_open`, `dumps`, `exit`, `is_dse_time_open` |


---

### 📄 [`scripts/generate_code_map.py`](/scripts/generate_code_map.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `AstVisitor` | `L51–L146` | `ast.NodeVisitor` | — | 9 |


**Methods in `AstVisitor`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L52–L59` | `(self, filepath: Path, code_lines: l...)` | — | — | — |
| `visit_Import` | `L61–L64` | `(self, node: ast.Import...)` | — | — | `append`, `generic_visit` |
| `visit_ImportFrom` | `L66–L70` | `(self, node: ast.ImportFrom...)` | — | — | `append`, `generic_visit` |
| `visit_ClassDef` | `L72–L87` | `(self, node: ast.ClassDef...)` | — | — | `append`, `generic_visit`, `get_docstring`, `getattr` |
| `visit_FunctionDef` | `L89–L90` | `(self, node: ast.FunctionDef...)` | — | — | `_record_func` |
| `visit_AsyncFunctionDef` | `L92–L93` | `(self, node: ast.AsyncFunctionDef...)` | — | — | `_record_func` |
| `_record_func` | `L95–L122` | `(self, node: ast.FunctionDef | ast.A...)` | — | — | `_compute_depth`, `append`, `generic_visit`, `get_docstring` |
| `visit_Call` | `L124–L133` | `(self, node: ast.Call...)` | — | — | `add`, `generic_visit`, `isinstance` |
| `_compute_depth` | `L135–L146` | `(self, node: ast.AST, current_depth:...)` | `int` | — | `_compute_depth`, `isinstance`, `iter_child_nodes` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `is_ignored` | `L26–L31` | `(path: Path...)` | `bool` | — | `startswith` |
| `collect_file_metrics` | `L34–L48` | `(...)` | — | — | `append`, `defaultdict`, `is_file`, `is_ignored` |
| `parse_python_files` | `L149–L165` | `(...)` | — | — | `AstVisitor`, `as_posix`, `is_ignored`, `list` |
| `parse_fastapi_routes` | `L168–L205` | `(router_paths: list[Path]...)` | — | — | `append`, `as_posix`, `exists`, `get_docstring` |
| `parse_css_design` | `L208–L310` | `(styles_file: Path, light_file: Path...)` | — | — | `append`, `exists`, `get`, `group` |
| `scan_file` | `L256–L305` | `(css_text: str, filename: str...)` | — | — | `any`, `append`, `escape`, `get` |
| `parse_frontend` | `L313–L338` | `(...)` | — | — | `add`, `append`, `enumerate`, `exists` |
| `generate_markdown` | `L341–L529` | `(...)` | — | — | `append`, `collect_file_metrics`, `get`, `items` |


---

### 📄 [`scripts/migrate_drop_hermes_tables.py`](/scripts/migrate_drop_hermes_tables.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `run_migration` | `L15–L70` | `(db_path: Path | str | None=None, ba...)` | `dict` | — | `Path`, `close`, `commit`, `connect` |


---

## 4. Database Schema X-Ray (`backend/database.py`)

SQLAlchemy ORM Entities backing the deterministic ledger and Hermes state store:

| Model Entity | Line Range | Base | Purpose & Managed Ledger State |
| :--- | :--- | :--- | :--- |
| `PortfolioState` | `L41–L58` | `Base` | Durable transactional entity |
| `CompanyProfile` | `L61–L74` | `Base` | Durable transactional entity |
| `CustomRule` | `L77–L88` | `Base` | Durable transactional entity |
| `TaxLot` | `L91–L116` | `Base` | Durable transactional entity |
| `AutomationCycle` | `L119–L128` | `Base` | Durable transactional entity |
| `TradeLog` | `L131–L156` | `Base` | Durable transactional entity |
| `CanaryThesis` | `L159–L171` | `Base` | Durable transactional entity |
| `KernelStateCheckpoint` | `L174–L184` | `Base` | Durable transactional entity |
| `CycleRequestKey` | `L187–L190` | `Base` | Durable transactional entity |
| `DecisionLog` | `L193–L203` | `Base` | Durable transactional entity |
| `RuleAudit` | `L206–L214` | `Base` | Durable transactional entity |
| `KernelAuditLog` | `L217–L228` | `Base` | Durable transactional entity |
| `ChatBudget` | `L231–L234` | `Base` | Durable transactional entity |

---

## 5. FastAPI Route Registry (All Sub-Routers & Endpoints)

| Method | Route Path | Module File | Line | Handler Function | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | [`backend/main.py`](/backend/main.py#L180) | `L180` | `health()` | Route endpoint |
| `GET` | `/api/portfolio` | [`backend/main.py`](/backend/main.py#L215) | `L215` | `portfolio()` | Route endpoint |
| `POST` | `/api/automation/cycle` | [`backend/main.py`](/backend/main.py#L219) | `L219` | `cycle()` | Route endpoint |
| `POST` | `/api/automation/pause` | [`backend/main.py`](/backend/main.py#L236) | `L236` | `pause()` | Route endpoint |
| `POST` | `/api/automation/config` | [`backend/main.py`](/backend/main.py#L246) | `L246` | `automation_config()` | Route endpoint |
| `POST` | `/api/demo/advance` | [`backend/main.py`](/backend/main.py#L287) | `L287` | `advance()` | Route endpoint |
| `GET` | `/api/market/map` | [`backend/main.py`](/backend/main.py#L301) | `L301` | `market_map_endpoint()` | Route endpoint |
| `PATCH` | `/api/companies/{symbol}/allocation` | [`backend/main.py`](/backend/main.py#L305) | `L305` | `allocation()` | Route endpoint |
| `GET` | `/api/stream` | [`backend/main.py`](/backend/main.py#L338) | `L338` | `event_stream()` | Route endpoint |
| `GET` | `/` | [`backend/main.py`](/backend/main.py#L374) | `L374` | `cockpit()` | Route endpoint |
| `GET` | `/api/hermes/conversations` | [`backend/routes_hermes.py`](/backend/routes_hermes.py#L29) | `L29` | `list_conversations()` | Returns conversation topics. |
| `POST` | `/api/hermes/conversations` | [`backend/routes_hermes.py`](/backend/routes_hermes.py#L34) | `L34` | `create_conversation()` | Creates a local conversation topic stub. |
| `GET` | `/api/hermes/conversations/{conversation_id}/messages` | [`backend/routes_hermes.py`](/backend/routes_hermes.py#L45) | `L45` | `conversation_messages()` | Returns messages for a conversation topic. |
| `GET` | `/api/system/changes` | [`backend/routes_hermes.py`](/backend/routes_hermes.py#L50) | `L50` | `system_changes()` | Returns git diff summary and recent kernel checkpoints. |
| `POST` | `/api/auth/login` | [`backend/routes_auth_settings.py`](/backend/routes_auth_settings.py#L44) | `L44` | `login()` | Route endpoint |
| `POST` | `/api/auth/logout` | [`backend/routes_auth_settings.py`](/backend/routes_auth_settings.py#L61) | `L61` | `logout()` | Route endpoint |
| `GET` | `/api/auth/session` | [`backend/routes_auth_settings.py`](/backend/routes_auth_settings.py#L68) | `L68` | `auth_session()` | Route endpoint |
| `GET` | `/api/settings/keys` | [`backend/routes_auth_settings.py`](/backend/routes_auth_settings.py#L83) | `L83` | `get_api_keys()` | Route endpoint |
| `POST` | `/api/settings/keys` | [`backend/routes_auth_settings.py`](/backend/routes_auth_settings.py#L125) | `L125` | `update_api_keys()` | Route endpoint |
| `GET` | `/api/stocknow/status` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L82) | `L82` | `get_stocknow_status()` | Route endpoint |
| `GET` | `/api/stocknow/page` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L86) | `L86` | `get_stocknow_page()` | Route endpoint |
| `POST` | `/api/stocknow/session` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L100) | `L100` | `post_stocknow_session()` | Route endpoint |
| `POST` | `/api/stocknow/sync-market` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L154) | `L154` | `post_stocknow_sync_market()` | Route endpoint |
| `GET` | `/api/stocknow/all-shares` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L166) | `L166` | `get_all_dse_shares()` | Returns the full 470+ DSE shares catalog with live LTP, +/- %, and sparkline curves. |
| `GET` | `/api/stocknow/history/{symbol}` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L171) | `L171` | `get_stocknow_symbol_history()` | Returns real 400-candle daily history for any DSE company directly from StockNow. |
| `POST` | `/api/stocknow/sync-portfolio` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L187) | `L187` | `post_stocknow_sync_portfolio()` | Route endpoint |
| `POST` | `/api/stocknow/execute-order` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L210) | `L210` | `post_stocknow_execute_order()` | Route endpoint |
| `GET` | `/api/stocknow/scheduler` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L292) | `L292` | `get_stocknow_scheduler()` | Route endpoint |
| `POST` | `/api/stocknow/scheduler` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L296) | `L296` | `post_stocknow_scheduler()` | Route endpoint |

---

## 6. Frontend DOM, JS Controller & CSS Design X-Ray

### Theme Color & Layout Tokens Table (`:root` Dark vs Light Mode)

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


### Component CSS Selector Map

| Component Selector | Stylesheet File | Line | Display | Grid / Layout | Position | Background / Color | Flex Wrap |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `.app-shell` | [`frontend/styles.css`](/frontend/styles.css#L242) | `L242` | `grid` | `64px minmax(0, 1fr) var(--hermes-width)` | — | — | — |
| `.nav-rail` | [`frontend/styles.css`](/frontend/styles.css#L255) | `L255` | `flex` | — | — | `var(--nav-bg)` | — |
| `.workspace` | [`frontend/styles.css`](/frontend/styles.css#L356) | `L356` | — | — | `relative` | — | — |
| `.topbar` | [`frontend/styles.css`](/frontend/styles.css#L380) | `L380` | `flex` | — | `sticky` | `rgba(10, 16, 24, 0.88)` | `nowrap` |
| `.topbar-right` | [`frontend/styles.css`](/frontend/styles.css#L416) | `L416` | `flex` | — | — | — | `nowrap` |
| `.topbar` | [`frontend/styles.css`](/frontend/styles.css#L426) | `L426` | `flex` | — | — | — | `nowrap` |
| `.topbar` | [`frontend/styles.css`](/frontend/styles.css#L435) | `L435` | — | — | — | — | — |
| `.topbar` | [`frontend/styles.css`](/frontend/styles.css#L479) | `L479` | — | — | — | — | — |
| `.engine-controls` | [`frontend/styles.css`](/frontend/styles.css#L582) | `L582` | `flex` | — | — | — | — |
| `.session-bar` | [`frontend/styles.css`](/frontend/styles.css#L618) | `L618` | `flex` | — | — | `#0e161f` | `wrap` |
| `.metric-card` | [`frontend/styles.css`](/frontend/styles.css#L670) | `L670` | — | — | — | `var(--panel)` | — |
| `.skills-drawer` | [`frontend/styles.css`](/frontend/styles.css#L2287) | `L2287` | — | — | — | `#0c141d` | — |
| `.model-dropup-menu` | [`frontend/styles.css`](/frontend/styles.css#L4060) | `L4060` | — | — | `absolute` | `var(--panel, #111a24)` | — |
| `.session-bar` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L69) | `L69` | — | — | — | `#ffffff` | — |
| `.metric-card` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L95) | `L95` | — | — | — | `#ffffff` | — |
| `.nav-rail` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L499) | `L499` | — | — | — | `#f8fafc !important` | — |
| `.chat-messages` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L557) | `L557` | — | — | — | `#ffffff !important` | — |
| `.diff-card` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L596) | `L596` | — | — | — | `#ffffff !important` | — |
| `.nav-rail` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L784) | `L784` | — | — | — | `#ccfbf1 !important` | — |
| `.topbar` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L846) | `L846` | — | — | — | `rgba(226, 232, 240, 0.92)` | — |
| `#hermes-resizer` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L869) | `L869` | — | — | `absolute` | `transparent` | — |
| `.app-shell` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L910) | `L910` | — | — | — | — | — |
| `.chat-messages` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L1019) | `L1019` | — | — | — | — | — |
| `.diff-card` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L1509) | `L1509` | — | — | — | `var(--panel)` | — |
| `.model-dropup-menu` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L1644) | `L1644` | — | — | `absolute` | `var(--panel, #111a24)` | — |
| `.model-dropup-menu` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L1661) | `L1661` | — | — | — | `#ffffff` | — |
| `.workspace` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L1784) | `L1784` | — | — | — | — | — |
| `.skills-drawer` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L2115) | `L2115` | — | — | — | `#ffffff !important` | — |


### Key DOM Identifiers (`frontend/index.html`)

Identified **273** distinct element IDs in the UI shell. Key controller anchors:

`#overview`, `#watchlist`, `#market-map`, `#master-automation-toggle`, `#mode-btn-polling`, `#mode-btn-live`, `#polling-interval-pills`, `#main-chart`, `#bucket-stack`, `#what-if-slider`, `#theme-toggle-btn`, `#topbar-clock-widget`


### Frontend Stylesheets (`frontend/*.css`)

| Stylesheet File | Lines | Purpose |
| :--- | :--- | :--- |
| `styles.css` | 5587 | Core design tokens, layout & widgets |
| `theme_light_hermes.css` | 2842 | Daylight overrides & Hermes IDE sidebar |


### Frontend API Contract Invocations (`frontend/*.js`)

| Endpoint Invocated | Direction | Purpose |
| :--- | :--- | :--- |
| `/api/auth/login` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/auth/logout` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/auth/session` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/automation/config` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/automation/cycle` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/automation/pause` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/demo/advance` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/hermes/bridge/state` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/hermes/conversations` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/hermes/rollback` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/portfolio` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/settings/keys` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/stocknow/all-shares` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/stocknow/execute-order` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/stocknow/session` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/stocknow/sync-market` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/stocknow/sync-portfolio` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/system/changes` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |


### Core JavaScript Controllers (`frontend/*.js`)

| Function | Module File | Line | Role |
| :--- | :--- | :--- | :--- |
| `element()` | `app.js` | `L46` | Reactive DOM rendering / event controller |
| `svgElement()` | `app.js` | `L53` | Reactive DOM rendering / event controller |
| `currency()` | `app.js` | `L59` | Reactive DOM rendering / event controller |
| `percentage()` | `app.js` | `L66` | Reactive DOM rendering / event controller |
| `sessionDate()` | `app.js` | `L71` | Reactive DOM rendering / event controller |
| `setText()` | `app.js` | `L75` | Reactive DOM rendering / event controller |
| `setPnl()` | `app.js` | `L80` | Reactive DOM rendering / event controller |
| `tone()` | `app.js` | `L88` | Reactive DOM rendering / event controller |
| `badge()` | `app.js` | `L98` | Reactive DOM rendering / event controller |
| `notify()` | `app.js` | `L105` | Reactive DOM rendering / event controller |
| `showError()` | `app.js` | `L115` | Reactive DOM rendering / event controller |
| `api()` | `app.js` | `L122` | Reactive DOM rendering / event controller |
| `updateControls()` | `app.js` | `L147` | Reactive DOM rendering / event controller |
| `refresh()` | `app.js` | `L178` | Reactive DOM rendering / event controller |
| `mutate()` | `app.js` | `L191` | Reactive DOM rendering / event controller |
| `renderSnapshot()` | `app.js` | `L200` | Reactive DOM rendering / event controller |
| `renderEquitySparkline()` | `app.js` | `L234` | Reactive DOM rendering / event controller |
| `renderActiveHoldings()` | `app.js` | `L248` | Reactive DOM rendering / event controller |
| `renderBuckets()` | `app.js` | `L401` | Reactive DOM rendering / event controller |
| `cell()` | `app.js` | `L433` | Reactive DOM rendering / event controller |
| `selectCompany()` | `app.js` | `L435` | Reactive DOM rendering / event controller |
| `formatCompactNumber()` | `app.js` | `L442` | Reactive DOM rendering / event controller |
| `renderWatchlist()` | `app.js` | `L450` | Reactive DOM rendering / event controller |
| `renderCanaryTheses()` | `app.js` | `L646` | Reactive DOM rendering / event controller |
| `renderInspector()` | `app.js` | `L680` | Reactive DOM rendering / event controller |
| `renderDecisions()` | `app.js` | `L715` | Reactive DOM rendering / event controller |
| `renderLedger()` | `app.js` | `L760` | Reactive DOM rendering / event controller |
| `initMarketMapResizeObserver()` | `app.js` | `L918` | Reactive DOM rendering / event controller |
| `initTheme()` | `app.js` | `L944` | Reactive DOM rendering / event controller |
| `setTheme()` | `app.js` | `L950` | Reactive DOM rendering / event controller |
| `toggleTheme()` | `app.js` | `L961` | Reactive DOM rendering / event controller |
| `tickMarketClock()` | `app.js` | `L967` | Reactive DOM rendering / event controller |
| `tickClock()` | `app.js` | `L1038` | Reactive DOM rendering / event controller |
| `renderAutomationControlBar()` | `app.js` | `L1047` | Reactive DOM rendering / event controller |
| `setAutomationConfig()` | `app.js` | `L1229` | Reactive DOM rendering / event controller |
| `switchToLiveHours()` | `app.js` | `L1352` | Reactive DOM rendering / event controller |
| `switchToTestMode()` | `app.js` | `L1361` | Reactive DOM rendering / event controller |
| `initRealtimeStream()` | `app.js` | `L1413` | Reactive DOM rendering / event controller |
| `switchView()` | `app.js` | `L1439` | Reactive DOM rendering / event controller |
| `initViewRouter()` | `app.js` | `L1490` | Reactive DOM rendering / event controller |
| `initScrollSpy()` | `app.js` | `L1527` | Reactive DOM rendering / event controller |
| `updateActiveNav()` | `app.js` | `L1540` | Reactive DOM rendering / event controller |
| `smoothCurvePath()` | `charts.js` | `L8` | Reactive DOM rendering / event controller |
| `getBezierPointAtContinuousIndex()` | `charts.js` | `L31` | Reactive DOM rendering / event controller |
| `renderMainChart()` | `charts.js` | `L63` | Reactive DOM rendering / event controller |
| `sparkline()` | `charts.js` | `L350` | Reactive DOM rendering / event controller |
| `squarify()` | `charts.js` | `L366` | Reactive DOM rendering / event controller |
| `layoutRow()` | `charts.js` | `L376` | Reactive DOM rendering / event controller |
| `worst()` | `charts.js` | `L423` | Reactive DOM rendering / event controller |
| `showTreemapTooltip()` | `charts.js` | `L460` | Reactive DOM rendering / event controller |
| `hideTreemapTooltip()` | `charts.js` | `L473` | Reactive DOM rendering / event controller |
| `renderMarketMap()` | `charts.js` | `L478` | Reactive DOM rendering / event controller |
| `renderTopSectorsChart()` | `charts.js` | `L657` | Reactive DOM rendering / event controller |
| `renderGainerChart()` | `charts.js` | `L817` | Reactive DOM rendering / event controller |
| `updateWhatIfSimulator()` | `charts.js` | `L822` | Reactive DOM rendering / event controller |
| `updateModalSimulator()` | `charts.js` | `L866` | Reactive DOM rendering / event controller |
| `openDeepTrendModal()` | `charts.js` | `L905` | Reactive DOM rendering / event controller |
| `closeDeepTrendModal()` | `charts.js` | `L1014` | Reactive DOM rendering / event controller |
| `renderDeepTrendChart()` | `charts.js` | `L1024` | Reactive DOM rendering / event controller |
| `initCharts()` | `charts.js` | `L1308` | Reactive DOM rendering / event controller |
| `renderHermesSkills()` | `hermes_ui.js` | `L8` | Reactive DOM rendering / event controller |
| `loadHermesOSState()` | `hermes_ui.js` | `L55` | Reactive DOM rendering / event controller |
| `renderHermesBrainCard()` | `hermes_ui.js` | `L115` | Reactive DOM rendering / event controller |
| `renderHermesCronJobs()` | `hermes_ui.js` | `L165` | Reactive DOM rendering / event controller |
| `formatChatMarkdown()` | `hermes_ui.js` | `L233` | Reactive DOM rendering / event controller |
| `syncQuickPromptsPlacement()` | `hermes_ui.js` | `L274` | Reactive DOM rendering / event controller |
| `addMessage()` | `hermes_ui.js` | `L294` | Reactive DOM rendering / event controller |
| `sendChat()` | `hermes_ui.js` | `L311` | Reactive DOM rendering / event controller |
| `initHermesSidebar()` | `hermes_ui.js` | `L481` | Reactive DOM rendering / event controller |
| `loadConversations()` | `hermes_ui.js` | `L626` | Reactive DOM rendering / event controller |
| `switchConversation()` | `hermes_ui.js` | `L660` | Reactive DOM rendering / event controller |
| `createNewConversation()` | `hermes_ui.js` | `L689` | Reactive DOM rendering / event controller |
| `formatRelativeTime()` | `hermes_ui.js` | `L716` | Reactive DOM rendering / event controller |
| `escapeHtml()` | `hermes_ui.js` | `L730` | Reactive DOM rendering / event controller |
| `executeRollback()` | `hermes_ui.js` | `L740` | Reactive DOM rendering / event controller |
| `loadApiKeysSettings()` | `hermes_ui.js` | `L776` | Reactive DOM rendering / event controller |
| `saveApiKeysSettings()` | `hermes_ui.js` | `L800` | Reactive DOM rendering / event controller |
| `checkAuthSession()` | `hermes_ui.js` | `L839` | Reactive DOM rendering / event controller |
| `openOperatorProfile()` | `hermes_ui.js` | `L857` | Reactive DOM rendering / event controller |
| `closeOperatorProfile()` | `hermes_ui.js` | `L862` | Reactive DOM rendering / event controller |
| `handleOperatorLogin()` | `hermes_ui.js` | `L867` | Reactive DOM rendering / event controller |
| `handleOperatorLogout()` | `hermes_ui.js` | `L896` | Reactive DOM rendering / event controller |
| `markKeysDirty()` | `hermes_ui.js` | `L906` | Reactive DOM rendering / event controller |
| `initAuthAndSettings()` | `hermes_ui.js` | `L916` | Reactive DOM rendering / event controller |
| `loadSystemChanges()` | `hermes_ui.js` | `L998` | Reactive DOM rendering / event controller |
| `initHermesChatListeners()` | `hermes_ui.js` | `L1087` | Reactive DOM rendering / event controller |

---

## 7. Code Health & Complexity Radar

Functions requiring architectural attention (> 70 lines or nesting depth >= 4):


| File | Function / Method | Length (Lines) | Max Nesting Depth | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| `backend/adapters/stocknow_client.py` | `_launch_internal` | 82 | 6 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_client.py` | `_ensure_authenticated_internal` | 189 | 7 | Decompose into sub-functions |
| `backend/adapters/stocknow_client.py` | `_discover_portfolio_internal` | 66 | 5 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_market_sync.py` | `_normalize_history_series` | 16 | 6 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_market_sync.py` | `extract_quotes_from_payload` | 88 | 6 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_market_sync.py` | `fetch_stocknow_live_market_data` | 172 | 6 | Decompose into sub-functions |
| `backend/adapters/stocknow_market_sync.py` | `fetch_hist` | 17 | 4 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_market_sync.py` | `_extract_quotes_from_stocknow_impl` | 163 | 5 | Decompose into sub-functions |
| `backend/adapters/stocknow_market_sync.py` | `_sync_in_session` | 98 | 4 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_order_executor.py` | `_execute_stocknow_virtual_order_impl` | 220 | 8 | Decompose into sub-functions |
| `backend/adapters/stocknow_portfolio_sync.py` | `_find_portfolio_dict` | 17 | 5 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_portfolio_sync.py` | `extract_hummingbird_portfolio` | 59 | 6 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_portfolio_sync.py` | `_extract_hummingbird_portfolio_from_browser_impl` | 123 | 7 | Decompose into sub-functions |
| `backend/adapters/stocknow_portfolio_sync.py` | `_execute_reconciliation` | 120 | 3 | Decompose into sub-functions |
| `backend/database.py` | `create_schema` | 48 | 4 | Acceptable; well-scoped logic |
| `backend/engine/agent_actions.py` | `emergency_quarantine_and_canary` | 106 | 5 | Decompose into sub-functions |
| `backend/engine/agent_actions.py` | `check_canary_theses` | 31 | 4 | Acceptable; well-scoped logic |
| `backend/engine/agent_actions.py` | `execute_agentic_buy` | 83 | 3 | Acceptable; well-scoped logic |
| `backend/engine/agent_actions.py` | `execute_agentic_sell` | 101 | 3 | Decompose into sub-functions |
| `backend/engine/auto_trader.py` | `_run_cycle_internal` | 259 | 7 | Decompose into sub-functions |
| `backend/engine/auto_trader.py` | `advance_demo` | 38 | 5 | Acceptable; well-scoped logic |
| `backend/engine/checkpoint.py` | `rollback_last` | 100 | 3 | Acceptable; well-scoped logic |
| `backend/engine/curve_analyzer.py` | `analyze_curve` | 82 | 3 | Acceptable; well-scoped logic |
| `backend/engine/scheduler.py` | `is_dse_market_open` | 44 | 4 | Acceptable; well-scoped logic |
| `backend/engine/scheduler.py` | `run_scheduled_tick` | 59 | 4 | Acceptable; well-scoped logic |
| `backend/engine/scheduler.py` | `_loop` | 21 | 4 | Acceptable; well-scoped logic |
| `backend/engine/sequential_seller.py` | `plan_sale` | 105 | 3 | Decompose into sub-functions |
| `backend/engine/t2_ledger.py` | `bucket_balances` | 31 | 4 | Acceptable; well-scoped logic |
| `backend/hermes_bridge.py` | `stream_hermes_chat` | 56 | 4 | Acceptable; well-scoped logic |
| `backend/hermes_bridge.py` | `read_hermes_state` | 147 | 6 | Decompose into sub-functions |
| `backend/hermes_bridge.py` | `_extract_skill_meta` | 18 | 5 | Acceptable; well-scoped logic |
| `backend/kernel_api.py` | `post_quarantine` | 51 | 4 | Acceptable; well-scoped logic |
| `backend/kernel_api.py` | `post_sync` | 54 | 5 | Acceptable; well-scoped logic |
| `backend/kernel_api.py` | `post_order` | 160 | 6 | Decompose into sub-functions |
| `backend/kernel_api.py` | `post_automation_config` | 62 | 4 | Acceptable; well-scoped logic |
| `backend/kernel_api.py` | `post_scheduler_control` | 51 | 5 | Acceptable; well-scoped logic |
| `backend/kernel_api.py` | `post_stocknow_session` | 63 | 5 | Acceptable; well-scoped logic |
| `backend/main.py` | `create_app` | 287 | 4 | Decompose into sub-functions |
| `backend/main.py` | `local_security` | 39 | 4 | Acceptable; well-scoped logic |
| `backend/main.py` | `cycle` | 15 | 4 | Acceptable; well-scoped logic |
| `backend/main.py` | `automation_config` | 39 | 4 | Acceptable; well-scoped logic |
| `backend/main.py` | `event_stream` | 26 | 4 | Acceptable; well-scoped logic |
| `backend/main.py` | `generator` | 13 | 4 | Acceptable; well-scoped logic |
| `backend/market_map.py` | `build_market_map_payload` | 72 | 5 | Acceptable; well-scoped logic |
| `backend/portfolio.py` | `snapshot_from_session` | 291 | 5 | Decompose into sub-functions |
| `backend/portfolio.py` | `normalized_watchlist` | 20 | 4 | Acceptable; well-scoped logic |
| `backend/routes_auth_settings.py` | `build_auth_settings_router` | 134 | 2 | Decompose into sub-functions |
| `backend/routes_hermes.py` | `build_hermes_router` | 100 | 5 | Acceptable; well-scoped logic |
| `backend/routes_hermes.py` | `system_changes` | 73 | 5 | Acceptable; well-scoped logic |
| `backend/routes_stocknow.py` | `build_stocknow_router` | 244 | 4 | Decompose into sub-functions |
| `backend/routes_stocknow.py` | `post_stocknow_session` | 52 | 4 | Acceptable; well-scoped logic |
| `backend/routes_stocknow.py` | `post_stocknow_execute_order` | 80 | 4 | Acceptable; well-scoped logic |
| `backend/routes_stocknow.py` | `post_stocknow_scheduler` | 9 | 4 | Acceptable; well-scoped logic |
| `backend/secret_guard.py` | `redact_secrets` | 11 | 4 | Acceptable; well-scoped logic |
| `backend/seed.py` | `seed_demo` | 87 | 3 | Acceptable; well-scoped logic |
| `backend/seed.py` | `migrate_real_stocknow_market` | 148 | 7 | Decompose into sub-functions |
| `scripts/check_dse_market_open.py` | `check_kernel_market_open` | 19 | 4 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `is_ignored` | 6 | 4 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `collect_file_metrics` | 15 | 4 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `parse_fastapi_routes` | 38 | 10 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `parse_css_design` | 103 | 8 | Decompose into sub-functions |
| `scripts/generate_code_map.py` | `scan_file` | 50 | 8 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `parse_frontend` | 26 | 4 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `generate_markdown` | 189 | 6 | Decompose into sub-functions |
| `scripts/generate_code_map.py` | `visit_Call` | 10 | 4 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `_compute_depth` | 12 | 4 | Acceptable; well-scoped logic |


> **Audit Summary:** 33 Python modules inspected, 29 FastAPI endpoints registered, 42,010 total LOC indexed.