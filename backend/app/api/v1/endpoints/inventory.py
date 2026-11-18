"""Stock movements, batches, stock history and the expiry dashboard."""

from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession, require, require_any
from app.core.clock import store_today, store_tz
from app.core.constants import EXPIRY_LOOKAHEAD_MAX_DAYS, IDEMPOTENCY_KEY_MAX_LENGTH, MAX_QUANTITY
from app.core.errors import AppError
from app.core.pagination import Pagination, paginate
from app.enums.error_code import ErrorCode
from app.enums.permission import Permission
from app.enums.stock import ExpiryStatus, StockTransactionType
from app.models import InventoryAdjustment, Product, ProductBatch, StockTransaction, User
from app.schemas.common import DataResponse, Page
from app.schemas.inventory import (
    AdjustmentOut,
    AdjustRequest,
    BatchOut,
    BatchUpdateRequest,
    DamageRequest,
    ExpiryBatchOut,
    ExpiryBucketOut,
    ExpirySummaryOut,
    FefoLineOut,
    FefoPreviewOut,
    StockInRequest,
    StockOutRequest,
    TransactionOut,
    WriteOffRequest,
)
from app.services.catalogue.common import get_in_store
from app.services.inventory.expiry_rules import expiry_limits
from app.services.inventory.expiry_service import ExpiryFilters, ExpiryService
from app.services.inventory.fefo import allocate, is_expired
from app.services.inventory.inventory_service import InventoryService, StockResult

router = APIRouter(tags=["inventory"])

Inventory = Annotated[InventoryService, Depends()]
CanViewStock = Annotated[User, Depends(require(Permission.STOCK_VIEW))]
CanUpdateStock = Annotated[User, Depends(require(Permission.STOCK_UPDATE))]
CanViewBatches = Annotated[User, Depends(require_any(Permission.STOCK_VIEW, Permission.EXPIRY_VIEW))]
CanUpdateExpiry = Annotated[User, Depends(require(Permission.EXPIRY_UPDATE))]
CanViewExpiry = Annotated[User, Depends(require(Permission.EXPIRY_VIEW))]
IdempotencyKey = Annotated[
    str | None,
    Header(
        alias="Idempotency-Key",
        max_length=IDEMPOTENCY_KEY_MAX_LENGTH,
        description="Same key again = same result, stock is not moved twice (safe retries)",
    ),
]

HIDE_UNSET = {"response_model_exclude_unset": True}
MOVEMENT = {"status_code": status.HTTP_201_CREATED, "response_model": DataResponse[AdjustmentOut], **HIDE_UNSET}


def _respond(result: StockResult, user: User, response: Response) -> DataResponse[AdjustmentOut]:
    if result.replayed:
        response.status_code = status.HTTP_200_OK
        response.headers["Idempotent-Replayed"] = "true"
    return DataResponse(data=AdjustmentOut.for_user(result.adjustment, result.products, user))


# --- Movements --------------------------------------------------------------------------------------


@router.post("/inventory/stock-in", summary="Receive stock (creates a batch)", **MOVEMENT)
def stock_in(
    body: StockInRequest, user: CanUpdateStock, inventory: Inventory, response: Response, key: IdempotencyKey = None
) -> DataResponse[AdjustmentOut]:
    return _respond(inventory.stock_in(user, body.model_dump(), key), user, response)


@router.post("/inventory/stock-out", summary="Take stock out (FEFO unless a batch is chosen)", **MOVEMENT)
def stock_out(
    body: StockOutRequest, user: CanUpdateStock, inventory: Inventory, response: Response, key: IdempotencyKey = None
) -> DataResponse[AdjustmentOut]:
    return _respond(inventory.stock_out(user, body.model_dump(), key), user, response)


@router.post("/inventory/adjust", summary="Set a batch to the counted quantity", **MOVEMENT)
def adjust(
    body: AdjustRequest, user: CanUpdateStock, inventory: Inventory, response: Response, key: IdempotencyKey = None
) -> DataResponse[AdjustmentOut]:
    return _respond(inventory.adjust(user, body.model_dump(), key), user, response)


