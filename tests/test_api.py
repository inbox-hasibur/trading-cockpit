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


def test_local_chat_and_api_security(client):
    count = client.get("/api/portfolio").json()["trade_count"]
    reply = client.post("/api/chat", json={"message": "Portfolio kemon ache?"}).json()
    assert reply["provider"] == "local" and "DEMO" in reply["reply"]
    assert client.get("/api/portfolio").json()["trade_count"] == count
    assert client.post("/api/automation/cycle", headers={"Origin": "https://evil.example"}).status_code == 403


def test_openrouter_mock_and_call_limit(settings):
    app = create_app(replace(settings, openrouter_api_key="test-key", chat_daily_call_limit=1))
    requests = []

    def respond(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "Demo response"}}]})

    app.state.chat.transport = httpx.MockTransport(respond)
    with TestClient(app, base_url="http://localhost") as client:
        first = client.post("/api/chat", json={"message": "status"}).json()
        second = client.post("/api/chat", json={"message": "status"}).json()
        assert first["provider"] == "openrouter" and first["reply"] == "Demo response"
        assert second["provider"] == "local" and len(requests) == 1
        assert "SYNTHETIC" in requests[0]["messages"][0]["content"]
        assert "tools" not in requests[0]


def test_agentic_emergency_quarantine_and_canary(client):
    before = client.get("/api/portfolio").json()
    squr = next(c for c in before["companies"] if c["symbol"] == "SQURPHARMA")
    assert not squr["quarantined"]
    assert squr["holding_qty"] > 0

    # User alerts Hermes of imminent ruin/bankruptcy
    msg = "Ajke SQURPHARMA er onek boro khoti hoye geche, 1 month e deulia hoye jabe"
    res = client.post("/api/chat", json={"message": msg}).json()

    assert res["agentic_action"] == "EMERGENCY_QUARANTINE"
    assert "CRASH_QUARANTINE" in res["reply"] or "ক্যানারি" in res["reply"]

    after = client.get("/api/portfolio").json()
    after_squr = next(c for c in after["companies"] if c["symbol"] == "SQURPHARMA")
    assert after_squr["quarantined"]
    assert after_squr["holding_qty"] < squr["holding_qty"]
    # 10% canary preserved
    assert after_squr["holding_qty"] >= 1

    # Check canary theses registered
    assert len(after["canary_theses"]) >= 1
    thesis = after["canary_theses"][0]
    assert thesis["symbol"] == "SQURPHARMA"
    assert thesis["status"] == "OBSERVING"

    # Now restore from quarantine
    restore_res = client.post("/api/chat", json={"message": "SQURPHARMA ekhon valoe ashe restore koro"}).json()
    assert restore_res["agentic_action"] == "RESTORE_QUARANTINE"

    restored = client.get("/api/portfolio").json()
    restored_squr = next(c for c in restored["companies"] if c["symbol"] == "SQURPHARMA")
    assert not restored_squr["quarantined"]


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


def test_hermes_automation_config_chat_and_rollback(client):
    # 1. Instruct Hermes to switch to side by side mode
    chat_res = client.post("/api/chat", json={"message": "Switch to side by side mode"}).json()
    assert chat_res["tool_executed"] == "set_automation_config"
    assert chat_res["tool_result"]["ingestion_mode"] == "SIDE_BY_SIDE_LIVE"

    snap = client.get("/api/portfolio").json()
    assert snap["app"]["ingestion_mode"] == "SIDE_BY_SIDE_LIVE"

    # 2. Instruct Hermes to switch to 60s background polling
    chat_res2 = client.post("/api/chat", json={"message": "Background polling 60s koro"}).json()
    assert chat_res2["tool_executed"] == "set_automation_config"
    assert chat_res2["tool_result"]["ingestion_mode"] == "BACKGROUND_POLLING"
    assert chat_res2["tool_result"]["polling_interval_sec"] == 60

    snap2 = client.get("/api/portfolio").json()
    assert snap2["app"]["ingestion_mode"] == "BACKGROUND_POLLING"
    assert snap2["app"]["polling_interval_sec"] == 60

    # 3. Rollback the last checkpoint
    rollback_res = client.post("/api/hermes/rollback").json()
    assert rollback_res["action_reverted"] == "SET_AUTOMATION_CONFIG"

    snap3 = client.get("/api/portfolio").json()
    assert snap3["app"]["ingestion_mode"] == "SIDE_BY_SIDE_LIVE"


def test_generate_code_map_script():
    from scripts.generate_code_map import generate_markdown, OUTPUT_FILE
    generate_markdown()
    assert OUTPUT_FILE.exists()
    content = OUTPUT_FILE.read_text(encoding="utf-8")
    assert "# 🗺️ Codebase AST Map & System Architecture Radar" in content
    assert "Repository Topology & File Metrics" in content
    assert "Database Schema X-Ray" in content
    assert "FastAPI Route Registry" in content
    assert "Code Health & Complexity Radar" in content
    assert "PortfolioState" in content
    assert "/api/automation/config" in content


def test_hermes_conversations_and_system_changes(client):
    # 1. Create a conversation thread
    create_res = client.post("/api/hermes/conversations", json={"title": "Macro Strategy 2026"}).json()
    conv_id = create_res["id"]
    assert conv_id
    assert create_res["title"] == "Macro Strategy 2026"

    # 2. List conversations
    conv_list = client.get("/api/hermes/conversations").json()
    assert any(c["id"] == conv_id for c in conv_list["conversations"])

    # 3. Chat with conversation_id
    chat_res = client.post("/api/chat", json={
        "message": "Portfolio kemon ache?",
        "conversation_id": conv_id,
    }).json()
    assert chat_res["reply"]
    assert chat_res["conversation_id"] == conv_id

    # 4. Fetch conversation messages
    msgs_res = client.get(f"/api/hermes/conversations/{conv_id}/messages").json()
    assert len(msgs_res["messages"]) >= 2  # user + assistant

    # 5. Check system changes endpoint
    changes = client.get("/api/system/changes").json()
    assert "files_changed" in changes
    assert "checkpoints" in changes
    assert changes["total_files"] >= 1




