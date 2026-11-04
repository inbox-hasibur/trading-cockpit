# 🗺️ Codebase AST Map & System Architecture Radar

> Auto-generated via `scripts/generate_code_map.py` (Zero-dependency stdlib AST inspection) on **2026-11-04 14:16:22 UTC**.

---

## 1. Repository Topology & File Metrics

| Extension / Type | File Count | Total Lines of Code | Description |
| :--- | :--- | :--- | :--- |
| `.py` | 28 | 4,992 | Python Core Kernel, Engine & Hermes Agent |
| `.js` | 1 | 1,869 | Vanilla ES6+ Reactive Terminal Controller |
| `.css` | 1 | 1,538 | Custom Dark / Light / Terminal Design System |
| `.md` | 9 | 1,357 | Architecture & Strategy Documentation |
| `.html` | 1 | 398 | Single Page Application DOM Structure |
| `.agentignore` | 1 | 12 | Configuration / Asset |
| `.cursorignore` | 1 | 12 | Configuration / Asset |
| `.opencodeignore` | 1 | 12 | Configuration / Asset |
| `.txt` | 2 | 11 | Dependency Specifications |
| `.toml` | 1 | 10 | PyProject Configuration |
| `.svg` | 1 | 1 | Configuration / Asset |
| **TOTAL** | **47** | **10,212** | *Entire Humming Bird Repository* |

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
| [`backend/hermes/agent_loop.py`](/backend/hermes/agent_loop.py) | `backend.chat.local_summary`, `backend.config.DHAKA`, `backend.config.Settings`, `backend.database.CanaryThesis`, `backend.database.ChatBudget`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.HermesSkillRevision`, `backend.database.HermesStateCheckpoint`, `backend.database.PortfolioState`, `backend.database.RuleAudit`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.database.portfolio_state`, `backend.engine.agent_actions.check_canary_theses`, `backend.engine.agent_actions.emergency_quarantine_and_canary`, `backend.engine.agent_actions.execute_agentic_buy`, `backend.engine.agent_actions.restore_quarantine`, `backend.engine.money.ZERO`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.price`, `backend.engine.money.purchase_amount`, `backend.engine.money.sale_amount`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.assert_ledger`, `backend.engine.t2_ledger.bucket_balances`, `backend.hermes.memory.HermesMemory`, `backend.hermes.secret_guard.SecretGuard`, `backend.hermes.secret_guard.redact_secrets`, `backend.hermes.skills_manager.SkillsManager`, `backend.portfolio.build_snapshot` |
| [`backend/hermes/memory.py`](/backend/hermes/memory.py) | `backend.database.CanaryThesis`, `backend.database.CompanyProfile`, `backend.database.HermesDurableFact`, `backend.database.HermesSessionMemory`, `backend.database.HermesUserProfile`, `backend.hermes.secret_guard.redact_secrets` |
| [`backend/hermes/secret_guard.py`](/backend/hermes/secret_guard.py) | *Independent Core Module* |
| [`backend/hermes/skills_manager.py`](/backend/hermes/skills_manager.py) | `backend.database.HermesSkillRevision`, `backend.hermes.secret_guard.SecretGuard` |
| [`backend/main.py`](/backend/main.py) | `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.chat.ChatRequest`, `backend.chat.ChatService`, `backend.config.ROOT`, `backend.config.Settings`, `backend.config.VERSION`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.RuleAudit`, `backend.database.portfolio_state`, `backend.engine.auto_trader.AutoTrader`, `backend.engine.auto_trader.AutomationPaused`, `backend.engine.money.ZERO`, `backend.hermes.agent_loop.CheckpointManager`, `backend.market_map.build_market_map_payload`, `backend.portfolio.build_snapshot`, `backend.portfolio.rule_view`, `backend.seed.seed_demo` |
| [`backend/market_map.py`](/backend/market_map.py) | *Independent Core Module* |
| [`backend/portfolio.py`](/backend/portfolio.py) | `backend.adapters.stocknow_adapter.StockNowAdapter`, `backend.config.DHAKA`, `backend.config.Settings`, `backend.config.VERSION`, `backend.database.AutomationCycle`, `backend.database.CanaryThesis`, `backend.database.ChatBudget`, `backend.database.CompanyProfile`, `backend.database.CustomRule`, `backend.database.Database`, `backend.database.DecisionLog`, `backend.database.HermesDurableFact`, `backend.database.HermesSkillRevision`, `backend.database.HermesStateCheckpoint`, `backend.database.HermesUserProfile`, `backend.database.RuleAudit`, `backend.database.TaxLot`, `backend.database.TradeLog`, `backend.database.portfolio_state`, `backend.engine.money.HUNDRED`, `backend.engine.money.ZERO`, `backend.engine.money.decimal`, `backend.engine.money.money`, `backend.engine.money.sale_amount`, `backend.engine.signals.assess_company`, `backend.engine.t2_ledger.TradingCalendar`, `backend.engine.t2_ledger.bucket_balances`, `backend.hermes.skills_manager.SkillsManager`, `backend.market_map.build_market_map_payload` |
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
| `ChatRequest` | `L52–L63` | `BaseModel` | — | 1 |
| `ChatService` | `L180–L193` | `object` | — | 2 |


**Methods in `ChatRequest`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `nonempty` | `L59–L63` | `(cls, value: str...)` | `str` | — | `ValueError`, `field_validator`, `strip` |


**Methods in `ChatService`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L181–L186` | `(self, database: Database, settings:...)` | — | — | `HermesAgentLoop` |
| `respond` | `L188–L193` | `(self, request: ChatRequest...)` | `dict` | — | `model_dump`, `run_turn` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `match_symbol` | `L66–L81` | `(text: str, companies: list[dict]...)` | `dict | None` | — | `get`, `lower` |
| `format_canary_updates` | `L84–L99` | `(snapshot: dict...)` | `str` | — | `append`, `get`, `join` |
| `local_summary` | `L102–L177` | `(message: str, snapshot: dict...)` | `str` | — | `any`, `format_canary_updates`, `get`, `join` |


