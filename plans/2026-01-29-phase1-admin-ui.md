# Phase 1: Admin UI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the admin panel UI with dashboard stats, CRUD pages for companies/employers/candidates/jobs, and a public lead capture form.

**Architecture:** React frontend using TanStack Query for data fetching, TanStack Table for data grids, shadcn/ui for components, and React Hook Form for forms. Pages follow a consistent pattern: list view with search/filter, create/edit modals or pages, and detail views where needed.

**Tech Stack:** React 19, TypeScript, TanStack Query, TanStack Table, React Hook Form, shadcn/ui, Tailwind CSS, Zod validation

---

## Task 1: Install shadcn/ui Base Components

**Files:**
- Create: `hiremenow-fe/src/components/ui/button.tsx`
- Create: `hiremenow-fe/src/components/ui/input.tsx`
- Create: `hiremenow-fe/src/components/ui/label.tsx`
- Create: `hiremenow-fe/src/components/ui/card.tsx`
- Create: `hiremenow-fe/src/components/ui/table.tsx`
- Create: `hiremenow-fe/src/components/ui/dialog.tsx`
- Create: `hiremenow-fe/src/components/ui/select.tsx`
- Create: `hiremenow-fe/src/components/ui/badge.tsx`
- Create: `hiremenow-fe/src/components/ui/textarea.tsx`

**Step 1: Install shadcn/ui components**

Run:
```bash
cd hiremenow-fe && npx shadcn@latest add button input label card table dialog select badge textarea -y
```

Expected: Components created in `src/components/ui/`

**Step 2: Install additional dependencies**

Run:
```bash
cd hiremenow-fe && npm install react-hook-form @hookform/resolvers zod
```

Expected: Packages added to package.json

**Step 3: Verify installation**

Run:
```bash
cd hiremenow-fe && npm run build
```

Expected: Build succeeds without errors

**Step 4: Commit**

```bash
cd hiremenow-fe && git add . && git commit -m "feat(ui): add shadcn/ui base components and form dependencies"
```

---

## Task 2: Create API Service Layer

**Files:**
- Create: `hiremenow-fe/src/lib/api/companies.ts`
- Create: `hiremenow-fe/src/lib/api/employers.ts`
- Create: `hiremenow-fe/src/lib/api/candidates.ts`
- Create: `hiremenow-fe/src/lib/api/jobs.ts`
- Create: `hiremenow-fe/src/lib/api/stats.ts`
- Create: `hiremenow-fe/src/types/index.ts`

**Step 1: Create TypeScript types**

```typescript
// hiremenow-fe/src/types/index.ts
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface Company {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  logo_url: string | null;
  website: string | null;
  location: string | null;
  industry: string | null;
  is_agency_owned: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CompanyCreate {
  name: string;
  description?: string;
  logo_url?: string;
  website?: string;
  location?: string;
  industry?: string;
  is_agency_owned?: boolean;
}

export interface Employer {
  id: string;
  user_id: string;
  company_id: string;
  created_at: string;
  user: {
    id: string;
    email: string;
    is_active: boolean;
  };
  company: {
    id: string;
    name: string;
    slug: string;
  };
}

export interface EmployerCreate {
  email: string;
  password: string;
  company_id: string;
}

export type PassportStatus = 'valid' | 'expired' | 'none' | 'in_progress';
export type LeadSource = 'website' | 'facebook' | 'instagram' | 'referral' | 'other';

export interface Candidate {
  id: string;
  user_id: string;
  first_name: string | null;
  last_name: string | null;
  phone: string | null;
  date_of_birth: string | null;
  nationality: string | null;
  current_country: string | null;
  passport_status: PassportStatus;
  passport_expiry: string | null;
  preferred_positions: string[];
  experience_years: number;
  photo_url: string | null;
  resume_url: string | null;
  source: LeadSource;
  referral_code: string | null;
  current_stage: string;
  stage_notes: string | null;
  stage_updated_at: string;
  created_at: string;
  updated_at: string;
  user: {
    id: string;
    email: string;
    is_active: boolean;
  };
}

export interface CandidateCreate {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  source?: LeadSource;
}

export type WorkMode = 'onsite' | 'accommodation_provided';
export type JobType = 'full_time' | 'part_time' | 'contract' | 'seasonal';
export type JobStatus = 'draft' | 'pending_approval' | 'active' | 'paused' | 'closed' | 'rejected';
export type SalaryPeriod = 'hourly' | 'monthly';

export interface Job {
  id: string;
  company_id: string;
  created_by: string | null;
  title: string;
  slug: string;
  description: string;
  category: string | null;
  country: string;
  city: string | null;
  work_mode: WorkMode;
  job_type: JobType;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string;
  salary_period: SalaryPeriod;
  benefits: string[];
  requirements: Record<string, unknown>;
  total_slots: number;
  filled_slots: number;
  available_slots: number;
  status: JobStatus;
  rejection_reason: string | null;
  deadline: string | null;
  start_date: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
  company: {
    id: string;
    name: string;
    slug: string;
  };
  creator: {
    id: string;
    email: string;
  } | null;
}

export interface JobCreate {
  title: string;
  description: string;
  company_id: string;
  country: string;
  city?: string;
  category?: string;
  work_mode?: WorkMode;
  job_type?: JobType;
  salary_min?: number;
  salary_max?: number;
  salary_currency?: string;
  salary_period?: SalaryPeriod;
  benefits?: string[];
  total_slots?: number;
  deadline?: string;
  start_date?: string;
}

export interface DashboardStats {
  total_companies: number;
  total_employers: number;
  total_candidates: number;
  total_jobs: number;
  active_jobs: number;
  candidates_by_stage: Record<string, number>;
}
```

**Step 2: Create companies API**

```typescript
// hiremenow-fe/src/lib/api/companies.ts
import api from '../api';
import type { Company, CompanyCreate, PaginatedResponse } from '@/types';

export interface CompanyFilters {
  page?: number;
  page_size?: number;
  is_active?: boolean;
  search?: string;
}

export const companiesApi = {
  list: async (filters: CompanyFilters = {}): Promise<PaginatedResponse<Company>> => {
    const params = new URLSearchParams();
    if (filters.page) params.set('page', String(filters.page));
    if (filters.page_size) params.set('page_size', String(filters.page_size));
    if (filters.is_active !== undefined) params.set('is_active', String(filters.is_active));
    if (filters.search) params.set('search', filters.search);

    const response = await api.get(`/admin/companies?${params}`);
    return response.data;
  },

  get: async (id: string): Promise<Company> => {
    const response = await api.get(`/admin/companies/${id}`);
    return response.data;
  },

  create: async (data: CompanyCreate): Promise<Company> => {
    const response = await api.post('/admin/companies', data);
    return response.data;
  },

  update: async (id: string, data: Partial<CompanyCreate>): Promise<Company> => {
    const response = await api.patch(`/admin/companies/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/admin/companies/${id}`);
  },
};
```

**Step 3: Create employers API**

