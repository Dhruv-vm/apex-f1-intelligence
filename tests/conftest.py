"""APEX — Pytest Configuration and Fixtures."""

import os
import sys
from typing import Generator

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from backend.config import Settings, get_settings
from backend.database import Base, get_db
from backend.main import create_app

# Test database: SQLite in-memory with StaticPool for fast, isolated testing
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def get_test_settings() -> Settings:
    return Settings(
        ENVIRONMENT="testing",
        DATABASE_URL=TEST_DATABASE_URL,
        ADMIN_API_KEY="test_admin_key_123",
        JOLPICA_BASE_URL="https://api.jolpi.ca/ergast/f1",
        OPENF1_BASE_URL="https://api.openf1.org/v1",
        JOLPICA_CACHE_DIR="./data/raw/jolpica",
        OPENF1_CACHE_DIR="./data/raw/openf1",
    )


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create database tables once for the test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Yield a database session and purge rows after each test for clean isolation."""
    session = TestingSessionLocal()
    yield session
    session.close()

    with test_engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """FastAPI TestClient with overridden get_db and settings dependencies."""
    app = create_app()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = get_test_settings

    with TestClient(app) as test_client:
        yield test_client
