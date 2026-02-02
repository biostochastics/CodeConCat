"""Unit tests for AI provider implementations."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from codeconcat.ai.base import AIProviderConfig, AIProviderType, SummarizationResult
from codeconcat.ai.factory import get_ai_provider, list_available_providers


class TestAIProviderBase:
    """Tests for the base AI provider functionality."""

    def test_provider_config_creation(self):
        """Test that provider configuration is created correctly."""
        config = AIProviderConfig(
            provider_type=AIProviderType.OPENAI,
            api_key="test-key",
            model="gpt-3.5-turbo",
            temperature=0.5,
            max_tokens=1000,
        )

        assert config.provider_type == AIProviderType.OPENAI
        assert config.api_key == "test-key"
        assert config.model == "gpt-3.5-turbo"
        assert config.temperature == 0.5
        assert config.max_tokens == 1000
        assert config.cache_enabled is True  # Default

    def test_summarization_result_creation(self):
        """Test that summarization results are created correctly."""
        result = SummarizationResult(
            summary="This is a test summary",
            tokens_used=100,
            cost_estimate=0.001,
            model_used="gpt-3.5-turbo",
            provider="openai",
            cached=False,
        )

        assert result.summary == "This is a test summary"
        assert result.tokens_used == 100
        assert result.cost_estimate == 0.001
        assert result.model_used == "gpt-3.5-turbo"
        assert result.provider == "openai"
        assert result.cached is False
        assert result.error is None

    @pytest.mark.skip(reason="Requires OpenAI API key - provider validates on init")
    def test_cache_key_generation(self):
        """Test cache key generation for content."""
        config = AIProviderConfig(provider_type=AIProviderType.OPENAI, model="gpt-3.5-turbo")

        # Create a mock provider to test the base method
        from codeconcat.ai.providers.openai_provider import OpenAIProvider

        provider = OpenAIProvider(config)

        key1 = provider._generate_cache_key("test content", language="python")
        key2 = provider._generate_cache_key("test content", language="python")
        key3 = provider._generate_cache_key("different content", language="python")

        assert key1 == key2  # Same content should generate same key
        assert key1 != key3  # Different content should generate different key

    @pytest.mark.skip(reason="Requires OpenAI API key - provider validates on init")
    def test_token_estimation(self):
        """Test token estimation for text."""
        config = AIProviderConfig(provider_type=AIProviderType.OPENAI)

        from codeconcat.ai.providers.openai_provider import OpenAIProvider

        provider = OpenAIProvider(config)

        # Rough estimate: 1 token ≈ 4 characters
        text = "This is a test string with about 40 chars"
        estimated = provider._estimate_tokens(text)

        assert 8 <= estimated <= 12  # Should be around 10 tokens

    @pytest.mark.skip(reason="Requires OpenAI API key - provider validates on init")
    def test_cost_calculation(self):
        """Test cost calculation based on token usage."""
        config = AIProviderConfig(
            provider_type=AIProviderType.OPENAI,
            cost_per_1k_input_tokens=0.001,
            cost_per_1k_output_tokens=0.002,
        )

        from codeconcat.ai.providers.openai_provider import OpenAIProvider

        provider = OpenAIProvider(config)

        cost = provider._calculate_cost(1000, 500)  # 1000 input, 500 output
        expected = (1000 / 1000) * 0.001 + (500 / 1000) * 0.002

        assert cost == expected


class TestOpenAIProvider:
    """Tests for the OpenAI provider implementation."""

    @pytest.mark.asyncio
    async def test_openai_provider_initialization(self):
        """Test OpenAI provider initialization with defaults."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            config = AIProviderConfig(provider_type=AIProviderType.OPENAI)
            provider = get_ai_provider(config)

            assert provider.config.api_key == "test-key"
            assert provider.config.api_base == "https://api.openai.com/v1"
            assert provider.config.model == "gpt-5-mini-2025-08-07"  # Updated default to 2025 model

    @pytest.mark.asyncio
    async def test_openai_summarize_code(self):
        """Test code summarization with mocked API response."""
        config = AIProviderConfig(
            provider_type=AIProviderType.OPENAI,
            api_key="test-key",
            model="gpt-5-mini-2025-08-07",  # Updated to 2025 model
            cache_enabled=False,  # Disable cache for testing
        )

        from codeconcat.ai.providers.openai_provider import OpenAIProvider

        provider = OpenAIProvider(config)

        # Mock the API call
        mock_response = {
            "choices": [
                {"message": {"content": "This function calculates the factorial of a number."}}
            ],
            "usage": {"prompt_tokens": 50, "completion_tokens": 10, "total_tokens": 60},
        }

        with patch.object(provider, "_make_api_call", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_response

            result = await provider.summarize_code(
                "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
                "python",
            )

            assert result.summary == "This function calculates the factorial of a number."
            assert result.tokens_used == 60
            assert result.provider == "openai"
            assert result.model_used == "gpt-5-mini-2025-08-07"
            assert result.error is None

    @pytest.mark.asyncio
    async def test_openai_error_handling(self):
        """Test error handling in OpenAI provider."""
        config = AIProviderConfig(provider_type=AIProviderType.OPENAI, api_key="test-key")

        from codeconcat.ai.providers.openai_provider import OpenAIProvider

        provider = OpenAIProvider(config)

        # Mock an API error
        with patch.object(provider, "_make_api_call", new_callable=AsyncMock) as mock_api:
            mock_api.side_effect = Exception("API Error")

            result = await provider.summarize_code("test code", "python")

            assert result.summary == ""
            assert result.error == "API Error"
            assert result.provider == "openai"


class TestAnthropicProvider:
    """Tests for the Anthropic provider implementation."""

    @pytest.mark.asyncio
    async def test_anthropic_provider_initialization(self):
        """Test Anthropic provider initialization."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            config = AIProviderConfig(provider_type=AIProviderType.ANTHROPIC)
            provider = get_ai_provider(config)

            assert provider.config.api_key == "test-key"
            assert provider.config.api_base == "https://api.anthropic.com/v1"
            assert provider.config.model == "claude-3-5-haiku-20241022"  # Updated to current model


class TestProviderFactory:
    """Tests for the AI provider factory."""

    def test_get_ai_provider_openai(self):
        """Test getting an OpenAI provider."""
        config = AIProviderConfig(provider_type=AIProviderType.OPENAI, api_key="test")
        provider = get_ai_provider(config)

        from codeconcat.ai.providers.openai_provider import OpenAIProvider

        assert isinstance(provider, OpenAIProvider)

    def test_get_ai_provider_anthropic(self):
        """Test getting an Anthropic provider."""
        config = AIProviderConfig(provider_type=AIProviderType.ANTHROPIC, api_key="test")
        provider = get_ai_provider(config)

        from codeconcat.ai.providers.anthropic_provider import AnthropicProvider

        assert isinstance(provider, AnthropicProvider)

    def test_get_ai_provider_openrouter(self):
        """Test getting an OpenRouter provider."""
        config = AIProviderConfig(provider_type=AIProviderType.OPENROUTER, api_key="test")
        provider = get_ai_provider(config)

        from codeconcat.ai.providers.openrouter_provider import OpenRouterProvider

        assert isinstance(provider, OpenRouterProvider)

    def test_get_ai_provider_ollama(self):
        """Test getting an Ollama provider."""
        config = AIProviderConfig(provider_type=AIProviderType.OLLAMA)
        provider = get_ai_provider(config)

        from codeconcat.ai.providers.ollama_provider import OllamaProvider

        assert isinstance(provider, OllamaProvider)

    @patch("requests.get")
    def test_list_available_providers(self, mock_get):
        """Test listing available providers."""
        # Mock successful Ollama check
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Test with specific imports not available
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name in ["openai", "anthropic", "llama_cpp"]:
                raise ImportError(f"No module named '{name}'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            providers = list_available_providers()
            # Should always have openrouter and ollama (mocked as available)
            assert "openrouter" in providers
            assert "ollama" in providers
