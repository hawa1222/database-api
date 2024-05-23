from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

# Custom imports
from config import Settings
from app.utils.logging import setup_logging

from app.schemas import auth_schemas
from app.crud import auth_crud
from app.auth import auth_users, hashing, token, permissions
from app.database import db_connect

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

# ------------------------------
# API routes & endpoints for authentication
# ------------------------------


# Register new API user
@router.post('/register-api-user', status_code=201,
             summary='Register new API user', tags=['API Authentication'])
@limiter.limit(Settings.API_RATE_LIMIT)
async def register_api_user(
    request: Request,
    user: auth_schemas.UserCreate,
    db: AsyncSession = Depends(db_connect.get_db),
    current_user: auth_schemas.UserCreate = Depends(permissions.admin_user)
):
    '''
    Endpoint allows authenticated admin user to register new API user.

    Parameters:
    - **user**: user schemcontaining username and
    password of API user to be registered.
    - **db**: database session obtained from *get_db* dependency.
    - **current_user**: currently authenticated admin user obtained
    from *admin_user* dependency.

    Returns:
    - Success message with username of registered API user.

    Raises:
    - HTTPException (403): If current user is not an admin.

    Example request body:
    ```json
    {
        'username': 'api_user',
        'password': 'password123'
        'is_admin': True
    }
    ```

    Example response:
    ```json
    {
        "message": 'API user "api_user" created successfully"
    }
    ```
    '''

    logger.info('auth_routes.py ---> register_api_user:')

    # Check if user exists
    db_user = await auth_users.check_user_exists(db, user.username)

    if db_user:  # If user is not None (i.e. user exists)
        message = f'API user "{user.username}" already registered'
        logger.error(message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    else:
        # Hash password
        hashed_password = hashing.hash_password(user.password)
        # Create user
        message = await auth_crud.create_api_user(db, user, hashed_password)

    return message


# Create and return an access token
@router.post('/get-token', response_model=auth_schemas.Token, status_code=200,
             summary='Get an access token', tags=['API Authentication'])
@limiter.limit(Settings.API_RATE_LIMIT)
async def get_access_token(
    request: Request,
    db: AsyncSession = Depends(db_connect.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    '''
    Endpoint allows API user to obtain access token
    by providing their username and password.

    Parameters:
    - **db**: database session obtained from *get_db* dependency.
    - **form_data**: OAuth2 password request form containing username
    and password of API user.

    Returns:
    - access token.

    Raises:
    - HTTPException (401): If username is not found in database.
    - HTTPException (403): If user not admin or password is invalid.

    Example request body:
    ```json
    {
        'username': 'api_user",
        'password': 'password123'
    }
    ```

    Example response:
    ```json
    {
        'access_token': 'eyJ0eXA',
        'token_type': 'bearer"
    }
    ```
    '''
    logger.info('auth_routes.py ---> get_access_token:')

    # Authenticate user
    user = await auth_users.authenticate_user(db, form_data.username,
                                              form_data.password)

    # Create access token
    access_token = token.create_access_token(data={'sub': user.username})

    return access_token
