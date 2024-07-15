from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import authenticate, token
from app.database import db_connect
from app.schemas import auth_schemas

# Custom imports
from app.utils.logging import setup_logging

# ------------------------------
# Set up logging
# ------------------------------

# Initialise logging
logger = setup_logging()

# ------------------------------
# Set up OAuth2 password bearer
# ------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="get-token")

# ------------------------------
# User permissions
# ------------------------------


# Function to get current user based on provided token
async def active_user(
    db: AsyncSession = Depends(db_connect.get_db),
    access_token: str = Depends(oauth2_scheme),
):
    """
    Retrieves current user based on provided token.

    Args:
        db (AsyncSession): database session.
        token (str): authentication token.

    Returns:
        User: current user: id, username, hashed_password and admin status.

    Raises:
        HTTPException: If token is invalid.
    """

    logger.info("authorise.py ---> active_user:")

    logger.info("Token received")

    # Decode token and extract username
    username = token.decode_token(access_token)

    # Get user from database based on username
    user = await authenticate.check_user_exists(db, username)

    # If no user found in database, raise exception
    if user is None:
        logger.warning(f'API user "{username}" not found in database')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    user = auth_schemas.User(**user.__dict__)

    logger.info(
        f'API user "{user.username}" found in database, '
        f'is_admin set to "{user.is_admin}"'
    )

    return user


# Function to get current admin user
async def admin_user(current_user: auth_schemas.User = Depends(active_user)):
    """
    Get current admin user.

    Args:
        current_user (UserCreate): current user.

    Returns:
        UserCreate: current active user object containing username,
        password and admin status.

    Raises:
        HTTPException: If current user not an admin.
    """

    logger.info("authorise.py ---> admin_user:")

    # If current user.is_admin is False or None, raise exception
    if not current_user.is_admin:
        error_message = (
            "Unauthorised access, admin access required. "
            f'Current admin status is "{current_user.is_admin}"'
        )
        logger.error(error_message)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_message)

    return current_user
