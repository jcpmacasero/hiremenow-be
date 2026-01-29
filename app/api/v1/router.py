# hiremenow-be/app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.admin.companies import router as admin_companies_router
from app.api.v1.admin.employers import router as admin_employers_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(admin_companies_router, prefix="/admin")
api_router.include_router(admin_employers_router, prefix="/admin")
