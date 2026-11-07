# StockNow Read-Only curl & Network Audit

**Audit Date:** November 07, 2026  
**Auditor:** Humming Bird Systems / Real-Hermes Autonomous Agent  
**Target:** `https://www.stocknow.com.bd`  
**Execution Constraints:** Read-only (`GET` and `HEAD` only), rate limit $\le 1$ req/sec, zero credentials transmitted, strict adherence to `robots.txt`, no speculative probing.

---

## 1. Endpoint Fetch Audit Table

All endpoints were audited via non-intrusive `curl -sS -D <headers> -o <body>` commands with a minimum 1.5-second pacing between requests.

| Target URL | HTTP Status | Redirects | Content-Type | Content-Length | Server | ETag | Cache-Control / Expires | Set-Cookie Flags |
|---|:---:|:---:|---|:---:|---|---|---|---|
| `https://www.stocknow.com.bd/` | `200 OK` | `None` | `text/html` | 4,251 bytes | `nginx/1.22.0` | `"6ae81001-109b"` | `max-age=1800, public, no-transform` (Expires: +30m) | *None* |
| `https://www.stocknow.com.bd/login` | `200 OK` | `None` | `text/html` | 4,251 bytes | `nginx/1.22.0` | `"6ae81001-109b"` | `max-age=1800, public, no-transform` (Expires: +30m) | *None* |
| `https://www.stocknow.com.bd/favorites` | `200 OK` | `None` | `text/html` | 4,251 bytes | `nginx/1.22.0` | `"6ae81001-109b"` | `max-age=1800, public, no-transform` (Expires: +30m) | *None* |
| `https://www.stocknow.com.bd/top-shares` | `200 OK` | `None` | `text/html` | 4,251 bytes | `nginx/1.22.0` | `"6ae81001-109b"` | `max-age=1800, public, no-transform` (Expires: +30m) | *None* |
| `https://www.stocknow.com.bd/news` | `200 OK` | `None` | `text/html` | 4,251 bytes | `nginx/1.22.0` | `"6ae81001-109b"` | `max-age=1800, public, no-transform` (Expires: +30m) | *None* |
| `https://www.stocknow.com.bd/robots.txt` | `200 OK` | `None` | `text/plain` | 69 bytes | `nginx/1.22.0` | `"6ae81000-45"` | `max-age=1800, public, no-transform` (Expires: +30m) | *None* |

### Raw Header Artifact Sample (`/login`)
```http
HTTP/1.1 200 OK
Server: nginx/1.22.0
Date: Sat, 07 Nov 2026 17:34:25 GMT
Content-Type: text/html
Content-Length: 4251
Last-Modified: Mon, 02 Nov 2026 04:22:25 GMT
Connection: keep-alive
ETag: "6ae81001-109b"
Expires: Sat, 07 Nov 2026 18:04:25 GMT
Cache-Control: max-age=1800
Cache-Control: public, no-transform
Pragma: public
Accept-Ranges: bytes
```

### Robots.txt Analysis
The `robots.txt` payload returned:
```text
User-agent: *
Allow: /

Sitemap: https://stocknow.com.bd/sitemap.xml
```
- **Observations:** StockNow permits global crawling (`User-agent: *`, `Allow: /`). No endpoints or paths are blocked or disallowed.
- **Sitemap:** An XML sitemap is maintained at `https://stocknow.com.bd/sitemap.xml`.

---

## 2. `/login` Form & Authentication Mechanism

### Server-Side Form HTML Inspection
On requesting `GET https://www.stocknow.com.bd/login`, the server response contains **no static HTML form markup**. Like all other routes, it returns the SPA shell:
```html
<!doctype html>
<html lang="en" mode="ios">
  <head>
    ...
    <script defer="defer" src="/js/chunk-vendors.63ce6077.js" type="module"></script>
    <script defer="defer" src="/js/app.cdcacfd3.js" type="module"></script>
  </head>
  <body class="light">
    <noscript><strong>We're sorry but stocknow doesn't work properly without JavaScript enabled. Please enable it to continue.</strong></noscript>
    <div id="app"></div>
  </body>
</html>
```

### Dynamic Component Disassembly (`js/9048.64f7ca9e.js`)
Inspection of the client-side router in `app.cdcacfd3.js` identified that `/login` dynamically lazy-loads Webpack chunk `9048` (`/js/9048.64f7ca9e.js`):
```javascript
{
  path: "/login",
  name: "Login",
  component: (0, I.$V)(() => o.e(9048).then(o.bind(o, 19048))),
  meta: { guest: true }
}
```