---

### 📄 [`backend/config.py`](/backend/config.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `Settings` | `L25–L102` | `object` | — | 2 |


**Methods in `Settings`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__post_init__` | `L45–L69` | `(self...)` | `None` | — | `Decimal`, `ValueError`, `any`, `is_finite` |
| `from_env` | `L72–L102` | `(cls...)` | `Settings` | — | `Decimal`, `cls`, `fromisoformat`, `frozenset` |


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
| `PortfolioState` | `L41–L56` | `Base` | — | 0 |
| `CompanyProfile` | `L59–L72` | `Base` | — | 0 |
| `CustomRule` | `L75–L86` | `Base` | — | 0 |
| `TaxLot` | `L89–L114` | `Base` | — | 0 |
| `AutomationCycle` | `L117–L126` | `Base` | — | 0 |
| `TradeLog` | `L129–L154` | `Base` | — | 0 |
| `CanaryThesis` | `L157–L169` | `Base` | — | 0 |
| `HermesSkillRevision` | `L172–L180` | `Base` | — | 0 |
| `HermesUserProfile` | `L183–L194` | `Base` | — | 0 |
| `HermesSessionMemory` | `L197–L205` | `Base` | — | 0 |
| `HermesDurableFact` | `L208–L216` | `Base` | — | 0 |
| `HermesStateCheckpoint` | `L219–L227` | `Base` | — | 0 |
| `CycleRequestKey` | `L230–L233` | `Base` | — | 0 |
| `DecisionLog` | `L236–L245` | `Base` | — | 0 |
| `RuleAudit` | `L248–L255` | `Base` | — | 0 |
| `ChatBudget` | `L258–L261` | `Base` | — | 0 |
| `Database` | `L264–L326` | `object` | — | 5 |


**Methods in `Database`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L265–L285` | `(self, url: str...)` | — | — | `Path`, `RLock`, `ValueError`, `create_engine` |
| `configure_sqlite` | `L278–L283` | `(connection: Any, _record: Any...)` | `None` | — | `close`, `cursor`, `execute`, `listens_for` |
| `create_schema` | `L287–L305` | `(self...)` | `None` | — | `commit`, `connect`, `create_all`, `execute` |
| `read` | `L308–L315` | `(self...)` | — | — | `execute`, `rollback`, `sessions`, `text` |
| `write` | `L318–L326` | `(self...)` | — | — | `commit`, `execute`, `rollback`, `sessions` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `portfolio_state` | `L329–L333` | `(session: Session...)` | `PortfolioState` | — | `RuntimeError`, `get` |


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
| `CheckpointManager` | `L67–L153` | `object` | — | 2 |
| `HermesAgentLoop` | `L156–L724` | `object` | — | 8 |


