from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.utils.logging import setup_logging
from config import Settings

# ------------------------------
# Set up logging
# ------------------------------

logger = setup_logging()

# ------------------------------
# Define authentication functions
# ------------------------------


def create_access_token(data, expires_delta=timedelta(Settings.TOKEN_EXPIRE_MINUTES)):
    """
    Create access token for API user.

    Parameters:
        data (dict): Data to be encoded in access token (username)
        expires_delt (timedelta, optional): expiration time for access token.
        Defaults to 60 minutes.

    Returns:
        JWT (dict): Access token and token type.

    Raises:
        HTTPException: If error creating access token.
    """

    logger.debug("Creating API OAuth2 access token...")

    try:
        to_encode = data.copy()
        expire = datetime.now(UTC) + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, Settings.TOKEN_SECRET_KEY, algorithm=Settings.TOKEN_ALGORITHM
        )  # Create access token using username, expiration time, and secret key

        logger.debug(
            "Encoding complete. Access token created for API user "
            f"'{data.get('sub')}'"
        )

        return {"access_token": encoded_jwt, "token_type": "bearer"}

    except Exception as e:
        logger.error(f"Error creating API user access token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


def decode_token(token):
    """
    Decodes provided token and extracts username.

    Parameters:
        token (str): Authentication token.

    Returns:
        username (str): Username extracted from token.

    Raises:
        HTTPException: If token is invalid or missing.
    """

    logger.debug("Decoding access token...")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing token"
    )

    try:
        payload = jwt.decode(
            token, Settings.TOKEN_SECRET_KEY, algorithms=[Settings.TOKEN_ALGORITHM]
        )  # Decode token using secret key
        logger.debug("Token decoded")
        username = payload.get("sub")  # Extract username from token

        if username is None:
            logger.error("Invalid token: No username found")
            raise credentials_exception

        logger.debug(f"Token is valid. Username '{username}' extracted")

    except JWTError:
        logger.error("Invalid token: JWTError")
        raise credentials_exception

    return username
