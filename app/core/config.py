"""Application configuration using Pydantic Settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Application
    APP_NAME: str = "Conversation AI Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENV: str = "dev"

    # LLM Provider
    LLM_PROVIDER: str = "euri"  # "euri" or "azure"

    # EURI API (Development)
    EURI_API_KEY: str = ""
    EURI_BASE_URL: str = "https://api.euri.ai/v1"
    EURI_MODEL: str = "claude-sonnet-4-20250514"

    # Azure OpenAI (Production)
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_KEY: str = ""
    AZURE_DEPLOYMENT_NAME: str = "gpt-4o"
    AZURE_API_VERSION: str = "2024-02-01"
    AZURE_EMBEDDING_DEPLOYMENT: str = "text-embedding-ada-002"
    AZURE_EMBEDDING_DIMENSIONS: int = 1536

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/conversation_ai"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 86400  # 24 hours

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # Security
    JWT_SECRET_KEY: str = "change-this-secret-key-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 120
    RATE_LIMIT_BURST: int = 20

    # Session Settings
    SESSION_INACTIVITY_THRESHOLD_DAYS: int = 7
    SESSION_ARCHIVE_BATCH_SIZE: int = 100

    # Message Settings
    MESSAGE_MAX_LENGTH: int = 10000
    CONTEXT_WINDOW_SIZE: int = 20
    SUMMARY_THRESHOLD_MESSAGES: int = 50

    # Attachment Settings
    MAX_ATTACHMENT_SIZE_MB: int = 10
    ATTACHMENT_CLEANUP_DAYS: int = 90
    USE_LOCAL_STORAGE: bool = True
    LOCAL_STORAGE_PATH: str = "./storage/attachments"

    # Azure Blob Storage
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_CONTAINER_NAME: str = "attachments"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def is_production(self) -> bool:
        return self.ENV == "prod"

    @property
    def is_development(self) -> bool:
        return self.ENV == "dev"

    @property
    def llm_provider_type(self) -> str:
        return self.LLM_PROVIDER.lower()


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()