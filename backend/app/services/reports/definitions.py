"""The ten reports. Each lists the permissions it needs, its columns and how rows are built.
Columns with a permission are removed for users who lack it, so private values never leave the server."""

from datetime import UTC, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.core.clock import store_today, store_tz
from app.core.constants import REPORT_DEFAULT_EXPIRY_DAYS, REPORT_DEFAULT_MOVEMENT_DAYS, REPORT_MAX_ROWS
from app.core.i18n import has_key, t
from app.core.money import money
from app.enums.permission import Permission
from app.enums.report import ColumnKind as K
from app.enums.report import ReportType
from app.enums.stock import StockStatus
from app.models import Category, Product, ProductBatch, StockTransaction, User
from app.services.catalogue import pricing

from .base import Column, ReportDefinition, ReportFilters, Row

# --- Shared helpers -------------------------------------------------------------------------------


def _products(user: User, filters: ReportFilters) -> Select:
    stmt = (
        select(Product)
        .options(joinedload(Product.category), joinedload(Product.brand), joinedload(Product.unit))
        .where(Product.store_id == user.store_id, Product.deleted_at.is_(None))
        .order_by(Product.name)
        .limit(REPORT_MAX_ROWS + 1)
    )
    if filters.category_id:
        stmt = stmt.where(Product.category_id == filters.category_id)
    return stmt


def _cost_values(db: Session, store_id: int) -> dict[int, Decimal]:
    """Stock value at cost per product: Σ remaining × batch cost (falls back to the product's cost)."""
    rows = db.execute(
        select(
            ProductBatch.product_id,
            func.sum(
                ProductBatch.quantity_remaining * func.coalesce(ProductBatch.purchase_price, Product.purchase_price, 0)
            ),
        )
        .join(Product, Product.id == ProductBatch.product_id)
        .where(ProductBatch.store_id == store_id, ProductBatch.quantity_remaining > 0)
        .group_by(ProductBatch.product_id)
    ).all()
    return {product_id: money(value or 0) for product_id, value in rows}


def _status(value: str) -> str:
    return t(f"reports.values.stock_status.{value}")


def _yes_no(value: bool) -> str:
    return t("reports.values.yes") if value else t("reports.values.no")


def _base(p: Product) -> Row:
    return {"product": p.name, "sku": p.sku, "category": p.category.name, "unit": p.unit.short_name}


def _utc_start(day) -> datetime:
    return datetime.combine(day, time.min, tzinfo=store_tz()).astimezone(UTC).replace(tzinfo=None)


# --- Row builders ---------------------------------------------------------------------------------


def _products_rows(db: Session, user: User, f: ReportFilters):
    for p in db.scalars(_products(user, f)).unique():
        yield _base(p) | {
            "barcode": p.barcode,
            "brand": p.brand.name if p.brand else None,
            "selling_price": p.selling_price,
            "mrp": p.mrp,
            "purchase_price": p.purchase_price,
            "status": t("reports.values.active") if p.is_active else t("reports.values.inactive"),
            "visible": _yes_no(p.is_visible_to_customers),
        }


def _categories_rows(db: Session, user: User, f: ReportFilters):
    costs = _cost_values(db, user.store_id)
    stmt = (
        select(Category)
        .where(Category.store_id == user.store_id, Category.deleted_at.is_(None))
        .order_by(Category.sort_order, Category.name)
    )
    if f.category_id:
        stmt = stmt.where(Category.id == f.category_id)
    products_by_category: dict[int, list[Product]] = {}
    for p in db.scalars(select(Product).where(Product.store_id == user.store_id, Product.deleted_at.is_(None))):
        products_by_category.setdefault(p.category_id, []).append(p)
    for c in db.scalars(stmt):
        items = products_by_category.get(c.id, [])
        yield {
            "category": c.name,
            "products": len(items),
            "active_products": sum(1 for p in items if p.is_active),
            "quantity": sum((p.current_stock for p in items), Decimal(0)),
            "cost_value": sum((costs.get(p.id, Decimal(0)) for p in items), Decimal(0)),
            "status": t("reports.values.active") if c.is_active else t("reports.values.inactive"),
        }


def _stock_rows(db: Session, user: User, f: ReportFilters, only_problems: bool = False):
    stmt = _products(user, f).where(Product.is_active.is_(True))
    if only_problems:
        stmt = stmt.where(Product.stock_status.in_([StockStatus.LOW_STOCK.value, StockStatus.OUT_OF_STOCK.value]))
    for p in db.scalars(stmt).unique():
        yield _base(p) | {
            "current_stock": p.current_stock,
            "sellable_stock": p.sellable_stock,
            "min_stock_level": p.min_stock_level,
            "stock_status": _status(p.stock_status),
        }


def _low_stock_rows(db: Session, user: User, f: ReportFilters):
    return _stock_rows(db, user, f, only_problems=True)


