"""Single entry point for writing to the activity log, so every entry has the same shape."""

from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import DbSession
from app.enums.activity import ActivityAction, AuditSubject
from app.models import ActivityLog, User

USER_AGENT_MAX_LENGTH = 255


@dataclass(frozen=True)
class RequestContext:
    ip_address: str | None
    user_agent: str | None


def get_request_context(request: Request) -> RequestContext:
    user_agent = request.headers.get("user-agent")
    return RequestContext(
        ip_address=request.client.host if request.client else None,
        user_agent=user_agent[:USER_AGENT_MAX_LENGTH] if user_agent else None,
    )


ClientContext = Annotated[RequestContext, Depends(get_request_context)]


class AuditLogger:
    def __init__(self, db: DbSession, context: ClientContext) -> None:
        self.db = db
        self.context = context

    def record(
        self,
        action: ActivityAction,
        *,
        actor: User | None,
        subject: tuple[AuditSubject, int] | None = None,
        properties: dict[str, Any] | None = None,
        store_id: int | None = None,
    ) -> None:
        """Adds the entry to the current transaction (saved when the service commits)."""
        self.db.add(
            ActivityLog(
                store_id=store_id or (actor.store_id if actor else None),
                user_id=actor.id if actor else None,
                action=action.value,
                subject_type=subject[0].value if subject else None,
                subject_id=subject[1] if subject else None,
                properties=properties or None,
                ip_address=self.context.ip_address,
                user_agent=self.context.user_agent,
            )
        )


Audit = Annotated[AuditLogger, Depends()]


def changed_fields(model: Any, values: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Applies `values` to `model`; returns (old, new) for the fields that actually changed."""
    old: dict[str, Any] = {}
    new: dict[str, Any] = {}
    for field, value in values.items():
        current = getattr(model, field)
        if current != value:
            old[field], new[field] = current, value
            setattr(model, field, value)
    return old, new


__all__ = ["Audit", "AuditLogger", "ClientContext", "RequestContext", "Session", "changed_fields"]
