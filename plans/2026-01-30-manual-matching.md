# Manual Candidate-Job Matching Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable admins to manually assign candidates to jobs with status tracking, creating a simple matching system for Phase 1.

**Architecture:** Create a `job_matches` table linking candidates to jobs with status (assigned, confirmed, rejected, deployed). Admin can create matches from job detail page. Slot tracking automatically increments when match status changes to confirmed/deployed.

**Tech Stack:** SQLAlchemy, Alembic, FastAPI, React, TanStack Query

---

## Task 1: Create JobMatch Model

**Files:**
- Create: `hiremenow-be/app/models/job_match.py`
- Modify: `hiremenow-be/app/models/__init__.py`

**Step 1: Create JobMatch model**

```python
# hiremenow-be/app/models/job_match.py
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
from app.database import Base


class MatchStatus(str, PyEnum):
    ASSIGNED = "assigned"        # Admin assigned candidate to job
    CONFIRMED = "confirmed"      # Match confirmed, candidate will start
    REJECTED = "rejected"        # Candidate or employer rejected
    DEPLOYED = "deployed"        # Candidate started working


# PostgreSQL ENUM type
matchstatus_enum = ENUM('assigned', 'confirmed', 'rejected', 'deployed', name='matchstatus', create_type=False)


class JobMatch(Base):
    __tablename__ = "job_matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    candidate_id = Column(UUID(as_uuid=True), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)

    status = Column(matchstatus_enum, default='assigned', nullable=False)
    notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    confirmed_at = Column(DateTime, nullable=True)
    deployed_at = Column(DateTime, nullable=True)

    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    candidate = relationship("Candidate", backref="job_matches")
    job = relationship("Job", backref="matches")
    assigner = relationship("User", backref="assigned_matches")

    # Unique constraint: one candidate per job
    __table_args__ = (
        UniqueConstraint('candidate_id', 'job_id', name='uq_candidate_job'),
    )

    def __repr__(self):
        return f"<JobMatch candidate={self.candidate_id} job={self.job_id} status={self.status}>"
```

**Step 2: Update models __init__.py**

```python
# hiremenow-be/app/models/__init__.py
from app.models.user import User, UserRole
from app.models.company import Company
from app.models.employer import Employer
from app.models.candidate import Candidate, PassportStatus, LeadSource
from app.models.job import Job, WorkMode, JobType, JobStatus, SalaryPeriod
from app.models.job_match import JobMatch, MatchStatus

__all__ = [
    "User", "UserRole",
    "Company",
    "Employer",
    "Candidate", "PassportStatus", "LeadSource",
    "Job", "WorkMode", "JobType", "JobStatus", "SalaryPeriod",
    "JobMatch", "MatchStatus",
]
```

**Step 3: Commit**

```bash
git add hiremenow-be/app/models/job_match.py hiremenow-be/app/models/__init__.py
git commit -m "feat(model): add JobMatch model for candidate-job assignments"
```

---

## Task 2: Create Database Migration

**Files:**
- Create: `hiremenow-be/alembic/versions/xxxx_add_job_matches.py`

**Step 1: Generate migration**

Run:
```bash
cd hiremenow-be && alembic revision --autogenerate -m "add job_matches table"
```

**Step 2: Verify migration file**

The generated migration should include:
- Create `matchstatus` enum type
- Create `job_matches` table with all columns
- Add unique constraint on (candidate_id, job_id)
- Foreign keys to candidates, jobs, users

**Step 3: Run migration**

Run:
```bash
cd hiremenow-be && alembic upgrade head
```

Expected: Migration applied successfully

**Step 4: Commit**

```bash
git add hiremenow-be/alembic/versions/
git commit -m "feat(db): add job_matches migration"
```

---

## Task 3: Create JobMatch Schemas

**Files:**
- Create: `hiremenow-be/app/schemas/job_match.py`
- Modify: `hiremenow-be/app/schemas/__init__.py`

**Step 1: Create job_match schemas**

