from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from app.models.conversation import MessageContentType


class MessageReadResponse(BaseModel):
    message_id: UUID
    user_id: UUID
    read_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_id: Optional[UUID]
    content: str
    content_type: MessageContentType
    file_url: Optional[str]
    is_edited: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationParticipantResponse(BaseModel):
    user_id: UUID
    role: str
    joined_at: datetime
    last_read_at: Optional[datetime]

    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    id: UUID
    type: str
    subject: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]
    total: int
    page: int
    page_size: int


class MessageCreate(BaseModel):
    content: str
    content_type: MessageContentType = MessageContentType.TEXT


class ConversationCreate(BaseModel):
    type: str = "direct"
    subject: Optional[str] = None
    participant_user_ids: list[UUID]
