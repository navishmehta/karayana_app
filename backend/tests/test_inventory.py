from datetime import timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.clock import store_today
from app.enums.permission import Permission
from app.models import Product, ProductBatch, StockTransaction, User
from tests.helpers import admin_headers, create_seller, make_product, seller_headers, unit_id

IN, OUT = "/api/v1/inventory/stock-in", "/api/v1/inventory/stock-out"
TODAY = store_today()


def _days(n: int) -> str:
    return (TODAY + timedelta(days=n)).isoformat()


def _receive(client: TestClient, headers: dict, product_id: int, qty: str, expiry_in_days: int | None = 30, **extra):
    body = {"product_id": product_id, "quantity": qty} | extra
    if expiry_in_days is not None:
        body["expiry_date"] = _days(expiry_in_days)
    return client.post(IN, json=body, headers=headers)


def _batch(db: Session, product_id: int, qty: str, expiry_in_days: int | None) -> ProductBatch:
    """A batch inserted directly (e.g. one that is already expired, which stock-in refuses)."""
    batch = ProductBatch(
        store_id=db.get(Product, product_id).store_id,
        product_id=product_id,
        batch_number=f"X{qty}",
        expiry_date=TODAY + timedelta(days=expiry_in_days) if expiry_in_days is not None else None,
        quantity_received=Decimal(qty),
        quantity_remaining=Decimal(qty),
        received_at=TODAY,
        created_by=db.scalar(select(func.min(User.id))),
    )
    db.add(batch)
    db.commit()
    return batch


def _ledger(db: Session, product_id: int) -> list[StockTransaction]:
    return list(
        db.scalars(
            select(StockTransaction).where(StockTransaction.product_id == product_id).order_by(StockTransaction.id)
        )
    )


def test_first_receipt_is_opening_stock_then_stock_in(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db, min_stock_level=Decimal(5))
    headers = admin_headers(client)

    first = _receive(client, headers, product.id, "12", purchase_price="38.50").json()["data"]
    assert first["type"] == "stock_in"
    assert first["lines"][0]["type"] == "opening"
    assert first["lines"][0]["unit_cost"] == "38.50"
    assert first["cost_impact"] == "462.00"
    assert first["products"][0] == {
        "id": product.id,
        "name": product.name,
        "current_stock": "12.000",
        "sellable_stock": "12.000",
        "stock_status": "in_stock",
        "next_expiry_date": _days(30),
    }
    second = _receive(client, headers, product.id, "3", expiry_in_days=10).json()["data"]
    assert second["lines"][0]["type"] == "stock_in"
    assert second["products"][0]["next_expiry_date"] == _days(10)
    seeded_db.expire_all()
    assert seeded_db.get(Product, product.id).opening_stock == Decimal("12.000")


def test_stock_in_rules(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db)
    headers = admin_headers(client)

    def errors(**body) -> dict:
        return client.post(IN, json={"product_id": product.id, "quantity": "5"} | body, headers=headers).json()[
            "errors"
        ]

    assert errors() == {"expiry_date": ["Expiry date is required."]}
    assert errors(expiry_date=_days(-1)) == {
        "expiry_date": ["Expiry date has already passed. Record expired goods as a write-off."]
    }
    assert errors(expiry_date=_days(5), manufacturing_date=_days(1)) == {
        "manufacturing_date": ["Manufacturing date cannot be in the future."]
    }
    assert errors(expiry_date=_days(5), quantity="1.5") == {"quantity": ["Use a whole number for items sold in pcs."]}
    assert errors(expiry_date=_days(5), reason="theft") == {"reason": ["This reason cannot be used here."]}
    assert "quantity" in errors(quantity="0", expiry_date=_days(5))


def test_products_without_expiry_tracking_need_no_date(client: TestClient, seeded_db: Session) -> None:
    pen = make_product(seeded_db, track_expiry=False)
    response = _receive(client, admin_headers(client), pen.id, "100", expiry_in_days=None)
    assert response.status_code == 201
    assert response.json()["data"]["products"][0]["next_expiry_date"] is None


def test_loose_items_accept_decimals(client: TestClient, seeded_db: Session) -> None:
    rice = make_product(seeded_db, unit_id=unit_id(seeded_db, "kg"))
    data = _receive(client, admin_headers(client), rice.id, "25.750").json()["data"]
    assert data["products"][0]["current_stock"] == "25.750"


