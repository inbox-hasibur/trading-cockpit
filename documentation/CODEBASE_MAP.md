# 🗺️ Codebase AST Map & System Architecture Radar

> Auto-generated via `scripts/generate_code_map.py` (Zero-dependency stdlib AST inspection) on **2026-11-05 14:03:37 UTC**.

---

## 1. Repository Topology & File Metrics

| Extension / Type | File Count | Total Lines of Code | Description |
| :--- | :--- | :--- | :--- |
| `.css` | 2 | 6,705 | Custom Dark / Light / Terminal Design System |
| `.py` | 31 | 6,041 | Python Core Kernel, Engine & Hermes Agent |
| `.js` | 3 | 2,938 | Vanilla ES6+ Reactive Terminal Controller |
| `.md` | 10 | 1,666 | Architecture & Strategy Documentation |
| `.html` | 1 | 837 | Single Page Application DOM Structure |
| `.agentignore` | 1 | 12 | Configuration / Asset |
| `.cursorignore` | 1 | 12 | Configuration / Asset |
| `.opencodeignore` | 1 | 12 | Configuration / Asset |
| `.txt` | 2 | 11 | Dependency Specifications |
| `.toml` | 1 | 10 | PyProject Configuration |
| `.svg` | 1 | 1 | Configuration / Asset |
| **TOTAL** | **54** | **18,245** | *Entire Humming Bird Repository* |

## 2. Internal Dependency & Import Graph

Shows intra-repo module dependencies within `backend/` and `scripts/`:

