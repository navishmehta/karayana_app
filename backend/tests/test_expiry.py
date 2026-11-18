from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.enums.permission import Permission
from tests.helpers import admin_headers, create_seller, make_product, seller_headers
from tests.test_inventory import TODAY, _batch


def _setup(db: Session):
    product = make_product(db, name="Milk")
    other = make_product(db, name="Bread")
    _batch(db, product.id, "2", -1)  # expired
    _batch(db, product.id, "3", 0)  # expires today: still within 7
    _batch(db, product.id, "4", 10)  # within 15
    _batch(db, other.id, "5", 25)  # within 30
    _batch(db, other.id, "6", 90)  # safe
    _batch(db, other.id, "9", None)  # no expiry
    return product, other


def test_summary_counts_cumulative_windows(client: TestClient, seeded_db: Session) -> None:
    _setup(seeded_db)
    data = client.get("/api/v1/expiry/summary", headers=admin_headers(client)).json()["data"]
    assert data["as_of"] == TODAY.isoformat()
    by_key = {b["key"]: (b["batches"], b["quantity"]) for b in data["buckets"]}
    assert by_key == {
        "expired": (1, "2.000"),
        "within_7": (1, "3.000"),
        "within_15": (2, "7.000"),
        "within_30": (3, "12.000"),
    }
    assert "cost_value" in data["buckets"][0]


def test_batch_list_filters_and_bands(client: TestClient, seeded_db: Session) -> None:
    product, _ = _setup(seeded_db)
    headers = admin_headers(client)

    def rows(**params) -> list:
        return client.get("/api/v1/expiry/batches", params=params, headers=headers).json()["data"]

    assert [(r["quantity_remaining"], r["bucket"]) for r in rows(status="all")] == [
        ("2.000", "expired"),
        ("3.000", "critical"),
        ("4.000", "warning"),
        ("5.000", "notice"),
        ("6.000", "safe"),
    ]
    assert [r["days_to_expiry"] for r in rows(status="expired")] == [-1]
    assert len(rows(within_days=15)) == 2
    assert {r["product"]["name"] for r in rows(status="all", product_id=product.id)} == {"Milk"}
    first = rows(within_days=7)[0]
    assert first["sku"] and first["category"]["name"] and first["unit"] == "pcs"


def test_product_list_expiry_filter_and_sort(client: TestClient, seeded_db: Session) -> None:
    product, other = _setup(seeded_db)
    from app.services.inventory.stock_cache import refresh_product_stock

    for p in (product, other):
        refresh_product_stock(seeded_db, p)
    seeded_db.commit()
    headers = admin_headers(client)

    expired = client.get("/api/v1/products", params={"expiry": "expired"}, headers=headers).json()["data"]
    assert [p["name"] for p in expired] == ["Milk"]
    soon = client.get("/api/v1/products", params={"expiry": "expiring", "within_days": 20}, headers=headers).json()
    assert [p["name"] for p in soon["data"]] == ["Milk"]
    ordered = client.get("/api/v1/products", params={"sort": "expiry_asc"}, headers=headers).json()["data"]
    assert [p["name"] for p in ordered][:2] == ["Milk", "Bread"]
    assert ordered[0]["next_expiry_date"] == TODAY.isoformat()


def test_expiry_needs_permission_and_hides_costs(client: TestClient, seeded_db: Session) -> None:
    _setup(seeded_db)
    viewer = seller_headers(client, create_seller(seeded_db, [Permission.PRODUCTS_VIEW, Permission.EXPIRY_VIEW]))
    data = client.get("/api/v1/expiry/summary", headers=viewer).json()["data"]
    assert "cost_value" not in data["buckets"][0]
    batch = client.get("/api/v1/expiry/batches", params={"status": "all"}, headers=viewer).json()["data"][0]
    assert "purchase_price" not in batch

    nobody = seller_headers(client, create_seller(seeded_db, [Permission.PRODUCTS_VIEW]))
    assert client.get("/api/v1/expiry/summary", headers=nobody).status_code == 403
    assert client.get("/api/v1/products", params={"expiry": "expired"}, headers=nobody).status_code == 403


def test_expiry_limits_follow_the_setting(client: TestClient, seeded_db: Session) -> None:
    from sqlalchemy import select

    from app.enums.setting_key import SettingKey
    from app.models import AppSetting

    _setup(seeded_db)
    setting = seeded_db.scalar(select(AppSetting).where(AppSetting.key == SettingKey.EXPIRY_BUCKETS.value))
    setting.value = [5, 12, 40]
    seeded_db.commit()
    keys = [
        b["key"] for b in client.get("/api/v1/expiry/summary", headers=admin_headers(client)).json()["data"]["buckets"]
    ]
    assert keys == ["expired", "within_5", "within_12", "within_40"]
    assert Decimal(0) == Decimal("0")
