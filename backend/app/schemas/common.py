"""Shared request/response building blocks."""

import re
from datetime import datetime
from decimal import Decimal
from typing import Annotated, TypeVar

from email_validator import EmailNotValidError, validate_email
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, PlainSerializer, StringConstraints

from app.core.clock import to_store_time
from app.core.config import get_settings
from app.core.constants import DEFAULT_PER_PAGE, EMAIL_MAX_LENGTH, MAX_PER_PAGE, NAME_MAX_LENGTH, PHONE_PATTERN
from app.core.money import money, quantity
from app.core.text import normalize_email

T = TypeVar("T")


class ApiModel(BaseModel):
    """Base for request bodies: unknown fields are rejected, text is trimmed."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


# --- Field types ---------------------------------------------------------------------------------


def _check_email(value: str) -> str:
    try:
        validate_email(value, check_deliverability=False, test_environment=not get_settings().is_production)
    except EmailNotValidError as exc:
        raise ValueError("validation.email") from exc
    return normalize_email(value)


def _check_locale(value: str) -> str:
    if value not in get_settings().supported_locales:
        raise ValueError("validation.locale_unsupported")
    return value


def _check_phone(value: str | None) -> str | None:
    if value and not re.fullmatch(PHONE_PATTERN, value):
        raise ValueError("validation.phone_invalid")
    return value or None


def _check_new_password(value: str) -> str:
    settings = get_settings()
    if len(value) < settings.password_min_length or not re.search(r"[A-Za-z]", value) or not re.search(r"\d", value):
        raise ValueError("validation.password_weak")
    return value


Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=NAME_MAX_LENGTH)]
Email = Annotated[str, StringConstraints(max_length=EMAIL_MAX_LENGTH), AfterValidator(_check_email)]
Phone = Annotated[str | None, AfterValidator(_check_phone)]
Locale = Annotated[str, AfterValidator(_check_locale)]
NewPassword = Annotated[str, StringConstraints(max_length=128), AfterValidator(_check_new_password)]

# Money always leaves the API as a string with 2 decimals ("285.00"), quantities with 3 ("1.250").
MoneyOut = Annotated[Decimal, PlainSerializer(lambda v: str(money(v)), return_type=str, when_used="json")]
QuantityOut = Annotated[Decimal, PlainSerializer(lambda v: str(quantity(v)), return_type=str, when_used="json")]

# Datetimes are stored in UTC and sent to clients in store time (+05:30).
StoreDateTime = Annotated[
    datetime, PlainSerializer(lambda v: to_store_time(v).isoformat(), return_type=str, when_used="json")
]


# --- Response envelopes ---------------------------------------------------------------------------


class DataResponse[T](BaseModel):
    data: T


class MessageResponse(BaseModel):
    message: str


class PageMeta(BaseModel):
    page: int
    per_page: int
    total: int
    last_page: int


class Page[T](BaseModel):
    data: list[T]
    meta: PageMeta


class PageParams(BaseModel):
    page: int = Field(1, ge=1)
    per_page: int = Field(DEFAULT_PER_PAGE, ge=1, le=MAX_PER_PAGE)
