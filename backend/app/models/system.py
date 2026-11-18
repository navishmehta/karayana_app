"""Alerts, notifications, settings and the activity log."""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BigId, CreatedAtMixin, IdMixin, TimestampMixin, UtcDateTime


class StockAlert(IdMixin, Base):
    """One open alert per problem, so users get one push per problem, not one per stock movement."""

    __tablename__ = "stock_alerts"
    __table_args__ = (Index("ix_alerts_status", "store_id", "status", "type"),)

    store_id: Mapped[int] = mapped_column(BigId, ForeignKey("stores.id", ondelete="RESTRICT"))
    type: Mapped[str] = mapped_column(String(20))  # app.enums.stock.AlertType
    product_id: Mapped[int] = mapped_column(BigId, ForeignKey("products.id", ondelete="CASCADE"))
    batch_id: Mapped[int | None] = mapped_column(BigId, ForeignKey("product_batches.id", ondelete="CASCADE"))
    dedupe_key: Mapped[str] = mapped_column(String(100), unique=True)
    status: Mapped[str] = mapped_column(String(10), default="open")  # app.enums.stock.AlertStatus
    triggered_at: Mapped[datetime] = mapped_column(UtcDateTime)
    resolved_at: Mapped[datetime | None] = mapped_column(UtcDateTime)
    last_notified_at: Mapped[datetime | None] = mapped_column(UtcDateTime)


class Notification(IdMixin, CreatedAtMixin, Base):
    """In-app notification. Text is rendered in the reader's language when displayed."""

    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user", "user_id", "read_at", "created_at"),)

    store_id: Mapped[int] = mapped_column(BigId, ForeignKey("stores.id", ondelete="RESTRICT"))
    user_id: Mapped[int] = mapped_column(BigId, ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(40))
    data: Mapped[dict[str, Any]] = mapped_column(JSON)
    read_at: Mapped[datetime | None] = mapped_column(UtcDateTime)


class NotificationPreference(IdMixin, TimestampMixin, Base):
    __tablename__ = "notification_preferences"
    __table_args__ = (UniqueConstraint("user_id", "type"),)

    user_id: Mapped[int] = mapped_column(BigId, ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(40))
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class AppSetting(IdMixin, TimestampMixin, Base):
    """Runtime settings the admin can change (store name, logo, thresholds…). Keys: app.enums.SettingKey."""

    __tablename__ = "app_settings"
    __table_args__ = (UniqueConstraint("store_id", "key"),)

    store_id: Mapped[int] = mapped_column(BigId, ForeignKey("stores.id", ondelete="CASCADE"))
    key: Mapped[str] = mapped_column(String(80))
    value: Mapped[Any] = mapped_column(JSON)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)


class ActivityLog(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "activity_logs"
    __table_args__ = (
        Index("ix_activity_user", "user_id", "created_at"),
        Index("ix_activity_subject", "subject_type", "subject_id"),
        Index("ix_activity_action", "store_id", "action", "created_at"),
    )

    store_id: Mapped[int | None] = mapped_column(BigId, ForeignKey("stores.id", ondelete="RESTRICT"))
    user_id: Mapped[int | None] = mapped_column(BigId, ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(60))  # e.g. auth.login, products.price_changed
    subject_type: Mapped[str | None] = mapped_column(String(40))
    subject_id: Mapped[int | None] = mapped_column(BigId)
    properties: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)

    user: Mapped["User | None"] = relationship(viewonly=True)  # noqa: F821
