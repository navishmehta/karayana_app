"""The logged-in user's notifications and notification preferences."""

from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import func, select, update

from app.api.deps import CurrentUser, DbSession
from app.core.clock import utc_now
from app.core.errors import AppError
from app.core.i18n import t
from app.core.pagination import Pagination, paginate
from app.enums.error_code import ErrorCode
from app.enums.notification import NotificationType
from app.models import Notification, NotificationPreference
from app.schemas.common import DataResponse, MessageResponse, Page
from app.schemas.notifications import NotificationOut, PreferenceItem, PreferencesUpdate, UnreadCountOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=Page[NotificationOut], summary="My notifications, newest first")
def list_notifications(
    user: CurrentUser, db: DbSession, pagination: Pagination, unread_only: Annotated[bool, Query()] = False
) -> Page[NotificationOut]:
    stmt = select(Notification).where(Notification.user_id == user.id).order_by(Notification.id.desc())
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))
    return paginate(db, stmt, pagination, NotificationOut.from_model)


@router.get("/unread-count", response_model=DataResponse[UnreadCountOut])
def unread_count(user: CurrentUser, db: DbSession) -> DataResponse[UnreadCountOut]:
    count = db.scalar(
        select(func.count(Notification.id)).where(Notification.user_id == user.id, Notification.read_at.is_(None))
    )
    return DataResponse(data=UnreadCountOut(count=count or 0))


@router.post("/{notification_id}/read", response_model=DataResponse[NotificationOut])
def mark_read(notification_id: int, user: CurrentUser, db: DbSession) -> DataResponse[NotificationOut]:
    notification = db.get(Notification, notification_id)
    if notification is None or notification.user_id != user.id:
        raise AppError(ErrorCode.NOT_FOUND)
    notification.read_at = notification.read_at or utc_now()
    db.commit()
    return DataResponse(data=NotificationOut.from_model(notification))


@router.post("/read-all", response_model=MessageResponse)
def mark_all_read(user: CurrentUser, db: DbSession) -> MessageResponse:
    db.execute(
        update(Notification)
        .where(Notification.user_id == user.id, Notification.read_at.is_(None))
        .values(read_at=utc_now())
    )
    db.commit()
    return MessageResponse(message=t("messages.notifications_read"))


def _my_types(user) -> list[NotificationType]:
    return [kind for kind in NotificationType if user.has_permission(kind.permission)]


@router.get("/preferences", response_model=DataResponse[list[PreferenceItem]], summary="Which alerts I get")
def get_preferences(user: CurrentUser, db: DbSession) -> DataResponse[list[PreferenceItem]]:
    saved = {
        p.type: p for p in db.scalars(select(NotificationPreference).where(NotificationPreference.user_id == user.id))
    }
    items = []
    for kind in _my_types(user):
        p = saved.get(kind.value)
        items.append(
            PreferenceItem(
                type=kind, push_enabled=p.push_enabled if p else True, in_app_enabled=p.in_app_enabled if p else True
            )
        )
    return DataResponse(data=items)


@router.put("/preferences", response_model=DataResponse[list[PreferenceItem]])
def update_preferences(body: PreferencesUpdate, user: CurrentUser, db: DbSession) -> DataResponse[list[PreferenceItem]]:
    allowed = set(_my_types(user))
    for item in body.preferences:
        if item.type not in allowed:
            continue
        pref = db.scalar(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user.id, NotificationPreference.type == item.type.value
            )
        )
        if pref is None:
            pref = NotificationPreference(user_id=user.id, type=item.type.value)
            db.add(pref)
        pref.push_enabled = item.push_enabled
        pref.in_app_enabled = item.in_app_enabled
    db.commit()
    return get_preferences(user, db)
