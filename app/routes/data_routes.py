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
from config import Settings

# ------------------------------
# Set up logging
# ------------------------------

logger = setup_logging()

# ------------------------------
# API Router configuration
# ------------------------------

router = APIRouter()

limiter = Limiter(key_func=get_remote_address)

# ------------------------------
# API routes & endpoints for database operations
# ------------------------------


@router.post("/create-database", status_code=201, summary="Create new database", tags=["Database"])
@limiter.limit(Settings.API_RATE_LIMIT)
async def create_database(
    request: Request,
    database: data_schemas.DatabaseCreate,
    db: AsyncSession = Depends(db_connect.get_db),
    current_user: auth_schemas.User = Depends(authorise.admin_user),
):
    """
    Endpoint allows authenticated user with admin privileges to create new database.

    Parameters:
        **database**: Pydantic model containing name of database to be created.
        **db**: Async database session obtained from *get_db* dependency.
        **current_user**: Active authenticated admin user obtained from *admin_user* dependency.

    Returns:
        dict: Success message with name of created database.

    Raises:
        HTTPException (400): If database already exists.
        HTTPException (401): If token is invalid.
        HTTPException (403): If current user is not an admin.
        HTTPException (500): If any other error occurs.

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

    logger.debug("Executing create-database endpoint...")

    return await data_crud.create_database(db, database)


@router.post("/create-db-user", status_code=201, summary="Create new database user", tags=["User"])
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
        **user**: Pydantic model containing host, username, password, database name,
        and privileges of database user to be created.
        **db**: Async database session obtained from *get_db* dependency.
        **current_user**: Active authenticated admin user obtained from *admin_user* dependency.

    Returns:
        dict: Success message with name of created database user.

    Raises:
        HTTPException (401): If token is invalid.
        HTTPException (403): If current user is not an admin.
        HTTPException (500): If any other error occurs.

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

    logger.debug("Executing create-db-user endpoint...")

    return await data_crud.create_db_user(db, user)


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
        **tables**: Pydantic model containing name of database, name of database
        and table to be created.
        **db**: Async database session obtained from *get_db* dependency.
        **current_user**: Active authenticated admin user obtained from *admin_user* dependency.

    Returns:
        dict: Success message with name of created table.

    Raises:
        HTTPException (400): If table already exists.
        HTTPException (401): If token is invalid.
        HTTPException (403): If current user is not an admin.
        HTTPException (500): If any other error occurs.

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

    logger.debug("Executing create-table endpoint...")

    return await data_crud.create_table(db, tables)


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
        **data_insert**: Pydantic model containing name of database and table, and data.
        **db**: Async database session obtained from *get_db* dependency
        **current_user**: Active authenticated admin user obtained from *admin_user* dependency.

    Returns:
        dict: Success message with number of records added and updated.

    Raises:
        HTTPException (401): If token is invalid.
        HTTPException (403): If current user is not an admin.
        HTTPException (404): If table does not exist in database.
        HTTPException (500): If any other error occurs.

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

    logger.debug("Executing insert-data endpoint...")

    return await data_crud.insert_data(db, data_insert)


@router.get(
    "/get-table/{db_name}/{table_name}", status_code=200, summary="Get table data", tags=["Tables"]
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
        **db_name**: Name of database.
        **table_name**: Name of table.
        **db**: Async database session obtained from *get_db* dependency.
        **current_user**: Active authenticated user obtained from *active_user* dependency.

    Returns:
        dict: Dictionary containing table name and data.

    Raises:
        HTTPException (401): If token is invalid.
        HTTPException (404): If table does not exist in database.
        HTTPException (500): If any other error occurs.

    Example get request:
    ```
    GET / get - table / new_database / new_table
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

    logger.debug("Executing get-table endpoint...")

    table_fetch = data_schemas.TableIdentify(db_name=db_name, table_name=table_name)

    return await data_crud.get_table(db, table_fetch)


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
        **db_name**: Name of database.
        **table_name**: Name of table.
        **db**: Async database session obtained from *get_db* dependency.
        **current_user**: Active authenticated admin user obtained from *admin_user* dependency.

    Returns:
        dict: Success message with name of deleted table.

    Raises:
        HTTPException (401): If token is invalid.
        HTTPException (403): If current user is not an admin.
        HTTPException (404): If table does not exist in database.
        HTTPException (500): If any other error occurs.

    Example delete request:
    ```
    DELETE / delete - table / new_database / new_table
    ```

    Example response:
    ```json
    {
        'message': 'Table "new_table" deleted successfully
            from database "new_database"'
    }
    """

    logger.debug("Executing delete-table endpoint...")

    table_delete = data_schemas.TableIdentify(db_name=db_name, table_name=table_name)

    return await data_crud.delete_table(db, table_delete)
