"""Tests for unified StockNowExecutor, ApiTransport, and BrowserTransport.

Verifies:
1. Logged-out order fails with ledger unchanged on both transports (NOT_AUTHENTICATED).
2. Timeout then ledger check prevents a duplicate order.
3. Ledger mismatch / missing receipt restores checkpoint cleanly (NO_RECEIPT).
4. Explicit DEMO paper fill returns DEMO_PAPER and never returns PAPER_VERIFIED.
5. BrowserTransport dialog handler accepts logout confirm and dismisses all other dialogs.
6. Session logout action (/k/stocknow/session) logs out both transports.
"""

from __future__ import annotations

import asyncio
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from backend.adapters.stocknow_executor import (
    ApiTransport,
    BrowserTransport,
    DemoPaperExecutor,
    NoReceiptExecutionError,
    NotAuthenticatedExecutionError,
    TimeoutExecutionError,
    get_stocknow_executor,
    match_ledger_entry,
)
from backend.config import Settings
from backend.database import Database, TaxLot, TradeLog, portfolio_state
from backend.engine.checkpoint import CheckpointManager
from backend.main import create_app
from backend.seed import seed_demo


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def auth_headers(monkeypatch):
    token = "test-kernel-token-executor"
    monkeypatch.setenv("KERNEL_TOKEN", token)
    monkeypatch.setenv("STOCKNOW_TEST_PORTFOLIO_ID", "164580")
    return {"X-Kernel-Token": token}


@pytest.fixture
def test_app_and_db(tmp_path, monkeypatch):
    monkeypatch.setenv("STOCKNOW_TEST_PORTFOLIO_ID", "164580")
    monkeypatch.setenv("STOCKNOW_LIVE_PORTFOLIO_ID", "164580")
    db_file = tmp_path / "test_executor.db"
    settings = Settings(
        database_url=f"sqlite:///{db_file.as_posix()}",
        demo_start_date=date(2026, 11, 3),
        stocknow_test_portfolio_id="164580",
        stocknow_live_portfolio_id="164580",
    )
    db = Database(settings.database_url)
    db.create_schema()
    with db.write() as session:
        seed_demo(session, settings)
    app = create_app(settings)
    return app, db, settings


# -----------------------------------------------------------------------------
# Test 1: Logged-out Order Fails on Both Transports
# -----------------------------------------------------------------------------

@pytest.mark.anyio
async def test_logged_out_order_fails_on_api_transport():
    """ApiTransport raises NotAuthenticatedExecutionError when token is missing."""
    mock_api = MagicMock()
    mock_api._access_token = None
    mock_api.ensure_authenticated = AsyncMock(return_value=None)

    transport = ApiTransport(api_client=mock_api, configured_test_id="164580")
    assert await transport.is_authenticated() is False

    with pytest.raises(NotAuthenticatedExecutionError) as exc_info:
        await transport.execute_order(
            symbol="GP",
            side="BUY",
            quantity=10,
            price=Decimal("250.00"),
            portfolio_id="164580",
            trade_date=date(2026, 11, 3),
        )
    assert exc_info.value.error_code == "NOT_AUTHENTICATED"
    mock_api.buy.assert_not_called()


@pytest.mark.anyio
async def test_logged_out_order_fails_on_browser_transport():
    """BrowserTransport raises NotAuthenticatedExecutionError when browser has no token."""
    mock_page = MagicMock()
    mock_page.is_closed = MagicMock(return_value=False)
    # localStorage returns None for access_token
    mock_page.evaluate = AsyncMock(return_value=None)

    mock_client = MagicMock()
    mock_client.page = mock_page

    transport = BrowserTransport(stocknow_client=mock_client, configured_test_id="164580")
    assert await transport.is_authenticated() is False

    with pytest.raises(NotAuthenticatedExecutionError) as exc_info:
        await transport.execute_order(
            symbol="GP",
            side="BUY",
            quantity=10,
            price=Decimal("250.00"),
            portfolio_id="164580",
            trade_date=date(2026, 11, 3),
        )
    assert exc_info.value.error_code == "NOT_AUTHENTICATED"


# -----------------------------------------------------------------------------
# Test 2: Timeout Then Ledger Check Prevents Duplicate Order
# -----------------------------------------------------------------------------

