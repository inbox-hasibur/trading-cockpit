from pathlib import Path
import pytest

from backend.secret_guard import SecretGuard, SecurityViolation, redact_secrets


def test_secret_guard_isolation_and_redaction():
    # 1. Block access to sensitive files
    with pytest.raises(SecurityViolation):
        SecretGuard.assert_safe_path(".env")
    with pytest.raises(SecurityViolation):
        SecretGuard.assert_safe_path(".env.local")
    with pytest.raises(SecurityViolation):
        SecretGuard.assert_safe_path("config/auth.json")
    with pytest.raises(SecurityViolation):
        SecretGuard.assert_safe_path("browser_profile/cookies.sqlite")
    with pytest.raises(SecurityViolation):
        SecretGuard.assert_safe_path("backend/data/hummingbird.db")

    # Safe files are permitted
    safe_path = Path("documentation/About_Project.md")
    assert SecretGuard.assert_safe_path(safe_path) == safe_path.resolve()

    # 2. Token scrubbing
    sample_text = (
        "Using OpenRouter sk-or-v1-abcdef1234567890abcdef1234567890 and key sk-99887766554433221100. "
        "Authorization: Bearer secret_session_token_12345"
    )
    redacted = redact_secrets(sample_text)
    assert "sk-or-v1-" not in redacted
    assert "sk-998877" not in redacted
    assert "secret_session_token" not in redacted
    assert "[REDACTED_OPENROUTER_KEY]" in redacted
    assert "[REDACTED_API_KEY]" in redacted
    assert "[REDACTED_TOKEN]" in redacted
