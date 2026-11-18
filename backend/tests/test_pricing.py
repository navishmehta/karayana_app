from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.core.money import is_whole, money, percent_of
from app.models import Product
from app.services.catalogue import pricing

TODAY = date(2026, 11, 18)


def _product(**values) -> Product:
    defaults = {"selling_price": Decimal("50.00"), "mrp": Decimal("60.00"), "purchase_price": Decimal("40.00")}
    product = Product()
    for key, value in (defaults | values).items():
        setattr(product, key, value)
    return product


def test_profit_shows_amount_markup_margin_and_inputs() -> None:
    result = pricing.profit(_product(), TODAY)
    assert result.model_dump() == {
        "price_used": Decimal("50.00"),
        "purchase_price": Decimal("40.00"),
        "amount": Decimal("10.00"),
        "markup_percent": Decimal("25.00"),
        "margin_percent": Decimal("20.00"),
    }


def test_no_profit_without_purchase_price() -> None:
    assert pricing.profit(_product(purchase_price=None), TODAY) is None


def test_running_offer_changes_price_discount_and_profit() -> None:
    product = _product(offer_price=Decimal("45.00"), offer_starts_at=TODAY, offer_ends_at=TODAY)
    assert pricing.is_offer_active(product, TODAY)
    assert pricing.effective_price(product, TODAY) == Decimal("45.00")
    assert pricing.discount_percent(product, TODAY) == Decimal("25.00")  # 15 off 60
    assert pricing.profit(product, TODAY).amount == Decimal("5.00")


def test_expired_or_future_offer_is_ignored() -> None:
    expired = _product(offer_price=Decimal("45.00"), offer_ends_at=TODAY - timedelta(days=1))
    future = _product(offer_price=Decimal("45.00"), offer_starts_at=TODAY + timedelta(days=1))
    assert pricing.effective_price(expired, TODAY) == Decimal("50.00")
    assert pricing.effective_price(future, TODAY) == Decimal("50.00")


def test_no_discount_without_mrp_or_at_mrp() -> None:
    assert pricing.discount_percent(_product(mrp=None), TODAY) is None
    assert pricing.discount_percent(_product(mrp=Decimal("50.00")), TODAY) is None


@pytest.mark.parametrize(
    ("value", "expected"), [("0.125", "0.13"), ("0.124", "0.12"), ("-0.125", "-0.13"), ("10", "10.00")]
)
def test_money_rounds_half_up(value: str, expected: str) -> None:
    assert money(value) == Decimal(expected)


def test_percent_and_whole_helpers() -> None:
    assert percent_of(Decimal(1), Decimal(3)) == Decimal("33.33")
    assert percent_of(Decimal(1), Decimal(0)) is None
    assert is_whole(Decimal("2.000")) and not is_whole(Decimal("2.5"))
