---
name: gsc_tiers
description: "Big Giant Stable (GSC) 3-Tier Watchlist Methodology for DSE risk, tier hierarchy, and capital allocation."
version: 1.2.0
author: Humming Bird
license: MIT
metadata:
  hermes:
    tags: [gsc, watchlist, tier, allocation, trends, momentum, scalp, observation, dse_risk]
---

# Big Giant Stable (GSC) 3-Tier Watchlist Methodology

## 1. Core Philosophy & Risk Architecture
The Dhaka Stock Exchange (DSE) exhibits high volatility, regulatory circuit interventions, and wide liquidity spreads. To prevent emotional trading, capital entrapment, or catastrophic permanent loss, stocks are strictly segregated into three distinct risk, curve, and execution tiers:

---

### Tier 1: Giant Stable Companies (GSC — Master Observation Pool)
- **Profile:** Master observation pool of established, long-surviving giant companies with proven operating track records and massive fundamental depth (e.g. `WALTONHIL`, `GP`, `ROBI`, `BANKASIA`, `SQURPHARMA`, `ACI`, `DHAKABANK`, `IFIC`, `PUBALIBANK`).
- **Domain Meaning:** Membership in GSC signifies negligible bankruptcy/delisting/vanish risk over multi-year horizons. **Being in GSC does NOT mean the company is currently on a profit curve or safe to buy today.**
- **Trading Rule:** Hermes continuously monitors, tracks, and analyzes all GSC stocks to build market intelligence and detect curve inflections. However, `AutoTrader` **NEVER auto-buys** from the base GSC observation pool (`WAIT_OBSERVATION_ONLY`) unless the stock is actively evaluated and promoted to `GSC_L1` or `GSC_L2`.

---

### Tier 2: GSC Upper Trends L1 (GSC_L1 — Safe Primary Active Buy List, Priority #1)
- **Profile:** High-conviction subset of **GSC** companies whose multi-week and long-term macro curve is visibly turning upward into a genuine company recovery wave (`BANKASIA`, `MATINSPINN`).
- **Noise Filter:** Filters out 1-day market noise (red today, green tomorrow). Short 1-day fluctuations may dip temporarily, but the underlying multi-week momentum provides high confidence of recovery into net profit within T+2 or a few market sessions.
- **Trading Rule:** **Highest buy priority (Priority #1)** in `AutoTrader` evaluation cycles. Receives primary capital allocation.

---

### Tier 3: GSC Upper Trends L2 (GSC_L2 — Risky Short-Term Swing / Scalp List, Priority #2)
- **Profile:** **NOT necessarily GSC** — vetted non-Z (`PUBLIC`, Category A/B) companies emerging from red into early green fluctuation momentum (e.g. `DHAKABANK`).
- **Tactics:** High-frequency / swing fluctuation scalp. Enter early on small initial green momentum coming out of support, and exit quickly in tiered slices on average or modest green gain before momentum fades.
- **Risk Posture:** Inherently higher risk than L1 due to shorter holding horizon and less macro stability.
- **Trading Rule:** **Secondary buy priority (Priority #2)** in `AutoTrader` evaluation cycles. Position sizes are strictly constrained by a **smaller position cap** and tighter preflight risk guard compared to `GSC_L1`.

---

## 2. Hard Exchange Exclusions (Non-Negotiable)
Regardless of tier or technical curve signals, the trading kernel and Hermes must **ALWAYS ENFORCE**:
1. **NEVER BUY Z-CATEGORY:** Junk, distressed, non-compliant, non-dividend-paying companies are strictly blacklisted.
2. **NEVER BUY SPOT SETTLEMENT:** Securities trading on `SPOT` settlement (immediate T+0 cash freeze or corporate action lock) are strictly blocked. All orders must be standard `PUBLIC` settlement.
