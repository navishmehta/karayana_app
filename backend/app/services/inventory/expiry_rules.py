"""Expiry bands and day limits."""

from datetime import date

from sqlalchemy.orm import Session

from app.enums.setting_key import SettingKey
from app.enums.stock import ExpiryBucket
from app.services.settings_service import get_setting


def expiry_limits(db: Session, store_id: int) -> list[int]:
    """Day limits for the bands, e.g. [7, 15, 30], from the admin-editable setting."""
    limits = get_setting(db, store_id, SettingKey.EXPIRY_BUCKETS) or SettingKey.EXPIRY_BUCKETS.default
    return sorted(int(d) for d in limits)[:3]


def days_to_expiry(expiry: date | None, today: date) -> int | None:
    return (expiry - today).days if expiry else None


def bucket_for(expiry: date | None, today: date, limits: list[int]) -> ExpiryBucket:
    if expiry is None:
        return ExpiryBucket.NO_EXPIRY
    days = (expiry - today).days
    if days < 0:
        return ExpiryBucket.EXPIRED
    for limit, bucket in zip(limits, (ExpiryBucket.CRITICAL, ExpiryBucket.WARNING, ExpiryBucket.NOTICE), strict=False):
        if days <= limit:
            return bucket
    return ExpiryBucket.SAFE