```python
# hiremenow-be/app/schemas/job_match.py
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.job_match import MatchStatus


class JobMatchCandidateInfo(BaseModel):
    id: UUID
    first_name: Optional[str]
    last_name: Optional[str]
    current_stage: str
    user_email: str

    class Config:
        from_attributes = True


class JobMatchJobInfo(BaseModel):
    id: UUID
    title: str
    company_name: str
    country: str
    city: Optional[str]

    class Config:
        from_attributes = True


class JobMatchCreate(BaseModel):
    candidate_id: UUID
    job_id: UUID
    notes: Optional[str] = Field(None, max_length=1000)


class JobMatchUpdateStatus(BaseModel):
    status: MatchStatus
    notes: Optional[str] = Field(None, max_length=1000)
    rejection_reason: Optional[str] = Field(None, max_length=500)


class JobMatchResponse(BaseModel):
    id: UUID
    candidate_id: UUID
    job_id: UUID
    status: MatchStatus
    notes: Optional[str]
    rejection_reason: Optional[str]
    assigned_at: datetime
    confirmed_at: Optional[datetime]
    deployed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobMatchDetailResponse(JobMatchResponse):
    candidate: JobMatchCandidateInfo
    job: JobMatchJobInfo


class JobMatchListResponse(BaseModel):
    items: list[JobMatchDetailResponse]
    total: int
    page: int
    page_size: int
```

**Step 2: Update schemas __init__.py**

Add to `hiremenow-be/app/schemas/__init__.py`:

```python
from app.schemas.job_match import (
    JobMatchCreate,
    JobMatchUpdateStatus,
    JobMatchResponse,
    JobMatchDetailResponse,
    JobMatchListResponse,
)
```

**Step 3: Commit**

```bash
git add hiremenow-be/app/schemas/job_match.py hiremenow-be/app/schemas/__init__.py
git commit -m "feat(schemas): add JobMatch Pydantic schemas"
```

---

## Task 4: Create JobMatch API Endpoints

**Files:**
- Create: `hiremenow-be/app/api/v1/admin/matches.py`
- Modify: `hiremenow-be/app/api/v1/router.py`

**Step 1: Create matches endpoints**

