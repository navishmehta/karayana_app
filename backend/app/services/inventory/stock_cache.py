"""Keeps the cached stock columns on products in line with their batches.

products.current_stock    = all remaining stock (including expired, until written off)
products.sellable_stock   = remaining stock in batches that have not expired
products.next_expiry_date = earliest expiry among sellable batches
Batches are the source of truth; these caches make lists, filters and sorting fast.
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.core.clock import store_today
from app.models import Product, ProductBatch


def refresh_product_stock(db: Session, product: Product, today: date | None = None) -> None:
    today = today or store_today()
    not_expired = or_(ProductBatch.expiry_date.is_(None), ProductBatch.expiry_date >= today)
    total, sellable, next_expiry = db.execute(
        select(
            func.coalesce(func.sum(ProductBatch.quantity_remaining), 0),
            func.coalesce(func.sum(case((not_expired, ProductBatch.quantity_remaining), else_=0)), 0),
            func.min(case((not_expired, ProductBatch.expiry_date))),
        ).where(ProductBatch.product_id == product.id, ProductBatch.quantity_remaining > 0)
    ).one()
    product.current_stock = Decimal(total)
    product.sellable_stock = Decimal(sellable)
    product.next_expiry_date = next_expiry


def refresh_all_stock(db: Session, store_id: int | None = None) -> int:
    """Nightly job: batches that expired at midnight stop counting as sellable. Returns products updated."""
    stmt = select(Product).where(Product.deleted_at.is_(None))
    if store_id is not None:
        stmt = stmt.where(Product.store_id == store_id)
    today = store_today()
    count = 0
    for product in db.scalars(stmt):
        refresh_product_stock(db, product, today)
        count += 1
    db.commit()
    return count
