# 🗺️ Humming Bird Trading Cockpit V1 — Frontend Architecture & Contract Map

> **Auto-Generated on:** `2026-11-26 07:26:10 UTC` via `scripts/generate_frontend_map.py`  
> **Zero-Regression Mandate:** 0 `MISSING_LIGHT_OVERRIDE` CSS issues, 0 Field Contract mismatches.

---

## 1. UI Layout & Component Hierarchy Tree

```text
index.html (.app-shell)
├── main.workspace.tx-workspace
│   ├── header.tx-top-header (#tx-top-header)
│   │   ├── .tx-topbar-brand (Logo, Title, SHADOW_DUMMY badge)
│   │   └── .tx-topbar-telemetry (Client A/C, Buying Power, Gain/Loss, DSEX, Clock, RunMode, Automation)
│   ├── nav.tx-main-nav (#tx-main-nav)
│   │   ├── Tab: Trade Workstation (#tx-nav-trade -> #view-dashboard)
│   │   ├── Tab: Market Map (#tx-nav-heatmap -> #view-heatmap-wrap)
│   │   ├── Tab: Strategy Rules (#tx-nav-rules -> #view-rules-wrap)
│   │   ├── Tab: T+2 Ledger (#tx-nav-ledger -> #view-ledger-wrap)
│   │   ├── Tab: Learning Logs (#tx-nav-learning -> #tx-learning-view)
│   │   └── Tab: Settings (#tx-nav-settings -> #view-settings)
│   └── section#view-dashboard (#tx-trade-workspace)
│       ├── top-pane: #tx-market-watch (~54% height)
│       │   ├── header: .tx-mw-header (Category Tabs: My Favorites, GSC, L1, L2, All DSE; Search Box)
│       │   └── table.tx-mw-table (#watchlist-thead, #watchlist-body: 13 NetPlus Columns)
│       └── bottom-split: .tx-bottom-split (~46% height)
│           ├── bottom-left: #tx-order-ticket (New Order Ticket, Steppers, 5-Level Depth, Submit Button)
│           └── bottom-right: #tx-monitor-panel (Sub-tabs: Holdings, Orders, Account Summary [Donut + Mirror Card])
├── aside#hermes-sidebar (Hermes AI Co-pilot Dock, 300..440px Resizable)
│   ├── nav#hermes-tabs (Chat, Conversations, Changes, Skills)
│   └── panes (#pane-hermes-chat, #pane-hermes-conversations, #pane-hermes-changes, #pane-hermes-skills)
└── modals
    ├── dialog#tx-confirm-order-modal (2-Step Execution Confirmation Modal)
    ├── dialog#tx-cdp-setup-modal (1-Click Safe Browser Launcher)
    └── dialog#deep-trend-modal (400-Candle Historical Chart)
```

---

## 2. Dark vs Light Mode CSS Parity Audit Table

Audit of `.tx-*`, `#tx-*`, and critical ticket/search elements in `styles.css` vs `theme_light_hermes.css`:

> **Status:** `0` Missing Light Overrides.


