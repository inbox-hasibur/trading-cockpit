from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.database import CompanyProfile, CustomRule, HermesSkillRevision, HermesStateCheckpoint
from backend.hermes.agent_loop import CheckpointManager
from backend.hermes.memory import HermesMemory
from backend.hermes.secret_guard import SecretGuard, SecurityViolation, redact_secrets
from backend.hermes.skills_manager import SkillsManager
from backend.main import create_app


def test_secret_guard_isolation_and_redaction():
    # 1. Block access to sensitive files
    with pytest.raises(SecurityViolation):
        SecretGuard.assert_safe_path(".env")
    with pytest.raises(SecurityViolation):
        SecretGuard.assert_safe_path(".env.local")
    with pytest.raises(SecurityViolation):
        SecretGuard.assert_safe_path("config/auth.json")
    with pytest.raises(SecurityViolation):
        SecretGuard.assert_safe_path("browser_profile/cookies.sqlite")
    with pytest.raises(SecurityViolation):
        SecretGuard.assert_safe_path("backend/data/hummingbird.db")

    # Safe files are permitted
    safe_path = Path("documentation/About_Project.md")
    assert SecretGuard.assert_safe_path(safe_path) == safe_path.resolve()

    # 2. Token scrubbing
    sample_text = (
        "Using OpenRouter sk-or-v1-abcdef1234567890abcdef1234567890 and key sk-99887766554433221100. "
        "Authorization: Bearer secret_session_token_12345"
    )
    redacted = redact_secrets(sample_text)
    assert "sk-or-v1-" not in redacted
    assert "sk-998877" not in redacted
    assert "secret_session_token" not in redacted
    assert "[REDACTED_OPENROUTER_KEY]" in redacted
    assert "[REDACTED_API_KEY]" in redacted
    assert "[REDACTED_TOKEN]" in redacted


def test_skills_engine_on_demand_and_self_patch(tmp_path):
    mgr = SkillsManager()
    skills = mgr.list_skills()
    skill_names = {s.name for s in skills}
    assert {"SKILL_gsc_tiers", "SKILL_canary_90_10", "SKILL_sequential_no_regret", "SKILL_stocknow_dse_quirks"} <= skill_names

    # Test keyword matching
    matched = mgr.match_skills("Tell me about GSC tiers and momentum scalp")
    assert any("gsc_tiers" in s.name for s in matched)

    canary_matched = mgr.match_skills("Company collapse and insolvency threat")
    assert any("canary_90_10" in s.name for s in canary_matched)


def test_three_layer_memory(settings):
    app = create_app(settings)
    with TestClient(app) as client:
        with app.state.database.write() as session:
            memory = HermesMemory(session)

            # Layer 1: User Profile
            prof = memory.get_user_profile()
            assert prof["operator_name"] == "Hasibur"
            assert "Strict No-Loss" in prof["risk_posture"]
            layer1_text = memory.format_layer_1_prompt()
            assert "OPERATOR DIRECTIVES" in layer1_text

            # Layer 2: Session memory & search
            today = date(2026, 11, 4)
            memory.record_turn(today, "user", "How is GP curve behaving?", symbol_mentioned="GP")
            memory.record_turn(today, "assistant", "GP is oscillating near support at ৳265", symbol_mentioned="GP")

            search_results = memory.search_sessions("GP curve")
            assert len(search_results) >= 1
            assert "GP" in search_results[0]["content"]

            # Layer 3: Durable company facts
            memory.record_fact("GP", "Market leader with solid dividend payout", "FUNDAMENTAL", "HIGH")
            recalled = memory.recall_facts_for_symbol("GP")
            assert any("Market leader" in f.get("fact", "") for f in recalled)
            layer3_text = memory.format_layer_3_prompt(["GP"])
            assert "Market leader" in layer3_text


