from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import pytest

from app.services.inventory.fefo import InsufficientStockError, allocate, fefo_order

TODAY = date(2026, 11, 18)


@dataclass
class B:
    id: int
    expiry_date: date | None
    quantity_remaining: Decimal


def test_earliest_expiry_first_and_undated_last() -> None:
    batches = [B(1, None, Decimal(5)), B(2, date(2027, 3, 1), Decimal(5)), B(3, date(2026, 12, 1), Decimal(5))]
    assert [b.id for b in fefo_order(batches)] == [3, 2, 1]


def test_same_expiry_uses_oldest_receipt_first() -> None:
    batches = [B(7, date(2027, 1, 1), Decimal(5)), B(4, date(2027, 1, 1), Decimal(5))]
    assert [a.batch.id for a in allocate(batches, Decimal(6), TODAY)] == [4, 7]


def test_allocation_spans_batches() -> None:
    batches = [B(1, date(2026, 12, 1), Decimal(4)), B(2, date(2027, 1, 1), Decimal(10))]
    result = allocate(batches, Decimal(6), TODAY)
    assert [(a.batch.id, a.quantity) for a in result] == [(1, Decimal(4)), (2, Decimal(2))]


def test_expired_and_empty_batches_are_skipped() -> None:
    batches = [B(1, date(2026, 11, 17), Decimal(50)), B(2, date(2026, 12, 1), Decimal(0)), B(3, None, Decimal(3))]
    assert [(a.batch.id, a.quantity) for a in allocate(batches, Decimal(3), TODAY)] == [(3, Decimal(3))]


def test_expiring_today_is_still_sellable() -> None:
    assert allocate([B(1, TODAY, Decimal(1))], Decimal(1), TODAY)[0].batch.id == 1


def test_not_enough_stock_reports_what_is_available() -> None:
    with pytest.raises(InsufficientStockError) as exc:
        allocate([B(1, None, Decimal("2.5")), B(2, date(2026, 1, 1), Decimal(9))], Decimal(3), TODAY)
    assert exc.value.available == Decimal("2.5")
