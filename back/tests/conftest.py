import os
import sys

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

BACK_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACK_DIR not in sys.path:
    sys.path.insert(0, BACK_DIR)

# Tests run against a real Postgres instance (same engine/driver as prod) rather
# than SQLite, so they exercise the actual DATABASE_URL code path. Uses a
# separate database on the same server so it never touches dev data.
PG_HOST = os.environ.get("TEST_PG_HOST", "localhost")
PG_PORT = os.environ.get("TEST_PG_PORT", "5432")
PG_USER = os.environ.get("TEST_PG_USER", "pool_play")
PG_PASSWORD = os.environ.get("TEST_PG_PASSWORD", "pool_play")
TEST_DB_NAME = os.environ.get("TEST_PG_DB", "pool_play_test")

ADMIN_URL = f"postgresql+psycopg://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_USER}"
TEST_DATABASE_URL = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{TEST_DB_NAME}"

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ["DATABASE_URL"] = TEST_DATABASE_URL


def _ensure_test_database():
    admin_engine = create_engine(ADMIN_URL, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": TEST_DB_NAME},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    except OperationalError:
        pytest.exit(
            f"Could not reach Postgres at {PG_HOST}:{PG_PORT} — start it with "
            "`docker compose up -d postgres` before running tests.",
            returncode=1,
        )
    finally:
        admin_engine.dispose()


_ensure_test_database()

from database.db import engine as test_engine  # noqa: E402
from database.models import Base  # noqa: E402

Base.metadata.create_all(test_engine)

_TABLES_IN_FK_ORDER = (
    "team_golfers", "teams", "golfers",
    "password_reset_tokens", "users", "tournament_settings",
)


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    with test_engine.begin() as conn:
        for table in _TABLES_IN_FK_ORDER:
            conn.execute(text(f'TRUNCATE TABLE "{table}" RESTART IDENTITY CASCADE'))
