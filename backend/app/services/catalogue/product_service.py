"""Product details and prices.

Stock quantities are NOT changed here — only the inventory service may change stock,
so every change has a ledger entry.
"""

import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from fastapi import UploadFile
from sqlalchemy import Select, func, or_, select, update
from sqlalchemy.orm import joinedload, selectinload

from app.api.deps import DbSession
from app.core.clock import store_today, utc_now
from app.core.constants import MAX_IMAGES_PER_PRODUCT, SKU_PAD_LENGTH, SKU_PREFIX
from app.core.errors import AppError
from app.core.i18n import t
from app.core.money import is_whole
from app.core.text import LIKE_ESCAPE, like_contains, like_prefix
from app.enums.activity import ActivityAction, AuditSubject
from app.enums.catalogue import MediaFolder, ProductSort
from app.enums.error_code import ErrorCode
from app.enums.permission import Permission
from app.enums.stock import ExpiryStatus, StockStatus
from app.models import Brand, Category, Product, ProductBatch, ProductImage, Unit, User
from app.schemas.products import PRIVATE_FIELDS, SELLING_PRICE_FIELDS
from app.services.audit import Audit, changed_fields
from app.services.catalogue.common import ensure_exists_in_store, get_in_store, unique_slug
from app.services.images import store_image
from app.services.notifications.alerts import AlertService
from app.services.notifications.push import deliver
from app.services.storage import get_storage

PRICE_FIELDS = SELLING_PRICE_FIELDS | {"purchase_price"}


@dataclass
class ProductFilters:
    search: str | None = None
    category_ids: list[int] | None = None
    brand_ids: list[int] | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    stock_status: StockStatus | None = None
    is_active: bool | None = None
    is_visible_to_customers: bool | None = None
    is_featured: bool | None = None
    expiry: ExpiryStatus | None = None
    within_days: int | None = None
    sort: ProductSort = ProductSort.NAME_ASC

    def check_allowed(self, user: User) -> None:
        """Filtering or sorting by a value the user can't see would reveal it, so it is refused."""
        needed: set[Permission] = set()
        if self.min_price is not None or self.max_price is not None:
            needed.add(Permission.PRICING_VIEW_SELLING)
        if self.stock_status is not None:
            needed.add(Permission.STOCK_VIEW)
        if self.expiry is not None:
            needed.add(Permission.EXPIRY_VIEW)
        if self.sort.required_permission:
            needed.add(self.sort.required_permission)
        if not all(user.has_permission(p) for p in needed):
            raise AppError(ErrorCode.FORBIDDEN)


def product_query(store_id: int, filters: ProductFilters) -> Select:
    """Shared by the staff list and (Phase 5) the public catalogue."""
    stmt = (
        select(Product)
        .options(
            joinedload(Product.category),
            joinedload(Product.brand),
            joinedload(Product.unit),
            selectinload(Product.images),
        )
        .where(Product.store_id == store_id, Product.deleted_at.is_(None))
    )
    if filters.search and filters.search.strip():
        contains, prefix = like_contains(filters.search), like_prefix(filters.search)
        stmt = (
            stmt.outerjoin(Brand, Brand.id == Product.brand_id)
            .join(Category, Category.id == Product.category_id)
            .where(
                or_(
                    Product.name.like(contains, escape=LIKE_ESCAPE),
                    Product.sku.like(prefix, escape=LIKE_ESCAPE),
                    Product.barcode.like(prefix, escape=LIKE_ESCAPE),
                    Brand.name.like(contains, escape=LIKE_ESCAPE),
                    Category.name.like(contains, escape=LIKE_ESCAPE),
                )
            )
        )
    if filters.category_ids:
        stmt = stmt.where(Product.category_id.in_(filters.category_ids))
    if filters.brand_ids:
        stmt = stmt.where(Product.brand_id.in_(filters.brand_ids))
    if filters.min_price is not None:
        stmt = stmt.where(Product.selling_price >= filters.min_price)
    if filters.max_price is not None:
        stmt = stmt.where(Product.selling_price <= filters.max_price)
    if filters.stock_status is not None:
        stmt = stmt.where(Product.stock_status == filters.stock_status.value)
    if filters.expiry in (ExpiryStatus.EXPIRED, ExpiryStatus.EXPIRING):
        today = store_today()
        batch = (
            select(ProductBatch.id)
            .where(
                ProductBatch.product_id == Product.id,
                ProductBatch.quantity_remaining > 0,
                ProductBatch.expiry_date.is_not(None),
            )
            .correlate(Product)
        )
        if filters.expiry == ExpiryStatus.EXPIRED:
            batch = batch.where(ProductBatch.expiry_date < today)
        else:
            batch = batch.where(ProductBatch.expiry_date >= today)
            if filters.within_days is not None:
                batch = batch.where(ProductBatch.expiry_date <= today + timedelta(days=filters.within_days))
        stmt = stmt.where(batch.exists())
    for column, value in (
        (Product.is_active, filters.is_active),
        (Product.is_visible_to_customers, filters.is_visible_to_customers),
        (Product.is_featured, filters.is_featured),
    ):
        if value is not None:
            stmt = stmt.where(column.is_(value))
    return stmt.order_by(*filters.sort.order_by)


