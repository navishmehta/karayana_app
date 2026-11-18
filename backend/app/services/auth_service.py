"""Login sessions: each device gets its own session holding a hashed refresh token."""

from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession
from app.core.clock import utc_now
from app.core.config import get_settings
from app.core.errors import AppError, field_error
from app.core.security import create_access_token, generate_refresh_token, hash_password, hash_token, verify_password
from app.core.text import normalize_email
from app.enums.activity import ActivityAction, AuditSubject
from app.enums.error_code import ErrorCode
from app.models import AuthSession, DeviceToken, User
from app.schemas.auth import TokenPair
from app.services.audit import Audit, ClientContext, changed_fields


def active_user_by_email(db: DbSession, email: str) -> User | None:
    return db.scalar(
        select(User)
        .options(selectinload(User.permissions))
        .where(User.email == normalize_email(email), User.deleted_at.is_(None))
    )


def revoke_all_sessions(db: DbSession, user_id: int, *, except_session_id: int | None = None) -> None:
    """Signs a user out of every device (optionally keeping one) and stops their push notifications."""
    stmt = update(AuthSession).where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
    if except_session_id is not None:
        stmt = stmt.where(AuthSession.id != except_session_id)
    db.execute(stmt.values(revoked_at=utc_now()))
    if except_session_id is None:
        db.query(DeviceToken).filter(DeviceToken.user_id == user_id).delete()


class AuthService:
    def __init__(self, db: DbSession, audit: Audit, context: ClientContext) -> None:
        self.db = db
        self.audit = audit
        self.context = context

    def login(self, email: str, password: str, device_name: str) -> tuple[TokenPair, User]:
        user = active_user_by_email(self.db, email)

        if not verify_password(password, user.password_hash if user else None) or user is None:
            self.audit.record(ActivityAction.LOGIN_FAILED, actor=None, properties={"email": normalize_email(email)})
            self.db.commit()
            raise AppError(ErrorCode.INVALID_CREDENTIALS)

        if not user.is_active:
            raise AppError(ErrorCode.ACCOUNT_INACTIVE)

        refresh_token = generate_refresh_token()
        session = AuthSession(
            user_id=user.id,
            refresh_token_hash=hash_token(refresh_token),
            device_name=device_name,
            ip_address=self.context.ip_address,
            expires_at=utc_now() + timedelta(days=get_settings().refresh_token_ttl_days),
            last_used_at=utc_now(),
        )
        self.db.add(session)
        user.last_login_at = utc_now()
        self.db.flush()

        self.audit.record(ActivityAction.LOGIN, actor=user, properties={"device": device_name})
        self.db.commit()
        return self._tokens(user, session, refresh_token), user

    def refresh(self, refresh_token: str) -> TokenPair:
        """Exchanges a refresh token for new tokens. The old refresh token stops working (rotation)."""
        session = self.db.scalar(select(AuthSession).where(AuthSession.refresh_token_hash == hash_token(refresh_token)))
        if session is None or session.revoked_at is not None or session.expires_at <= utc_now():
            raise AppError(ErrorCode.UNAUTHENTICATED)

        user = self.db.get(User, session.user_id)
        if user is None or user.deleted_at is not None:
            raise AppError(ErrorCode.UNAUTHENTICATED)
        if not user.is_active:
            session.revoked_at = utc_now()
            self.db.commit()
            raise AppError(ErrorCode.ACCOUNT_INACTIVE)

        new_refresh_token = generate_refresh_token()
        session.refresh_token_hash = hash_token(new_refresh_token)
        session.last_used_at = utc_now()
        self.db.commit()
        return self._tokens(user, session, new_refresh_token)

    def logout(self, user: User, session_id: int) -> None:
        session = self.db.get(AuthSession, session_id)
        if session and session.user_id == user.id:
            session.revoked_at = utc_now()
        self.audit.record(ActivityAction.LOGOUT, actor=user)
        self.db.commit()

    def logout_all(self, user: User) -> None:
        revoke_all_sessions(self.db, user.id)
        self.audit.record(ActivityAction.LOGOUT_ALL, actor=user)
        self.db.commit()

    def update_profile(self, user: User, values: dict) -> User:
        _, new = changed_fields(user, values)
        if new:
            self.audit.record(ActivityAction.PROFILE_UPDATED, actor=user, properties={"changed": sorted(new)})
        self.db.commit()
        return user

    def change_password(self, user: User, session_id: int, current_password: str, new_password: str) -> None:
        if not verify_password(current_password, user.password_hash):
            raise field_error("current_password", "validation.current_password")
        user.password_hash = hash_password(new_password)
        revoke_all_sessions(self.db, user.id, except_session_id=session_id)
        self.audit.record(ActivityAction.PASSWORD_CHANGED, actor=user, subject=(AuditSubject.USER, user.id))
        self.db.commit()

    @staticmethod
    def _tokens(user: User, session: AuthSession, refresh_token: str) -> TokenPair:
        access_token, access_expires = create_access_token(user.id, session.id)
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            access_token_expires_at=access_expires,
            refresh_token_expires_at=session.expires_at,
        )
