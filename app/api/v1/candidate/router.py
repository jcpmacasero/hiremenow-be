from fastapi import APIRouter
from app.api.v1.candidate import profile, progress, documents, jobs

router = APIRouter(prefix="/candidate", tags=["candidate"])
router.include_router(profile.router)
router.include_router(progress.router)
router.include_router(documents.router)
router.include_router(jobs.router)
