from fastapi import HTTPException
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import auth_models
from app.schemas import auth_schemas
from app.utils.logging import setup_logging

# ------------------------------
# Set up logging
# ------------------------------

logger = setup_logging()

# ------------------------------
# Authentication and Authorisation
# ------------------------------


async def create_api_user(db: AsyncSession, user: auth_schemas.UserCreate):
    """
    Creates API user in database.

    Parameters:
        db (AsyncSession): Async database session.
        user (Pydantic model): User object (username, password (hashed), is_admin status).

    Returns:
        dict: Success message with username of registered API user.

    Raises:
        HTTPException (500): If error creating API user.
    """
    logger.debug("Creating API user...")

    try:
        db_user = auth_models.User(
            username=user.username, hashed_password=user.password, is_admin=user.is_admin
        )  # Create user object
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        message = f"API user '{user.username}' created successfully"
        logger.info(message)

        return {"message": message}

    except Exception as e:
        db.rollback()
        error_message = f"Error occurred creating API user '{user.username}'"
        logger.error(error_message + f": {str(e.orig)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_message
        )
