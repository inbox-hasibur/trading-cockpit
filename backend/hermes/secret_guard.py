"""Runtime Secret Guard & Token Scrubbing.

Guarantees Zero-Secret-Read & .env isolation:
No Hermes prompt, skill learner, memory search, or tool may inspect
credential files, environment secret values, or browser session profiles.
"""

from __future__ import annotations

import re
from pathlib import Path


class SecurityViolation(PermissionError):
    """Raised when an operation attempts to inspect sensitive credentials or isolated files."""
    pass


BLOCKED_FILE_PATTERNS = (
    re.compile(r"(^|[\\/])\.env(\.[a-zA-Z0-9_\-]+)?$", re.IGNORECASE),
    re.compile(r"(^|[\\/])auth\.json$", re.IGNORECASE),
    re.compile(r"(^|[\\/])cookies(\.[a-zA-Z0-9_\-]+)?$", re.IGNORECASE),
    re.compile(r"[\\/]browser_profile([\\/]|$)", re.IGNORECASE),
    re.compile(r"\.(sqlite3?|db)(-shm|-wal)?$", re.IGNORECASE),
)

SECRET_PATTERNS = (
    # OpenRouter API keys
    (re.compile(r"sk-or-v1-[a-zA-Z0-9_\-]{20,}", re.IGNORECASE), "[REDACTED_OPENROUTER_KEY]"),
    # General sk- prefixed AI keys (DeepSeek, OpenAI, Anthropic, etc.)
    (re.compile(r"sk-[a-zA-Z0-9_\-]{16,}", re.IGNORECASE), "[REDACTED_API_KEY]"),
    # Bearer tokens in headers or logs
    (re.compile(r"(Bearer\s+)[a-zA-Z0-9_\-\.]{8,}", re.IGNORECASE), r"\1[REDACTED_TOKEN]"),
    # Generic password / secret assignments
    (re.compile(r"(api[_\-]?key|secret|token|password)\s*[:=]\s*['\"]?[a-zA-Z0-9_\-\.]{8,}['\"]?", re.IGNORECASE),
     r"\1=[REDACTED_SECRET]"),
)


class SecretGuard:
    @staticmethod
    def assert_safe_path(target: str | Path) -> Path:
        resolved = Path(target).resolve()
        path_str = str(resolved).replace("\\", "/")
        for pattern in BLOCKED_FILE_PATTERNS:
            if pattern.search(path_str):
                raise SecurityViolation(
                    f"Access Denied: Hermes Agent isolation strictly forbids reading '{resolved.name}'."
                )
        return resolved

    @staticmethod
    def redact_secrets(text: str, custom_tokens: list[str] | None = None) -> str:
        if not text:
            return ""
        scrubbed = str(text)
        for pattern, replacement in SECRET_PATTERNS:
            scrubbed = pattern.sub(replacement, scrubbed)
        if custom_tokens:
            for token in custom_tokens:
                if token and len(token) >= 6:
                    scrubbed = scrubbed.replace(token, "[REDACTED_TOKEN]")
        return scrubbed


def redact_secrets(text: str, custom_tokens: list[str] | None = None) -> str:
    return SecretGuard.redact_secrets(text, custom_tokens)

