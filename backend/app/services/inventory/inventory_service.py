"""All stock changes go through this service.

Every change:
  - runs in one database transaction, locking the product row first and then its batches
    (two people updating the same product at once can never corrupt the numbers);
  - creates one inventory_adjustments header (who, why, when) and one stock_transactions line per batch
    touched, with quantities before and after — the ledger is never edited;
  - refreshes the product's cached stock columns.

A request may carry an Idempotency-Key: if the same key arrives again (a retry on a weak connection),
the first result is returned and stock is not moved twice.

Future POS sales will call `take_stock()` the same way.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession
from app.core.clock import store_today, utc_now
from app.core.errors import AppError, field_error
from app.core.i18n import t
from app.core.money import is_whole, money
from app.enums.activity import ActivityAction, AuditSubject
from app.enums.error_code import ErrorCode
from app.enums.permission import Permission
from app.enums.stock import AdjustmentType, StockReason, StockTransactionType
from app.models import InventoryAdjustment, Product, ProductBatch, StockTransaction, User
from app.services.audit import Audit, changed_fields
from app.services.inventory.fefo import InsufficientStockError, allocate, is_expired
from app.services.inventory.stock_cache import refresh_product_stock
from app.services.notifications.alerts import AlertService
from app.services.notifications.push import deliver

ADJUSTMENT_REFERENCE = "inventory_adjustment"

_AUDIT_ACTION = {
    AdjustmentType.STOCK_IN: ActivityAction.STOCK_IN,
    AdjustmentType.STOCK_OUT: ActivityAction.STOCK_OUT,
    AdjustmentType.ADJUSTMENT: ActivityAction.STOCK_ADJUSTED,
    AdjustmentType.DAMAGE: ActivityAction.STOCK_DAMAGED,
    AdjustmentType.EXPIRY_WRITEOFF: ActivityAction.STOCK_EXPIRED_WRITTEN_OFF,
}


@dataclass
class StockResult:
    adjustment: InventoryAdjustment
    products: list[Product]
    replayed: bool = False


class InventoryService:
    def __init__(self, db: DbSession, audit: Audit) -> None:
        self.db = db
        self.audit = audit

    # --- Public operations ------------------------------------------------------------------------

    def stock_in(self, user: User, data: dict[str, Any], key: str | None) -> StockResult:
        """Receive stock as a new batch. The very first receipt of a product is recorded as opening stock."""
        if replay := self._replay(user, key):
            return replay
        reason = StockReason(data.get("reason") or StockReason.PURCHASE)
        self._check_reason(AdjustmentType.STOCK_IN, reason)

        product = self._lock_product(user, data["product_id"])
        quantity = Decimal(data["quantity"])
        self._check_unit(product, quantity, "quantity")
        cost = self._batch_cost(user, product, data.get("purchase_price"))
        self._check_batch_dates(product, data.get("manufacturing_date"), data.get("expiry_date"), receiving=True)

        batches = self._lock_batches(product)
        first_receipt = not batches
        adjustment = self._start(user, AdjustmentType.STOCK_IN, reason, data.get("notes"), key)

        batch = ProductBatch(
            store_id=product.store_id,
            product_id=product.id,
            batch_number=data.get("batch_number"),
            manufacturing_date=data.get("manufacturing_date"),
            expiry_date=data.get("expiry_date"),
            quantity_received=quantity,
            quantity_remaining=Decimal(0),
            purchase_price=cost,
            received_at=utc_now(),
            notes=data.get("notes"),
            created_by=user.id,
        )
        self.db.add(batch)
        self.db.flush()
        if not batch.batch_number:
            batch.batch_number = f"B{batch.id:06d}"

        tx_type = StockTransactionType.OPENING if first_receipt else StockTransactionType.STOCK_IN
        self._move(user, adjustment, product, batch, quantity, tx_type, self._total(batches))
        if first_receipt:
            product.opening_stock = quantity
        return self._finish(user, adjustment, [product])

    def stock_out(self, user: User, data: dict[str, Any], key: str | None) -> StockResult:
        """Take stock out. Without a batch, FEFO picks the batches; expired batches are never used."""
        if replay := self._replay(user, key):
            return replay
        reason = StockReason(data["reason"])
        self._check_reason(AdjustmentType.STOCK_OUT, reason)
        product = self._lock_product(user, data["product_id"])
        quantity = Decimal(data["quantity"])
        self._check_unit(product, quantity, "quantity")
        adjustment = self._start(user, AdjustmentType.STOCK_OUT, reason, data.get("notes"), key)
        self.take_stock(user, adjustment, product, quantity, StockTransactionType.STOCK_OUT, data.get("batch_id"))
        return self._finish(user, adjustment, [product])

    def adjust(self, user: User, data: dict[str, Any], key: str | None) -> StockResult:
        """Set a batch to the quantity actually counted on the shelf."""
        if replay := self._replay(user, key):
            return replay
        reason = StockReason(data.get("reason") or StockReason.COUNT_CORRECTION)
        self._check_reason(AdjustmentType.ADJUSTMENT, reason)
        product, batch, batches = self._lock_batch(user, data["batch_id"])
        counted = Decimal(data["counted_quantity"])
        self._check_unit(product, counted, "counted_quantity")
        difference = counted - batch.quantity_remaining
        if difference == 0:
            raise field_error("counted_quantity", "validation.no_change")

        adjustment = self._start(user, AdjustmentType.ADJUSTMENT, reason, data.get("notes"), key)
        tx_type = StockTransactionType.ADJUSTMENT_IN if difference > 0 else StockTransactionType.ADJUSTMENT_OUT
        self._move(user, adjustment, product, batch, difference, tx_type, self._total(batches))
        return self._finish(user, adjustment, [product])

    def damage(self, user: User, data: dict[str, Any], key: str | None) -> StockResult:
        if replay := self._replay(user, key):
            return replay
        reason = StockReason(data["reason"])
        self._check_reason(AdjustmentType.DAMAGE, reason)
        product, batch, batches = self._lock_batch(user, data["batch_id"])
        quantity = Decimal(data["quantity"])
        self._check_unit(product, quantity, "quantity")
        if quantity > batch.quantity_remaining:
            raise self._insufficient(batch.quantity_remaining)

        adjustment = self._start(user, AdjustmentType.DAMAGE, reason, data.get("notes"), key)
        self._move(user, adjustment, product, batch, -quantity, StockTransactionType.DAMAGED, self._total(batches))
        return self._finish(user, adjustment, [product])

    def write_off_expired(self, user: User, batch_ids: list[int], notes: str | None, key: str | None) -> StockResult:
        """Remove everything left in batches that have expired."""
        if replay := self._replay(user, key):
            return replay
        today = store_today()
        product_ids = sorted(
            set(
                self.db.scalars(
                    select(ProductBatch.product_id).where(
                        ProductBatch.id.in_(batch_ids), ProductBatch.store_id == user.store_id
                    )
                )
            )
        )
        adjustment = self._start(user, AdjustmentType.EXPIRY_WRITEOFF, StockReason.EXPIRED, notes, key)

        found: set[int] = set()
        products: list[Product] = []
        for product_id in product_ids:  # fixed order avoids deadlocks between concurrent write-offs
            product = self._lock_product(user, product_id)
            batches = self._lock_batches(product)
            running = self._total(batches)
            for batch in batches:
                if batch.id not in batch_ids:
                    continue
                found.add(batch.id)
                if not is_expired(batch, today):
                    raise AppError(ErrorCode.BATCH_NOT_EXPIRED)
                if batch.quantity_remaining > 0:
                    running = self._move(
                        user,
                        adjustment,
                        product,
                        batch,
                        -batch.quantity_remaining,
                        StockTransactionType.EXPIRED,
                        running,
                    )
            products.append(product)

        if found != set(batch_ids):
            raise field_error("batch_ids", "validation.not_found_in_store")
        return self._finish(user, adjustment, products)

    def update_batch(self, user: User, batch_id: int, values: dict[str, Any]) -> ProductBatch:
        """Correct batch number or dates (never the quantity — that goes through `adjust`)."""
        product, batch, _ = self._lock_batch(user, batch_id)
        manufacturing = values.get("manufacturing_date", batch.manufacturing_date)
        expiry = values.get("expiry_date", batch.expiry_date)
        if "expiry_date" in values and expiry is None and product.track_expiry:
            raise field_error("expiry_date", "validation.missing", attribute=t("attributes.expiry_date"))
        self._check_batch_dates(product, manufacturing, expiry, receiving=False)

        old, new = changed_fields(batch, values)
        pushes = []
        if new:
            refresh_product_stock(self.db, product)
            pushes = AlertService(self.db).evaluate_stock(product)
            self.audit.record(
                ActivityAction.BATCH_UPDATED,
                actor=user,
                subject=(AuditSubject.BATCH, batch.id),
                properties={"product_id": product.id, "old": old, "new": new},
            )
        self.db.commit()
        deliver(self.db, pushes)
        return batch

    # --- Reusable building block (also for the future POS) ---------------------------------------

    def take_stock(
        self,
        user: User,
        adjustment: InventoryAdjustment,
        product: Product,
        quantity: Decimal,
        tx_type: StockTransactionType,
        batch_id: int | None = None,
    ) -> None:
        """Remove `quantity` from a locked product: from the given batch, or by FEFO across batches."""
        batches = self._lock_batches(product)
        running = self._total(batches)
        today = store_today()

        if batch_id is not None:
            batch = next((b for b in batches if b.id == batch_id), None)
            if batch is None:
                raise field_error("batch_id", "validation.not_found_in_store")
            if is_expired(batch, today):
                raise AppError(ErrorCode.BATCH_EXPIRED)
            if quantity > batch.quantity_remaining:
                raise self._insufficient(batch.quantity_remaining)
            self._move(user, adjustment, product, batch, -quantity, tx_type, running)
            return

        try:
            allocations = allocate(batches, quantity, today)
        except InsufficientStockError as exc:
            raise self._insufficient(exc.available) from exc
        for allocation in allocations:
            running = self._move(user, adjustment, product, allocation.batch, -allocation.quantity, tx_type, running)

    # --- Internals --------------------------------------------------------------------------------

    def _lock_product(self, user: User, product_id: int) -> Product:
        product = self.db.scalar(
            select(Product)
            .where(Product.id == product_id, Product.store_id == user.store_id, Product.deleted_at.is_(None))
            .with_for_update()
        )
        if product is None:
            raise field_error("product_id", "validation.not_found_in_store")
        return product

    def _lock_batches(self, product: Product) -> list[ProductBatch]:
        return list(
            self.db.scalars(
                select(ProductBatch)
                .where(ProductBatch.product_id == product.id)
                .order_by(ProductBatch.id)
                .with_for_update()
            )
        )

    def _lock_batch(self, user: User, batch_id: int) -> tuple[Product, ProductBatch, list[ProductBatch]]:
        product_id = self.db.scalar(
            select(ProductBatch.product_id).where(ProductBatch.id == batch_id, ProductBatch.store_id == user.store_id)
        )
        if product_id is None:
            raise field_error("batch_id", "validation.not_found_in_store")
        product = self._lock_product(user, product_id)  # product first, then batches: same order everywhere
        batches = self._lock_batches(product)
        return product, next(b for b in batches if b.id == batch_id), batches

    @staticmethod
    def _total(batches: Iterable[ProductBatch]) -> Decimal:
        return sum((b.quantity_remaining for b in batches), Decimal(0))

    def _replay(self, user: User, key: str | None) -> StockResult | None:
        if not key:
            return None
        adjustment = self.db.scalar(
            select(InventoryAdjustment).where(
                InventoryAdjustment.store_id == user.store_id, InventoryAdjustment.idempotency_key == key
            )
        )
        if adjustment is None:
            return None
        product_ids = {line.product_id for line in adjustment.lines}
        products = list(self.db.scalars(select(Product).where(Product.id.in_(product_ids)))) if product_ids else []
        return StockResult(adjustment=adjustment, products=products, replayed=True)

    def _start(
        self, user: User, kind: AdjustmentType, reason: StockReason, notes: str | None, key: str | None
    ) -> InventoryAdjustment:
        adjustment = InventoryAdjustment(
            store_id=user.store_id,
            type=kind.value,
            reason_code=reason.value,
            notes=notes,
            idempotency_key=key,
            created_by=user.id,
        )
        self.db.add(adjustment)
        try:
            self.db.flush()
        except IntegrityError as exc:  # the same key arrived twice at the same moment; the first one wins
            self.db.rollback()
            raise AppError(ErrorCode.CONFLICT) from exc
        return adjustment

    def _move(
        self,
        user: User,
        adjustment: InventoryAdjustment,
        product: Product,
        batch: ProductBatch,
        change: Decimal,
        tx_type: StockTransactionType,
        product_before: Decimal,
    ) -> Decimal:
        """Apply one change to one batch and write its ledger line. Returns the product total after."""
        batch_before = batch.quantity_remaining
        batch.quantity_remaining = batch_before + change
        product_after = product_before + change
        self.db.add(
            StockTransaction(
                store_id=product.store_id,
                product_id=product.id,
                batch_id=batch.id,
                type=tx_type.value,
                quantity_change=change,
                product_qty_before=product_before,
                product_qty_after=product_after,
                batch_qty_before=batch_before,
                batch_qty_after=batch.quantity_remaining,
                unit_cost=batch.purchase_price,
                reason=adjustment.reason_code,
                reference_type=ADJUSTMENT_REFERENCE,
                reference_id=adjustment.id,
                idempotency_key=adjustment.idempotency_key,
                user_id=user.id,
            )
        )
        return product_after

    def _finish(self, user: User, adjustment: InventoryAdjustment, products: list[Product]) -> StockResult:
        self.db.flush()
        lines = list(
            self.db.scalars(
                select(StockTransaction).where(
                    StockTransaction.reference_type == ADJUSTMENT_REFERENCE,
                    StockTransaction.reference_id == adjustment.id,
                )
            )
        )
        if not lines:
            raise field_error("batch_ids", "validation.nothing_to_write_off")
        costs = [abs(line.quantity_change) * line.unit_cost for line in lines if line.unit_cost is not None]
        adjustment.cost_impact = money(sum(costs, Decimal(0))) if costs else None

        for product in products:
            refresh_product_stock(self.db, product)
        alerts = AlertService(self.db)
        pushes = [message for product in products for message in alerts.evaluate_stock(product)]
        self.audit.record(
            _AUDIT_ACTION[AdjustmentType(adjustment.type)],
            actor=user,
            subject=(AuditSubject.ADJUSTMENT, adjustment.id),
            properties={
                "reason": adjustment.reason_code,
                "lines": [
                    {"product_id": line.product_id, "batch_id": line.batch_id, "change": line.quantity_change}
                    for line in lines
                ],
            },
        )
        self.db.commit()
        deliver(self.db, pushes)
        for product in products:
            self.db.refresh(product)
        adjustment = self.db.scalar(
            select(InventoryAdjustment)
            .options(selectinload(InventoryAdjustment.lines))
            .where(InventoryAdjustment.id == adjustment.id)
        )
        return StockResult(adjustment=adjustment, products=products)

    # --- Validation helpers -----------------------------------------------------------------------

    @staticmethod
    def _check_reason(kind: AdjustmentType, reason: StockReason) -> None:
        if reason not in StockReason.allowed_for(kind):
            raise field_error("reason", "validation.reason_not_allowed")

    @staticmethod
    def _check_unit(product: Product, quantity: Decimal, field: str) -> None:
        if not product.unit.allows_decimal and not is_whole(quantity):
            raise field_error(field, "validation.whole_number_for_unit", unit=product.unit.short_name)

    @staticmethod
    def _batch_cost(user: User, product: Product, given: Decimal | None) -> Decimal | None:
        """Cost per unit for the batch. Users who can't see purchase prices can't set them either;
        their batches use the product's current purchase price."""
        if given is not None:
            if not user.has_permission(Permission.PRICING_VIEW_PURCHASE):
                raise field_error(
                    "purchase_price", "validation.field_not_permitted", attribute=t("attributes.purchase_price")
                )
            return Decimal(given)
        return product.purchase_price

    @staticmethod
    def _check_batch_dates(
        product: Product, manufacturing: date | None, expiry: date | None, *, receiving: bool
    ) -> None:
        today = store_today()
        errors: dict[str, list[str]] = {}
        if receiving and product.track_expiry and expiry is None:
            errors["expiry_date"] = [t("validation.missing", attribute=t("attributes.expiry_date"))]
        if receiving and expiry is not None and expiry < today:
            errors["expiry_date"] = [t("validation.expiry_in_past")]
        if manufacturing is not None and manufacturing > today:
            errors["manufacturing_date"] = [t("validation.manufacturing_in_future")]
        if manufacturing is not None and expiry is not None and expiry < manufacturing:
            errors["expiry_date"] = [t("validation.expiry_before_manufacturing")]
        if errors:
            raise AppError(ErrorCode.VALIDATION_FAILED, errors=errors)

    @staticmethod
    def _insufficient(available: Decimal) -> AppError:
        return AppError(
            ErrorCode.STOCK_INSUFFICIENT, errors={"quantity": [t("validation.only_available", available=available)]}
        )
