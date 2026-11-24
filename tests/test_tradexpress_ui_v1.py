"""Unit and integration tests for TradeXpress V1 3-Pane Cockpit UI & 2-Step Order Flow.

Verifies:
1. Index HTML structure, 3-pane elements, confirm modal, and tradexpress_ui.js loading.
2. Enriched portfolio snapshot microstructure & position profit telemetry.
3. 2-Step limit order execution: Step 1 (preview) -> Step 2 (confirm).
4. Order cancellation in SHADOW_DUMMY mode.
"""

from decimal import Decimal
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.database import Database
from backend.main import create_app
from backend.portfolio import snapshot_from_session
from backend.seed import seed_demo


@pytest.fixture
def app_client(tmp_path: Path):
    """FastAPI TestClient with isolated temporary database."""
    db_file = tmp_path / "test_tx_ui.db"
    settings = Settings(
        database_url=f"sqlite:///{db_file}",
        initial_capital=Decimal("100000.00"),
    )
    db = Database(settings.database_url)
    db.create_schema()
    with db.write() as session:
        seed_demo(session, settings)

    app = create_app(settings)
    with TestClient(app, base_url="http://localhost") as client:
        yield client, settings, db


def test_index_html_tradexpress_3pane_structure():
    """Verify index.html contains all 3-pane terminal elements and controller script."""
    html_file = Path("frontend/index.html")
    assert html_file.exists(), "frontend/index.html not found"
    content = html_file.read_text(encoding="utf-8")

    # Script tag
    assert "tradexpress_ui.js" in content, "tradexpress_ui.js script tag missing"

    # Topbar & badges
    assert 'id="portfolio-header-badge"' in content
    assert 'id="tx-hdr-buying-power"' in content
    assert 'id="tx-hdr-gain-loss"' in content
    assert 'id="topbar-clock-widget"' in content
    assert 'id="topbar-run-mode-switch"' in content
    assert 'id="topbar-automation-control"' in content
    assert 'id="run-cycle"' in content
    assert 'id="theme-toggle-btn"' in content

    # Secondary Navigation Tabs
    assert 'id="tx-main-nav"' in content
    assert 'id="tx-nav-trade"' in content
    assert 'id="tx-nav-heatmap"' in content
    assert 'id="tx-nav-rules"' in content
    assert 'id="tx-nav-ledger"' in content
    assert 'id="tx-nav-learning"' in content
    assert 'id="tx-nav-settings"' in content

    # 3-Pane Terminal Layout
    assert 'id="tx-trade-workspace"' in content
    assert 'id="tx-market-watch"' in content
    assert 'id="tx-order-ticket"' in content
    assert 'id="tx-depth-table"' in content
    assert 'id="tx-monitor-panel"' in content
    assert 'id="tx-pane-order-list"' in content
    assert 'id="tx-pane-portfolio"' in content
    assert 'id="tx-pane-account-summary"' in content
    assert 'id="tx-account-donut"' in content
    assert 'id="tx-pane-order-search"' in content

    # Step-2 Confirm Order Modal
    assert 'id="tx-confirm-order-modal"' in content
    assert 'id="tx-confirm-submit-btn"' in content
    assert 'id="tx-confirm-cancel-btn"' in content

    # Hermes Dock & Passive sync guide quick-chip
    assert 'id="hermes-sidebar"' in content
    assert 'id="chip-passive-sync-guide"' in content

    # Filter checkboxes
    assert 'id="filter-hide-z-spot"' in content
    assert 'id="filter-held-only"' in content


def test_enriched_portfolio_snapshot_payload(app_client):
    """Verify GET /api/portfolio includes microstructure and position telemetry."""
    client, settings, db = app_client
    resp = client.get("/api/portfolio")
    assert resp.status_code == 200
    data = resp.json()

    # Top-level portfolio telemetry
    assert "execution_venue" in data
    assert data["execution_venue"] in ("SHADOW_DUMMY", "DEMO")
    assert "buying_power_bdt" in data
    assert "unsettled_sales_bdt" in data
    assert isinstance(data["buying_power_bdt"], (int, float))

    # Company views enriched fields
    companies = data.get("companies", [])
    assert len(companies) > 0

    for c in companies:
        assert "tradexpress_symbol" in c
        assert c["tradexpress_symbol"].endswith("`PB")
        assert "bid" in c
        assert "offer" in c
        assert "symbol_category" in c
        assert "settlement_type" in c
        assert "hold_day_label" in c
        assert "bought_total" in c
        assert "sell_total_net" in c
        assert "net_profit_bdt" in c
        assert "net_profit_pct" in c


def test_two_step_shadow_limit_order_flow(app_client):
    """Verify 2-step limit order: Step 1 (confirm=false preview) -> Step 2 (confirm=true execution)."""
    client, settings, db = app_client

    # Step 1: Preview without execution
    preview_req = {
        "symbol": "BANKASIA",
        "side": "BUY",
        "quantity": 10,
        "price": 18.40,
        "order_type": "LIMIT",
        "confirm": False,
    }
    resp_prev = client.post("/api/tradexpress/shadow-order", json=preview_req)
    assert resp_prev.status_code == 200
    data_prev = resp_prev.json()
    assert data_prev.get("status") == "PREVIEW"
    assert "estimated_fee" in data_prev
    assert "net_value" in data_prev
    assert data_prev["symbol"] == "BANKASIA"
    assert data_prev["quantity"] == 10

    # Step 2: Confirm execution
    confirm_req = dict(preview_req)
    confirm_req["confirm"] = True
    resp_exec = client.post("/api/tradexpress/shadow-order", json=confirm_req)
    assert resp_exec.status_code == 200
    data_exec = resp_exec.json()
    assert data_exec.get("status") in ("SUBMITTED", "FILLED", "QUEUED")
    order_ref = data_exec.get("order_ref")
    assert order_ref is not None

    # Verify order is queryable via GET /api/tradexpress/orders
    resp_orders = client.get("/api/tradexpress/orders")
    assert resp_orders.status_code == 200
    orders_data = resp_orders.json()
    orders = orders_data if isinstance(orders_data, list) else orders_data.get("orders", [])
    found = any(o.get("order_ref") == order_ref for o in orders)
    assert found, f"Order {order_ref} not found in /api/tradexpress/orders"


def test_cancel_order_in_shadow_dummy(app_client):
    """Verify cancelling an order via POST /api/tradexpress/shadow-order/{order_ref}/cancel."""
    client, settings, db = app_client

    # Submit an order that remains resting/QUEUED (valid within circuit limits 16.5-20.2, but below LTP, allow_offhours_ltp_fill=False)
    req = {
        "symbol": "BANKASIA",
        "side": "BUY",
        "quantity": 5,
        "price": 17.50,
        "order_type": "LIMIT",
        "confirm": True,
        "allow_offhours_ltp_fill": False,
    }
    res = client.post("/api/tradexpress/shadow-order", json=req)
    assert res.status_code == 200
    order_ref = res.json().get("order_ref")
    assert res.json().get("status") == "QUEUED"

    # Cancel the resting queued order
    cancel_resp = client.post(f"/api/tradexpress/shadow-order/{order_ref}/cancel")
    assert cancel_resp.status_code == 200
    cancel_data = cancel_resp.json()
    assert cancel_data.get("status") == "CANCELLED"
    assert cancel_data.get("order_ref") == order_ref
