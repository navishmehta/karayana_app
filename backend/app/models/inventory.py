"""Stock rules:
- Every unit of stock lives in a batch (expiry_date NULL for non-perishables).
- product_batches.quantity_remaining is the source of truth.
- stock_transactions is an append-only ledger; mistakes are fixed with a new reversing row.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, String, Text, UniqueConstraint, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BigId, CreatedAtMixin, IdMixin, Money, Quantity, TimestampMixin, UtcDateTime
from app.models.catalogue import Product


class ProductBatch(IdMixin, TimestampMixin, Base):
    __tablename__ = "product_batches"
    __table_args__ = (
        Index("ix_batches_fefo", "product_id", "expiry_date", "id"),
        Index("ix_batches_expiry", "store_id", "expiry_date", "quantity_remaining"),
        CheckConstraint("quantity_received > 0", name="qty_received_positive"),
        CheckConstraint("quantity_remaining >= 0", name="qty_remaining_non_negative"),
        CheckConstraint("purchase_price IS NULL OR purchase_price >= 0", name="cost_non_negative"),
        CheckConstraint(
            "expiry_date IS NULL OR manufacturing_date IS NULL OR expiry_date >= manufacturing_date",
            name="dates_order",
        ),
    )

    store_id: Mapped[int] = mapped_column(BigId, ForeignKey("stores.id", ondelete="RESTRICT"))
    product_id: Mapped[int] = mapped_column(BigId, ForeignKey("products.id", ondelete="RESTRICT"))
    batch_number: Mapped[str | None] = mapped_column(String(64))
    manufacturing_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    quantity_received: Mapped[Decimal] = mapped_column(Quantity)
    quantity_remaining: Mapped[Decimal] = mapped_column(Quantity)
    purchase_price: Mapped[Decimal | None] = mapped_column(Money)  # PRIVATE: cost per unit for this batch
    received_at: Mapped[datetime] = mapped_column(UtcDateTime)
    purchase_item_id: Mapped[int | None] = mapped_column(BigId)  # V2 purchases link
    notes: Mapped[str | None] = mapped_column(String(255))
    created_by: Mapped[int] = mapped_column(BigId, ForeignKey("users.id", ondelete="RESTRICT"))

    product: Mapped[Product] = relationship()


class InventoryAdjustment(IdMixin, CreatedAtMixin, Base):
    """Header for one stock event entered by a person; its lines are stock_transactions."""

    __tablename__ = "inventory_adjustments"
    __table_args__ = (Index("ix_adjustments_type", "store_id", "type", "created_at"),)

    store_id: Mapped[int] = mapped_column(BigId, ForeignKey("stores.id", ondelete="RESTRICT"))
    type: Mapped[str] = mapped_column(String(20))  # app.enums.stock.AdjustmentType
    reason_code: Mapped[str] = mapped_column(String(40))
    notes: Mapped[str | None] = mapped_column(Text)
    attachment_path: Mapped[str | None] = mapped_column(String(255))
    cost_impact: Mapped[Decimal | None] = mapped_column(Money)  # PRIVATE
    created_by: Mapped[int] = mapped_column(BigId, ForeignKey("users.id", ondelete="RESTRICT"))


class StockTransaction(IdMixin, CreatedAtMixin, Base):
    __tablename__ = "stock_transactions"
    __table_args__ = (
        Index("ix_stock_tx_product", "product_id", "created_at"),
        Index("ix_stock_tx_type", "store_id", "type", "created_at"),
        Index("ix_stock_tx_user", "user_id", "created_at"),
        Index("ix_stock_tx_reference", "reference_type", "reference_id"),
        UniqueConstraint("store_id", "idempotency_key", "batch_id", name="uq_stock_tx_idempotency"),
        CheckConstraint("quantity_change <> 0", name="nonzero"),
        CheckConstraint("product_qty_after = product_qty_before + quantity_change", name="product_math"),
        CheckConstraint("batch_qty_after = batch_qty_before + quantity_change", name="batch_math"),
    )

    store_id: Mapped[int] = mapped_column(BigId, ForeignKey("stores.id", ondelete="RESTRICT"))
    product_id: Mapped[int] = mapped_column(BigId, ForeignKey("products.id", ondelete="RESTRICT"))
    batch_id: Mapped[int] = mapped_column(BigId, ForeignKey("product_batches.id", ondelete="RESTRICT"))
    type: Mapped[str] = mapped_column(String(24))  # app.enums.stock.StockTransactionType
    quantity_change: Mapped[Decimal] = mapped_column(Quantity)  # signed
    product_qty_before: Mapped[Decimal] = mapped_column(Quantity)
    product_qty_after: Mapped[Decimal] = mapped_column(Quantity)
    batch_qty_before: Mapped[Decimal] = mapped_column(Quantity)
    batch_qty_after: Mapped[Decimal] = mapped_column(Quantity)
    unit_cost: Mapped[Decimal | None] = mapped_column(Money)  # PRIVATE snapshot
    reason: Mapped[str | None] = mapped_column(String(255))
    reference_type: Mapped[str | None] = mapped_column(
        String(60)
    )  # inventory_adjustment; later sale_item, purchase_item
    reference_id: Mapped[int | None] = mapped_column(BigId)
    idempotency_key: Mapped[str | None] = mapped_column(String(64))
    user_id: Mapped[int] = mapped_column(BigId, ForeignKey("users.id", ondelete="RESTRICT"))


class LedgerImmutableError(RuntimeError):
    pass


@event.listens_for(StockTransaction, "before_update")
@event.listens_for(StockTransaction, "before_delete")
def _ledger_is_append_only(*_args) -> None:  # noqa: ANN002
    raise LedgerImmutableError("stock_transactions is append-only")
