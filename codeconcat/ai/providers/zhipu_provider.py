"""Zhipu GLM provider implementation for code summarization."""

import asyncio
import logging
import os
from typing import Any

from ..base import AIProvider, AIProviderConfig, SummarizationResult
from ..cache import SummaryCache

logger = logging.getLogger(__name__)


class ZhipuProvider(AIProvider):
    """Zhipu GLM API provider for code summarization.

    Supports GLM-4, GLM-4-Plus, GLM-4-Flash, and CodeGeeX-4 models.
    Uses the official zhipuai SDK.
    """

    def __init__(self, config: AIProviderConfig):
        """Initialize Zhipu GLM provider."""
        super().__init__(config)
        logger.info(f"Initializing Zhipu GLM provider with model: {config.model}")

        # Set defaults for Zhipu
        if not config.api_key:
            config.api_key = os.getenv("ZHIPUAI_API_KEY") or os.getenv("ZHIPU_API_KEY")
            logger.debug(f"API key loaded from env: {bool(config.api_key)}")

        if not config.model:
            config.model = "glm-4-flash"  # Efficient default
            logger.debug(f"Using default model: {config.model}")

        # Set costs from models_config if not specified
        if config.cost_per_1k_input_tokens == 0:
            from ..models_config import get_model_config

            model_cfg = get_model_config(config.model)
            if model_cfg:
                config.cost_per_1k_input_tokens = model_cfg.cost_per_1k_input
                config.cost_per_1k_output_tokens = model_cfg.cost_per_1k_output

        self.cache = SummaryCache() if config.cache_enabled else None

        # Rate limiting for Zhipu API
        self._rate_limit_delay = 0.3  # seconds between requests
        self._last_request_time = 0.0
        self._rate_limit_lock = asyncio.Lock()
        self._concurrent_limit = asyncio.Semaphore(10)  # Max 10 concurrent requests

        # Lazy-load the client
        self._client = None

        logger.info(
            f"Zhipu GLM provider initialized - Model: {config.model}, "
            f"Cache: {bool(self.cache)}, API Key: {bool(config.api_key)}"
        )

    def _get_client(self):
        """Get or create the Zhipu AI client."""
        if self._client is None:
            try:
                from zhipuai import ZhipuAI  # type: ignore[import-untyped]

                self._client = ZhipuAI(api_key=self.config.api_key)

            except ImportError as err:
                raise ImportError(
                    "zhipuai package is required for Zhipu GLM support. "
                    "Install it with: pip install zhipuai"
                ) from err

        return self._client

    async def _make_api_call(
        self, messages: list[dict[str, str]], max_tokens: int | None = None
    ) -> dict:
        """Make an API call to Zhipu GLM with rate limiting."""
        import time

        # Use semaphore to limit concurrent requests and enforce minimum delay
        async with self._concurrent_limit, self._rate_limit_lock:
            now = time.time()
            time_since_last = now - self._last_request_time
            if time_since_last < self._rate_limit_delay:
                wait_time = self._rate_limit_delay - time_since_last
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
            self._last_request_time = time.time()

        client = self._get_client()

        logger.info(f"Making Zhipu GLM API call with model {self.config.model}")
        logger.debug(f"Messages: {len(messages)} msgs, max_tokens: {max_tokens}")

        # Run the synchronous API call in a thread pool
        loop = asyncio.get_event_loop()

        def make_request():
            return client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
            )

        response = await loop.run_in_executor(None, make_request)

        # Extract response data (OpenAI-like format)
        result = {
            "choices": [
                {
                    "message": {
                        "content": response.choices[0].message.content if response.choices else ""
                    }
                }
            ],
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
        }

        logger.info(f"Zhipu GLM API call successful - tokens used: {result['usage']}")
        return result

    async def summarize_code(
        self,
        code: str,
        language: str,
        context: dict[str, Any] | None = None,
        max_length: int | None = None,
    ) -> SummarizationResult:
        """Generate a summary for a code file using Zhipu GLM."""
        # Check cache first
        if self.cache:
            cache_key = self.cache.generate_key(
                code, "zhipu", self.config.model, "summarize_code", language=language
            )
            cached_summary = await self.cache.get(cache_key)
            if cached_summary:
                logger.info(f"Cache hit for {language} code - returning cached summary")
                return SummarizationResult(
                    summary=cached_summary,
                    model_used=self.config.model,
                    provider="zhipu",
                    cached=True,
                )

        # Create the prompt
        system_prompt = getattr(
            self,
            "SYSTEM_PROMPT_CODE_SUMMARY",
            "You are a helpful assistant that creates concise, informative code summaries.",
        )
        user_prompt = self._create_code_summary_prompt(code, language, context)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            # Make API call with retry
            response = await self._retry_with_backoff(self._make_api_call, messages, max_length)

            # Extract summary and token usage
            summary = response["choices"][0]["message"]["content"].strip()
            usage = response["usage"]
            tokens_used = usage["total_tokens"]
            input_tokens = usage["prompt_tokens"]
            output_tokens = usage["completion_tokens"]

            # Calculate cost
            cost = self._calculate_cost(input_tokens, output_tokens)

            # Cache the result
            if self.cache and cache_key:
                await self.cache.set(cache_key, summary, {"tokens": tokens_used, "cost": cost})

            return SummarizationResult(
                summary=summary,
                tokens_used=tokens_used,
                cost_estimate=cost,
                model_used=self.config.model,
                provider="zhipu",
                cached=False,
                metadata={"input_tokens": input_tokens, "output_tokens": output_tokens},
            )

        except Exception as e:
            logger.error(f"Zhipu GLM API error: {e}")
            return SummarizationResult(
                summary="", error=str(e), model_used=self.config.model, provider="zhipu"
            )

    async def summarize_function(
        self,
        function_code: str,
        function_name: str,
        language: str,
        context: dict[str, Any] | None = None,
    ) -> SummarizationResult:
        """Generate a summary for a specific function using Zhipu GLM."""
        # Check cache first
        if self.cache:
            cache_key = self.cache.generate_key(
                function_code,
                "zhipu",
                self.config.model,
                "summarize_function",
                function_name=function_name,
                language=language,
            )
            cached_summary = await self.cache.get(cache_key)
            if cached_summary:
                logger.info(f"Cache hit for {function_name} - returning cached summary")
                return SummarizationResult(
                    summary=cached_summary,
                    model_used=self.config.model,
                    provider="zhipu",
                    cached=True,
                )

        # Create the prompt
        system_prompt = getattr(
            self,
            "SYSTEM_PROMPT_FUNCTION_SUMMARY",
            "You are a helpful assistant that creates concise function summaries.",
        )
        user_prompt = self._create_function_summary_prompt(
            function_code, function_name, language, context
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            # Make API call with retry
            response = await self._retry_with_backoff(
                self._make_api_call,
                messages,
                200,  # Shorter max tokens for function summaries
            )

            # Extract summary and token usage
            summary = response["choices"][0]["message"]["content"].strip()
            usage = response["usage"]
            tokens_used = usage["total_tokens"]
            input_tokens = usage["prompt_tokens"]
            output_tokens = usage["completion_tokens"]

            # Calculate cost
            cost = self._calculate_cost(input_tokens, output_tokens)

            # Cache the result
            if self.cache and cache_key:
                await self.cache.set(cache_key, summary, {"tokens": tokens_used, "cost": cost})

            return SummarizationResult(
                summary=summary,
                tokens_used=tokens_used,
                cost_estimate=cost,
                model_used=self.config.model,
                provider="zhipu",
                cached=False,
                metadata={"input_tokens": input_tokens, "output_tokens": output_tokens},
            )

        except Exception as e:
            logger.error(f"Zhipu GLM API error: {e}")
            return SummarizationResult(
                summary="", error=str(e), model_used=self.config.model, provider="zhipu"
            )

    async def get_model_info(self) -> dict[str, Any]:
        """Get information about the current Zhipu GLM model."""
        from ..models_config import get_model_config

        model_cfg = get_model_config(self.config.model)

        info: dict[str, Any] = {
            "provider": "zhipu",
            "model": self.config.model,
            "temperature": self.config.temperature,
        }

        if model_cfg:
            info.update(
                {
                    "context_window": model_cfg.context_window,
                    "max_output": model_cfg.max_output,
                    "cost_per_1k_input": model_cfg.cost_per_1k_input,
                    "cost_per_1k_output": model_cfg.cost_per_1k_output,
                    "supports_functions": model_cfg.supports_functions,
                }
            )
        else:
            info.update(
                {
                    "context_window": 128000,  # Default GLM-4 context
                    "max_output": 4096,
                    "cost_per_1k_input": self.config.cost_per_1k_input_tokens,
                    "cost_per_1k_output": self.config.cost_per_1k_output_tokens,
                }
            )

        return info

    async def validate_connection(self) -> bool:
        """Validate that the Zhipu GLM provider is properly configured."""
        if not self.config.api_key:
            logger.warning("No Zhipu API key configured")
            return False

        try:
            # Try a minimal API call
            messages = [{"role": "user", "content": "test"}]
            response = await self._make_api_call(messages, max_tokens=10)
            return bool(response.get("choices"))
        except Exception as e:
            logger.error(f"Zhipu GLM connection validation failed: {e}")
            return False

    async def close(self):
        """Clean up resources."""
        # zhipuai client doesn't need explicit cleanup
        await super().close()
