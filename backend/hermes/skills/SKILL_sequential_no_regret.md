# SKILL: Sequential No-Regret Selling & T+2 3-Bucket Rolling Ledger
Version: 1.0.0
Tags: sequential, selling, tiers, profit, pullback, 50_50, t2, buckets, fees, no_loss

## 1. DSE Settlement Mechanics & Rolling Capital
- DSE trading days: Sunday through Thursday (Friday & Saturday closed).
- Settlement: T+2 working sessions.
- Rolling Capital: Capital is partitioned into 3 rolling buckets (Bucket A, B, C) so matured inventory is available on rotating days.

## 2. Brokerage Fee Hurdle
- ~1.00% round-trip brokerage commission (~0.5% on Buy + ~0.5% on Sell).
- Break-even price requires at least +1.005% gross gain.
- All evaluation tiers evaluate TRUE NET PROFIT % after deducting both buy and sell commissions.

## 3. Sequential No-Regret Selling
To eliminate the regret of selling too early or selling too late:
- **Tier 1 (+1.5% Net):** Sell 25% of starting lot shares.
- **Tier 2 (+3.5% Net):** Sell 25% of starting lot shares.
- **Tier 3 (+6.0% Net):** Sell 25% of starting lot shares.
- **Runner (25%):** Let the final slice run for major multi-week rallies.

## 4. 50/50 Pullback Split & Recovery Anchor
- Track the peak price (High-Water Mark) of each lot.
- When price drops >= 3% from peak while still in net profit:
  - Immediately sell 50% of remaining shares to secure profit.
  - Retain the other 50% in `RECOVERY_HOLD`.
  - Once price climbs back above the anchor price, sequential selling rules restart!

