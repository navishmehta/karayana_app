from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.enums.activity import ActivityAction
from app.enums.permission import Permission
from app.models import ActivityLog, Product, Store
from tests.helpers import (
    admin_headers,
    create_seller,
    make_brand,
    make_category,
    make_product,
    seller_headers,
    unit_id,
)

URL = "/api/v1/products"
PRIVATE = {"purchase_price", "profit", "internal_notes"}
SELLING = {"selling_price", "mrp", "offer_price", "effective_price", "discount_percent", "on_offer"}
STOCK = {"current_stock", "sellable_stock", "stock_status", "min_stock_level", "opening_stock"}


def _payload(db: Session, **overrides) -> dict:
    return {
        "name": "Amul Butter 500g",
        "category_id": make_category(db, "Dairy Fresh").id,
        "unit_id": unit_id(db),
        "selling_price": "285",
        "mrp": "290",
        "purchase_price": "250",
    } | overrides


def _logged(db: Session, action: ActivityAction) -> int:
    return db.scalar(select(func.count(ActivityLog.id)).where(ActivityLog.action == action.value))


def test_admin_creates_product_with_auto_sku_and_profit(client: TestClient, seeded_db: Session) -> None:
    response = client.post(URL, json=_payload(seeded_db), headers=admin_headers(client))
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["slug"] == "amul-butter-500g"
    assert data["sku"] == f"SK-{data['id']:06d}"
    assert data["selling_price"] == "285.00"
    assert data["profit"] == {
        "price_used": "285.00",
        "purchase_price": "250.00",
        "amount": "35.00",
        "markup_percent": "14.00",
        "margin_percent": "12.28",
    }
    assert data["current_stock"] == "0.000"
    assert data["stock_status"] == "out_of_stock"
    assert _logged(seeded_db, ActivityAction.PRODUCT_CREATED) == 1


def test_only_admin_can_add_products(client: TestClient, seeded_db: Session) -> None:
    seller = create_seller(seeded_db, [p for p in Permission.grantable()])  # every grantable permission
    response = client.post(URL, json=_payload(seeded_db), headers=seller_headers(client, seller))
    assert response.status_code == 403


def test_stock_cannot_be_set_through_product_api(client: TestClient, seeded_db: Session) -> None:
    response = client.post(URL, json=_payload(seeded_db, current_stock="500"), headers=admin_headers(client))
    assert response.status_code == 422  # unknown field rejected


def test_price_rules(client: TestClient, seeded_db: Session) -> None:
    headers = admin_headers(client)

    def errors(**overrides) -> dict:
        return client.post(URL, json=_payload(seeded_db, **overrides), headers=headers).json()["errors"]

    assert errors(selling_price="300") == {"selling_price": ["Selling price cannot be more than the MRP."]}
    assert "offer_price" in errors(offer_price="285")
    assert "offer_ends_at" in errors(offer_price="280", offer_starts_at="2026-12-10", offer_ends_at="2026-12-01")
    assert "selling_price" in errors(selling_price="10.555")
    assert errors(min_stock_level="2.5") == {"min_stock_level": ["Use a whole number for items sold in pcs."]}


def test_decimal_stock_levels_allowed_for_kg(client: TestClient, seeded_db: Session) -> None:
    body = _payload(seeded_db, unit_id=unit_id(seeded_db, "kg"), min_stock_level="2.5")
    assert client.post(URL, json=body, headers=admin_headers(client)).status_code == 201


def test_update_compares_with_stored_values(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db)  # selling 50, mrp 55
    response = client.patch(f"{URL}/{product.id}", json={"mrp": "45"}, headers=admin_headers(client))
    assert response.json()["errors"] == {"selling_price": ["Selling price cannot be more than the MRP."]}


