"""Two people taking stock out of the same product at the same moment.

Uses real committed data and separate connections (not the rolled-back test transaction),
so the row locks are exercised exactly as in production. Cleans up after itself.
"""

import threading
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from app.core.clock import store_today, utc_now
from app.core.database import engine
from app.core.errors import AppError
from app.models import Category, Product, ProductBatch, Store, Unit, User
from app.services.audit import AuditLogger, RequestContext
from app.services.inventory.inventory_service import InventoryService


def _service(session: Session) -> InventoryService:
    return InventoryService(session, AuditLogger(session, RequestContext(ip_address=None, user_agent=None)))


def test_parallel_stock_out_never_oversells() -> None:
    with Session(engine) as setup:
        from app.db import seed

        seed.run(setup)
        user = setup.scalar(select(User).order_by(User.id))
        product = Product(
            store_id=setup.scalar(select(Store.id)),
            category_id=setup.scalar(select(Category.id)),
            unit_id=setup.scalar(select(Unit.id).where(Unit.short_name == "pcs")),
            name="Concurrency Test",
            slug="concurrency-test",
            sku="CONC-1",
            selling_price=Decimal(10),
        )
        setup.add(product)
        setup.flush()
        setup.add(
            ProductBatch(
                store_id=product.store_id,
                product_id=product.id,
                expiry_date=store_today() + timedelta(days=30),
                quantity_received=Decimal(10),
                quantity_remaining=Decimal(10),
                received_at=utc_now(),
                created_by=user.id,
            )
        )
        setup.commit()
        product_id, user_id = product.id, user.id

    outcomes: list[str] = []
    barrier = threading.Barrier(2)

    def take_six() -> None:
        with Session(engine, expire_on_commit=False) as session:
            actor = session.get(User, user_id)
            barrier.wait()
            try:
                _service(session).stock_out(
                    actor, {"product_id": product_id, "quantity": Decimal(6), "reason": "sold_manually"}, None
                )
                outcomes.append("ok")
            except AppError as exc:
                outcomes.append(exc.code.value)

    try:
        threads = [threading.Thread(target=take_six) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert sorted(outcomes) == ["STOCK_INSUFFICIENT", "ok"]
        with Session(engine) as check:
            assert (
                check.scalar(select(ProductBatch.quantity_remaining).where(ProductBatch.product_id == product_id)) == 4
            )
            assert check.get(Product, product_id).current_stock == 4
    finally:
        with engine.begin() as conn:  # raw SQL: the ORM refuses to delete ledger rows, by design
            conn.execute(text("DELETE FROM stock_transactions WHERE product_id = :p"), {"p": product_id})
            conn.execute(text("DELETE FROM activity_logs WHERE action LIKE 'stock.%'"))
            conn.execute(text("DELETE FROM inventory_adjustments WHERE type = :t"), {"t": "stock_out"})
            conn.execute(delete(ProductBatch).where(ProductBatch.product_id == product_id))
            conn.execute(delete(Product).where(Product.id == product_id))
