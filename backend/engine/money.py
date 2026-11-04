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
