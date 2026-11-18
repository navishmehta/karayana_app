"""Small text helpers."""

import re
import unicodedata


def slugify(value: str, fallback: str = "item") -> str:
    """'Cold Drinks!' -> 'cold-drinks'. Names in Gurmukhi only produce the fallback."""
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or fallback


def normalize_email(email: str) -> str:
    return email.strip().lower()
