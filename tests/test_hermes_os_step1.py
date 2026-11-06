"""Comprehensive tests for Hermes OS Core (NousResearch hermes-agent integration).

Step 1: State Layout, MemoryCurator (USER.md & MEMORY.md), SQLite FTS5 search,
Context Compression (>50% -> 20%), Skill Loader, and HermesMemory integration.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from backend.database import Base, Database
from backend.hermes.memory import HermesMemory
from backend.hermes.secret_guard import SecretGuard, SecurityViolation
from backend.hermes_os.config import (
    HermesConfig,
    ensure_hermes_state_dir,
    get_hermes_home,
    load_hermes_config,
)
from backend.hermes_os.memory_curator import MemoryCurator
from backend.hermes_os.skill_loader import SkillLoader
from backend.hermes_os.agent_loop import HermesOSAgentLoop


def test_hermes_state_dir_initialization(tmp_path: Path):
    """Verifies state directory creates config.yaml, USER.md, MEMORY.md, and skills."""
    state_dir = tmp_path / "hermes_test_home"
    returned_dir = ensure_hermes_state_dir(state_dir)
    assert returned_dir.exists()
    assert (returned_dir / "config.yaml").exists()
    assert (returned_dir / "USER.md").exists()
    assert (returned_dir / "MEMORY.md").exists()
    assert (returned_dir / "skills").is_dir()

    skills = list((returned_dir / "skills").glob("*.md"))
    assert len(skills) >= 4
    canary_skill = (returned_dir / "skills" / "SKILL_canary_90_10.md").read_text(encoding="utf-8")
    assert "Canary" in canary_skill or "CANARY" in canary_skill


def test_hermes_config_loading(tmp_path: Path):
    """Verifies HermesConfig loads default models, fallback chains, and context token limit."""
    state_dir = ensure_hermes_state_dir(tmp_path / "hermes_cfg")
    cfg = load_hermes_config(state_dir)
    assert isinstance(cfg, HermesConfig)
    assert cfg.active_model == "xiaomi/mimo-v2.6-pro"
    assert cfg.max_context_tokens == 8000
    assert len(cfg.fallback_chain) >= 3
    assert cfg.fallback_chain[0]["tier"] == 1
    assert cfg.fallback_chain[1]["tier"] == 2
    assert cfg.fallback_chain[2]["tier"] == 3


def test_secret_guard_safety_and_redaction(tmp_path: Path):
    """Verifies SecretGuard blocks unsafe paths and redacts secrets from USER.md and MEMORY.md."""
    state_dir = ensure_hermes_state_dir(tmp_path / "hermes_guard")
    curator = MemoryCurator(hermes_dir=state_dir)

    # Assert secret redaction in USER.md
    secret_text = "sk-or-v1-abcdef0123456789abcdef0123456789 is my key. Operator prefers MATINSPINN."
    curator.write_user_md(secret_text)
    saved_user = curator.read_user_md()
    assert "[REDACTED_OPENROUTER_KEY]" in saved_user or "sk-or-v1-***" in saved_user
    assert "abcdef0123456789" not in saved_user

    # Assert secret redaction in MEMORY.md
    curator.patch_memory("password=supersecretpass! SQURPHARMA tested support floor at 210.")
    saved_mem = curator.read_memory_md()
    assert "supersecretpass" not in saved_mem
    assert "SQURPHARMA" in saved_mem

    # Assert blocked unsafe paths (.env, passwords, etc.)
    with pytest.raises(SecurityViolation):
        curator.write_user_md_at_path = lambda p: SecretGuard.assert_safe_path(Path(".env"))
        SecretGuard.assert_safe_path(Path("c:/Users/inbox/.env"))


def test_fts5_indexing_and_search(tmp_path: Path):
    """Verifies SQLite FTS5 table indexing and high-precision full-text session search."""
    state_dir = ensure_hermes_state_dir(tmp_path / "hermes_fts")
    curator = MemoryCurator(hermes_dir=state_dir)

    curator.index_message(
        conversation_id="conv_101",
        role="user",
        content="Hasibur instructed to never sell BANKASIA at a net loss below 17.50.",
        symbol="BANKASIA",
    )
    curator.index_message(
        conversation_id="conv_101",
        role="assistant",
        content="Understood. Enforcing strict no-loss hold guard for BANKASIA at ৳17.50.",
        symbol="BANKASIA",
    )
    curator.index_message(
        conversation_id="conv_102",
        role="user",
        content="Check MATINSPINN multi-session price curve and support levels.",
        symbol="MATINSPINN",
    )

    # Search for BANKASIA
    results = curator.session_search("BANKASIA", limit=5)
    assert len(results) >= 2
    assert any("never sell BANKASIA" in r["content"] for r in results)

    # Search for MATINSPINN curve
    curve_res = curator.session_search("MATINSPINN curve", limit=2)
    assert len(curve_res) >= 1
    assert "MATINSPINN" in curve_res[0]["content"]


def test_user_preference_auto_curation(tmp_path: Path):
    """Verifies automatic curation of learned operator directives into USER.md."""
    state_dir = ensure_hermes_state_dir(tmp_path / "hermes_curate_user")
    curator = MemoryCurator(hermes_dir=state_dir)

    res = curator.curate_turn(
        role="user",
        message="Ami chai je amar order sob somoy 25% partial sell e hobe, never sell 100% at once",
    )
    assert res["user_updated"] is True
    user_content = curator.read_user_md()
    assert "never sell 100% at once" in user_content.lower() or "partial sell" in user_content.lower()


def test_market_thesis_auto_curation(tmp_path: Path):
    """Verifies automatic curation of market theses into MEMORY.md."""
    state_dir = ensure_hermes_state_dir(tmp_path / "hermes_curate_mem")
    curator = MemoryCurator(hermes_dir=state_dir)

    res = curator.curate_turn(
        role="assistant",
        message="Notice: SQURPHARMA broke below support floor 214.00; quarantining with 10% canary probe.",
        context={"symbol": "SQURPHARMA", "action": "QUARANTINE"},
    )
    assert res["memory_updated"] is True
    mem_content = curator.read_memory_md()
    assert "SQURPHARMA" in mem_content
    assert "support" in mem_content.lower() or "quarantine" in mem_content.lower()


def test_context_compression_trigger(tmp_path: Path):
    """Verifies context compression triggers when history fill > 50% and distills to <= 20%."""
    state_dir = ensure_hermes_state_dir(tmp_path / "hermes_compress")
    curator = MemoryCurator(hermes_dir=state_dir)

    # Generate message list exceeding 50% of 1000 tokens (i.e. > 500 tokens / 2000 chars)
    messages = [{"role": "system", "content": "You are Hermes assistant."}]
    for i in range(25):
        messages.append({"role": "user", "content": f"Turn {i}: Analyzing market curve for symbol BANKASIA and evaluating DSE trend depth."})
        messages.append({"role": "assistant", "content": f"Turn {i}: Observed support floor stability and booked partial gains on cycle {i}."})

    # max_tokens = 500, so 25 turns will definitely exceed 50%
    compressed, was_compressed = curator.check_and_compress_context(messages, max_tokens=500)
    assert was_compressed is True
    # The compressed list should preserve system message, a summary item, and recent turns
    assert len(compressed) <= 7
    assert any("compressed" in m["content"].lower() for m in compressed)

    # MEMORY.md should have received distilled notes from the compressed turns
    mem_content = curator.read_memory_md()
    assert "BANKASIA" in mem_content or "Session History Summary" in mem_content


def test_skill_loader_parsing_and_matching(tmp_path: Path):
    """Verifies SkillLoader parses YAML frontmatter and scores keywords/triggers."""
    state_dir = ensure_hermes_state_dir(tmp_path / "hermes_skills")
    loader = SkillLoader(state_dir)
    skills = loader.load_skills()
    assert len(skills) >= 4

    matched = loader.match_skills("Alert! Dangerous bankruptcy threat on SQURPHARMA, company is in deep trouble!")
    assert len(matched) >= 1
    # Canary 90/10 defense skill should be top matched
    assert any("canary" in s.name.lower() or "threat" in s.name.lower() or "canary" in s.filename.lower() for s in matched)


def test_hermes_memory_curator_integration(tmp_path: Path):
    """Verifies HermesMemory connects to MemoryCurator for Layer 1, 2, and 3."""
    state_dir = ensure_hermes_state_dir(tmp_path / "hermes_mem_integration")
    curator = MemoryCurator(hermes_dir=state_dir)

    db = Database("sqlite:///:memory:")
    Base.metadata.create_all(db.engine)

    with db.write() as session:
        mem = HermesMemory(session, curator=curator)

        # Layer 1 prompt should include USER.md content
        l1 = mem.format_layer_1_prompt()
        assert "OPERATOR DIRECTIVES" in l1
        assert "USER.md" in l1

        # Recording a turn indexes FTS5 and updates memory
        mem.record_turn(
            session_date=__import__("datetime").date.today(),
            role="user",
            content="Hasibur always preserves capital on DSE swing trades with T+2 buckets.",
            symbol_mentioned="DSE",
        )

        # Search sessions should retrieve via FTS5
        hits = mem.search_sessions("preserves capital")
        assert len(hits) >= 1
        assert "preserves capital" in hits[0]["content"]

        # Layer 3 prompt should include MEMORY.md
        l3 = mem.format_layer_3_prompt(["BANKASIA"])
        assert "MEMORY.md" in l3


def test_hermes_os_agent_loop_turn_preparation(tmp_path: Path):
    """Verifies HermesOSAgentLoop prepares prompt context and executes post-turn curation."""
    state_dir = ensure_hermes_state_dir(tmp_path / "hermes_loop_test")
    agent_loop = HermesOSAgentLoop(hermes_dir=state_dir)

    prepared = agent_loop.prepare_turn_messages(
        user_message="SQURPHARMA danger threat bankruptcy alert!",
        history=[{"role": "user", "content": "Hello Hermes"}, {"role": "assistant", "content": "Welcome back."}],
        conversation_id="conv_loop_1",
    )
    assert len(prepared) >= 3
    # First message is system prompt containing USER.md, MEMORY.md, and Canary skill
    assert prepared[0]["role"] == "system"
    assert "Canary" in prepared[0]["content"] or "quarantine" in prepared[0]["content"].lower()

    # Post turn
    post_res = agent_loop.post_turn(
        conversation_id="conv_loop_1",
        user_message="Always retain 10% canary probe",
        assistant_reply="Quarantining SQURPHARMA with 10% canary probe retained.",
        context={"symbol": "SQURPHARMA", "action": "QUARANTINE"},
    )
    assert post_res is not None
