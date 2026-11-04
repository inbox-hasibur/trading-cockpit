# SKILL: DSE Latency vs StockNow Real-Time Feed Nuances & Virtual Portfolio
Version: 1.0.0
Tags: stocknow, dse, quirks, latency, virtual, paper, websocket, market_hours

## 1. Exchange Execution Realities
- **DSE Official (`dsebd.org`):** Often experiences 1-3 minute lag during 10:00 AM – 11:30 AM peak market load. HTML scraping triggers frequent IP rate-limits and cloudflare challenges.
- **StockNow (`stocknow.com.bd`):** Fast sub-second JSON/WebSocket feeds providing tick-by-tick DSE updates and consolidated market depth.

## 2. StockNow Virtual Portfolio ("Humming Bird")
- Target execution venue for Phase 1 paper validation.
- All purchases must account for available settled virtual cash and 1% simulated commissions.
- Orders must be tagged with unique idempotency keys to prevent duplicate execution across network retries.

## 3. Market Hours Execution Window
- DSE Working hours: 10:00 AM – 2:30 PM (Asia/Dhaka timezone).
- Sunday through Thursday. Off-hour cycles must run in synthetic demo scenario mode.

