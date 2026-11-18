"""Translations for API messages (errors, validation, notifications).

Messages live in app/locales/<locale>.json as nested keys, e.g. t("errors.not_found").
The request language comes from the Accept-Language header (see LocaleMiddleware).
Missing keys fall back to the default locale, then to the key itself.
"""

import json
from contextvars import ContextVar
from functools import cache
from pathlib import Path
from typing import Any

from app.core.config import get_settings

LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"

_current_locale: ContextVar[str] = ContextVar("current_locale", default="en")


@cache
def _load(locale: str) -> dict[str, Any]:
    path = LOCALES_DIR / f"{locale}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _lookup(messages: dict[str, Any], key: str) -> str | None:
    node: Any = messages
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node if isinstance(node, str) else None


def set_locale(locale: str) -> None:
    _current_locale.set(locale)


def get_locale() -> str:
    return _current_locale.get()


def t(key: str, locale: str | None = None, **params: Any) -> str:
    """Translate `key` and fill {placeholders} from params."""
    locale = locale or get_locale()
    default = get_settings().default_locale
    text = _lookup(_load(locale), key) or _lookup(_load(default), key) or key
    try:
        return text.format(**params)
    except (KeyError, IndexError):
        return text


def has_key(key: str, locale: str | None = None) -> bool:
    return _lookup(_load(locale or get_locale()), key) is not None


def negotiate_locale(accept_language: str | None) -> str:
    """Pick the best supported locale from an Accept-Language header ('pa-IN,pa;q=0.9,en;q=0.8')."""
    settings = get_settings()
    if not accept_language:
        return settings.default_locale

    candidates: list[tuple[float, str]] = []
    for part in accept_language.split(","):
        pieces = part.strip().split(";")
        lang = pieces[0].strip().lower()
        quality = 1.0
        for piece in pieces[1:]:
            if piece.strip().startswith("q="):
                try:
                    quality = float(piece.strip()[2:])
                except ValueError:
                    quality = 0.0
        candidates.append((quality, lang))

    for _, lang in sorted(candidates, key=lambda c: c[0], reverse=True):
        base = lang.split("-")[0]
        if base in settings.supported_locales:
            return base
    return settings.default_locale
