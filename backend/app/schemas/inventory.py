"""Stock movements, batches, ledger and expiry."""

from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.core.constants import (
    BATCH_NUMBER_MAX_LENGTH,
    MAX_BATCHES_PER_WRITE_OFF,
    MAX_PRICE,
    MAX_QUANTITY,
    MONEY_DECIMALS,
    NOTES_MAX_LENGTH,
    QUANTITY_DECIMALS,
)
from app.enums.permission import Permission
from app.enums.stock import StockReason
from app.models import InventoryAdjustment, Product, ProductBatch, StockTransaction, User
from app.schemas.common import ApiModel, MoneyOut, QuantityOut, StoreDateTime
from app.services.inventory.expiry_rules import bucket_for, days_to_expiry

PositiveQuantity = Annotated[Decimal, Field(gt=0, le=MAX_QUANTITY, decimal_places=QUANTITY_DECIMALS)]
CountedQuantity = Annotated[Decimal, Field(ge=0, le=MAX_QUANTITY, decimal_places=QUANTITY_DECIMALS)]
Cost = Annotated[Decimal, Field(ge=0, le=MAX_PRICE, decimal_places=MONEY_DECIMALS)]
Notes = Annotated[str, StringConstraints(strip_whitespace=True, max_length=NOTES_MAX_LENGTH)]
BatchNumber = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=BATCH_NUMBER_MAX_LENGTH)]


# --- Requests -------------------------------------------------------------------------------------


class StockInRequest(ApiModel):
    product_id: int
    quantity: PositiveQuantity
    batch_number: BatchNumber | None = None
    manufacturing_date: date | None = None
    expiry_date: date | None = None
    purchase_price: Cost | None = Field(None, description="Cost per unit. Needs pricing.view_purchase.")
    reason: StockReason = StockReason.PURCHASE
    notes: Notes | None = None


class StockOutRequest(ApiModel):
    product_id: int
    quantity: PositiveQuantity
    batch_id: int | None = Field(None, description="Leave empty to use FEFO (first expiry, first out)")
    reason: StockReason
    notes: Notes | None = None


class AdjustRequest(ApiModel):
    batch_id: int
    counted_quantity: CountedQuantity
    reason: StockReason = StockReason.COUNT_CORRECTION
    notes: Notes | None = None


class DamageRequest(ApiModel):
    batch_id: int
    quantity: PositiveQuantity
    reason: StockReason
    notes: Notes | None = None


class WriteOffRequest(ApiModel):
    batch_ids: list[int] = Field(min_length=1, max_length=MAX_BATCHES_PER_WRITE_OFF)
    notes: Notes | None = None


class BatchUpdateRequest(ApiModel):
    batch_number: BatchNumber | None = None
    manufacturing_date: date | None = None
    expiry_date: date | None = None


# --- Responses (cost fields only for pricing.view_purchase; left out of JSON otherwise) -----------


class RefOut(BaseModel):
    id: int
    name: str


class BatchOut(BaseModel):
    id: int
    product_id: int
    batch_number: str | None
    manufacturing_date: date | None
    expiry_date: date | None
    days_to_expiry: int | None
    bucket: str
    quantity_received: QuantityOut
    quantity_remaining: QuantityOut
    received_at: StoreDateTime
    notes: str | None
    purchase_price: MoneyOut | None = None

    @classmethod
    def for_user(cls, batch: ProductBatch, user: User, today: date, limits: list[int]) -> "BatchOut":
        fields = {
            "id": batch.id,
            "product_id": batch.product_id,
            "batch_number": batch.batch_number,
            "manufacturing_date": batch.manufacturing_date,
            "expiry_date": batch.expiry_date,
            "days_to_expiry": days_to_expiry(batch.expiry_date, today),
            "bucket": bucket_for(batch.expiry_date, today, limits).value,
            "quantity_received": batch.quantity_received,
            "quantity_remaining": batch.quantity_remaining,
            "received_at": batch.received_at,
            "notes": batch.notes,
        }
        if user.has_permission(Permission.PRICING_VIEW_PURCHASE):
            fields["purchase_price"] = batch.purchase_price
        return cls(**fields)


