from fastapi import UploadFile
from sqlalchemy import Select, func, select, update

from app.api.deps import DbSession
from app.core.clock import utc_now
from app.core.errors import AppError, field_error
from app.core.text import LIKE_ESCAPE, like_contains
from app.enums.activity import ActivityAction, AuditSubject
from app.enums.catalogue import CategorySort, MediaFolder
from app.enums.error_code import ErrorCode
from app.models import Category, Product, User
from app.services.audit import Audit, changed_fields
from app.services.catalogue.common import ensure_unique_name, get_in_store, unique_slug
from app.services.images import store_image
from app.services.storage import get_storage


def products_count_subquery():
    return (
        select(func.count(Product.id))
        .where(Product.category_id == Category.id, Product.deleted_at.is_(None))
        .correlate(Category)
        .scalar_subquery()
    )


class CategoryService:
    def __init__(self, db: DbSession, audit: Audit) -> None:
        self.db = db
        self.audit = audit

    def list_query(self, user: User, search: str | None, is_active: bool | None, sort: CategorySort) -> Select:
        stmt = select(Category, products_count_subquery().label("products_count")).where(
            Category.store_id == user.store_id, Category.deleted_at.is_(None)
        )
        if search:
            stmt = stmt.where(Category.name.like(like_contains(search), escape=LIKE_ESCAPE))
        if is_active is not None:
            stmt = stmt.where(Category.is_active.is_(is_active))
        return stmt.order_by(*sort.order_by)

    def get(self, user: User, category_id: int) -> Category:
        return get_in_store(self.db, Category, category_id, user.store_id)

    def products_count(self, category: Category) -> int:
        return self.db.scalar(
            select(func.count(Product.id)).where(Product.category_id == category.id, Product.deleted_at.is_(None))
        )

    def create(self, user: User, data: dict) -> Category:
        ensure_unique_name(self.db, Category, user.store_id, data["name"])
        if data.get("sort_order") is None:
            max_order = self.db.scalar(select(func.max(Category.sort_order)).where(Category.store_id == user.store_id))
            data["sort_order"] = (max_order or 0) + 1
        category = Category(
            store_id=user.store_id,
            slug=unique_slug(self.db, Category, user.store_id, data["name"]),
            created_by=user.id,
            **data,
        )
        self.db.add(category)
        self.db.flush()
        self.audit.record(
            ActivityAction.CATEGORY_CREATED,
            actor=user,
            subject=(AuditSubject.CATEGORY, category.id),
            properties={"name": category.name},
        )
        self.db.commit()
        return category

    def update(self, user: User, category: Category, values: dict) -> Category:
        if "name" in values:
            ensure_unique_name(self.db, Category, user.store_id, values["name"], ignore_id=category.id)
        old, new = changed_fields(category, values)
        if new:
            category.updated_by = user.id
            self.audit.record(
                ActivityAction.CATEGORY_UPDATED,
                actor=user,
                subject=(AuditSubject.CATEGORY, category.id),
                properties={"old": old, "new": new},
            )
        self.db.commit()
        return category

    def reorder(self, user: User, ordered_ids: list[int]) -> None:
        own_ids = set(
            self.db.scalars(
                select(Category.id).where(
                    Category.store_id == user.store_id, Category.deleted_at.is_(None), Category.id.in_(ordered_ids)
                )
            )
        )
        if own_ids != set(ordered_ids) or len(ordered_ids) != len(set(ordered_ids)):
            raise field_error("ids", "validation.invalid")
        for position, category_id in enumerate(ordered_ids):
            self.db.execute(update(Category).where(Category.id == category_id).values(sort_order=position))
        self.audit.record(ActivityAction.CATEGORIES_REORDERED, actor=user, properties={"order": ordered_ids})
        self.db.commit()

    def replace_image(self, user: User, category: Category, upload: UploadFile) -> Category:
        stored = store_image(upload, MediaFolder.CATEGORIES)
        old = (category.image_path, category.image_thumb_path)
        category.image_path, category.image_thumb_path = stored.path, stored.thumb_path
        self.audit.record(
            ActivityAction.CATEGORY_IMAGE_UPDATED, actor=user, subject=(AuditSubject.CATEGORY, category.id)
        )
        self.db.commit()
        get_storage().delete(*old)
        return category

    def remove_image(self, user: User, category: Category) -> Category:
        old = (category.image_path, category.image_thumb_path)
        category.image_path = category.image_thumb_path = None
        self.audit.record(
            ActivityAction.CATEGORY_IMAGE_REMOVED, actor=user, subject=(AuditSubject.CATEGORY, category.id)
        )
        self.db.commit()
        get_storage().delete(*old)
        return category

    def delete(self, user: User, category: Category) -> None:
        """Only empty categories can be deleted; otherwise deactivate it or move its products first."""
        if self.products_count(category):
            raise AppError(ErrorCode.CATEGORY_NOT_EMPTY)
        category.deleted_at = utc_now()
        self.audit.record(
            ActivityAction.CATEGORY_DELETED,
            actor=user,
            subject=(AuditSubject.CATEGORY, category.id),
            properties={"name": category.name},
        )
        self.db.commit()
        get_storage().delete(category.image_path, category.image_thumb_path)
