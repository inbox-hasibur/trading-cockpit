"""Hermes OS - Official NousResearch/hermes-agent Core & Agent-Curated Memory Engine.

Provides:
- MemoryCurator: USER.md, MEMORY.md disk persistence, SQLite FTS5 search, and context compression (>50% -> 20%)
- SkillLoader: Versioned YAML frontmatter skill loader and on-demand matching
- HermesOSAgentLoop: Core agent conversation and ReAct execution loop
- HermesConfig: Provider-agnostic model routing (OpenRouter / Google Gemini / Local)
"""

from backend.hermes_os.agent_loop import HermesOSAgentLoop
from backend.hermes_os.config import (
    HermesConfig,
    ensure_hermes_state_dir,
    get_hermes_home,
    load_hermes_config,
)
from backend.hermes_os.memory_curator import MemoryCurator
from backend.hermes_os.skill_learner import SkillLearner, bump_version
from backend.hermes_os.skill_loader import Skill, SkillLoader
from backend.hermes_os.toolsets import (
    HermesToolRegistry,
    ToolContext,
    ToolDefinition,
    default_registry,
)

__all__ = [
    "HermesOSAgentLoop",
    "HermesConfig",
    "ensure_hermes_state_dir",
    "get_hermes_home",
    "load_hermes_config",
    "MemoryCurator",
    "SkillLoader",
    "SkillLearner",
    "Skill",
    "bump_version",
    "HermesToolRegistry",
    "ToolContext",
    "ToolDefinition",
    "default_registry",
]

