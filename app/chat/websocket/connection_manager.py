"""WebSocket connection manager for real-time chat."""
import uuid
import logging
from typing import Dict, Set, Optional
from datetime import datetime, timezone
from fastapi import WebSocket

logger = logging.getLogger("conversation_ai.ws.connection")


class ConnectionManager:
    """Manages WebSocket connections for chat sessions."""

    def __init__(self):
        # session_id -> set of websocket connections
        self._session_connections: Dict[str, Set[WebSocket]] = {}
        # websocket -> (session_id, user_id) mapping
        self._connection_info: Dict[WebSocket, tuple] = {}
        # heartbeat tracking
        self._last_heartbeat: Dict[WebSocket, datetime] = {}

    async def connect(
        self,
        websocket: WebSocket,
        session_id: str,
        user_id: str
    ) -> bool:
        """Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            session_id: Session UUID string
            user_id: User identifier

        Returns:
            True if connection successful
        """
        try:
            await websocket.accept()

            if session_id not in self._session_connections:
                self._session_connections[session_id] = set()

            self._session_connections[session_id].add(websocket)
            self._connection_info[websocket] = (session_id, user_id)
            self._last_heartbeat[websocket] = datetime.now(timezone.utc)

            logger.info(f"WebSocket connected: session={session_id}, user={user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to accept WebSocket connection: {e}")
            return False

    async def disconnect(self, websocket: WebSocket) -> Optional[str]:
        """Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove

        Returns:
            Session_id that was disconnected from, or None
        """
        info = self._connection_info.pop(websocket, None)
        if info:
            session_id, _ = info
            if session_id in self._session_connections:
                self._session_connections[session_id].discard(websocket)
                if not self._session_connections[session_id]:
                    del self._session_connections[session_id]

        self._last_heartbeat.pop(websocket, None)

        if info:
            logger.info(f"WebSocket disconnected: session={info[0]}")
            return info[0]
        return None

    async def send_message(self, websocket: WebSocket, message: dict) -> bool:
        """Send a message to a specific WebSocket.

        Args:
            websocket: Target WebSocket
            message: Message dict to send

        Returns:
            True if sent successfully
        """
        try:
            await websocket.send_json(message)
            return True
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            await self.disconnect(websocket)
            return False

    async def send_to_session(
        self,
        session_id: str,
        message: dict,
        exclude: Optional[WebSocket] = None
    ) -> int:
        """Broadcast a message to all connections in a session.

        Args:
            session_id: Target session UUID
            message: Message dict to send
            exclude: Optional WebSocket to exclude

        Returns:
            Number of messages sent
        """
        if session_id not in self._session_connections:
            return 0

        sent_count = 0
        dead_connections = []

        for websocket in self._session_connections[session_id]:
            if websocket != exclude:
                success = await self.send_message(websocket, message)
                if success:
                    sent_count += 1
                else:
                    dead_connections.append(websocket)

        for ws in dead_connections:
            await self.disconnect(ws)

        return sent_count

    async def broadcast_to_session(
        self,
        session_id: str,
        message_type: str,
        payload: dict
    ) -> int:
        """Broadcast a typed message to all session connections.

        Args:
            session_id: Target session UUID
            message_type: Type of message
            payload: Message payload

        Returns:
            Number of broadcasts sent
        """
        message = {
            "type": message_type,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        return await self.send_to_session(session_id, message)

    def get_session_connection_count(self, session_id: str) -> int:
        """Get number of active connections for a session.

        Args:
            session_id: Target session UUID

        Returns:
            Connection count
        """
        return len(self._session_connections.get(session_id, set()))

    def get_total_connection_count(self) -> int:
        """Get total number of active connections.

        Returns:
            Total connection count
        """
        return len(self._connection_info)

    async def update_heartbeat(self, websocket: WebSocket) -> None:
        """Update heartbeat timestamp for a connection."""
        self._last_heartbeat[websocket] = datetime.now(timezone.utc)

    def is_alive(self, websocket: WebSocket, timeout_seconds: int = 30) -> bool:
        """Check if a connection is still alive based on heartbeat.

        Args:
            websocket: WebSocket to check
            timeout_seconds: Heartbeat timeout threshold

        Returns:
            True if connection is alive
        """
        last_heartbeat = self._last_heartbeat.get(websocket)
        if not last_heartbeat:
            return False

        elapsed = (datetime.now(timezone.utc) - last_heartbeat).total_seconds()
        return elapsed < timeout_seconds

    async def send_typing_indicator(
        self,
        session_id: str,
        user_id: str,
        is_typing: bool
    ) -> int:
        """Send typing indicator to session.

        Args:
            session_id: Target session UUID
            user_id: User who is/isn't typing
            is_typing: Whether user is typing

        Returns:
            Number of indicators sent
        """
        return await self.broadcast_to_session(
            session_id,
            "typing_indicator",
            {"user_id": user_id, "is_typing": is_typing}
        )

    async def send_progress_update(
        self,
        session_id: str,
        progress: float,
        status: str,
        message: Optional[str] = None
    ) -> int:
        """Send progress update to session.

        Args:
            session_id: Target session UUID
            progress: Progress percentage (0-100)
            status: Status string
            message: Optional status message

        Returns:
            Number of updates sent
        """
        return await self.broadcast_to_session(
            session_id,
            "progress_update",
            {"progress": progress, "status": status, "message": message}
        )

    async def send_error(
        self,
        websocket: WebSocket,
        error_code: str,
        message: str,
        retry_after: Optional[int] = None
    ) -> bool:
        """Send error message to a specific connection.

        Args:
            websocket: Target WebSocket
            error_code: Error code string
            message: Error message
            retry_after: Optional retry hint in seconds

        Returns:
            True if sent successfully
        """
        return await self.send_message(
            websocket,
            {
                "type": "error",
                "payload": {
                    "code": error_code,
                    "message": message,
                    "retry_after": retry_after
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    def get_connection_info(self, websocket: WebSocket) -> Optional[tuple]:
        """Get connection info (session_id, user_id).

        Args:
            websocket: WebSocket connection

        Returns:
            Tuple of (session_id, user_id) or None
        """
        return self._connection_info.get(websocket)


# Global connection manager instance
connection_manager = ConnectionManager()