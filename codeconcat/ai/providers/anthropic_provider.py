"""Anthropic provider implementation for code summarization."""

import asyncio
import logging
import os
import time
from typing import Any, Dict, Optional

import aiohttp

from ..base import AIProvider, AIProviderConfig, SummarizationResult
from ..cache import SummaryCache

logger = logging.getLogger(__name__)


class AnthropicProvider(AIProvider):
    """Anthropic API provider for code summarization."""

    def __init__(self, config: AIProviderConfig):
        """Initialize Anthropic provider."""
        super().__init__(config)
        logger.info(f"Initializing Anthropic provider with model: {config.model}")

        # Set defaults for Anthropic
        if not config.api_key:
            config.api_key = os.getenv("ANTHROPIC_API_KEY")
            logger.debug(f"API key loaded from env: {bool(config.api_key)}")

        if not config.api_base:
            config.api_base = "https://api.anthropic.com/v1"

        if not config.model:
            config.model = (
                "claude-3-5-haiku-20241022"  # Specific Haiku version for individual summaries
            )

        # Set costs from models_config if not specified
        if config.cost_per_1k_input_tokens == 0:
            from ..models_config import get_model_config

            model_cfg = get_model_config(config.model)
            if model_cfg:
                config.cost_per_1k_input_tokens = model_cfg.cost_per_1k_input
                config.cost_per_1k_output_tokens = model_cfg.cost_per_1k_output
            else:
                # Fallback for unknown models
                if "opus" in config.model:
                    config.cost_per_1k_input_tokens = 0.015
                    config.cost_per_1k_output_tokens = 0.075
                elif "sonnet" in config.model:
                    config.cost_per_1k_input_tokens = 0.003
                    config.cost_per_1k_output_tokens = 0.015
                else:  # Default to haiku pricing
                    config.cost_per_1k_input_tokens = 0.00025
                    config.cost_per_1k_output_tokens = 0.00125

        self.cache = SummaryCache() if config.cache_enabled else None

        # Rate limiting: Anthropic tier-dependent limits
        # Tier 1: 5 RPM, Tier 2: 50 RPM, Tier 3: 1000 RPM, Tier 4: 2000 RPM
        # Using Tier 1 with concurrent requests: 5 RPM = 1 req every 12s, but allow 5 concurrent
        self._rate_limit_delay = 2.5  # seconds between requests (allows ~24 RPM with concurrency)
        self._last_request_time = 0.0
        self._rate_limit_lock = asyncio.Lock()
        self._concurrent_limit = asyncio.Semaphore(5)  # Max 5 concurrent requests

        logger.info(
            f"Anthropic provider initialized - Model: {config.model}, Cache: {bool(self.cache)}, API Key: {bool(config.api_key)}, Rate limit: {self._rate_limit_delay}s"
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if not self._session:
            headers = {
                "x-api-key": self.config.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
                **(self.config.custom_headers or {}),
            }
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self._session

    async def _make_api_call(self, messages: list, max_tokens: Optional[int] = None) -> dict:
        """Make an API call to Anthropic with rate limiting and concurrency control."""
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

        # Convert messages to Anthropic format
        system_message = None
        user_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                user_messages.append(msg)

        payload = {
            "model": self.config.model,
            "messages": user_messages,
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": self.config.temperature,
            **self.config.extra_params,
        }

        if system_message:
            payload["system"] = system_message

        url = f"{self.config.api_base}/messages"

        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Anthropic API error ({response.status}): {error_text}")

            result = await response.json()
            return dict(result) if result else {}

    async def summarize_code(
        self,
        code: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
        max_length: Optional[int] = None,
    ) -> SummarizationResult:
        """Generate a summary for a code file using Anthropic."""
        # Check cache first
        if self.cache:
            cache_key = self.cache.generate_key(
                code, "anthropic", self.config.model, "summarize_code", language=language
            )
            cached_summary = await self.cache.get(cache_key)
            if cached_summary:
                return SummarizationResult(
                    summary=cached_summary,
                    model_used=self.config.model,
                    provider="anthropic",
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
            # Make API call with retry
            response = await self._retry_with_backoff(self._make_api_call, messages, max_length)

            # Extract summary and token usage
            summary = response["content"][0]["text"].strip()

            # Anthropic provides usage info differently
            input_tokens = response.get("usage", {}).get("input_tokens", 0)
            output_tokens = response.get("usage", {}).get("output_tokens", 0)
            tokens_used = input_tokens + output_tokens

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
                provider="anthropic",
                cached=False,
                metadata={"input_tokens": input_tokens, "output_tokens": output_tokens},
            )

        except Exception as e:
            return SummarizationResult(
                summary="", error=str(e), model_used=self.config.model, provider="anthropic"
            )

    async def summarize_function(
        self,
        function_code: str,
        function_name: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> SummarizationResult:
        """Generate a summary for a specific function using Anthropic."""
        # Check cache first
        if self.cache:
            cache_key = self.cache.generate_key(
                function_code,
                "anthropic",
                self.config.model,
                "summarize_function",
                function_name=function_name,
                language=language,
            )
            cached_summary = await self.cache.get(cache_key)
            if cached_summary:
                return SummarizationResult(
                    summary=cached_summary,
                    model_used=self.config.model,
                    provider="anthropic",
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
            summary = response["content"][0]["text"].strip()

            input_tokens = response.get("usage", {}).get("input_tokens", 0)
            output_tokens = response.get("usage", {}).get("output_tokens", 0)
            tokens_used = input_tokens + output_tokens

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
                provider="anthropic",
                cached=False,
                metadata={"input_tokens": input_tokens, "output_tokens": output_tokens},
            )

        except Exception as e:
            return SummarizationResult(
                summary="", error=str(e), model_used=self.config.model, provider="anthropic"
            )

    async def generate_meta_overview(
        self,
        file_summaries: Dict[str, Any],
        custom_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        tree_structure: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> SummarizationResult:
        """Generate meta-overview using higher-tier Claude Sonnet 4.5 with extended thinking.

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

        # Try to get config from self.config if it exists
        use_higher_tier = True  # Default to True
        override_model = None

        if hasattr(self, "config") and isinstance(self.config, CodeConCatConfig):
            use_higher_tier = getattr(self.config, "ai_meta_overview_use_higher_tier", True)
            override_model = getattr(self.config, "ai_meta_overview_model", None)

        # Determine which model to use
        meta_model = override_model or (
            "claude-sonnet-4-5-20250929" if use_higher_tier else self.config.model
        )

        logger.info(f"Generating meta-overview with model: {meta_model}")

        # Use the enhanced prompt generator
        final_prompt = self._create_meta_overview_prompt(
            file_summaries,
            tree_structure=tree_structure,
            context=context,
            custom_prompt=custom_prompt,
        )

        # Prepare messages with extended thinking for Sonnet 4.5
        system_prompt = (
            "You are a senior software architect conducting a comprehensive codebase analysis. "
            "Your expertise includes system design, architectural patterns, technology assessment, "
            "and identifying technical debt and improvement opportunities across large-scale projects."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": final_prompt},
        ]

        # Temporarily override model and add extended thinking parameters
        original_model = self.config.model
        original_extra_params = self.config.extra_params.copy()
        original_temp = self.config.temperature  # Initialize to avoid NameError in finally block

        try:
            self.config.model = meta_model

            # Add extended thinking for Sonnet 4.5
            # Note: When extended thinking is enabled, temperature must be set to 1
            # and max_tokens must be > budget_tokens
            if "sonnet-4" in meta_model.lower() or "sonnet-5" in meta_model.lower():
                self.config.temperature = 1.0  # Required for extended thinking
                thinking_budget = 10000
                response_tokens = max_tokens or 4096
                total_max_tokens = thinking_budget + response_tokens
                self.config.extra_params = {
                    **original_extra_params,
                    "thinking": {"type": "enabled", "budget_tokens": thinking_budget},
                }
                logger.debug(
                    f"Extended thinking enabled for meta-overview (temperature=1.0, "
                    f"thinking={thinking_budget}, max_tokens={total_max_tokens})"
                )
            else:
                total_max_tokens = max_tokens or 2000

            # Make API call with higher max_tokens
            response = await self._retry_with_backoff(
                self._make_api_call, messages, total_max_tokens
            )

            # Extract summary and token usage
            summary = response["content"][0]["text"].strip()

            input_tokens = response.get("usage", {}).get("input_tokens", 0)
            output_tokens = response.get("usage", {}).get("output_tokens", 0)
            tokens_used = input_tokens + output_tokens

            # Calculate cost
            cost = self._calculate_cost(input_tokens, output_tokens)

            return SummarizationResult(
                summary=summary,
                tokens_used=tokens_used,
                cost_estimate=cost,
                model_used=meta_model,
                provider="anthropic",
                cached=False,
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "extended_thinking": True,
                },
            )

        except (asyncio.CancelledError, asyncio.TimeoutError):
            # These can occur during async cleanup but don't affect functionality
            # Meta-overview was successfully generated before cleanup issues
            logger.debug("Async cleanup issue (non-fatal) - meta-overview generated successfully")
            # This exception only occurs after successful return, but mypy needs a return statement
            return SummarizationResult(
                summary="",
                error="Async cleanup error (non-fatal)",
                model_used=meta_model,
                provider="anthropic",
            )
        except Exception as e:
            error_msg = str(e) if e else "Unknown error"
            logger.error(f"Meta-overview generation failed: {error_msg}")
            import traceback

            tb = traceback.format_exc()
            logger.debug(f"Full traceback:\n{tb}")
            return SummarizationResult(
                summary="", error=error_msg, model_used=meta_model, provider="anthropic"
            )
        finally:
            # Restore original configuration
            try:
                self.config.model = original_model
                self.config.extra_params = original_extra_params
                if "sonnet-4" in meta_model.lower() or "sonnet-5" in meta_model.lower():
                    self.config.temperature = original_temp
            except Exception:
                # Ignore any errors during config restoration
                pass

    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current Anthropic model."""
        model_info = {
            "claude-3-opus-20240229": {
                "context_window": 200000,
                "max_output": 4096,
                "cost_per_1k_input": 0.015,
                "cost_per_1k_output": 0.075,
            },
            "claude-3-sonnet-20240229": {
                "context_window": 200000,
                "max_output": 4096,
                "cost_per_1k_input": 0.003,
                "cost_per_1k_output": 0.015,
            },
            "claude-3-haiku-20240307": {
                "context_window": 200000,
                "max_output": 4096,
                "cost_per_1k_input": 0.00025,
                "cost_per_1k_output": 0.00125,
            },
        }

        info = model_info.get(
            self.config.model,
            {
                "context_window": 100000,
                "max_output": 4096,
                "cost_per_1k_input": self.config.cost_per_1k_input_tokens,
                "cost_per_1k_output": self.config.cost_per_1k_output_tokens,
            },
        )

        # Add provider metadata separately to avoid type conflicts
        provider_info = {
            "provider": "anthropic",
            "model": str(self.config.model),
            "temperature": float(self.config.temperature),
            "api_base": str(self.config.api_base) if self.config.api_base else None,
        }

        # Merge dictionaries
        return {**info, **provider_info}

    async def validate_connection(self) -> bool:
        """Validate that the Anthropic provider is properly configured."""
        if not self.config.api_key:
            return False

        try:
            # Try a minimal API call
            messages = [{"role": "user", "content": "test"}]
            response = await self._make_api_call(messages, max_tokens=1)
            return "content" in response
        except Exception:
            return False