def test_price_changes_logged_separately_and_slug_kept(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db, name="Old Name")
    slug = product.slug
    body = {"selling_price": "52", "name": "New Name"}
    data = client.patch(f"{URL}/{product.id}", json=body, headers=admin_headers(client)).json()["data"]
    assert data["slug"] == slug
    assert _logged(seeded_db, ActivityAction.PRODUCT_PRICE_CHANGED) == 1
    assert _logged(seeded_db, ActivityAction.PRODUCT_UPDATED) == 1


def test_hidden_fields_are_absent_not_null(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db, internal_notes="supplier gives 5% extra")
    headers = seller_headers(client, create_seller(seeded_db, [Permission.PRODUCTS_VIEW]))

    data = client.get(f"{URL}/{product.id}", headers=headers).json()["data"]
    assert not (PRIVATE | SELLING | STOCK) & data.keys()

    listed = client.get(URL, headers=headers).json()["data"][0]
    assert not (PRIVATE | SELLING | STOCK) & listed.keys()


def test_field_groups_follow_permissions(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db)
    perms = [Permission.PRODUCTS_VIEW, Permission.PRICING_VIEW_SELLING, Permission.STOCK_VIEW]
    data = client.get(f"{URL}/{product.id}", headers=seller_headers(client, create_seller(seeded_db, perms))).json()

    assert data["data"].keys() >= SELLING and data["data"].keys() >= STOCK
    assert not PRIVATE & data["data"].keys()


def test_seller_edit_rules(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db)
    editor = seller_headers(client, create_seller(seeded_db, [Permission.PRODUCTS_VIEW, Permission.PRODUCTS_UPDATE]))

    blocked = client.patch(f"{URL}/{product.id}", json={"selling_price": "1", "purchase_price": "1"}, headers=editor)
    assert blocked.json()["errors"] == {
        "purchase_price": ["You do not have permission to set Purchase price."],
        "selling_price": ["You do not have permission to set Selling price."],
    }
    ok = client.patch(f"{URL}/{product.id}", json={"name": "Renamed", "is_active": False}, headers=editor)
    assert ok.status_code == 200

    pricer_perms = [
        Permission.PRODUCTS_VIEW,
        Permission.PRODUCTS_UPDATE,
        Permission.PRICING_VIEW_SELLING,
        Permission.PRICING_UPDATE_SELLING,
    ]
    pricer = seller_headers(client, create_seller(seeded_db, pricer_perms))
    assert (
        client.patch(f"{URL}/{product.id}", json={"selling_price": "45"}, headers=pricer).json()["data"][
            "selling_price"
        ]
        == "45.00"
    )


def test_search_matches_name_brand_category_sku_barcode(client: TestClient, seeded_db: Session) -> None:
    make_product(seeded_db, "Bhujia", brand_id=make_brand(seeded_db, "Haldiram").id)
    make_product(
        seeded_db, "Milk", category_id=make_category(seeded_db, "Fresh Dairy").id, barcode="8901234567890", sku="MLK-1"
    )
    make_product(seeded_db, "50% Off Soap")
    headers = admin_headers(client)

    def names(term: str) -> list[str]:
        return [p["name"] for p in client.get(URL, params={"search": term}, headers=headers).json()["data"]]

    assert names("haldi") == ["Bhujia"]
    assert names("fresh dairy") == ["Milk"]
    assert names("89012") == ["Milk"]
    assert names("MLK") == ["Milk"]
    assert names("%") == ["50% Off Soap"]  # literal %, not a wildcard


def test_filters_and_sorting(client: TestClient, seeded_db: Session) -> None:
    category = make_category(seeded_db)
    make_product(seeded_db, "A", category_id=category.id, selling_price=30, mrp=None, is_active=False)
    make_product(seeded_db, "B", category_id=category.id, selling_price=10, mrp=None)
    make_product(seeded_db, "C", category_id=category.id, selling_price=20, mrp=None, is_visible_to_customers=False)
    headers = admin_headers(client)

    def names(**params) -> list[str]:
        params["category_id"] = category.id
        return [p["name"] for p in client.get(URL, params=params, headers=headers).json()["data"]]

    assert names(sort="price_asc") == ["B", "C", "A"]
    assert names(sort="name_desc") == ["C", "B", "A"]
    assert names(min_price=15, max_price=25) == ["C"]
    assert names(is_active=False) == ["A"]
    assert names(is_visible_to_customers=False) == ["C"]
    assert names(stock_status="out_of_stock") == ["A", "B", "C"]


