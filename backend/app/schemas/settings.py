"""Admin-editable store settings. Each API field maps to one SettingKey."""

from typing import Annotated, Any

from pydantic import BaseModel, Field, StringConstraints, field_validator

from app.core.constants import EXPIRY_LOOKAHEAD_MAX_DAYS
from app.enums.setting_key import SettingKey
from app.schemas.common import ApiModel, Phone
from app.services.storage import get_storage

FIELD_TO_KEY: dict[str, SettingKey] = {
    "store_name": SettingKey.STORE_NAME,
    "tagline": SettingKey.STORE_TAGLINE,
    "phone": SettingKey.STORE_PHONE,
    "whatsapp": SettingKey.STORE_WHATSAPP,
    "address": SettingKey.STORE_ADDRESS,
    "hours": SettingKey.STORE_HOURS,
    "offers_enabled": SettingKey.OFFERS_ENABLED,
    "show_out_of_stock": SettingKey.SHOW_OUT_OF_STOCK,
    "default_min_stock": SettingKey.DEFAULT_MIN_STOCK,
    "expiry_buckets": SettingKey.EXPIRY_BUCKETS,
    "notify_low_stock": SettingKey.NOTIFY_LOW_STOCK,
    "notify_out_of_stock": SettingKey.NOTIFY_OUT_OF_STOCK,
    "notify_expiry": SettingKey.NOTIFY_EXPIRY,
    "expiry_digest_time": SettingKey.EXPIRY_DIGEST_TIME,
}

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=150)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]
StoreName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)]
DigestTime = Annotated[str, StringConstraints(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")]


class SettingsUpdate(ApiModel):
    store_name: StoreName | None = None
    tagline: ShortText | None = None
    phone: Phone = None
    whatsapp: Phone = None
    address: LongText | None = None
    hours: ShortText | None = None
    offers_enabled: bool | None = None
    show_out_of_stock: bool | None = None
    default_min_stock: int | None = Field(None, ge=0, le=100_000)
    expiry_buckets: list[int] | None = None
    notify_low_stock: bool | None = None
    notify_out_of_stock: bool | None = None
    notify_expiry: bool | None = None
    expiry_digest_time: DigestTime | None = None

    @field_validator("expiry_buckets")
    @classmethod
    def _three_increasing_limits(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return None
        if (
            len(value) != 3
            or value != sorted(set(value))
            or not all(1 <= d <= EXPIRY_LOOKAHEAD_MAX_DAYS for d in value)
        ):
            raise ValueError("validation.expiry_buckets")
        return value

    def to_settings(self) -> dict[SettingKey, Any]:
        """Only the fields that were sent. Clearing an optional text field: send an empty string."""
        return {FIELD_TO_KEY[name]: value for name, value in self.model_dump(exclude_unset=True).items()}


class SettingsOut(BaseModel):
    store_name: str
    tagline: str | None
    logo_url: str | None
    logo_thumb_url: str | None
    phone: str | None
    whatsapp: str | None
    address: str | None
    hours: str | None
    offers_enabled: bool
    show_out_of_stock: bool
    default_min_stock: int
    expiry_buckets: list[int]
    notify_low_stock: bool
    notify_out_of_stock: bool
    notify_expiry: bool
    expiry_digest_time: str

    @classmethod
    def from_settings(cls, values: dict[SettingKey, Any]) -> "SettingsOut":
        logo = values[SettingKey.STORE_LOGO] or {}
        storage = get_storage()
        fields = {name: values[key] for name, key in FIELD_TO_KEY.items()}
        for name in ("tagline", "phone", "whatsapp", "address", "hours"):
            fields[name] = fields[name] or None  # empty text means "not set"
        return cls(**fields, logo_url=storage.url(logo.get("path")), logo_thumb_url=storage.url(logo.get("thumb_path")))
