from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import authenticate, authorise, hashing, token
from app.crud import auth_crud
from app.database import db_connect
from app.schemas import auth_schemas
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
# API routes & endpoints for authentication
# ------------------------------


@router.post(
    "/register-api-user",
    status_code=201,
    summary="Register new API user",
    tags=["API Authentication"],
)
@limiter.limit(Settings.API_RATE_LIMIT)
async def register_api_user(
    request: Request,
    user: auth_schemas.UserCreate,
    db: AsyncSession = Depends(db_connect.get_db),
    current_user: auth_schemas.UserCreate = Depends(authorise.admin_user),
):
    """
    Endpoint allows authenticated admin user to register new API user.

    Parameters:
        **user**: Pydantic model containing username, password, is_admin flag of
        API user to be registered.
        **db**: Async database session obtained from *get_db* dependency.
        **current_user**: Active authenticated admin user obtained from *admin_user* dependency.

    Returns:
        dict: Success message with username of registered API user.

    Raises:
        HTTPException (400): If API user already exists.
        HTTPException (403): If current user is not an admin.
        HTTPException (500): If any other error occurs.

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
    """

    logger.debug(f"Registering new API user '{user.username}'...")

    db_user = await authenticate.check_user_exists(db, user.username)

    if db_user:
        message = f"API user '{user.username}' already registered"
        logger.error(message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)
    else:
        hashed_password = hashing.hash_password(user.password)
        user.password = hashed_password  # Update password with hashed password
        message = await auth_crud.create_api_user(db, user)

    return message


@router.post(
    "/get-token",
    response_model=auth_schemas.Token,
    status_code=200,
    summary="Get an access token",
    tags=["API Authentication"],
)
@limiter.limit(Settings.API_RATE_LIMIT)
async def get_access_token(
    request: Request,
    db: AsyncSession = Depends(db_connect.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    Endpoint allows API user to obtain access token by providing their username and password.

    Parameters:
        **db**: Async database session obtained from *get_db* dependency.
        **form_data**: OAuth2 password request form containing username & password of API user.

    Returns:
        dict: Access token and token type.

    Raises:
        HTTPException (401): If API user not found in database.
        HTTPException (500): If any other error occurs.

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
    """
    logger.debug("Executing get-token endpoint...")

    user = await authenticate.authenticate_user(db, form_data.username, form_data.password)

    access_token = token.create_access_token(data={"sub": user.username})

    return access_token
