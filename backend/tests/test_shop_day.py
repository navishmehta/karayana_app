"""One full day in the shop, end to end through the API: every module working together."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core import clock
from app.core.clock import store_today
from app.services.inventory.expiry_rules import bucket_for
from tests.helpers import admin_headers, image_bytes, login, unit_id
from tests.test_inventory import _batch

API = "/api/v1"


def _days(n: int) -> str:
    return (store_today() + timedelta(days=n)).isoformat()


def test_a_full_shop_day(client: TestClient, seeded_db: Session) -> None:
    admin = admin_headers(client)

    # 1. Morning: the admin sets up the shop.
    client.patch(
        f"{API}/admin/settings", json={"store_name": "Ramesh Karayana Store", "phone": "9876500000"}, headers=admin
    )
    category = client.post(f"{API}/categories", json={"name": "Daily Needs", "name_translations": {"pa": "ਰੋਜ਼ਾਨਾ"}},
                           headers=admin).json()["data"]  # fmt: skip
    milk = client.post(f"{API}/products", headers=admin, json={
        "name": "Fresh Milk 1L", "category_id": category["id"], "unit_id": unit_id(seeded_db),
        "selling_price": "68", "mrp": "70", "purchase_price": "60", "min_stock_level": "5",
        "offer_price": "65", "offer_starts_at": store_today().isoformat(), "offer_ends_at": _days(2),
    }).json()["data"]  # fmt: skip
    rice = client.post(f"{API}/products", headers=admin, json={
        "name": "Basmati Rice (loose)", "category_id": category["id"], "unit_id": unit_id(seeded_db, "kg"),
        "selling_price": "120", "purchase_price": "95", "min_stock_level": "2.5", "track_expiry": False,
    }).json()["data"]  # fmt: skip
    files = {"image": ("milk.jpg", image_bytes(800, 800), "image/jpeg")}
    assert client.post(f"{API}/products/{milk['id']}/images", files=files, headers=admin).status_code == 201

    seller = client.post(f"{API}/admin/sellers", headers=admin, json={
        "name": "Raju", "email": "raju@kirana.test", "password": "Counter123", "password_confirmation": "Counter123",
        "permissions": ["dashboard.view", "products.view", "pricing.view_selling", "stock.view", "stock.update"],
    }).json()["data"]  # fmt: skip
    raju = {"Authorization": f"Bearer {login(client, seller['email'], 'Counter123')['access_token']}"}

    # 2. Stock arrives: two milk batches with different expiry dates, and loose rice by the kg.
    for qty, expiry in (("6", 1), ("10", 5)):
        body = {"product_id": milk["id"], "quantity": qty, "expiry_date": _days(expiry)}
        assert client.post(f"{API}/inventory/stock-in", json=body, headers=raju).status_code == 201
    client.post(f"{API}/inventory/stock-in", json={"product_id": rice["id"], "quantity": "25.5"}, headers=raju)

    # 3. The counter sells: FEFO takes the older batch first; 2.75 kg of loose rice.
    sell = {"product_id": milk["id"], "quantity": "8", "reason": "sold_manually"}
    sale = client.post(f"{API}/inventory/stock-out", json=sell, headers=raju).json()["data"]
    assert [(line["batch"]["expiry_date"], line["quantity_change"]) for line in sale["lines"]] == [
        (_days(1), "-6.000"),
        (_days(5), "-2.000"),
    ]
    rice_sale = client.post(f"{API}/inventory/stock-out", headers=raju,
                            json={"product_id": rice["id"], "quantity": "2.75", "reason": "sold_manually"})  # fmt: skip
    assert rice_sale.json()["data"]["products"][0]["current_stock"] == "22.750"

    # 4. More milk sold -> low stock alert reaches the admin, once.
    client.post(f"{API}/inventory/stock-out", headers=raju,
                json={"product_id": milk["id"], "quantity": "4", "reason": "sold_manually"})  # fmt: skip
    notes = client.get(f"{API}/notifications", headers=admin).json()["data"]
    assert [n["title"] for n in notes] == ["Low stock: Fresh Milk 1L"]

    # 5. A customer browses without logging in: offer price, never the cost.
    product = client.get(f"{API}/public/products/{milk['slug']}").json()["data"]
    assert (product["price"], product["on_offer"], product["availability"]) == ("65.00", True, "low_stock")
    assert "purchase_price" not in product and "60.00" not in str(product)
    assert client.get(f"{API}/public/categories").json()["data"][0]["name_translations"] == {"pa": "ਰੋਜ਼ਾਨਾ"}

    # 6. The seller can't see costs or do admin-only things.
    seller_view = client.get(f"{API}/products/{milk['id']}", headers=raju).json()["data"]
    assert "purchase_price" not in seller_view and seller_view["selling_price"] == "68.00"
    assert client.get(f"{API}/admin/sellers", headers=raju).status_code == 403
    assert client.post(f"{API}/products", json={}, headers=raju).status_code == 403
    assert client.get(f"{API}/reports", headers=raju).status_code == 403

    # 7. Evening: an old batch found expired is written off; the admin checks the books.
    expired = _batch(seeded_db, milk["id"], "2", -1)
    write_off = client.post(f"{API}/inventory/expired-writeoff", json={"batch_ids": [expired.id]}, headers=admin)
    assert write_off.status_code == 201
    valuation = client.get(f"{API}/reports/valuation", params={"category_id": category["id"]}, headers=admin)
    totals = valuation.json()["data"]["totals"]
    # milk: 4 left × cost 60 = 240; rice: 22.75 kg × 95 = 2161.25  -> 2401.25 at cost
    assert totals["cost_value"] == "2401.25"
    history = client.get(f"{API}/inventory/transactions", params={"product_id": milk["id"]}, headers=admin).json()
    # opening + stock in, two FEFO sale lines, one more sale, the write-off
    # (the test inserted the expired batch directly, so it has no "received" line)
    assert history["meta"]["total"] == 6
    dashboard = client.get(f"{API}/dashboard", headers=admin).json()["data"]
    assert dashboard["stock"]["low_stock"] >= 1


def test_today_follows_india_time_at_midnight(monkeypatch) -> None:
    """00:30 IST on the 19th is still 19:00 UTC on the 18th — 'today' must already be the 19th."""
    utc_moment = datetime(2026, 11, 18, 19, 0, tzinfo=UTC)

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):  # noqa: ANN001
            return utc_moment.astimezone(tz) if tz else utc_moment.replace(tzinfo=None)

    monkeypatch.setattr(clock, "datetime", FrozenDatetime)
    assert clock.store_today() == date(2026, 11, 19)
    # A batch expiring on the 18th is already expired at 00:30 IST on the 19th.
    assert bucket_for(date(2026, 11, 18), clock.store_today(), [7, 15, 30]).value == "expired"
    assert bucket_for(date(2026, 11, 19), clock.store_today(), [7, 15, 30]).value == "critical"


def test_decimal_money_has_no_float_drift(client: TestClient, seeded_db: Session) -> None:
    """₹0.10 × 3 must be exactly ₹0.30 in valuation (floats would give 0.30000000000000004)."""
    from tests.helpers import make_category, make_product

    category = make_category(seeded_db, "Pennies")
    product = make_product(seeded_db, "Toffee", category_id=category.id, purchase_price=Decimal("0.10"),
                           selling_price=Decimal("0.50"), mrp=None)  # fmt: skip
    _batch(seeded_db, product.id, "3", 100)
    from app.services.inventory.stock_cache import refresh_product_stock

    refresh_product_stock(seeded_db, product)
    seeded_db.commit()
    report = client.get("/api/v1/reports/valuation", params={"category_id": category.id}, headers=admin_headers(client))
    assert report.json()["data"]["totals"]["cost_value"] == "0.30"
