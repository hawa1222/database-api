# test_main.py

import pytest
from httpx import AsyncClient, ASGITransport

# Custom imports
from config import Settings
from app.utils.logging import setup_logging

from app.main import app

# ------------------------------
# Set up logging
# ------------------------------

logger = setup_logging()

# ------------------------------
# API Token Tests
# ------------------------------


@pytest.mark.asyncio(scope="session")
async def test_get_token(api_admin_user_payload):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        logger.info('!!!!!!!! Starting test_get_token')
        response = await client.post(
            '/get-token',
            data=api_admin_user_payload
        )
        assert response.status_code == 200
        headers = {
            'Authorization': f'Bearer {response.json()['access_token']}'
        }
        logger.info(f'!!!!!!!! Headers: {headers}')


@pytest.mark.asyncio(scope='session')
@pytest.mark.parametrize(
    'api_admin_user_payload',
    [{'username': 'invalid'}],
    indirect=True
)
async def test_invalid_usr_token(api_admin_user_payload):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        logger.info('!!!!!!!! Starting test_invalid_usr_token')
        response = await client.post(
            '/get-token',
            data=api_admin_user_payload
        )
        assert response.status_code == 401
        assert 'Invalid username or password' in response.json()['detail']
        logger.info(
            f'!!!!!!!! Response test_invalid_usr_token: {response.json()}'
        )


@pytest.mark.asyncio(scope='session')
@pytest.mark.parametrize(
    'api_admin_user_payload',
    [{'password': 'invalid'}],
    indirect=True
)
async def test_invalid_pwd_token(api_admin_user_payload):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        logger.info('!!!!!!!! Starting test_invalid_pwd_token')
        response = await client.post(
            '/get-token',
            data=api_admin_user_payload
        )
        assert response.status_code == 401
        assert 'Invalid username or password' in response.json()['detail']
        logger.info(
            f'!!!!!!!! Response test_invalid_pwd_token: {response.json()}'
        )


# ------------------------------
# Register API User Tests
# ------------------------------


@pytest.mark.asyncio(scope="session")
async def test_register_api_user(access_token, api_non_admin_user_payload):
    headers = await access_token
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        logger.info('!!!!!!!! Starting test_register_api_user')
        # Send POST request to registration endpoint
        response = await client.post(
            '/register-api-user',
            json=api_non_admin_user_payload,
            headers=headers
        )
        assert response.status_code == 201
        assert 'created successfully' in response.json()['message']
        logger.info(
            f'!!!!!!!! Response test_register_api_user: {response.json()}'
        )


@pytest.mark.asyncio(scope='session')
async def test_dup_usr_reg(access_token, api_non_admin_user_payload):
    headers = await access_token
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        logger.info('!!!!!!!! Starting test_dup_usr_reg')
        # Send POST request to registration endpoint
        response = await client.post(
            '/register-api-user',
            json=api_non_admin_user_payload,
            headers=headers
        )
        assert response.status_code == 400
        assert 'already registered' in response.json()['detail']
        logger.info(
            f'!!!!!!!! Response test_dup_usr_reg: {response.json()}'
        )


@pytest.mark.asyncio(scope='session')
async def test_unauth_usr_reg(
    non_admin_access_token,
    api_non_admin_user_payload
):
    headers = await non_admin_access_token
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        logger.info('!!!!!!!! Starting test_unauth_usr_reg')
        # Send POST request to registration endpoint
        response = await client.post(
            '/register-api-user',
            json=api_non_admin_user_payload,
            headers=headers
        )
        assert response.status_code == 403
        assert 'Unauthorised access' in response.json()['detail']
        logger.info(
            f'!!!!!!!! Response test_unauth_usr_reg: {response.json()}'
        )

# ------------------------------
# Create Database Tests
# ------------------------------


@pytest.mark.asyncio(scope='session')
async def test_create_db(access_token):
    headers = await access_token
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        logger.info('!!!!!!!! Starting test_create_db')
        response = await client.post(
            '/create-database',
            json={'db_name': Settings.TEST_DB_NAME},
            headers=headers
        )
        assert response.status_code == 201
        assert 'created successfully' in response.json()['message']
        logger.info(f'!!!!!!!! Response test_create_db: {response.json()}')


@pytest.mark.asyncio(scope='session')
async def test_create_dup_db(access_token):
    headers = await access_token
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        logger.info('!!!!!!!! Starting test_create_dup_db')
        response = await client.post(
            '/create-database',
            json={'db_name': Settings.TEST_DB_NAME},
            headers=headers
        )
        assert response.status_code == 400
        assert 'already exists' in response.json()['detail']
        logger.info(f'!!!!!!!! Response test_create_dup_db: {response.json()}')


