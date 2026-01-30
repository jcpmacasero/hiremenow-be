import uuid
from datetime import datetime, date
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Boolean, DateTime, Date, Integer, ForeignKey, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
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


# PostgreSQL ENUM types
workmode_enum = ENUM('onsite', 'accommodation_provided', name='workmode', create_type=False)
jobtype_enum = ENUM('full_time', 'part_time', 'contract', 'seasonal', name='jobtype', create_type=False)
jobstatus_enum = ENUM('draft', 'pending_approval', 'active', 'paused', 'closed', 'rejected', name='jobstatus', create_type=False)
salaryperiod_enum = ENUM('hourly', 'monthly', name='salaryperiod', create_type=False)


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
    work_mode = Column(workmode_enum, default='onsite', nullable=False)

    # Employment
    job_type = Column(jobtype_enum, default='full_time', nullable=False)

    # Salary
    salary_min = Column(Numeric(10, 2), nullable=True)
    salary_max = Column(Numeric(10, 2), nullable=True)
    salary_currency = Column(String(3), default="EUR", nullable=False)
    salary_period = Column(salaryperiod_enum, default='monthly', nullable=False)

    # Details
    benefits = Column(JSONB, default=list, nullable=False)
    requirements = Column(JSONB, default=dict, nullable=False)

    # Slots
    total_slots = Column(Integer, default=1, nullable=False)
    filled_slots = Column(Integer, default=0, nullable=False)

    # Status & dates
    status = Column(jobstatus_enum, default='draft', nullable=False)
    rejection_reason = Column(Text, nullable=True)
    deadline = Column(Date, nullable=True)
    start_date = Column(Date, nullable=True)
    published_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    company = relationship("Company", back_populates="jobs")
    creator = relationship("User", backref="created_jobs")
    job_matches = relationship("JobMatch", back_populates="job", cascade="all, delete-orphan")

    @property
    def available_slots(self) -> int:
        return max(0, self.total_slots - self.filled_slots)

    def __repr__(self):
        return f"<Job {self.title}>"
