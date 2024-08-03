from sqlalchemy import Boolean, Column, Integer, String

from app.database.db_connect import Base

# ------------------------------
# Define database models
# ------------------------------


class User(Base):
    __tablename__ = "api_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    hashed_password = Column(String(255))
    is_admin = Column(Boolean, default=False)
