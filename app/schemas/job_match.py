from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

from app.models.job_match import MatchStatus


class JobMatchCandidateInfo(BaseModel):
    id: UUID
    first_name: Optional[str]
    last_name: Optional[str]
    current_stage: str

    class Config:
        from_attributes = True


class JobMatchJobInfo(BaseModel):
    id: UUID
    title: str
    slug: str
    country: str
    status: str
    total_slots: int
    filled_slots: int
    available_slots: int

    class Config:
        from_attributes = True


class JobMatchResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    job_id: UUID
    match_score: int
    match_reasons: list
    status: MatchStatus
    suggested_at: datetime
    confirmed_at: Optional[datetime]
    rejected_reason: Optional[str]
    notes: Optional[str]
    candidate: Optional[JobMatchCandidateInfo] = None
    job: Optional[JobMatchJobInfo] = None

    class Config:
        from_attributes = True


class JobMatchListResponse(BaseModel):
    items: list[JobMatchResponse]
    total: int
    page: int
    page_size: int


class GenerateMatchesResponse(BaseModel):
    generated: int
    message: str


class ExpressInterestRequest(BaseModel):
    interested: bool = True
