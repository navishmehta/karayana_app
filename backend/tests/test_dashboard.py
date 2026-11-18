from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.clock import store_today
from app.enums.permission import Permission
from app.services.inventory.stock_cache import refresh_product_stock
from tests.helpers import admin_headers, create_seller, make_product, seller_headers
from tests.test_inventory import _batch

URL = "/api/v1/dashboard"


def _stock(db: Session, product, qty: str, expiry_in_days: int | None) -> None:
    _batch(db, product.id, qty, expiry_in_days)
    refresh_product_stock(db, product)
    db.commit()


def _shop(db: Session):
    rice = make_product(
        db, "Rice", purchase_price=Decimal("40"), selling_price=Decimal("50"), min_stock_level=Decimal(5)
    )
    _stock(db, rice, "10", 60)
    milk = make_product(
        db, "Milk", purchase_price=Decimal("20"), selling_price=Decimal("25"), min_stock_level=Decimal(5)
    )
    _stock(db, milk, "3", 2)  # low stock, expiring soon
    _stock(db, milk, "4", -1)  # expired
    make_product(db, "Paneer")  # out of stock
    return rice, milk


def test_admin_sees_everything(client: TestClient, seeded_db: Session) -> None:
    _shop(seeded_db)
    create_seller(seeded_db)
    data = client.get(URL, headers=admin_headers(client)).json()["data"]

    assert (data["products_total"], data["products_active"], data["sellers_total"]) == (3, 3, 1)
    assert data["categories_total"] == 13  # 10 seeded + 3 made by the helpers
    assert data["stock"] == {"total_quantity": "17.000", "low_stock": 1, "out_of_stock": 1}
    assert data["expiry"] == {"expired_batches": 1, "expiring_batches": 1, "expiring_within_days": 7}
    # cost: 10×40 + 3×20 + 4×20 (expired still costs money until written off); selling: sellable only (10×50 + 3×25)
    assert data["value"] == {"purchase_cost": "540.00", "selling_value": "575.00"}
    assert len(data["movements"]) == 7 and data["movements"][-1]["day"] == store_today().isoformat()
    assert sum(len(c) for c in data["stock_by_category"]) > 0
    assert [p["name"] for p in data["recent_products"]][:1] == ["Paneer"]


def test_movement_chart_counts_today(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db)
    headers = admin_headers(client)
    body = {
        "product_id": product.id,
        "quantity": "12",
        "expiry_date": store_today().replace(year=store_today().year + 1).isoformat(),
    }
    client.post("/api/v1/inventory/stock-in", json=body, headers=headers)
    client.post(
        "/api/v1/inventory/stock-out",
        json={"product_id": product.id, "quantity": "5", "reason": "sold_manually"},
        headers=headers,
    )
    response = client.get(URL, params={"days": 30}, headers=headers)
    assert response.status_code == 200, response.text
    today = response.json()["data"]["movements"][-1]
    assert today == {"day": store_today().isoformat(), "stock_in": "12.000", "stock_out": "5.000"}


def test_blocks_follow_permissions(client: TestClient, seeded_db: Session) -> None:
    _shop(seeded_db)
    basic = seller_headers(client, create_seller(seeded_db, [Permission.DASHBOARD_VIEW]))
    data = client.get(URL, headers=basic).json()["data"]
    assert set(data) == {"products_total", "products_active", "categories_total"}

    perms = [
        Permission.DASHBOARD_VIEW,
        Permission.PRODUCTS_VIEW,
        Permission.STOCK_VIEW,
        Permission.PRICING_VIEW_SELLING,
    ]
    data = client.get(URL, headers=seller_headers(client, create_seller(seeded_db, perms))).json()["data"]
    assert {"stock", "movements", "recent_products", "value"} <= set(data)
    assert data["value"] == {"selling_value": "575.00"}  # no purchase cost
    assert "sellers_total" not in data and "expiry" not in data
    assert "purchase_price" not in data["recent_products"][0]

    assert client.get(URL, headers=seller_headers(client, create_seller(seeded_db))).status_code == 403


def test_days_parameter_is_limited(client: TestClient) -> None:
    assert client.get(URL, params={"days": 9}, headers=admin_headers(client)).status_code == 422