**Methods in `CheckpointManager`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `create_checkpoint` | `L69–L108` | `(session: Session, state: PortfolioS...)` | `HermesStateCheckpoint` | — | `HermesStateCheckpoint`, `add`, `flush`, `get` |
| `rollback_last` | `L111–L153` | `(session: Session, state: PortfolioS...)` | `dict[str, Any]` | — | `ValueError`, `append`, `decimal`, `desc` |


**Methods in `HermesAgentLoop`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L157–L161` | `(self, database: Database, settings:...)` | — | — | `SkillsManager` |
| `execute_tool` | `L163–L283` | `(self, tool_name: str, args: dict[st...)` | `dict[str, Any]` | Deterministic execution of Hermes Agent tools with automatic checkpointing. | `HermesMemory`, `RuleAudit`, `TradingCalendar`, `ValueError` |
| `compress_history` | `L285–L297` | `(self, history: list[dict[str, str]]...)` | `list[dict[str, str]]` | Summarizes older conversation turns to keep context window compact & lightweight. | `append`, `capitalize`, `join`, `len` |
| `detect_intent_and_tool` | `L299–L430` | `(self, message: str, snapshot: dict...)` | `tuple[str | None, dict[str, Any]]` | High-precision intent detector for Bangla, Banglish & English agent commands. | `any`, `float`, `get`, `int` |
| `run_turn` | `L432–L496` | `(self, user_message: str, history: l...)` | `dict[str, Any]` | Main turn loop: Layered Memory + Skills Injection + Tool Execution + Context Scrubbing. | `HermesMemory`, `_conversational_inference`, `_format_tool_response`, `build_snapshot` |
| `_format_tool_response` | `L498–L612` | `(self, tool_name: str, tool_res: dic...)` | `str` | — | `any`, `get`, `join`, `lower` |
| `_conversational_inference` | `L614–L707` | `(self, message: str, history: list[d...)` | `dict[str, Any]` | Runs conversational response with Layered Memory and Matched SKILL.md injection. | `AsyncClient`, `ChatBudget`, `HermesMemory`, `Timeout` |
| `_local_conversational_fallback` | `L709–L724` | `(self, message: str, snapshot: dict,...)` | `dict[str, Any]` | — | `HermesMemory`, `local_summary`, `portfolio_state`, `record_turn` |


---

### 📄 [`backend/hermes/memory.py`](/backend/hermes/memory.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `HermesMemory` | `L26–L184` | `object` | — | 8 |


**Methods in `HermesMemory`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L27–L28` | `(self, session: Session...)` | — | — | — |
| `get_user_profile` | `L33–L56` | `(self...)` | `dict[str, Any]` | — | `HermesUserProfile`, `add`, `flush`, `get` |
| `format_layer_1_prompt` | `L58–L67` | `(self...)` | `str` | — | `get_user_profile`, `join` |
| `record_turn` | `L72–L89` | `(self, session_date: date, role: str...)` | `None` | — | `HermesSessionMemory`, `add`, `flush`, `redact_secrets` |
| `search_sessions` | `L91–L118` | `(self, query: str, limit: int=4...)` | `list[dict[str, Any]]` | — | `any`, `append`, `desc`, `isoformat` |
| `record_fact` | `L123–L140` | `(self, symbol: str, fact: str, categ...)` | `HermesDurableFact` | — | `HermesDurableFact`, `add`, `flush`, `redact_secrets` |
| `recall_facts_for_symbol` | `L142–L166` | `(self, symbol: str...)` | `list[dict[str, Any]]` | — | `append`, `desc`, `float`, `limit` |
| `format_layer_3_prompt` | `L168–L184` | `(self, symbols: list[str]...)` | `str` | — | `append`, `join`, `recall_facts_for_symbol` |


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

### 📄 [`backend/main.py`](/backend/main.py)

#### Classes & Methods

| Class | Line Range | Inherits | Docstring / Purpose | Methods Count |
| :--- | :--- | :--- | :--- | :--- |
| `PauseRequest` | `L31–L33` | `BaseModel` | — | 0 |
| `AutomationConfigRequest` | `L36–L40` | `BaseModel` | — | 0 |
| `AdvanceRequest` | `L43–L45` | `BaseModel` | — | 0 |
| `AllocationRequest` | `L48–L51` | `BaseModel` | — | 0 |
| `EventBroadcaster` | `L54–L71` | `object` | — | 4 |


**Methods in `EventBroadcaster`:**

| Method | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `__init__` | `L55–L56` | `(self...)` | — | — | `set` |
| `subscribe` | `L58–L61` | `(self...)` | `asyncio.Queue` | — | `Queue`, `add` |
| `unsubscribe` | `L63–L64` | `(self, queue: asyncio.Queue...)` | — | — | `discard` |
| `publish` | `L66–L71` | `(self, event_type: str, data: dict...)` | — | — | `list`, `put_nowait` |


#### Standalone Functions

| Function | Line Range | Signature | Return Type | Docstring | Internal Calls |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `create_app` | `L74–L284` | `(settings: Settings | None=None...)` | `FastAPI` | — | `AutoTrader`, `ChatService`, `Database`, `EventBroadcaster` |
| `lifespan` | `L82–L89` | `(_app: FastAPI...)` | — | — | `create_schema`, `dispose`, `seed_demo`, `write` |
| `local_security` | `L103–L141` | `(request: Request, call_next...)` | — | — | `JSONResponse`, `call_next`, `compare_digest`, `encode` |
| `health` | `L144–L145` | `(...)` | — | — | `get` |
| `portfolio` | `L148–L149` | `(...)` | — | — | `build_snapshot`, `get` |
| `cycle` | `L152–L158` | `(idempotency_key: Annotated[UUID | N...)` | — | — | `HTTPException`, `Header`, `post`, `publish` |
| `pause` | `L161–L168` | `(body: PauseRequest...)` | — | — | `portfolio_state`, `post`, `publish`, `write` |
| `automation_config` | `L171–L189` | `(body: AutomationConfigRequest...)` | — | — | `StockNowAdapter`, `get_adapter_status`, `portfolio_state`, `post` |
| `advance` | `L192–L203` | `(body: AdvanceRequest...)` | — | — | `Decimal`, `advance_demo`, `build_market_map_payload`, `get` |
| `market_map_endpoint` | `L206–L207` | `(...)` | — | — | `build_market_map_payload`, `get` |
| `allocation` | `L210–L233` | `(symbol: str, body: AllocationReques...)` | — | — | `HTTPException`, `RuleAudit`, `add`, `get` |
| `chat_route` | `L236–L240` | `(body: ChatRequest...)` | — | — | `get`, `post`, `publish`, `respond` |
| `rollback_checkpoint` | `L243–L249` | `(...)` | — | — | `portfolio_state`, `post`, `publish`, `rollback_last` |
| `event_stream` | `L252–L277` | `(request: Request...)` | — | — | `StreamingResponse`, `generator`, `get`, `subscribe` |
| `generator` | `L255–L267` | `(...)` | — | — | `dumps`, `get`, `is_disconnected`, `unsubscribe` |
| `cockpit` | `L280–L281` | `(...)` | — | — | `FileResponse`, `get` |


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
| `generate_extended_history` | `L113–L154` | `(history: list[dict[str, str]], fund...)` | `dict[str, list[dict[str, Any]]]` | Generates 7d, 1m, 6m, 1y series for TradingView-style deep trend views. | `add_sessions`, `append`, `cos`, `float` |
| `rule_view` | `L157–L167` | `(rule: CustomRule...)` | `dict` | — | `decimal`, `float` |
| `trade_view` | `L170–L189` | `(trade: TradeLog...)` | `dict` | — | `float`, `isoformat` |
| `period_totals` | `L192–L207` | `(trades: list[TradeLog], start: date...)` | `dict` | — | `float`, `isoformat`, `len`, `sum` |
| `build_snapshot` | `L210–L212` | `(database: Database, settings: Setti...)` | `dict` | — | `read`, `snapshot_from_session` |
| `snapshot_from_session` | `L215–L473` | `(session: Session, settings: Setting...)` | `dict` | — | `SkillsManager`, `StockNowAdapter`, `TradingCalendar`, `append` |
| `normalized_watchlist` | `L476–L495` | `(companies: list[dict]...)` | `list[dict]` | Equal-weight normalized PRICE index, explicitly not portfolio performance. | `any`, `append`, `decimal`, `float` |


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
| `parse_frontend` | `L195–L213` | `(...)` | — | — | `append`, `enumerate`, `exists`, `findall` |
| `generate_markdown` | `L216–L368` | `(...)` | — | — | `append`, `collect_file_metrics`, `get`, `items` |


---

## 4. Database Schema X-Ray (`backend/database.py`)

SQLAlchemy ORM Entities backing the deterministic ledger and Hermes state store:

| Model Entity | Line Range | Base | Purpose & Managed Ledger State |
| :--- | :--- | :--- | :--- |
| `PortfolioState` | `L41–L56` | `Base` | Durable transactional entity |
| `CompanyProfile` | `L59–L72` | `Base` | Durable transactional entity |
| `CustomRule` | `L75–L86` | `Base` | Durable transactional entity |
| `TaxLot` | `L89–L114` | `Base` | Durable transactional entity |
| `AutomationCycle` | `L117–L126` | `Base` | Durable transactional entity |
| `TradeLog` | `L129–L154` | `Base` | Durable transactional entity |
| `CanaryThesis` | `L157–L169` | `Base` | Durable transactional entity |
| `HermesSkillRevision` | `L172–L180` | `Base` | Durable transactional entity |
| `HermesUserProfile` | `L183–L194` | `Base` | Durable transactional entity |
| `HermesSessionMemory` | `L197–L205` | `Base` | Durable transactional entity |
| `HermesDurableFact` | `L208–L216` | `Base` | Durable transactional entity |
| `HermesStateCheckpoint` | `L219–L227` | `Base` | Durable transactional entity |
| `CycleRequestKey` | `L230–L233` | `Base` | Durable transactional entity |
| `DecisionLog` | `L236–L245` | `Base` | Durable transactional entity |
| `RuleAudit` | `L248–L255` | `Base` | Durable transactional entity |
| `ChatBudget` | `L258–L261` | `Base` | Durable transactional entity |

---

## 5. FastAPI Route Registry (`backend/main.py`)

| Method | Route Path | Handler Function | Line | Description |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | `health` | `L144` | Route endpoint |
| `GET` | `/api/portfolio` | `portfolio` | `L148` | Route endpoint |
| `POST` | `/api/automation/cycle` | `cycle` | `L152` | Route endpoint |
| `POST` | `/api/automation/pause` | `pause` | `L161` | Route endpoint |
| `POST` | `/api/automation/config` | `automation_config` | `L171` | Route endpoint |
| `POST` | `/api/demo/advance` | `advance` | `L192` | Route endpoint |
| `GET` | `/api/market/map` | `market_map_endpoint` | `L206` | Route endpoint |
| `PATCH` | `/api/companies/{symbol}/allocation` | `allocation` | `L210` | Route endpoint |
| `POST` | `/api/chat` | `chat_route` | `L236` | Route endpoint |
| `POST` | `/api/hermes/rollback` | `rollback_checkpoint` | `L243` | Route endpoint |
| `GET` | `/api/stream` | `event_stream` | `L252` | Route endpoint |
| `GET` | `/` | `cockpit` | `L280` | Route endpoint |

---

## 6. Frontend DOM & JS Controller X-Ray

### Key DOM Identifiers (`frontend/index.html`)

Identified **152** distinct element IDs in the UI shell. Key controller anchors:

`#overview`, `#watchlist`, `#market-map`, `#automation-control-bar`, `#master-automation-toggle`, `#mode-btn-polling`, `#mode-btn-live`, `#polling-interval-pills`, `#adapter-status-badge`, `#main-chart`, `#bucket-stack`, `#what-if-slider`, `#theme-toggle-btn`, `#topbar-clock-widget`


### Frontend API Contract Invocations (`frontend/app.js`)

| Endpoint Invocated | Direction | Purpose |
| :--- | :--- | :--- |
| `/api/automation/config` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/automation/cycle` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/automation/pause` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/chat` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/demo/advance` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/hermes/rollback` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |
| `/api/portfolio` | Cockpit UI -> Kernel | Synchronous state mutation or telemetry poll |


### Core JavaScript Controllers (`frontend/app.js`)

| Function | Line in `app.js` | Role |
| :--- | :--- | :--- |
| `element()` | `L39` | Reactive DOM rendering / event controller |
| `svgElement()` | `L46` | Reactive DOM rendering / event controller |
| `currency()` | `L52` | Reactive DOM rendering / event controller |
| `percentage()` | `L59` | Reactive DOM rendering / event controller |
| `sessionDate()` | `L64` | Reactive DOM rendering / event controller |
| `setText()` | `L68` | Reactive DOM rendering / event controller |
| `setPnl()` | `L70` | Reactive DOM rendering / event controller |
| `tone()` | `L77` | Reactive DOM rendering / event controller |
| `badge()` | `L84` | Reactive DOM rendering / event controller |
| `notify()` | `L91` | Reactive DOM rendering / event controller |
| `showError()` | `L99` | Reactive DOM rendering / event controller |
| `api()` | `L105` | Reactive DOM rendering / event controller |
| `updateControls()` | `L130` | Reactive DOM rendering / event controller |
| `refresh()` | `L152` | Reactive DOM rendering / event controller |
| `mutate()` | `L165` | Reactive DOM rendering / event controller |
| `renderSnapshot()` | `L174` | Reactive DOM rendering / event controller |
| `renderBuckets()` | `L209` | Reactive DOM rendering / event controller |
| `renderMainChart()` | `L228` | Reactive DOM rendering / event controller |
| `sparkline()` | `L374` | Reactive DOM rendering / event controller |
| `cell()` | `L384` | Reactive DOM rendering / event controller |
| `selectCompany()` | `L386` | Reactive DOM rendering / event controller |
| `renderWatchlist()` | `L393` | Reactive DOM rendering / event controller |
| `squarify()` | `L450` | Reactive DOM rendering / event controller |
| `layoutRow()` | `L460` | Reactive DOM rendering / event controller |
| `worst()` | `L507` | Reactive DOM rendering / event controller |

---

## 7. Code Health & Complexity Radar

Functions requiring architectural attention (> 70 lines or nesting depth >= 4):


| File | Function / Method | Length (Lines) | Max Nesting Depth | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| `backend/chat.py` | `match_symbol` | 16 | 4 | Acceptable; well-scoped logic |
| `backend/chat.py` | `format_canary_updates` | 16 | 4 | Acceptable; well-scoped logic |
| `backend/chat.py` | `local_summary` | 76 | 2 | Acceptable; well-scoped logic |
| `backend/database.py` | `create_schema` | 19 | 4 | Acceptable; well-scoped logic |
| `backend/engine/agent_actions.py` | `emergency_quarantine_and_canary` | 106 | 5 | Decompose into sub-functions |
| `backend/engine/agent_actions.py` | `check_canary_theses` | 31 | 4 | Acceptable; well-scoped logic |
| `backend/engine/agent_actions.py` | `execute_agentic_buy` | 83 | 3 | Acceptable; well-scoped logic |
| `backend/engine/auto_trader.py` | `run_cycle` | 202 | 5 | Decompose into sub-functions |
| `backend/engine/auto_trader.py` | `advance_demo` | 38 | 5 | Acceptable; well-scoped logic |
| `backend/engine/curve_analyzer.py` | `analyze_curve` | 82 | 3 | Acceptable; well-scoped logic |
| `backend/engine/sequential_seller.py` | `plan_sale` | 105 | 3 | Decompose into sub-functions |
| `backend/engine/t2_ledger.py` | `bucket_balances` | 31 | 4 | Acceptable; well-scoped logic |
| `backend/hermes/agent_loop.py` | `execute_tool` | 121 | 11 | Decompose into sub-functions |
| `backend/hermes/agent_loop.py` | `detect_intent_and_tool` | 132 | 5 | Decompose into sub-functions |
| `backend/hermes/agent_loop.py` | `run_turn` | 65 | 4 | Acceptable; well-scoped logic |
| `backend/hermes/agent_loop.py` | `_format_tool_response` | 115 | 4 | Decompose into sub-functions |
| `backend/hermes/agent_loop.py` | `_conversational_inference` | 94 | 3 | Acceptable; well-scoped logic |
| `backend/hermes/memory.py` | `search_sessions` | 28 | 4 | Acceptable; well-scoped logic |
| `backend/hermes/memory.py` | `format_layer_3_prompt` | 17 | 5 | Acceptable; well-scoped logic |
| `backend/hermes/secret_guard.py` | `redact_secrets` | 11 | 4 | Acceptable; well-scoped logic |
| `backend/hermes/skills_manager.py` | `match_skills` | 22 | 4 | Acceptable; well-scoped logic |
| `backend/main.py` | `create_app` | 211 | 4 | Decompose into sub-functions |
| `backend/main.py` | `local_security` | 39 | 4 | Acceptable; well-scoped logic |
| `backend/main.py` | `event_stream` | 26 | 4 | Acceptable; well-scoped logic |
| `backend/main.py` | `generator` | 13 | 4 | Acceptable; well-scoped logic |
| `backend/market_map.py` | `build_market_map_payload` | 72 | 5 | Acceptable; well-scoped logic |
| `backend/portfolio.py` | `snapshot_from_session` | 259 | 3 | Decompose into sub-functions |
| `backend/portfolio.py` | `normalized_watchlist` | 20 | 4 | Acceptable; well-scoped logic |
| `backend/seed.py` | `seed_demo` | 87 | 3 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `is_ignored` | 6 | 4 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `collect_file_metrics` | 15 | 4 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `parse_fastapi_routes` | 25 | 7 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `parse_frontend` | 19 | 4 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `generate_markdown` | 153 | 6 | Decompose into sub-functions |
| `scripts/generate_code_map.py` | `visit_Call` | 10 | 4 | Acceptable; well-scoped logic |
| `scripts/generate_code_map.py` | `_compute_depth` | 12 | 4 | Acceptable; well-scoped logic |


> **Audit Summary:** 24 Python modules inspected, 12 FastAPI endpoints registered, 10,212 total LOC indexed.