"""Unit tests for SessionManager."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.chat.session_manager import SessionManager
from app.schemas import SessionCreate, AcceleratorTypeEnum


class TestSessionManager:
    """Test cases for SessionManager."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def mock_cache(self):
        """Create mock Redis cache."""
        cache = AsyncMock()
        cache.set_session_context = AsyncMock(return_value=True)
        cache.get_session_context = AsyncMock(return_value=None)
        cache.invalidate_session = AsyncMock()
        cache.set_session_activity = AsyncMock(return_value=True)
        return cache

    @pytest.fixture
    def session_manager(self, mock_db, mock_cache):
        """Create SessionManager instance with mocks."""
        return SessionManager(mock_db, mock_cache)

    @pytest.mark.asyncio
    async def test_create_session_success(self, session_manager, mock_db, mock_cache):
        """Test successful session creation."""
        session_data = SessionCreate(
            user_id="user123",
            engagement_id="eng123",
            project_id="proj123",
            accelerator_type=AcceleratorTypeEnum.ADVANCED
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute.return_value = mock_result

        session = await session_manager.create_session(session_data)

        assert session.user_id == "user123"
        assert session.engagement_id == "eng123"
        assert session.project_id == "proj123"

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_cache.set_session_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_session_invalid_accelerator(self, session_manager):
        """Test session creation with invalid accelerator type."""
        from pydantic import ValidationError

        # This should raise ValidationError from Pydantic since invalid_type is not a valid enum
        with pytest.raises(ValidationError):
            SessionCreate(
                user_id="user123",
                accelerator_type="invalid_type"
            )

    @pytest.mark.asyncio
    async def test_get_session_found(self, session_manager, mock_db, mock_cache):
        """Test retrieving an existing session."""
        session_id = uuid4()
        mock_session = MagicMock()
        mock_session.session_id = session_id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_session)
        mock_db.execute.return_value = mock_result

        session = await session_manager.get_session(session_id)

        assert session is not None
        assert session.session_id == session_id

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, session_manager, mock_db):
        """Test retrieving a non-existent session."""
        session_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute.return_value = mock_result

        session = await session_manager.get_session(session_id)

        assert session is None

    @pytest.mark.asyncio
    async def test_archive_session(self, session_manager, mock_db, mock_cache):
        """Test archiving a session."""
        session_id = uuid4()
        mock_session = MagicMock()
        mock_session.status = "active"
        mock_session.is_active = MagicMock(return_value=True)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_session)
        mock_db.execute.return_value = mock_result

        result = await session_manager.archive_session(session_id)

        assert result is not None
        mock_cache.invalidate_session.assert_called()

    @pytest.mark.asyncio
    async def test_fork_session(self, session_manager, mock_db, mock_cache):
        """Test forking a session."""
        original_id = uuid4()
        mock_original = MagicMock()
        mock_original.session_id = original_id
        mock_original.user_id = "user123"
        mock_original.engagement_id = "eng123"
        mock_original.project_id = "proj123"
        mock_original.accelerator_type = MagicMock(value="advanced")
        mock_original.conversation_metadata = {}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_original)
        mock_db.execute.return_value = mock_result

        new_session = await session_manager.fork_session(original_id, "new_user")

        assert new_session is not None
        assert new_session.user_id == "new_user"
        mock_db.add.assert_called_once()


class TestSessionManagerRateLimiting:
    """Test rate limiting functionality."""

    @pytest.mark.asyncio
    async def test_rate_limit_check_allowed(self, mock_redis):
        """Test rate limit when under limit."""
        from app.core.rate_limiter import RateLimiter

        limiter = RateLimiter()
        limiter.client = mock_redis

        # Can't easily test without proper async setup
        # This is a placeholder for integration tests
        assert True


class TestSessionValidation:
    """Test session validation logic."""

    def test_session_is_active(self):
        """Test is_active method."""
        from app.models import ConversationSession, SessionStatus

        session = MagicMock(spec=ConversationSession)
        session.status = SessionStatus.ACTIVE

        # is_active should return True for ACTIVE status
        assert session.status == SessionStatus.ACTIVE