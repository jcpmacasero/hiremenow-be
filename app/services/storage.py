import uuid
import shutil
from pathlib import Path
from typing import Optional

from fastapi import UploadFile, HTTPException, status

from app.config import get_settings


class StorageService:
    """Service for handling file storage operations."""

    def __init__(self, base_path: str):
        """Initialize storage service with base path for uploads.

        Args:
            base_path: Base directory path for file storage
        """
        self.base_path = Path(base_path)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create photos/, resumes/, and documents/ subdirectories if they don't exist."""
        photos_dir = self.base_path / "photos"
        resumes_dir = self.base_path / "resumes"
        documents_dir = self.base_path / "documents"

        photos_dir.mkdir(parents=True, exist_ok=True)
        resumes_dir.mkdir(parents=True, exist_ok=True)
        documents_dir.mkdir(parents=True, exist_ok=True)

    def _get_extension(self, filename: str) -> str:
        """Extract file extension from filename.

        Args:
            filename: Original filename

        Returns:
            File extension including the dot (e.g., '.jpg')
        """
        if not filename:
            return ""
        path = Path(filename)
        return path.suffix.lower()

    def _validate_file_size(self, file: UploadFile) -> None:
        """Validate file size against maximum allowed size.

        Args:
            file: Uploaded file to validate

        Raises:
            HTTPException: 413 if file exceeds max_file_size_mb
        """
        settings = get_settings()
        max_size_bytes = settings.max_file_size_mb * 1024 * 1024

        # Read file to check size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        if file_size > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {settings.max_file_size_mb}MB"
            )

    def _validate_content_type(self, content_type: Optional[str], allowed_types: str) -> None:
        """Validate content type against allowed types.

        Args:
            content_type: MIME type of the uploaded file
            allowed_types: Comma-separated string of allowed MIME types

        Raises:
            HTTPException: 415 if content type is not allowed
        """
        if not content_type:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Content type not provided"
            )

        allowed_list = [t.strip() for t in allowed_types.split(",")]

        if content_type not in allowed_list:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Content type '{content_type}' not allowed. Allowed types: {', '.join(allowed_list)}"
            )

    async def save_photo(self, file: UploadFile, candidate_id: uuid.UUID) -> str:
        """Save a candidate photo.

        Args:
            file: Uploaded photo file
            candidate_id: UUID of the candidate

        Returns:
            URL path to the saved photo

        Raises:
            HTTPException: 413 if file too large, 415 if invalid content type
        """
        settings = get_settings()

        # Validate file
        self._validate_file_size(file)
        self._validate_content_type(file.content_type, settings.allowed_image_types)

        # Get extension and build file path
        extension = self._get_extension(file.filename or "")
        if not extension:
            extension = ".jpg"  # Default extension for photos

        filename = f"{candidate_id}{extension}"
        file_path = self.base_path / "photos" / filename

        # Delete any existing photos for this candidate
        self.delete_photo(candidate_id)

        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return f"/uploads/photos/{filename}"

    async def save_resume(self, file: UploadFile, candidate_id: uuid.UUID) -> str:
        """Save a candidate resume.

        Args:
            file: Uploaded resume file
            candidate_id: UUID of the candidate

        Returns:
            URL path to the saved resume

        Raises:
            HTTPException: 413 if file too large, 415 if invalid content type
        """
        settings = get_settings()

        # Validate file
        self._validate_file_size(file)
        self._validate_content_type(file.content_type, settings.allowed_resume_types)

        # Get extension and build file path
        extension = self._get_extension(file.filename or "")
        if not extension:
            extension = ".pdf"  # Default extension for resumes

        filename = f"{candidate_id}{extension}"
        file_path = self.base_path / "resumes" / filename

        # Delete any existing resumes for this candidate
        self.delete_resume(candidate_id)

        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return f"/uploads/resumes/{filename}"

    def delete_photo(self, candidate_id: uuid.UUID) -> None:
        """Delete all photo files for a candidate.

        Args:
            candidate_id: UUID of the candidate
        """
        photos_dir = self.base_path / "photos"
        pattern = f"{candidate_id}.*"

        for file_path in photos_dir.glob(pattern):
            file_path.unlink()

    def delete_resume(self, candidate_id: uuid.UUID) -> None:
        """Delete all resume files for a candidate.

        Args:
            candidate_id: UUID of the candidate
        """
        resumes_dir = self.base_path / "resumes"
        pattern = f"{candidate_id}.*"

        for file_path in resumes_dir.glob(pattern):
            file_path.unlink()

    async def save_document(
        self, file: UploadFile, candidate_id: uuid.UUID, document_id: uuid.UUID
    ) -> tuple[str, int]:
        """Save a candidate document (passport, certificate, etc.).

        Args:
            file: Uploaded file
            candidate_id: UUID of the candidate
            document_id: UUID of the document record

        Returns:
            Tuple of (URL path to the saved file, file_size in bytes)
        """
        settings = get_settings()
        self._validate_file_size(file)
        allowed = f"{settings.allowed_image_types},{settings.allowed_resume_types}"
        self._validate_content_type(file.content_type, allowed)

        extension = self._get_extension(file.filename or "")
        if not extension:
            extension = ".pdf"

        candidate_dir = self.base_path / "documents" / str(candidate_id)
        candidate_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{document_id}{extension}"
        file_path = candidate_dir / filename

        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return f"/uploads/documents/{candidate_id}/{filename}", file_size


# Singleton instance
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Get or create the singleton StorageService instance.

    Returns:
        StorageService instance configured with settings from config
    """
    global _storage_service

    if _storage_service is None:
        settings = get_settings()
        _storage_service = StorageService(settings.upload_dir)

    return _storage_service