def test_filtering_or_sorting_by_hidden_values_is_forbidden(client: TestClient, seeded_db: Session) -> None:
    headers = seller_headers(client, create_seller(seeded_db, [Permission.PRODUCTS_VIEW]))
    assert client.get(URL, headers=headers).status_code == 200
    for params in ({"sort": "price_desc"}, {"min_price": 10}, {"stock_status": "low_stock"}, {"sort": "stock_asc"}):
        assert client.get(URL, params=params, headers=headers).status_code == 403, params


def test_lookup_by_barcode_or_sku(client: TestClient, seeded_db: Session) -> None:
    make_product(seeded_db, barcode="8900000000001", sku="ABC-1")
    headers = admin_headers(client)
    assert (
        client.get(f"{URL}/lookup", params={"barcode": "8900000000001"}, headers=headers).json()["data"]["sku"]
        == "ABC-1"
    )
    assert client.get(f"{URL}/lookup", params={"sku": "ABC-1"}, headers=headers).status_code == 200
    assert client.get(f"{URL}/lookup", params={"barcode": "000"}, headers=headers).status_code == 404
    assert client.get(f"{URL}/lookup", headers=headers).status_code == 422


def test_barcode_and_sku_must_be_unique(client: TestClient, seeded_db: Session) -> None:
    make_product(seeded_db, barcode="111", sku="DUP")
    errors = client.post(URL, json=_payload(seeded_db, barcode="111", sku="DUP"), headers=admin_headers(client)).json()
    assert set(errors["errors"]) == {"barcode", "sku"}


def test_soft_delete_and_admin_restore(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db)
    headers = admin_headers(client)
    assert client.delete(f"{URL}/{product.id}", headers=headers).status_code == 204
    assert client.get(f"{URL}/{product.id}", headers=headers).status_code == 404
    assert client.post(f"/api/v1/admin/products/{product.id}/restore", headers=headers).status_code == 200
    assert client.get(f"{URL}/{product.id}", headers=headers).status_code == 200


def test_seller_delete_needs_permission_and_cannot_restore(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db)
    viewer = seller_headers(client, create_seller(seeded_db, [Permission.PRODUCTS_VIEW]))
    deleter = seller_headers(client, create_seller(seeded_db, [Permission.PRODUCTS_VIEW, Permission.PRODUCTS_DELETE]))

    assert client.delete(f"{URL}/{product.id}", headers=viewer).status_code == 403
    assert client.delete(f"{URL}/{product.id}", headers=deleter).status_code == 204
    assert client.post(f"/api/v1/admin/products/{product.id}/restore", headers=deleter).status_code == 403


def test_other_stores_products_are_invisible(client: TestClient, seeded_db: Session) -> None:
    other = Store(name="Other", slug="other", timezone="Asia/Kolkata", currency="INR")
    seeded_db.add(other)
    seeded_db.commit()
    foreign_category = make_category(seeded_db, store_id=other.id)
    foreign = make_product(seeded_db, store_id=other.id, category_id=foreign_category.id)
    headers = admin_headers(client)

    assert client.get(f"{URL}/{foreign.id}", headers=headers).status_code == 404
    assert foreign.id not in [p["id"] for p in client.get(URL, headers=headers).json()["data"]]
    body = _payload(seeded_db, category_id=foreign_category.id)
    assert client.post(URL, json=body, headers=headers).json()["errors"] == {
        "category_id": ["The selected item does not exist."]
    }
    assert seeded_db.scalar(select(func.count(Product.id)).where(Product.store_id == other.id)) == 1
