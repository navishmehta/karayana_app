"""Exact rupee arithmetic with Decimal (never floats). Results are rounded half-up to paise."""

from decimal import ROUND_HALF_UP, Decimal

from app.core.constants import MONEY_DECIMALS, QUANTITY_DECIMALS

PAISA = Decimal(1).scaleb(-MONEY_DECIMALS)  # 0.01
MILLI = Decimal(1).scaleb(-QUANTITY_DECIMALS)  # 0.001
HUNDRED = Decimal(100)


def money(value: Decimal | int | str) -> Decimal:
    return Decimal(value).quantize(PAISA, rounding=ROUND_HALF_UP)


def quantity(value: Decimal | int | str) -> Decimal:
    return Decimal(value).quantize(MILLI, rounding=ROUND_HALF_UP)


def percent_of(part: Decimal, whole: Decimal) -> Decimal | None:
    """(part / whole) × 100, or None when whole is zero."""
    if whole == 0:
        return None
    return money(part / whole * HUNDRED)


def is_whole(value: Decimal) -> bool:
    return value == value.to_integral_value()
