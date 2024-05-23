from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

# Custom imports
from config import Settings
from app.utils.logging import setup_logging

from app.models import auth_models
from app.auth import hashing

# ------------------------------
# Set up logging
# ------------------------------

# Initialise logging
logger = setup_logging()

# ------------------------------
# Create admin user
# ------------------------------


# Function to create an admin user
async def create_admin_user(db: AsyncSession):
    '''
    Creates an admin user in database if it doesn't already exist.

    This function checks if admin user already exists in database.
    If it does, function logs message and skips creation process.
    If admin user doesn't exist, function creates new admin user
    with provided username and password, hashes password, and adds
    user to database.

    Args:
        None

    Returns:
        None
    '''

    logger.info('create_admin.py ---> create_admin_user:')

    # Check if admin user already exists
    query = select(auth_models.User).where(
        auth_models.User.username == Settings.API_ADM_USER)
    user = await db.execute(query)  # Execute query
    admin_user = user.scalars().first()  # Get first result

    # If admin_user is not None:
    if admin_user:
        logger.info(f'Admin user "{Settings.API_ADM_USER}" '
                    f'already exists, skipping creation.')
    else:
        # Create admin user
        hashed_password = hashing.hash_password(Settings.API_ADM_PASSWORD)
        admin_user = auth_models.User(
            username=Settings.API_ADM_USER,
            hashed_password=hashed_password,
            is_admin=True
        )
        db.add(admin_user)  # Add user to database
        logger.info('Admin user added to database')
        await db.commit()  # Commit transaction
        logger.info(f'Admin user "{Settings.API_ADM_USER}" created '
                    f'successfully.')
