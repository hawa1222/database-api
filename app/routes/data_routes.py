from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import authorise
from app.crud import data_crud
from app.database import db_connect
from app.schemas import auth_schemas
from app.schemas import data_schemas
from app.utils.logging import setup_logging

# Custom imports
from config import Settings

# ------------------------------
# Set up logging
# ------------------------------

# Initialise logging
logger = setup_logging()

# ------------------------------
# API Router configuration
# ------------------------------

router = APIRouter()

limiter = Limiter(key_func=get_remote_address)

# -----------------how -------------
# API routes & endpoints for database operations
# ------------------------------


# Create new database
@router.post(
    "/create-database",
    status_code=201,
    summary="Create new database",
    tags=["Database"],
)
@limiter.limit(Settings.API_RATE_LIMIT)
async def create_database(
    request: Request,
    database: data_schemas.DatabaseCreate,
    db: AsyncSession = Depends(db_connect.get_db),
    current_user: auth_schemas.User = Depends(authorise.admin_user),
):
    """
    Endpoint allows authenticated user with or without
    admin privileges to create new database.

    Parameters:
    - **database**: Database schemcontaining name of database to be created.
    - **db**: database session obtained from *get_db* dependency.
    - **current_user**: currently authenticated user obtained from
    *active_user* dependency.

    Returns:
    -  Success message with name of created database.

    Raises:
    - HTTPException (400): If database already exists.

    Example request body:
    ```json
    {
        'name': 'new_database'
    }
    ```

    Example response:
    ```json
    {
        'message': 'Database 'new_database' created successfully'
    }
    ```
    """

    logger.info("data_routes ---> create_database:")

    return await data_crud.create_database(db, database)


# Create new database user
@router.post(
    "/create-db-user",
    status_code=201,
    summary="Create new database user",
    tags=["User"],
)
@limiter.limit(Settings.API_RATE_LIMIT)
async def create_db_user(
    request: Request,
    user: auth_schemas.DBUserCreate,
    db: AsyncSession = Depends(db_connect.get_db),
    current_user: auth_schemas.User = Depends(authorise.admin_user),
):
    """
    Endpoint allows authenticated admin user to create new database user.

    Parameters:
    - **user**: user schemcontaining host, username, password,
    database name, and privileges of database user to be created.
    - **db**: database session obtained from *get_db* dependency.
    - **current_user**: currently authenticated admin user obtained
    from *admin_user* dependency.

    Returns:
    - Success message with username of created database user.

    Raises:
    - HTTPException (500): If there is an error creating database user.

    Example request body:
    ```json
    {
        'host': 'localhost',
        'username': 'db_user',
        'password': 'password123',
        'db_name': 'new_database',
        'privileges': 'SELECT'
    }
    ```

    Example response:
    ```json
    {
        'message': 'DB user "db_user" created successfully'
    }
    ```
    """

    logger.info("data_routes ---> create_db_user:")

    return await data_crud.create_db_user(db, user)


# Create new table
@router.post("/create-table", status_code=201, summary="Create new table", tags=["Tables"])
@limiter.limit(Settings.API_RATE_LIMIT)
async def create_table(
    request: Request,
    tables: data_schemas.TableCreate,
    db: AsyncSession = Depends(db_connect.get_db),
    current_user: auth_schemas.User = Depends(authorise.admin_user),
):
    """
    Endpoint allows authenticated user to create new table in database.

    Parameters:
    - **tables**: table schemcontaining name of database and
    table to be created.
    - **db**: database session obtained from *get_db* dependency.
    - **current_user**: currently authenticated user obtained from
    *active_user* dependency.

    Returns:
    - Success message with name of created table.

    Raises:
    - HTTPException (400): If table already exists.

    Example request body:
    ```json
    {
        'db_name': 'new_database',
        'table_name': 'new_table'
        'table_schema': {
            'id': 'int',
            'name': 'str',
            'age': 'int'
        }
    }
    ```

    Example response:
    ```json
    {
        'message': 'Table "new_table" created
                    successfully in database "new_database"'
    }
    ```
    """

    logger.info("data_routes ---> create_table:")

    return await data_crud.create_table(db, tables)


