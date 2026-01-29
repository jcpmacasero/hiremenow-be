# HireMeNow - Recruitment Agency Platform Design

## Overview

A recruitment agency platform for placing workers in Slovakia/Czech Republic jobs. Candidates go through a multi-stage pipeline from lead acquisition to deployment, with paid services (tests, language courses, legal packages) along the way.

## User Types

| Role | Description |
|------|-------------|
| **Admin** | Full control - manages pipeline, jobs, candidates, partners, services |
| **Candidate** | Goes through pipeline, takes tests, pays for services, tracks progress |
| **Partner** | Service providers (language schools, legal services) - manage offerings, receive payments |
| **Employer** | Posts jobs (admin approves), views matched candidates |

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER TYPES                                │
├─────────────┬─────────────┬─────────────┬───────────────────────┤
│   Admin     │  Candidate  │   Partner   │      Employer         │
│  (agency)   │  (worker)   │ (services)  │   (job source)        │
├─────────────┴─────────────┴─────────────┴───────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              CONFIGURABLE PIPELINE ENGINE                 │   │
│  │  Lead → Screen → Assess → Match → Agree → Prepare → Deploy│  │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────────────┐   │
│  │  Job Board  │  │  Services   │  │   Payments (Stripe)    │   │
│  │  + Matching │  │  Marketplace│  │   Split to Partners    │   │
│  └─────────────┘  └─────────────┘  └────────────────────────┘   │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────────────┐   │
│  │  Testing    │  │  Mini LMS   │  │   In-App Messaging     │   │
│  │  Engine     │  │  (courses)  │  │                        │   │
│  └─────────────┘  └─────────────┘  └────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Key components:**
- **Pipeline Engine**: Configurable stages per job type/country
- **Job Board**: Employer-posted + agency-sourced jobs with slot management
- **Services Marketplace**: Tests, courses, legal packages from agency + partners
- **Payment System**: Stripe Connect for split payments
- **Testing Engine**: Built-in IQ/logic tests + manual score entry
- **Mini LMS**: Basic course hosting + external partner integration
- **Messaging**: In-app chat between all parties

---

## Data Model

### Users & Auth

```
users
├── id (UUID)
├── email (unique)
├── password_hash (nullable for OAuth)
├── role (enum: admin, candidate, partner, employer)
├── is_active (boolean)
├── created_at, updated_at

oauth_accounts
├── id
├── user_id → users
├── provider (google, linkedin, facebook)
├── provider_user_id
├── access_token, refresh_token
```

### Partners (Service Providers)

```
partners
├── id (UUID)
├── user_id → users (role=partner)
├── name (business name)
├── slug
├── description
├── logo_url
├── type (enum: language_school, legal_services, transport, accommodation, other)
├── stripe_account_id (for payouts)
├── commission_percent (agency cut, e.g., 10%)
├── is_verified (boolean)
├── created_at, updated_at
```

### Employers & Companies

```
companies
├── id (UUID)
├── name
├── slug
├── description
├── logo_url
├── location
├── industry
├── is_agency_owned (boolean - agency-sourced vs external)
├── is_active
├── created_at, updated_at

employers
├── id
├── user_id → users (role=employer)
├── company_id → companies
├── created_at
```

### Candidates

```
candidates
├── id (UUID)
├── user_id → users (role=candidate)
├── first_name, last_name
├── phone
├── date_of_birth
├── nationality
├── current_country
├── passport_status (enum: valid, expired, none, in_progress)
├── passport_expiry
├── preferred_positions (JSON array)
├── experience_years
├── photo_url
├── resume_url
├── source (enum: website, facebook, instagram, referral, other)
├── referral_code
├── current_stage_id → pipeline_stages
├── current_pipeline_id → pipelines
├── created_at, updated_at
```

### Configurable Pipelines

