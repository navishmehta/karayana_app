"""Database engine and session handling."""

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def build_engine(url: str | None = None) -> Engine:
    settings = get_settings()
    engine = create_engine(
        url or settings.database_url,
        echo=settings.database_echo,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

    # All timestamps are stored in UTC; "today" for the shop is computed in core/clock.py.
    @event.listens_for(engine, "connect")
    def _set_utc(dbapi_connection, _record):  # noqa: ANN001
        with dbapi_connection.cursor() as cursor:
            cursor.execute("SET time_zone = '+00:00'")

    return engine


engine = build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one session per request."""
    with SessionLocal() as session:
        yield session
