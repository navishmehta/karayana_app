"""All models, imported here so Alembic and the app see every table."""

from app.models.base import Base
from app.models.catalogue import Brand, Category, Product, ProductImage, Unit
from app.models.inventory import InventoryAdjustment, ProductBatch, StockTransaction
from app.models.store import Store
from app.models.system import ActivityLog, AppSetting, Notification, NotificationPreference, StockAlert
from app.models.user import AuthSession, DeviceToken, PasswordResetCode, PermissionModel, Role, User

__all__ = [
    "ActivityLog",
    "AppSetting",
    "AuthSession",
    "Base",
    "Brand",
    "Category",
    "DeviceToken",
    "InventoryAdjustment",
    "Notification",
    "NotificationPreference",
    "PasswordResetCode",
    "PermissionModel",
    "Product",
    "ProductBatch",
    "ProductImage",
    "Role",
    "StockAlert",
    "StockTransaction",
    "Store",
    "Unit",
    "User",
]