```python
# hiremenow-be/app/api/v1/admin/matches.py
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.api.deps import get_admin_user
from app.models.user import User
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.job_match import JobMatch, MatchStatus
from app.schemas.job_match import (
    JobMatchCreate,
    JobMatchUpdateStatus,
    JobMatchDetailResponse,
    JobMatchListResponse,
    JobMatchCandidateInfo,
    JobMatchJobInfo,
)

router = APIRouter(prefix="/matches", tags=["admin-matches"])


def build_match_detail(match: JobMatch) -> JobMatchDetailResponse:
    """Build detailed match response with nested info."""
    return JobMatchDetailResponse(
        id=match.id,
        candidate_id=match.candidate_id,
        job_id=match.job_id,
        status=match.status,
        notes=match.notes,
        rejection_reason=match.rejection_reason,
        assigned_at=match.assigned_at,
        confirmed_at=match.confirmed_at,
        deployed_at=match.deployed_at,
        created_at=match.created_at,
        updated_at=match.updated_at,
        candidate=JobMatchCandidateInfo(
            id=match.candidate.id,
            first_name=match.candidate.first_name,
            last_name=match.candidate.last_name,
            current_stage=match.candidate.current_stage,
            user_email=match.candidate.user.email,
        ),
        job=JobMatchJobInfo(
            id=match.job.id,
            title=match.job.title,
            company_name=match.job.company.name,
            country=match.job.country,
            city=match.job.city,
        ),
    )


@router.get("", response_model=JobMatchListResponse)
def list_matches(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    job_id: UUID = Query(None),
    candidate_id: UUID = Query(None),
    status_filter: MatchStatus = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """List all job matches with filters."""
    query = db.query(JobMatch).options(
        joinedload(JobMatch.candidate).joinedload(Candidate.user),
        joinedload(JobMatch.job).joinedload(Job.company),
    )

    if job_id:
        query = query.filter(JobMatch.job_id == job_id)
    if candidate_id:
        query = query.filter(JobMatch.candidate_id == candidate_id)
    if status_filter:
        query = query.filter(JobMatch.status == status_filter)

    total = query.count()
    items = query.order_by(JobMatch.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return JobMatchListResponse(
        items=[build_match_detail(m) for m in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=JobMatchDetailResponse, status_code=status.HTTP_201_CREATED)
def create_match(
    data: JobMatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Assign a candidate to a job."""
    # Verify candidate exists
    candidate = db.query(Candidate).options(
        joinedload(Candidate.user)
    ).filter(Candidate.id == data.candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    # Verify job exists and is active
    job = db.query(Job).options(
        joinedload(Job.company)
    ).filter(Job.id == data.job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    if job.status != 'active':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job is not active",
        )

    # Check if job has available slots
    if job.available_slots <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job has no available slots",
        )

    # Check if match already exists
    existing = db.query(JobMatch).filter(
        JobMatch.candidate_id == data.candidate_id,
        JobMatch.job_id == data.job_id,
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Candidate is already assigned to this job",
        )

    match = JobMatch(
        candidate_id=data.candidate_id,
        job_id=data.job_id,
        notes=data.notes,
        assigned_by=current_user.id,
    )
    db.add(match)
    db.commit()

    # Reload with relationships
    match = db.query(JobMatch).options(
        joinedload(JobMatch.candidate).joinedload(Candidate.user),
        joinedload(JobMatch.job).joinedload(Job.company),
    ).filter(JobMatch.id == match.id).first()

    return build_match_detail(match)


@router.get("/{match_id}", response_model=JobMatchDetailResponse)
def get_match(
    match_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Get a match by ID."""
    match = db.query(JobMatch).options(
        joinedload(JobMatch.candidate).joinedload(Candidate.user),
        joinedload(JobMatch.job).joinedload(Job.company),
    ).filter(JobMatch.id == match_id).first()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    return build_match_detail(match)


@router.patch("/{match_id}", response_model=JobMatchDetailResponse)
def update_match_status(
    match_id: UUID,
    data: JobMatchUpdateStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Update a match's status."""
    match = db.query(JobMatch).options(
        joinedload(JobMatch.candidate).joinedload(Candidate.user),
        joinedload(JobMatch.job).joinedload(Job.company),
    ).filter(JobMatch.id == match_id).first()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    old_status = match.status
    new_status = data.status

    # Validate status transitions
    valid_transitions = {
        MatchStatus.ASSIGNED: [MatchStatus.CONFIRMED, MatchStatus.REJECTED],
        MatchStatus.CONFIRMED: [MatchStatus.DEPLOYED, MatchStatus.REJECTED],
        MatchStatus.REJECTED: [],  # Terminal state
        MatchStatus.DEPLOYED: [],  # Terminal state
    }

    if new_status not in valid_transitions.get(old_status, []):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from {old_status.value} to {new_status.value}",
        )

    # Update filled_slots on job when confirming or deploying
    job = match.job
    if new_status == MatchStatus.CONFIRMED and old_status == MatchStatus.ASSIGNED:
        match.confirmed_at = datetime.utcnow()
        job.filled_slots += 1
        # Auto-close job if filled
        if job.filled_slots >= job.total_slots:
            job.status = 'closed'

    if new_status == MatchStatus.DEPLOYED:
        match.deployed_at = datetime.utcnow()

    # Handle rejection
    if new_status == MatchStatus.REJECTED:
        match.rejection_reason = data.rejection_reason
        # If was confirmed, decrement filled_slots
        if old_status == MatchStatus.CONFIRMED:
            job.filled_slots = max(0, job.filled_slots - 1)

    match.status = new_status
    if data.notes:
        match.notes = data.notes

    db.commit()
    db.refresh(match)

    return build_match_detail(match)


@router.delete("/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_match(
    match_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Delete a match (only if assigned, not confirmed/deployed)."""
    match = db.query(JobMatch).filter(JobMatch.id == match_id).first()

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found",
        )

    if match.status not in [MatchStatus.ASSIGNED, MatchStatus.REJECTED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete confirmed or deployed matches",
        )

    db.delete(match)
    db.commit()
```

**Step 2: Register matches router**

Update `hiremenow-be/app/api/v1/router.py`:

