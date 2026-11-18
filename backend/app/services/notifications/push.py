"""Sending push notifications. PUSH_DRIVER=log (local/testing) or expo (production).

Expo's push service delivers to Android through Firebase Cloud Messaging and to iOS through APNs;
the FCM / APNs credentials are uploaded to EAS, so this server never holds Firebase secrets.
"""

import logging
from dataclasses import dataclass, field
from typing import ClassVar, Protocol

import httpx
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import EXPO_PUSH_BATCH_SIZE, EXPO_PUSH_URL, PUSH_CHANNEL_ID, PUSH_TIMEOUT_SECONDS
from app.models import DeviceToken

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PushMessage:
    token: str
    title: str
    body: str
    data: dict = field(default_factory=dict)


class PushSender(Protocol):
    def send(self, messages: list[PushMessage]) -> list[str]:
        """Send; return tokens the push service says are no longer valid."""
        ...


class LogPushSender:
    sent: ClassVar[list[PushMessage]] = []  # inspected by tests

    def send(self, messages: list[PushMessage]) -> list[str]:
        for message in messages:
            self.sent.append(message)
            logger.info("Push to %s…: %s — %s", message.token[:12], message.title, message.body)
        return []


class ExpoPushSender:
    def send(self, messages: list[PushMessage]) -> list[str]:
        settings = get_settings()
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if settings.expo_push_access_token:
            headers["Authorization"] = f"Bearer {settings.expo_push_access_token.get_secret_value()}"
        invalid: list[str] = []
        with httpx.Client(timeout=PUSH_TIMEOUT_SECONDS) as client:
            for start in range(0, len(messages), EXPO_PUSH_BATCH_SIZE):
                batch = messages[start : start + EXPO_PUSH_BATCH_SIZE]
                payload = [
                    {
                        "to": m.token,
                        "title": m.title,
                        "body": m.body,
                        "data": m.data,
                        "sound": "default",
                        "channelId": PUSH_CHANNEL_ID,
                    }
                    for m in batch
                ]
                response = client.post(EXPO_PUSH_URL, json=payload, headers=headers)
                response.raise_for_status()
                for message, ticket in zip(batch, response.json().get("data", []), strict=False):
                    if (
                        ticket.get("status") == "error"
                        and ticket.get("details", {}).get("error") == "DeviceNotRegistered"
                    ):
                        invalid.append(message.token)
        return invalid


def get_push_sender() -> PushSender:
    return ExpoPushSender() if get_settings().push_driver == "expo" else LogPushSender()


def deliver(db: Session, messages: list[PushMessage]) -> None:
    """Send after the database work is committed. A push problem never breaks the action that caused it."""
    if not messages:
        return
    try:
        invalid = get_push_sender().send(messages)
    except Exception:
        logger.exception("Could not send %d push notifications", len(messages))
        return
    if invalid:
        db.execute(delete(DeviceToken).where(DeviceToken.token.in_(invalid)))
        db.commit()
