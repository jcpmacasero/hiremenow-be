# File Storage Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add file upload/download capabilities for candidate photos and resumes with local filesystem storage abstraction.

**Architecture:** Create a storage service abstraction layer that handles file uploads to configurable local directory. Files are stored with UUID-based names to prevent conflicts. The API provides multipart upload endpoints and serves files through static file serving.

**Tech Stack:** FastAPI (python-multipart), aiofiles, Pillow (image validation), pathlib

---

## Task 1: Add Storage Configuration

**Files:**
- Modify: `hiremenow-be/app/config.py`
- Modify: `hiremenow-be/.env`

**Step 1: Update config.py with storage settings**

Add to `hiremenow-be/app/config.py` in the Settings class:

```python
# hiremenow-be/app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str

    # App
    environment: str = "development"
    debug: bool = True
    api_version: str = "v1"

    # Security
    secret_key: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    cors_origins: str = "http://localhost:5173"

    # File Storage
    upload_dir: str = "./uploads"
    max_file_size_mb: int = 10
    allowed_image_types: str = "image/jpeg,image/png,image/webp"
    allowed_resume_types: str = "application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

**Step 2: Update .env with storage settings**

Add to `hiremenow-be/.env`:

```
UPLOAD_DIR=./uploads
MAX_FILE_SIZE_MB=10
```

**Step 3: Commit**

```bash
git add hiremenow-be/app/config.py hiremenow-be/.env
git commit -m "feat(config): add file storage configuration"
```

---

## Task 2: Create Storage Service

**Files:**
- Create: `hiremenow-be/app/services/__init__.py`
- Create: `hiremenow-be/app/services/storage.py`

**Step 1: Create services package**

```python
# hiremenow-be/app/services/__init__.py
from app.services.storage import StorageService, get_storage_service

__all__ = ["StorageService", "get_storage_service"]
```

**Step 2: Create storage service**

```python
# hiremenow-be/app/services/storage.py
import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, Tuple
from fastapi import UploadFile, HTTPException, status
from app.config import get_settings

settings = get_settings()


class StorageService:
    """Local filesystem storage service."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self._ensure_directories()

    def _ensure_directories(self):
        """Create upload directories if they don't exist."""
        (self.base_path / "photos").mkdir(parents=True, exist_ok=True)
        (self.base_path / "resumes").mkdir(parents=True, exist_ok=True)

    def _get_extension(self, filename: str) -> str:
        """Extract file extension from filename."""
        return Path(filename).suffix.lower()

    def _validate_file_size(self, file: UploadFile) -> None:
        """Validate file doesn't exceed max size."""
        # Read file to check size
        file.file.seek(0, 2)  # Seek to end
        size = file.file.tell()
        file.file.seek(0)  # Reset to start

        max_bytes = settings.max_file_size_mb * 1024 * 1024
        if size > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Max size is {settings.max_file_size_mb}MB",
            )

    def _validate_content_type(self, content_type: str, allowed_types: str) -> None:
        """Validate content type is allowed."""
        allowed = [t.strip() for t in allowed_types.split(",")]
        if content_type not in allowed:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"File type not allowed. Allowed types: {', '.join(allowed)}",
            )

    async def save_photo(self, file: UploadFile, candidate_id: uuid.UUID) -> str:
        """Save a photo file and return the relative path."""
        self._validate_file_size(file)
        self._validate_content_type(file.content_type, settings.allowed_image_types)

        ext = self._get_extension(file.filename or ".jpg")
        filename = f"{candidate_id}{ext}"
        file_path = self.base_path / "photos" / filename

        # Remove old photo if exists (any extension)
        for old_file in (self.base_path / "photos").glob(f"{candidate_id}.*"):
            old_file.unlink()

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return f"/uploads/photos/{filename}"

    async def save_resume(self, file: UploadFile, candidate_id: uuid.UUID) -> str:
        """Save a resume file and return the relative path."""
        self._validate_file_size(file)
        self._validate_content_type(file.content_type, settings.allowed_resume_types)

        ext = self._get_extension(file.filename or ".pdf")
        filename = f"{candidate_id}{ext}"
        file_path = self.base_path / "resumes" / filename

        # Remove old resume if exists (any extension)
        for old_file in (self.base_path / "resumes").glob(f"{candidate_id}.*"):
            old_file.unlink()

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return f"/uploads/resumes/{filename}"

    def delete_photo(self, candidate_id: uuid.UUID) -> None:
        """Delete a candidate's photo."""
        for old_file in (self.base_path / "photos").glob(f"{candidate_id}.*"):
            old_file.unlink()

    def delete_resume(self, candidate_id: uuid.UUID) -> None:
        """Delete a candidate's resume."""
        for old_file in (self.base_path / "resumes").glob(f"{candidate_id}.*"):
            old_file.unlink()

    def get_file_path(self, relative_path: str) -> Optional[Path]:
        """Get absolute path for a relative upload path."""
        if not relative_path or not relative_path.startswith("/uploads/"):
            return None
        # Remove /uploads/ prefix
        subpath = relative_path[9:]
        full_path = self.base_path / subpath
        if full_path.exists():
            return full_path
        return None


