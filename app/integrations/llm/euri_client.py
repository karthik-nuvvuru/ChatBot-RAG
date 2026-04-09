"""EURI API client for Claude/OpenRouter compatible models."""
import json
import logging
from typing import AsyncIterator, List, Dict, Optional
import httpx

from app.core.config import settings
from app.integrations.llm.base import BaseLLM, MessageDict

logger = logging.getLogger("conversation_ai.llm.euri")


class EURIError(Exception):
    """EURI API specific error."""
    pass


class EURIClient(BaseLLM):
    """EURI API client for chat completions and embeddings."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """Initialize EURI client.

        Args:
            api_key: EURI API key (defaults to env)
            base_url: EURI base URL (defaults to env)
            model: Model name (defaults to env)
        """
        self.api_key = api_key or settings.EURI_API_KEY
        self.base_url = base_url or settings.EURI_BASE_URL
        self.model = model or settings.EURI_MODEL

        if not self.api_key:
            logger.warning("EURI_API_KEY not set - EURI client may not work")

        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(60.0, connect=10.0),
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def generate(
        self,
        messages: List[MessageDict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> str:
        """Generate a completion using EURI API.

        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            stream: Whether to stream

        Returns:
            Generated text
        """
        if stream:
            full_content = ""
            async for chunk in self.stream(messages, temperature, max_tokens):
                full_content += chunk
            return full_content

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }

        try:
            response = await self.client.post("/euri/chat/completions", json=payload)
            response.raise_for_status()

            data = response.json()
            return data["choices"][0]["message"]["content"]

        except httpx.HTTPStatusError as e:
            logger.error(f"EURI API error: {e.response.status_code} - {e.response.text}")
            raise EURIError(f"API request failed: {e.response.status_code}")
        except Exception as e:
            logger.error(f"EURI generate error: {e}")
            raise EURIError(f"Failed to generate: {str(e)}")

    async def stream(
        self,
        messages: List[MessageDict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Stream a completion using EURI API.

        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Yields:
            Text chunks
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        try:
            async with self.client.stream("POST", "/euri/chat/completions", json=payload) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    # Handle both "data:" prefix and raw JSON lines
                    data_str = line
                    if line.startswith("data:"):
                        data_str = line[5:].strip()

                    if data_str == "[DONE]" or data_str == "done":
                        break

                    if not data_str:
                        continue

                    try:
                        data = json.loads(data_str)
                        # Try different response formats (OpenAI, Claude, etc.)
                        content = None

                        # Format 1: OpenAI style
                        if "choices" in data and data["choices"]:
                            choice = data["choices"][0]
                            if "delta" in choice and "content" in choice["delta"]:
                                content = choice["delta"]["content"]
                            elif "message" in choice and "content" in choice["message"]:
                                content = choice["message"]["content"]

                        # Format 2: Claude style with content blocks
                        elif "content" in data:
                            if isinstance(data["content"], list):
                                for block in data["content"]:
                                    if block.get("type") == "text":
                                        content = block.get("text", "")
                                        break
                            elif isinstance(data["content"], str):
                                content = data["content"]

                        # Format 3: Direct content field
                        elif "text" in data:
                            content = data["text"]

                        if content:
                            yield content

                    except json.JSONDecodeError:
                        continue
                    except (IndexError, KeyError) as e:
                        logger.warning(f"Failed to parse stream chunk: {e}")
                        continue

        except httpx.HTTPStatusError as e:
            logger.error(f"EURI streaming error: {e.response.status_code} - {e.response.text}")
            raise EURIError(f"Stream failed: {e.response.status_code}")
        except Exception as e:
            logger.error(f"EURI stream error: {e}")
            raise EURIError(f"Stream failed: {str(e)}")

    async def embed(self, text: str) -> List[float]:
        """Generate embedding using EURI API.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        # EURI uses the same endpoint format as OpenAI for embeddings
        payload = {
            "model": "text-embedding-3-small",
            "input": text,
        }

        try:
            response = await self.client.post("/euri/embeddings", json=payload)
            response.raise_for_status()

            data = response.json()
            return data["data"][0]["embedding"]

        except Exception as e:
            logger.warning(f"EURI embed error, using fallback: {e}")
            return self._mock_embedding(text)

    def _mock_embedding(self, text: str) -> List[float]:
        """Generate a mock embedding for development.

        Args:
            text: Text to embed

        Returns:
            Mock embedding vector (1536 dimensions)
        """
        import hashlib
        import numpy as np

        # Create deterministic mock embedding based on text hash
        text_hash = hashlib.sha256(text.encode()).digest()
        rng = np.random.RandomState(int.from_bytes(text_hash[:4], 'little'))
        embedding = rng.randn(1536).tolist()

        # Normalize
        norm = sum(x**2 for x in embedding) ** 0.5
        return [x / norm for x in embedding]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts

        Returns:
            List of embedding vectors
        """
        return [await self.embed(text) for text in texts]

    def supports_streaming(self) -> bool:
        """Check if streaming is supported."""
        return True