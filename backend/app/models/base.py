"""Declarative base, shared column types and mixins for every model."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, MetaData, Numeric, func
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.core.constants import MONEY_DECIMALS, MONEY_PRECISION, QUANTITY_DECIMALS, QUANTITY_PRECISION

# Predictable constraint names so Alembic migrations stay stable.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# Shared column types
BigId = BigInteger().with_variant(mysql.BIGINT(unsigned=True), "mysql")
Money = Numeric(MONEY_PRECISION, MONEY_DECIMALS, asdecimal=True)
Quantity = Numeric(QUANTITY_PRECISION, QUANTITY_DECIMALS, asdecimal=True)
UtcDateTime = DateTime(timezone=False)  # naive UTC (connection time_zone is +00:00)


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class IdMixin:
    id: Mapped[int] = mapped_column(BigId, primary_key=True, autoincrement=True)


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(UtcDateTime, server_default=func.now(), nullable=False)


class TimestampMixin(CreatedAtMixin):
    updated_at: Mapped[datetime] = mapped_column(
        UtcDateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SoftDeleteMixin:
    """Rows are hidden, not removed, because history (stock, activity) still points at them."""

    deleted_at: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True, index=True)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


__all__ = ["Base", "BigId", "Money", "Quantity", "UtcDateTime", "Decimal"]
