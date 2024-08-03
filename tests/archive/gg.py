import pytest
from httpx import AsyncClient, ASGITransport
import asyncio

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from config import Settings
from app.utils.logging import setup_logging

from app.database import db_connect
from app.main import app

# ------------------------------
# Set up logging
# ------------------------------

logger = setup_logging()

# ------------------------------
# Set up test database connection
# ------------------------------

# Create an asynchronous test engine
test_engine = create_async_engine(
    Settings.TEST_DATABASE_URL, echo=False, pool_pre_ping=True
)

# Create an asynchronous test session
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# drop all database every time when test complete
@pytest.fixture(scope="session")
async def async_db_engine():
    async with test_engine.begin() as conn:
        await conn.run_sync(db_connect.Base.metadata.create_all)

    yield test_engine

    async with test_engine.begin() as conn:
        await conn.run_sync(db_connect.Base.metadata.create_all)


# truncate all table to isolate tests
@pytest.fixture(scope="function")
async def async_db(async_db_engine):

    async with TestingSessionLocal() as session:
        await session.begin()

        yield session

        await session.rollback()

        for table in reversed(db_connect.Base.metadata.sorted_tables):
            await session.execute(f"TRUNCATE {table.name} CASCADE;")
            await session.commit()


@pytest.fixture(scope="session")
async def async_client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# let test session to know it is running inside event loop
@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio(scope="session")
async def test_register_api_user(async_client):
    logger.info("!!!!!!!! Starting test_get_token")

    payload = {"username": Settings.API_ADM_USER, "password": Settings.API_ADM_PASSWORD}
    response = await async_client.post("/get-token", data=payload)
    assert response.status_code == 200
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    logger.info(f"!!!!!!!! Access Token received: {headers}")

    logger.info(f"Test Engine: {test_engine.url}")
    pending = asyncio.all_tasks()
    for task in pending:
        logger.info(f"Pending task at test end: {task}")

    logger.info("!!!!!!!! Starting test_register_api_user")

    # Prepare test data
    user_dat = {
        "username": Settings.TEST_USER,
        "password": Settings.TEST_PASSWORD,
        "is_admin": True,
    }
    # Send POST request to registration endpoint
    response = await async_client.post(
        "/register-api-user", json=user_data, headers=headers
    )
    assert response.status_code == 201
    assert "created successfully" in response.json()["message"]
    logger.info(f"!!!!!!!! Response register-api-user: {response.json()}")
