<div align="center">
  <img src="frontend/favicon.svg" alt="Humming Bird Logo" width="84" height="84" />
  <h1>Humming Bird</h1>

  <p>
    <a href="http://127.0.0.1:8000"><img src="https://img.shields.io/badge/Local_Cockpit-127.0.0.1%3A8000-0D9488?style=flat-square&logo=fastapi&logoColor=white" alt="Local Cockpit" /></a>
    <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.12+" /></a>
    <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-Async_Kernel-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" /></a>
    <a href="https://sqlite.org"><img src="https://img.shields.io/badge/SQLite-Transactional_WAL-003B57?style=flat-square&logo=sqlite&logoColor=white" alt="SQLite WAL" /></a>
    <a href="https://developer.chrome.com/docs/extensions/mv3/"><img src="https://img.shields.io/badge/Edge_Extension-100%25_Passive_MV3-0078D7?style=flat-square&logo=microsoftedge&logoColor=white" alt="Passive Edge Extension" /></a>
    <a href="https://playwright.dev"><img src="https://img.shields.io/badge/Playwright-Visual_&_E2E_Gates-2EAD33?style=flat-square&logo=playwright&logoColor=white" alt="Playwright" /></a>
    <img src="https://img.shields.io/badge/Hermes_Advisor-25_Kernel_Tools-7C3AED?style=flat-square" alt="Hermes Advisor" />
    <img src="https://img.shields.io/badge/Pytest-287%2B_Tests_Passing-16A34A?style=flat-square&logo=pytest&logoColor=white" alt="Pytest Passing" />
  </p>

  <h3>Local-First DSE Trading Cockpit, Passive TradeXpress Mirror &amp; Real-Data Decision Advisor.</h3>

  <p>
    Real-time passive Market Watch, 5-level Order Depth, real 30-day DSE curves, T+2 bucket accounting, and an AI co-pilot.<br />
    Zero broker login automation. Zero dummy data. Strict no-loss &amp; capital guardrails.
  </p>

  <p>
    <a href="http://127.0.0.1:8000">
      <img src="https://img.shields.io/badge/%F0%9F%9A%80%20Launch%20Cockpit-127.0.0.1%3A8000-0D9488?style=for-the-badge&logo=fastapi&logoColor=white" alt="Launch Humming Bird Cockpit" />
    </a>
  </p>
</div>

---

## ⚡ Why Humming Bird? (Problem & Solution)

- **The Problem:** Trading on Dhaka Stock Exchange (DSE) via web terminals makes it hard to track 7–30 day price curves, T+2 settlement buckets (`A`/`B`/`C`), round-trip brokerage breakeven hurdles (`~0.80%–1.00%`), and Z/SPOT traps in real time — while automating broker logins risks account lockouts.
- **The Solution:** Humming Bird runs 100% locally on your machine. A 100% read-only Edge/Chrome Manifest V3 extension passively mirrors your logged-in TradeXpress session (`LTP`, `Bid/Offer`, `5-Level Depth`, `H9210` Account Summary, `Order List`), pairs it with real 30-day DSE daily curves, and generates an actionable **Today's Buy / Sell Decision Table** + **Hermes AI Advisor** so you can trade with clarity and zero broker ban risk.

---

## ✨ Key Features

- 📡 **100% Passive Broker Mirror:** Read-only Edge/Chrome extension (`extension/tradexpress_mirror/`) + WebSocket/XHR tap (`network_tap.js`) with zero automated clicks, logins, or broker HTTP requests.
- 📈 **Real 30-Day DSE Curves:** Fetches verified daily OHLCV history (`history_provider.py`) and merges live TradeXpress LTP — `< 7` real bars renders `—` (`NO_HISTORY`) with zero synthetic curves.
- 🧠 **Decision Table & Hermes Advisor:** One-click **`Decision`** view ranks `BUY_CANDIDATE`, `SELL_CANDIDATE`, `HOLD_WAIT`, and `BLOCKED` (`Z`/`SPOT`) stocks with exact Limit Prices, Support–Resistance, net upside after fees, and `hb_analyze_market`.
- 🏦 **3-Bucket T+2 Settlement Ledger:** Tracks Sunday–Thursday DSE sessions across rolling `A`, `B`, and `C` buckets with strict `0.00` BDT drift reconciliation.
- 🛡️ **Strict No-Loss & Sequential Scaling:** Blocks sales below net breakeven after fees, enforces 90/10 canary probes on crash quarantines, and excludes Z-category / SPOT instruments.
- 🌓 **Zero-Build Dark & Light Terminal:** Instant SSE-reactive 3-pane cockpit with Dark and Light themes verified in headless Playwright across `800px`, `1280px`, and `1440px` viewports.

---

## 📡 Core Architecture & Workflows

