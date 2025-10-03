"""OpenAI-compatible local server provider for vLLM, TGI, LocalAI, etc."""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

import aiohttp
from aiohttp import ClientConnectorError

from ..base import AIProvider, AIProviderConfig, AIProviderType, SummarizationResult
from ..cache import SummaryCache

_SERVER_PRESETS: Dict[AIProviderType, Dict[str, Optional[str]]] = {
    AIProviderType.LOCAL_SERVER: {
        "name": "local server",
        "api_base": "http://localhost:8000",
        "api_base_env": "LOCAL_LLM_API_BASE",
        "api_key_env": "LOCAL_LLM_API_KEY",
        "model_env": "LOCAL_LLM_MODEL",
    },
    AIProviderType.VLLM: {
        "name": "vLLM",
        "api_base": "http://localhost:8000",
        "api_base_env": "VLLM_API_BASE",
        "api_key_env": "VLLM_API_KEY",
        "model_env": "VLLM_MODEL",
    },
    AIProviderType.LMSTUDIO: {
        "name": "LM Studio",
        "api_base": "http://localhost:1234",
        "api_base_env": "LMSTUDIO_API_BASE",
        "api_key_env": "LMSTUDIO_API_KEY",
        "model_env": "LMSTUDIO_MODEL",
    },
    AIProviderType.LLAMACPP_SERVER: {
        "name": "llama.cpp server",
        "api_base": "http://localhost:8080",
        "api_base_env": "LLAMACPP_SERVER_API_BASE",
        "api_key_env": "LLAMACPP_SERVER_API_KEY",
        "model_env": "LLAMACPP_SERVER_MODEL",
    },
}


def _first_non_empty_env(*env_names: Optional[str]) -> Optional[str]:
    """Return the first environment variable with a non-empty value."""

    for env_name in env_names:
        if not env_name:
            continue
        value = os.getenv(env_name)
        if value and value.strip():
            return value.strip()
    return None


logger = logging.getLogger(__name__)


