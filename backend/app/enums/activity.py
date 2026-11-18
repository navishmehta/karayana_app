"""Every audited action. The part before the dot is the log group (auth, sellers, …)."""

from enum import StrEnum

from app.core.i18n import t


class ActivityAction(StrEnum):
    LOGIN = "auth.login"
    LOGIN_FAILED = "auth.login_failed"
    LOGOUT = "auth.logout"
    LOGOUT_ALL = "auth.logout_all"
    PROFILE_UPDATED = "auth.profile_updated"
    PASSWORD_CHANGED = "auth.password_changed"
    PASSWORD_RESET_REQUESTED = "auth.password_reset_requested"
    PASSWORD_RESET = "auth.password_reset"

    SELLER_CREATED = "sellers.created"
    SELLER_UPDATED = "sellers.updated"
    SELLER_PERMISSIONS_UPDATED = "sellers.permissions_updated"
    SELLER_ACTIVATED = "sellers.activated"
    SELLER_DEACTIVATED = "sellers.deactivated"
    SELLER_PASSWORD_RESET = "sellers.password_reset"
    SELLER_DELETED = "sellers.deleted"

    CATEGORY_CREATED = "categories.created"
    CATEGORY_UPDATED = "categories.updated"
    CATEGORY_IMAGE_UPDATED = "categories.image_updated"
    CATEGORY_IMAGE_REMOVED = "categories.image_removed"
    CATEGORIES_REORDERED = "categories.reordered"
    CATEGORY_DELETED = "categories.deleted"

    PRODUCT_CREATED = "products.created"
    PRODUCT_UPDATED = "products.updated"
    PRODUCT_PRICE_CHANGED = "products.price_changed"
    PRODUCT_IMAGE_ADDED = "products.image_added"
    PRODUCT_IMAGE_REMOVED = "products.image_removed"
    PRODUCT_DELETED = "products.deleted"
    PRODUCT_RESTORED = "products.restored"

    BRAND_CREATED = "brands.created"
    BRAND_UPDATED = "brands.updated"
    BRAND_DELETED = "brands.deleted"

    STOCK_IN = "stock.in"
    STOCK_OUT = "stock.out"
    STOCK_ADJUSTED = "stock.adjusted"
    STOCK_DAMAGED = "stock.damaged"
    STOCK_EXPIRED_WRITTEN_OFF = "stock.expired_written_off"
    BATCH_UPDATED = "stock.batch_updated"

    UNIT_CREATED = "units.created"
    UNIT_UPDATED = "units.updated"
    UNIT_DELETED = "units.deleted"

    @property
    def group(self) -> str:
        return self.value.split(".")[0]

    @property
    def description(self) -> str:
        return t(f"activity.{self.value}")


class AuditSubject(StrEnum):
    """Types of records an activity can be about."""

    USER = "user"
    CATEGORY = "category"
    PRODUCT = "product"
    BRAND = "brand"
    UNIT = "unit"
    BATCH = "batch"
    ADJUSTMENT = "adjustment"
    SETTING = "setting"
