"""OpenRouter provider implementation for multi-model access."""

import asyncio
import logging
import os
from typing import Any

import aiohttp

from ..base import AIProvider, AIProviderConfig, SummarizationResult
from ..cache import SummaryCache

logger = logging.getLogger(__name__)


class OpenRouterProvider(AIProvider):
    """OpenRouter API provider for multi-model code summarization."""

    _session: aiohttp.ClientSession | None

    def __init__(self, config: AIProviderConfig):
        """Initialize OpenRouter provider."""
        super().__init__(config)

        # Set defaults for OpenRouter
        if not config.api_key:
            config.api_key = os.getenv("OPENROUTER_API_KEY")

        if not config.api_base:
            config.api_base = "https://openrouter.ai/api/v1"

        if not config.model:
            config.model = "qwen/qwen3-coder"  # Coder-optimized model for individual file summaries

        # OpenRouter pricing varies by model - user should set these
        if config.cost_per_1k_input_tokens == 0:
            # Default to a low estimate
            config.cost_per_1k_input_tokens = 0.0001
            config.cost_per_1k_output_tokens = 0.0001

        self.cache = SummaryCache() if config.cache_enabled else None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "HTTP-Referer": "https://github.com/codeconcat",  # Required by OpenRouter
                "X-Title": "CodeConcat AI Summarization",  # Optional but recommended
                "Content-Type": "application/json",
                **self.config.custom_headers,
            }
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self._session

    async def _make_api_call(self, messages: list, max_tokens: int | None = None) -> dict:
        """Make an API call to OpenRouter."""
        session = await self._get_session()

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
            **self.config.extra_params,
        }

        url = f"{self.config.api_base}/chat/completions"

        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"OpenRouter API error ({response.status}): {error_text}")

            result = await response.json()
            return dict(result) if result else {}

    async def summarize_code(
        self,
        code: str,
        language: str,
        context: dict[str, Any] | None = None,
        max_length: int | None = None,
    ) -> SummarizationResult:
        """Generate a summary for a code file using OpenRouter."""
        # Check cache first
        if self.cache:
            cache_key = self.cache.generate_key(
                code, "openrouter", self.config.model, "summarize_code", language=language
            )
            cached_summary = await self.cache.get(cache_key)
            if cached_summary:
                return SummarizationResult(
                    summary=cached_summary,
                    model_used=self.config.model,
                    provider="openrouter",
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
            summary = response["choices"][0]["message"]["content"].strip()

            # OpenRouter returns usage info in the same format as OpenAI
            tokens_used = response.get("usage", {}).get("total_tokens", 0)
            input_tokens = response.get("usage", {}).get("prompt_tokens", 0)
            output_tokens = response.get("usage", {}).get("completion_tokens", 0)

            # Calculate cost (OpenRouter provides this in the response)
            cost = response.get("usage", {}).get("total_cost", 0.0)
            if cost == 0:
                cost = self._calculate_cost(input_tokens, output_tokens)

            # Cache the result
            if self.cache and cache_key:
                await self.cache.set(
                    cache_key,
                    summary,
                    {
                        "tokens": tokens_used,
                        "cost": cost,
                        "model": response.get("model", self.config.model),
                    },
                )

            return SummarizationResult(
                summary=summary,
                tokens_used=tokens_used,
                cost_estimate=cost,
                model_used=response.get("model", self.config.model),
                provider="openrouter",
                cached=False,
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "actual_model": response.get("model"),
                },
            )

        except Exception as e:
            return SummarizationResult(
                summary="", error=str(e), model_used=self.config.model, provider="openrouter"
            )

    async def summarize_function(
        self,
        function_code: str,
        function_name: str,
        language: str,
        context: dict[str, Any] | None = None,
    ) -> SummarizationResult:
        """Generate a summary for a specific function using OpenRouter."""
        # Check cache first
        if self.cache:
            cache_key = self.cache.generate_key(
                function_code,
                "openrouter",
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
                    provider="openrouter",
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

            tokens_used = response.get("usage", {}).get("total_tokens", 0)
            input_tokens = response.get("usage", {}).get("prompt_tokens", 0)
            output_tokens = response.get("usage", {}).get("completion_tokens", 0)

            # Calculate cost
            cost = response.get("usage", {}).get("total_cost", 0.0)
            if cost == 0:
                cost = self._calculate_cost(input_tokens, output_tokens)

            # Cache the result
            if self.cache and cache_key:
                await self.cache.set(
                    cache_key,
                    summary,
                    {
                        "tokens": tokens_used,
                        "cost": cost,
                        "model": response.get("model", self.config.model),
                    },
                )

            return SummarizationResult(
                summary=summary,
                tokens_used=tokens_used,
                cost_estimate=cost,
                model_used=response.get("model", self.config.model),
                provider="openrouter",
                cached=False,
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "actual_model": response.get("model"),
                },
            )

        except Exception as e:
            return SummarizationResult(
                summary="", error=str(e), model_used=self.config.model, provider="openrouter"
            )

    async def generate_meta_overview(
        self,
        file_summaries: dict[str, Any],
        custom_prompt: str | None = None,
        max_tokens: int | None = None,
        tree_structure: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> SummarizationResult:
        """Generate meta-overview using higher-tier Gemini 2.5 Pro via OpenRouter.

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
        meta_model = override_model or ("z-ai/glm-4.6" if use_higher_tier else self.config.model)

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

        # Temporarily override model
        original_model = self.config.model
        original_extra_params = self.config.extra_params.copy()

        try:
            self.config.model = meta_model

            # Add extended thinking parameters for Gemini (if supported)
            if "gemini" in meta_model.lower():
                self.config.extra_params = {
                    **original_extra_params,
                    # Gemini parameters may differ - adjust as needed
                    "thinking_time": "extended",
                }
                logger.debug("Extended thinking requested for Gemini meta-overview")

            # Make API call with higher max_tokens
            response = await self._retry_with_backoff(
                self._make_api_call, messages, max_tokens or 2000
            )

            # Extract summary and token usage
            summary = response["choices"][0]["message"]["content"].strip()
            tokens_used = response.get("usage", {}).get("total_tokens", 0)
            input_tokens = response.get("usage", {}).get("prompt_tokens", 0)
            output_tokens = response.get("usage", {}).get("completion_tokens", 0)

            # Calculate cost
            cost = self._calculate_cost(input_tokens, output_tokens)

            return SummarizationResult(
                summary=summary,
                tokens_used=tokens_used,
                cost_estimate=cost,
                model_used=meta_model,
                provider="openrouter",
                cached=False,
                metadata={"input_tokens": input_tokens, "output_tokens": output_tokens},
            )

        except Exception as e:
            logger.error(f"Meta-overview generation failed: {e}")
            return SummarizationResult(
                summary="", error=str(e), model_used=meta_model, provider="openrouter"
            )
        finally:
            # Restore original configuration
            self.config.model = original_model
            self.config.extra_params = original_extra_params

    async def get_model_info(self) -> dict[str, Any]:
        """Get information about the current OpenRouter model."""
        # OpenRouter supports many models, return generic info
        info = {
            "provider": "openrouter",
            "model": self.config.model,
            "temperature": self.config.temperature,
            "api_base": self.config.api_base,
            "note": "OpenRouter provides access to multiple models. Check openrouter.ai/models for details.",
        }

        # Try to get live model info if possible
        try:
            session = await self._get_session()
            async with session.get(f"{self.config.api_base}/models") as response:
                if response.status == 200:
                    models_data = await response.json()
                    for model in models_data.get("data", []):
                        if model["id"] == self.config.model:
                            info.update(
                                {
                                    "context_window": model.get("context_length", "unknown"),
                                    "cost_per_1k_input": model.get("pricing", {}).get("prompt", 0),
                                    "cost_per_1k_output": model.get("pricing", {}).get(
                                        "completion", 0
                                    ),
                                    "description": model.get("description", ""),
                                }
                            )
                            break
        except (aiohttp.ClientError, asyncio.TimeoutError, KeyError, ValueError):
            # Log error but continue - model info retrieval is not critical
            pass

        return info

    async def validate_connection(self) -> bool:
        """Validate that the OpenRouter provider is properly configured."""
        if not self.config.api_key:
            return False

        try:
            # Try to fetch models list
            session = await self._get_session()
            async with session.get(f"{self.config.api_base}/models") as response:
                return bool(response.status == 200)
        except Exception:
            return False
