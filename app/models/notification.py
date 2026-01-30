import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from sqlalchemy.orm import relationship
from app.database import Base


class NotificationType(str, PyEnum):
    STAGE_CHANGED = "stage_changed"
    PAYMENT_RECEIVED = "payment_received"
    TEST_RESULT = "test_result"
    JOB_MATCH = "job_match"
    MESSAGE_RECEIVED = "message_received"
    DOCUMENT_REQUIRED = "document_required"
    APPLICATION_UPDATE = "application_update"
    COURSE_REMINDER = "course_reminder"
    SYSTEM = "system"


notificationtype_enum = ENUM(
    "stage_changed", "payment_received", "test_result", "job_match",
    "message_received", "document_required", "application_update", "course_reminder", "system",
    name="notificationtype", create_type=False
)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    type = Column(notificationtype_enum, nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    data = Column(JSONB, default=dict, nullable=False)
    action_url = Column(String(500), nullable=True)

    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", backref="notifications")

    def __repr__(self):
        return f"<Notification {self.type} for user={self.user_id}>"
