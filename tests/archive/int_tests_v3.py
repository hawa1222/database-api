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
        logger.info(f'Database connection picked from connection pool. '
                    f'Session ID: {session_id}')
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
# Fixtures
# ------------------------------


@pytest.fixture
async def access_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.disabled = True  # Disable logger
        logger.info('-------> Getting access_token')
        payload = {
            'username': Settings.API_ADM_USER,
            'password': Settings.API_ADM_PASSWORD
        }
        response = await client.post(
            '/get-token',
            data=payload
        )
        headers = {'Authorization': f'Bearer {response.json()['access_token']}'}
        logger.info(f'-------> Access Token received: {headers}')
        logger.disabled = False  # Enable logger
    return headers


@pytest.fixture
async def non_admin_access_token(access_token):
    logger.disabled = True  # Disable logger
    headers = await access_token
    logger.disabled = False  # Enable logger
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.disabled = True  # Disable logger
        logger.info('-------> Getting non_admin_access_token')
        user_dat= {
            'username': Settings.TEST_USER,
            'password': Settings.TEST_PASSWORD,
            'is_admin': False
        }
        response = await client.post(
            '/register-api-user',
            json=user_data,
            headers=headers
        )
        payload = {
            'username': Settings.TEST_USER,
            'password': Settings.TEST_PASSWORD
        }
        response = await client.post(
            '/get-token',
            data=payload
        )
        headers = {'Authorization': f'Bearer {response.json()['access_token']}'}
        logger.info(f'-------> Non-Admin Access Token received: {headers}')
        logger.disabled = False  # Enable logger
        return headers


# ------------------------------
# API Token Tests
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


@pytest.mark.asyncio(scope='session')
async def test_get_token_user_fail():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_get_token_user_fail')
        payload = {
            'username': Settings.TEST_DB_NAME,
            'password': Settings.API_ADM_PASSWORD
        }
        response = await client.post(
            '/get-token',
            data=payload
        )
        assert response.status_code == 401
        assert 'not found' in response.json()['detail']
        logger.info(f'!!!!!!!! Response test_get_token_user_fail: {response.json()}')


@pytest.mark.asyncio(scope='session')
async def test_get_token_pw_fail():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_get_token_pw_fail')
        payload = {
            'username': Settings.API_ADM_USER,
            'password': Settings.TEST_DB_NAME
        }
        response = await client.post(
            '/get-token',
            data=payload
        )
        assert response.status_code == 403
        assert 'Invalid password' in response.json()['detail']
        logger.info(f'!!!!!!!! Response test_get_token_pw_fail: {response.json()}')


# ------------------------------
# Register API User Tests
# ------------------------------


@pytest.mark.asyncio(scope="session")
async def test_register_api_user(access_token):
    headers = await access_token
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_register_api_user')
        # Prepare test data
        user_dat= {
            'username': Settings.TEST_USER,
            'password': Settings.TEST_PASSWORD,
            'is_admin': False
        }
        # Send POST request to registration endpoint
        response = await client.post(
            '/register-api-user',
            json=user_data,
            headers=headers
        )
        assert response.status_code == 201
        assert 'created successfully' in response.json()['message']
        logger.info(f'!!!!!!!! Response test_register_api_user: {response.json()}')


@pytest.mark.asyncio(scope='session')
async def test_register_dup_api_user(access_token):
    headers = await access_token
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_register_dup_api_user')
        # Prepare test data
        user_dat= {
            'username': Settings.TEST_USER,
            'password': Settings.TEST_PASSWORD,
            'is_admin': False
        }
        # Send POST request to registration endpoint
        response = await client.post(
            '/register-api-user',
            json=user_data,
            headers=headers
        )
        assert response.status_code == 400
        assert 'already registered' in response.json()['detail']
        logger.info(f'!!!!!!!! Response test_register_dup_api_user: {response.json()}')


