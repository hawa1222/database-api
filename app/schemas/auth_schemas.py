from pydantic import BaseModel
from pydantic import Field

# ------------------------------
# Database User Model
# ------------------------------


class DBUserCreate(BaseModel):
    """
    Represents database user creation request.
    """

    host: str = Field("localhost", min_length=1, max_length=255)
    username: str = Field("testing", min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=100)
    privileges: str = Field("SELECT", min_length=1, max_length=100)
    db_name: str = Field("testdb", pattern=r"^[a-z][a-z0-9_]*$", min_length=1, max_length=30)


# ------------------------------
# Authentication and Authorisation
# ------------------------------


class User(BaseModel):
    id: int
    username: str
    hashed_password: str
    is_admin: bool | None = False


class UserCreate(BaseModel):
    username: str
    password: str
    is_admin: bool | None = False


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
