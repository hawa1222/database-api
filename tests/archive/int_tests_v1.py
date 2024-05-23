import pytest
from httpx import AsyncClient
import asyncio

# Custom imports
from config import Settings
from app.utils.logging import setup_logging

from app.main import app

# ------------------------------
# Constants
# ------------------------------

TEST_USER = 'testing'
TEST_PASSWORD = 'testing'
TEST_DB_NAME = 'testdb'
TEST_TABLE_NAME = 'users'

# ------------------------------
# Set up logging
# ------------------------------

logger = setup_logging()

# ------------------------------
# Set test client
# ------------------------------

# client = TestClient(app)


# ------------------------------
# Test cases
# ------------------------------


@pytest.mark.asyncio(scope="session")
async def test_get_token():
    async with AsyncClient(app=app, base_url="http://test") as client:
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

    # Close AsyncClient
    await client.aclose()

    pending = asyncio.all_tasks()
    for task in pending:
        logger.info(f'Pending task at test end: {task}')


@pytest.mark.asyncio(scope="session")
async def test_register_api_user():
    async with AsyncClient(app=app, base_url="http://test") as client:
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
            'username': TEST_USER,
            'password': TEST_PASSWORD,
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
    async with AsyncClient(app=app, base_url="http://test") as client:
        logger.info('!!!!!!!! Starting test_create_db')

        payload = {
            'username': Settings.API_ADM_USER,
            'password': Settings.API_ADM_PASSWORD
        }
        response = await client.post('/get-token', data=payload)
        assert response.status_code == 200

        headers = {'Authorization': f'Bearer {response.json()['access_token']}'}
        logger.info(f'!!!!!!!! Headers: {headers}')

        payload = {'db_name': TEST_DB_NAME}
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
    async with AsyncClient(app=app, base_url='http://test') as client:
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
            'host': 'localhost',
            'username': TEST_USER,
            'password': TEST_PASSWORD,
            'db_name': TEST_DB_NAME,
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
    async with AsyncClient(app=app, base_url='http://test') as client:
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
            'db_name': TEST_DB_NAME,
            'table_name': TEST_TABLE_NAME,
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
    async with AsyncClient(app=app, base_url='http://test') as client:
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
            'db_name': TEST_DB_NAME,
            'table_name': TEST_TABLE_NAME,
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
