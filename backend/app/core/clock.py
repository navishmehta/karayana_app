"""Store-local time helpers.

The database stores UTC. Anything about "today" (expiry buckets, daily reports) must use
the store's timezone (Asia/Kolkata), otherwise dates are wrong between 00:00 and 05:30 IST.
"""

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.core.constants import DISPLAY_DATE_FORMAT


def store_tz() -> ZoneInfo:
    return ZoneInfo(get_settings().store_timezone)


def utc_now() -> datetime:
    """Naive UTC datetime, matching what is stored in DATETIME columns."""
    return datetime.now(UTC).replace(tzinfo=None)


def store_now() -> datetime:
    return datetime.now(store_tz())


def store_today() -> date:
    return store_now().date()


def to_store_time(value: datetime | None) -> datetime | None:
    """Stored (naive UTC) datetime -> aware datetime in store time, e.g. for API output (+05:30)."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(store_tz())


def format_display_date(value: date | datetime | None) -> str | None:
    """DD-MM-YYYY for exports and notification text."""
    return value.strftime(DISPLAY_DATE_FORMAT) if value else None
