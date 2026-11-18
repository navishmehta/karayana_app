"""Mobile-friendly password reset: a short numeric code is emailed and typed into the app.

Only a hash of the code is stored, it expires, and it allows a limited number of wrong tries.
Unknown emails get exactly the same response, so nobody can discover which emails have accounts.
"""

from datetime import timedelta

from fastapi import BackgroundTasks
from sqlalchemy import select

from app.api.deps import DbSession
from app.core.clock import utc_now
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.i18n import t
from app.core.security import generate_numeric_code, hash_password, verify_password
from app.enums.activity import ActivityAction, AuditSubject
from app.enums.error_code import ErrorCode
from app.enums.setting_key import SettingKey
from app.models import PasswordResetCode, User
from app.services.audit import Audit
from app.services.auth_service import active_user_by_email, revoke_all_sessions
from app.services.mail import Mail, get_mailer, send_safely
from app.services.settings_service import get_setting


class PasswordResetService:
    def __init__(self, db: DbSession, audit: Audit) -> None:
        self.db = db
        self.audit = audit

    def send_code(self, email: str, background: BackgroundTasks) -> None:
        user = active_user_by_email(self.db, email)
        if user is None or not user.is_active:
            return

        settings = get_settings()
        code = generate_numeric_code(settings.reset_code_length)
        record = self.db.scalar(select(PasswordResetCode).where(PasswordResetCode.user_id == user.id))
        if record is None:
            record = PasswordResetCode(user_id=user.id)
            self.db.add(record)
        record.code_hash = hash_password(code)
        record.attempts = 0
        record.expires_at = utc_now() + timedelta(minutes=settings.reset_code_ttl_minutes)

        self.audit.record(ActivityAction.PASSWORD_RESET_REQUESTED, actor=user)
        self.db.commit()

        background.add_task(send_safely, get_mailer(), self._email(user, code))

    def reset(self, email: str, code: str, new_password: str) -> None:
        user = active_user_by_email(self.db, email)
        record = self.db.scalar(select(PasswordResetCode).where(PasswordResetCode.user_id == user.id)) if user else None
        if user is None or not user.is_active or record is None:
            raise AppError(ErrorCode.INVALID_RESET_CODE)

        settings = get_settings()
        if record.expires_at <= utc_now() or record.attempts >= settings.reset_code_max_attempts:
            self.db.delete(record)
            self.db.commit()
            raise AppError(ErrorCode.INVALID_RESET_CODE)

        if not verify_password(code, record.code_hash):
            record.attempts += 1
            self.db.commit()
            raise AppError(ErrorCode.INVALID_RESET_CODE)

        user.password_hash = hash_password(new_password)
        self.db.delete(record)
        revoke_all_sessions(self.db, user.id)
        self.audit.record(ActivityAction.PASSWORD_RESET, actor=user, subject=(AuditSubject.USER, user.id))
        self.db.commit()

    def _email(self, user: User, code: str) -> Mail:
        """Written in the user's own language."""
        locale = user.locale
        store = get_setting(self.db, user.store_id, SettingKey.STORE_NAME)
        minutes = get_settings().reset_code_ttl_minutes
        body = "\n\n".join(
            [
                t("emails.password_reset.greeting", locale, name=user.name),
                t("emails.password_reset.intro", locale),
                code,
                t("emails.password_reset.expiry", locale, minutes=minutes),
                t("emails.password_reset.ignore", locale),
                store,
            ]
        )
        return Mail(to=user.email, subject=t("emails.password_reset.subject", locale, store=store), body=body)