@pytest.mark.asyncio(scope='session')
async def test_non_auth_register_api_user(non_admin_access_token):
    headers = await non_admin_access_token
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_non_auth_register_api_user')
        # Prepare test data
        user_dat= {
            'username': Settings.TEST_USER,
            'password': Settings.TEST_PASSWORD,
            'is_admin': False
        }
        # Send POST request to registration endpoint
        response = await client.post(
            '/register-api-user',
            json=user_data,
            headers=headers
        )
        assert response.status_code == 403
        assert 'Unauthorised access' in response.json()['detail']
        logger.info(f'!!!!!!!! Response test_non_auth_register_api_user: {response.json()}')

# ------------------------------
# Create Database Tests
# ------------------------------


@pytest.mark.asyncio(scope='session')
async def test_create_db(access_token):
    headers = await access_token
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_create_db')
        payload = {'db_name': Settings.TEST_DB_NAME}
        response = await client.post(
            '/create-database',
            json=payload,
            headers=headers
        )
        assert response.status_code == 201
        assert 'created successfully' in response.json()['message']
        logger.info(f'!!!!!!!! Response test_create_db: {response.json()}')


@pytest.mark.asyncio(scope='session')
async def test_non_admin_create_db(non_admin_access_token):
    headers = await non_admin_access_token
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_non_admin_create_db')
        payload = {'db_name': Settings.TEST_DB_NAME_2}
        response = await client.post(
            '/create-database',
            json=payload,
            headers=headers
        )
        assert response.status_code == 201
        assert 'created successfully' in response.json()['message']
        logger.info(f'!!!!!!!! Response test_non_admin_create_db: {response.json()}')


@pytest.mark.asyncio(scope='session')
async def test_create_dup_db(access_token):
    headers = await access_token
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_create_dup_db')
        payload = {'db_name': Settings.TEST_DB_NAME}
        response = await client.post(
            '/create-database',
            json=payload,
            headers=headers
        )
        assert response.status_code == 400
        assert 'already exists' in response.json()['detail']
        logger.info(f'!!!!!!!! Response test_create_dup_db: {response.json()}')


# ------------------------------
# Create Database User Tests
# ------------------------------


@pytest.mark.asyncio(scope='session')
async def test_create_db_user(access_token):
    headers = await access_token
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_create_db_user')
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
        logger.info(f'!!!!!!!! Response test_create_db_user: {response.json()}')


@pytest.mark.asyncio(scope='session')
async def test_create_user_already_exists(access_token):
    headers = await access_token
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_create_user_already_exists')
        payload = {
            'host': Settings.MYSQL_HOST,
            'username': Settings.TEST_USER,
            'password': Settings.TEST_PASSWORD,
            'db_name': Settings.TEST_DB_NAME,
            'privileges': 'ALL'
        }
        response = await client.post(
            '/create-db-user',
            json=payload,
            headers=headers
        )
        assert response.status_code == 201
        assert 'already exists' in response.json()['message']
        logger.info(f'!!!!!!!! Response test_create_user_already_exists: {response.json()}')


@pytest.mark.asyncio(scope='session')
async def test_create_user_invalid_privileges(non_admin_access_token):
    headers = await non_admin_access_token
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_create_user_invalid_privileges')
        payload = {
            'host': Settings.MYSQL_HOST,
            'username': Settings.TEST_USER,
            'password': Settings.TEST_PASSWORD,
            'db_name': Settings.TEST_DB_NAME,
            'privileges': 'ALL'
        }
        response = await client.post(
            '/create-db-user',
            json=payload,
            headers=headers
        )
        assert response.status_code == 403
        assert 'Unauthorised access' in response.json()['detail']
        logger.info(f'!!!!!!!! Response test_create_user_invalid_privileges: {response.json()}')


# ------------------------------
# Create Table Tests
# ------------------------------


@pytest.mark.asyncio(scope='session')
async def test_create_table(access_token):
    headers = await access_token
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_create_table')
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


@pytest.mark.asyncio(scope='session')
async def test_create_table_already_exists(access_token):
    headers = await access_token
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_create_table_already_exists')
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
        assert response.status_code == 400
        assert 'already exists' in response.json()['detail']
        logger.info(f'!!!!!!!! Response test_create_table_already_exists: {response.json()}')


