import pytest
from httpx import ASGITransport
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker

from app.database import db_connect
from app.main import app
from app.utils.logging import setup_logging

# Custom imports
from config import Settings

# ------------------------------
# Set up logging
# ------------------------------

logger = setup_logging()

# ------------------------------
# Set up test database connection
# ------------------------------

# Create an asynchronous test engine
test_engine = create_async_engine(Settings.TEST_DATABASE_URL, echo=False, pool_pre_ping=True)

# Create an asynchronous test session
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine, class_=AsyncSession
)

# ------------------------------
# Override dependency
# ------------------------------


# Dependency to get database connection
async def override_get_db():
    db = TestingSessionLocal()
    session_id = hash(db)
    try:
        logger.info(
            f'Database connection picked from connection pool. ' f'Session ID: {session_id}'
        )
        yield db
    finally:
        try:
            await db.close()
            logger.info(f'Database connection closed. Session ID: {session_id}')
        except RuntimeError as e:
            if 'Event loop is closed' not in str(e):
                raise


app.dependency_overrides[db_connect.get_db] = override_get_db


# ------------------------------
# Payloads
# ------------------------------


@pytest.fixture
def create_table_payload(request):
    payload = {
        'db_name': Settings.TEST_DB_NAME,
        'table_name': Settings.TEST_TABLE_NAME,
        'table_schema': {'id': 'INT PRIMARY KEY', 'name': 'VARCHAR(50)', 'age': 'INT'},
    }

    if hasattr(request, 'param'):
        payload.update(request.param)

    return payload


@pytest.fixture
def insert_data_payload(request):
    payload = {
        'db_name': Settings.TEST_DB_NAME,
        'table_name': Settings.TEST_TABLE_NAME,
        'data': [
            {'id': 1, 'name': 'John Doe', 'age': 25},
            {'id': 2, 'name': 'Jane Smith', 'age': 30},
        ],
    }

    if hasattr(request, 'param'):
        payload.update(request.param)

    return payload


@pytest.fixture
def db_user_payload():
    payload = {
        'host': Settings.MYSQL_HOST,
        'username': Settings.TEST_USER,
        'password': Settings.TEST_PASSWORD,
        'db_name': Settings.TEST_DB_NAME,
        'privileges': 'SELECT',
    }

    return payload


@pytest.fixture
def api_admin_user_payload(request):
    payload = {
        'username': Settings.API_ADM_USER,
        'password': Settings.API_ADM_PASSWORD,
        'is_admin': True,
    }

    if hasattr(request, 'param'):
        payload.update(request.param)

    return payload


@pytest.fixture
def api_non_admin_user_payload():
    payload = {
        'username': Settings.TEST_USER,
        'password': Settings.TEST_PASSWORD,
        'is_admin': False,
    }

    return payload


# ------------------------------
# Fixtures
# ------------------------------


@pytest.fixture
async def access_token(api_admin_user_payload):
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        logger.disabled = True  # Disable logger
        logger.info('-------> Getting access_token')
        response = await client.post('/get-token', data=api_admin_user_payload)
        headers = {'Authorization': f'Bearer {response.json()['access_token']}'}
        logger.info(f'-------> Access Token received: {headers}')
        logger.disabled = False  # Enable logger
    return headers


@pytest.fixture
async def non_admin_access_token(access_token, api_non_admin_user_payload):
    logger.disabled = True  # Disable logger
    headers = await access_token
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        logger.disabled = True  # Disable logger
        logger.info('-------> Getting non_admin_access_token')
        response = await client.post(
            '/register-api-user', json=api_non_admin_user_payload, headers=headers
        )
        response = await client.post('/get-token', data=api_non_admin_user_payload)
        headers = {'Authorization': f'Bearer {response.json()['access_token']}'}
        logger.info(f'-------> Non-Admin Access Token received: {headers}')
        logger.disabled = False  # Enable logger
        return headers
