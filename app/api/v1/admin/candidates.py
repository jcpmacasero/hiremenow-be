from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.api.deps import get_admin_user
from app.models.user import User
from app.models.candidate import Candidate, PassportStatus, LeadSource
from app.core.security import hash_password
from app.schemas.candidate import (
    CandidateCreate,
    CandidateUpdate,
    CandidateResponse,
    CandidateListResponse,
)

router = APIRouter(prefix="/candidates", tags=["admin-candidates"])


@router.get("", response_model=CandidateListResponse)
def list_candidates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_stage: str = Query(None),
    passport_status: PassportStatus = Query(None),
    source: LeadSource = Query(None),
    nationality: str = Query(None),
    search: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """List all candidates with pagination and filtering."""
    query = db.query(Candidate).options(joinedload(Candidate.user))

    if current_stage:
        query = query.filter(Candidate.current_stage == current_stage)

    if passport_status:
        query = query.filter(Candidate.passport_status == passport_status)

    if source:
        query = query.filter(Candidate.source == source)

    if nationality:
        query = query.filter(Candidate.nationality.ilike(f"%{nationality}%"))

    if search:
        search_term = f"%{search}%"
        query = query.join(Candidate.user).filter(
            (Candidate.first_name.ilike(search_term)) |
            (Candidate.last_name.ilike(search_term)) |
            (User.email.ilike(search_term)) |
            (Candidate.phone.ilike(search_term))
        )

    total = query.count()
    items = query.order_by(Candidate.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return CandidateListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
def create_candidate(
    data: CandidateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Create a new candidate with user account."""
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user with candidate role
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role='candidate',
        is_active=True,
    )
    db.add(user)
    db.flush()

    # Create candidate profile
    candidate = Candidate(
        user_id=user.id,
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        date_of_birth=data.date_of_birth,
        nationality=data.nationality,
        current_country=data.current_country,
        passport_status=data.passport_status,
        passport_expiry=data.passport_expiry,
        preferred_positions=data.preferred_positions,
        experience_years=data.experience_years,
        source=data.source,
        referral_code=data.referral_code,
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    # Load relationships
    candidate = db.query(Candidate).options(
        joinedload(Candidate.user),
    ).filter(Candidate.id == candidate.id).first()

    return candidate


@router.get("/{candidate_id}", response_model=CandidateResponse)
def get_candidate(
    candidate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Get a candidate by ID."""
    candidate = db.query(Candidate).options(
        joinedload(Candidate.user),
    ).filter(Candidate.id == candidate_id).first()

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )
    return candidate


@router.patch("/{candidate_id}", response_model=CandidateResponse)
def update_candidate(
    candidate_id: UUID,
    data: CandidateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Update a candidate."""
    candidate = db.query(Candidate).options(
        joinedload(Candidate.user),
    ).filter(Candidate.id == candidate_id).first()

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    update_data = data.model_dump(exclude_unset=True)

    # Handle user active status
    if "is_active" in update_data:
        candidate.user.is_active = update_data.pop("is_active")

    # Handle stage change
    if "current_stage" in update_data:
        candidate.stage_updated_at = datetime.utcnow()

    for field, value in update_data.items():
        setattr(candidate, field, value)

    db.commit()
    db.refresh(candidate)
    return candidate


@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate(
    candidate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Delete a candidate and their user account."""
    candidate = db.query(Candidate).options(
        joinedload(Candidate.user),
    ).filter(Candidate.id == candidate_id).first()

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    # Delete user (candidate will be cascade deleted)
    db.delete(candidate.user)
    db.commit()
    return None


@router.patch("/{candidate_id}/stage", response_model=CandidateResponse)
def update_candidate_stage(
    candidate_id: UUID,
    stage: str = Query(..., max_length=50),
    notes: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Update candidate's pipeline stage."""
    candidate = db.query(Candidate).options(
        joinedload(Candidate.user),
    ).filter(Candidate.id == candidate_id).first()

    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    candidate.current_stage = stage
    candidate.stage_notes = notes
    candidate.stage_updated_at = datetime.utcnow()

    db.commit()
    db.refresh(candidate)
    return candidate
