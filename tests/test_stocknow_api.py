"""Contract and unit tests for StockNow async API client."""

import json
import os
import time
from pathlib import Path
from typing import Any

import httpx
import pytest

from backend.adapters.stocknow_api import (
    NETWORK,
    NOT_AUTHENTICATED,
    RATE_LIMITED,
    SCHEMA_CHANGED,
    NetworkError,
    NotAuthenticatedError,
    RateLimitedError,
    SchemaChangedError,
    StockNowAPI,
    StockNowError,
)
from backend.adapters.stocknow_write_guard import StockNowWriteGuardError

FIXTURES_DIR = Path("tests/fixtures/stocknow")


def load_fixture(name: str) -> Any:
    path = FIXTURES_DIR / name
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# -----------------------------------------------------------------------------
# Authentication & Token Lifecycle Tests
# -----------------------------------------------------------------------------

@pytest.mark.anyio
async def test_login_success(monkeypatch):
    """Client logs in, stores token strictly in memory, and decodes expiration."""
    monkeypatch.setenv("STOCKNOW_MOBILE", "01700000000")
    monkeypatch.setenv("STOCKNOW_PASSWORD", "secret123")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert "/auth/login" in str(request.url)
        body = json.loads(request.content.decode("utf-8"))
        assert body["email"] == "01700000000"
        assert body["password"] == "secret123"
        return httpx.Response(
            200,
            json={"access_token": "valid.memory.token", "expires_in": 3600},
        )

    transport = httpx.MockTransport(handler)
    async with StockNowAPI(transport=transport, rate_limit_interval=0.0) as api:
        token = await api.login()
        assert token == "valid.memory.token"
        assert api._access_token == "valid.memory.token"
        assert api._token_expires_at > time.time()


@pytest.mark.anyio
async def test_login_missing_credentials(monkeypatch):
    """Missing credentials raises NOT_AUTHENTICATED immediately."""
    monkeypatch.setenv("STOCKNOW_MOBILE", "")
    monkeypatch.setenv("STOCKNOW_PASSWORD", "")

    async with StockNowAPI(rate_limit_interval=0.0) as api:
        with pytest.raises(NOT_AUTHENTICATED) as exc_info:
            await api.login()
        assert "not found in environment" in str(exc_info.value)


@pytest.mark.anyio
async def test_login_invalid_credentials(monkeypatch):
    """Failed login returns 401 or 422 raising NOT_AUTHENTICATED."""
    monkeypatch.setenv("STOCKNOW_MOBILE", "01700000000")
    monkeypatch.setenv("STOCKNOW_PASSWORD", "wrongpass")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"error": {"code": 401, "message": "Invalid mobile or password."}},
        )

    transport = httpx.MockTransport(handler)
    async with StockNowAPI(transport=transport, rate_limit_interval=0.0) as api:
        with pytest.raises(NOT_AUTHENTICATED):
            await api.login()


@pytest.mark.anyio
async def test_reauth_on_margin(monkeypatch):
    """Client re-authenticates automatically before token expiration margin."""
    monkeypatch.setenv("STOCKNOW_MOBILE", "01700000000")
    monkeypatch.setenv("STOCKNOW_PASSWORD", "secret123")

    login_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal login_calls
        if "/auth/login" in str(request.url):
            login_calls += 1
            return httpx.Response(200, json={"access_token": f"token_{login_calls}", "expires_in": 3600})
        if "/user/lists" in str(request.url):
            return httpx.Response(200, json=[])
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with StockNowAPI(transport=transport, rate_limit_interval=0.0, reauth_margin_seconds=300.0) as api:
        await api.login()
        assert login_calls == 1

        # Simulate time near expiry (within 300s margin)
        api._token_expires_at = time.time() + 100.0
        # ensure_authenticated should trigger re-login
        token = await api.ensure_authenticated()
        assert login_calls == 2
        assert token == "token_2"


@pytest.mark.anyio
async def test_401_triggers_relogin_and_retry(monkeypatch):
    """On 401 from an authenticated endpoint, client re-authenticates once and retries."""
    monkeypatch.setenv("STOCKNOW_MOBILE", "01700000000")
    monkeypatch.setenv("STOCKNOW_PASSWORD", "secret123")

    lists_fixture = load_fixture("user_lists.json")
    list_calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal list_calls
        url = str(request.url)
        if "/auth/login" in url:
            return httpx.Response(200, json={"access_token": "fresh_token", "expires_in": 3600})
        if "/user/lists" in url:
            list_calls += 1
            auth = request.headers.get("Authorization", "")
            if auth == "Bearer initial_token":
                return httpx.Response(401, json={"error": {"code": 401, "message": "Please login."}})
            if auth == "Bearer fresh_token":
                return httpx.Response(200, json=lists_fixture)
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with StockNowAPI(transport=transport, rate_limit_interval=0.0) as api:
        api._access_token = "initial_token"
        api._token_expires_at = time.time() + 10000.0

        res = await api.get_lists()
        assert list_calls == 2
        assert len(res) == 3
        assert api._access_token == "fresh_token"


