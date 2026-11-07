import json
from dataclasses import replace
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient

from backend.main import create_app


def test_first_cycle_and_duplicate(client):
    before = client.get("/api/portfolio").json()
    assert before["app"]["source"] == "SYNTHETIC"
    assert before["metrics"]["book_reconciled"]
    key = str(uuid4())
    result = client.post("/api/automation/cycle", headers={"Idempotency-Key": key}).json()
    actions = {trade["action"] for trade in result["trades"]}
    assert {"BUY", "SELL_TIER_1", "PULLBACK_SPLIT"} <= actions
    assert any(d["symbol"] == "BXPHARMA" and d["action"] == "BUY_BLOCKED"
               for d in result["decisions"])
    assert all(t["realized_pnl"] > 0 for t in result["trades"] if t["side"] == "SELL")
    after = client.get("/api/portfolio").json()
    assert after["metrics"]["book_reconciled"] and after["metrics"]["equity_reconciled"]
    assert after["metrics"]["unsettled_proceeds"] > 0
    assert client.post("/api/automation/cycle", headers={"Idempotency-Key": key}).json()["duplicate"]
    assert client.post("/api/automation/cycle").json()["duplicate"]
    assert client.get("/api/portfolio").json()["trade_count"] == after["trade_count"]


def test_restart_retains_ledger_and_recovery(settings):
    with TestClient(create_app(settings), base_url="http://localhost") as client:
        client.post("/api/automation/cycle")
        before = client.get("/api/portfolio").json()
    with TestClient(create_app(settings), base_url="http://localhost") as client:
        after = client.get("/api/portfolio").json()
        assert after["trade_count"] == before["trade_count"]
        assert next(l for l in after["lots"] if l["symbol"] == "GP")["phase"] == "RECOVERY_HOLD"
        assert client.post("/api/automation/cycle").json()["duplicate"]


def test_pause_and_allocation_validation(client):
    assert client.post("/api/automation/pause", json={"paused": True}).status_code == 200
    assert client.post("/api/automation/cycle").status_code == 409
    assert client.post("/api/automation/pause", json={"paused": False}).status_code == 200
    invalid = client.patch("/api/companies/BANKASIA/allocation", json={
        "buy_allocation_pct": 50, "enabled": True,
    })
    assert invalid.status_code == 422
    valid = client.patch("/api/companies/BANKASIA/allocation", json={
        "buy_allocation_pct": 5, "enabled": True,
    })
    assert valid.status_code == 200 and valid.json()["changed"]
    assert client.get("/api/portfolio").json()["rule_audit"][0]["symbol"] == "BANKASIA"


def test_api_security_origin_blocking(client):
    assert client.post("/api/automation/cycle", headers={"Origin": "https://evil.example"}).status_code == 403


def test_watchlist_categories_and_stream(client):
    snap = client.get("/api/portfolio").json()
    categories = {c["symbol"]: c["watchlist_category"] for c in snap["companies"]}
    assert categories["BANKASIA"] == "GSC_L2"
    assert categories["SQURPHARMA"] == "GSC_L1"
    assert categories["GP"] == "GSC"

    # Test SSE stream endpoint connection
    with client.stream("GET", "/api/stream") as stream:
        assert stream.status_code == 200
        line = next(stream.iter_lines())
        assert "connected" in line


def test_cockpit_smoke_and_assets(client):
    html = client.get("/").text
    assert "Humming Bird" in html
    assert "id=\"watchlist\"" in html
    assert "id=\"market-map\"" in html
    assert "id=\"treemap-container\"" in html
    assert "id=\"sector-gainer-chart\"" in html
    assert "id=\"topbar-clock-widget\"" in html
    assert "id=\"theme-toggle-btn\"" in html
    assert "id=\"what-if-card\"" in html
    assert "id=\"deep-trend-modal\"" in html
    assert "id=\"fundamentals-grid\"" in html
    assert "id=\"canary-section\"" in html
    assert "category-tabs" in html
    assert "id=\"header-mode-slider\"" in html
    assert "id=\"view-dashboard\"" in html
    assert "id=\"view-settings\"" in html
    assert "id=\"operator-modal\"" in html
    assert "id=\"login-gate-overlay\"" in html
    assert "id=\"api-keys-card\"" in html
    assert "id=\"hermes-model-trigger\"" in html or "id=\"hermes-bottom-model-btn\"" in html
    assert client.get("/assets/app.js").status_code == 200
    assert client.get("/assets/styles.css").status_code == 200
    assert client.get("/assets/favicon.svg").status_code == 200