@pytest.mark.asyncio(scope='session')
async def test_create_table_invalid_schema(access_token):
    headers = await access_token
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_create_table_invalid_schema')
        payload = {
            'db_name': Settings.TEST_DB_NAME,
            'table_name': 'invalid_table',
            'table_schema': {
                'id': 'INVALID_TYPE',
                'name': 'VARCHAR(50)',
                'age': 'INT'
            }
        }
        response = await client.post(
            '/create-table',
            json=payload,
            headers=headers
        )
        assert response.status_code == 500
        assert 'Error creating table' in response.json()['detail']
        logger.info(f'!!!!!!!! Response test_create_table_invalid_schema: {response.json()}')


# ------------------------------
# Insert DatTests
# ------------------------------

@pytest.mark.asyncio(scope='session')
async def test_insert_data(access_token):
    headers = await access_token
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_insert_data')
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
        logger.info(f'!!!!!!!! Response test_insert_data: {response.json()}')


@pytest.mark.asyncio(scope='session')
async def test_insert_data_table_not_exists(access_token):
    headers = await access_token
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_insert_data_table_not_exists')
        payload = {
            'db_name': Settings.TEST_DB_NAME,
            'table_name': 'nonexistent_table',
            'data': [
                {
                    'id': 1,
                    'name': 'John Doe',
                    'age': 25
                }
            ]
        }
        response = await client.post(
            '/insert-data',
            json=payload,
            headers=headers
        )
        assert response.status_code == 404
        assert 'doesn\'t exist' in response.json()['detail']
        logger.info(f'!!!!!!!! Response insert-dat(table not exists): {response.json()}')


@pytest.mark.asyncio(scope='session')
async def test_insert_data_invalid_data(access_token):
    headers = await access_token
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_insert_data_invalid_data')
        payload = {
            'db_name': Settings.TEST_DB_NAME,
            'table_name': Settings.TEST_TABLE_NAME,
            'data': [
                {
                    'id': 'invalid_id',
                    'name': 'John Doe',
                    'age': 25
                }
            ]
        }
        response = await client.post(
            '/insert-data',
            json=payload,
            headers=headers
        )
        assert response.status_code == 500
        assert 'Error during datinsertion' in response.json()['detail']
        logger.info(f'!!!!!!!! Response insert-dat(invalid data): {response.json()}')


# ------------------------------
# Get Table Tests
# ------------------------------

@pytest.mark.asyncio(scope='session')
async def test_get_table(access_token):
    headers = await access_token
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_get_table')
        response = await client.get(
            f'/get-table/{Settings.TEST_DB_NAME}/{Settings.TEST_TABLE_NAME}',
            headers=headers
        )
        assert response.status_code == 200
        logger.info(f'!!!!!!!! Response test_get_table: {response.json()}')


@pytest.mark.asyncio(scope='session')
async def test_get_table_not_exists(access_token):
    headers = await access_token
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_get_table_not_exists')
        response = await client.get(
            f'/get-table/{Settings.TEST_DB_NAME}/nonexistent_table',
            headers=headers
        )
        assert response.status_code == 404
        assert 'does not exist' in response.json()['detail']
        logger.info(f'!!!!!!!! Response test_get_table_not_exists: {response.json()}')


# ------------------------------
# Delete Table Tests
# ------------------------------


@pytest.mark.asyncio(scope='session')
async def test_delete_table(access_token):
    headers = await access_token
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_delete_table')
        response = await client.delete(
            f'/delete-table/{Settings.TEST_DB_NAME}/{Settings.TEST_TABLE_NAME}',
            headers=headers
        )
        assert response.status_code == 200
        assert 'deleted successfully' in response.json()['message']
        logger.info(f'!!!!!!!! Response test_delete_table): {response.json()}')


@pytest.mark.asyncio(scope='session')
async def test_delete_table_not_exists(access_token):
    headers = await access_token
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_delete_table_not_exists')

        response = await client.delete(
            f'/delete-table/{Settings.TEST_DB_NAME}/nonexistent_table',
            headers=headers
        )
        assert response.status_code == 404
        assert 'does not exist' in response.json()['detail']
        logger.info(f'!!!!!!!! Response test_delete_table_not_exists: {response.json()}')