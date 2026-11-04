# SKILL: 90/10 Canary Probe & Insolvency Threat Quarantine
Version: 1.0.0
Tags: canary, threat, insolvency, bankruptcy, deulia, khoti, quarantine, emergency, 90_10

## 1. Trigger Conditions
When an operator reports insider intelligence, severe operational damage, or impending company collapse (e.g. *"Ajke ei company-r khoti hoyeche, 1 month e deulia hoye jabe"*):

## 2. Immediate Procedural Actions
1. **Crash Quarantine:**
   - Mark the symbol `quarantined = True`.
   - Strictly prohibit any new automated or scheduled purchases.
2. **Emergency Profit-Lock (90% Liquidation):**
   - If open lots currently have net positive unrealized P/L (after 1% fees), immediately sell 90% of total shares.
   - Lock in all accrued capital before any sudden free-fall or floor-price lock occurs.
3. **10% Canary Observation Probe:**
   - Retain exactly 10% of shares (minimum 1 share) in portfolio.
   - Purpose: Real-world observation probe to test the operator's hypothesis over future sessions.
4. **Strict No-Loss Guard:**
   - If open lots are currently at an unrealized loss, do NOT panic-sell. Quarantine future buys and hold as Canary probe.
5. **Multi-Session Verification & Proactive Reporting:**
   - Track price across subsequent market sessions.
   - If price drops >= 8%: Mark `CONFIRMED_LOSS`. Report: *"আপনার সতর্কবার্তা সত্যি প্রমাণিত হয়েছে; ৯০% বিক্রি করে ক্যাপিটাল রক্ষা করা হয়েছে।"*
   - If price stabilizes or gains across >= 3 sessions: Mark `FALSE_ALARM_STABLE`. Proactively suggest: *"কোম্পানিটি এখনো ভালো করছে; আপনি চাইলে আমরা কোয়ারেন্টাইন রিস্টোর করতে পারি।"*