# Insert data into table
@router.post("/insert-data", status_code=201, summary="Insert data into table", tags=["Tables"])
@limiter.limit(Settings.API_RATE_LIMIT)
async def insert_data(
    request: Request,
    data_insert: data_schemas.TableData,
    db: AsyncSession = Depends(db_connect.get_db),
    current_user: auth_schemas.User = Depends(authorise.admin_user),
):
    """
    Endpoint allows authenticated admin user to insert datinto database.

    Parameters:
    - **data_insert**: datschemcontaining name of database
    and table, and datto be inserted.
    - **db**: database session obtained from *get_db* dependency.
    - **current_user**: currently authenticated admin user obtained from
    *admin_user* dependency.

    Returns:
    - Success message with number of rows inserted.

    Raises:
    - HTTPException (404): If table does not exist in database.

    Example request body:
    ```json
    {
        'db_name': 'new_database',
        'table_name': "new_table',
        'data: [
            {
                'id": 1,
                'name': "Alice',
                'age': 25
            },
            {
                'id': 2,
                'name': 'Bob',
                'age": 30
            }
        ]
    }
    ```

    Example response:
    ```json
    {
        'message': 'Datinsertion completed for table "new_table" in database
                    "new_database": 2 records added, 0 records updated'
    }
    ```
    """

    logger.info("data_routes ---> insert_data:")

    return await data_crud.insert_data(db, data_insert)


# Get data from table
@router.get(
    "/get-table/{db_name}/{table_name}",
    status_code=200,
    summary="Get table data",
    tags=["Tables"],
)
@limiter.limit(Settings.API_RATE_LIMIT)
async def get_table(
    request: Request,
    db_name: str,
    table_name: str,
    db: AsyncSession = Depends(db_connect.get_db),
    current_user: auth_schemas.User = Depends(authorise.active_user),
):
    """
    Endpoint allows authenticated admin user to retrieve datfrom table.

    Parameters:
    - **db_name**: name of database.
    - **table_name**: name of table.
    - **db**: database session obtained from *get_db* dependency.
    - **current_user**: currently authenticated admin user obtained
    from *admin_user* dependency.

    Returns:
    - datfrom table.

    Raises:
    - HTTPException (404): If table does not exist in database.

    Example get request:
    ```
    GET /get-table/new_database/new_table
    ```

    Example response:
    ```json
    {
        'new_table': [
            {
                'id': 1,
                'name': 'Alice',
                'age': 25
            },
            {
                'id': 2,
                'name': 'Bob',
                'age': 30
            }
        ]
    }
    """

    logger.info("data_routes ---> get_table:")

    # Create table identification object
    table_fetch = data_schemas.TableIdentify(db_name=db_name, table_name=table_name)

    return await data_crud.get_table(db, table_fetch)


# Delete table
@router.delete(
    "/delete-table/{db_name}/{table_name}",
    status_code=200,
    summary="Delete table",
    tags=["Tables"],
)
@limiter.limit(Settings.API_RATE_LIMIT)
async def delete_table(
    request: Request,
    db_name: str,
    table_name: str,
    db: AsyncSession = Depends(db_connect.get_db),
    current_user: auth_schemas.User = Depends(authorise.admin_user),
):
    """
    Endpoint allows authenticated admin user to delete table from database.

    Parameters:
    - **db_name**: name of database.
    - **table_name**: name of table.
    - **db**: database session obtained from *get_db* dependency.
    - **current_user**: currently authenticated admin user obtained
    from *admin_user* dependency.

    Returns:
    - Success message with name of deleted table.

    Raises:
    - HTTPException (404): If table does not exist in database.

    Example delete request:
    ```
    DELETE /delete-table/new_database/new_table
    ```

    Example response:
    ```json
    {
        'message': 'Table "new_table" deleted successfully
            from database "new_database"'
    }
    """

    logger.info("data_routes ---> delete_table:")

    # Create table identification object
    table_delete = data_schemas.TableIdentify(db_name=db_name, table_name=table_name)

    return await data_crud.delete_table(db, table_delete)