```python
# hiremenow-be/app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.public import router as public_router
from app.api.v1.admin.companies import router as admin_companies_router
from app.api.v1.admin.employers import router as admin_employers_router
from app.api.v1.admin.candidates import router as admin_candidates_router
from app.api.v1.admin.jobs import router as admin_jobs_router
from app.api.v1.admin.stats import router as admin_stats_router
from app.api.v1.admin.uploads import router as admin_uploads_router
from app.api.v1.admin.matches import router as admin_matches_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(public_router)
api_router.include_router(admin_companies_router, prefix="/admin")
api_router.include_router(admin_employers_router, prefix="/admin")
api_router.include_router(admin_candidates_router, prefix="/admin")
api_router.include_router(admin_jobs_router, prefix="/admin")
api_router.include_router(admin_stats_router, prefix="/admin")
api_router.include_router(admin_uploads_router, prefix="/admin")
api_router.include_router(admin_matches_router, prefix="/admin")
```

**Step 3: Commit**

```bash
git add hiremenow-be/app/api/v1/admin/matches.py hiremenow-be/app/api/v1/router.py
git commit -m "feat(api): add job match CRUD endpoints"
```

---

## Task 5: Create Frontend Types and API

**Files:**
- Modify: `hiremenow-fe/src/types/index.ts`
- Create: `hiremenow-fe/src/lib/api/matches.ts`

**Step 1: Add match types**

Add to `hiremenow-fe/src/types/index.ts`:

```typescript
export type MatchStatus = 'assigned' | 'confirmed' | 'rejected' | 'deployed';

export interface JobMatchCandidateInfo {
  id: string;
  first_name: string | null;
  last_name: string | null;
  current_stage: string;
  user_email: string;
}

export interface JobMatchJobInfo {
  id: string;
  title: string;
  company_name: string;
  country: string;
  city: string | null;
}

export interface JobMatch {
  id: string;
  candidate_id: string;
  job_id: string;
  status: MatchStatus;
  notes: string | null;
  rejection_reason: string | null;
  assigned_at: string;
  confirmed_at: string | null;
  deployed_at: string | null;
  created_at: string;
  updated_at: string;
  candidate: JobMatchCandidateInfo;
  job: JobMatchJobInfo;
}

export interface JobMatchCreate {
  candidate_id: string;
  job_id: string;
  notes?: string;
}

export interface JobMatchUpdateStatus {
  status: MatchStatus;
  notes?: string;
  rejection_reason?: string;
}
```

**Step 2: Create matches API module**

```typescript
// hiremenow-fe/src/lib/api/matches.ts
import api from '../api';
import type { JobMatch, JobMatchCreate, JobMatchUpdateStatus, PaginatedResponse, MatchStatus } from '@/types';

export interface MatchFilters {
  page?: number;
  page_size?: number;
  job_id?: string;
  candidate_id?: string;
  status?: MatchStatus;
}

export const matchesApi = {
  list: async (filters: MatchFilters = {}): Promise<PaginatedResponse<JobMatch>> => {
    const params = new URLSearchParams();
    if (filters.page) params.set('page', String(filters.page));
    if (filters.page_size) params.set('page_size', String(filters.page_size));
    if (filters.job_id) params.set('job_id', filters.job_id);
    if (filters.candidate_id) params.set('candidate_id', filters.candidate_id);
    if (filters.status) params.set('status', filters.status);

    const response = await api.get(`/admin/matches?${params}`);
    return response.data;
  },

  get: async (id: string): Promise<JobMatch> => {
    const response = await api.get(`/admin/matches/${id}`);
    return response.data;
  },

  create: async (data: JobMatchCreate): Promise<JobMatch> => {
    const response = await api.post('/admin/matches', data);
    return response.data;
  },

  updateStatus: async (id: string, data: JobMatchUpdateStatus): Promise<JobMatch> => {
    const response = await api.patch(`/admin/matches/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/admin/matches/${id}`);
  },
};

export const MATCH_STATUS_LABELS: Record<MatchStatus, string> = {
  assigned: 'Assigned',
  confirmed: 'Confirmed',
  rejected: 'Rejected',
  deployed: 'Deployed',
};

export const MATCH_STATUS_COLORS: Record<MatchStatus, string> = {
  assigned: 'bg-blue-100 text-blue-800',
  confirmed: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
  deployed: 'bg-emerald-100 text-emerald-800',
};
```

