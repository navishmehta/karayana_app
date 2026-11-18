from datetime import timedelta
from decimal import Decimal

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.clock import store_today
from app.enums.permission import Permission as Perm
from app.enums.setting_key import SettingKey
from app.models import AppSetting, DeviceToken, Notification, StockAlert, User
from app.services.notifications import push
from app.services.notifications.alerts import AlertService
from app.services.notifications.push import ExpoPushSender, LogPushSender, PushMessage
from tests.helpers import ADMIN_EMAIL, admin_headers, create_seller, make_product, seller_headers
from tests.test_inventory import _batch

STOCK_IN, STOCK_OUT = "/api/v1/inventory/stock-in", "/api/v1/inventory/stock-out"


def _admin(db: Session) -> User:
    return db.scalar(select(User).where(User.email == ADMIN_EMAIL))


def _notes(db: Session, user: User, kind: str | None = None) -> int:
    stmt = select(func.count(Notification.id)).where(Notification.user_id == user.id)
    if kind:
        stmt = stmt.where(Notification.type == kind)
    return db.scalar(stmt)


def _out(client: TestClient, headers: dict, product_id: int, qty: str):
    body = {"product_id": product_id, "quantity": qty, "reason": "sold_manually"}
    assert client.post(STOCK_OUT, json=body, headers=headers).status_code == 201


def _in(client: TestClient, headers: dict, product_id: int, qty: str):
    body = {"product_id": product_id, "quantity": qty, "expiry_date": (store_today() + timedelta(days=60)).isoformat()}
    assert client.post(STOCK_IN, json=body, headers=headers).status_code == 201


def test_one_alert_per_problem_low_then_out_then_recovered(client: TestClient, seeded_db: Session) -> None:
    headers = admin_headers(client)
    admin = _admin(seeded_db)
    product = make_product(seeded_db, "Bread", min_stock_level=Decimal(5))
    _in(client, headers, product.id, "10")
    assert _notes(seeded_db, admin) == 0

    _out(client, headers, product.id, "6")  # 4 left: low
    _out(client, headers, product.id, "1")  # still low: no repeat
    assert _notes(seeded_db, admin, "low_stock") == 1

    _out(client, headers, product.id, "3")  # 0 left: out of stock
    assert _notes(seeded_db, admin, "out_of_stock") == 1

    _in(client, headers, product.id, "20")  # recovered: alert resolved
    assert seeded_db.scalar(select(func.count(StockAlert.id)).where(StockAlert.status == "open")) == 0
    _out(client, headers, product.id, "17")  # low again: new alert
    assert _notes(seeded_db, admin, "low_stock") == 2


def test_recipients_follow_permissions_and_push_goes_to_their_devices(client: TestClient, seeded_db: Session) -> None:
    keeper = create_seller(seeded_db, [Perm.PRODUCTS_VIEW, Perm.STOCK_VIEW])
    counter = create_seller(seeded_db, [Perm.PRODUCTS_VIEW])
    seeded_db.add(DeviceToken(user_id=keeper.id, token="ExponentPushToken[keeper]", platform="android"))
    seeded_db.commit()
    product = make_product(seeded_db, "Eggs", min_stock_level=Decimal(5))
    headers = admin_headers(client)
    _in(client, headers, product.id, "6")
    _out(client, headers, product.id, "2")

    assert _notes(seeded_db, keeper) == 1
    assert _notes(seeded_db, counter) == 0
    assert [m.token for m in LogPushSender.sent] == ["ExponentPushToken[keeper]"]
    assert LogPushSender.sent[0].title == "Low stock: Eggs"
    assert LogPushSender.sent[0].data == {"type": "low_stock", "product_id": product.id}


def test_push_uses_each_users_language(client: TestClient, seeded_db: Session) -> None:
    seller = create_seller(seeded_db, [Perm.PRODUCTS_VIEW, Perm.STOCK_VIEW], locale="pa")
    seeded_db.add(DeviceToken(user_id=seller.id, token="ExponentPushToken[pa]", platform="ios"))
    seeded_db.commit()
    product = make_product(seeded_db, "Atta", min_stock_level=Decimal(5))
    headers = admin_headers(client)
    _in(client, headers, product.id, "3")  # first receipt already below minimum
    assert LogPushSender.sent[0].title == "ਘੱਟ ਸਟਾਕ: Atta"


def test_store_setting_switches_alerts_off(client: TestClient, seeded_db: Session) -> None:
    setting = seeded_db.scalar(select(AppSetting).where(AppSetting.key == SettingKey.NOTIFY_LOW_STOCK.value))
    setting.value = False
    seeded_db.commit()
    product = make_product(seeded_db, "Salt", min_stock_level=Decimal(5))
    _in(client, admin_headers(client), product.id, "2")
    assert _notes(seeded_db, _admin(seeded_db)) == 0


