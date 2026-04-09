"""Unit tests for LLM factory and providers."""
import pytest
from unittest.mock import patch, MagicMock

from app.integrations.llm.factory import (
    get_llm_provider,
    create_llm_client,
    LLMProvider,
    reset_llm_clients
)
from app.integrations.llm.base import MessageDict


class TestLLMFactory:
    """Test cases for LLM factory."""

    def test_get_llm_provider_default(self):
        """Test getting default LLM provider."""
        with patch('app.integrations.llm.factory.settings') as mock_settings:
            mock_settings.LLM_PROVIDER = "euri"
            provider = get_llm_provider()
            assert provider == "euri"

    def test_get_llm_provider_invalid(self):
        """Test getting provider with invalid value."""
        with patch('app.integrations.llm.factory.settings') as mock_settings:
            mock_settings.LLM_PROVIDER = "invalid"
            provider = get_llm_provider()
            # Should default to euri
            assert provider == "euri"

    def test_create_euri_client(self):
        """Test creating EURI client."""
        with patch('app.integrations.llm.factory.settings') as mock_settings:
            mock_settings.LLM_PROVIDER = "euri"
            mock_settings.EURI_API_KEY = "test-key"
            mock_settings.EURI_BASE_URL = "https://api.euri.ai/v1"
            mock_settings.EURI_MODEL = "claude-sonnet-4-20250514"

            reset_llm_clients()
            client = create_llm_client("euri")

            assert client is not None
            from app.integrations.llm.euri_client import EURIClient
            assert isinstance(client, EURIClient)

    def test_create_azure_client(self):
        """Test creating Azure OpenAI client."""
        with patch('app.integrations.llm.factory.settings') as mock_settings:
            mock_settings.LLM_PROVIDER = "azure"
            mock_settings.AZURE_OPENAI_ENDPOINT = "https://test.openai.azure.com"
            mock_settings.AZURE_OPENAI_KEY = "test-key"
            mock_settings.AZURE_DEPLOYMENT_NAME = "gpt-4o"
            mock_settings.AZURE_API_VERSION = "2024-02-01"

            reset_llm_clients()
            client = create_llm_client("azure")

            assert client is not None
            from app.integrations.llm.azure_openai import AzureOpenAIClient
            assert isinstance(client, AzureOpenAIClient)

    def test_unsupported_provider(self):
        """Test creating client with unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            create_llm_client("unsupported")


class TestMessageDict:
    """Test cases for MessageDict helper."""

    def test_message_dict_creation(self):
        """Test MessageDict creation."""
        msg = MessageDict("user", "Hello, world!")
        assert msg["role"] == "user"
        assert msg["content"] == "Hello, world!"

    def test_message_dict_iteration(self):
        """Test MessageDict iteration."""
        msg = MessageDict("assistant", "How can I help?")
        assert list(msg.items())[0] == ("role", "assistant")


class TestEURIClient:
    """Test cases for EURI client."""

    @pytest.mark.asyncio
    async def test_mock_embedding(self):
        """Test mock embedding generation."""
        from app.integrations.llm.euri_client import EURIClient

        client = EURIClient(api_key="test-key", base_url="http://test")
        embedding = client._mock_embedding("test text")

        assert len(embedding) == 1536
        # Check it's normalized
        norm = sum(x**2 for x in embedding) ** 0.5
        assert abs(norm - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_embedding_consistency(self):
        """Test that same text produces same embedding."""
        from app.integrations.llm.euri_client import EURIClient

        client = EURIClient(api_key="test-key", base_url="http://test")
        emb1 = client._mock_embedding("same text")
        emb2 = client._mock_embedding("same text")

        assert emb1 == emb2


class TestAzureOpenAIClient:
    """Test cases for Azure OpenAI client."""

    def test_client_initialization(self):
        """Test Azure client initialization."""
        from app.integrations.llm.azure_openai import AzureOpenAIClient

        client = AzureOpenAIClient(
            endpoint="https://test.openai.azure.com",
            api_key="test-key",
            deployment_name="gpt-4o"
        )

        assert client.endpoint == "https://test.openai.azure.com"
        assert client.deployment_name == "gpt-4o"