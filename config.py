import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")

    ROOT_DIRECTORY = os.getenv("ROOT_DIRECTORY", ".")

    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
    DATABASE_URL = (
        f"mysql+aiomysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    )

    API_RATE_LIMIT = "30/minute"

    API_ADM_USER = os.getenv("API_ADMIN_USER")
    API_ADM_PASSWORD = os.getenv("API_ADMIN_PASSWORD")

    TOKEN_EXPIRE_MINUTES = 60
    TOKEN_SECRET_KEY = os.getenv("SECRET_KEY")
    TOKEN_ALGORITHM = os.getenv("ALGORITHM")

    SSL_KEYFILE_PASSWORD = os.getenv("SSL_KEYFILE_PASSWORD")

    # Test Config
    MYSQL_TEST_USER = os.getenv("MYSQL_TEST_USER")
    TEST_DATABASE_URL = (
        f"mysql+aiomysql://{MYSQL_TEST_USER}:{MYSQL_PASSWORD}"
        f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    )
    TEST_USER = "testing"
    TEST_PASSWORD = "testing"
    TEST_DB_NAME = "testdb"
    TEST_DB_NAME_2 = "testdb2"
    TEST_TABLE_NAME = "users"