```
pipelines
├── id (UUID)
├── name (e.g., "Slovakia Standard", "Czech Fast-Track")
├── description
├── country (nullable - if country-specific)
├── job_type (nullable - if job-type-specific)
├── is_default (boolean)
├── is_active
├── created_at, updated_at

pipeline_stages
├── id (UUID)
├── pipeline_id → pipelines
├── name (e.g., "Lead", "Pre-Screening", "Assessment")
├── slug
├── order (integer)
├── type (enum: manual, automated, payment_required, test_required, agreement_required)
├── description
├── required_services (JSON - service IDs that must be purchased)
├── auto_advance_on (nullable - event that triggers next stage)
├── created_at

candidate_stage_history
├── id
├── candidate_id → candidates
├── stage_id → pipeline_stages
├── status (enum: entered, in_progress, completed, skipped, rejected)
├── entered_at
├── completed_at
├── notes
├── updated_by → users

stage_requirements
├── id
├── stage_id → pipeline_stages
├── requirement_type (enum: test, document, payment, agreement, manual_approval)
├── requirement_id (nullable - links to test_id, service_id, etc.)
├── is_required (boolean)
├── order
```

**Example pipeline:**
```
Slovakia Standard Pipeline:
├── 1. Lead (manual)
├── 2. Pre-Screening (manual_approval)
├── 3. Assessment (test_required) → IQ, Manual Skills
├── 4. Job Matching (automated)
├── 5. Pre-Agreement (agreement_required)
├── 6. Language Course (payment_required) → Slovak Course
├── 7. Legal & Paperwork (payment_required) → Legal Package
├── 8. Departure Prep (manual)
├── 9. Transport (manual)
├── 10. Deployed (manual)
└── 11. After-Sales (ongoing)
```

### Jobs & Matching

```
job_categories
├── id
├── name (Factory Worker, Warehouse, Construction, etc.)
├── slug

jobs
├── id (UUID)
├── company_id → companies
├── created_by → users (admin or employer)
├── pipeline_id → pipelines (which pipeline candidates follow)
├── title
├── slug
├── description
├── category_id → job_categories
├── country
├── city
├── work_mode (enum: onsite, accommodation_provided)
├── job_type (enum: full_time, part_time, contract, seasonal)
├── salary_min, salary_max
├── salary_currency
├── salary_period (enum: hourly, monthly)
├── benefits (JSON - accommodation, transport, meals, etc.)
├── requirements (JSON - skills, experience, language level)
├── total_slots (integer)
├── filled_slots (integer, default 0)
├── status (enum: draft, pending_approval, active, paused, closed)
├── deadline
├── start_date
├── created_at, updated_at

candidate_skills
├── candidate_id → candidates
├── skill_id → skills
├── proficiency (enum: beginner, intermediate, advanced)
├── verified (boolean - from test results)

job_matches
├── id (UUID)
├── candidate_id → candidates
├── job_id → jobs
├── match_score (integer 0-100)
├── match_reasons (JSON - why they matched)
├── status (enum: suggested, candidate_interested, admin_approved, confirmed, rejected)
├── suggested_at
├── confirmed_at
├── rejected_reason
├── notes

job_applications
├── id (UUID)
├── candidate_id → candidates
├── job_id → jobs
├── match_id → job_matches (nullable)
├── status (enum: applied, reviewing, matched, deployed, withdrawn, rejected)
├── applied_at
├── updated_at
```

**Slot management trigger:**
```
ON job_matches.status → 'confirmed':
  jobs.filled_slots += 1
  IF filled_slots >= total_slots:
    jobs.status = 'closed'
```

### Services Marketplace & Payments

