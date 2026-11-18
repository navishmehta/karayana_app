from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.enums.activity import ActivityAction
from app.enums.permission import Permission
from app.models import ActivityLog, Store
from tests.helpers import SELLER_PASSWORD, admin_headers, create_seller, login, seller_headers

SELLERS = "/api/v1/admin/sellers"


def _new_seller(**overrides) -> dict:
    return {
        "name": "Raju",
        "email": "raju@kirana.test",
        "phone": "9876543210",
        "password": "Seller123",
        "password_confirmation": "Seller123",
        "permissions": ["products.view", "stock.view"],
    } | overrides


def test_admin_creates_seller_who_can_log_in(client: TestClient, seeded_db: Session) -> None:
    response = client.post(SELLERS, json=_new_seller(), headers=admin_headers(client))

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["permissions"] == ["products.view", "stock.view"]
    assert data["is_active"] is True
    assert login(client, "raju@kirana.test", "Seller123")["user"]["role"] == "seller"
    assert seeded_db.scalar(
        select(func.count(ActivityLog.id)).where(ActivityLog.action == ActivityAction.SELLER_CREATED.value)
    )


def test_add_products_cannot_be_given_to_sellers(client: TestClient) -> None:
    payload = _new_seller(permissions=["products.view", "products.create"])
    response = client.post(SELLERS, json=payload, headers=admin_headers(client))
    assert response.status_code == 422
    assert response.json()["errors"]["permissions"] == ['"Add products" can only be done by the admin.']


def test_permission_dependencies_are_enforced(client: TestClient) -> None:
    response = client.post(SELLERS, json=_new_seller(permissions=["stock.update"]), headers=admin_headers(client))
    assert response.json()["errors"]["permissions"] == ['"Update stock" also requires: View stock, View products.']


def test_unknown_permission_and_duplicate_email_are_rejected(client: TestClient, seeded_db: Session) -> None:
    headers = admin_headers(client)
    assert client.post(SELLERS, json=_new_seller(permissions=["everything"]), headers=headers).status_code == 422

    create_seller(seeded_db, email="raju@kirana.test")
    response = client.post(SELLERS, json=_new_seller(), headers=headers)
    assert response.json()["errors"]["email"] == ["This email is already used by another account."]


def test_permission_changes_apply_on_next_request(client: TestClient, seeded_db: Session) -> None:
    seller = create_seller(seeded_db, [Permission.PRODUCTS_VIEW])
    s_headers = seller_headers(client, seller)

    response = client.put(f"{SELLERS}/{seller.id}/permissions", json={"permissions": []}, headers=admin_headers(client))
    assert response.status_code == 200

    assert client.get("/api/v1/auth/me", headers=s_headers).json()["data"]["permissions"] == []


def test_deactivating_seller_logs_them_out_immediately(client: TestClient, seeded_db: Session) -> None:
    seller = create_seller(seeded_db)
    s_tokens = login(client, seller.email, SELLER_PASSWORD)
    s_headers = {"Authorization": f"Bearer {s_tokens['access_token']}"}

    response = client.patch(f"{SELLERS}/{seller.id}/status", json={"is_active": False}, headers=admin_headers(client))
    assert response.json()["data"]["is_active"] is False

    assert client.get("/api/v1/auth/me", headers=s_headers).status_code == 401
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": s_tokens["refresh_token"]}).status_code == 401


def test_admin_resets_seller_password(client: TestClient, seeded_db: Session) -> None:
    seller = create_seller(seeded_db)
    body = {"password": "Reset1234", "password_confirmation": "Reset1234"}
    assert (
        client.post(f"{SELLERS}/{seller.id}/reset-password", json=body, headers=admin_headers(client)).status_code
        == 200
    )
    login(client, seller.email, "Reset1234")


