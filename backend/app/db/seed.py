"""Idempotent seeding: safe to run on an existing database; never overwrites existing values."""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import DEFAULT_STORE_SLUG
from app.core.security import hash_password
from app.core.text import normalize_email, slugify
from app.db.seed_data import CATEGORIES, UNITS
from app.enums.permission import Permission
from app.enums.role import Role
from app.enums.setting_key import SettingKey
from app.models import AppSetting, Category, PermissionModel, Store, Unit, User
from app.models import Role as RoleModel

logger = logging.getLogger(__name__)


def seed_store(db: Session) -> Store:
    settings = get_settings()
    store = db.scalar(select(Store).where(Store.slug == DEFAULT_STORE_SLUG))
    if store is None:
        store = Store(
            name=settings.default_store_name,
            slug=DEFAULT_STORE_SLUG,
            timezone=settings.store_timezone,
            currency=settings.store_currency,
        )
        db.add(store)
        db.flush()
    return store


def seed_roles_and_permissions(db: Session) -> None:
    existing = {p.key: p for p in db.scalars(select(PermissionModel))}
    for permission in Permission:
        if permission.value not in existing:
            existing[permission.value] = PermissionModel(key=permission.value, group=permission.group)
            db.add(existing[permission.value])

    roles = {r.name: r for r in db.scalars(select(RoleModel))}
    for role in Role:
        if role.value not in roles:
            roles[role.value] = RoleModel(name=role.value)
            db.add(roles[role.value])

    # Admin's role lists every permission (informational; admin also bypasses checks). Seller role has none.
    roles[Role.ADMIN].permissions = list(existing.values())
    db.flush()


def seed_admin(db: Session, store: Store) -> None:
    settings = get_settings()
    if not settings.admin_email or not settings.admin_password:
        logger.warning("ADMIN_EMAIL / ADMIN_PASSWORD not set: admin user not created.")
        return

    email = normalize_email(settings.admin_email)
    if db.scalar(select(User).where(User.email == email)) is None:
        admin_role = db.scalar(select(RoleModel).where(RoleModel.name == Role.ADMIN))
        db.add(
            User(
                store_id=store.id,
                role_id=admin_role.id,
                name=settings.admin_name,
                email=email,
                password_hash=hash_password(settings.admin_password.get_secret_value()),
                locale=settings.default_locale,
            )
        )


def seed_units(db: Session) -> None:
    existing = set(db.scalars(select(Unit.short_name)))
    for name, short_name, allows_decimal in UNITS:
        if short_name not in existing:
            db.add(Unit(name=name, short_name=short_name, allows_decimal=allows_decimal))


def seed_settings(db: Session, store: Store) -> None:
    existing = set(db.scalars(select(AppSetting.key).where(AppSetting.store_id == store.id)))
    for key in SettingKey:
        if key.value not in existing:
            db.add(AppSetting(store_id=store.id, key=key.value, value=key.default, is_public=key.is_public))


def seed_categories(db: Session, store: Store) -> None:
    existing = set(db.scalars(select(Category.slug).where(Category.store_id == store.id)))
    for position, (name, punjabi) in enumerate(CATEGORIES.items()):
        slug = slugify(name)
        if slug not in existing:
            db.add(
                Category(
                    store_id=store.id, name=name, slug=slug, name_translations={"pa": punjabi}, sort_order=position
                )
            )


def run(db: Session) -> None:
    store = seed_store(db)
    seed_roles_and_permissions(db)
    seed_admin(db, store)
    seed_units(db)
    seed_settings(db, store)
    seed_categories(db, store)
    db.commit()
