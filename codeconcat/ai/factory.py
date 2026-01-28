"""Factory for creating AI provider instances."""

from typing import Any

from .base import AIProvider, AIProviderConfig, AIProviderType

_PROVIDER_REGISTRY: dict[AIProviderType, type[AIProvider]] = {}


def register_provider(provider_type: AIProviderType):
    """Decorator to register an AI provider class.

    Args:
        provider_type: The type of provider to register

    Returns:
        Decorator function that registers the provider class

    Example:
        @register_provider(AIProviderType.OPENAI)
        class OpenAIProvider(AIProvider):
            ...
    """

    def decorator(cls: type[AIProvider]):
        """Register the decorated class as a provider.

        Args:
            cls: The provider class to register

        Returns:
            The same class, unmodified
        """
        _PROVIDER_REGISTRY[provider_type] = cls
        return cls

    return decorator


def get_ai_provider(config: AIProviderConfig) -> AIProvider:
    """Create an AI provider instance based on configuration.

    Args:
        config: Provider configuration

    Returns:
        Configured AI provider instance

    Raises:
        ValueError: If provider type is not supported or not available
    """
    # Lazy import providers to avoid circular dependencies and optional deps
    if config.provider_type == AIProviderType.OPENAI:
        from .providers.openai_provider import OpenAIProvider

        return OpenAIProvider(config)

    elif config.provider_type == AIProviderType.ANTHROPIC:
        from .providers.anthropic_provider import AnthropicProvider

        return AnthropicProvider(config)

    elif config.provider_type == AIProviderType.OPENROUTER:
        from .providers.openrouter_provider import OpenRouterProvider

        return OpenRouterProvider(config)

    elif config.provider_type == AIProviderType.OLLAMA:
        from .providers.ollama_provider import OllamaProvider

        return OllamaProvider(config)

    elif config.provider_type == AIProviderType.LLAMACPP:
        from .providers.llamacpp_provider import LlamaCppProvider

        return LlamaCppProvider(config)

    elif config.provider_type in {
        AIProviderType.LOCAL_SERVER,
        AIProviderType.VLLM,
        AIProviderType.LMSTUDIO,
        AIProviderType.LLAMACPP_SERVER,
    }:
        from .providers.local_server_provider import LocalServerProvider

        return LocalServerProvider(config)

    else:
        raise ValueError(f"Unsupported provider type: {config.provider_type}")


def list_available_providers() -> list[str]:
    """List all available AI providers.

    Returns:
        List of provider names that can be used
    """
    available = []

    # Check for OpenAI
    import importlib.util

    if importlib.util.find_spec("openai") is not None:
        available.append("openai")

    # Check for Anthropic
    if importlib.util.find_spec("anthropic") is not None:
        available.append("anthropic")

    # OpenRouter uses standard HTTP, always available
    available.append("openrouter")

    # Check for Ollama (uses HTTP but check if server is reachable)
    import os

    try:
        import requests  # type: ignore[import-untyped]
    except ImportError:
        requests = None  # type: ignore

    if requests is not None:
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        try:
            response = requests.get(f"{ollama_host.rstrip('/')}/api/tags", timeout=1)
            response.raise_for_status()  # Raises an exception for 4xx/5xx status codes
            available.append("ollama")
        except requests.exceptions.RequestException:
            # This will catch connection errors, timeouts, and bad status codes
            pass

    # Check for llama-cpp-python
    if importlib.util.find_spec("llama_cpp") is not None:
        available.append("llamacpp")

    # Local server presets are always available (uses standard HTTP)
    available.extend(["local_server", "vllm", "lmstudio", "llamacpp_server"])

    return available


