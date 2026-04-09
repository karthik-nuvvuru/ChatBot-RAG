"""Redis-based rate limiter implementation."""
import time
from typing import Tuple, Optional
from fastapi import HTTPException, status

from app.core.config import settings
from app.chat.redis_cache import get_redis


class RateLimiter:
    """Redis-based rate limiter for API endpoints."""

    def __init__(
        self,
        requests_per_minute: int = None,
        burst_size: int = None
    ):
        """Initialize rate limiter.

        Args:
            requests_per_minute: Max requests per minute
            burst_size: Max burst requests allowed
        """
        self.requests_per_minute = requests_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self.burst_size = burst_size or settings.RATE_LIMIT_BURST
        self.window = 60  # 1 minute window

    async def check_rate_limit(self, user_id: str) -> Tuple[bool, int]:
        """Check if user is within rate limits.

        Args:
            user_id: User identifier

        Returns:
            Tuple of (is_allowed, current_count)
        """
        redis = await get_redis()
        key = f"rate_limit:{user_id}"

        try:
            current = await redis.incr(key)

            if current == 1:
                await redis.expire(key, self.window)

            is_allowed = current <= self.requests_per_minute

            return is_allowed, current

        except Exception as e:
            # If Redis fails, allow the request but log the error
            import logging
            logging.getLogger("conversation_ai.rate_limiter").error(
                f"Rate limit check failed: {e}"
            )
            return True, 0

    async def consume_token(self, user_id: str) -> bool:
        """Consume a token from the rate limit bucket.

        Args:
            user_id: User identifier

        Returns:
            True if token consumed, False if rate limited
        """
        is_allowed, _ = await self.check_rate_limit(user_id)
        return is_allowed

    async def get_remaining(self, user_id: str) -> int:
        """Get remaining requests for user.

        Args:
            user_id: User identifier

        Returns:
            Number of remaining requests
        """
        redis = await get_redis()
        key = f"rate_limit:{user_id}"

        try:
            current = await redis.get(key)
            if current is None:
                return self.requests_per_minute

            remaining = max(0, self.requests_per_minute - int(current))
            return remaining

        except Exception:
            return self.requests_per_minute

    async def reset(self, user_id: str) -> None:
        """Reset rate limit for user.

        Args:
            user_id: User identifier
        """
        redis = await get_redis()
        key = f"rate_limit:{user_id}"
        await redis.delete(key)


async def check_rate_limit(user_id: str) -> None:
    """Check rate limit and raise exception if exceeded.

    Args:
        user_id: User identifier

    Raises:
        HTTPException: If rate limit exceeded
    """
    limiter = RateLimiter()
    is_allowed, count = await limiter.check_rate_limit(user_id)

    if not is_allowed:
        remaining = max(0, limiter.requests_per_minute - count)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "limit": limiter.requests_per_minute,
                "remaining": remaining,
                "retry_after": 60,
            },
            headers={
                "X-RateLimit-Limit": str(limiter.requests_per_minute),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": "60",
            }
        )


def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance."""
    return RateLimiter()