def _expiry_rows(db: Session, user: User, f: ReportFilters):
    today = store_today()
    days = f.within_days if f.within_days is not None else REPORT_DEFAULT_EXPIRY_DAYS
    stmt = (
        select(ProductBatch)
        .options(
            joinedload(ProductBatch.product).joinedload(Product.category),
            joinedload(ProductBatch.product).joinedload(Product.unit),
        )
        .join(Product, Product.id == ProductBatch.product_id)
        .where(
            ProductBatch.store_id == user.store_id,
            ProductBatch.quantity_remaining > 0,
            ProductBatch.expiry_date.is_not(None),
            ProductBatch.expiry_date <= today + timedelta(days=days),
            Product.deleted_at.is_(None),
        )
        .order_by(ProductBatch.expiry_date, Product.name)
        .limit(REPORT_MAX_ROWS + 1)
    )
    if f.category_id:
        stmt = stmt.where(Product.category_id == f.category_id)
    for b in db.scalars(stmt).unique():
        cost = b.purchase_price if b.purchase_price is not None else b.product.purchase_price
        yield _base(b.product) | {
            "batch": b.batch_number,
            "expiry_date": b.expiry_date,
            "days_left": (b.expiry_date - today).days,
            "quantity": b.quantity_remaining,
            "cost_value": money(b.quantity_remaining * cost) if cost is not None else None,
        }


def _purchase_cost_rows(db: Session, user: User, f: ReportFilters):
    costs = _cost_values(db, user.store_id)
    for p in db.scalars(_products(user, f)).unique():
        yield _base(p) | {
            "purchase_price": p.purchase_price,
            "current_stock": p.current_stock,
            "cost_value": costs.get(p.id, Decimal(0)),
        }


def _selling_price_rows(db: Session, user: User, f: ReportFilters):
    for p in db.scalars(_products(user, f)).unique():
        yield _base(p) | {
            "selling_price": p.selling_price,
            "mrp": p.mrp,
            "offer_price": p.offer_price,
            "effective_price": pricing.effective_price(p),
            "discount_percent": pricing.discount_percent(p),
        }


def _valuation_rows(db: Session, user: User, f: ReportFilters):
    costs = _cost_values(db, user.store_id)
    for p in db.scalars(_products(user, f)).unique():
        cost = costs.get(p.id, Decimal(0))
        selling = money(p.sellable_stock * p.selling_price)
        yield _base(p) | {
            "sellable_stock": p.sellable_stock,
            "cost_value": cost,
            "selling_value": selling,
            "potential_profit": money(selling - cost),
        }


def _profit_rows(db: Session, user: User, f: ReportFilters):
    for p in db.scalars(_products(user, f)).unique():
        profit = pricing.profit(p)
        yield _base(p) | {
            "purchase_price": p.purchase_price,
            "effective_price": pricing.effective_price(p),
            "profit": profit.amount if profit else None,
            "markup_percent": profit.markup_percent if profit else None,
            "margin_percent": profit.margin_percent if profit else None,
        }


def _movement_rows(db: Session, user: User, f: ReportFilters):
    today = store_today()
    start = f.date_from or today - timedelta(days=REPORT_DEFAULT_MOVEMENT_DAYS - 1)
    end = f.date_to or today
    stmt = (
        select(StockTransaction)
        .options(joinedload(StockTransaction.product).joinedload(Product.category), joinedload(StockTransaction.user))
        .where(
            StockTransaction.store_id == user.store_id,
            StockTransaction.created_at >= _utc_start(start),
            StockTransaction.created_at < _utc_start(end + timedelta(days=1)),
        )
        .order_by(StockTransaction.id.desc())
        .limit(REPORT_MAX_ROWS + 1)
    )
    if f.category_id:
        stmt = stmt.join(Product, Product.id == StockTransaction.product_id).where(Product.category_id == f.category_id)
    for tx in db.scalars(stmt).unique():
        reason_key = f"stock_reasons.{tx.reason}"
        yield {
            "date": tx.created_at,
            "product": tx.product.name,
            "category": tx.product.category.name,
            "movement": t(f"reports.values.movement.{tx.type}"),
            "reason": t(reason_key) if tx.reason and has_key(reason_key) else tx.reason,
            "change": tx.quantity_change,
            "after": tx.product_qty_after,
            "user": tx.user.name,
        }


# --- Definitions ----------------------------------------------------------------------------------

PRODUCT = Column("product", K.TEXT)
SKU = Column("sku", K.TEXT)
CATEGORY = Column("category", K.TEXT)
UNIT = Column("unit", K.TEXT)
SELLING = Column("selling_price", K.MONEY, Permission.PRICING_VIEW_SELLING)
MRP = Column("mrp", K.MONEY, Permission.PRICING_VIEW_SELLING)
PURCHASE = Column("purchase_price", K.MONEY, Permission.PRICING_VIEW_PURCHASE)
COST_VALUE = Column("cost_value", K.MONEY, Permission.PRICING_VIEW_PURCHASE, total=True)

