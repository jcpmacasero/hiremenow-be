from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.api.deps import get_current_employer
from app.models.employer import Employer
from app.models.company import Company
from app.schemas.company import CompanyResponse, CompanyUpdate

router = APIRouter(prefix="/company", tags=["employer-company"])


@router.get("", response_model=CompanyResponse)
def get_company(
    db: Session = Depends(get_db),
    employer: Employer = Depends(get_current_employer),
):
    """Get current employer's company."""
    company = db.query(Company).filter(Company.id == employer.company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company


@router.put("", response_model=CompanyResponse)
def update_company(
    data: CompanyUpdate,
    db: Session = Depends(get_db),
    employer: Employer = Depends(get_current_employer),
):
    """Update current employer's company (limited fields)."""
    company = db.query(Company).filter(Company.id == employer.company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    update_data = data.model_dump(exclude_unset=True)
    update_data.pop("is_active", None)  # only admin can change
    for field, value in update_data.items():
        setattr(company, field, value)
    db.commit()
    db.refresh(company)
    return company
