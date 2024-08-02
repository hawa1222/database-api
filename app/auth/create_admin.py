from sqlalchemy.future import select

from app.auth import hashing
from app.models import auth_models
from app.utils.logging import setup_logging
from config import Settings

# ------------------------------
# Set up logging
# ------------------------------

logger = setup_logging()

# ------------------------------
# Create admin user
# ------------------------------


async def create_admin_user(db):
    """
    Creates admin user in database if doesn't already exist.

    Checks if an admin user already exists in database.
    If yes, logs message and skips creation process.
    If no, creates new admin user by hashing str password,
    adding User object (id, username, hashed_password, is_admin) to database

    Parameters:
        db (AsyncSession): Async database session.

    Returns:
        None

    Raises:
        Exception: If error creating admin user.
    """

    logger.debug("Creating admin user...")

    try:
        query = select(auth_models.User).where(auth_models.User.username == Settings.API_ADM_USER)
        user = await db.execute(query)  # Check if admin user already exists
        admin_user = user.scalars().first()

        if admin_user:
            logger.warning(
                f"Admin user '{Settings.API_ADM_USER}' already exists, skipping creation."
            )
        else:
            hashed_password = hashing.hash_password(Settings.API_ADM_PASSWORD)
            admin_user = auth_models.User(
                username=Settings.API_ADM_USER, hashed_password=hashed_password, is_admin=True
            )
            db.add(admin_user)
            logger.debug("Admin user added to database")
            await db.commit()
            logger.info(f"Admin user '{Settings.API_ADM_USER}' created successfully.")

    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        raise