def test_deleted_seller_cannot_log_in_and_email_stays_reserved(client: TestClient, seeded_db: Session) -> None:
    seller = create_seller(seeded_db, email="raju@kirana.test")
    headers = admin_headers(client)

    assert client.delete(f"{SELLERS}/{seller.id}", headers=headers).status_code == 204
    assert client.get(f"{SELLERS}/{seller.id}", headers=headers).status_code == 404
    response = client.post(
        "/api/v1/auth/login", json={"email": seller.email, "password": SELLER_PASSWORD, "device_name": "x"}
    )
    assert response.status_code == 401
    assert client.post(SELLERS, json=_new_seller(), headers=headers).status_code == 422


def test_list_search_filter_and_pagination(client: TestClient, seeded_db: Session) -> None:
    create_seller(seeded_db, name="Aman Singh")
    create_seller(seeded_db, name="Bunty", is_active=False)
    headers = admin_headers(client)

    page = client.get(SELLERS, params={"search": "aman"}, headers=headers).json()
    assert [s["name"] for s in page["data"]] == ["Aman Singh"]
    assert page["meta"] == {"page": 1, "per_page": 20, "total": 1, "last_page": 1}

    inactive = client.get(SELLERS, params={"is_active": "false"}, headers=headers).json()["data"]
    assert [s["name"] for s in inactive] == ["Bunty"]


def test_admin_cannot_manage_admins_or_other_stores_sellers(client: TestClient, seeded_db: Session) -> None:
    headers = admin_headers(client)
    admin_id = login(client, "admin@kirana.test", "Admin12345")["user"]["id"]
    other_store = Store(name="Other", slug="other", timezone="Asia/Kolkata", currency="INR")
    seeded_db.add(other_store)
    seeded_db.flush()
    foreign = create_seller(seeded_db, store_id=other_store.id)

    assert client.get(f"{SELLERS}/{admin_id}", headers=headers).status_code == 404
    assert client.get(f"{SELLERS}/{foreign.id}", headers=headers).status_code == 404


def test_sellers_never_reach_admin_routes(client: TestClient, seeded_db: Session) -> None:
    seller = create_seller(seeded_db, [p for p in Permission.grantable()])
    headers = seller_headers(client, seller)

    for method, url in [
        ("get", SELLERS),
        ("post", SELLERS),
        ("get", "/api/v1/admin/permissions"),
        ("get", "/api/v1/admin/activity-logs"),
    ]:
        response = client.request(method, url, headers=headers, json=_new_seller())
        assert response.status_code == 403, url
        assert response.json()["code"] == "FORBIDDEN"


def test_permission_catalogue_is_grouped_translated_and_excludes_admin_only(client: TestClient) -> None:
    groups = client.get("/api/v1/admin/permissions", headers=admin_headers(client) | {"Accept-Language": "pa"})
    data = groups.json()["data"]
    assert data[0] == {
        "key": "dashboard",
        "label": "ਡੈਸ਼ਬੋਰਡ",
        "permissions": [{"key": "dashboard.view", "label": "ਡੈਸ਼ਬੋਰਡ ਦੇਖੋ", "depends_on": []}],
    }
    keys = [p["key"] for g in data for p in g["permissions"]]
    assert "products.create" not in keys
    assert len(keys) == len(Permission) - 1


def test_activity_log_filters(client: TestClient, seeded_db: Session) -> None:
    seller = create_seller(seeded_db)
    login(client, seller.email, SELLER_PASSWORD)
    headers = admin_headers(client)

    activity = client.get(f"{SELLERS}/{seller.id}/activity", headers=headers).json()["data"]
    assert activity[0]["action"] == "auth.login"
    assert activity[0]["description"] == "Logged in"
    assert activity[0]["user"] == {"id": seller.id, "name": seller.name}

    logins = client.get("/api/v1/admin/activity-logs", params={"action": "auth.login"}, headers=headers).json()
    assert logins["meta"]["total"] == 2  # seller + admin
    assert client.get("/api/v1/admin/activity-logs", params={"group": "sellers"}, headers=headers).json()["data"] == []