def test_state_checkpoint_and_rollback(client):
    # Set initial state
    before = client.get("/api/portfolio").json()
    gp = next(c for c in before["companies"] if c["symbol"] == "GP")
    assert not gp["quarantined"]
    assert gp["watchlist_category"] == "GSC"

    # 1. Move GP to GSC_L2 via Hermes
    res_tier = client.post("/api/chat", json={"message": "GP-ke GSC_L2 swing scalp tier-e move koro"}).json()
    assert res_tier["agentic_action"] == "SET_WATCHLIST_TIER"

    after_tier = client.get("/api/portfolio").json()
    gp_tier = next(c for c in after_tier["companies"] if c["symbol"] == "GP")
    assert gp_tier["watchlist_category"] == "GSC_L2"

    # Verify checkpoint registered
    assert len(after_tier["hermes"]["checkpoints"]) >= 1

    # 2. Rollback via /rollback in chat
    res_rollback = client.post("/api/chat", json={"message": "/rollback"}).json()
    assert res_rollback["agentic_action"] == "ROLLBACK"

    after_rollback = client.get("/api/portfolio").json()
    gp_restored = next(c for c in after_rollback["companies"] if c["symbol"] == "GP")
    assert gp_restored["watchlist_category"] == "GSC"

    # 3. Test explicit API endpoint /api/hermes/rollback
    # Emergency threat to create checkpoint
    res_threat = client.post("/api/chat", json={"message": "GP er khoti hoye geche deulia hobe"}).json()
    assert res_threat["agentic_action"] == "EMERGENCY_QUARANTINE"

    after_threat = client.get("/api/portfolio").json()
    gp_threatened = next(c for c in after_threat["companies"] if c["symbol"] == "GP")
    assert gp_threatened["quarantined"]

    # Call /api/hermes/rollback
    rb_api = client.post("/api/hermes/rollback").json()
    assert rb_api["action_reverted"] == "REPORT_THREAT"

    after_rb = client.get("/api/portfolio").json()
    gp_restored2 = next(c for c in after_rb["companies"] if c["symbol"] == "GP")
    assert not gp_restored2["quarantined"]


def test_teach_lesson_self_improving_skill(client):
    # Teach Hermes a new trading insight
    msg = "Hermes mone rakhba: Sunday sokal 10 tay DSE te market open hole 10:15 porjonto trade na kora bhalo."
    res = client.post("/api/chat", json={"message": msg}).json()
    assert res["agentic_action"] == "LEARN_SKILL"

    snap = client.get("/api/portfolio").json()
    skills = snap["hermes"]["skills"]
    assert any("learned_rule" in s["name"] for s in skills)


def test_hermes_model_switching_and_aliases(client):
    # Test switching via chat with alias "mimov2.6 pro"
    res1 = client.post("/api/chat", json={"message": "/model mimov2.6 pro"}).json()
    assert res1["agentic_action"] == "SET_AI_MODEL"
    assert res1["tool_result"]["active_model"] == "xiaomi/mimo-v2.6-pro"

    # Test switching via chat with alias "deepseek 4.1 flash"
    res2 = client.post("/api/chat", json={"message": "/model deepseek 4.1 flash"}).json()
    assert res2["agentic_action"] == "SET_AI_MODEL"
    assert res2["tool_result"]["active_model"] == "deepseek/deepseek-chat"

    # Test switching via chat with alias "gemini lite"
    res3 = client.post("/api/chat", json={"message": "/model gemini lite"}).json()
    assert res3["agentic_action"] == "SET_AI_MODEL"
    assert res3["tool_result"]["active_model"] == "google/gemini-3.1-flash-lite"

    # Test direct POST /api/hermes/model endpoint
    res4 = client.post("/api/hermes/model", json={"model": "google/gemini-3.5-flash"}).json()
    assert res4["status"] == "ok"
    assert res4["active_model"] == "google/gemini-3.5-flash"

    # Verify model catalog GET /api/hermes/models
    catalog = client.get("/api/hermes/models").json()
    assert catalog["active_model"] == "google/gemini-3.5-flash"
    model_ids = [m["id"] for m in catalog["models"]]
    assert "xiaomi/mimo-v2.6-pro" in model_ids
    assert "deepseek/deepseek-chat" in model_ids
    assert "google/gemini-3.1-flash-lite" in model_ids


def test_gemini_multi_key_rotation_on_429(settings):
    import asyncio
    import httpx
    from backend.hermes.agent_loop import HermesAgentLoop
    from backend.main import create_app

    # Configure multiple keys separated by comma
    object.__setattr__(settings, "gemini_api_key", "key_first_429, key_second_ok")
    object.__setattr__(settings, "openrouter_api_key", "")

    app = create_app(settings)
    with TestClient(app):
        db = app.state.database

        # Create mock transport: key_first_429 returns 429, key_second_ok returns 200
        call_log = []

        def mock_handler(request: httpx.Request):
            url_str = str(request.url)
            call_log.append(url_str)
            if "key_first_429" in url_str:
                return httpx.Response(429, json={"error": {"code": 429, "message": "Resource has been exhausted."}})
            elif "key_second_ok" in url_str:
                return httpx.Response(200, json={
                    "candidates": [{"content": {"parts": [{"text": "Hello from Gemini Key 2! Market looks healthy."}]}}]
                })
            return httpx.Response(500)

        transport = httpx.MockTransport(mock_handler)
        agent = HermesAgentLoop(db, settings, transport=transport)

        assert agent.get_gemini_keys() == ["key_first_429", "key_second_ok"]

        turn_res = asyncio.run(agent.run_turn("What is your analysis of current DSE market?", history=[]))
        assert turn_res["provider"] == "gemini"
        assert "Hello from Gemini Key 2" in turn_res["reply"]
        assert "Key #2/2" in turn_res["warning"]
        assert len(call_log) >= 2
