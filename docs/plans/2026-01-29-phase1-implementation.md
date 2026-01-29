# Phase 1: Foundation (MVP) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the foundational backend and admin panel for managing companies, employers, candidates, jobs, and a fixed pipeline with manual stage advancement.

**Architecture:** FastAPI backend with SQLAlchemy ORM, PostgreSQL database, JWT authentication. React frontend with React Router, TanStack Query, and shadcn/ui components. Role-based access control with Admin, Employer, and Candidate roles.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL, JWT (python-jose), React 19, TypeScript, Vite, TanStack Query, React Router v6, Tailwind CSS, shadcn/ui

---

## Task 1: Backend Project Structure

**Files:**
- Create: `hiremenow-be/app/__init__.py`
- Create: `hiremenow-be/app/main.py`
- Create: `hiremenow-be/app/config.py`
- Create: `hiremenow-be/app/database.py`

**Step 1: Create app package init**

```python
# hiremenow-be/app/__init__.py
```

(Empty file to make it a package)

**Step 2: Create config module**

```python
# hiremenow-be/app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str

    # App
    environment: str = "development"
    debug: bool = True
    api_version: str = "v1"

    # Security
    secret_key: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    cors_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Step 3: Create database module**

```python
# hiremenow-be/app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Step 4: Create main FastAPI app**

```python
# hiremenow-be/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="HireMeNow API",
    description="Recruitment Agency Platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS
origins = [origin.strip() for origin in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "environment": settings.environment}
```

**Step 5: Create .env file from example**

```bash
cd hiremenow-be && cp .env.example .env
```

Edit `.env` with actual values:
```
DATABASE_URL=postgresql://hiremenow:devpassword123@localhost:54321/hiremenow_db
POSTGRES_USER=hiremenow
POSTGRES_PASSWORD=devpassword123
POSTGRES_DB=hiremenow_db
POSTGRES_HOST=postgres
POSTGRES_PORT=54321
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production
API_VERSION=v1
CORS_ORIGINS=http://localhost:5173
JWT_SECRET_KEY=jwt-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
HOST=0.0.0.0
PORT=8000
```

**Step 6: Test the setup**

Run: `cd hiremenow-be && docker compose -f docker-compose.linux.yml up --build`

Expected: Services start, backend accessible at `http://localhost:8000/api/health`

**Step 7: Commit**

```bash
git add hiremenow-be/app hiremenow-be/.env
git commit -m "feat(backend): add FastAPI project structure with config and database"
```

---

## Task 2: Alembic Setup & User Model

**Files:**
- Create: `hiremenow-be/alembic.ini`
- Create: `hiremenow-be/alembic/env.py`
- Create: `hiremenow-be/alembic/script.py.mako`
- Create: `hiremenow-be/alembic/versions/` (directory)
- Create: `hiremenow-be/app/models/__init__.py`
- Create: `hiremenow-be/app/models/user.py`

**Step 1: Initialize Alembic**

Run: `cd hiremenow-be && alembic init alembic`

**Step 2: Update alembic.ini**

Edit `hiremenow-be/alembic.ini`, find `sqlalchemy.url` line and set:
```ini
sqlalchemy.url = postgresql://hiremenow:devpassword123@localhost:54321/hiremenow_db
```

**Step 3: Update alembic/env.py**

```python
# hiremenow-be/alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base
from app.models import *  # noqa: F401, F403

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Step 4: Create models package**

```python
# hiremenow-be/app/models/__init__.py
from app.models.user import User

__all__ = ["User"]
```

**Step 5: Create User model**

```python
# hiremenow-be/app/models/user.py
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class UserRole(str, PyEnum):
    ADMIN = "admin"
    EMPLOYER = "employer"
    CANDIDATE = "candidate"
    PARTNER = "partner"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # nullable for OAuth
    role = Column(Enum(UserRole), nullable=False, default=UserRole.CANDIDATE)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User {self.email}>"
```

**Step 6: Create first migration**

Run: `cd hiremenow-be && alembic revision --autogenerate -m "create users table"`

Expected: New file in `alembic/versions/` with create_users_table migration

**Step 7: Run migration**

Run: `cd hiremenow-be && alembic upgrade head`

Expected: Migration applied successfully

**Step 8: Commit**

```bash
git add hiremenow-be/alembic hiremenow-be/alembic.ini hiremenow-be/app/models
git commit -m "feat(backend): add Alembic setup and User model"
```

---

## Task 3: Authentication - Schemas & Utils

**Files:**
- Create: `hiremenow-be/app/schemas/__init__.py`
- Create: `hiremenow-be/app/schemas/user.py`
- Create: `hiremenow-be/app/schemas/auth.py`
- Create: `hiremenow-be/app/core/__init__.py`
- Create: `hiremenow-be/app/core/security.py`

**Step 1: Create schemas package**

```python
# hiremenow-be/app/schemas/__init__.py
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.schemas.auth import Token, TokenPayload, LoginRequest

__all__ = [
    "UserCreate", "UserResponse", "UserUpdate",
    "Token", "TokenPayload", "LoginRequest"
]
```

**Step 2: Create user schemas**

```python
# hiremenow-be/app/schemas/user.py
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str
    role: UserRole = UserRole.CANDIDATE


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: UUID
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

**Step 3: Create auth schemas**

```python
# hiremenow-be/app/schemas/auth.py
from pydantic import BaseModel, EmailStr
from uuid import UUID
from app.models.user import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: UUID
    role: UserRole
    exp: int
    type: str  # "access" or "refresh"
```

**Step 4: Create core package**

```python
# hiremenow-be/app/core/__init__.py
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token"
]
```

**Step 5: Create security module**

```python
# hiremenow-be/app/core/security.py
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import get_settings
from app.models.user import UserRole

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: UUID, role: UserRole) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "role": role.value,
        "exp": expire,
        "type": "access"
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: UUID, role: UserRole) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": str(user_id),
        "role": role.value,
        "exp": expire,
        "type": "refresh"
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None
```

**Step 6: Commit**

```bash
git add hiremenow-be/app/schemas hiremenow-be/app/core
git commit -m "feat(backend): add auth schemas and security utilities"
```

---

## Task 4: Authentication - Dependencies & Routes

**Files:**
- Create: `hiremenow-be/app/api/__init__.py`
- Create: `hiremenow-be/app/api/deps.py`
- Create: `hiremenow-be/app/api/v1/__init__.py`
- Create: `hiremenow-be/app/api/v1/router.py`
- Create: `hiremenow-be/app/api/v1/auth.py`
- Modify: `hiremenow-be/app/main.py`

**Step 1: Create API dependencies**

```python
# hiremenow-be/app/api/__init__.py
```

```python
# hiremenow-be/app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.database import get_db
from app.core.security import decode_token
from app.models.user import User, UserRole

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_token(token)

    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    user_id = UUID(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    return user


def require_roles(allowed_roles: List[UserRole]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker


# Convenience dependencies
def get_admin_user(user: User = Depends(require_roles([UserRole.ADMIN]))) -> User:
    return user


def get_employer_user(user: User = Depends(require_roles([UserRole.ADMIN, UserRole.EMPLOYER]))) -> User:
    return user


def get_candidate_user(user: User = Depends(require_roles([UserRole.ADMIN, UserRole.CANDIDATE]))) -> User:
    return user
```

