"""Progress streaming for action updates."""
import asyncio
import logging
from typing import Optional, AsyncGenerator
from datetime import datetime, timezone

from app.chat.websocket.connection_manager import connection_manager

logger = logging.getLogger("conversation_ai.ws.progress")


class ProgressStreamer:
    """Streams progress updates for long-running actions."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.manager = connection_manager
        self._last_update: float = 0
        self._update_interval: float = 1.0  # Throttle to 1 update per second

    async def stream_progress(
        self,
        action_id: str,
        progress: float,
        status: str,
        message: Optional[str] = None
    ) -> None:
        """Stream a progress update.

        Args:
            action_id: UUID of the action
            progress: Progress percentage (0-100)
            status: Current status string
            message: Optional status message
        """
        current_time = asyncio.get_event_loop().time()
        if current_time - self._last_update < self._update_interval:
            return

        self._last_update = current_time

        await self.manager.broadcast_to_session(
            self.session_id,
            "progress_update",
            {
                "action_id": action_id,
                "progress": progress,
                "status": status,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    async def stream_status(
        self,
        action_id: str,
        status: str,
        details: Optional[dict] = None
    ) -> None:
        """Stream a status change.

        Args:
            action_id: UUID of the action
            status: New status
            details: Optional additional details
        """
        await self.manager.broadcast_to_session(
            self.session_id,
            "status_update",
            {
                "action_id": action_id,
                "status": status,
                "details": details or {},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    async def stream_action_start(
        self,
        action_id: str,
        action_type: str,
        metadata: Optional[dict] = None
    ) -> None:
        """Stream action start event.

        Args:
            action_id: UUID of the action
            action_type: Type of action starting
            metadata: Optional action metadata
        """
        await self.manager.broadcast_to_session(
            self.session_id,
            "action_start",
            {
                "action_id": action_id,
                "action_type": action_type,
                "metadata": metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    async def stream_action_complete(
        self,
        action_id: str,
        result: dict,
        success: bool = True
    ) -> None:
        """Stream action completion event.

        Args:
            action_id: UUID of the action
            result: Action result data
            success: Whether action succeeded
        """
        await self.manager.broadcast_to_session(
            self.session_id,
            "action_complete",
            {
                "action_id": action_id,
                "success": success,
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

    async def stream_action_error(
        self,
        action_id: str,
        error: str,
        retryable: bool = True
    ) -> None:
        """Stream action error event.

        Args:
            action_id: UUID of the action
            error: Error message
            retryable: Whether the action can be retried
        """
        await self.manager.broadcast_to_session(
            self.session_id,
            "action_error",
            {
                "action_id": action_id,
                "error": error,
                "retryable": retryable,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


class ProgressGenerator:
    """Async generator for streaming progress updates."""

    def __init__(self, action_id: str, session_id: str):
        self.action_id = action_id
        self.session_id = session_id
        self.streamer = ProgressStreamer(session_id)

    async def generate(
        self,
        steps: list,
        interval: float = 0.5
    ) -> AsyncGenerator[dict, None]:
        """Generate progress updates for a multi-step action.

        Args:
            steps: List of step descriptions
            interval: Time between steps in seconds

        Yields:
            Progress update dicts
        """
        total_steps = len(steps)
        for i, step in enumerate(steps):
            progress = ((i + 1) / total_steps) * 100

            update = {
                "action_id": self.action_id,
                "step": i + 1,
                "total_steps": total_steps,
                "progress": progress,
                "status": step,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            await self.streamer.stream_progress(
                self.action_id,
                progress,
                step
            )

            yield update

            if i < total_steps - 1:
                await asyncio.sleep(interval)


async def stream_action_progress(
    action_id: str,
    session_id: str,
    steps: list
) -> AsyncGenerator[dict, None]:
    """Convenience function to stream action progress.

    Args:
        action_id: UUID of the action
        session_id: UUID of the session
        steps: List of step descriptions

    Yields:
        Progress update dicts
    """
    generator = ProgressGenerator(action_id, session_id)
    async for update in generator.generate(steps):
        yield update