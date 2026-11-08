"""Structured rotating logging configuration with automatic secret redaction.

Features:
- RotatingFileHandler (5MB limit, 5 backups, UTF-8) writing to logs/cockpit.log.
- SecretRedactingFilter that sanitizes:
  - BD phone numbers (01[3-9]\\d{8})
  - Passwords and secret parameters
  - Authorization / Bearer tokens
  - JWT tokens (eyJ...)
- Clean console and file formatting.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
from typing import Any

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = WORKSPACE_ROOT / "logs"

# Redaction regular expressions
PHONE_REGEX = re.compile(r"\b01[3-9]\d{8}\b")
BEARER_REGEX = re.compile(r"Bearer\s+([A-Za-z0-9_\-\.]+)", re.IGNORECASE)
JWT_REGEX = re.compile(r"\beyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\b")
KEY_SECRET_REGEX = re.compile(
    r'(?i)(password|passwd|secret|token|apikey|api_key|kernel_token)["\']?\s*[:=]\s*["\']?([^"\'\s,;]+)',
)


def redact_secrets(text: str) -> str:
    """Sanitize secrets, phones, tokens and credentials from string."""
    if not isinstance(text, str):
        text = str(text)

    # 1. Redact JWT tokens
    text = JWT_REGEX.sub("[REDACTED_JWT]", text)

    # 2. Redact Bearer tokens
    text = BEARER_REGEX.sub("Bearer [REDACTED_TOKEN]", text)

    # 3. Redact key-value secrets (password, secret, etc.)
    text = KEY_SECRET_REGEX.sub(r"\1=[REDACTED]", text)

    # 4. Redact Bangladeshi phone numbers
    text = PHONE_REGEX.sub("[REDACTED_PHONE]", text)

    return text


class SecretRedactingFilter(logging.Filter):
    """Logging filter that scrubs sensitive credentials from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_secrets(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: redact_secrets(str(v)) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    redact_secrets(str(arg)) if isinstance(arg, str) else arg
                    for arg in record.args
                )
        return True


def setup_logging(
    log_dir: Path | str | None = None,
    log_file: str = "cockpit.log",
    level: int = logging.INFO,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 5,
) -> logging.Logger:
    """Configure rotating file and console logging with secret redaction."""
    target_dir = Path(log_dir) if log_dir else LOG_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    log_path = target_dir / log_file

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    redaction_filter = SecretRedactingFilter()

    # Avoid duplicate handlers if setup is called multiple times
    has_file = False
    has_stream = False
    for h in list(root_logger.handlers):
        if isinstance(h, RotatingFileHandler):
            has_file = True
        elif isinstance(h, logging.StreamHandler):
            has_stream = True

    if not has_file:
        file_handler = RotatingFileHandler(
            filename=str(log_path),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(redaction_filter)
        root_logger.addHandler(file_handler)

    if not has_stream:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(level)
        stream_handler.setFormatter(formatter)
        stream_handler.addFilter(redaction_filter)
        root_logger.addHandler(stream_handler)

    return root_logger

