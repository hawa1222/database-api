from sqlalchemy import Column, Integer, String, Boolean

# Custom imports
from app.database.db_connect import Base

# ------------------------------
# Define database models
# ------------------------------


# Define User model
# Inherits from Base class, represents users table in database
class User(Base):
    __tablename__ = "api_users"  # Table name in database

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(255))
    is_admin = Column(Boolean, default=False)
