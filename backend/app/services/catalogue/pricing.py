"""Price maths for a product. Profit is always calculated here, never stored.

effective price: offer price while the offer is running, otherwise the selling price
markup %       : profit ÷ purchase price  (how much was added on top of cost)
margin %       : profit ÷ effective price (share of the sale that is profit)
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.core.clock import store_today
from app.core.money import money, percent_of
from app.models import Product
from app.schemas.common import MoneyOut


class ProfitBreakdown(BaseModel):
    price_used: MoneyOut
    purchase_price: MoneyOut
    amount: MoneyOut
    markup_percent: MoneyOut | None
    margin_percent: MoneyOut | None


def is_offer_active(product: Product, today: date | None = None) -> bool:
    if product.offer_price is None:
        return False
    today = today or store_today()
    starts_ok = product.offer_starts_at is None or product.offer_starts_at <= today
    ends_ok = product.offer_ends_at is None or product.offer_ends_at >= today
    return starts_ok and ends_ok


def effective_price(product: Product, today: date | None = None) -> Decimal:
    return product.offer_price if is_offer_active(product, today) else product.selling_price


def discount_percent(product: Product, today: date | None = None) -> Decimal | None:
    """How far the customer's price is below MRP."""
    price = effective_price(product, today)
    if product.mrp is None or product.mrp <= price:
        return None
    return percent_of(product.mrp - price, product.mrp)


def profit(product: Product, today: date | None = None) -> ProfitBreakdown | None:
    if product.purchase_price is None:
        return None
    price = effective_price(product, today)
    amount = money(price - product.purchase_price)
    return ProfitBreakdown(
        price_used=price,
        purchase_price=product.purchase_price,
        amount=amount,
        markup_percent=percent_of(amount, product.purchase_price),
        margin_percent=percent_of(amount, price),
    )
