"""Every seller permission, end to end: a seller holding just that permission (plus what it needs) gets in,
and a seller holding every OTHER grantable permission is refused. "Add products" stays admin-only."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.clock import store_today
from app.enums.permission import Permission
from tests.helpers import admin_headers, create_seller, make_category, make_product, seller_headers, unit_id
from tests.test_inventory import _batch


@dataclass
class World:
    product_id: int
    empty_category_id: int
    batch_id: int
    category_id: int


@dataclass(frozen=True)
class Case:
    permission: Permission
    method: str
    url: Callable[[World], str]
    body: Callable[[World], dict] | None = None


def _future(days: int) -> str:
    return (store_today() + timedelta(days=days)).isoformat()


CASES = [
    Case(Permission.DASHBOARD_VIEW, "get", lambda w: "/api/v1/dashboard"),
    Case(Permission.PRODUCTS_VIEW, "get", lambda w: "/api/v1/products"),
    Case(Permission.PRODUCTS_VIEW, "get", lambda w: f"/api/v1/products/{w.product_id}"),
    Case(
        Permission.PRODUCTS_UPDATE, "patch", lambda w: f"/api/v1/products/{w.product_id}", lambda w: {"name": "Renamed"}
    ),
    Case(Permission.PRODUCTS_DELETE, "delete", lambda w: f"/api/v1/products/{w.product_id}"),
    Case(Permission.CATEGORIES_VIEW, "get", lambda w: "/api/v1/categories"),
    Case(Permission.CATEGORIES_CREATE, "post", lambda w: "/api/v1/categories", lambda w: {"name": "Matrix Cat"}),
    Case(
        Permission.CATEGORIES_UPDATE,
        "patch",
        lambda w: f"/api/v1/categories/{w.category_id}",
        lambda w: {"description": "x"},
    ),
    Case(Permission.CATEGORIES_DELETE, "delete", lambda w: f"/api/v1/categories/{w.empty_category_id}"),
    Case(Permission.STOCK_VIEW, "get", lambda w: "/api/v1/inventory/transactions"),
    Case(
        Permission.STOCK_UPDATE,
        "post",
        lambda w: "/api/v1/inventory/stock-in",
        lambda w: {"product_id": w.product_id, "quantity": "2", "expiry_date": _future(60)},
    ),
    Case(Permission.EXPIRY_VIEW, "get", lambda w: "/api/v1/expiry/summary"),
    Case(
        Permission.EXPIRY_UPDATE,
        "patch",
        lambda w: f"/api/v1/batches/{w.batch_id}",
        lambda w: {"batch_number": "LOT-1"},
    ),
]


def _with_dependencies(permission: Permission) -> list[Permission]:
    return [permission, *permission.all_dependencies()]


def _everything_except(permission: Permission) -> list[Permission]:
    """All grantable permissions, minus this one and anything that depends on it."""
    return [p for p in Permission.grantable() if p != permission and permission not in p.all_dependencies()]


def _world(db: Session) -> World:
    category = make_category(db, "Matrix Home")
    product = make_product(db, "Matrix Product", category_id=category.id)
    batch = _batch(db, product.id, "5", 30)
    return World(product.id, make_category(db, "Matrix Empty").id, batch.id, category.id)


def _call(client: TestClient, case: Case, world: World, headers: dict):
    body = case.body(world) if case.body else None
    return client.request(case.method.upper(), case.url(world), json=body, headers=headers)


@pytest.mark.parametrize("case", CASES, ids=lambda c: f"{c.method}-{c.permission.value}")
def test_permission_grants_access(case: Case, client: TestClient, seeded_db: Session) -> None:
    world = _world(seeded_db)
    headers = seller_headers(client, create_seller(seeded_db, _with_dependencies(case.permission)))
    response = _call(client, case, world, headers)
    assert response.status_code not in (401, 403), response.text
    assert response.status_code < 400, response.text


@pytest.mark.parametrize("case", CASES, ids=lambda c: f"{c.method}-{c.permission.value}")
def test_missing_permission_is_refused(case: Case, client: TestClient, seeded_db: Session) -> None:
    world = _world(seeded_db)
    headers = seller_headers(client, create_seller(seeded_db, _everything_except(case.permission)))
    response = _call(client, case, world, headers)
    assert response.status_code == 403, response.text
    assert response.json()["code"] == "FORBIDDEN"


def test_every_grantable_permission_is_covered() -> None:
    covered = {c.permission for c in CASES}
    # Pricing permissions change which fields appear (tested in test_products.py), reports arrive in Phase 10.
    field_level = {Permission.PRICING_VIEW_PURCHASE, Permission.PRICING_VIEW_SELLING, Permission.PRICING_UPDATE_SELLING}
    later = {Permission.REPORTS_VIEW, Permission.REPORTS_EXPORT}
    assert set(Permission.grantable()) - field_level - later == covered


def test_add_products_is_admin_only(client: TestClient, seeded_db: Session) -> None:
    category = make_category(seeded_db, "Admin Only")
    body = {"name": "New", "category_id": category.id, "unit_id": unit_id(seeded_db), "selling_price": "10"}
    every = seller_headers(client, create_seller(seeded_db, Permission.grantable()))
    assert client.post("/api/v1/products", json=body, headers=every).status_code == 403
    assert client.post("/api/v1/products", json=body, headers=admin_headers(client)).status_code == 201
