"""Tests for Hermes skills origin classification: plugin vs learned vs bundled."""

from pathlib import Path
from unittest.mock import patch
import pytest

from backend.hermes_bridge import read_hermes_state, _get_bundled_skill_names


def test_hermes_skills_origin_classification(tmp_path: Path):
    """Verifies that read_hermes_state correctly classifies skills into plugin, learned, and bundled."""
    # 1. Setup mock Hermes directory and skills directory
    mock_hermes_dir = tmp_path / "hermes_home" / "profiles" / "hummingbird"
    profile_skills_dir = mock_hermes_dir / "skills"
    profile_skills_dir.mkdir(parents=True)

    # Create .bundled_manifest in profile skills
    manifest_file = profile_skills_dir / ".bundled_manifest"
    manifest_file.write_text("sample-bundled:abcdef1234567890\napple-notes:hash123\n", encoding="utf-8")

    # Create a bundled skill in profile
    bundled_skill_dir = profile_skills_dir / "sample-bundled"
    bundled_skill_dir.mkdir()
    (bundled_skill_dir / "SKILL.md").write_text(
        "---\nname: sample-bundled\ndescription: Bundled utility skill\nversion: 1.0.0\n---\nSkill content",
        encoding="utf-8",
    )

    # Create a learned skill in profile (not in manifest, not in vendor)
    learned_skill_dir = profile_skills_dir / "user-custom-rule"
    learned_skill_dir.mkdir()
    (learned_skill_dir / "SKILL.md").write_text(
        "---\nname: user-custom-rule\ndescription: Custom user learned rule\nversion: 1.2.0\n---\nRule content",
        encoding="utf-8",
    )

    # 2. Setup mock Hummingbird plugin skills directory
    mock_workspace = tmp_path / "workspace"
    plugin_skills_dir = mock_workspace / "plugins" / "humming_bird" / "skills"
    plugin_skill_dir = plugin_skills_dir / "hb_trading_flow"
    plugin_skill_dir.mkdir(parents=True)
    (plugin_skill_dir / "SKILL.md").write_text(
        "---\nname: hb_trading_flow\ndescription: Plugin core execution skill\nversion: 2.0.0\n---\nPlugin content",
        encoding="utf-8",
    )

    # 3. Patch get_hermes_dir and WORKSPACE_ROOT
    with patch("backend.hermes_bridge.get_hermes_dir", return_value=mock_hermes_dir), \
         patch("backend.hermes_bridge.WORKSPACE_ROOT", mock_workspace):
        state = read_hermes_state()

    skills = state.get("skills", [])
    assert len(skills) >= 3

    by_name = {s["name"]: s for s in skills}

    # Verify Plugin skill
    assert "hb_trading_flow" in by_name
    plugin_skill = by_name["hb_trading_flow"]
    assert plugin_skill["origin"] == "plugin"
    assert plugin_skill["is_auto_learned"] is False
    assert "plugin" in plugin_skill["source"].lower()

    # Verify Bundled skill
    assert "sample-bundled" in by_name
    bundled_skill = by_name["sample-bundled"]
    assert bundled_skill["origin"] == "bundled"
    assert bundled_skill["is_auto_learned"] is False
    assert "bundled" in bundled_skill["source"].lower()

    # Verify Learned skill
    assert "user-custom-rule" in by_name
    learned_skill = by_name["user-custom-rule"]
    assert learned_skill["origin"] == "learned"
    assert learned_skill["is_auto_learned"] is True
    assert "profile skill" in learned_skill["source"].lower() or "learned" in learned_skill["source"].lower()


def test_bundled_skill_fallback_to_vendor(tmp_path: Path):
    """When .bundled_manifest does not exist, bundled skills fallback to vendor/hermes-agent/skills."""
    mock_skills_dir = tmp_path / "skills"
    mock_skills_dir.mkdir()
    # No .bundled_manifest created here

    # Test vendor fallback resolution
    bundled_names = _get_bundled_skill_names(skills_root=mock_skills_dir)
    # apple-notes is a known bundled skill inside vendor/hermes-agent/skills
    assert "apple-notes" in bundled_names
    assert "user-unknown-custom-skill" not in bundled_names