REPORTS: dict[ReportType, ReportDefinition] = {
    d.type: d
    for d in (
        ReportDefinition(
            ReportType.PRODUCTS,
            (Permission.PRODUCTS_VIEW,),
            (
                PRODUCT,
                SKU,
                Column("barcode", K.TEXT),
                CATEGORY,
                Column("brand", K.TEXT),
                UNIT,
                SELLING,
                MRP,
                PURCHASE,
                Column("status", K.TEXT),
                Column("visible", K.TEXT),
            ),
            _products_rows,
        ),
        ReportDefinition(
            ReportType.CATEGORIES,
            (Permission.CATEGORIES_VIEW,),
            (
                CATEGORY,
                Column("products", K.INT, total=True),
                Column("active_products", K.INT, total=True),
                Column("quantity", K.QUANTITY, Permission.STOCK_VIEW, total=True),
                COST_VALUE,
                Column("status", K.TEXT),
            ),
            _categories_rows,
        ),
        ReportDefinition(
            ReportType.STOCK,
            (Permission.STOCK_VIEW,),
            (
                PRODUCT,
                SKU,
                CATEGORY,
                UNIT,
                Column("current_stock", K.QUANTITY, total=True),
                Column("sellable_stock", K.QUANTITY, total=True),
                Column("min_stock_level", K.QUANTITY),
                Column("stock_status", K.TEXT),
            ),
            _stock_rows,
        ),
        ReportDefinition(
            ReportType.LOW_STOCK,
            (Permission.STOCK_VIEW,),
            (
                PRODUCT,
                SKU,
                CATEGORY,
                UNIT,
                Column("current_stock", K.QUANTITY),
                Column("sellable_stock", K.QUANTITY),
                Column("min_stock_level", K.QUANTITY),
                Column("stock_status", K.TEXT),
            ),
            _low_stock_rows,
        ),
        ReportDefinition(
            ReportType.EXPIRY,
            (Permission.EXPIRY_VIEW,),
            (
                PRODUCT,
                SKU,
                CATEGORY,
                Column("batch", K.TEXT),
                Column("expiry_date", K.DATE),
                Column("days_left", K.INT),
                Column("quantity", K.QUANTITY, total=True),
                UNIT,
                COST_VALUE,
            ),
            _expiry_rows,
            filters=("category_id", "within_days"),
        ),
        ReportDefinition(
            ReportType.PURCHASE_COST,
            (Permission.PRICING_VIEW_PURCHASE, Permission.STOCK_VIEW),
            (PRODUCT, SKU, CATEGORY, UNIT, PURCHASE, Column("current_stock", K.QUANTITY), COST_VALUE),
            _purchase_cost_rows,
        ),
        ReportDefinition(
            ReportType.SELLING_PRICE,
            (Permission.PRICING_VIEW_SELLING,),
            (
                PRODUCT,
                SKU,
                CATEGORY,
                UNIT,
                SELLING,
                MRP,
                Column("offer_price", K.MONEY),
                Column("effective_price", K.MONEY),
                Column("discount_percent", K.PERCENT),
            ),
            _selling_price_rows,
        ),
        ReportDefinition(
            ReportType.VALUATION,
            (Permission.STOCK_VIEW, Permission.PRICING_VIEW_PURCHASE, Permission.PRICING_VIEW_SELLING),
            (
                PRODUCT,
                SKU,
                CATEGORY,
                Column("sellable_stock", K.QUANTITY),
                COST_VALUE,
                Column("selling_value", K.MONEY, total=True),
                Column("potential_profit", K.MONEY, total=True),
            ),
            _valuation_rows,
        ),
        ReportDefinition(
            ReportType.PROFIT_MARGIN,
            (Permission.PRICING_VIEW_PURCHASE, Permission.PRICING_VIEW_SELLING),
            (
                PRODUCT,
                SKU,
                CATEGORY,
                PURCHASE,
                Column("effective_price", K.MONEY),
                Column("profit", K.MONEY),
                Column("markup_percent", K.PERCENT),
                Column("margin_percent", K.PERCENT),
            ),
            _profit_rows,
        ),
        ReportDefinition(
            ReportType.STOCK_MOVEMENTS,
            (Permission.STOCK_VIEW,),
            (
                Column("date", K.DATETIME),
                PRODUCT,
                CATEGORY,
                Column("movement", K.TEXT),
                Column("reason", K.TEXT),
                Column("change", K.QUANTITY),
                Column("after", K.QUANTITY),
                Column("user", K.TEXT),
            ),
            _movement_rows,
            filters=("category_id", "date_from", "date_to"),
        ),
    )
}

assert set(REPORTS) == set(ReportType), "every report type needs a definition"
