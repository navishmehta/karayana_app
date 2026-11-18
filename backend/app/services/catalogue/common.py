"""Helpers shared by catalogue services: store-scoped lookups and unique slugs."""

from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError, field_error
from app.core.text import slugify
from app.enums.error_code import ErrorCode


def get_in_store[ModelT](
    db: Session, model: type[ModelT], obj_id: int, store_id: int, *, with_deleted: bool = False
) -> ModelT:
    """Fetch a row of the user's store, or 404. Another store's rows look exactly like missing ones."""
    stmt = select(model).where(model.id == obj_id, model.store_id == store_id)
    if not with_deleted and hasattr(model, "deleted_at"):
        stmt = stmt.where(model.deleted_at.is_(None))
    obj = db.scalar(stmt)
    if obj is None:
        raise AppError(ErrorCode.NOT_FOUND)
    return obj


def ensure_exists_in_store(db: Session, model: type, obj_id: int, store_id: int, field: str) -> Any:
    """For foreign keys in request bodies: a 422 on the field instead of a 404."""
    obj = db.scalar(select(model).where(model.id == obj_id, model.store_id == store_id, model.deleted_at.is_(None)))
    if obj is None:
        raise field_error(field, "validation.not_found_in_store")
    return obj


def ensure_unique_name(db: Session, model: type, store_id: int, name: str, ignore_id: int | None = None) -> None:
    """Names are unique (case-insensitive) among the store's non-deleted rows."""
    stmt = select(model.id).where(
        model.store_id == store_id, func.lower(model.name) == name.lower(), model.deleted_at.is_(None)
    )
    if ignore_id:
        stmt = stmt.where(model.id != ignore_id)
    if db.scalar(stmt):
        raise field_error("name", "validation.name_taken")


def unique_slug(db: Session, model: type, store_id: int, name: str) -> str:
    """amul-butter, amul-butter-2, … Deleted rows count too (the database index includes them).
    Slugs never change after creation, so shared customer links keep working."""
    base = slugify(name, fallback=model.__tablename__.rstrip("s"))
    taken = set(
        db.scalars(
            select(model.slug).where(model.store_id == store_id, or_(model.slug == base, model.slug.like(f"{base}-%")))
        )
    )
    slug, n = base, 2
    while slug in taken:
        slug, n = f"{base}-{n}", n + 1
    return slug
