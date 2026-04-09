"""Unit tests for ConnectionManager."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import WebSocket
from datetime import datetime, timezone

from app.chat.websocket.connection_manager import ConnectionManager


@pytest.fixture
def manager():
    """Create fresh ConnectionManager instance."""
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket."""
    ws = MagicMock(spec=WebSocket)
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.close = AsyncMock()
    return ws


class TestConnectionManager:
    """Test cases for ConnectionManager."""

    @pytest.mark.asyncio
    async def test_connect_success(self, manager, mock_websocket):
        """Test successful WebSocket connection."""
        result = await manager.connect(
            mock_websocket,
            "session-123",
            "user-456"
        )

        assert result is True
        mock_websocket.accept.assert_called_once()
        assert manager.get_session_connection_count("session-123") == 1

    @pytest.mark.asyncio
    async def test_disconnect(self, manager, mock_websocket):
        """Test WebSocket disconnection."""
        await manager.connect(mock_websocket, "session-123", "user-456")
        await manager.disconnect(mock_websocket)

        assert manager.get_session_connection_count("session-123") == 0

    @pytest.mark.asyncio
    async def test_send_message_success(self, manager, mock_websocket):
        """Test sending a message."""
        await manager.connect(mock_websocket, "session-123", "user-456")

        result = await manager.send_message(
            mock_websocket,
            {"type": "test", "data": "hello"}
        )

        assert result is True
        mock_websocket.send_json.assert_called()

    @pytest.mark.asyncio
    async def test_send_to_session(self, manager, mock_websocket):
        """Test broadcasting to session."""
        await manager.connect(mock_websocket, "session-123", "user-456")

        count = await manager.send_to_session(
            "session-123",
            {"type": "broadcast"}
        )

        assert count == 1

    @pytest.mark.asyncio
    async def test_send_to_nonexistent_session(self, manager):
        """Test broadcasting to non-existent session."""
        count = await manager.send_to_session(
            "nonexistent-session",
            {"type": "test"}
        )

        assert count == 0

    @pytest.mark.asyncio
    async def test_broadcast_to_session(self, manager, mock_websocket):
        """Test broadcasting message type to session."""
        await manager.connect(mock_websocket, "session-123", "user-456")

        count = await manager.broadcast_to_session(
            "session-123",
            "user_message",
            {"content": "Hello"}
        )

        assert count == 1

    @pytest.mark.asyncio
    async def test_get_connection_counts(self, manager, mock_websocket):
        """Test connection count tracking."""
        await manager.connect(mock_websocket, "session-123", "user-456")

        assert manager.get_session_connection_count("session-123") == 1
        assert manager.get_total_connection_count() == 1

    @pytest.mark.asyncio
    async def test_send_typing_indicator(self, manager, mock_websocket):
        """Test sending typing indicator."""
        await manager.connect(mock_websocket, "session-123", "user-456")

        count = await manager.send_typing_indicator("session-123", "user-456", True)

        assert count == 1

    @pytest.mark.asyncio
    async def test_send_progress_update(self, manager, mock_websocket):
        """Test sending progress update."""
        await manager.connect(mock_websocket, "session-123", "user-456")

        count = await manager.send_progress_update(
            "session-123",
            progress=50.0,
            status="processing",
            message="Working..."
        )

        assert count == 1


class TestConnectionManagerErrorHandling:
    """Test error handling in ConnectionManager."""

    @pytest.mark.asyncio
    async def test_send_message_failure(self, manager, mock_websocket):
        """Test handling send message failure."""
        await manager.connect(mock_websocket, "session-123", "user-456")
        mock_websocket.send_json.side_effect = Exception("Send failed")

        result = await manager.send_message(
            mock_websocket,
            {"type": "test"}
        )

        assert result is False