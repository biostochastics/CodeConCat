"""Unit tests for new AI providers (Google, Zhipu, DeepSeek, MiniMax, Qwen)."""

import json
from collections.abc import Callable
from unittest.mock import AsyncMock, patch

import pytest

from codeconcat.ai.base import AIProviderConfig, AIProviderType
from codeconcat.ai.factory import get_ai_provider, get_provider_info


class StubResponse:
    """Minimal aiohttp-like response context manager."""

    def __init__(self, status: int, payload: dict | None = None, text_body: str | None = None):
        self.status = status
        self._payload = payload
        self._text = text_body if text_body is not None else json.dumps(payload or {})

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def json(self):
        if self._payload is None:
            raise ValueError("No JSON payload set")
        return self._payload

    async def text(self):
        return self._text


class FakeSession:
    """Fake aiohttp session that serves pre-defined responses."""

    def __init__(
        self,
        routes: dict[tuple[str, str], StubResponse | Callable[[dict | None], StubResponse]],
    ):
        self._routes = routes

    def _resolve(self, method: str, url: str, payload: dict | None = None) -> StubResponse:
        responder = self._routes.get((method, url))
        if responder is None:
            return StubResponse(404, {"error": "not found"})
        if callable(responder):
            return responder(payload)
        return responder

    def get(self, url: str):
        return self._resolve("GET", url)

    def post(self, url: str, json: dict):
        return self._resolve("POST", url, payload=json)

    async def close(self):
        return None


# =============================================================================
# Google Gemini Provider Tests
# =============================================================================