def test_stock_out_uses_fefo_and_skips_expired(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db)
    headers = admin_headers(client)
    _batch(seeded_db, product.id, "50", -1)  # expired: must never be sold
    late = _receive(client, headers, product.id, "10", expiry_in_days=60).json()["data"]["lines"][0]["batch"]["id"]
    early = _receive(client, headers, product.id, "4", expiry_in_days=5).json()["data"]["lines"][0]["batch"]["id"]

    data = client.post(
        OUT, json={"product_id": product.id, "quantity": "6", "reason": "sold_manually"}, headers=headers
    )
    lines = data.json()["data"]["lines"]
    assert [(line["batch"]["id"], line["quantity_change"]) for line in lines] == [(early, "-4.000"), (late, "-2.000")]
    assert data.json()["data"]["products"][0]["sellable_stock"] == "8.000"
    assert data.json()["data"]["products"][0]["current_stock"] == "58.000"  # expired 50 still counted until written off


def test_stock_out_more_than_sellable_is_refused(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db)
    headers = admin_headers(client)
    _batch(seeded_db, product.id, "50", -1)
    _receive(client, headers, product.id, "3")

    response = client.post(
        OUT, json={"product_id": product.id, "quantity": "4", "reason": "sold_manually"}, headers=headers
    )
    assert response.status_code == 409
    assert response.json() == {
        "message": "Not enough stock.",
        "code": "STOCK_INSUFFICIENT",
        "errors": {"quantity": ["Only 3.000 available."]},
    }
    assert len(_ledger(seeded_db, product.id)) == 1  # nothing changed


def test_stock_out_from_expired_batch_is_refused(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db)
    expired = _batch(seeded_db, product.id, "5", -2)
    body = {"product_id": product.id, "quantity": "1", "reason": "sold_manually", "batch_id": expired.id}
    assert client.post(OUT, json=body, headers=admin_headers(client)).json()["code"] == "BATCH_EXPIRED"


def test_adjust_damage_and_ledger_math(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db)
    headers = admin_headers(client)
    batch_id = _receive(client, headers, product.id, "20").json()["data"]["lines"][0]["batch"]["id"]

    counted = client.post(
        "/api/v1/inventory/adjust", json={"batch_id": batch_id, "counted_quantity": "17"}, headers=headers
    )
    assert counted.json()["data"]["lines"][0]["type"] == "adjustment_out"
    same = client.post(
        "/api/v1/inventory/adjust", json={"batch_id": batch_id, "counted_quantity": "17"}, headers=headers
    )
    assert same.status_code == 422

    damaged = {"batch_id": batch_id, "quantity": "2", "reason": "rodent", "notes": "shelf 3"}
    assert client.post("/api/v1/inventory/damage", json=damaged, headers=headers).status_code == 201

    ledger = _ledger(seeded_db, product.id)
    assert [(t.type, t.quantity_change, t.product_qty_after) for t in ledger] == [
        ("opening", Decimal("20.000"), Decimal("20.000")),
        ("adjustment_out", Decimal("-3.000"), Decimal("17.000")),
        ("damaged", Decimal("-2.000"), Decimal("15.000")),
    ]
    for previous, current in zip(ledger, ledger[1:], strict=False):  # every row continues from the previous one
        assert current.product_qty_before == previous.product_qty_after


def test_write_off_expired(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db)
    headers = admin_headers(client)
    expired = _batch(seeded_db, product.id, "7", -3)
    fresh = _receive(client, headers, product.id, "5").json()["data"]["lines"][0]["batch"]["id"]
    url = "/api/v1/inventory/expired-writeoff"

    assert client.post(url, json={"batch_ids": [fresh]}, headers=headers).json()["code"] == "BATCH_NOT_EXPIRED"
    data = client.post(url, json={"batch_ids": [expired.id]}, headers=headers).json()["data"]
    assert data["lines"][0]["type"] == "expired"
    assert data["lines"][0]["quantity_change"] == "-7.000"
    assert data["products"][0]["current_stock"] == "5.000"
    assert client.post(url, json={"batch_ids": [expired.id]}, headers=headers).status_code == 422  # nothing left


