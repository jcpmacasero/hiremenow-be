from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.api.deps import get_current_candidate
from app.models.candidate import Candidate
from app.models.job import Job, JobStatus
from app.models.job_match import JobMatch, MatchStatus
from app.schemas.job import JobResponse, JobListResponse
from app.schemas.job_match import JobMatchResponse, JobMatchListResponse, ExpressInterestRequest

router = APIRouter(prefix="/jobs", tags=["candidate-jobs"])


@router.get("", response_model=JobListResponse)
def list_available_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    candidate: Candidate = Depends(get_current_candidate),
):
    """List jobs that are matched to the candidate (suggested or candidate_interested)."""
    subq = (
        db.query(JobMatch.job_id)
        .filter(
            JobMatch.candidate_id == candidate.id,
            JobMatch.status.in_([MatchStatus.SUGGESTED, MatchStatus.CANDIDATE_INTERESTED, MatchStatus.ADMIN_APPROVED]),
        )
    )
    query = (
        db.query(Job)
        .options(joinedload(Job.company), joinedload(Job.creator))
        .filter(Job.id.in_(subq), Job.status == JobStatus.ACTIVE)
    )
    total = query.count()
    items = query.order_by(Job.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return JobListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/matches", response_model=JobMatchListResponse)
def list_my_matches(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: MatchStatus | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    candidate: Candidate = Depends(get_current_candidate),
):
    """List job matches for the current candidate."""
    query = (
        db.query(JobMatch)
        .options(
            joinedload(JobMatch.job).joinedload(Job.company),
            joinedload(JobMatch.candidate),
        )
        .filter(JobMatch.candidate_id == candidate.id)
    )
    if status_filter:
        query = query.filter(JobMatch.status == status_filter)
    total = query.count()
    items = query.order_by(JobMatch.suggested_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return JobMatchListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    candidate: Candidate = Depends(get_current_candidate),
):
    """Get a job detail (only if candidate has a match for this job)."""
    match = (
        db.query(JobMatch)
        .filter(
            JobMatch.candidate_id == candidate.id,
            JobMatch.job_id == job_id,
            JobMatch.status.in_([MatchStatus.SUGGESTED, MatchStatus.CANDIDATE_INTERESTED, MatchStatus.ADMIN_APPROVED, MatchStatus.CONFIRMED]),
        )
        .first()
    )
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found or not matched to you")
    job = db.query(Job).options(joinedload(Job.company), joinedload(Job.creator)).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.post("/{job_id}/interest", response_model=JobMatchResponse)
def express_interest(
    job_id: UUID,
    data: ExpressInterestRequest = ExpressInterestRequest(),
    db: Session = Depends(get_db),
    candidate: Candidate = Depends(get_current_candidate),
):
    """Express interest in a matched job (or withdraw interest)."""
    match = (
        db.query(JobMatch)
        .options(joinedload(JobMatch.job), joinedload(JobMatch.candidate))
        .filter(JobMatch.candidate_id == candidate.id, JobMatch.job_id == job_id)
        .first()
    )
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    if match.status not in (MatchStatus.SUGGESTED, MatchStatus.CANDIDATE_INTERESTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change interest for this match status",
        )
    match.status = MatchStatus.CANDIDATE_INTERESTED if data.interested else MatchStatus.SUGGESTED
    db.commit()
    db.refresh(match)
    return match
