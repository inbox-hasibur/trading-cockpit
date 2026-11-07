"""Single-writer execution lock for Humming Bird trading operations.

Guarantees AutoTrader background cycles and Hermes on-demand order/cycle paths
never execute concurrently.
"""

from __future__ import annotations

import logging
import threading
from contextlib import contextmanager
from typing import Generator

logger = logging.getLogger("hummingbird.trading_lock")

# Global re-entrant single-writer trading lock
_TRADING_LOCK = threading.RLock()


@contextmanager
def acquire_trading_lock(timeout: float = 30.0) -> Generator[None, None, None]:
    """Acquires the single-writer trading lock with timeout protection."""
    acquired = _TRADING_LOCK.acquire(timeout=timeout)
    if not acquired:
        logger.error("Failed to acquire trading lock within %.1fs timeout", timeout)
        raise RuntimeError("Trading lock contention: another trade or cycle is currently executing.")
    try:
        yield
    finally:
        _TRADING_LOCK.release()

