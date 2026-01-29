from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class EmployerUserInfo(BaseModel):
    id: UUID
    email: str
    is_active: bool

    class Config:
        from_attributes = True


class EmployerCompanyInfo(BaseModel):
    id: UUID
    name: str
    slug: str

    class Config:
        from_attributes = True


class EmployerCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    company_id: UUID


class EmployerUpdate(BaseModel):
    company_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class EmployerResponse(BaseModel):
    id: UUID
    user_id: UUID
    company_id: UUID
    created_at: datetime
    user: EmployerUserInfo
    company: EmployerCompanyInfo

    class Config:
        from_attributes = True


class EmployerListResponse(BaseModel):
    items: list[EmployerResponse]
    total: int
    page: int
    page_size: int
