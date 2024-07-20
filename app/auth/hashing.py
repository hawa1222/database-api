from passlib.hash import bcrypt

# Custom imports
from app.utils.logging import setup_logging

# ------------------------------
# Set up logging
# ------------------------------

# Initialise logging
logger = setup_logging()

# ------------------------------
# Define hashing functions
# ------------------------------


def hash_password(password):
    """
    Hashes given password using bcrypt.

    Parameters:
        password (str): password to be hashed.

    Returns:
        str: hashed password.
    """

    logger.info("hashing.py ---> hash_password:")

    hashed_password = bcrypt.hash(password)
    logger.info("Password hashed")

    return hashed_password


def verify_password(plain_password, hashed_password):
    """
    Verify if plain password matches hashed password.

    Parameters:
        plain_password (str): plain password to verify.
        hashed_password (str): hashed password to compare against.

    Returns:
        bool: True if plain password matches hashed password,
        False otherwise.
    """

    logger.info("hashing.py ---> verify_password:")

    password_verified = bcrypt.verify(plain_password, hashed_password)

    if password_verified:
        logger.info("Password verified")
    else:
        logger.error("Password incorrect")

    return password_verified
