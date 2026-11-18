"""Categories, brands and units."""

from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator

from app.core.config import get_settings
from app.core.constants import NAME_MAX_LENGTH
from app.models import Brand, Category, Unit
from app.schemas.common import ApiModel, Name, StoreDateTime
from app.services.storage import get_storage

TranslatedName = Annotated[str, StringConstraints(strip_whitespace=True, max_length=NAME_MAX_LENGTH)]


def _check_translations(value: dict[str, str] | None) -> dict[str, str] | None:
    """Optional names in other languages, e.g. {"pa": "ਡੇਅਰੀ"}. Keys must be supported non-default locales."""
    if value is None:
        return None
    settings = get_settings()
    allowed = set(settings.supported_locales) - {settings.default_locale}
    if set(value) - allowed:
        raise ValueError("validation.locale_unsupported")
    return {k: v for k, v in value.items() if v} or None


# --- Categories -----------------------------------------------------------------------------------


class CategoryCreate(ApiModel):
    name: Name
    name_translations: dict[str, TranslatedName] | None = None
    description: Annotated[str, StringConstraints(max_length=1000)] | None = None
    sort_order: int | None = Field(None, ge=0)
    is_active: bool = True

    _translations = field_validator("name_translations")(_check_translations)


class CategoryUpdate(ApiModel):
    name: Name | None = None
    name_translations: dict[str, TranslatedName] | None = None
    description: Annotated[str, StringConstraints(max_length=1000)] | None = None
    sort_order: int | None = Field(None, ge=0)
    is_active: bool | None = None

    _translations = field_validator("name_translations")(_check_translations)


class CategoryReorder(ApiModel):
    ids: list[int] = Field(min_length=1)


class CategoryOut(BaseModel):
    id: int
    name: str
    name_translations: dict[str, str]
    slug: str
    description: str | None
    image_url: str | None
    image_thumb_url: str | None
    sort_order: int
    is_active: bool
    products_count: int
    created_at: StoreDateTime
    updated_at: StoreDateTime

    @classmethod
    def from_model(cls, category: Category, products_count: int = 0) -> "CategoryOut":
        storage = get_storage()
        return cls(
            id=category.id,
            name=category.name,
            name_translations=category.name_translations or {},
            slug=category.slug,
            description=category.description,
            image_url=storage.url(category.image_path),
            image_thumb_url=storage.url(category.image_thumb_path),
            sort_order=category.sort_order,
            is_active=category.is_active,
            products_count=products_count,
            created_at=category.created_at,
            updated_at=category.updated_at,
        )


# --- Brands ---------------------------------------------------------------------------------------


class BrandCreate(ApiModel):
    name: Name
    is_active: bool = True


class BrandUpdate(ApiModel):
    name: Name | None = None
    is_active: bool | None = None


class BrandOut(BaseModel):
    id: int
    name: str
    slug: str
    is_active: bool

    @classmethod
    def from_model(cls, brand: Brand) -> "BrandOut":
        return cls(id=brand.id, name=brand.name, slug=brand.slug, is_active=brand.is_active)


# --- Units ----------------------------------------------------------------------------------------

ShortName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10)]
UnitName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]


class UnitCreate(ApiModel):
    name: UnitName
    short_name: ShortName
    allows_decimal: bool
    is_active: bool = True


class UnitUpdate(ApiModel):
    name: UnitName | None = None
    short_name: ShortName | None = None
    allows_decimal: bool | None = None
    is_active: bool | None = None


class UnitOut(BaseModel):
    id: int
    name: str
    short_name: str
    allows_decimal: bool
    is_active: bool

    @classmethod
    def from_model(cls, unit: Unit) -> "UnitOut":
        return cls(
            id=unit.id,
            name=unit.name,
            short_name=unit.short_name,
            allows_decimal=unit.allows_decimal,
            is_active=unit.is_active,
        )
