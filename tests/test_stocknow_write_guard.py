"""Tests for the StockNow write hard guard."""

import pytest

from backend.adapters.stocknow_write_guard import (
    StockNowWriteGuardError,
    verify_test_portfolio_post_guard,
)


def test_guard_accepts_matching_test_portfolio():
    """Guard allows POST when target matches configured test portfolio ID."""
    res = verify_test_portfolio_post_guard(
        target_portfolio_id="164580",
        configured_test_id="164580",
    )
    assert res == "164580"


def test_guard_rejects_mismatched_portfolio():
    """Guard strictly refuses POST when target differs from configured test ID."""
    with pytest.raises(StockNowWriteGuardError) as exc_info:
        verify_test_portfolio_post_guard(
            target_portfolio_id="164580",
            configured_test_id="164581_test",
        )
    assert "does not match test id" in str(exc_info.value)


def test_guard_rejects_missing_target():
    """Guard refuses POST when target portfolio ID is missing or empty."""
    with pytest.raises(StockNowWriteGuardError) as exc_info:
        verify_test_portfolio_post_guard(
            target_portfolio_id="",
            configured_test_id="164580",
        )
    assert "Target portfolio ID is missing" in str(exc_info.value)


def test_guard_rejects_unconfigured_test_id(monkeypatch):
    """Guard refuses POST when STOCKNOW_TEST_PORTFOLIO_ID is unset/empty."""
    monkeypatch.setenv("STOCKNOW_TEST_PORTFOLIO_ID", "")
    with pytest.raises(StockNowWriteGuardError) as exc_info:
        verify_test_portfolio_post_guard(target_portfolio_id="164580", configured_test_id="")
    assert "STOCKNOW_TEST_PORTFOLIO_ID is not configured" in str(exc_info.value)


def test_guard_resolves_from_env(monkeypatch):
    """Guard resolves test id from environment variable correctly."""
    monkeypatch.setenv("STOCKNOW_TEST_PORTFOLIO_ID", "164580")
    res = verify_test_portfolio_post_guard(target_portfolio_id="164580")
    assert res == "164580"
