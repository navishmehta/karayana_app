from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdMixin, TimestampMixin


class Store(IdMixin, TimestampMixin, Base):
    """One row in V1. Store-scoped tables carry store_id so multi-store (V4) needs no schema rewrite.
    The display name customers see comes from app_settings (store.name), editable by the admin."""

    __tablename__ = "stores"

    name: Mapped[str] = mapped_column(String(150))
    slug: Mapped[str] = mapped_column(String(160), unique=True)
    phone: Mapped[str | None] = mapped_column(String(20))
    address: Mapped[str | None] = mapped_column(Text)
    gstin: Mapped[str | None] = mapped_column(String(15))
    timezone: Mapped[str] = mapped_column(String(40))
    currency: Mapped[str] = mapped_column(String(3))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
