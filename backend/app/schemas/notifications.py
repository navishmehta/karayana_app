from typing import Any

from pydantic import BaseModel, Field

from app.enums.notification import NotificationType
from app.models import Notification
from app.schemas.common import ApiModel, StoreDateTime
from app.services.notifications.alerts import render


class NotificationOut(BaseModel):
    id: int
    type: str
    title: str
    body: str
    data: dict[str, Any]
    read: bool
    created_at: StoreDateTime

    @classmethod
    def from_model(cls, n: Notification) -> "NotificationOut":
        title, body = render(NotificationType(n.type), n.data)  # in the reader's current language
        return cls(
            id=n.id,
            type=n.type,
            title=title,
            body=body,
            data=n.data,
            read=n.read_at is not None,
            created_at=n.created_at,
        )


class UnreadCountOut(BaseModel):
    count: int


class PreferenceItem(ApiModel):
    type: NotificationType
    push_enabled: bool = True
    in_app_enabled: bool = True


class PreferencesUpdate(ApiModel):
    preferences: list[PreferenceItem] = Field(min_length=1)