class LocalServerProvider(AIProvider):
    """Provider for OpenAI-compatible local inference servers (vLLM, TGI, LocalAI, etc.)."""

    _session: Optional[aiohttp.ClientSession]

    def __init__(self, config: AIProviderConfig):
        """Initialize local server provider."""
        super().__init__(config)

        preset = _SERVER_PRESETS.get(
            config.provider_type, _SERVER_PRESETS[AIProviderType.LOCAL_SERVER]
        )

        # Derive human-friendly server label
        extra_server_kind = config.extra_params.get("server_kind", None)
        self.server_kind = extra_server_kind or preset.get("name") or "local server"

        # Resolve API base precedence: explicit config > provider-specific env > generic env > preset default
        api_base_from_env = _first_non_empty_env(preset.get("api_base_env"), "LOCAL_LLM_API_BASE")
        config.api_base = config.api_base or api_base_from_env or preset.get("api_base")

        # Default to environment model if provided; otherwise mark for auto-discovery
        model_from_env = _first_non_empty_env(preset.get("model_env"), "LOCAL_LLM_MODEL")
        if model_from_env and not config.model:
            config.model = model_from_env

        # Local models have no cost
        config.cost_per_1k_input_tokens = 0
        config.cost_per_1k_output_tokens = 0

        # Some local servers may require an API key (e.g., for auth)
        api_key_from_env = _first_non_empty_env(preset.get("api_key_env"), "LOCAL_LLM_API_KEY")
        if not config.api_key and api_key_from_env:
            config.api_key = api_key_from_env
        if config.api_key is None:
            config.api_key = ""

        self.cache = SummaryCache() if config.cache_enabled else None
        self._auto_discovery_needed = not bool(config.model)
        self._model_autodiscovery_attempted = False
        self._auto_discovered_model: Optional[str] = None
        self._last_error_message: Optional[str] = None

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

    @staticmethod
    def _parse_models_response(data: Any) -> List[str]:
        """Extract model names from a variety of OpenAI-compatible responses."""

        models: List[str] = []

        if isinstance(data, dict):
            if isinstance(data.get("data"), list):
                for item in data["data"]:
                    if isinstance(item, dict):
                        candidate = item.get("id") or item.get("model") or item.get("name")
                        if candidate:
                            models.append(str(candidate))
            elif isinstance(data.get("models"), list):
                for item in data["models"]:
                    if isinstance(item, dict):
                        candidate = item.get("id") or item.get("model") or item.get("name")
                        if candidate:
                            models.append(str(candidate))
                    elif isinstance(item, str):
                        models.append(item)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    candidate = item.get("id") or item.get("model") or item.get("name")
                    if candidate:
                        models.append(str(candidate))
                elif isinstance(item, str):
                    models.append(item)

        return models

    async def _ensure_model(self) -> None:
        """Ensure a model name is available, attempting auto-discovery when needed."""

        if self.config.model:
            self._auto_discovery_needed = False
            return

        if not self._auto_discovery_needed and self._model_autodiscovery_attempted:
            return

        if self._model_autodiscovery_attempted:
            if not self.config.model:
                raise RuntimeError(
                    "No model configured for local server. Set ai_model or LOCAL_LLM_MODEL."
                )
            return

        self._model_autodiscovery_attempted = True

        try:
            session = await self._get_session()
            api_base = self.config.api_base or "http://localhost:8000"
            for endpoint in ["/v1/models", "/models"]:
                url = f"{api_base.rstrip('/')}{endpoint}"
                try:
                    async with session.get(url) as response:
                        if response.status != 200:
                            continue
                        data = await response.json()
                        models = self._parse_models_response(data)
                        if models:
                            discovered = models[0]
                            self.config.model = discovered
                            self._auto_discovered_model = discovered
                            self._auto_discovery_needed = False
                            logger.info(
                                "Auto-discovered local model '%s' from %s",
                                discovered,
                                url,
                            )
                            return
                except Exception as exc:  # pragma: no cover - network errors logged elsewhere
                    logger.debug("Model auto-discovery failed for %s: %s", url, exc)
                    continue
        except Exception as exc:  # pragma: no cover - unexpected loop exceptions
            logger.debug("Model auto-discovery aborted: %s", exc)

        if not self.config.model:
            self._last_error_message = (
                "Unable to auto-discover a model. Specify ai_model or set LOCAL_LLM_MODEL."
            )
            raise RuntimeError(self._last_error_message)

    async def _make_api_call(self, messages: list, max_tokens: Optional[int] = None) -> dict:
        """Make an OpenAI-compatible API call to the local server."""
        session = await self._get_session()
        await self._ensure_model()

        # Build OpenAI-compatible payload
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": max_tokens or self.config.max_tokens,
        }

        # Add any extra parameters that might be server-specific
        safe_extra_params = {
            key: value
            for key, value in self.config.extra_params.items()
            if key not in {"server_kind"}
        }
        payload.update(safe_extra_params)

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
                    "server_kind": self.server_kind,
                    "auto_discovered_model": self._auto_discovered_model,
                },
            )

        except Exception as e:
            self._last_error_message = str(e)
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
                    "api_base": self.config.api_base,
                    "server_kind": self.server_kind,
                    "auto_discovered_model": self._auto_discovered_model,
                },
            )

        except Exception as e:
            self._last_error_message = str(e)
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
            "supported_servers": [
                "vLLM",
                "LM Studio",
                "llama.cpp server",
                "TGI",
                "LocalAI",
                "FastChat",
                "Oobabooga",
            ],
            "server_kind": self.server_kind,
            "auto_discovered_model": self._auto_discovered_model,
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
                            models = self._parse_models_response(data)
                            if models:
                                info["available_models"] = models
                                if not self.config.model:
                                    self.config.model = models[0]
                                    self._auto_discovered_model = models[0]
                                    self._auto_discovery_needed = False
                            break
                except Exception:
                    continue
        except Exception:
            # Not critical if we can't get model list
            pass

        return info

    async def validate_connection(self) -> bool:
        """Validate that the local server is properly configured and accessible."""

        api_base = self.config.api_base or "http://localhost:8000"
        session = await self._get_session()
        health_endpoints = [
            "/health",
            "/healthz",
            "/readyz",
            "/status",
            "/livez",
            "/v1/health",
            "/v1/models",
            "/models",
        ]

        for endpoint in health_endpoints:
            url = f"{api_base.rstrip('/')}{endpoint}"
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        if endpoint in {"/v1/models", "/models"}:
                            try:
                                data = await response.json()
                            except Exception:  # pragma: no cover - server returned non-JSON
                                data = None
                            if data is not None:
                                models = self._parse_models_response(data)
                                if models and not self.config.model:
                                    self.config.model = models[0]
                                    self._auto_discovered_model = models[0]
                                    self._auto_discovery_needed = False
                                    logger.info(
                                        "%s model auto-discovered during validation: %s",
                                        self.server_kind,
                                        models[0],
                                    )
                        logger.info("%s server validated at %s", self.server_kind, url)
                        self._last_error_message = None
                        return True
                    if response.status in {401, 403}:
                        message = (
                            f"Authentication failed for {self.server_kind} at {url} (status "
                            f"{response.status})."
                        )
                        logger.warning(message)
                        self._last_error_message = message
                        return False
            except ClientConnectorError:
                message = (
                    f"Connection refused at {api_base}. Is your {self.server_kind} server running?"
                )
                logger.warning(message)
                self._last_error_message = message
                return False
            except asyncio.TimeoutError:
                message = f"Timed out connecting to {self.server_kind} at {url}."
                logger.warning(message)
                self._last_error_message = message
                return False
            except Exception as exc:  # pragma: no cover - unexpected validation errors
                logger.debug("Validation request to %s failed: %s", url, exc)
                continue

        # If health endpoints didn't return success, try minimal completion
        try:
            await self._ensure_model()
        except Exception as exc:
            self._last_error_message = str(exc)
            logger.warning(str(exc))
            return False

        try:
            messages = [{"role": "user", "content": "ping"}]
            result = await self._make_api_call(messages, max_tokens=1)
            if result and "choices" in result:
                logger.info(
                    "%s server validated via chat completion at %s", self.server_kind, api_base
                )
                self._last_error_message = None
                return True
        except ClientConnectorError:
            message = (
                f"Connection refused at {api_base}. Is your {self.server_kind} server running?"
            )
            logger.warning(message)
            self._last_error_message = message
            return False
        except Exception as exc:
            message = f"Failed to validate {self.server_kind} via completion: {exc}"
            logger.warning(message)
            self._last_error_message = message
            return False

        logger.warning("Could not validate %s at %s", self.server_kind, api_base)
        self._last_error_message = f"Could not validate {self.server_kind} at {api_base}"
        return False

    @property
    def last_error(self) -> Optional[str]:
        """Return the most recent error message from the provider, if any."""

        return self._last_error_message
