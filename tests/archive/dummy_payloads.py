import pytest

from config import Settings


@pytest.fixture
def create_table_payload():
    return {
        "db_name": Settings.TEST_DB_NAME,
        "table_name": Settings.TEST_TABLE_NAME,
        "table_schema": {"id": "INT PRIMARY KEY", "name": "VARCHAR(50)", "age": "INT"},
    }


@pytest.fixture
def insert_data_payload():
    return {
        "db_name": Settings.TEST_DB_NAME,
        "table_name": Settings.TEST_TABLE_NAME,
        "data": [
            {"id": 1, "name": "John Doe", "age": 25},
            {"id": 2, "name": "Jane Smith", "age": 30},
        ],
    }


@pytest.fixture
def insert_invalid_data_payload():
    return {
        "db_name": Settings.TEST_DB_NAME,
        "table_name": Settings.TEST_TABLE_NAME,
        "data": [{"id": "invalid_id", "name": "John Doe", "age": 25}],
    }
