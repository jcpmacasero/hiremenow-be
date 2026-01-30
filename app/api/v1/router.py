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
from app.api.v1.admin.documents import router as admin_documents_router
from app.api.v1.admin.matches import router as admin_matches_router
from app.api.v1.candidate.router import router as candidate_router
from app.api.v1.employer.router import router as employer_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.notifications import router as notifications_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(public_router)
api_router.include_router(candidate_router)
api_router.include_router(employer_router)
api_router.include_router(conversations_router)
api_router.include_router(notifications_router)
api_router.include_router(admin_companies_router, prefix="/admin")
api_router.include_router(admin_employers_router, prefix="/admin")
api_router.include_router(admin_candidates_router, prefix="/admin")
api_router.include_router(admin_jobs_router, prefix="/admin")
api_router.include_router(admin_stats_router, prefix="/admin")
api_router.include_router(admin_uploads_router, prefix="/admin")
api_router.include_router(admin_documents_router, prefix="/admin")
api_router.include_router(admin_matches_router, prefix="/admin")
