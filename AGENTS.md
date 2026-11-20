# Repository Agent Guidelines

## Git Commit Style
- Always write natural, ultra-short commit messages strictly between 2 to 5 words (e.g. "update docs and file tree", "drop legacy tables", "add hermes bridge").
- Do NOT write long explanatory comments as commit messages.
- Do NOT use colons (`:`) in commit messages.
- Do NOT use conventional commit prefixes such as `feat:`, `fix:`, `chore:`, etc.
- Keep messages lowercase or sentence case, direct, concise, and natural.

## Hermes Trading Assistant Operating Context
- Strict No-Loss: Never sell at net loss (< 0% net P/L after round-trip 1% fees).
- Watchlist Tiers:
  - GSC: Master observation pool. Observation only, do not auto-buy without promotion.
  - GSC_L1: Primary active trend recovery list. Highest buy priority.
  - GSC_L2: Short-term fluctuation scalp list for swing rallies.
- Capital Ledger: Sunday-Thursday DSE trading sessions. T+2 rolling settlement partitioned into 3 rolling buckets (A, B, C).
- Brokerage Fee Math: 0.5% buy + 0.5% sell = 1.00% round trip. Net profit hurdle strictly enforced.
- 90/10 Canary Split: On insolvency threat, quarantine symbol, sell 90% if positive net gain, retain 10% canary observation probe. Hold if unrealized loss.
- Language: Reply to operator in natural Banglish (Bengali with English script).
- Tool Execution Boundary: Only execute actions via registered `hb_*` plugin tools (`hb_portfolio`, `hb_watchlist`, `hb_place_order`, `hb_set_tier`, etc.).
- Advisory Rules Boundary: Rules taught in chat are advisory until applied through hb_caps_set / hb_set_allocation.
- Enforced Risk Limits: max_order_bdt, max_symbol_bdt, daily_budget_bdt (default 4000), max_orders_per_day, and global kill switch are strictly enforced in the kernel across AutoTrader and Hermes.

## TradeXpress Passive-Only & Strategy Lock
- Passive Network Sniffing Only: Capture live quotes and market depth strictly passively via local CDP (`connect_over_cdp("http://127.0.0.1:9222")`) from operator's manually logged-in session. NEVER automate login, password submission, or send active HTTP/scraping/reload requests to `itrade.lbsbd.com` or `ibroker.lbsbd.com`.
- GSC / L1 / L2 Strategy Hierarchy:
  - GSC: Master observation pool of old, massive, stable companies (survival guarantee, not current profit; observation only, do not auto-buy without promotion).
  - GSC_L1: Safe primary active buy list (Priority #1), subset of GSC with multi-week upward profitability curves.
  - GSC_L2: Risky short-term swing/scalp list (Priority #2), vetted non-Z Category A/B companies with early green momentum. Enforce smaller position caps and tighter risk guards.
- Hard Exchange Filters: NEVER buy Z-category or SPOT settlement stocks.
- Verified DSE Schedule: Sunday–Thursday (`10:00–14:00` Continuous, `14:00–14:10` Post-Closing exact LTP only, `14:10` Market Close).
- Two-Stage Graduation: Stage 1 (`SHADOW_DUMMY`) feeds local simulator with 0 real BDT risk; Stage 2 (`TRADEXPRESS_LIVE`) requires explicit operator graduation with mandatory 2-step limit order confirmation (`New Order` -> read-back verify -> `Confirm Order`).
- Master Blueprint: Refer to `documentation/TRADEXPRESS_CONTEXT.md` for verified Ember.js DOM selectors, dual WebSockets, and operational protocol.


