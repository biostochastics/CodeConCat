"""Model configurations with current pricing and defaults for AI providers."""

from dataclasses import dataclass
from enum import Enum


class ModelTier(Enum):
    """Model pricing tiers."""

    BUDGET = "budget"  # Cheapest models
    STANDARD = "standard"  # Good balance
    PREMIUM = "premium"  # High quality
    FLAGSHIP = "flagship"  # Best available


@dataclass
class ModelConfig:
    """Configuration for a specific AI model."""

    provider: str
    model_id: str
    display_name: str
    tier: ModelTier
    context_window: int
    max_output: int
    cost_per_1k_input: float  # in USD
    cost_per_1k_output: float  # in USD
    supports_functions: bool = False
    supports_vision: bool = False
    supports_streaming: bool = True
    tokenizer: str | None = None  # tiktoken model or custom
    notes: str | None = None


# Current model configurations (as of 2025)
MODEL_CONFIGS = {
    # OpenAI Models (2025)
    "gpt-5": ModelConfig(
        provider="openai",
        model_id="gpt-5",
        display_name="GPT-5",
        tier=ModelTier.FLAGSHIP,
        context_window=400000,
        max_output=32768,
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.03,
        supports_functions=True,
        supports_vision=True,
        tokenizer="o200k_base",
        notes="Latest flagship OpenAI model (2025)",
    ),
    "gpt-5-nano-2025-08-07": ModelConfig(
        provider="openai",
        model_id="gpt-5-nano-2025-08-07",
        display_name="GPT-5 Nano",
        tier=ModelTier.BUDGET,
        context_window=128000,
        max_output=16384,
        cost_per_1k_input=0.00010,
        cost_per_1k_output=0.0004,
        supports_functions=True,
        supports_vision=True,
        tokenizer="o200k_base",
        notes="Latest budget GPT-5 variant (August 2025)",
    ),
    "gpt-4o-nano": ModelConfig(
        provider="openai",
        model_id="gpt-4o-nano",
        display_name="GPT-4o Nano",
        tier=ModelTier.BUDGET,
        context_window=128000,
        max_output=16384,
        cost_per_1k_input=0.00010,
        cost_per_1k_output=0.0004,
        supports_functions=True,
        supports_vision=True,
        tokenizer="o200k_base",
        notes="Legacy budget model, use gpt-5-nano-2025-08-07 instead",
    ),
    "gpt-4o-mini": ModelConfig(
        provider="openai",
        model_id="gpt-4o-mini",
        display_name="GPT-4o Mini",
        tier=ModelTier.BUDGET,
        context_window=128000,
        max_output=16384,
        cost_per_1k_input=0.00015,
        cost_per_1k_output=0.0006,
        supports_functions=True,
        supports_vision=True,
        tokenizer="o200k_base",
        notes="Cost-effective OpenAI model",
    ),
    "gpt-4o": ModelConfig(
        provider="openai",
        model_id="gpt-4o",
        display_name="GPT-4o",
        tier=ModelTier.PREMIUM,
        context_window=128000,
        max_output=16384,
        cost_per_1k_input=0.0025,
        cost_per_1k_output=0.01,
        supports_functions=True,
        supports_vision=True,
        tokenizer="o200k_base",
        notes="Standard GPT-4 optimized model",
    ),
    "gpt-3.5-turbo": ModelConfig(
        provider="openai",
        model_id="gpt-3.5-turbo",
        display_name="GPT-3.5 Turbo",
        tier=ModelTier.BUDGET,
        context_window=16385,
        max_output=4096,
        cost_per_1k_input=0.0005,
        cost_per_1k_output=0.0015,
        supports_functions=True,
        tokenizer="cl100k_base",
        notes="Legacy model, consider gpt-4o-nano instead",
    ),
    # Anthropic Models (2025)
    "claude-3-5-haiku-latest": ModelConfig(
        provider="anthropic",
        model_id="claude-3-5-haiku-latest",
        display_name="Claude 3.5 Haiku (Latest)",
        tier=ModelTier.BUDGET,
        context_window=200000,
        max_output=8192,
        cost_per_1k_input=0.0008,
        cost_per_1k_output=0.004,
        supports_vision=True,
        tokenizer="claude",
        notes="Latest Claude 3.5 Haiku - fastest and cheapest",
    ),
    "claude-haiku-4.1": ModelConfig(
        provider="anthropic",
        model_id="claude-haiku-4.1",
        display_name="Claude Haiku 4.1",
        tier=ModelTier.BUDGET,
        context_window=200000,
        max_output=8192,
        cost_per_1k_input=0.0008,
        cost_per_1k_output=0.004,
        supports_vision=True,
        tokenizer="claude",
        notes="Legacy alias, use claude-3-5-haiku-latest instead",
    ),
    "claude-sonnet-4.1": ModelConfig(
        provider="anthropic",
        model_id="claude-sonnet-4.1",
        display_name="Claude Sonnet 4.1",
        tier=ModelTier.STANDARD,
        context_window=200000,
        max_output=8192,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        supports_vision=True,
        tokenizer="claude",
        notes="Best balance Claude model (2025)",
    ),
    "claude-3-haiku-20240307": ModelConfig(
        provider="anthropic",
        model_id="claude-3-haiku-20240307",
        display_name="Claude 3 Haiku",
        tier=ModelTier.BUDGET,
        context_window=200000,
        max_output=8192,
        cost_per_1k_input=0.00025,
        cost_per_1k_output=0.00125,
        supports_vision=True,
        tokenizer="claude",
        notes="Previous generation Haiku",
    ),
    "claude-3-opus-20240229": ModelConfig(
        provider="anthropic",
        model_id="claude-3-opus-20240229",
        display_name="Claude 3 Opus",
        tier=ModelTier.FLAGSHIP,
        context_window=200000,
        max_output=4096,
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
        supports_vision=True,
        tokenizer="claude",
        notes="Most capable Claude model",
    ),
    # Google Models (2025)
    "google/gemini-2.5-pro": ModelConfig(
        provider="google",
        model_id="google/gemini-2.5-pro",
        display_name="Gemini 2.5 Pro",
        tier=ModelTier.STANDARD,
        context_window=2097152,
        max_output=8192,
        cost_per_1k_input=0.00125,
        cost_per_1k_output=0.005,
        supports_functions=True,
        supports_vision=True,
        tokenizer="gemini",
        notes="Latest Gemini Pro with 2M context (2025)",
    ),
    "google/gemini-2.5-flash": ModelConfig(
        provider="google",
        model_id="google/gemini-2.5-flash",
        display_name="Gemini 2.5 Flash",
        tier=ModelTier.BUDGET,
        context_window=1048576,
        max_output=8192,
        cost_per_1k_input=0.000075,
        cost_per_1k_output=0.0003,
        supports_functions=True,
        supports_vision=True,
        tokenizer="gemini",
        notes="Latest Flash model with 1M context (2025)",
    ),
    "gemini-2.0-flash-exp": ModelConfig(
        provider="google",
        model_id="gemini-2.0-flash-exp",
        display_name="Gemini 2.0 Flash Experimental",
        tier=ModelTier.BUDGET,
        context_window=1048576,
        max_output=8192,
        cost_per_1k_input=0.0,  # Free during experimental phase
        cost_per_1k_output=0.0,
        supports_functions=True,
        supports_vision=True,
        tokenizer="gemini",
        notes="Free experimental model with 1M context",
    ),
    # OpenRouter Exclusive Models (2025)
    "z-ai/glm-4.5": ModelConfig(
        provider="openrouter",
        model_id="z-ai/glm-4.5",
        display_name="Z-AI GLM-4.5",
        tier=ModelTier.BUDGET,
        context_window=128000,
        max_output=4096,
        cost_per_1k_input=0.0004,
        cost_per_1k_output=0.0016,
        tokenizer="gpt2",  # Fallback tokenizer
        notes="Z-AI model, excellent for multilingual (2025)",
    ),
    "qwen/qwq-32b-preview": ModelConfig(
        provider="openrouter",
        model_id="qwen/qwq-32b-preview",
        display_name="Qwen QwQ 32B Preview",
        tier=ModelTier.STANDARD,
        context_window=32768,
        max_output=4096,
        cost_per_1k_input=0.00018,
        cost_per_1k_output=0.00018,
        tokenizer="gpt2",
        notes="Qwen's reasoning model - strong on logic and math (2025)",
    ),
    "openrouter/gpt-5": ModelConfig(
        provider="openrouter",
        model_id="openai/gpt-5",
        display_name="GPT-5 (via OpenRouter)",
        tier=ModelTier.FLAGSHIP,
        context_window=400000,
        max_output=32768,
        cost_per_1k_input=0.01,
        cost_per_1k_output=0.03,
        supports_functions=True,
        supports_vision=True,
        tokenizer="o200k_base",
        notes="GPT-5 accessed via OpenRouter (2025)",
    ),
    "openrouter/claude-haiku-4.1": ModelConfig(
        provider="openrouter",
        model_id="anthropic/claude-haiku-4.1",
        display_name="Claude Haiku 4.1 (via OpenRouter)",
        tier=ModelTier.BUDGET,
        context_window=200000,
        max_output=8192,
        cost_per_1k_input=0.0008,
        cost_per_1k_output=0.004,
        supports_vision=True,
        tokenizer="claude",
        notes="Haiku 4.1 via OpenRouter (2025)",
    ),
    "openrouter/claude-sonnet-4.1": ModelConfig(
        provider="openrouter",
        model_id="anthropic/claude-sonnet-4.1",
        display_name="Claude Sonnet 4.1 (via OpenRouter)",
        tier=ModelTier.STANDARD,
        context_window=200000,
        max_output=8192,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        supports_vision=True,
        tokenizer="claude",
        notes="Sonnet 4.1 via OpenRouter (2025)",
    ),
    "openrouter/deepseek/deepseek-chat": ModelConfig(
        provider="openrouter",
        model_id="deepseek/deepseek-chat",
        display_name="DeepSeek Chat",
        tier=ModelTier.BUDGET,
        context_window=64000,
        max_output=4096,
        cost_per_1k_input=0.00014,
        cost_per_1k_output=0.00028,
        tokenizer="gpt2",
        notes="Very cheap alternative model",
    ),
    "openrouter/mistralai/mistral-7b-instruct": ModelConfig(
        provider="openrouter",
        model_id="mistralai/mistral-7b-instruct",
        display_name="Mistral 7B Instruct (Free)",
        tier=ModelTier.BUDGET,
        context_window=32768,
        max_output=4096,
        cost_per_1k_input=0.0,  # Free tier
        cost_per_1k_output=0.0,
        tokenizer="gpt2",
        notes="Free model, good for testing",
    ),
    # Local Models
    "ollama/llama3.2": ModelConfig(
        provider="ollama",
        model_id="llama3.2",
        display_name="Llama 3.2 (Local)",
        tier=ModelTier.BUDGET,
        context_window=128000,
        max_output=4096,
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        tokenizer="llama",
        notes="Local model, no API costs",
    ),
    # DeepSeek Models (2025) - OpenAI-compatible API
    "deepseek-chat": ModelConfig(
        provider="deepseek",
        model_id="deepseek-chat",
        display_name="DeepSeek Chat",
        tier=ModelTier.BUDGET,
        context_window=64000,
        max_output=8192,
        cost_per_1k_input=0.00014,
        cost_per_1k_output=0.00028,
        supports_functions=True,
        tokenizer="gpt2",
        notes="DeepSeek's general-purpose chat model - extremely cost-effective",
    ),
    "deepseek-coder": ModelConfig(
        provider="deepseek",
        model_id="deepseek-coder",
        display_name="DeepSeek Coder",
        tier=ModelTier.BUDGET,
        context_window=64000,
        max_output=8192,
        cost_per_1k_input=0.00014,
        cost_per_1k_output=0.00028,
        supports_functions=True,
        tokenizer="gpt2",
        notes="DeepSeek's code-specialized model - excellent for code tasks",
    ),
    "deepseek-reasoner": ModelConfig(
        provider="deepseek",
        model_id="deepseek-reasoner",
        display_name="DeepSeek Reasoner",
        tier=ModelTier.STANDARD,
        context_window=64000,
        max_output=8192,
        cost_per_1k_input=0.00055,
        cost_per_1k_output=0.00219,
        supports_functions=True,
        tokenizer="gpt2",
        notes="DeepSeek R1 reasoning model - chain-of-thought capabilities",
    ),
    # MiniMax Models (2025) - OpenAI-compatible API
    "minimax-m2": ModelConfig(
        provider="minimax",
        model_id="MiniMax-Text-01",
        display_name="MiniMax M2",
        tier=ModelTier.STANDARD,
        context_window=1000000,
        max_output=16384,
        cost_per_1k_input=0.0004,
        cost_per_1k_output=0.0016,
        supports_functions=True,
        tokenizer="gpt2",
        notes="MiniMax's flagship model with 1M context window",
    ),
    "minimax-m1": ModelConfig(
        provider="minimax",
        model_id="abab6.5s-chat",
        display_name="MiniMax M1",
        tier=ModelTier.BUDGET,
        context_window=245760,
        max_output=8192,
        cost_per_1k_input=0.0001,
        cost_per_1k_output=0.0001,
        supports_functions=True,
        tokenizer="gpt2",
        notes="MiniMax's efficient model - good balance of cost and quality",
    ),
    # Qwen/DashScope Models (2025) - OpenAI-compatible API
    "qwen-coder-plus": ModelConfig(
        provider="qwen",
        model_id="qwen-coder-plus",
        display_name="Qwen Coder Plus",
        tier=ModelTier.STANDARD,
        context_window=131072,
        max_output=16384,
        cost_per_1k_input=0.0008,
        cost_per_1k_output=0.0024,
        supports_functions=True,
        tokenizer="gpt2",
        notes="Qwen's premium code model - excellent for complex code tasks",
    ),
    "qwen-coder-turbo": ModelConfig(
        provider="qwen",
        model_id="qwen-coder-turbo",
        display_name="Qwen Coder Turbo",
        tier=ModelTier.BUDGET,
        context_window=131072,
        max_output=16384,
        cost_per_1k_input=0.0002,
        cost_per_1k_output=0.0006,
        supports_functions=True,
        tokenizer="gpt2",
        notes="Qwen's fast code model - good for quick tasks",
    ),
    "qwen3-235b-instruct": ModelConfig(
        provider="qwen",
        model_id="qwen3-235b-a22b",
        display_name="Qwen3 235B Instruct",
        tier=ModelTier.FLAGSHIP,
        context_window=131072,
        max_output=16384,
        cost_per_1k_input=0.002,
        cost_per_1k_output=0.006,
        supports_functions=True,
        tokenizer="gpt2",
        notes="Qwen's flagship model - MoE architecture with top performance",
    ),
    # Google Gemini Models (direct API - 2025)
    "gemini-2.5-pro": ModelConfig(
        provider="google",
        model_id="gemini-2.5-pro-preview-05-06",
        display_name="Gemini 2.5 Pro",
        tier=ModelTier.STANDARD,
        context_window=1048576,
        max_output=65536,
        cost_per_1k_input=0.00125,
        cost_per_1k_output=0.005,
        supports_functions=True,
        supports_vision=True,
        tokenizer="gemini",
        notes="Google's latest Pro model with thinking capabilities (direct API)",
    ),
    "gemini-2.0-flash": ModelConfig(
        provider="google",
        model_id="gemini-2.0-flash",
        display_name="Gemini 2.0 Flash",
        tier=ModelTier.BUDGET,
        context_window=1048576,
        max_output=8192,
        cost_per_1k_input=0.0,  # Free tier available
        cost_per_1k_output=0.0,
        supports_functions=True,
        supports_vision=True,
        tokenizer="gemini",
        notes="Google's fast model - free tier available (direct API)",
    ),
    "gemini-1.5-flash": ModelConfig(
        provider="google",
        model_id="gemini-1.5-flash",
        display_name="Gemini 1.5 Flash",
        tier=ModelTier.BUDGET,
        context_window=1048576,
        max_output=8192,
        cost_per_1k_input=0.000075,
        cost_per_1k_output=0.0003,
        supports_functions=True,
        supports_vision=True,
        tokenizer="gemini",
        notes="Google's efficient 1.5 model (direct API)",
    ),
    # Zhipu GLM Models (2025) - Native API
    "glm-4": ModelConfig(
        provider="zhipu",
        model_id="glm-4",
        display_name="GLM-4",
        tier=ModelTier.STANDARD,
        context_window=128000,
        max_output=4096,
        cost_per_1k_input=0.0014,
        cost_per_1k_output=0.0014,
        supports_functions=True,
        tokenizer="gpt2",
        notes="Zhipu's flagship model - strong multilingual capabilities",
    ),
    "glm-4-plus": ModelConfig(
        provider="zhipu",
        model_id="glm-4-plus",
        display_name="GLM-4 Plus",
        tier=ModelTier.PREMIUM,
        context_window=128000,
        max_output=4096,
        cost_per_1k_input=0.007,
        cost_per_1k_output=0.007,
        supports_functions=True,
        tokenizer="gpt2",
        notes="Zhipu's premium model with extended thinking",
    ),
    "glm-4-flash": ModelConfig(
        provider="zhipu",
        model_id="glm-4-flash",
        display_name="GLM-4 Flash",
        tier=ModelTier.BUDGET,
        context_window=128000,
        max_output=4096,
        cost_per_1k_input=0.0001,
        cost_per_1k_output=0.0001,
        supports_functions=True,
        tokenizer="gpt2",
        notes="Zhipu's efficient model - excellent cost-performance ratio",
    ),
    "codegeex-4": ModelConfig(
        provider="zhipu",
        model_id="codegeex-4",
        display_name="CodeGeeX-4",
        tier=ModelTier.BUDGET,
        context_window=128000,
        max_output=4096,
        cost_per_1k_input=0.0001,
        cost_per_1k_output=0.0001,
        supports_functions=True,
        tokenizer="gpt2",
        notes="Zhipu's code-specialized model - free for developers",
    ),
}


