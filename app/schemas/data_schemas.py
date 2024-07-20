from typing import Any
from typing import Dict
from typing import List

from pydantic import BaseModel
from pydantic import Field

# ------------------------------
# Field Validators
# ------------------------------

"""
Define reusable field validators

1. Starts with lowercase letter ([a-z])
2. Followed by any combination of lowercase letters,
digits, or underscores ([a-z0-9_]*)
3. Does not contain any uppercase letters, spaces, or special characters
"""

db_name_field = Field(default="testdb", pattern=r"^[a-z][a-z0-9_]*$", min_length=1, max_length=30)

table_name_field = Field(
    default="users", pattern=r"^[a-z][a-z0-9_]*$", min_length=1, max_length=30
)

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