def test_preferences_can_turn_off_push_but_keep_in_app(client: TestClient, seeded_db: Session) -> None:
    seller = create_seller(seeded_db, [Perm.PRODUCTS_VIEW, Perm.STOCK_VIEW])
    s_headers = seller_headers(client, seller)
    seeded_db.add(DeviceToken(user_id=seller.id, token="ExponentPushToken[quiet]", platform="android"))
    seeded_db.commit()
    prefs = client.get("/api/v1/notifications/preferences", headers=s_headers).json()["data"]
    assert [p["type"] for p in prefs] == ["low_stock", "out_of_stock"]  # no expiry.view: no expiry alerts
    body = {"preferences": [{"type": "low_stock", "push_enabled": False, "in_app_enabled": True}]}
    assert client.put("/api/v1/notifications/preferences", json=body, headers=s_headers).status_code == 200

    product = make_product(seeded_db, "Tea", min_stock_level=Decimal(5))
    _in(client, admin_headers(client), product.id, "2")
    assert _notes(seeded_db, seller) == 1
    assert all(m.token != "ExponentPushToken[quiet]" for m in LogPushSender.sent)


def test_min_stock_change_can_trigger_alert(client: TestClient, seeded_db: Session) -> None:
    product = make_product(seeded_db, "Sugar", min_stock_level=Decimal(1))
    headers = admin_headers(client)
    _in(client, headers, product.id, "5")
    assert _notes(seeded_db, _admin(seeded_db)) == 0
    client.patch(f"/api/v1/products/{product.id}", json={"min_stock_level": "10"}, headers=headers)
    assert _notes(seeded_db, _admin(seeded_db), "low_stock") == 1


def test_list_read_and_unread(client: TestClient, seeded_db: Session) -> None:
    headers = admin_headers(client)
    for name in ("Ghee", "Oil"):
        _in(client, headers, make_product(seeded_db, name, min_stock_level=Decimal(5)).id, "1")

    assert client.get("/api/v1/notifications/unread-count", headers=headers).json()["data"] == {"count": 2}
    page = client.get("/api/v1/notifications", headers=headers | {"Accept-Language": "pa"}).json()
    first = page["data"][0]
    assert first["title"].startswith("ਘੱਟ ਸਟਾਕ") and first["read"] is False

    assert client.post(f"/api/v1/notifications/{first['id']}/read", headers=headers).json()["data"]["read"] is True
    assert client.get("/api/v1/notifications/unread-count", headers=headers).json()["data"] == {"count": 1}
    client.post("/api/v1/notifications/read-all", headers=headers)
    assert client.get("/api/v1/notifications", params={"unread_only": True}, headers=headers).json()["data"] == []

    other = seller_headers(client, create_seller(seeded_db, [Perm.PRODUCTS_VIEW, Perm.STOCK_VIEW]))
    assert client.post(f"/api/v1/notifications/{first['id']}/read", headers=other).status_code == 404


def test_expiry_digest_once_a_day_and_only_when_needed(client: TestClient, seeded_db: Session) -> None:
    admin = _admin(seeded_db)
    alerts = AlertService(seeded_db)
    assert alerts.expiry_digest(admin.store_id) == []  # nothing to report
    assert _notes(seeded_db, admin) == 0

    product = make_product(seeded_db, "Curd")
    _batch(seeded_db, product.id, "4", -1)
    _batch(seeded_db, product.id, "2", 3)
    alerts.expiry_digest(admin.store_id)
    seeded_db.commit()
    alerts.expiry_digest(admin.store_id)  # second run the same day: nothing new
    seeded_db.commit()
    assert _notes(seeded_db, admin, "expiry_digest") == 1
    text = client.get("/api/v1/notifications", headers=admin_headers(client)).json()["data"][0]["body"]
    assert text == "1 expired batch(es) still in stock, 1 expiring within 7 days."


def test_expo_sender_drops_unregistered_devices(seeded_db: Session, monkeypatch) -> None:
    seller = create_seller(seeded_db, [Perm.PRODUCTS_VIEW, Perm.STOCK_VIEW])
    for token in ("ExponentPushToken[ok]", "ExponentPushToken[gone]"):
        seeded_db.add(DeviceToken(user_id=seller.id, token=token, platform="android"))
    seeded_db.commit()
    sent_payloads = []

    class FakeClient:
        def __init__(self, *args, **kwargs) -> None: ...
        def __enter__(self):
            return self  # noqa: E704

        def __exit__(self, *args) -> None: ...  # noqa: E704

        def post(self, url, json, headers):
            sent_payloads.append(json)
            tickets = [{"status": "ok", "id": "1"}, {"status": "error", "details": {"error": "DeviceNotRegistered"}}]
            return httpx.Response(200, json={"data": tickets}, request=httpx.Request("POST", url))

    monkeypatch.setattr(push.httpx, "Client", FakeClient)
    monkeypatch.setattr(push, "get_push_sender", lambda: ExpoPushSender())
    messages = [PushMessage(token=t, title="T", body="B") for t in ("ExponentPushToken[ok]", "ExponentPushToken[gone]")]
    push.deliver(seeded_db, messages)

    assert sent_payloads[0][0]["channelId"] == "alerts"
    tokens = set(seeded_db.scalars(select(DeviceToken.token).where(DeviceToken.user_id == seller.id)))
    assert tokens == {"ExponentPushToken[ok]"}
