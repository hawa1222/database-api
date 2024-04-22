import os
from sqlalchemy.future import select

# Custom imports
from app.utils.logging import setup_logging
from app.database.database import SessionLocal
from app.database.models import User
from app.auth.auth import hash_password

# ------------------------------
# Set up logging
# ------------------------------

# Initialise logging
logger = setup_logging()

# ------------------------------
# Environment variables
# ------------------------------

# Load environment variables
API_ADMIN_USER = os.getenv('API_ADMIN_USER')
API_ADMIN_PASSWORD = os.getenv('API_ADMIN_PASSWORD')

# ------------------------------
# Create the admin user
# ------------------------------

async def create_admin_user():
    """
    Creates an admin user in the database if it doesn't already exist.

    This function checks if the admin user already exists in the database. If it does, the function
    logs a message and skips the creation process. If the admin user doesn't exist, the function
    creates a new admin user with the provided username and password, hashes the password, and adds
    the user to the database.

    Args:
        None

    Returns:
        None
    """
    
    logger.info(f"create_admin.py create_admin_user:")

    # Create a database session
    async with SessionLocal() as db:

        # Check if the admin user already exists
        query = select(User).where(User.username == API_ADMIN_USER)
        user = await db.execute(query)
        admin_user = user.scalars().first()
        if admin_user:
            logger.info(f"Admin user '{API_ADMIN_USER}' already exists, skipping creation.")
        else:
            # Create the admin user
            hashed_password = hash_password(API_ADMIN_PASSWORD)
            admin_user = User(username=API_ADMIN_USER, hashed_password=hashed_password, is_admin=True)
            db.add(admin_user)
            logger.info('Admin user added to the database')
            await db.commit()
            logger.info(f"Admin user '{API_ADMIN_USER}' created successfully.")
