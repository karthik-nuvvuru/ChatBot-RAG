"""Message service with caching and full-text search."""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ConversationMessage, MessageRole, ConversationSession
from app.schemas import MessageCreate
from app.chat.redis_cache import RedisCache

logger = logging.getLogger("conversation_ai.messages")


class MessageService:
    """Service for managing conversation messages with caching."""

    def __init__(self, db: AsyncSession, cache: RedisCache):
        self.db = db
        self.cache = cache

    async def add_message(
        self,
        session_id: uuid.UUID,
        message_data: MessageCreate
    ) -> ConversationMessage:
        """Add a new message to a session.

        Args:
            session_id: Session UUID
            message_data: Message creation data

        Returns:
            Created ConversationMessage

        Raises:
            ValueError: If session doesn't exist or content invalid
        """
        # Verify session exists and is active
        result = await self.db.execute(
            select(ConversationSession).where(
                ConversationSession.session_id == session_id
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        if not session.is_active():
            raise ValueError(f"Session {session_id} is not active")

        # Validate content length
        content = message_data.content.strip()
        if len(content) > 10000:
            raise ValueError("Message content exceeds maximum length of 10000 characters")

        # Create message
        message = ConversationMessage(
            message_id=uuid.uuid4(),
            session_id=session_id,
            role=MessageRole(message_data.role.value),
            content=content,
            message_metadata=message_data.message_metadata or {},
            parent_message_id=message_data.parent_message_id,
            created_at=datetime.utcnow(),
        )

        self.db.add(message)

        # Update session activity
        session.last_active_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(message)

        # Cache the message
        msg_dict = {
            "message_id": str(message.message_id),
            "role": message.role.value if hasattr(message.role, 'value') else message.role,
            "content": message.content,
            "created_at": message.created_at.isoformat() if message.created_at else None,
        }
        await self.cache.append_message(str(session_id), msg_dict)

        logger.info(f"Added message {message.message_id} to session {session_id}")
        return message

    async def get_session_messages(
        self,
        session_id: uuid.UUID,
        limit: int = 20,
        cursor: Optional[str] = None,
        role_filter: Optional[str] = None
    ) -> Tuple[List[ConversationMessage], Optional[str], int]:
        """Get messages for a session with cursor pagination.

        Args:
            session_id: Session UUID
            limit: Maximum messages to return
            cursor: Optional cursor (message_id)
            role_filter: Optional role filter

        Returns:
            Tuple of (messages, next_cursor, total_count)
        """
        query = select(ConversationMessage).where(
            ConversationMessage.session_id == session_id
        )

        # Apply role filter if specified
        if role_filter:
            query = query.where(ConversationMessage.role == role_filter)

        # Apply cursor-based pagination
        if cursor:
            cursor_result = await self.db.execute(
                select(ConversationMessage.created_at).where(
                    ConversationMessage.message_id == uuid.UUID(cursor)
                )
            )
            cursor_time = cursor_result.scalar_one_or_none()
            if cursor_time:
                query = query.where(ConversationMessage.created_at < cursor_time)

        # Get total count
        count_query = select(func.count()).select_from(
            select(ConversationMessage).where(
                ConversationMessage.session_id == session_id
            ).subquery()
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get messages ordered by created_at desc (newest first)
        query = query.order_by(ConversationMessage.created_at.desc())
        query = query.limit(limit)

        result = await self.db.execute(query)
        messages = list(result.scalars().all())

        # Reverse to get oldest first within limit
        messages.reverse()

        # Calculate next cursor
        next_cursor = str(messages[-1].message_id) if messages else None

        return messages, next_cursor, total

    async def get_message_thread(
        self,
        message_id: uuid.UUID
    ) -> Tuple[ConversationMessage, List[ConversationMessage]]:
        """Get a message and its replies.

        Args:
            message_id: Message UUID

        Returns:
            Tuple of (parent message, list of replies)
        """
        result = await self.db.execute(
            select(ConversationMessage).where(
                ConversationMessage.message_id == message_id
            )
        )
        message = result.scalar_one_or_none()

        if not message:
            raise ValueError(f"Message {message_id} not found")

        # Get replies
        replies_result = await self.db.execute(
            select(ConversationMessage).where(
                ConversationMessage.parent_message_id == message_id
            ).order_by(ConversationMessage.created_at.asc())
        )
        replies = list(replies_result.scalars().all())

        return message, replies

    async def search_messages(
        self,
        session_id: uuid.UUID,
        query: str,
        limit: int = 20
    ) -> List[ConversationMessage]:
        """Search messages using ILIKE (simple full-text search).

        Args:
            session_id: Session UUID
            query: Search query
            limit: Maximum results

        Returns:
            List of matching messages
        """
        search_pattern = f"%{query}%"

        result = await self.db.execute(
            select(ConversationMessage).where(
                and_(
                    ConversationMessage.session_id == session_id,
                    ConversationMessage.content.ilike(search_pattern)
                )
            ).order_by(ConversationMessage.created_at.desc()).limit(limit)
        )

        return list(result.scalars().all())

    async def count_session_messages(self, session_id: uuid.UUID) -> int:
        """Count total messages in a session.

        Args:
            session_id: Session UUID

        Returns:
            Total message count
        """
        result = await self.db.execute(
            select(func.count()).select_from(ConversationMessage).where(
                ConversationMessage.session_id == session_id
            )
        )
        return result.scalar() or 0

    async def delete_message(self, message_id: uuid.UUID) -> bool:
        """Delete a message.

        Args:
            message_id: Message UUID

        Returns:
            True if deleted
        """
        result = await self.db.execute(
            select(ConversationMessage).where(
                ConversationMessage.message_id == message_id
            )
        )
        message = result.scalar_one_or_none()

        if not message:
            return False

        await self.db.delete(message)
        await self.db.commit()

        logger.info(f"Deleted message {message_id}")
        return True

    async def get_recent_messages(
        self,
        session_id: uuid.UUID,
        count: int = 20
    ) -> List[ConversationMessage]:
        """Get recent messages for context.

        Args:
            session_id: Session UUID
            count: Number of recent messages

        Returns:
            List of recent messages
        """
        # Check cache first
        cached = await self.cache.get_cached_messages(str(session_id))
        if cached and len(cached) >= count:
            # Return from cache (converted to mock message objects)
            return cached[-count:]

        # Get from database
        result = await self.db.execute(
            select(ConversationMessage).where(
                ConversationMessage.session_id == session_id
            ).order_by(ConversationMessage.created_at.desc()).limit(count)
        )
        messages = list(result.scalars().all())
        messages.reverse()

        # Warm cache
        msg_dicts = [
            {
                "message_id": str(m.message_id),
                "role": m.role.value if hasattr(m.role, 'value') else m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ]
        await self.cache.cache_messages(str(session_id), msg_dicts)

        return messages

    async def bulk_add_messages(
        self,
        session_id: uuid.UUID,
        messages_data: List[MessageCreate]
    ) -> List[ConversationMessage]:
        """Bulk insert messages.

        Args:
            session_id: Session UUID
            messages_data: List of message data

        Returns:
            List of created messages
        """
        messages = []
        for msg_data in messages_data:
            content = msg_data.content.strip()[:10000]
            message = ConversationMessage(
                message_id=uuid.uuid4(),
                session_id=session_id,
                role=MessageRole(msg_data.role.value),
                content=content,
                message_metadata=msg_data.message_metadata or {},
                parent_message_id=msg_data.parent_message_id,
                created_at=datetime.utcnow(),
            )
            messages.append(message)

        self.db.add_all(messages)
        await self.db.commit()

        for msg in messages:
            await self.db.refresh(msg)

        return messages


async def get_message_service(db: AsyncSession, cache: RedisCache) -> MessageService:
    """Factory to create MessageService instance."""
    return MessageService(db, cache)