@pytest.mark.anyio
async def test_timeout_then_ledger_check_prevents_duplicate():
    """If buy POST times out, transport inspects server ledger first to avoid duplicate."""
    mock_api = MagicMock()
    mock_api._access_token = "valid-token"
    mock_api.ensure_authenticated = AsyncMock(return_value="valid-token")

    # buy raises TimeoutException
    mock_api.buy = AsyncMock(side_effect=httpx.TimeoutException("Read timed out"))

    # get_ledger returns matching row (order was executed on server despite client timeout)
    matching_row = {
        "id": 998811,
        "action": "BUY",
        "description": "GP",
        "qty": 5,
        "rate": 250.00,
        "created_at": "2026-11-03 11:30:00",
    }
    mock_api.get_ledger = AsyncMock(return_value={"ledger": [matching_row]})

    transport = ApiTransport(api_client=mock_api, configured_test_id="164580")

    # Must succeed because ledger inspection found the fill, preventing a duplicate retry
    receipt = await transport.execute_order(
        symbol="GP",
        side="BUY",
        quantity=5,
        price=Decimal("250.00"),
        portfolio_id="164580",
        trade_date=date(2026, 11, 3),
    )

    assert receipt["success"] is True
    assert receipt["status"] == "FILLED"
    assert receipt["symbol"] == "GP"
    assert receipt["quantity"] == 5
    assert receipt["ledger_record"]["id"] == 998811
    # buy should only have been called ONCE, not retried blindly
    assert mock_api.buy.call_count == 1


@pytest.mark.anyio
async def test_timeout_without_ledger_fill_raises_timeout_error():
    """If buy POST times out and ledger has NO fill, raises TimeoutExecutionError."""
    mock_api = MagicMock()
    mock_api._access_token = "valid-token"
    mock_api.ensure_authenticated = AsyncMock(return_value="valid-token")
    mock_api.buy = AsyncMock(side_effect=httpx.TimeoutException("Read timed out"))
    mock_api.get_ledger = AsyncMock(return_value={"ledger": []})

    transport = ApiTransport(api_client=mock_api, configured_test_id="164580")

    with pytest.raises(TimeoutExecutionError) as exc_info:
        await transport.execute_order(
            symbol="GP",
            side="BUY",
            quantity=5,
            price=Decimal("250.00"),
            portfolio_id="164580",
            trade_date=date(2026, 11, 3),
        )
    assert exc_info.value.error_code == "TIMEOUT"


# -----------------------------------------------------------------------------
# Test 3: Ledger Mismatch Restores Checkpoint
# -----------------------------------------------------------------------------

def test_ledger_mismatch_restores_checkpoint(test_app_and_db, auth_headers):
    """When order fill cannot be verified in ledger, checkpoint is rolled back cleanly."""
    app, db, settings = test_app_and_db

    with db.read() as session:
        initial_lots = len(session.scalars(select(TaxLot)).all())
        initial_trades = len(session.scalars(select(TradeLog)).all())

    # Mock execute_order to raise NoReceiptExecutionError
    async def mock_execute_order(*args, **kwargs):
        raise NoReceiptExecutionError("Order fill not verified in StockNow ledger.")

    with patch("backend.adapters.stocknow_adapter.StockNowAdapter.execute_order", side_effect=mock_execute_order):
        with TestClient(app, base_url="http://localhost") as client:
            client.post("/k/mode", json={"trading_mode": "TEST_OFFHOURS", "confirm": True}, headers=auth_headers)

            res = client.post("/k/order", json={
                "idempotency_key": str(uuid4()),
                "symbol": "GP",
                "side": "BUY",
                "quantity": 5,
                "dry_run": False,
                "operator_confirmed": True,
            }, headers=auth_headers)

            assert res.status_code == 422
            data = res.json()
            assert data["error"] == "NO_RECEIPT", f"Actual response data: {data}"
            assert "not verified in StockNow ledger" in data["detail"]

    # Verify SQLite ledger is untouched (checkpoint restored)
    with db.read() as session:
        final_lots = len(session.scalars(select(TaxLot)).all())
        final_trades = len(session.scalars(select(TradeLog)).all())
        assert final_lots == initial_lots
        assert final_trades == initial_trades


# -----------------------------------------------------------------------------
# Test 4: Explicit DEMO Paper Fill
# -----------------------------------------------------------------------------

@pytest.mark.anyio
async def test_explicit_demo_paper_fill_returns_demo_paper():
    """DEMO mode produces DEMO_PAPER receipt and never returns PAPER_VERIFIED."""
    executor = get_stocknow_executor(mode="DEMO")
    assert isinstance(executor, DemoPaperExecutor)

    receipt = await executor.execute_order(
        symbol="GP",
        side="BUY",
        quantity=10,
        price=Decimal("250.00"),
        portfolio_id="164580",
        trade_date=date(2026, 11, 3),
        commission_pct=Decimal("0.5"),
    )

    assert receipt["success"] is True
    assert receipt["status"] == "ACKNOWLEDGED"
    assert receipt["execution_mode"] == "DEMO_PAPER"
    assert receipt["execution_mode"] != "PAPER_VERIFIED"
    assert receipt["commission_pct"] == 0.5


