from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    type: str
    title: str
    message: Optional[str]
    data: dict
    action_url: Optional[str]
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    page_size: int
    unread_count: int
