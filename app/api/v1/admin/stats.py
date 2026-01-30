from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.api.deps import get_admin_user
from app.models.user import User
from app.models.company import Company
from app.models.employer import Employer
from app.models.candidate import Candidate
from app.models.job import Job

router = APIRouter(prefix="/stats", tags=["admin-stats"])


@router.get("")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Get dashboard statistics."""
    total_companies = db.query(func.count(Company.id)).scalar() or 0
    total_employers = db.query(func.count(Employer.id)).scalar() or 0
    total_candidates = db.query(func.count(Candidate.id)).scalar() or 0
    total_jobs = db.query(func.count(Job.id)).scalar() or 0
    active_jobs = db.query(func.count(Job.id)).filter(Job.status == "active").scalar() or 0

    # Candidates by stage
    stage_counts = (
        db.query(Candidate.current_stage, func.count(Candidate.id))
        .group_by(Candidate.current_stage)
        .all()
    )
    candidates_by_stage = {str(stage) if stage else "unknown": count for stage, count in stage_counts}

    return {
        "total_companies": total_companies,
        "total_employers": total_employers,
        "total_candidates": total_candidates,
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "candidates_by_stage": candidates_by_stage,
    }
