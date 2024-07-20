from fastapi import HTTPException
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import auth_models

# Custom imports
from app.schemas import auth_schemas
from app.utils.logging import setup_logging

# ------------------------------
# Set up logging
# ------------------------------

# Initialise logger
logger = setup_logging()

# ------------------------------
# Authentication and Authorisation
# ------------------------------


# Function to create an API user
async def create_api_user(db: AsyncSession, user: auth_schemas.UserCreate, hashed_password: str):
    """
    Create an API user in database.

    Parameters:
        db (AsyncSession): database session.
        user (schemas.UserCreate): user object containing username,
        password, and is_admin flag.
        hashed_password (str): hashed password for user.

    Returns:
        dict: dictionary containing success message or an error message.

    Raises:
        HTTPException: If there is an error creating API user.
    """

    logger.info("auth_crud.py ---> create_api_user:")

    try:
        # Create new user object
        db_user = auth_models.User(
            username=user.username, hashed_password=hashed_password, is_admin=user.is_admin
        )
        db.add(db_user)  # Add user to database
        await db.commit()  # Commit transaction
        await db.refresh(db_user)  # Refresh user object

        message = f"API user '{user.username}' created successfully"
        logger.info(message)

        return {"message": message}  # Return success message

    # If there is an error creating user, log error and raise exception
    except Exception as e:
        db.rollback()  # Rollback transaction
        error_message = f"Error creating API user '{user.username}': {str(e)}"
        logger.error(error_message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
        )