@router.post("/inventory/damage", summary="Record damaged goods", **MOVEMENT)
def damage(
    body: DamageRequest, user: CanUpdateStock, inventory: Inventory, response: Response, key: IdempotencyKey = None
) -> DataResponse[AdjustmentOut]:
    return _respond(inventory.damage(user, body.model_dump(), key), user, response)


@router.post("/inventory/expired-writeoff", summary="Write off expired batches", **MOVEMENT)
def write_off(
    body: WriteOffRequest, user: CanUpdateStock, inventory: Inventory, response: Response, key: IdempotencyKey = None
) -> DataResponse[AdjustmentOut]:
    return _respond(inventory.write_off_expired(user, body.batch_ids, body.notes, key), user, response)


# --- Batches ----------------------------------------------------------------------------------------


@router.get("/products/{product_id}/batches", response_model=DataResponse[list[BatchOut]], **HIDE_UNSET)
def product_batches(
    product_id: int, user: CanViewBatches, db: DbSession, include_empty: bool = False
) -> DataResponse[list[BatchOut]]:
    """Batches in FEFO order (the one to sell first is on top)."""
    product = get_in_store(db, Product, product_id, user.store_id)
    stmt = select(ProductBatch).where(ProductBatch.product_id == product.id)
    if not include_empty:
        stmt = stmt.where(ProductBatch.quantity_remaining > 0)
    stmt = stmt.order_by(ProductBatch.expiry_date.is_(None), ProductBatch.expiry_date, ProductBatch.id)
    today, limits = store_today(), expiry_limits(db, user.store_id)
    return DataResponse(data=[BatchOut.for_user(b, user, today, limits) for b in db.scalars(stmt)])


@router.patch(
    "/batches/{batch_id}", response_model=DataResponse[BatchOut], summary="Fix batch number or dates", **HIDE_UNSET
)
def update_batch(
    batch_id: int, body: BatchUpdateRequest, user: CanUpdateExpiry, inventory: Inventory, db: DbSession
) -> DataResponse[BatchOut]:
    batch = inventory.update_batch(user, batch_id, body.model_dump(exclude_unset=True))
    return DataResponse(data=BatchOut.for_user(batch, user, store_today(), expiry_limits(db, user.store_id)))


@router.get(
    "/inventory/fefo-preview", response_model=DataResponse[FefoPreviewOut], summary="Which batches FEFO would use"
)
def fefo_preview(
    user: CanViewStock,
    db: DbSession,
    product_id: int,
    quantity: Annotated[Decimal, Query(gt=0, le=MAX_QUANTITY)],
) -> DataResponse[FefoPreviewOut]:
    product = get_in_store(db, Product, product_id, user.store_id)
    batches = list(
        db.scalars(select(ProductBatch).where(ProductBatch.product_id == product.id).order_by(ProductBatch.id))
    )
    today = store_today()
    usable = [b for b in batches if b.quantity_remaining > 0 and not is_expired(b, today)]
    available = sum((b.quantity_remaining for b in usable), Decimal(0))
    allocations = allocate(usable, min(quantity, available), today) if available else []
    lines = [
        FefoLineOut(
            batch_id=a.batch.id, batch_number=a.batch.batch_number, expiry_date=a.batch.expiry_date, quantity=a.quantity
        )
        for a in allocations
    ]
    return DataResponse(data=FefoPreviewOut(available=available, enough=available >= quantity, lines=lines))


# --- History ----------------------------------------------------------------------------------------


def _utc_start(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=store_tz()).astimezone(UTC).replace(tzinfo=None)