Detailed inspection of chunk `9048.64f7ca9e.js` reveals:
1. **Rendered Form Structure:**
   - `<form method="post" action="" @submit="login">`
2. **Form Fields:**
   - **Username / Identifier:** `<ion-input name="mobile" type="text" label="Mobile *" required v-model="mobile">`
     *Note:* While named `mobile`, it accepts phone number or email string.
   - **Password:** `<ion-input name="password" type="password" label="Password *" required v-model="password">`
   - **Remember Credentials:** `<ion-checkbox v-model="rememberCredentials">`
   - **Submit Element:** `<ion-button type="submit">`
3. **Hidden Inputs:** `0` (None). No hidden state fields exist in the form.
4. **CSRF Token:** `None`. No CSRF token input, meta tag, or anti-CSRF request header is utilized.
5. **Submission Type (Classic POST vs. XHR/JSON):**
   - **Pure XHR/JSON Call.**
   - The native form submit event is prevented via `e.preventDefault()`.
   - The login action dispatches an Axios POST request:
     ```javascript
     login(e) {
       e.preventDefault();
       u.A.with(this).post("/auth/login", {
         email: this.mobile,
         password: this.password
       }).then(res => {
         localStorage.setItem("access_token", res.data.access_token);
         u.A.defaults.headers.common["Authorization"] = "Bearer " + localStorage.access_token;
         if (this.rememberCredentials) {
           localStorage.setItem("rememberCredentials", "true");
           localStorage.setItem("username", this.mobile);
           localStorage.setItem("password", this.password);
         } else {
           localStorage.setItem("rememberCredentials", "false");
           localStorage.removeItem("username");
           localStorage.removeItem("password");
         }
         this.$store.dispatch("userInfo").then(() => {
           this.$store.dispatch("loadFavorites");
           this.$router.replace(this.$route.query.nextUrl);
         });
       }).catch(err => {
         alert(err.response.data.error.message);
         this.sent = false;
       });
       this.sent = true;
     }
     ```

---

## 3. Discovered JavaScript Bundles, APIs & WebSocket Endpoints

### Referenced Core JavaScript Bundles
- `/js/chunk-vendors.63ce6077.js` (1.74 MB, vendor libraries: Vue 3, Ionic Vue, Axios, Socket.IO client, Lodash).
- `/js/app.cdcacfd3.js` (722 KB, core application logic, Vuex store, Vue Router, API defaults).
- `/js/9048.64f7ca9e.js` (7.1 KB, login component lazy chunk).

### Base URLs
- **REST API Base URL:** `https://stocknow.com.bd/api/v1`
- **Real-Time WebSocket Server:** `https://ws.stocknow.com.bd`

### Discovered API Endpoints (Read from JS Bundles — Uninvoked)

#### Authentication & Session Management
- `POST /auth/login` — Authenticate credentials (`email`, `password`), returns `{ access_token }`.
- `POST /auth/logout` — Invalidate user session.
- `POST /fcm-token` — Register Google Firebase Cloud Messaging token (`token`) for mobile push notifications.

#### User & Portfolio Data (Requires Bearer Token)
- `GET /user` — Current user profile and subscription entitlements (`VIP`).
- `GET /user/lists` — User watchlist / synchronized favorites.
- `GET /portfolios` — List of user brokerage/paper portfolios.
- `GET /portfolios/:id/ledger` — Detailed ledger entries and cash allocations for portfolio ID.
- `GET /portfolios/:id/show` — Overview of holdings and unrealized P/L.
- `POST /portfolios/new` — Create a new portfolio entity.
- `POST /portfolios/:id/buy` — Record or execute a stock purchase.
- `POST /portfolios/:id/sell` — Record or execute a stock liquidation.
- `PUT /portfolios/:id/edit` — Edit portfolio metadata.
- `GET /portfolio-v2` (and subpaths `/:id`, `/:id/transactions`, `/:id/invoice`) — V2 portfolio management endpoints.

#### Market Data & Instruments (Public Read)
- `GET /instruments` — Complete listing of DSE/CSE trading symbols, latest trade prices, volume, High/Low, change.
- `GET /sectors` — Sector categorizations, weightings, and sector-specific counters.
- `GET /fundamentals-hash` — Hash of current fundamental dataset (cache invalidation).
- `GET /fundamentals?h={hash}` — Detailed company balance sheet, P/E, EPS, dividend history.
- `GET /config` — System parameters, market status flags, announcements.

#### Learning & Courses
- `GET /courses`
- `GET /courses/:id/details`
- `POST /courses/:id/enroll`
- `GET /courses/:id/lessons/:lesson_id`
- `GET /lessons/:id`
- `POST /lessons/:id/complete`
- `POST /lessons/:id/feedback`
- `PUT /enrollments/:id/tracking`

