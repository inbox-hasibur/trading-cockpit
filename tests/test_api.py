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



