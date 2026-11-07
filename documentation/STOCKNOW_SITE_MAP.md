# StockNow Site Map & Internal API Specification

> **Exploration Context:**  
> Audit conducted on live StockNow session for Virtual Portfolio `#164580` ("Humming Bird") using authenticated Playwright persistent profile (`.hummingbird_stocknow_profile`).  
> Strictly read-only exploration (zero mutating requests, zero Buy/Sell/Delete executions). Auth tokens and PII are redacted.

---

## 1. Per-Page Breakdown

| Page Path | Purpose | Logged-in vs Logged-out Signal | Stable DOM Selectors | Primary XHR Calls Made |
|:---|:---|:---|:---|:---|
| `/` | Live Market Overview & Indices | Presence of profile avatar vs "Login" button (`a[href*="/login"]`) | `ion-grid`, `.price-table`, `ion-segment` | `GET /api/v1/instruments`<br>`GET /api/v1/config`<br>`GET /api/v1/sectors` |
| `/portfolios` | Portfolio Directory | Lists user portfolios; redirect to `/login` if unauthenticated | `.portfolio-card`, `ion-item`, `a[href*="/portfolios/"]` | `GET /api/v1/user/portfolios` |
| `/portfolios/164580/show` | Active Virtual Portfolio Cockpit | Shows portfolio balance, scrip breakdown table, gain/loss metrics | `.portfolio-detail`, `.scrip-item`, `button:has-text("Buy")` | `GET /api/v1/user/portfolios/164580`<br>`GET /api/v1/instruments` |
| `/portfolios/164580/ledger` | FIFO Realized Accounting Ledger | Detailed closed trade lots and cash flow history | `.ledger-table`, `.transaction-row`, `.filter-segment` | `GET /api/v1/user/portfolios/164580/ledger` |
| `/portfolios/164580/buy` | Manual Order Entry: Buy | Scrip search input, quantity, price, date picker, submit button | `input[name="scrip_id"]`, `input[name="no_of_shares"]`, `input[name="buying_price"]` | `GET /api/v1/instruments`<br>`POST /api/v1/user/portfolios/164580` *(on save)* |
| `/portfolios/164580/sell` | Position Exit Form: Sell | Holding selection, sell lot quantity, sell execution price | `select[name="scrip_id"]`, `input[name="no_of_shares"]`, `input[name="buying_price"]` | `GET /api/v1/user/portfolios/164580`<br>`POST /api/v1/user/portfolios/164580` *(on save)* |
| `/favorites` | Watchlist Multi-Tier Manager | Segment bar with 3 custom tiers (GSC, L1, L2) | `ion-segment-button`, `.favorite-item`, `ion-reorder-group` | `GET /api/v1/user/lists`<br>`GET /api/v1/instruments` |
| `/top-shares` | Gainers, Losers, Turnover Leaders | Tabs: Top Gainers, Losers, Most Active, Volume | `ion-segment`, `.top-share-row`, `ion-badge` | `GET /api/v1/instruments`<br>`GET /api/v1/sectors` |
| `/news` | Exchange Disclosures & Corporate News | Chronological news feed items with scrip tags | `.news-card`, `ion-card-title`, `ion-note` | `GET /api/v1/news`<br>`GET /api/v1/instruments` |
| `/user` | Operator Account & Subscription Profile | Displays user name, mobile `+8801XXXXXXXXX`, and VIP status | `.profile-card`, `ion-button:has-text("Logout")` | `GET /api/v1/user` |

---

## 2. API Contract Specification

All authenticated requests include:
- `Accept: application/json`
- `Authorization: Bearer <access_token>`

### 2.1 `GET /api/v1/user`
Retrieves authenticated operator profile and account validity.
- **Method:** `GET`
- **Path:** `/api/v1/user`
- **Response Shape & Sample:**
```json
{
  "id": 202083,
  "name": "Operator",
  "email": "operator@example.com",
  "contact_no": "+8801XXXXXXXXX",
  "created_at": "2024-01-15 12:30:00",
  "expired_at": "2027-11-05 00:00:00",
  "recommended_coupon": null
}
```

