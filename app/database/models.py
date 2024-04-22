from sqlalchemy import Column, Integer, String, Boolean

# Custom imports
from app.database.database import Base

# ------------------------------
# Define the database models
# ------------------------------

# Define the User model, which inherits from the Base class, to represent the users table in the database
class User(Base):
    __tablename__ = "api_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(255))
    is_admin = Column(Boolean, default=False)