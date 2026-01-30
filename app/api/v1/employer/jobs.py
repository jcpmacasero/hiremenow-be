import re
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.api.deps import get_current_employer
from app.models.employer import Employer
from app.models.company import Company
from app.models.job import Job, JobStatus
from app.models.job_match import JobMatch
from app.schemas.job import JobCreate, JobUpdate, JobResponse, JobListResponse
from app.schemas.job_match import JobMatchResponse, JobMatchListResponse

router = APIRouter(prefix="/jobs", tags=["employer-jobs"])


def generate_slug(title: str) -> str:
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug


def get_unique_slug(db: Session, base_slug: str, company_id: UUID, exclude_id: UUID | None = None) -> str:
    slug = base_slug
    counter = 1
    while True:
        q = db.query(Job).filter(Job.slug == slug, Job.company_id == company_id)
        if exclude_id:
            q = q.filter(Job.id != exclude_id)
        if not q.first():
            return slug
        slug = f"{base_slug}-{counter}"
        counter += 1


@router.get("", response_model=JobListResponse)
def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: JobStatus | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    employer: Employer = Depends(get_current_employer),
):
    """List jobs for current employer's company."""
    query = (
        db.query(Job)
        .options(joinedload(Job.company), joinedload(Job.creator))
        .filter(Job.company_id == employer.company_id)
    )
    if status_filter:
        query = query.filter(Job.status == status_filter)
    total = query.count()
    items = query.order_by(Job.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return JobListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    data: JobCreate,
    db: Session = Depends(get_db),
    employer: Employer = Depends(get_current_employer),
):
    """Create a job for employer's company (must use own company_id)."""
    if data.company_id != employer.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create job for another company",
        )
    company = db.query(Company).filter(Company.id == data.company_id).first()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    slug = get_unique_slug(db, generate_slug(data.title), employer.company_id)
    job = Job(
        company_id=data.company_id,
        created_by=employer.user_id,
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
    job = db.query(Job).options(joinedload(Job.company), joinedload(Job.creator)).filter(Job.id == job.id).first()
    return job


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    employer: Employer = Depends(get_current_employer),
):
    """Get a job by ID (must belong to employer's company)."""
    job = (
        db.query(Job)
        .options(joinedload(Job.company), joinedload(Job.creator))
        .filter(Job.id == job_id, Job.company_id == employer.company_id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.patch("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: UUID,
    data: JobUpdate,
    db: Session = Depends(get_db),
    employer: Employer = Depends(get_current_employer),
):
    """Update a job (only draft or rejected)."""
    job = (
        db.query(Job)
        .options(joinedload(Job.company), joinedload(Job.creator))
        .filter(Job.id == job_id, Job.company_id == employer.company_id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.status not in (JobStatus.DRAFT, JobStatus.REJECTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only edit draft or rejected jobs",
        )
    update_data = data.model_dump(exclude_unset=True)
    update_data.pop("status", None)
    update_data.pop("filled_slots", None)
    if "title" in update_data:
        update_data["slug"] = get_unique_slug(db, generate_slug(update_data["title"]), employer.company_id, exclude_id=job_id)
    for field, value in update_data.items():
        setattr(job, field, value)
    db.commit()
    db.refresh(job)
    return job


@router.post("/{job_id}/submit", response_model=JobResponse)
def submit_for_approval(
    job_id: UUID,
    db: Session = Depends(get_db),
    employer: Employer = Depends(get_current_employer),
):
    """Submit job for admin approval."""
    job = (
        db.query(Job)
        .options(joinedload(Job.company), joinedload(Job.creator))
        .filter(Job.id == job_id, Job.company_id == employer.company_id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.status != JobStatus.DRAFT and job.status != JobStatus.REJECTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft or rejected jobs can be submitted",
        )
    job.status = JobStatus.PENDING_APPROVAL
    db.commit()
    db.refresh(job)
    return job


@router.get("/{job_id}/matches", response_model=JobMatchListResponse)
def list_job_matches(
    job_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    employer: Employer = Depends(get_current_employer),
):
    """List matches for a job (employer's company only)."""
    job = db.query(Job).filter(Job.id == job_id, Job.company_id == employer.company_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    query = (
        db.query(JobMatch)
        .options(joinedload(JobMatch.candidate), joinedload(JobMatch.job))
        .filter(JobMatch.job_id == job_id)
    )
    total = query.count()
    items = query.order_by(JobMatch.suggested_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return JobMatchListResponse(items=items, total=total, page=page, page_size=page_size)
