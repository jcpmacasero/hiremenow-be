import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
from app.database import Base


class DocumentType(str, PyEnum):
    PASSPORT = "passport"
    RESUME = "resume"
    PHOTO = "photo"
    CERTIFICATE = "certificate"
    AGREEMENT = "agreement"
    OTHER = "other"


class DocumentStatus(str, PyEnum):
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"


documenttype_enum = ENUM(
    "passport", "resume", "photo", "certificate", "agreement", "other",
    name="documenttype", create_type=False
)
documentstatus_enum = ENUM(
    "pending_review", "approved", "rejected",
    name="documentstatus", create_type=False
)


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)

    type = Column(documenttype_enum, nullable=False)
    name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)

    status = Column(documentstatus_enum, default="pending_review", nullable=False)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reviewed_at = Column(DateTime, nullable=True)

    # Relationships
    candidate = relationship("Candidate", back_populates="documents")
    reviewer = relationship("User", backref="reviewed_documents")

    def __repr__(self):
        return f"<Document {self.type} {self.name}>"
