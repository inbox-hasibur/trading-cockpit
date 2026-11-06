"""Provider-agnostic Configuration & State Layout for Hermes OS.

Vendored and adapted from official NousResearch/hermes-agent architecture.
Manages persistent state isolated under `backend/data/.hermes/` outside git/OneDrive locks.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from backend.hermes.secret_guard import SecretGuard

DEFAULT_CONFIG_YAML = """# Hermes OS Model Router & System Configuration
# Provider-agnostic router supporting OpenRouter, Google Gemini, and Local Brain.

models:
  primary: "xiaomi/mimo-v2.6-pro"
  openrouter:
    - id: "xiaomi/mimo-v2.6-pro"
      name: "Xiaomi MiMo-v2.6-Pro (Primary Brain)"
      tier: 1
    - id: "xiaomi/mimo-v2.6-flash"
      name: "Xiaomi MiMo-v2.6-Flash (Ultra Fast)"
      tier: 1
    - id: "deepseek/deepseek-chat"
      name: "DeepSeek V3 / 4.1 Flash (Deep Reasoning)"
      tier: 1
    - id: "deepseek/deepseek-r1"
      name: "DeepSeek R1 (Reasoning / Math)"
      tier: 1
    - id: "meta-llama/llama-3.3-70b-instruct"
      name: "Llama 3.3 70B (High Precision)"
      tier: 1
    - id: "anthropic/claude-3.5-sonnet"
      name: "Claude 3.5 Sonnet (Elite Quant)"
      tier: 1
  gemini:
    - id: "google/gemini-3.1-flash-lite"
      name: "Google Gemini 3.1 Flash-Lite (Fastest ~1.5s)"
      tier: 2
    - id: "google/gemini-3.5-flash"
      name: "Google Gemini 3.5 Flash (Balanced Analysis)"
      tier: 2
    - id: "google/gemini-3.8-flash"
      name: "Google Gemini 3.8 Flash (Latest Preview)"
      tier: 2
    - id: "google/gemini-3.7-flash"
      name: "Google Gemini 3.7 Flash (Hybrid Reasoning)"
      tier: 2
  local:
    - id: "local-quant-brain"
      name: "Local Deterministic Quant Brain ($0 Offline)"
      tier: 3

memory:
  user_profile_enabled: true
  working_memory_enabled: true
  fts_enabled: true
  compression_threshold: 0.50   # Trigger compression when context fill > 50%
  compression_target: 0.20      # Target 20% context fill after compression
  max_context_tokens: 8000
  max_memory_lines: 250

skills:
  auto_load: true
  skills_dir: "skills"
  max_injected_skills: 3
"""

DEFAULT_USER_MD = """# OPERATOR PROFILE: HASIBUR
*Agent-curated profile maintained by Hermes OS*

## Identity & Workspace
- **Operator Name:** Hasibur Rahman
- **Market:** Dhaka Stock Exchange (DSE), Bangladesh
- **Execution Target:** StockNow Virtual Portfolio #164580 ("Humming Bird")
- **Language Preference:** Bangla, Banglish, English (multilingual understanding)
- **Role:** Autonomous Share Portfolio Co-Pilot & Risk Guardian

## Risk Posture & Execution Rules
- **Strict Capital Preservation:** Never panic-sell at a net loss (< 0% after 1% round-trip brokerage fee).
- **Emergency 90/10 Protocol:** On verified bankruptcy or catastrophic thesis alert, quarantine stock immediately, lock in 90% profit if positive, and hold 10% canary probe.
- **T+2 Rolling Capital:** Respect T+2 clearing cycles (Buckets A, B, C) to ensure cash liquidity for rotation.
- **Watchlist Tiers:** Focus on Big Giant Stable (GSC) blue chips. Prioritize GSC_L1 for long-term turnaround comeback and GSC_L2 for short-term swing fluctuation.

## Learned Preferences
"""

DEFAULT_MEMORY_MD = """# HERMES WORKING CONTEXT & MARKET MEMORY
*Agent-curated working context and cross-session knowledge scratchpad.*

