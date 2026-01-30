from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.api.deps import get_admin_user
from app.models.user import User
from app.models.document import Document, DocumentStatus
from app.schemas.document import DocumentResponse, DocumentListResponse

router = APIRouter(prefix="/documents", tags=["admin-documents"])


@router.get("/pending", response_model=DocumentListResponse)
def list_pending_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """List documents pending review."""
    query = (
        db.query(Document)
        .filter(Document.status == DocumentStatus.PENDING_REVIEW)
        .order_by(Document.uploaded_at.asc())
    )
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return DocumentListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/{document_id}/approve", response_model=DocumentResponse)
def approve_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Approve a document."""
    from datetime import datetime

    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if doc.status != DocumentStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document is not pending review",
        )
    doc.status = DocumentStatus.APPROVED
    doc.reviewed_by = current_user.id
    doc.reviewed_at = datetime.utcnow()
    doc.rejection_reason = None
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/{document_id}/reject", response_model=DocumentResponse)
def reject_document(
    document_id: UUID,
    reason: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Reject a document."""
    from datetime import datetime

    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if doc.status != DocumentStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document is not pending review",
        )
    doc.status = DocumentStatus.REJECTED
    doc.reviewed_by = current_user.id
    doc.reviewed_at = datetime.utcnow()
    doc.rejection_reason = reason
    db.commit()
    db.refresh(doc)
    return doc
