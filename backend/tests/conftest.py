import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db, Base

# Uses a separate test DB on the same Postgres instance.
# Set TEST_DATABASE_URL env var to override (e.g. for CI).
import os

TEST_DB_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://library:library@db:5432/library_test",
)

engine = create_engine(TEST_DB_URL, pool_pre_ping=True)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def create_test_schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_tables():
    yield
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE borrowings, members, books RESTART IDENTITY CASCADE"))
        conn.commit()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
