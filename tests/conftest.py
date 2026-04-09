"""Pytest configuration and fixtures."""
import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture(scope="function")
def event_loop():
    """Create function-scoped event loop for async tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    client = MagicMock()
    client.get = AsyncMock(return_value=None)
    client.setex = AsyncMock(return_value=True)
    client.delete = AsyncMock()
    client.incr = AsyncMock(return_value=1)
    client.expire = AsyncMock()
    client.ping = AsyncMock(return_value=True)
    client.pipeline = MagicMock(return_value=MagicMock(
        rpush=AsyncMock(),
        expire=AsyncMock(),
        execute=AsyncMock()
    ))
    client.scan_iter = AsyncMock(return_value=iter([]))
    return client


@pytest.fixture
def sample_user():
    """Create sample user data."""
    return {
        "sub": "user123",
        "email": "user@example.com",
        "roles": ["user"]
    }


@pytest.fixture
def sample_session_data():
    """Create sample session creation data."""
    return {
        "user_id": "user123",
        "engagement_id": "eng123",
        "project_id": "proj123",
        "accelerator_type": "basic"
    }


@pytest.fixture
def sample_message_data():
    """Create sample message data."""
    return {
        "role": "user",
        "content": "Hello, how are you?"
    }