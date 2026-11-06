# 🗺️ Codebase AST Map & System Architecture Radar

> Auto-generated via `scripts/generate_code_map.py` (Zero-dependency stdlib AST inspection) on **2026-11-06 12:18:15 UTC**.

---

## 1. Repository Topology & File Metrics

| Extension / Type | File Count | Total Lines of Code | Description |
| :--- | :--- | :--- | :--- |
| `.py` | 44 | 11,555 | Python Core Kernel, Engine & Hermes Agent |
| `.css` | 2 | 7,865 | Custom Dark / Light / Terminal Design System |
| `.js` | 3 | 3,791 | Vanilla ES6+ Reactive Terminal Controller |
| `.md` | 11 | 2,393 | Architecture & Strategy Documentation |
| `.html` | 1 | 953 | Single Page Application DOM Structure |
| `.json` | 1 | 13 | Configuration / Asset |
| `.agentignore` | 1 | 12 | Configuration / Asset |
| `.cursorignore` | 1 | 12 | Configuration / Asset |
| `.opencodeignore` | 1 | 12 | Configuration / Asset |
| `.txt` | 2 | 11 | Dependency Specifications |
| `.toml` | 1 | 10 | PyProject Configuration |
| `.sh` | 1 | 10 | Configuration / Asset |
| `.bat` | 1 | 9 | Configuration / Asset |
| `.svg` | 1 | 1 | Configuration / Asset |
| **TOTAL** | **71** | **26,647** | *Entire Humming Bird Repository* |

## 2. Internal Dependency & Import Graph

Shows intra-repo module dependencies within `backend/` and `scripts/`:

| Module File | Imported Internal Dependencies |
| :--- | :--- |
| [`backend/__init__.py`](/backend/__init__.py) | *Independent Core Module* |
| [`backend/adapters/__init__.py`](/backend/adapters/__init__.py) | `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.adapters.stocknow_client.StockNowLiveClient`, `backend.adapters.stocknow_client.get_safe_profile_dir`, `backend.adapters.stocknow_market_sync.extract_quotes_from_payload`, `backend.adapters.stocknow_market_sync.extract_quotes_from_stocknow`, `backend.adapters.stocknow_market_sync.sync_live_market_to_db` |
| [`backend/adapters/stocknow_adapter.py`](/backend/adapters/stocknow_adapter.py) | `backend.adapters.stocknow_client.get_safe_profile_dir`, `backend.adapters.stocknow_order_executor.execute_stocknow_virtual_order`, `backend.database.CompanyProfile`, `backend.engine.money.ZERO`, `backend.engine.money.decimal` |
| [`backend/adapters/stocknow_client.py`](/backend/adapters/stocknow_client.py) | `backend.hermes.secret_guard.SecretGuard`, `backend.hermes.secret_guard.redact_secrets` |
| [`backend/adapters/stocknow_market_sync.py`](/backend/adapters/stocknow_market_sync.py) | `backend.adapters.stocknow_client.StockNowLiveClient`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.portfolio_state`, `backend.engine.money.ZERO`, `backend.engine.money.decimal`, `backend.portfolio.COMPANY_FUNDAMENTALS`, `backend.portfolio.DEFAULT_FUNDAMENTALS` |
| [`backend/adapters/stocknow_order_executor.py`](/backend/adapters/stocknow_order_executor.py) | `backend.adapters.stocknow_client.StockNowLiveClient` |
| [`backend/adapters/stocknow_portfolio_sync.py`](/backend/adapters/stocknow_portfolio_sync.py) | `backend.adapters.stocknow_client.StockNowLiveClient`, `backend.config.Settings`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.PortfolioState`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.price`, `backend.engine.money.purchase_amount`, `backend.engine.t2_ledger.BUCKETS`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.assert_ledger`, `backend.hermes.agent_loop.CheckpointManager` |
| [`backend/chat.py`](/backend/chat.py) | `backend.config.DHAKA`, `backend.config.Settings`, `backend.database.CanaryThesis`, `backend.database.ChatBudget`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.PortfolioState`, `backend.database.portfolio_state`, `backend.engine.agent_actions.check_canary_theses`, `backend.engine.agent_actions.emergency_quarantine_and_canary`, `backend.engine.agent_actions.execute_agentic_buy`, `backend.engine.agent_actions.restore_quarantine`, `backend.hermes.agent_loop.HermesAgentLoop`, `backend.portfolio.build_snapshot` |
| [`backend/config.py`](/backend/config.py) | *Independent Core Module* |
| [`backend/database.py`](/backend/database.py) | `backend.config.utc_now_iso` |
| [`backend/engine/__init__.py`](/backend/engine/__init__.py) | *Independent Core Module* |
| [`backend/engine/agent_actions.py`](/backend/engine/agent_actions.py) | `backend.config.Settings`, `backend.database.CanaryThesis`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.DecisionLog`, `backend.database.PortfolioState`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.engine.money.ZERO`, `backend.engine.money.allocated_basis`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.price`, `backend.engine.money.purchase_amount`, `backend.engine.money.sale_amount`, `backend.engine.money.whole_shares`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.assert_ledger`, `backend.engine.t2_ledger.bucket_balances` |
| [`backend/engine/auto_trader.py`](/backend/engine/auto_trader.py) | `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.config.Settings`, `backend.database.AutomationCycle`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.CycleRequestKey`, `backend.database.Database`, `backend.database.DecisionLog`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.database.portfolio_state`, `backend.engine.agent_actions.check_canary_theses`, `backend.engine.money.HUNDRED`, `backend.engine.money.ZERO`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.price`, `backend.engine.money.purchase_amount`, `backend.engine.money.whole_shares`, `backend.engine.sequential_seller.SellState`, `backend.engine.sequential_seller.plan_sale`, `backend.engine.signals.BLOCK_ALL_TRADING`, `backend.engine.signals.assess_company`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.assert_ledger`, `backend.engine.t2_ledger.bucket_balances` |
| [`backend/engine/curve_analyzer.py`](/backend/engine/curve_analyzer.py) | `backend.engine.money.HUNDRED`, `backend.engine.money.ZERO`, `backend.engine.money.decimal` |
| [`backend/engine/money.py`](/backend/engine/money.py) | *Independent Core Module* |
| [`backend/engine/scheduler.py`](/backend/engine/scheduler.py) | `backend.adapters.stocknow_client.StockNowLiveClient`, `backend.adapters.stocknow_market_sync.extract_quotes_from_stocknow`, `backend.adapters.stocknow_market_sync.sync_live_market_to_db`, `backend.config.DHAKA`, `backend.config.Settings`, `backend.database.Database`, `backend.database.portfolio_state`, `backend.engine.auto_trader.AutoTrader`, `backend.engine.t2_ledger.TradingCalendar`, `backend.portfolio.build_snapshot` |
| [`backend/engine/sequential_seller.py`](/backend/engine/sequential_seller.py) | `backend.engine.money.HUNDRED`, `backend.engine.money.ZERO`, `backend.engine.money.allocated_basis`, `backend.engine.money.sale_amount`, `backend.engine.money.whole_shares` |
| [`backend/engine/signals.py`](/backend/engine/signals.py) | `backend.adapters.stocknow_adapter.DemoQuote`, `backend.adapters.stocknow_adapter.QuoteError`, `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.config.Settings`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.engine.curve_analyzer.CurveAnalysis`, `backend.engine.curve_analyzer.analyze_curve`, `backend.engine.money.decimal` |
| [`backend/engine/t2_ledger.py`](/backend/engine/t2_ledger.py) | `backend.database.PortfolioState`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.engine.money.CENT`, `backend.engine.money.ZERO`, `backend.engine.money.money` |
| [`backend/hermes/__init__.py`](/backend/hermes/__init__.py) | `backend.hermes.secret_guard.SecretGuard`, `backend.hermes.secret_guard.SecurityViolation`, `backend.hermes.secret_guard.redact_secrets` |
| [`backend/hermes/agent_loop.py`](/backend/hermes/agent_loop.py) | `backend.chat.local_summary`, `backend.config.DHAKA`, `backend.config.Settings`, `backend.database.ChatBudget`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.HermesStateCheckpoint`, `backend.database.PortfolioState`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.database.portfolio_state`, `backend.engine.money.decimal`, `backend.engine.t2_ledger.assert_ledger`, `backend.hermes.memory.HermesMemory`, `backend.hermes.secret_guard.SecretGuard`, `backend.hermes.secret_guard.redact_secrets`, `backend.hermes.skills_manager.SkillsManager`, `backend.hermes.tools_dispatcher.detect_intent_and_tool`, `backend.hermes.tools_dispatcher.dispatch_tool`, `backend.hermes.tools_dispatcher.format_tool_response`, `backend.portfolio.build_snapshot` |
| [`backend/hermes/memory.py`](/backend/hermes/memory.py) | `backend.config.utc_now_iso`, `backend.database.CanaryThesis`, `backend.database.CompanyProfile`, `backend.database.HermesConversationThread`, `backend.database.HermesDurableFact`, `backend.database.HermesSessionMemory`, `backend.database.HermesUserProfile`, `backend.hermes.secret_guard.redact_secrets` |
| [`backend/hermes/secret_guard.py`](/backend/hermes/secret_guard.py) | *Independent Core Module* |
| [`backend/hermes/skills_manager.py`](/backend/hermes/skills_manager.py) | `backend.database.HermesSkillRevision`, `backend.hermes.secret_guard.SecretGuard` |
| [`backend/hermes/tools_dispatcher.py`](/backend/hermes/tools_dispatcher.py) | `backend.adapters.stocknow_client.StockNowLiveClient`, `backend.adapters.stocknow_market_sync.extract_quotes_from_payload`, `backend.adapters.stocknow_market_sync.extract_quotes_from_stocknow`, `backend.adapters.stocknow_market_sync.sync_live_market_to_db`, `backend.adapters.stocknow_order_executor.execute_stocknow_virtual_order`, `backend.adapters.stocknow_portfolio_sync.extract_hummingbird_portfolio`, `backend.adapters.stocknow_portfolio_sync.reconcile_portfolio_to_db`, `backend.config.Settings`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.PortfolioState`, `backend.database.RuleAudit`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.engine.agent_actions.check_canary_theses`, `backend.engine.agent_actions.emergency_quarantine_and_canary`, `backend.engine.agent_actions.execute_agentic_buy`, `backend.engine.agent_actions.execute_agentic_sell`, `backend.engine.agent_actions.restore_quarantine`, `backend.engine.money.decimal`, `backend.engine.scheduler.get_active_scheduler`, `backend.hermes.memory.HermesMemory`, `backend.hermes.skills_manager.SkillsManager` |
| [`backend/main.py`](/backend/main.py) | `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.adapters.stocknow_client.StockNowLiveClient`, `backend.adapters.stocknow_market_sync.extract_quotes_from_stocknow`, `backend.adapters.stocknow_market_sync.sync_live_market_to_db`, `backend.chat.ChatRequest`, `backend.chat.ChatService`, `backend.config.ROOT`, `backend.config.Settings`, `backend.config.VERSION`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.RuleAudit`, `backend.database.portfolio_state`, `backend.engine.auto_trader.AutoTrader`, `backend.engine.auto_trader.AutomationPaused`, `backend.engine.money.ZERO`, `backend.engine.scheduler.DSEMarketScheduler`, `backend.market_map.build_market_map_payload`, `backend.portfolio.build_snapshot`, `backend.portfolio.rule_view`, `backend.routes_auth_settings.KeysSettingsRequest`, `backend.routes_auth_settings.LoginRequest`, `backend.routes_auth_settings.build_auth_settings_router`, `backend.routes_hermes.CreateThreadRequest`, `backend.routes_hermes.build_hermes_router`, `backend.routes_stocknow.build_stocknow_router`, `backend.seed.migrate_real_stocknow_market`, `backend.seed.seed_demo` |
| [`backend/market_map.py`](/backend/market_map.py) | *Independent Core Module* |
| [`backend/portfolio.py`](/backend/portfolio.py) | `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.config.DHAKA`, `backend.config.Settings`, `backend.config.VERSION`, `backend.database.AutomationCycle`, `backend.database.CanaryThesis`, `backend.database.ChatBudget`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.DecisionLog`, `backend.database.HermesDurableFact`, `backend.database.HermesSkillRevision`, `backend.database.HermesStateCheckpoint`, `backend.database.HermesUserProfile`, `backend.database.RuleAudit`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.database.portfolio_state`, `backend.engine.money.HUNDRED`, `backend.engine.money.ZERO`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.sale_amount`, `backend.engine.signals.assess_company`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.bucket_balances`, `backend.hermes.skills_manager.SkillsManager`, `backend.market_map.build_market_map_payload` |
| [`backend/routes_auth_settings.py`](/backend/routes_auth_settings.py) | `backend.config.DHAKA`, `backend.config.Settings`, `backend.database.ChatBudget`, `backend.database.Database`, `backend.database.HermesSessionMemory`, `backend.database.portfolio_state`, `backend.hermes.agent_loop.CheckpointManager` |
| [`backend/routes_hermes.py`](/backend/routes_hermes.py) | `backend.chat.ChatRequest`, `backend.chat.ChatService`, `backend.config.Settings`, `backend.database.Database`, `backend.database.HermesSkillRevision`, `backend.database.HermesStateCheckpoint`, `backend.database.portfolio_state`, `backend.hermes.agent_loop.CheckpointManager`, `backend.hermes.memory.HermesMemory` |
| [`backend/routes_stocknow.py`](/backend/routes_stocknow.py) | `backend.adapters.stocknow_client.StockNowLiveClient`, `backend.adapters.stocknow_market_sync.extract_quotes_from_stocknow`, `backend.adapters.stocknow_market_sync.sync_live_market_to_db`, `backend.adapters.stocknow_order_executor.execute_stocknow_virtual_order`, `backend.adapters.stocknow_portfolio_sync.extract_hummingbird_portfolio`, `backend.adapters.stocknow_portfolio_sync.extract_hummingbird_portfolio_from_browser`, `backend.adapters.stocknow_portfolio_sync.reconcile_portfolio_to_db`, `backend.config.Settings`, `backend.database.CompanyProfile`, `backend.database.Database`, `backend.database.PortfolioState`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.engine.agent_actions.execute_agentic_buy`, `backend.engine.agent_actions.execute_agentic_sell`, `backend.engine.scheduler.DSEMarketScheduler`, `backend.engine.scheduler.get_active_scheduler`, `backend.hermes.agent_loop.CheckpointManager`, `backend.portfolio.build_snapshot` |
| [`backend/seed.py`](/backend/seed.py) | `backend.config.DHAKA`, `backend.config.Settings`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.DecisionLog`, `backend.database.PortfolioState`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.price`, `backend.engine.money.purchase_amount`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.assert_ledger`, `backend.engine.t2_ledger.bucket_balances` |
| [`scripts/generate_code_map.py`](/scripts/generate_code_map.py) | *Independent Core Module* |

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
| `StockNowLiveClient` | `L80–L609` | `object` | Persistent Playwright browser controller, auto-login assistant & XHR network sniffer. | 13 |


