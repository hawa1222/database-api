import pytest
from httpx import AsyncClient, ASGITransport
import asyncio

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Custom imports
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
        logger.info(f"Database connection picked from connection pool. "
                    f"Session ID: {session_id}")
        yield db
    finally:
        try:
            await db.close()
            logger.info(f"Database connection closed. Session ID: {session_id}")
        except RuntimeError as e:
            if "Event loop is closed" not in str(e):
                raise

app.dependency_overrides[db_connect.get_db] = override_get_db

# ------------------------------
# Test cases
# ------------------------------


@pytest.mark.asyncio(scope="session")
async def test_get_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_get_token')

        payload = {
            'username': Settings.API_ADM_USER,
            'password': Settings.API_ADM_PASSWORD
        }
        response = await client.post(
            '/get-token',
            data=payload
        )
        assert response.status_code == 200

        headers = {'Authorization': f'Bearer {response.json()['access_token']}'}
        logger.info(f'!!!!!!!! Headers: {headers}')

    logger.info(f'Test Engine: {test_engine.url}')

    pending = asyncio.all_tasks()
    for task in pending:
        logger.info(f'Pending task at test end: {task}')


@pytest.mark.asyncio(scope="session")
async def test_register_api_user():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_register_api_user')

        payload = {
            'username': Settings.API_ADM_USER,
            'password': Settings.API_ADM_PASSWORD,
        }
        response = await client.post('/get-token', data=payload)
        assert response.status_code == 200

        headers = {'Authorization': f'Bearer {response.json()['access_token']}'}
        logger.info(f'!!!!!!!! Headers: {headers}')

        # Prepare test data
        user_dat= {
            'username': Settings.TEST_USER,
            'password': Settings.TEST_PASSWORD,
            'is_admin': True
        }
        # Send POST request to registration endpoint
        response = await client.post(
            '/register-api-user',
            json=user_data,
            headers=headers
        )
        assert response.status_code == 201
        assert 'created successfully' in response.json()['message']
        logger.info(f'!!!!!!!! Response register-api-user: {response.json()}')


@pytest.mark.asyncio(scope="session")
async def test_create_db():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_create_db')

        payload = {
            'username': Settings.API_ADM_USER,
            'password': Settings.API_ADM_PASSWORD
        }
        response = await client.post('/get-token', data=payload)
        assert response.status_code == 200

        headers = {'Authorization': f'Bearer {response.json()['access_token']}'}
        logger.info(f'!!!!!!!! Headers: {headers}')

        payload = {'db_name': Settings.TEST_DB_NAME}
        response = await client.post(
            '/create-database',
            json=payload,
            headers=headers
        )
        logger.info(f'!!!!!!!! Response: {response}')
        assert response.status_code == 201
        assert 'created successfully' in response.json()['message']
        logger.info(f'!!!!!!!! Response create-database: {response.json()}')


@pytest.mark.asyncio(scope="session")
async def test_create_db_user():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_create_db_user')

        payload = {
            'username': Settings.API_ADM_USER,
            'password': Settings.API_ADM_PASSWORD
        }
        response = await client.post('/get-token', data=payload)
        assert response.status_code == 200

        headers = {'Authorization': f'Bearer {response.json()['access_token']}'}
        logger.info(f'!!!!!!!! Headers: {headers}')

        payload = {
            'host': Settings.MYSQL_HOST,
            'username': Settings.TEST_USER,
            'password': Settings.TEST_PASSWORD,
            'db_name': Settings.TEST_DB_NAME,
            'privileges': 'SELECT'
        }
        response = await client.post(
            '/create-db-user',
            json=payload,
            headers=headers
        )
        assert response.status_code == 201
        assert 'created successfully' in response.json()['message']
        logger.info(f'!!!!!!!! Response create-db-user: {response.json()}')


@pytest.mark.asyncio(scope="session")
async def test_create_table():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_create_table')

        payload = {
            'username': Settings.API_ADM_USER,
            'password': Settings.API_ADM_PASSWORD
        }
        response = await client.post('/get-token', data=payload)
        assert response.status_code == 200

        headers = {'Authorization': f'Bearer {response.json()['access_token']}'}
        logger.info(f'!!!!!!!! Headers: {headers}')

        payload = {
            'db_name': Settings.TEST_DB_NAME,
            'table_name': Settings.TEST_TABLE_NAME,
            'table_schema': {
                'id': 'INT PRIMARY KEY',
                'name': 'VARCHAR(50)',
                'age': 'INT'
            }
        }
        response = await client.post(
            '/create-table',
            json=payload,
            headers=headers
        )
        assert response.status_code == 201
        assert 'created successfully' in response.json()['message']
        logger.info(f'!!!!!!!! Response create-table: {response.json()}')


@pytest.mark.asyncio(scope="session")
async def test_insert_data():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_insert_data')

        payload = {
            'username': Settings.API_ADM_USER,
            'password': Settings.API_ADM_PASSWORD
        }
        response = await client.post('/get-token', data=payload)
        assert response.status_code == 200

        headers = {'Authorization': f'Bearer {response.json()["access_token"]}'}
        logger.info(f'!!!!!!!! Headers: {headers}')

        payload = {
            'db_name': Settings.TEST_DB_NAME,
            'table_name': Settings.TEST_TABLE_NAME,
            'data': [
                {
                    'id': 1,
                    'name': 'John Doe',
                    'age': 25
                },
                {
                    'id': 2,
                    'name': 'Jane Smith',
                    'age': 30
                }
            ]
        }
        response = await client.post(
            '/insert-data',
            json=payload,
            headers=headers
        )
        assert response.status_code == 201
        assert 'Datinsertion completed' in response.json()['message']
        logger.info(f'!!!!!!!! Response insert-data: {response.json()}')
