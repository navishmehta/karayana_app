"""Admin operations on seller accounts. Sellers are always limited to the admin's own store."""

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession
from app.core.clock import utc_now
from app.core.errors import AppError, field_error
from app.core.i18n import t
from app.core.security import hash_password
from app.core.text import normalize_email
from app.enums.activity import ActivityAction, AuditSubject
from app.enums.error_code import ErrorCode
from app.enums.permission import Permission
from app.enums.role import Role
from app.models import AuthSession, PermissionModel, User
from app.models import Role as RoleModel
from app.services.audit import Audit, changed_fields
from app.services.auth_service import revoke_all_sessions


def validate_permission_set(permissions: list[Permission]) -> set[Permission]:
    """Only grantable permissions, each with all its dependencies (e.g. stock.update needs stock.view)."""
    granted = set(permissions)
    messages = [
        t("validation.permission_not_grantable", permission=p.label) for p in granted if not p.is_grantable_to_sellers
    ]
    for permission, missing in sorted(Permission.missing_dependencies(granted).items()):
        messages.append(
            t(
                "validation.permission_dependency",
                permission=permission.label,
                required=", ".join(m.label for m in missing),
            )
        )
    if messages:
        raise AppError(ErrorCode.VALIDATION_FAILED, errors={"permissions": messages})
    return granted


class SellerService:
    def __init__(self, db: DbSession, audit: Audit) -> None:
        self.db = db
        self.audit = audit

    # --- Queries ----------------------------------------------------------------------------------

    def list_query(self, admin: User, search: str | None, active: bool | None) -> Select:
        stmt = self._sellers(admin).order_by(User.name)
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(or_(User.name.like(term), User.email.like(term), User.phone.like(term)))
        if active is not None:
            stmt = stmt.where(User.is_active.is_(active))
        return stmt

    def get(self, admin: User, seller_id: int) -> User:
        seller = self.db.scalar(self._sellers(admin).where(User.id == seller_id))
        if seller is None:
            raise AppError(ErrorCode.NOT_FOUND)
        return seller

    def active_sessions(self, user_id: int) -> int:
        return (
            self.db.scalar(
                select(func.count(AuthSession.id)).where(
                    AuthSession.user_id == user_id,
                    AuthSession.revoked_at.is_(None),
                    AuthSession.expires_at > utc_now(),
                )
            )
            or 0
        )

    # --- Commands ---------------------------------------------------------------------------------

    def create(self, admin: User, data: dict, permissions: list[Permission]) -> User:
        granted = validate_permission_set(permissions)
        self._ensure_email_free(data["email"])

        seller = User(
            store_id=admin.store_id,
            role_id=self.db.scalar(select(RoleModel.id).where(RoleModel.name == Role.SELLER)),
            name=data["name"],
            email=normalize_email(data["email"]),
            phone=data.get("phone"),
            locale=data.get("locale") or "en",
            password_hash=hash_password(data["password"]),
            created_by=admin.id,
        )
        seller.permissions = self._permission_rows(granted)
        self.db.add(seller)
        self.db.flush()

        self.audit.record(
            ActivityAction.SELLER_CREATED,
            actor=admin,
            subject=(AuditSubject.USER, seller.id),
            properties={"email": seller.email, "permissions": sorted(granted)},
        )
        self.db.commit()
        return seller

    def update(self, admin: User, seller: User, values: dict) -> User:
        if "email" in values:
            values["email"] = normalize_email(values["email"])
            if values["email"] != seller.email:
                self._ensure_email_free(values["email"])
        old, new = changed_fields(seller, values)
        if new:
            self.audit.record(
                ActivityAction.SELLER_UPDATED,
                actor=admin,
                subject=(AuditSubject.USER, seller.id),
                properties={"old": old, "new": new},
            )
        self.db.commit()
        return seller

    def set_permissions(self, admin: User, seller: User, permissions: list[Permission]) -> User:
        granted = validate_permission_set(permissions)
        old = sorted(seller.permission_set)
        seller.permissions = self._permission_rows(granted)
        self.audit.record(
            ActivityAction.SELLER_PERMISSIONS_UPDATED,
            actor=admin,
            subject=(AuditSubject.USER, seller.id),
            properties={"old": old, "new": sorted(granted)},
        )
        self.db.commit()
        return seller

    def set_active(self, admin: User, seller: User, active: bool) -> User:
        """Deactivating signs the seller out of every device immediately."""
        seller.is_active = active
        if not active:
            revoke_all_sessions(self.db, seller.id)
        action = ActivityAction.SELLER_ACTIVATED if active else ActivityAction.SELLER_DEACTIVATED
        self.audit.record(action, actor=admin, subject=(AuditSubject.USER, seller.id))
        self.db.commit()
        return seller

    def reset_password(self, admin: User, seller: User, password: str) -> None:
        seller.password_hash = hash_password(password)
        revoke_all_sessions(self.db, seller.id)
        self.audit.record(ActivityAction.SELLER_PASSWORD_RESET, actor=admin, subject=(AuditSubject.USER, seller.id))
        self.db.commit()

    def delete(self, admin: User, seller: User) -> None:
        """Soft delete: their past actions keep pointing at them; the email stays reserved."""
        revoke_all_sessions(self.db, seller.id)
        seller.deleted_at = utc_now()
        seller.is_active = False
        self.audit.record(
            ActivityAction.SELLER_DELETED,
            actor=admin,
            subject=(AuditSubject.USER, seller.id),
            properties={"email": seller.email},
        )
        self.db.commit()

    # --- Helpers ----------------------------------------------------------------------------------

    @staticmethod
    def _sellers(admin: User) -> Select:
        return (
            select(User)
            .join(User.role)
            .options(selectinload(User.permissions))
            .where(RoleModel.name == Role.SELLER, User.store_id == admin.store_id, User.deleted_at.is_(None))
        )

    def _ensure_email_free(self, email: str) -> None:
        """Emails of deleted users stay reserved, because history still refers to them."""
        if self.db.scalar(select(User.id).where(User.email == normalize_email(email))):
            raise field_error("email", "validation.email_taken")

    def _permission_rows(self, granted: set[Permission]) -> list[PermissionModel]:
        if not granted:
            return []
        return list(self.db.scalars(select(PermissionModel).where(PermissionModel.key.in_([p.value for p in granted]))))
