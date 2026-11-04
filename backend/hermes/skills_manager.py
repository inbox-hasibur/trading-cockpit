"""Hermes Self-Improving Procedural Skills Engine.

Loads, matches, and self-patches versioned SKILL_*.md files on disk,
recording procedural learning revisions in the SQLite ledger.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Sequence

from sqlalchemy.orm import Session

from backend.database import HermesSkillRevision
from backend.hermes.secret_guard import SecretGuard

SKILLS_DIR = Path(__file__).parent / "skills"


@dataclass
class SkillDoc:
    name: str
    title: str
    version: str
    tags: list[str]
    content: str
    path: Path


class SkillsManager:
    def __init__(self, directory: Path | None = None):
        self.directory = directory or SKILLS_DIR
        self.directory.mkdir(parents=True, exist_ok=True)

    def list_skills(self) -> list[SkillDoc]:
        skills = []
        for file in sorted(self.directory.glob("SKILL_*.md")):
            SecretGuard.assert_safe_path(file)
            content = file.read_text(encoding="utf-8")
            title_match = re.search(r"^#\s+SKILL:\s*(.+)$", content, re.MULTILINE)
            version_match = re.search(r"^Version:\s*([0-9\.]+)", content, re.MULTILINE)
            tags_match = re.search(r"^Tags:\s*(.+)$", content, re.MULTILINE)

            title = title_match.group(1).strip() if title_match else file.stem
            version = version_match.group(1).strip() if version_match else "1.0.0"
            tags = [t.strip().lower() for t in tags_match.group(1).split(",")] if tags_match else []

            skills.append(SkillDoc(
                name=file.stem,
                title=title,
                version=version,
                tags=tags,
                content=content,
                path=file,
            ))
        return skills

    def match_skills(self, context_text: str, max_skills: int = 2) -> list[SkillDoc]:
        text = context_text.lower()
        all_skills = self.list_skills()
        scored = []
        for skill in all_skills:
            score = 0
            for tag in skill.tags:
                if tag in text:
                    score += 3
            # Title words
            for word in skill.title.lower().split():
                if len(word) >= 3 and word in text:
                    score += 1
            if score > 0:
                scored.append((score, skill))

        scored.sort(key=lambda item: item[0], reverse=True)
        matched = [item[1] for item in scored[:max_skills]]
        # Default fallback: if no specific match, include the core tiers and canary skills
        if not matched and all_skills:
            matched = all_skills[:2]
        return matched

    def learn_or_patch_skill(
        self,
        skill_name: str,
        lesson_markdown: str,
        reason: str,
        session: Session,
        session_date: date,
    ) -> dict:
        clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", skill_name.strip())
        if not clean_name.startswith("SKILL_"):
            clean_name = f"SKILL_{clean_name}"
        file_path = self.directory / f"{clean_name}.md"
        SecretGuard.assert_safe_path(file_path)

        new_version = 1
        if file_path.exists():
            existing_content = file_path.read_text(encoding="utf-8")
            v_match = re.search(r"^Version:\s*(\d+)\.(\d+)\.?(\d+)?", existing_content, re.MULTILINE)
            if v_match:
                major = int(v_match.group(1))
                minor = int(v_match.group(2)) + 1
                version_str = f"{major}.{minor}.0"
                new_version = minor
                updated_content = re.sub(
                    r"^Version:\s*([0-9\.]+)",
                    f"Version: {version_str}",
                    existing_content,
                    flags=re.MULTILINE,
                )
            else:
                version_str = "1.1.0"
                updated_content = f"Version: {version_str}\n" + existing_content

            patch_section = (
                f"\n\n## 📝 Learned Revision ({session_date.isoformat()}) — Version {version_str}\n"
                f"**Reason:** {reason}\n\n"
                f"{lesson_markdown.strip()}\n"
            )
            final_content = updated_content + patch_section
        else:
            version_str = "1.0.0"
            final_content = (
                f"# SKILL: {clean_name.replace('SKILL_', '').replace('_', ' ').title()}\n"
                f"Version: {version_str}\n"
                f"Tags: auto_learned, {clean_name.lower()}\n\n"
                f"## 1. Initial Knowledge Base ({session_date.isoformat()})\n"
                f"**Creation Reason:** {reason}\n\n"
                f"{lesson_markdown.strip()}\n"
            )

        file_path.write_text(final_content, encoding="utf-8")

        # Record revision in database
        rev = HermesSkillRevision(
            skill_name=clean_name,
            version=new_version,
            reason=reason,
            patch_diff=lesson_markdown[:2000],
            session_on=session_date,
        )
        session.add(rev)
        session.flush()

        return {
            "skill_name": clean_name,
            "version": version_str,
            "reason": reason,
            "file": str(file_path.name),
        }