**Step 2: Create auth routes**

```python
# hiremenow-be/app/api/v1/__init__.py
```

```python
# hiremenow-be/app/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate, UserResponse
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new candidate (public registration is only for candidates)"""
    # Check if email exists
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Force role to candidate for public registration
    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=UserRole.CANDIDATE
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password"""
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    return Token(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id, user.role)
    )


@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Get new access token using refresh token"""
    payload = decode_token(refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    from uuid import UUID
    user_id = UUID(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated"
        )

    return Token(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id, user.role)
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user
```

**Step 3: Create v1 router**

```python
# hiremenow-be/app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.auth import router as auth_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
```

**Step 4: Update main.py to include router**

```python
# hiremenow-be/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api.v1.router import api_router

settings = get_settings()

app = FastAPI(
    title="HireMeNow API",
    description="Recruitment Agency Platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS
origins = [origin.strip() for origin in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "environment": settings.environment}
```

**Step 5: Test auth endpoints**

Run: `cd hiremenow-be && docker compose -f docker-compose.linux.yml up --build`

Test registration:
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'
```

Expected: 201 response with user data

Test login:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'
```

Expected: 200 response with tokens

**Step 6: Commit**

```bash
git add hiremenow-be/app/api hiremenow-be/app/main.py
git commit -m "feat(backend): add authentication routes and dependencies"
```

---

## Task 5: Company & Employer Models

**Files:**
- Create: `hiremenow-be/app/models/company.py`
- Create: `hiremenow-be/app/models/employer.py`
- Modify: `hiremenow-be/app/models/__init__.py`

**Step 1: Create Company model**

```python
# hiremenow-be/app/models/company.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)
    website = Column(String(500), nullable=True)
    location = Column(String(255), nullable=True)
    industry = Column(String(100), nullable=True)
    is_agency_owned = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    employers = relationship("Employer", back_populates="company", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Company {self.name}>"
```

**Step 2: Create Employer model**

```python
# hiremenow-be/app/models/employer.py
import uuid
from datetime import datetime
from sqlalchemy import Column, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Employer(Base):
    __tablename__ = "employers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="employer_profile")
    company = relationship("Company", back_populates="employers")

    def __repr__(self):
        return f"<Employer user_id={self.user_id}>"
```

**Step 3: Update models init**

```python
# hiremenow-be/app/models/__init__.py
from app.models.user import User, UserRole
from app.models.company import Company
from app.models.employer import Employer

__all__ = ["User", "UserRole", "Company", "Employer"]
```

**Step 4: Create migration**

Run: `cd hiremenow-be && alembic revision --autogenerate -m "add companies and employers tables"`

**Step 5: Run migration**

Run: `cd hiremenow-be && alembic upgrade head`

**Step 6: Commit**

```bash
git add hiremenow-be/app/models hiremenow-be/alembic/versions
git commit -m "feat(backend): add Company and Employer models"
```

---

## Task 6: Candidate Model

**Files:**
- Create: `hiremenow-be/app/models/candidate.py`
- Modify: `hiremenow-be/app/models/__init__.py`

**Step 1: Create Candidate model**

```python
# hiremenow-be/app/models/candidate.py
import uuid
from datetime import datetime, date
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Boolean, DateTime, Date, Integer, ForeignKey, Enum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class PassportStatus(str, PyEnum):
    VALID = "valid"
    EXPIRED = "expired"
    NONE = "none"
    IN_PROGRESS = "in_progress"


class LeadSource(str, PyEnum):
    WEBSITE = "website"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    REFERRAL = "referral"
    OTHER = "other"


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Personal info
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    nationality = Column(String(100), nullable=True)
    current_country = Column(String(100), nullable=True)

    # Passport
    passport_status = Column(Enum(PassportStatus), default=PassportStatus.NONE, nullable=False)
    passport_expiry = Column(Date, nullable=True)

    # Professional
    preferred_positions = Column(JSONB, default=list, nullable=False)
    experience_years = Column(Integer, default=0, nullable=False)

    # Files
    photo_url = Column(String(500), nullable=True)
    resume_url = Column(String(500), nullable=True)

    # Tracking
    source = Column(Enum(LeadSource), default=LeadSource.WEBSITE, nullable=False)
    referral_code = Column(String(50), nullable=True)

    # Pipeline tracking (will link to pipeline_stages later)
    current_stage = Column(String(50), default="lead", nullable=False)
    stage_notes = Column(Text, nullable=True)
    stage_updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="candidate_profile")

    def __repr__(self):
        return f"<Candidate {self.first_name} {self.last_name}>"
```

**Step 2: Update models init**

```python
# hiremenow-be/app/models/__init__.py
from app.models.user import User, UserRole
from app.models.company import Company
from app.models.employer import Employer
from app.models.candidate import Candidate, PassportStatus, LeadSource

__all__ = [
    "User", "UserRole",
    "Company",
    "Employer",
    "Candidate", "PassportStatus", "LeadSource"
]
```

**Step 3: Create migration**

Run: `cd hiremenow-be && alembic revision --autogenerate -m "add candidates table"`

**Step 4: Run migration**

Run: `cd hiremenow-be && alembic upgrade head`

**Step 5: Commit**

```bash
git add hiremenow-be/app/models hiremenow-be/alembic/versions
git commit -m "feat(backend): add Candidate model"
```

---

## Task 7: Job Model

**Files:**
- Create: `hiremenow-be/app/models/job.py`
- Modify: `hiremenow-be/app/models/__init__.py`

**Step 1: Create Job model**

```python
# hiremenow-be/app/models/job.py
import uuid
from datetime import datetime, date
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Boolean, DateTime, Date, Integer, ForeignKey, Enum, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class WorkMode(str, PyEnum):
    ONSITE = "onsite"
    ACCOMMODATION_PROVIDED = "accommodation_provided"


class JobType(str, PyEnum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    SEASONAL = "seasonal"


class JobStatus(str, PyEnum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"
    REJECTED = "rejected"


class SalaryPeriod(str, PyEnum):
    HOURLY = "hourly"
    MONTHLY = "monthly"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Basic info
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)

    # Location
    country = Column(String(100), nullable=False)
    city = Column(String(100), nullable=True)
    work_mode = Column(Enum(WorkMode), default=WorkMode.ONSITE, nullable=False)

    # Employment
    job_type = Column(Enum(JobType), default=JobType.FULL_TIME, nullable=False)

    # Salary
    salary_min = Column(Numeric(10, 2), nullable=True)
    salary_max = Column(Numeric(10, 2), nullable=True)
    salary_currency = Column(String(3), default="EUR", nullable=False)
    salary_period = Column(Enum(SalaryPeriod), default=SalaryPeriod.MONTHLY, nullable=False)

    # Details
    benefits = Column(JSONB, default=list, nullable=False)
    requirements = Column(JSONB, default=dict, nullable=False)

    # Slots
    total_slots = Column(Integer, default=1, nullable=False)
    filled_slots = Column(Integer, default=0, nullable=False)

    # Status & dates
    status = Column(Enum(JobStatus), default=JobStatus.DRAFT, nullable=False)
    rejection_reason = Column(Text, nullable=True)
    deadline = Column(Date, nullable=True)
    start_date = Column(Date, nullable=True)
    published_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    company = relationship("Company", back_populates="jobs")
    creator = relationship("User", backref="created_jobs")

    @property
    def available_slots(self) -> int:
        return max(0, self.total_slots - self.filled_slots)

    def __repr__(self):
        return f"<Job {self.title}>"
```

