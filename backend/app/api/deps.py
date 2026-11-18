"""Shared FastAPI dependencies: database session, current user, admin and permission checks.

Every protected route declares what it needs, e.g.:
    def endpoint(user: CurrentUser) ...                                  # any logged-in staff
    def endpoint(admin: AdminUser) ...                                   # admin only
    def endpoint(user: Annotated[User, Depends(require(Permission.X))])  # specific permission
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.clock import utc_now
from app.core.database import get_db
from app.core.errors import AppError
from app.core.security import TokenExpiredError, decode_access_token
from app.enums.error_code import ErrorCode
from app.enums.permission import Permission
from app.models import AuthSession, User

DbSession = Annotated[Session, Depends(get_db)]

_bearer = HTTPBearer(auto_error=False, description="Access token from /auth/login")


def get_current_user(
    request: Request,
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    """Valid token + live session + active, non-deleted user. Logout or deactivation takes effect immediately."""
    if credentials is None:
        raise AppError(ErrorCode.UNAUTHENTICATED)
    try:
        claims = decode_access_token(credentials.credentials)
    except TokenExpiredError as exc:
        raise AppError(ErrorCode.TOKEN_EXPIRED) from exc
    except Exception as exc:
        raise AppError(ErrorCode.UNAUTHENTICATED) from exc

    session = db.get(AuthSession, claims.session_id)
    if (
        session is None
        or session.user_id != claims.user_id
        or session.revoked_at is not None
        or session.expires_at <= utc_now()
    ):
        raise AppError(ErrorCode.UNAUTHENTICATED)

    user = db.scalar(
        select(User).options(selectinload(User.permissions)).where(User.id == claims.user_id, User.deleted_at.is_(None))
    )
    if user is None:
        raise AppError(ErrorCode.UNAUTHENTICATED)
    if not user.is_active:
        session.revoked_at = utc_now()
        db.commit()
        raise AppError(ErrorCode.ACCOUNT_INACTIVE)

    request.state.session_id = session.id
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def current_session_id(request: Request, _user: CurrentUser) -> int:
    return request.state.session_id


CurrentSessionId = Annotated[int, Depends(current_session_id)]


def require_admin(user: CurrentUser) -> User:
    if not user.is_admin:
        raise AppError(ErrorCode.FORBIDDEN)
    return user


AdminUser = Annotated[User, Depends(require_admin)]


def require(*permissions: Permission) -> Callable[[User], User]:
    """Dependency factory: the user must have ALL the given permissions (admin always passes)."""

    def _check(user: CurrentUser) -> User:
        if not all(user.has_permission(p) for p in permissions):
            raise AppError(ErrorCode.FORBIDDEN)
        return user

    return _check


def require_any(*permissions: Permission) -> Callable[[User], User]:
    """Dependency factory: the user must have AT LEAST ONE of the given permissions."""

    def _check(user: CurrentUser) -> User:
        if not any(user.has_permission(p) for p in permissions):
            raise AppError(ErrorCode.FORBIDDEN)
        return user

    return _check