def test_idempotency_key_prevents_double_stock(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db)
    headers = admin_headers(client) | {"Idempotency-Key": "tap-123"}

    first = _receive(client, headers, product.id, "10")
    retry = _receive(client, headers, product.id, "10")

    assert first.status_code == 201
    assert retry.status_code == 200
    assert retry.headers["idempotent-replayed"] == "true"
    assert retry.json()["data"]["id"] == first.json()["data"]["id"]
    seeded_db.expire_all()
    assert seeded_db.get(Product, product.id).current_stock == Decimal("10.000")


def test_batch_dates_can_be_corrected_but_not_quantity(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db)
    headers = admin_headers(client)
    batch_id = _receive(client, headers, product.id, "5").json()["data"]["lines"][0]["batch"]["id"]

    fixed = client.patch(
        f"/api/v1/batches/{batch_id}", json={"expiry_date": _days(3), "batch_number": "LOT-9"}, headers=headers
    )
    assert fixed.json()["data"]["expiry_date"] == _days(3)
    assert fixed.json()["data"]["bucket"] == "critical"
    assert (
        client.patch(f"/api/v1/batches/{batch_id}", json={"quantity_remaining": "99"}, headers=headers).status_code
        == 422
    )
    assert client.patch(f"/api/v1/batches/{batch_id}", json={"expiry_date": None}, headers=headers).status_code == 422
    seeded_db.expire_all()
    assert seeded_db.get(Product, product.id).next_expiry_date == TODAY + timedelta(days=3)


def test_permissions(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db)
    viewer = seller_headers(client, create_seller(seeded_db, [Permission.PRODUCTS_VIEW, Permission.STOCK_VIEW]))
    keeper = seller_headers(
        client, create_seller(seeded_db, [Permission.PRODUCTS_VIEW, Permission.STOCK_VIEW, Permission.STOCK_UPDATE])
    )

    assert _receive(client, viewer, product.id, "5").status_code == 403
    received = _receive(client, keeper, product.id, "5")
    assert received.status_code == 201
    data = received.json()["data"]
    assert "cost_impact" not in data and "unit_cost" not in data["lines"][0]  # keeper can't see costs
    seeded_db.expire_all()
    assert seeded_db.scalar(select(ProductBatch.purchase_price)) == Decimal("40.00")  # product's cost used

    assert _receive(client, keeper, product.id, "5", purchase_price="1").json()["errors"] == {
        "purchase_price": ["You do not have permission to set Purchase price."]
    }
    assert client.get("/api/v1/inventory/transactions", headers=viewer).status_code == 200
    assert client.get(f"/api/v1/products/{product.id}/batches", headers=viewer).status_code == 200
    no_stock = seller_headers(client, create_seller(seeded_db, [Permission.PRODUCTS_VIEW]))
    assert client.get("/api/v1/inventory/transactions", headers=no_stock).status_code == 403


def test_history_filters_and_adjustment_detail(client: TestClient, seeded_db: Session) -> None:
    a, b = make_product(seeded_db), make_product(seeded_db)
    headers = admin_headers(client)
    adjustment_id = _receive(client, headers, a.id, "5").json()["data"]["id"]
    _receive(client, headers, b.id, "8")

    history = client.get("/api/v1/inventory/transactions", params={"product_id": a.id}, headers=headers).json()
    assert history["meta"]["total"] == 1
    assert history["data"][0]["user"]["name"] == "Store Admin"
    opening = client.get("/api/v1/inventory/transactions", params={"type": "opening"}, headers=headers).json()
    assert opening["meta"]["total"] == 2

    detail = client.get(f"/api/v1/inventory/adjustments/{adjustment_id}", headers=headers).json()["data"]
    assert detail["lines"][0]["product"]["id"] == a.id


def test_fefo_preview(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db)
    headers = admin_headers(client)
    _receive(client, headers, product.id, "4", expiry_in_days=5)
    _receive(client, headers, product.id, "10", expiry_in_days=60)

    params = {"product_id": product.id, "quantity": "6"}
    preview = client.get("/api/v1/inventory/fefo-preview", params=params, headers=headers).json()["data"]
    assert preview["enough"] is True
    assert [line["quantity"] for line in preview["lines"]] == ["4.000", "2.000"]
    params["quantity"] = "99"
    assert (
        client.get("/api/v1/inventory/fefo-preview", params=params, headers=headers).json()["data"]["enough"] is False
    )
