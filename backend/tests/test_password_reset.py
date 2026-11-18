import re
from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.core.config import get_settings
from app.models import PasswordResetCode
from app.services.mail import LogMailer
from tests.helpers import SELLER_PASSWORD, create_seller, login

FORGOT = "/api/v1/auth/forgot-password"
RESET = "/api/v1/auth/reset-password"


def _code_from_email() -> str:
    assert LogMailer.outbox, "no email sent"
    return re.search(r"^\d{6}$", LogMailer.outbox[-1].body, re.MULTILINE).group(0)


def test_full_reset_flow(client: TestClient, seeded_db: Session) -> None:
    seller = create_seller(seeded_db, email="raju@kirana.test")
    old_session = login(client, seller.email, SELLER_PASSWORD)

    assert client.post(FORGOT, json={"email": "raju@kirana.test"}).status_code == 200
    mail = LogMailer.outbox[-1]
    assert mail.to == "raju@kirana.test"
    assert "Ramesh Karayana Store" in mail.subject

    body = {
        "email": seller.email,
        "code": _code_from_email(),
        "password": "Brand123",
        "password_confirmation": "Brand123",
    }
    assert client.post(RESET, json=body).status_code == 200

    login(client, seller.email, "Brand123")
    old = {"Authorization": f"Bearer {old_session['access_token']}"}
    assert client.get("/api/v1/auth/me", headers=old).status_code == 401  # signed out everywhere
    assert seeded_db.scalar(select(PasswordResetCode)) is None  # code used up


def test_email_is_in_the_users_language(client: TestClient, seeded_db: Session) -> None:
    create_seller(seeded_db, email="pa@kirana.test", locale="pa")
    client.post(FORGOT, json={"email": "pa@kirana.test"})
    assert "ਪਾਸਵਰਡ ਰੀਸੈੱਟ ਕੋਡ" in LogMailer.outbox[-1].subject


def test_unknown_email_gets_same_answer_and_no_mail(client: TestClient) -> None:
    response = client.post(FORGOT, json={"email": "nobody@kirana.test"})
    assert response.status_code == 200
    assert response.json()["message"] == "If this email is registered, a reset code has been sent to it."
    assert LogMailer.outbox == []


def test_code_is_stored_hashed(client: TestClient, seeded_db: Session) -> None:
    create_seller(seeded_db, email="raju@kirana.test")
    client.post(FORGOT, json={"email": "raju@kirana.test"})
    assert seeded_db.scalar(select(PasswordResetCode)).code_hash != _code_from_email()


def test_wrong_code_counts_attempts_and_locks(client: TestClient, seeded_db: Session) -> None:
    seller = create_seller(seeded_db, email="raju@kirana.test")
    client.post(FORGOT, json={"email": seller.email})
    code = _code_from_email()
    wrong = "000000" if code != "000000" else "111111"
    body = {"email": seller.email, "password": "Brand123", "password_confirmation": "Brand123"}

    record = seeded_db.scalar(select(PasswordResetCode))
    record.attempts = get_settings().reset_code_max_attempts - 1
    seeded_db.commit()

    assert client.post(RESET, json=body | {"code": wrong}).json()["code"] == "INVALID_RESET_CODE"
    # Locked now: even the right code no longer works
    assert client.post(RESET, json=body | {"code": code}).json()["code"] == "INVALID_RESET_CODE"


def test_expired_code_is_rejected(client: TestClient, seeded_db: Session) -> None:
    seller = create_seller(seeded_db, email="raju@kirana.test")
    client.post(FORGOT, json={"email": seller.email})
    record = seeded_db.scalar(select(PasswordResetCode))
    record.expires_at = utc_now() - timedelta(seconds=1)
    seeded_db.commit()

    body = {
        "email": seller.email,
        "code": _code_from_email(),
        "password": "Brand123",
        "password_confirmation": "Brand123",
    }
    assert client.post(RESET, json=body).status_code == 422
