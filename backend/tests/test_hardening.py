"""Security fixes from the Phase 11 review, plus paths the main tests didn't reach."""

import csv
import io
import smtplib
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import store_today, store_tz
from app.core.config import Settings, get_settings
from app.enums.permission import Permission as Perm
from app.main import check_settings
from app.models import DeviceToken, Product, StockAlert, User
from app.services.inventory.stock_cache import refresh_all_stock
from app.services.mail import Mail, SmtpMailer
from app.services.notifications import push
from app.services.notifications.alerts import is_digest_due
from app.services.notifications.push import PushMessage
from app.services.reports.service import safe_text
from tests.helpers import ADMIN_EMAIL, admin_headers, create_seller, make_brand, make_product, seller_headers
from tests.test_inventory import _batch

# --- Spreadsheet formula injection ----------------------------------------------------------------


@pytest.mark.parametrize("name", ['=HYPERLINK("http://evil","x")', "+1+1", "-2", "@SUM(A1)"])
def test_text_that_looks_like_a_formula_is_neutralised(name: str) -> None:
    assert safe_text(name) == f"'{name}"
    assert safe_text("Amul Butter") == "Amul Butter"


def test_exports_never_contain_live_formulas(client: TestClient, seeded_db: Session) -> None:
    make_product(seeded_db, '=HYPERLINK("http://evil.example","click")')
    headers = admin_headers(client)

    csv_text = client.get("/api/v1/reports/products/export", params={"format": "csv"}, headers=headers).content
    names = [row[0] for row in csv.reader(io.StringIO(csv_text.decode("utf-8-sig")))]
    assert '\'=HYPERLINK("http://evil.example","click")' in names

    xlsx = client.get("/api/v1/reports/products/export", params={"format": "xlsx"}, headers=headers).content
    sheet = load_workbook(io.BytesIO(xlsx)).active
    cells = [c for c in sheet["A"] if isinstance(c.value, str) and "HYPERLINK" in c.value]
    assert cells and all(c.data_type == "s" and c.value.startswith("'") for c in cells)


# --- Login limits, headers, production settings --------------------------------------------------


def test_one_ip_cannot_try_unlimited_emails(client: TestClient) -> None:
    limit = get_settings().rate_limit_login_ip_per_minute
    for i in range(limit):
        client.post("/api/v1/auth/login", json={"email": f"guess{i}@kirana.test", "password": "x", "device_name": "x"})
    response = client.post(
        "/api/v1/auth/login", json={"email": "another@kirana.test", "password": "x", "device_name": "x"}
    )
    assert response.status_code == 429


def test_security_headers_are_sent(client: TestClient) -> None:
    headers = client.get("/api/v1/health").headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "strict-transport-security" not in headers  # only in production (HTTPS)


def test_production_refuses_unsafe_settings() -> None:
    unsafe = Settings(environment="production", debug=True, jwt_secret="short", mail_driver="log")
    with pytest.raises(RuntimeError) as error:
        check_settings(unsafe)
    assert "DEBUG" in str(error.value) and "JWT_SECRET" in str(error.value) and "MAIL_DRIVER" in str(error.value)
    check_settings(Settings(environment="production", debug=False, jwt_secret="x" * 40, mail_driver="smtp"))


# --- Nightly refresh, digest timing, delivery failures ---------------------------------------------


def test_nightly_refresh_stops_counting_expired_stock_and_alerts(seeded_db: Session) -> None:
    product = make_product(seeded_db, "Yogurt", min_stock_level=Decimal(2))
    batch = _batch(seeded_db, product.id, "5", 1)
    from app.services.inventory.stock_cache import refresh_product_stock

    refresh_product_stock(seeded_db, product)
    seeded_db.commit()
    assert product.sellable_stock == Decimal("5.000")

    batch.expiry_date = store_today() - timedelta(days=1)  # midnight passed: the batch has now expired
    seeded_db.commit()
    assert refresh_all_stock(seeded_db) >= 1
    seeded_db.refresh(product)
    assert product.sellable_stock == Decimal("0.000")
    assert product.current_stock == Decimal("5.000")  # still physically there until written off
    assert seeded_db.scalar(select(StockAlert.type).where(StockAlert.product_id == product.id)) == "out_of_stock"


@pytest.mark.parametrize(
    ("clock", "due"),
    [("07:59", False), ("08:00", True), ("08:14", True), ("08:15", False), ("20:00", False)],
)
def test_expiry_digest_window(clock: str, due: bool) -> None:
    hour, minute = map(int, clock.split(":"))
    now = datetime(2026, 11, 19, hour, minute, tzinfo=store_tz())
    assert is_digest_due(now, "08:00", 15) is due


def test_send_expiry_alerts_command_respects_time(seeded_db: Session, monkeypatch) -> None:
    from app import cli

    product = make_product(seeded_db, "Old Bread")
    _batch(seeded_db, product.id, "3", -2)
    seeded_db.add(DeviceToken(user_id=seeded_db.scalar(select(User.id).where(User.email == ADMIN_EMAIL)),
                              token="ExponentPushToken[admin]", platform="android"))  # fmt: skip
    seeded_db.commit()
    monkeypatch.setattr("app.core.clock.store_now", lambda: datetime(2026, 11, 19, 3, 0, tzinfo=store_tz()))
    assert cli.send_expiry_alerts(seeded_db, force=False) == 0  # 03:00: not the alert time
    assert cli.send_expiry_alerts(seeded_db, force=True) == 1
    assert cli.send_expiry_alerts(seeded_db, force=True) == 0  # already sent today


