from datetime import date
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Computed,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import NAME_MAX_LENGTH
from app.models.base import Base, BigId, IdMixin, Money, Quantity, SoftDeleteMixin, TimestampMixin

STOCK_STATUS_SQL = (
    "CASE WHEN sellable_stock <= 0 THEN 'out_of_stock' "
    "WHEN sellable_stock <= min_stock_level THEN 'low_stock' ELSE 'in_stock' END"
)


class Unit(IdMixin, TimestampMixin, Base):
    __tablename__ = "units"

    name: Mapped[str] = mapped_column(String(50))
    short_name: Mapped[str] = mapped_column(String(10), unique=True)
    allows_decimal: Mapped[bool] = mapped_column(Boolean, default=False)  # kg/L allow 1.5; pcs does not
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")


class Brand(IdMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "brands"
    __table_args__ = (UniqueConstraint("store_id", "slug"),)

    store_id: Mapped[int] = mapped_column(BigId, ForeignKey("stores.id", ondelete="RESTRICT"))
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH))
    slug: Mapped[str] = mapped_column(String(140))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")


class Category(IdMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("store_id", "slug"),
        Index("ix_categories_listing", "store_id", "is_active", "sort_order"),
    )

    store_id: Mapped[int] = mapped_column(BigId, ForeignKey("stores.id", ondelete="RESTRICT"))
    parent_id: Mapped[int | None] = mapped_column(BigId, ForeignKey("categories.id", ondelete="RESTRICT"))
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH))
    name_translations: Mapped[dict | None] = mapped_column(JSON)  # optional admin-entered {"pa": "..."}
    slug: Mapped[str] = mapped_column(String(140))
    description: Mapped[str | None] = mapped_column(Text)
    image_path: Mapped[str | None] = mapped_column(String(255))
    image_thumb_path: Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    created_by: Mapped[int | None] = mapped_column(BigId, ForeignKey("users.id", ondelete="SET NULL"))
    updated_by: Mapped[int | None] = mapped_column(BigId, ForeignKey("users.id", ondelete="SET NULL"))


class Product(IdMixin, TimestampMixin, SoftDeleteMixin, Base):
    """Stock columns are caches of product_batches, changed only by the inventory service.
    purchase_price and internal_notes are PRIVATE: never returned by the public API.
    Profit is calculated on read, never stored."""

    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("store_id", "slug"),
        UniqueConstraint("store_id", "sku"),
        UniqueConstraint("store_id", "barcode"),
        Index("ix_products_catalogue", "store_id", "is_active", "is_visible_to_customers", "category_id"),
        Index("ix_products_stock_status", "store_id", "stock_status"),
        Index("ix_products_price", "store_id", "selling_price"),
        Index("ix_products_created", "store_id", "created_at"),
        CheckConstraint(
            "selling_price >= 0 AND (purchase_price IS NULL OR purchase_price >= 0)", name="prices_non_negative"
        ),
        CheckConstraint("mrp IS NULL OR selling_price <= mrp", name="selling_le_mrp"),
        CheckConstraint(
            "offer_price IS NULL OR (offer_price >= 0 AND offer_price < selling_price)", name="offer_lt_selling"
        ),
        CheckConstraint(
            "min_stock_level >= 0 AND (max_stock_level IS NULL OR max_stock_level >= min_stock_level)",
            name="stock_levels",
        ),
    )

    store_id: Mapped[int] = mapped_column(BigId, ForeignKey("stores.id", ondelete="RESTRICT"))
    category_id: Mapped[int] = mapped_column(BigId, ForeignKey("categories.id", ondelete="RESTRICT"))
    brand_id: Mapped[int | None] = mapped_column(BigId, ForeignKey("brands.id", ondelete="SET NULL"))
    unit_id: Mapped[int] = mapped_column(BigId, ForeignKey("units.id", ondelete="RESTRICT"))
    name: Mapped[str] = mapped_column(String(191))
    slug: Mapped[str] = mapped_column(String(210))
    description: Mapped[str | None] = mapped_column(Text)
    sku: Mapped[str] = mapped_column(String(64))
    barcode: Mapped[str | None] = mapped_column(String(64))

    purchase_price: Mapped[Decimal | None] = mapped_column(Money)
    selling_price: Mapped[Decimal] = mapped_column(Money)
    mrp: Mapped[Decimal | None] = mapped_column(Money)
    offer_price: Mapped[Decimal | None] = mapped_column(Money)
    offer_starts_at: Mapped[date | None] = mapped_column(Date)
    offer_ends_at: Mapped[date | None] = mapped_column(Date)
    tax_rate: Mapped[Decimal | None] = mapped_column(Money)  # future GST billing
    hsn_code: Mapped[str | None] = mapped_column(String(10))

    opening_stock: Mapped[Decimal] = mapped_column(Quantity, default=Decimal(0), server_default="0")
    current_stock: Mapped[Decimal] = mapped_column(Quantity, default=Decimal(0), server_default="0")
    sellable_stock: Mapped[Decimal] = mapped_column(Quantity, default=Decimal(0), server_default="0")
    min_stock_level: Mapped[Decimal] = mapped_column(Quantity, default=Decimal(0), server_default="0")
    max_stock_level: Mapped[Decimal | None] = mapped_column(Quantity)
    stock_status: Mapped[str] = mapped_column(String(12), Computed(STOCK_STATUS_SQL, persisted=True))
    # Cache: earliest expiry among batches that still have stock and haven't expired (for sorting / customers).
    next_expiry_date: Mapped[date | None] = mapped_column(Date, index=True)

    track_expiry: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    show_expiry_to_customers: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    is_visible_to_customers: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    internal_notes: Mapped[str | None] = mapped_column(Text)

    created_by: Mapped[int | None] = mapped_column(BigId, ForeignKey("users.id", ondelete="SET NULL"))
    updated_by: Mapped[int | None] = mapped_column(BigId, ForeignKey("users.id", ondelete="SET NULL"))

    category: Mapped[Category] = relationship()
    brand: Mapped[Brand | None] = relationship()
    unit: Mapped[Unit] = relationship()
    images: Mapped[list["ProductImage"]] = relationship(
        back_populates="product",
        order_by="(ProductImage.is_primary.desc(), ProductImage.sort_order)",
        cascade="all, delete-orphan",
    )


class ProductImage(IdMixin, TimestampMixin, Base):
    __tablename__ = "product_images"

    product_id: Mapped[int] = mapped_column(BigId, ForeignKey("products.id", ondelete="CASCADE"), index=True)
    path: Mapped[str] = mapped_column(String(255))
    thumb_path: Mapped[str] = mapped_column(String(255))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    product: Mapped[Product] = relationship(back_populates="images")