class TestGoogleProvider:
    """Tests for the Google Gemini provider implementation."""

    def test_google_provider_factory(self):
        """Test that factory returns GoogleProvider for GOOGLE type."""
        config = AIProviderConfig(provider_type=AIProviderType.GOOGLE, api_key="test-key")
        provider = get_ai_provider(config)

        from codeconcat.ai.providers.google_provider import GoogleProvider

        assert isinstance(provider, GoogleProvider)

    @pytest.mark.asyncio
    async def test_google_provider_initialization(self):
        """Test Google provider initialization with defaults."""
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "test-key"}):
            config = AIProviderConfig(provider_type=AIProviderType.GOOGLE)

            from codeconcat.ai.providers.google_provider import GoogleProvider

            provider = GoogleProvider(config)

            assert provider.config.api_key == "test-key"
            assert provider.config.model == "gemini-2.0-flash"

    @pytest.mark.asyncio
    async def test_google_provider_initialization_with_gemini_env(self):
        """Test Google provider uses GEMINI_API_KEY fallback."""
        with patch.dict("os.environ", {"GEMINI_API_KEY": "gemini-key"}, clear=True):
            config = AIProviderConfig(provider_type=AIProviderType.GOOGLE)

            from codeconcat.ai.providers.google_provider import GoogleProvider

            provider = GoogleProvider(config)

            assert provider.config.api_key == "gemini-key"

    @pytest.mark.asyncio
    async def test_google_summarize_code(self):
        """Test code summarization with mocked Google API response."""
        config = AIProviderConfig(
            provider_type=AIProviderType.GOOGLE,
            api_key="test-key",
            model="gemini-2.0-flash",
            cache_enabled=False,
        )

        from codeconcat.ai.providers.google_provider import GoogleProvider

        provider = GoogleProvider(config)

        # Mock the API call
        mock_response = {
            "text": "This function calculates the factorial of a number.",
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
            assert result.provider == "google"
            assert result.model_used == "gemini-2.0-flash"
            assert result.error is None

    @pytest.mark.asyncio
    async def test_google_summarize_function(self):
        """Test function summarization with Google provider."""
        config = AIProviderConfig(
            provider_type=AIProviderType.GOOGLE,
            api_key="test-key",
            model="gemini-2.0-flash",
            cache_enabled=False,
        )

        from codeconcat.ai.providers.google_provider import GoogleProvider

        provider = GoogleProvider(config)

        mock_response = {
            "text": "Adds two numbers together.",
            "usage": {"prompt_tokens": 30, "completion_tokens": 5, "total_tokens": 35},
        }

        with patch.object(provider, "_make_api_call", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_response

            result = await provider.summarize_function(
                "def add(a, b):\n    return a + b",
                "add",
                "python",
            )

            assert result.summary == "Adds two numbers together."
            assert result.provider == "google"
            assert result.error is None

    @pytest.mark.asyncio
    async def test_google_error_handling(self):
        """Test error handling in Google provider."""
        config = AIProviderConfig(
            provider_type=AIProviderType.GOOGLE,
            api_key="test-key",
            cache_enabled=False,
        )

        from codeconcat.ai.providers.google_provider import GoogleProvider

        provider = GoogleProvider(config)

        with patch.object(provider, "_make_api_call", new_callable=AsyncMock) as mock_api:
            mock_api.side_effect = Exception("API Error")

            result = await provider.summarize_code("test code", "python")

            assert result.summary == ""
            assert result.error == "API Error"
            assert result.provider == "google"

    @pytest.mark.asyncio
    async def test_google_get_model_info(self):
        """Test model info retrieval for Google provider."""
        config = AIProviderConfig(
            provider_type=AIProviderType.GOOGLE,
            api_key="test-key",
            model="gemini-2.0-flash",
        )

        from codeconcat.ai.providers.google_provider import GoogleProvider

        provider = GoogleProvider(config)
        info = await provider.get_model_info()

        assert info["provider"] == "google"
        assert info["model"] == "gemini-2.0-flash"
        assert "context_window" in info

    def test_google_provider_info(self):
        """Test get_provider_info returns correct Google info."""
        info = get_provider_info("google")

        assert info["name"] == "Google Gemini"
        assert info["requires_api_key"] is True
        assert info["supports_streaming"] is True
        assert info["pip_install"] == "google-genai"
        assert info["env_var"] == "GOOGLE_API_KEY"


# =============================================================================
# Zhipu GLM Provider Tests
# =============================================================================


class TestZhipuProvider:
    """Tests for the Zhipu GLM provider implementation."""

    def test_zhipu_provider_factory(self):
        """Test that factory returns ZhipuProvider for ZHIPU type."""
        config = AIProviderConfig(provider_type=AIProviderType.ZHIPU, api_key="test-key")
        provider = get_ai_provider(config)

        from codeconcat.ai.providers.zhipu_provider import ZhipuProvider

        assert isinstance(provider, ZhipuProvider)

    @pytest.mark.asyncio
    async def test_zhipu_provider_initialization(self):
        """Test Zhipu provider initialization with defaults."""
        with patch.dict("os.environ", {"ZHIPUAI_API_KEY": "test-key"}):
            config = AIProviderConfig(provider_type=AIProviderType.ZHIPU)

            from codeconcat.ai.providers.zhipu_provider import ZhipuProvider

            provider = ZhipuProvider(config)

            assert provider.config.api_key == "test-key"
            assert provider.config.model == "glm-4-flash"

    @pytest.mark.asyncio
    async def test_zhipu_provider_initialization_with_zhipu_env(self):
        """Test Zhipu provider uses ZHIPU_API_KEY fallback."""
        with patch.dict("os.environ", {"ZHIPU_API_KEY": "zhipu-key"}, clear=True):
            config = AIProviderConfig(provider_type=AIProviderType.ZHIPU)

            from codeconcat.ai.providers.zhipu_provider import ZhipuProvider

            provider = ZhipuProvider(config)

            assert provider.config.api_key == "zhipu-key"

    @pytest.mark.asyncio
    async def test_zhipu_summarize_code(self):
        """Test code summarization with mocked Zhipu API response."""
        config = AIProviderConfig(
            provider_type=AIProviderType.ZHIPU,
            api_key="test-key",
            model="glm-4-flash",
            cache_enabled=False,
        )

        from codeconcat.ai.providers.zhipu_provider import ZhipuProvider

        provider = ZhipuProvider(config)

        # Mock the API call (OpenAI-like format)
        mock_response = {
            "choices": [
                {"message": {"content": "This function calculates the factorial."}}
            ],
            "usage": {"prompt_tokens": 50, "completion_tokens": 10, "total_tokens": 60},
        }

        with patch.object(provider, "_make_api_call", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_response

            result = await provider.summarize_code(
                "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
                "python",
            )

            assert result.summary == "This function calculates the factorial."
            assert result.tokens_used == 60
            assert result.provider == "zhipu"
            assert result.model_used == "glm-4-flash"
            assert result.error is None

    @pytest.mark.asyncio
    async def test_zhipu_summarize_function(self):
        """Test function summarization with Zhipu provider."""
        config = AIProviderConfig(
            provider_type=AIProviderType.ZHIPU,
            api_key="test-key",
            model="glm-4-flash",
            cache_enabled=False,
        )

        from codeconcat.ai.providers.zhipu_provider import ZhipuProvider

        provider = ZhipuProvider(config)

        mock_response = {
            "choices": [{"message": {"content": "Multiplies two numbers."}}],
            "usage": {"prompt_tokens": 30, "completion_tokens": 5, "total_tokens": 35},
        }

        with patch.object(provider, "_make_api_call", new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_response

            result = await provider.summarize_function(
                "def multiply(a, b):\n    return a * b",
                "multiply",
                "python",
            )

            assert result.summary == "Multiplies two numbers."
            assert result.provider == "zhipu"
            assert result.error is None

    @pytest.mark.asyncio
    async def test_zhipu_error_handling(self):
        """Test error handling in Zhipu provider."""
        config = AIProviderConfig(
            provider_type=AIProviderType.ZHIPU,
            api_key="test-key",
            cache_enabled=False,
        )

        from codeconcat.ai.providers.zhipu_provider import ZhipuProvider

        provider = ZhipuProvider(config)

        with patch.object(provider, "_make_api_call", new_callable=AsyncMock) as mock_api:
            mock_api.side_effect = Exception("Zhipu API Error")

            result = await provider.summarize_code("test code", "python")

            assert result.summary == ""
            assert result.error == "Zhipu API Error"
            assert result.provider == "zhipu"

    @pytest.mark.asyncio
    async def test_zhipu_get_model_info(self):
        """Test model info retrieval for Zhipu provider."""
        config = AIProviderConfig(
            provider_type=AIProviderType.ZHIPU,
            api_key="test-key",
            model="glm-4",
        )

        from codeconcat.ai.providers.zhipu_provider import ZhipuProvider

        provider = ZhipuProvider(config)
        info = await provider.get_model_info()

        assert info["provider"] == "zhipu"
        assert info["model"] == "glm-4"
        assert "context_window" in info

    def test_zhipu_provider_info(self):
        """Test get_provider_info returns correct Zhipu info."""
        info = get_provider_info("zhipu")

        assert info["name"] == "Zhipu GLM"
        assert info["requires_api_key"] is True
        assert info["supports_streaming"] is True
        assert info["pip_install"] == "zhipuai"
        assert info["env_var"] == "ZHIPUAI_API_KEY"


# =============================================================================
# DeepSeek Provider Tests (via LocalServerProvider)
# =============================================================================


class TestDeepSeekProvider:
    """Tests for the DeepSeek provider (OpenAI-compatible via LocalServerProvider)."""

    def test_deepseek_provider_factory(self):
        """Test that factory returns LocalServerProvider for DEEPSEEK type."""
        config = AIProviderConfig(provider_type=AIProviderType.DEEPSEEK, api_key="test-key")
        provider = get_ai_provider(config)

        from codeconcat.ai.providers.local_server_provider import LocalServerProvider

        assert isinstance(provider, LocalServerProvider)

    @pytest.mark.asyncio
    async def test_deepseek_provider_initialization(self):
        """Test DeepSeek provider initialization with defaults."""
        with patch.dict("os.environ", {"DEEPSEEK_API_KEY": "test-key"}):
            config = AIProviderConfig(provider_type=AIProviderType.DEEPSEEK)

            from codeconcat.ai.providers.local_server_provider import LocalServerProvider

            provider = LocalServerProvider(config)

            assert provider.config.api_key == "test-key"
            assert provider.config.api_base == "https://api.deepseek.com"
            assert provider.config.model == "deepseek-coder"
            assert provider.server_kind == "DeepSeek"

    @pytest.mark.asyncio
    async def test_deepseek_summarize_code(self):
        """Test code summarization with DeepSeek provider."""
        api_base = "https://api.deepseek.com"
        routes = {
            ("GET", f"{api_base}/health"): StubResponse(200, {"status": "ok"}),
            ("GET", f"{api_base}/v1/models"): StubResponse(
                200,
                {"data": [{"id": "deepseek-coder"}, {"id": "deepseek-chat"}]},
            ),
            ("POST", f"{api_base}/v1/chat/completions"): lambda payload: StubResponse(
                200,
                {
                    "choices": [
                        {"message": {"content": f"DeepSeek summary for {payload['model']}"}}
                    ],
                    "usage": {"prompt_tokens": 50, "completion_tokens": 10, "total_tokens": 60},
                },
            ),
        }

        config = AIProviderConfig(
            provider_type=AIProviderType.DEEPSEEK,
            api_key="test-key",
            cache_enabled=False,
        )

        from codeconcat.ai.providers.local_server_provider import LocalServerProvider

        provider = LocalServerProvider(config)
        provider._session = FakeSession(routes)

        try:
            result = await provider.summarize_code("def test(): pass", "python")
            assert "DeepSeek" in result.summary
            assert result.provider == "deepseek"
            assert result.error is None
        finally:
            await provider.close()

    def test_deepseek_provider_info(self):
        """Test get_provider_info returns correct DeepSeek info."""
        info = get_provider_info("deepseek")

        assert info["name"] == "DeepSeek"
        assert info["requires_api_key"] is True
        assert info["supports_streaming"] is True
        assert info["env_var"] == "DEEPSEEK_API_KEY"


# =============================================================================
# MiniMax Provider Tests (via LocalServerProvider)
# =============================================================================


class TestMiniMaxProvider:
    """Tests for the MiniMax provider (OpenAI-compatible via LocalServerProvider)."""

    def test_minimax_provider_factory(self):
        """Test that factory returns LocalServerProvider for MINIMAX type."""
        config = AIProviderConfig(provider_type=AIProviderType.MINIMAX, api_key="test-key")
        provider = get_ai_provider(config)

        from codeconcat.ai.providers.local_server_provider import LocalServerProvider

        assert isinstance(provider, LocalServerProvider)

    @pytest.mark.asyncio
    async def test_minimax_provider_initialization(self):
        """Test MiniMax provider initialization with defaults."""
        with patch.dict("os.environ", {"MINIMAX_API_KEY": "test-key"}):
            config = AIProviderConfig(provider_type=AIProviderType.MINIMAX)

            from codeconcat.ai.providers.local_server_provider import LocalServerProvider

            provider = LocalServerProvider(config)

            assert provider.config.api_key == "test-key"
            assert provider.config.api_base == "https://api.minimax.chat/v1"
            assert provider.config.model == "MiniMax-Text-01"
            assert provider.server_kind == "MiniMax"

    @pytest.mark.asyncio
    async def test_minimax_summarize_code(self):
        """Test code summarization with MiniMax provider."""
        api_base = "https://api.minimax.chat/v1"
        routes = {
            ("GET", f"{api_base}/health"): StubResponse(200, {"status": "ok"}),
            ("GET", f"{api_base}/v1/models"): StubResponse(
                200,
                {"data": [{"id": "MiniMax-Text-01"}]},
            ),
            ("POST", f"{api_base}/v1/chat/completions"): lambda payload: StubResponse(
                200,
                {
                    "choices": [
                        {"message": {"content": f"MiniMax summary for {payload['model']}"}}
                    ],
                    "usage": {"prompt_tokens": 50, "completion_tokens": 10, "total_tokens": 60},
                },
            ),
        }

        config = AIProviderConfig(
            provider_type=AIProviderType.MINIMAX,
            api_key="test-key",
            cache_enabled=False,
        )

        from codeconcat.ai.providers.local_server_provider import LocalServerProvider

        provider = LocalServerProvider(config)
        provider._session = FakeSession(routes)

        try:
            result = await provider.summarize_code("def test(): pass", "python")
            assert "MiniMax" in result.summary
            assert result.provider == "minimax"
            assert result.error is None
        finally:
            await provider.close()

    def test_minimax_provider_info(self):
        """Test get_provider_info returns correct MiniMax info."""
        info = get_provider_info("minimax")

        assert info["name"] == "MiniMax"
        assert info["requires_api_key"] is True
        assert info["supports_streaming"] is True
        assert info["env_var"] == "MINIMAX_API_KEY"


# =============================================================================
# Qwen/DashScope Provider Tests (via LocalServerProvider)
# =============================================================================


class TestQwenProvider:
    """Tests for the Qwen provider (OpenAI-compatible via LocalServerProvider)."""

    def test_qwen_provider_factory(self):
        """Test that factory returns LocalServerProvider for QWEN type."""
        config = AIProviderConfig(provider_type=AIProviderType.QWEN, api_key="test-key")
        provider = get_ai_provider(config)

        from codeconcat.ai.providers.local_server_provider import LocalServerProvider

        assert isinstance(provider, LocalServerProvider)

    @pytest.mark.asyncio
    async def test_qwen_provider_initialization(self):
        """Test Qwen provider initialization with defaults."""
        with patch.dict("os.environ", {"DASHSCOPE_API_KEY": "test-key"}):
            config = AIProviderConfig(provider_type=AIProviderType.QWEN)

            from codeconcat.ai.providers.local_server_provider import LocalServerProvider

            provider = LocalServerProvider(config)

            assert provider.config.api_key == "test-key"
            assert provider.config.api_base == "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
            assert provider.config.model == "qwen-coder-plus"
            assert provider.server_kind == "Qwen/DashScope"

    @pytest.mark.asyncio
    async def test_qwen_summarize_code(self):
        """Test code summarization with Qwen provider."""
        api_base = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
        routes = {
            ("GET", f"{api_base}/health"): StubResponse(200, {"status": "ok"}),
            ("GET", f"{api_base}/v1/models"): StubResponse(
                200,
                {"data": [{"id": "qwen-coder-plus"}]},
            ),
            ("POST", f"{api_base}/v1/chat/completions"): lambda payload: StubResponse(
                200,
                {
                    "choices": [
                        {"message": {"content": f"Qwen summary for {payload['model']}"}}
                    ],
                    "usage": {"prompt_tokens": 50, "completion_tokens": 10, "total_tokens": 60},
                },
            ),
        }

        config = AIProviderConfig(
            provider_type=AIProviderType.QWEN,
            api_key="test-key",
            cache_enabled=False,
        )

        from codeconcat.ai.providers.local_server_provider import LocalServerProvider

        provider = LocalServerProvider(config)
        provider._session = FakeSession(routes)

        try:
            result = await provider.summarize_code("def test(): pass", "python")
            assert "Qwen" in result.summary
            assert result.provider == "qwen_dashscope"
            assert result.error is None
        finally:
            await provider.close()

    def test_qwen_provider_info(self):
        """Test get_provider_info returns correct Qwen info."""
        info = get_provider_info("qwen")

        assert info["name"] == "Qwen/DashScope"
        assert info["requires_api_key"] is True
        assert info["supports_streaming"] is True
        assert info["env_var"] == "DASHSCOPE_API_KEY"


# =============================================================================
# Cloud Provider Cost Calculation Tests
# =============================================================================


class TestCloudProviderCosts:
    """Tests for cost calculation in cloud providers."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "provider_type, expected_cost_gt_zero",
        [
            (AIProviderType.DEEPSEEK, True),
            (AIProviderType.MINIMAX, True),
            (AIProviderType.QWEN, True),
        ],
    )
    async def test_cloud_providers_calculate_costs(self, provider_type, expected_cost_gt_zero):
        """Test that cloud providers via LocalServerProvider calculate costs correctly."""
        config = AIProviderConfig(
            provider_type=provider_type,
            api_key="test-key",
            cost_per_1k_input_tokens=0.001,
            cost_per_1k_output_tokens=0.002,
            cache_enabled=False,
        )

        from codeconcat.ai.providers.local_server_provider import LocalServerProvider

        provider = LocalServerProvider(config)

        # Test cost calculation
        cost = provider._calculate_cost(1000, 500)

        if expected_cost_gt_zero:
            expected = (1000 / 1000) * 0.001 + (500 / 1000) * 0.002
            assert cost == expected
            assert cost > 0


# =============================================================================
# Provider Type Enum Tests
# =============================================================================


class TestNewProviderTypes:
    """Tests for the new provider types in AIProviderType enum."""

    def test_new_provider_types_exist(self):
        """Test that all new provider types exist in the enum."""
        assert hasattr(AIProviderType, "GOOGLE")
        assert hasattr(AIProviderType, "DEEPSEEK")
        assert hasattr(AIProviderType, "MINIMAX")
        assert hasattr(AIProviderType, "QWEN")
        assert hasattr(AIProviderType, "ZHIPU")

    def test_new_provider_type_values(self):
        """Test that new provider types have correct string values."""
        assert AIProviderType.GOOGLE.value == "google"
        assert AIProviderType.DEEPSEEK.value == "deepseek"
        assert AIProviderType.MINIMAX.value == "minimax"
        assert AIProviderType.QWEN.value == "qwen"
        assert AIProviderType.ZHIPU.value == "zhipu"


# =============================================================================
# Provider Exports Tests
# =============================================================================


class TestProviderExports:
    """Tests for provider module exports."""

    def test_google_provider_exported(self):
        """Test that GoogleProvider is exported from providers module."""
        from codeconcat.ai.providers import GoogleProvider

        assert GoogleProvider is not None

    def test_zhipu_provider_exported(self):
        """Test that ZhipuProvider is exported from providers module."""
        from codeconcat.ai.providers import ZhipuProvider

        assert ZhipuProvider is not None

    def test_all_exports_available(self):
        """Test that all expected providers are in __all__."""
        from codeconcat.ai import providers

        assert "GoogleProvider" in providers.__all__
        assert "ZhipuProvider" in providers.__all__
        assert "LocalServerProvider" in providers.__all__