```
services
├── id (UUID)
├── partner_id → partners (nullable - null means agency-owned)
├── name
├── slug
├── description
├── type (enum: test, course, legal_package, transport, accommodation, document, subscription, other)
├── price
├── currency
├── is_recurring (boolean)
├── recurring_interval (enum: monthly, yearly - if recurring)
├── duration_days (nullable - for courses)
├── is_active
├── created_at, updated_at

service_packages (bundles)
├── id (UUID)
├── name (e.g., "Full Package", "Basic Package")
├── description
├── price (discounted bundle price)
├── currency
├── is_active
├── created_at

package_items
├── package_id → service_packages
├── service_id → services

orders
├── id (UUID)
├── candidate_id → candidates
├── total_amount
├── currency
├── status (enum: pending, paid, failed, refunded, partially_refunded)
├── stripe_payment_intent_id
├── paid_at
├── created_at, updated_at

order_items
├── id
├── order_id → orders
├── service_id → services (nullable)
├── package_id → service_packages (nullable)
├── quantity
├── unit_price
├── subtotal
├── partner_id → partners (nullable - for split)
├── partner_amount (amount going to partner)
├── agency_amount (amount kept by agency)

payouts (to partners)
├── id (UUID)
├── partner_id → partners
├── amount
├── currency
├── status (enum: pending, processing, completed, failed)
├── stripe_transfer_id
├── period_start, period_end
├── created_at, completed_at

candidate_subscriptions (after-sales)
├── id (UUID)
├── candidate_id → candidates
├── service_id → services
├── stripe_subscription_id
├── status (enum: active, cancelled, past_due, paused)
├── current_period_start, current_period_end
├── created_at, cancelled_at

candidate_services
├── id
├── candidate_id → candidates
├── service_id → services
├── order_id → orders
├── status (enum: purchased, in_progress, completed, expired)
├── started_at
├── completed_at
├── expires_at
├── progress_percent (for courses)
```

### Testing & LMS

```
tests
├── id (UUID)
├── service_id → services (links to purchasable service)
├── name
├── slug
├── type (enum: iq, logic, language, manual_skills, custom)
├── description
├── time_limit_minutes (nullable)
├── passing_score (nullable)
├── is_built_in (boolean - system vs manual entry)
├── is_active
├── created_at

test_questions (for built-in tests)
├── id (UUID)
├── test_id → tests
├── question_text
├── question_type (enum: multiple_choice, true_false, numeric)
├── options (JSON array for multiple choice)
├── correct_answer
├── points
├── order

test_attempts
├── id (UUID)
├── candidate_id → candidates
├── test_id → tests
├── started_at
├── completed_at
├── time_spent_seconds
├── score
├── max_score
├── passed (boolean)
├── is_manual_entry (boolean - admin entered results)
├── entered_by → users (nullable - for manual)
├── notes

test_answers (for built-in tests)
├── id
├── attempt_id → test_attempts
├── question_id → test_questions
├── answer_given
├── is_correct
├── points_earned

courses
├── id (UUID)
├── service_id → services
├── partner_id → partners (nullable)
├── name
├── slug
├── description
├── thumbnail_url
├── is_external (boolean - hosted elsewhere)
├── external_url (nullable)
├── total_lessons
├── estimated_hours
├── is_active
├── created_at

course_modules
├── id (UUID)
├── course_id → courses
├── name
├── description
├── order

course_lessons
├── id (UUID)
├── module_id → course_modules
├── name
├── content_type (enum: video, text, quiz, download)
├── content_url (video/file URL)
├── content_text (for text lessons)
├── duration_minutes
├── order

candidate_course_progress
├── id
├── candidate_id → candidates
├── course_id → courses
├── current_lesson_id → course_lessons
├── completed_lessons (JSON array of lesson IDs)
├── progress_percent
├── started_at
├── completed_at

lesson_completions
├── candidate_id → candidates
├── lesson_id → course_lessons
├── completed_at
```

### Messaging & Notifications

