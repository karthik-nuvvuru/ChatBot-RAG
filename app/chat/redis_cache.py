"""Redis cache layer for session and message caching."""
import json
import logging
from typing import Optional, List, Any
import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger("conversation_ai.cache")

_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get Redis client instance.

    Returns:
        Redis client
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis():
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


class RedisCache:
    """Redis cache operations for session and message management."""

    def __init__(self, client: redis.Redis):
        self.client = client
        self.ttl = settings.REDIS_CACHE_TTL

    # Session context operations
    async def set_session_context(self, session_id: str, context: dict) -> bool:
        """Cache session context.

        Args:
            session_id: Session UUID
            context: Context dict

        Returns:
            True if successful
        """
        key = f"session:context:{session_id}"
        try:
            await self.client.setex(key, self.ttl, json.dumps(context))
            return True
        except Exception as e:
            logger.error(f"Failed to set session context: {e}")
            return False

    async def get_session_context(self, session_id: str) -> Optional[dict]:
        """Get cached session context.

        Args:
            session_id: Session UUID

        Returns:
            Context dict or None
        """
        key = f"session:context:{session_id}"
        try:
            data = await self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get session context: {e}")
            return None

    # Message caching
    async def cache_messages(self, session_id: str, messages: List[dict]) -> bool:
        """Cache session messages.

        Args:
            session_id: Session UUID
            messages: List of message dicts

        Returns:
            True if successful
        """
        key = f"session:messages:{session_id}"
        try:
            # Only keep last 100 messages in cache
            messages = messages[-100:] if len(messages) > 100 else messages
            await self.client.setex(key, self.ttl, json.dumps(messages))
            return True
        except Exception as e:
            logger.error(f"Failed to cache messages: {e}")
            return False

    async def get_cached_messages(self, session_id: str) -> Optional[List[dict]]:
        """Get cached session messages.

        Args:
            session_id: Session UUID

        Returns:
            List of message dicts or None
        """
        key = f"session:messages:{session_id}"
        try:
            data = await self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get cached messages: {e}")
            return None

    async def append_message(self, session_id: str, message: dict) -> bool:
        """Append a message to cached session messages.

        Args:
            session_id: Session UUID
            message: Message dict to append

        Returns:
            True if successful
        """
        key = f"session:messages:{session_id}"
        try:
            # Get existing cached messages (may be JSON string or None)
            existing = await self.client.get(key)
            messages = json.loads(existing) if existing else []
            if not isinstance(messages, list):
                messages = []
            messages.append(message)
            # Only keep last 100 messages
            messages = messages[-100:] if len(messages) > 100 else messages
            await self.client.setex(key, self.ttl, json.dumps(messages))
            return True
        except Exception as e:
            logger.error(f"Failed to append message to cache: {e}")
            return False

    async def invalidate_session(self, session_id: str) -> None:
        """Invalidate all cached data for a session.

        Args:
            session_id: Session UUID
        """
        try:
            # Use SCAN to find all keys for this session
            pattern = f"session:*:{session_id}"
            async for key in self.client.scan_iter(match=pattern, count=100):
                await self.client.delete(key)
        except Exception as e:
            logger.error(f"Failed to invalidate session: {e}")

    # Rate limiting
    async def set_user_rate_limit(self, user_id: str, window: int = 60) -> int:
        """Increment and check rate limit for user.

        Args:
            user_id: User identifier
            window: Time window in seconds

        Returns:
            Current request count
        """
        key = f"rate_limit:{user_id}"
        try:
            current = await self.client.incr(key)
            if current == 1:
                await self.client.expire(key, window)
            return current
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return 0

    async def get_user_rate_limit(self, user_id: str) -> int:
        """Get current rate limit count for user.

        Args:
            user_id: User identifier

        Returns:
            Current request count
        """
        key = f"rate_limit:{user_id}"
        try:
            value = await self.client.get(key)
            return int(value) if value else 0
        except Exception:
            return 0

    # Session activity tracking
    async def set_session_activity(self, session_id: str) -> bool:
        """Mark session as active.

        Args:
            session_id: Session UUID

        Returns:
            True if successful
        """
        key = f"session:activity:{session_id}"
        try:
            await self.client.setex(key, self.ttl, "1")
            return True
        except Exception as e:
            logger.error(f"Failed to set session activity: {e}")
            return False

    async def is_session_active(self, session_id: str) -> bool:
        """Check if session is marked as active.

        Args:
            session_id: Session UUID

        Returns:
            True if active
        """
        key = f"session:activity:{session_id}"
        try:
            return await self.client.exists(key) > 0
        except Exception:
            return False

    # Generic operations
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a generic cache value.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL in seconds

        Returns:
            True if successful
        """
        try:
            if ttl:
                await self.client.setex(key, ttl, json.dumps(value))
            else:
                await self.client.setex(key, self.ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.error(f"Failed to set cache: {e}")
            return False

    async def get(self, key: str) -> Optional[Any]:
        """Get a generic cache value.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        try:
            data = await self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get cache: {e}")
            return None

    async def delete(self, key: str) -> bool:
        """Delete a cache key.

        Args:
            key: Cache key

        Returns:
            True if deleted
        """
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache: {e}")
            return False


async def get_cache() -> RedisCache:
    """Get Redis cache instance.

    Returns:
        RedisCache instance
    """
    client = await get_redis()
    return RedisCache(client)