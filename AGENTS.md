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


