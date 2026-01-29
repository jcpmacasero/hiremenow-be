from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.api.deps import get_admin_user
from app.models.user import User
from app.models.company import Company
from app.models.employer import Employer
from app.core.security import hash_password
from app.schemas.employer import (
    EmployerCreate,
    EmployerUpdate,
    EmployerResponse,
    EmployerListResponse,
)

router = APIRouter(prefix="/employers", tags=["admin-employers"])


@router.get("", response_model=EmployerListResponse)
def list_employers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    company_id: UUID = Query(None),
    search: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """List all employers with pagination and filtering."""
    query = db.query(Employer).options(
        joinedload(Employer.user),
        joinedload(Employer.company),
    )

    if company_id:
        query = query.filter(Employer.company_id == company_id)

    if search:
        search_term = f"%{search}%"
        query = query.join(Employer.user).filter(User.email.ilike(search_term))

    total = query.count()
    items = query.order_by(Employer.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return EmployerListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=EmployerResponse, status_code=status.HTTP_201_CREATED)
def create_employer(
    data: EmployerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Create a new employer with user account."""
    # Check if company exists
    company = db.query(Company).filter(Company.id == data.company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    # Check if email already exists
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user with employer role
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role='employer',
        is_active=True,
    )
    db.add(user)
    db.flush()

    # Create employer profile
    employer = Employer(
        user_id=user.id,
        company_id=data.company_id,
    )
    db.add(employer)
    db.commit()
    db.refresh(employer)

    # Load relationships
    employer = db.query(Employer).options(
        joinedload(Employer.user),
        joinedload(Employer.company),
    ).filter(Employer.id == employer.id).first()

    return employer


@router.get("/{employer_id}", response_model=EmployerResponse)
def get_employer(
    employer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Get an employer by ID."""
    employer = db.query(Employer).options(
        joinedload(Employer.user),
        joinedload(Employer.company),
    ).filter(Employer.id == employer_id).first()

    if not employer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer not found",
        )
    return employer


@router.patch("/{employer_id}", response_model=EmployerResponse)
def update_employer(
    employer_id: UUID,
    data: EmployerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Update an employer."""
    employer = db.query(Employer).options(
        joinedload(Employer.user),
        joinedload(Employer.company),
    ).filter(Employer.id == employer_id).first()

    if not employer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer not found",
        )

    update_data = data.model_dump(exclude_unset=True)

    # Handle company change
    if "company_id" in update_data:
        company = db.query(Company).filter(Company.id == update_data["company_id"]).first()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found",
            )
        employer.company_id = update_data.pop("company_id")

    # Handle user active status
    if "is_active" in update_data:
        employer.user.is_active = update_data.pop("is_active")

    db.commit()
    db.refresh(employer)
    return employer


@router.delete("/{employer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employer(
    employer_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Delete an employer and their user account."""
    employer = db.query(Employer).options(
        joinedload(Employer.user),
    ).filter(Employer.id == employer_id).first()

    if not employer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer not found",
        )

    # Delete user (employer will be cascade deleted)
    db.delete(employer.user)
    db.commit()
    return None
