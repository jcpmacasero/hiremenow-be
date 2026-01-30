import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.orm import relationship
from app.database import Base


class MatchStatus(str, PyEnum):
    SUGGESTED = "suggested"
    CANDIDATE_INTERESTED = "candidate_interested"
    ADMIN_APPROVED = "admin_approved"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


matchstatus_enum = ENUM(
    "suggested", "candidate_interested", "admin_approved", "confirmed", "rejected",
    name="matchstatus", create_type=False
)


class JobMatch(Base):
    __tablename__ = "job_matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)

    match_score = Column(Integer, default=0, nullable=False)  # 0-100
    match_reasons = Column(JSONB, default=list, nullable=False)

    status = Column(matchstatus_enum, default="suggested", nullable=False)
    suggested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    confirmed_at = Column(DateTime, nullable=True)
    rejected_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    candidate = relationship("Candidate", back_populates="job_matches")
    job = relationship("Job", back_populates="job_matches")

    def __repr__(self):
        return f"<JobMatch candidate={self.candidate_id} job={self.job_id} status={self.status}>"
