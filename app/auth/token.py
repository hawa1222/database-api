from fastapi import HTTPException, status
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

# Custom imports
from config import Settings
from app.utils.logging import setup_logging

# ------------------------------
# Set up logging
# ------------------------------

# Initialise logging
logger = setup_logging()

# ------------------------------
# Define authentication functions
# ------------------------------

minutes = Settings.TOKEN_EXPIRE_MINUTES


# Function to create an access token given user
def create_access_token(
        data: dict,
        expires_delta: timedelta = timedelta(minutes)
):
    '''
    Create access token for API user.

    Args:
        dat(dict): datto be encoded in access token (username)
        expires_delt(timedelta, optional): expiration time for access token.
        Defaults to timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES).

    Returns:
        str: encoded access token.

    Raises:
        HTTPException: If there is an error creating access token.
    '''

    logger.info('token.py ---> create_access_token:')

    try:
        to_encode = data.copy()  # Copy datto encode
        # Set expiration time for token using current time
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})  # Update datto encode
        # Encode token using data, secret key and algorithm
        encoded_jwt = jwt.encode(to_encode, Settings.TOKEN_SECRET_KEY,
                                 algorithm=Settings.TOKEN_ALGORITHM)

        logger.info('Encoding complete. Access token created for API user '
                    f'"{data.get('sub')}"')

        return {'access_token': encoded_jwt, 'token_type': 'bearer'}

    except Exception as e:
        logger.error(f'Error creating API user access token: {str(e)}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail='Internal server error')


def decode_token(token: str):
    '''
    Decodes provided token and extracts username.

    Args:
        token (str): authentication token.

    Returns:
        str: username extracted from token.

    Raises:
        HTTPException: If token is invalid or missing.
    '''

    logger.info('token.py ---> decode_token:')

    # Create an exception to handle invalid credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Invalid or missing token')

    try:
        # Decode token and extract username
        payload = jwt.decode(token, Settings.TOKEN_SECRET_KEY,
                             algorithms=[Settings.TOKEN_ALGORITHM])
        logger.info('Token decoded')
        username = payload.get('sub')  # Get username from token
        # If no username is found in token, raise exception
        if username is None:
            logger.error('Invalid token: No username found')
            raise credentials_exception

        logger.info(f'Token is valid. Username "{username}" '
                    f'extracted from token')

    # If token is invalid, raise exception
    except JWTError:
        logger.error('Invalid token: JWTError')
        raise credentials_exception

    return username
