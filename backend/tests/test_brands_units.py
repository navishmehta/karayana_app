from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.enums.permission import Permission
from tests.helpers import admin_headers, create_seller, make_brand, make_product, seller_headers


def test_brand_autocomplete_and_who_can_create(client: TestClient, seeded_db: Session) -> None:
    make_brand(seeded_db, "Amul")
    viewer = seller_headers(client, create_seller(seeded_db, [Permission.PRODUCTS_VIEW]))
    editor = seller_headers(client, create_seller(seeded_db, [Permission.PRODUCTS_VIEW, Permission.PRODUCTS_UPDATE]))

    assert [
        b["name"] for b in client.get("/api/v1/brands", params={"search": "am"}, headers=viewer).json()["data"]
    ] == ["Amul"]
    assert client.post("/api/v1/brands", json={"name": "Mother Dairy"}, headers=viewer).status_code == 403
    assert client.post("/api/v1/brands", json={"name": "Mother Dairy"}, headers=editor).status_code == 201
    assert client.post("/api/v1/brands", json={"name": "amul"}, headers=editor).status_code == 422


def test_brand_in_use_cannot_be_deleted(client: TestClient, seeded_db: Session) -> None:
    brand = make_brand(seeded_db, "Parle")
    make_product(seeded_db, brand_id=brand.id)
    response = client.delete(f"/api/v1/admin/brands/{brand.id}", headers=admin_headers(client))
    assert response.status_code == 409
    assert response.json()["code"] == "IN_USE"


def test_units_are_admin_managed(client: TestClient, seeded_db: Session) -> None:
    headers = admin_headers(client)
    product = make_product(seeded_db)

    assert len(client.get("/api/v1/units", params={"active_only": True}, headers=headers).json()["data"]) == 9
    tray = client.post(
        "/api/v1/admin/units", json={"name": "Tray", "short_name": "tray", "allows_decimal": False}, headers=headers
    )
    assert tray.status_code == 201
    assert client.delete(f"/api/v1/admin/units/{tray.json()['data']['id']}", headers=headers).status_code == 204
    in_use = client.delete(f"/api/v1/admin/units/{product.unit_id}", headers=headers)
    assert in_use.status_code == 409

    seller = seller_headers(client, create_seller(seeded_db, [p for p in Permission.grantable()]))
    body = {"name": "X", "short_name": "x", "allows_decimal": True}
    assert client.post("/api/v1/admin/units", json=body, headers=seller).status_code == 403