def get_provider_info(provider_name: str) -> dict[str, Any]:
    """Get information about a specific provider.

    Args:
        provider_name: Name of the provider

    Returns:
        Dictionary with provider information
    """
    from .models_config import MODEL_CONFIGS

    # Get models for this provider from models_config
    provider_models = [
        config.model_id for config in MODEL_CONFIGS.values() if config.provider == provider_name
    ]

    # Define provider metadata
    info = {
        "openai": {
            "name": "OpenAI",
            "models": provider_models
            if provider_models
            else ["gpt-5-nano-2025-08-07", "gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
            "requires_api_key": True,
            "supports_streaming": True,
            "supports_function_calling": True,
            "pip_install": "openai",
            "env_var": "OPENAI_API_KEY",
        },
        "anthropic": {
            "name": "Anthropic",
            "models": provider_models
            if provider_models
            else [
                "claude-3-5-haiku-latest",
                "claude-3-haiku-20240307",
                "claude-3-sonnet-20240229",
                "claude-3-opus-20240229",
            ],
            "requires_api_key": True,
            "supports_streaming": True,
            "supports_function_calling": False,
            "pip_install": "anthropic",
            "env_var": "ANTHROPIC_API_KEY",
        },
        "openrouter": {
            "name": "OpenRouter",
            "models": provider_models if provider_models else ["varies - see openrouter.ai/models"],
            "requires_api_key": True,
            "supports_streaming": True,
            "supports_function_calling": True,
            "pip_install": None,
            "env_var": "OPENROUTER_API_KEY",
        },
        "ollama": {
            "name": "Ollama",
            "models": provider_models
            if provider_models
            else ["llama3.2", "mistral", "codellama", "deepseek-coder"],
            "requires_api_key": False,
            "supports_streaming": True,
            "supports_function_calling": False,
            "pip_install": None,
            "env_var": None,
            "notes": "Requires Ollama server running locally",
        },
        "google": {
            "name": "Google Gemini",
            "models": provider_models
            if provider_models
            else ["gemini-2.5-pro", "gemini-1.5-flash"],
            "requires_api_key": True,
            "supports_streaming": True,
            "supports_function_calling": True,
            "pip_install": "google-generativeai",
            "env_var": "GOOGLE_API_KEY",
        },
        "llamacpp": {
            "name": "Llama.cpp",
            "models": ["depends on loaded model file"],
            "requires_api_key": False,
            "supports_streaming": True,
            "supports_function_calling": False,
            "pip_install": "llama-cpp-python",
            "env_var": None,
            "notes": "Deprecated direct integration. Use 'llamacpp_server' preset instead.",
        },
        "local_server": {
            "name": "OpenAI-Compatible Local Server",
            "models": ["depends on server configuration"],
            "requires_api_key": False,
            "supports_streaming": True,
            "supports_function_calling": True,
            "pip_install": None,
            "env_var": "LOCAL_LLM_API_KEY",
            "notes": "Supports vLLM, LM Studio, llama.cpp server, and other OpenAI-compatible runtimes",
        },
        "vllm": {
            "name": "vLLM Server",
            "models": ["auto-discovered from server"],
            "requires_api_key": False,
            "supports_streaming": True,
            "supports_function_calling": True,
            "pip_install": None,
            "env_var": "VLLM_API_KEY",
            "notes": "Defaults to http://localhost:8000; uses LocalServerProvider",
        },
        "lmstudio": {
            "name": "LM Studio",
            "models": ["auto-discovered from server"],
            "requires_api_key": False,
            "supports_streaming": True,
            "supports_function_calling": True,
            "pip_install": None,
            "env_var": "LMSTUDIO_API_KEY",
            "notes": "Defaults to http://localhost:1234; uses LocalServerProvider",
        },
        "llamacpp_server": {
            "name": "llama.cpp Server",
            "models": ["auto-discovered from server"],
            "requires_api_key": False,
            "supports_streaming": True,
            "supports_function_calling": True,
            "pip_install": None,
            "env_var": "LLAMACPP_SERVER_API_KEY",
            "notes": "Defaults to http://localhost:8080; uses LocalServerProvider",
        },
    }

    return info.get(provider_name, {})
