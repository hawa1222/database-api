import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

# Custom imports
from app.utils.logging import setup_logging

# ------------------------------
# Set up logging
# ------------------------------

# Initialise logging
logger = setup_logging()

# ------------------------------
# Environment variables
# ------------------------------

# Load environment variables from the .env file
load_dotenv()

# Load environment variables
MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_PORT = os.getenv('MYSQL_PORT')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')

# ------------------------------
# Database connection
# ------------------------------

# Define the database URL
DATABASE_URL = f"mysql+aiomysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
# Create an asynchronous database engine, echo=False to disable logging
engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
# Create an asynchronous session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
# Create a base class for the database models
Base = declarative_base()

# ------------------------------
# Database connection function
# ------------------------------

# Function to get the database connection
async def get_db():
    """
    Returns a database session for performing database operations.

    Returns:
        SessionLocal: The database session object.

    Raises:
        None

    """
    db = SessionLocal()
    try:
        logger.info('Primary database connection established')
        yield db
    finally:
        await db.close()
        logger.info("Database connection closed")