```typescript
// hiremenow-fe/src/lib/api/employers.ts
import api from '../api';
import type { Employer, EmployerCreate, PaginatedResponse } from '@/types';

export interface EmployerFilters {
  page?: number;
  page_size?: number;
  company_id?: string;
}

export const employersApi = {
  list: async (filters: EmployerFilters = {}): Promise<PaginatedResponse<Employer>> => {
    const params = new URLSearchParams();
    if (filters.page) params.set('page', String(filters.page));
    if (filters.page_size) params.set('page_size', String(filters.page_size));
    if (filters.company_id) params.set('company_id', filters.company_id);

    const response = await api.get(`/admin/employers?${params}`);
    return response.data;
  },

  get: async (id: string): Promise<Employer> => {
    const response = await api.get(`/admin/employers/${id}`);
    return response.data;
  },

  create: async (data: EmployerCreate): Promise<Employer> => {
    const response = await api.post('/admin/employers', data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/admin/employers/${id}`);
  },
};
```

**Step 4: Create candidates API**

```typescript
// hiremenow-fe/src/lib/api/candidates.ts
import api from '../api';
import type { Candidate, CandidateCreate, PaginatedResponse, PassportStatus, LeadSource } from '@/types';

export interface CandidateFilters {
  page?: number;
  page_size?: number;
  current_stage?: string;
  passport_status?: PassportStatus;
  source?: LeadSource;
  nationality?: string;
  search?: string;
}

export const candidatesApi = {
  list: async (filters: CandidateFilters = {}): Promise<PaginatedResponse<Candidate>> => {
    const params = new URLSearchParams();
    if (filters.page) params.set('page', String(filters.page));
    if (filters.page_size) params.set('page_size', String(filters.page_size));
    if (filters.current_stage) params.set('current_stage', filters.current_stage);
    if (filters.passport_status) params.set('passport_status', filters.passport_status);
    if (filters.source) params.set('source', filters.source);
    if (filters.nationality) params.set('nationality', filters.nationality);
    if (filters.search) params.set('search', filters.search);

    const response = await api.get(`/admin/candidates?${params}`);
    return response.data;
  },

  get: async (id: string): Promise<Candidate> => {
    const response = await api.get(`/admin/candidates/${id}`);
    return response.data;
  },

  create: async (data: CandidateCreate): Promise<Candidate> => {
    const response = await api.post('/admin/candidates', data);
    return response.data;
  },

  update: async (id: string, data: Partial<Candidate>): Promise<Candidate> => {
    const response = await api.patch(`/admin/candidates/${id}`, data);
    return response.data;
  },

  updateStage: async (id: string, stage: string, notes?: string): Promise<Candidate> => {
    const params = new URLSearchParams({ stage });
    if (notes) params.set('notes', notes);
    const response = await api.patch(`/admin/candidates/${id}/stage?${params}`);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/admin/candidates/${id}`);
  },
};

export const PIPELINE_STAGES = [
  'lead',
  'pre_screening',
  'assessment',
  'job_matching',
  'pre_agreement',
  'language_course',
  'legal_paperwork',
  'departure_prep',
  'transport',
  'deployed',
  'after_sales',
] as const;

export const STAGE_LABELS: Record<string, string> = {
  lead: 'Lead',
  pre_screening: 'Pre-Screening',
  assessment: 'Assessment',
  job_matching: 'Job Matching',
  pre_agreement: 'Pre-Agreement',
  language_course: 'Language Course',
  legal_paperwork: 'Legal Paperwork',
  departure_prep: 'Departure Prep',
  transport: 'Transport',
  deployed: 'Deployed',
  after_sales: 'After Sales',
};
```

**Step 5: Create jobs API**

```typescript
// hiremenow-fe/src/lib/api/jobs.ts
import api from '../api';
import type { Job, JobCreate, JobStatus, PaginatedResponse } from '@/types';

export interface JobFilters {
  page?: number;
  page_size?: number;
  company_id?: string;
  status?: JobStatus;
  country?: string;
  search?: string;
}

export const jobsApi = {
  list: async (filters: JobFilters = {}): Promise<PaginatedResponse<Job>> => {
    const params = new URLSearchParams();
    if (filters.page) params.set('page', String(filters.page));
    if (filters.page_size) params.set('page_size', String(filters.page_size));
    if (filters.company_id) params.set('company_id', filters.company_id);
    if (filters.status) params.set('status', filters.status);
    if (filters.country) params.set('country', filters.country);
    if (filters.search) params.set('search', filters.search);

    const response = await api.get(`/admin/jobs?${params}`);
    return response.data;
  },

  get: async (id: string): Promise<Job> => {
    const response = await api.get(`/admin/jobs/${id}`);
    return response.data;
  },

  create: async (data: JobCreate): Promise<Job> => {
    const response = await api.post('/admin/jobs', data);
    return response.data;
  },

  update: async (id: string, data: Partial<JobCreate & { status?: JobStatus }>): Promise<Job> => {
    const response = await api.patch(`/admin/jobs/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/admin/jobs/${id}`);
  },
};

export const JOB_STATUS_LABELS: Record<JobStatus, string> = {
  draft: 'Draft',
  pending_approval: 'Pending Approval',
  active: 'Active',
  paused: 'Paused',
  closed: 'Closed',
  rejected: 'Rejected',
};

export const JOB_STATUS_COLORS: Record<JobStatus, string> = {
  draft: 'bg-gray-100 text-gray-800',
  pending_approval: 'bg-yellow-100 text-yellow-800',
  active: 'bg-green-100 text-green-800',
  paused: 'bg-orange-100 text-orange-800',
  closed: 'bg-red-100 text-red-800',
  rejected: 'bg-red-100 text-red-800',
};
```

**Step 6: Create stats API**

```typescript
// hiremenow-fe/src/lib/api/stats.ts
import api from '../api';
import type { DashboardStats } from '@/types';

export const statsApi = {
  getDashboard: async (): Promise<DashboardStats> => {
    const response = await api.get('/admin/stats');
    return response.data;
  },
};
```

**Step 7: Verify build**

Run:
```bash
cd hiremenow-fe && npm run build
```

Expected: Build succeeds

**Step 8: Commit**

```bash
cd hiremenow-fe && git add . && git commit -m "feat(api): add API service layer for all admin endpoints"
```

---

## Task 3: Add Dashboard Stats Backend Endpoint

**Files:**
- Create: `hiremenow-be/app/api/v1/admin/stats.py`
- Modify: `hiremenow-be/app/api/v1/router.py`

**Step 1: Create stats endpoint**

```python
# hiremenow-be/app/api/v1/admin/stats.py
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
    total_companies = db.query(func.count(Company.id)).scalar()
    total_employers = db.query(func.count(Employer.id)).scalar()
    total_candidates = db.query(func.count(Candidate.id)).scalar()
    total_jobs = db.query(func.count(Job.id)).scalar()
    active_jobs = db.query(func.count(Job.id)).filter(Job.status == 'active').scalar()

    # Candidates by stage
    stage_counts = db.query(
        Candidate.current_stage,
        func.count(Candidate.id)
    ).group_by(Candidate.current_stage).all()

    candidates_by_stage = {stage: count for stage, count in stage_counts}

    return {
        "total_companies": total_companies,
        "total_employers": total_employers,
        "total_candidates": total_candidates,
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "candidates_by_stage": candidates_by_stage,
    }
```

**Step 2: Register stats router**

Add to `hiremenow-be/app/api/v1/router.py`:

```python
from app.api.v1.admin.stats import router as admin_stats_router

# Add after other admin routers:
api_router.include_router(admin_stats_router, prefix="/admin")
```

**Step 3: Test endpoint**

Run:
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@hiremenow.com", "password": "admin123"}' | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

curl -s http://localhost:8000/api/v1/admin/stats \
  -H "Authorization: Bearer $TOKEN"
```

Expected: JSON response with stats

**Step 4: Commit**

```bash
cd hiremenow-be && git add . && git commit -m "feat(api): add dashboard stats endpoint"
```

---

## Task 4: Create React Query Hooks

**Files:**
- Create: `hiremenow-fe/src/hooks/useCompanies.ts`
- Create: `hiremenow-fe/src/hooks/useEmployers.ts`
- Create: `hiremenow-fe/src/hooks/useCandidates.ts`
- Create: `hiremenow-fe/src/hooks/useJobs.ts`
- Create: `hiremenow-fe/src/hooks/useStats.ts`

**Step 1: Create companies hooks**

```typescript
// hiremenow-fe/src/hooks/useCompanies.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { companiesApi, type CompanyFilters } from '@/lib/api/companies';
import type { CompanyCreate } from '@/types';

export function useCompanies(filters: CompanyFilters = {}) {
  return useQuery({
    queryKey: ['companies', filters],
    queryFn: () => companiesApi.list(filters),
  });
}

export function useCompany(id: string) {
  return useQuery({
    queryKey: ['companies', id],
    queryFn: () => companiesApi.get(id),
    enabled: !!id,
  });
}

export function useCreateCompany() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CompanyCreate) => companiesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    },
  });
}

