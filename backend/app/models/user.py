from datetime import datetime

from sqlalchemy import Boolean, Column, ForeignKey, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import EMAIL_MAX_LENGTH, LOCALE_MAX_LENGTH, NAME_MAX_LENGTH, PHONE_MAX_LENGTH
from app.models.base import Base, BigId, CreatedAtMixin, IdMixin, SoftDeleteMixin, TimestampMixin, UtcDateTime

# role_permissions / user_permissions: plain association tables.
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", BigId, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", BigId, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

user_permissions = Table(
    "user_permissions",
    Base.metadata,
    Column("user_id", BigId, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", BigId, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Role(IdMixin, TimestampMixin, Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(30), unique=True)  # app.enums.Role values
    permissions: Mapped[list["PermissionModel"]] = relationship(secondary=role_permissions)


class PermissionModel(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "permissions"

    key: Mapped[str] = mapped_column(String(60), unique=True)  # app.enums.Permission values
    group: Mapped[str] = mapped_column(String(30))


class User(IdMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "users"

    store_id: Mapped[int] = mapped_column(BigId, ForeignKey("stores.id", ondelete="RESTRICT"), index=True)
    role_id: Mapped[int] = mapped_column(BigId, ForeignKey("roles.id", ondelete="RESTRICT"))
    name: Mapped[str] = mapped_column(String(NAME_MAX_LENGTH))
    email: Mapped[str] = mapped_column(String(EMAIL_MAX_LENGTH), unique=True)  # login identity, stored lowercase
    phone: Mapped[str | None] = mapped_column(String(PHONE_MAX_LENGTH))
    password_hash: Mapped[str] = mapped_column(String(255))
    locale: Mapped[str] = mapped_column(String(LOCALE_MAX_LENGTH), default="en", server_default="en")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    last_login_at: Mapped[datetime | None] = mapped_column(UtcDateTime)
    created_by: Mapped[int | None] = mapped_column(BigId, ForeignKey("users.id", ondelete="SET NULL"))

    role: Mapped[Role] = relationship(lazy="joined")
    permissions: Mapped[list[PermissionModel]] = relationship(secondary=user_permissions)


class AuthSession(IdMixin, CreatedAtMixin, Base):
    """One per logged-in device. Holds a hash of the refresh token so a device can be signed out."""

    __tablename__ = "auth_sessions"

    user_id: Mapped[int] = mapped_column(BigId, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    refresh_token_hash: Mapped[str] = mapped_column(String(64), unique=True)  # sha256 hex
    device_name: Mapped[str] = mapped_column(String(100))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime)
    last_used_at: Mapped[datetime | None] = mapped_column(UtcDateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(UtcDateTime)


class PasswordResetCode(IdMixin, CreatedAtMixin, Base):
    """A short code emailed to the user; only its hash is stored."""

    __tablename__ = "password_reset_codes"

    user_id: Mapped[int] = mapped_column(BigId, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    code_hash: Mapped[str] = mapped_column(String(255))
    attempts: Mapped[int] = mapped_column(default=0, server_default="0")
    expires_at: Mapped[datetime] = mapped_column(UtcDateTime)


class DeviceToken(IdMixin, TimestampMixin, Base):
    """Firebase push token. A token moves to whoever logged in last on that device."""

    __tablename__ = "device_tokens"

    user_id: Mapped[int] = mapped_column(BigId, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token: Mapped[str] = mapped_column(String(255), unique=True)
    platform: Mapped[str] = mapped_column(String(10))  # app.enums.device.DevicePlatform
    last_seen_at: Mapped[datetime | None] = mapped_column(UtcDateTime)