# Singleton instance
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Get or create storage service singleton."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService(settings.upload_dir)
    return _storage_service
```

**Step 3: Commit**

```bash
git add hiremenow-be/app/services
git commit -m "feat(storage): add local file storage service"
```

---

## Task 3: Add File Upload Endpoints

**Files:**
- Create: `hiremenow-be/app/api/v1/admin/uploads.py`
- Modify: `hiremenow-be/app/api/v1/router.py`

**Step 1: Create upload endpoints**

```python
# hiremenow-be/app/api/v1/admin/uploads.py
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_admin_user
from app.models.user import User
from app.models.candidate import Candidate
from app.services.storage import get_storage_service, StorageService
from pydantic import BaseModel


router = APIRouter(prefix="/uploads", tags=["admin-uploads"])


class UploadResponse(BaseModel):
    url: str
    message: str


@router.post("/candidates/{candidate_id}/photo", response_model=UploadResponse)
async def upload_candidate_photo(
    candidate_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
    storage: StorageService = Depends(get_storage_service),
):
    """Upload a photo for a candidate."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    url = await storage.save_photo(file, candidate_id)
    candidate.photo_url = url
    db.commit()

    return UploadResponse(url=url, message="Photo uploaded successfully")


@router.post("/candidates/{candidate_id}/resume", response_model=UploadResponse)
async def upload_candidate_resume(
    candidate_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
    storage: StorageService = Depends(get_storage_service),
):
    """Upload a resume for a candidate."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    url = await storage.save_resume(file, candidate_id)
    candidate.resume_url = url
    db.commit()

    return UploadResponse(url=url, message="Resume uploaded successfully")


@router.delete("/candidates/{candidate_id}/photo", status_code=status.HTTP_204_NO_CONTENT)
async def delete_candidate_photo(
    candidate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
    storage: StorageService = Depends(get_storage_service),
):
    """Delete a candidate's photo."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    storage.delete_photo(candidate_id)
    candidate.photo_url = None
    db.commit()


@router.delete("/candidates/{candidate_id}/resume", status_code=status.HTTP_204_NO_CONTENT)
async def delete_candidate_resume(
    candidate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_admin_user),
    storage: StorageService = Depends(get_storage_service),
):
    """Delete a candidate's resume."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    storage.delete_resume(candidate_id)
    candidate.resume_url = None
    db.commit()
```

**Step 2: Register uploads router**

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

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(public_router)
api_router.include_router(admin_companies_router, prefix="/admin")
api_router.include_router(admin_employers_router, prefix="/admin")
api_router.include_router(admin_candidates_router, prefix="/admin")
api_router.include_router(admin_jobs_router, prefix="/admin")
api_router.include_router(admin_stats_router, prefix="/admin")
api_router.include_router(admin_uploads_router, prefix="/admin")
```

**Step 3: Commit**

```bash
git add hiremenow-be/app/api/v1/admin/uploads.py hiremenow-be/app/api/v1/router.py
git commit -m "feat(api): add file upload endpoints for candidate photos and resumes"
```

---

## Task 4: Mount Static File Serving

**Files:**
- Modify: `hiremenow-be/app/main.py`

**Step 1: Add static file mounting**

```python
# hiremenow-be/app/main.py
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import get_settings
from app.api.v1.router import api_router

settings = get_settings()

app = FastAPI(
    title="HireMeNow API",
    description="Recruitment Agency Platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS
origins = [origin.strip() for origin in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)

# Mount uploads directory for static file serving
uploads_path = Path(settings.upload_dir)
uploads_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "environment": settings.environment}
```

**Step 2: Commit**

```bash
git add hiremenow-be/app/main.py
git commit -m "feat(api): mount static file serving for uploads"
```

---

## Task 5: Add Frontend Upload API

**Files:**
- Create: `hiremenow-fe/src/lib/api/uploads.ts`
- Modify: `hiremenow-fe/src/types/index.ts`

**Step 1: Add upload response type**

Add to `hiremenow-fe/src/types/index.ts`:

```typescript
export interface UploadResponse {
  url: string;
  message: string;
}
```

**Step 2: Create uploads API module**

```typescript
// hiremenow-fe/src/lib/api/uploads.ts
import api from '../api';
import type { UploadResponse } from '@/types';

export const uploadsApi = {
  uploadPhoto: async (candidateId: string, file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post(
      `/admin/uploads/candidates/${candidateId}/photo`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return response.data;
  },

  uploadResume: async (candidateId: string, file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post(
      `/admin/uploads/candidates/${candidateId}/resume`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return response.data;
  },

  deletePhoto: async (candidateId: string): Promise<void> => {
    await api.delete(`/admin/uploads/candidates/${candidateId}/photo`);
  },

  deleteResume: async (candidateId: string): Promise<void> => {
    await api.delete(`/admin/uploads/candidates/${candidateId}/resume`);
  },
};
```