| Module File | Imported Internal Dependencies |
| :--- | :--- |
| [`backend/__init__.py`](/backend/__init__.py) | *Independent Core Module* |
| [`backend/adapters/__init__.py`](/backend/adapters/__init__.py) | *Independent Core Module* |
| [`backend/adapters/stocknow_adapter.py`](/backend/adapters/stocknow_adapter.py) | `backend.database.CompanyProfile`, `backend.engine.money.ZERO`, `backend.engine.money.decimal` |
| [`backend/chat.py`](/backend/chat.py) | `backend.config.DHAKA`, `backend.config.Settings`, `backend.database.CanaryThesis`, `backend.database.ChatBudget`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.PortfolioState`, `backend.database.portfolio_state`, `backend.engine.agent_actions.check_canary_theses`, `backend.engine.agent_actions.emergency_quarantine_and_canary`, `backend.engine.agent_actions.execute_agentic_buy`, `backend.engine.agent_actions.restore_quarantine`, `backend.hermes.agent_loop.HermesAgentLoop`, `backend.portfolio.build_snapshot` |
| [`backend/config.py`](/backend/config.py) | *Independent Core Module* |
| [`backend/database.py`](/backend/database.py) | `backend.config.utc_now_iso` |
| [`backend/engine/__init__.py`](/backend/engine/__init__.py) | *Independent Core Module* |
| [`backend/engine/agent_actions.py`](/backend/engine/agent_actions.py) | `backend.config.Settings`, `backend.database.CanaryThesis`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.DecisionLog`, `backend.database.PortfolioState`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.engine.money.ZERO`, `backend.engine.money.allocated_basis`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.price`, `backend.engine.money.purchase_amount`, `backend.engine.money.sale_amount`, `backend.engine.money.whole_shares`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.assert_ledger`, `backend.engine.t2_ledger.bucket_balances` |
| [`backend/engine/auto_trader.py`](/backend/engine/auto_trader.py) | `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.config.Settings`, `backend.database.AutomationCycle`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.CycleRequestKey`, `backend.database.Database`, `backend.database.DecisionLog`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.database.portfolio_state`, `backend.engine.agent_actions.check_canary_theses`, `backend.engine.money.HUNDRED`, `backend.engine.money.ZERO`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.price`, `backend.engine.money.purchase_amount`, `backend.engine.money.whole_shares`, `backend.engine.sequential_seller.SellState`, `backend.engine.sequential_seller.plan_sale`, `backend.engine.signals.BLOCK_ALL_TRADING`, `backend.engine.signals.assess_company`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.assert_ledger`, `backend.engine.t2_ledger.bucket_balances` |
| [`backend/engine/curve_analyzer.py`](/backend/engine/curve_analyzer.py) | `backend.engine.money.HUNDRED`, `backend.engine.money.ZERO`, `backend.engine.money.decimal` |
| [`backend/engine/money.py`](/backend/engine/money.py) | *Independent Core Module* |
| [`backend/engine/sequential_seller.py`](/backend/engine/sequential_seller.py) | `backend.engine.money.HUNDRED`, `backend.engine.money.ZERO`, `backend.engine.money.allocated_basis`, `backend.engine.money.sale_amount`, `backend.engine.money.whole_shares` |
| [`backend/engine/signals.py`](/backend/engine/signals.py) | `backend.adapters.stocknow_adapter.DemoQuote`, `backend.adapters.stocknow_adapter.QuoteError`, `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.config.Settings`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.engine.curve_analyzer.CurveAnalysis`, `backend.engine.curve_analyzer.analyze_curve`, `backend.engine.money.decimal` |
| [`backend/engine/t2_ledger.py`](/backend/engine/t2_ledger.py) | `backend.database.PortfolioState`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.engine.money.CENT`, `backend.engine.money.ZERO`, `backend.engine.money.money` |
| [`backend/hermes/__init__.py`](/backend/hermes/__init__.py) | `backend.hermes.secret_guard.SecretGuard`, `backend.hermes.secret_guard.SecurityViolation`, `backend.hermes.secret_guard.redact_secrets` |
| [`backend/hermes/agent_loop.py`](/backend/hermes/agent_loop.py) | `backend.chat.local_summary`, `backend.config.DHAKA`, `backend.config.Settings`, `backend.database.ChatBudget`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.HermesStateCheckpoint`, `backend.database.PortfolioState`, `backend.database.portfolio_state`, `backend.engine.money.decimal`, `backend.hermes.memory.HermesMemory`, `backend.hermes.secret_guard.SecretGuard`, `backend.hermes.secret_guard.redact_secrets`, `backend.hermes.skills_manager.SkillsManager`, `backend.hermes.tools_dispatcher.detect_intent_and_tool`, `backend.hermes.tools_dispatcher.dispatch_tool`, `backend.hermes.tools_dispatcher.format_tool_response`, `backend.portfolio.build_snapshot` |
| [`backend/hermes/memory.py`](/backend/hermes/memory.py) | `backend.config.utc_now_iso`, `backend.database.CanaryThesis`, `backend.database.CompanyProfile`, `backend.database.HermesConversationThread`, `backend.database.HermesDurableFact`, `backend.database.HermesSessionMemory`, `backend.database.HermesUserProfile`, `backend.hermes.secret_guard.redact_secrets` |
| [`backend/hermes/secret_guard.py`](/backend/hermes/secret_guard.py) | *Independent Core Module* |
| [`backend/hermes/skills_manager.py`](/backend/hermes/skills_manager.py) | `backend.database.HermesSkillRevision`, `backend.hermes.secret_guard.SecretGuard` |
| [`backend/hermes/tools_dispatcher.py`](/backend/hermes/tools_dispatcher.py) | `backend.config.Settings`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.PortfolioState`, `backend.database.RuleAudit`, `backend.engine.agent_actions.check_canary_theses`, `backend.engine.agent_actions.emergency_quarantine_and_canary`, `backend.engine.agent_actions.execute_agentic_buy`, `backend.engine.agent_actions.restore_quarantine`, `backend.engine.money.decimal`, `backend.hermes.memory.HermesMemory`, `backend.hermes.skills_manager.SkillsManager` |
| [`backend/main.py`](/backend/main.py) | `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.chat.ChatRequest`, `backend.chat.ChatService`, `backend.config.ROOT`, `backend.config.Settings`, `backend.config.VERSION`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.RuleAudit`, `backend.database.portfolio_state`, `backend.engine.auto_trader.AutoTrader`, `backend.engine.auto_trader.AutomationPaused`, `backend.engine.money.ZERO`, `backend.market_map.build_market_map_payload`, `backend.portfolio.build_snapshot`, `backend.portfolio.rule_view`, `backend.routes_auth_settings.KeysSettingsRequest`, `backend.routes_auth_settings.LoginRequest`, `backend.routes_auth_settings.build_auth_settings_router`, `backend.routes_hermes.CreateThreadRequest`, `backend.routes_hermes.build_hermes_router`, `backend.seed.seed_demo` |
| [`backend/market_map.py`](/backend/market_map.py) | *Independent Core Module* |
| [`backend/portfolio.py`](/backend/portfolio.py) | `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.config.DHAKA`, `backend.config.Settings`, `backend.config.VERSION`, `backend.database.AutomationCycle`, `backend.database.CanaryThesis`, `backend.database.ChatBudget`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.DecisionLog`, `backend.database.HermesDurableFact`, `backend.database.HermesSkillRevision`, `backend.database.HermesStateCheckpoint`, `backend.database.HermesUserProfile`, `backend.database.RuleAudit`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.database.portfolio_state`, `backend.engine.money.HUNDRED`, `backend.engine.money.ZERO`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.sale_amount`, `backend.engine.signals.assess_company`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.bucket_balances`, `backend.hermes.skills_manager.SkillsManager`, `backend.market_map.build_market_map_payload` |
| [`backend/routes_auth_settings.py`](/backend/routes_auth_settings.py) | `backend.config.DHAKA`, `backend.config.Settings`, `backend.database.ChatBudget`, `backend.database.Database`, `backend.database.HermesSessionMemory`, `backend.database.portfolio_state`, `backend.hermes.agent_loop.CheckpointManager` |
| [`backend/routes_hermes.py`](/backend/routes_hermes.py) | `backend.chat.ChatRequest`, `backend.chat.ChatService`, `backend.config.Settings`, `backend.database.Database`, `backend.database.HermesSkillRevision`, `backend.database.HermesStateCheckpoint`, `backend.database.portfolio_state`, `backend.hermes.agent_loop.CheckpointManager`, `backend.hermes.memory.HermesMemory` |
| [`backend/seed.py`](/backend/seed.py) | `backend.config.DHAKA`, `backend.config.Settings`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.PortfolioState`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.price`, `backend.engine.money.purchase_amount`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.bucket_balances` |
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
| `StockNowAdapter` | `L32–L78` | `object` | Sprint 1's explicitly synthetic data/paper-fill boundary. | 6 |
| `StockNowBrowserSession` | `L81–L107` | `object` | Opt-in persistent browser foundation, not a login or order implementation. | 2 |


**Methods in `StockNowAdapter`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L35–L37` | `(self, mode: str='DEMO'...)` | — | — | `LiveIntegrationNotImplemented` |
| `quote` | `L39–L52` | `(self, company: CompanyProfile, as_o...)` | `DemoQuote` | — | `DemoQuote`, `QuoteError`, `decimal`, `is_finite` |
| `paper_fill` | `L54–L57` | `(self, quote: DemoQuote, quantity: i...)` | `Decimal` | — | `ValueError` |
| `read_virtual_portfolio` | `L59–L60` | `(self...)` | — | — | `LiveIntegrationNotImplemented` |
| `execute_order` | `L62–L63` | `(self, *_args, **_kwargs...)` | — | — | `LiveIntegrationNotImplemented` |
| `get_adapter_status` | `L65–L78` | `(self, ingestion_mode: str='BACKGROU...)` | `dict` | — | — |


