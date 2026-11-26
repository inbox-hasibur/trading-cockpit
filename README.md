<div align="center">
  <img src="frontend/favicon.svg" alt="Humming Bird Logo" width="84" height="84" />
  <h1>Humming Bird</h1>

  <p>
    <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.12+" /></a>
    <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-Async_Core-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI" /></a>
    <a href="https://sqlite.org"><img src="https://img.shields.io/badge/SQLite-Transactional_WAL-003B57?style=flat-square&logo=sqlite&logoColor=white" alt="SQLite WAL" /></a>
    <a href="https://developer.chrome.com/docs/extensions/mv3/"><img src="https://img.shields.io/badge/Browser_Extension-Passive_MV3-0078D7?style=flat-square&logo=microsoftedge&logoColor=white" alt="Passive Browser Extension" /></a>
    <a href="https://playwright.dev"><img src="https://img.shields.io/badge/Playwright-E2E_Verified-2EAD33?style=flat-square&logo=playwright&logoColor=white" alt="Playwright" /></a>
    <img src="https://img.shields.io/badge/AI_Co--Pilot-Multi--Provider-7C3AED?style=flat-square" alt="AI Co-Pilot" />
    <img src="https://img.shields.io/badge/Pytest-290%2B_Tests_Passing-16A34A?style=flat-square&logo=pytest&logoColor=white" alt="Pytest Passing" />
  </p>

  <h3>Experimental Market Telemetry, Portfolio Tracking &amp; Workflow Automation Cockpit.</h3>

  <p>
    An attempt to streamline and automate repetitive manual buy/sell workflows with real-time market telemetry, simulation, and an AI assistant.<br />
    <strong>Disclaimer:</strong> Experimental personal project — <strong>no guarantee of profit</strong> or financial returns.
  </p>
</div>

---

## ⚡ Why Humming Bird? (Problem & Attempted Solution)

- **The Problem:** Active market monitoring requires repeatedly checking prices, watching order books, tracking portfolio state, and executing repetitive buy/sell decisions manually across web terminals.
- **The Attempted Solution:** Humming Bird is a local-first cockpit that tries to organize and automate parts of this repetitive buy/sell workflow. It passively observes market quotes from an active browser session, combines them with historical price context, provides a local simulation mode, and offers an AI co-pilot for analysis — without guaranteeing profits or financial outcomes.

---

## ✨ Key Features

- 📡 **Passive Telemetry Mirror:** Read-only browser extension that mirrors live market quotes and session state locally without automated login or credential handling.
- 📈 **Market Context & Charts:** Pairs live market prices with historical daily price data and interactive sparklines for quick visual review.
- 🧠 **Decision Support & AI Co-Pilot:** Summarizes market candidates and integrates a multi-provider AI assistant for interactive Q&A and workflow assistance.
- 📒 **Local Portfolio Ledger:** Tracks cash, holdings, realized/unrealized performance, and order history in an atomic local database.
- 🧪 **Simulation Mode:** Lets you test and observe automated or manual workflows locally with zero real capital exposure.
- 🌓 **Dark & Light Terminal:** Zero-build, real-time reactive web UI verified across desktop viewports.

---

## 📡 High-Level Architecture

| Layer | Purpose | How It Fits Together |
| :--- | :--- | :--- |
| **🧩 Passive Browser Bridge** | Live market telemetry | Read-only Manifest V3 extension forwards live quote updates to the local backend. |
| **⚙️ Local Backend Engine** | State & workflow logic | FastAPI service manages market state, risk guardrails, simulation, and real-time events. |
| **🗄️ Transactional Store** | Reliable persistence | SQLite (WAL) stores portfolio state, order logs, price history, and checkpoints. |
| **🤖 AI Co-Pilot** | Interactive assistance | Multi-provider LLM router with availability checks and tool-assisted analysis. |
| **🖥️ Web Terminal** | Operator interface | Vanilla JS + CSS cockpit with live updates, charts, and Dark/Light themes. |

---

## 🛠️ Tech Stack

| Domain | Technology | Role |
| :--- | :--- | :--- |
| **Backend & API** | [Python 3.12+](https://python.org) · [FastAPI](https://fastapi.tiangolo.com) · [Pydantic v2](https://docs.pydantic.dev) | Core engine, REST/SSE APIs, and schema validation. |
| **Database** | [SQLAlchemy 2.0](https://sqlalchemy.org) · [SQLite (WAL)](https://sqlite.org) | Local transactional persistence. |
| **Browser Bridge** | Chrome / Edge Extension (Manifest V3) | Read-only local telemetry capture. |
| **Frontend** | Vanilla ES6+ · Custom Dark/Light CSS | Zero-build reactive dashboard and charts. |
| **Testing** | [Pytest](https://pytest.org) · [Playwright](https://playwright.dev) | Automated unit, API, and browser UI verification. |

---

## 💻 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/inbox-hasibur/trading-cockpit.git
cd trading-cockpit

# 2. Create virtual environment & install dependencies (Windows PowerShell)
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend/requirements.txt

# 3. Start the server
python run.py
```

Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser, and optionally load **`extension/tradexpress_mirror/`** as an unpacked extension in `edge://extensions` (or `chrome://extensions`).

---

## 🔒 Safety & Disclaimer

- **No Profit Guarantee:** This software is an experimental automation and telemetry tool. Markets carry inherent risk, and there is no guarantee of profit.
- **No Automated Logins:** Credential entry and session authentication remain strictly manual.
- **Local-First & Explicit Confirmation:** Runs locally on loopback (`127.0.0.1`) with explicit confirmation steps and configurable risk limits.

---

## 📄 Maintainer

- **Author & Maintainer:** [IncodeBD / Hasibur](https://github.com/inbox-hasibur)
- **Branch:** `trading-cockpit-v1`
