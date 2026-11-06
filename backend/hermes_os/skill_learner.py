"""Hermes OS Closed Learning Loop (Auto-Skill Generation & Evolution).

Implements NousResearch Hermes Agent self-improving skill compilation:
1. When Hermes executes a complex multi-step task, handles an edge case,
   or discovers a successful retry workflow (e.g. Ionic DOM fallback, Canary 90/10 outcome),
   it compiles the lesson into an executable SKILL_<name>.md file with YAML frontmatter.
2. If the skill already exists:
   - Increments semantic minor version (e.g. 1.0.0 -> 1.1.0).
   - Merges newly discovered pitfalls and execution steps without duplication.
   - Appends an evolutionary revision log.
3. If new skill:
   - Creates SKILL_<name>.md with version 1.0.0, triggers, tags, pitfalls, and steps.
4. Ensures zero secret leakage via SecretGuard and immediate indexability via SkillLoader / SkillsManager.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy.orm import Session

from backend.hermes.secret_guard import SecretGuard, redact_secrets
from backend.hermes_os.config import ensure_hermes_state_dir, get_hermes_home
from backend.hermes_os.skill_loader import Skill, SkillLoader

logger = logging.getLogger(__name__)

REPO_SKILLS_DIR = Path(__file__).resolve().parent.parent / "hermes" / "skills"


def bump_version(current_ver: str) -> str:
    """Increments minor version (e.g. 1.0.0 -> 1.1.0, 1.1.0 -> 1.2.0)."""
    m = re.match(r"^(\d+)\.(\d+)(?:\.(\d+))?", current_ver.strip())
    if m:
        major = int(m.group(1))
        minor = int(m.group(2)) + 1
        return f"{major}.{minor}.0"
    return "1.1.0"


class SkillLearner:
    """Autonomous closed learning loop for procedural skill synthesis and evolution."""

    def __init__(
        self,
        skills_dir: Path | str | None = None,
        state_dir: Path | str | None = None,
    ):
        self.primary_dir = Path(skills_dir).resolve() if skills_dir else REPO_SKILLS_DIR
        self.primary_dir.mkdir(parents=True, exist_ok=True)
        SecretGuard.assert_safe_path(self.primary_dir)

        self.home_dir = ensure_hermes_state_dir(state_dir)
        self.state_skills_dir = self.home_dir / "skills"
        self.state_skills_dir.mkdir(parents=True, exist_ok=True)
        SecretGuard.assert_safe_path(self.state_skills_dir)

        self.loader = SkillLoader(self.home_dir)

    def normalize_skill_filename(self, name: str) -> str:
        """Converts human title to standardized SKILL_<snake_case>.md filename."""
        clean = re.sub(r"[^a-zA-Z0-9_]+", "_", name.strip().lower()).strip("_")
        if not clean.startswith("skill_"):
            clean = f"skill_{clean}"
        return f"{clean.upper() if clean.startswith('SKILL_') else 'SKILL_' + clean[6:]}.md"

    def learn_from_execution(
        self,
        task_name: str,
        task_description: str,
        execution_log: list[str] | str,
        outcome: str,
        context: dict[str, Any] | None = None,
        session: Session | None = None,
    ) -> Skill:
        """Analyzes execution logs, extracts pitfalls & proven steps, and generates/patches SKILL.md."""
        ctx = context or {}
        raw_logs = execution_log if isinstance(execution_log, list) else [execution_log]
        clean_logs = [redact_secrets(str(line).strip()) for line in raw_logs if str(line).strip()]

        # 1. Identify pitfalls (failures, timeouts, retries, errors, quirks)
        pitfalls: list[str] = []
        for line in clean_logs:
            lower_line = line.lower()
            if any(k in lower_line for k in ("fail", "error", "timeout", "hang", "retry", "quirk", "shadow dom", "fallback")):
                clean_p = re.sub(r"^(error|warning|info|traceback):\s*", "", line, flags=re.IGNORECASE).strip()
                if clean_p and clean_p not in pitfalls:
                    pitfalls.append(clean_p)

        # 2. Extract proven successful steps
        steps: list[str] = []
        for line in clean_logs:
            lower_line = line.lower()
            if any(k in lower_line for k in ("success", "resolved", "executed", "verified", "passed", "clicked", "completed")):
                clean_s = re.sub(r"^(success|info):\s*", "", line, flags=re.IGNORECASE).strip()
                if clean_s and clean_s not in steps:
                    steps.append(clean_s)

        if not steps and outcome:
            steps.append(redact_secrets(outcome.strip()))

        # 3. Determine triggers and tags
        base_text = f"{task_name} {task_description} {' '.join(clean_logs)}".lower()
        triggers: list[str] = []
        tags: list[str] = ["auto_learned"]

        for kw in (
            "stocknow", "ion-select", "favorites", "all_shares", "canary", "quarantine",
            "support_floor", "t+2", "gsc", "retry", "login", "playwright", "dom", "buy", "sell"
        ):
            if kw in base_text:
                triggers.append(kw)
                tags.append(kw)

        if not triggers:
            words = [w for w in re.split(r"\W+", task_name.lower()) if len(w) >= 4]
            triggers = words[:3]
            tags.extend(triggers)

        # 4. Formulate markdown body
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        body_sections = [
            f"## Procedural Execution Guide",
            f"**Objective:** {task_description}",
            f"\n### Known Pitfalls & Traps to Avoid:",
            "\n".join(f"- ⚠️ {p}" for p in (pitfalls or ["No recorded pitfalls"])) ,
            f"\n### Proven Step-by-Step Resolution:",
            "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps or [outcome])),
            f"\n### Execution Summary & Outcome:",
            f"{outcome}",
        ]
        body_content = "\n\n".join(body_sections)

        return self.create_or_patch_skill(
            name=task_name,
            description=task_description,
            triggers=triggers,
            content=body_content,
            pitfalls=pitfalls,
            steps=steps,
            tags=tags,
            session=session,
            reason=f"Closed-loop auto-compilation from task '{task_name}' on {now_iso}",
        )

    def create_or_patch_skill(
        self,
        name: str,
        description: str,
        triggers: list[str],
        content: str,
        pitfalls: list[str] | None = None,
        steps: list[str] | None = None,
        tags: list[str] | None = None,
        session: Session | None = None,
        reason: str | None = None,
    ) -> Skill:
        """Saves a new skill or increments/evolves an existing skill with YAML frontmatter."""
        filename = self.normalize_skill_filename(name)
        target_path = self.primary_dir / filename
        SecretGuard.assert_safe_path(target_path)

        clean_desc = redact_secrets(description.strip())
        clean_content = redact_secrets(content.strip())
        new_pitfalls = [redact_secrets(p) for p in (pitfalls or [])]
        new_steps = [redact_secrets(s) for s in (steps or [])]
        clean_triggers = list(dict.fromkeys([t.lower().strip() for t in triggers if t.strip()]))
        clean_tags = list(dict.fromkeys(["auto_learned"] + [t.lower().strip() for t in (tags or []) if t.strip()]))

        now_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        creation_reason = reason or "Autonomous closed-loop learning"

        if target_path.exists():
            # Evolution of existing skill
            existing_skill = self.loader.load_skill(target_path)
            current_ver = existing_skill.version if existing_skill else "1.0.0"
            next_ver = bump_version(current_ver)

            # Merge triggers, tags, pitfalls, steps
            merged_triggers = list(dict.fromkeys((existing_skill.triggers if existing_skill else []) + clean_triggers))
            merged_tags = list(dict.fromkeys((existing_skill.tags if existing_skill else []) + clean_tags))

            merged_pitfalls = list(existing_skill.pitfalls if existing_skill else [])
            for p in new_pitfalls:
                if p not in merged_pitfalls:
                    merged_pitfalls.append(p)

            merged_steps = list(existing_skill.steps if existing_skill else [])
            for s in new_steps:
                if s not in merged_steps:
                    merged_steps.append(s)

            # Build evolved body
            old_body = existing_skill.body if existing_skill else ""
            revision_block = (
                f"\n\n## 📝 Evolutionary Revision (v{next_ver} — {now_ts})\n"
                f"**Reason:** {creation_reason}\n\n"
                f"{clean_content}\n"
            )
            evolved_body = old_body.rstrip() + revision_block

            skill = Skill(
                name=name,
                description=clean_desc,
                version=next_ver,
                tags=merged_tags,
                triggers=merged_triggers,
                pitfalls=merged_pitfalls,
                steps=merged_steps,
                body=evolved_body,
                filename=filename,
                file_path=target_path,
            )
        else:
            # Creation of brand new skill
            skill = Skill(
                name=name,
                description=clean_desc,
                version="1.0.0",
                tags=clean_tags,
                triggers=clean_triggers,
                pitfalls=new_pitfalls,
                steps=new_steps,
                body=f"## 1. Initial Knowledge Base ({now_date})\n**Creation Reason:** {creation_reason}\n\n{clean_content}",
                filename=filename,
                file_path=target_path,
            )

        # Write to primary skills repository
        target_path.write_text(skill.full_content, encoding="utf-8")

        # Mirror to Hermes OS state skills directory
        state_mirror = self.state_skills_dir / filename
        SecretGuard.assert_safe_path(state_mirror)
        state_mirror.write_text(skill.full_content, encoding="utf-8")

        logger.info("Hermes Closed Learning Loop compiled skill '%s' (v%s) to disk.", filename, skill.version)

        # Record revision in SQLite if session provided
        if session is not None:
            try:
                from backend.database import HermesSkillRevision
                m_ver = int(skill.version.split(".")[1]) if "." in skill.version else 1
                rev = HermesSkillRevision(
                    skill_name=skill.name,
                    version=m_ver,
                    reason=creation_reason,
                    patch_diff=clean_content[:2000],
                    session_on=datetime.now(timezone.utc).date(),
                )
                session.add(rev)
                session.flush()
            except Exception as exc:
                logger.debug("Failed recording HermesSkillRevision in DB: %s", exc)

        return skill

