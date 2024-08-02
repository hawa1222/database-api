from passlib.hash import bcrypt

from app.utils.logging import setup_logging

# ------------------------------
# Set up logging
# ------------------------------

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

    logger.debug("Hashing password...")

    hashed_password = bcrypt.hash(password)
    logger.info("Password hashed")

    return hashed_password


def verify_password(plain_password, hashed_password):
    """
    Verifies plain password against hashed password.

    Parameters:
        plain_password (str): plain password to verify.
        hashed_password (str): hashed password to compare against.

    Returns:
        password_verified (bool): True if plain password matches hashed password,
        False otherwise.
    """

    logger.debug("Verifying hashed password...")

    password_verified = bcrypt.verify(plain_password, hashed_password)

    if password_verified:
        logger.info("Password verified")
    else:
        logger.error("Password incorrect")

    return password_verified