**Step 2: Update models init**

```python
# hiremenow-be/app/models/__init__.py
from app.models.user import User, UserRole
from app.models.company import Company
from app.models.employer import Employer
from app.models.candidate import Candidate, PassportStatus, LeadSource
from app.models.job import Job, WorkMode, JobType, JobStatus, SalaryPeriod

__all__ = [
    "User", "UserRole",
    "Company",
    "Employer",
    "Candidate", "PassportStatus", "LeadSource",
    "Job", "WorkMode", "JobType", "JobStatus", "SalaryPeriod"
]
```

**Step 3: Create migration**

Run: `cd hiremenow-be && alembic revision --autogenerate -m "add jobs table"`

**Step 4: Run migration**

Run: `cd hiremenow-be && alembic upgrade head`

**Step 5: Commit**

```bash
git add hiremenow-be/app/models hiremenow-be/alembic/versions
git commit -m "feat(backend): add Job model"
```

---

## Task 8: Admin - Company CRUD Endpoints

**Files:**
- Create: `hiremenow-be/app/schemas/company.py`
- Create: `hiremenow-be/app/api/v1/admin/__init__.py`
- Create: `hiremenow-be/app/api/v1/admin/companies.py`
- Modify: `hiremenow-be/app/schemas/__init__.py`
- Modify: `hiremenow-be/app/api/v1/router.py`

**Step 1: Create company schemas**

```python
# hiremenow-be/app/schemas/company.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class CompanyBase(BaseModel):
    name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    is_agency_owned: bool = False


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    industry: Optional[str] = None
    is_active: Optional[bool] = None


class CompanyResponse(CompanyBase):
    id: UUID
    slug: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompanyListResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    location: Optional[str]
    industry: Optional[str]
    is_agency_owned: bool
    is_active: bool
    employer_count: int = 0

    class Config:
        from_attributes = True
```

**Step 2: Update schemas init**

```python
# hiremenow-be/app/schemas/__init__.py
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.schemas.auth import Token, TokenPayload, LoginRequest
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse, CompanyListResponse

__all__ = [
    "UserCreate", "UserResponse", "UserUpdate",
    "Token", "TokenPayload", "LoginRequest",
    "CompanyCreate", "CompanyUpdate", "CompanyResponse", "CompanyListResponse"
]
```

**Step 3: Create admin companies router**

```python
# hiremenow-be/app/api/v1/admin/__init__.py
```

```python
# hiremenow-be/app/api/v1/admin/companies.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from uuid import UUID
from typing import List
import re

from app.database import get_db
from app.models.company import Company
from app.models.employer import Employer
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse, CompanyListResponse
from app.api.deps import get_admin_user

router = APIRouter(prefix="/companies", tags=["Admin - Companies"])


def generate_slug(name: str, db: Session) -> str:
    """Generate unique slug from company name"""
    base_slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    slug = base_slug
    counter = 1
    while db.query(Company).filter(Company.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


@router.get("", response_model=List[CompanyListResponse])
def list_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    is_active: bool = None,
    search: str = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """List all companies with employer count"""
    query = db.query(
        Company,
        func.count(Employer.id).label("employer_count")
    ).outerjoin(Employer).group_by(Company.id)

    if is_active is not None:
        query = query.filter(Company.is_active == is_active)

    if search:
        query = query.filter(Company.name.ilike(f"%{search}%"))

    results = query.order_by(Company.created_at.desc()).offset(skip).limit(limit).all()

    return [
        CompanyListResponse(
            id=company.id,
            name=company.name,
            slug=company.slug,
            location=company.location,
            industry=company.industry,
            is_agency_owned=company.is_agency_owned,
            is_active=company.is_active,
            employer_count=employer_count
        )
        for company, employer_count in results
    ]


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(
    data: CompanyCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Create a new company"""
    company = Company(
        **data.model_dump(),
        slug=generate_slug(data.name, db)
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(
    company_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Get company by ID"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: UUID,
    data: CompanyUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Update company"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    update_data = data.model_dump(exclude_unset=True)

    # Regenerate slug if name changed
    if "name" in update_data and update_data["name"] != company.name:
        update_data["slug"] = generate_slug(update_data["name"], db)

    for field, value in update_data.items():
        setattr(company, field, value)

    db.commit()
    db.refresh(company)
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    company_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Delete company (cascades to employers and jobs)"""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    db.delete(company)
    db.commit()
```

**Step 4: Update v1 router**

```python
# hiremenow-be/app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.admin.companies import router as admin_companies_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(admin_companies_router, prefix="/admin")
```

**Step 5: Test company endpoints**

First create an admin user (manually in DB or via script):
```bash
# In the backend container or with psql
docker exec -it hiremenow-postgres psql -U hiremenow -d hiremenow_db -c "UPDATE users SET role='admin' WHERE email='test@example.com';"
```

Get new token after role change:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'
```

Create company:
```bash
curl -X POST http://localhost:8000/api/v1/admin/companies \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"name": "Acme Corp", "location": "Slovakia", "industry": "Manufacturing"}'
```

Expected: 201 response with company data

**Step 6: Commit**

```bash
git add hiremenow-be/app/schemas hiremenow-be/app/api
git commit -m "feat(backend): add admin company CRUD endpoints"
```

---

## Task 9: Admin - Employer CRUD Endpoints

**Files:**
- Create: `hiremenow-be/app/schemas/employer.py`
- Create: `hiremenow-be/app/api/v1/admin/employers.py`
- Modify: `hiremenow-be/app/schemas/__init__.py`
- Modify: `hiremenow-be/app/api/v1/router.py`

**Step 1: Create employer schemas**

```python
# hiremenow-be/app/schemas/employer.py
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Optional


class EmployerCreate(BaseModel):
    email: EmailStr
    password: str
    company_id: UUID


class EmployerResponse(BaseModel):
    id: UUID
    user_id: UUID
    company_id: UUID
    email: str
    is_active: bool
    company_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class EmployerListResponse(BaseModel):
    id: UUID
    user_id: UUID
    email: str
    company_id: UUID
    company_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
```

**Step 2: Update schemas init**

```python
# hiremenow-be/app/schemas/__init__.py
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.schemas.auth import Token, TokenPayload, LoginRequest
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse, CompanyListResponse
from app.schemas.employer import EmployerCreate, EmployerResponse, EmployerListResponse

__all__ = [
    "UserCreate", "UserResponse", "UserUpdate",
    "Token", "TokenPayload", "LoginRequest",
    "CompanyCreate", "CompanyUpdate", "CompanyResponse", "CompanyListResponse",
    "EmployerCreate", "EmployerResponse", "EmployerListResponse"
]
```

**Step 3: Create employers router**

```python
# hiremenow-be/app/api/v1/admin/employers.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.database import get_db
from app.models.user import User, UserRole
from app.models.company import Company
from app.models.employer import Employer
from app.schemas.employer import EmployerCreate, EmployerResponse, EmployerListResponse
from app.core.security import hash_password
from app.api.deps import get_admin_user