def test_company_fundamentals_and_extended_history(client):
    snap = client.get("/api/portfolio").json()
    companies = {c["symbol"]: c for c in snap["companies"]}

    # Check fundamentals
    assert "GP" in companies
    gp = companies["GP"]
    assert "fundamentals" in gp
    fund = gp["fundamentals"]
    assert fund["pe_ratio"] > 0
    assert fund["eps"] > 0
    assert fund["nav"] > 0
    assert fund["market_cap_cr"] > 1000

    # Check curve support / resistance
    assert "support" in gp["curve"]
    assert "resistance" in gp["curve"]
    assert gp["curve"]["resistance"] >= gp["curve"]["support"]

    # Check extended history horizons
    assert "extended_history" in gp
    ext = gp["extended_history"]
    assert {"7d", "1m", "6m", "1y"} <= set(ext.keys())
    assert len(ext["7d"]) >= 2
    assert len(ext["1m"]) >= 10
    assert len(ext["6m"]) >= 20
    assert len(ext["1y"]) >= 30


def test_market_map_endpoint_and_portfolio_snapshot(client):
    res = client.get("/api/market/map")
    assert res.status_code == 200
    data = res.json()
    assert "treemap" in data
    assert "top_sectors_by_gainer" in data
    assert data["total_turnover_cr"] > 100
    assert data["total_companies"] > 50

    sectors = {s["name"]: s for s in data["treemap"]}
    assert "Textile" in sectors
    assert "Insurance" in sectors
    assert "Bank" in sectors
    assert "Engineering" in sectors

    textile_symbols = {c["symbol"] for c in sectors["Textile"]["companies"]}
    assert {"MATINSPINN", "ENVOYTEX", "SAIHAMTEX"} <= textile_symbols

    # Top sectors by gainer
    gainers = data["top_sectors_by_gainer"]
    assert len(gainers) >= 15
    # First sector has high up count
    assert gainers[0]["up"] >= gainers[-1]["up"]

    # Verify /api/portfolio includes market_map
    snap = client.get("/api/portfolio").json()
    assert "market_map" in snap
    assert snap["market_map"]["total_turnover_cr"] == data["total_turnover_cr"]


def test_automation_config_endpoint(client):
    # 1. Switch to SIDE_BY_SIDE_LIVE mode
    res = client.post("/api/automation/config", json={
        "automation_enabled": True,
        "ingestion_mode": "SIDE_BY_SIDE_LIVE",
        "polling_interval_sec": 60,
    })
    assert res.status_code == 200
    data = res.json()
    assert data["automation_enabled"] is True
    assert data["paused"] is False
    assert data["ingestion_mode"] == "SIDE_BY_SIDE_LIVE"
    assert data["polling_interval_sec"] == 60
    assert data["adapter"]["mode"] == "SIDE_BY_SIDE_LIVE"

    snap = client.get("/api/portfolio").json()
    assert snap["app"]["ingestion_mode"] == "SIDE_BY_SIDE_LIVE"
    assert snap["app"]["automation_enabled"] is True
    assert snap["adapter"]["mode"] == "SIDE_BY_SIDE_LIVE"

    # 2. Switch back to BACKGROUND_POLLING mode with 180s
    res2 = client.post("/api/automation/config", json={
        "automation_enabled": True,
        "ingestion_mode": "BACKGROUND_POLLING",
        "polling_interval_sec": 180,
    })
    assert res2.status_code == 200
    assert res2.json()["ingestion_mode"] == "BACKGROUND_POLLING"
    assert res2.json()["polling_interval_sec"] == 180

    # 3. Disable automation (Master OFF)
    res3 = client.post("/api/automation/config", json={
        "automation_enabled": False,
        "ingestion_mode": "BACKGROUND_POLLING",
        "polling_interval_sec": 120,
    })
    assert res3.status_code == 200
    assert res3.json()["automation_enabled"] is False
    assert res3.json()["paused"] is True
    assert client.post("/api/automation/cycle").status_code == 409

    # 4. Input validation (interval out of bounds or invalid mode)
    assert client.post("/api/automation/config", json={
        "automation_enabled": True,
        "ingestion_mode": "BACKGROUND_POLLING",
        "polling_interval_sec": 10,  # Below 30
    }).status_code == 422

    assert client.post("/api/automation/config", json={
        "automation_enabled": True,
        "ingestion_mode": "INVALID_MODE",
        "polling_interval_sec": 120,
    }).status_code == 422


