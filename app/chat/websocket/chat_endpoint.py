"""WebSocket chat endpoint handler."""
import uuid
import logging
from typing import Optional
from fastapi import WebSocket, WebSocketDisconnect, Query, Path

from app.chat.websocket.connection_manager import connection_manager
from app.core.security import validate_token
from app.db.session import AsyncSessionLocal
from app.chat.redis_cache import get_cache
from app.chat.orchestrator import ChatOrchestrator

logger = logging.getLogger("conversation_ai.ws.chat")


class ChatWebSocketHandler:
    """Handles WebSocket chat connections and message routing."""

    def __init__(self):
        self.manager = connection_manager

    async def authenticate(self, token: Optional[str]) -> Optional[dict]:
        """Authenticate WebSocket connection using JWT.

        Args:
            token: JWT token from query parameter

        Returns:
            User dict if authenticated, None otherwise
        """
        if not token:
            return None

        try:
            return validate_token(token)
        except Exception:
            return None

    async def handle_message(
        self,
        websocket: WebSocket,
        session_id: str,
        user_id: str,
        message: dict
    ) -> None:
        """Handle incoming WebSocket message.

        Args:
            websocket: WebSocket connection
            session_id: Target session UUID
            user_id: User identifier
            message: Message dict
        """
        msg_type = message.get("type", "")

        if msg_type == "user_message":
            await self._handle_user_message(websocket, session_id, user_id, message)
        elif msg_type == "typing_start":
            await self.manager.send_typing_indicator(session_id, user_id, True)
        elif msg_type == "typing_stop":
            await self.manager.send_typing_indicator(session_id, user_id, False)
        elif msg_type == "ping":
            await self.manager.update_heartbeat(websocket)
            await self.manager.send_message(websocket, {"type": "pong"})
        else:
            await self.manager.send_error(
                websocket,
                "UNKNOWN_MESSAGE_TYPE",
                f"Unknown message type: {msg_type}"
            )

    async def _handle_user_message(
        self,
        websocket: WebSocket,
        session_id: str,
        user_id: str,
        message: dict
    ) -> None:
        """Handle user message - process via orchestrator.

        Args:
            websocket: WebSocket connection
            session_id: Target session UUID
            user_id: User identifier
            message: Message dict with 'content'
        """
        content = message.get("content", "")

        logger.info(f"WebSocket message received: type={message.get('type')}, content length={len(content) if content else 0}, content={repr(content[:100]) if content else 'None'}")

        if not content:
            await self.manager.send_error(
                websocket,
                "EMPTY_MESSAGE",
                "Message content cannot be empty"
            )
            return

        # Send typing indicator
        await self.manager.send_typing_indicator(session_id, user_id, True)

        # Send acknowledgment
        await self.manager.send_message(
            websocket,
            {
                "type": "message_received",
                "payload": {"content": content[:100]},
                "timestamp": message.get("timestamp")
            }
        )

        # Create orchestrator and process message
        async with AsyncSessionLocal() as db:
            cache = await get_cache()
            orchestrator = ChatOrchestrator(db, cache)

            async def stream_callback(chunk: str):
                """Stream chunks back to client."""
                await self.manager.send_message(
                    websocket,
                    {
                        "type": "stream_chunk",
                        "payload": {"content": chunk},
                        "done": False
                    }
                )

            try:
                from app.schemas import ChatRequest
                request = ChatRequest(
                    session_id=uuid.UUID(session_id),
                    message=content,
                    stream=message.get("stream", True)
                )
                result = await orchestrator.process_message(request, stream_callback)

                # Send completion
                await self.manager.send_message(
                    websocket,
                    {
                        "type": "message_complete",
                        "payload": {
                            "message_id": str(result.message_id),
                            "content": result.content,
                        },
                        "done": True
                    }
                )

            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await self.manager.send_error(
                    websocket,
                    "PROCESSING_ERROR",
                    f"Failed to process message: {str(e)}"
                )

        # Send typing stopped
        await self.manager.send_typing_indicator(session_id, user_id, False)

    async def handle_disconnect(self, websocket: WebSocket) -> None:
        """Handle WebSocket disconnection."""
        await self.manager.disconnect(websocket)


ws_handler = ChatWebSocketHandler()


async def websocket_chat_endpoint(
    websocket: WebSocket,
    session_id: str = Path(...),
    token: Optional[str] = Query(None)
):
    """WebSocket endpoint for real-time chat.

    Query Params:
        session_id: UUID of the session to connect to
        token: JWT access token for authentication

    Path: ws://api/v1/chat/sessions/{session_id}/ws
    """
    user = await ws_handler.authenticate(token)
    if not user:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    connected = await ws_handler.manager.connect(
        websocket,
        session_id,
        user["sub"]
    )

    if not connected:
        await websocket.close(code=4002, reason="Connection failed")
        return

    try:
        while True:
            data = await websocket.receive_json()
            await ws_handler.handle_message(
                websocket,
                session_id,
                user["sub"],
                data
            )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: session={session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await ws_handler.handle_disconnect(websocket)