**Methods in `StockNowLiveClient`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L83–L111` | `(self, profile_directory: Path | str...)` | — | — | `Thread`, `_create_proactor_loop`, `get_safe_profile_dir`, `rstrip` |
| `_run_worker_loop` | `L113–L118` | `(self...)` | `None` | — | `debug`, `format_exception_str`, `run_forever`, `set_event_loop` |
| `_run_in_proactor` | `L120–L143` | `(self, coro: Any...)` | `Any` | Run a coroutine inside the dedicated proactor event loop thread. | `Thread`, `_create_proactor_loop`, `get_running_loop`, `hasattr` |
| `_handle_response` | `L145–L176` | `(self, response: Any...)` | `None` | Passively capture JSON responses from stocknow.com.bd. | `debug`, `format_exception_str`, `get`, `getattr` |
| `launch` | `L178–L180` | `(self, mode: str | None=None...)` | `dict[str, Any]` | Launch or attach persistent Chromium session on dedicated Proactor thread. | `_launch_internal`, `_run_in_proactor` |
| `_launch_internal` | `L182–L263` | `(self, mode: str | None=None...)` | `dict[str, Any]` | — | `RuntimeError`, `_handle_response`, `async_playwright`, `callable` |
| `close` | `L265–L267` | `(self...)` | `dict[str, Any]` | Close browser context and stop Playwright cleanly. | `_close_internal`, `_run_in_proactor` |
| `_close_internal` | `L269–L292` | `(self...)` | `dict[str, Any]` | — | `close`, `get_status`, `stop` |
| `ensure_authenticated` | `L294–L299` | `(self, phone: str='', password: str=...)` | `dict[str, Any]` | Inspect authentication state on stocknow.com.bd, filling credentials if needed. | `_ensure_authenticated_internal`, `_run_in_proactor` |
| `_ensure_authenticated_internal` | `L301–L509` | `(self, phone: str='', password: str=...)` | `dict[str, Any]` | — | `_discover_portfolio_internal`, `check`, `click`, `debug` |
| `discover_portfolio` | `L511–L513` | `(self...)` | `dict[str, Any]` | Discover 'Humming Bird' portfolio stats and ID from /portfolios. | `_discover_portfolio_internal`, `_run_in_proactor` |
| `_discover_portfolio_internal` | `L515–L580` | `(self...)` | `dict[str, Any]` | — | `debug`, `evaluate`, `format_exception_str`, `get` |
| `get_status` | `L582–L609` | `(self...)` | `dict[str, Any]` | Return structured telemetry for live session status endpoint. | `hasattr`, `is_closed`, `keys`, `len` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `format_exception_str` | `L33–L36` | `(e: Exception | BaseException...)` | `str` | Format exception to guarantee non-empty diagnostic message. | `repr`, `str`, `strip`, `type` |
| `_create_proactor_loop` | `L39–L46` | `(...)` | `asyncio.AbstractEventLoop` | Create a new ProactorEventLoop on Windows or standard event loop on POSIX. | `WindowsProactorEventLoopPolicy`, `getattr`, `new_event_loop` |
| `get_safe_profile_dir` | `L49–L67` | `(custom_path: Path | str | None=None...)` | `Path` | Resolve an isolated Playwright profile directory outside OneDrive. | `Path`, `expanduser`, `lower`, `resolve` |
| `mask_phone` | `L70–L77` | `(phone: str...)` | `str` | Mask phone number for safe display and logging without revealing identity. | `isdigit`, `join`, `len`, `str` |


---

### 📄 [`backend/adapters/stocknow_market_sync.py`](/backend/adapters/stocknow_market_sync.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `_parse_positive_decimal` | `L30–L39` | `(val: Any...)` | `Decimal | None` | — | `decimal`, `is_finite`, `replace`, `str` |
| `_normalize_history_series` | `L42–L57` | `(raw_history: Any, fallback_price: D...)` | `list[dict[str, str]]` | Normalize 7-30 session curve observations into [{"date": "YYYY-MM-DD", "close": "XX.XX"}]. | `_parse_positive_decimal`, `append`, `get`, `isinstance` |
| `_extract_fundamentals_from_dict` | `L60–L121` | `(item: dict[str, Any]...)` | `dict[str, Any]` | — | `dict`, `float`, `get`, `int` |
| `extract_quotes_from_payload` | `L124–L211` | `(payload: Any, as_of_date: date | No...)` | `list[dict[str, Any]]` | Extract and normalize quotes from an arbitrary JSON payload. | `_extract_fundamentals_from_dict`, `_normalize_history_series`, `_parse_positive_decimal`, `append` |
| `extract_quotes_from_stocknow` | `L214–L219` | `(client: Any, injected_payload: Any=...)` | `list[dict[str, Any]]` | Extracts live DSE ticker quotes from sniffer cache, page DOM or injected payload. | `_extract_quotes_from_stocknow_impl`, `_run_in_proactor`, `hasattr`, `isinstance` |
| `_extract_quotes_from_stocknow_impl` | `L222–L375` | `(client: Any, injected_payload: Any=...)` | `list[dict[str, Any]]` | — | `debug`, `evaluate`, `extract_quotes_from_payload`, `get` |
| `_sync_in_session` | `L378–L470` | `(session: Any, quotes: list[dict[str...)` | `dict[str, Any]` | — | `CompanyProfile`, `CustomRule`, `add`, `append` |
| `sync_live_market_to_db` | `L473–L482` | `(target: Database | Any, quotes: lis...)` | `dict[str, Any]` | Synchronizes extracted live quotes into SQLite CompanyProfile records. | `_sync_in_session`, `hasattr`, `write` |


---

### 📄 [`backend/adapters/stocknow_order_executor.py`](/backend/adapters/stocknow_order_executor.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `clear_idempotency_cache` | `L17–L19` | `(...)` | `None` | Clear in-memory deduplication cache (for testing isolation). | `clear` |
| `execute_stocknow_virtual_order` | `L22–L60` | `(client: Any | None=None, symbol: st...)` | `dict[str, Any]` | Execute a virtual transaction for 'Humming Bird' portfolio with idempotency. | `Decimal`, `_execute_stocknow_virtual_order_impl`, `_run_in_proactor`, `hasattr` |
| `_execute_stocknow_virtual_order_impl` | `L63–L242` | `(client: Any | None=None, symbol: st...)` | `dict[str, Any]` | — | `Decimal`, `ValueError`, `capitalize`, `click` |


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
| `_extract_hummingbird_portfolio_from_browser_impl` | `L138–L239` | `(client: Any...)` | `dict[str, Any]` | — | `RuntimeError`, `append`, `debug`, `decimal` |
| `_execute_reconciliation` | `L242–L358` | `(session: Session, settings: Setting...)` | `dict[str, Any]` | — | `CompanyProfile`, `CustomRule`, `Decimal`, `RuntimeError` |
| `reconcile_portfolio_to_db` | `L361–L368` | `(target: Database | Session, setting...)` | `dict[str, Any]` | Reconcile virtual portfolio holdings and cash balance into SQLite ledger. | `_execute_reconciliation`, `isinstance`, `write` |


---

### 📄 [`backend/chat.py`](/backend/chat.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `ChatTurn` | `L46–L49` | `BaseModel` | — | 0 |
| `ChatRequest` | `L52–L64` | `BaseModel` | — | 1 |
| `ChatService` | `L204–L228` | `object` | — | 2 |


**Methods in `ChatRequest`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `nonempty` | `L60–L64` | `(cls, value: str...)` | `str` | — | `ValueError`, `field_validator`, `strip` |


**Methods in `ChatService`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L205–L210` | `(self, database: Database, settings:...)` | — | — | `HermesAgentLoop` |
| `respond` | `L212–L228` | `(self, request: ChatRequest...)` | `dict` | — | `get`, `model_dump`, `run_turn`, `upper` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `match_symbol` | `L67–L82` | `(text: str, companies: list[dict]...)` | `dict | None` | — | `get`, `lower` |
| `format_canary_updates` | `L85–L100` | `(snapshot: dict...)` | `str` | — | `append`, `get`, `join` |
| `local_summary` | `L103–L201` | `(message: str, snapshot: dict...)` | `str` | — | `abs`, `any`, `append`, `float` |


---

### 📄 [`backend/config.py`](/backend/config.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `Settings` | `L25–L120` | `object` | — | 3 |


**Methods in `Settings`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `operator_phone` | `L53–L54` | `(self...)` | `str` | — | — |
| `__post_init__` | `L56–L80` | `(self...)` | `None` | — | `Decimal`, `ValueError`, `any`, `is_finite` |
| `from_env` | `L83–L120` | `(cls...)` | `Settings` | — | `Decimal`, `cls`, `fromisoformat`, `frozenset` |


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
| `PortfolioState` | `L41–L57` | `Base` | — | 0 |
| `CompanyProfile` | `L60–L73` | `Base` | — | 0 |
| `CustomRule` | `L76–L87` | `Base` | — | 0 |
| `TaxLot` | `L90–L115` | `Base` | — | 0 |
| `AutomationCycle` | `L118–L127` | `Base` | — | 0 |
| `TradeLog` | `L130–L155` | `Base` | — | 0 |
| `CanaryThesis` | `L158–L170` | `Base` | — | 0 |
| `HermesSkillRevision` | `L173–L181` | `Base` | — | 0 |
| `HermesUserProfile` | `L184–L195` | `Base` | — | 0 |
| `HermesConversationThread` | `L198–L203` | `Base` | — | 0 |
| `HermesSessionMemory` | `L206–L215` | `Base` | — | 0 |
| `HermesDurableFact` | `L218–L226` | `Base` | — | 0 |
| `HermesStateCheckpoint` | `L229–L239` | `Base` | — | 0 |
| `CycleRequestKey` | `L242–L245` | `Base` | — | 0 |
| `DecisionLog` | `L248–L257` | `Base` | — | 0 |
| `RuleAudit` | `L260–L267` | `Base` | — | 0 |
| `ChatBudget` | `L270–L273` | `Base` | — | 0 |
| `Database` | `L276–L355` | `object` | — | 5 |


**Methods in `Database`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L277–L297` | `(self, url: str...)` | — | — | `Path`, `RLock`, `ValueError`, `create_engine` |
| `configure_sqlite` | `L290–L295` | `(connection: Any, _record: Any...)` | `None` | — | `close`, `cursor`, `execute`, `listens_for` |
| `create_schema` | `L299–L334` | `(self...)` | `None` | — | `commit`, `connect`, `create_all`, `execute` |
| `read` | `L337–L344` | `(self...)` | — | — | `execute`, `rollback`, `sessions`, `text` |
| `write` | `L347–L355` | `(self...)` | — | — | `commit`, `execute`, `rollback`, `sessions` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `portfolio_state` | `L358–L362` | `(session: Session...)` | `PortfolioState` | — | `RuntimeError`, `get` |


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
| `AutomationPaused` | `L35–L36` | `ValueError` | — | 0 |
| `AutoTrader` | `L39–L357` | `object` | — | 7 |


**Methods in `AutoTrader`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L40–L44` | `(self, database: Database, settings:...)` | — | — | `StockNowAdapter`, `TradingCalendar` |
| `run_cycle` | `L46–L50` | `(self, request_id: str | None=None, ...)` | `dict` | — | `_run_cycle_internal`, `write` |
| `_run_cycle_internal` | `L52–L309` | `(self, session: Session, request_id:...)` | `dict` | — | `AutomationCycle`, `AutomationPaused`, `CycleRequestKey`, `Decimal` |
| `record` | `L88–L96` | `(symbol: str, action: str, reason: s...)` | — | — | `DecisionLog`, `add`, `append` |
| `buy_priority` | `L201–L207` | `(comp: CompanyProfile...)` | `tuple[int, str]` | — | `getattr` |
| `_trade_result` | `L312–L318` | `(trade: TradeLog, action: str...)` | `dict` | — | `float` |
| `advance_demo` | `L320–L357` | `(self, scenario: str...)` | `dict` | — | `Decimal`, `ValueError`, `add_sessions`, `assert_ledger` |


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
| `DSEMarketScheduler` | `L81–L288` | `object` | Async background scheduler enforcing DSE market hours and periodic trading cycles. | 8 |


**Methods in `DSEMarketScheduler`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L84–L106` | `(self, database: Database, settings:...)` | — | — | `AutoTrader`, `hasattr` |
| `get_status` | `L108–L127` | `(self...)` | `dict[str, Any]` | Returns scheduler operational status, telemetry, and DSE market gate. | `getattr`, `is_dse_market_open`, `portfolio_state`, `read` |
| `run_scheduled_tick` | `L129–L186` | `(self, force: bool=False...)` | `dict[str, Any]` | Executes a single scheduler tick, enforcing gate & automation state unless force=True. | `build_snapshot`, `debug`, `extract_quotes_from_stocknow`, `get` |
| `run_scheduled_tick_sync` | `L188–L240` | `(self, force: bool=False, session: A...)` | `dict[str, Any]` | Synchronous version of tick execution (e.g. for Hermes chat turn). | `build_snapshot`, `debug`, `getattr`, `info` |
| `start` | `L242–L252` | `(self...)` | `dict[str, Any]` | Starts background periodic polling loop. | `_loop`, `create_task`, `get_running_loop`, `get_status` |
| `stop_sync` | `L254–L262` | `(self...)` | `dict[str, Any]` | Stops background periodic polling loop gracefully (sync). | `cancel`, `done`, `get_status` |
| `stop` | `L264–L266` | `(self...)` | `dict[str, Any]` | Stops background periodic polling loop gracefully. | `stop_sync` |
| `_loop` | `L268–L288` | `(self...)` | `None` | Background periodic execution loop respecting configured polling interval. | `error`, `getattr`, `info`, `max` |


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

### 📄 [`backend/hermes/__init__.py`](/backend/hermes/__init__.py)

---

### 📄 [`backend/hermes/agent_loop.py`](/backend/hermes/agent_loop.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `CheckpointManager` | `L70–L230` | `object` | — | 2 |
| `HermesAgentLoop` | `L233–L635` | `object` | — | 10 |


**Methods in `CheckpointManager`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `create_checkpoint` | `L72–L124` | `(session: Session, state: PortfolioS...)` | `HermesStateCheckpoint` | — | `HermesStateCheckpoint`, `add`, `flush`, `get` |
| `rollback_last` | `L127–L230` | `(session: Session, state: PortfolioS...)` | `dict[str, Any]` | — | `TaxLot`, `TradeLog`, `ValueError`, `add` |


**Methods in `HermesAgentLoop`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L234–L238` | `(self, database: Database, settings:...)` | — | — | `SkillsManager` |
| `execute_tool` | `L240–L242` | `(self, tool_name: str, args: dict[st...)` | `dict[str, Any]` | Deterministic execution of Hermes Agent tools with automatic checkpointing and rule diff tracking. | `dispatch_tool` |
| `compress_history` | `L244–L256` | `(self, history: list[dict[str, str]]...)` | `list[dict[str, str]]` | Summarizes older conversation turns to keep context window compact & lightweight. | `append`, `capitalize`, `join`, `len` |
| `detect_intent_and_tool` | `L258–L260` | `(self, message: str, snapshot: dict...)` | `tuple[str | None, dict[str, Any]]` | High-precision intent detector for Bangla, Banglish & English agent commands. | `detect_intent_and_tool` |
| `run_turn` | `L262–L339` | `(self, user_message: str, history: l...)` | `dict[str, Any]` | Main turn loop: Layered Memory + Skills Injection + Tool Execution + Context Scrubbing. | `HermesMemory`, `_conversational_inference`, `_format_tool_response`, `build_snapshot` |
| `_format_tool_response` | `L341–L342` | `(self, tool_name: str, tool_res: dic...)` | `str` | — | `format_tool_response` |
| `get_gemini_keys` | `L344–L353` | `(self...)` | `list[str]` | — | `append`, `getattr`, `replace`, `split` |
| `_call_gemini_with_key_rotation` | `L355–L445` | `(self, target_model: str, full_syste...)` | `dict[str, Any] | None` | Calls Google Gemini API with automatic multi-key rotation / rollback on 429, 403, 503 or quota limits. | `AsyncClient`, `ChatBudget`, `HermesMemory`, `Timeout` |
| `_conversational_inference` | `L447–L604` | `(self, message: str, history: list[d...)` | `dict[str, Any]` | Runs conversational response with Layered Memory and Matched SKILL.md injection. | `AsyncClient`, `ChatBudget`, `HermesMemory`, `Timeout` |
| `_local_conversational_fallback` | `L606–L635` | `(self, message: str, snapshot: dict,...)` | `dict[str, Any]` | — | `HermesMemory`, `local_summary`, `portfolio_state`, `record_turn` |


---

### 📄 [`backend/hermes/memory.py`](/backend/hermes/memory.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `HermesMemory` | `L28–L248` | `object` | — | 11 |


**Methods in `HermesMemory`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L29–L30` | `(self, session: Session...)` | — | — | — |
| `get_user_profile` | `L35–L58` | `(self...)` | `dict[str, Any]` | — | `HermesUserProfile`, `add`, `flush`, `get` |
| `format_layer_1_prompt` | `L60–L69` | `(self...)` | `str` | — | `get_user_profile`, `join` |
| `get_or_create_thread` | `L74–L86` | `(self, conversation_id: str | None=N...)` | `HermesConversationThread` | — | `HermesConversationThread`, `add`, `flush`, `get` |
| `list_threads` | `L88–L107` | `(self...)` | `list[dict[str, Any]]` | — | `append`, `count`, `desc`, `get_or_create_thread` |
| `get_thread_messages` | `L109–L123` | `(self, conversation_id: str, limit: ...)` | `list[dict[str, Any]]` | — | `asc`, `isoformat`, `limit`, `list` |
| `record_turn` | `L125–L153` | `(self, session_date: date, role: str...)` | `None` | — | `HermesSessionMemory`, `add`, `flush`, `get` |
| `search_sessions` | `L155–L182` | `(self, query: str, limit: int=4...)` | `list[dict[str, Any]]` | — | `any`, `append`, `desc`, `isoformat` |
| `record_fact` | `L187–L204` | `(self, symbol: str, fact: str, categ...)` | `HermesDurableFact` | — | `HermesDurableFact`, `add`, `flush`, `redact_secrets` |
| `recall_facts_for_symbol` | `L206–L230` | `(self, symbol: str...)` | `list[dict[str, Any]]` | — | `append`, `desc`, `float`, `limit` |
| `format_layer_3_prompt` | `L232–L248` | `(self, symbols: list[str]...)` | `str` | — | `append`, `join`, `recall_facts_for_symbol` |


---

### 📄 [`backend/hermes/secret_guard.py`](/backend/hermes/secret_guard.py)

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

### 📄 [`backend/hermes/skills_manager.py`](/backend/hermes/skills_manager.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `SkillDoc` | `L24–L30` | `object` | — | 0 |
| `SkillsManager` | `L33–L152` | `object` | — | 4 |


**Methods in `SkillsManager`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L34–L36` | `(self, directory: Path | None=None...)` | — | — | `mkdir` |
| `list_skills` | `L38–L59` | `(self...)` | `list[SkillDoc]` | — | `SkillDoc`, `append`, `assert_safe_path`, `glob` |
| `match_skills` | `L61–L82` | `(self, context_text: str, max_skills...)` | `list[SkillDoc]` | — | `append`, `len`, `list_skills`, `lower` |
| `learn_or_patch_skill` | `L84–L152` | `(self, skill_name: str, lesson_markd...)` | `dict` | — | `HermesSkillRevision`, `add`, `assert_safe_path`, `exists` |


---

### 📄 [`backend/hermes/tools_dispatcher.py`](/backend/hermes/tools_dispatcher.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `handle_report_company_threat` | `L38–L66` | `(args: dict[str, Any], session: Sess...)` | `dict[str, Any]` | — | `HermesMemory`, `create_checkpoint`, `emergency_quarantine_and_canary`, `record_fact` |
| `handle_restore_quarantined_company` | `L69–L96` | `(args: dict[str, Any], session: Sess...)` | `dict[str, Any]` | — | `HermesMemory`, `create_checkpoint`, `get`, `record_fact` |
| `handle_set_watchlist_tier` | `L99–L134` | `(args: dict[str, Any], session: Sess...)` | `dict[str, Any]` | — | `HermesMemory`, `ValueError`, `create_checkpoint`, `flush` |
| `handle_update_company_allocation` | `L137–L173` | `(args: dict[str, Any], session: Sess...)` | `dict[str, Any]` | — | `RuleAudit`, `ValueError`, `add`, `bool` |
| `handle_execute_manual_order` | `L176–L253` | `(args: dict[str, Any], session: Sess...)` | `dict[str, Any]` | — | `ThreadPoolExecutor`, `ValueError`, `all`, `create_checkpoint` |
| `handle_learn_or_patch_skill` | `L256–L282` | `(args: dict[str, Any], session: Sess...)` | `dict[str, Any]` | — | `create_checkpoint`, `get`, `learn_or_patch_skill` |
| `handle_set_automation_config` | `L285–L331` | `(args: dict[str, Any], session: Sess...)` | `dict[str, Any]` | — | `ValueError`, `bool`, `create_checkpoint`, `flush` |
| `handle_set_ai_model` | `L334–L379` | `(args: dict[str, Any], session: Sess...)` | `dict[str, Any]` | — | `create_checkpoint`, `flush`, `get`, `getattr` |
| `handle_evaluate_canary_theses` | `L382–L398` | `(session: Session, state: PortfolioS...)` | `dict[str, Any]` | — | `check_canary_theses`, `isoformat`, `learn_or_patch_skill` |
| `handle_control_stocknow_session` | `L401–L543` | `(args: dict[str, Any], session: Sess...)` | `dict[str, Any]` | — | `Database`, `StockNowLiveClient`, `ThreadPoolExecutor`, `append` |
| `dispatch_tool` | `L550–L584` | `(tool_name: str, args: dict[str, Any...)` | `dict[str, Any]` | Routes tool execution to dedicated handlers with low nesting depth (<= 3). | `ValueError`, `handle_control_stocknow_session`, `handle_evaluate_canary_theses`, `handle_execute_manual_order` |
| `_fmt_rollback` | `L591–L607` | `(res: dict[str, Any], bangla: bool...)` | `str` | — | `join` |
| `_fmt_report_threat` | `L610–L636` | `(res: dict[str, Any], bangla: bool...)` | `str` | — | — |
| `_fmt_watchlist_tier` | `L639–L650` | `(tool_res: dict[str, Any], bangla: b...)` | `str` | — | `get` |
| `_fmt_automation_config` | `L653–L675` | `(tool_res: dict[str, Any], bangla: b...)` | `str` | — | — |
| `_fmt_ai_model` | `L678–L708` | `(tool_res: dict[str, Any], bangla: b...)` | `str` | — | `get`, `join` |
| `format_tool_response` | `L711–L888` | `(tool_name: str, tool_res: dict[str,...)` | `str` | Formats human-friendly Bangla/English message summarizing the executed tool's outcome. | `_fmt_ai_model`, `_fmt_automation_config`, `_fmt_report_threat`, `_fmt_rollback` |
| `detect_intent_and_tool` | `L895–L1129` | `(message: str, snapshot: dict...)` | `tuple[str | None, dict[str, Any]]` | High-precision intent detector for Bangla, Banglish & English agent commands. | `any`, `float`, `get`, `int` |


---

### 📄 [`backend/main.py`](/backend/main.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `PauseRequest` | `L52–L54` | `BaseModel` | — | 0 |
| `AutomationConfigRequest` | `L57–L61` | `BaseModel` | — | 0 |
| `AdvanceRequest` | `L64–L66` | `BaseModel` | — | 0 |
| `AllocationRequest` | `L69–L72` | `BaseModel` | — | 0 |
| `EventBroadcaster` | `L75–L92` | `object` | — | 4 |
| `DevStaticFiles` | `L326–L332` | `StaticFiles` | — | 1 |


**Methods in `EventBroadcaster`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L76–L77` | `(self...)` | — | — | `set` |
| `subscribe` | `L79–L82` | `(self...)` | `asyncio.Queue` | — | `Queue`, `add` |
| `unsubscribe` | `L84–L85` | `(self, queue: asyncio.Queue...)` | — | — | `discard` |
| `publish` | `L87–L92` | `(self, event_type: str, data: dict...)` | — | — | `list`, `put_nowait` |


**Methods in `DevStaticFiles`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `get_response` | `L327–L332` | `(self, path: str, scope...)` | — | — | `get_response`, `super` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `create_app` | `L95–L346` | `(settings: Settings | None=None...)` | `FastAPI` | — | `AutoTrader`, `ChatService`, `DSEMarketScheduler`, `Database` |
| `lifespan` | `L105–L121` | `(_app: FastAPI...)` | — | — | `close`, `create_schema`, `dispose`, `migrate_real_stocknow_market` |
| `local_security` | `L137–L175` | `(request: Request, call_next...)` | — | — | `JSONResponse`, `call_next`, `compare_digest`, `encode` |
| `health` | `L178–L179` | `(...)` | — | — | `get` |
| `portfolio` | `L182–L183` | `(...)` | — | — | `build_snapshot`, `get` |
| `cycle` | `L186–L200` | `(idempotency_key: Annotated[UUID | N...)` | — | — | `HTTPException`, `Header`, `extract_quotes_from_stocknow`, `post` |
| `pause` | `L203–L210` | `(body: PauseRequest...)` | — | — | `portfolio_state`, `post`, `publish`, `write` |
| `automation_config` | `L213–L248` | `(body: AutomationConfigRequest...)` | — | — | `StockNowAdapter`, `ensure_authenticated`, `extract_quotes_from_stocknow`, `get_adapter_status` |
| `advance` | `L251–L262` | `(body: AdvanceRequest...)` | — | — | `Decimal`, `advance_demo`, `build_market_map_payload`, `get` |
| `market_map_endpoint` | `L265–L266` | `(...)` | — | — | `build_market_map_payload`, `get` |
| `allocation` | `L269–L292` | `(symbol: str, body: AllocationReques...)` | — | — | `HTTPException`, `RuleAudit`, `add`, `get` |
| `event_stream` | `L299–L324` | `(request: Request...)` | — | — | `StreamingResponse`, `generator`, `get`, `subscribe` |
| `generator` | `L302–L314` | `(...)` | — | — | `dumps`, `get`, `is_disconnected`, `unsubscribe` |
| `cockpit` | `L335–L343` | `(...)` | — | — | `FileResponse`, `get` |


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
| `generate_extended_history` | `L235–L287` | `(history: list[dict[str, str]], fund...)` | `dict[str, list[dict[str, Any]]]` | Generates 7d, 1m, 6m, 1y series for TradingView-style deep trend views. | `add_sessions`, `append`, `cos`, `float` |
| `rule_view` | `L290–L300` | `(rule: CustomRule...)` | `dict` | — | `decimal`, `float` |
| `trade_view` | `L303–L322` | `(trade: TradeLog...)` | `dict` | — | `float`, `isoformat` |
| `period_totals` | `L325–L340` | `(trades: list[TradeLog], start: date...)` | `dict` | — | `float`, `isoformat`, `len`, `sum` |
| `build_snapshot` | `L343–L345` | `(database: Database, settings: Setti...)` | `dict` | — | `read`, `snapshot_from_session` |
| `snapshot_from_session` | `L348–L662` | `(session: Session, settings: Setting...)` | `dict` | — | `SkillsManager`, `StockNowAdapter`, `TradingCalendar`, `abs` |
| `normalized_watchlist` | `L665–L684` | `(companies: list[dict]...)` | `list[dict]` | Equal-weight normalized PRICE index, explicitly not portfolio performance. | `any`, `append`, `decimal`, `float` |


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
| `build_auth_settings_router` | `L40–L175` | `(database: Database, settings: Setti...)` | `APIRouter` | — | `APIRouter` |
| `login` | `L44–L58` | `(body: LoginRequest...)` | — | — | `HTTPException`, `add`, `post`, `uuid4` |
| `logout` | `L61–L65` | `(request: Request...)` | — | — | `discard`, `get`, `post`, `replace` |
| `auth_session` | `L68–L80` | `(request: Request...)` | — | — | `bool`, `get`, `replace`, `strip` |
| `get_api_keys` | `L83–L124` | `(...)` | — | — | `bool`, `date`, `get`, `getattr` |
| `mask_single` | `L84–L89` | `(s: str...)` | `str` | — | `len` |
| `mask` | `L91–L97` | `(s: str...)` | `str` | — | `join`, `len`, `mask_single`, `replace` |
| `update_api_keys` | `L127–L173` | `(body: KeysSettingsRequest...)` | — | — | `__setattr__`, `append`, `create_checkpoint`, `join` |


---

### 📄 [`backend/routes_hermes.py`](/backend/routes_hermes.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `CreateThreadRequest` | `L21–L23` | `BaseModel` | — | 0 |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `build_hermes_router` | `L26–L209` | `(database: Database, settings: Setti...)` | `APIRouter` | — | `APIRouter` |
| `chat_route` | `L30–L34` | `(body: ChatRequest...)` | — | — | `get`, `post`, `publish`, `respond` |
| `list_conversations` | `L37–L41` | `(...)` | — | — | `HermesMemory`, `get`, `list_threads`, `read` |
| `create_conversation` | `L44–L55` | `(body: CreateThreadRequest...)` | — | — | `HermesMemory`, `get_or_create_thread`, `post`, `write` |
| `conversation_messages` | `L58–L62` | `(conversation_id: str...)` | — | — | `HermesMemory`, `get`, `get_thread_messages`, `read` |
| `system_changes` | `L65–L127` | `(...)` | — | — | `Path`, `append`, `desc`, `get` |
| `hermes_models` | `L130–L162` | `(...)` | — | — | `any`, `bool`, `get`, `getattr` |
| `set_hermes_model` | `L165–L198` | `(payload: dict...)` | — | — | `HTTPException`, `create_checkpoint`, `get`, `getattr` |
| `rollback_checkpoint` | `L201–L207` | `(...)` | — | — | `portfolio_state`, `post`, `publish`, `rollback_last` |


---

### 📄 [`backend/routes_stocknow.py`](/backend/routes_stocknow.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `StockNowSessionActionRequest` | `L30–L33` | `BaseModel` | — | 0 |
| `StockNowMarketSyncRequest` | `L36–L38` | `BaseModel` | — | 0 |
| `StockNowPortfolioSyncRequest` | `L41–L43` | `BaseModel` | — | 0 |
| `StockNowExecuteOrderRequest` | `L46–L52` | `BaseModel` | — | 0 |
| `StockNowSchedulerActionRequest` | `L55–L58` | `BaseModel` | — | 0 |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `build_stocknow_router` | `L61–L254` | `(database: Database, settings: Setti...)` | `APIRouter` | — | `APIRouter`, `DSEMarketScheduler`, `StockNowLiveClient`, `get_active_scheduler` |
| `get_stocknow_status` | `L80–L81` | `(...)` | — | — | `get`, `get_status` |
| `post_stocknow_session` | `L84–L117` | `(body: StockNowSessionActionRequest...)` | — | — | `HTTPException`, `_background_auth`, `close`, `create_task` |
| `_background_auth` | `L92–L99` | `(...)` | — | — | `ensure_authenticated`, `get_status`, `publish`, `warning` |
| `post_stocknow_sync_market` | `L120–L129` | `(body: StockNowMarketSyncRequest | N...)` | — | — | `build_snapshot`, `extract_quotes_from_stocknow`, `post`, `publish` |
| `post_stocknow_sync_portfolio` | `L132–L155` | `(body: StockNowPortfolioSyncRequest ...)` | — | — | `build_snapshot`, `debug`, `extract_hummingbird_portfolio`, `extract_hummingbird_portfolio_from_browser` |
| `post_stocknow_execute_order` | `L158–L237` | `(body: StockNowExecuteOrderRequest...)` | — | — | `HTTPException`, `all`, `build_snapshot`, `create_checkpoint` |
| `get_stocknow_scheduler` | `L240–L241` | `(...)` | — | — | `get`, `get_status` |
| `post_stocknow_scheduler` | `L244–L252` | `(body: StockNowSchedulerActionReques...)` | — | — | `HTTPException`, `post`, `run_scheduled_tick`, `start` |


---

### 📄 [`backend/seed.py`](/backend/seed.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `seed_demo` | `L35–L121` | `(session: Session, settings: Setting...)` | `None` | — | `CompanyProfile`, `CustomRule`, `Decimal`, `PortfolioState` |
| `migrate_real_stocknow_market` | `L141–L298` | `(session: Session, settings: Setting...)` | `None` | Migrates existing SQLite database on boot to real StockNow #164580 portfolio and watchlist. | `CompanyProfile`, `CustomRule`, `Decimal`, `TaxLot` |


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

## 4. Database Schema X-Ray (`backend/database.py`)

SQLAlchemy ORM Entities backing the deterministic ledger and Hermes state store:

| Model Entity | Line Range | Base | Purpose & Managed Ledger State |
| :--- | :--- | :--- | :--- |
| `PortfolioState` | `L41–L57` | `Base` | Durable transactional entity |
| `CompanyProfile` | `L60–L73` | `Base` | Durable transactional entity |
| `CustomRule` | `L76–L87` | `Base` | Durable transactional entity |
| `TaxLot` | `L90–L115` | `Base` | Durable transactional entity |
| `AutomationCycle` | `L118–L127` | `Base` | Durable transactional entity |
| `TradeLog` | `L130–L155` | `Base` | Durable transactional entity |
| `CanaryThesis` | `L158–L170` | `Base` | Durable transactional entity |
| `HermesSkillRevision` | `L173–L181` | `Base` | Durable transactional entity |
| `HermesUserProfile` | `L184–L195` | `Base` | Durable transactional entity |
| `HermesConversationThread` | `L198–L203` | `Base` | Durable transactional entity |
| `HermesSessionMemory` | `L206–L215` | `Base` | Durable transactional entity |
| `HermesDurableFact` | `L218–L226` | `Base` | Durable transactional entity |
| `HermesStateCheckpoint` | `L229–L239` | `Base` | Durable transactional entity |
| `CycleRequestKey` | `L242–L245` | `Base` | Durable transactional entity |
| `DecisionLog` | `L248–L257` | `Base` | Durable transactional entity |
| `RuleAudit` | `L260–L267` | `Base` | Durable transactional entity |
| `ChatBudget` | `L270–L273` | `Base` | Durable transactional entity |

---

## 5. FastAPI Route Registry (All Sub-Routers & Endpoints)

| Method | Route Path | Module File | Line | Handler Function | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | [`backend/main.py`](/backend/main.py#L178) | `L178` | `health()` | Route endpoint |
| `GET` | `/api/portfolio` | [`backend/main.py`](/backend/main.py#L182) | `L182` | `portfolio()` | Route endpoint |
| `POST` | `/api/automation/cycle` | [`backend/main.py`](/backend/main.py#L186) | `L186` | `cycle()` | Route endpoint |
| `POST` | `/api/automation/pause` | [`backend/main.py`](/backend/main.py#L203) | `L203` | `pause()` | Route endpoint |
| `POST` | `/api/automation/config` | [`backend/main.py`](/backend/main.py#L213) | `L213` | `automation_config()` | Route endpoint |
| `POST` | `/api/demo/advance` | [`backend/main.py`](/backend/main.py#L251) | `L251` | `advance()` | Route endpoint |
| `GET` | `/api/market/map` | [`backend/main.py`](/backend/main.py#L265) | `L265` | `market_map_endpoint()` | Route endpoint |
| `PATCH` | `/api/companies/{symbol}/allocation` | [`backend/main.py`](/backend/main.py#L269) | `L269` | `allocation()` | Route endpoint |
| `GET` | `/api/stream` | [`backend/main.py`](/backend/main.py#L299) | `L299` | `event_stream()` | Route endpoint |
| `GET` | `/` | [`backend/main.py`](/backend/main.py#L335) | `L335` | `cockpit()` | Route endpoint |
| `POST` | `/api/chat` | [`backend/routes_hermes.py`](/backend/routes_hermes.py#L30) | `L30` | `chat_route()` | Route endpoint |
| `GET` | `/api/hermes/conversations` | [`backend/routes_hermes.py`](/backend/routes_hermes.py#L37) | `L37` | `list_conversations()` | Route endpoint |
| `POST` | `/api/hermes/conversations` | [`backend/routes_hermes.py`](/backend/routes_hermes.py#L44) | `L44` | `create_conversation()` | Route endpoint |
| `GET` | `/api/hermes/conversations/{conversation_id}/messages` | [`backend/routes_hermes.py`](/backend/routes_hermes.py#L58) | `L58` | `conversation_messages()` | Route endpoint |
| `GET` | `/api/system/changes` | [`backend/routes_hermes.py`](/backend/routes_hermes.py#L65) | `L65` | `system_changes()` | Route endpoint |
| `GET` | `/api/hermes/models` | [`backend/routes_hermes.py`](/backend/routes_hermes.py#L130) | `L130` | `hermes_models()` | Route endpoint |
| `POST` | `/api/hermes/model` | [`backend/routes_hermes.py`](/backend/routes_hermes.py#L165) | `L165` | `set_hermes_model()` | Route endpoint |
| `POST` | `/api/hermes/rollback` | [`backend/routes_hermes.py`](/backend/routes_hermes.py#L201) | `L201` | `rollback_checkpoint()` | Route endpoint |
| `POST` | `/api/auth/login` | [`backend/routes_auth_settings.py`](/backend/routes_auth_settings.py#L44) | `L44` | `login()` | Route endpoint |
| `POST` | `/api/auth/logout` | [`backend/routes_auth_settings.py`](/backend/routes_auth_settings.py#L61) | `L61` | `logout()` | Route endpoint |
| `GET` | `/api/auth/session` | [`backend/routes_auth_settings.py`](/backend/routes_auth_settings.py#L68) | `L68` | `auth_session()` | Route endpoint |
| `GET` | `/api/settings/keys` | [`backend/routes_auth_settings.py`](/backend/routes_auth_settings.py#L83) | `L83` | `get_api_keys()` | Route endpoint |
| `POST` | `/api/settings/keys` | [`backend/routes_auth_settings.py`](/backend/routes_auth_settings.py#L127) | `L127` | `update_api_keys()` | Route endpoint |
| `GET` | `/api/stocknow/status` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L80) | `L80` | `get_stocknow_status()` | Route endpoint |
| `POST` | `/api/stocknow/session` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L84) | `L84` | `post_stocknow_session()` | Route endpoint |
| `POST` | `/api/stocknow/sync-market` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L120) | `L120` | `post_stocknow_sync_market()` | Route endpoint |
| `POST` | `/api/stocknow/sync-portfolio` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L132) | `L132` | `post_stocknow_sync_portfolio()` | Route endpoint |
| `POST` | `/api/stocknow/execute-order` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L158) | `L158` | `post_stocknow_execute_order()` | Route endpoint |
| `GET` | `/api/stocknow/scheduler` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L240) | `L240` | `get_stocknow_scheduler()` | Route endpoint |
| `POST` | `/api/stocknow/scheduler` | [`backend/routes_stocknow.py`](/backend/routes_stocknow.py#L244) | `L244` | `post_stocknow_scheduler()` | Route endpoint |

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
| `.diff-card` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L1327) | `L1327` | — | — | — | `var(--panel)` | — |
| `.model-dropup-menu` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L1456) | `L1456` | — | — | `absolute` | `var(--panel)` | — |
| `.model-dropup-menu` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L1470) | `L1470` | — | — | — | `#ffffff` | — |
| `.workspace` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L1593) | `L1593` | — | — | — | — | — |
| `.skills-drawer` | [`frontend/theme_light_hermes.css`](/frontend/theme_light_hermes.css#L1924) | `L1924` | — | — | — | `#ffffff !important` | — |


### Key DOM Identifiers (`frontend/index.html`)

Identified **253** distinct element IDs in the UI shell. Key controller anchors:

`#overview`, `#watchlist`, `#market-map`, `#master-automation-toggle`, `#mode-btn-polling`, `#mode-btn-live`, `#polling-interval-pills`, `#main-chart`, `#bucket-stack`, `#what-if-slider`, `#theme-toggle-btn`, `#topbar-clock-widget`


### Frontend Stylesheets (`frontend/*.css`)

| Stylesheet File | Lines | Purpose |
| :--- | :--- | :--- |
| `styles.css` | 5225 | Core design tokens, layout & widgets |
| `theme_light_hermes.css` | 2640 | Daylight overrides & Hermes IDE sidebar |


### Frontend API Contract Invocations (`frontend/*.js`)

| Endpoint Invocated | Direction | Purpose |
| :--- | :--- | :--- |
| `/api/auth/login` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/auth/logout` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/auth/session` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/automation/config` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/automation/cycle` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/automation/pause` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/chat` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/demo/advance` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/hermes/conversations` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/hermes/model` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/hermes/models` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/hermes/rollback` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/portfolio` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/settings/keys` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
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
| `renderEquitySparkline()` | `app.js` | `L250` | Reactive DOM rendering / event controller |
| `renderActiveHoldings()` | `app.js` | `L264` | Reactive DOM rendering / event controller |
| `renderBuckets()` | `app.js` | `L393` | Reactive DOM rendering / event controller |
| `cell()` | `app.js` | `L425` | Reactive DOM rendering / event controller |
| `selectCompany()` | `app.js` | `L427` | Reactive DOM rendering / event controller |
| `renderWatchlist()` | `app.js` | `L434` | Reactive DOM rendering / event controller |
| `renderCanaryTheses()` | `app.js` | `L504` | Reactive DOM rendering / event controller |
| `renderInspector()` | `app.js` | `L538` | Reactive DOM rendering / event controller |
| `renderDecisions()` | `app.js` | `L573` | Reactive DOM rendering / event controller |
| `renderLedger()` | `app.js` | `L613` | Reactive DOM rendering / event controller |
| `initMarketMapResizeObserver()` | `app.js` | `L752` | Reactive DOM rendering / event controller |
| `initTheme()` | `app.js` | `L778` | Reactive DOM rendering / event controller |
| `setTheme()` | `app.js` | `L784` | Reactive DOM rendering / event controller |
| `toggleTheme()` | `app.js` | `L795` | Reactive DOM rendering / event controller |
| `tickMarketClock()` | `app.js` | `L801` | Reactive DOM rendering / event controller |
| `tickClock()` | `app.js` | `L872` | Reactive DOM rendering / event controller |
| `renderAutomationControlBar()` | `app.js` | `L881` | Reactive DOM rendering / event controller |
| `setAutomationConfig()` | `app.js` | `L1022` | Reactive DOM rendering / event controller |
| `initRealtimeStream()` | `app.js` | `L1167` | Reactive DOM rendering / event controller |
| `switchView()` | `app.js` | `L1193` | Reactive DOM rendering / event controller |
| `initViewRouter()` | `app.js` | `L1244` | Reactive DOM rendering / event controller |
| `initScrollSpy()` | `app.js` | `L1310` | Reactive DOM rendering / event controller |
| `updateActiveNav()` | `app.js` | `L1323` | Reactive DOM rendering / event controller |
| `smoothCurvePath()` | `charts.js` | `L8` | Reactive DOM rendering / event controller |
| `getBezierPointAtContinuousIndex()` | `charts.js` | `L31` | Reactive DOM rendering / event controller |
| `renderMainChart()` | `charts.js` | `L63` | Reactive DOM rendering / event controller |
| `sparkline()` | `charts.js` | `L350` | Reactive DOM rendering / event controller |
| `squarify()` | `charts.js` | `L365` | Reactive DOM rendering / event controller |
| `layoutRow()` | `charts.js` | `L375` | Reactive DOM rendering / event controller |
| `worst()` | `charts.js` | `L422` | Reactive DOM rendering / event controller |
| `showTreemapTooltip()` | `charts.js` | `L459` | Reactive DOM rendering / event controller |
| `hideTreemapTooltip()` | `charts.js` | `L472` | Reactive DOM rendering / event controller |
| `renderMarketMap()` | `charts.js` | `L477` | Reactive DOM rendering / event controller |
| `renderTopSectorsChart()` | `charts.js` | `L656` | Reactive DOM rendering / event controller |
| `renderGainerChart()` | `charts.js` | `L816` | Reactive DOM rendering / event controller |
| `updateWhatIfSimulator()` | `charts.js` | `L821` | Reactive DOM rendering / event controller |
| `updateModalSimulator()` | `charts.js` | `L865` | Reactive DOM rendering / event controller |
| `openDeepTrendModal()` | `charts.js` | `L904` | Reactive DOM rendering / event controller |
| `closeDeepTrendModal()` | `charts.js` | `L961` | Reactive DOM rendering / event controller |
| `renderDeepTrendChart()` | `charts.js` | `L971` | Reactive DOM rendering / event controller |
| `initCharts()` | `charts.js` | `L1255` | Reactive DOM rendering / event controller |
| `renderHermesSkills()` | `hermes_ui.js` | `L8` | Reactive DOM rendering / event controller |
| `formatChatMarkdown()` | `hermes_ui.js` | `L52` | Reactive DOM rendering / event controller |
| `syncQuickPromptsPlacement()` | `hermes_ui.js` | `L93` | Reactive DOM rendering / event controller |
| `addMessage()` | `hermes_ui.js` | `L113` | Reactive DOM rendering / event controller |
| `sendChat()` | `hermes_ui.js` | `L133` | Reactive DOM rendering / event controller |
| `initHermesSidebar()` | `hermes_ui.js` | `L208` | Reactive DOM rendering / event controller |
| `loadConversations()` | `hermes_ui.js` | `L353` | Reactive DOM rendering / event controller |
| `switchConversation()` | `hermes_ui.js` | `L387` | Reactive DOM rendering / event controller |
| `createNewConversation()` | `hermes_ui.js` | `L416` | Reactive DOM rendering / event controller |
| `formatRelativeTime()` | `hermes_ui.js` | `L443` | Reactive DOM rendering / event controller |
| `escapeHtml()` | `hermes_ui.js` | `L457` | Reactive DOM rendering / event controller |
| `executeRollback()` | `hermes_ui.js` | `L467` | Reactive DOM rendering / event controller |
| `loadHermesModels()` | `hermes_ui.js` | `L490` | Reactive DOM rendering / event controller |
| `switchHermesModel()` | `hermes_ui.js` | `L564` | Reactive DOM rendering / event controller |
| `loadApiKeysSettings()` | `hermes_ui.js` | `L617` | Reactive DOM rendering / event controller |
| `saveApiKeysSettings()` | `hermes_ui.js` | `L683` | Reactive DOM rendering / event controller |
| `checkAuthSession()` | `hermes_ui.js` | `L735` | Reactive DOM rendering / event controller |
| `openOperatorProfile()` | `hermes_ui.js` | `L753` | Reactive DOM rendering / event controller |
| `closeOperatorProfile()` | `hermes_ui.js` | `L758` | Reactive DOM rendering / event controller |
| `handleOperatorLogin()` | `hermes_ui.js` | `L763` | Reactive DOM rendering / event controller |
| `handleOperatorLogout()` | `hermes_ui.js` | `L792` | Reactive DOM rendering / event controller |
| `markKeysDirty()` | `hermes_ui.js` | `L802` | Reactive DOM rendering / event controller |
| `initAuthAndSettings()` | `hermes_ui.js` | `L812` | Reactive DOM rendering / event controller |
| `loadSystemChanges()` | `hermes_ui.js` | `L889` | Reactive DOM rendering / event controller |
| `initHermesChatListeners()` | `hermes_ui.js` | `L977` | Reactive DOM rendering / event controller |

---

## 7. Code Health & Complexity Radar

Functions requiring architectural attention (> 70 lines or nesting depth >= 4):


| File | Function / Method | Length (Lines) | Max Nesting Depth | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| `backend/adapters/stocknow_client.py` | `_launch_internal` | 82 | 6 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_client.py` | `_ensure_authenticated_internal` | 209 | 7 | Decompose into sub-functions |
| `backend/adapters/stocknow_client.py` | `_discover_portfolio_internal` | 66 | 5 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_market_sync.py` | `_normalize_history_series` | 16 | 6 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_market_sync.py` | `extract_quotes_from_payload` | 88 | 6 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_market_sync.py` | `_extract_quotes_from_stocknow_impl` | 154 | 4 | Decompose into sub-functions |
| `backend/adapters/stocknow_market_sync.py` | `_sync_in_session` | 93 | 4 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_order_executor.py` | `_execute_stocknow_virtual_order_impl` | 180 | 6 | Decompose into sub-functions |
| `backend/adapters/stocknow_portfolio_sync.py` | `_find_portfolio_dict` | 17 | 5 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_portfolio_sync.py` | `extract_hummingbird_portfolio` | 59 | 6 | Acceptable; well-scoped logic |
| `backend/adapters/stocknow_portfolio_sync.py` | `_extract_hummingbird_portfolio_from_browser_impl` | 102 | 7 | Decompose into sub-functions |
| `backend/adapters/stocknow_portfolio_sync.py` | `_execute_reconciliation` | 117 | 3 | Decompose into sub-functions |
| `backend/chat.py` | `match_symbol` | 16 | 4 | Acceptable; well-scoped logic |
| `backend/chat.py` | `format_canary_updates` | 16 | 4 | Acceptable; well-scoped logic |
| `backend/chat.py` | `local_summary` | 99 | 6 | Acceptable; well-scoped logic |
| `backend/database.py` | `create_schema` | 36 | 4 | Acceptable; well-scoped logic |
| `backend/engine/agent_actions.py` | `emergency_quarantine_and_canary` | 106 | 5 | Decompose into sub-functions |
| `backend/engine/agent_actions.py` | `check_canary_theses` | 31 | 4 | Acceptable; well-scoped logic |
| `backend/engine/agent_actions.py` | `execute_agentic_buy` | 83 | 3 | Acceptable; well-scoped logic |
| `backend/engine/agent_actions.py` | `execute_agentic_sell` | 101 | 3 | Decompose into sub-functions |
| `backend/engine/auto_trader.py` | `_run_cycle_internal` | 258 | 7 | Decompose into sub-functions |
| `backend/engine/auto_trader.py` | `advance_demo` | 38 | 5 | Acceptable; well-scoped logic |
| `backend/engine/curve_analyzer.py` | `analyze_curve` | 82 | 3 | Acceptable; well-scoped logic |
| `backend/engine/scheduler.py` | `is_dse_market_open` | 44 | 4 | Acceptable; well-scoped logic |
| `backend/engine/scheduler.py` | `run_scheduled_tick` | 58 | 4 | Acceptable; well-scoped logic |
| `backend/engine/scheduler.py` | `_loop` | 21 | 4 | Acceptable; well-scoped logic |
| `backend/engine/sequential_seller.py` | `plan_sale` | 105 | 3 | Decompose into sub-functions |
| `backend/engine/t2_ledger.py` | `bucket_balances` | 31 | 4 | Acceptable; well-scoped logic |
| `backend/hermes/agent_loop.py` | `rollback_last` | 104 | 3 | Decompose into sub-functions |
| `backend/hermes/agent_loop.py` | `run_turn` | 78 | 4 | Acceptable; well-scoped logic |
| `backend/hermes/agent_loop.py` | `_call_gemini_with_key_rotation` | 91 | 7 | Acceptable; well-scoped logic |
| `backend/hermes/agent_loop.py` | `_conversational_inference` | 158 | 5 | Decompose into sub-functions |
| `backend/hermes/memory.py` | `record_turn` | 29 | 4 | Acceptable; well-scoped logic |
| `backend/hermes/memory.py` | `search_sessions` | 28 | 4 | Acceptable; well-scoped logic |
| `backend/hermes/memory.py` | `format_layer_3_prompt` | 17 | 5 | Acceptable; well-scoped logic |
| `backend/hermes/secret_guard.py` | `redact_secrets` | 11 | 4 | Acceptable; well-scoped logic |
| `backend/hermes/skills_manager.py` | `match_skills` | 22 | 4 | Acceptable; well-scoped logic |
| `backend/hermes/tools_dispatcher.py` | `handle_execute_manual_order` | 78 | 3 | Acceptable; well-scoped logic |
| `backend/hermes/tools_dispatcher.py` | `handle_control_stocknow_session` | 143 | 12 | Decompose into sub-functions |
| `backend/hermes/tools_dispatcher.py` | `dispatch_tool` | 35 | 12 | Acceptable; well-scoped logic |
| `backend/hermes/tools_dispatcher.py` | `format_tool_response` | 178 | 9 | Decompose into sub-functions |
| `backend/hermes/tools_dispatcher.py` | `detect_intent_and_tool` | 235 | 5 | Decompose into sub-functions |
| `backend/main.py` | `create_app` | 252 | 4 | Decompose into sub-functions |
| `backend/main.py` | `local_security` | 39 | 4 | Acceptable; well-scoped logic |
| `backend/main.py` | `cycle` | 15 | 4 | Acceptable; well-scoped logic |
| `backend/main.py` | `automation_config` | 36 | 4 | Acceptable; well-scoped logic |
| `backend/main.py` | `event_stream` | 26 | 4 | Acceptable; well-scoped logic |
| `backend/main.py` | `generator` | 13 | 4 | Acceptable; well-scoped logic |
| `backend/market_map.py` | `build_market_map_payload` | 72 | 5 | Acceptable; well-scoped logic |
| `backend/portfolio.py` | `snapshot_from_session` | 315 | 5 | Decompose into sub-functions |
| `backend/portfolio.py` | `normalized_watchlist` | 20 | 4 | Acceptable; well-scoped logic |
| `backend/routes_auth_settings.py` | `build_auth_settings_router` | 136 | 2 | Decompose into sub-functions |
| `backend/routes_hermes.py` | `build_hermes_router` | 184 | 5 | Decompose into sub-functions |
| `backend/routes_hermes.py` | `system_changes` | 63 | 5 | Acceptable; well-scoped logic |
| `backend/routes_stocknow.py` | `build_stocknow_router` | 194 | 4 | Decompose into sub-functions |
| `backend/routes_stocknow.py` | `post_stocknow_session` | 34 | 4 | Acceptable; well-scoped logic |
| `backend/routes_stocknow.py` | `post_stocknow_sync_portfolio` | 24 | 4 | Acceptable; well-scoped logic |
| `backend/routes_stocknow.py` | `post_stocknow_execute_order` | 80 | 4 | Acceptable; well-scoped logic |
| `backend/routes_stocknow.py` | `post_stocknow_scheduler` | 9 | 4 | Acceptable; well-scoped logic |
| `backend/seed.py` | `seed_demo` | 87 | 3 | Acceptable; well-scoped logic |
| `backend/seed.py` | `migrate_real_stocknow_market` | 158 | 7 | Decompose into sub-functions |
| `scripts/generate_code_map.py` | `is_ignored` | 6 | 4 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `collect_file_metrics` | 15 | 4 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `parse_fastapi_routes` | 38 | 10 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `parse_css_design` | 103 | 8 | Decompose into sub-functions |
| `scripts/generate_code_map.py` | `scan_file` | 50 | 8 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `parse_frontend` | 26 | 4 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `generate_markdown` | 189 | 6 | Decompose into sub-functions |
| `scripts/generate_code_map.py` | `visit_Call` | 10 | 4 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `_compute_depth` | 12 | 4 | Acceptable; well-scoped logic |


> **Audit Summary:** 33 Python modules inspected, 30 FastAPI endpoints registered, 26,647 total LOC indexed.