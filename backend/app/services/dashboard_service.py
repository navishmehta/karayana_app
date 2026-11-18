"""Dashboard numbers for the staff home screen. Every block is computed only if the user may see it."""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.orm import joinedload, selectinload

from app.api.deps import DbSession
from app.core.clock import store_today, store_tz
from app.core.constants import DASHBOARD_RECENT_LIMIT
from app.enums.permission import Permission
from app.enums.role import Role
from app.enums.stock import StockStatus
from app.models import Category, Product, ProductBatch, StockTransaction, User
from app.models import Role as RoleModel
from app.services.inventory.expiry_rules import expiry_limits


@dataclass
class MovementDay:
    day: date
    stock_in: Decimal
    stock_out: Decimal


@dataclass
class Dashboard:
    products_total: int = 0
    products_active: int = 0
    categories_total: int = 0
    sellers_total: int | None = None
    stock: dict | None = None
    expiry: dict | None = None
    value: dict = field(default_factory=dict)
    stock_by_category: list[dict] | None = None
    movements: list[MovementDay] | None = None
    recent_products: list[Product] | None = None
    recent_movements: list[StockTransaction] | None = None


class DashboardService:
    def __init__(self, db: DbSession) -> None:
        self.db = db

    def build(self, user: User, chart_days: int) -> Dashboard:
        store_id = user.store_id
        live = (Product.store_id == store_id, Product.deleted_at.is_(None))
        result = Dashboard()

        result.products_total, result.products_active = self.db.execute(
            select(func.count(Product.id), func.coalesce(func.sum(case((Product.is_active, 1), else_=0)), 0)).where(
                *live
            )
        ).one()
        result.categories_total = self.db.scalar(
            select(func.count(Category.id)).where(Category.store_id == store_id, Category.deleted_at.is_(None))
        )
        if user.is_admin:
            result.sellers_total = self.db.scalar(
                select(func.count(User.id))
                .join(User.role)
                .where(RoleModel.name == Role.SELLER, User.store_id == store_id, User.deleted_at.is_(None))
            )

        if user.has_permission(Permission.STOCK_VIEW):
            quantity, low, out = self.db.execute(
                select(
                    func.coalesce(func.sum(Product.current_stock), 0),
                    func.coalesce(func.sum(case((Product.stock_status == StockStatus.LOW_STOCK.value, 1), else_=0)), 0),
                    func.coalesce(
                        func.sum(case((Product.stock_status == StockStatus.OUT_OF_STOCK.value, 1), else_=0)), 0
                    ),
                ).where(*live, Product.is_active.is_(True))
            ).one()
            result.stock = {"total_quantity": Decimal(quantity), "low_stock": int(low), "out_of_stock": int(out)}
            result.stock_by_category = self._stock_by_category(store_id)
            result.movements = self._movements(store_id, chart_days)
            result.recent_movements = list(
                self.db.scalars(
                    select(StockTransaction)
                    .options(
                        selectinload(StockTransaction.product),
                        selectinload(StockTransaction.batch),
                        selectinload(StockTransaction.user),
                    )
                    .where(StockTransaction.store_id == store_id)
                    .order_by(StockTransaction.id.desc())
                    .limit(DASHBOARD_RECENT_LIMIT)
                )
            )

        if user.has_permission(Permission.EXPIRY_VIEW):
            result.expiry = self._expiry(store_id)

        if user.has_permission(Permission.PRICING_VIEW_PURCHASE):
            cost = self.db.scalar(
                select(
                    func.coalesce(
                        func.sum(
                            ProductBatch.quantity_remaining
                            * func.coalesce(ProductBatch.purchase_price, Product.purchase_price, 0)
                        ),
                        0,
                    )
                )
                .join(Product, Product.id == ProductBatch.product_id)
                .where(*live, ProductBatch.quantity_remaining > 0)
            )
            result.value["purchase_cost"] = Decimal(cost)
        if user.has_permission(Permission.PRICING_VIEW_SELLING) and user.has_permission(Permission.STOCK_VIEW):
            selling = self.db.scalar(
                select(func.coalesce(func.sum(Product.sellable_stock * Product.selling_price), 0)).where(*live)
            )
            result.value["selling_value"] = Decimal(selling)

        if user.has_permission(Permission.PRODUCTS_VIEW):
            result.recent_products = list(
                self.db.scalars(
                    select(Product)
                    .options(
                        joinedload(Product.category),
                        joinedload(Product.brand),
                        joinedload(Product.unit),
                        selectinload(Product.images),
                    )
                    .where(*live)
                    .order_by(Product.created_at.desc(), Product.id.desc())
                    .limit(DASHBOARD_RECENT_LIMIT)
                )
            )
        return result

    def _stock_by_category(self, store_id: int) -> list[dict]:
        rows = self.db.execute(
            select(
                Category.id, Category.name, func.count(Product.id), func.coalesce(func.sum(Product.current_stock), 0)
            )
            .join(Product, Product.category_id == Category.id)
            .where(Product.store_id == store_id, Product.deleted_at.is_(None), Category.deleted_at.is_(None))
            .group_by(Category.id, Category.name)
            .order_by(func.sum(Product.current_stock).desc())
        ).all()
        return [{"id": r[0], "name": r[1], "products": r[2], "quantity": Decimal(r[3])} for r in rows]

    def _movements(self, store_id: int, days: int) -> list[MovementDay]:
        """Quantity received vs. taken out per store-local day, oldest first, including empty days."""
        today = store_today()
        first = today - timedelta(days=days - 1)
        local_day = func.date(func.convert_tz(StockTransaction.created_at, "+00:00", _store_offset()))
        received = case((StockTransaction.quantity_change > 0, StockTransaction.quantity_change), else_=0)
        taken = case((StockTransaction.quantity_change < 0, -StockTransaction.quantity_change), else_=0)
        rows = self.db.execute(
            select(local_day, func.coalesce(func.sum(received), 0), func.coalesce(func.sum(taken), 0))
            .where(StockTransaction.store_id == store_id, local_day >= first)
            .group_by(local_day)
        ).all()
        by_day = {r[0]: (Decimal(r[1]), Decimal(r[2])) for r in rows}
        zero = (Decimal(0), Decimal(0))
        return [MovementDay(d, *by_day.get(d, zero)) for d in (first + timedelta(days=i) for i in range(days))]

    def _expiry(self, store_id: int) -> dict:
        today = store_today()
        soon_days = expiry_limits(self.db, store_id)[0]
        base = (
            select(func.count(ProductBatch.id))
            .join(Product, Product.id == ProductBatch.product_id)
            .where(
                ProductBatch.store_id == store_id,
                ProductBatch.quantity_remaining > 0,
                ProductBatch.expiry_date.is_not(None),
                Product.deleted_at.is_(None),
            )
        )
        expired = self.db.scalar(base.where(ProductBatch.expiry_date < today))
        soon = self.db.scalar(base.where(ProductBatch.expiry_date.between(today, today + timedelta(days=soon_days))))
        return {"expired_batches": expired, "expiring_batches": soon, "expiring_within_days": soon_days}


def _store_offset() -> str:
    """Store timezone as a fixed offset for MySQL CONVERT_TZ, e.g. '+05:30' (India has no daylight saving)."""
    offset = datetime.now(store_tz()).utcoffset() or timedelta(0)
    total = int(offset.total_seconds() // 60)
    sign = "+" if total >= 0 else "-"
    return f"{sign}{abs(total) // 60:02d}:{abs(total) % 60:02d}"
