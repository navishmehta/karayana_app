"""Test helpers for creating staff and logging in."""

from decimal import Decimal
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.enums.permission import Permission
from app.enums.role import Role
from app.models import Brand, Category, PermissionModel, Product, Store, Unit, User
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


def store_id(db: Session) -> int:
    return db.scalar(select(Store.id).order_by(Store.id))


def make_category(db: Session, name: str | None = None, **values) -> Category:
    _counter["n"] += 1
    name = name or f"Category {_counter['n']}"
    category = Category(
        store_id=values.pop("store_id", None) or store_id(db),
        name=name,
        slug=values.pop("slug", f"cat-{_counter['n']}"),
        **values,
    )
    db.add(category)
    db.commit()
    return category


def make_brand(db: Session, name: str, **values) -> Brand:
    _counter["n"] += 1
    brand = Brand(store_id=store_id(db), name=name, slug=f"brand-{_counter['n']}", **values)
    db.add(brand)
    db.commit()
    return brand


def unit_id(db: Session, short_name: str = "pcs") -> int:
    return db.scalar(select(Unit.id).where(Unit.short_name == short_name))


def make_product(db: Session, name: str | None = None, **values) -> Product:
    _counter["n"] += 1
    defaults = {
        "store_id": store_id(db),
        "category_id": values.pop("category_id", None) or make_category(db).id,
        "unit_id": unit_id(db),
        "name": name or f"Product {_counter['n']}",
        "slug": f"product-{_counter['n']}",
        "sku": f"T-{_counter['n']:06d}",
        "purchase_price": Decimal("40.00"),
        "selling_price": Decimal("50.00"),
        "mrp": Decimal("55.00"),
        "min_stock_level": Decimal("5"),
    }
    product = Product(**(defaults | values))
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def image_bytes(width: int = 1600, height: int = 1200, fmt: str = "JPEG") -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (width, height), (200, 120, 40)).save(buffer, format=fmt)
    return buffer.getvalue()