**Step 3: Commit**

```bash
git add hiremenow-fe/src/types/index.ts hiremenow-fe/src/lib/api/matches.ts
git commit -m "feat(frontend): add job match types and API module"
```

---

## Task 6: Create Match Hooks

**Files:**
- Create: `hiremenow-fe/src/hooks/use-matches.ts`

**Step 1: Create match hooks**

```typescript
// hiremenow-fe/src/hooks/use-matches.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { matchesApi, type MatchFilters } from '@/lib/api/matches';
import type { JobMatchCreate, JobMatchUpdateStatus } from '@/types';
import { jobKeys } from './use-jobs';

export const matchKeys = {
  all: ['matches'] as const,
  lists: () => [...matchKeys.all, 'list'] as const,
  list: (filters: MatchFilters) => [...matchKeys.lists(), filters] as const,
  details: () => [...matchKeys.all, 'detail'] as const,
  detail: (id: string) => [...matchKeys.details(), id] as const,
};

export function useMatches(filters: MatchFilters = {}) {
  return useQuery({
    queryKey: matchKeys.list(filters),
    queryFn: () => matchesApi.list(filters),
  });
}

export function useMatch(id: string) {
  return useQuery({
    queryKey: matchKeys.detail(id),
    queryFn: () => matchesApi.get(id),
    enabled: !!id,
  });
}

export function useCreateMatch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: JobMatchCreate) => matchesApi.create(data),
    onSuccess: (_, data) => {
      queryClient.invalidateQueries({ queryKey: matchKeys.lists() });
      queryClient.invalidateQueries({ queryKey: jobKeys.detail(data.job_id) });
    },
  });
}

export function useUpdateMatchStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: JobMatchUpdateStatus }) =>
      matchesApi.updateStatus(id, data),
    onSuccess: (match) => {
      queryClient.invalidateQueries({ queryKey: matchKeys.lists() });
      queryClient.invalidateQueries({ queryKey: matchKeys.detail(match.id) });
      queryClient.invalidateQueries({ queryKey: jobKeys.detail(match.job_id) });
    },
  });
}

export function useDeleteMatch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => matchesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: matchKeys.lists() });
      queryClient.invalidateQueries({ queryKey: jobKeys.lists() });
    },
  });
}
```

**Step 2: Commit**

```bash
git add hiremenow-fe/src/hooks/use-matches.ts
git commit -m "feat(frontend): add job match React Query hooks"
```

---

## Task 7: Create AssignCandidateDialog Component

**Files:**
- Create: `hiremenow-fe/src/components/admin/jobs/AssignCandidateDialog.tsx`

**Step 1: Create the dialog component**