export function useUpdateCompany() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CompanyCreate> }) =>
      companiesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] });
    },
  });
}

export function useDeleteCompany() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => companiesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    },
  });
}
```

**Step 2: Create employers hooks**

```typescript
// hiremenow-fe/src/hooks/useEmployers.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { employersApi, type EmployerFilters } from '@/lib/api/employers';
import type { EmployerCreate } from '@/types';

export function useEmployers(filters: EmployerFilters = {}) {
  return useQuery({
    queryKey: ['employers', filters],
    queryFn: () => employersApi.list(filters),
  });
}

export function useEmployer(id: string) {
  return useQuery({
    queryKey: ['employers', id],
    queryFn: () => employersApi.get(id),
    enabled: !!id,
  });
}

export function useCreateEmployer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: EmployerCreate) => employersApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employers'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    },
  });
}

export function useDeleteEmployer() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => employersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employers'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    },
  });
}
```

**Step 3: Create candidates hooks**

```typescript
// hiremenow-fe/src/hooks/useCandidates.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { candidatesApi, type CandidateFilters } from '@/lib/api/candidates';
import type { Candidate, CandidateCreate } from '@/types';

export function useCandidates(filters: CandidateFilters = {}) {
  return useQuery({
    queryKey: ['candidates', filters],
    queryFn: () => candidatesApi.list(filters),
  });
}

export function useCandidate(id: string) {
  return useQuery({
    queryKey: ['candidates', id],
    queryFn: () => candidatesApi.get(id),
    enabled: !!id,
  });
}

export function useCreateCandidate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CandidateCreate) => candidatesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    },
  });
}

export function useUpdateCandidate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Candidate> }) =>
      candidatesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
    },
  });
}

export function useUpdateCandidateStage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, stage, notes }: { id: string; stage: string; notes?: string }) =>
      candidatesApi.updateStage(id, stage, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    },
  });
}

export function useDeleteCandidate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => candidatesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['candidates'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    },
  });
}
```

**Step 4: Create jobs hooks**

```typescript
// hiremenow-fe/src/hooks/useJobs.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { jobsApi, type JobFilters } from '@/lib/api/jobs';
import type { Job, JobCreate, JobStatus } from '@/types';

export function useJobs(filters: JobFilters = {}) {
  return useQuery({
    queryKey: ['jobs', filters],
    queryFn: () => jobsApi.list(filters),
  });
}

export function useJob(id: string) {
  return useQuery({
    queryKey: ['jobs', id],
    queryFn: () => jobsApi.get(id),
    enabled: !!id,
  });
}

export function useCreateJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: JobCreate) => jobsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    },
  });
}

export function useUpdateJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<JobCreate & { status?: JobStatus }> }) =>
      jobsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });
}

export function useDeleteJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => jobsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      queryClient.invalidateQueries({ queryKey: ['stats'] });
    },
  });
}
```

**Step 5: Create stats hooks**

```typescript
// hiremenow-fe/src/hooks/useStats.ts
import { useQuery } from '@tanstack/react-query';
import { statsApi } from '@/lib/api/stats';

export function useDashboardStats() {
  return useQuery({
    queryKey: ['stats', 'dashboard'],
    queryFn: () => statsApi.getDashboard(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });
}
```

**Step 6: Verify build**

Run:
```bash
cd hiremenow-fe && npm run build
```

Expected: Build succeeds

**Step 7: Commit**

```bash
cd hiremenow-fe && git add . && git commit -m "feat(hooks): add React Query hooks for all admin APIs"
```

---

## Task 5: Implement Dashboard Page with Stats

**Files:**
- Modify: `hiremenow-fe/src/pages/admin/DashboardPage.tsx`

**Step 1: Implement dashboard with stats cards**

```typescript
// hiremenow-fe/src/pages/admin/DashboardPage.tsx
import { Link } from 'react-router-dom';
import { Building2, Users, Briefcase, UserCheck } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useDashboardStats } from '@/hooks/useStats';
import { STAGE_LABELS } from '@/lib/api/candidates';

