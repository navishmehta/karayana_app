"""Read runtime settings (store name, thresholds…) with their defaults from SettingKey."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums.setting_key import SettingKey
from app.models import AppSetting


def get_setting(db: Session, store_id: int, key: SettingKey) -> Any:
    value = db.scalar(select(AppSetting.value).where(AppSetting.store_id == store_id, AppSetting.key == key.value))
    return key.default if value is None else value