# Default model selections by use case (2025)
DEFAULT_MODELS = {
    "budget": [
        "gpt-5-nano-2025-08-07",  # OpenAI latest budget (Aug 2025)
        "claude-3-5-haiku-latest",  # Anthropic latest Haiku
        "gemini-2.0-flash",  # Google free tier (direct API)
        "deepseek-coder",  # DeepSeek extremely cheap
        "qwen-coder-turbo",  # Qwen fast and cheap
        "glm-4-flash",  # Zhipu efficient
    ],
    "standard": [
        "claude-sonnet-4.1",  # Best balance (2025)
        "gpt-4o",  # OpenAI standard
        "gemini-2.5-pro",  # Google standard (direct API)
        "qwen-coder-plus",  # Qwen code specialist
        "glm-4",  # Zhipu standard
        "minimax-m2",  # MiniMax 1M context
    ],
    "premium": [
        "gpt-5",  # OpenAI flagship (2025)
        "claude-3-opus-20240229",  # Claude most capable
        "qwen3-235b-instruct",  # Qwen flagship
        "glm-4-plus",  # Zhipu premium
    ],
    "free": [
        "gemini-2.0-flash",  # Google free tier
        "openrouter/mistralai/mistral-7b-instruct",  # Free tier
        "ollama/llama3.2",  # Local
        "codegeex-4",  # Zhipu code model (free for devs)
    ],
    "code_review": [
        "deepseek-coder",  # Excellent for code, very cheap
        "qwen-coder-plus",  # Premium code model
        "codegeex-4",  # Zhipu code specialist
        "gemini-2.0-flash",  # Free with good code understanding
    ],
}


