"""Base LLM interface for all providers."""
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, List, Dict, Any
import logging

logger = logging.getLogger("conversation_ai.llm")


class MessageDict(Dict[str, str]):
    """Message format for LLM providers."""
    def __init__(self, role: str, content: str):
        super().__init__()
        self["role"] = role
        self["content"] = content


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        messages: List[MessageDict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> str:
        """Generate a completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response

        Returns:
            Generated text string
        """
        pass

    @abstractmethod
    async def stream(
        self,
        messages: List[MessageDict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Stream a completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate

        Yields:
            Text chunks as they are generated
        """
        pass

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate an embedding for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        pass

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        results = []
        for text in texts:
            embedding = await self.embed(text)
            results.append(embedding)
        return results

    def supports_streaming(self) -> bool:
        """Check if this provider supports streaming."""
        return True


class EmbeddingResult:
    """Result from embedding generation."""
    def __init__(self, embedding: List[float], model: str, tokens: int = 0):
        self.embedding = embedding
        self.model = model
        self.tokens = tokens