import time
import os

import ssl
import uvicorn

from fastapi import FastAPI, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

# Custom imports
from app.database import database, crud, models
from app.schemas import schemas
from app.auth import auth, permissions

from app.utils.create_admin import create_admin_user
from app.utils.logging import setup_logging

# ------------------------------
# Set up logging
# ------------------------------

# Initialise logging
logger = setup_logging()

# ------------------------------
# Environment variables
# ------------------------------

# Load environment variables from .env file
load_dotenv()

# Get the root directory
ROOT_DIRECTORY = os.getenv("ROOT_DIRECTORY")
SSL_KEYFILE_PASSWORD = os.getenv("SSL_KEYFILE_PASSWORD")

# ------------------------------
# HTTPS configuration
# ------------------------------

# def start():

#     # Create an SSL context, this means that the server will use HTTPS
#     ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
#     # Load the certificate and key files
#     cert_file = os.path.join(ROOT_DIRECTORY, "cert.pem")
#     key_file = os.path.join(ROOT_DIRECTORY, "key.pem")
#     # Load the certificate and key files into the SSL context
#     ssl_context.load_cert_chain(cert_file, key_file, password=SSL_KEYFILE_PASSWORD)

#     # Start the server with the SSL context
#     logger.info("Starting the server...")
#     uvicorn.run("app.main:app", host='localhost', port=8000, reload=True, ssl_certfile=cert_file, 
#                 ssl_keyfile=key_file, ssl_keyfile_password=SSL_KEYFILE_PASSWORD)


# ------------------------------
# Setting up the FastAPI application
# ------------------------------

async def lifespan(app: FastAPI):
    logger.info("Starting up the app")

    async with database.engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all, checkfirst=True)
        logger.info(f"Table '{models.User.__tablename__}' created")
        await create_admin_user()  # Create the admin user

    logger.info("App started successfully")

    yield

    logger.info("Shutting down the app and disposing of the engine")
    await database.engine.dispose()
    logger.info("App shut down successfully")

# Create an instance of the FastAPI class with the lifespan dependency
app = FastAPI(lifespan=lifespan)

# ------------------------------
# Rate limiting configuration
# ------------------------------

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ------------------------------
# API endpoints for authentication
# ------------------------------

@app.post("/register-api-user", status_code=201, summary="Register a new API user", 
          tags=["API Authentication"])
@limiter.limit("10/minute")
async def register_user(request: Request, user: schemas.UserCreate, db: AsyncSession = Depends(database.get_db),
                        current_user: schemas.UserCreate = Depends(permissions.get_current_admin_user)):
    """
    This endpoint allows an authenticated admin user to register a new API user.

    Parameters:
    - **user**: The user schema containing the username and password of the API user to be registered.
    - **db**: The database session obtained from the *get_db* dependency.
    - **current_user**: The currently authenticated admin user obtained from the *get_current_admin_user* dependency.

    Returns:
    - Success message with the username of the registered API user.

    Raises:
    - HTTPException (403): If the current user is not an admin.

    Example request body:
    ```json
    {
        "username": "api_user",
        "password": "password123"
    }
    ```

    Example response:
    ```json
    {
        "message": "API user 'api_user' created successfully"
    }
    ```

    """
    db_user = await crud.get_user_by_username(db, user.username)

    if db_user:
        raise HTTPException(status_code=400, detail=f"API user '{user.username}' already registered")
    else:
        hashed_password = auth.hash_password(user.password)
        db_user = await crud.create_api_user(db, user, hashed_password)

    return db_user


@app.post("/get-token", response_model=schemas.Token, summary="Get an access token",
          tags=["API Authentication"])
@limiter.limit("10/minute")
async def login_for_access_token(request: Request, db: AsyncSession = Depends(database.get_db), 
                                 form_data: OAuth2PasswordRequestForm = Depends()):
    """
    This endpoint allows an API user to obtain an access token by providing their username and password.

    Parameters:
    - **db**: The database session obtained from the *get_db* dependency.
    - **form_data**: The OAuth2 password request form containing the username and password of the API user.

    Returns:
    - The access token.

    Raises:
    - HTTPException (401): If the username or password is incorrect.

    Example request body:
    ```json
    {
        "username": "api_user",
        "password": "password123"
    }
    ```

    Example response:
    ```json
    {
        "access_token": "eyJ0eXA",
        "token_type": "bearer"
    }
    ```

    """
    user = await auth.authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth.create_access_token(data={"sub": user.username})

    return {"access_token": access_token, "token_type": "bearer"}

