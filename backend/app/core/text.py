"""Small text helpers."""

import re
import unicodedata

LIKE_ESCAPE = "\\"


def slugify(value: str, fallback: str = "item") -> str:
    """'Cold Drinks!' -> 'cold-drinks'. Names in Gurmukhi only produce the fallback."""
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug[:150].strip("-") or fallback


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _escape_like(term: str) -> str:
    return term.strip().replace(LIKE_ESCAPE, LIKE_ESCAPE * 2).replace("%", r"\%").replace("_", r"\_")


def like_contains(term: str) -> str:
    """'%term%' for LIKE, treating the user's % and _ as plain characters (use escape=LIKE_ESCAPE)."""
    return f"%{_escape_like(term)}%"


def like_prefix(term: str) -> str:
    return f"{_escape_like(term)}%"
