"""Memory service - high-level facade coordinating DB, cache, and embeddings."""
import uuid
import logging
from typing import Optional, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ConversationMemory, MemoryType
from app.chat.memory_store import MemoryStore, get_memory_store
from app.chat.embedding_service import EmbeddingService, get_embedding_service
from app.chat.redis_cache import RedisCache
from app.chat.message_service import MessageService

logger = logging.getLogger("conversation_ai.memory")


class MemoryService:
    """High-level memory service coordinating storage, caching, and embeddings."""

    def __init__(
        self,
        db: AsyncSession,
        memory_store: MemoryStore,
        embedding_service: EmbeddingService,
        cache: RedisCache
    ):
        self.db = db
        self.memory_store = memory_store
        self.embedding_service = embedding_service
        self.cache = cache

    async def add_message_memory(
        self,
        session_id: uuid.UUID,
        message_id: uuid.UUID,
        content: str,
        importance: float = 0.5
    ) -> Optional[ConversationMemory]:
        """Add a memory from an important message.

        Args:
            session_id: Session UUID
            message_id: Message UUID
            content: Message content
            importance: Importance score (0-1)

        Returns:
            Created memory or None if not important enough
        """
        if importance < 0.7:
            return None

        try:
            embedding = await self.embedding_service.embed_text(content)

            memory = await self.memory_store.store_memory(
                session_id=session_id,
                memory_type=MemoryType.EPISODIC,
                content=content,
                embedding=embedding,
                metadata={
                    "source_message_id": str(message_id),
                    "importance": importance,
                }
            )

            logger.info(f"Added message memory {memory.memory_id} for session {session_id}")
            return memory

        except Exception as e:
            logger.error(f"Failed to add message memory: {e}")
            return None

    async def get_conversation_history(
        self,
        session_id: uuid.UUID,
        limit: int = 50
    ) -> str:
        """Get conversation history as formatted string.

        Args:
            session_id: Session UUID
            limit: Maximum number of recent messages

        Returns:
            Formatted conversation history
        """
        msg_service = MessageService(self.db, self.cache)
        messages = await msg_service.get_recent_messages(session_id, limit)

        if isinstance(messages[0], dict) if messages else False:
            # Messages came from cache
            history = []
            for msg in messages:
                role = msg.get("role", "unknown").upper()
                content = msg.get("content", "")
                if len(content) > 500:
                    content = content[:500] + "..."
                history.append(f"{role}: {content}")
        else:
            history = []
            for msg in messages:
                role = msg.role.value if hasattr(msg.role, 'value') else msg.role
                content = msg.content
                if len(content) > 500:
                    content = content[:500] + "..."
                history.append(f"{role.upper()}: {content}")

        return "\n".join(history[-limit:])

    async def retrieve_relevant_context(
        self,
        session_id: uuid.UUID,
        query: str,
        k: int = 5
    ) -> Tuple[str, List[ConversationMemory], float]:
        """Retrieve relevant context for a query.

        Args:
            session_id: Session UUID
            query: Query string
            k: Number of memories to retrieve

        Returns:
            Tuple of (context string, memories list, avg similarity score)
        """
        try:
            query_embedding = await self.embedding_service.embed_text(query)

            results = await self.memory_store.search_similar(
                session_id=session_id,
                query_embedding=query_embedding,
                k=k,
                threshold=0.6
            )

            if not results:
                return "", [], 0.0

            memories, scores = zip(*results)
            avg_score = sum(scores) / len(scores)

            context_parts = []
            for memory in memories:
                mem_type = memory.memory_type.value if hasattr(memory.memory_type, 'value') else memory.memory_type
                content = memory.content[:300] + "..." if len(memory.content) > 300 else memory.content
                context_parts.append(f"[{mem_type}] {content}")

            context = "\n\n".join(context_parts)
            return context, list(memories), avg_score

        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            return "", [], 0.0

    async def summarize_session(self, session_id: uuid.UUID) -> str:
        """Generate a summary of session key points.

        Args:
            session_id: Session UUID

        Returns:
            Summary string
        """
        try:
            history = await self.get_conversation_history(session_id, limit=50)

            if not history:
                return "No conversation history available."

            summary_parts = []
            memories = await self.memory_store.get_session_memories(session_id, limit=10)

            semantic_memories = [
                m for m in memories
                if (m.memory_type.value if hasattr(m.memory_type, 'value') else m.memory_type) == "semantic"
            ]

            if semantic_memories:
                summary_parts.append("Key Information:")
                for mem in semantic_memories[:3]:
                    summary_parts.append(f"- {mem.content[:100]}")

            episodic_memories = [
                m for m in memories
                if (m.memory_type.value if hasattr(m.memory_type, 'value') else m.memory_type) == "episodic"
            ]

            if episodic_memories:
                summary_parts.append("\nImportant Events:")
                for mem in episodic_memories[:3]:
                    summary_parts.append(f"- {mem.content[:100]}")

            return "\n".join(summary_parts) if summary_parts else "Summary not available."

        except Exception as e:
            logger.error(f"Failed to summarize session: {e}")
            return "Summary not available."

    async def store_semantic_memory(
        self,
        session_id: uuid.UUID,
        content: str,
        metadata: Optional[dict] = None
    ) -> Optional[ConversationMemory]:
        """Store a semantic (factual) memory.

        Args:
            session_id: Session UUID
            content: Memory content
            metadata: Optional metadata

        Returns:
            Created memory
        """
        try:
            embedding = await self.embedding_service.embed_text(content)

            return await self.memory_store.store_memory(
                session_id=session_id,
                memory_type=MemoryType.SEMANTIC,
                content=content,
                embedding=embedding,
                metadata=metadata or {}
            )
        except Exception as e:
            logger.error(f"Failed to store semantic memory: {e}")
            return None

    async def store_working_memory(
        self,
        session_id: uuid.UUID,
        content: str,
        metadata: Optional[dict] = None
    ) -> Optional[ConversationMemory]:
        """Store a working (temporary) memory.

        Args:
            session_id: Session UUID
            content: Memory content
            metadata: Optional metadata

        Returns:
            Created memory
        """
        try:
            return await self.memory_store.store_memory(
                session_id=session_id,
                memory_type=MemoryType.WORKING,
                content=content,
                embedding=None,  # Working memory doesn't need embedding
                metadata=metadata or {"ttl": "session"}
            )
        except Exception as e:
            logger.error(f"Failed to store working memory: {e}")
            return None

    async def cleanup_old_working_memory(self, session_id: uuid.UUID) -> int:
        """Clean up expired working memories for a session.

        Args:
            session_id: Session UUID

        Returns:
            Number of deleted memories
        """
        memories = await self.memory_store.get_session_memories(
            session_id,
            memory_type=MemoryType.WORKING
        )

        count = 0
        for memory in memories:
            metadata = memory.memory_metadata or {}
            if metadata.get("ttl") == "session":
                await self.memory_store.delete_memory(memory.memory_id)
                count += 1

        return count


async def get_memory_service(
    db: AsyncSession,
    memory_store: MemoryStore,
    embedding_service: EmbeddingService,
    cache: RedisCache
) -> MemoryService:
    """Factory to create MemoryService instance."""
    return MemoryService(db, memory_store, embedding_service, cache)