```
conversations
├── id (UUID)
├── type (enum: direct, support, group)
├── subject (nullable)
├── created_at, updated_at

conversation_participants
├── conversation_id → conversations
├── user_id → users
├── role (enum: member, admin)
├── joined_at
├── last_read_at
├── is_muted (boolean)

messages
├── id (UUID)
├── conversation_id → conversations
├── sender_id → users
├── content
├── content_type (enum: text, file, image, system)
├── file_url (nullable)
├── is_edited (boolean)
├── created_at, updated_at

message_reads
├── message_id → messages
├── user_id → users
├── read_at

notifications
├── id (UUID)
├── user_id → users
├── type (enum: stage_changed, payment_received, test_result,
│         job_match, message_received, document_required,
│         application_update, course_reminder, system)
├── title
├── message
├── data (JSON - contextual IDs)
├── action_url (nullable - deep link)
├── is_read (boolean)
├── read_at
├── created_at

notification_preferences
├── user_id → users (primary key)
├── email_enabled (boolean)
├── push_enabled (boolean)
├── sms_enabled (boolean)
├── stage_updates (boolean)
├── payment_confirmations (boolean)
├── messages (boolean)
├── marketing (boolean)
├── updated_at

push_subscriptions
├── id
├── user_id → users
├── endpoint
├── p256dh_key
├── auth_key
├── device_name
├── created_at

email_templates
├── id
├── slug (e.g., "welcome", "stage_advanced", "payment_confirmed")
├── subject
├── body_html
├── body_text
├── variables (JSON - available placeholders)
├── is_active
├── updated_at
```

### Documents & Supporting Tables

```
documents
├── id (UUID)
├── candidate_id → candidates
├── type (enum: passport, resume, photo, certificate, agreement, other)
├── name
├── file_url
├── file_size
├── mime_type
├── status (enum: pending_review, approved, rejected)
├── reviewed_by → users (nullable)
├── rejection_reason (nullable)
├── expires_at (nullable - for passport)
├── uploaded_at
├── reviewed_at

document_requirements
├── id
├── stage_id → pipeline_stages (nullable)
├── job_id → jobs (nullable)
├── document_type (enum)
├── is_required (boolean)
├── description

agreements
├── id (UUID)
├── name
├── slug
├── content_html
├── version
├── is_active
├── created_at

candidate_agreements
├── id
├── candidate_id → candidates
├── agreement_id → agreements
├── stage_id → pipeline_stages (nullable - signed at which stage)
├── ip_address
├── user_agent
├── signed_at

activity_logs
├── id (UUID)
├── user_id → users (nullable - system actions)
├── action (e.g., "candidate.stage_changed", "job.approved")
├── entity_type (e.g., "candidate", "job", "order")
├── entity_id
├── old_values (JSON)
├── new_values (JSON)
├── ip_address
├── created_at

admin_notes
├── id (UUID)
├── entity_type (candidate, job, partner, etc.)
├── entity_id
├── author_id → users
├── content
├── is_internal (boolean - visible to admins only)
├── created_at, updated_at

countries
├── code (PK - ISO 3166)
├── name
├── is_source (boolean - candidates come from)
├── is_destination (boolean - jobs located in)

skills
├── id
├── name
├── slug
├── category (nullable)

settings
├── key (PK)
├── value (JSON)
├── description
├── updated_at
```

---

## API Structure

### Auth

```
POST   /api/v1/auth/register              (candidates only)
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
POST   /api/v1/auth/refresh
POST   /api/v1/auth/forgot-password
POST   /api/v1/auth/reset-password
GET    /api/v1/auth/oauth/{provider}
GET    /api/v1/auth/oauth/{provider}/callback
GET    /api/v1/auth/me
```

### Admin - Users & Organizations

