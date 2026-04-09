"""WebSocket package initialization."""
from app.chat.websocket.connection_manager import connection_manager
from app.chat.websocket.error_handler import error_handler

__all__ = ["connection_manager", "error_handler"]