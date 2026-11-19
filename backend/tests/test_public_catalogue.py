from datetime import timedelta
from decimal import Decimal
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import store_today
from app.core.config import get_settings
from app.enums.permission import Permission
from app.enums.setting_key import SettingKey
from app.models import AppSetting, Category
from app.services.inventory.stock_cache import refresh_product_stock
from tests.helpers import admin_headers, create_seller, make_brand, make_category, make_product, seller_headers
from tests.test_inventory import _batch

P = "/api/v1/public"
TODAY = store_today()

# Anything internal. None of these keys may appear anywhere in any public response.
FORBIDDEN_KEYS = {
    "purchase_price", "profit", "internal_notes", "cost", "unit_cost", "cost_value", "cost_impact",
    "current_stock", "sellable_stock", "opening_stock", "min_stock_level", "max_stock_level", "stock_status",
    "sku", "barcode", "id", "created_by", "updated_by", "deleted_at", "is_active", "is_visible_to_customers",
    "tax_rate", "hsn_code", "markup_percent", "margin_percent", "batches", "quantity_remaining",
}  # fmt: skip


def _keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_keys(v) for v in value.values()))
    if isinstance(value, list):
        return set().union(*(_keys(v) for v in value)) if value else set()
    return set()


def _set(db: Session, key: SettingKey, value: Any) -> None:
    db.scalar(select(AppSetting).where(AppSetting.key == key.value)).value = value
    db.commit()


def _stock(db: Session, product, qty: str = "20", expiry_in_days: int | None = 30) -> None:
    _batch(db, product.id, qty, expiry_in_days)
    refresh_product_stock(db, product)
    db.commit()


def _shop(db: Session) -> dict:
    dairy = db.scalar(select(Category).where(Category.slug == "dairy"))
    hidden_category = make_category(db, "Back Room", is_active=False)
    amul = make_brand(db, "Amul")
    butter = make_product(
        db, "Amul Butter", category_id=dairy.id, brand_id=amul.id, barcode="890100", sku="BUT-1",
        internal_notes="secret margin", is_featured=True, show_expiry_to_customers=True,
        selling_price=Decimal("285"), mrp=Decimal("290"), purchase_price=Decimal("250"),
    )  # fmt: skip
    _stock(db, butter, expiry_in_days=12)
    milk = make_product(
        db, "Milk", category_id=dairy.id, selling_price=Decimal("68"), mrp=Decimal("70"),
        offer_price=Decimal("60"), offer_starts_at=TODAY, offer_ends_at=TODAY + timedelta(days=3),
    )  # fmt: skip
    _stock(db, milk)
    paneer = make_product(db, "Paneer", category_id=dairy.id, selling_price=Decimal("90"), mrp=None)  # no stock
    return {
        "butter": butter,
        "milk": milk,
        "paneer": paneer,
        "hidden_product": make_product(db, "Hidden", category_id=dairy.id, is_visible_to_customers=False),
        "inactive_product": make_product(db, "Inactive", category_id=dairy.id, is_active=False),
        "in_hidden_category": make_product(db, "Back Item", category_id=hidden_category.id),
        "deleted": make_product(db, "Gone", category_id=dairy.id, deleted_at=TODAY),
    }


def _names(client: TestClient, **params) -> list[str]:
    return [p["name"] for p in client.get(f"{P}/products", params=params).json()["data"]]


def test_no_login_needed_and_only_visible_products_shown(client: TestClient, seeded_db: Session) -> None:
    _shop(seeded_db)
    response = client.get(f"{P}/products")
    assert response.status_code == 200
    assert [p["name"] for p in response.json()["data"]] == ["Amul Butter", "Milk", "Paneer"]


def test_public_responses_never_contain_private_fields(client: TestClient, seeded_db: Session) -> None:
    shop = _shop(seeded_db)
    urls = [
        f"{P}/store",
        f"{P}/categories",
        f"{P}/categories/dairy",
        f"{P}/products",
        f"{P}/products?search=amul&sort=price_desc",
        f"{P}/products/featured",
        f"{P}/products/new",
        f"{P}/products/offers",
        f"{P}/products/{shop['butter'].slug}",
    ]
    for url in urls:
        response = client.get(url)
        assert response.status_code == 200, url
        leaked = _keys(response.json()) & FORBIDDEN_KEYS
        assert not leaked, f"{url} leaked {leaked}"
        assert "secret margin" not in response.text and "250.00" not in response.text


def test_product_shape(client: TestClient, seeded_db: Session) -> None:
    shop = _shop(seeded_db)
    butter = client.get(f"{P}/products/{shop['butter'].slug}").json()["data"]
    assert butter == {
        "slug": shop["butter"].slug,
        "name": "Amul Butter",
        "description": None,
        "brand": "Amul",
        "category": {"slug": "dairy", "name": "Dairy", "name_translations": {"pa": "ਡੇਅਰੀ"}},
        "unit": "pcs",
        "price": "285.00",
        "selling_price": "285.00",
        "mrp": "290.00",
        "discount_percent": "1.72",
        "on_offer": False,
        "offer_ends_at": None,
        "availability": "in_stock",
        "expiry_date": (TODAY + timedelta(days=12)).isoformat(),
        "is_featured": True,
        "images": [],
    }


