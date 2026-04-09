"""Azure OpenAI client for GPT models."""
import logging
from typing import AsyncIterator, List, Dict, Optional
from openai import AsyncAzureOpenAI

from app.core.config import settings
from app.integrations.llm.base import BaseLLM, MessageDict

logger = logging.getLogger("conversation_ai.llm.azure")


class AzureOpenAIClient(BaseLLM):
    """Azure OpenAI client for chat completions and embeddings."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        api_version: Optional[str] = None,
        deployment_name: Optional[str] = None,
        embedding_deployment: Optional[str] = None,
    ):
        """Initialize Azure OpenAI client.

        Args:
            endpoint: Azure endpoint URL
            api_key: Azure API key
            api_version: API version
            deployment_name: Chat deployment name
            embedding_deployment: Embedding deployment name
        """
        self.endpoint = endpoint or settings.AZURE_OPENAI_ENDPOINT
        self.api_key = api_key or settings.AZURE_OPENAI_KEY
        self.api_version = api_version or settings.AZURE_API_VERSION
        self.deployment_name = deployment_name or settings.AZURE_DEPLOYMENT_NAME
        self.embedding_deployment = embedding_deployment or settings.AZURE_EMBEDDING_DEPLOYMENT

        if not self.api_key or not self.endpoint:
            logger.warning("Azure OpenAI credentials not fully configured")

        self._client: Optional[AsyncAzureOpenAI] = None

    @property
    def client(self) -> AsyncAzureOpenAI:
        """Get or create Azure OpenAI client."""
        if self._client is None:
            self._client = AsyncAzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=self.endpoint,
                api_version=self.api_version,
            )
        return self._client

    async def close(self):
        """Close the Azure OpenAI client."""
        if self._client:
            await self._client.close()
            self._client = None

    async def generate(
        self,
        messages: List[MessageDict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: bool = False,
    ) -> str:
        """Generate a completion using Azure OpenAI.

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

        try:
            response = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )

            return response.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"Azure OpenAI generate error: {e}")
            raise

    async def stream(
        self,
        messages: List[MessageDict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Stream a completion using Azure OpenAI.

        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            max_tokens: Maximum tokens

        Yields:
            Text chunks
        """
        try:
            stream = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            async for chunk in stream:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content

        except Exception as e:
            logger.error(f"Azure OpenAI stream error: {e}")
            raise

    async def embed(self, text: str) -> List[float]:
        """Generate embedding using Azure OpenAI.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_deployment,
                input=text,
            )

            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Azure OpenAI embed error: {e}")
            raise

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts

        Returns:
            List of embedding vectors
        """
        try:
            response = await self.client.embeddings.create(
                model=self.embedding_deployment,
                input=texts,
            )

            return [item.embedding for item in response.data]

        except Exception as e:
            logger.error(f"Azure OpenAI batch embed error: {e}")
            raise

    def supports_streaming(self) -> bool:
        """Check if streaming is supported."""
        return True