@pytest.mark.asyncio(scope='session')
async def test_create_db_2(access_token):
    headers = await access_token
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        logger.info('!!!!!!!! Starting test_create_db_2')
        response = await client.post(
            '/create-database',
            json={'db_name': Settings.TEST_DB_NAME_2},
            headers=headers
        )
        assert response.status_code == 201
        assert 'created successfully' in response.json()['message']
        logger.info(f'!!!!!!!! Response test_create_db_2: {response.json()}')


@pytest.mark.asyncio(scope='session')
async def test_non_admin_create_db(non_admin_access_token):
    headers = await non_admin_access_token
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        logger.info('!!!!!!!! Starting test_non_admin_create_db')
        response = await client.post(
            '/create-database',
            json={'db_name': Settings.TEST_DB_NAME_2},
            headers=headers
        )
        assert response.status_code == 403
        assert 'Unauthorised access' in response.json()['detail']
        logger.info(
            f'!!!!!!!! Response test_non_admin_create_db: {response.json()}'
        )


@pytest.mark.asyncio(scope='session')
async def test_unauth_create_db():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        logger.info('!!!!!!!! Starting test_unauth_create_db')
        response = await client.post(
            '/create-database',
            json={'db_name': Settings.TEST_DB_NAME_2}
        )
        assert response.status_code == 401
        assert 'Not authenticated' in response.json()['detail']
        logger.info(
            f'!!!!!!!! Response test_unauth_create_db: {response.json()}'
        )

# ------------------------------
# Create Database User Tests
# ------------------------------


@pytest.mark.asyncio(scope='session')
async def test_create_db_user(access_token, db_user_payload):
    headers = await access_token
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        logger.info('!!!!!!!! Starting test_create_db_user')
        response = await client.post(
            '/create-db-user',
            json=db_user_payload,
            headers=headers
        )
        assert response.status_code == 201
        assert 'created successfully' in response.json()['message']
        logger.info(
            f'!!!!!!!! Response test_create_db_user: {response.json()}'
        )


@pytest.mark.asyncio(scope='session')
async def test_ext_usr_creation(access_token, db_user_payload):
    headers = await access_token
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        logger.info('!!!!!!!! Starting test_ext_usr_creation')
        response = await client.post(
            '/create-db-user',
            json=db_user_payload,
            headers=headers
        )
        assert response.status_code == 201
        assert 'already exists' in response.json()['message']
        logger.info(
            f'!!!!!!!! Response test_ext_usr_creation: {response.json()}'
        )


@pytest.mark.asyncio(scope='session')
async def test_create_user_unauth(non_admin_access_token, db_user_payload):
    headers = await non_admin_access_token
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        logger.info('!!!!!!!! Starting test_create_user_unauth')
        response = await client.post(
            '/create-db-user',
            json=db_user_payload,
            headers=headers
        )
        assert response.status_code == 403
        assert 'Unauthorised access' in response.json()['detail']
        logger.info(
            f'!!!!!!!! Response test_create_user_unauth: {response.json()}'
        )


# ------------------------------
# Create Table Tests
# ------------------------------


@pytest.mark.asyncio(scope='session')
async def test_create_table(access_token, create_table_payload):
    headers = await access_token
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        logger.info('!!!!!!!! Starting test_create_table')
        response = await client.post(
            '/create-table',
            json=create_table_payload,
            headers=headers
        )
        assert response.status_code == 201
        assert 'created successfully' in response.json()['message']
        logger.info(f'!!!!!!!! Response create-table: {response.json()}')


@pytest.mark.asyncio(scope='session')
async def test_ext_create_table(access_token, create_table_payload):
    headers = await access_token
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        logger.info('!!!!!!!! Starting test_ext_create_table')
        response = await client.post(
            '/create-table',
            json=create_table_payload,
            headers=headers
        )
        assert response.status_code == 400
        assert 'already exists' in response.json()['detail']
        logger.info(
            f'!!!!!!!! Response test_ext_create_table: {response.json()}'
        )


@pytest.mark.asyncio(scope='session')
@pytest.mark.parametrize(
    'create_table_payload',
    [{'table_schema': {'id': 'invalid'}}],
    indirect=True
)
async def test_invalid_tbl_schema(access_token, create_table_payload):
    headers = await access_token
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        logger.info('!!!!!!!! Starting test_invalid_tbl_schema')
        response = await client.post(
            '/create-table',
            json=create_table_payload,
            headers=headers
        )
        assert response.status_code == 500
        assert 'Error creating table' in response.json()['detail']
        logger.info(
            f'!!!!!!!! Response test_invalid_tbl_schema: {response.json()}'
        )


