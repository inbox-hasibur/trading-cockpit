"""Hard guard for StockNow write operations.

Refuses any POST/mutating request unless the target portfolio ID strictly equals
the configured STOCKNOW_TEST_PORTFOLIO_ID.
"""

from __future__ import annotations

import os
from typing import Any


class StockNowWriteGuardError(PermissionError):
    """Raised when a POST operation attempts to target an unauthorized or non-test portfolio."""
    pass


def verify_test_portfolio_post_guard(
    target_portfolio_id: str | int | None,
    configured_test_id: str | int | None = None,
) -> str:
    """Enforce strict hard guard: refuses any POST unless portfolio_id equals the test id.

    Parameters
    ----------
    target_portfolio_id : str | int | None
        The portfolio ID being targeted for a POST / write operation.
    configured_test_id : str | int | None, optional
        Explicit test portfolio ID. If omitted, resolved from STOCKNOW_TEST_PORTFOLIO_ID env var.

    Returns
    -------
    str
        The verified test portfolio ID string.

    Raises
    ------
    StockNowWriteGuardError
        If test ID is not configured, target ID is empty, or target ID does not strictly equal test ID.
    """
    test_id = str(configured_test_id if configured_test_id is not None else os.getenv("STOCKNOW_TEST_PORTFOLIO_ID", "")).strip()
    if not test_id:
        raise StockNowWriteGuardError(
            "Hard guard violation: STOCKNOW_TEST_PORTFOLIO_ID is not configured. "
            "All write/POST requests are strictly blocked."
        )

    target_id = str(target_portfolio_id or "").strip()
    if not target_id:
        raise StockNowWriteGuardError(
            f"Hard guard violation: Target portfolio ID is missing. Expected test id '{test_id}'."
        )

    if target_id != test_id:
        raise StockNowWriteGuardError(
            f"Hard guard violation: Target portfolio '{target_id}' does not match test id '{test_id}'. "
            "All write/POST operations to non-test portfolios are strictly refused."
        )

    return target_id
