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
