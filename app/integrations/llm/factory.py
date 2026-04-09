"""LLM provider factory for switching between EURI and Azure."""
import logging
from typing import Optional, Type
from app.core.config import settings

from app.integrations.llm.base import BaseLLM
from app.integrations.llm.euri_client import EURIClient
from app.integrations.llm.azure_openai import AzureOpenAIClient

logger = logging.getLogger("conversation_ai.llm.factory")

# Global client instances
_llm_client: Optional[BaseLLM] = None
_embedding_client: Optional[BaseLLM] = None


class LLMProvider(str):
    """LLM provider types."""
    EURI = "euri"
    AZURE = "azure"


def get_llm_provider() -> str:
    """Get the configured LLM provider.

    Returns:
        Provider name ('euri' or 'azure')
    """
    provider = settings.LLM_PROVIDER.lower()
    if provider not in [LLMProvider.EURI, LLMProvider.AZURE]:
        logger.warning(f"Unknown LLM provider '{provider}', defaulting to 'euri'")
        return LLMProvider.EURI
    return provider


def create_llm_client(provider: Optional[str] = None) -> BaseLLM:
    """Create an LLM client based on provider.

    Args:
        provider: Provider name (defaults to env config)

    Returns:
        LLM client instance

    Raises:
        ValueError: If provider is not supported
    """
    provider = provider or get_llm_provider()

    if provider == LLMProvider.AZURE:
        logger.info("Creating Azure OpenAI client")
        return AzureOpenAIClient()

    elif provider == LLMProvider.EURI:
        logger.info("Creating EURI API client")
        return EURIClient()

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def create_embedding_client(provider: Optional[str] = None) -> BaseLLM:
    """Create an embedding client based on provider.

    Args:
        provider: Provider name (defaults to env config)

    Returns:
        Embedding client instance
    """
    provider = provider or get_llm_provider()

    if provider == LLMProvider.AZURE:
        logger.info("Creating Azure OpenAI embedding client")
        return AzureOpenAIClient()

    elif provider == LLMProvider.EURI:
        logger.info("Creating EURI API client (with embed support)")
        return EURIClient()

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def get_llm_client() -> BaseLLM:
    """Get the global LLM client instance.

    Returns:
        LLM client (creates if not exists)
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = create_llm_client()
    return _llm_client


def get_embedding_client() -> BaseLLM:
    """Get the global embedding client instance.

    Returns:
        Embedding client (creates if not exists)
    """
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = create_embedding_client()
    return _embedding_client


async def close_llm_clients():
    """Close all LLM client connections."""
    global _llm_client, _embedding_client

    if _llm_client is not None:
        await _llm_client.close()
        _llm_client = None

    if _embedding_client is not None:
        if hasattr(_embedding_client, 'close'):
            await _embedding_client.close()
        _embedding_client = None


def reset_llm_clients():
    """Reset LLM client instances (for testing)."""
    global _llm_client, _embedding_client
    _llm_client = None
    _embedding_client = None