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
