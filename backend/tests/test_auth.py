from datetime import timedelta

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.core.config import get_settings
from app.core.constants import JWT_ALGORITHM
from app.enums.activity import ActivityAction
from app.enums.permission import Permission
from app.models import ActivityLog, AuthSession, DeviceToken
from tests.helpers import ADMIN_EMAIL, ADMIN_PASSWORD, SELLER_PASSWORD, auth_headers, create_seller, login

LOGIN = "/api/v1/auth/login"


def _audit_count(db: Session, action: ActivityAction) -> int:
    return db.scalar(select(func.count(ActivityLog.id)).where(ActivityLog.action == action.value))


def test_seller_logs_in_and_gets_tokens_role_and_permissions(client: TestClient, seeded_db: Session) -> None:
    create_seller(seeded_db, [Permission.PRODUCTS_VIEW], email="raju@kirana.test")

    data = login(client, "  RAJU@Kirana.TEST ", SELLER_PASSWORD)

    assert data["token_type"] == "Bearer"
    assert data["access_token"] and data["refresh_token"]
    assert data["access_token_expires_at"].endswith("+05:30")
    assert data["user"]["role"] == "seller"
    assert data["user"]["permissions"] == ["products.view"]
    assert _audit_count(seeded_db, ActivityAction.LOGIN) == 1


def test_admin_has_every_permission(client: TestClient) -> None:
    assert len(login(client, ADMIN_EMAIL, ADMIN_PASSWORD)["user"]["permissions"]) == len(Permission)


def test_wrong_password_is_rejected_and_logged(client: TestClient, seeded_db: Session) -> None:
    response = client.post(LOGIN, json={"email": ADMIN_EMAIL, "password": "wrong", "device_name": "x"})
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"

    response = client.post(LOGIN, json={"email": "nobody@kirana.test", "password": "x", "device_name": "x"})
    assert response.json()["code"] == "INVALID_CREDENTIALS"  # same answer for unknown emails
    assert _audit_count(seeded_db, ActivityAction.LOGIN_FAILED) == 2


def test_inactive_seller_cannot_log_in(client: TestClient, seeded_db: Session) -> None:
    seller = create_seller(seeded_db, is_active=False)
    response = client.post(LOGIN, json={"email": seller.email, "password": SELLER_PASSWORD, "device_name": "x"})
    assert response.status_code == 403
    assert response.json()["code"] == "ACCOUNT_INACTIVE"


def test_login_is_rate_limited(client: TestClient) -> None:
    for _ in range(get_settings().rate_limit_login_per_minute):
        client.post(LOGIN, json={"email": ADMIN_EMAIL, "password": "wrong", "device_name": "x"})

    response = client.post(LOGIN, json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "device_name": "x"})
    assert response.status_code == 429
    assert response.json()["code"] == "TOO_MANY_REQUESTS"
    assert int(response.headers["retry-after"]) > 0


def test_validation_errors_in_punjabi(client: TestClient) -> None:
    response = client.post(LOGIN, json={}, headers={"Accept-Language": "pa"})
    assert response.status_code == 422
    assert response.json()["errors"]["email"] == ["ਈਮੇਲ ਭਰਨਾ ਲਾਜ਼ਮੀ ਹੈ।"]


def test_protected_routes_need_a_valid_token(client: TestClient) -> None:
    assert client.get("/api/v1/auth/me").json()["code"] == "UNAUTHENTICATED"
    bad = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-token"})
    assert bad.status_code == 401
    assert bad.json()["code"] == "UNAUTHENTICATED"


def test_expired_access_token_says_token_expired(client: TestClient) -> None:
    data = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    claims = jwt.decode(data["access_token"], options={"verify_signature": False})
    claims["exp"] = utc_now() - timedelta(minutes=1)
    expired = jwt.encode(claims, get_settings().jwt_secret.get_secret_value(), algorithm=JWT_ALGORITHM)

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401
    assert response.json()["code"] == "TOKEN_EXPIRED"


def test_token_signed_with_another_key_is_rejected(client: TestClient) -> None:
    data = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    claims = jwt.decode(data["access_token"], options={"verify_signature": False})
    forged = jwt.encode(claims, "attacker-key-" + "x" * 32, algorithm=JWT_ALGORITHM)
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_refresh_rotates_the_refresh_token(client: TestClient) -> None:
    data = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)

    first = client.post("/api/v1/auth/refresh", json={"refresh_token": data["refresh_token"]})
    assert first.status_code == 200
    new = first.json()["data"]
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new['access_token']}"}).status_code == 200

    reused = client.post("/api/v1/auth/refresh", json={"refresh_token": data["refresh_token"]})
    assert reused.status_code == 401  # old refresh token no longer works


