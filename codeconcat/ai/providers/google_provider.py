"""Google Gemini provider implementation for code summarization."""

import asyncio
import logging
import os
from typing import Any

from ..base import AIProvider, AIProviderConfig, SummarizationResult
from ..cache import SummaryCache

logger = logging.getLogger(__name__)


class GoogleProvider(AIProvider):
    """Google Gemini API provider for code summarization.

    Supports both Gemini Developer API (via API key) and Vertex AI (via ADC).
    Uses the official google-genai SDK for native API access.
    """

    def __init__(self, config: AIProviderConfig):
        """Initialize Google Gemini provider."""
        super().__init__(config)
        logger.info(f"Initializing Google Gemini provider with model: {config.model}")

        # Set defaults for Google Gemini
        if not config.api_key:
            config.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            logger.debug(f"API key loaded from env: {bool(config.api_key)}")

        if not config.model:
            config.model = "gemini-2.0-flash"  # Free tier model
            logger.debug(f"Using default model: {config.model}")

        # Set costs from models_config if not specified
        if config.cost_per_1k_input_tokens == 0:
            from ..models_config import get_model_config

            model_cfg = get_model_config(config.model)
            if model_cfg:
                config.cost_per_1k_input_tokens = model_cfg.cost_per_1k_input
                config.cost_per_1k_output_tokens = model_cfg.cost_per_1k_output

        self.cache = SummaryCache() if config.cache_enabled else None

        # Rate limiting for Google API
        self._rate_limit_delay = 0.5  # seconds between requests
        self._last_request_time = 0.0
        self._rate_limit_lock = asyncio.Lock()
        self._concurrent_limit = asyncio.Semaphore(5)  # Max 5 concurrent requests

        # Lazy-load the client
        self._client = None

        logger.info(
            f"Google Gemini provider initialized - Model: {config.model}, "
            f"Cache: {bool(self.cache)}, API Key: {bool(config.api_key)}"
        )

    def _get_client(self):
        """Get or create the Google Generative AI client."""
        if self._client is None:
            try:
                from google import genai  # type: ignore[import-untyped]

                # Initialize client with API key
                if self.config.api_key:
                    self._client = genai.Client(api_key=self.config.api_key)
                else:
                    # Try to use Application Default Credentials (Vertex AI)
                    self._client = genai.Client()

            except ImportError as err:
                raise ImportError(
                    "google-genai package is required for Google Gemini support. "
                    "Install it with: pip install google-genai"
                ) from err

        return self._client

    async def _make_api_call(self, prompt: str, max_tokens: int | None = None) -> dict:
        """Make an API call to Google Gemini with rate limiting."""
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

        # Configure generation parameters
        generation_config = {
            "temperature": self.config.temperature,
            "max_output_tokens": max_tokens or self.config.max_tokens,
        }

        logger.info(f"Making Google Gemini API call with model {self.config.model}")
        logger.debug(f"Generation config: {generation_config}")

        # Run the synchronous API call in a thread pool
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model=self.config.model,
                contents=prompt,
                config=generation_config,
            ),
        )

        # Extract response data
        result = {
            "text": response.text if response.text else "",
            "usage": {
                "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0)
                if response.usage_metadata
                else 0,
                "completion_tokens": getattr(response.usage_metadata, "candidates_token_count", 0)
                if response.usage_metadata
                else 0,
                "total_tokens": getattr(response.usage_metadata, "total_token_count", 0)
                if response.usage_metadata
                else 0,
            },
        }

        logger.info(f"Google Gemini API call successful - tokens used: {result['usage']}")
        return result

    async def summarize_code(
        self,
        code: str,
        language: str,
        context: dict[str, Any] | None = None,
        max_length: int | None = None,
    ) -> SummarizationResult:
        """Generate a summary for a code file using Google Gemini."""
        # Check cache first
        if self.cache:
            cache_key = self.cache.generate_key(
                code, "google", self.config.model, "summarize_code", language=language
            )
            cached_summary = await self.cache.get(cache_key)
            if cached_summary:
                logger.info(f"Cache hit for {language} code - returning cached summary")
                return SummarizationResult(
                    summary=cached_summary,
                    model_used=self.config.model,
                    provider="google",
                    cached=True,
                )

        # Create the prompt
        system_prompt = getattr(
            self,
            "SYSTEM_PROMPT_CODE_SUMMARY",
            "You are a helpful assistant that creates concise, informative code summaries.",
        )
        user_prompt = self._create_code_summary_prompt(code, language, context)

        # Combine system and user prompts for Gemini
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        try:
            # Make API call with retry
            response = await self._retry_with_backoff(self._make_api_call, full_prompt, max_length)

            # Extract summary and token usage
            summary = response["text"].strip()
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
                provider="google",
                cached=False,
                metadata={"input_tokens": input_tokens, "output_tokens": output_tokens},
            )

        except Exception as e:
            logger.error(f"Google Gemini API error: {e}")
            return SummarizationResult(
                summary="", error=str(e), model_used=self.config.model, provider="google"
            )

    async def summarize_function(
        self,
        function_code: str,
        function_name: str,
        language: str,
        context: dict[str, Any] | None = None,
    ) -> SummarizationResult:
        """Generate a summary for a specific function using Google Gemini."""
        # Check cache first
        if self.cache:
            cache_key = self.cache.generate_key(
                function_code,
                "google",
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
                    provider="google",
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

        # Combine system and user prompts for Gemini
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        try:
            # Make API call with retry
            response = await self._retry_with_backoff(
                self._make_api_call,
                full_prompt,
                200,  # Shorter max tokens for function summaries
            )

            # Extract summary and token usage
            summary = response["text"].strip()
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
                provider="google",
                cached=False,
                metadata={"input_tokens": input_tokens, "output_tokens": output_tokens},
            )

        except Exception as e:
            logger.error(f"Google Gemini API error: {e}")
            return SummarizationResult(
                summary="", error=str(e), model_used=self.config.model, provider="google"
            )

    async def get_model_info(self) -> dict[str, Any]:
        """Get information about the current Google Gemini model."""
        from ..models_config import get_model_config

        model_cfg = get_model_config(self.config.model)

        info: dict[str, Any] = {
            "provider": "google",
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
                    "supports_vision": model_cfg.supports_vision,
                    "supports_functions": model_cfg.supports_functions,
                }
            )
        else:
            info.update(
                {
                    "context_window": 1048576,  # Default 1M context
                    "max_output": 8192,
                    "cost_per_1k_input": self.config.cost_per_1k_input_tokens,
                    "cost_per_1k_output": self.config.cost_per_1k_output_tokens,
                }
            )

        return info

    async def validate_connection(self) -> bool:
        """Validate that the Google Gemini provider is properly configured."""
        if not self.config.api_key:
            logger.warning("No Google API key configured")
            return False

        try:
            # Try a minimal API call
            response = await self._make_api_call("test", max_tokens=10)
            return bool(response.get("text"))
        except Exception as e:
            logger.error(f"Google Gemini connection validation failed: {e}")
            return False

    async def close(self):
        """Clean up resources."""
        # google-genai client doesn't need explicit cleanup
        await super().close()
