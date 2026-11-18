"""Test helpers for creating staff and logging in."""

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.enums.permission import Permission
from app.enums.role import Role
from app.models import PermissionModel, Store, User
from app.models import Role as RoleModel

ADMIN_EMAIL = "admin@kirana.test"
ADMIN_PASSWORD = "Admin12345"
SELLER_PASSWORD = "Seller123"

_counter = {"n": 0}


def create_seller(
    db: Session, permissions: list[Permission] | None = None, *, store_id: int | None = None, **values
) -> User:
    _counter["n"] += 1
    seller = User(
        store_id=store_id or db.scalar(select(Store.id)),
        role_id=db.scalar(select(RoleModel.id).where(RoleModel.name == Role.SELLER)),
        name=values.pop("name", f"Seller {_counter['n']}"),
        email=values.pop("email", f"seller{_counter['n']}@kirana.test"),
        password_hash=hash_password(values.pop("password", SELLER_PASSWORD)),
        **values,
    )
    keys = [p.value for p in permissions or []]
    seller.permissions = list(db.scalars(select(PermissionModel).where(PermissionModel.key.in_(keys)))) if keys else []
    db.add(seller)
    db.commit()
    return seller


def login(client: TestClient, email: str, password: str, device: str = "test-device") -> dict:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password, "device_name": device})
    assert response.status_code == 200, response.text
    return response.json()["data"]


def auth_headers(client: TestClient, email: str = ADMIN_EMAIL, password: str = ADMIN_PASSWORD) -> dict[str, str]:
    return {"Authorization": f"Bearer {login(client, email, password)['access_token']}"}


def admin_headers(client: TestClient) -> dict[str, str]:
    return auth_headers(client)


def seller_headers(client: TestClient, seller: User) -> dict[str, str]:
    return auth_headers(client, seller.email, SELLER_PASSWORD)
