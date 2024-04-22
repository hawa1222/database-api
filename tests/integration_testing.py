import os
import httpx
import pytest

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from app.database.database import get_db
from app.database.models import Base
from app.main import app
from app.schemas import schemas
from dotenv import load_dotenv

# ------------------------------
# Environment variables
# ------------------------------

# Load environment variables from .env file
load_dotenv()

# Get environment variables
MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_PORT = os.getenv('MYSQL_PORT')
MYSQL_TEST_USER = os.getenv('MYSQL_TEST_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')

# Define the database URL
# SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{MYSQL_TEST_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

# ------------------------------
# Set up the database connection
# ------------------------------
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = f"mysql+aiomysql://{MYSQL_TEST_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"

# Create an asynchronous database engine
engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

@pytest.mark.asyncio
async def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        try:
            await db.close()
        except RuntimeError as e:
            if "Event loop is closed" not in str(e):
                raise

# engine = create_engine(SQLALCHEMY_DATABASE_URL)
# TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# def override_get_db():
#     try:
#         db = TestingSessionLocal()
#         yield db
#     finally:
#         db.close()


# Base.metadata.create_all(bind=engine)



# Override the get_db dependency with the override_get_db function
app.dependency_overrides[get_db] = override_get_db

# ------------------------------
# Set test client
# ------------------------------

client = TestClient(app)

# ------------------------------
# Set up authentication headers
# ------------------------------

API_ADMIN_USER = os.getenv('API_ADMIN_USER')
API_ADMIN_PASSWORD = os.getenv('API_ADMIN_PASSWORD')

# ------------------------------
# Test cases
# ------------------------------

TEST_DB_NAME = 'tesdb'
TEST_TABLE_NAME = 'users'

# @pytest.mark.asyncio
# async def test_create_database_success():
#     async with httpx.AsyncClient(app=app, base_url="http://test") as client:
#         payload = {"username": API_ADMIN_USER, "password": API_ADMIN_PASSWORD}
#         response = await client.post("/get-token", data=payload)
#         access_token = response.json()["access_token"]
#         assert response.status_code == 200
#         headers = {"Authorization": f"Bearer {access_token}"}

#         payload = schemas.DatabaseCreate(db_name=TEST_DB_NAME)
#         response = await client.post("/create-database", json=payload.model_dump(), headers=headers)
#         assert response.status_code == 201

#         payload = schemas.DBUserCreate(
#             host=MYSQL_HOST,
#             username="testing",
#             password="testing",
#             db_name=TEST_DB_NAME,
#             privileges="SELECT")
#         response = await client.post("/create-db-user", json=payload.model_dump(), headers=headers)
#         assert response.status_code == 201
#         assert "created successfully" in response.json()["message"]

@pytest.mark.asyncio
async def get_admin_token():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        payload = {"username": API_ADMIN_USER, "password": API_ADMIN_PASSWORD}
        response = await client.post("/get-token", data=payload)
        access_token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        return headers

# Test cases for create_database endpoint
@pytest.mark.asyncio
async def test_create_database_success():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        payload = schemas.DatabaseCreate(db_name=TEST_DB_NAME)
        headers = await get_admin_token()
        response = await client.post("/create-database", json=payload.model_dump(), headers=headers)
        assert response.status_code == 201

# Test cases for create_user endpoint
@pytest.mark.asyncio
async def test_create_user_success():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        payload = schemas.DBUserCreate(
            host=MYSQL_HOST,
            username="testing",
            password="testing",
            db_name=TEST_DB_NAME,
            privileges="SELECT"
        )
        headers = await get_admin_token()
        response = await client.post("/create-db-user", json=payload.model_dump(), headers=headers)
        assert response.status_code == 201
        assert "created successfully" in response.json()["message"]

# def test_create_user_already_exists():
#     payload = schemas.DBUserCreate(
#         host=MYSQL_HOST,
#         username=MYSQL_TEST_USER,
#         password=MYSQL_PASSWORD,
#         db_name=TEST_DB_NAME,
#         privileges="ALL"
#     )
#     headers = get_admin_token()
#     response = client.post("/create-db-user", json=payload.model_dump(), headers=headers)
#     assert response.status_code == 201
#     assert "already exists" in response.json()["message"]

# def test_create_user_invalid_privileges():
#     payload = schemas.DBUserCreate(
#         host=headers,
#         username="invaliduser",
#         password="invalidpassword",
#         db_name=TEST_DB_NAME,
#         privileges="INVALID_PRIVILEGE"
#     )
#     headers = get_admin_token()
#     response = client.post("/create-db-user", json=payload.model_dump(), headers=headers)
#     assert response.status_code == 500
#     assert "Error creating or updating DB user" in response.json()["detail"]

# # Test cases for create_table endpoint
# def test_create_table_success():
#     payload = schemas.TableCreate(
#         db_name=TEST_DB_NAME,
#         table_name=TEST_TABLE_NAME,
#         table_schema={
#             "id": "INT PRIMARY KEY",
#             "name": "VARCHAR(50)",
#             "email": "VARCHAR(100)"
#         }
#     )
#     headers = get_admin_token()
#     response = client.post("/create-table", json=payload.model_dump(), headers=headers)
#     assert response.status_code == 201
#     assert "created successfully" in response.json()["message"]