```typescript
// hiremenow-fe/src/components/admin/jobs/AssignCandidateDialog.tsx
import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Loader2, Search, UserPlus } from 'lucide-react';
import { useCandidates } from '@/hooks/use-candidates';
import { useCreateMatch } from '@/hooks/use-matches';
import type { Candidate, Job } from '@/types';

interface Props {
  job: Job;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AssignCandidateDialog({ job, open, onOpenChange }: Props) {
  const [search, setSearch] = useState('');
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [notes, setNotes] = useState('');

  const { data: candidatesData, isLoading: loadingCandidates } = useCandidates({
    search: search || undefined,
    page_size: 10,
  });

  const createMatch = useCreateMatch();

  const handleAssign = async () => {
    if (!selectedCandidate) return;

    try {
      await createMatch.mutateAsync({
        candidate_id: selectedCandidate.id,
        job_id: job.id,
        notes: notes || undefined,
      });
      onOpenChange(false);
      setSelectedCandidate(null);
      setNotes('');
      setSearch('');
    } catch (error) {
      // Error handled by mutation
    }
  };

  const candidates = candidatesData?.items || [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Assign Candidate to Job</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="p-3 bg-slate-50 rounded-lg">
            <p className="text-sm text-slate-600">Job:</p>
            <p className="font-medium">{job.title}</p>
            <p className="text-sm text-slate-500">
              {job.company?.name} - {job.country}
              {job.available_slots > 0 ? (
                <span className="ml-2 text-green-600">
                  ({job.available_slots} slots available)
                </span>
              ) : (
                <span className="ml-2 text-red-600">(No slots available)</span>
              )}
            </p>
          </div>

          {!selectedCandidate ? (
            <>
              <div>
                <Label>Search Candidates</Label>
                <div className="relative mt-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <Input
                    placeholder="Search by name or email..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>

              <div className="max-h-60 overflow-y-auto border rounded-lg divide-y">
                {loadingCandidates ? (
                  <div className="p-4 text-center text-slate-500">
                    <Loader2 className="h-5 w-5 animate-spin mx-auto" />
                  </div>
                ) : candidates.length === 0 ? (
                  <div className="p-4 text-center text-slate-500">
                    No candidates found
                  </div>
                ) : (
                  candidates.map((candidate) => (
                    <button
                      key={candidate.id}
                      onClick={() => setSelectedCandidate(candidate)}
                      className="w-full p-3 text-left hover:bg-slate-50 transition-colors"
                    >
                      <p className="font-medium">
                        {candidate.first_name} {candidate.last_name}
                      </p>
                      <p className="text-sm text-slate-500">{candidate.user?.email}</p>
                      <p className="text-xs text-slate-400">
                        Stage: {candidate.current_stage}
                      </p>
                    </button>
                  ))
                )}
              </div>
            </>
          ) : (
            <>
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-emerald-600">Selected Candidate:</p>
                    <p className="font-medium">
                      {selectedCandidate.first_name} {selectedCandidate.last_name}
                    </p>
                    <p className="text-sm text-slate-500">
                      {selectedCandidate.user?.email}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedCandidate(null)}
                  >
                    Change
                  </Button>
                </div>
              </div>

              <div>
                <Label>Notes (optional)</Label>
                <Textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Add any notes about this assignment..."
                  rows={3}
                />
              </div>

              <div className="flex gap-3 justify-end">
                <Button variant="outline" onClick={() => onOpenChange(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={handleAssign}
                  disabled={createMatch.isPending || job.available_slots <= 0}
                >
                  {createMatch.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Assigning...
                    </>
                  ) : (
                    <>
                      <UserPlus className="h-4 w-4 mr-2" />
                      Assign Candidate
                    </>
                  )}
                </Button>
              </div>
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

**Step 2: Commit**

```bash
git add hiremenow-fe/src/components/admin/jobs/AssignCandidateDialog.tsx
git commit -m "feat(ui): add AssignCandidateDialog component"
```

---

## Task 8: Create JobMatchesTable Component

**Files:**
- Create: `hiremenow-fe/src/components/admin/jobs/JobMatchesTable.tsx`

**Step 1: Create the matches table component**

```typescript
// hiremenow-fe/src/components/admin/jobs/JobMatchesTable.tsx
import { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Loader2, Check, X, Rocket, Trash2 } from 'lucide-react';
import { useMatches, useUpdateMatchStatus, useDeleteMatch } from '@/hooks/use-matches';
import { MATCH_STATUS_LABELS, MATCH_STATUS_COLORS } from '@/lib/api/matches';
import type { MatchStatus } from '@/types';
import { DeleteDialog } from '@/components/admin/DeleteDialog';

interface Props {
  jobId: string;
}