| Module / Channel | Best For | How It Works |
| :--- | :--- | :--- |
| **🧩 Passive Edge Mirror** | Real-time TradeXpress telemetry | MutationObserver (`0.35s`) + `network_tap.js` streams quotes, depth, `H9210` cash & `Order List` to `127.0.0.1:8000`. |
| **📈 Real 30d Curve Sync** | Accurate 7–30d range & signals | Unauthenticated public DSE `1D` candle sync merged with live TradeXpress LTP (`POST /api/tradexpress/sync-history`). |
| **🎯 Decision Advisor** | Daily manual buy/sell planning | Deterministic evaluator (`decision_advisor.py`) computes Limit Price, Support–Resistance, net upside & `H9210` qty. |
| **🤖 Hermes Co-Pilot** | Strategy check & Banglish Q&A | 25 registered kernel tools (`hb_analyze_market`, `hb_portfolio`, `hb_place_order`, etc.) with strict `pre_tool_call` hooks. |
| **🧪 Shadow Simulator** | Risk-free strategy practice | Local `SHADOW_DUMMY` order book (`H9210_SHADOW`) with 2-step confirmation and `0 BDT` real exposure. |
| **🔌 Kernel API & SSE** | Instant reactive UI updates | FastAPI loopback kernel pushes live `"portfolio"` & `"tradexpress_feed_update"` Server-Sent Events. |

---

## 🛠️ Tech Stack & Key Technologies

| Domain / Layer | Technology | Role in Humming Bird |
| :--- | :--- | :--- |
| **Core Kernel & API** | [Python 3.12+](https://python.org) · [FastAPI](https://fastapi.tiangolo.com) · [Pydantic v2](https://docs.pydantic.dev) | Deterministic trading engine, REST/SSE endpoints, and strict schema validation. |
| **Persistence & Ledger** | [SQLAlchemy 2.0](https://sqlalchemy.org) · [SQLite (WAL)](https://sqlite.org) | Atomic T+2 bucket accounting, tax lots, idempotency locks, and state checkpoints. |
| **Passive Browser Mirror** | Chrome/Edge Extension (Manifest V3) | 100% read-only Ember DOM & WebSocket/XHR mirror scoped strictly to `127.0.0.1:8000`. |
| **Cockpit Frontend** | Vanilla ES6+ · Custom Dark/Light CSS | Zero-build 3-pane operator terminal with inline SVG sparklines, treemap, and donut charts. |
| **Agentic Co-Pilot** | Hermes Agent (`plugins/humming_bird/`) | 25 kernel tools + lifecycle hooks (`pre_tool_call`) + Gemini / OpenRouter model routing. |
| **Testing & Quality** | [Pytest](https://pytest.org) · [Playwright](https://playwright.dev) | 287+ automated unit, accounting, API, DOM-audit, and headless Chromium layout tests. |

---

## 💻 Quick Start & Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/inbox-hasibur/trading-cockpit.git
cd trading-cockpit

# 2. Create virtual environment & install dependencies (Windows PowerShell)
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend/requirements.txt

# 3. Start the cockpit server
python run.py
```

Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser (API docs at `/docs`), and load **`extension/tradexpress_mirror/`** as an unpacked extension in `edge://extensions` (or `chrome://extensions`).

> **Storage Note:** For sustained SQLite WAL performance, keep `DATABASE_URL` pointed to a fast local path outside cloud-synced folders if needed.

---

## 🔒 Privacy, Safety & Zero-Ban Firewall

- **2-Touchpoint Broker Firewall:** Zero automated login, password entry, clicking, or active HTTP polling against `itrade.lbsbd.com` or `ibroker.lbsbd.com`.
- **Zero-Secret Isolation:** `network_tap.js` and `secret_guard.py` redact `sesnId`, `SSOTOK`, `token`, `password`, and cookies before local logging; Hermes physically lacks file/terminal toolsets.
- **2-Step Order Confirmation:** Manual and tool-driven orders enforce Step 1 preview (`dry_run` / `confirm=False`) before Step 2 execution (`confirm=True`).
- **Loopback-Only Security:** Kernel binds strictly to `127.0.0.1` with TrustedHost and cross-origin protections.

---

## 📄 Documentation & License

- **Documentation:** [`documentation/About_Project.md`](documentation/About_Project.md) · [`documentation/TRADEXPRESS_CONTEXT.md`](documentation/TRADEXPRESS_CONTEXT.md) · [`documentation/CODEBASE_MAP.md`](documentation/CODEBASE_MAP.md) · [`documentation/FRONTEND_MAP.md`](documentation/FRONTEND_MAP.md) · [`documentation/CHANGELOG.md`](documentation/CHANGELOG.md)
- **Author & Maintainer:** [IncodeBD / Hasibur](https://github.com/inbox-hasibur)
- **Branch:** `trading-cockpit-v1` (Active V1 Development)
