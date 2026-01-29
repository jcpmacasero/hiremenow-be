import re
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.api.deps import get_admin_user
from app.models.user import User
from app.models.company import Company
from app.models.job import Job, JobStatus, WorkMode, JobType
from app.schemas.job import (
    JobCreate,
    JobUpdate,
    JobResponse,
    JobListResponse,
)

router = APIRouter(prefix="/jobs", tags=["admin-jobs"])


def generate_slug(title: str) -> str:
    """Generate a URL-friendly slug from job title."""
    slug = title.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug


def get_unique_slug(db: Session, base_slug: str, exclude_id: UUID = None) -> str:
    """Ensure slug is unique, append number if needed."""
    slug = base_slug
    counter = 1
    while True:
        query = db.query(Job).filter(Job.slug == slug)
        if exclude_id:
            query = query.filter(Job.id != exclude_id)
        if not query.first():
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


@router.get("", response_model=JobListResponse)
def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    company_id: UUID = Query(None),
    status_filter: JobStatus = Query(None, alias="status"),
    work_mode: WorkMode = Query(None),
    job_type: JobType = Query(None),
    country: str = Query(None),
    search: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """List all jobs with pagination and filtering."""
    query = db.query(Job).options(
        joinedload(Job.company),
        joinedload(Job.creator),
    )

    if company_id:
        query = query.filter(Job.company_id == company_id)

    if status_filter:
        query = query.filter(Job.status == status_filter)

    if work_mode:
        query = query.filter(Job.work_mode == work_mode)

    if job_type:
        query = query.filter(Job.job_type == job_type)

    if country:
        query = query.filter(Job.country.ilike(f"%{country}%"))

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Job.title.ilike(search_term)) |
            (Job.description.ilike(search_term)) |
            (Job.category.ilike(search_term))
        )

    total = query.count()
    items = query.order_by(Job.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return JobListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    data: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Create a new job."""
    # Check if company exists
    company = db.query(Company).filter(Company.id == data.company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found",
        )

    base_slug = generate_slug(data.title)
    slug = get_unique_slug(db, base_slug)

    job = Job(
        company_id=data.company_id,
        created_by=current_user.id,
        title=data.title,
        slug=slug,
        description=data.description,
        category=data.category,
        country=data.country,
        city=data.city,
        work_mode=data.work_mode,
        job_type=data.job_type,
        salary_min=data.salary_min,
        salary_max=data.salary_max,
        salary_currency=data.salary_currency,
        salary_period=data.salary_period,
        benefits=data.benefits,
        requirements=data.requirements,
        total_slots=data.total_slots,
        deadline=data.deadline,
        start_date=data.start_date,
        status=JobStatus.DRAFT,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Load relationships
    job = db.query(Job).options(
        joinedload(Job.company),
        joinedload(Job.creator),
    ).filter(Job.id == job.id).first()

    return job


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Get a job by ID."""
    job = db.query(Job).options(
        joinedload(Job.company),
        joinedload(Job.creator),
    ).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    return job


@router.patch("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: UUID,
    data: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Update a job."""
    job = db.query(Job).options(
        joinedload(Job.company),
        joinedload(Job.creator),
    ).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    update_data = data.model_dump(exclude_unset=True)

    # Update slug if title changes
    if "title" in update_data:
        base_slug = generate_slug(update_data["title"])
        update_data["slug"] = get_unique_slug(db, base_slug, exclude_id=job_id)

    # Handle status change to active
    if "status" in update_data and update_data["status"] == JobStatus.ACTIVE:
        if not job.published_at:
            update_data["published_at"] = datetime.utcnow()

    for field, value in update_data.items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Delete a job."""
    job = db.query(Job).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    db.delete(job)
    db.commit()
    return None


@router.post("/{job_id}/approve", response_model=JobResponse)
def approve_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Approve a pending job and set it to active."""
    job = db.query(Job).options(
        joinedload(Job.company),
        joinedload(Job.creator),
    ).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if job.status != JobStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job is not pending approval",
        )

    job.status = JobStatus.ACTIVE
    job.published_at = datetime.utcnow()

    db.commit()
    db.refresh(job)
    return job


@router.post("/{job_id}/reject", response_model=JobResponse)
def reject_job(
    job_id: UUID,
    reason: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Reject a pending job."""
    job = db.query(Job).options(
        joinedload(Job.company),
        joinedload(Job.creator),
    ).filter(Job.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if job.status != JobStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job is not pending approval",
        )

    job.status = JobStatus.REJECTED
    job.rejection_reason = reason

    db.commit()
    db.refresh(job)
    return job
