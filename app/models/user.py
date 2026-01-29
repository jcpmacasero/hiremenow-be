# hiremenow-be/app/models/user.py
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, ENUM
from app.database import Base


class UserRole(str, PyEnum):
    ADMIN = "admin"
    EMPLOYER = "employer"
    CANDIDATE = "candidate"
    PARTNER = "partner"


# Use postgresql ENUM with lowercase values to match the database
userrole_enum = ENUM('admin', 'employer', 'candidate', 'partner', name='userrole', create_type=False)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # nullable for OAuth
    role = Column(userrole_enum, nullable=False, default='candidate')
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User {self.email}>"
