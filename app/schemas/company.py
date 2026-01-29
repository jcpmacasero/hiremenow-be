from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class CompanyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    website: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    is_agency_owned: bool = False


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    logo_url: Optional[str] = Field(None, max_length=500)
    website: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=255)
    industry: Optional[str] = Field(None, max_length=100)
    is_agency_owned: Optional[bool] = None
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
    items: list[CompanyResponse]
    total: int
    page: int
    page_size: int
