from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_candidate
from app.models.candidate import Candidate
from app.models.document import Document, DocumentType, DocumentStatus
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentListResponse
from app.services.storage import StorageService, get_storage_service

router = APIRouter(prefix="/documents", tags=["candidate-documents"])


@router.get("", response_model=DocumentListResponse)
def list_documents(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    candidate: Candidate = Depends(get_current_candidate),
):
    """List current candidate's documents."""
    query = db.query(Document).filter(Document.candidate_id == candidate.id)
    total = query.count()
    items = query.order_by(Document.uploaded_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return DocumentListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    type: DocumentType = Form(DocumentType.OTHER),
    name: str | None = Form(None),
    db: Session = Depends(get_db),
    candidate: Candidate = Depends(get_current_candidate),
    storage: StorageService = Depends(get_storage_service),
):
    """Upload a document (passport, certificate, etc.)."""
    doc = Document(
        candidate_id=candidate.id,
        type=type,
        name=name or (file.filename or "document"),
        file_url="",  # set after save
        status=DocumentStatus.PENDING_REVIEW,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    try:
        url, file_size = await storage.save_document(file, candidate.id, doc.id)
        doc.file_url = url
        doc.file_size = file_size
        if file.content_type:
            doc.mime_type = file.content_type[:100]
        db.commit()
        db.refresh(doc)
        return doc
    except Exception:
        db.delete(doc)
        db.commit()
        raise


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    candidate: Candidate = Depends(get_current_candidate),
):
    """Get a document by ID (must belong to current candidate)."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.candidate_id == candidate.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    candidate: Candidate = Depends(get_current_candidate),
):
    """Delete a document (only if pending or rejected)."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.candidate_id == candidate.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if doc.status == DocumentStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete an approved document",
        )
    db.delete(doc)
    db.commit()
    return None
