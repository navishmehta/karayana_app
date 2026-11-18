from datetime import timedelta

import pytest

from app.core.clock import store_now
from app.core.i18n import negotiate_locale, t
from app.core.text import normalize_email, slugify
from app.enums.error_code import ErrorCode
from app.enums.permission import Permission
from app.enums.setting_key import SettingKey


@pytest.mark.parametrize(
    ("header", "expected"),
    [(None, "en"), ("pa", "pa"), ("pa-IN", "pa"), ("en;q=0.5, pa;q=0.9", "pa"), ("fr, de", "en"), ("hi", "en")],
)
def test_locale_negotiation(header: str | None, expected: str) -> None:
    assert negotiate_locale(header) == expected


def test_translation_fallback_and_params() -> None:
    assert t("validation.missing", locale="pa", attribute="ਨਾਮ") == "ਨਾਮ ਭਰਨਾ ਲਾਜ਼ਮੀ ਹੈ।"
    assert t("does.not.exist") == "does.not.exist"


def test_every_error_code_has_both_translations() -> None:
    for code in ErrorCode:
        for locale in ("en", "pa"):
            assert t(f"errors.{code.value.lower()}", locale=locale) != f"errors.{code.value.lower()}", (code, locale)


def test_every_permission_has_both_labels() -> None:
    for permission in Permission:
        for locale in ("en", "pa"):
            assert t(f"permissions.{permission.value}", locale=locale) != f"permissions.{permission.value}"


def test_store_clock_is_india_time() -> None:
    assert store_now().utcoffset() == timedelta(hours=5, minutes=30)


def test_slugify_and_email_normalisation() -> None:
    assert slugify("Cold Drinks!") == "cold-drinks"
    assert slugify("ਡੇਅਰੀ") == "item"
    assert normalize_email("  Admin@Example.COM ") == "admin@example.com"


def test_add_products_is_admin_only() -> None:
    assert not Permission.PRODUCTS_CREATE.is_grantable_to_sellers
    assert Permission.PRODUCTS_CREATE not in Permission.grantable()
    assert len(Permission.grantable()) == len(Permission) - 1


def test_dependencies_are_transitive() -> None:
    assert Permission.STOCK_UPDATE.all_dependencies() == [Permission.STOCK_VIEW, Permission.PRODUCTS_VIEW]
    missing = Permission.missing_dependencies({Permission.STOCK_UPDATE})
    assert missing == {Permission.STOCK_UPDATE: [Permission.STOCK_VIEW, Permission.PRODUCTS_VIEW]}
    assert (
        Permission.missing_dependencies({Permission.STOCK_UPDATE, Permission.STOCK_VIEW, Permission.PRODUCTS_VIEW})
        == {}
    )


def test_store_name_setting_defaults_to_configured_name_and_is_public() -> None:
    assert SettingKey.STORE_NAME.default == "Ramesh Karayana Store"
    assert SettingKey.STORE_NAME.is_public
    assert not SettingKey.DEFAULT_MIN_STOCK.is_public