### 2.2 `GET /api/v1/user/lists`
Fetches operator custom watchlists including Giant Stable Companies (GSC), GSC Upper Trends L1, and GSC Upper Trends L2.
- **Method:** `GET`
- **Path:** `/api/v1/user/lists`
- **Response Shape & Sample:**
```json
[
  {
    "id": 573287,
    "name": "Giant Stable Companies",
    "user_id": 202083,
    "order": 1,
    "items": [
      { "id": 21130146, "watchlist_id": 573287, "code": "ACI" },
      { "id": 21130147, "watchlist_id": 573287, "code": "BRACBANK" },
      { "id": 21130148, "watchlist_id": 573287, "code": "GP" },
      { "id": 21130149, "watchlist_id": 573287, "code": "SQURPHARMA" }
    ]
  },
  {
    "id": 573288,
    "name": "GSC Upper Trends L1",
    "user_id": 202083,
    "order": 2,
    "items": [
      { "id": 21130155, "watchlist_id": 573288, "code": "SQURPHARMA" },
      { "id": 21130156, "watchlist_id": 573288, "code": "GP" }
    ]
  },
  {
    "id": 573289,
    "name": "GSC Upper Trends L2",
    "user_id": 202083,
    "order": 3,
    "items": [
      { "id": 21130160, "watchlist_id": 573289, "code": "BRACBANK" }
    ]
  }
]
```

### 2.3 `GET /api/v1/user/portfolios`
Lists available user portfolios.
- **Method:** `GET`
- **Path:** `/api/v1/user/portfolios`
- **Response Sample:**
```json
[
  {
    "id": 164580,
    "user_id": 202083,
    "portfolio_name": "Humming Bird",
    "portfolio_value": 75000.0,
    "cash_amount": 25000.0
  }
]
```

### 2.4 `GET /api/v1/user/portfolios/{id}`
Live portfolio breakdown for portfolio `164580`.
- **Method:** `GET`
- **Path:** `/api/v1/user/portfolios/164580`
- **Response Sample:**
```json
{
  "id": 164580,
  "portfolio_name": "Humming Bird",
  "portfolio_value": 75000.0,
  "cash_amount": 25000.0,
  "scrips": [
    {
      "id": 412093,
      "portfolio_id": 164580,
      "instrument_id": 105,
      "code": "SQURPHARMA",
      "no_of_shares": 100,
      "buying_price": 215.4,
      "buying_date": "2026-11-04",
      "commission": 0.5
    }
  ]
}
```

### 2.5 `GET /api/v1/user/portfolios/{id}/ledger`
Closed trade history and cash transactions.
- **Method:** `GET`
- **Path:** `/api/v1/user/portfolios/164580/ledger`
- **Response Sample:**
```json
{
  "id": 164580,
  "portfolio_name": "Humming Bird",
  "cash_amount": 25000.0,
  "broker_fee": 0.5,
  "transactions": [
    {
      "id": 98214,
      "type": "SELL",
      "code": "GP",
      "no_of_shares": 50,
      "price": 284.5,
      "fee": 71.12,
      "net_pnl": 420.5,
      "date": "2026-11-02"
    }
  ]
}
```

### 2.6 `GET /api/v1/instruments`
Complete live DSE scrip ticker catalog.
- **Method:** `GET`
- **Path:** `/api/v1/instruments`
- **Response Structure (Sample Instrument Entry):**
```json
{
  "SQURPHARMA": {
    "id": 105,
    "code": "SQURPHARMA",
    "name": "Square Pharmaceuticals PLC",
    "ltp": 216.8,
    "high": 218.0,
    "low": 215.2,
    "close": 216.8,
    "ycp": 215.4,
    "change": 1.4,
    "change_per": 0.65,
    "volume": 284500,
    "value": 61.68,
    "trade": 1420,
    "sector_id": 12,
    "updated_at": "2026-11-05 14:30:00"
  }
}
```

### 2.7 `GET /api/v1/sectors` & `GET /api/v1/config`
- `GET /api/v1/sectors`: Sector dictionary mapping numeric sector IDs to descriptions (Pharmaceuticals, Banking, Telecommunication, Engineering, etc.).
- `GET /api/v1/config`: Client configuration constants, banner triggers, websocket enabled flag (`"useWbSocket": true`).

---

## 3. Chart Historical Candles & WebSocket Feed

### 3.1 Historical Daily Candles Endpoint
- **URL:** `GET https://stocknow.com.bd/api/v1/instruments/{symbol}/history?data2=true&resolution=1D&skip=0`
- **Response Schema:**
```json
[
  [1730073600, 214.5, 217.0, 214.0, 216.2, 312000],
  [1730160000, 216.2, 218.5, 215.8, 217.4, 289000],
  [1730246400, 217.4, 219.0, 216.5, 216.8, 245000]
]
```
*Tuple Schema:* `[timestamp_epoch_sec, open, high, low, close, volume]`

