from typing import Any

from pydantic import BaseModel

from app.core.i18n import has_key, t
from app.models import ActivityLog
from app.schemas.common import StoreDateTime


class ActivityUserOut(BaseModel):
    id: int
    name: str


class ActivitySubjectOut(BaseModel):
    type: str
    id: int


class ActivityOut(BaseModel):
    id: int
    action: str
    description: str
    user: ActivityUserOut | None
    subject: ActivitySubjectOut | None
    properties: dict[str, Any] | None
    ip_address: str | None
    created_at: StoreDateTime

    @classmethod
    def from_model(cls, log: ActivityLog) -> "ActivityOut":
        key = f"activity.{log.action}"
        return cls(
            id=log.id,
            action=log.action,
            description=t(key) if has_key(key) else log.action,
            user=ActivityUserOut(id=log.user.id, name=log.user.name) if log.user else None,
            subject=ActivitySubjectOut(type=log.subject_type, id=log.subject_id)
            if log.subject_type and log.subject_id
            else None,
            properties=log.properties,
            ip_address=log.ip_address,
            created_at=log.created_at,
        )
