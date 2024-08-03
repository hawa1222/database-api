from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.auth import authenticate, token
from app.database import db_connect
from app.schemas import auth_schemas
from app.utils.logging import setup_logging

# ------------------------------
# Set up logging
# ------------------------------

logger = setup_logging()

# ------------------------------
# Set up OAuth2 password bearer
# ------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="get-token")

# ------------------------------
# User permissions
# ------------------------------


async def active_user(db=Depends(db_connect.get_db), access_token=Depends(oauth2_scheme)):
    """
    Fetches current user based on provided token.

    Parameters:
        db (AsyncSession): Async database session.
        token (str): Authentication token.

    Returns:
        user (schema.User): User object (id, username, hashed_password and admin status).

    Raises:
        HTTPException (401): If token is invalid.
    """

    logger.debug("Processing API token for active user...")

    username = token.decode_token(access_token)

    user = await authenticate.check_user_exists(db, username)

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = auth_schemas.User(**user.__dict__)

    logger.info(f"API user '{user.username}' authenticated, admin status is'{user.is_admin}'")

    return user


async def admin_user(current_user: auth_schemas.User = Depends(active_user)):
    """
    Checks if current user has admin status.

    Parameters:
        current_user (schema.User): User object (id, username, hashed_password and admin status).

    Returns:
        current_user (schema.User): User object.

    Raises:
        HTTPException (403): If user is not admin.
    """

    if not current_user.is_admin:
        error_message = (
            f"Unauthorised access, admin access required. "
            f"Current admin status is '{current_user.is_admin}'"
        )
        logger.error(error_message)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_message)

    return current_user