# def test_create_table_already_exists():
#     payload = schemas.TableCreate(
#         db_name=TEST_DB_NAME,
#         table_name=TEST_TABLE_NAME,
#         table_schema={
#             "id": "INT PRIMARY KEY",
#             "name": "VARCHAR(50)",
#             "email": "VARCHAR(100)"
#         }
#     )
#     headers = get_admin_token()
#     response = client.post("/create-table", json=payload.model_dump(), headers=headers)
#     assert response.status_code == 400
#     assert "already exists" in response.json()["detail"]

# def test_create_table_invalid_schema():
#     payload = schemas.TableCreate(
#         db_name=TEST_DB_NAME,
#         table_name="invalid_table",
#         table_schema={
#             "id": "INVALID_TYPE",
#             "name": "VARCHAR(50)",
#             "email": "VARCHAR(100)"
#         }
#     )
#     headers = get_admin_token()
#     response = client.post("/create-table", json=payload.model_dump(), headers=headers)
#     assert response.status_code == 500
#     assert "Error creating table" in response.json()["detail"]

# # Test cases for insert_data endpoint
# def test_insert_data_success():
#     payload = schemas.TableData(
#         db_name=TEST_DB_NAME,
#         table_name=TEST_TABLE_NAME,
#         data=[
#             {"id": 1, "name": "John Doe", "email": "john@example.com"},
#             {"id": 2, "name": "Jane Smith", "email": "jane@example.com"}
#         ]
#     )
#     headers = get_admin_token()
#     response = client.post("/insert-data", json=payload.model_dump(), headers=headers)
#     assert response.status_code == 201
#     assert "Data insertion completed" in response.json()["message"]

# def test_insert_data_table_not_exists():
#     payload = schemas.TableData(
#         db_name=TEST_DB_NAME,
#         table_name="nonexistent_table",
#         data=[
#             {"id": 1, "name": "John Doe", "email": "john@example.com"}
#         ]
#     )
#     headers = get_admin_token()
#     response = client.post("/insert-data", json=payload.model_dump(), headers=headers)
#     assert response.status_code == 404
#     assert "does not exist" in response.json()["detail"]

# def test_insert_data_invalid_data():
#     payload = schemas.TableData(
#         db_name=TEST_DB_NAME,
#         table_name=TEST_TABLE_NAME,
#         data=[
#             {"id": "invalid_id", "name": "John Doe", "email": "john@example.com"}
#         ]
#     )
#     headers = get_admin_token()
#     response = client.post("/insert-data", json=payload.model_dump(), headers=headers)
#     assert response.status_code == 500
#     assert "Error during data insertion" in response.json()["detail"]

# # Test cases for get_table endpoint
# def test_get_table_success():
#     table_fetch = schemas.TableIdentify(db_name=TEST_DB_NAME, table_name=TEST_TABLE_NAME)
#     headers = get_admin_token()
#     response = client.get(f"/get-table/{table_fetch.db_name}/{table_fetch.table_name}", headers=headers)
#     assert response.status_code == 200
#     assert "users" in response.json()
#     assert len(response.json()["users"]["data"]) == 2

# def test_get_table_not_exists():
#     table_fetch = schemas.TableIdentify(db_name=TEST_DB_NAME, table_name=TEST_TABLE_NAME)
#     headers = get_admin_token()
#     response = client.get(f"/get-table/{table_fetch.db_name}/{table_fetch.table_name}", headers=headers)
#     assert response.status_code == 404
#     assert "does not exist" in response.json()["detail"]

# # Test cases for delete_table endpoint
# def test_delete_table_success():
#     table_delete = schemas.TableIdentify(db_name=TEST_DB_NAME, table_name=TEST_TABLE_NAME)
#     headers = get_admin_token()
#     response = client.delete(f"/delete-table/{table_delete.db_name}/{table_delete.table_name}", headers=headers)
#     assert response.status_code == 200
#     assert "deleted successfully" in response.json()["message"]

# def test_delete_table_not_exists():
#     table_delete = schemas.TableIdentify(db_name=TEST_DB_NAME, table_name="nonexistent_table")
#     headers = get_admin_token()
#     response = client.delete(f"/delete-table/{table_delete.db_name}/{table_delete.table_name}", headers=headers)
#     assert response.status_code == 404
#     assert "does not exist" in response.json()["detail"]

# # Test cases for authentication and authorization
# def test_register_user_success():
#     payload = schemas.UserCreate(username="testuser", password="testpassword", is_admin=False)
#     response = client.post("/register-api-user", json=payload.model_dump())
#     assert response.status_code == 201
#     assert response.json()["username"] == "testuser"

# def test_register_user_already_exists():
#     payload = schemas.UserCreate(username="testuser", password="testpassword", is_admin=False)
#     response = client.post("/register-api-user", json=payload.model_dump())
#     assert response.status_code == 400
#     assert "already exists" in response.json()["detail"]

# def test_login_success():
#     payload = {"username": "testuser", "password": "testpassword"}
#     response = client.post("/login", data=payload)
#     assert response.status_code == 200
#     assert "access_token" in response.json()

# def test_login_invalid_credentials():
#     payload = {"username": "testuser", "password": "wrongpassword"}
#     response = client.post("/login", data=payload)
#     assert response.status_code == 401
#     assert "Invalid credentials" in response.json()["detail"]

# def test_protected_endpoint_unauthorized():
#     token = get_admin_token()
#     headers = create_headers(token)
#     response = client.get("/protected-endpoint", headers=headers)
#     assert response.status_code == 401
#     assert "Not authenticated" in response.json()["detail"]
