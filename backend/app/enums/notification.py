"""Notification types: who may receive them and which store setting switches them on."""

from enum import StrEnum

from app.enums.permission import Permission
from app.enums.setting_key import SettingKey


class NotificationType(StrEnum):
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    EXPIRY_DIGEST = "expiry_digest"

    @property
    def permission(self) -> Permission:
        """Sellers receive it only if they can see this area (the admin always does)."""
        return Permission.EXPIRY_VIEW if self is NotificationType.EXPIRY_DIGEST else Permission.STOCK_VIEW

    @property
    def setting(self) -> SettingKey:
        return {
            NotificationType.LOW_STOCK: SettingKey.NOTIFY_LOW_STOCK,
            NotificationType.OUT_OF_STOCK: SettingKey.NOTIFY_OUT_OF_STOCK,
            NotificationType.EXPIRY_DIGEST: SettingKey.NOTIFY_EXPIRY,
        }[self]
