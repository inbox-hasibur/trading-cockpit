"""All trading arithmetic uses Decimal; floats are only for JSON/chart display."""

from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

ZERO = Decimal("0")
CENT = Decimal("0.01")
PRICE_TICK = Decimal("0.0001")
HUNDRED = Decimal("100")


def decimal(value: object) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def price(value: Decimal) -> Decimal:
    return value.quantize(PRICE_TICK, rounding=ROUND_HALF_UP)


def whole_shares(value: Decimal) -> int:
    return int(value.to_integral_value(rounding=ROUND_DOWN))


def purchase_amount(quantity: int, unit_price: Decimal, fee_rate: Decimal) -> tuple[Decimal, Decimal]:
    gross = money(quantity * unit_price)
    fee = money(gross * fee_rate)
    return gross + fee, fee


def sale_amount(quantity: int, unit_price: Decimal, fee_rate: Decimal) -> tuple[Decimal, Decimal]:
    gross = money(quantity * unit_price)
    fee = money(gross * fee_rate)
    return gross - fee, fee


def allocated_basis(remaining_basis: Decimal, remaining_qty: int, sold_qty: int) -> Decimal:
    if not 0 < sold_qty <= remaining_qty:
        raise ValueError("Sold quantity must be positive and cannot exceed available shares.")
    if sold_qty == remaining_qty:
        return remaining_basis
    return money(remaining_basis * sold_qty / remaining_qty)


def calculate_broker_fee_breakdown(
    gross_amount: Decimal,
    *,
    commission_rate: Decimal,
    vat_rate: Decimal = Decimal("0.15"),
    exchange_fee_rate: Decimal = Decimal("0"),
) -> dict[str, Decimal]:
    """Calculate exact gross, broker commission, VAT on commission, and exchange fees."""
    gross = money(gross_amount)
    comm = money(gross * commission_rate)
    vat = money(comm * vat_rate)
    exch = money(gross * exchange_fee_rate)
    total_fee = comm + vat + exch
    effective_rate = (total_fee / gross).quantize(PRICE_TICK, rounding=ROUND_HALF_UP) if gross > 0 else ZERO
    return {
        "gross": gross,
        "commission": comm,
        "vat": vat,
        "exchange_fee": exch,
        "total_fee": total_fee,
        "effective_rate": effective_rate,
    }


def round_trip_breakeven_price(
    buy_price: Decimal,
    *,
    buy_fee_rate: Decimal,
    sell_fee_rate: Decimal,
) -> Decimal:
    """Computes exact minimum gross sell price required for net_profit >= 0 after both fees.

    Break-even equation: sell_price * (1 - sell_fee_rate) >= buy_price * (1 + buy_fee_rate)
    => sell_price >= buy_price * (1 + buy_fee_rate) / (1 - sell_fee_rate).
    """
    if sell_fee_rate >= Decimal("1"):
        raise ValueError("Sell fee rate must be less than 1.0 (100%).")
    min_sell = (buy_price * (Decimal("1") + buy_fee_rate)) / (Decimal("1") - sell_fee_rate)
    return money(min_sell)

