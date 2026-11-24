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
    assert any("https://itrade.lbsbd.com/*" in cs.get("matches", []) for cs in content_scripts)
    assert any("content.js" in cs.get("js", []) for cs in content_scripts)
    assert any("network_tap.js" in cs.get("js", []) for cs in content_scripts)

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


def test_unseen_symbol_1janatamf_sod_no_keyerror(client: TestClient, test_db_and_settings):
    """Verifies that an unseen symbol (e.g. 1JANATAMF) arriving during SOD with ltp=0.00

    automatically creates a CustomRule and causes ZERO KeyErrors in build_snapshot.
    """
    test_db, settings = test_db_and_settings

    # Verify 1JANATAMF does not exist initially
    with test_db.read() as session:
        from backend.database import CustomRule

        assert session.get(CompanyProfile, "1JANATAMF") is None
        assert session.get(CustomRule, "1JANATAMF") is None

    # Ingest passive SOD snapshot with 1JANATAMF at ltp=0.00
    sod_payload = {
        "source": "EDGE_EXTENSION_PASSIVE",
        "dse_status": "SOD",
        "tab": "market_watch",
        "market_watch_rows": [
            {
                "sDes": "1JANATAMF",
                "ltp": "0.00",
                "chg": "0.00",
                "pctChg": "0.00",
                "vol": "0",
                "open": "0.00",
                "high": "0.00",
                "low": "0.00",
                "dispSettType": "PUBLIC",
                "dispSymCat": "A",
            }
        ],
    }
    resp = client.post(
        "/api/tradexpress/passive-ingest",
        json=sod_payload,
        headers={"Origin": "chrome-extension://testextension123"},
    )
    assert resp.status_code == 200, resp.text

    # Verify CompanyProfile and CustomRule were both created
    with test_db.read() as session:
        cp = session.get(CompanyProfile, "1JANATAMF")
        assert cp is not None
        assert cp.last_price == Decimal("0.00")
        assert cp.price_history == []

        rule = session.get(CustomRule, "1JANATAMF")
        assert rule is not None
        assert rule.enabled is False
        assert rule.buy_allocation_pct == Decimal("0.00")

    # Critical Assertion: build_snapshot MUST NOT raise KeyError: '1JANATAMF'
    from backend.portfolio import build_snapshot

    snap = build_snapshot(test_db, settings)
    assert snap is not None
    assert "companies" in snap
    janata_view = next((c for c in snap["companies"] if c["symbol"] == "1JANATAMF"), None)
    assert janata_view is not None
    assert janata_view["price"] == 0.0
    assert janata_view["curve"]["signal"] == "WAIT_SOD"
    assert "SOD reset" in janata_view["curve"]["support_position"]


def test_sod_zero_price_protection_preserves_positive_price(client: TestClient, test_db_and_settings):
    """Verifies that SOD 0.00 quotes do NOT overwrite last_price or append 0.00 candles."""
    test_db, settings = test_db_and_settings

    # 1. Establish positive price and candle on BANKASIA
    with test_db.write() as session:
        cp = session.get(CompanyProfile, "BANKASIA")
        cp.last_price = Decimal("18.40")
        cp.price_history = [
            {"date": "2026-11-20", "close": "18.30", "open": "18.20", "high": "18.40", "low": "18.10", "volume": "1000"},
            {"date": "2026-11-22", "close": "18.40", "open": "18.30", "high": "18.50", "low": "18.20", "volume": "1200"},
        ]
        session.flush()

    # 2. Incoming SOD snapshot with ltp=0.00
    sod_payload = {
        "source": "EDGE_EXTENSION_PASSIVE",
        "dse_status": "SOD",
        "tab": "gsc",
        "market_watch_rows": [
            {
                "sDes": "BANKASIA",
                "ltp": "0.00",
                "chg": "0.00",
                "pctChg": "0.00",
                "vol": "0",
                "open": "0.00",
                "high": "0.00",
                "low": "0.00",
            }
        ],
    }
    resp = client.post(
        "/api/tradexpress/passive-ingest",
        json=sod_payload,
        headers={"Origin": "chrome-extension://testextension123"},
    )
    assert resp.status_code == 200

    # 3. Verify BANKASIA last_price is preserved at 18.40 and NO 0.00 candle was added
    with test_db.read() as session:
        cp = session.get(CompanyProfile, "BANKASIA")
        assert cp.last_price == Decimal("18.40"), f"Expected 18.40 preserved, got {cp.last_price}"
        assert len(cp.price_history) == 2
        assert cp.price_history[-1]["close"] == "18.40"