### 3.2 WebSocket Architecture & `TradeUpdate` Payload
- **Socket Server:** Socket.IO server at `https://ws.stocknow.com.bd`
- **Event Mapping:**
  - `join`: `"j"` (subscribe to scrip or room)
  - `leave`: `"l"` (unsubscribe)
  - `tradeSummary`: `"TradeUpdate"` (live tick updates)
  - `marketDepth`: `"d"` (top 5 buy/sell order book)
- **Sample `TradeUpdate` Payload:**
```json
{
  "c": "SQURPHARMA",
  "ltp": 216.8,
  "cp": 0.65,
  "ch": 1.4,
  "v": 284500,
  "t": 1730246400
}
```

---

## 4. Authentication Audit

| Property | Value / Verification |
|:---|:---|
| **Login Request Endpoint** | `POST https://stocknow.com.bd/api/v1/auth/login` |
| **Login Request Payload** | `{"username": "+8801XXXXXXXXX", "password": "[REDACTED]"}` |
| **Login Response** | `{"token_type": "Bearer", "expires_in": 31536000, "access_token": "[REDACTED]", "refresh_token": null}` |
| **JWT Expiration Lifetime** | **31,536,000 seconds (365 days / 1 full year)**. Decoded payload contains `iat`, `exp`, `jti`, `sub`, `scopes`. |
| **LocalStorage Keys** | `access_token`, `rememberCredentials`, `username`, `password`, `cached_favorites_202083`, `cached_instruments`, `cached_sectors`, `cached_user_info`, `darkMode`, `fundamentals`, `fundamentals-hash`, `stocknowAdvancedChartSettings`, `stocknow_banner_first_place_v1`, `stocknow_last_feature_intent`, `stocknow_usage_session_id`, `tvlocalstorage.available` |
| **"Remember mobile and password" plain text storage** | **YES**. When "Remember mobile and password" is enabled, `localStorage.setItem("password", this.password)` executes, saving the operator's cleartext password directly in browser localStorage. |

---

## 5. Buy & Sell Save API Signatures (from Disassembled JS)

Both `/buy` and `/sell` Vue components intercept form submission with `e.preventDefault()` and execute XHR POST requests to the portfolio endpoint:

### 5.1 Buy Save Request
- **Endpoint:** `POST https://stocknow.com.bd/api/v1/user/portfolios/164580`
- **Headers:** `Authorization: Bearer <access_token>`, `Content-Type: application/json`
- **Payload Structure:**
```json
{
  "actions": ["Buy"],
  "scrip_id": ["SQURPHARMA"],
  "commission": [0.5],
  "instrument_ids": [105],
  "no_of_shares": [100],
  "buying_price": [215.4],
  "buying_date": ["2026-11-08"]
}
```

### 5.2 Sell Save Request
- **Endpoint:** `POST https://stocknow.com.bd/api/v1/user/portfolios/164580`
- **Headers:** `Authorization: Bearer <access_token>`, `Content-Type: application/json`
- **Payload Structure:**
```json
{
  "broker_fee": 0.5,
  "actions": ["Sell"],
  "scrip_id": ["SQURPHARMA"],
  "commission": [0.5],
  "no_of_shares": [25],
  "buying_price": [220.0],
  "buying_date": ["2026-11-08"]
}
```
*(Note: StockNow reuses `"buying_price"` key for the executed sell price in sell actions).*

---

## 6. Risks and Unknowns

1. **Single-Device Session Eviction:**
   - StockNow sessions can be evicted if logged in from an alternate mobile app or browser session. A background heartbeat check is recommended before executing trades.
2. **Cleartext Password in LocalStorage:**
   - Because `rememberCredentials: true` writes the plaintext password to `localStorage.password`, any XSS vulnerability or extension on the client host poses a credential leak risk.
3. **DSE Market Hours & Latency Spikes:**
   - Market session runs 10:00 AM – 2:30 PM (Sunday–Thursday). During peak open (10:00–10:15 AM), StockNow API responses can exhibit latency up to 3.5 seconds; caching with local stale-while-revalidate is mandatory.
4. **Rate Limiting & IP Blocking:**
   - Requests exceeding 2 req/sec risk temporary IP throttling or Cloudflare challenges. The Cockpit must strictly adhere to rate limits ($\ge 1.0$s interval).
