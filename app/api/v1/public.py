# hiremenow-be/app/api/v1/public.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.candidate import Candidate, LeadSource
from app.core.security import hash_password

router = APIRouter(prefix="/public", tags=["public"])


class LeadCaptureRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    nationality: Optional[str] = Field(None, max_length=100)
    current_country: Optional[str] = Field(None, max_length=100)
    source: LeadSource = LeadSource.WEBSITE
    referral_code: Optional[str] = Field(None, max_length=50)


class LeadCaptureResponse(BaseModel):
    success: bool
    message: str


@router.post("/lead", response_model=LeadCaptureResponse)
def capture_lead(
    data: LeadCaptureRequest,
    db: Session = Depends(get_db),
):
    """Public endpoint for lead capture (candidate registration)."""
    # Check if email exists
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role='candidate',
        is_active=True,
    )
    db.add(user)
    db.flush()

    # Create candidate
    candidate = Candidate(
        user_id=user.id,
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        nationality=data.nationality,
        current_country=data.current_country,
        source=data.source,
        referral_code=data.referral_code,
        current_stage='lead',
    )
    db.add(candidate)
    db.commit()

    return LeadCaptureResponse(
        success=True,
        message="Thank you for registering! We will contact you soon.",
    )
