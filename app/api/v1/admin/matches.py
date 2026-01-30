from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.api.deps import get_admin_user
from app.models.user import User
from app.models.job import Job, JobStatus
from app.models.candidate import Candidate
from app.models.job_match import JobMatch, MatchStatus
from app.schemas.job_match import JobMatchResponse, JobMatchListResponse, GenerateMatchesResponse

router = APIRouter(prefix="/matches", tags=["admin-matches"])


def _compute_match_score(candidate: Candidate, job: Job) -> int:
    """Simple matching: same country + category overlap gives higher score."""
    score = 50  # base
    if candidate.current_country and job.country and candidate.current_country.lower() == job.country.lower():
        score += 20
    if job.category and candidate.preferred_positions:
        for pos in candidate.preferred_positions:
            if pos and job.category and pos.lower() in job.category.lower():
                score += 15
                break
    return min(100, score)


def _match_reasons(candidate: Candidate, job: Job) -> list[str]:
    reasons = []
    if candidate.current_country and job.country and candidate.current_country.lower() == job.country.lower():
        reasons.append("Location match")
    if job.category and candidate.preferred_positions:
        for pos in candidate.preferred_positions:
            if pos and job.category and pos.lower() in job.category.lower():
                reasons.append("Category match")
                break
    if not reasons:
        reasons.append("Suggested by admin")
    return reasons


@router.post("/jobs/{job_id}/generate", response_model=GenerateMatchesResponse)
def generate_matches_for_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Generate suggested matches for a job (candidates not yet matched, simple algorithm)."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    if job.status != JobStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only generate matches for active jobs",
        )
    if job.filled_slots >= job.total_slots:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job has no available slots",
        )
    # Candidates already matched to this job
    existing = {m.candidate_id for m in db.query(JobMatch.candidate_id).filter(JobMatch.job_id == job_id).all()}
    # Candidates not yet matched to this job
    query = db.query(Candidate)
    if existing:
        query = query.filter(Candidate.id.notin_(list(existing)))
    candidates = query.all()
    generated = 0
    for c in candidates:
        if job.filled_slots + generated >= job.total_slots:
            break
        score = _compute_match_score(c, job)
        reasons = _match_reasons(c, job)
        match = JobMatch(
            candidate_id=c.id,
            job_id=job_id,
            match_score=score,
            match_reasons=reasons,
            status=MatchStatus.SUGGESTED,
        )
        db.add(match)
        generated += 1
    db.commit()
    return GenerateMatchesResponse(generated=generated, message=f"Generated {generated} match(es)")


@router.get("/jobs/{job_id}", response_model=JobMatchListResponse)
def list_job_matches(
    job_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: MatchStatus | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """List matches for a job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    query = (
        db.query(JobMatch)
        .options(joinedload(JobMatch.candidate), joinedload(JobMatch.job))
        .filter(JobMatch.job_id == job_id)
    )
    if status_filter:
        query = query.filter(JobMatch.status == status_filter)
    total = query.count()
    items = query.order_by(JobMatch.match_score.desc(), JobMatch.suggested_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()
    return JobMatchListResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/{match_id}/confirm", response_model=JobMatchResponse)
def confirm_match(
    match_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Confirm a match: set status to confirmed and increment job filled_slots."""
    match = (
        db.query(JobMatch)
        .options(joinedload(JobMatch.job), joinedload(JobMatch.candidate))
        .filter(JobMatch.id == match_id)
        .first()
    )
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    if match.status not in (MatchStatus.SUGGESTED, MatchStatus.CANDIDATE_INTERESTED, MatchStatus.ADMIN_APPROVED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Match cannot be confirmed in current status",
        )
    job = match.job
    if job.filled_slots >= job.total_slots:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job has no available slots",
        )
    match.status = MatchStatus.CONFIRMED
    match.confirmed_at = datetime.utcnow()
    job.filled_slots = job.filled_slots + 1
    if job.filled_slots >= job.total_slots:
        job.status = JobStatus.CLOSED
    db.commit()
    db.refresh(match)
    return match


@router.post("/{match_id}/reject", response_model=JobMatchResponse)
def reject_match(
    match_id: UUID,
    reason: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Reject a match."""
    match = (
        db.query(JobMatch)
        .options(joinedload(JobMatch.job), joinedload(JobMatch.candidate))
        .filter(JobMatch.id == match_id)
        .first()
    )
    if not match:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")
    if match.status in (MatchStatus.CONFIRMED, MatchStatus.REJECTED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Match already confirmed or rejected",
        )
    match.status = MatchStatus.REJECTED
    match.rejected_reason = reason
    db.commit()
    db.refresh(match)
    return match
