"""Stock and expiry alerts → in-app notifications + push messages.

One open alert per problem: an alert fires when a product becomes low / out of stock and is resolved
automatically when it recovers, so people get one message per problem — not one per stock movement.
"""

from datetime import datetime, time, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.clock import store_today, utc_now
from app.core.i18n import t
from app.core.money import quantity
from app.enums.notification import NotificationType
from app.enums.role import Role
from app.enums.stock import AlertStatus, AlertType, StockStatus
from app.models import (
    DeviceToken,
    Notification,
    NotificationPreference,
    Product,
    ProductBatch,
    StockAlert,
    User,
)
from app.models import Role as RoleModel
from app.services.inventory.expiry_rules import expiry_limits
from app.services.notifications.push import PushMessage
from app.services.settings_service import get_setting

STOCK_ALERT_TYPES = (AlertType.LOW_STOCK.value, AlertType.OUT_OF_STOCK.value)


def render(kind: NotificationType, data: dict[str, Any], locale: str | None = None) -> tuple[str, str]:
    """Title and body in the reader's language (stored data, rendered on demand)."""
    return t(f"notifications.{kind.value}.title", locale, **data), t(f"notifications.{kind.value}.body", locale, **data)


def is_digest_due(now: datetime, digest_time: str, window_minutes: int) -> bool:
    """True during the cron window that starts at the store's alert time (e.g. 08:00–08:14 for a 15-minute cron)."""
    hour, minute = map(int, digest_time.split(":"))
    due = datetime.combine(now.date(), time(hour, minute), tzinfo=now.tzinfo)
    return due <= now < due + timedelta(minutes=window_minutes)


def _trim(value: Any) -> str:
    text = f"{quantity(value):f}"
    return text.rstrip("0").rstrip(".") if "." in text else text


class AlertService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- Stock ------------------------------------------------------------------------------------

    def evaluate_stock(self, product: Product) -> list[PushMessage]:
        """Call after a product's stock changed (inside the same transaction)."""
        self.db.flush()
        self.db.refresh(product, ["stock_status", "sellable_stock", "min_stock_level"])
        desired = {
            StockStatus.OUT_OF_STOCK.value: AlertType.OUT_OF_STOCK,
            StockStatus.LOW_STOCK.value: AlertType.LOW_STOCK,
        }.get(product.stock_status)
        if not product.is_active or product.deleted_at is not None:
            desired = None

        current = self.db.scalar(
            select(StockAlert).where(
                StockAlert.product_id == product.id,
                StockAlert.status == AlertStatus.OPEN.value,
                StockAlert.type.in_(STOCK_ALERT_TYPES),
            )
        )
        if current and desired and current.type == desired.value:
            return []  # already told people about this problem
        if current:
            current.status = AlertStatus.RESOLVED.value
            current.resolved_at = utc_now()
        if desired is None:
            return []

        now = utc_now()
        self.db.add(
            StockAlert(
                store_id=product.store_id,
                type=desired.value,
                product_id=product.id,
                dedupe_key=f"{desired.value}:product:{product.id}:{now.timestamp()}",
                status=AlertStatus.OPEN.value,
                triggered_at=now,
                last_notified_at=now,
            )
        )
        kind = NotificationType(desired.value)
        data = {
            "product_id": product.id,
            "product": product.name,
            "quantity": _trim(product.sellable_stock),
            "unit": product.unit.short_name,
            "minimum": _trim(product.min_stock_level),
        }
        return self.notify(product.store_id, kind, data)

    # --- Expiry -----------------------------------------------------------------------------------

    def expiry_digest(self, store_id: int) -> list[PushMessage]:
        """Daily summary: expired stock still on the shelf, and batches expiring within the first limit.
        Sent at most once a day, and only when there is something to report."""
        if self._sent_today(store_id, NotificationType.EXPIRY_DIGEST):
            return []
        today = store_today()
        days = expiry_limits(self.db, store_id)[0]
        base = (
            select(func.count(ProductBatch.id))
            .join(Product, Product.id == ProductBatch.product_id)
            .where(
                ProductBatch.store_id == store_id,
                ProductBatch.quantity_remaining > 0,
                ProductBatch.expiry_date.is_not(None),
                Product.deleted_at.is_(None),
            )
        )
        expired = self.db.scalar(base.where(ProductBatch.expiry_date < today)) or 0
        expiring = (
            self.db.scalar(base.where(ProductBatch.expiry_date.between(today, today + timedelta(days=days)))) or 0
        )
        if not expired and not expiring:
            return []
        return self.notify(
            store_id, NotificationType.EXPIRY_DIGEST, {"expired": expired, "expiring": expiring, "days": days}
        )

    def _sent_today(self, store_id: int, kind: NotificationType) -> bool:
        start = utc_now() - timedelta(hours=24)
        return bool(
            self.db.scalar(
                select(func.count(Notification.id)).where(
                    Notification.store_id == store_id, Notification.type == kind.value, Notification.created_at >= start
                )
            )
        )

    # --- Delivery ---------------------------------------------------------------------------------

    def notify(self, store_id: int, kind: NotificationType, data: dict[str, Any]) -> list[PushMessage]:
        """In-app notification for every recipient; returns push messages to send after commit."""
        if not get_setting(self.db, store_id, kind.setting):
            return []
        messages: list[PushMessage] = []
        for user in self._recipients(store_id, kind):
            preference = self.db.scalar(
                select(NotificationPreference).where(
                    NotificationPreference.user_id == user.id, NotificationPreference.type == kind.value
                )
            )
            if preference is None or preference.in_app_enabled:
                self.db.add(Notification(store_id=store_id, user_id=user.id, type=kind.value, data=data))
            if preference is None or preference.push_enabled:
                title, body = render(kind, data, user.locale)
                payload = {"type": kind.value, **({"product_id": data["product_id"]} if "product_id" in data else {})}
                for device in self.db.scalars(select(DeviceToken).where(DeviceToken.user_id == user.id)):
                    messages.append(PushMessage(token=device.token, title=title, body=body, data=payload))
        return messages

    def _recipients(self, store_id: int, kind: NotificationType) -> list[User]:
        users = self.db.scalars(
            select(User)
            .join(User.role)
            .options(selectinload(User.permissions))
            .where(
                User.store_id == store_id,
                User.is_active.is_(True),
                User.deleted_at.is_(None),
                RoleModel.name.in_([Role.ADMIN, Role.SELLER]),
            )
        )
        return [u for u in users if u.has_permission(kind.permission)]
