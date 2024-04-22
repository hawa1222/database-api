from fastapi import Depends, HTTPException, status

# Custom imports
from app.utils.logging import setup_logging
from app.auth.auth import get_current_user
from app.schemas.schemas import UserCreate

# ------------------------------
# Set up logging
# ------------------------------

# Initialise logging
logger = setup_logging()

# ------------------------------
# Set up permissions
# ------------------------------

# Function to get the current active user
async def get_current_active_user(current_user: UserCreate = Depends(get_current_user)):
    """
    Get the current active user.

    Args:
        current_user (UserCreate): The current user object.

    Returns:
        UserCreate: The current active user object containing username, password and admin status.

    Raises:
        HTTPException: If the authentication credentials are invalid.
    """
    
    logger.info(f"permissions.py get_current_active_user:")
    
    if not current_user:
        error_message = "Invalid authentication credentials"
        logger.error(error_message)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error_message)

    return current_user

# Function to get the current admin user
async def get_current_admin_user(current_user: UserCreate = Depends(get_current_active_user)):
    """
    Get the current admin user.

    Args:
        current_user (UserCreate): The current user.

    Returns:
        UserCreate: The current active user object containing username, password and admin status.

    Raises:
        HTTPException: If the current user is not an admin.
    """

    logger.info(f"permissions.py get_current_admin_user:")

    if not current_user.is_admin:
        error_message = f"Unauthorised access, admin access required. Current admin status is '{current_user.is_admin}'"
        logger.error(error_message)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_message)

    return current_user
