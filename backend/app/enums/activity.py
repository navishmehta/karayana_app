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
    SETTING = "setting"
