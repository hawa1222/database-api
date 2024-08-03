from fastapi import HTTPException, status
from sqlalchemy.future import select

from app.auth import hashing
from app.models import auth_models
from app.utils.logging import setup_logging

# ------------------------------
# Set up logging
# ------------------------------

logger = setup_logging()

# ------------------------------
# Define user authentication functions
# ------------------------------


async def check_user_exists(db, username):
    """
    Fetches user details from database based on username.

    Parameters:
        db (AsyncSession): Async database session.
        username (str): Username of user to check.

    Returns:
        User: User object (id, username, hashed_password, is_admin) if user exists,

    Raises:
        HTTPException (500): If error retrieving user.
    """
    logger.debug("Checking if user exists in database...")

    try:
        query = select(auth_models.User).where(auth_models.User.username == username)
        result = await db.execute(query)
        user = result.scalars().first()

        if not user:
            logger.warning(f"API user '{username}' not found in database")
            return None

        return user

    except Exception as e:
        await db.rollback()
        error_message = f"Error occurred checking if user '{username}' exists"
        logger.error(error_message + f": {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
        )


async def authenticate_user(db, username, password):
    """
    Authenticate user by checking if provided username and password match
    stored credentials.

    Parameters:
        db (AsyncSession): Async database session.
        username (str): Username of user.
        password (str): Password of user.

    Returns:
        user: User object (id, username, hashed_password, is_admin) if authentication
        succeeds, None otherwise.

    Raises:
        HTTPException (401): Authentication fails due to invalid credentials.
    """

    logger.debug("Authenticating provided user credentials...")

    user = await check_user_exists(db, username)

    if user and hashing.verify_password(password, user.hashed_password):
        logger.info(f"API user '{username}' exists and credentials are valid")
        return user

    message = "Invalid username or password"
    logger.error(message)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)