class ProductService:
    def __init__(self, db: DbSession, audit: Audit) -> None:
        self.db = db
        self.audit = audit

    # --- Reads ------------------------------------------------------------------------------------

    def get(self, user: User, product_id: int, *, with_deleted: bool = False) -> Product:
        return get_in_store(self.db, Product, product_id, user.store_id, with_deleted=with_deleted)

    def lookup(self, user: User, barcode: str | None, sku: str | None) -> Product:
        if not barcode and not sku:
            raise AppError(ErrorCode.VALIDATION_FAILED, errors={"barcode": [t("validation.barcode_or_sku")]})
        stmt = select(Product).where(Product.store_id == user.store_id, Product.deleted_at.is_(None))
        stmt = stmt.where(Product.barcode == barcode) if barcode else stmt.where(Product.sku == sku)
        product = self.db.scalar(stmt)
        if product is None:
            raise AppError(ErrorCode.NOT_FOUND)
        return product

    # --- Writes -----------------------------------------------------------------------------------

    def create(self, user: User, data: dict[str, Any]) -> Product:
        """Admin only (enforced by the route)."""
        self._validate(user, data, existing=None)
        sku = data.pop("sku", None)
        product = Product(
            store_id=user.store_id,
            slug=unique_slug(self.db, Product, user.store_id, data["name"]),
            sku=sku or f"TMP-{uuid.uuid4().hex}",  # replaced by SK-000123 once the ID exists
            created_by=user.id,
            **data,
        )
        self.db.add(product)
        self.db.flush()
        if not sku:
            product.sku = self._generate_sku(product)
        self.audit.record(
            ActivityAction.PRODUCT_CREATED,
            actor=user,
            subject=(AuditSubject.PRODUCT, product.id),
            properties={"name": product.name, "sku": product.sku},
        )
        self.db.commit()
        self.db.refresh(product)  # load values as stored (e.g. 285 -> 285.00, computed stock status)
        return product

    def update(self, user: User, product: Product, values: dict[str, Any]) -> Product:
        """Slug stays the same after a rename, so shared customer links keep working.
        Price changes are logged separately so price history is easy to find."""
        self._validate(user, values, existing=product)
        old, new = changed_fields(product, values)
        pushes = AlertService(self.db).evaluate_stock(product) if {"min_stock_level", "is_active"} & new.keys() else []
        if new:
            product.updated_by = user.id
            price_new = {k: v for k, v in new.items() if k in PRICE_FIELDS}
            other_new = {k: v for k, v in new.items() if k not in PRICE_FIELDS}
            for action, changes in (
                (ActivityAction.PRODUCT_PRICE_CHANGED, price_new),
                (ActivityAction.PRODUCT_UPDATED, other_new),
            ):
                if changes:
                    self.audit.record(
                        action,
                        actor=user,
                        subject=(AuditSubject.PRODUCT, product.id),
                        properties={"old": {k: old[k] for k in changes}, "new": changes},
                    )
        self.db.commit()
        deliver(self.db, pushes)
        self.db.refresh(product)
        return product

    def delete(self, user: User, product: Product) -> None:
        """Soft delete: stock history keeps pointing at it, and the admin can restore it."""
        product.deleted_at = utc_now()
        self.audit.record(
            ActivityAction.PRODUCT_DELETED,
            actor=user,
            subject=(AuditSubject.PRODUCT, product.id),
            properties={"name": product.name},
        )
        self.db.commit()

    def restore(self, admin: User, product: Product) -> Product:
        product.deleted_at = None
        self.audit.record(
            ActivityAction.PRODUCT_RESTORED,
            actor=admin,
            subject=(AuditSubject.PRODUCT, product.id),
            properties={"name": product.name},
        )
        self.db.commit()
        self.db.refresh(product)
        return product

    # --- Images -----------------------------------------------------------------------------------

    def add_image(self, user: User, product: Product, upload: UploadFile) -> ProductImage:
        if len(product.images) >= MAX_IMAGES_PER_PRODUCT:
            raise AppError(ErrorCode.IMAGE_LIMIT_REACHED)
        stored = store_image(upload, MediaFolder.PRODUCTS)
        image = ProductImage(
            path=stored.path,
            thumb_path=stored.thumb_path,
            is_primary=not product.images,
            sort_order=max((i.sort_order for i in product.images), default=0) + 1,
        )
        product.images.append(image)  # keeps the loaded image list (and the limit check) up to date
        self.db.flush()
        self.audit.record(
            ActivityAction.PRODUCT_IMAGE_ADDED,
            actor=user,
            subject=(AuditSubject.PRODUCT, product.id),
            properties={"image_id": image.id},
        )
        self.db.commit()
        return image

    def get_image(self, product: Product, image_id: int) -> ProductImage:
        image = next((i for i in product.images if i.id == image_id), None)
        if image is None:  # images of other products are invisible through this product
            raise AppError(ErrorCode.NOT_FOUND)
        return image

    def update_image(self, product: Product, image: ProductImage, values: dict[str, Any]) -> Product:
        if values.get("is_primary"):
            self.db.execute(update(ProductImage).where(ProductImage.product_id == product.id).values(is_primary=False))
            image.is_primary = True
        if values.get("sort_order") is not None:
            image.sort_order = values["sort_order"]
        self.db.commit()
        self.db.refresh(product)
        return product

    def delete_image(self, user: User, product: Product, image: ProductImage) -> None:
        """Deleting the main image promotes the next one."""
        was_primary = image.is_primary
        paths = (image.path, image.thumb_path)
        product.images.remove(image)
        self.db.flush()
        if was_primary and product.images:
            min(product.images, key=lambda i: i.sort_order).is_primary = True
        self.audit.record(
            ActivityAction.PRODUCT_IMAGE_REMOVED,
            actor=user,
            subject=(AuditSubject.PRODUCT, product.id),
            properties={"image_id": image.id},
        )
        self.db.commit()
        get_storage().delete(*paths)

    # --- Rules ------------------------------------------------------------------------------------

    def _validate(self, user: User, values: dict[str, Any], existing: Product | None) -> None:
        """Permission rules per field, links to the store's own rows, and rules that compare fields
        (using stored values for anything not sent). All problems are reported together."""
        errors: dict[str, list[str]] = {}

        def add(field: str, key: str, **params: Any) -> None:
            errors.setdefault(field, []).append(t(key, **params))

        blocked = set()
        if not user.has_permission(Permission.PRICING_VIEW_PURCHASE):
            blocked |= PRIVATE_FIELDS
        if existing is not None and not user.has_permission(Permission.PRICING_UPDATE_SELLING):
            blocked |= SELLING_PRICE_FIELDS
        for field in sorted(blocked & values.keys()):
            add(field, "validation.field_not_permitted", attribute=t(f"attributes.{field}"))

        for field in ("name", "category_id", "unit_id", "selling_price", "sku", "min_stock_level"):
            if existing is not None and field in values and values[field] is None:
                add(field, "validation.missing", attribute=t(f"attributes.{field}"))
        if errors:
            raise AppError(ErrorCode.VALIDATION_FAILED, errors=errors)

        store_id = user.store_id
        if values.get("category_id"):
            ensure_exists_in_store(self.db, Category, values["category_id"], store_id, "category_id")
        if values.get("brand_id"):
            ensure_exists_in_store(self.db, Brand, values["brand_id"], store_id, "brand_id")

        ignore_id = existing.id if existing else None
        for field in ("sku", "barcode"):
            if values.get(field) and self._code_taken(store_id, field, values[field], ignore_id):
                add(field, "validation.code_taken", attribute=t(f"attributes.{field}"))

        def current(field: str) -> Any:
            return values[field] if field in values else getattr(existing, field, None)

        unit = self.db.get(Unit, current("unit_id")) if current("unit_id") else None
        if "unit_id" in values and (unit is None or not unit.is_active):
            add("unit_id", "validation.not_found_in_store", attribute=t("attributes.unit_id"))

        selling, mrp, offer = current("selling_price"), current("mrp"), current("offer_price")
        if mrp is not None and selling is not None and selling > mrp:
            add("selling_price", "validation.selling_above_mrp")
        if offer is not None and selling is not None and offer >= selling:
            add("offer_price", "validation.offer_not_below_selling")

        starts: date | None = current("offer_starts_at")
        ends: date | None = current("offer_ends_at")
        if starts and ends and ends < starts:
            add("offer_ends_at", "validation.offer_end_before_start")

        min_level = current("min_stock_level") or Decimal(0)
        max_level = current("max_stock_level")
        if max_level is not None and max_level < min_level:
            add("max_stock_level", "validation.max_below_min_stock")

        if unit is not None and not unit.allows_decimal:
            for field in ("min_stock_level", "max_stock_level"):
                value = current(field)
                if value is not None and not is_whole(Decimal(value)):
                    add(field, "validation.whole_number_for_unit", unit=unit.short_name)

        if errors:
            raise AppError(ErrorCode.VALIDATION_FAILED, errors=errors)

    def _code_taken(self, store_id: int, field: str, value: str, ignore_id: int | None) -> bool:
        column = getattr(Product, field)
        stmt = select(func.count(Product.id)).where(Product.store_id == store_id, column == value)
        if ignore_id:
            stmt = stmt.where(Product.id != ignore_id)
        return bool(self.db.scalar(stmt))  # deleted products included: the database index includes them

    def _generate_sku(self, product: Product) -> str:
        base = f"{SKU_PREFIX}{product.id:0{SKU_PAD_LENGTH}d}"
        sku, n = base, 2
        while self._code_taken(product.store_id, "sku", sku, product.id):  # someone typed this code manually
            sku, n = f"{base}-{n}", n + 1
        return sku
