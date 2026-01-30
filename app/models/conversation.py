import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
from app.database import Base


class ConversationType(str, PyEnum):
    DIRECT = "direct"
    SUPPORT = "support"
    GROUP = "group"


class ParticipantRole(str, PyEnum):
    MEMBER = "member"
    ADMIN = "admin"


class MessageContentType(str, PyEnum):
    TEXT = "text"
    FILE = "file"
    IMAGE = "image"
    SYSTEM = "system"


conversationtype_enum = ENUM("direct", "support", "group", name="conversationtype", create_type=False)
participantrole_enum = ENUM("member", "admin", name="participantrole", create_type=False)
messagecontenttype_enum = ENUM("text", "file", "image", "system", name="messagecontenttype", create_type=False)


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(conversationtype_enum, default="direct", nullable=False)
    subject = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    participants = relationship("ConversationParticipant", back_populates="conversation", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class ConversationParticipant(Base):
    __tablename__ = "conversation_participants"

    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role = Column(participantrole_enum, default="member", nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_read_at = Column(DateTime, nullable=True)
    is_muted = Column(Boolean, default=False, nullable=False)

    conversation = relationship("Conversation", back_populates="participants")
    user = relationship("User", backref="conversation_participations")


class Message(Base):
    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    content = Column(Text, nullable=False)
    content_type = Column(messagecontenttype_enum, default="text", nullable=False)
    file_url = Column(String(500), nullable=True)
    is_edited = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", backref="sent_messages")
    reads = relationship("MessageRead", back_populates="message", cascade="all, delete-orphan")


class MessageRead(Base):
    __tablename__ = "message_reads"

    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    read_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    message = relationship("Message", back_populates="reads")
    user = relationship("User", backref="message_reads")
