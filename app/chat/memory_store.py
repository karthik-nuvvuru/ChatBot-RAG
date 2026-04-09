"""Vector store implementation using pgvector for similarity search."""
import uuid
import logging
from typing import List, Optional, Tuple

import numpy as np
from sqlalchemy import select, func, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ConversationMemory, MemoryType

logger = logging.getLogger("conversation_ai.memory_store")


class MemoryStore:
    """Vector store for conversation memories using pgvector for similarity search."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _compute_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not vec1 or not vec2:
            return 0.0

        v1 = np.array(vec1)
        v2 = np.array(vec2)

        dot = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot / (norm1 * norm2))

    async def store_memory(
        self,
        session_id: uuid.UUID,
        memory_type: MemoryType,
        content: str,
        embedding: Optional[List[float]] = None,
        metadata: Optional[dict] = None
    ) -> ConversationMemory:
        """Store a memory with optional embedding.

        Args:
            session_id: Session UUID
            memory_type: Type of memory
            content: Memory content text
            embedding: Optional vector embedding
            metadata: Optional metadata

        Returns:
            Created ConversationMemory instance
        """
        memory = ConversationMemory(
            memory_id=uuid.uuid4(),
            session_id=session_id,
            memory_type=memory_type,
            content=content,
            embedding=embedding,
            memory_metadata=metadata or {},
        )

        self.db.add(memory)
        await self.db.commit()
        await self.db.refresh(memory)

        logger.info(f"Stored memory {memory.memory_id} for session {session_id}")
        return memory

    async def search_similar(
        self,
        session_id: Optional[uuid.UUID] = None,
        query_embedding: Optional[List[float]] = None,
        memory_type: Optional[MemoryType] = None,
        k: int = 5,
        threshold: float = 0.7
    ) -> List[Tuple[ConversationMemory, float]]:
        """Search for similar memories using cosine similarity.

        Args:
            session_id: Optional session filter
            query_embedding: Query embedding vector
            memory_type: Optional memory type filter
            k: Number of results to return
            threshold: Minimum similarity threshold

        Returns:
            List of (memory, similarity_score) tuples
        """
        if not query_embedding:
            return []

        # Build query
        query = select(ConversationMemory)

        if session_id:
            query = query.where(ConversationMemory.session_id == session_id)

        if memory_type:
            query = query.where(ConversationMemory.memory_type == memory_type)

        result = await self.db.execute(query)
        all_memories = result.scalars().all()

        # Compute similarities
        scored = []
        for memory in all_memories:
            if memory.embedding:
                similarity = self._compute_cosine_similarity(
                    query_embedding,
                    memory.embedding
                )
                if similarity >= threshold:
                    scored.append((memory, similarity))

        # Sort by similarity descending
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored[:k]

    async def get_session_memories(
        self,
        session_id: uuid.UUID,
        memory_type: Optional[MemoryType] = None,
        limit: int = 100
    ) -> List[ConversationMemory]:
        """Get all memories for a session.

        Args:
            session_id: Session UUID
            memory_type: Optional type filter
            limit: Maximum memories to return

        Returns:
            List of ConversationMemory instances
        """
        query = select(ConversationMemory).where(
            ConversationMemory.session_id == session_id
        )

        if memory_type:
            query = query.where(ConversationMemory.memory_type == memory_type)

        query = query.order_by(ConversationMemory.created_at.desc())
        query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_memory(self, memory_id: uuid.UUID) -> bool:
        """Delete a memory.

        Args:
            memory_id: Memory UUID

        Returns:
            True if deleted
        """
        result = await self.db.execute(
            select(ConversationMemory).where(
                ConversationMemory.memory_id == memory_id
            )
        )
        memory = result.scalar_one_or_none()

        if not memory:
            return False

        await self.db.delete(memory)
        await self.db.commit()

        logger.info(f"Deleted memory {memory_id}")
        return True

    async def delete_session_memories(self, session_id: uuid.UUID) -> int:
        """Delete all memories for a session.

        Args:
            session_id: Session UUID

        Returns:
            Number of deleted memories
        """
        # Count first
        count_result = await self.db.execute(
            select(func.count()).select_from(ConversationMemory).where(
                ConversationMemory.session_id == session_id
            )
        )
        count = count_result.scalar() or 0

        # Delete
        await self.db.execute(
            delete(ConversationMemory).where(
                ConversationMemory.session_id == session_id
            )
        )
        await self.db.commit()

        logger.info(f"Deleted {count} memories for session {session_id}")
        return count

    async def get_memory_stats(self, session_id: uuid.UUID) -> dict:
        """Get memory statistics for a session.

        Args:
            session_id: Session UUID

        Returns:
            Dict with memory counts by type
        """
        result = await self.db.execute(
            select(
                ConversationMemory.memory_type,
                func.count(ConversationMemory.memory_id).label("count")
            ).where(
                ConversationMemory.session_id == session_id
            ).group_by(ConversationMemory.memory_type)
        )

        rows = result.all()
        return {
            row.memory_type.value if hasattr(row.memory_type, 'value') else row.memory_type: row.count
            for row in rows
        }


async def get_memory_store(db: AsyncSession) -> MemoryStore:
    """Factory to create MemoryStore instance."""
    return MemoryStore(db)