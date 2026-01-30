from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_admin_user
from app.models.user import User
from app.models.candidate import Candidate
from app.services.storage import StorageService, get_storage_service


router = APIRouter(prefix="/uploads", tags=["admin-uploads"])


class UploadResponse(BaseModel):
    url: str
    message: str


@router.post("/candidates/{candidate_id}/photo", response_model=UploadResponse)
async def upload_candidate_photo(
    candidate_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
    storage: StorageService = Depends(get_storage_service),
):
    """Upload a photo for a candidate."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    url = await storage.save_photo(file, candidate_id)
    candidate.photo_url = url
    db.commit()

    return UploadResponse(url=url, message="Photo uploaded successfully")


@router.post("/candidates/{candidate_id}/resume", response_model=UploadResponse)
async def upload_candidate_resume(
    candidate_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
    storage: StorageService = Depends(get_storage_service),
):
    """Upload a resume for a candidate."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    url = await storage.save_resume(file, candidate_id)
    candidate.resume_url = url
    db.commit()

    return UploadResponse(url=url, message="Resume uploaded successfully")


@router.delete("/candidates/{candidate_id}/photo", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate_photo(
    candidate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
    storage: StorageService = Depends(get_storage_service),
):
    """Delete a candidate's photo."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    storage.delete_photo(candidate_id)
    candidate.photo_url = None
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/candidates/{candidate_id}/resume", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate_resume(
    candidate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
    storage: StorageService = Depends(get_storage_service),
):
    """Delete a candidate's resume."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    storage.delete_resume(candidate_id)
    candidate.resume_url = None
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