| Selector | Dark Background in `styles.css` | Light Override in `theme_light_hermes.css` | Audit Status |
| :--- | :--- | :--- | :--- |
| `.tx-topbar` | `#0d1522` | `#ffffff` | ✅ PARITY_OK |
| `.tx-acc-badge` | `#1e293b` | `#e0f2fe` | ✅ PARITY_OK |
| `.tx-main-nav` | `#0a0f18` | `#f8fafc` | ✅ PARITY_OK |
| `.tx-spy-pill-btn` | `#1e293b` | `#f1f5f9` | ✅ PARITY_OK |
| `.tx-pane` | `#0d1522` | `#ffffff` | ✅ PARITY_OK |
| `.tx-mw-header` | `#0a0f18` | `#f8fafc` | ✅ PARITY_OK |
| `.tx-search-wrap` | `#090e17` | `#ffffff` | ✅ PARITY_OK |
| `.tx-mw-table thead th` | `#0f172a` | `#f1f5f9` | ✅ PARITY_OK |
| `.tx-panel-header` | `#0a0f18` | `#f1f5f9` | ✅ PARITY_OK |
| `.tx-ticket-strip` | `#0d1522` | `#f8fafc` | ✅ PARITY_OK |
| `.tx-side-toggle` | `#090e17` | `#f1f5f9` | ✅ PARITY_OK |
| `.tx-side-btn.tx-side-buy.active` | `#10b981` | `#10b981` | ✅ PARITY_OK |
| `.tx-field select` | `#090e17` | `#ffffff` | ✅ PARITY_OK |
| `.tx-field input` | `#090e17` | `inherit` | ✅ PARITY_OK |
| `.tx-step-btn` | `#1e293b` | `#ffffff` | ✅ PARITY_OK |
| `.tx-btn-xs` | `#1e293b` | `#f1f5f9` | ✅ PARITY_OK |
| `.tx-depth-pane` | `#090e17` | `#ffffff` | ✅ PARITY_OK |
| `.tx-depth-head` | `#0f172a` | `#f1f5f9` | ✅ PARITY_OK |
| `.tx-depth-table th` | `#0d1522` | `#f1f5f9` | ✅ PARITY_OK |
| `.tx-depth-foot` | `#090e17` | `#f8fafc` | ✅ PARITY_OK |
| `.tx-ticket-footer` | `#0a0f18` | `#f8fafc` | ✅ PARITY_OK |
| `.tx-mon-header` | `#0a0f18` | `#f8fafc` | ✅ PARITY_OK |
| `#tx-confirm-order-modal` | `#0f172a` | `#ffffff` | ✅ PARITY_OK |
| `#tx-confirm-order-modal::backdrop` | `rgba(0, 0, 0, 0.7)` | `inherit` | ✅ PARITY_OK |
| `.tx-confirm-banner.buy` | `#10b981` | `#dcfce7` | ✅ PARITY_OK |
| `.tx-confirm-note` | `rgba(0, 0, 0, 0.2)` | `#f8fafc` | ✅ PARITY_OK |
| `.tx-confirm-actions` | `#0a0f18` | `#f8fafc` | ✅ PARITY_OK |
| `.tx-decisions-summary-bar` | `#0f172a` | `#ffffff` | ✅ PARITY_OK |
| `.tx-decisions-scroll` | `#0f172a` | `#ffffff` | ✅ PARITY_OK |
| `.tx-decisions-table th` | `#111827` | `#f1f5f9` | ✅ PARITY_OK |

---

## 3. Backend Snapshot ↔ Frontend Field Contract Matrix

Verification of data contracts between `backend/portfolio.py` and frontend JS (`app.js`, `tradexpress_ui.js`):

> **Status:** `0` Field Contract Mismatches.