# ------------------------------
# API endpoints for database operations
# ------------------------------

@app.post("/create-database", status_code=201, summary="Create a new database",
          tags=["Database"])
@limiter.limit("10/minute")
async def create_database(request: Request, database: schemas.DatabaseCreate, db: AsyncSession = Depends(database.get_db),
                    current_user: schemas.User = Depends(permissions.get_current_active_user)):
    """

    This endpoint allows an authenticated user with or without admin privileges to create a new database.

    Parameters:
    - **database**: The database schema containing the name of the database to be created.
    - **db**: The database session obtained from the *get_db* dependency.
    - **current_user**: The currently authenticated user obtained from the *get_current_active_user* dependency.

    Returns:
    -  Success message with the name of the created database.

    Raises:
    - HTTPException (400): If the database already exists.

    Example request body:
    ```json
    {
        "name": "new_database"
    }
    ```

    Example response:
    ```json
    {
        "message": "Database 'new_database' created successfully"
    }
    ```

    """

    return await crud.create_database(db, database)


@app.post("/create-db-user", status_code=201, summary="Create a new database user",
          tags=["User"])
@limiter.limit("10/minute")
async def create_user(request: Request, user: schemas.DBUserCreate, db: AsyncSession = Depends(database.get_db),
                    current_user: schemas.User = Depends(permissions.get_current_admin_user)):
    """
    This endpoint allows an authenticated admin user to create a new database user.

    Parameters:
    - **user**: The user schema containing the host, username, password, database name, 
    and privileges of the database user to be created.
    - **db**: The database session obtained from the *get_db* dependency.
    - **current_user**: The currently authenticated admin user obtained from the *get_current_admin_user* dependency.

    Returns:
    - Success message with the username of the created database user.

    Raises:
    - HTTPException (500): If there is an error creating the database user.

    Example request body:
    ```json
    {
        "host": "localhost",
        "username": "db_user",
        "password": "password123"
        "db_name": "new_database",
        "privileges": "SELECT"
    }
    ```

    Example response:
    ```json
    {
        "message": "DB user 'db_user' created successfully"
    }
    ```
    
    
    """
    return await crud.create_db_user(db, user)


@app.post("/create-table", status_code=201, summary="Create a new table",
          tags=["Table"])
@limiter.limit("10/minute")
async def create_table(request: Request, tables: schemas.TableCreate, db: AsyncSession = Depends(database.get_db),
                    current_user: schemas.User = Depends(permissions.get_current_active_user)):
    """
    This endpoint allows an authenticated user to create a new table in a database.

    Parameters:
    - **tables**: The table schema containing the name of the database and the table to be created.
    - **db**: The database session obtained from the *get_db* dependency.
    - **current_user**: The currently authenticated user obtained from the *get_current_active_user* dependency.

    Returns:
    - Success message with the name of the created table.

    Raises:
    - HTTPException (400): If the table already exists.

    Example request body:
    ```json
    {
        "db_name": "new_database",
        "table_name": "new_table"
        "table_schema": {
            "id": "int",
            "name": "str",
            "age": "int"
        }
    }
    ```

    Example response:
    ```json
    {
        "message": "Table 'new_table' created successfully in database 'new_database'"
    }
    ```
    
    """
    return await crud.create_table(db, tables)


@app.post("/insert-data", status_code=201, summary="Insert data into a table",
          tags=["Data"])
