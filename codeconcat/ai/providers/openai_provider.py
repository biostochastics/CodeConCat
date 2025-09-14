"""OpenAI provider implementation for code summarization."""

import os
from typing import Any, Dict, Optional

import aiohttp

from ..base import AIProvider, AIProviderConfig, SummarizationResult
from ..cache import SummaryCache


class OpenAIProvider(AIProvider):
    """OpenAI API provider for code summarization."""

    def __init__(self, config: AIProviderConfig):
        """Initialize OpenAI provider."""
        super().__init__(config)

        # Set defaults for OpenAI
        if not config.api_key:
            config.api_key = os.getenv("OPENAI_API_KEY")

        if not config.api_base:
            config.api_base = "https://api.openai.com/v1"

        if not config.model:
            config.model = "gpt-4o-nano"  # Updated to 2025 budget model

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

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if not self._session:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
                **(self.config.custom_headers or {}),
            }
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self._session

    async def _make_api_call(self, messages: list, max_tokens: Optional[int] = None) -> dict:
        """Make an API call to OpenAI."""
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
                raise Exception(f"OpenAI API error ({response.status}): {error_text}")

            result = await response.json()
            return dict(result) if result else {}

    async def summarize_code(
        self,
        code: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
        max_length: Optional[int] = None,
    ) -> SummarizationResult:
        """Generate a summary for a code file using OpenAI."""
        # Check cache first
        if self.cache:
            cache_key = self.cache.generate_key(
                code, "openai", self.config.model, "summarize_code", language=language
            )
            cached_summary = await self.cache.get(cache_key)
            if cached_summary:
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
            # Make API call with retry
            response = await self._retry_with_backoff(self._make_api_call, messages, max_length)

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
        context: Optional[Dict[str, Any]] = None,
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

    async def get_model_info(self) -> Dict[str, Any]:
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