@router.get("/inventory/transactions", response_model=Page[TransactionOut], summary="Stock history", **HIDE_UNSET)
def transactions(
    user: CanViewStock,
    db: DbSession,
    pagination: Pagination,
    product_id: int | None = None,
    batch_id: int | None = None,
    type: Annotated[list[StockTransactionType] | None, Query()] = None,  # noqa: A002
    user_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> Page[TransactionOut]:
    """Dates are store-local days (IST)."""
    stmt = (
        select(StockTransaction)
        .options(
            selectinload(StockTransaction.product),
            selectinload(StockTransaction.batch),
            selectinload(StockTransaction.user),
        )
        .where(StockTransaction.store_id == user.store_id)
        .order_by(StockTransaction.id.desc())
    )
    if product_id:
        stmt = stmt.where(StockTransaction.product_id == product_id)
    if batch_id:
        stmt = stmt.where(StockTransaction.batch_id == batch_id)
    if type:
        stmt = stmt.where(StockTransaction.type.in_([t.value for t in type]))
    if user_id:
        stmt = stmt.where(StockTransaction.user_id == user_id)
    if date_from:
        stmt = stmt.where(StockTransaction.created_at >= _utc_start(date_from))
    if date_to:
        stmt = stmt.where(StockTransaction.created_at < _utc_start(date_to + timedelta(days=1)))
    return paginate(db, stmt, pagination, lambda tx: TransactionOut.for_user(tx, user))


@router.get("/inventory/adjustments/{adjustment_id}", response_model=DataResponse[AdjustmentOut], **HIDE_UNSET)
def get_adjustment(adjustment_id: int, user: CanViewStock, db: DbSession) -> DataResponse[AdjustmentOut]:
    adjustment = db.scalar(
        select(InventoryAdjustment)
        .options(selectinload(InventoryAdjustment.lines))
        .where(InventoryAdjustment.id == adjustment_id, InventoryAdjustment.store_id == user.store_id)
    )
    if adjustment is None:
        raise AppError(ErrorCode.NOT_FOUND)
    product_ids = {line.product_id for line in adjustment.lines}
    products = list(db.scalars(select(Product).where(Product.id.in_(product_ids)))) if product_ids else []
    return DataResponse(data=AdjustmentOut.for_user(adjustment, products, user))


# --- Expiry dashboard -------------------------------------------------------------------------------


@router.get("/expiry/summary", response_model=DataResponse[ExpirySummaryOut], tags=["expiry"], **HIDE_UNSET)
def expiry_summary(user: CanViewExpiry, expiry: Annotated[ExpiryService, Depends()]) -> DataResponse[ExpirySummaryOut]:
    """Expired, and expiring within each day limit (default 7 / 15 / 30, cumulative from today)."""
    today, buckets = expiry.summary(user)
    show_cost = user.has_permission(Permission.PRICING_VIEW_PURCHASE)
    out = []
    for b in buckets:
        fields = {"key": b.key, "days": b.days, "batches": b.batches, "products": b.products, "quantity": b.quantity}
        if show_cost:
            fields["cost_value"] = b.cost_value
        out.append(ExpiryBucketOut(**fields))
    return DataResponse(data=ExpirySummaryOut(as_of=today, buckets=out))


@router.get("/expiry/batches", response_model=Page[ExpiryBatchOut], tags=["expiry"], **HIDE_UNSET)
def expiry_batches(
    user: CanViewExpiry,
    expiry: Annotated[ExpiryService, Depends()],
    db: DbSession,
    pagination: Pagination,
    status_filter: Annotated[ExpiryStatus, Query(alias="status")] = ExpiryStatus.EXPIRING,
    within_days: Annotated[int | None, Query(ge=0, le=EXPIRY_LOOKAHEAD_MAX_DAYS)] = None,
    category_id: int | None = None,
    product_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> Page[ExpiryBatchOut]:
    """Batches that still hold stock, soonest expiry first."""
    filters = ExpiryFilters(status_filter, within_days, category_id, product_id, date_from, date_to)
    today, limits = store_today(), expiry_limits(db, user.store_id)
    return paginate(
        db, expiry.batches_query(user, filters), pagination, lambda b: ExpiryBatchOut.for_user(b, user, today, limits)
    )
