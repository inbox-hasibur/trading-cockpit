"""Broker-Agnostic Interface, Dataclasses, and TradeXpress Safety Validators.

Provides decoupled abstractions for market data feeds, order execution, symbol
normalization between internal format and broker backtick format, and preflight
safety validation. Pure Python with zero network calls.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class OrderBookLevel:
    price: Decimal
    quantity: int


@dataclass
class MarketQuote:
    symbol: str
    ltp: Decimal
    change: Decimal
    pct_change: Decimal
    volume: int
    open_price: Decimal
    high: Decimal
    low: Decimal
    bid: Decimal
    bid_qty: int
    offer: Decimal
    offer_qty: int
    min_limit: Decimal | None
    max_limit: Decimal | None
    settlement_type: str
    symbol_category: str
    hit_52w_high: bool = False
    hit_upper_circuit: bool = False
    last_trade_time: str = ""
    source: str = "TRADEXPRESS_PASSIVE"


@dataclass
class PortfolioHolding:
    symbol: str
    total_qty: int
    available_dse_qty: int
    pending_holding_qty: int
    buy_pending_qty: int
    sell_pending_qty: int
    avg_cost: Decimal
    market_price: Decimal


class MarketFeedAdapter(ABC):
    """Abstract base interface for real-time market quote feeds."""

    @abstractmethod
    async def get_quote(self, symbol: str) -> MarketQuote | None:
        """Fetch current quote for a single symbol."""
        raise NotImplementedError

    @abstractmethod
    async def get_quotes(self, symbols: list[str]) -> dict[str, MarketQuote]:
        """Fetch current quotes for multiple symbols."""
        raise NotImplementedError


class BrokerOrderExecutor(ABC):
    """Abstract base interface for executing orders against a brokerage."""

    @abstractmethod
    async def execute_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        price: Decimal,
        order_type: str = "LIMIT",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute or simulate order placement."""
        raise NotImplementedError


def to_tradexpress_symbol(symbol: str, board: str = "PB") -> str:
    """Normalize internal symbol to TradeXpress backtick board format (e.g. BANKASIA`PB).

    Defensively strips any existing `PB or 'PB suffix and normalizes case.
    """
    clean = re.sub(r"[`'][A-Za-z0-9_]+$", "", symbol.strip()).upper()
    clean_board = board.strip().lstrip("`'").upper()
    return f"{clean}`{clean_board}"


def from_tradexpress_symbol(raw_symbol: str) -> str:
    """Normalize raw TradeXpress symbol by stripping backtick or apostrophe board suffix.

    Defensively accepts both BANKASIA`PB and BANKASIA'PB and returns BANKASIA.
    """
    clean = re.sub(r"[`'][A-Za-z0-9_]+$", "", raw_symbol.strip()).upper()
    return clean


def validate_tradexpress_order_safety(
    *,
    symbol: str,
    side: str,
    quantity: int,
    price: Decimal,
    order_type: str = "LIMIT",
    tif: str = "DAY",
    all_or_none: bool = False,
    settlement_type: str = "PUBLIC",
    symbol_category: str = "A",
    min_limit: Decimal | None = None,
    max_limit: Decimal | None = None,
    ltp: Decimal | None = None,
    session_phase: str = "CONTINUOUS",
    allow_offhours_na: bool = False,
    cached_settlement_type: str | None = None,
    cached_symbol_category: str | None = None,
) -> tuple[bool, list[str]]:
    """Strict preflight safety validation for TradeXpress order execution.

    Rejects:
    - Non-positive quantity or price
    - SPOT settlement (requires PUBLIC, or allows N/A only with cached PUBLIC fallback)
    - Z category junk companies (allows A, B, or cached fallback in off-hours N/A)
    - Non-LIMIT order types (NEVER Market)
    - Non-DAY time-in-force (NEVER GTC)
    - all_or_none == True (must permit partial fills)
    - Prices violating exchange circuit limits [min_limit, max_limit]
    - Post-closing orders where limit price does not equal exact LTP
    - Orders attempted during CLOSED session phase
    """
    errors: list[str] = []

    # Basic parameter checks
    if quantity <= 0:
        errors.append(f"Invalid quantity {quantity}: share count must be a positive integer.")
    if price <= Decimal("0"):
        errors.append(f"Invalid price {price}: limit price must be positive.")
    if side.upper() not in ("BUY", "SELL"):
        errors.append(f"Invalid order side '{side}': must be BUY or SELL.")

    # Order type enforcement (Strictly LIMIT)
    if order_type.upper() != "LIMIT":
        errors.append(f"Invalid order type '{order_type}': TradeXpress strictly requires LIMIT orders (never MARKET).")

    # Time in Force (TIF)
    if tif.upper() != "DAY":
        errors.append(f"Invalid TIF '{tif}': TradeXpress orders must be DAY (never GTC).")

    # All or None
    if all_or_none:
        errors.append("Invalid order flag: 'All or None' must be False to allow partial exchange execution.")

    # Settlement type enforcement (NEVER SPOT)
    sett = settlement_type.strip().upper()
    if sett == "SPOT":
        errors.append(f"SPOT settlement rejected for '{symbol}': securities trading on SPOT are strictly blocked.")
    elif sett == "N/A":
        cached_sett = (cached_settlement_type or "").strip().upper()
        if not (allow_offhours_na and cached_sett == "PUBLIC"):
            errors.append(f"Settlement type 'N/A' rejected for '{symbol}' without verified cached PUBLIC fallback.")
    elif sett != "PUBLIC":
        errors.append(f"Settlement type '{settlement_type}' rejected for '{symbol}': must be standard PUBLIC.")

    # Category enforcement (NEVER Z)
    cat = symbol_category.strip().upper()
    if cat == "Z":
        errors.append(f"Category 'Z' rejected for '{symbol}': junk/distressed companies are strictly prohibited.")
    elif cat == "N/A":
        cached_cat = (cached_symbol_category or "").strip().upper()
        if not (allow_offhours_na and cached_cat in ("A", "B")):
            errors.append(f"Category 'N/A' rejected for '{symbol}' without verified cached A/B fallback.")
    elif cat not in ("A", "B"):
        errors.append(f"Category '{symbol_category}' rejected for '{symbol}': must be category A or B.")

    # Circuit limit bounds
    if min_limit is not None and price < min_limit:
        errors.append(f"Order price {price} is below minimum circuit limit {min_limit}.")
    if max_limit is not None and price > max_limit:
        errors.append(f"Order price {price} exceeds maximum circuit limit {max_limit}.")

    # Session phase validation
    phase = session_phase.strip().upper()
    if phase == "POST_CLOSING":
        if ltp is None or price != ltp:
            errors.append(
                f"Post-Closing session execution requires exact LTP matching. Order price {price} != LTP {ltp}."
            )
    elif phase == "CLOSED":
        errors.append("Exchange is closed. Orders cannot be submitted outside trading hours.")

    return len(errors) == 0, errors