def test_offers_change_price_and_can_be_switched_off(client: TestClient, seeded_db: Session) -> None:
    shop = _shop(seeded_db)
    milk = client.get(f"{P}/products/{shop['milk'].slug}").json()["data"]
    assert (milk["price"], milk["on_offer"], milk["discount_percent"]) == ("60.00", True, "14.29")
    assert [p["name"] for p in client.get(f"{P}/products/offers").json()["data"]] == ["Milk"]
    # Sorted by today's price; out-of-stock Paneer (₹90) still comes after the things customers can buy.
    assert _names(client, sort="price_asc") == ["Milk", "Amul Butter", "Paneer"]

    _set(seeded_db, SettingKey.OFFERS_ENABLED, False)
    milk = client.get(f"{P}/products/{shop['milk'].slug}").json()["data"]
    assert (milk["price"], milk["on_offer"]) == ("68.00", False)
    assert client.get(f"{P}/products/offers").json()["data"] == []


def test_out_of_stock_label_or_hidden(client: TestClient, seeded_db: Session) -> None:
    shop = _shop(seeded_db)
    assert client.get(f"{P}/products/{shop['paneer'].slug}").json()["data"]["availability"] == "out_of_stock"
    assert "Paneer" not in _names(client, in_stock=True)
    for sort in ("name_asc", "name_desc", "price_asc", "price_desc", "newest"):
        assert _names(client, sort=sort)[-1] == "Paneer", sort  # sold-out items always come last

    _set(seeded_db, SettingKey.SHOW_OUT_OF_STOCK, False)
    assert "Paneer" not in _names(client)
    assert client.get(f"{P}/products/{shop['paneer'].slug}").status_code == 404


def test_hidden_inactive_deleted_and_hidden_category_return_404(client: TestClient, seeded_db: Session) -> None:
    shop = _shop(seeded_db)
    for key in ("hidden_product", "inactive_product", "in_hidden_category", "deleted"):
        assert client.get(f"{P}/products/{shop[key].slug}").status_code == 404, key


def test_search_filters_and_internal_codes_not_searchable(client: TestClient, seeded_db: Session) -> None:
    _shop(seeded_db)
    assert _names(client, search="amul") == ["Amul Butter"]  # brand
    assert _names(client, search="dairy") == ["Amul Butter", "Milk", "Paneer"]  # category
    assert _names(client, search="890100") == []  # barcode is internal
    assert _names(client, search="BUT-1") == []  # SKU is internal
    assert _names(client, category="dairy", min_price=61, max_price=100) == ["Paneer"]
    assert _names(client, featured=True) == ["Amul Butter"]


def test_categories_list_only_those_with_visible_products(client: TestClient, seeded_db: Session) -> None:
    _shop(seeded_db)
    categories = client.get(f"{P}/categories").json()["data"]
    assert [(c["slug"], c["products_count"]) for c in categories] == [("dairy", 3)]
    assert client.get(f"{P}/categories/grocery").status_code == 404  # no products yet
    assert client.get(f"{P}/categories/back-room").status_code == 404


def test_store_info_follows_admin_settings(client: TestClient) -> None:
    assert client.get(f"{P}/store").json()["data"]["name"] == "Ramesh Karayana Store"

    body = {"store_name": "Ramesh General Store", "phone": "9876543210", "hours": "8 AM - 10 PM"}
    assert client.patch("/api/v1/admin/settings", json=body, headers=admin_headers(client)).status_code == 200

    store = client.get(f"{P}/store").json()["data"]
    assert (store["name"], store["phone"], store["hours"], store["currency"]) == (
        "Ramesh General Store",
        "9876543210",
        "8 AM - 10 PM",
        "INR",
    )


def test_public_routes_are_cacheable_and_rate_limited(client: TestClient) -> None:
    response = client.get(f"{P}/store")
    assert response.headers["cache-control"] == "public, max-age=60"
    for _ in range(get_settings().rate_limit_public_per_minute - 1):
        client.get(f"{P}/store")
    blocked = client.get(f"{P}/store")
    assert blocked.status_code == 429
    assert blocked.json()["code"] == "TOO_MANY_REQUESTS"


def test_admin_settings_validation_and_access(client: TestClient, seeded_db: Session) -> None:
    headers = admin_headers(client)
    settings = client.get("/api/v1/admin/settings", headers=headers).json()["data"]
    assert settings["expiry_buckets"] == [7, 15, 30]
    assert settings["store_name"] == "Ramesh Karayana Store"

    bad = {"expiry_buckets": [30, 15, 7], "expiry_digest_time": "25:00", "phone": "123"}
    errors = client.patch("/api/v1/admin/settings", json=bad, headers=headers).json()["errors"]
    assert set(errors) == {"expiry_buckets", "expiry_digest_time", "phone"}

    seller = seller_headers(client, create_seller(seeded_db, [p for p in Permission.grantable()]))
    assert client.get("/api/v1/admin/settings", headers=seller).status_code == 403
    assert client.patch("/api/v1/admin/settings", json={"store_name": "x"}, headers=seller).status_code == 403


def test_store_logo_upload(client: TestClient) -> None:
    from tests.helpers import image_bytes

    files = {"image": ("logo.png", image_bytes(800, 800, "PNG"), "image/png")}
    data = client.post("/api/v1/admin/settings/logo", files=files, headers=admin_headers(client)).json()["data"]
    assert data["logo_url"].endswith(".webp")
    assert client.get(f"{P}/store").json()["data"]["logo_url"] == data["logo_url"]
