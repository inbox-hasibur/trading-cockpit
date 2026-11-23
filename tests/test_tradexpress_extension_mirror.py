"""Tests for TradeXpress Passive Extension Mirror, MV3 static safety, and off-hours cash guard."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.adapters.tradexpress.passive_feed import (
    TradeXpressPassiveFeed,
    get_global_passive_feed,
    ingest_passive_snapshot,
)
from backend.config import Settings
from backend.database import CompanyProfile, Database
from backend.main import create_app
from backend.seed import seed_demo


@pytest.fixture
def test_db_and_settings(tmp_path: Path):
    db_file = tmp_path / "test_ext.db"
    settings = Settings(
        database_url=f"sqlite:///{db_file}",
        initial_capital=Decimal("100000.00"),
        stocknow_live_portfolio_id="H9210_SHADOW",
        stocknow_test_portfolio_id="H9210_SHADOW",
    )
    db = Database(settings.database_url)
    db.create_schema()
    with db.write() as session:
        seed_demo(session, settings)
    return db, settings


@pytest.fixture
def client(test_db_and_settings):
    db, settings = test_db_and_settings
    app = create_app(settings=settings, database=db)
    app.state.database = db
    with TestClient(app, base_url="http://127.0.0.1:8000") as c:
        yield c


def test_manifest_mv3_structure():
    manifest_path = Path("extension/tradexpress_mirror/manifest.json")
    assert manifest_path.exists(), "extension/tradexpress_mirror/manifest.json must exist"

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("manifest_version") == 3
    assert data.get("name") == "Humming Bird — TradeXpress Passive Mirror"
    assert "storage" in data.get("permissions", [])
    assert "http://127.0.0.1:8000/*" in data.get("host_permissions", [])

    content_scripts = data.get("content_scripts", [])
    assert len(content_scripts) > 0
    assert "https://itrade.lbsbd.com/*" in content_scripts[0].get("matches", [])
    assert "content.js" in content_scripts[0].get("js", [])

    bg = data.get("background", {})
    assert bg.get("service_worker") == "background.js"


def test_static_safety_scan_zero_forbidden():
    ext_dir = Path("extension/tradexpress_mirror")
    content_js = (ext_dir / "content.js").read_text(encoding="utf-8")
    bg_js = (ext_dir / "background.js").read_text(encoding="utf-8")

    # Content Script checks
    assert ".click(" not in content_js, "content.js must NEVER invoke .click()"
    assert ".reload(" not in content_js, "content.js must NEVER invoke .reload()"
    assert "location.href" not in content_js, "content.js must NEVER navigate via location.href"
    assert "document.cookie" not in content_js, "content.js must NEVER read document.cookie"
    assert "itrade.lbsbd.com" not in bg_js, "background.js must NEVER target itrade.lbsbd.com"
    assert "ibroker.lbsbd.com" not in bg_js, "background.js must NEVER target ibroker.lbsbd.com"


def test_extension_passive_ingest_endpoint_and_status(client: TestClient, test_db_and_settings):
    test_db, _ = test_db_and_settings
    payload = {
        "source": "EDGE_EXTENSION_PASSIVE",
        "dse_status": "Trading",
        "tab": "gsc",
        "market_watch_rows": [
            {
                "sDes": "BANKASIA",
                "ltp": "18.50",
                "chg": "0.10",
                "pctChg": "0.54",
                "vol": "15000",
                "open": "18.40",
                "high": "18.60",
                "low": "18.30",
                "dispSettType": "PUBLIC",
                "dispSymCat": "A",
            }
        ],
        "order_ticket_limits": {
            "symbol": "BANKASIA",
            "min_limit": 16.50,
            "max_limit": 20.00,
        },
        "account_summary": {
            "cash_balance": 75000.0,
            "available_cash_balance": 75000.0,
            "buying_power": 75000.0,
            "unsettled_sales": 5000.0,
        },
    }

    # Ingest from simulated Chrome Extension Origin
    headers = {
        "Origin": "chrome-extension://abcdefghijklmnopqrstuvwxyz123456",
        "X-Hummingbird-Source": "EDGE_EXTENSION_PASSIVE",
    }
    resp = client.post("/api/tradexpress/passive-ingest", json=payload, headers=headers)
    assert resp.status_code == 200, resp.text
    res_data = resp.json()
    assert res_data.get("status") == "INGESTED"
    assert res_data.get("bridge_source") == "EDGE_EXTENSION_PASSIVE"
    assert res_data.get("quotes_updated") == 1

    # Verify CompanyProfile updated in DB
    with test_db.read() as session:
        cp = session.get(CompanyProfile, "BANKASIA")
        assert cp is not None
        assert cp.last_price == Decimal("18.50")
        assert cp.min_limit == Decimal("16.50")
        assert cp.max_limit == Decimal("20.00")

    # Verify /api/tradexpress/status reports Extension Live
    status_resp = client.get("/api/tradexpress/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data.get("bridge_connected") is True
    assert status_data.get("bridge_source") == "EDGE_EXTENSION_PASSIVE"
    assert status_data.get("active_tab") == "gsc"
    assert status_data.get("buying_power") == 75000.0


def test_offhours_zero_cash_guard(test_db_and_settings):
    test_db, _ = test_db_and_settings
    feed = TradeXpressPassiveFeed(database=test_db)

    # 1. Active trading session snapshot sets positive cash
    active_payload = {
        "source": "EDGE_EXTENSION_PASSIVE",
        "dse_status": "Trading",
        "tab": "account_summary",
        "account_summary": {
            "cash_balance": 45000.0,
            "available_cash_balance": 45000.0,
            "buying_power": 45000.0,
            "unsettled_sales": 2000.0,
        },
    }
    res1 = ingest_passive_snapshot(test_db, active_payload, feed=feed)
    assert res1.get("status") == "INGESTED"
    assert feed.get_account_summary().buying_power == Decimal("45000.0")

    # 2. Off-hours closed snapshot arrives with 0.00 cash & buying power
    closed_payload = {
        "source": "EDGE_EXTENSION_PASSIVE",
        "dse_status": "Close",
        "tab": "gsc",
        "market_watch_rows": [
            {
                "sDes": "BANKASIA",
                "ltp": "18.60",
                "chg": "0.20",
                "pctChg": "1.09",
                "vol": "22000",
            }
        ],
        "account_summary": {
            "cash_balance": 0.0,
            "available_cash_balance": 0.0,
            "buying_power": 0.0,
            "unsettled_sales": 0.0,
        },
    }
    res2 = ingest_passive_snapshot(test_db, closed_payload, feed=feed)
    assert res2.get("status") == "INGESTED"

    # Price was updated
    with test_db.read() as session:
        cp = session.get(CompanyProfile, "BANKASIA")
        assert cp is not None
        assert cp.last_price == Decimal("18.60")

    # BUT cash balances were PRESERVED by the Off-Hours 0.00 Cash Guard!
    acct = feed.get_account_summary()
    assert acct.buying_power == Decimal("45000.0"), f"Expected 45000.0 preserved, got {acct.buying_power}"
    assert acct.cash_balance == Decimal("45000.0")


def test_cross_origin_security_blocking(client: TestClient):
    # Cross-origin API request from an untrusted origin must be rejected with 403
    untrusted_resp = client.get("/api/portfolio", headers={"Origin": "https://malicious-site.com"})
    assert untrusted_resp.status_code == 403
    assert untrusted_resp.json().get("error") == "FORBIDDEN"

    # Permitted loopback extension request to passive-ingest returns 200
    ext_resp = client.post(
        "/api/tradexpress/passive-ingest",
        json={"source": "EDGE_EXTENSION_PASSIVE"},
        headers={"Origin": "chrome-extension://trustedextensionid123"},
    )
    assert ext_resp.status_code == 200
