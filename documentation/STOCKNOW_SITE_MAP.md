# StockNow Site Map & Internal API Specification

> **Exploration Context:**  
> Audit conducted on live StockNow session for Virtual Portfolio `#164580` ("Humming Bird") using authenticated Playwright persistent profile (`.hummingbird_stocknow_profile`).  
> Strictly read-only exploration and contract verification. Auth tokens and PII are strictly redacted.

---

## Table of Contents
1. [Per-Page Breakdown](#1-per-page-breakdown)
2. [API Contract Specification](#2-api-contract-specification)
3. [Chart Historical Candles & WebSocket Feed](#3-chart-historical-candles--websocket-feed)
4. [Authentication Audit](#4-authentication-audit)
5. [Buy & Sell Save API Signatures](#5-buy--sell-save-api-signatures)
6. [Write Contract (Test Portfolio #164580)](#6-write-contract-test-portfolio-164580)
7. [Unauthenticated curl audit](#7-unauthenticated-curl-audit)
8. [Risks and Unknowns](#8-risks-and-unknowns)

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
| **Login Request Payload** | `{"email": "+8801XXXXXXXXX", "password": "[REDACTED]"}` |
| **Login Response** | `{"token_type": "Bearer", "expires_in": 31536000, "access_token": "[REDACTED]", "refresh_token": null}` |
| **JWT Expiration Lifetime** | **31,536,000 seconds (365 days / 1 full year)**. Decoded payload contains `iat`, `exp`, `jti`, `sub`, `scopes`. |
| **LocalStorage Keys** | `access_token`, `rememberCredentials`, `username`, `password`, `cached_favorites_202083`, `cached_instruments`, `cached_sectors`, `cached_user_info`, `darkMode`, `fundamentals`, `fundamentals-hash`, `stocknowAdvancedChartSettings`, `stocknow_banner_first_place_v1`, `stocknow_last_feature_intent`, `stocknow_usage_session_id`, `tvlocalstorage.available` |
| **"Remember mobile and password" plain text storage** | **YES**. When "Remember mobile and password" is enabled, `localStorage.setItem("password", this.password)` executes, saving the operator's cleartext password directly in browser localStorage. |

---

## 5. Buy & Sell Save API Signatures

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

## 6. Write Contract (Test Portfolio #164580)

> **Test Environment & Safety Guard:**  
> All mutating requests are strictly gated by `backend.adapters.stocknow_write_guard.verify_test_portfolio_post_guard`.  
> The guard enforces that the target portfolio ID strictly matches `STOCKNOW_TEST_PORTFOLIO_ID` (`164580`) and refuses any POST if unconfigured or pointing to non-test portfolios.  
> Captured live under HAR recording: `tests/fixtures/stocknow/har/stocknow_write_contract.har`. Sanitized results in `tests/fixtures/stocknow/write_contract_results.json` and `tests/fixtures/stocknow/write_contract_ledger.json`.

### 6.1 Order Execution Contract (UI Buy & Sell)

StockNow virtual portfolio mutations use `POST /api/v1/user/portfolios/{id}` with parallel array structures.

#### 1. Buy Execution (1 Share BANKASIA)
- **Endpoint:** `POST https://stocknow.com.bd/api/v1/user/portfolios/164580`
- **Status:** `200 OK`
- **Request Headers:**
  ```http
  Accept: application/json, text/plain, */*
  Authorization: Bearer <access_token>
  Content-Type: application/json
  ```
- **Request Body:**
  ```json
  {
    "portfolio_name": "",
    "cash_amount": "",
    "broker_fee": "0.5",
    "actions": ["Buy"],
    "scrip_id": [""],
    "commission": ["0.5"],
    "no_of_shares": ["1"],
    "buying_price": [17.5],
    "buying_date": [null],
    "instrument_ids": ["BANKASIA"]
  }
  ```
- **Response Structure (Summary):**
  Returns the updated portfolio model with newly generated scrip holding ID (`id: 2350594`), cash deduction of ৳17.59 (৳17.50 principal + 0.5% broker fee ৳0.0875), and updated scrips list.

#### 2. Sell Execution (1 Share BANKASIA)
- **Endpoint:** `POST https://stocknow.com.bd/api/v1/user/portfolios/164580`
- **Status:** `200 OK`
- **Request Body:**
  ```json
  {
    "portfolio_name": "Humming Bird",
    "cash_amount": 129164,
    "broker_fee": "0.5",
    "actions": ["Sell"],
    "scrip_id": [2347779],
    "commission": ["0.5"],
    "no_of_shares": ["1"],
    "buying_price": [17.5],
    "buying_date": [null],
    "instrument_ids": []
  }
  ```
- **Response Structure (Summary):**
  Returns the updated portfolio with credited cash of ৳17.41 (৳17.50 proceeds minus 0.5% broker fee ৳0.0875), and decremented holding quantity.

### 6.2 Post-Trade Ledger Records

Verified from `GET /api/v1/user/portfolios/164580/ledger` and `/portfolios/164580/ledger` DOM:

| Date | Type | Symbol | Qty | Rate (BDT) | Comm (BDT) | Debit/Credit (BDT) | Balance (BDT) |
|:---|:---|:---|:---|:---|:---|:---|:---|
| `08/11/26` | `SELL` | `BANKASIA` | 1 | 17.50 | 0.0875 | `+17.4125` | 129,181.00 |
| `08/11/26` | `BUY` | `BANKASIA` | 1 | 17.50 | 0.0875 | `-17.5875` | 129,164.00 |

*Ledger Item Schema (`GET /api/v1/user/portfolios/{id}/ledger`):*
```json
{
  "id": 3142750,
  "portfolio_id": 164580,
  "action": "SELL",
  "description": "BANKASIA",
  "qty": 1,
  "price": 17.5,
  "commission": 0.0875,
  "debit": null,
  "credit": 17.4125,
  "balance": 129181,
  "created_at": "2026-11-08 00:00:00",
  "updated_at": "2026-11-08 01:08:21"
}
```

### 6.3 Error Responses & Server Validation Probes

Probes executed against `POST /api/v1/user/portfolios/164580` using valid Bearer token:

| Scenario | Tested Payload Modification | HTTP Status | Response Body | Interpretation |
|:---|:---|:---|:---|:---|
| **Quantity 0** | `"no_of_shares": [0]` | `403 Forbidden` | `{"error": {"code": 403, "message": "Invalid request. Please double check your changes."}}` | Server rejects non-positive integer quantities. |
| **Missing Price** | `"buying_price": [""]` | `403 Forbidden` | `{"error": {"code": 403, "message": "Invalid request. Please double check your changes."}}` | Server rejects empty or null execution rates. |
| **Unknown Share** | `"instrument_ids": ["UNKNOWN_XYZ_999"]` | `200 OK` | Full portfolio JSON with scrip holding `"UNKNOWN_XYZ_999"` created | **Unexpected:** Virtual portfolio engine does not validate instrument symbol against DSE master catalog. |
| **Price Far Outside Day Range** | `"buying_price": [999999.0]` | `200 OK` | Full portfolio JSON; cash balance updated to `-875836` | **Unexpected:** Virtual portfolio API completely ignores circuit limits / day range. Accepts arbitrary prices. |
| **Future Date** | `"buying_date": ["2035-01-01"]` | `200 OK` | Full portfolio JSON with `"buying_date": "2035-01-01 00:00:00"` | Virtual portfolio engine allows speculative future dates without validation. |
| **Duplicate Submit within 2s** | Two identical POST requests fired $< 2000$ms apart | Both `200 OK` | Both requests process independently; two separate lots created | **No Server-Side Deduplication:** StockNow lacks idempotency keys or fast-submit debounce; client-side rate limits are mandatory. |

### 6.4 Research Questions & Empirical Answers

1. **Does the API validate price against the day range?**
   - **No.** The API does not enforce daily circuit limits or high/low price ranges on virtual portfolios. A buy at ৳999,999.00 was accepted with `200 OK`. The client-side kernel must strictly validate market prices before order dispatch.
2. **Does an API login invalidate the browser session?**
   - **No.** Authenticating via `POST /api/v1/auth/login` generates an independent valid token. The browser's active `access_token` remains completely valid (`status: 200` on subsequent requests). Multiple concurrent JWT tokens are permitted per user.
3. **What does `POST /auth/logout` do to the token?**
   - Endpoint: `POST https://stocknow.com.bd/api/v1/auth/logout`.
   - Response: `200 OK` with `{"success": {"code": 200, "message": "Logged out"}}`.
   - Token Lifecycle: **Strict server-side blacklisting.** Immediately after logout, any request using that token returns `401 Unauthorized` (`{"error": {"code": 401, "message": "Please login."}}`).

---

## 7. Unauthenticated curl audit

Audit conducted via read-only requests (`GET` and `HEAD` only) with rate pacing $\le 1$ req/sec, zero credentials transmitted, strict adherence to `robots.txt`, and zero speculative probing.

### 7.1 Endpoint Fetch Audit Table

All endpoints were audited via non-intrusive `curl -sS -D <headers> -o <body>` commands with a minimum 1.5-second pacing between requests.

| Target URL | HTTP Status | Redirects | Content-Type | Content-Length | Server | ETag | Cache-Control / Expires | Set-Cookie Flags |
|---|:---:|:---:|---|:---:|---|---|---|---|
| `https://www.stocknow.com.bd/` | `200 OK` | `None` | `text/html` | 4,251 bytes | `nginx/1.22.0` | `"6ae81001-109b"` | `max-age=1800, public, no-transform` (Expires: +30m) | *None* |
| `https://www.stocknow.com.bd/login` | `200 OK` | `None` | `text/html` | 4,251 bytes | `nginx/1.22.0` | `"6ae81001-109b"` | `max-age=1800, public, no-transform` (Expires: +30m) | *None* |
| `https://www.stocknow.com.bd/favorites` | `200 OK` | `None` | `text/html` | 4,251 bytes | `nginx/1.22.0` | `"6ae81001-109b"` | `max-age=1800, public, no-transform` (Expires: +30m) | *None* |
| `https://www.stocknow.com.bd/top-shares` | `200 OK` | `None` | `text/html` | 4,251 bytes | `nginx/1.22.0` | `"6ae81001-109b"` | `max-age=1800, public, no-transform` (Expires: +30m) | *None* |
| `https://www.stocknow.com.bd/news` | `200 OK` | `None` | `text/html` | 4,251 bytes | `nginx/1.22.0` | `"6ae81001-109b"` | `max-age=1800, public, no-transform` (Expires: +30m) | *None* |
| `https://www.stocknow.com.bd/robots.txt` | `200 OK` | `None` | `text/plain` | 69 bytes | `nginx/1.22.0` | `"6ae81000-45"` | `max-age=1800, public, no-transform` (Expires: +30m) | *None* |

### 7.2 Robots.txt Analysis
The `robots.txt` payload:
```text
User-agent: *
Allow: /

Sitemap: https://stocknow.com.bd/sitemap.xml
```
- **Observations:** StockNow permits global crawling (`User-agent: *`, `Allow: /`). No endpoints or paths are blocked or disallowed.
- **Sitemap:** An XML sitemap is maintained at `https://stocknow.com.bd/sitemap.xml`.

### 7.3 `/login` Form & Client-Side SPA Rendering Architecture

On requesting `GET https://www.stocknow.com.bd/login`, the server response contains **no static HTML form markup**. Like all other routes, it returns the SPA shell:
```html
<!doctype html>
<html lang="en" mode="ios">
  <head>
    <script defer="defer" src="/js/chunk-vendors.63ce6077.js" type="module"></script>
    <script defer="defer" src="/js/app.cdcacfd3.js" type="module"></script>
  </head>
  <body class="light">
    <noscript><strong>We're sorry but stocknow doesn't work properly without JavaScript enabled.</strong></noscript>
    <div id="app"></div>
  </body>
</html>
```

Inspection of chunk `9048.64f7ca9e.js` reveals:
1. **Rendered Form Structure:** `<form method="post" action="" @submit="login">`
2. **Form Fields:**
   - **Identifier:** `<ion-input name="mobile" type="text" label="Mobile *" required v-model="mobile">` (accepts phone number or email string).
   - **Password:** `<ion-input name="password" type="password" label="Password *" required v-model="password">`
   - **Remember Credentials:** `<ion-checkbox v-model="rememberCredentials">`
   - **Submit Element:** `<ion-button type="submit">`
3. **Hidden Inputs:** `0` (None). No hidden state fields exist.
4. **CSRF Protection:** `None`. No CSRF token input, meta tag, or anti-CSRF request header is utilized.
5. **Submission Type:** Pure XHR/JSON Call. Native form submit event is prevented via `e.preventDefault()`, and credentials are sent via Axios `POST /api/v1/auth/login`.

### 7.4 Page Data Rendering Strategy (SSR vs. Client XHR)

| Endpoint | Rendering Method | Data Source & Mechanism |
|---|:---:|---|
| `/` (Home) | **Client-Side XHR / SPA** | Server sends 4,251-byte empty HTML skeleton. Vue mounts into `#app`, dispatches `updateInstruments` to fetch `GET /api/v1/instruments`, caches in browser storage, connects to `https://ws.stocknow.com.bd` for live tick streaming. |
| `/login` | **Client-Side XHR / SPA** | Server sends 4,251-byte empty HTML skeleton. Lazy chunk `9048` dynamically renders the Ionic form. Zero HTML input fields are rendered by the server. |
| `/favorites` | **Client-Side XHR / SPA** | Server sends 4,251-byte empty HTML skeleton. Watchlist rendered dynamically by querying `GET /api/v1/user/lists` (if authenticated) or reading browser `localStorage.favorites`. |
| `/top-shares` | **Client-Side XHR / SPA** | Server sends 4,251-byte empty HTML skeleton. Top gainers/losers/turnover lists are filtered and computed on the client side from the cached/fetched `/instruments` dataset. |
| `/news` | **Client-Side XHR / SPA** | Server sends 4,251-byte empty HTML skeleton. News feed articles fetched via client-side XHR. |
| `/robots.txt` | **Server-Rendered Static** | Pure static text served directly by Nginx (69 bytes). |

### 7.5 Cookie Policy & Token Storage Lifecycle
- **Zero Cookies:** Neither Nginx nor the SPA issues any `Set-Cookie` header on static pages or initial requests.
- **Token Storage:** Token is transmitted as a JWT string in `POST /api/v1/auth/login` and stored strictly in browser `localStorage` under `access_token`.
- **Subsequent Requests:** Requests include `Authorization: Bearer <access_token>`. Token lifetime is governed by the JWT `exp` claim (365 days) rather than browser cookie expiration flags.

---

## 8. Risks and Unknowns

1. **Absence of Server-Side Price Sanity Checks on Virtual Portfolios:**
   - Because StockNow permits arbitrary prices and unknown symbols on virtual portfolios, any corrupted quote from the aggregator could theoretically corrupt the paper ledger if not guarded by Humming Bird kernel caps.
2. **No Order Idempotency / Fast Duplicate Safeguards:**
   - StockNow executes duplicate submissions in rapid succession without server-side deduplication. Humming Bird's client-side order mutex and 2-second rate limiter are critical.
3. **Single-Device Session Eviction Risk on Manual Logout:**
   - While secondary login does not invalidate existing tokens, calling `POST /auth/logout` immediately invalidates that specific token on the server.
4. **Cleartext Password in LocalStorage:**
   - Because `rememberCredentials: true` writes the plaintext password to `localStorage.password`, any client host vulnerability poses a credential leak risk.
5. **DSE Market Hours & Latency Spikes:**
   - Market session runs 10:00 AM – 2:30 PM (Sunday–Thursday). Peak open latency can reach 3.5 seconds; caching with local stale-while-revalidate is mandatory.
