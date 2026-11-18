"""Products: request bodies and the permission-aware response."""

from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.core.constants import (
    CODE_MAX_LENGTH,
    DESCRIPTION_MAX_LENGTH,
    MAX_PRICE,
    MAX_QUANTITY,
    MONEY_DECIMALS,
    NOTES_MAX_LENGTH,
    PRODUCT_NAME_MAX_LENGTH,
    QUANTITY_DECIMALS,
)
from app.enums.permission import Permission
from app.models import Product, User
from app.schemas.catalogue import UnitOut
from app.schemas.common import ApiModel, MoneyOut, QuantityOut, StoreDateTime
from app.services.catalogue import pricing
from app.services.storage import get_storage

Price = Annotated[Decimal, Field(ge=0, le=MAX_PRICE, decimal_places=MONEY_DECIMALS)]
Quantity = Annotated[Decimal, Field(ge=0, le=MAX_QUANTITY, decimal_places=QUANTITY_DECIMALS)]
ProductName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=PRODUCT_NAME_MAX_LENGTH)]
Code = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=CODE_MAX_LENGTH, pattern=r"^[A-Za-z0-9._/-]+$")
]
Barcode = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=CODE_MAX_LENGTH, pattern=r"^[A-Za-z0-9]+$")
]
TaxRate = Annotated[Decimal, Field(ge=0, le=100, decimal_places=2)]
HsnCode = Annotated[str, StringConstraints(strip_whitespace=True, max_length=10, pattern=r"^\d+$")]

# Fields only users with pricing.view_purchase may see or set.
PRIVATE_FIELDS = frozenset({"purchase_price", "internal_notes"})
# Fields that need pricing.update_selling to change after the product exists.
SELLING_PRICE_FIELDS = frozenset({"selling_price", "mrp", "offer_price", "offer_starts_at", "offer_ends_at"})


class _ProductFields(ApiModel):
    description: Annotated[str, StringConstraints(max_length=DESCRIPTION_MAX_LENGTH)] | None = None
    brand_id: int | None = None
    sku: Code | None = None
    barcode: Barcode | None = None
    mrp: Price | None = None
    offer_price: Price | None = None
    offer_starts_at: date | None = None
    offer_ends_at: date | None = None
    purchase_price: Price | None = None
    tax_rate: TaxRate | None = None
    hsn_code: HsnCode | None = None
    max_stock_level: Quantity | None = None
    internal_notes: Annotated[str, StringConstraints(max_length=NOTES_MAX_LENGTH)] | None = None


class ProductCreate(_ProductFields):
    """Stock quantities are not accepted here: stock changes only through the inventory module."""

    name: ProductName
    category_id: int
    unit_id: int
    selling_price: Price
    min_stock_level: Quantity = Decimal(0)
    track_expiry: bool = True
    show_expiry_to_customers: bool = False
    is_active: bool = True
    is_visible_to_customers: bool = True
    is_featured: bool = False


class ProductUpdate(_ProductFields):
    name: ProductName | None = None
    category_id: int | None = None
    unit_id: int | None = None
    selling_price: Price | None = None
    min_stock_level: Quantity | None = None
    track_expiry: bool | None = None
    show_expiry_to_customers: bool | None = None
    is_active: bool | None = None
    is_visible_to_customers: bool | None = None
    is_featured: bool | None = None


class ImageUpdate(ApiModel):
    is_primary: bool | None = Field(None, description="Only true is meaningful: make this the main image")
    sort_order: int | None = Field(None, ge=0)


# --- Responses ------------------------------------------------------------------------------------


class RefOut(BaseModel):
    id: int
    name: str


class ProductImageOut(BaseModel):
    id: int
    url: str
    thumb_url: str
    is_primary: bool
    sort_order: int