| Scope | Field / Property Name | Emitted by Backend | Contract Status |
| :--- | :--- | :--- | :--- |
| Company View (`company.*` / `c.*`) | `avg_bought_price` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `bid` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `bid_qty` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `bought_total` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `change_pct` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `cost_basis` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `curve` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `day_change_pct` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `estimated_net_value` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `favorite` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `history` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `history_days` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `hit_52w_high` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `hit_upper_circuit` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `hold_day_label` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `holding_qty` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `last_price` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `lots` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `mature_qty` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `mature_shares` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `max_limit` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `min_limit` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `name` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `net_profit_bdt` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `net_profit_pct` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `net_return_pct` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `offer` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `offer_qty` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `order_book_depth` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `pct_change` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `price` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `quarantine_persisted` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `quarantine_reason` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `quarantined` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `rule` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `sector` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `sell_total_net` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `settlement_type` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `source` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `sparkline_points` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `symbol` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `symbol_category` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `tradexpress_symbol` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `unrealized_pnl` | Yes | ✅ CONTRACT_VERIFIED |
| Company View (`company.*` / `c.*`) | `watchlist_category` | Yes | ✅ CONTRACT_VERIFIED |
| Root Snapshot (`snapshot.*` / `state.snapshot.*`) | `adapter` | Yes | ✅ CONTRACT_VERIFIED |
| Root Snapshot (`snapshot.*` / `state.snapshot.*`) | `app` | Yes | ✅ CONTRACT_VERIFIED |
| Root Snapshot (`snapshot.*` / `state.snapshot.*`) | `broker_mirror_account` | Yes | ✅ CONTRACT_VERIFIED |
| Root Snapshot (`snapshot.*` / `state.snapshot.*`) | `buckets` | Yes | ✅ CONTRACT_VERIFIED |
| Root Snapshot (`snapshot.*` / `state.snapshot.*`) | `buying_power_bdt` | Yes | ✅ CONTRACT_VERIFIED |
| Root Snapshot (`snapshot.*` / `state.snapshot.*`) | `canary_theses` | Yes | ✅ CONTRACT_VERIFIED |
| Root Snapshot (`snapshot.*` / `state.snapshot.*`) | `companies` | Yes | ✅ CONTRACT_VERIFIED |
| Root Snapshot (`snapshot.*` / `state.snapshot.*`) | `decisions` | Yes | ✅ CONTRACT_VERIFIED |
| Root Snapshot (`snapshot.*` / `state.snapshot.*`) | `dse_index` | Yes | ✅ CONTRACT_VERIFIED |
| Root Snapshot (`snapshot.*` / `state.snapshot.*`) | `last_market_sync` | Yes | ✅ CONTRACT_VERIFIED |
| Root Snapshot (`snapshot.*` / `state.snapshot.*`) | `market_map` | Yes | ✅ CONTRACT_VERIFIED |
| Root Snapshot (`snapshot.*` / `state.snapshot.*`) | `metrics` | Yes | ✅ CONTRACT_VERIFIED |
| Root Snapshot (`snapshot.*` / `state.snapshot.*`) | `periods` | Yes | ✅ CONTRACT_VERIFIED |
| Root Snapshot (`snapshot.*` / `state.snapshot.*`) | `portfolio_id` | Yes | ✅ CONTRACT_VERIFIED |
| Root Snapshot (`snapshot.*` / `state.snapshot.*`) | `portfolio_name` | Yes | ✅ CONTRACT_VERIFIED |
| Root Snapshot (`snapshot.*` / `state.snapshot.*`) | `summary` | Yes | ✅ CONTRACT_VERIFIED |
| Root Snapshot (`snapshot.*` / `state.snapshot.*`) | `trades` | Yes | ✅ CONTRACT_VERIFIED |
| Root Snapshot (`snapshot.*` / `state.snapshot.*`) | `trading_mode` | Yes | ✅ CONTRACT_VERIFIED |
| Root Snapshot (`snapshot.*` / `state.snapshot.*`) | `unsettled_sales_bdt` | Yes | ✅ CONTRACT_VERIFIED |

---

## 4. JS Function → DOM IDs & API Endpoints Map

Mapping of client functions to active DOM elements and localhost API endpoints:


