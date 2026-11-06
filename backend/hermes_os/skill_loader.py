"""Skill Loader & YAML Frontmatter Parser for Hermes OS.

Vendored and adapted from NousResearch/hermes-agent skill execution patterns.
Loads modular, on-demand markdown skills with YAML frontmatter tags and triggers.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from backend.hermes.secret_guard import SecretGuard, redact_secrets
from backend.hermes_os.config import ensure_hermes_state_dir

logger = logging.getLogger(__name__)

FRONTMATTER_PATTERN = re.compile(r"^---\s*[\r\n]+(.*?)\s*[\r\n]+---\s*[\r\n]+(.*)$", re.DOTALL)


@dataclass
class Skill:
    name: str
    description: str
    tags: list[str] = field(default_factory=list)
    triggers: list[str] = field(default_factory=list)
    body: str = ""
    filename: str = ""
    file_path: Path | None = None

    @property
    def full_content(self) -> str:
        front = {
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "triggers": self.triggers,
        }
        yaml_str = yaml.dump(front, sort_keys=False).strip()
        return f"---\n{yaml_str}\n---\n\n{self.body.strip()}\n"


class SkillLoader:
    """Manages versioned markdown skills with on-demand retrieval and execution."""

    def __init__(self, hermes_dir: Path | str | None = None):
        self.home_dir = ensure_hermes_state_dir(hermes_dir)
        self.skills_dir = self.home_dir / "skills"
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        SecretGuard.assert_safe_path(self.skills_dir)

    def list_skills(self) -> list[Skill]:
        """Loads and parses all skills found in the skills directory."""
        skills: list[Skill] = []
        for file in sorted(self.skills_dir.glob("SKILL_*.md")):
            skill = self.load_skill(file)
            if skill:
                skills.append(skill)
        return skills

    def load_skills(self) -> list[Skill]:
        """Alias for list_skills."""
        return self.list_skills()

    def load_skill(self, path: Path) -> Skill | None:
        """Parses a single skill file into a Skill object."""
        try:
            SecretGuard.assert_safe_path(path)
            raw = path.read_text(encoding="utf-8")
            m = FRONTMATTER_PATTERN.match(raw)
            if m:
                meta = yaml.safe_load(m.group(1)) or {}
                body = m.group(2).strip()
                return Skill(
                    name=str(meta.get("name", path.stem)),
                    description=str(meta.get("description", "")),
                    tags=[str(t).lower() for t in meta.get("tags", [])],
                    triggers=[str(tr).lower() for tr in meta.get("triggers", [])],
                    body=body,
                    filename=path.name,
                    file_path=path,
                )
            else:
                # Support legacy header format (# SKILL: ..., Version: ..., Tags: ...)
                lines = raw.splitlines()
                name = path.stem.replace("SKILL_", "").replace("_", " ").title()
                tags: list[str] = []
                triggers: list[str] = []
                body_lines: list[str] = []
                for line in lines:
                    if line.startswith("# SKILL:"):
                        name = line.replace("# SKILL:", "").strip()
                    elif line.lower().startswith("tags:"):
                        raw_tags = line.split(":", 1)[1]
                        tags = [t.strip().lower() for t in raw_tags.split(",") if t.strip()]
                        triggers = list(tags)
                    else:
                        body_lines.append(line)

                return Skill(
                    name=name,
                    description=f"{name} trading methodology",
                    tags=tags,
                    triggers=triggers,
                    body="\n".join(body_lines).strip(),
                    filename=path.name,
                    file_path=path,
                )
        except Exception as exc:
            logger.warning("Failed parsing skill file '%s': %s", path.name, exc)
            return None

    def match_skills(self, prompt: str, max_skills: int = 3) -> list[Skill]:
        """Matches skills based on triggers, tags, and keywords in the user prompt."""
        clean_p = prompt.lower()
        scored: list[tuple[int, Skill]] = []

        for skill in self.list_skills():
            score = 0
            # 1. Triggers match (highest weight)
            for trigger in skill.triggers:
                if trigger in clean_p:
                    score += 5
            # 2. Tags match
            for tag in skill.tags:
                if tag in clean_p:
                    score += 3
            # 3. Name keywords match
            for word in skill.name.lower().split():
                if len(word) >= 4 and word in clean_p:
                    score += 2

            if score > 0:
                scored.append((score, skill))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:max_skills]]

    def format_matched_skills_prompt(self, skills: list[Skill]) -> str:
        """Formats matched skills for injection into the system prompt."""
        if not skills:
            return ""

        sections = []
        for s in skills:
            sections.append(
                f"[ACTIVE SKILL: {s.name}]\n"
                f"Description: {s.description}\n"
                f"{s.body.strip()}"
            )
        return "\n\n".join(sections) + "\n\n"

    def save_skill(self, skill: Skill) -> Path:
        """Saves a skill to disk after zero-secret scrubbing."""
        filename = skill.filename or f"SKILL_{skill.name.lower().replace(' ', '_')}.md"
        target_path = self.skills_dir / filename
        SecretGuard.assert_safe_path(target_path)

        clean_content = redact_secrets(skill.full_content)
        target_path.write_text(clean_content, encoding="utf-8")
        skill.file_path = target_path
        skill.filename = filename
        return target_path