```
# Partners
GET    /api/v1/admin/partners
POST   /api/v1/admin/partners
GET    /api/v1/admin/partners/{id}
PUT    /api/v1/admin/partners/{id}
DELETE /api/v1/admin/partners/{id}

# Employers & Companies
GET    /api/v1/admin/companies
POST   /api/v1/admin/companies
PUT    /api/v1/admin/companies/{id}
DELETE /api/v1/admin/companies/{id}
POST   /api/v1/admin/companies/{id}/employers
DELETE /api/v1/admin/employers/{id}

# Candidates
GET    /api/v1/admin/candidates
GET    /api/v1/admin/candidates/{id}
PUT    /api/v1/admin/candidates/{id}
POST   /api/v1/admin/candidates/{id}/advance-stage
POST   /api/v1/admin/candidates/{id}/reject
GET    /api/v1/admin/candidates/{id}/history
POST   /api/v1/admin/candidates/{id}/notes
```

### Admin - Pipeline & Jobs

```
# Pipelines
GET    /api/v1/admin/pipelines
POST   /api/v1/admin/pipelines
GET    /api/v1/admin/pipelines/{id}
PUT    /api/v1/admin/pipelines/{id}
DELETE /api/v1/admin/pipelines/{id}
POST   /api/v1/admin/pipelines/{id}/stages
PUT    /api/v1/admin/pipelines/{id}/stages/{stageId}
DELETE /api/v1/admin/pipelines/{id}/stages/{stageId}

# Jobs
GET    /api/v1/admin/jobs
POST   /api/v1/admin/jobs
GET    /api/v1/admin/jobs/{id}
PUT    /api/v1/admin/jobs/{id}
POST   /api/v1/admin/jobs/{id}/approve
POST   /api/v1/admin/jobs/{id}/reject
GET    /api/v1/admin/jobs/{id}/matches

# Matching
POST   /api/v1/admin/jobs/{id}/generate-matches
POST   /api/v1/admin/matches/{id}/confirm
POST   /api/v1/admin/matches/{id}/reject
```

### Admin - Services & Content

```
# Services
GET    /api/v1/admin/services
POST   /api/v1/admin/services
PUT    /api/v1/admin/services/{id}
DELETE /api/v1/admin/services/{id}
POST   /api/v1/admin/service-packages
PUT    /api/v1/admin/service-packages/{id}

# Tests
GET    /api/v1/admin/tests
POST   /api/v1/admin/tests
PUT    /api/v1/admin/tests/{id}
POST   /api/v1/admin/tests/{id}/questions
POST   /api/v1/admin/candidates/{id}/test-results  (manual entry)

# Courses
GET    /api/v1/admin/courses
POST   /api/v1/admin/courses
PUT    /api/v1/admin/courses/{id}
POST   /api/v1/admin/courses/{id}/modules
POST   /api/v1/admin/courses/{id}/lessons

# Documents
GET    /api/v1/admin/documents/pending
POST   /api/v1/admin/documents/{id}/approve
POST   /api/v1/admin/documents/{id}/reject

# Dashboard
GET    /api/v1/admin/stats
GET    /api/v1/admin/activity
```

### Partner Endpoints

```
GET    /api/v1/partner/profile
PUT    /api/v1/partner/profile

# Services they provide
GET    /api/v1/partner/services
POST   /api/v1/partner/services
PUT    /api/v1/partner/services/{id}

# Courses they provide
GET    /api/v1/partner/courses
POST   /api/v1/partner/courses
PUT    /api/v1/partner/courses/{id}
POST   /api/v1/partner/courses/{id}/modules
POST   /api/v1/partner/courses/{id}/lessons

# Candidates using their services
GET    /api/v1/partner/candidates
PUT    /api/v1/partner/candidates/{id}/service-status

# Earnings
GET    /api/v1/partner/earnings
GET    /api/v1/partner/payouts
```

### Employer Endpoints

```
GET    /api/v1/employer/company
PUT    /api/v1/employer/company

GET    /api/v1/employer/jobs
POST   /api/v1/employer/jobs
GET    /api/v1/employer/jobs/{id}
PUT    /api/v1/employer/jobs/{id}

GET    /api/v1/employer/jobs/{id}/matches
GET    /api/v1/employer/candidates/{id}
```

