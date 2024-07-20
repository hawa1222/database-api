from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from app.utils.logging import setup_logging

# Custom imports
from config import Settings

# ------------------------------
# Set up logging
# ------------------------------

# Initialise logging
logger = setup_logging()

# ------------------------------
# Database connection
# ------------------------------

"""
When you call create_async_engine in SQLAlchemy, it automatically sets up a
pool of connections to database specified by DATABASE_URL.
pool_pre_ping=True option enables feature where SQLAlchemy will test
availability of database connection before returning it from pool,
which can help to avoid errors due to stale or disconnected connections.
"""

# Create asynchronous engine, echo=False to disable logging of SQL queries
engine = create_async_engine(Settings.DATABASE_URL, echo=False, pool_pre_ping=True)

# Create an asynchronous session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

# Create base class for database models
Base = declarative_base()

# ------------------------------
# Database connection function
# ------------------------------


# Function to get database connection
async def get_db():
    """
    Returns database session for performing database operations.

    Returns:
        SessionLocal: database session object.

    Raises:
        None
    """

    logger.info("db_connect.py ---> get_db:")
    db = SessionLocal()  # Create new database session
    session_id = hash(db)  # Get session ID

    try:
        logger.info(
            f"Database connection picked from connection pool. " f"Session ID: {session_id}"
        )
        yield db
    finally:
        try:
            await db.close()
            logger.info(f"Database connection closed. Session ID: {session_id}")
        except RuntimeError as e:
            if "Event loop is closed" not in str(e):
                raise
