"""Embedding service for generating text embeddings."""
import logging
from typing import List, Optional

from app.core.config import settings
from app.integrations.llm.factory import get_embedding_client

logger = logging.getLogger("conversation_ai.embedding")


class EmbeddingService:
    """Service for generating text embeddings via configured provider."""

    def __init__(self):
        self._client = None
        self._cache: dict = {}

    @property
    def client(self):
        """Get embedding client."""
        if self._client is None:
            self._client = get_embedding_client()
        return self._client

    async def embed_text(self, text: str, use_cache: bool = True) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed
            use_cache: Whether to use cached embeddings

        Returns:
            Embedding vector as list of floats
        """
        if use_cache and text in self._cache:
            logger.debug(f"Embedding cache hit for text length {len(text)}")
            return self._cache[text]

        try:
            embedding = await self.client.embed(text)

            if use_cache:
                self._cache[text] = embedding

            logger.debug(f"Generated embedding for text length {len(text)}")
            return embedding

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            # Return mock embedding for development
            return self._mock_embedding(text)

    async def embed_batch(self, texts: List[str], use_cache: bool = True) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            use_cache: Whether to use cached embeddings

        Returns:
            List of embedding vectors
        """
        # Filter out cached texts
        uncached_texts = []
        cached_embeddings = []
        result = []

        for text in texts:
            if use_cache and text in self._cache:
                cached_embeddings.append(self._cache[text])
            else:
                uncached_texts.append((text, len(result)))
                result.append(None)  # Placeholder

        # Embed uncached texts
        if uncached_texts:
            try:
                # Try batch embedding
                embeddings = await self.client.embed_batch([t for t, _ in uncached_texts])
                for i, emb in enumerate(embeddings):
                    idx = uncached_texts[i][1]
                    result[idx] = emb
                    if use_cache:
                        self._cache[uncached_texts[i][0]] = emb
            except Exception as e:
                logger.error(f"Batch embedding failed, falling back to individual: {e}")
                for text, idx in uncached_texts:
                    emb = await self.embed_text(text, use_cache)
                    result[idx] = emb

        return result

    def _mock_embedding(self, text: str) -> List[float]:
        """Generate a deterministic mock embedding for development.

        Args:
            text: Text to embed

        Returns:
            Mock embedding vector
        """
        import hashlib
        import numpy as np

        text_hash = hashlib.sha256(text.encode()).digest()
        rng = np.random.RandomState(int.from_bytes(text_hash[:4], 'little'))
        embedding = rng.randn(1536).tolist()

        # Normalize
        norm = sum(x**2 for x in embedding) ** 0.5
        return [x / norm if norm > 0 else x for x in embedding]

    async def embed_conversation(
        self,
        messages: List[dict],
        max_tokens: int = 8000
    ) -> List[float]:
        """Generate embedding for a conversation.

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum token limit

        Returns:
            Embedding vector for the conversation
        """
        # Format conversation into a single text
        formatted_parts = []
        total_len = 0

        for msg in reversed(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            part = f"{role}: {content}"

            if total_len + len(part) > max_tokens * 4:
                break

            formatted_parts.append(part)
            total_len += len(part)

        text = "\n".join(reversed(formatted_parts))
        return await self.embed_text(text)

    def clear_cache(self):
        """Clear the embedding cache."""
        self._cache.clear()
        logger.info("Embedding cache cleared")


# Global instance
embedding_service = EmbeddingService()


async def get_embedding_service() -> EmbeddingService:
    """Get embedding service instance."""
    return embedding_service