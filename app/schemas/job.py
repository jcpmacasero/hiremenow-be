from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.job import WorkMode, JobType, JobStatus, SalaryPeriod


class JobCompanyInfo(BaseModel):
    id: UUID
    name: str
    slug: str

    class Config:
        from_attributes = True


class JobCreatorInfo(BaseModel):
    id: UUID
    email: str

    class Config:
        from_attributes = True


class JobBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    category: Optional[str] = Field(None, max_length=100)
    country: str = Field(..., max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    work_mode: WorkMode = WorkMode.ONSITE
    job_type: JobType = JobType.FULL_TIME
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    salary_currency: str = Field("EUR", max_length=3)
    salary_period: SalaryPeriod = SalaryPeriod.MONTHLY
    benefits: list[str] = []
    requirements: dict = {}
    total_slots: int = Field(1, ge=1)
    deadline: Optional[date] = None
    start_date: Optional[date] = None


class JobCreate(JobBase):
    company_id: UUID


class JobUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    work_mode: Optional[WorkMode] = None
    job_type: Optional[JobType] = None
    salary_min: Optional[Decimal] = None
    salary_max: Optional[Decimal] = None
    salary_currency: Optional[str] = Field(None, max_length=3)
    salary_period: Optional[SalaryPeriod] = None
    benefits: Optional[list[str]] = None
    requirements: Optional[dict] = None
    total_slots: Optional[int] = Field(None, ge=1)
    filled_slots: Optional[int] = Field(None, ge=0)
    status: Optional[JobStatus] = None
    rejection_reason: Optional[str] = None
    deadline: Optional[date] = None
    start_date: Optional[date] = None


class JobResponse(BaseModel):
    id: UUID
    company_id: UUID
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
    benefits: list[str]
    requirements: dict
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
    company: JobCompanyInfo
    creator: Optional[JobCreatorInfo]

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    items: list[JobResponse]
    total: int
    page: int
    page_size: int