### WebSocket Architecture & Event Protocol
- **Transport:** WebSocket over TLS (`https://ws.stocknow.com.bd`, `transports: ["websocket"]`, `upgrade: false`).
- **Client Protocol:** Socket.IO.
- **Event Mappings:**
  ```javascript
  $eventMappings = {
    join: "j",
    leave: "l",
    marketDepth: "d",
    tradeSummary: "TradeUpdate"
  };
  ```
- **Operational Pattern:**
  - On connection, client joins symbol rooms via `t.emit("j", symbolCode)`.
  - Server streams live ticks via `"TradeUpdate"` and order book levels via `"d"`.
  - When navigating away from a symbol view, client leaves room via `t.emit("l", symbolCode)`.

---

## 4. Page-by-Page Data Rendering Strategy (SSR vs. Client XHR)

| Endpoint | Rendering Method | Data Source & Mechanism |
|---|:---:|---|
| `/` (Home) | **Client-Side XHR / SPA** | Server sends 4,251-byte empty HTML skeleton. Vue mounts into `#app`, dispatches `updateInstruments` to fetch `GET /api/v1/instruments`, caches in browser storage, connects to `https://ws.stocknow.com.bd` for live tick streaming. |
| `/login` | **Client-Side XHR / SPA** | Server sends 4,251-byte empty HTML skeleton. Lazy chunk `9048` dynamically renders the Ionic form. Zero HTML input fields are rendered by the server. |
| `/favorites` | **Client-Side XHR / SPA** | Server sends 4,251-byte empty HTML skeleton. Watchlist rendered dynamically by querying `GET /api/v1/user/lists` (if authenticated with Bearer token) or reading browser `localStorage.favorites`. |
| `/top-shares` | **Client-Side XHR / SPA** | Server sends 4,251-byte empty HTML skeleton. Top gainers/losers/turnover lists are filtered and computed on the client side from the cached/fetched `/instruments` dataset. |
| `/news` | **Client-Side XHR / SPA** | Server sends 4,251-byte empty HTML skeleton. News feed articles fetched via client-side XHR. |
| `/robots.txt` | **Server-Rendered Static** | Pure static text served directly by Nginx (69 bytes). |

---

## 5. Authentication, Sessions & Public Accessibility Summary

### Publicly Accessible (Without Login)
1. **Market Prices & Ticks:** `/` (Home price board, market movers, indices).
2. **Instrument Catalogs:** `GET /api/v1/instruments`, `GET /api/v1/sectors`, `GET /api/v1/config`.
3. **Top Shares & Statistics:** `/top-shares` (gainers, losers, active volume).
4. **Fundamentals:** `/fundamentals-hash`, `/fundamentals?h={hash}`.
5. **News & Static Information:** `/news`, `/about-us`, `/privacy-policy`, `/robots.txt`, `/sitemap.xml`.

### Session-Gated (Requires Authentication)
1. **User Profile & Status:** `GET /api/v1/user` (returns user ID, subscription status, VIP entitlements).
2. **Watchlist Synchronization:** `GET /api/v1/user/lists` (cloud-synced symbol favorites across devices).
3. **Portfolio Management:** `GET /portfolios`, `GET /portfolios/:id/ledger`, `GET /portfolios/:id/show`, `POST /portfolios/new`, `POST /portfolios/:id/buy`, `POST /portfolios/:id/sell`, `PUT /portfolios/:id/edit`.
4. **Push Notification Registration:** `POST /api/v1/fcm-token`.

### Cookie Behavior & Lifetimes
- **Cookie Presence on Audited Endpoints:** `0` (Zero). Neither Nginx nor the SPA server issues any `Set-Cookie` header on static pages or initial unauthenticated requests.
- **Session Mechanism:** StockNow does **not** rely on standard HTTP session cookies (`PHPSESSID`, `JSESSIONID`, or `session`).
- **Token Storage:**
  - Token is transmitted as a JWT string in the JSON response of `POST /api/v1/auth/login`.
  - Stored strictly in browser **`localStorage`** under the key **`access_token`**.
  - All subsequent authorized API requests attach this token via the standard header:
    ```http
    Authorization: Bearer <access_token>
    ```
  - Optional client header attached when premium is active:
    ```http
    VIP: <localStorage.premium>
    ```
- **Lifetime:** Token lifetime is governed by the JWT expiration claim (`exp`) issued by the authentication server rather than browser cookie expiration flags (`Max-Age` / `Expires`).
