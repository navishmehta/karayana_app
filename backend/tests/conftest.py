"""Test setup: a real MySQL test database (CHECK constraints and generated columns must behave like production).

Schema is rebuilt once per run with Alembic; each test runs inside a transaction that is rolled back.
"""

import os
import tempfile

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "mysql+pymysql://kirana:kirana_local_pw@127.0.0.1:3306/kirana_test"
)
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "false"  # like production: no internal details in errors
os.environ["ADMIN_EMAIL"] = "admin@kirana.test"
os.environ["ADMIN_PASSWORD"] = "Admin12345"
os.environ["JWT_SECRET"] = "test-secret-not-for-production-0123456789abcdef"
os.environ["MAIL_DRIVER"] = "log"
os.environ["MEDIA_ROOT"] = tempfile.mkdtemp(prefix="kirana-media-")  # uploads never touch the real folder

from collections.abc import Iterator  # noqa: E402

import pytest  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from alembic import command  # noqa: E402
from app.core.database import engine, get_db  # noqa: E402
from app.core.rate_limit import rate_limiter  # noqa: E402
from app.db import seed  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import Base  # noqa: E402
from app.services.mail import LogMailer  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _schema() -> Iterator[None]:
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f"DROP TABLE IF EXISTS `{table.name}`"))
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    command.upgrade(Config("alembic.ini"), "head")
    yield


@pytest.fixture
def db() -> Iterator[Session]:
    """Session whose commits become savepoints inside an outer transaction that is always rolled back."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def seeded_db(db: Session) -> Session:
    seed.run(db)
    return db


@pytest.fixture(autouse=True)
def _reset_shared_state() -> Iterator[None]:
    rate_limiter.reset()
    LogMailer.outbox.clear()
    yield


@pytest.fixture
def client(seeded_db: Session) -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_db] = lambda: seeded_db
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
