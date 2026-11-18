"""Every runtime setting the admin can change, with its default and whether customers may see it.

The seed command, the settings service and the public API all read from here.
"""

from enum import StrEnum
from typing import Any

from app.core.config import get_settings


class SettingKey(StrEnum):
    STORE_NAME = "store.name"
    STORE_TAGLINE = "store.tagline"
    STORE_LOGO = "store.logo"
    STORE_PHONE = "store.phone"
    STORE_WHATSAPP = "store.whatsapp"
    STORE_ADDRESS = "store.address"
    STORE_HOURS = "store.hours"

    OFFERS_ENABLED = "catalogue.offers_enabled"
    SHOW_OUT_OF_STOCK = "catalogue.show_out_of_stock"

    DEFAULT_MIN_STOCK = "inventory.default_min_stock"
    EXPIRY_BUCKETS = "expiry.buckets"

    NOTIFY_LOW_STOCK = "notifications.low_stock.enabled"
    NOTIFY_OUT_OF_STOCK = "notifications.out_of_stock.enabled"
    NOTIFY_EXPIRY = "notifications.expiry.enabled"
    EXPIRY_DIGEST_TIME = "notifications.expiry.digest_time"

    @property
    def default(self) -> Any:
        match self:
            case SettingKey.STORE_NAME:
                return get_settings().default_store_name
            case (
                SettingKey.OFFERS_ENABLED
                | SettingKey.SHOW_OUT_OF_STOCK
                | SettingKey.NOTIFY_LOW_STOCK
                | SettingKey.NOTIFY_OUT_OF_STOCK
                | SettingKey.NOTIFY_EXPIRY
            ):
                return True
            case SettingKey.DEFAULT_MIN_STOCK:
                return 5
            case SettingKey.EXPIRY_BUCKETS:
                return [7, 15, 30]
            case SettingKey.EXPIRY_DIGEST_TIME:
                return "08:00"
            case _:
                return None

    @property
    def is_public(self) -> bool:
        """Public settings are served to customers by the catalogue API."""
        return self.value.startswith(("store.", "catalogue."))
