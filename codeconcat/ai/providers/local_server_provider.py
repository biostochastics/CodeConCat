"""OpenAI-compatible local server provider for vLLM, TGI, LocalAI, etc."""

import os
from typing import Any, Dict, Optional

import aiohttp

from ..base import AIProvider, AIProviderConfig, SummarizationResult
from ..cache import SummaryCache


class LocalServerProvider(AIProvider):
    """Provider for OpenAI-compatible local inference servers (vLLM, TGI, LocalAI, etc.)."""

    _session: Optional[aiohttp.ClientSession]

    def __init__(self, config: AIProviderConfig):
        """Initialize local server provider."""
        super().__init__(config)

        # Set defaults for local servers
        if not config.api_base:
            # Common local server endpoints
            config.api_base = os.getenv("LOCAL_LLM_API_BASE", "http://localhost:8000")

        # Default to a common model name if not specified
        if not config.model:
            config.model = os.getenv("LOCAL_LLM_MODEL", "local-model")

        # Local models have no cost
        config.cost_per_1k_input_tokens = 0
        config.cost_per_1k_output_tokens = 0

        # Some local servers may require an API key (e.g., for auth)
        if not config.api_key:
            config.api_key = os.getenv("LOCAL_LLM_API_KEY", "")

        self.cache = SummaryCache() if config.cache_enabled else None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None:
            headers = {"Content-Type": "application/json"}
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            headers.update(self.config.custom_headers)

            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self._session

    async def _make_api_call(self, messages: list, max_tokens: Optional[int] = None) -> dict:
        """Make an OpenAI-compatible API call to the local server."""
        session = await self._get_session()

        # Build OpenAI-compatible payload
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
        }

        # Add any extra parameters that might be server-specific
        payload.update(self.config.extra_params)

        # Support both /v1/chat/completions and /chat/completions
        api_base = self.config.api_base or "http://localhost:8000"
        url = f"{api_base.rstrip('/')}/v1/chat/completions"

        async with session.post(url, json=payload) as response:
            if response.status == 404:
                # Try without /v1 prefix
                url = f"{api_base.rstrip('/')}/chat/completions"
                async with session.post(url, json=payload) as retry_response:
                    if retry_response.status != 200:
                        error_text = await retry_response.text()
                        raise Exception(
                            f"Local server API error ({retry_response.status}): {error_text}"
                        )
                    result = await retry_response.json()
                    return dict(result) if result else {}
            elif response.status != 200:
                error_text = await response.text()
                raise Exception(f"Local server API error ({response.status}): {error_text}")
            else:
                result = await response.json()
                return dict(result) if result else {}

    async def summarize_code(
        self,
        code: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
        max_length: Optional[int] = None,
    ) -> SummarizationResult:
        """Generate a summary for a code file using local server."""
        # Check cache first
        if self.cache:
            cache_key = self.cache.generate_key(
                code, "local_server", self.config.model, "summarize_code", language=language
            )
            cached_summary = await self.cache.get(cache_key)
            if cached_summary:
                return SummarizationResult(
                    summary=cached_summary,
                    model_used=self.config.model,
                    provider="local_server",
                    cached=True,
                )

        # Create messages for OpenAI-compatible format
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

            # Extract summary (OpenAI format)
            summary = response["choices"][0]["message"]["content"].strip()

            # Extract token usage if available
            usage = response.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            tokens_used = usage.get("total_tokens", prompt_tokens + completion_tokens)

            # Local models have no cost
            cost = 0.0

            # Cache the result
            if self.cache and cache_key:
                await self.cache.set(
                    cache_key, summary, {"tokens": tokens_used, "model": self.config.model}
                )

            return SummarizationResult(
                summary=summary,
                tokens_used=tokens_used,
                cost_estimate=cost,
                model_used=self.config.model,
                provider="local_server",
                cached=False,
                metadata={
                    "input_tokens": prompt_tokens,
                    "output_tokens": completion_tokens,
                    "api_base": self.config.api_base,
                },
            )

        except Exception as e:
            return SummarizationResult(
                summary="", error=str(e), model_used=self.config.model, provider="local_server"
            )

    async def summarize_function(
        self,
        function_code: str,
        function_name: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> SummarizationResult:
        """Generate a summary for a specific function using local server."""
        # Check cache first
        if self.cache:
            cache_key = self.cache.generate_key(
                function_code,
                "local_server",
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
                    provider="local_server",
                    cached=True,
                )

        # Create messages
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

            # Extract summary
            summary = response["choices"][0]["message"]["content"].strip()

            usage = response.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            tokens_used = usage.get("total_tokens", prompt_tokens + completion_tokens)

            # Local models have no cost
            cost = 0.0

            # Cache the result
            if self.cache and cache_key:
                await self.cache.set(
                    cache_key, summary, {"tokens": tokens_used, "model": self.config.model}
                )

            return SummarizationResult(
                summary=summary,
                tokens_used=tokens_used,
                cost_estimate=cost,
                model_used=self.config.model,
                provider="local_server",
                cached=False,
                metadata={
                    "input_tokens": prompt_tokens,
                    "output_tokens": completion_tokens,
                },
            )

        except Exception as e:
            return SummarizationResult(
                summary="", error=str(e), model_used=self.config.model, provider="local_server"
            )

    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current local server model."""
        info = {
            "provider": "local_server",
            "model": self.config.model,
            "api_base": self.config.api_base,
            "temperature": self.config.temperature,
            "cost_per_1k_input": 0,
            "cost_per_1k_output": 0,
            "note": "OpenAI-compatible local inference server",
            "supported_servers": ["vLLM", "TGI", "LocalAI", "FastChat", "Oobabooga"],
        }

        # Try to get server info if available
        try:
            session = await self._get_session()
            # Try common model listing endpoints
            api_base = self.config.api_base or "http://localhost:8000"
            for endpoint in ["/v1/models", "/models"]:
                url = f"{api_base.rstrip('/')}{endpoint}"
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            info["available_models"] = data.get("data", [])
                            break
                except Exception:
                    continue
        except Exception:
            # Not critical if we can't get model list
            pass

        return info

    async def validate_connection(self) -> bool:
        """Validate that the local server is properly configured and accessible."""
        import logging

        logger = logging.getLogger(__name__)

        try:
            session = await self._get_session()

            # Try to list models first (common health check)
            api_base = self.config.api_base or "http://localhost:8000"
            for endpoint in ["/v1/models", "/models", "/health", "/healthz"]:
                url = f"{api_base.rstrip('/')}{endpoint}"
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            logger.info(f"Local server validated at {self.config.api_base}")
                            return True
                except Exception:
                    continue

            # If no health endpoints work, try a minimal completion
            messages = [{"role": "user", "content": "Hi"}]
            try:
                result = await self._make_api_call(messages, max_tokens=1)
                if result and "choices" in result:
                    logger.info(
                        f"Local server validated via completion test at {self.config.api_base}"
                    )
                    return True
            except Exception:
                pass

            logger.warning(f"Could not validate local server at {self.config.api_base}")
            return False

        except Exception as e:
            logger.error(f"Local server validation error: {e}")
            logger.info(
                f"Make sure your OpenAI-compatible server is running at {self.config.api_base}"
            )
            return False
