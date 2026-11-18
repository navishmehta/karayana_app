"""Brands (store-scoped, for product form autocomplete) and units (shared list, admin-managed)."""

from sqlalchemy import Select, func, select

from app.api.deps import DbSession
from app.core.clock import utc_now
from app.core.errors import AppError, field_error
from app.core.text import LIKE_ESCAPE, like_contains
from app.enums.activity import ActivityAction, AuditSubject
from app.enums.error_code import ErrorCode
from app.models import Brand, Product, Unit, User
from app.services.audit import Audit, changed_fields
from app.services.catalogue.common import ensure_unique_name, get_in_store, unique_slug


class BrandService:
    def __init__(self, db: DbSession, audit: Audit) -> None:
        self.db = db
        self.audit = audit

    def list_query(self, user: User, search: str | None) -> Select:
        stmt = select(Brand).where(Brand.store_id == user.store_id, Brand.deleted_at.is_(None)).order_by(Brand.name)
        if search:
            stmt = stmt.where(Brand.name.like(like_contains(search), escape=LIKE_ESCAPE))
        return stmt

    def get(self, user: User, brand_id: int) -> Brand:
        return get_in_store(self.db, Brand, brand_id, user.store_id)

    def create(self, user: User, data: dict) -> Brand:
        ensure_unique_name(self.db, Brand, user.store_id, data["name"])
        brand = Brand(store_id=user.store_id, slug=unique_slug(self.db, Brand, user.store_id, data["name"]), **data)
        self.db.add(brand)
        self.db.flush()
        self.audit.record(
            ActivityAction.BRAND_CREATED, actor=user, subject=(AuditSubject.BRAND, brand.id), properties=data
        )
        self.db.commit()
        return brand

    def update(self, user: User, brand: Brand, values: dict) -> Brand:
        if "name" in values:
            ensure_unique_name(self.db, Brand, user.store_id, values["name"], ignore_id=brand.id)
        old, new = changed_fields(brand, values)
        if new:
            self.audit.record(
                ActivityAction.BRAND_UPDATED,
                actor=user,
                subject=(AuditSubject.BRAND, brand.id),
                properties={"old": old, "new": new},
            )
        self.db.commit()
        return brand

    def delete(self, user: User, brand: Brand) -> None:
        in_use = self.db.scalar(
            select(func.count(Product.id)).where(Product.brand_id == brand.id, Product.deleted_at.is_(None))
        )
        if in_use:
            raise AppError(ErrorCode.IN_USE)
        brand.deleted_at = utc_now()
        self.audit.record(
            ActivityAction.BRAND_DELETED,
            actor=user,
            subject=(AuditSubject.BRAND, brand.id),
            properties={"name": brand.name},
        )
        self.db.commit()


class UnitService:
    def __init__(self, db: DbSession, audit: Audit) -> None:
        self.db = db
        self.audit = audit

    def list(self, active_only: bool) -> list[Unit]:
        stmt = select(Unit).order_by(Unit.name)
        if active_only:
            stmt = stmt.where(Unit.is_active.is_(True))
        return list(self.db.scalars(stmt))

    def get(self, unit_id: int) -> Unit:
        unit = self.db.get(Unit, unit_id)
        if unit is None:
            raise AppError(ErrorCode.NOT_FOUND)
        return unit

    def _ensure_short_name_free(self, short_name: str, ignore_id: int | None = None) -> None:
        stmt = select(Unit.id).where(func.lower(Unit.short_name) == short_name.lower())
        if ignore_id:
            stmt = stmt.where(Unit.id != ignore_id)
        if self.db.scalar(stmt):
            raise field_error("short_name", "validation.name_taken")

    def create(self, admin: User, data: dict) -> Unit:
        self._ensure_short_name_free(data["short_name"])
        unit = Unit(**data)
        self.db.add(unit)
        self.db.flush()
        self.audit.record(
            ActivityAction.UNIT_CREATED, actor=admin, subject=(AuditSubject.UNIT, unit.id), properties=data
        )
        self.db.commit()
        return unit

    def update(self, admin: User, unit: Unit, values: dict) -> Unit:
        if "short_name" in values:
            self._ensure_short_name_free(values["short_name"], ignore_id=unit.id)
        old, new = changed_fields(unit, values)
        if new:
            self.audit.record(
                ActivityAction.UNIT_UPDATED,
                actor=admin,
                subject=(AuditSubject.UNIT, unit.id),
                properties={"old": old, "new": new},
            )
        self.db.commit()
        return unit

    def delete(self, admin: User, unit: Unit) -> None:
        """A unit used by any product (even a deleted one) can only be deactivated."""
        if self.db.scalar(select(func.count(Product.id)).where(Product.unit_id == unit.id)):
            raise AppError(ErrorCode.IN_USE)
        self.audit.record(
            ActivityAction.UNIT_DELETED,
            actor=admin,
            subject=(AuditSubject.UNIT, unit.id),
            properties={"short_name": unit.short_name},
        )
        self.db.delete(unit)
        self.db.commit()
