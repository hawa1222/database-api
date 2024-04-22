import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.hash import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone

# Custom imports
from app.database.crud import get_user_by_username
from app.database.database import get_db
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
SECRET_KEY = os.getenv('SECRET_KEY')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 60))
ALGORITHM = "HS256"

# ------------------------------
# Set up authentication and authorisation
# ------------------------------

# Set up the OAuth2 password bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="get-token")

# ------------------------------
# Define the authentication functions
# ------------------------------

def hash_password(password):
    """
    Hashes the given password using bcrypt.

    Args:
        password (str): The password to be hashed.

    Returns:
        str: The hashed password.
    """

    logger.info(f"authy.py get_password_hash:")

    hashed_password = bcrypt.hash(password)
    logger.info(f"Password hashed")

    return hashed_password

def verify_password(plain_password, hashed_password):
    """
    Verify if a plain password matches a hashed password.

    Args:
        plain_password (str): The plain password to verify.
        hashed_password (str): The hashed password to compare against.

    Returns:
        bool: True if the plain password matches the hashed password, False otherwise.
    """

    logger.info(f"authy.py verify_password:")

    password_verified = bcrypt.verify(plain_password, hashed_password)
    logger.info(f"Password verified")

    return password_verified

async def get_current_user(db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """
    Retrieves the current user based on the provided token.

    Args:
        db (AsyncSession): The database session.
        token (str): The authentication token.

    Returns:
        User: The current user: id, username, password and admin status.

    Raises:
        HTTPException: If the token is not provided or is invalid.
    """

    logger.info("authy.py get_current_user:")
    
    # Create an exception to handle invalid credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise HTTPException(status_code=400, detail="Token not provided")
    
    logger.info(f"Token received")

    try:
        # Decode the token and extract the username
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info(f"Token decoded")
        username: str = payload.get("sub")

        # If no username is found in the token, raise an exception
        if username is None:
            logger.warning("Invalid token: No username found")
            raise credentials_exception

        logger.info(f"Token is valid. Username '{username}' extracted from token")

    except JWTError:
        logger.warning("Invalid token: JWTError")
        raise credentials_exception
    
    # Get the user from the database based on the username
    user = await get_user_by_username(db, username)

    # If no user is found in the database, raise an exception
    if user is None:
        logger.warning(f"API user '{username}' not found in database")
        raise credentials_exception

    logger.info(f"API user '{username}' found in database, is_admin set to '{user.is_admin}'")
    
    return user

async def authenticate_user(db: AsyncSession, username: str, password: str):
    """
    Authenticates a user by checking if the provided username and password match the stored credentials.

    Args:
        db (AsyncSession): The database session.
        username (str): The username of the user to authenticate.
        password (str): The password of the user to authenticate.

    Returns:
        Union[User, bool]: The authenticated user object if the credentials are valid, False otherwise.
    """

    logger.info(f"authy.py authenticate_user:")

    user = await get_user_by_username(db, username)
    if not user:
        logger.warning(f"API user '{username}' not found")
        return False
    if not verify_password(password, user.hashed_password):
        logger.warning(f"Invalid password for API user '{username}'")
        return False
    logger.info(f"API user '{username}' authenticated")

    return user

def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    """
    Create an access token for the API user.

    Args:
        data (dict): The data to be encoded in the access token (username)
        expires_delta (timedelta, optional): The expiration time for the access token.
            Defaults to timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES).

    Returns:
        str: The encoded access token.

    Raises:
        HTTPException: If there is an error creating the access token.
    """
    
    logger.info(f"authy.py create_access_token:")

    try:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode.update({"exp": expire})
        # Encode the token using the secret key and algorithm
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.info(f"Encoding complete. Access token created for API user '{data.get('sub')}'")
        return encoded_jwt
    
    except Exception as e:
        logger.error(f"Error creating API user access token: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
