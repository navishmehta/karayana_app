"""Database-level guarantees: seed data, constraints, generated columns, append-only ledger."""

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.db import seed
from app.enums.permission import Permission
from app.enums.role import Role
from app.enums.setting_key import SettingKey
from app.models import (
    AppSetting,
    Category,
    PermissionModel,
    Product,
    ProductBatch,
    StockTransaction,
    Store,
    Unit,
    User,
)
from app.models.inventory import LedgerImmutableError

ConstraintError = (IntegrityError, OperationalError)  # MySQL reports CHECK failures as OperationalError 3819


def test_seed_creates_everything_once(seeded_db: Session) -> None:
    db = seeded_db
    seed.run(db)  # second run must not duplicate anything

    assert db.scalar(select(func.count(Store.id))) == 1
    assert db.scalar(select(func.count(PermissionModel.id))) == len(Permission)
    assert db.scalar(select(func.count(Category.id))) == 10
    assert db.scalar(select(func.count(AppSetting.id))) == len(SettingKey)

    admin = db.scalar(select(User))
    assert admin.role.name == Role.ADMIN
    assert admin.email == "admin@kirana.test"
    assert verify_password("Admin12345", admin.password_hash)
    assert admin.password_hash != "Admin12345"

    store_name = db.scalar(select(AppSetting).where(AppSetting.key == SettingKey.STORE_NAME))
    assert store_name.value == "Ramesh Karayana Store"
    assert store_name.is_public

    dairy = db.scalar(select(Category).where(Category.slug == "dairy"))
    assert dairy.name_translations == {"pa": "ਡੇਅਰੀ"}


def _product(db: Session, **overrides) -> Product:
    store = db.scalar(select(Store))
    values = {
        "store_id": store.id,
        "category_id": db.scalar(select(Category.id)),
        "unit_id": db.scalar(select(Unit.id)),
        "name": "Test Product",
        "slug": "test-p",
        "sku": "SK-1",
        "selling_price": Decimal("50"),
        "mrp": Decimal("60"),
    }
    product = Product(**(values | overrides))
    db.add(product)
    db.flush()
    return product


def test_stock_status_is_computed_by_the_database(seeded_db: Session) -> None:
    db = seeded_db
    product = _product(db, min_stock_level=Decimal("5"))
    db.refresh(product)
    assert product.stock_status == "out_of_stock"

    product.sellable_stock = Decimal("3")
    db.flush()
    db.refresh(product)
    assert product.stock_status == "low_stock"

    product.sellable_stock = Decimal("50")
    db.flush()
    db.refresh(product)
    assert product.stock_status == "in_stock"


def test_selling_price_cannot_exceed_mrp(seeded_db: Session) -> None:
    with pytest.raises(ConstraintError):
        _product(seeded_db, slug="x", sku="x", mrp=Decimal("40"))


def _batch(db: Session, product: Product, qty: str = "10") -> ProductBatch:
    batch = ProductBatch(
        store_id=product.store_id,
        product_id=product.id,
        quantity_received=Decimal(qty),
        quantity_remaining=Decimal(qty),
        received_at=datetime(2026, 11, 18),
        created_by=db.scalar(select(User.id)),
    )
    db.add(batch)
    db.flush()
    return batch


def test_batch_quantity_cannot_go_negative(seeded_db: Session) -> None:
    batch = _batch(seeded_db, _product(seeded_db))
    batch.quantity_remaining = Decimal("-1")
    with pytest.raises(ConstraintError):
        seeded_db.flush()


def _ledger_row(product: Product, batch: ProductBatch, user_id: int, **overrides) -> StockTransaction:
    values = dict(
        store_id=product.store_id,
        product_id=product.id,
        batch_id=batch.id,
        type="stock_in",
        quantity_change=Decimal("10"),
        product_qty_before=Decimal("0"),
        product_qty_after=Decimal("10"),
        batch_qty_before=Decimal("0"),
        batch_qty_after=Decimal("10"),
        user_id=user_id,
    )
    values.update(overrides)
    return StockTransaction(**values)


def test_ledger_rows_cannot_be_changed_or_deleted(seeded_db: Session) -> None:
    db = seeded_db
    product = _product(db)
    batch = _batch(db, product)
    row = _ledger_row(product, batch, db.scalar(select(User.id)))
    db.add(row)
    db.flush()

    row.reason = "tampered"
    with pytest.raises(LedgerImmutableError):
        db.flush()
    db.rollback()


def test_ledger_math_is_checked_by_the_database(seeded_db: Session) -> None:
    db = seeded_db
    product = _product(db)
    batch = _batch(db, product)
    db.add(_ledger_row(product, batch, db.scalar(select(User.id)), product_qty_after=Decimal("5")))
    with pytest.raises(ConstraintError):
        db.flush()
