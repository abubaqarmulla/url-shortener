import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database.database import Base, get_database
from app.cache.redis import redis_client
from contextlib import asynccontextmanager

@asynccontextmanager
async def test_lifespan(app):
    yield

TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def clear_rate_limit_keys():
    """
    Clear only rate-limit keys before every test.

    We intentionally do NOT flush the entire Redis database because
    URL cache and analytics click-counter data may also be stored there.
    """

    for key in redis_client.scan_iter(
        match="rate_limit:*"
    ):
        redis_client.delete(key)

    yield

    for key in redis_client.scan_iter(
        match="rate_limit:*"
    ):
        redis_client.delete(key)



@pytest.fixture
def client(monkeypatch):
    def override_get_database():
        database = TestingSessionLocal()

        try:
            yield database
        finally:
            database.close()

    app.dependency_overrides[get_database] = override_get_database

    monkeypatch.setattr(
        app.router,
        "lifespan_context",
        test_lifespan,
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
