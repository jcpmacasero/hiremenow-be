from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.api.deps import get_current_candidate
from app.models.candidate import Candidate
from app.schemas.candidate import CandidateResponse, CandidateUpdate

router = APIRouter(prefix="/profile", tags=["candidate-profile"])


@router.get("", response_model=CandidateResponse)
def get_profile(
    db: Session = Depends(get_db),
    candidate: Candidate = Depends(get_current_candidate),
):
    """Get current candidate profile."""
    db.refresh(candidate)
    candidate = (
        db.query(Candidate)
        .options(joinedload(Candidate.user))
        .filter(Candidate.id == candidate.id)
        .first()
    )
    return candidate


@router.put("", response_model=CandidateResponse)
def update_profile(
    data: CandidateUpdate,
    db: Session = Depends(get_db),
    candidate: Candidate = Depends(get_current_candidate),
):
    """Update current candidate profile (candidate-owned fields only)."""
    update_data = data.model_dump(exclude_unset=True)
    # Disallow changing current_stage from candidate side
    update_data.pop("current_stage", None)
    update_data.pop("stage_notes", None)
    update_data.pop("is_active", None)
    for field, value in update_data.items():
        setattr(candidate, field, value)
    db.commit()
    db.refresh(candidate)
    candidate = (
        db.query(Candidate)
        .options(joinedload(Candidate.user))
        .filter(Candidate.id == candidate.id)
        .first()
    )
    return candidate
