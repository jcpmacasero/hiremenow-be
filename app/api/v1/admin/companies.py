import re
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.api.deps import get_admin_user
from app.models.user import User
from app.models.company import Company
from app.schemas.company import (
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    CompanyListResponse,
)

router = APIRouter(prefix="/companies", tags=["admin-companies"])


def generate_slug(name: str) -> str:
    """Generate a URL-friendly slug from company name."""
    slug = name.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug


def get_unique_slug(db: Session, base_slug: str, exclude_id: UUID = None) -> str:
    """Ensure slug is unique, append number if needed."""
    slug = base_slug
    counter = 1
    while True:
        query = db.query(Company).filter(Company.slug == slug)
        if exclude_id:
            query = query.filter(Company.id != exclude_id)
        if not query.first():
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


@router.get("", response_model=CompanyListResponse)
def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: bool = Query(None),
    search: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """List all companies with pagination and filtering."""
    query = db.query(Company)

    if is_active is not None:
        query = query.filter(Company.is_active == is_active)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Company.name.ilike(search_term)) |
            (Company.industry.ilike(search_term)) |
            (Company.location.ilike(search_term))
        )

    total = query.count()
    items = query.order_by(Company.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return CompanyListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(
    data: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Create a new company."""
    base_slug = generate_slug(data.name)
    slug = get_unique_slug(db, base_slug)

    company = Company(
        name=data.name,
        slug=slug,
        description=data.description,
        logo_url=data.logo_url,
        website=data.website,
        location=data.location,
        industry=data.industry,
        is_agency_owned=data.is_agency_owned,
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Get a company by ID."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )
    return company


@router.patch("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: UUID,
    data: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Update a company."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    update_data = data.model_dump(exclude_unset=True)

    # Update slug if name changes
    if "name" in update_data:
        base_slug = generate_slug(update_data["name"])
        update_data["slug"] = get_unique_slug(db, base_slug, exclude_id=company_id)

    for field, value in update_data.items():
        setattr(company, field, value)

    db.commit()
    db.refresh(company)
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Delete a company."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    db.delete(company)
    db.commit()
    return None
