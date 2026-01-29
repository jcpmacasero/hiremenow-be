from datetime import datetime, date
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

from app.models.candidate import PassportStatus, LeadSource


class CandidateUserInfo(BaseModel):
    id: UUID
    email: str
    is_active: bool

    class Config:
        from_attributes = True


class CandidateCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = Field(None, max_length=100)
    current_country: Optional[str] = Field(None, max_length=100)
    passport_status: PassportStatus = PassportStatus.NONE
    passport_expiry: Optional[date] = None
    preferred_positions: list[str] = []
    experience_years: int = 0
    source: LeadSource = LeadSource.WEBSITE
    referral_code: Optional[str] = Field(None, max_length=50)


class CandidateUpdate(BaseModel):
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = Field(None, max_length=100)
    current_country: Optional[str] = Field(None, max_length=100)
    passport_status: Optional[PassportStatus] = None
    passport_expiry: Optional[date] = None
    preferred_positions: Optional[list[str]] = None
    experience_years: Optional[int] = None
    photo_url: Optional[str] = Field(None, max_length=500)
    resume_url: Optional[str] = Field(None, max_length=500)
    source: Optional[LeadSource] = None
    referral_code: Optional[str] = Field(None, max_length=50)
    current_stage: Optional[str] = Field(None, max_length=50)
    stage_notes: Optional[str] = None
    is_active: Optional[bool] = None


class CandidateResponse(BaseModel):
    id: UUID
    user_id: UUID
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    date_of_birth: Optional[date]
    nationality: Optional[str]
    current_country: Optional[str]
    passport_status: PassportStatus
    passport_expiry: Optional[date]
    preferred_positions: list[str]
    experience_years: int
    photo_url: Optional[str]
    resume_url: Optional[str]
    source: LeadSource
    referral_code: Optional[str]
    current_stage: str
    stage_notes: Optional[str]
    stage_updated_at: datetime
    created_at: datetime
    updated_at: datetime
    user: CandidateUserInfo

    class Config:
        from_attributes = True


class CandidateListResponse(BaseModel):
    items: list[CandidateResponse]
    total: int
    page: int
    page_size: int
