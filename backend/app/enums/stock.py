from enum import StrEnum


class StockStatus(StrEnum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"


class StockTransactionType(StrEnum):
    OPENING = "opening"
    STOCK_IN = "stock_in"
    STOCK_OUT = "stock_out"
    ADJUSTMENT_IN = "adjustment_in"
    ADJUSTMENT_OUT = "adjustment_out"
    DAMAGED = "damaged"
    EXPIRED = "expired"
    # Future (V2 POS / purchasing)
    SALE = "sale"
    SALE_RETURN = "sale_return"
    PURCHASE_RETURN = "purchase_return"


class AdjustmentType(StrEnum):
    STOCK_IN = "stock_in"
    STOCK_OUT = "stock_out"
    ADJUSTMENT = "adjustment"
    DAMAGE = "damage"
    EXPIRY_WRITEOFF = "expiry_writeoff"


class AlertType(StrEnum):
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    EXPIRING_SOON = "expiring_soon"
    EXPIRED = "expired"


class AlertStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"


class StockReason(StrEnum):
    """Why stock changed. Each kind of movement allows only the reasons that make sense for it."""

    PURCHASE = "purchase"
    CUSTOMER_RETURN = "customer_return"
    FOUND = "found"
    SOLD_MANUALLY = "sold_manually"
    RETURNED_TO_SUPPLIER = "returned_to_supplier"
    PERSONAL_USE = "personal_use"
    SAMPLE = "sample"
    THEFT = "theft"
    COUNT_CORRECTION = "count_correction"
    BROKEN = "broken"
    RODENT = "rodent"
    SPOILED = "spoiled"
    LEAKED = "leaked"
    EXPIRED = "expired"
    OTHER = "other"

    @classmethod
    def allowed_for(cls, kind: "AdjustmentType") -> frozenset["StockReason"]:
        return _ALLOWED_REASONS[kind]


_ALLOWED_REASONS: dict[AdjustmentType, frozenset[StockReason]] = {
    AdjustmentType.STOCK_IN: frozenset(
        {StockReason.PURCHASE, StockReason.CUSTOMER_RETURN, StockReason.FOUND, StockReason.OTHER}
    ),
    AdjustmentType.STOCK_OUT: frozenset(
        {
            StockReason.SOLD_MANUALLY,
            StockReason.RETURNED_TO_SUPPLIER,
            StockReason.PERSONAL_USE,
            StockReason.SAMPLE,
            StockReason.THEFT,
            StockReason.OTHER,
        }
    ),
    AdjustmentType.ADJUSTMENT: frozenset({StockReason.COUNT_CORRECTION, StockReason.OTHER}),
    AdjustmentType.DAMAGE: frozenset(
        {StockReason.BROKEN, StockReason.RODENT, StockReason.SPOILED, StockReason.LEAKED, StockReason.OTHER}
    ),
    AdjustmentType.EXPIRY_WRITEOFF: frozenset({StockReason.EXPIRED}),
}


class ExpiryBucket(StrEnum):
    """Colour band for a batch on the expiry screen. Day limits come from the expiry.buckets setting
    (default 7 / 15 / 30), so the names describe urgency rather than fixed day counts."""

    EXPIRED = "expired"  # red
    CRITICAL = "critical"  # within the 1st limit (7 days)
    WARNING = "warning"  # within the 2nd limit (15 days)
    NOTICE = "notice"  # within the 3rd limit (30 days)
    SAFE = "safe"  # green
    NO_EXPIRY = "no_expiry"  # grey


class ExpiryStatus(StrEnum):
    """Filter for the expiry batch list."""

    EXPIRED = "expired"
    EXPIRING = "expiring"  # not expired yet, within N days
    ALL = "all"
