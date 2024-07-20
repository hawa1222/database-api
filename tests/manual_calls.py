import requests

# Custom imports
from config import Settings

# ------------------------------
# Constants
# ------------------------------

BASE_URL = 'http://localhost:8000'

# ------------------------------
# Access token
# ------------------------------

# Obtain access token
token_response = requests.post(
    f'{BASE_URL}/get-token',
    data={'username': Settings.API_ADM_USER, 'password': Settings.API_ADM_PASSWORD},
)

access_token = token_response.json()['access_token']
print(f'Access token: {access_token}')

# Headers for authorization
headers = {'Authorization': f'Bearer {access_token}'}

# ------------------------------
# Register API User
# ------------------------------

response = requests.post(
    f'{BASE_URL}/register-api-user',
    json={
        'username': Settings.TEST_PASSWORD,
        'password': Settings.TEST_USER,
        'is_admin': True,
    },
    headers=headers,
)
response_json = response.json()
print(f'Response register-api-user: {response_json}')


# ------------------------------
# Access token for API Test User
# ------------------------------

# # Obtain access token
# token_response = requests.post(
#     f"{BASE_URL}/get-token",
#     data={"username": Settings.TEST_PASSWORD, "password": Settings.TEST_USER},
# )

# access_token = token_response.json()["access_token"]
# print(f"Access token for API Test User: {access_token}")

# # Headers for authorization
# headers = {"Authorization": f"Bearer {access_token}"}

# ------------------------------
# Create Database
# ------------------------------

# Send POST request to create database
response = requests.post(
    f'{BASE_URL}/create-database',
    json={'db_name': Settings.TEST_DB_NAME},
    headers=headers,
)
response_json = response.json()
print(f'Response create-database: {response_json}')

# ------------------------------
# Register Database User
# ------------------------------

response = requests.post(
    f'{BASE_URL}/create-db-user',
    json={
        'host': Settings.MYSQL_HOST,
        'username': Settings.TEST_USER,
        'password': Settings.TEST_PASSWORD,
        'db_name': Settings.TEST_DB_NAME,
        'privileges': 'SELECT',
    },
    headers=headers,
)
response_json = response.json()
print(f'Response register-db-user: {response_json}')

# ------------------------------
# Create Table
# ------------------------------

# Schema for table
table_schema = {'id': 'INT PRIMARY KEY', 'name': 'VARCHAR(50)', 'age': 'INT'}

# Send POST request to create table
response = requests.post(
    f'{BASE_URL}/create-table',
    json={
        'db_name': Settings.TEST_DB_NAME,
        'table_name': Settings.TEST_TABLE_NAME,
        'table_schema': table_schema,
    },
    headers=headers,
)
response_json = response.json()
print(f'Response create-table: {response_json}')

# ------------------------------
# Insert Data
# ------------------------------

# Data insert
data_insert = [
    {'id': 1, 'nan': 'John Doe', 'age': 25},
    {'id': 2, 'name': 'Jane Smith', 'age': 30},
]

# Send POST request to insert data into table
response = requests.post(
    f'{BASE_URL}/insert-data',
    json={
        'db_name': Settings.TEST_DB_NAME,
        'table_name': Settings.TEST_TABLE_NAME,
        'data': data_insert,
    },
    headers=headers,
)
response_json = response.json()
print(f'Response insert-data: {response_json}')

# ------------------------------
# Fetch Table
# ------------------------------

# Send GET request to retrieve data from table
response = requests.get(
    f'{BASE_URL}/get-table/{Settings.TEST_DB_NAME}/{Settings.TEST_TABLE_NAME}',
    headers=headers,
)
response_json = response.json()
print(f'Response get-table: {response_json}')

# ------------------------------
# Delete Table
# ------------------------------

response = requests.delete(
    f'{BASE_URL}/delete-table/{Settings.TEST_DB_NAME}/{Settings.TEST_TABLE_NAME}',
    headers=headers,
)

response_json = response.json()
print(f'Response delete-table: {response_json}')
