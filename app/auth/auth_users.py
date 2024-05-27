from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.auth import hashing
from app.models import auth_models

# Custom imports
from app.utils.logging import setup_logging

# ------------------------------
# Set up logging
# ------------------------------

# Initialise logging
logger = setup_logging()

# ------------------------------
# Define user authentication function
# ------------------------------


# Function to retrieve user by their username
async def check_user_exists(db: AsyncSession, username: str):
    """
    Retrieve user from database by their username.

    Args:
        db (AsyncSession): database session.
        username (str): username of user to retrieve.

    Returns:
        User: user object if found, None otherwise.

    Raises:
        HTTPException: If there is an error retrieving user.

    """

    logger.info("auth_users.py ---> check_user_exists:")

    try:
        # Create query to retrieve user by their username
        query = select(auth_models.User).where(auth_models.User.username == username)
        result = await db.execute(query)  # Execute query
        user = result.scalars().first()  # Get first result

        # If user is None, log message and return None
        if not user:
            logger.info(f'API user "{username}" not found')
            return None

        logger.info(f'API user "{username}" details found')

        return user  # Return user object

    # If there is an error retrieving user, log error and raise exception
    except Exception as e:
        await db.rollback()  # Rollback transaction
        error_message = f'Error retrieving API user "{username}": {str(e)}'
        logger.error(error_message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
        )


# Function to authenticate user based on provided username and password
async def authenticate_user(db: AsyncSession, username: str, password: str):
    """
    Authenticate user by checking if provided username and password match
    stored credentials.

    Args:
        db (AsyncSession): database session.
        username (str): username of user to authenticate.
        password (str): password of user to authenticate.

    Returns:
        User: user object (username, hashed_password) if authentication
        succeeds, None otherwise.

    Raises:
        HTTPException (401): authentication fails due to invalid credentials.
    """

    logger.info("auth_users.py ---> authenticate_user:")

    # Check if user exists in database
    user = await check_user_exists(db, username)

    # If user is found and password is valid, return user object
    if user and hashing.verify_password(password, user.hashed_password):
        logger.info(f"API user '{username}' authenticated")
        return user

    # If authentication fails, log message and raise generic HTTPException
    message = "Invalid username or password"
    logger.error(message)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message)
