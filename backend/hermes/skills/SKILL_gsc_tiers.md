# SKILL: Big Giant Stable (GSC) 3-Tier Watchlist Methodology
Version: 1.1.0
Tags: gsc, watchlist, tier, allocation, trends, momentum, scalp, observation

## 1. Core Philosophy
The DSE has high volatility and regulatory halts. Stocks are segregated into three distinct risk and execution confidence tiers:

### 1. Giant Stable Companies (GSC — Master Observation Pool)
- **Profile:** Master observation pool of established, long-surviving giant companies with proven operating records (`ACI`, `BANKASIA`, `DHAKABANK`, `FUWANGCER`, `IFIC`, `NPOLYMER`, `PRIMEBANK`, `PUBALIBANK`, `SPCERAMICS`).
- **Domain Meaning:** Being in GSC signifies long-term survival stability and fundamental resilience, NOT that the company is currently on a profit curve.
- **Trading Rules:** Hermes observes, tracks, and analyzes all GSC stocks to build continuous market intelligence. However, `AutoTrader` does NOT auto-buy from the base GSC observation pool (`WAIT_OBSERVATION_ONLY`) unless a stock is actively promoted to `GSC_L1` or `GSC_L2`.

### 2. GSC Upper Trends L1 (GSC_L1 — Primary Active Trading List)
- **Profile:** GSC companies that were previously in a downward curve and are now visibly turning upward on their genuine company recovery curve.
- **Noise Filter:** Strictly filters out 1-day market noise (where the market is red today, green tomorrow) to capture sustained recovery momentum.
- **Active Members:** `BANKASIA`, `MATINSPINN`.
- **Trading Rules:** Highest buy priority in `AutoTrader` evaluation cycles.

### 3. GSC Upper Trends L2 (GSC_L2 — Secondary Active Trading List / Fluctuation Scalp)
- **Profile:** GSC companies whose macro curve is not yet fully stabilized, but are turning green in short-term oscillation (e.g. `DHAKABANK`).
- **Tactics:** High-frequency / swing fluctuation scalp. Buy as green momentum starts coming out of support, and sell in tiered slices while still green to profit from market fluctuation before momentum fades.
- **Active Members:** `DHAKABANK`.
- **Trading Rules:** Evaluated by `AutoTrader` second, after `GSC_L1` opportunities are satisfied.