def test_manifest_icons_and_network_tap_registration():
    """Verifies that extension manifest declares icons and registers network_tap.js in MAIN world."""
    manifest_path = Path("extension/tradexpress_mirror/manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # 1. Icons check
    icons = manifest.get("icons", {})
    for sz in ["16", "32", "48", "128"]:
        assert sz in icons, f"Icon {sz} missing in manifest"
        icon_path = Path("extension/tradexpress_mirror") / icons[sz]
        assert icon_path.exists(), f"Icon file {icon_path} does not exist"
        assert icon_path.stat().st_size > 0, f"Icon file {icon_path} is empty"

    action_icons = manifest.get("action", {}).get("default_icon", {})
    for sz in ["16", "32", "48", "128"]:
        assert sz in action_icons, f"Action icon {sz} missing in manifest"

    # 2. Network tap content script check
    content_scripts = manifest.get("content_scripts", [])
    tap_script = next((cs for cs in content_scripts if "network_tap.js" in cs.get("js", [])), None)
    assert tap_script is not None, "network_tap.js must be registered in manifest content_scripts"
    assert tap_script.get("world") == "MAIN", "network_tap.js must run in MAIN world to intercept WebSocket/XHR"
    assert tap_script.get("run_at") == "document_start", "network_tap.js must run at document_start"


def test_network_tap_static_safety_and_redaction():
    """Ensures network_tap.js is 100% passive, fail-safe, and redacts sensitive credentials."""
    tap_path = Path("extension/tradexpress_mirror/network_tap.js")
    assert tap_path.exists(), "network_tap.js must exist"
    code = tap_path.read_text(encoding="utf-8")

    # Anti-bot and passive guarantees
    assert ".click(" not in code, "network_tap.js must NEVER click"
    assert ".reload(" not in code, "network_tap.js must NEVER reload"
    assert "location.href" not in code, "network_tap.js must NEVER navigate"
    assert "itrade.lbsbd.com" not in code, "network_tap.js must NEVER send external requests"
    assert "ibroker.lbsbd.com" not in code, "network_tap.js must NEVER send external requests"

    # Redaction checks
    assert "redactString" in code
    assert "sesnId" in code
    assert "SSOTOK" in code or "ssotok" in code
    assert "AUTH_REDACTED" in code


def test_passive_net_tap_endpoints_and_telemetry(client: TestClient, test_db_and_settings):
    """Verifies POST /api/tradexpress/passive-net-tap and GET /api/tradexpress/net-tap/summary."""
    ext_origin = {"Origin": "chrome-extension://testabcdef123456"}

    # 1. Ingest simulated net tap batch
    batch_payload = {
        "events": [
            {
                "type": "ws_in",
                "endpoint": "wss://itrade.lbsbd.com/price_feed",
                "channel": "market_depth",
                "payload": {"symbol": "BANKASIA", "bid": 18.40, "offer": 18.50},
                "timestamp": 1700000000000,
            },
            {
                "type": "ws_out",
                "endpoint": "wss://itrade.lbsbd.com/price_feed",
                "channel": "client_send",
                "payload": {"subscribe": "BANKASIA"},
                "timestamp": 1700000000050,
            },
            {
                "type": "xhr",
                "method": "GET",
                "url": "https://itrade.lbsbd.com/web/price?symbol=BANKASIA",
                "endpoint": "https://itrade.lbsbd.com/web/price",
                "status": 200,
                "payload": {"lastPrice": 18.40},
                "timestamp": 1700000000100,
            },
        ]
    }

    resp = client.post("/api/tradexpress/passive-net-tap", json=batch_payload, headers=ext_origin)
    assert resp.status_code == 200, resp.text
    res_data = resp.json()
    assert res_data.get("status") == "INGESTED"
    assert res_data.get("count") == 3

    # 2. Verify summary endpoint
    summary_resp = client.get("/api/tradexpress/net-tap/summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary.get("ws_in_count") >= 1
    assert summary.get("ws_out_count") >= 1
    assert summary.get("xhr_count") >= 1
    assert "market_depth" in summary.get("channels_seen", [])
    assert any("itrade.lbsbd.com" in ep for ep in summary.get("endpoints_seen", []))

    # 3. Verify status endpoint includes net_tap
    status_resp = client.get("/api/tradexpress/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert "net_tap" in status_data
    assert status_data["net_tap"]["total_events"] >= 3