# -----------------------------------------------------------------------------
# Test 5: BrowserTransport Dialog Handler
# -----------------------------------------------------------------------------

@pytest.mark.anyio
async def test_browser_dialog_handler_accepts_logout_and_dismisses_others():
    """Dialog handler accepts only logout confirmation and dismisses all other dialogs."""
    registered_handlers = []

    mock_page = MagicMock()
    mock_page._stocknow_dialog_registered = False

    def on_register(event, handler):
        if event == "dialog":
            registered_handlers.append(handler)

    mock_page.on = MagicMock(side_effect=on_register)

    mock_client = MagicMock()
    mock_client.page = mock_page

    transport = BrowserTransport(stocknow_client=mock_client)
    transport._ensure_dialog_handler(mock_page)

    assert len(registered_handlers) == 1
    dialog_callback = registered_handlers[0]

    # 1. Test logout confirm dialog -> should accept
    logout_dialog = MagicMock()
    logout_dialog.message = "Are you sure you want to log out?"
    logout_dialog.accept = AsyncMock()
    logout_dialog.dismiss = AsyncMock()

    await dialog_callback(logout_dialog)
    logout_dialog.accept.assert_called_once()
    logout_dialog.dismiss.assert_not_called()

    # 2. Test unexpected dialog -> should dismiss
    other_dialog = MagicMock()
    other_dialog.message = "Some unexpected promotion popup!"
    other_dialog.type = "alert"
    other_dialog.accept = AsyncMock()
    other_dialog.dismiss = AsyncMock()

    await dialog_callback(other_dialog)
    other_dialog.dismiss.assert_called_once()
    other_dialog.accept.assert_not_called()


# -----------------------------------------------------------------------------
# Test 6: Kernel Session Logout for Both Transports
# -----------------------------------------------------------------------------

def test_session_logout_action_logs_out_both_transports(test_app_and_db, auth_headers):
    """POST /k/stocknow/session with action='logout' terminates sessions cleanly."""
    app, db, settings = test_app_and_db

    with TestClient(app, base_url="http://localhost") as client:
        # Mock client logout
        mock_client = MagicMock()
        mock_client.logout = AsyncMock(return_value={"status": "LOGGED_OUT", "transport": "BROWSER"})
        app.state.stocknow_client = mock_client

        res = client.post("/k/stocknow/session", json={"action": "logout"}, headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["action"] == "logout"
        assert data["status"] == "ok"
        assert data["browser"]["status"] == "LOGGED_OUT"
        assert data["api"]["status"] == "LOGGED_OUT"


# -----------------------------------------------------------------------------
# Test 7: Architectural Isolation Guard - No Direct StockNow Buy/Sell Calls
# -----------------------------------------------------------------------------

def test_architectural_order_executor_isolation():
    """Verify stocknow_order_executor is retired and no module outside stocknow_executor dispatches orders."""
    import re
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent

    # 1. stocknow_order_executor.py must not exist on disk
    legacy_file = repo_root / "backend" / "adapters" / "stocknow_order_executor.py"
    assert not legacy_file.exists(), f"Legacy executor file {legacy_file} must be deleted."

    # 2. No codebase file should import or reference stocknow_order_executor
    code_dirs = [repo_root / "backend", repo_root / "frontend", repo_root / "plugins", repo_root / "scripts"]
    for c_dir in code_dirs:
        if not c_dir.exists():
            continue
        for file_path in c_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix in (".py", ".js", ".ts", ".html"):
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                assert "stocknow_order_executor" not in content, (
                    f"Forbidden reference to stocknow_order_executor found in {file_path}"
                )

    # 3. No module outside backend/adapters/stocknow_executor.py may call direct StockNow buy/sell endpoints
    backend_dir = repo_root / "backend"
    forbidden_patterns = [
        re.compile(r"\bapi_client\.(buy|sell)\b"),
        re.compile(r"\.post\([\"'][^\"']*/portfolios/[^\"']*/(buy|sell)"),
    ]
    for py_file in backend_dir.rglob("*.py"):
        rel_posix = py_file.relative_to(repo_root).as_posix()
        if rel_posix in ("backend/adapters/stocknow_executor.py", "backend/adapters/stocknow_api.py"):
            continue
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        for pat in forbidden_patterns:
            match = pat.search(content)
            assert not match, (
                f"Direct StockNow buy/sell call found in {rel_posix}: '{match.group(0)}'. "
                f"All order dispatches must flow strictly through StockNowExecutor."
            )
