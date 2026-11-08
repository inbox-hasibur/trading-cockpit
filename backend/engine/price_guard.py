"""Price sanity guard for virtual and live StockNow order preflight."""

from __future__ import annotations

from decimal import Decimal
from typing import Any


_MARKET_QUOTES: dict[str, dict[str, Any]] = {}


def set_market_quote(
    symbol: str,
    ltp: float | Decimal | None,
    day_low: float | Decimal | None = None,
    day_high: float | Decimal | None = None,
    close: float | Decimal | None = None,
) -> None:
    """Explicitly register an in-memory market quote for tests or runtime hooks."""
    _MARKET_QUOTES[symbol.strip().upper()] = {
        "ltp": float(ltp) if ltp is not None else None,
        "day_low": float(day_low) if day_low is not None else None,
        "day_high": float(day_high) if day_high is not None else None,
        "close": float(close) if close is not None else None,
    }


def get_market_quote(symbol: str, comp: Any = None) -> dict[str, Any] | None:
    """Retrieves cached live market quote for symbol."""
    sym = symbol.strip().upper()
    if sym in _MARKET_QUOTES:
        return _MARKET_QUOTES[sym]

    try:
        from backend.adapters.stocknow_market_sync import _ALL_DSE_SHARES_CACHE
        for s in _ALL_DSE_SHARES_CACHE:
            if s.get("symbol", "").strip().upper() == sym:
                return {
                    "ltp": s.get("ltp") or s.get("price"),
                    "day_low": s.get("low"),
                    "day_high": s.get("high"),
                    "close": s.get("close") or s.get("ycp"),
                }
    except Exception:
        pass

    if comp and getattr(comp, "source", "").startswith("DEMO_") and getattr(comp, "last_price", None):
        return {
            "ltp": float(comp.last_price),
            "day_low": None,
            "day_high": None,
            "close": float(comp.last_price),
        }

    return None


def clear_market_quotes() -> None:
    """Clears in-memory market quotes registry."""
    _MARKET_QUOTES.clear()


def check_price_sanity(
    price: float | Decimal | int | str | None,
    ltp: float | Decimal | int | str | None,
    day_low: float | Decimal | int | str | None = None,
    day_high: float | Decimal | int | str | None = None,
    max_pct: float | Decimal | int | str = 1.5,
) -> tuple[bool, str]:
    """Validates order price against market LTP and day range.

    Rules:
    - ltp missing gives NO_QUOTE
    - price differs from ltp by more than max_pct gives PRICE_OUT_OF_RANGE
    - price outside [day_low, day_high] when both exist gives PRICE_OUT_OF_RANGE
    - valid price gives (True, "OK")
    """
    if ltp is None:
        return False, "NO_QUOTE"

    try:
        f_ltp = float(ltp)
        if f_ltp <= 0:
            return False, "NO_QUOTE"
    except (ValueError, TypeError):
        return False, "NO_QUOTE"

    if price is None:
        return False, "PRICE_OUT_OF_RANGE"

    try:
        f_price = float(price)
        if f_price <= 0:
            return False, "PRICE_OUT_OF_RANGE"
    except (ValueError, TypeError):
        return False, "PRICE_OUT_OF_RANGE"

    try:
        f_max_pct = float(max_pct)
    except (ValueError, TypeError):
        f_max_pct = 1.5

    # Check deviation from LTP: differs by more than max_pct
    diff_pct = (abs(f_price - f_ltp) / f_ltp) * 100.0
    if diff_pct > f_max_pct + 1e-9:
        return False, "PRICE_OUT_OF_RANGE"

    # Check day range: price outside [day_low, day_high] when both exist
    if day_low is not None and day_high is not None:
        try:
            f_low = float(day_low)
            f_high = float(day_high)
            if f_low > 0 and f_high > 0:
                if f_low > f_high:
                    f_low, f_high = f_high, f_low
                if f_price < f_low - 1e-9 or f_price > f_high + 1e-9:
                    return False, "PRICE_OUT_OF_RANGE"
        except (ValueError, TypeError):
            pass

    return True, "OK"
