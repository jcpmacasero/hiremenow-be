from fastapi import APIRouter
from app.api.v1.employer import company, jobs

router = APIRouter(prefix="/employer", tags=["employer"])
router.include_router(company.router)
router.include_router(jobs.router)