@limiter.limit("10/minute")
async def insert_data(request: Request, data_insert: schemas.TableData, db: AsyncSession = Depends(database.get_db),
                current_user: schemas.User = Depends(permissions.get_current_admin_user)):
    """
    This endpoint allows an authenticated admin user to insert data into a table in a database.

    Parameters:
    - **data_insert**: The data schema containing the name of the database and table, and the data to be inserted.
    - **db**: The database session obtained from the *get_db* dependency.
    - **current_user**: The currently authenticated admin user obtained from the *get_current_admin_user* dependency.

    Returns:
    - Success message with the number of rows inserted.

    Raises:
    - HTTPException (404): If the table does not exist in the database.

    Example request body:
    ```json
    {
        "db_name": "new_database",
        "table_name": "new_table",
        "data": [
            {
                "id": 1,
                "name": "Alice",
                "age": 25
            },
            {
                "id": 2,
                "name": "Bob",
                "age": 30
            }
        ]
    }
    ```

    Example response:
    ```json
    {
        "message": "Data insertion completed for table 'new_table' in database 'new_database': 2 records added, 0 records updated"
    }
    ```

    """

    return await crud.insert_data(db, data_insert)


@app.get("/get-table/{db_name}/{table_name}", status_code=200, summary="Get table data",
         tags=["Table"])
@limiter.limit("10/minute")
async def get_table(request: Request, db_name: str, table_name: str, db: AsyncSession = Depends(database.get_db),
              current_user: schemas.User = Depends(permissions.get_current_admin_user)):
    """
    This endpoint allows an authenticated admin user to retrieve data from a table in a database.

    Parameters:
    - **db_name**: The name of the database.
    - **table_name**: The name of the table.
    - **db**: The database session obtained from the *get_db* dependency.
    - **current_user**: The currently authenticated admin user obtained from the *get_current_admin_user* dependency.

    Returns:
    - The data from the table.

    Raises:
    - HTTPException (404): If the table does not exist in the database.

    Example get request:
    ```
    GET /get-table/new_database/new_table
    ```

    Example response:
    ```json
    {
        "new_table": [
            {
                "id": 1,
                "name": "Alice",
                "age": 25
            },
            {
                "id": 2,
                "name": "Bob",
                "age": 30
            }
        ]
    }

    """

    table_fetch = schemas.TableIdentify(db_name=db_name, table_name=table_name)
    return await crud.get_table(db, table_fetch)


@app.delete("/delete-table/{db_name}/{table_name}", status_code=200, summary="Delete a table",
            tags=["Table"])
@limiter.limit("10/minute")
async def delete_table(request: Request, db_name: str, table_name: str, db: AsyncSession = Depends(database.get_db),
                 current_user: schemas.User = Depends(permissions.get_current_admin_user)):
    """
    This endpoint allows an authenticated admin user to delete a table from a database.

    Parameters:
    - **db_name**: The name of the database.
    - **table_name**: The name of the table.
    - **db**: The database session obtained from the *get_db* dependency.
    - **current_user**: The currently authenticated admin user obtained from the *get_current_admin_user* dependency.

    Returns:
    - Success message with the name of the deleted table.

    Raises:
    - HTTPException (404): If the table does not exist in the database.

    Example delete request:
    ```
    DELETE /delete-table/new_database/new_table
    ```

    Example response:
    ```json
    {
        "message": "Table 'new_table' deleted successfully from database 'new_database'"
    }

    """
    
    table_delete = schemas.TableIdentify(db_name=db_name, table_name=table_name)
    return await crud.delete_table(db, table_delete)


# ------------------------------
# Middleware for logging
# ------------------------------

# Logging middleware: middleware decorators are used to execute code before and after each request
@app.middleware("http")
async def log_requests_and_performance(request: Request, call_next):
    """
    Middleware function to log incoming requests, outgoing responses, and execution time.

    Args:
        request (Request): The incoming request object.
        call_next (Callable): The next middleware or endpoint to call.

    Returns:
        Response: The outgoing response object.
    """
    start_time = time.time()
    
    # Log incoming request
    logger.info(f"Incoming request: {request.method} {request.url}")
    
    response = await call_next(request)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Log outgoing response and execution time
    logger.info(f"Outgoing response: {response.status_code}, Endpoint: {request.method} {request.url.path},  " +
                f"Execution Time: {execution_time:.4f} seconds")
    
    return response