**Methods in `StockNowBrowserSession`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L89–L90` | `(self, profile_directory: Path...)` | — | — | — |
| `open` | `L93–L107` | `(self...)` | — | — | `async_playwright`, `close`, `launch_persistent_context`, `mkdir` |


---

### 📄 [`backend/chat.py`](/backend/chat.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `ChatTurn` | `L46–L49` | `BaseModel` | — | 0 |
| `ChatRequest` | `L52–L64` | `BaseModel` | — | 1 |
| `ChatService` | `L181–L195` | `object` | — | 2 |


**Methods in `ChatRequest`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `nonempty` | `L60–L64` | `(cls, value: str...)` | `str` | — | `ValueError`, `field_validator`, `strip` |


**Methods in `ChatService`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L182–L187` | `(self, database: Database, settings:...)` | — | — | `HermesAgentLoop` |
| `respond` | `L189–L195` | `(self, request: ChatRequest...)` | `dict` | — | `model_dump`, `run_turn` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `match_symbol` | `L67–L82` | `(text: str, companies: list[dict]...)` | `dict | None` | — | `get`, `lower` |
| `format_canary_updates` | `L85–L100` | `(snapshot: dict...)` | `str` | — | `append`, `get`, `join` |
| `local_summary` | `L103–L178` | `(message: str, snapshot: dict...)` | `str` | — | `any`, `format_canary_updates`, `get`, `join` |


---

### 📄 [`backend/config.py`](/backend/config.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `Settings` | `L25–L116` | `object` | — | 2 |


**Methods in `Settings`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__post_init__` | `L52–L76` | `(self...)` | `None` | — | `Decimal`, `ValueError`, `any`, `is_finite` |
| `from_env` | `L79–L116` | `(cls...)` | `Settings` | — | `Decimal`, `cls`, `fromisoformat`, `frozenset` |


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
| `cycle_key` | `L282–L283` | `(state: PortfolioState...)` | `str` | — | — |


---

### 📄 [`backend/engine/auto_trader.py`](/backend/engine/auto_trader.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `AutomationPaused` | `L31–L32` | `ValueError` | — | 0 |
| `AutoTrader` | `L35–L291` | `object` | — | 5 |


**Methods in `AutoTrader`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L36–L40` | `(self, database: Database, settings:...)` | — | — | `StockNowAdapter`, `TradingCalendar` |
| `run_cycle` | `L42–L243` | `(self, request_id: str | None=None...)` | `dict` | — | `AutomationCycle`, `AutomationPaused`, `CycleRequestKey`, `SellState` |
| `record` | `L79–L87` | `(symbol: str, action: str, reason: s...)` | — | — | `DecisionLog`, `add`, `append` |
| `_trade_result` | `L246–L252` | `(trade: TradeLog, action: str...)` | `dict` | — | `float` |
| `advance_demo` | `L254–L291` | `(self, scenario: str...)` | `dict` | — | `Decimal`, `ValueError`, `add_sessions`, `assert_ledger` |


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
| `CheckpointManager` | `L62–L158` | `object` | — | 2 |
| `HermesAgentLoop` | `L161–L415` | `object` | — | 8 |


**Methods in `CheckpointManager`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `create_checkpoint` | `L64–L113` | `(session: Session, state: PortfolioS...)` | `HermesStateCheckpoint` | — | `HermesStateCheckpoint`, `add`, `flush`, `get` |
| `rollback_last` | `L116–L158` | `(session: Session, state: PortfolioS...)` | `dict[str, Any]` | — | `ValueError`, `append`, `decimal`, `desc` |