def test_system_changes_and_conversations(client):
    changes = client.get("/api/system/changes").json()
    assert "files_changed" in changes
    assert "checkpoints" in changes
    assert "changes" in changes
    conv_list = client.get("/api/hermes/conversations").json()
    assert "conversations" in conv_list


def test_auth_operator_login_and_session(client):
    # Invalid credentials
    bad = client.post("/api/auth/login", json={"username": "test_operator", "password": "wrong"}).status_code
    assert bad == 401

    # Valid operator credentials
    res = client.post("/api/auth/login", json={"username": "test_operator", "password": "test_password_123"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["user"]["name"] == "Hasibur Rahman"
    assert data["user"]["username"] == "test_operator"
    token = data["token"]
    assert token.startswith("hb-sess-")

    # Check session endpoint with token
    sess = client.get("/api/auth/session", headers={"Authorization": f"Bearer {token}"}).json()
    assert sess["authenticated"] is True
    assert sess["user"]["username"] == "test_operator"

    # Logout
    logout = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"}).json()
    assert logout["status"] == "ok"


def test_api_keys_and_telemetry(client):
    # Fetch keys info
    keys = client.get("/api/settings/keys").json()
    assert "openrouter_key_masked" in keys
    assert "daily_call_limit" in keys
    assert "daily_calls_used" in keys
    assert "guardrail_status" in keys
    assert keys["guardrail_status"] == "ZERO-SECRET-READ ACTIVE"

    # Update keys and limit
    update_res = client.post("/api/settings/keys", json={
        "openrouter_key": "sk-or-v1-fake-openrouter-key-12345678",
        "gemini_key": "AIzaSy-fake-gemini-key-12345678",
        "telegram_bot_token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
        "telegram_chat_id": "987654321",
        "daily_call_limit": 50,
    }).json()
    assert update_res["status"] == "ok"
    assert len(update_res["updated_fields"]) >= 4

    # Verify updated keys
    after = client.get("/api/settings/keys").json()
    assert after["daily_call_limit"] == 50
    assert after["openrouter_configured"] is True
    assert after["gemini_configured"] is True
    assert "sk-o...5678" in after["openrouter_key_masked"]


def test_onscreen_live_mode_config(client):
    res = client.post("/api/automation/config", json={
        "automation_enabled": True,
        "ingestion_mode": "ONSCREEN_LIVE",
        "polling_interval_sec": 60,
    }).json()
    assert res["ingestion_mode"] == "ONSCREEN_LIVE"
    assert res["automation_enabled"] is True
    assert "Method B: Onscreen Live Mode" in res["adapter"]["description"]


def test_api_health_telemetry(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "gateway" in data
    assert "kernel" in data
    assert "stocknow" in data
    assert data["kernel"]["status"] == "online"
    assert "status" in data["gateway"]
    assert "state" in data["stocknow"]


def test_hermes_models_and_switcher(client):
    res = client.get("/api/hermes/models")
    assert res.status_code == 200
    data = res.json()
    assert "active_model" in data
    assert "active_provider" in data
    assert len(data["models"]) >= 5

    switch_res = client.post("/api/hermes/model", json={"model": "deepseek/deepseek-chat", "provider": "openrouter"})
    assert switch_res.status_code == 200
    s_data = switch_res.json()
    assert s_data["status"] == "ok"
    assert s_data["active_model"] == "deepseek/deepseek-chat"
    assert s_data["active_provider"] == "openrouter"

    # Reset back to default
    client.post("/api/hermes/model", json={"model": "gemini-3.1-flash-lite", "provider": "gemini"})