@pytest.mark.anyio
async def test_persistent_401_fails_not_authenticated(monkeypatch):
    """When 401 persists after re-login, NOT_AUTHENTICATED is raised."""
    monkeypatch.setenv("STOCKNOW_MOBILE", "01700000000")
    monkeypatch.setenv("STOCKNOW_PASSWORD", "secret123")

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "/auth/login" in url:
            return httpx.Response(200, json={"access_token": "dummy_token", "expires_in": 3600})
        if "/user/lists" in url:
            return httpx.Response(401, json={"error": {"code": 401, "message": "Please login."}})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with StockNowAPI(transport=transport, rate_limit_interval=0.0) as api:
        with pytest.raises(NOT_AUTHENTICATED):
            await api.get_lists()


@pytest.mark.anyio
async def test_rate_limited_429(monkeypatch):
    """HTTP 429 raises RATE_LIMITED typed error."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": {"code": 429, "message": "Too Many Requests"}})

    transport = httpx.MockTransport(handler)
    async with StockNowAPI(transport=transport, rate_limit_interval=0.0) as api:
        with pytest.raises(RATE_LIMITED):
            await api.get_instruments()


# -----------------------------------------------------------------------------
# Public Endpoints & ETag Caching Tests
# -----------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_instruments_contract_and_etag():
    """get_instruments returns fixture and caches response with ETag (304)."""
    instruments_fixture = load_fixture("instruments.json")
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert "/instruments" in str(request.url)
        if request.headers.get("If-None-Match") == '"test_etag_123"':
            return httpx.Response(304)
        return httpx.Response(
            200,
            json=instruments_fixture,
            headers={"ETag": '"test_etag_123"'},
        )

    transport = httpx.MockTransport(handler)
    async with StockNowAPI(transport=transport, rate_limit_interval=0.0) as api:
        # First call: populates cache
        res1 = await api.get_instruments()
        assert "BANKASIA" in res1
        price = res1["BANKASIA"].get("close") or res1["BANKASIA"].get("ltp")
        assert price == 17.5
        assert calls == 1

        # Second call: sends If-None-Match, gets 304, returns cached data
        res2 = await api.get_instruments()
        assert calls == 2
        assert "BANKASIA" in res2
        price2 = res2["BANKASIA"].get("close") or res2["BANKASIA"].get("ltp")
        assert price2 == 17.5


@pytest.mark.anyio
async def test_get_instruments_schema_changed():
    """Missing expected fields raises SCHEMA_CHANGED."""
    def handler(request: httpx.Request) -> httpx.Response:
        # Returns invalid schema (missing ltp)
        return httpx.Response(200, json={"BANKASIA": {"name": "Bank Asia"}})

    transport = httpx.MockTransport(handler)
    async with StockNowAPI(transport=transport, rate_limit_interval=0.0) as api:
        with pytest.raises(SCHEMA_CHANGED) as exc_info:
            await api.get_instruments()
        assert "misses required price field" in str(exc_info.value)


# -----------------------------------------------------------------------------
# Watchlists, History, Portfolio & Ledger Contract Tests
# -----------------------------------------------------------------------------

@pytest.mark.anyio
async def test_get_lists_contract(monkeypatch):
    """get_lists parses user_lists fixture correctly."""
    monkeypatch.setenv("STOCKNOW_MOBILE", "01700000000")
    monkeypatch.setenv("STOCKNOW_PASSWORD", "secret123")
    lists_fixture = load_fixture("user_lists.json")

    def handler(request: httpx.Request) -> httpx.Response:
        if "/auth/login" in str(request.url):
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        return httpx.Response(200, json=lists_fixture)

    transport = httpx.MockTransport(handler)
    async with StockNowAPI(transport=transport, rate_limit_interval=0.0) as api:
        res = await api.get_lists()
        assert len(res) == 3
        assert res[0]["name"] == "Giant Stable Companies"
        assert res[1]["name"] == "GSC Upper Trends L1"
        assert res[2]["name"] == "GSC Upper Trends L2"


@pytest.mark.anyio
async def test_get_history_contract():
    """get_history parses 6-array candle structure and slices requested sessions."""
    candles_fixture = load_fixture("history_candles.json")

    def handler(request: httpx.Request) -> httpx.Response:
        assert "history" in str(request.url)
        return httpx.Response(200, json=candles_fixture)

    transport = httpx.MockTransport(handler)
    async with StockNowAPI(transport=transport, rate_limit_interval=0.0) as api:
        candles = await api.get_history("BANKASIA", sessions=10)
        assert len(candles) == 10
        # Candle shape: [timestamp, open, high, low, close, volume]
        first_candle = candles[0]
        assert len(first_candle) == 6
        assert isinstance(first_candle[0], (int, float))  # timestamp
        assert isinstance(first_candle[4], (int, float))  # close


@pytest.mark.anyio
async def test_get_portfolio_contract(monkeypatch):
    """get_portfolio parses portfolio_show fixture and validates schema."""
    monkeypatch.setenv("STOCKNOW_MOBILE", "01700000000")
    monkeypatch.setenv("STOCKNOW_PASSWORD", "secret123")
    show_fixture = load_fixture("portfolio_show.json")

    def handler(request: httpx.Request) -> httpx.Response:
        if "/auth/login" in str(request.url):
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        return httpx.Response(200, json=show_fixture)

    transport = httpx.MockTransport(handler)
    async with StockNowAPI(transport=transport, rate_limit_interval=0.0) as api:
        port = await api.get_portfolio(164580)
        assert port["id"] == 164580
        assert port["cash_amount"] == 129200
        assert len(port["scrips"]) == 2


@pytest.mark.anyio
async def test_get_portfolio_schema_changed(monkeypatch):
    """Missing scrips field in portfolio raises SCHEMA_CHANGED."""
    monkeypatch.setenv("STOCKNOW_MOBILE", "01700000000")
    monkeypatch.setenv("STOCKNOW_PASSWORD", "secret123")

    def handler(request: httpx.Request) -> httpx.Response:
        if "/auth/login" in str(request.url):
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        return httpx.Response(200, json={"id": 164580, "cash_amount": 10000})

    transport = httpx.MockTransport(handler)
    async with StockNowAPI(transport=transport, rate_limit_interval=0.0) as api:
        with pytest.raises(SCHEMA_CHANGED):
            await api.get_portfolio(164580)


@pytest.mark.anyio
async def test_get_ledger_contract(monkeypatch):
    """get_ledger parses portfolio_ledger fixture."""
    monkeypatch.setenv("STOCKNOW_MOBILE", "01700000000")
    monkeypatch.setenv("STOCKNOW_PASSWORD", "secret123")
    ledger_fixture = load_fixture("portfolio_ledger.json")

    def handler(request: httpx.Request) -> httpx.Response:
        if "/auth/login" in str(request.url):
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        return httpx.Response(200, json=ledger_fixture)

    transport = httpx.MockTransport(handler)
    async with StockNowAPI(transport=transport, rate_limit_interval=0.0) as api:
        ledger = await api.get_ledger(164580)
        assert ledger["id"] == 164580
        assert len(ledger["ledger"]) == 16
        assert ledger["ledger"][0]["action"] == "SELL"


# -----------------------------------------------------------------------------
# Mutation & Safety Guard Tests
# -----------------------------------------------------------------------------

@pytest.mark.anyio
async def test_buy_and_sell_hard_guard(monkeypatch):
    """Mutating calls to non-test portfolios are rejected by hard guard."""
    monkeypatch.setenv("STOCKNOW_TEST_PORTFOLIO_ID", "164580")
    async with StockNowAPI(rate_limit_interval=0.0) as api:
        with pytest.raises(StockNowWriteGuardError):
            await api.buy(999999, [{"symbol": "BANKASIA", "qty": 1, "price": 17.5}])

        with pytest.raises(StockNowWriteGuardError):
            await api.sell(999999, [{"scrip_id": 1234, "qty": 1, "price": 17.5}])


@pytest.mark.anyio
async def test_buy_contract_payload_and_response(monkeypatch):
    """Buy formats parallel arrays per contract and returns updated portfolio."""
    monkeypatch.setenv("STOCKNOW_MOBILE", "01700000000")
    monkeypatch.setenv("STOCKNOW_PASSWORD", "secret123")
    monkeypatch.setenv("STOCKNOW_TEST_PORTFOLIO_ID", "164580")

    def handler(request: httpx.Request) -> httpx.Response:
        if "/auth/login" in str(request.url):
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        if request.method == "POST" and "/portfolios/164580" in str(request.url):
            body = json.loads(request.content.decode("utf-8"))
            assert body["actions"] == ["Buy"]
            assert body["instrument_ids"] == ["BANKASIA"]
            assert body["no_of_shares"] == ["1"]
            assert body["buying_price"] == [17.5]
            return httpx.Response(200, json={"id": 164580, "scrips": [{"id": 2350594, "code": "BANKASIA"}]})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with StockNowAPI(transport=transport, rate_limit_interval=0.0) as api:
        res = await api.buy("164580", [{"symbol": "BANKASIA", "qty": 1, "price": 17.5, "commission": 0.5}])
        assert res["id"] == 164580
        assert len(res["scrips"]) == 1


@pytest.mark.anyio
async def test_never_retry_mutation_blindly_ledger_check(monkeypatch):
    """On transport timeout during Buy/Sell, client reads ledger first to prevent double submit."""
    monkeypatch.setenv("STOCKNOW_MOBILE", "01700000000")
    monkeypatch.setenv("STOCKNOW_PASSWORD", "secret123")
    monkeypatch.setenv("STOCKNOW_TEST_PORTFOLIO_ID", "164580")

    post_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal post_count
        url = str(request.url)
        if "/auth/login" in url:
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        if request.method == "POST" and "/portfolios/164580" in url:
            post_count += 1
            # Simulate network timeout / drop after server processed it
            raise httpx.ConnectTimeout("Connection timed out after write")
        if request.method == "GET" and "/portfolios/164580/ledger" in url:
            # Ledger contains the trade already recorded by the server
            return httpx.Response(
                200,
                json={
                    "id": 164580,
                    "ledger": [
                        {
                            "id": 3142750,
                            "action": "BUY",
                            "description": "BANKASIA",
                            "qty": 1,
                            "price": 17.5,
                        }
                    ],
                },
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with StockNowAPI(transport=transport, rate_limit_interval=0.0, max_retries=2) as api:
        # Buy should NOT retry blindly when the ledger confirms the order was recorded
        result = await api.buy("164580", [{"symbol": "BANKASIA", "qty": 1, "price": 17.5}])
        assert post_count == 1  # Exactly 1 POST, NO blind second POST!
        assert result.get("status") == "confirmed_via_ledger"


@pytest.mark.anyio
async def test_logout_clears_token(monkeypatch):
    """Logout calls endpoint and purges in-memory token."""
    logout_called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal logout_called
        if "/auth/logout" in str(request.url):
            logout_called = True
            assert request.headers.get("Authorization") == "Bearer active_token"
            return httpx.Response(200, json={"success": {"message": "Logged out"}})
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with StockNowAPI(transport=transport, rate_limit_interval=0.0) as api:
        api._access_token = "active_token"
        api._token_expires_at = time.time() + 1000.0
        await api.logout()
        assert logout_called is True
        assert api._access_token is None
        assert api._token_expires_at == 0.0


# -----------------------------------------------------------------------------
# Opt-In Live Smoke Test (Read-Only)
# -----------------------------------------------------------------------------

@pytest.mark.live
@pytest.mark.skipif(
    os.getenv("RUN_LIVE_STOCKNOW_TESTS", "").lower() not in ("1", "true", "yes"),
    reason="Live smoke test is opt-in only. Set RUN_LIVE_STOCKNOW_TESTS=1 to run.",
)
@pytest.mark.anyio
async def test_live_smoke_read_only():
    """Opt-in live smoke test against StockNow. Performs read-only calls only."""
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv("backend/.env")

    mobile = os.getenv("STOCKNOW_MOBILE")
    password = os.getenv("STOCKNOW_PASSWORD")
    test_portfolio_id = os.getenv("STOCKNOW_TEST_PORTFOLIO_ID", "164580")

    if not mobile or not password:
        pytest.skip("STOCKNOW_MOBILE and STOCKNOW_PASSWORD required for live smoke test.")

    async with StockNowAPI(rate_limit_interval=1.0) as api:
        # 1. Login
        token = await api.login()
        assert token and len(token) > 20

        # 2. Read public instruments
        instruments = await api.get_instruments()
        assert "BANKASIA" in instruments

        # 3. Read user watchlists
        lists = await api.get_lists()
        assert isinstance(lists, list)

        # 4. Read test portfolio
        port = await api.get_portfolio(test_portfolio_id)
        assert port["id"] == int(test_portfolio_id)