**Methods in `HermesAgentLoop`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L162–L166` | `(self, database: Database, settings:...)` | — | — | `SkillsManager` |
| `execute_tool` | `L168–L170` | `(self, tool_name: str, args: dict[st...)` | `dict[str, Any]` | Deterministic execution of Hermes Agent tools with automatic checkpointing and rule diff tracking. | `dispatch_tool` |
| `compress_history` | `L172–L184` | `(self, history: list[dict[str, str]]...)` | `list[dict[str, str]]` | Summarizes older conversation turns to keep context window compact & lightweight. | `append`, `capitalize`, `join`, `len` |
| `detect_intent_and_tool` | `L186–L188` | `(self, message: str, snapshot: dict...)` | `tuple[str | None, dict[str, Any]]` | High-precision intent detector for Bangla, Banglish & English agent commands. | `detect_intent_and_tool` |
| `run_turn` | `L190–L261` | `(self, user_message: str, history: l...)` | `dict[str, Any]` | Main turn loop: Layered Memory + Skills Injection + Tool Execution + Context Scrubbing. | `HermesMemory`, `_conversational_inference`, `_format_tool_response`, `build_snapshot` |
| `_format_tool_response` | `L263–L264` | `(self, tool_name: str, tool_res: dic...)` | `str` | — | `format_tool_response` |
| `_conversational_inference` | `L266–L397` | `(self, message: str, history: list[d...)` | `dict[str, Any]` | Runs conversational response with Layered Memory and Matched SKILL.md injection. | `AsyncClient`, `ChatBudget`, `HermesMemory`, `Timeout` |
| `_local_conversational_fallback` | `L399–L415` | `(self, message: str, snapshot: dict,...)` | `dict[str, Any]` | — | `HermesMemory`, `local_summary`, `portfolio_state`, `record_turn` |


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
| `handle_report_company_threat` | `L35–L63` | `(args: dict[str, Any], session: Sess...)` | `dict[str, Any]` | — | `HermesMemory`, `create_checkpoint`, `emergency_quarantine_and_canary`, `record_fact` |
| `handle_restore_quarantined_company` | `L66–L93` | `(args: dict[str, Any], session: Sess...)` | `dict[str, Any]` | — | `HermesMemory`, `create_checkpoint`, `get`, `record_fact` |
| `handle_set_watchlist_tier` | `L96–L131` | `(args: dict[str, Any], session: Sess...)` | `dict[str, Any]` | — | `HermesMemory`, `ValueError`, `create_checkpoint`, `flush` |
| `handle_update_company_allocation` | `L134–L170` | `(args: dict[str, Any], session: Sess...)` | `dict[str, Any]` | — | `RuleAudit`, `ValueError`, `add`, `bool` |
| `handle_execute_manual_order` | `L173–L198` | `(args: dict[str, Any], session: Sess...)` | `dict[str, Any]` | — | `ValueError`, `create_checkpoint`, `execute_agentic_buy`, `get` |
| `handle_learn_or_patch_skill` | `L201–L227` | `(args: dict[str, Any], session: Sess...)` | `dict[str, Any]` | — | `create_checkpoint`, `get`, `learn_or_patch_skill` |
| `handle_set_automation_config` | `L230–L276` | `(args: dict[str, Any], session: Sess...)` | `dict[str, Any]` | — | `ValueError`, `bool`, `create_checkpoint`, `flush` |
| `handle_set_ai_model` | `L279–L319` | `(args: dict[str, Any], session: Sess...)` | `dict[str, Any]` | — | `create_checkpoint`, `flush`, `get`, `getattr` |
| `handle_evaluate_canary_theses` | `L322–L338` | `(session: Session, state: PortfolioS...)` | `dict[str, Any]` | — | `check_canary_theses`, `isoformat`, `learn_or_patch_skill` |
| `dispatch_tool` | `L345–L377` | `(tool_name: str, args: dict[str, Any...)` | `dict[str, Any]` | Routes tool execution to dedicated handlers with low nesting depth (<= 3). | `ValueError`, `handle_evaluate_canary_theses`, `handle_execute_manual_order`, `handle_learn_or_patch_skill` |
| `_fmt_rollback` | `L384–L400` | `(res: dict[str, Any], bangla: bool...)` | `str` | — | `join` |
| `_fmt_report_threat` | `L403–L429` | `(res: dict[str, Any], bangla: bool...)` | `str` | — | — |
| `_fmt_watchlist_tier` | `L432–L443` | `(tool_res: dict[str, Any], bangla: b...)` | `str` | — | `get` |
| `_fmt_automation_config` | `L446–L468` | `(tool_res: dict[str, Any], bangla: b...)` | `str` | — | — |
| `_fmt_ai_model` | `L471–L501` | `(tool_res: dict[str, Any], bangla: b...)` | `str` | — | `get`, `join` |
| `format_tool_response` | `L504–L556` | `(tool_name: str, tool_res: dict[str,...)` | `str` | Formats human-friendly Bangla/English message summarizing the executed tool's outcome. | `_fmt_ai_model`, `_fmt_automation_config`, `_fmt_report_threat`, `_fmt_rollback` |
| `detect_intent_and_tool` | `L563–L700` | `(message: str, snapshot: dict...)` | `tuple[str | None, dict[str, Any]]` | High-precision intent detector for Bangla, Banglish & English agent commands. | `any`, `float`, `get`, `int` |


---

### 📄 [`backend/main.py`](/backend/main.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `PauseRequest` | `L38–L40` | `BaseModel` | — | 0 |
| `AutomationConfigRequest` | `L43–L47` | `BaseModel` | — | 0 |
| `AdvanceRequest` | `L50–L52` | `BaseModel` | — | 0 |
| `AllocationRequest` | `L55–L58` | `BaseModel` | — | 0 |
| `EventBroadcaster` | `L61–L78` | `object` | — | 4 |
| `DevStaticFiles` | `L273–L279` | `StaticFiles` | — | 1 |


**Methods in `EventBroadcaster`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L62–L63` | `(self...)` | — | — | `set` |
| `subscribe` | `L65–L68` | `(self...)` | `asyncio.Queue` | — | `Queue`, `add` |
| `unsubscribe` | `L70–L71` | `(self, queue: asyncio.Queue...)` | — | — | `discard` |
| `publish` | `L73–L78` | `(self, event_type: str, data: dict...)` | — | — | `list`, `put_nowait` |


**Methods in `DevStaticFiles`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `get_response` | `L274–L279` | `(self, path: str, scope...)` | — | — | `get_response`, `super` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `create_app` | `L81–L293` | `(settings: Settings | None=None...)` | `FastAPI` | — | `AutoTrader`, `ChatService`, `Database`, `DevStaticFiles` |
| `lifespan` | `L89–L96` | `(_app: FastAPI...)` | — | — | `create_schema`, `dispose`, `seed_demo`, `write` |
| `local_security` | `L110–L148` | `(request: Request, call_next...)` | — | — | `JSONResponse`, `call_next`, `compare_digest`, `encode` |
| `health` | `L151–L152` | `(...)` | — | — | `get` |
| `portfolio` | `L155–L156` | `(...)` | — | — | `build_snapshot`, `get` |
| `cycle` | `L159–L165` | `(idempotency_key: Annotated[UUID | N...)` | — | — | `HTTPException`, `Header`, `post`, `publish` |
| `pause` | `L168–L175` | `(body: PauseRequest...)` | — | — | `portfolio_state`, `post`, `publish`, `write` |
| `automation_config` | `L178–L196` | `(body: AutomationConfigRequest...)` | — | — | `StockNowAdapter`, `get_adapter_status`, `portfolio_state`, `post` |
| `advance` | `L199–L210` | `(body: AdvanceRequest...)` | — | — | `Decimal`, `advance_demo`, `build_market_map_payload`, `get` |
| `market_map_endpoint` | `L213–L214` | `(...)` | — | — | `build_market_map_payload`, `get` |
| `allocation` | `L217–L240` | `(symbol: str, body: AllocationReques...)` | — | — | `HTTPException`, `RuleAudit`, `add`, `get` |
| `event_stream` | `L246–L271` | `(request: Request...)` | — | — | `StreamingResponse`, `generator`, `get`, `subscribe` |
| `generator` | `L249–L261` | `(...)` | — | — | `dumps`, `get`, `is_disconnected`, `unsubscribe` |
| `cockpit` | `L282–L290` | `(...)` | — | — | `FileResponse`, `get` |


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
| `generate_extended_history` | `L114–L166` | `(history: list[dict[str, str]], fund...)` | `dict[str, list[dict[str, Any]]]` | Generates 7d, 1m, 6m, 1y series for TradingView-style deep trend views. | `add_sessions`, `append`, `cos`, `float` |
| `rule_view` | `L169–L179` | `(rule: CustomRule...)` | `dict` | — | `decimal`, `float` |
| `trade_view` | `L182–L201` | `(trade: TradeLog...)` | `dict` | — | `float`, `isoformat` |
| `period_totals` | `L204–L219` | `(trades: list[TradeLog], start: date...)` | `dict` | — | `float`, `isoformat`, `len`, `sum` |
| `build_snapshot` | `L222–L224` | `(database: Database, settings: Setti...)` | `dict` | — | `read`, `snapshot_from_session` |
| `snapshot_from_session` | `L227–L499` | `(session: Session, settings: Setting...)` | `dict` | — | `SkillsManager`, `StockNowAdapter`, `TradingCalendar`, `add_sessions` |
| `normalized_watchlist` | `L502–L521` | `(companies: list[dict]...)` | `list[dict]` | Equal-weight normalized PRICE index, explicitly not portfolio performance. | `any`, `append`, `decimal`, `float` |


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
| `build_auth_settings_router` | `L40–L166` | `(database: Database, settings: Setti...)` | `APIRouter` | — | `APIRouter` |
| `login` | `L44–L58` | `(body: LoginRequest...)` | — | — | `HTTPException`, `add`, `post`, `uuid4` |
| `logout` | `L61–L65` | `(request: Request...)` | — | — | `discard`, `get`, `post`, `replace` |
| `auth_session` | `L68–L80` | `(request: Request...)` | — | — | `bool`, `get`, `replace`, `strip` |
| `get_api_keys` | `L83–L115` | `(...)` | — | — | `bool`, `date`, `get`, `getattr` |
| `mask` | `L84–L89` | `(s: str...)` | `str` | — | `len` |
| `update_api_keys` | `L118–L164` | `(body: KeysSettingsRequest...)` | — | — | `__setattr__`, `append`, `create_checkpoint`, `join` |


---

### 📄 [`backend/routes_hermes.py`](/backend/routes_hermes.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `CreateThreadRequest` | `L21–L23` | `BaseModel` | — | 0 |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `build_hermes_router` | `L26–L199` | `(database: Database, settings: Setti...)` | `APIRouter` | — | `APIRouter` |
| `chat_route` | `L30–L34` | `(body: ChatRequest...)` | — | — | `get`, `post`, `publish`, `respond` |
| `list_conversations` | `L37–L41` | `(...)` | — | — | `HermesMemory`, `get`, `list_threads`, `read` |
| `create_conversation` | `L44–L55` | `(body: CreateThreadRequest...)` | — | — | `HermesMemory`, `get_or_create_thread`, `post`, `write` |
| `conversation_messages` | `L58–L62` | `(conversation_id: str...)` | — | — | `HermesMemory`, `get`, `get_thread_messages`, `read` |
| `system_changes` | `L65–L127` | `(...)` | — | — | `Path`, `append`, `desc`, `get` |
| `hermes_models` | `L130–L152` | `(...)` | — | — | `get`, `getattr`, `getenv`, `portfolio_state` |
| `set_hermes_model` | `L155–L188` | `(payload: dict...)` | — | — | `HTTPException`, `create_checkpoint`, `get`, `getattr` |
| `rollback_checkpoint` | `L191–L197` | `(...)` | — | — | `portfolio_state`, `post`, `publish`, `rollback_last` |


---

### 📄 [`backend/seed.py`](/backend/seed.py)

#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `seed_demo` | `L26–L112` | `(session: Session, settings: Setting...)` | `None` | — | `CompanyProfile`, `CustomRule`, `Decimal`, `PortfolioState` |


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
| `parse_fastapi_routes` | `L168–L192` | `(main_path: Path...)` | — | — | `append`, `exists`, `get_docstring`, `isinstance` |
| `parse_frontend` | `L195–L220` | `(...)` | — | — | `add`, `append`, `enumerate`, `exists` |
| `generate_markdown` | `L223–L383` | `(...)` | — | — | `append`, `collect_file_metrics`, `get`, `items` |


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

## 5. FastAPI Route Registry (`backend/main.py`)

| Method | Route Path | Handler Function | Line | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | `health` | `L151` | Route endpoint |
| `GET` | `/api/portfolio` | `portfolio` | `L155` | Route endpoint |
| `POST` | `/api/automation/cycle` | `cycle` | `L159` | Route endpoint |
| `POST` | `/api/automation/pause` | `pause` | `L168` | Route endpoint |
| `POST` | `/api/automation/config` | `automation_config` | `L178` | Route endpoint |
| `POST` | `/api/demo/advance` | `advance` | `L199` | Route endpoint |
| `GET` | `/api/market/map` | `market_map_endpoint` | `L213` | Route endpoint |
| `PATCH` | `/api/companies/{symbol}/allocation` | `allocation` | `L217` | Route endpoint |
| `GET` | `/api/stream` | `event_stream` | `L246` | Route endpoint |
| `GET` | `/` | `cockpit` | `L282` | Route endpoint |

---

## 6. Frontend DOM & JS Controller X-Ray

### Key DOM Identifiers (`frontend/index.html`)

Identified **229** distinct element IDs in the UI shell. Key controller anchors:

`#overview`, `#watchlist`, `#market-map`, `#master-automation-toggle`, `#mode-btn-polling`, `#mode-btn-live`, `#polling-interval-pills`, `#main-chart`, `#bucket-stack`, `#what-if-slider`, `#theme-toggle-btn`, `#topbar-clock-widget`


### Frontend Stylesheets (`frontend/*.css`)

| Stylesheet File | Lines | Purpose |
| :--- | :--- | :--- |
| `styles.css` | 4362 | Core design tokens, layout & widgets |
| `theme_light_hermes.css` | 2343 | Daylight overrides & Hermes IDE sidebar |


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
| `badge()` | `app.js` | `L95` | Reactive DOM rendering / event controller |
| `notify()` | `app.js` | `L102` | Reactive DOM rendering / event controller |
| `showError()` | `app.js` | `L112` | Reactive DOM rendering / event controller |
| `api()` | `app.js` | `L119` | Reactive DOM rendering / event controller |
| `updateControls()` | `app.js` | `L144` | Reactive DOM rendering / event controller |
| `refresh()` | `app.js` | `L168` | Reactive DOM rendering / event controller |
| `mutate()` | `app.js` | `L181` | Reactive DOM rendering / event controller |
| `renderSnapshot()` | `app.js` | `L190` | Reactive DOM rendering / event controller |
| `renderBuckets()` | `app.js` | `L225` | Reactive DOM rendering / event controller |
| `cell()` | `app.js` | `L244` | Reactive DOM rendering / event controller |
| `selectCompany()` | `app.js` | `L246` | Reactive DOM rendering / event controller |
| `renderWatchlist()` | `app.js` | `L253` | Reactive DOM rendering / event controller |
| `renderCanaryTheses()` | `app.js` | `L309` | Reactive DOM rendering / event controller |
| `renderInspector()` | `app.js` | `L343` | Reactive DOM rendering / event controller |
| `renderDecisions()` | `app.js` | `L378` | Reactive DOM rendering / event controller |
| `renderLedger()` | `app.js` | `L395` | Reactive DOM rendering / event controller |
| `initTheme()` | `app.js` | `L521` | Reactive DOM rendering / event controller |
| `setTheme()` | `app.js` | `L527` | Reactive DOM rendering / event controller |
| `toggleTheme()` | `app.js` | `L538` | Reactive DOM rendering / event controller |
| `tickMarketClock()` | `app.js` | `L544` | Reactive DOM rendering / event controller |
| `tickClock()` | `app.js` | `L609` | Reactive DOM rendering / event controller |
| `renderAutomationControlBar()` | `app.js` | `L618` | Reactive DOM rendering / event controller |
| `setAutomationConfig()` | `app.js` | `L744` | Reactive DOM rendering / event controller |
| `initRealtimeStream()` | `app.js` | `L858` | Reactive DOM rendering / event controller |
| `switchView()` | `app.js` | `L884` | Reactive DOM rendering / event controller |
| `initViewRouter()` | `app.js` | `L935` | Reactive DOM rendering / event controller |
| `initScrollSpy()` | `app.js` | `L1001` | Reactive DOM rendering / event controller |
| `updateActiveNav()` | `app.js` | `L1014` | Reactive DOM rendering / event controller |
| `smoothCurvePath()` | `charts.js` | `L8` | Reactive DOM rendering / event controller |
| `renderMainChart()` | `charts.js` | `L31` | Reactive DOM rendering / event controller |
| `sparkline()` | `charts.js` | `L153` | Reactive DOM rendering / event controller |
| `squarify()` | `charts.js` | `L168` | Reactive DOM rendering / event controller |
| `layoutRow()` | `charts.js` | `L178` | Reactive DOM rendering / event controller |
| `worst()` | `charts.js` | `L225` | Reactive DOM rendering / event controller |
| `showTreemapTooltip()` | `charts.js` | `L262` | Reactive DOM rendering / event controller |
| `hideTreemapTooltip()` | `charts.js` | `L275` | Reactive DOM rendering / event controller |
| `renderMarketMap()` | `charts.js` | `L280` | Reactive DOM rendering / event controller |
| `renderTopSectorsChart()` | `charts.js` | `L451` | Reactive DOM rendering / event controller |
| `renderGainerChart()` | `charts.js` | `L611` | Reactive DOM rendering / event controller |
| `updateWhatIfSimulator()` | `charts.js` | `L616` | Reactive DOM rendering / event controller |
| `updateModalSimulator()` | `charts.js` | `L660` | Reactive DOM rendering / event controller |
| `openDeepTrendModal()` | `charts.js` | `L699` | Reactive DOM rendering / event controller |
| `closeDeepTrendModal()` | `charts.js` | `L756` | Reactive DOM rendering / event controller |
| `renderDeepTrendChart()` | `charts.js` | `L766` | Reactive DOM rendering / event controller |
| `initCharts()` | `charts.js` | `L1005` | Reactive DOM rendering / event controller |
| `renderHermesSkills()` | `hermes_ui.js` | `L8` | Reactive DOM rendering / event controller |
| `addMessage()` | `hermes_ui.js` | `L52` | Reactive DOM rendering / event controller |
| `sendChat()` | `hermes_ui.js` | `L65` | Reactive DOM rendering / event controller |
| `initHermesSidebar()` | `hermes_ui.js` | `L109` | Reactive DOM rendering / event controller |
| `loadConversations()` | `hermes_ui.js` | `L253` | Reactive DOM rendering / event controller |
| `switchConversation()` | `hermes_ui.js` | `L287` | Reactive DOM rendering / event controller |
| `createNewConversation()` | `hermes_ui.js` | `L316` | Reactive DOM rendering / event controller |
| `formatRelativeTime()` | `hermes_ui.js` | `L343` | Reactive DOM rendering / event controller |
| `escapeHtml()` | `hermes_ui.js` | `L357` | Reactive DOM rendering / event controller |
| `executeRollback()` | `hermes_ui.js` | `L367` | Reactive DOM rendering / event controller |
| `loadHermesModels()` | `hermes_ui.js` | `L390` | Reactive DOM rendering / event controller |
| `switchHermesModel()` | `hermes_ui.js` | `L445` | Reactive DOM rendering / event controller |
| `loadApiKeysSettings()` | `hermes_ui.js` | `L467` | Reactive DOM rendering / event controller |
| `saveApiKeysSettings()` | `hermes_ui.js` | `L517` | Reactive DOM rendering / event controller |
| `checkAuthSession()` | `hermes_ui.js` | `L557` | Reactive DOM rendering / event controller |
| `openOperatorProfile()` | `hermes_ui.js` | `L575` | Reactive DOM rendering / event controller |
| `closeOperatorProfile()` | `hermes_ui.js` | `L580` | Reactive DOM rendering / event controller |
| `handleOperatorLogin()` | `hermes_ui.js` | `L585` | Reactive DOM rendering / event controller |
| `handleOperatorLogout()` | `hermes_ui.js` | `L614` | Reactive DOM rendering / event controller |
| `initAuthAndSettings()` | `hermes_ui.js` | `L624` | Reactive DOM rendering / event controller |
| `loadSystemChanges()` | `hermes_ui.js` | `L692` | Reactive DOM rendering / event controller |
| `initHermesChatListeners()` | `hermes_ui.js` | `L780` | Reactive DOM rendering / event controller |

---

## 7. Code Health & Complexity Radar

Functions requiring architectural attention (> 70 lines or nesting depth >= 4):


| File | Function / Method | Length (Lines) | Max Nesting Depth | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| `backend/chat.py` | `match_symbol` | 16 | 4 | Acceptable; well-scoped logic |
| `backend/chat.py` | `format_canary_updates` | 16 | 4 | Acceptable; well-scoped logic |
| `backend/chat.py` | `local_summary` | 76 | 2 | Acceptable; well-scoped logic |
| `backend/database.py` | `create_schema` | 36 | 4 | Acceptable; well-scoped logic |
| `backend/engine/agent_actions.py` | `emergency_quarantine_and_canary` | 106 | 5 | Decompose into sub-functions |
| `backend/engine/agent_actions.py` | `check_canary_theses` | 31 | 4 | Acceptable; well-scoped logic |
| `backend/engine/agent_actions.py` | `execute_agentic_buy` | 83 | 3 | Acceptable; well-scoped logic |
| `backend/engine/auto_trader.py` | `run_cycle` | 202 | 5 | Decompose into sub-functions |
| `backend/engine/auto_trader.py` | `advance_demo` | 38 | 5 | Acceptable; well-scoped logic |
| `backend/engine/curve_analyzer.py` | `analyze_curve` | 82 | 3 | Acceptable; well-scoped logic |
| `backend/engine/sequential_seller.py` | `plan_sale` | 105 | 3 | Decompose into sub-functions |
| `backend/engine/t2_ledger.py` | `bucket_balances` | 31 | 4 | Acceptable; well-scoped logic |
| `backend/hermes/agent_loop.py` | `run_turn` | 72 | 4 | Acceptable; well-scoped logic |
| `backend/hermes/agent_loop.py` | `_conversational_inference` | 132 | 4 | Decompose into sub-functions |
| `backend/hermes/memory.py` | `record_turn` | 29 | 4 | Acceptable; well-scoped logic |
| `backend/hermes/memory.py` | `search_sessions` | 28 | 4 | Acceptable; well-scoped logic |
| `backend/hermes/memory.py` | `format_layer_3_prompt` | 17 | 5 | Acceptable; well-scoped logic |
| `backend/hermes/secret_guard.py` | `redact_secrets` | 11 | 4 | Acceptable; well-scoped logic |
| `backend/hermes/skills_manager.py` | `match_skills` | 22 | 4 | Acceptable; well-scoped logic |
| `backend/hermes/tools_dispatcher.py` | `dispatch_tool` | 33 | 11 | Acceptable; well-scoped logic |
| `backend/hermes/tools_dispatcher.py` | `detect_intent_and_tool` | 138 | 5 | Decompose into sub-functions |
| `backend/main.py` | `create_app` | 213 | 4 | Decompose into sub-functions |
| `backend/main.py` | `local_security` | 39 | 4 | Acceptable; well-scoped logic |
| `backend/main.py` | `event_stream` | 26 | 4 | Acceptable; well-scoped logic |
| `backend/main.py` | `generator` | 13 | 4 | Acceptable; well-scoped logic |
| `backend/market_map.py` | `build_market_map_payload` | 72 | 5 | Acceptable; well-scoped logic |
| `backend/portfolio.py` | `snapshot_from_session` | 273 | 3 | Decompose into sub-functions |
| `backend/portfolio.py` | `normalized_watchlist` | 20 | 4 | Acceptable; well-scoped logic |
| `backend/routes_auth_settings.py` | `build_auth_settings_router` | 127 | 2 | Decompose into sub-functions |
| `backend/routes_hermes.py` | `build_hermes_router` | 174 | 5 | Decompose into sub-functions |
| `backend/routes_hermes.py` | `system_changes` | 63 | 5 | Acceptable; well-scoped logic |
| `backend/seed.py` | `seed_demo` | 87 | 3 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `is_ignored` | 6 | 4 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `collect_file_metrics` | 15 | 4 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `parse_fastapi_routes` | 25 | 7 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `parse_frontend` | 26 | 4 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `generate_markdown` | 161 | 6 | Decompose into sub-functions |
| `scripts/generate_code_map.py` | `visit_Call` | 10 | 4 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `_compute_depth` | 12 | 4 | Acceptable; well-scoped logic |


> **Audit Summary:** 27 Python modules inspected, 10 FastAPI endpoints registered, 18,245 total LOC indexed.