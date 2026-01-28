"""OpenAI provider implementation for code summarization."""

import asyncio
import logging
import os
import time
from typing import Any

import aiohttp

from ..base import AIProvider, AIProviderConfig, SummarizationResult
from ..cache import SummaryCache

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """OpenAI API provider for code summarization."""

    _session: aiohttp.ClientSession | None

    def __init__(self, config: AIProviderConfig):
        """Initialize OpenAI provider."""
        super().__init__(config)
        logger.info(f"Initializing OpenAI provider with model: {config.model}")

        # Set defaults for OpenAI
        if not config.api_key:
            config.api_key = os.getenv("OPENAI_API_KEY")
            logger.debug(f"API key loaded from env: {bool(config.api_key)}")

        if not config.api_base:
            config.api_base = "https://api.openai.com/v1"

        if not config.model:
            config.model = "gpt-5-mini-2025-08-07"  # Budget model for individual file summaries
            logger.debug(f"Using default model: {config.model}")

        # Set costs from models_config if not specified
        if config.cost_per_1k_input_tokens == 0:
            from ..models_config import get_model_config

            model_cfg = get_model_config(config.model)
            if model_cfg:
                config.cost_per_1k_input_tokens = model_cfg.cost_per_1k_input
                config.cost_per_1k_output_tokens = model_cfg.cost_per_1k_output
            else:
                # Fallback for unknown models
                if "gpt-4" in config.model:
                    config.cost_per_1k_input_tokens = 0.03
                    config.cost_per_1k_output_tokens = 0.06
                else:  # Default to gpt-3.5-turbo pricing
                    config.cost_per_1k_input_tokens = 0.001
                    config.cost_per_1k_output_tokens = 0.002

        self.cache = SummaryCache() if config.cache_enabled else None

        # Rate limiting: OpenAI tier-dependent limits
        # Free tier: 3 RPM, Tier 1: 500 RPM, Tier 2: 5000 RPM
        # Using Tier 1 with concurrent requests: 500 RPM / 10 concurrent = 50 RPM per slot = 1.2s delay
        self._rate_limit_delay = 0.3  # seconds between requests (allows ~200 RPM with concurrency)
        self._last_request_time = 0.0
        self._rate_limit_lock = asyncio.Lock()
        self._concurrent_limit = asyncio.Semaphore(10)  # Max 10 concurrent requests

        logger.info(
            f"OpenAI provider initialized - Model: {config.model}, Cache: {bool(self.cache)}, API Key: {bool(config.api_key)}, Rate limit: {self._rate_limit_delay}s"
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                **(self.config.custom_headers or {}),
            }
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self._session

    async def _make_api_call(self, messages: list, max_tokens: int | None = None) -> dict:
        """Make an API call to OpenAI with rate limiting and concurrency control."""
        # Use semaphore to limit concurrent requests
        async with self._concurrent_limit:
            # Enforce minimum delay between requests
            async with self._rate_limit_lock:
                now = time.time()
                time_since_last = now - self._last_request_time
                if time_since_last < self._rate_limit_delay:
                    wait_time = self._rate_limit_delay - time_since_last
                    logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                self._last_request_time = time.time()

            session = await self._get_session()

        # GPT-5 and o-series models use max_completion_tokens instead of max_tokens
        # and require temperature=1.0
        model_lower = self.config.model.lower()
        is_reasoning_model = any(x in model_lower for x in ["gpt-5", "o1", "o3"])

        if is_reasoning_model:
            payload = {
                "model": self.config.model,
                "messages": messages,
                "temperature": 1.0,  # Required for reasoning models
                "max_completion_tokens": max_tokens or self.config.max_tokens,
                **self.config.extra_params,
            }
        else:
            payload = {
                "model": self.config.model,
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens,
                **self.config.extra_params,
            }

        url = f"{self.config.api_base}/chat/completions"
        logger.info(f"Making OpenAI API call to {url} with model {self.config.model}")
        logger.debug(
            f"Payload: messages={len(messages)} msgs, max_tokens={max_tokens or self.config.max_tokens}"
        )

        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"OpenAI API error ({response.status}): {error_text}")
                raise Exception(f"OpenAI API error ({response.status}): {error_text}")

            result = await response.json()
            logger.info(
                f"OpenAI API call successful - tokens used: {result.get('usage', {}).get('total_tokens', 'unknown')}"
            )
            return dict(result) if result else {}

    async def summarize_code(
        self,
        code: str,
        language: str,
        context: dict[str, Any] | None = None,
        max_length: int | None = None,
    ) -> SummarizationResult:
        """Generate a summary for a code file using OpenAI."""
        # Check cache first
        if self.cache:
            cache_key = self.cache.generate_key(
                code, "openai", self.config.model, "summarize_code", language=language
            )
            cached_summary = await self.cache.get(cache_key)
            if cached_summary:
                logger.info(f"Cache hit for {language} code - returning cached summary")
                return SummarizationResult(
                    summary=cached_summary,
                    model_used=self.config.model,
                    provider="openai",
                    cached=True,
                )

        # Create the prompt
        prompt = self._create_code_summary_prompt(code, language, context)

        # Use getattr with fallback to prevent AttributeError
        system_prompt = getattr(
            self,
            "SYSTEM_PROMPT_CODE_SUMMARY",
            "You are a helpful assistant that creates concise, informative code summaries.",
        )
        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {"role": "user", "content": prompt},
        ]

        try:
            # For reasoning models, increase max_tokens significantly as they use tokens for reasoning
            model_lower = self.config.model.lower()
            is_reasoning_model = any(x in model_lower for x in ["gpt-5", "o1", "o3"])
            actual_max_length: int | None
            if is_reasoning_model and (max_length is None or max_length < 2000):
                # Reasoning models need more tokens - they use many for reasoning
                actual_max_length = 2000
            else:
                actual_max_length = max_length

            # Make API call with retry
            response = await self._retry_with_backoff(
                self._make_api_call, messages, actual_max_length
            )

            # Extract summary and token usage
            summary = response["choices"][0]["message"]["content"].strip()
            tokens_used = response["usage"]["total_tokens"]
            input_tokens = response["usage"]["prompt_tokens"]
            output_tokens = response["usage"]["completion_tokens"]

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
                provider="openai",
                cached=False,
                metadata={"input_tokens": input_tokens, "output_tokens": output_tokens},
            )

        except Exception as e:
            return SummarizationResult(
                summary="", error=str(e), model_used=self.config.model, provider="openai"
            )

    async def summarize_function(
        self,
        function_code: str,
        function_name: str,
        language: str,
        context: dict[str, Any] | None = None,
    ) -> SummarizationResult:
        """Generate a summary for a specific function using OpenAI."""
        # Check cache first
        if self.cache:
            cache_key = self.cache.generate_key(
                function_code,
                "openai",
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
                    provider="openai",
                    cached=True,
                )

        # Create the prompt
        prompt = self._create_function_summary_prompt(
            function_code, function_name, language, context
        )

        # Use getattr with fallback to prevent AttributeError
        system_prompt = getattr(
            self,
            "SYSTEM_PROMPT_FUNCTION_SUMMARY",
            "You are a helpful assistant that creates concise function summaries.",
        )
        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {"role": "user", "content": prompt},
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
            tokens_used = response["usage"]["total_tokens"]
            input_tokens = response["usage"]["prompt_tokens"]
            output_tokens = response["usage"]["completion_tokens"]

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
                provider="openai",
                cached=False,
                metadata={"input_tokens": input_tokens, "output_tokens": output_tokens},
            )

        except Exception as e:
            return SummarizationResult(
                summary="", error=str(e), model_used=self.config.model, provider="openai"
            )

    async def generate_meta_overview(
        self,
        file_summaries: dict[str, Any],
        custom_prompt: str | None = None,
        max_tokens: int | None = None,
        tree_structure: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> SummarizationResult:
        """Generate meta-overview using higher-tier GPT-5 with reasoning parameters.

        Args:
            file_summaries: Dictionary mapping file paths to their summaries
            custom_prompt: Optional custom prompt
            max_tokens: Maximum tokens for the overview
            tree_structure: Optional tree structure visualization
            context: Optional context dict

        Returns:
            SummarizationResult with the generated meta-overview
        """
        # Check if we should use higher-tier model
        from ...base_types import CodeConCatConfig

        use_higher_tier = True  # Default to True
        override_model = None

        if hasattr(self, "config") and isinstance(self.config, CodeConCatConfig):
            use_higher_tier = getattr(self.config, "ai_meta_overview_use_higher_tier", True)
            override_model = getattr(self.config, "ai_meta_overview_model", None)

        # Determine which model to use
        meta_model = override_model or (
            "gpt-5-2025-08-07" if use_higher_tier else self.config.model
        )

        logger.info(f"Generating meta-overview with model: {meta_model}")

        # Use the enhanced prompt generator
        final_prompt = self._create_meta_overview_prompt(
            file_summaries,
            tree_structure=tree_structure,
            context=context,
            custom_prompt=custom_prompt,
        )

        # Prepare messages
        system_prompt = (
            "You are a senior software architect conducting a comprehensive codebase analysis. "
            "Your expertise includes system design, architectural patterns, technology assessment, "
            "and identifying technical debt and improvement opportunities across large-scale projects."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": final_prompt},
        ]

        # Temporarily override model and add reasoning parameters
        original_model = self.config.model
        original_extra_params = self.config.extra_params.copy()

        try:
            self.config.model = meta_model

            # Add reasoning parameters for GPT-5 and o-series models
            # These models require temperature=1.0
            if (
                "gpt-5" in meta_model.lower()
                or "o1" in meta_model.lower()
                or "o3" in meta_model.lower()
            ):
                original_temp = self.config.temperature
                self.config.temperature = 1.0  # Required for reasoning models
                self.config.extra_params = {
                    **original_extra_params,
                    "reasoning_effort": "high",
                }
                logger.debug("High reasoning effort enabled for meta-overview (temperature=1.0)")

            # Make API call with higher max_tokens (default 8000 for meta-overview)
            # Reasoning models need longer timeout - close existing session and create new one with longer timeout
            original_timeout = self.config.timeout
            original_session = self._session
            if (
                "gpt-5" in meta_model.lower()
                or "o1" in meta_model.lower()
                or "o3" in meta_model.lower()
            ):
                self.config.timeout = 300  # 5 minutes for reasoning models
                # Close existing session to force creation of new one with updated timeout
                if self._session:
                    await self._session.close()
                    self._session = None
                logger.debug("Increased timeout to 300s for reasoning model")

            try:
                response = await self._retry_with_backoff(
                    self._make_api_call, messages, max_tokens or 8000
                )
            finally:
                # Restore original timeout and session
                self.config.timeout = original_timeout
                # Close the long-timeout session
                if (
                    "gpt-5" in meta_model.lower()
                    or "o1" in meta_model.lower()
                    or "o3" in meta_model.lower()
                ):
                    if self._session:
                        await self._session.close()
                    self._session = original_session

            # Extract summary and token usage
            # For reasoning models, check if content is in refusal or content field
            message = response["choices"][0]["message"]
            message_content = message.get("content") or message.get("refusal", "")
            summary = message_content.strip() if message_content else ""
            tokens_used = response["usage"]["total_tokens"]
            input_tokens = response["usage"]["prompt_tokens"]
            output_tokens = response["usage"]["completion_tokens"]
            logger.debug(f"Meta-overview: {len(summary)} chars, {tokens_used} tokens")

            # Calculate cost
            cost = self._calculate_cost(input_tokens, output_tokens)

            return SummarizationResult(
                summary=summary,
                tokens_used=tokens_used,
                cost_estimate=cost,
                model_used=meta_model,
                provider="openai",
                cached=False,
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "reasoning_enabled": True,
                },
            )

        except Exception as e:
            logger.error(f"Meta-overview generation failed: {e}")
            import traceback

            logger.debug(traceback.format_exc())
            return SummarizationResult(
                summary="", error=str(e), model_used=meta_model, provider="openai"
            )
        finally:
            # Restore original configuration
            self.config.model = original_model
            self.config.extra_params = original_extra_params
            # Restore temperature if it was changed for reasoning models
            if (
                "gpt-5" in meta_model.lower()
                or "o1" in meta_model.lower()
                or "o3" in meta_model.lower()
            ):
                self.config.temperature = original_temp

    async def get_model_info(self) -> dict[str, Any]:
        """Get information about the current OpenAI model."""
        model_info = {
            "gpt-4-turbo-preview": {
                "context_window": 128000,
                "max_output": 4096,
                "cost_per_1k_input": 0.01,
                "cost_per_1k_output": 0.03,
            },
            "gpt-4": {
                "context_window": 8192,
                "max_output": 4096,
                "cost_per_1k_input": 0.03,
                "cost_per_1k_output": 0.06,
            },
            "gpt-3.5-turbo": {
                "context_window": 16385,
                "max_output": 4096,
                "cost_per_1k_input": 0.001,
                "cost_per_1k_output": 0.002,
            },
        }

        info = model_info.get(
            self.config.model,
            {
                "context_window": 4096,
                "max_output": 2048,
                "cost_per_1k_input": self.config.cost_per_1k_input_tokens,
                "cost_per_1k_output": self.config.cost_per_1k_output_tokens,
            },
        )

        # Add provider metadata separately to avoid type conflicts
        provider_info = {
            "provider": "openai",
            "model": str(self.config.model),
            "temperature": float(self.config.temperature),
            "api_base": str(self.config.api_base) if self.config.api_base else None,
        }

        # Merge dictionaries
        return {**info, **provider_info}

    async def validate_connection(self) -> bool:
        """Validate that the OpenAI provider is properly configured."""
        if not self.config.api_key:
            return False

        try:
            # Try a minimal API call
            messages = [{"role": "user", "content": "test"}]
            response = await self._make_api_call(messages, max_tokens=1)
            return "choices" in response
        except Exception:
            return False
