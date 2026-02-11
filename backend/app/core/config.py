"""
Application configuration settings.
"""

from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Basic
    PROJECT_NAME: str = "AI Vision Platform"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./ai_vision.db"
    # DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/ai_vision"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Media Server
    MEDIA_SERVER_URL: str = "http://localhost:8554"  # MediaMTX default port
    
    # AI Inference
    INFERENCE_SERVER_URL: str = "http://localhost:8001"  # Triton or custom inference server
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