### Candidate Endpoints

```
# Profile
GET    /api/v1/candidate/profile
PUT    /api/v1/candidate/profile
POST   /api/v1/candidate/profile/photo
POST   /api/v1/candidate/profile/resume

# Pipeline progress
GET    /api/v1/candidate/progress
GET    /api/v1/candidate/requirements

# Jobs
GET    /api/v1/candidate/jobs                 (available matches)
GET    /api/v1/candidate/jobs/{id}
POST   /api/v1/candidate/jobs/{id}/interest   (express interest)
GET    /api/v1/candidate/matches

# Tests
GET    /api/v1/candidate/tests
POST   /api/v1/candidate/tests/{id}/start
POST   /api/v1/candidate/tests/{id}/submit
GET    /api/v1/candidate/test-results

# Courses
GET    /api/v1/candidate/courses
GET    /api/v1/candidate/courses/{id}
POST   /api/v1/candidate/courses/{id}/lessons/{lessonId}/complete
GET    /api/v1/candidate/courses/{id}/progress

# Services & Payments
GET    /api/v1/candidate/services
POST   /api/v1/candidate/checkout
GET    /api/v1/candidate/orders
GET    /api/v1/candidate/subscriptions
POST   /api/v1/candidate/subscriptions/{id}/cancel

# Documents
GET    /api/v1/candidate/documents
POST   /api/v1/candidate/documents
DELETE /api/v1/candidate/documents/{id}

# Agreements
GET    /api/v1/candidate/agreements
POST   /api/v1/candidate/agreements/{id}/sign

# Departure info
GET    /api/v1/candidate/departure
```

### Shared Endpoints

```
# Messaging
GET    /api/v1/conversations
POST   /api/v1/conversations
GET    /api/v1/conversations/{id}
POST   /api/v1/conversations/{id}/messages
PUT    /api/v1/conversations/{id}/read

# Notifications
GET    /api/v1/notifications
PUT    /api/v1/notifications/{id}/read
PUT    /api/v1/notifications/read-all
GET    /api/v1/notification-preferences
PUT    /api/v1/notification-preferences

# Webhooks (Stripe)
POST   /api/v1/webhooks/stripe
```

---

## Frontend Pages

### Public Pages

```
/                       → Landing page (lead capture form)
/login                  → Login (all roles)
/register               → Candidate registration
/oauth/callback         → OAuth return handler
/forgot-password        → Password reset request
/reset-password/:token  → Password reset form
/jobs                   → Public job listings (preview)
/jobs/:slug             → Job detail (with apply CTA)
/companies/:slug        → Company profile
```

### Candidate Portal

```
/candidate
├── /dashboard          → Progress overview, next steps, notifications
├── /profile            → Edit profile, upload photo/resume
├── /progress           → Pipeline stages, current status, requirements
├── /jobs               → Matched jobs, express interest
├── /jobs/:id           → Job detail with match score
├── /tests              → Available tests, take test, view results
├── /tests/:id          → Test taking interface
├── /courses            → Enrolled courses, progress
├── /courses/:id        → Course player (lessons, videos)
├── /services           → Available services, packages
├── /checkout           → Purchase flow
├── /orders             → Payment history
├── /documents          → Upload/manage documents
├── /agreements         → Sign required agreements
├── /departure          → Travel details, coordinator info
├── /messages           → Conversations
├── /settings           → Notification preferences, password
```

### Partner Portal

```
/partner
├── /dashboard          → Earnings overview, active candidates
├── /profile            → Business profile, Stripe setup
├── /services           → Manage service offerings
├── /courses            → Manage courses, modules, lessons
├── /courses/:id/edit   → Course builder
├── /candidates         → Candidates using their services
├── /candidates/:id     → Update service progress
├── /earnings           → Revenue breakdown, payout history
├── /messages           → Conversations with candidates/admin
├── /settings           → Account settings
```