router = APIRouter(prefix="/employers", tags=["Admin - Employers"])


@router.get("", response_model=List[EmployerListResponse])
def list_employers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    company_id: UUID = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """List all employers"""
    query = db.query(Employer).join(User).join(Company)

    if company_id:
        query = query.filter(Employer.company_id == company_id)

    employers = query.order_by(Employer.created_at.desc()).offset(skip).limit(limit).all()

    return [
        EmployerListResponse(
            id=emp.id,
            user_id=emp.user_id,
            email=emp.user.email,
            company_id=emp.company_id,
            company_name=emp.company.name,
            is_active=emp.user.is_active,
            created_at=emp.created_at
        )
        for emp in employers
    ]


@router.post("", response_model=EmployerResponse, status_code=status.HTTP_201_CREATED)
def create_employer(
    data: EmployerCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Create employer account (admin creates user + links to company)"""
    # Check company exists
    company = db.query(Company).filter(Company.id == data.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Check email not taken
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user with employer role
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role=UserRole.EMPLOYER
    )
    db.add(user)
    db.flush()

    # Create employer profile
    employer = Employer(
        user_id=user.id,
        company_id=data.company_id
    )
    db.add(employer)
    db.commit()
    db.refresh(employer)

    return EmployerResponse(
        id=employer.id,
        user_id=employer.user_id,
        company_id=employer.company_id,
        email=user.email,
        is_active=user.is_active,
        company_name=company.name,
        created_at=employer.created_at
    )


@router.get("/{employer_id}", response_model=EmployerResponse)
def get_employer(
    employer_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Get employer by ID"""
    employer = db.query(Employer).filter(Employer.id == employer_id).first()
    if not employer:
        raise HTTPException(status_code=404, detail="Employer not found")

    return EmployerResponse(
        id=employer.id,
        user_id=employer.user_id,
        company_id=employer.company_id,
        email=employer.user.email,
        is_active=employer.user.is_active,
        company_name=employer.company.name,
        created_at=employer.created_at
    )


@router.delete("/{employer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employer(
    employer_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Delete employer (also deletes user account)"""
    employer = db.query(Employer).filter(Employer.id == employer_id).first()
    if not employer:
        raise HTTPException(status_code=404, detail="Employer not found")

    # Delete user (cascades to employer)
    user = employer.user
    db.delete(user)
    db.commit()
```

**Step 4: Update v1 router**

```python
# hiremenow-be/app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.admin.companies import router as admin_companies_router
from app.api.v1.admin.employers import router as admin_employers_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(admin_companies_router, prefix="/admin")
api_router.include_router(admin_employers_router, prefix="/admin")
```

**Step 5: Test employer endpoints**

Create employer:
```bash
curl -X POST http://localhost:8000/api/v1/admin/employers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin_token>" \
  -d '{"email": "employer@acme.com", "password": "emp123", "company_id": "<company_uuid>"}'
```

Expected: 201 response with employer data

**Step 6: Commit**

```bash
git add hiremenow-be/app/schemas hiremenow-be/app/api
git commit -m "feat(backend): add admin employer CRUD endpoints"
```

---

## Task 10: Admin - Candidate CRUD Endpoints

**Files:**
- Create: `hiremenow-be/app/schemas/candidate.py`
- Create: `hiremenow-be/app/api/v1/admin/candidates.py`
- Modify: `hiremenow-be/app/schemas/__init__.py`
- Modify: `hiremenow-be/app/api/v1/router.py`

**Step 1: Create candidate schemas**

```python
# hiremenow-be/app/schemas/candidate.py
from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime, date
from typing import Optional, List
from app.models.candidate import PassportStatus, LeadSource


class CandidateCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    source: LeadSource = LeadSource.WEBSITE


class CandidateUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = None
    current_country: Optional[str] = None
    passport_status: Optional[PassportStatus] = None
    passport_expiry: Optional[date] = None
    preferred_positions: Optional[List[str]] = None
    experience_years: Optional[int] = None
    is_active: Optional[bool] = None


class CandidateStageUpdate(BaseModel):
    stage: str
    notes: Optional[str] = None


class CandidateResponse(BaseModel):
    id: UUID
    user_id: UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    date_of_birth: Optional[date]
    nationality: Optional[str]
    current_country: Optional[str]
    passport_status: PassportStatus
    passport_expiry: Optional[date]
    preferred_positions: List[str]
    experience_years: int
    photo_url: Optional[str]
    resume_url: Optional[str]
    source: LeadSource
    current_stage: str
    stage_notes: Optional[str]
    stage_updated_at: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CandidateListResponse(BaseModel):
    id: UUID
    user_id: UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    current_country: Optional[str]
    current_stage: str
    source: LeadSource
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
```

**Step 2: Update schemas init**

```python
# hiremenow-be/app/schemas/__init__.py
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.schemas.auth import Token, TokenPayload, LoginRequest
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse, CompanyListResponse
from app.schemas.employer import EmployerCreate, EmployerResponse, EmployerListResponse
from app.schemas.candidate import (
    CandidateCreate, CandidateUpdate, CandidateStageUpdate,
    CandidateResponse, CandidateListResponse
)

__all__ = [
    "UserCreate", "UserResponse", "UserUpdate",
    "Token", "TokenPayload", "LoginRequest",
    "CompanyCreate", "CompanyUpdate", "CompanyResponse", "CompanyListResponse",
    "EmployerCreate", "EmployerResponse", "EmployerListResponse",
    "CandidateCreate", "CandidateUpdate", "CandidateStageUpdate",
    "CandidateResponse", "CandidateListResponse"
]
```

**Step 3: Create candidates router**

```python
# hiremenow-be/app/api/v1/admin/candidates.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import List

from app.database import get_db
from app.models.user import User, UserRole
from app.models.candidate import Candidate
from app.schemas.candidate import (
    CandidateCreate, CandidateUpdate, CandidateStageUpdate,
    CandidateResponse, CandidateListResponse
)
from app.core.security import hash_password
from app.api.deps import get_admin_user

router = APIRouter(prefix="/candidates", tags=["Admin - Candidates"])

# Fixed pipeline stages for Phase 1
PIPELINE_STAGES = [
    "lead",
    "pre_screening",
    "assessment",
    "job_matching",
    "pre_agreement",
    "language_course",
    "legal_paperwork",
    "departure_prep",
    "transport",
    "deployed",
    "after_sales"
]


def get_next_stage(current_stage: str) -> str:
    """Get next stage in pipeline"""
    try:
        idx = PIPELINE_STAGES.index(current_stage)
        if idx < len(PIPELINE_STAGES) - 1:
            return PIPELINE_STAGES[idx + 1]
    except ValueError:
        pass
    return current_stage


@router.get("", response_model=List[CandidateListResponse])
def list_candidates(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    stage: str = None,
    search: str = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """List all candidates"""
    query = db.query(Candidate).join(User)

    if stage:
        query = query.filter(Candidate.current_stage == stage)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (User.email.ilike(search_filter)) |
            (Candidate.first_name.ilike(search_filter)) |
            (Candidate.last_name.ilike(search_filter)) |
            (Candidate.phone.ilike(search_filter))
        )

    candidates = query.order_by(Candidate.created_at.desc()).offset(skip).limit(limit).all()

    return [
        CandidateListResponse(
            id=c.id,
            user_id=c.user_id,
            email=c.user.email,
            first_name=c.first_name,
            last_name=c.last_name,
            phone=c.phone,
            current_country=c.current_country,
            current_stage=c.current_stage,
            source=c.source,
            is_active=c.user.is_active,
            created_at=c.created_at
        )
        for c in candidates
    ]


@router.get("/stages", response_model=List[str])
def get_pipeline_stages(admin: User = Depends(get_admin_user)):
    """Get list of pipeline stages"""
    return PIPELINE_STAGES


@router.post("", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
def create_candidate(
    data: CandidateCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Admin creates a candidate (lead capture)"""
    # Check email not taken
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role=UserRole.CANDIDATE
    )
    db.add(user)
    db.flush()

    # Create candidate profile
    candidate = Candidate(
        user_id=user.id,
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        source=data.source
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    return CandidateResponse(
        id=candidate.id,
        user_id=candidate.user_id,
        email=user.email,
        first_name=candidate.first_name,
        last_name=candidate.last_name,
        phone=candidate.phone,
        date_of_birth=candidate.date_of_birth,
        nationality=candidate.nationality,
        current_country=candidate.current_country,
        passport_status=candidate.passport_status,
        passport_expiry=candidate.passport_expiry,
        preferred_positions=candidate.preferred_positions or [],
        experience_years=candidate.experience_years,
        photo_url=candidate.photo_url,
        resume_url=candidate.resume_url,
        source=candidate.source,
        current_stage=candidate.current_stage,
        stage_notes=candidate.stage_notes,
        stage_updated_at=candidate.stage_updated_at,
        is_active=user.is_active,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at
    )


@router.get("/{candidate_id}", response_model=CandidateResponse)
def get_candidate(
    candidate_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Get candidate details"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    return CandidateResponse(
        id=candidate.id,
        user_id=candidate.user_id,
        email=candidate.user.email,
        first_name=candidate.first_name,
        last_name=candidate.last_name,
        phone=candidate.phone,
        date_of_birth=candidate.date_of_birth,
        nationality=candidate.nationality,
        current_country=candidate.current_country,
        passport_status=candidate.passport_status,
        passport_expiry=candidate.passport_expiry,
        preferred_positions=candidate.preferred_positions or [],
        experience_years=candidate.experience_years,
        photo_url=candidate.photo_url,
        resume_url=candidate.resume_url,
        source=candidate.source,
        current_stage=candidate.current_stage,
        stage_notes=candidate.stage_notes,
        stage_updated_at=candidate.stage_updated_at,
        is_active=candidate.user.is_active,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at
    )


@router.put("/{candidate_id}", response_model=CandidateResponse)
def update_candidate(
    candidate_id: UUID,
    data: CandidateUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Update candidate profile"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    update_data = data.model_dump(exclude_unset=True)

    # Handle user fields
    if "is_active" in update_data:
        candidate.user.is_active = update_data.pop("is_active")

    for field, value in update_data.items():
        setattr(candidate, field, value)

    db.commit()
    db.refresh(candidate)

    return CandidateResponse(
        id=candidate.id,
        user_id=candidate.user_id,
        email=candidate.user.email,
        first_name=candidate.first_name,
        last_name=candidate.last_name,
        phone=candidate.phone,
        date_of_birth=candidate.date_of_birth,
        nationality=candidate.nationality,
        current_country=candidate.current_country,
        passport_status=candidate.passport_status,
        passport_expiry=candidate.passport_expiry,
        preferred_positions=candidate.preferred_positions or [],
        experience_years=candidate.experience_years,
        photo_url=candidate.photo_url,
        resume_url=candidate.resume_url,
        source=candidate.source,
        current_stage=candidate.current_stage,
        stage_notes=candidate.stage_notes,
        stage_updated_at=candidate.stage_updated_at,
        is_active=candidate.user.is_active,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at
    )


@router.post("/{candidate_id}/advance-stage", response_model=CandidateResponse)
def advance_candidate_stage(
    candidate_id: UUID,
    data: CandidateStageUpdate = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Advance candidate to next pipeline stage"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    if data and data.stage:
        # Set specific stage
        if data.stage not in PIPELINE_STAGES:
            raise HTTPException(status_code=400, detail=f"Invalid stage: {data.stage}")
        candidate.current_stage = data.stage
    else:
        # Auto-advance to next
        candidate.current_stage = get_next_stage(candidate.current_stage)

    if data and data.notes:
        candidate.stage_notes = data.notes

    candidate.stage_updated_at = datetime.utcnow()
    db.commit()
    db.refresh(candidate)

    return CandidateResponse(
        id=candidate.id,
        user_id=candidate.user_id,
        email=candidate.user.email,
        first_name=candidate.first_name,
        last_name=candidate.last_name,
        phone=candidate.phone,
        date_of_birth=candidate.date_of_birth,
        nationality=candidate.nationality,
        current_country=candidate.current_country,
        passport_status=candidate.passport_status,
        passport_expiry=candidate.passport_expiry,
        preferred_positions=candidate.preferred_positions or [],
        experience_years=candidate.experience_years,
        photo_url=candidate.photo_url,
        resume_url=candidate.resume_url,
        source=candidate.source,
        current_stage=candidate.current_stage,
        stage_notes=candidate.stage_notes,
        stage_updated_at=candidate.stage_updated_at,
        is_active=candidate.user.is_active,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at
    )


@router.post("/{candidate_id}/reject", response_model=CandidateResponse)
def reject_candidate(
    candidate_id: UUID,
    data: CandidateStageUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Reject/deactivate candidate"""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    candidate.user.is_active = False
    candidate.stage_notes = data.notes or "Rejected"
    candidate.stage_updated_at = datetime.utcnow()
    db.commit()
    db.refresh(candidate)

    return CandidateResponse(
        id=candidate.id,
        user_id=candidate.user_id,
        email=candidate.user.email,
        first_name=candidate.first_name,
        last_name=candidate.last_name,
        phone=candidate.phone,
        date_of_birth=candidate.date_of_birth,
        nationality=candidate.nationality,
        current_country=candidate.current_country,
        passport_status=candidate.passport_status,
        passport_expiry=candidate.passport_expiry,
        preferred_positions=candidate.preferred_positions or [],
        experience_years=candidate.experience_years,
        photo_url=candidate.photo_url,
        resume_url=candidate.resume_url,
        source=candidate.source,
        current_stage=candidate.current_stage,
        stage_notes=candidate.stage_notes,
        stage_updated_at=candidate.stage_updated_at,
        is_active=candidate.user.is_active,
        created_at=candidate.created_at,
        updated_at=candidate.updated_at
    )
```

**Step 4: Update v1 router**

```python
# hiremenow-be/app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.admin.companies import router as admin_companies_router
from app.api.v1.admin.employers import router as admin_employers_router
from app.api.v1.admin.candidates import router as admin_candidates_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(admin_companies_router, prefix="/admin")
api_router.include_router(admin_employers_router, prefix="/admin")
api_router.include_router(admin_candidates_router, prefix="/admin")
```

**Step 5: Commit**

```bash
git add hiremenow-be/app/schemas hiremenow-be/app/api
git commit -m "feat(backend): add admin candidate CRUD and pipeline stage endpoints"
```

---

## Task 11: Admin - Job CRUD Endpoints

**Files:**
- Create: `hiremenow-be/app/schemas/job.py`
- Create: `hiremenow-be/app/api/v1/admin/jobs.py`
- Modify: `hiremenow-be/app/schemas/__init__.py`
- Modify: `hiremenow-be/app/api/v1/router.py`

**Step 1: Create job schemas**

```python
# hiremenow-be/app/schemas/job.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from app.models.job import WorkMode, JobType, JobStatus, SalaryPeriod


class JobCreate(BaseModel):
    company_id: UUID
    title: str
    description: str
    category: Optional[str] = None
    country: str
    city: Optional[str] = None
    work_mode: WorkMode = WorkMode.ONSITE
    job_type: JobType = JobType.FULL_TIME
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    salary_currency: str = "EUR"
    salary_period: SalaryPeriod = SalaryPeriod.MONTHLY
    benefits: List[str] = []
    requirements: Dict[str, Any] = {}
    total_slots: int = 1
    deadline: Optional[date] = None
    start_date: Optional[date] = None


class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    work_mode: Optional[WorkMode] = None
    job_type: Optional[JobType] = None
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    salary_currency: Optional[str] = None
    salary_period: Optional[SalaryPeriod] = None
    benefits: Optional[List[str]] = None
    requirements: Optional[Dict[str, Any]] = None
    total_slots: Optional[int] = None
    deadline: Optional[date] = None
    start_date: Optional[date] = None
    status: Optional[JobStatus] = None


class JobApproval(BaseModel):
    rejection_reason: Optional[str] = None


class JobResponse(BaseModel):
    id: UUID
    company_id: UUID
    company_name: str
    created_by: Optional[UUID]
    title: str
    slug: str
    description: str
    category: Optional[str]
    country: str
    city: Optional[str]
    work_mode: WorkMode
    job_type: JobType
    salary_min: Optional[Decimal]
    salary_max: Optional[Decimal]
    salary_currency: str
    salary_period: SalaryPeriod
    benefits: List[str]
    requirements: Dict[str, Any]
    total_slots: int
    filled_slots: int
    available_slots: int
    status: JobStatus
    rejection_reason: Optional[str]
    deadline: Optional[date]
    start_date: Optional[date]
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    id: UUID
    company_id: UUID
    company_name: str
    title: str
    slug: str
    country: str
    city: Optional[str]
    job_type: JobType
    status: JobStatus
    total_slots: int
    filled_slots: int
    available_slots: int
    created_at: datetime

    class Config:
        from_attributes = True
```

**Step 2: Update schemas init**

```python
# hiremenow-be/app/schemas/__init__.py
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.schemas.auth import Token, TokenPayload, LoginRequest
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse, CompanyListResponse
from app.schemas.employer import EmployerCreate, EmployerResponse, EmployerListResponse
from app.schemas.candidate import (
    CandidateCreate, CandidateUpdate, CandidateStageUpdate,
    CandidateResponse, CandidateListResponse
)
from app.schemas.job import (
    JobCreate, JobUpdate, JobApproval,
    JobResponse, JobListResponse
)

__all__ = [
    "UserCreate", "UserResponse", "UserUpdate",
    "Token", "TokenPayload", "LoginRequest",
    "CompanyCreate", "CompanyUpdate", "CompanyResponse", "CompanyListResponse",
    "EmployerCreate", "EmployerResponse", "EmployerListResponse",
    "CandidateCreate", "CandidateUpdate", "CandidateStageUpdate",
    "CandidateResponse", "CandidateListResponse",
    "JobCreate", "JobUpdate", "JobApproval",
    "JobResponse", "JobListResponse"
]
```

**Step 3: Create jobs router**

```python
# hiremenow-be/app/api/v1/admin/jobs.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from typing import List
import re

from app.database import get_db
from app.models.user import User
from app.models.company import Company
from app.models.job import Job, JobStatus
from app.schemas.job import JobCreate, JobUpdate, JobApproval, JobResponse, JobListResponse
from app.api.deps import get_admin_user

router = APIRouter(prefix="/jobs", tags=["Admin - Jobs"])


def generate_job_slug(title: str, company_name: str, db: Session) -> str:
    """Generate unique slug from job title and company"""
    base = f"{company_name}-{title}"
    base_slug = re.sub(r'[^a-z0-9]+', '-', base.lower()).strip('-')
    slug = base_slug
    counter = 1
    while db.query(Job).filter(Job.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


@router.get("", response_model=List[JobListResponse])
def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: JobStatus = None,
    company_id: UUID = None,
    search: str = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """List all jobs"""
    query = db.query(Job).join(Company)

    if status_filter:
        query = query.filter(Job.status == status_filter)

    if company_id:
        query = query.filter(Job.company_id == company_id)

    if search:
        query = query.filter(Job.title.ilike(f"%{search}%"))

    jobs = query.order_by(Job.created_at.desc()).offset(skip).limit(limit).all()

    return [
        JobListResponse(
            id=job.id,
            company_id=job.company_id,
            company_name=job.company.name,
            title=job.title,
            slug=job.slug,
            country=job.country,
            city=job.city,
            job_type=job.job_type,
            status=job.status,
            total_slots=job.total_slots,
            filled_slots=job.filled_slots,
            available_slots=job.available_slots,
            created_at=job.created_at
        )
        for job in jobs
    ]


@router.get("/pending", response_model=List[JobListResponse])
def list_pending_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """List jobs pending approval"""
    jobs = db.query(Job).join(Company).filter(
        Job.status == JobStatus.PENDING_APPROVAL
    ).order_by(Job.created_at.asc()).offset(skip).limit(limit).all()

    return [
        JobListResponse(
            id=job.id,
            company_id=job.company_id,
            company_name=job.company.name,
            title=job.title,
            slug=job.slug,
            country=job.country,
            city=job.city,
            job_type=job.job_type,
            status=job.status,
            total_slots=job.total_slots,
            filled_slots=job.filled_slots,
            available_slots=job.available_slots,
            created_at=job.created_at
        )
        for job in jobs
    ]


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    data: JobCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Admin creates a job (goes directly to active)"""
    company = db.query(Company).filter(Company.id == data.company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    job = Job(
        **data.model_dump(),
        created_by=admin.id,
        slug=generate_job_slug(data.title, company.name, db),
        status=JobStatus.ACTIVE,
        published_at=datetime.utcnow()
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return JobResponse(
        id=job.id,
        company_id=job.company_id,
        company_name=company.name,
        created_by=job.created_by,
        title=job.title,
        slug=job.slug,
        description=job.description,
        category=job.category,
        country=job.country,
        city=job.city,
        work_mode=job.work_mode,
        job_type=job.job_type,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_currency=job.salary_currency,
        salary_period=job.salary_period,
        benefits=job.benefits or [],
        requirements=job.requirements or {},
        total_slots=job.total_slots,
        filled_slots=job.filled_slots,
        available_slots=job.available_slots,
        status=job.status,
        rejection_reason=job.rejection_reason,
        deadline=job.deadline,
        start_date=job.start_date,
        published_at=job.published_at,
        created_at=job.created_at,
        updated_at=job.updated_at
    )


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Get job details"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(
        id=job.id,
        company_id=job.company_id,
        company_name=job.company.name,
        created_by=job.created_by,
        title=job.title,
        slug=job.slug,
        description=job.description,
        category=job.category,
        country=job.country,
        city=job.city,
        work_mode=job.work_mode,
        job_type=job.job_type,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_currency=job.salary_currency,
        salary_period=job.salary_period,
        benefits=job.benefits or [],
        requirements=job.requirements or {},
        total_slots=job.total_slots,
        filled_slots=job.filled_slots,
        available_slots=job.available_slots,
        status=job.status,
        rejection_reason=job.rejection_reason,
        deadline=job.deadline,
        start_date=job.start_date,
        published_at=job.published_at,
        created_at=job.created_at,
        updated_at=job.updated_at
    )


@router.put("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: UUID,
    data: JobUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Update job"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    update_data = data.model_dump(exclude_unset=True)

    # Regenerate slug if title changed
    if "title" in update_data and update_data["title"] != job.title:
        update_data["slug"] = generate_job_slug(update_data["title"], job.company.name, db)

    for field, value in update_data.items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)

    return JobResponse(
        id=job.id,
        company_id=job.company_id,
        company_name=job.company.name,
        created_by=job.created_by,
        title=job.title,
        slug=job.slug,
        description=job.description,
        category=job.category,
        country=job.country,
        city=job.city,
        work_mode=job.work_mode,
        job_type=job.job_type,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_currency=job.salary_currency,
        salary_period=job.salary_period,
        benefits=job.benefits or [],
        requirements=job.requirements or {},
        total_slots=job.total_slots,
        filled_slots=job.filled_slots,
        available_slots=job.available_slots,
        status=job.status,
        rejection_reason=job.rejection_reason,
        deadline=job.deadline,
        start_date=job.start_date,
        published_at=job.published_at,
        created_at=job.created_at,
        updated_at=job.updated_at
    )


@router.post("/{job_id}/approve", response_model=JobResponse)
def approve_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Approve a pending job"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=400, detail="Job is not pending approval")

    job.status = JobStatus.ACTIVE
    job.published_at = datetime.utcnow()
    job.rejection_reason = None
    db.commit()
    db.refresh(job)

    return JobResponse(
        id=job.id,
        company_id=job.company_id,
        company_name=job.company.name,
        created_by=job.created_by,
        title=job.title,
        slug=job.slug,
        description=job.description,
        category=job.category,
        country=job.country,
        city=job.city,
        work_mode=job.work_mode,
        job_type=job.job_type,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_currency=job.salary_currency,
        salary_period=job.salary_period,
        benefits=job.benefits or [],
        requirements=job.requirements or {},
        total_slots=job.total_slots,
        filled_slots=job.filled_slots,
        available_slots=job.available_slots,
        status=job.status,
        rejection_reason=job.rejection_reason,
        deadline=job.deadline,
        start_date=job.start_date,
        published_at=job.published_at,
        created_at=job.created_at,
        updated_at=job.updated_at
    )


@router.post("/{job_id}/reject", response_model=JobResponse)
def reject_job(
    job_id: UUID,
    data: JobApproval,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Reject a pending job"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=400, detail="Job is not pending approval")

    job.status = JobStatus.REJECTED
    job.rejection_reason = data.rejection_reason
    db.commit()
    db.refresh(job)

    return JobResponse(
        id=job.id,
        company_id=job.company_id,
        company_name=job.company.name,
        created_by=job.created_by,
        title=job.title,
        slug=job.slug,
        description=job.description,
        category=job.category,
        country=job.country,
        city=job.city,
        work_mode=job.work_mode,
        job_type=job.job_type,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_currency=job.salary_currency,
        salary_period=job.salary_period,
        benefits=job.benefits or [],
        requirements=job.requirements or {},
        total_slots=job.total_slots,
        filled_slots=job.filled_slots,
        available_slots=job.available_slots,
        status=job.status,
        rejection_reason=job.rejection_reason,
        deadline=job.deadline,
        start_date=job.start_date,
        published_at=job.published_at,
        created_at=job.created_at,
        updated_at=job.updated_at
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    """Delete a job"""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    db.delete(job)
    db.commit()
```

**Step 4: Update v1 router**

```python
# hiremenow-be/app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.admin.companies import router as admin_companies_router
from app.api.v1.admin.employers import router as admin_employers_router
from app.api.v1.admin.candidates import router as admin_candidates_router
from app.api.v1.admin.jobs import router as admin_jobs_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(admin_companies_router, prefix="/admin")
api_router.include_router(admin_employers_router, prefix="/admin")
api_router.include_router(admin_candidates_router, prefix="/admin")
api_router.include_router(admin_jobs_router, prefix="/admin")
```

**Step 5: Commit**

```bash
git add hiremenow-be/app/schemas hiremenow-be/app/api
git commit -m "feat(backend): add admin job CRUD and approval endpoints"
```

---

## Task 12: Create Admin User Seed Script

**Files:**
- Create: `hiremenow-be/scripts/__init__.py`
- Create: `hiremenow-be/scripts/seed_admin.py`

**Step 1: Create scripts package**

```python
# hiremenow-be/scripts/__init__.py
```

**Step 2: Create admin seed script**

```python
# hiremenow-be/scripts/seed_admin.py
"""
Seed script to create initial admin user.
Run with: python -m scripts.seed_admin
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password


def create_admin():
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if admin:
            print(f"Admin user already exists: {admin.email}")
            return

        # Create admin user
        admin = User(
            email="admin@hiremenow.com",
            password_hash=hash_password("admin123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin)
        db.commit()
        print(f"Created admin user: admin@hiremenow.com / admin123")
        print("WARNING: Change the password immediately!")
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
```

**Step 3: Test the script**

Run: `cd hiremenow-be && python -m scripts.seed_admin`

Expected: "Created admin user: admin@hiremenow.com / admin123"

**Step 4: Commit**

```bash
git add hiremenow-be/scripts
git commit -m "feat(backend): add admin user seed script"
```

---

## Task 13: Frontend - Project Setup with Router and Dependencies

**Files:**
- Modify: `hiremenow-fe/package.json`
- Create: `hiremenow-fe/src/lib/api.ts`
- Create: `hiremenow-fe/src/lib/auth.ts`
- Modify: `hiremenow-fe/src/main.tsx`
- Create: `hiremenow-fe/src/routes.tsx`

**Step 1: Install dependencies**

Run:
```bash
cd hiremenow-fe && npm install react-router-dom@6 zustand zod react-hook-form @hookform/resolvers axios
```

**Step 2: Create API client**

```typescript
// hiremenow-fe/src/lib/api.ts
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

**Step 3: Create auth store**

```typescript
// hiremenow-fe/src/lib/auth.ts
import { create } from 'zustand';
import { api } from './api';

interface User {
  id: string;
  email: string;
  role: 'admin' | 'employer' | 'candidate' | 'partner';
  is_active: boolean;
}

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  fetchUser: () => Promise<void>;
}

export const useAuth = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,

  login: async (email: string, password: string) => {
    const response = await api.post('/auth/login', { email, password });
    const { access_token, refresh_token } = response.data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);

    // Fetch user after login
    const userResponse = await api.get('/auth/me');
    set({ user: userResponse.data, isAuthenticated: true, isLoading: false });
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ user: null, isAuthenticated: false });
  },

  fetchUser: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      set({ isLoading: false });
      return;
    }

    try {
      const response = await api.get('/auth/me');
      set({ user: response.data, isAuthenticated: true, isLoading: false });
    } catch {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },
}));
```

**Step 4: Create routes**

```typescript
// hiremenow-fe/src/routes.tsx
import { createBrowserRouter, Navigate, Outlet } from 'react-router-dom';
import { useAuth } from './lib/auth';

// Placeholder components - will be replaced
const LoginPage = () => <div>Login Page</div>;
const AdminDashboard = () => <div>Admin Dashboard</div>;
const AdminCompanies = () => <div>Companies</div>;
const AdminEmployers = () => <div>Employers</div>;
const AdminCandidates = () => <div>Candidates</div>;
const AdminJobs = () => <div>Jobs</div>;

// Auth guard component
function RequireAuth({ allowedRoles }: { allowedRoles: string[] }) {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div className="flex h-screen items-center justify-center">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (user && !allowedRoles.includes(user.role)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <Outlet />;
}

// Admin layout
function AdminLayout() {
  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow">
        <div className="mx-auto max-w-7xl px-4 py-4">
          <span className="text-xl font-bold">HireMeNow Admin</span>
        </div>
      </nav>
      <main className="mx-auto max-w-7xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/admin',
    element: <RequireAuth allowedRoles={['admin']} />,
    children: [
      {
        element: <AdminLayout />,
        children: [
          { index: true, element: <Navigate to="dashboard" replace /> },
          { path: 'dashboard', element: <AdminDashboard /> },
          { path: 'companies', element: <AdminCompanies /> },
          { path: 'employers', element: <AdminEmployers /> },
          { path: 'candidates', element: <AdminCandidates /> },
          { path: 'jobs', element: <AdminJobs /> },
        ],
      },
    ],
  },
  {
    path: '/',
    element: <Navigate to="/admin" replace />,
  },
  {
    path: '/unauthorized',
    element: <div>Unauthorized</div>,
  },
]);
```

**Step 5: Update main.tsx**

```typescript
// hiremenow-fe/src/main.tsx
import { StrictMode, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { router } from './routes';
import { useAuth } from './lib/auth';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

function AppInitializer({ children }: { children: React.ReactNode }) {
  const fetchUser = useAuth((state) => state.fetchUser);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  return <>{children}</>;
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AppInitializer>
        <RouterProvider router={router} />
      </AppInitializer>
    </QueryClientProvider>
  </StrictMode>
);
```

**Step 6: Create .env for frontend**

Create `hiremenow-fe/.env`:
```
VITE_API_URL=http://localhost:8000
```

**Step 7: Test frontend runs**

Run: `cd hiremenow-fe && npm run dev`

Expected: App starts at http://localhost:5173, shows "Loading..." then redirects to login

**Step 8: Commit**

```bash
git add hiremenow-fe/package.json hiremenow-fe/package-lock.json hiremenow-fe/src hiremenow-fe/.env
git commit -m "feat(frontend): add router, auth store, and API client setup"
```

---

## Task 14: Frontend - Login Page

**Files:**
- Create: `hiremenow-fe/src/pages/auth/LoginPage.tsx`
- Modify: `hiremenow-fe/src/routes.tsx`

**Step 1: Create login page**

```typescript
// hiremenow-fe/src/pages/auth/LoginPage.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/lib/auth';

export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const login = useAuth((state) => state.login);
  const user = useAuth((state) => state.user);

  // Redirect if already logged in
  if (user) {
    if (user.role === 'admin') {
      navigate('/admin');
    }
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login(email, password);
      navigate('/admin');
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100">
      <div className="w-full max-w-md rounded-lg bg-white p-8 shadow-md">
        <h1 className="mb-6 text-center text-2xl font-bold text-gray-900">
          HireMeNow Admin
        </h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-600">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
          >
            {isLoading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  );
}
```

**Step 2: Update routes to use LoginPage**

```typescript
// hiremenow-fe/src/routes.tsx
import { createBrowserRouter, Navigate, Outlet } from 'react-router-dom';
import { useAuth } from './lib/auth';
import { LoginPage } from './pages/auth/LoginPage';

// Placeholder components - will be replaced
const AdminDashboard = () => <div>Admin Dashboard</div>;
const AdminCompanies = () => <div>Companies</div>;
const AdminEmployers = () => <div>Employers</div>;
const AdminCandidates = () => <div>Candidates</div>;
const AdminJobs = () => <div>Jobs</div>;

// Auth guard component
function RequireAuth({ allowedRoles }: { allowedRoles: string[] }) {
  const { user, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div className="flex h-screen items-center justify-center">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (user && !allowedRoles.includes(user.role)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <Outlet />;
}

// Admin layout
function AdminLayout() {
  const logout = useAuth((state) => state.logout);

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <span className="text-xl font-bold">HireMeNow Admin</span>
          <button
            onClick={logout}
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            Logout
          </button>
        </div>
      </nav>
      <main className="mx-auto max-w-7xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/admin',
    element: <RequireAuth allowedRoles={['admin']} />,
    children: [
      {
        element: <AdminLayout />,
        children: [
          { index: true, element: <Navigate to="dashboard" replace /> },
          { path: 'dashboard', element: <AdminDashboard /> },
          { path: 'companies', element: <AdminCompanies /> },
          { path: 'employers', element: <AdminEmployers /> },
          { path: 'candidates', element: <AdminCandidates /> },
          { path: 'jobs', element: <AdminJobs /> },
        ],
      },
    ],
  },
  {
    path: '/',
    element: <Navigate to="/admin" replace />,
  },
  {
    path: '/unauthorized',
    element: <div>Unauthorized</div>,
  },
]);
```

**Step 3: Test login flow**

1. Start backend: `cd hiremenow-be && docker compose -f docker-compose.linux.yml up`
2. Seed admin: `cd hiremenow-be && python -m scripts.seed_admin`
3. Start frontend: `cd hiremenow-fe && npm run dev`
4. Go to http://localhost:5173/login
5. Login with admin@hiremenow.com / admin123

Expected: Redirects to /admin/dashboard

**Step 4: Commit**

```bash
git add hiremenow-fe/src
git commit -m "feat(frontend): add login page with auth flow"
```

---

## Summary

This completes Phase 1 foundation tasks. The plan covers:

1. **Backend structure** (Task 1)
2. **Alembic & User model** (Task 2)
3. **Auth schemas & utils** (Task 3)
4. **Auth routes** (Task 4)
5. **Company & Employer models** (Task 5)
6. **Candidate model** (Task 6)
7. **Job model** (Task 7)
8. **Admin company CRUD** (Task 8)
9. **Admin employer CRUD** (Task 9)
10. **Admin candidate CRUD + pipeline** (Task 10)
11. **Admin job CRUD** (Task 11)
12. **Admin seed script** (Task 12)
13. **Frontend setup** (Task 13)
14. **Login page** (Task 14)

**Remaining for Phase 1 (separate plan):**
- Admin sidebar navigation
- Admin dashboard with stats
- Companies list/create/edit pages
- Employers list/create pages
- Candidates list/detail/stage management pages
- Jobs list/create/edit/approve pages
- File upload abstraction
- Lead capture public form