def test_push_failure_never_breaks_the_action(seeded_db: Session, monkeypatch) -> None:
    class Broken:
        def send(self, messages):
            raise ConnectionError("push service down")

    monkeypatch.setattr(push, "get_push_sender", lambda: Broken())
    push.deliver(seeded_db, [PushMessage(token="t", title="x", body="y")])  # must not raise


def test_smtp_mailer_sends_with_tls_and_login(monkeypatch) -> None:
    calls = []

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            calls.append(("connect", host, port))

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def starttls(self):
            calls.append(("tls",))

        def login(self, user, password):
            calls.append(("login", user))

        def send_message(self, message):
            calls.append(("send", message["To"], message["Subject"]))

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    settings = get_settings()
    monkeypatch.setattr(settings, "smtp_username", "shop@example.com")
    monkeypatch.setattr(settings, "smtp_password", __import__("pydantic").SecretStr("app-password"))
    SmtpMailer().send(Mail(to="raju@example.com", subject="Code", body="123456"))
    assert [c[0] for c in calls] == ["connect", "tls", "login", "send"]
    assert calls[-1][1:] == ("raju@example.com", "Code")


# --- Remaining admin / auth paths -----------------------------------------------------------------


def test_refresh_is_refused_for_a_deactivated_user(client: TestClient, seeded_db: Session) -> None:
    seller = create_seller(seeded_db)
    tokens = client.post(
        "/api/v1/auth/login", json={"email": seller.email, "password": "Seller123", "device_name": "x"}
    ).json()["data"]
    seller.is_active = False
    seeded_db.commit()
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert response.status_code == 403
    assert response.json()["code"] == "ACCOUNT_INACTIVE"


def test_admin_changes_seller_email(client: TestClient, seeded_db: Session) -> None:
    seller = create_seller(seeded_db)
    other = create_seller(seeded_db)
    headers = admin_headers(client)
    url = f"/api/v1/admin/sellers/{seller.id}"
    assert client.patch(url, json={"email": other.email}, headers=headers).status_code == 422
    assert (
        client.patch(url, json={"email": "NEW@kirana.test"}, headers=headers).json()["data"]["email"]
        == "new@kirana.test"
    )


def test_brand_and_unit_edits(client: TestClient, seeded_db: Session) -> None:
    headers = admin_headers(client)
    brand, taken = make_brand(seeded_db, "Amul"), make_brand(seeded_db, "Verka")
    assert client.patch(f"/api/v1/admin/brands/{brand.id}", json={"name": "Verka"}, headers=headers).status_code == 422
    assert (
        client.patch(f"/api/v1/admin/brands/{brand.id}", json={"name": "Amul India"}, headers=headers).status_code
        == 200
    )
    assert client.delete(f"/api/v1/admin/brands/{taken.id}", headers=headers).status_code == 204

    units = client.get("/api/v1/units", headers=headers).json()["data"]
    kg = next(u for u in units if u["short_name"] == "kg")
    assert (
        client.patch(f"/api/v1/admin/units/{kg['id']}", json={"short_name": "pcs"}, headers=headers).status_code == 422
    )
    updated = client.patch(f"/api/v1/admin/units/{kg['id']}", json={"name": "Kilo"}, headers=headers).json()["data"]
    assert updated["name"] == "Kilo"


def test_categories_report_numbers(client: TestClient, seeded_db: Session) -> None:
    from tests.helpers import make_category

    category = make_category(seeded_db, "Numbers")
    product = make_product(seeded_db, "Counted", category_id=category.id, purchase_price=Decimal("10"))
    make_product(seeded_db, "Sleeping", category_id=category.id, is_active=False)
    _batch(seeded_db, product.id, "4", 30)
    from app.services.inventory.stock_cache import refresh_product_stock

    refresh_product_stock(seeded_db, seeded_db.get(Product, product.id))
    seeded_db.commit()
    report = client.get(
        "/api/v1/reports/categories", params={"category_id": category.id}, headers=admin_headers(client)
    )
    row = report.json()["data"]["rows"][0]
    assert (row["products"], row["active_products"], row["quantity"], row["cost_value"]) == ("2", "1", "4", "40.00")


def test_seller_without_stock_view_never_gets_stock_alerts(client: TestClient, seeded_db: Session) -> None:
    viewer = create_seller(seeded_db, [Perm.PRODUCTS_VIEW])
    product = make_product(seeded_db, "Quiet", min_stock_level=Decimal(5))
    body = {"product_id": product.id, "quantity": "1", "expiry_date": (store_today() + timedelta(days=9)).isoformat()}
    client.post("/api/v1/inventory/stock-in", json=body, headers=admin_headers(client))
    response = client.get("/api/v1/notifications/unread-count", headers=seller_headers(client, viewer))
    assert response.json()["data"]["count"] == 0