### Employer Portal

```
/employer
├── /dashboard          → Job stats, recent matches
├── /company            → Company profile edit
├── /jobs               → Job listings (draft, pending, active)
├── /jobs/new           → Create job posting
├── /jobs/:id           → Job detail, view matches
├── /jobs/:id/edit      → Edit job
├── /candidates/:id     → View matched candidate profile
├── /messages           → Conversations
├── /settings           → Account settings
```

### Admin Panel

```
/admin
├── /dashboard          → Stats, pending items, recent activity
│
├── /candidates         → All candidates, filter by stage
├── /candidates/:id     → Full candidate view, advance/reject, notes
│
├── /companies          → Manage companies
├── /companies/new      → Create company
├── /companies/:id      → Edit company, manage employers
│
├── /partners           → Manage partners
├── /partners/new       → Create partner account
├── /partners/:id       → Edit partner, view earnings
│
├── /jobs               → All jobs, filter by status
├── /jobs/pending       → Jobs awaiting approval
├── /jobs/:id           → Job detail, approve/reject, view matches
│
├── /pipelines          → Manage pipelines
├── /pipelines/new      → Create pipeline
├── /pipelines/:id      → Edit stages, requirements
│
├── /services           → Manage agency services
├── /services/:id       → Edit service
├── /packages           → Manage service bundles
│
├── /tests              → Manage tests
├── /tests/new          → Create test with questions
├── /tests/:id          → Edit test, view attempts
│
├── /courses            → All courses (agency + partner)
├── /courses/:id        → Edit course content
│
├── /orders             → All transactions
├── /payouts            → Partner payout management
│
├── /documents          → Pending document reviews
│
├── /messages           → All conversations, support queue
├── /activity           → Audit log
├── /settings           → System settings, email templates
```

---

## Tech Stack

### Frontend

- React 18 + TypeScript + Vite
- React Router v6
- TanStack Query (data fetching, caching)
- Zustand (global state)
- Tailwind CSS + shadcn/ui
- React Hook Form + Zod (forms, validation)
- Stripe.js (payments)
- Firebase/Web Push API (push notifications)

### Backend

- FastAPI
- SQLAlchemy 2.0 + Alembic
- PostgreSQL
- Redis (sessions, queues, caching)
- Celery (background jobs - emails, notifications, matching)
- Stripe Connect (payments, payouts)
- AWS S3 / Local (file storage - abstracted)
- python-jose + passlib (JWT auth)

### Infrastructure

- Docker Compose
- Nginx (reverse proxy, static files)
- Let's Encrypt (SSL)

---

## Implementation Phases

### Phase 1: Foundation (MVP)

- Auth (email/password, roles)
- Admin: manage companies, employers, candidates
- Basic candidate profile + lead form
- Simple fixed pipeline (no configurability yet)
- Admin advances candidates through stages
- Basic job posting + manual matching
- File storage abstraction (local)

### Phase 2: Core Features

- Candidate portal (progress, profile, documents)
- Employer portal (post jobs, view matches)
- Job approval workflow
- Smart matching algorithm
- Slot management
- In-app messaging
- Basic notifications (in-app)

### Phase 3: Monetization

- Stripe Connect integration
- Services marketplace
- Checkout flow
- Partner portal (basic)
- Payment history + receipts
- Partner payouts

### Phase 4: Testing & Courses

- Built-in test engine
- Test taking UI
- Manual score entry
- Mini LMS (course player)
- Course builder for admin/partners
- Progress tracking

### Phase 5: Advanced Features

- Configurable pipelines
- OAuth (Google, LinkedIn, Facebook)
- Email notifications
- Push notifications
- Agreements (e-signature)
- Full partner management
- Departure tracking

### Phase 6: Polish

- Admin dashboard analytics
- Activity logs / audit
- Email templates
- Candidate subscriptions (after-sales)
- Mobile responsiveness
- Performance optimization
