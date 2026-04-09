"""Session management service with caching and rate limiting."""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ConversationSession
from app.schemas import SessionCreate, SessionUpdate
from app.models import SessionStatus
from app.chat.redis_cache import RedisCache
from app.core.config import settings

logger = logging.getLogger("conversation_ai.session")


class SessionManager:
    """Manages conversation sessions with async DB operations and caching."""

    def __init__(self, db: AsyncSession, cache: RedisCache):
        self.db = db
        self.cache = cache

    async def create_session(self, session_data: SessionCreate) -> ConversationSession:
        """Create a new conversation session.

        Args:
            session_data: Session creation data

        Returns:
            Created ConversationSession instance

        Raises:
            ValueError: If accelerator_type is invalid
        """
        try:
            accelerator = session_data.accelerator_type.value
        except ValueError:
            raise ValueError(f"Invalid accelerator_type: {session_data.accelerator_type}")

        session = ConversationSession(
            session_id=uuid.uuid4(),
            user_id=session_data.user_id,
            engagement_id=session_data.engagement_id,
            project_id=session_data.project_id,
            accelerator_type=accelerator,
            conversation_metadata=session_data.conversation_metadata or {},
            started_at=datetime.utcnow(),
            last_active_at=datetime.utcnow(),
            status="active",
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        # Cache session context
        await self.cache.set_session_context(
            str(session.session_id),
            {
                "user_id": session.user_id,
                "status": session.status.value if hasattr(session.status, 'value') else session.status,
                "accelerator_type": session.accelerator_type.value if hasattr(session.accelerator_type, 'value') else session.accelerator_type,
                "started_at": session.started_at.isoformat() if session.started_at else None,
            }
        )

        logger.info(f"Created session {session.session_id} for user {session.user_id}")
        return session

    async def get_session(self, session_id: uuid.UUID) -> Optional[ConversationSession]:
        """Get a session by ID.

        Args:
            session_id: UUID of the session

        Returns:
            ConversationSession if found, None otherwise
        """
        result = await self.db.execute(
            select(ConversationSession).where(
                ConversationSession.session_id == session_id
            )
        )
        return result.scalar_one_or_none()

    async def get_user_sessions(
        self,
        user_id: str,
        status_filter: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[ConversationSession], int]:
        """Get all sessions for a user with optional filtering.

        Args:
            user_id: User identifier
            status_filter: Optional status filter
            limit: Maximum number of sessions
            offset: Number of sessions to skip

        Returns:
            Tuple of (sessions list, total count)
        """
        query = select(ConversationSession).where(
            ConversationSession.user_id == user_id
        )

        if status_filter:
            query = query.where(ConversationSession.status == status_filter)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = query.order_by(ConversationSession.last_active_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        sessions = result.scalars().all()

        return list(sessions), total

    async def update_session_activity(self, session_id: uuid.UUID) -> bool:
        """Update the last activity timestamp.

        Args:
            session_id: UUID of the session

        Returns:
            True if successful
        """
        result = await self.db.execute(
            select(ConversationSession).where(
                ConversationSession.session_id == session_id
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            return False

        session.last_active_at = datetime.utcnow()
        await self.db.commit()

        # Update cache
        await self.cache.set_session_activity(str(session_id))

        return True

    async def update_session_metadata(
        self,
        session_id: uuid.UUID,
        metadata: dict
    ) -> Optional[ConversationSession]:
        """Update session metadata.

        Args:
            session_id: UUID of the session
            metadata: New metadata to merge

        Returns:
            Updated session if found
        """
        result = await self.db.execute(
            select(ConversationSession).where(
                ConversationSession.session_id == session_id
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            return None

        # Merge metadata
        existing = session.conversation_metadata or {}
        existing.update(metadata)
        session.conversation_metadata = existing

        await self.db.commit()
        await self.db.refresh(session)

        # Update cache
        await self.cache.set_session_context(
            str(session_id),
            {
                "user_id": session.user_id,
                "status": session.status.value if hasattr(session.status, 'value') else session.status,
                "metadata": session.conversation_metadata,
            }
        )

        return session

    async def update_session_status(
        self,
        session_id: uuid.UUID,
        status: SessionStatus
    ) -> Optional[ConversationSession]:
        """Update session status.

        Args:
            session_id: UUID of the session
            status: New status

        Returns:
            Updated session if found
        """
        result = await self.db.execute(
            select(ConversationSession).where(
                ConversationSession.session_id == session_id
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            return None

        session.status = status
        await self.db.commit()
        await self.db.refresh(session)

        # Invalidate cache
        await self.cache.invalidate_session(str(session_id))

        logger.info(f"Updated session {session_id} status to {status}")
        return session

    async def archive_session(self, session_id: uuid.UUID) -> bool:
        """Archive a session.

        Args:
            session_id: UUID of the session

        Returns:
            True if successful
        """
        session = await self.update_session_status(session_id, SessionStatus.ARCHIVED)
        return session is not None

    async def get_active_sessions_count(self, user_id: Optional[str] = None) -> int:
        """Get count of active sessions.

        Args:
            user_id: Optional user filter

        Returns:
            Count of active sessions
        """
        query = select(func.count()).select_from(ConversationSession).where(
            ConversationSession.status == SessionStatus.ACTIVE
        )

        if user_id:
            query = query.where(ConversationSession.user_id == user_id)

        result = await self.db.execute(query)
        return result.scalar() or 0

    async def fork_session(
        self,
        session_id: uuid.UUID,
        new_user_id: Optional[str] = None
    ) -> Optional[ConversationSession]:
        """Fork a session to create a new one.

        Args:
            session_id: UUID of the session to fork
            new_user_id: Optional new user ID

        Returns:
            New forked session
        """
        original = await self.get_session(session_id)
        if not original:
            return None

        new_session = ConversationSession(
            session_id=uuid.uuid4(),
            user_id=new_user_id or original.user_id,
            engagement_id=original.engagement_id,
            project_id=original.project_id,
            accelerator_type=original.accelerator_type,
            conversation_metadata=original.conversation_metadata.copy() if original.conversation_metadata else {},
            started_at=datetime.utcnow(),
            last_active_at=datetime.utcnow(),
            status=SessionStatus.ACTIVE,
        )

        self.db.add(new_session)
        await self.db.commit()
        await self.db.refresh(new_session)

        logger.info(f"Forked session {session_id} to {new_session.session_id}")
        return new_session


async def get_session_manager(db: AsyncSession, cache: RedisCache) -> SessionManager:
    """Factory to create SessionManager instance."""
    return SessionManager(db, cache)