from datetime import date

from pydantic import BaseModel

from app.models import User
from app.schemas.common import MoneyOut, QuantityOut
from app.schemas.inventory import TransactionOut
from app.schemas.products import ProductOut
from app.services.dashboard_service import Dashboard


class StockTotalsOut(BaseModel):
    total_quantity: QuantityOut
    low_stock: int
    out_of_stock: int


class ExpiryTotalsOut(BaseModel):
    expired_batches: int
    expiring_batches: int
    expiring_within_days: int


class ValueOut(BaseModel):
    purchase_cost: MoneyOut | None = None
    selling_value: MoneyOut | None = None


class CategoryStockOut(BaseModel):
    id: int
    name: str
    products: int
    quantity: QuantityOut


class MovementDayOut(BaseModel):
    day: date
    stock_in: QuantityOut
    stock_out: QuantityOut


class DashboardOut(BaseModel):
    """Blocks the user may not see are left out of the JSON (endpoint uses exclude_unset)."""

    products_total: int
    products_active: int
    categories_total: int
    sellers_total: int | None = None
    stock: StockTotalsOut | None = None
    expiry: ExpiryTotalsOut | None = None
    value: ValueOut | None = None
    stock_by_category: list[CategoryStockOut] | None = None
    movements: list[MovementDayOut] | None = None
    recent_products: list[ProductOut] | None = None
    recent_movements: list[TransactionOut] | None = None

    @classmethod
    def for_user(cls, d: Dashboard, user: User) -> "DashboardOut":
        fields: dict = {
            "products_total": d.products_total,
            "products_active": d.products_active,
            "categories_total": d.categories_total,
        }
        if d.sellers_total is not None:
            fields["sellers_total"] = d.sellers_total
        if d.stock is not None:
            fields["stock"] = StockTotalsOut(**d.stock)
            fields["stock_by_category"] = [CategoryStockOut(**c) for c in d.stock_by_category or []]
            fields["movements"] = [
                MovementDayOut(day=m.day, stock_in=m.stock_in, stock_out=m.stock_out) for m in d.movements or []
            ]
            fields["recent_movements"] = [TransactionOut.for_user(t, user) for t in d.recent_movements or []]
        if d.expiry is not None:
            fields["expiry"] = ExpiryTotalsOut(**d.expiry)
        if d.value:
            fields["value"] = ValueOut(**d.value)
        if d.recent_products is not None:
            fields["recent_products"] = [ProductOut.for_user(p, user) for p in d.recent_products]
        return cls(**fields)