export function JobMatchesTable({ jobId }: Props) {
  const [deleteMatchId, setDeleteMatchId] = useState<string | null>(null);

  const { data, isLoading } = useMatches({ job_id: jobId });
  const updateStatus = useUpdateMatchStatus();
  const deleteMatch = useDeleteMatch();

  const matches = data?.items || [];

  const handleStatusChange = async (matchId: string, newStatus: MatchStatus) => {
    await updateStatus.mutateAsync({
      id: matchId,
      data: { status: newStatus },
    });
  };

  const handleDelete = async () => {
    if (deleteMatchId) {
      await deleteMatch.mutateAsync(deleteMatchId);
      setDeleteMatchId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
      </div>
    );
  }

  if (matches.length === 0) {
    return (
      <div className="text-center py-8 text-slate-500">
        No candidates assigned to this job yet.
      </div>
    );
  }

  return (
    <>
      <div className="border rounded-lg divide-y">
        {matches.map((match) => (
          <div
            key={match.id}
            className="p-4 flex items-center justify-between gap-4"
          >
            <div className="flex-1 min-w-0">
              <p className="font-medium truncate">
                {match.candidate.first_name} {match.candidate.last_name}
              </p>
              <p className="text-sm text-slate-500 truncate">
                {match.candidate.user_email}
              </p>
              {match.notes && (
                <p className="text-sm text-slate-400 mt-1">{match.notes}</p>
              )}
            </div>

            <div className="flex items-center gap-3">
              <Badge className={MATCH_STATUS_COLORS[match.status]}>
                {MATCH_STATUS_LABELS[match.status]}
              </Badge>

              {match.status === 'assigned' && (
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleStatusChange(match.id, 'confirmed')}
                    disabled={updateStatus.isPending}
                  >
                    <Check className="h-4 w-4 mr-1" />
                    Confirm
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleStatusChange(match.id, 'rejected')}
                    disabled={updateStatus.isPending}
                  >
                    <X className="h-4 w-4 mr-1" />
                    Reject
                  </Button>
                </div>
              )}

              {match.status === 'confirmed' && (
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleStatusChange(match.id, 'deployed')}
                    disabled={updateStatus.isPending}
                  >
                    <Rocket className="h-4 w-4 mr-1" />
                    Deploy
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleStatusChange(match.id, 'rejected')}
                    disabled={updateStatus.isPending}
                  >
                    <X className="h-4 w-4 mr-1" />
                    Reject
                  </Button>
                </div>
              )}

              {(match.status === 'assigned' || match.status === 'rejected') && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setDeleteMatchId(match.id)}
                >
                  <Trash2 className="h-4 w-4 text-red-500" />
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>

      <DeleteDialog
        open={!!deleteMatchId}
        onOpenChange={() => setDeleteMatchId(null)}
        onConfirm={handleDelete}
        title="Remove Assignment"
        description="Are you sure you want to remove this candidate assignment? This action cannot be undone."
        isDeleting={deleteMatch.isPending}
      />
    </>
  );
}
```

**Step 2: Commit**

```bash
git add hiremenow-fe/src/components/admin/jobs/JobMatchesTable.tsx
git commit -m "feat(ui): add JobMatchesTable component"
```

---

## Task 9: Add Matches Section to Job Detail

**Files:**
- Modify: `hiremenow-fe/src/components/admin/jobs/columns.tsx` or create job detail dialog

**Step 1: Create JobDetailDialog with matches section**

Create a job detail dialog that shows job info and assigned candidates, with button to assign new candidates.

The implementation should:
1. Show job details (title, company, status, slots info)
2. Show JobMatchesTable component
3. Show "Assign Candidate" button that opens AssignCandidateDialog
4. Add this dialog to the jobs table actions

**Step 2: Commit**

```bash
git add hiremenow-fe/src/components/admin/jobs/
git commit -m "feat(ui): add job detail dialog with matches management"
```

---

## Task 10: Verify and Test

**Step 1: Build frontend**

Run:
```bash
cd hiremenow-fe && npm run build
```

Expected: Build succeeds

**Step 2: Test backend imports**

Run:
```bash
cd hiremenow-be && python3 -c "from app.models.job_match import JobMatch; from app.api.v1.admin.matches import router; print('OK')"
```

Expected: OK

**Step 3: Final commit**

```bash
git add . && git commit -m "feat: complete manual candidate-job matching"
```

---

## Summary

This plan implements:
1. **JobMatch model** - Links candidates to jobs with status tracking
2. **Database migration** - Creates job_matches table
3. **Pydantic schemas** - Request/response models for matches
4. **Match API endpoints** - CRUD operations with status transitions
5. **Frontend types/API** - TypeScript types and API module
6. **Match hooks** - React Query mutations and queries
7. **AssignCandidateDialog** - Search and select candidates to assign
8. **JobMatchesTable** - Display assigned candidates with status actions
9. **Job detail integration** - View and manage matches from job page

Key features:
- Unique constraint prevents duplicate assignments
- Status transitions: assigned → confirmed → deployed
- Slot tracking updates automatically on confirm/reject
- Jobs auto-close when filled