def test_logout_ends_only_this_device(client: TestClient, seeded_db: Session) -> None:
    phone = login(client, ADMIN_EMAIL, ADMIN_PASSWORD, "phone")
    tablet = login(client, ADMIN_EMAIL, ADMIN_PASSWORD, "tablet")
    phone_headers = {"Authorization": f"Bearer {phone['access_token']}"}
    tablet_headers = {"Authorization": f"Bearer {tablet['access_token']}"}

    assert client.post("/api/v1/auth/logout", headers=phone_headers).status_code == 200

    assert client.get("/api/v1/auth/me", headers=phone_headers).status_code == 401
    assert client.get("/api/v1/auth/me", headers=tablet_headers).status_code == 200
    assert client.post("/api/v1/auth/refresh", json={"refresh_token": phone["refresh_token"]}).status_code == 401


def test_logout_all_ends_every_device_and_push(client: TestClient, seeded_db: Session) -> None:
    headers = auth_headers(client)
    other = auth_headers(client)
    client.post("/api/v1/devices", json={"token": "fcm-1", "platform": "android"}, headers=headers)

    assert client.post("/api/v1/auth/logout-all", headers=headers).status_code == 200

    assert client.get("/api/v1/auth/me", headers=other).status_code == 401
    assert seeded_db.scalar(select(func.count(DeviceToken.id))) == 0


def test_profile_update_changes_name_and_language_not_email(client: TestClient) -> None:
    headers = auth_headers(client)

    response = client.patch("/api/v1/auth/me", json={"name": "Ramesh", "locale": "pa"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Ramesh"
    assert response.json()["data"]["locale"] == "pa"

    rejected = client.patch("/api/v1/auth/me", json={"email": "new@kirana.test"}, headers=headers)
    assert rejected.status_code == 422  # unknown field: email can't be changed here


def test_profile_rejects_bad_language_and_phone(client: TestClient) -> None:
    response = client.patch("/api/v1/auth/me", json={"locale": "fr", "phone": "12345"}, headers=auth_headers(client))
    errors = response.json()["errors"]
    assert errors["locale"] == ["This language is not supported."]
    assert errors["phone"] == ["Enter a 10-digit mobile number."]


def test_change_password_signs_out_other_devices(client: TestClient, seeded_db: Session) -> None:
    current = auth_headers(client)
    other = auth_headers(client)
    body = {"current_password": "wrong", "password": "NewPass123", "password_confirmation": "NewPass123"}

    assert client.put("/api/v1/auth/password", json=body, headers=current).json()["errors"]["current_password"]

    body["current_password"] = ADMIN_PASSWORD
    assert client.put("/api/v1/auth/password", json=body, headers=current).status_code == 200
    assert client.get("/api/v1/auth/me", headers=current).status_code == 200
    assert client.get("/api/v1/auth/me", headers=other).status_code == 401
    login(client, ADMIN_EMAIL, "NewPass123")


def test_weak_or_mismatched_password_is_rejected(client: TestClient) -> None:
    headers = auth_headers(client)
    weak = {"current_password": ADMIN_PASSWORD, "password": "short", "password_confirmation": "short"}
    errors = client.put("/api/v1/auth/password", json=weak, headers=headers).json()["errors"]
    assert errors["password"] == ["Password must be at least 8 characters and include a letter and a number."]

    mismatch = {"current_password": ADMIN_PASSWORD, "password": "Strong123", "password_confirmation": "Strong124"}
    errors = client.put("/api/v1/auth/password", json=mismatch, headers=headers).json()["errors"]
    assert errors == {"password_confirmation": ["The two passwords do not match."]}


def test_device_token_moves_to_latest_user(client: TestClient, seeded_db: Session) -> None:
    seller = create_seller(seeded_db)
    payload = {"token": "fcm-shared", "platform": "ios"}

    assert client.post("/api/v1/devices", json=payload, headers=auth_headers(client)).status_code == 201
    client.post("/api/v1/devices", json=payload, headers=auth_headers(client, seller.email, SELLER_PASSWORD))

    device = seeded_db.scalar(select(DeviceToken))
    assert device.user_id == seller.id
    assert seeded_db.scalar(select(func.count(DeviceToken.id))) == 1


def test_sessions_are_stored_hashed(client: TestClient, seeded_db: Session) -> None:
    data = login(client, ADMIN_EMAIL, ADMIN_PASSWORD)
    session = seeded_db.scalar(select(AuthSession))
    assert session.refresh_token_hash != data["refresh_token"]
    assert len(session.refresh_token_hash) == 64