## Active Portfolio State (#164580 - Humming Bird)
- **Tracked Holdings:** BANKASIA (138 sh @ ৳17.09), IBNSINA (16 sh @ ৳304.31), MATINSPINN (206 sh @ ৳97.89).
- **Available Cash:** ~৳107,596.00 settled cash.
- **Round-trip Breakeven:** 0.50% buy fee + 0.50% sell fee = ~1.005% gross gain required.

## DSE Market Facts & Quirks
- **Trading Session:** 10:00 AM to 2:30 PM (Asia/Dhaka timezone).
- **Settlement Rule:** T+2 rolling settlement in Bangladesh equity market.
- **Circuit Breaker:** Standard 10% daily price band (subject to floor price rules).
- **StockNow Automation:** Playwright CDP handles visible browser DOM orders at `/portfolios/164580/buy` and `/sell`.

## Distilled Market Notes & Theses
"""


def get_hermes_home(custom_path: Path | str | None = None) -> Path:
    """Returns the isolated runtime state directory for Hermes OS."""
    if custom_path:
        target = Path(custom_path).resolve()
    elif os.getenv("HERMES_HOME"):
        target = Path(os.getenv("HERMES_HOME")).resolve()
    else:
        # Default: backend/data/.hermes/
        target = Path(__file__).resolve().parent.parent / "data" / ".hermes"

    # Enforce SecretGuard on base path
    SecretGuard.assert_safe_path(target)
    return target


def ensure_hermes_state_dir(hermes_dir: Path | str | None = None) -> Path:
    """Initializes the official Hermes state directory layout."""
    home = get_hermes_home(hermes_dir)
    home.mkdir(parents=True, exist_ok=True)

    config_file = home / "config.yaml"
    if not config_file.exists():
        config_file.write_text(DEFAULT_CONFIG_YAML, encoding="utf-8")

    user_file = home / "USER.md"
    if not user_file.exists():
        user_file.write_text(DEFAULT_USER_MD, encoding="utf-8")

    memory_file = home / "MEMORY.md"
    if not memory_file.exists():
        memory_file.write_text(DEFAULT_MEMORY_MD, encoding="utf-8")

    skills_dir = home / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    # Seed initial skills from backend/hermes/skills if present and skills_dir is empty
    source_skills = Path(__file__).resolve().parent.parent / "hermes" / "skills"
    if source_skills.is_dir():
        for sf in source_skills.glob("SKILL_*.md"):
            dest_f = skills_dir / sf.name
            if not dest_f.exists():
                dest_f.write_text(sf.read_text(encoding="utf-8"), encoding="utf-8")

    return home


@dataclass
class HermesConfig:
    home_dir: Path
    models: dict[str, Any] = field(default_factory=dict)
    memory: dict[str, Any] = field(default_factory=dict)
    skills: dict[str, Any] = field(default_factory=dict)

    @property
    def primary_model(self) -> str:
        return self.models.get("primary", "xiaomi/mimo-v2.6-pro")

    @property
    def active_model(self) -> str:
        return self.primary_model

    @property
    def fallback_chain(self) -> list[dict[str, Any]]:
        return [
            {"tier": 1, "name": "Primary Brain", "target": self.primary_model},
            {"tier": 2, "name": "1st Fallback", "target": "google/gemini-3.1-flash-lite"},
            {"tier": 3, "name": "2nd Fallback", "target": "local-quant-brain"},
        ]

    @property
    def compression_threshold(self) -> float:
        return float(self.memory.get("compression_threshold", 0.50))

    @property
    def compression_target(self) -> float:
        return float(self.memory.get("compression_target", 0.20))

    @property
    def max_context_tokens(self) -> int:
        return int(self.memory.get("max_context_tokens", 8000))

    @property
    def fts_enabled(self) -> bool:
        return bool(self.memory.get("fts_enabled", True))


def load_hermes_config(hermes_dir: Path | str | None = None) -> HermesConfig:
    """Loads and validates the Hermes configuration."""
    home = ensure_hermes_state_dir(hermes_dir)
    config_file = home / "config.yaml"
    try:
        data = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
    except Exception:
        data = yaml.safe_load(DEFAULT_CONFIG_YAML) or {}

    return HermesConfig(
        home_dir=home,
        models=data.get("models", {}),
        memory=data.get("memory", {}),
        skills=data.get("skills", {}),
    )
