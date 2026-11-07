"""StockNow Async API Client (HTTPX).

Implements the StockNow REST contract per documentation/STOCKNOW_SITE_MAP.md.
No browser required. Uses memory-only JWT token management, strict rate limiting,
ETag caching, typed error handling, bounded retries with jitter, and idempotent
ledger verification before mutating retries.
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
import time
from typing import Any, Mapping

import httpx
import jwt

from backend.adapters.stocknow_write_guard import (
    StockNowWriteGuardError,
    verify_test_portfolio_post_guard,
)

logger = logging.getLogger(__name__)


class StockNowError(Exception):
    """Base exception for StockNow API errors."""
    pass


class NotAuthenticatedError(StockNowError):
    """Raised on missing credentials, failed login, or persistent 401."""
    pass


class RateLimitedError(StockNowError):
    """Raised on 429 Too Many Requests."""
    pass


class SchemaChangedError(StockNowError):
    """Raised when an API response misses expected fields. Must stop trading."""
    pass


class NetworkError(StockNowError):
    """Raised on transport failures, DNS errors, or timeouts after retries."""
    pass


# Typed aliases required by contract
NOT_AUTHENTICATED = NotAuthenticatedError
RATE_LIMITED = RateLimitedError
SCHEMA_CHANGED = SchemaChangedError
NETWORK = NetworkError


class _RateLimiter:
    """Async token bucket / interval limiter ensuring max 1 req/sec per host."""

    def __init__(self, interval: float = 1.0) -> None:
        self.interval = max(0.0, float(interval))
        self._last_call = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        if self.interval <= 0:
            return
        async with self._lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_call
            if elapsed < self.interval:
                await asyncio.sleep(self.interval - elapsed)
            self._last_call = asyncio.get_event_loop().time()


class StockNowAPI:
    """Async HTTP client for StockNow REST endpoints."""

    def __init__(
        self,
        base_url: str = "https://stocknow.com.bd",
        mobile: str | None = None,
        password: str | None = None,
        timeout: float = 15.0,
        rate_limit_interval: float = 1.0,
        reauth_margin_seconds: float = 300.0,
        max_retries: int = 3,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._mobile = mobile
        self._password = password
        self._timeout = timeout
        self._rate_limiter = _RateLimiter(rate_limit_interval)
        self._reauth_margin_seconds = reauth_margin_seconds
        self._max_retries = max_retries

        # Token state held strictly in memory
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

        # ETag cache for public GET endpoints: url -> (etag_header, cached_json)
        self._etag_cache: dict[str, tuple[str, Any]] = {}

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self._timeout,
            transport=transport,
            headers={
                "User-Agent": "HummingBird-TradingCockpit/1.0",
                "Accept": "application/json",
            },
        )

    async def __aenter__(self) -> StockNowAPI:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close underlying HTTP client and wipe token from memory."""
        self._access_token = None
        self._token_expires_at = 0.0
        await self._client.aclose()

    # -------------------------------------------------------------------------
    # Authentication & Session Management
    # -------------------------------------------------------------------------

    async def login(self) -> str:
        """Authenticate using credentials from environment (or constructor).

        Stores access token strictly in memory.
        """
        mobile = self._mobile or os.getenv("STOCKNOW_MOBILE", "").strip()
        password = self._password or os.getenv("STOCKNOW_PASSWORD", "").strip()

        if not mobile or not password:
            raise NotAuthenticatedError(
                "STOCKNOW_MOBILE or STOCKNOW_PASSWORD credentials not found in environment."
            )

        url = f"{self.base_url}/api/v1/auth/login"
        payload = {"email": mobile, "password": password}

        await self._rate_limiter.acquire()
        try:
            resp = await self._client.post(url, json=payload)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise NetworkError(f"Network failure during login: {exc}") from exc

        if resp.status_code == 429:
            raise RateLimitedError("Login rate limited (HTTP 429)")
        if resp.status_code != 200:
            raise NotAuthenticatedError(
                f"Login failed with HTTP {resp.status_code}: {resp.text[:200]}"
            )

        try:
            data = resp.json()
        except Exception as exc:
            raise SchemaChangedError(f"Login response is not valid JSON: {exc}") from exc

        token = data.get("access_token")
        if not token:
            raise NotAuthenticatedError("Login response missing 'access_token'")

        self._access_token = str(token)

        # Determine expiration: try decoding JWT payload 'exp' without verification
        try:
            decoded = jwt.decode(self._access_token, options={"verify_signature": False})
            exp = float(decoded.get("exp", 0))
            if exp > 0:
                self._token_expires_at = exp
            else:
                expires_in = float(data.get("expires_in", 31536000))
                self._token_expires_at = time.time() + expires_in
        except Exception:
            expires_in = float(data.get("expires_in", 31536000))
            self._token_expires_at = time.time() + expires_in

        return self._access_token

    async def logout(self) -> None:
        """Terminate active session on server and clear token from memory."""
        token = self._access_token
        self._access_token = None
        self._token_expires_at = 0.0

        if not token:
            return

        url = f"{self.base_url}/api/v1/auth/logout"
        await self._rate_limiter.acquire()
        try:
            await self._client.post(
                url,
                headers={"Authorization": f"Bearer {token}"},
            )
        except Exception as exc:
            logger.warning("Error during logout POST: %s", exc)

    async def ensure_authenticated(self) -> str:
        """Ensure a valid, non-expired in-memory JWT token exists."""
        now = time.time()
        if not self._access_token or now >= (self._token_expires_at - self._reauth_margin_seconds):
            return await self.login()
        return self._access_token

    # -------------------------------------------------------------------------
    # Core Request Dispatcher with Idempotency & Jittered Retries
    # -------------------------------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_data: Any = None,
        authenticated: bool = True,
        is_public_get: bool = False,
        is_mutation: bool = False,
        portfolio_id: str | int | None = None,
        expected_items: list[dict[str, Any]] | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        has_reauthed = False

        for attempt in range(self._max_retries + 1):
            headers: dict[str, str] = {
                "Accept": "application/json",
            }

            if is_public_get and method.upper() == "GET":
                cached_etag, _ = self._etag_cache.get(url, ("", None))
                if cached_etag:
                    headers["If-None-Match"] = cached_etag

            if authenticated:
                token = await self.ensure_authenticated()
                headers["Authorization"] = f"Bearer {token}"

            await self._rate_limiter.acquire()

            try:
                resp = await self._client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=headers,
                )
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                # Crucial safety rule: Never retry a buy or sell blindly; check ledger first!
                if is_mutation and portfolio_id:
                    matched = await self._check_ledger_for_trade(portfolio_id, expected_items or [])
                    if matched:
                        return matched

                if attempt >= self._max_retries:
                    raise NetworkError(f"Network error after {self._max_retries} retries: {exc}") from exc

                jitter = random.uniform(0.1, 0.4)
                backoff = (0.5 * (2**attempt)) + jitter
                await asyncio.sleep(backoff)
                continue

            # 401 Unauthorized handling: re-login once
            if resp.status_code == 401:
                if authenticated and not has_reauthed:
                    has_reauthed = True
                    self._access_token = None
                    try:
                        await self.login()
                        continue
                    except Exception as reauth_err:
                        raise NotAuthenticatedError(
                            f"Re-login failed after 401: {reauth_err}"
                        ) from reauth_err
                raise NotAuthenticatedError(f"HTTP 401 Unauthorized for {path}")

            # 429 Rate Limited
            if resp.status_code == 429:
                raise RateLimitedError(f"HTTP 429 Too Many Requests for {path}")

            # 304 Not Modified for cached public GETs
            if resp.status_code == 304 and is_public_get:
                _, cached_json = self._etag_cache.get(url, ("", None))
                if cached_json is not None:
                    return cached_json

            # Server 5xx Transient Errors
            if resp.status_code in (500, 502, 503, 504):
                if is_mutation and portfolio_id:
                    matched = await self._check_ledger_for_trade(portfolio_id, expected_items or [])
                    if matched:
                        return matched

                if attempt >= self._max_retries:
                    raise NetworkError(f"Server error HTTP {resp.status_code} for {path}")

                jitter = random.uniform(0.1, 0.4)
                backoff = (0.5 * (2**attempt)) + jitter
                await asyncio.sleep(backoff)
                continue

            # Handle 403 or other 4xx errors
            if resp.status_code >= 400:
                raise StockNowError(f"StockNow returned HTTP {resp.status_code}: {resp.text[:300]}")

            # 200 OK Response
            try:
                data = resp.json()
            except Exception as exc:
                raise SchemaChangedError(f"Invalid JSON returned from {path}: {exc}") from exc

            # Store ETag if present on public GET
            if is_public_get and "etag" in resp.headers:
                self._etag_cache[url] = (resp.headers["etag"], data)

            return data

        raise NetworkError(f"Request to {path} exhausted all {self._max_retries} retries")

    async def _check_ledger_for_trade(
        self,
        portfolio_id: str | int,
        expected_items: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """Read ledger to verify if an unconfirmed mutation was executed on the server."""
        try:
            ledger_data = await self.get_ledger(portfolio_id)
        except Exception as exc:
            logger.warning("Could not read ledger during idempotent mutation check: %s", exc)
            return None

        ledger_rows = ledger_data.get("ledger") or ledger_data.get("transactions") or []
        if not ledger_rows or not expected_items:
            return None

        matched_count = 0
        for it in expected_items:
            sym = str(it.get("symbol") or it.get("instrument_id") or it.get("code", "")).upper()
            qty = int(it.get("shares") or it.get("qty") or it.get("no_of_shares", 1))

            found = False
            for row in ledger_rows[:5]:
                row_sym = str(row.get("description") or row.get("code") or "").upper()
                row_qty = int(row.get("qty") or row.get("no_of_shares", 0))
                if row_sym == sym and row_qty == qty:
                    found = True
                    break
            if found:
                matched_count += 1

        if matched_count == len(expected_items):
            logger.info("Mutation confirmed via ledger for portfolio %s", portfolio_id)
            return {
                "id": int(portfolio_id),
                "status": "confirmed_via_ledger",
                "scrips": ledger_rows[:len(expected_items)],
            }

        return None

    # -------------------------------------------------------------------------
    # Public Read Endpoints
    # -------------------------------------------------------------------------

    async def get_instruments(self) -> dict[str, Any]:
        """Fetch complete DSE instruments catalog.

        Applies ETag caching. Validates expected schema.
        """
        data = await self._request(
            "GET",
            "/api/v1/instruments",
            authenticated=False,
            is_public_get=True,
        )

        if not isinstance(data, dict):
            raise SchemaChangedError(
                f"Expected dict for instruments catalog, got {type(data).__name__}"
            )

        # Validate presence of instrument symbols with required quote fields
        symbols = [k for k in data.keys() if not k.startswith("_")]
        if not symbols:
            raise SchemaChangedError("Instruments dictionary contains no ticker symbols")

        sample_symbol = symbols[0]
        sample_item = data[sample_symbol]
        if not isinstance(sample_item, dict) or not any(k in sample_item for k in ("ltp", "close", "ycp")):
            raise SchemaChangedError(
                f"Instrument item for '{sample_symbol}' misses required price field ('ltp'/'close'/'ycp')"
            )

        return data

    async def get_lists(self) -> list[dict[str, Any]]:
        """Fetch operator watchlists (GSC, L1, L2). Validates expected schema."""
        data = await self._request("GET", "/api/v1/user/lists", authenticated=True)

        if not isinstance(data, list):
            raise SchemaChangedError(f"Expected list for user watchlists, got {type(data).__name__}")

        for wl in data:
            if not isinstance(wl, dict) or "id" not in wl or "name" not in wl or "items" not in wl:
                raise SchemaChangedError(
                    f"Watchlist item misses expected fields (id, name, items): {wl}"
                )
            if not isinstance(wl["items"], list):
                raise SchemaChangedError(f"Watchlist 'items' must be a list in watchlist {wl.get('id')}")

        return data

    async def get_history(self, symbol: str, sessions: int = 15) -> list[list[Any]]:
        """Fetch daily OHLCV candles for symbol sliced to requested sessions count.

        Schema: returns list of [timestamp, open, high, low, close, volume] tuples.
        """
        sym = str(symbol).strip().upper()
        path = f"/api/v1/instruments/{sym}/history?data2=true&resolution=1D&skip=0"
        data = await self._request("GET", path, authenticated=False, is_public_get=True)

        if not isinstance(data, list):
            raise SchemaChangedError(f"Expected list for history candles, got {type(data).__name__}")

        # StockNow native response: 6 parallel arrays [opens, highs, lows, closes, volumes, timestamps]
        if len(data) == 6 and all(isinstance(sub, list) for sub in data):
            opens, highs, lows, closes, volumes, timestamps = data
            n = min(len(opens), len(highs), len(lows), len(closes), len(volumes), len(timestamps))
            if n == 0:
                return []

            # Slice last N sessions
            start_idx = max(0, n - sessions)
            candles: list[list[Any]] = []
            for i in range(start_idx, n):
                candles.append([
                    timestamps[i],
                    opens[i],
                    highs[i],
                    lows[i],
                    closes[i],
                    volumes[i],
                ])
            return candles

        # Alternative format: list of tuples/lists already transposed
        if all(isinstance(row, (list, tuple)) for row in data):
            return data[-sessions:]

        raise SchemaChangedError(f"Unrecognized history response structure for '{sym}'")

    async def get_portfolio(self, id: str | int) -> dict[str, Any]:
        """Fetch portfolio holdings and cash balance. Validates expected schema."""
        pid = str(id).strip()
        path = f"/api/v1/user/portfolios/{pid}"
        data = await self._request("GET", path, authenticated=True)

        if not isinstance(data, dict):
            raise SchemaChangedError(f"Expected dict for portfolio show, got {type(data).__name__}")

        if "id" not in data or "cash_amount" not in data or "scrips" not in data:
            raise SchemaChangedError(
                f"Portfolio response missing required fields (id, cash_amount, scrips): {list(data.keys())}"
            )

        if not isinstance(data["scrips"], list):
            raise SchemaChangedError(f"Portfolio 'scrips' must be a list: {type(data['scrips']).__name__}")

        return data

    async def get_ledger(self, id: str | int) -> dict[str, Any]:
        """Fetch portfolio ledger transactions. Validates expected schema."""
        pid = str(id).strip()
        path = f"/api/v1/user/portfolios/{pid}/ledger"
        data = await self._request("GET", path, authenticated=True)

        if not isinstance(data, dict):
            raise SchemaChangedError(f"Expected dict for portfolio ledger, got {type(data).__name__}")

        if "id" not in data or ("ledger" not in data and "transactions" not in data):
            raise SchemaChangedError(
                f"Ledger response missing required fields (id, ledger/transactions): {list(data.keys())}"
            )

        ledger_list = data.get("ledger") if "ledger" in data else data.get("transactions")
        if not isinstance(ledger_list, list):
            raise SchemaChangedError(f"Ledger items must be a list: {type(ledger_list).__name__}")

        return data

    # -------------------------------------------------------------------------
    # Mutating Order Execution Endpoints
    # -------------------------------------------------------------------------

    async def buy(self, id: str | int, items: list[dict[str, Any]]) -> dict[str, Any]:
        """Execute Buy orders on StockNow portfolio.

        Strictly enforces test portfolio hard guard.
        Validates schema and employs ledger verification on network timeout.
        """
        verified_id = verify_test_portfolio_post_guard(id)
        if not items:
            raise ValueError("buy items list cannot be empty")

        actions = ["Buy"] * len(items)
        scrip_id = [it.get("scrip_id") or "" for it in items]
        commission = [str(it.get("commission", 0.5)) for it in items]
        no_of_shares = [str(it.get("shares") or it.get("qty") or it.get("no_of_shares", 1)) for it in items]
        buying_price = [float(it.get("price") or it.get("buying_price") or it.get("rate", 0.0)) for it in items]
        buying_date = [it.get("date") or it.get("buying_date") for it in items]
        instrument_ids = [str(it.get("symbol") or it.get("instrument_id") or it.get("code", "")).upper() for it in items]

        payload = {
            "portfolio_name": "",
            "cash_amount": "",
            "broker_fee": "0.5",
            "actions": actions,
            "scrip_id": scrip_id,
            "commission": commission,
            "no_of_shares": no_of_shares,
            "buying_price": buying_price,
            "buying_date": buying_date,
            "instrument_ids": instrument_ids,
        }

        path = f"/api/v1/user/portfolios/{verified_id}"
        data = await self._request(
            "POST",
            path,
            json_data=payload,
            authenticated=True,
            is_mutation=True,
            portfolio_id=verified_id,
            expected_items=items,
        )

        if not isinstance(data, dict) or "id" not in data or "scrips" not in data:
            raise SchemaChangedError(f"Buy response missing required fields (id, scrips): {data}")

        return data

    async def sell(self, id: str | int, items: list[dict[str, Any]]) -> dict[str, Any]:
        """Execute Sell orders on StockNow portfolio.

        Strictly enforces test portfolio hard guard.
        Validates schema and employs ledger verification on network timeout.
        """
        verified_id = verify_test_portfolio_post_guard(id)
        if not items:
            raise ValueError("sell items list cannot be empty")

        actions = ["Sell"] * len(items)
        scrip_id = [it.get("scrip_id") for it in items]
        commission = [str(it.get("commission", 0.5)) for it in items]
        no_of_shares = [str(it.get("shares") or it.get("qty") or it.get("no_of_shares", 1)) for it in items]
        buying_price = [float(it.get("price") or it.get("buying_price") or it.get("rate", 0.0)) for it in items]
        buying_date = [it.get("date") or it.get("buying_date") for it in items]
        instrument_ids: list[str] = []

        payload = {
            "portfolio_name": "",
            "cash_amount": "",
            "broker_fee": "0.5",
            "actions": actions,
            "scrip_id": scrip_id,
            "commission": commission,
            "no_of_shares": no_of_shares,
            "buying_price": buying_price,
            "buying_date": buying_date,
            "instrument_ids": instrument_ids,
        }

        path = f"/api/v1/user/portfolios/{verified_id}"
        data = await self._request(
            "POST",
            path,
            json_data=payload,
            authenticated=True,
            is_mutation=True,
            portfolio_id=verified_id,
            expected_items=items,
        )

        if not isinstance(data, dict) or "id" not in data or "scrips" not in data:
            raise SchemaChangedError(f"Sell response missing required fields (id, scrips): {data}")

        return data
