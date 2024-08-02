import requests

from config import Settings

# ------------------------------
# Constants
# ------------------------------

BASE_URL = "http://localhost:8000"

# ------------------------------
# Access token
# ------------------------------

token_response = requests.post(
    f"{BASE_URL}/get-token",
    data={"username": Settings.API_ADM_USER, "password": Settings.API_ADM_PASSWORD},
)

access_token = token_response.json()["access_token"]
headers = {"Authorization": f"Bearer {access_token}"}
print(f"\nAccess token for user {Settings.API_ADM_USER} received\n")

# ------------------------------
# Register API User
# ------------------------------

response = requests.post(
    f"{BASE_URL}/register-api-user",
    json={"username": Settings.TEST_PASSWORD, "password": Settings.TEST_USER, "is_admin": True},
    headers=headers,
)
response_json = response.json()
print(f"Response register-api-user: {response_json}\n")


# ------------------------------
# Access token for API Test User
# ------------------------------

token_response = requests.post(
    f"{BASE_URL}/get-token",
    data={"username": Settings.TEST_PASSWORD, "password": Settings.TEST_USER},
)

access_token = token_response.json()["access_token"]
headers = {"Authorization": f"Bearer {access_token}"}
print(f"Access token for user {Settings.TEST_USER} received\n")


# ------------------------------
# Create Database
# ------------------------------

response = requests.post(
    f"{BASE_URL}/create-database", json={"db_name": Settings.TEST_DB_NAME}, headers=headers
)
response_json = response.json()

print(f"Response create-database: {response_json}\n")

# ------------------------------
# Register Database User
# ------------------------------

response = requests.post(
    f"{BASE_URL}/create-db-user",
    json={
        "host": Settings.MYSQL_HOST,
        "username": Settings.TEST_USER,
        "password": Settings.TEST_PASSWORD,
        "db_name": Settings.TEST_DB_NAME,
        "privileges": "SELECT",
    },
    headers=headers,
)
response_json = response.json()
print(f"Response register-db-user: {response_json}\n")

# ------------------------------
# Create Table
# ------------------------------

table_schema = {"id": "INT PRIMARY KEY", "name": "VARCHAR(50)", "age": "INT"}

response = requests.post(
    f"{BASE_URL}/create-table",
    json={
        "db_name": Settings.TEST_DB_NAME,
        "table_name": Settings.TEST_TABLE_NAME,
        "table_schema": table_schema,
    },
    headers=headers,
)
response_json = response.json()
print(f"Response create-table: {response_json}\n")

# ------------------------------
# Insert Data
# ------------------------------

data_insert = [{"id": 1, "name": "None", "age": 25}, {"id": 2, "name": "Jane Smith", "age": 30}]

response = requests.post(
    f"{BASE_URL}/insert-data",
    json={
        "db_name": Settings.TEST_DB_NAME,
        "table_name": Settings.TEST_TABLE_NAME,
        "data": data_insert,
    },
    headers=headers,
)
response_json = response.json()
print(f"Response insert-data: {response_json}\n")

# ------------------------------
# Fetch Table
# ------------------------------

response = requests.get(
    f"{BASE_URL}/get-table/{Settings.TEST_DB_NAME}/{Settings.TEST_TABLE_NAME}", headers=headers
)
response_json = response.json()
print(f"Response get-table: {response_json}\n")

# ------------------------------
# Delete Table
# ------------------------------

response = requests.delete(
    f"{BASE_URL}/delete-table/{Settings.TEST_DB_NAME}/{Settings.TEST_TABLE_NAME}", headers=headers
)

response_json = response.json()
print(f"Response delete-table: {response_json}\n")
