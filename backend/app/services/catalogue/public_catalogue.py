"""What customers can see, with no login.

A product is visible only if it is active, marked visible to customers, not deleted, and in an active,
non-deleted category. Out-of-stock products are shown with a label unless the admin hides them.
Search covers name, brand and category — never internal codes (SKU / barcode).
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import ColumnElement, Select, and_, case, func, or_, select
from sqlalchemy.orm import joinedload, selectinload

from app.api.deps import DbSession
from app.core.clock import store_today
from app.core.constants import DEFAULT_STORE_SLUG
from app.core.errors import AppError
from app.core.text import LIKE_ESCAPE, like_contains
from app.enums.error_code import ErrorCode
from app.enums.setting_key import SettingKey
from app.enums.stock import StockStatus
from app.models import Brand, Category, Product, Store
from app.services.settings_service import all_settings


class PublicSort(StrEnum):
    NAME_ASC = "name_asc"
    NAME_DESC = "name_desc"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    NEWEST = "newest"


@dataclass
class PublicFilters:
    search: str | None = None
    category: str | None = None  # slug
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    in_stock_only: bool = False
    on_offer: bool = False
    featured: bool = False
    sort: PublicSort = PublicSort.NAME_ASC


def offer_running(today: date) -> ColumnElement[bool]:
    return and_(
        Product.offer_price.is_not(None),
        or_(Product.offer_starts_at.is_(None), Product.offer_starts_at <= today),
        or_(Product.offer_ends_at.is_(None), Product.offer_ends_at >= today),
    )


def customer_price(offers_enabled: bool, today: date) -> ColumnElement:
    """The price the customer pays today, as SQL (for sorting and price filters)."""
    if not offers_enabled:
        return Product.selling_price
    return case((offer_running(today), Product.offer_price), else_=Product.selling_price)


class PublicCatalogue:
    def __init__(self, db: DbSession) -> None:
        self.db = db
        self.store = self._store()
        self.settings = all_settings(db, self.store.id, public_only=True)
        self.offers_enabled = bool(self.settings[SettingKey.OFFERS_ENABLED])
        self.today = store_today()

    def _store(self) -> Store:
        """V1 has one store. Multi-store (V4) would pick the store from the domain or a header here."""
        store = self.db.scalar(select(Store).where(Store.slug == DEFAULT_STORE_SLUG, Store.is_active.is_(True)))
        if store is None:
            raise AppError(ErrorCode.NOT_FOUND)
        return store

    # --- Visibility -------------------------------------------------------------------------------

    def _visible(self) -> list[ColumnElement[bool]]:
        conditions = [
            Product.store_id == self.store.id,
            Product.is_active.is_(True),
            Product.is_visible_to_customers.is_(True),
            Product.deleted_at.is_(None),
            Category.is_active.is_(True),
            Category.deleted_at.is_(None),
        ]
        if not self.settings[SettingKey.SHOW_OUT_OF_STOCK]:
            conditions.append(Product.stock_status != StockStatus.OUT_OF_STOCK.value)
        return conditions

    def _products(self) -> Select:
        return (
            select(Product)
            .join(Category, Category.id == Product.category_id)
            .options(
                joinedload(Product.category),
                joinedload(Product.brand),
                joinedload(Product.unit),
                selectinload(Product.images),
            )
            .where(*self._visible())
        )

    # --- Queries ----------------------------------------------------------------------------------

    def products_query(self, filters: PublicFilters) -> Select:
        price = customer_price(self.offers_enabled, self.today)
        stmt = self._products()
        if filters.search and filters.search.strip():
            term = like_contains(filters.search)
            stmt = stmt.outerjoin(Brand, Brand.id == Product.brand_id).where(
                or_(
                    Product.name.like(term, escape=LIKE_ESCAPE),
                    Brand.name.like(term, escape=LIKE_ESCAPE),
                    Category.name.like(term, escape=LIKE_ESCAPE),
                )
            )
        if filters.category:
            stmt = stmt.where(Category.slug == filters.category)
        if filters.min_price is not None:
            stmt = stmt.where(price >= filters.min_price)
        if filters.max_price is not None:
            stmt = stmt.where(price <= filters.max_price)
        if filters.in_stock_only:
            stmt = stmt.where(Product.stock_status != StockStatus.OUT_OF_STOCK.value)
        if filters.on_offer:
            stmt = stmt.where(offer_running(self.today)) if self.offers_enabled else stmt.where(False)
        if filters.featured:
            stmt = stmt.where(Product.is_featured.is_(True))

        order = {
            PublicSort.NAME_ASC: (Product.name.asc(),),
            PublicSort.NAME_DESC: (Product.name.desc(),),
            PublicSort.PRICE_ASC: (price.asc(), Product.name.asc()),
            PublicSort.PRICE_DESC: (price.desc(), Product.name.asc()),
            PublicSort.NEWEST: (Product.created_at.desc(), Product.id.desc()),
        }[filters.sort]
        # Things customers can buy come first in every list; out-of-stock items move to the end.
        sold_out_last = case((Product.stock_status == StockStatus.OUT_OF_STOCK.value, 1), else_=0)
        return stmt.order_by(sold_out_last, *order, Product.id)

    def product(self, slug: str) -> Product:
        product = self.db.scalar(self._products().where(Product.slug == slug))
        if product is None:
            raise AppError(ErrorCode.NOT_FOUND)
        return product

    def categories(self) -> list[tuple[Category, int]]:
        """Active categories that have at least one visible product, in the admin's order."""
        rows = self.db.execute(
            select(Category, func.count(Product.id))
            .join(Product, Product.category_id == Category.id)
            .where(*self._visible())
            .group_by(Category.id)
            .order_by(Category.sort_order, Category.name)
        ).all()
        return [(category, count) for category, count in rows]

    def category(self, slug: str) -> tuple[Category, int]:
        for category, count in self.categories():
            if category.slug == slug:
                return category, count
        raise AppError(ErrorCode.NOT_FOUND)
