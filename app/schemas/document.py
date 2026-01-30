from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.document import DocumentType, DocumentStatus


class DocumentBase(BaseModel):
    type: DocumentType
    name: str = Field(..., max_length=255)


class DocumentCreate(BaseModel):
    type: DocumentType
    name: str = Field(..., max_length=255)


class DocumentResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    type: DocumentType
    name: str
    file_url: str
    file_size: Optional[int]
    mime_type: Optional[str]
    status: DocumentStatus
    rejection_reason: Optional[str]
    uploaded_at: datetime
    reviewed_at: Optional[datetime]

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
    page: int
    page_size: int
