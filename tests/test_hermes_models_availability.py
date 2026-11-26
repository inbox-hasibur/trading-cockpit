"""Tests for Hermes free AI model catalog, provider key availability, and disabled UI rendering."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.database import Database
from backend.main import create_app
from backend.routes_hermes import PROVIDER_KEY_ENV_MAP


@pytest.fixture
def client(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "test_hermes_models.db"
    for keys in PROVIDER_KEY_ENV_MAP.values():
        for k in keys:
            monkeypatch.delenv(k, raising=False)

    settings = Settings(
        database_url=f"sqlite:///{db_path.as_posix()}",
        cockpit_api_token="",
        gemini_api_key="",
        openrouter_api_key="",
        telegram_bot_token="",
        telegram_chat_id="",
    )
    app = create_app(settings=settings)
    with TestClient(app, base_url="http://127.0.0.1") as tc:
        yield tc


def test_models_catalog_includes_all_free_providers(client: TestClient):
    with patch("backend.routes_hermes._read_configured_env_keys", return_value=set()):
        resp = client.get("/api/hermes/models")
    assert resp.status_code == 200
    data = resp.json()
    models = data["models"]
    providers = {m["provider"] for m in models}
    assert providers == {"gemini", "groq", "mistral", "cerebras", "sambanova", "openrouter", "cloudflare"}

    ids = {(m["provider"], m["id"]) for m in models}
    assert ("gemini", "gemini-3.8-flash") not in ids
    assert ("gemini", "gemini-3.6-flash") not in ids
    expected = {
        ("gemini", "gemini-2.5-pro"),
        ("gemini", "gemini-3.5-flash-lite"),
        ("gemini", "gemini-3.1-flash-lite"),
        ("gemini", "gemini-3-flash-preview"),
        ("groq", "openai/gpt-oss-120b"),
        ("groq", "qwen/qwen3.8-27b"),
        ("groq", "llama-3.3-70b-versatile"),
        ("groq", "kimi-k2-instruct"),
        ("mistral", "mistral-large-latest"),
        ("mistral", "codestral-latest"),
        ("mistral", "mistral-small-latest"),
        ("cerebras", "gpt-oss-120b"),
        ("cerebras", "qwen-3.8-27b"),
        ("sambanova", "DeepSeek-V3.1"),
        ("sambanova", "gpt-oss-120b"),
        ("sambanova", "Meta-Llama-3.3-70B-Instruct"),
        ("openrouter", "openrouter/free"),
        ("openrouter", "nvidia/nemotron-3-nano-30b-a3b:free"),
        ("cloudflare", "@cf/openai/gpt-oss-120b"),
        ("cloudflare", "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b"),
    }
    assert expected.issubset(ids)
    assert all(m["available"] is False for m in models)
    assert all(m["unavailable_reason"] for m in models)
    assert all(isinstance(m["intelligence"], int) and m["intelligence"] > 0 for m in models)
    assert all(m["intel_tier"] for m in models)


def test_models_availability_respects_configured_keys(client: TestClient, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    with patch("backend.routes_hermes._read_configured_env_keys", return_value={"GEMINI_API_KEY", "GROQ_API_KEY"}):
        resp = client.get("/api/hermes/models")
    assert resp.status_code == 200
    models = resp.json()["models"]
    for m in models:
        if m["provider"] in ("gemini", "groq"):
            assert m["available"] is True
            assert m["unavailable_reason"] == ""
        else:
            assert m["available"] is False
            assert "Missing" in m["unavailable_reason"]


def test_switch_model_blocks_unavailable_and_allows_available(client: TestClient, monkeypatch):
    with patch("backend.routes_hermes._read_configured_env_keys", return_value=set()):
        resp_blocked = client.post(
            "/api/hermes/model",
            json={"model": "mistral-large-latest", "provider": "mistral"},
        )
    assert resp_blocked.status_code == 400
    assert "Missing MISTRAL_API_KEY" in resp_blocked.json()["detail"]

    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    fake_hdir = client.app.state if hasattr(client, "app") else None
    with (
        patch("backend.routes_hermes._read_configured_env_keys", return_value={"GROQ_API_KEY"}),
        patch("backend.routes_hermes.subprocess.run"),
        patch("backend.hermes_bridge.get_hermes_dir", return_value=Path("tests/.tmp_hermes_test")),
    ):
        resp_ok = client.post(
            "/api/hermes/model",
            json={"model": "openai/gpt-oss-120b", "provider": "groq"},
        )
    assert resp_ok.status_code == 200
    body = resp_ok.json()
    assert body["active_model"] == "openai/gpt-oss-120b"
    assert body["active_provider"] == "groq"


def test_hermes_ui_grays_out_unavailable_models_in_dropdown():
    hermes_js = Path("frontend/hermes_ui.js").read_text(encoding="utf-8")
    styles_css = Path("frontend/styles.css").read_text(encoding="utf-8")
    light_css = Path("frontend/theme_light_hermes.css").read_text(encoding="utf-8")

    assert "is-unavailable" in hermes_js
    assert 'disabled aria-disabled="true"' in hermes_js
    assert "No Access" in hermes_js
    assert "model-iq-track" in hermes_js
    assert ".model-dropup-item.is-unavailable" in styles_css
    assert ".model-dropup-item.is-unavailable" in light_css
