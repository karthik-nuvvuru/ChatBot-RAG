"""Cache configuration for Redis session and message caching."""
import os
from typing import Optional


class CacheConfig:
    """Redis cache configuration."""

    # Redis connection URL
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Cache TTLs (in seconds)
    SESSION_CONTEXT_TTL: int = int(os.getenv("CACHE_SESSION_TTL", "86400"))  # 24 hours
    MESSAGE_CACHE_TTL: int = int(os.getenv("CACHE_MESSAGE_TTL", "86400"))  # 24 hours
    SESSION_ACTIVITY_TTL: int = int(os.getenv("CACHE_ACTIVITY_TTL", "3600"))  # 1 hour
    RATE_LIMIT_WINDOW: int = int(os.getenv("CACHE_RATE_LIMIT_WINDOW", "60"))  # 1 minute

    # Cache limits
    MAX_CACHED_MESSAGES: int = int(os.getenv("CACHE_MAX_MESSAGES", "100"))
    MAX_CONTEXT_SIZE_BYTES: int = int(os.getenv("CACHE_MAX_CONTEXT_SIZE", str(100 * 1024)))  # 100KB

    # Feature flags
    ENABLE_CACHE: bool = os.getenv("ENABLE_CONVERSATION_CACHE", "true").lower() == "true"
    ENABLE_MESSAGE_CACHE: bool = os.getenv("ENABLE_MESSAGE_CACHE", "true").lower() == "true"
    ENABLE_RATE_LIMITING: bool = os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"

    # Rate limiting
    MAX_REQUESTS_PER_WINDOW: int = int(os.getenv("CACHE_MAX_REQUESTS", "100"))
    MAX_SESSION_CREATIONS_PER_HOUR: int = int(os.getenv("MAX_SESSION_CREATIONS", "10"))

    # Connection pool settings
    REDIS_POOL_SIZE: int = int(os.getenv("REDIS_POOL_SIZE", "10"))
    REDIS_POOL_TIMEOUT: int = int(os.getenv("REDIS_POOL_TIMEOUT", "10"))


# Singleton instance
_cache_config: Optional[CacheConfig] = None


def get_cache_config() -> CacheConfig:
    """Get cache configuration instance.

    Returns:
        CacheConfig singleton
    """
    global _cache_config
    if _cache_config is None:
        _cache_config = CacheConfig()
    return _cache_config
