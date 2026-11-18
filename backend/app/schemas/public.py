"""Public (customer) catalogue responses.

These models deliberately have NO fields for purchase price, profit, internal notes, SKU, barcode,
exact stock quantities, IDs of staff or anything else internal — so the public API cannot leak them.
"""

from datetime import date
from typing import Any

from pydantic import BaseModel

from app.core.money import percent_of
from app.enums.setting_key import SettingKey
from app.enums.stock import StockStatus
from app.models import Category, Product, Store
from app.schemas.common import MoneyOut
from app.services.catalogue import pricing
from app.services.storage import get_storage


class PublicStoreOut(BaseModel):
    name: str
    tagline: str | None
    logo_url: str | None
    logo_thumb_url: str | None
    phone: str | None
    whatsapp: str | None
    address: str | None
    hours: str | None
    offers_enabled: bool
    currency: str

    @classmethod
    def build(cls, store: Store, settings: dict[SettingKey, Any]) -> "PublicStoreOut":
        logo = settings[SettingKey.STORE_LOGO] or {}
        storage = get_storage()
        return cls(
            name=settings[SettingKey.STORE_NAME],
            tagline=settings[SettingKey.STORE_TAGLINE] or None,
            logo_url=storage.url(logo.get("path")),
            logo_thumb_url=storage.url(logo.get("thumb_path")),
            phone=settings[SettingKey.STORE_PHONE] or None,
            whatsapp=settings[SettingKey.STORE_WHATSAPP] or None,
            address=settings[SettingKey.STORE_ADDRESS] or None,
            hours=settings[SettingKey.STORE_HOURS] or None,
            offers_enabled=bool(settings[SettingKey.OFFERS_ENABLED]),
            currency=store.currency,
        )


class PublicCategoryOut(BaseModel):
    slug: str
    name: str
    name_translations: dict[str, str]
    description: str | None
    image_url: str | None
    image_thumb_url: str | None
    products_count: int

    @classmethod
    def build(cls, category: Category, products_count: int) -> "PublicCategoryOut":
        storage = get_storage()
        return cls(
            slug=category.slug,
            name=category.name,
            name_translations=category.name_translations or {},
            description=category.description,
            image_url=storage.url(category.image_path),
            image_thumb_url=storage.url(category.image_thumb_path),
            products_count=products_count,
        )


class PublicCategoryRef(BaseModel):
    slug: str
    name: str
    name_translations: dict[str, str]


class PublicImageOut(BaseModel):
    url: str
    thumb_url: str


class PublicProductOut(BaseModel):
    slug: str
    name: str
    description: str | None
    brand: str | None
    category: PublicCategoryRef
    unit: str
    price: MoneyOut  # what the customer pays today (offer price while an offer runs)
    selling_price: MoneyOut
    mrp: MoneyOut | None
    discount_percent: MoneyOut | None
    on_offer: bool
    offer_ends_at: date | None
    availability: StockStatus  # in_stock / low_stock / out_of_stock — never the exact quantity
    expiry_date: date | None  # only when the admin chose to show it for this product
    is_featured: bool
    images: list[PublicImageOut]

    @classmethod
    def build(cls, product: Product, offers_enabled: bool) -> "PublicProductOut":
        storage = get_storage()
        on_offer = offers_enabled and pricing.is_offer_active(product)
        price = product.offer_price if on_offer else product.selling_price
        discount = percent_of(product.mrp - price, product.mrp) if product.mrp and product.mrp > price else None
        return cls(
            slug=product.slug,
            name=product.name,
            description=product.description,
            brand=product.brand.name if product.brand else None,
            category=PublicCategoryRef(
                slug=product.category.slug,
                name=product.category.name,
                name_translations=product.category.name_translations or {},
            ),
            unit=product.unit.short_name,
            price=price,
            selling_price=product.selling_price,
            mrp=product.mrp,
            discount_percent=discount,
            on_offer=on_offer,
            offer_ends_at=product.offer_ends_at if on_offer else None,
            availability=StockStatus(product.stock_status),
            expiry_date=product.next_expiry_date if product.show_expiry_to_customers else None,
            is_featured=product.is_featured,
            images=[
                PublicImageOut(url=storage.url(i.path), thumb_url=storage.url(i.thumb_path)) for i in product.images
            ],
        )