def get_model_config(model_id: str) -> ModelConfig | None:
    """Get configuration for a specific model.

    Args:
        model_id: Model identifier

    Returns:
        ModelConfig or None if not found
    """
    # Direct lookup
    if model_id in MODEL_CONFIGS:
        return MODEL_CONFIGS[model_id]

    # Try with openrouter prefix
    if f"openrouter/{model_id}" in MODEL_CONFIGS:
        return MODEL_CONFIGS[f"openrouter/{model_id}"]

    return None


def get_cheapest_model(provider: str | None = None, min_context: int = 16000) -> ModelConfig | None:
    """Get the cheapest available model.

    Args:
        provider: Optional provider filter
        min_context: Minimum context window required

    Returns:
        Cheapest ModelConfig meeting requirements
    """
    candidates = []

    for config in MODEL_CONFIGS.values():
        if provider and config.provider != provider:
            continue
        if config.context_window < min_context:
            continue

        total_cost = config.cost_per_1k_input + config.cost_per_1k_output
        candidates.append((total_cost, config))

    if candidates:
        return min(candidates, key=lambda x: x[0])[1]

    return None


def get_models_by_tier(tier: ModelTier) -> list[ModelConfig]:
    """Get all models in a specific tier.

    Args:
        tier: Model tier to filter by

    Returns:
        List of ModelConfig objects
    """
    return [config for config in MODEL_CONFIGS.values() if config.tier == tier]


def estimate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost for a specific model usage.

    Args:
        model_id: Model identifier
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        Estimated cost in USD
    """
    config = get_model_config(model_id)
    if not config:
        return 0.0

    input_cost = (input_tokens / 1000) * config.cost_per_1k_input
    output_cost = (output_tokens / 1000) * config.cost_per_1k_output

    return input_cost + output_cost
