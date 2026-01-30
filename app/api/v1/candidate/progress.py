from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.api.deps import get_current_candidate
from app.models.candidate import Candidate

router = APIRouter(prefix="/progress", tags=["candidate-progress"])


class ProgressResponse(BaseModel):
    current_stage: str
    stage_notes: str | None
    stage_updated_at: str
    requirements: list[str]  # placeholder for stage requirements

    class Config:
        from_attributes = True


@router.get("", response_model=ProgressResponse)
def get_progress(
    db: Session = Depends(get_db),
    candidate: Candidate = Depends(get_current_candidate),
):
    """Get current pipeline progress and next steps."""
    db.refresh(candidate)
    return ProgressResponse(
        current_stage=candidate.current_stage,
        stage_notes=candidate.stage_notes,
        stage_updated_at=candidate.stage_updated_at.isoformat() if candidate.stage_updated_at else "",
        requirements=[],  # Phase 2: simple fixed pipeline; requirements can be added later
    )
