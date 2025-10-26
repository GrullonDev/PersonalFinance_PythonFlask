import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configure environment for tests before importing application modules
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("ALLOW_TEST_TOKENS", "true")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_personal_finance.db")

from app.core.config import get_settings  # noqa: E402
from app.core.database import get_db, run_migrations  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def _settings() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    settings.ALLOW_TEST_TOKENS = True
    settings.ENVIRONMENT = "test"


@pytest.fixture(scope="session")
def db_engine(_settings):
    db_path = Path("test_personal_finance.db")
    if db_path.exists():
        db_path.unlink()

    run_migrations()

    engine = create_engine(
        os.environ["DATABASE_URL"],
        future=True,
        echo=False,
    )

    yield engine
    engine.dispose()
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()

    TestingSession = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )
    session = TestingSession()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