class ExpiryBatchOut(BatchOut):
    product: RefOut
    sku: str
    category: RefOut
    unit: str

    @classmethod
    def for_user(cls, batch: ProductBatch, user: User, today: date, limits: list[int]) -> "ExpiryBatchOut":
        base = BatchOut.for_user(batch, user, today, limits).model_dump(exclude_unset=True)
        product = batch.product
        return cls(
            **base,
            product=RefOut(id=product.id, name=product.name),
            sku=product.sku,
            category=RefOut(id=product.category.id, name=product.category.name),
            unit=product.unit.short_name,
        )


class LineBatchOut(BaseModel):
    id: int
    batch_number: str | None
    expiry_date: date | None


class TransactionOut(BaseModel):
    id: int
    type: str
    reason: str | None
    product: RefOut
    batch: LineBatchOut
    quantity_change: QuantityOut
    product_qty_before: QuantityOut
    product_qty_after: QuantityOut
    batch_qty_before: QuantityOut
    batch_qty_after: QuantityOut
    user: RefOut
    reference_type: str | None
    reference_id: int | None
    created_at: StoreDateTime
    unit_cost: MoneyOut | None = None

    @classmethod
    def for_user(cls, tx: StockTransaction, user: User) -> "TransactionOut":
        fields = {
            "id": tx.id,
            "type": tx.type,
            "reason": tx.reason,
            "product": RefOut(id=tx.product.id, name=tx.product.name),
            "batch": LineBatchOut(id=tx.batch.id, batch_number=tx.batch.batch_number, expiry_date=tx.batch.expiry_date),
            "quantity_change": tx.quantity_change,
            "product_qty_before": tx.product_qty_before,
            "product_qty_after": tx.product_qty_after,
            "batch_qty_before": tx.batch_qty_before,
            "batch_qty_after": tx.batch_qty_after,
            "user": RefOut(id=tx.user.id, name=tx.user.name),
            "reference_type": tx.reference_type,
            "reference_id": tx.reference_id,
            "created_at": tx.created_at,
        }
        if user.has_permission(Permission.PRICING_VIEW_PURCHASE):
            fields["unit_cost"] = tx.unit_cost
        return cls(**fields)


class ProductStockOut(BaseModel):
    id: int
    name: str
    current_stock: QuantityOut
    sellable_stock: QuantityOut
    stock_status: str
    next_expiry_date: date | None

    @classmethod
    def from_model(cls, product: Product) -> "ProductStockOut":
        return cls(
            id=product.id,
            name=product.name,
            current_stock=product.current_stock,
            sellable_stock=product.sellable_stock,
            stock_status=product.stock_status,
            next_expiry_date=product.next_expiry_date,
        )


class AdjustmentOut(BaseModel):
    id: int
    type: str
    reason: str
    notes: str | None
    created_by: RefOut
    created_at: StoreDateTime
    lines: list[TransactionOut]
    products: list[ProductStockOut]
    cost_impact: MoneyOut | None = None

    @classmethod
    def for_user(cls, adjustment: InventoryAdjustment, products: list[Product], user: User) -> "AdjustmentOut":
        fields = {
            "id": adjustment.id,
            "type": adjustment.type,
            "reason": adjustment.reason_code,
            "notes": adjustment.notes,
            "created_by": RefOut(id=adjustment.creator.id, name=adjustment.creator.name),
            "created_at": adjustment.created_at,
            "lines": [TransactionOut.for_user(line, user) for line in adjustment.lines],
            "products": [ProductStockOut.from_model(p) for p in products],
        }
        if user.has_permission(Permission.PRICING_VIEW_PURCHASE):
            fields["cost_impact"] = adjustment.cost_impact
        return cls(**fields)


class FefoLineOut(BaseModel):
    batch_id: int
    batch_number: str | None
    expiry_date: date | None
    quantity: QuantityOut


class FefoPreviewOut(BaseModel):
    available: QuantityOut
    enough: bool
    lines: list[FefoLineOut]


class ExpiryBucketOut(BaseModel):
    key: str
    days: int | None
    batches: int
    products: int
    quantity: QuantityOut
    cost_value: MoneyOut | None = None


class ExpirySummaryOut(BaseModel):
    as_of: date
    buckets: list[ExpiryBucketOut]