export default function DashboardPage() {
  const { data: stats, isLoading, error } = useDashboardStats();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-600">
        Failed to load dashboard stats. Please try again.
      </div>
    );
  }

  const statCards = [
    {
      title: 'Companies',
      value: stats?.total_companies ?? 0,
      icon: Building2,
      href: '/admin/companies',
      color: 'text-blue-600',
    },
    {
      title: 'Employers',
      value: stats?.total_employers ?? 0,
      icon: Users,
      href: '/admin/employers',
      color: 'text-green-600',
    },
    {
      title: 'Candidates',
      value: stats?.total_candidates ?? 0,
      icon: UserCheck,
      href: '/admin/candidates',
      color: 'text-purple-600',
    },
    {
      title: 'Active Jobs',
      value: stats?.active_jobs ?? 0,
      icon: Briefcase,
      href: '/admin/jobs',
      color: 'text-orange-600',
      subtitle: `${stats?.total_jobs ?? 0} total`,
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-gray-600">Overview of your recruitment platform</p>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => (
          <Link key={stat.title} to={stat.href}>
            <Card className="hover:shadow-md transition-shadow">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">
                  {stat.title}
                </CardTitle>
                <stat.icon className={`h-5 w-5 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                {stat.subtitle && (
                  <p className="text-xs text-gray-500 mt-1">{stat.subtitle}</p>
                )}
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* Pipeline Overview */}
      {stats?.candidates_by_stage && Object.keys(stats.candidates_by_stage).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Candidate Pipeline</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2 md:grid-cols-3 lg:grid-cols-4">
              {Object.entries(stats.candidates_by_stage).map(([stage, count]) => (
                <div
                  key={stage}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <span className="text-sm text-gray-600">
                    {STAGE_LABELS[stage] || stage}
                  </span>
                  <span className="font-semibold">{count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
```

**Step 2: Verify in browser**

1. Start frontend: `cd hiremenow-fe && npm run dev`
2. Login at http://localhost:5173/login
3. Navigate to dashboard

Expected: Dashboard shows stats cards and pipeline overview

**Step 3: Commit**

```bash
cd hiremenow-fe && git add . && git commit -m "feat(dashboard): implement dashboard with stats cards and pipeline overview"
```

---

## Task 6: Implement Companies List Page

**Files:**
- Modify: `hiremenow-fe/src/pages/admin/CompaniesPage.tsx`
- Create: `hiremenow-fe/src/components/admin/CompanyFormDialog.tsx`

**Step 1: Create company form dialog**

```typescript
// hiremenow-fe/src/components/admin/CompanyFormDialog.tsx
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
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
import type { Company } from '@/types';

const companySchema = z.object({
  name: z.string().min(1, 'Name is required'),
  description: z.string().optional(),
  website: z.string().url().optional().or(z.literal('')),
  location: z.string().optional(),
  industry: z.string().optional(),
  is_agency_owned: z.boolean().optional(),
});

type CompanyFormData = z.infer<typeof companySchema>;

interface CompanyFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  company?: Company | null;
  onSubmit: (data: CompanyFormData) => void;
  isLoading?: boolean;
}

export function CompanyFormDialog({
  open,
  onOpenChange,
  company,
  onSubmit,
  isLoading,
}: CompanyFormDialogProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<CompanyFormData>({
    resolver: zodResolver(companySchema),
  });

  useEffect(() => {
    if (open) {
      reset(company || { name: '', is_agency_owned: false });
    }
  }, [open, company, reset]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>{company ? 'Edit Company' : 'Add Company'}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <Label htmlFor="name">Name *</Label>
            <Input id="name" {...register('name')} />
            {errors.name && (
              <p className="text-sm text-red-600 mt-1">{errors.name.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea id="description" {...register('description')} rows={3} />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="location">Location</Label>
              <Input id="location" {...register('location')} />
            </div>
            <div>
              <Label htmlFor="industry">Industry</Label>
              <Input id="industry" {...register('industry')} />
            </div>
          </div>

          <div>
            <Label htmlFor="website">Website</Label>
            <Input id="website" type="url" {...register('website')} placeholder="https://" />
            {errors.website && (
              <p className="text-sm text-red-600 mt-1">{errors.website.message}</p>
            )}
          </div>

          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="is_agency_owned"
              {...register('is_agency_owned')}
              className="rounded border-gray-300"
            />
            <Label htmlFor="is_agency_owned">Agency Owned</Label>
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Saving...' : company ? 'Update' : 'Create'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
```

**Step 2: Implement companies list page**

```typescript
// hiremenow-fe/src/pages/admin/CompaniesPage.tsx
import { useState } from 'react';
import { Plus, Pencil, Trash2, Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { CompanyFormDialog } from '@/components/admin/CompanyFormDialog';
import { useCompanies, useCreateCompany, useUpdateCompany, useDeleteCompany } from '@/hooks/useCompanies';
import type { Company, CompanyCreate } from '@/types';

export default function CompaniesPage() {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingCompany, setEditingCompany] = useState<Company | null>(null);

  const { data, isLoading } = useCompanies({ page, search: search || undefined });
  const createMutation = useCreateCompany();
  const updateMutation = useUpdateCompany();
  const deleteMutation = useDeleteCompany();

  const handleCreate = () => {
    setEditingCompany(null);
    setDialogOpen(true);
  };

  const handleEdit = (company: Company) => {
    setEditingCompany(company);
    setDialogOpen(true);
  };

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this company?')) {
      await deleteMutation.mutateAsync(id);
    }
  };

  const handleSubmit = async (formData: CompanyCreate) => {
    if (editingCompany) {
      await updateMutation.mutateAsync({ id: editingCompany.id, data: formData });
    } else {
      await createMutation.mutateAsync(formData);
    }
    setDialogOpen(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Companies</h1>
          <p className="mt-1 text-gray-600">Manage partner companies</p>
        </div>
        <Button onClick={handleCreate}>
          <Plus className="h-4 w-4 mr-2" />
          Add Company
        </Button>
      </div>

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <Input
          placeholder="Search companies..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          className="pl-10"
        />
      </div>

      {/* Table */}
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Location</TableHead>
              <TableHead>Industry</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="w-[100px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8">
                  Loading...
                </TableCell>
              </TableRow>
            ) : data?.items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8 text-gray-500">
                  No companies found
                </TableCell>
              </TableRow>
            ) : (
              data?.items.map((company) => (
                <TableRow key={company.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{company.name}</div>
                      {company.is_agency_owned && (
                        <Badge variant="secondary" className="mt-1">Agency</Badge>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>{company.location || '-'}</TableCell>
                  <TableCell>{company.industry || '-'}</TableCell>
                  <TableCell>
                    <Badge variant={company.is_active ? 'default' : 'secondary'}>
                      {company.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEdit(company)}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(company.id)}
                        disabled={deleteMutation.isPending}
                      >
                        <Trash2 className="h-4 w-4 text-red-600" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {data && data.total > data.page_size && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600">
            Showing {(page - 1) * data.page_size + 1} to{' '}
            {Math.min(page * data.page_size, data.total)} of {data.total}
          </p>
          <div className="flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => p - 1)}
              disabled={page === 1}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => p + 1)}
              disabled={page * data.page_size >= data.total}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      <CompanyFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        company={editingCompany}
        onSubmit={handleSubmit}
        isLoading={createMutation.isPending || updateMutation.isPending}
      />
    </div>
  );
}
```

**Step 3: Verify in browser**

1. Navigate to http://localhost:5173/admin/companies
2. Test create, edit, delete operations

Expected: CRUD operations work correctly

**Step 4: Commit**

```bash
cd hiremenow-fe && git add . && git commit -m "feat(companies): implement companies list page with CRUD"
```

---

## Task 7: Implement Employers List Page

**Files:**
- Modify: `hiremenow-fe/src/pages/admin/EmployersPage.tsx`
- Create: `hiremenow-fe/src/components/admin/EmployerFormDialog.tsx`

**Step 1: Create employer form dialog**

```typescript
// hiremenow-fe/src/components/admin/EmployerFormDialog.tsx
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useCompanies } from '@/hooks/useCompanies';

const employerSchema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  company_id: z.string().min(1, 'Company is required'),
});

type EmployerFormData = z.infer<typeof employerSchema>;

interface EmployerFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: EmployerFormData) => void;
  isLoading?: boolean;
}

export function EmployerFormDialog({
  open,
  onOpenChange,
  onSubmit,
  isLoading,
}: EmployerFormDialogProps) {
  const { data: companies } = useCompanies({ page_size: 100 });

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors },
  } = useForm<EmployerFormData>({
    resolver: zodResolver(employerSchema),
  });

  const companyId = watch('company_id');

  useEffect(() => {
    if (open) {
      reset({ email: '', password: '', company_id: '' });
    }
  }, [open, reset]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>Add Employer</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <Label htmlFor="company_id">Company *</Label>
            <Select value={companyId} onValueChange={(v) => setValue('company_id', v)}>
              <SelectTrigger>
                <SelectValue placeholder="Select company" />
              </SelectTrigger>
              <SelectContent>
                {companies?.items.map((company) => (
                  <SelectItem key={company.id} value={company.id}>
                    {company.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.company_id && (
              <p className="text-sm text-red-600 mt-1">{errors.company_id.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="email">Email *</Label>
            <Input id="email" type="email" {...register('email')} />
            {errors.email && (
              <p className="text-sm text-red-600 mt-1">{errors.email.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="password">Password *</Label>
            <Input id="password" type="password" {...register('password')} />
            {errors.password && (
              <p className="text-sm text-red-600 mt-1">{errors.password.message}</p>
            )}
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Creating...' : 'Create'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
```

**Step 2: Implement employers list page**

```typescript
// hiremenow-fe/src/pages/admin/EmployersPage.tsx
import { useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { EmployerFormDialog } from '@/components/admin/EmployerFormDialog';
import { useEmployers, useCreateEmployer, useDeleteEmployer } from '@/hooks/useEmployers';
import type { EmployerCreate } from '@/types';

export default function EmployersPage() {
  const [page, setPage] = useState(1);
  const [dialogOpen, setDialogOpen] = useState(false);

  const { data, isLoading } = useEmployers({ page });
  const createMutation = useCreateEmployer();
  const deleteMutation = useDeleteEmployer();

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this employer?')) {
      await deleteMutation.mutateAsync(id);
    }
  };

  const handleSubmit = async (formData: EmployerCreate) => {
    await createMutation.mutateAsync(formData);
    setDialogOpen(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Employers</h1>
          <p className="mt-1 text-gray-600">Manage employer accounts</p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Employer
        </Button>
      </div>

      {/* Table */}
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Email</TableHead>
              <TableHead>Company</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Created</TableHead>
              <TableHead className="w-[80px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8">
                  Loading...
                </TableCell>
              </TableRow>
            ) : data?.items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8 text-gray-500">
                  No employers found
                </TableCell>
              </TableRow>
            ) : (
              data?.items.map((employer) => (
                <TableRow key={employer.id}>
                  <TableCell className="font-medium">{employer.user.email}</TableCell>
                  <TableCell>{employer.company.name}</TableCell>
                  <TableCell>
                    <Badge variant={employer.user.is_active ? 'default' : 'secondary'}>
                      {employer.user.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {new Date(employer.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(employer.id)}
                      disabled={deleteMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4 text-red-600" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {data && data.total > data.page_size && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600">
            Showing {(page - 1) * data.page_size + 1} to{' '}
            {Math.min(page * data.page_size, data.total)} of {data.total}
          </p>
          <div className="flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => p - 1)}
              disabled={page === 1}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => p + 1)}
              disabled={page * data.page_size >= data.total}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      <EmployerFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onSubmit={handleSubmit}
        isLoading={createMutation.isPending}
      />
    </div>
  );
}
```

**Step 3: Commit**

```bash
cd hiremenow-fe && git add . && git commit -m "feat(employers): implement employers list page with create/delete"
```

---

## Task 8: Implement Candidates List Page

**Files:**
- Modify: `hiremenow-fe/src/pages/admin/CandidatesPage.tsx`
- Create: `hiremenow-fe/src/components/admin/CandidateFormDialog.tsx`
- Create: `hiremenow-fe/src/components/admin/StageUpdateDialog.tsx`

**Step 1: Create candidate form dialog**

```typescript
// hiremenow-fe/src/components/admin/CandidateFormDialog.tsx
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const candidateSchema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  first_name: z.string().optional(),
  last_name: z.string().optional(),
  phone: z.string().optional(),
  source: z.enum(['website', 'facebook', 'instagram', 'referral', 'other']).optional(),
});

type CandidateFormData = z.infer<typeof candidateSchema>;

interface CandidateFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: CandidateFormData) => void;
  isLoading?: boolean;
}

export function CandidateFormDialog({
  open,
  onOpenChange,
  onSubmit,
  isLoading,
}: CandidateFormDialogProps) {
  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors },
  } = useForm<CandidateFormData>({
    resolver: zodResolver(candidateSchema),
    defaultValues: { source: 'website' },
  });

  const source = watch('source');

  useEffect(() => {
    if (open) {
      reset({ email: '', password: '', source: 'website' });
    }
  }, [open, reset]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Add Candidate</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="first_name">First Name</Label>
              <Input id="first_name" {...register('first_name')} />
            </div>
            <div>
              <Label htmlFor="last_name">Last Name</Label>
              <Input id="last_name" {...register('last_name')} />
            </div>
          </div>

          <div>
            <Label htmlFor="email">Email *</Label>
            <Input id="email" type="email" {...register('email')} />
            {errors.email && (
              <p className="text-sm text-red-600 mt-1">{errors.email.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="password">Password *</Label>
            <Input id="password" type="password" {...register('password')} />
            {errors.password && (
              <p className="text-sm text-red-600 mt-1">{errors.password.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="phone">Phone</Label>
            <Input id="phone" {...register('phone')} />
          </div>

          <div>
            <Label>Source</Label>
            <Select value={source} onValueChange={(v: CandidateFormData['source']) => setValue('source', v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="website">Website</SelectItem>
                <SelectItem value="facebook">Facebook</SelectItem>
                <SelectItem value="instagram">Instagram</SelectItem>
                <SelectItem value="referral">Referral</SelectItem>
                <SelectItem value="other">Other</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Creating...' : 'Create'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
```

**Step 2: Create stage update dialog**

```typescript
// hiremenow-fe/src/components/admin/StageUpdateDialog.tsx
import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { PIPELINE_STAGES, STAGE_LABELS } from '@/lib/api/candidates';
import type { Candidate } from '@/types';

interface StageUpdateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  candidate: Candidate | null;
  onSubmit: (stage: string, notes?: string) => void;
  isLoading?: boolean;
}

export function StageUpdateDialog({
  open,
  onOpenChange,
  candidate,
  onSubmit,
  isLoading,
}: StageUpdateDialogProps) {
  const [stage, setStage] = useState(candidate?.current_stage || 'lead');
  const [notes, setNotes] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(stage, notes || undefined);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>Update Pipeline Stage</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label>Current Stage</Label>
            <p className="text-sm text-gray-600">
              {STAGE_LABELS[candidate?.current_stage || ''] || candidate?.current_stage}
            </p>
          </div>

          <div>
            <Label>New Stage</Label>
            <Select value={stage} onValueChange={setStage}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PIPELINE_STAGES.map((s) => (
                  <SelectItem key={s} value={s}>
                    {STAGE_LABELS[s]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label htmlFor="notes">Notes (optional)</Label>
            <Textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              placeholder="Add notes about this stage change..."
            />
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Updating...' : 'Update Stage'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
```

**Step 3: Implement candidates list page**

```typescript
// hiremenow-fe/src/pages/admin/CandidatesPage.tsx
import { useState } from 'react';
import { Plus, Trash2, Search, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { CandidateFormDialog } from '@/components/admin/CandidateFormDialog';
import { StageUpdateDialog } from '@/components/admin/StageUpdateDialog';
import {
  useCandidates,
  useCreateCandidate,
  useUpdateCandidateStage,
  useDeleteCandidate,
} from '@/hooks/useCandidates';
import { PIPELINE_STAGES, STAGE_LABELS } from '@/lib/api/candidates';
import type { Candidate, CandidateCreate } from '@/types';

export default function CandidatesPage() {
  const [search, setSearch] = useState('');
  const [stageFilter, setStageFilter] = useState<string>('');
  const [page, setPage] = useState(1);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [stageDialogOpen, setStageDialogOpen] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);

  const { data, isLoading } = useCandidates({
    page,
    search: search || undefined,
    current_stage: stageFilter || undefined,
  });
  const createMutation = useCreateCandidate();
  const updateStageMutation = useUpdateCandidateStage();
  const deleteMutation = useDeleteCandidate();

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this candidate?')) {
      await deleteMutation.mutateAsync(id);
    }
  };

  const handleCreate = async (formData: CandidateCreate) => {
    await createMutation.mutateAsync(formData);
    setCreateDialogOpen(false);
  };

  const handleStageUpdate = async (stage: string, notes?: string) => {
    if (selectedCandidate) {
      await updateStageMutation.mutateAsync({
        id: selectedCandidate.id,
        stage,
        notes,
      });
      setStageDialogOpen(false);
    }
  };

  const openStageDialog = (candidate: Candidate) => {
    setSelectedCandidate(candidate);
    setStageDialogOpen(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Candidates</h1>
          <p className="mt-1 text-gray-600">Manage candidate pipeline</p>
        </div>
        <Button onClick={() => setCreateDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Candidate
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search candidates..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="pl-10"
          />
        </div>
        <Select
          value={stageFilter}
          onValueChange={(v) => {
            setStageFilter(v === 'all' ? '' : v);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Filter by stage" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Stages</SelectItem>
            {PIPELINE_STAGES.map((stage) => (
              <SelectItem key={stage} value={stage}>
                {STAGE_LABELS[stage]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Phone</TableHead>
              <TableHead>Stage</TableHead>
              <TableHead>Source</TableHead>
              <TableHead className="w-[120px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">
                  Loading...
                </TableCell>
              </TableRow>
            ) : data?.items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                  No candidates found
                </TableCell>
              </TableRow>
            ) : (
              data?.items.map((candidate) => (
                <TableRow key={candidate.id}>
                  <TableCell className="font-medium">
                    {candidate.first_name || candidate.last_name
                      ? `${candidate.first_name || ''} ${candidate.last_name || ''}`.trim()
                      : '-'}
                  </TableCell>
                  <TableCell>{candidate.user.email}</TableCell>
                  <TableCell>{candidate.phone || '-'}</TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      {STAGE_LABELS[candidate.current_stage] || candidate.current_stage}
                    </Badge>
                  </TableCell>
                  <TableCell className="capitalize">{candidate.source}</TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => openStageDialog(candidate)}
                        title="Update stage"
                      >
                        <ArrowRight className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(candidate.id)}
                        disabled={deleteMutation.isPending}
                      >
                        <Trash2 className="h-4 w-4 text-red-600" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {data && data.total > data.page_size && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600">
            Showing {(page - 1) * data.page_size + 1} to{' '}
            {Math.min(page * data.page_size, data.total)} of {data.total}
          </p>
          <div className="flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => p - 1)}
              disabled={page === 1}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => p + 1)}
              disabled={page * data.page_size >= data.total}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      <CandidateFormDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onSubmit={handleCreate}
        isLoading={createMutation.isPending}
      />

      <StageUpdateDialog
        open={stageDialogOpen}
        onOpenChange={setStageDialogOpen}
        candidate={selectedCandidate}
        onSubmit={handleStageUpdate}
        isLoading={updateStageMutation.isPending}
      />
    </div>
  );
}
```

**Step 4: Commit**

```bash
cd hiremenow-fe && git add . && git commit -m "feat(candidates): implement candidates list page with stage management"
```

---

## Task 9: Implement Jobs List Page

**Files:**
- Modify: `hiremenow-fe/src/pages/admin/JobsPage.tsx`
- Create: `hiremenow-fe/src/components/admin/JobFormDialog.tsx`

**Step 1: Create job form dialog**

```typescript
// hiremenow-fe/src/components/admin/JobFormDialog.tsx
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useCompanies } from '@/hooks/useCompanies';
import type { Job } from '@/types';

const jobSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  description: z.string().min(1, 'Description is required'),
  company_id: z.string().min(1, 'Company is required'),
  country: z.string().min(1, 'Country is required'),
  city: z.string().optional(),
  work_mode: z.enum(['onsite', 'accommodation_provided']).optional(),
  job_type: z.enum(['full_time', 'part_time', 'contract', 'seasonal']).optional(),
  salary_min: z.coerce.number().optional(),
  salary_max: z.coerce.number().optional(),
  total_slots: z.coerce.number().min(1).optional(),
});

type JobFormData = z.infer<typeof jobSchema>;

interface JobFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  job?: Job | null;
  onSubmit: (data: JobFormData) => void;
  isLoading?: boolean;
}

export function JobFormDialog({
  open,
  onOpenChange,
  job,
  onSubmit,
  isLoading,
}: JobFormDialogProps) {
  const { data: companies } = useCompanies({ page_size: 100 });

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors },
  } = useForm<JobFormData>({
    resolver: zodResolver(jobSchema),
    defaultValues: {
      work_mode: 'onsite',
      job_type: 'full_time',
      total_slots: 1,
    },
  });

  const companyId = watch('company_id');
  const workMode = watch('work_mode');
  const jobType = watch('job_type');

  useEffect(() => {
    if (open) {
      if (job) {
        reset({
          title: job.title,
          description: job.description,
          company_id: job.company_id,
          country: job.country,
          city: job.city || '',
          work_mode: job.work_mode,
          job_type: job.job_type,
          salary_min: job.salary_min || undefined,
          salary_max: job.salary_max || undefined,
          total_slots: job.total_slots,
        });
      } else {
        reset({
          title: '',
          description: '',
          company_id: '',
          country: '',
          work_mode: 'onsite',
          job_type: 'full_time',
          total_slots: 1,
        });
      }
    }
  }, [open, job, reset]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{job ? 'Edit Job' : 'Create Job'}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <Label htmlFor="company_id">Company *</Label>
            <Select value={companyId} onValueChange={(v) => setValue('company_id', v)}>
              <SelectTrigger>
                <SelectValue placeholder="Select company" />
              </SelectTrigger>
              <SelectContent>
                {companies?.items.map((company) => (
                  <SelectItem key={company.id} value={company.id}>
                    {company.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {errors.company_id && (
              <p className="text-sm text-red-600 mt-1">{errors.company_id.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="title">Title *</Label>
            <Input id="title" {...register('title')} />
            {errors.title && (
              <p className="text-sm text-red-600 mt-1">{errors.title.message}</p>
            )}
          </div>

          <div>
            <Label htmlFor="description">Description *</Label>
            <Textarea id="description" {...register('description')} rows={4} />
            {errors.description && (
              <p className="text-sm text-red-600 mt-1">{errors.description.message}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="country">Country *</Label>
              <Input id="country" {...register('country')} />
              {errors.country && (
                <p className="text-sm text-red-600 mt-1">{errors.country.message}</p>
              )}
            </div>
            <div>
              <Label htmlFor="city">City</Label>
              <Input id="city" {...register('city')} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label>Work Mode</Label>
              <Select value={workMode} onValueChange={(v: JobFormData['work_mode']) => setValue('work_mode', v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="onsite">Onsite</SelectItem>
                  <SelectItem value="accommodation_provided">Accommodation Provided</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Job Type</Label>
              <Select value={jobType} onValueChange={(v: JobFormData['job_type']) => setValue('job_type', v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="full_time">Full Time</SelectItem>
                  <SelectItem value="part_time">Part Time</SelectItem>
                  <SelectItem value="contract">Contract</SelectItem>
                  <SelectItem value="seasonal">Seasonal</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label htmlFor="salary_min">Min Salary</Label>
              <Input id="salary_min" type="number" {...register('salary_min')} />
            </div>
            <div>
              <Label htmlFor="salary_max">Max Salary</Label>
              <Input id="salary_max" type="number" {...register('salary_max')} />
            </div>
            <div>
              <Label htmlFor="total_slots">Slots</Label>
              <Input id="total_slots" type="number" min="1" {...register('total_slots')} />
            </div>
          </div>

          <div className="flex justify-end space-x-2 pt-4">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? 'Saving...' : job ? 'Update' : 'Create'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
```

**Step 2: Implement jobs list page**

```typescript
// hiremenow-fe/src/pages/admin/JobsPage.tsx
import { useState } from 'react';
import { Plus, Pencil, Trash2, Search, CheckCircle, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { JobFormDialog } from '@/components/admin/JobFormDialog';
import { useJobs, useCreateJob, useUpdateJob, useDeleteJob } from '@/hooks/useJobs';
import { JOB_STATUS_LABELS, JOB_STATUS_COLORS } from '@/lib/api/jobs';
import type { Job, JobCreate, JobStatus } from '@/types';

export default function JobsPage() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [page, setPage] = useState(1);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingJob, setEditingJob] = useState<Job | null>(null);

  const { data, isLoading } = useJobs({
    page,
    search: search || undefined,
    status: (statusFilter || undefined) as JobStatus | undefined,
  });
  const createMutation = useCreateJob();
  const updateMutation = useUpdateJob();
  const deleteMutation = useDeleteJob();

  const handleCreate = () => {
    setEditingJob(null);
    setDialogOpen(true);
  };

  const handleEdit = (job: Job) => {
    setEditingJob(job);
    setDialogOpen(true);
  };

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this job?')) {
      await deleteMutation.mutateAsync(id);
    }
  };

  const handleStatusChange = async (job: Job, newStatus: JobStatus) => {
    await updateMutation.mutateAsync({
      id: job.id,
      data: { status: newStatus },
    });
  };

  const handleSubmit = async (formData: JobCreate) => {
    if (editingJob) {
      await updateMutation.mutateAsync({ id: editingJob.id, data: formData });
    } else {
      await createMutation.mutateAsync(formData);
    }
    setDialogOpen(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Jobs</h1>
          <p className="mt-1 text-gray-600">Manage job postings</p>
        </div>
        <Button onClick={handleCreate}>
          <Plus className="h-4 w-4 mr-2" />
          Create Job
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search jobs..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="pl-10"
          />
        </div>
        <Select
          value={statusFilter}
          onValueChange={(v) => {
            setStatusFilter(v === 'all' ? '' : v);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            {Object.entries(JOB_STATUS_LABELS).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="border rounded-lg">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Title</TableHead>
              <TableHead>Company</TableHead>
              <TableHead>Location</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Slots</TableHead>
              <TableHead className="w-[150px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8">
                  Loading...
                </TableCell>
              </TableRow>
            ) : data?.items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                  No jobs found
                </TableCell>
              </TableRow>
            ) : (
              data?.items.map((job) => (
                <TableRow key={job.id}>
                  <TableCell className="font-medium">{job.title}</TableCell>
                  <TableCell>{job.company.name}</TableCell>
                  <TableCell>
                    {job.city ? `${job.city}, ${job.country}` : job.country}
                  </TableCell>
                  <TableCell>
                    <Badge className={JOB_STATUS_COLORS[job.status]}>
                      {JOB_STATUS_LABELS[job.status]}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {job.filled_slots}/{job.total_slots}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-1">
                      {job.status === 'pending_approval' && (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleStatusChange(job, 'active')}
                            title="Approve"
                          >
                            <CheckCircle className="h-4 w-4 text-green-600" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleStatusChange(job, 'rejected')}
                            title="Reject"
                          >
                            <XCircle className="h-4 w-4 text-red-600" />
                          </Button>
                        </>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEdit(job)}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(job.id)}
                        disabled={deleteMutation.isPending}
                      >
                        <Trash2 className="h-4 w-4 text-red-600" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      {data && data.total > data.page_size && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-600">
            Showing {(page - 1) * data.page_size + 1} to{' '}
            {Math.min(page * data.page_size, data.total)} of {data.total}
          </p>
          <div className="flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => p - 1)}
              disabled={page === 1}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => p + 1)}
              disabled={page * data.page_size >= data.total}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      <JobFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        job={editingJob}
        onSubmit={handleSubmit}
        isLoading={createMutation.isPending || updateMutation.isPending}
      />
    </div>
  );
}
```

**Step 3: Commit**

```bash
cd hiremenow-fe && git add . && git commit -m "feat(jobs): implement jobs list page with CRUD and approval"
```

---

## Task 10: Create Public Lead Capture Form

**Files:**
- Create: `hiremenow-fe/src/pages/LeadCapture.tsx`
- Modify: `hiremenow-fe/src/router.tsx`
- Create: `hiremenow-be/app/api/v1/public.py`
- Modify: `hiremenow-be/app/api/v1/router.py`

**Step 1: Create public candidate registration endpoint**

```python
# hiremenow-be/app/api/v1/public.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.candidate import Candidate, LeadSource
from app.core.security import hash_password

router = APIRouter(prefix="/public", tags=["public"])


class LeadCaptureRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    nationality: Optional[str] = Field(None, max_length=100)
    current_country: Optional[str] = Field(None, max_length=100)
    source: LeadSource = LeadSource.WEBSITE
    referral_code: Optional[str] = Field(None, max_length=50)


class LeadCaptureResponse(BaseModel):
    success: bool
    message: str


@router.post("/lead", response_model=LeadCaptureResponse)
def capture_lead(
    data: LeadCaptureRequest,
    db: Session = Depends(get_db),
):
    """Public endpoint for lead capture (candidate registration)."""
    # Check if email exists
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role='candidate',
        is_active=True,
    )
    db.add(user)
    db.flush()

    # Create candidate
    candidate = Candidate(
        user_id=user.id,
        first_name=data.first_name,
        last_name=data.last_name,
        phone=data.phone,
        nationality=data.nationality,
        current_country=data.current_country,
        source=data.source,
        referral_code=data.referral_code,
        current_stage='lead',
    )
    db.add(candidate)
    db.commit()

    return LeadCaptureResponse(
        success=True,
        message="Thank you for registering! We will contact you soon.",
    )
```

**Step 2: Register public router**

Add to `hiremenow-be/app/api/v1/router.py`:

```python
from app.api.v1.public import router as public_router

# Add after other routers:
api_router.include_router(public_router)
```

**Step 3: Create lead capture frontend page**

```typescript
// hiremenow-fe/src/pages/LeadCapture.tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import api from '@/lib/api';

const leadSchema = z.object({
  first_name: z.string().min(1, 'First name is required'),
  last_name: z.string().min(1, 'Last name is required'),
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  phone: z.string().optional(),
  nationality: z.string().optional(),
  current_country: z.string().optional(),
  source: z.enum(['website', 'facebook', 'instagram', 'referral', 'other']),
  referral_code: z.string().optional(),
});

type LeadFormData = z.infer<typeof leadSchema>;

export default function LeadCapturePage() {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<LeadFormData>({
    resolver: zodResolver(leadSchema),
    defaultValues: { source: 'website' },
  });

  const source = watch('source');

  const onSubmit = async (data: LeadFormData) => {
    setIsSubmitting(true);
    setError('');

    try {
      await api.post('/public/lead', data);
      setSuccess(true);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle className="text-green-600">Registration Successful!</CardTitle>
            <CardDescription>
              Thank you for registering with HireMeNow. Our team will contact you soon with job opportunities.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => navigate('/login')} className="w-full">
              Go to Login
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Join HireMeNow</CardTitle>
          <CardDescription>
            Register to receive job opportunities abroad
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {error && (
              <div className="p-3 rounded-md bg-red-50 text-red-600 text-sm">
                {error}
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="first_name">First Name *</Label>
                <Input id="first_name" {...register('first_name')} />
                {errors.first_name && (
                  <p className="text-sm text-red-600 mt-1">{errors.first_name.message}</p>
                )}
              </div>
              <div>
                <Label htmlFor="last_name">Last Name *</Label>
                <Input id="last_name" {...register('last_name')} />
                {errors.last_name && (
                  <p className="text-sm text-red-600 mt-1">{errors.last_name.message}</p>
                )}
              </div>
            </div>

            <div>
              <Label htmlFor="email">Email *</Label>
              <Input id="email" type="email" {...register('email')} />
              {errors.email && (
                <p className="text-sm text-red-600 mt-1">{errors.email.message}</p>
              )}
            </div>

            <div>
              <Label htmlFor="password">Password *</Label>
              <Input id="password" type="password" {...register('password')} />
              {errors.password && (
                <p className="text-sm text-red-600 mt-1">{errors.password.message}</p>
              )}
            </div>

            <div>
              <Label htmlFor="phone">Phone</Label>
              <Input id="phone" {...register('phone')} placeholder="+421..." />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="nationality">Nationality</Label>
                <Input id="nationality" {...register('nationality')} />
              </div>
              <div>
                <Label htmlFor="current_country">Current Country</Label>
                <Input id="current_country" {...register('current_country')} />
              </div>
            </div>

            <div>
              <Label>How did you hear about us?</Label>
              <Select value={source} onValueChange={(v: LeadFormData['source']) => setValue('source', v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="website">Website</SelectItem>
                  <SelectItem value="facebook">Facebook</SelectItem>
                  <SelectItem value="instagram">Instagram</SelectItem>
                  <SelectItem value="referral">Referral</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {source === 'referral' && (
              <div>
                <Label htmlFor="referral_code">Referral Code</Label>
                <Input id="referral_code" {...register('referral_code')} />
              </div>
            )}

            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? 'Registering...' : 'Register'}
            </Button>

            <p className="text-center text-sm text-gray-600">
              Already have an account?{' '}
              <a href="/login" className="text-blue-600 hover:underline">
                Sign in
              </a>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
```

**Step 4: Add route for lead capture**

Update `hiremenow-fe/src/router.tsx` to add the public route:

```typescript
// Add import
import LeadCapturePage from './pages/LeadCapture';

// Add route before the catch-all
{
  path: '/register',
  element: <LeadCapturePage />,
},
```

**Step 5: Test lead capture**

1. Navigate to http://localhost:5173/register
2. Fill out the form
3. Submit

Expected: Registration succeeds, user created as candidate

**Step 6: Commit**

```bash
cd hiremenow-be && git add . && git commit -m "feat(api): add public lead capture endpoint"
cd hiremenow-fe && git add . && git commit -m "feat(lead): add public lead capture registration page"
```

---

## Task 11: Final Verification and Build

**Step 1: Build frontend**

Run:
```bash
cd hiremenow-fe && npm run build
```

Expected: Build succeeds

**Step 2: Run backend tests** (if tests exist)

Run:
```bash
cd hiremenow-be && pytest -v
```

**Step 3: Manual verification checklist**

- [ ] Dashboard shows stats cards
- [ ] Dashboard shows pipeline overview
- [ ] Companies page: list, create, edit, delete
- [ ] Employers page: list, create, delete
- [ ] Candidates page: list, create, delete, stage update
- [ ] Jobs page: list, create, edit, delete, approve/reject
- [ ] Lead capture form works at /register

**Step 4: Final commit**

```bash
git add . && git commit -m "feat: complete Phase 1 admin UI implementation"
```

---

## Summary

This plan implements:

1. **shadcn/ui components** - Base UI component library
2. **API service layer** - Typed API functions for all endpoints
3. **Dashboard stats endpoint** - Backend stats aggregation
4. **React Query hooks** - Data fetching with cache invalidation
5. **Dashboard page** - Stats cards and pipeline overview
6. **Companies page** - Full CRUD with search
7. **Employers page** - Create and delete with company selection
8. **Candidates page** - CRUD with stage management
9. **Jobs page** - CRUD with approval workflow
10. **Lead capture form** - Public registration for candidates

All pages follow consistent patterns with:
- Search and filtering
- Pagination
- Form validation with Zod
- Loading and error states
- Optimistic cache updates
