"""Unit tests for MessageService."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.chat.message_service import MessageService
from app.schemas import MessageCreate, MessageRoleEnum


class TestMessageService:
    """Test cases for MessageService."""

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
        cache.get_cached_messages = AsyncMock(return_value=None)
        cache.append_message = AsyncMock(return_value=True)
        cache.cache_messages = AsyncMock(return_value=True)
        return cache

    @pytest.fixture
    def message_service(self, mock_db, mock_cache):
        """Create MessageService instance with mocks."""
        return MessageService(mock_db, mock_cache)

    @pytest.mark.asyncio
    async def test_add_message_success(self, message_service, mock_db, mock_cache):
        """Test adding a valid message."""
        session_id = uuid4()
        message_data = MessageCreate(
            role=MessageRoleEnum.USER,
            content="Hello, how are you?"
        )

        mock_session = MagicMock()
        mock_session.is_active = MagicMock(return_value=True)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_session)
        mock_db.execute.return_value = mock_result

        message = await message_service.add_message(session_id, message_data)

        assert message is not None
        assert message.content == "Hello, how are you?"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_message_session_not_found(self, message_service, mock_db):
        """Test adding message to non-existent session."""
        session_id = uuid4()
        message_data = MessageCreate(
            role=MessageRoleEnum.USER,
            content="Hello"
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Session .* not found"):
            await message_service.add_message(session_id, message_data)

    @pytest.mark.asyncio
    async def test_add_message_session_inactive(self, message_service, mock_db):
        """Test adding message to inactive session."""
        session_id = uuid4()
        message_data = MessageCreate(
            role=MessageRoleEnum.USER,
            content="Hello"
        )

        mock_session = MagicMock()
        mock_session.is_active = MagicMock(return_value=False)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_session)
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="not active"):
            await message_service.add_message(session_id, message_data)

    @pytest.mark.asyncio
    async def test_count_session_messages(self, message_service, mock_db):
        """Test counting session messages."""
        session_id = uuid4()

        # Configure the execute result to return the count directly
        mock_result = MagicMock()
        mock_result.scalar = MagicMock(return_value=10)

        mock_db.execute.return_value = mock_result

        count = await message_service.count_session_messages(session_id)

        assert count == 10

    @pytest.mark.asyncio
    async def test_search_messages(self, message_service, mock_db):
        """Test searching messages."""
        session_id = uuid4()
        query = "hello"

        mock_messages = [
            MagicMock(message_id=uuid4(), content="Hello there!")
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_messages
        mock_db.execute.return_value = mock_result

        results = await message_service.search_messages(session_id, query)

        assert len(results) == 1


class TestMessageValidation:
    """Test message validation."""

    def test_message_content_length(self):
        """Test message content length validation."""
        message_data = MessageCreate(
            role=MessageRoleEnum.USER,
            content="Hello"
        )

        assert len(message_data.content) <= 10000

    def test_message_role_enum(self):
        """Test message role enum values."""
        assert MessageRoleEnum.USER.value == "user"
        assert MessageRoleEnum.ASSISTANT.value == "assistant"
        assert MessageRoleEnum.SYSTEM.value == "system"