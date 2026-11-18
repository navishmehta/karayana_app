"""FEFO: First Expiry, First Out.

Pure logic (no database) so it is easy to test and reuse for the future POS:
take stock from the batch that expires first; batches without an expiry date go last;
ties go to the batch received first. Expired batches are never used — they must be written off.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol


class BatchLike(Protocol):
    id: int
    expiry_date: date | None
    quantity_remaining: Decimal


@dataclass(frozen=True)
class Allocation[B: BatchLike]:
    batch: B
    quantity: Decimal


class InsufficientStockError(Exception):
    def __init__(self, available: Decimal) -> None:
        super().__init__(f"only {available} available")
        self.available = available


def is_expired(batch: BatchLike, today: date) -> bool:
    return batch.expiry_date is not None and batch.expiry_date < today


def fefo_order[B: BatchLike](batches: Sequence[B]) -> list[B]:
    """Batches are expected in receiving order (by id); sorting is stable, so id breaks ties."""
    return sorted(batches, key=lambda b: (b.expiry_date is None, b.expiry_date or date.max))


def allocate[B: BatchLike](batches: Sequence[B], quantity: Decimal, today: date) -> list[Allocation[B]]:
    usable = [b for b in fefo_order(sorted(batches, key=lambda b: b.id)) if b.quantity_remaining > 0]
    usable = [b for b in usable if not is_expired(b, today)]
    available = sum((b.quantity_remaining for b in usable), Decimal(0))
    if quantity > available:
        raise InsufficientStockError(available)

    allocations: list[Allocation[B]] = []
    remaining = quantity
    for batch in usable:
        if remaining <= 0:
            break
        take = min(batch.quantity_remaining, remaining)
        allocations.append(Allocation(batch=batch, quantity=take))
        remaining -= take
    return allocations