**Step 3: Commit**

```bash
git add hiremenow-fe/src/lib/api/uploads.ts hiremenow-fe/src/types/index.ts
git commit -m "feat(frontend): add file upload API module"
```

---

## Task 6: Create Upload Hooks

**Files:**
- Create: `hiremenow-fe/src/hooks/use-uploads.ts`

**Step 1: Create upload hooks**

```typescript
// hiremenow-fe/src/hooks/use-uploads.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { uploadsApi } from '@/lib/api/uploads';
import { candidateKeys } from './use-candidates';

export function useUploadPhoto() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ candidateId, file }: { candidateId: string; file: File }) =>
      uploadsApi.uploadPhoto(candidateId, file),
    onSuccess: (_, { candidateId }) => {
      queryClient.invalidateQueries({ queryKey: candidateKeys.detail(candidateId) });
      queryClient.invalidateQueries({ queryKey: candidateKeys.lists() });
    },
  });
}

export function useUploadResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ candidateId, file }: { candidateId: string; file: File }) =>
      uploadsApi.uploadResume(candidateId, file),
    onSuccess: (_, { candidateId }) => {
      queryClient.invalidateQueries({ queryKey: candidateKeys.detail(candidateId) });
      queryClient.invalidateQueries({ queryKey: candidateKeys.lists() });
    },
  });
}

export function useDeletePhoto() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (candidateId: string) => uploadsApi.deletePhoto(candidateId),
    onSuccess: (_, candidateId) => {
      queryClient.invalidateQueries({ queryKey: candidateKeys.detail(candidateId) });
      queryClient.invalidateQueries({ queryKey: candidateKeys.lists() });
    },
  });
}

export function useDeleteResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (candidateId: string) => uploadsApi.deleteResume(candidateId),
    onSuccess: (_, candidateId) => {
      queryClient.invalidateQueries({ queryKey: candidateKeys.detail(candidateId) });
      queryClient.invalidateQueries({ queryKey: candidateKeys.lists() });
    },
  });
}
```

**Step 2: Commit**

```bash
git add hiremenow-fe/src/hooks/use-uploads.ts
git commit -m "feat(frontend): add upload mutation hooks"
```

---

## Task 7: Add File Upload UI to Candidate Detail

**Files:**
- Modify: `hiremenow-fe/src/components/admin/candidates/CandidateDetailDialog.tsx`

**Step 1: Read current CandidateDetailDialog**

First examine the current file structure.

**Step 2: Add file upload buttons to the dialog**

Add photo and resume upload buttons with file input handlers to the CandidateDetailDialog. Include:
- Photo upload with image preview
- Resume upload with download link
- Delete buttons for both
- Loading states during upload

The implementation should:
1. Import `useUploadPhoto`, `useUploadResume`, `useDeletePhoto`, `useDeleteResume` from hooks
2. Add hidden file inputs with refs
3. Add upload buttons that trigger file inputs
4. Show current photo as image, current resume as download link
5. Handle upload on file selection

**Step 3: Commit**

```bash
git add hiremenow-fe/src/components/admin/candidates/CandidateDetailDialog.tsx
git commit -m "feat(ui): add file upload UI to candidate detail dialog"
```

---

## Task 8: Install python-multipart dependency

**Files:**
- Modify: `hiremenow-be/requirements.txt` or `pyproject.toml`

**Step 1: Add python-multipart**

Run:
```bash
cd hiremenow-be && pip install python-multipart
```

Or add to requirements.txt:
```
python-multipart
```

**Step 2: Commit**

```bash
git add hiremenow-be/requirements.txt
git commit -m "chore(deps): add python-multipart for file uploads"
```

---

## Task 9: Verify and Test

**Step 1: Build frontend**

Run:
```bash
cd hiremenow-fe && npm run build
```

Expected: Build succeeds

**Step 2: Test backend imports**

Run:
```bash
cd hiremenow-be && python3 -c "from app.services.storage import StorageService; from app.api.v1.admin.uploads import router; print('OK')"
```

Expected: OK

**Step 3: Final commit**

```bash
git add . && git commit -m "feat: complete file storage implementation"
```

---

## Summary

This plan implements:
1. **Storage configuration** - Configurable upload directory and file size limits
2. **Storage service** - Local filesystem abstraction with photo/resume handling
3. **Upload endpoints** - POST/DELETE for photos and resumes
4. **Static file serving** - FastAPI StaticFiles for serving uploads
5. **Frontend API** - Upload functions with FormData
6. **Upload hooks** - React Query mutations with cache invalidation
7. **Upload UI** - File upload buttons in candidate detail dialog
