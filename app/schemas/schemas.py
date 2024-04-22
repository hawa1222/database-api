from pydantic import BaseModel, Field
from typing import Any, Union, Dict, List

# ------------------------------
# Field Validators
# ------------------------------
 
# Define a reusable field validator
db_name_field = Field(default='testdb', pattern=r'^[\w\d_]+$', min_length=1, max_length=30)
table_name_field = Field(default='users', pattern=r'^[\w\d_]+$', min_length=1, max_length=30)

# ------------------------------
# Database 
# ------------------------------

class DBUserCreate(BaseModel):
    """
    Represents a database user creation request.
    """
    
    host: str = Field('localhost', min_length=1, max_length=255)
    username: str = Field('testing', min_length=1, max_length=255)
    password: str = Field(..., min_length=1, max_length=255)
    db_name: str = db_name_field
    privileges: str = Field('SELECT', min_length=1, max_length=255)

# ------------------------------
# Database operations
# ------------------------------

class DatabaseCreate(BaseModel):
    db_name: str = db_name_field

class TableIdentify(BaseModel):
    db_name: str = db_name_field
    table_name: str = table_name_field

class TableCreate(TableIdentify):
    table_schema: Dict[str, str]

class TableData(TableIdentify):
    data: List[Dict[str, Any]]


# ------------------------------
# Authentication and Authorization
# ------------------------------

class User(BaseModel):
    username: str

class UserCreate(User):
    password: str
    is_admin: bool = False

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Union[str, None] = None