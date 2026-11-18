"""Runtime settings the admin can change (store name, contact details, thresholds…).

Keys and defaults live in app.enums.SettingKey; values are stored per store in app_settings.
"""

from typing import Any

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import DbSession
from app.enums.activity import ActivityAction, AuditSubject
from app.enums.catalogue import MediaFolder
from app.enums.setting_key import SettingKey
from app.models import AppSetting, User
from app.services.audit import Audit
from app.services.images import store_image
from app.services.storage import get_storage


def get_setting(db: Session, store_id: int, key: SettingKey) -> Any:
    value = db.scalar(select(AppSetting.value).where(AppSetting.store_id == store_id, AppSetting.key == key.value))
    return key.default if value is None else value


def all_settings(db: Session, store_id: int, *, public_only: bool = False) -> dict[SettingKey, Any]:
    stored = {s.key: s.value for s in db.scalars(select(AppSetting).where(AppSetting.store_id == store_id))}
    keys = [k for k in SettingKey if k.is_public] if public_only else list(SettingKey)
    return {k: (k.default if stored.get(k.value) is None else stored[k.value]) for k in keys}


class SettingsService:
    def __init__(self, db: DbSession, audit: Audit) -> None:
        self.db = db
        self.audit = audit

    def update(self, admin: User, values: dict[SettingKey, Any]) -> dict[SettingKey, Any]:
        current = all_settings(self.db, admin.store_id)
        changed = {k: v for k, v in values.items() if current[k] != v}
        for key, value in changed.items():
            self._put(admin.store_id, key, value)
        if changed:
            self.audit.record(
                ActivityAction.SETTINGS_UPDATED,
                actor=admin,
                properties={
                    "old": {k.value: current[k] for k in changed},
                    "new": {k.value: v for k, v in changed.items()},
                },
            )
        self.db.commit()
        return all_settings(self.db, admin.store_id)

    def replace_logo(self, admin: User, upload: UploadFile) -> dict[SettingKey, Any]:
        stored = store_image(upload, MediaFolder.STORE)
        old = get_setting(self.db, admin.store_id, SettingKey.STORE_LOGO) or {}
        self._put(admin.store_id, SettingKey.STORE_LOGO, {"path": stored.path, "thumb_path": stored.thumb_path})
        self.audit.record(
            ActivityAction.STORE_LOGO_UPDATED, actor=admin, subject=(AuditSubject.SETTING, admin.store_id)
        )
        self.db.commit()
        if old:
            get_storage().delete(old.get("path"), old.get("thumb_path"))
        return all_settings(self.db, admin.store_id)

    def _put(self, store_id: int, key: SettingKey, value: Any) -> None:
        setting = self.db.scalar(select(AppSetting).where(AppSetting.store_id == store_id, AppSetting.key == key.value))
        if setting is None:
            setting = AppSetting(store_id=store_id, key=key.value, is_public=key.is_public)
            self.db.add(setting)
        setting.value = value
