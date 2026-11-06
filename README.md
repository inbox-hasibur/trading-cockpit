# 🐦 H U M M I N G B I R D

### `trading-cockpit` · Autonomous Market Telemetry & Execution Kernel

[![Python](https://img.shields.io/badge/Python-3.12%2B-0f172a?style=for-the-badge&logo=python&logoColor=38bdf8)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Async_Core-0f172a?style=for-the-badge&logo=fastapi&logoColor=10b981)](https://fastapi.tiangolo.com)
[![Playwright](https://img.shields.io/badge/Playwright-CDP_Bridge-0f172a?style=for-the-badge&logo=playwright&logoColor=f59e0b)](https://playwright.dev)
[![SQLite](https://img.shields.io/badge/Ledger-Transactional_WAL-0f172a?style=for-the-badge&logo=sqlite&logoColor=6366f1)](https://sqlite.org)
[![Status](https://img.shields.io/badge/Build-Stealth_v0.1-0f172a?style=for-the-badge&logoColor=ec4899)](#)

> *“Stillness in volatility. Precision in execution.”*

---

## ◈ Overview

**Humming Bird** (`trading-cockpit`) is a private, local-first quantitative execution cockpit and state-machine engine engineered for frontier equity markets.

Designed around a zero-build reactive terminal and a deterministic Python kernel, the system orchestrates real-time telemetry, multi-stage settlement accounting, regime-aware signal evaluation, and automated browser-protocol adapters under strict capital guardrails.

> **Stealth Notice:** Core heuristic parameters, proprietary regime classifiers, and execution weights are abstracted from public documentation.

---

## ◈ System Topology

```text
  ┌─────────────────────────────────────────────────────────────────────┐
  │                     C O C K P I T   T E R M I N A L                 │
  │   [ Telemetry Matrix ]    [ Settlement Pipeline ]   [ Neural Side ] │
  └──────────────────────────────────┬──────────────────────────────────┘
                                     │  Loopback REST / State Stream
                                     ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │                   D E T E R M I N I S T I C   K E R N E L           │
  │                                                                     │
  │   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
  │   │  Regime Sensor   │  │  Execution Gate  │  │  Horizon Ledger  │  │
  │   └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘  │
  │            └─────────────────────┼─────────────────────┘            │
  │                                  ▼                                  │
  │                     [ Atomic Cycle Coordinator ]                    │
  └──────────────────┬───────────────────────────────┬──────────────────┘
                     │                               │
                     ▼                               ▼
       ┌───────────────────────────┐   ┌───────────────────────────┐
       │  CDP / Network Adapters   │   │   Encrypted Local Store   │
       └───────────────────────────┘   └───────────────────────────┘
```

---

## ◈ Technology Stack

| Layer | Stack | Role |
| :--- | :--- | :--- |
| **Core Runtime** | `Python 3.12+` · `FastAPI` · `Pydantic v2` | Asynchronous state coordination, deterministic cycle execution, strict schema validation |
| **Persistence** | `SQLAlchemy 2.0` · `SQLite (WAL)` | Atomic ledger accounting, lot-level state machines, idempotency locks & audit trails |
| **Web Automation** | `Playwright Async (CDP)` | Persistent context management, network payload inspection & headless/headed DOM bridge |
| **Cockpit UI** | `Vanilla ES6+` · `Custom Dark UI` | Zero-build, sub-millisecond local operator terminal served directly from the kernel |
| **Neural Bridge** | `OpenRouter API` · `Local Fallback` | Context-aware natural language telemetry inspector with hard rate & budget boundaries |
| **Verification** | `Pytest` · `FastAPI TestClient` | Deterministic unit, accounting, and end-to-end browser smoke verification |

---

## ◈ Quick Start

### 🚀 One-Command Launch (Like Next.js `npm run dev`)

```bash
# If you love npm / Next.js workflows:
npm run dev      # or npm run live

# Or directly in Git Bash / Terminal:
./run.sh         # or python run.py

# Or in Windows CMD / PowerShell:
run              # or .\run
```

The runner automatically detects `.venv`, handles dependencies, and spins up the live reload server.

---

### Manual Setup (First Time)

#### Windows (PowerShell / Git Bash)

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
python run.py
```

#### macOS / Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
python3 run.py
```

Once booted, open the operator terminal at **[http://127.0.0.1:8000](http://127.0.0.1:8000)** (Interactive API schema at `/docs`).

---

## ◈ Environment Configuration

Copy `backend/.env.example` to `backend/.env` to customize runtime parameters. All external credentials and local databases remain strictly off-repo.

| Variable | Description | Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | Local transactional ledger path | `backend/data/hummingbird.db` |
| `INITIAL_CAPITAL` | Base capital allocation for a fresh ledger | `15000` |
| `BUY_FEE_RATE` / `SELL_FEE_RATE` | Execution friction coefficients | `0.005` |
| `SETTLEMENT_DAYS` | Working-session maturity horizon | `2` |
| `OPENROUTER_API_KEY` | Optional key for the neural side-panel | *(Local fallback if empty)* |
| `OPENROUTER_MODEL` | Target LLM identifier | `deepseek/deepseek-chat` |
| `CHAT_DAILY_CALL_LIMIT` | Hard daily external inference cap | `30` |
| `COCKPIT_API_TOKEN` | Optional Bearer token for local API lock | *(Unset)* |

> **Storage Note:** Avoid placing active SQLite WAL files or persistent browser profiles inside cloud-synced directories (e.g., OneDrive/Dropbox). Point `DATABASE_URL` to a dedicated local path such as `sqlite:///C:/humming-bird-data/hummingbird.db` for sustained operation.

---

## ◈ Kernel Interface

| Method | Endpoint | Operation |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Kernel status & runtime version |
| `GET` | `/api/portfolio` | Full telemetry snapshot, positions, buckets & audit stream |
| `POST` | `/api/automation/cycle` | Trigger an atomic evaluation & execution cycle |
| `POST` | `/api/automation/pause` | Toggle global execution lock |
| `POST` | `/api/automation/config` | Update Master Automation switch, Ingestion Mode (`BACKGROUND_POLLING` vs `SIDE_BY_SIDE_LIVE`), and polling cadence |
| `POST` | `/api/demo/advance` | Step simulation clock & regime scenarios |
| `PATCH` | `/api/companies/{symbol}/allocation` | Update exposure weights & symbol status |
| `GET` | `/api/market/map` | Full DSE sector treemap and breadth metrics |
| `POST` | `/api/chat` | Query or command the Hermes agentic share assistant |
| `GET` | `/api/hermes/conversations` | List conversation threads (human strategy separator) |
| `POST` | `/api/hermes/conversations` | Create a new conversation thread |
| `GET` | `/api/hermes/conversations/{id}/messages` | Retrieve message history for a conversation |
| `GET` | `/api/system/changes` | Inspect workspace git modifications and state checkpoints |
| `POST` | `/api/hermes/rollback` | Undo last state mutation via checkpoint rollback |
| `GET` | `/api/stream` | Server-Sent Events (SSE) live reactive event stream |

---

## ◈ Documentation

Comprehensive system architecture, mathematical formulas, trading rules, and telemetry maps are maintained in [`documentation/`](documentation/):

| Document | Purpose |
| :--- | :--- |
| [**About_Project.md**](documentation/About_Project.md) | DSE Sun–Thu market hours, T+2 settlement pipeline, 3-tier GSC watchlist framework, 90/10 Canary probe, and Dual-Mode Ingestion mechanics. |
| [**Backlog.md**](documentation/Backlog.md) | Sprint deliverables, Hermes agent milestones, and technical audit trail. |
| [**CODEBASE_MAP.md**](documentation/CODEBASE_MAP.md) | Standard-library AST X-Ray: file metrics, dependency graphs, database schema, route registry, DOM topology, and Code Health Radar. |

---

## ◈ Verification Suite

Run the deterministic test suite (accounting, state transitions, and API contracts):

```powershell
.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
```

Optional headless browser smoke verification:

```powershell
.venv\Scripts\python.exe -m playwright install chromium
.venv\Scripts\python.exe tests/browser_smoke.py
```

---

*Project Humming Bird · Private Quantitative Infrastructure · All Rights Reserved*