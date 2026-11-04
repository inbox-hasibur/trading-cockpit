"""Hermes Autonomous Agent Architecture (Nous Research style).

Features:
- Zero-Secret-Read & Token Scrubbing Guardrails (SecretGuard)
- Self-Improving Procedural Memory via versioned Markdown Skills (SKILL_*.md)
- Three-Layer Memory: Layer 1 (Operator Profile), Layer 2 (Session FTS), Layer 3 (Durable Company Facts)
- Turn-based Agent Loop with Context Compression
- State Checkpoints with 1-click `/rollback`
"""

from backend.hermes.secret_guard import SecretGuard, SecurityViolation, redact_secrets

__all__ = ["SecretGuard", "SecurityViolation", "redact_secrets"]

