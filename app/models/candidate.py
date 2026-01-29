import uuid
from datetime import datetime, date
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Boolean, DateTime, Date, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
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


# PostgreSQL ENUM types
passportstatus_enum = ENUM('valid', 'expired', 'none', 'in_progress', name='passportstatus', create_type=False)
leadsource_enum = ENUM('website', 'facebook', 'instagram', 'referral', 'other', name='leadsource', create_type=False)


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
    passport_status = Column(passportstatus_enum, default='none', nullable=False)
    passport_expiry = Column(Date, nullable=True)

    # Professional
    preferred_positions = Column(JSONB, default=list, nullable=False)
    experience_years = Column(Integer, default=0, nullable=False)

    # Files
    photo_url = Column(String(500), nullable=True)
    resume_url = Column(String(500), nullable=True)

    # Tracking
    source = Column(leadsource_enum, default='website', nullable=False)
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
