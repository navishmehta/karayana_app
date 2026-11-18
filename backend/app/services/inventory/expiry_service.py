"""Expiry dashboard: summary counts and the filterable batch list (batches that still hold stock)."""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import Select, func, select
from sqlalchemy.orm import joinedload

from app.api.deps import DbSession
from app.core.clock import store_today
from app.enums.stock import ExpiryStatus
from app.models import Product, ProductBatch, User
from app.services.inventory.expiry_rules import expiry_limits


@dataclass
class BucketSummary:
    key: str
    days: int | None
    batches: int
    products: int
    quantity: Decimal
    cost_value: Decimal


@dataclass
class ExpiryFilters:
    status: ExpiryStatus = ExpiryStatus.EXPIRING
    within_days: int | None = None
    category_id: int | None = None
    product_id: int | None = None
    date_from: date | None = None
    date_to: date | None = None


class ExpiryService:
    def __init__(self, db: DbSession) -> None:
        self.db = db

    def _base(self, user: User) -> Select:
        return (
            select(ProductBatch)
            .join(Product, Product.id == ProductBatch.product_id)
            .where(
                ProductBatch.store_id == user.store_id,
                ProductBatch.quantity_remaining > 0,
                ProductBatch.expiry_date.is_not(None),
                Product.deleted_at.is_(None),
            )
        )

    def summary(self, user: User) -> tuple[date, list[BucketSummary]]:
        """Expired, then 'within N days' for each limit (cumulative from today, as people read it)."""
        today = store_today()
        ranges: list[tuple[str, int | None, Select]] = [
            ("expired", None, self._base(user).where(ProductBatch.expiry_date < today))
        ]
        for days in expiry_limits(self.db, user.store_id):
            stmt = self._base(user).where(ProductBatch.expiry_date.between(today, today + timedelta(days=days)))
            ranges.append((f"within_{days}", days, stmt))

        result = []
        for key, days, stmt in ranges:
            sub = stmt.subquery()
            batches, products, qty, cost = self.db.execute(
                select(
                    func.count(sub.c.id),
                    func.count(func.distinct(sub.c.product_id)),
                    func.coalesce(func.sum(sub.c.quantity_remaining), 0),
                    func.coalesce(func.sum(sub.c.quantity_remaining * sub.c.purchase_price), 0),
                )
            ).one()
            result.append(BucketSummary(key, days, batches, products, Decimal(qty), Decimal(cost)))
        return today, result

    def batches_query(self, user: User, filters: ExpiryFilters) -> Select:
        today = store_today()
        stmt = self._base(user).options(
            joinedload(ProductBatch.product).joinedload(Product.category),
            joinedload(ProductBatch.product).joinedload(Product.unit),
        )
        if filters.status == ExpiryStatus.EXPIRED:
            stmt = stmt.where(ProductBatch.expiry_date < today)
        elif filters.status == ExpiryStatus.EXPIRING:
            stmt = stmt.where(ProductBatch.expiry_date >= today)
            if filters.within_days is not None:
                stmt = stmt.where(ProductBatch.expiry_date <= today + timedelta(days=filters.within_days))
        if filters.category_id:
            stmt = stmt.where(Product.category_id == filters.category_id)
        if filters.product_id:
            stmt = stmt.where(ProductBatch.product_id == filters.product_id)
        if filters.date_from:
            stmt = stmt.where(ProductBatch.expiry_date >= filters.date_from)
        if filters.date_to:
            stmt = stmt.where(ProductBatch.expiry_date <= filters.date_to)
        return stmt.order_by(ProductBatch.expiry_date.asc(), ProductBatch.id.asc())
