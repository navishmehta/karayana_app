from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.enums.permission import Permission
from app.models import Category
from tests.helpers import admin_headers, create_seller, image_bytes, make_category, make_product, seller_headers

URL = "/api/v1/categories"


def _media(path: str) -> Path:
    return Path(get_settings().media_root) / path


def test_admin_creates_category_with_punjabi_name(client: TestClient) -> None:
    body = {"name": "Dry Fruits", "name_translations": {"pa": "ਸੁੱਕੇ ਮੇਵੇ"}, "description": "Almonds, cashews"}
    response = client.post(URL, json=body, headers=admin_headers(client))
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["slug"] == "dry-fruits"
    assert data["name_translations"] == {"pa": "ਸੁੱਕੇ ਮੇਵੇ"}
    assert data["products_count"] == 0
    assert data["sort_order"] == 10  # after the 10 seeded categories


def test_duplicate_name_and_unknown_language_are_rejected(client: TestClient) -> None:
    headers = admin_headers(client)
    errors = client.post(URL, json={"name": "dairy", "name_translations": {"fr": "x"}}, headers=headers).json()[
        "errors"
    ]
    assert errors == {"name_translations": ["This language is not supported."]}
    assert client.post(URL, json={"name": "DAIRY"}, headers=headers).json()["errors"]["name"] == [
        "This name is already in use."
    ]


def test_slug_is_unique_and_stable(client: TestClient) -> None:
    headers = admin_headers(client)
    first = client.post(URL, json={"name": "Frozen"}, headers=headers).json()["data"]
    assert client.delete(f"{URL}/{first['id']}", headers=headers).status_code == 204

    second = client.post(URL, json={"name": "Frozen"}, headers=headers).json()["data"]
    assert second["slug"] == "frozen-2"
    renamed = client.patch(f"{URL}/{second['id']}", json={"name": "Frozen Foods"}, headers=headers).json()["data"]
    assert renamed["slug"] == "frozen-2"


def test_list_search_filter_sort_and_counts(client: TestClient, seeded_db: Session) -> None:
    dairy = seeded_db.scalar(select(Category).where(Category.slug == "dairy"))
    make_product(seeded_db, category_id=dairy.id)
    make_product(seeded_db, category_id=dairy.id)
    seeded_db.scalar(select(Category).where(Category.slug == "bakery")).is_active = False
    seeded_db.commit()
    seller = create_seller(seeded_db, [Permission.CATEGORIES_VIEW])
    headers = seller_headers(client, seller)

    assert client.get(URL, headers=headers).json()["data"][0]["name"] == "Grocery"
    assert client.get(URL, params={"sort": "name_desc"}, headers=headers).json()["data"][0]["name"] == "Stationery"
    found = client.get(URL, params={"search": "dai"}, headers=headers).json()["data"]
    assert [(c["name"], c["products_count"]) for c in found] == [("Dairy", 2)]
    assert [c["name"] for c in client.get(URL, params={"is_active": False}, headers=headers).json()["data"]] == [
        "Bakery"
    ]


def test_category_with_products_cannot_be_deleted(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db)
    response = client.delete(f"{URL}/{product.category_id}", headers=admin_headers(client))
    assert response.status_code == 409
    assert response.json()["code"] == "CATEGORY_NOT_EMPTY"


def test_reorder(client: TestClient, seeded_db: Session) -> None:
    a, b = make_category(seeded_db), make_category(seeded_db)
    headers = admin_headers(client)
    assert client.patch(f"{URL}/reorder", json={"ids": [b.id, a.id]}, headers=headers).status_code == 204
    seeded_db.expire_all()
    assert (b.sort_order, a.sort_order) == (0, 1)
    assert client.patch(f"{URL}/reorder", json={"ids": [a.id, 999999]}, headers=headers).status_code == 422


def test_image_upload_replace_and_remove(client: TestClient, seeded_db: Session) -> None:
    category = make_category(seeded_db)
    headers = admin_headers(client)
    url = f"{URL}/{category.id}/image"

    first = client.post(url, files={"image": ("a.jpg", image_bytes(), "image/jpeg")}, headers=headers).json()["data"]
    assert first["image_url"].endswith(".webp") and first["image_thumb_url"].endswith("_thumb.webp")
    old_path = seeded_db.get(Category, category.id).image_path
    assert _media(old_path).exists()

    client.post(url, files={"image": ("b.png", image_bytes(fmt="PNG"), "image/png")}, headers=headers)
    assert not _media(old_path).exists()  # old file cleaned up

    assert client.delete(url, headers=headers).json()["data"]["image_url"] is None


def test_each_action_needs_its_own_permission(client: TestClient, seeded_db: Session) -> None:
    category = make_category(seeded_db)
    headers = seller_headers(client, create_seller(seeded_db, [Permission.CATEGORIES_VIEW]))

    assert client.get(URL, headers=headers).status_code == 200
    assert client.post(URL, json={"name": "New"}, headers=headers).status_code == 403
    assert client.patch(f"{URL}/{category.id}", json={"name": "New"}, headers=headers).status_code == 403
    assert client.delete(f"{URL}/{category.id}", headers=headers).status_code == 403
    assert client.get(URL, headers=seller_headers(client, create_seller(seeded_db))).status_code == 403
