import requests
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.database.database import get_db
from app.main import app
from app.database import crud
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

API_ADMIN_USER = os.getenv('API_ADMIN_USER')
API_ADMIN_PASSWORD = os.getenv('API_ADMIN_PASSWORD')

# Set the base URL for your API
BASE_URL = "http://localhost:8000"

# ------------------------------
# Access token
# ------------------------------

# Obtain the access token
token_response = requests.post(f"{BASE_URL}/get-token", 
                               data={"username": API_ADMIN_USER,
                                     "password": API_ADMIN_PASSWORD})

access_token = token_response.json()["access_token"]
print(f"Access token: {access_token}")

# Headers for authorization
headers = {"Authorization": f"Bearer {access_token}"}


# ------------------------------
# Create Database
# ------------------------------

# Name of the database to create
TEST_DB_NAME = 'testdb'

# Send a POST request to create a database
response = requests.post(
    f"{BASE_URL}/create-database",
    json={"db_name": TEST_DB_NAME},
    headers=headers
)
response_json = response.json()
print(f"Response create-database: {response_json}")


# ------------------------------
# Create Table
# ------------------------------

# Name of the table to create within the database
TEST_TABLE_NAME = 'users'

# Schema for the table
table_schema = {
    "id": "INT PRIMARY KEY",
    "name": "VARCHAR(50)",
    "age": "INT"
}

# Send a POST request to create a table
response = requests.post(
    f"{BASE_URL}/create-table",
    json={
        "db_name": TEST_DB_NAME,
        "table_name": TEST_TABLE_NAME,
        "table_schema": table_schema
    },
    headers=headers
)
response_json = response.json()
print(f"Response create-table: {response_json}")

# ------------------------------
# Insert Data
# ------------------------------

# Data to insert
data_insert =  [
     {
      "id": 1,
      "name": "John Doe",
      "age": 25
    },
    {
      "id": 2,
      "name": "Jane Smith",
      "age": 30
    }
  ]

# Send a POST request to insert data into the table
response = requests.post(
    f"{BASE_URL}/insert-data",
    json={
        "db_name": TEST_DB_NAME,
        "table_name": TEST_TABLE_NAME,
        "data": data_insert
    },
    headers=headers
)
response_json = response.json()
print(f"Response insert-data: {response_json}")


# ------------------------------
# Fetch Table
# ------------------------------

# Send a GET request to retrieve data from the table
response = requests.get(
    f"{BASE_URL}/get-table/{TEST_DB_NAME}/{TEST_TABLE_NAME}",
    headers=headers
)
response_json = response.json()
print(f"Response get-table: {response_json}")

# ------------------------------
# Delete Table
# ------------------------------

response = requests.delete(
    f"{BASE_URL}/delete-table/{TEST_DB_NAME}/{TEST_TABLE_NAME}",
    headers=headers
)

response_json = response.json()
print(f"Response delete-table: {response_json}")
