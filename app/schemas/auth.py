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