class ProductOut(BaseModel):
    """Optional groups are left OUT of the JSON (not sent as null) when the user lacks the permission.
    Endpoints return it with response_model_exclude_unset=True."""

    id: int
    name: str
    slug: str
    description: str | None
    sku: str
    barcode: str | None
    category: RefOut
    brand: RefOut | None
    unit: UnitOut
    images: list[ProductImageOut]
    tax_rate: MoneyOut | None
    hsn_code: str | None
    track_expiry: bool
    show_expiry_to_customers: bool
    is_active: bool
    is_visible_to_customers: bool
    is_featured: bool
    created_at: StoreDateTime
    updated_at: StoreDateTime
    deleted_at: StoreDateTime | None = None

    # pricing.view_selling
    selling_price: MoneyOut | None = None
    mrp: MoneyOut | None = None
    offer_price: MoneyOut | None = None
    offer_starts_at: date | None = None
    offer_ends_at: date | None = None
    on_offer: bool | None = None
    effective_price: MoneyOut | None = None
    discount_percent: MoneyOut | None = None

    # pricing.view_purchase
    purchase_price: MoneyOut | None = None
    profit: pricing.ProfitBreakdown | None = None
    internal_notes: str | None = None

    # stock.view
    opening_stock: QuantityOut | None = None
    current_stock: QuantityOut | None = None
    sellable_stock: QuantityOut | None = None
    min_stock_level: QuantityOut | None = None
    max_stock_level: QuantityOut | None = None
    stock_status: str | None = None

    # expiry.view
    next_expiry_date: date | None = None

    @classmethod
    def for_user(cls, product: Product, user: User) -> "ProductOut":
        storage = get_storage()
        fields: dict = {
            "id": product.id,
            "name": product.name,
            "slug": product.slug,
            "description": product.description,
            "sku": product.sku,
            "barcode": product.barcode,
            "category": RefOut(id=product.category.id, name=product.category.name),
            "brand": RefOut(id=product.brand.id, name=product.brand.name) if product.brand else None,
            "unit": UnitOut.from_model(product.unit),
            "images": [
                ProductImageOut(
                    id=i.id,
                    url=storage.url(i.path),
                    thumb_url=storage.url(i.thumb_path),
                    is_primary=i.is_primary,
                    sort_order=i.sort_order,
                )
                for i in product.images
            ],
            "tax_rate": product.tax_rate,
            "hsn_code": product.hsn_code,
            "track_expiry": product.track_expiry,
            "show_expiry_to_customers": product.show_expiry_to_customers,
            "is_active": product.is_active,
            "is_visible_to_customers": product.is_visible_to_customers,
            "is_featured": product.is_featured,
            "created_at": product.created_at,
            "updated_at": product.updated_at,
        }
        if product.deleted_at:
            fields["deleted_at"] = product.deleted_at

        if user.has_permission(Permission.PRICING_VIEW_SELLING):
            fields |= {
                "selling_price": product.selling_price,
                "mrp": product.mrp,
                "offer_price": product.offer_price,
                "offer_starts_at": product.offer_starts_at,
                "offer_ends_at": product.offer_ends_at,
                "on_offer": pricing.is_offer_active(product),
                "effective_price": pricing.effective_price(product),
                "discount_percent": pricing.discount_percent(product),
            }
        if user.has_permission(Permission.PRICING_VIEW_PURCHASE):
            fields |= {
                "purchase_price": product.purchase_price,
                "profit": pricing.profit(product),
                "internal_notes": product.internal_notes,
            }
        if user.has_permission(Permission.STOCK_VIEW):
            fields |= {
                "opening_stock": product.opening_stock,
                "current_stock": product.current_stock,
                "sellable_stock": product.sellable_stock,
                "min_stock_level": product.min_stock_level,
                "max_stock_level": product.max_stock_level,
                "stock_status": product.stock_status,
            }
        if user.has_permission(Permission.EXPIRY_VIEW):
            fields["next_expiry_date"] = product.next_expiry_date
        return cls(**fields)