# ------------------------------
# Insert DatTests
# ------------------------------

@pytest.mark.asyncio(scope='session')
async def test_insert_data(access_token, insert_data_payload):
    headers = await access_token
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        logger.info('!!!!!!!! Starting test_insert_data')
        response = await client.post(
            '/insert-data',
            json=insert_data_payload,
            headers=headers
        )
        assert response.status_code == 201
        assert 'Datinsertion completed' in response.json()['message']
        logger.info(f'!!!!!!!! Response test_insert_data: {response.json()}')


@pytest.mark.asyncio(scope='session')
@pytest.mark.parametrize(
    'insert_data_payload',
    [{'table_name': 'invalid'}],
    indirect=True
)
async def test_insert_nonexistent_tbl(
    access_token,
    insert_data_payload
):
    headers = await access_token
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        logger.info('!!!!!!!! Starting test_insert_nonexistent_tbl')
        response = await client.post(
            '/insert-data',
            json=insert_data_payload,
            headers=headers
        )
        assert response.status_code == 404
        assert 'doesn\'t exist' in response.json()['detail']
        logger.info(
            f'!!!!!!!! Response test_insert_nonexistent_tbl: {response.json()}'
        )


@pytest.mark.asyncio(scope='session')
@pytest.mark.parametrize(
    'insert_data_payload',
    [{'data': [{'id': 'invalid'}]}],
    indirect=True
)
async def test_insert_invalid_data(
    access_token,
    insert_data_payload
):
    headers = await access_token
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        logger.info('!!!!!!!! Starting test_insert_invalid_data')
        response = await client.post(
            '/insert-data',
            json=insert_data_payload,
            headers=headers
        )
        assert response.status_code == 500
        assert 'Error during datinsertion' in response.json()['detail']
        logger.info(
            f'!!!!!!!! Response test_insert_invalid_data: {response.json()}'
        )


# ------------------------------
# Get Table Tests
# ------------------------------

@pytest.mark.asyncio(scope='session')
async def test_get_table(access_token):
    headers = await access_token
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        logger.info('!!!!!!!! Starting test_get_table')
        response = await client.get(
            f'/get-table/{Settings.TEST_DB_NAME}/{Settings.TEST_TABLE_NAME}',
            headers=headers
        )
        assert response.status_code == 200
        logger.info(f'!!!!!!!! Response test_get_table: {response.json()}')


@pytest.mark.asyncio(scope='session')
async def test_get_nonexistent_tbl(access_token):
    headers = await access_token
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        logger.info('!!!!!!!! Starting test_get_nonexistent_tbl')
        response = await client.get(
            f'/get-table/{Settings.TEST_DB_NAME}/nonexistent_table',
            headers=headers
        )
        assert response.status_code == 404
        assert 'does not exist' in response.json()['detail']
        logger.info(
            f'!!!!!!!! Response test_get_nonexistent_tbl: {response.json()}'
        )


@pytest.mark.asyncio(scope='session')
async def test_non_admin_get_table(non_admin_access_token):
    headers = await non_admin_access_token
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        logger.info('!!!!!!!! Starting test_non_admin_get_table')
        response = await client.get(
            f'/get-table/{Settings.TEST_DB_NAME}/{Settings.TEST_TABLE_NAME}',
            headers=headers
        )
        assert response.status_code == 200
        logger.info(
            f'!!!!!!!! Response test_non_admin_get_table: {response.json()}'
        )


# ------------------------------
# Delete Table Tests
# ------------------------------


@pytest.mark.asyncio(scope='session')
async def test_delete_table(access_token):
    headers = await access_token
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        logger.info('!!!!!!!! Starting test_delete_table')
        response = await client.delete(
            f'/delete-table/{Settings.TEST_DB_NAME}/{Settings.TEST_TABLE_NAME}',
            headers=headers
        )
        assert response.status_code == 200
        assert 'deleted successfully' in response.json()['message']
        logger.info(f'!!!!!!!! Response test_delete_table): {response.json()}')


@pytest.mark.asyncio(scope='session')
async def test_del_nonexistent_tbl(access_token):
    headers = await access_token
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:

        logger.info('!!!!!!!! Starting test_del_nonexistent_tbl')
        response = await client.delete(
            f'/delete-table/{Settings.TEST_DB_NAME}/nonexistent_table',
            headers=headers
        )
        assert response.status_code == 404
        assert 'does not exist' in response.json()['detail']
        logger.info(
            f'!!!!!!!! Response test_del_nonexistent_tbl: {response.json()}'
        )