| File | Function Name | Referenced DOM IDs | API Endpoints Invoked |
| :--- | :--- | :--- | :--- |
| `frontend/app.js` | `formatTimestamp` | `#toast` | — |
| `frontend/app.js` | `element` | `#error-banner`, `#reset-breaker-btn`, `#toast` | — |
| `frontend/app.js` | `svgElement` | `#error-banner`, `#reset-breaker-btn`, `#toast` | — |
| `frontend/app.js` | `currency` | `#error-banner`, `#reset-breaker-btn`, `#toast` | — |
| `frontend/app.js` | `percentage` | `#error-banner`, `#reset-breaker-btn`, `#toast` | — |
| `frontend/app.js` | `sessionDate` | `#error-banner`, `#reset-breaker-btn`, `#toast` | — |
| `frontend/app.js` | `setText` | `#error-banner`, `#reset-breaker-btn`, `#toast` | — |
| `frontend/app.js` | `setPnl` | `#error-banner`, `#reset-breaker-btn`, `#toast` | — |
| `frontend/app.js` | `tone` | `#error-banner`, `#reset-breaker-btn`, `#toast` | — |
| `frontend/app.js` | `badge` | `#error-banner`, `#reset-breaker-btn`, `#toast` | — |
| `frontend/app.js` | `notify` | `#error-banner`, `#reset-breaker-btn`, `#run-cycle`, `#run-label`, `#toast`, `#topbar-handoff-btn` | — |
| `frontend/app.js` | `showError` | `#buy-allocation`, `#company-enabled`, `#error-banner`, `#next-session`, `#reset-breaker-btn`, `#run-cycle` | — |
| `frontend/app.js` | `api` | `#buy-allocation`, `#chat-send`, `#company-enabled`, `#engine-state`, `#next-session`, `#run-cycle` | — |
| `frontend/app.js` | `updateControls` | `#buy-allocation`, `#chat-send`, `#company-enabled`, `#engine-state`, `#error-banner`, `#next-session` | `/api/portfolio` |
| `frontend/app.js` | `refresh` | `#error-banner`, `#portfolio-header-badge`, `#portfolio-header-badge-dot`, `#portfolio-header-badge-text` | `/api/portfolio` |
| `frontend/app.js` | `mutate` | `#portfolio-header-badge`, `#portfolio-header-badge-dot`, `#portfolio-header-badge-text` | — |
| `frontend/app.js` | `isLiveSource` | `#footer-mode-tag`, `#portfolio-header-badge`, `#portfolio-header-badge-dot`, `#portfolio-header-badge-text` | — |
| `frontend/app.js` | `renderPortfolioHeaderBadge` | `#chat-safety-note`, `#footer-mode-tag`, `#portfolio-header-badge`, `#portfolio-header-badge-dot`, `#portfolio-header-badge-text` | — |
| `frontend/app.js` | `renderSnapshot` | `#active-holdings-body`, `#chat-safety-note`, `#equity-sparkline`, `#footer-mode-tag`, `#metric-total-gain` | — |
| `frontend/app.js` | `renderEquitySparkline` | `#active-holdings-body`, `#active-holdings-foot`, `#equity-sparkline`, `#holdings-unrealized-gain` | — |
| `frontend/app.js` | `renderActiveHoldings` | `#active-holdings-body`, `#active-holdings-foot`, `#holdings-unrealized-gain` | — |
| `frontend/app.js` | `renderBuckets` | `#bucket-stack`, `#cat-all-count`, `#cat-dse-count`, `#cat-gsc-count`, `#cat-l1-count`, `#cat-l2-count` | — |
| `frontend/app.js` | `cell` | `#cat-all-count`, `#cat-dse-count`, `#cat-gsc-count`, `#cat-l1-count`, `#cat-l2-count`, `#company-search` | — |
| `frontend/app.js` | `selectCompany` | `#cat-all-count`, `#cat-dse-count`, `#cat-gsc-count`, `#cat-l1-count`, `#cat-l2-count`, `#company-search` | — |
| `frontend/app.js` | `formatCompactNumber` | `#cat-all-count`, `#cat-dse-count`, `#cat-gsc-count`, `#cat-l1-count`, `#cat-l2-count`, `#company-search` | — |
| `frontend/app.js` | `renderWatchlist` | `#cat-all-count`, `#cat-dse-count`, `#cat-gsc-count`, `#cat-l1-count`, `#cat-l2-count`, `#company-search` | — |
| `frontend/app.js` | `renderCanaryTheses` | `#buy-allocation`, `#canary-feed`, `#canary-section`, `#company-enabled`, `#lots-body`, `#profit-tiers` | — |
| `frontend/app.js` | `renderInspector` | `#buy-allocation`, `#company-enabled`, `#lots-body`, `#profit-tiers` | — |
| `frontend/app.js` | `isBuyDecision` | `#decision-feed` | — |
| `frontend/app.js` | `isSellDecision` | `#decision-feed` | — |

---

## 5. Edge Extension Passive Sniffer Map (`extension/tradexpress_mirror/`)

- **Extension Name:** `Humming Bird — TradeXpress Passive Mirror` (v`1.0.0`)
- **Target Origin:** `https://itrade.lbsbd.com/*` (100% read-only content script)
- **Host Permissions:** `http://127.0.0.1:8000/*`

### 5.1 Targeted Broker DOM Selectors

- `#order-symbol-info [data-id="order-price-info-level-4"], [data-id="order-price-info-level-4"]`
- `#order-ticket-landscape-id, [container-id="orderTicket"]`
- `#portfolioContainer-8-1-2-3, [container-id="portfolio"]`
- `#table-8-1-1-2-cached, [container-id="marketWatch"]`

### 5.2 Storage Keys

- `telemetry`

### 5.3 Localhost Endpoints Forwarded

- `http://127.0.0.1:8000/api/tradexpress/passive-ingest`
- `http://127.0.0.1:8000/api/tradexpress/passive-net-tap`

