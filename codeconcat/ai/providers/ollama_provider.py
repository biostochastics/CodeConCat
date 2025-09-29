"""Ollama provider implementation for local model access."""

import asyncio
import os
from typing import Any, Dict, Optional

import aiohttp

from ..base import AIProvider, AIProviderConfig, SummarizationResult
from ..cache import SummaryCache


class OllamaProvider(AIProvider):
    """Ollama provider for local model code summarization."""

    def __init__(self, config: AIProviderConfig):
        """Initialize Ollama provider with auto-discovery."""
        super().__init__(config)

        # Set defaults for Ollama
        if not config.api_base:
            config.api_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")

        # Auto-discover models if not specified
        if not config.model:
            config.model = asyncio.run(self._auto_discover_model()) or "codellama"

        # Local models have no cost
        config.cost_per_1k_input_tokens = 0
        config.cost_per_1k_output_tokens = 0

        self.cache = SummaryCache() if config.cache_enabled else None

    async def _auto_discover_model(self) -> Optional[str]:
        """Auto-discover the best available model for code summarization."""
        try:
            # Create a temporary session for discovery
            headers = {"Content-Type": "application/json"}
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
                url = f"{self.config.api_base}/api/tags"
                async with session.get(url) as response:
                    if response.status != 200:
                        return None

                    data = await response.json()
                    models = [m["name"] for m in data.get("models", [])]

                    if not models:
                        return None

                    # Prioritized list of code-specific models
                    code_models = [
                        "deepseek-coder-v2",
                        "deepseek-coder",  # DeepSeek Coder models
                        "codellama",
                        "codellama:latest",  # Meta's CodeLlama
                        "codegemma",
                        "codegemma:latest",  # Google's CodeGemma
                        "starcoder2",
                        "starcoder",  # Hugging Face StarCoder
                        "wizardcoder",
                        "wizardlm",  # WizardCoder
                        "phind-codellama",
                        "phind",  # Phind's models
                        "mistral",
                        "mistral:latest",  # Mistral as fallback
                        "llama3.2",
                        "llama3",
                        "llama2",  # General Llama models
                    ]

                    # Find the first available code model
                    for preferred in code_models:
                        if any(preferred in model.lower() for model in models):
                            matching = [m for m in models if preferred in m.lower()][0]
                            import logging

                            logging.info(f"Auto-discovered Ollama model: {matching}")
                            return str(matching)

                    # Fallback to first available model
                    import logging

                    logging.info(f"Using first available Ollama model: {models[0]}")
                    return str(models[0])

        except Exception:
            # Silent failure, will use default
            return None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if not self._session:
            headers = {"Content-Type": "application/json", **self.config.custom_headers}
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self._session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self._session

    async def _make_api_call(self, prompt: str, max_tokens: Optional[int] = None) -> dict:
        """Make an API call to Ollama."""
        session = await self._get_session()

        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": max_tokens or self.config.max_tokens,
                **self.config.extra_params,
            },
        }

        url = f"{self.config.api_base}/api/generate"

        async with session.post(url, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Ollama API error ({response.status}): {error_text}")

            result = await response.json()
            return dict(result) if result else {}

    async def summarize_code(
        self,
        code: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
        max_length: Optional[int] = None,
    ) -> SummarizationResult:
        """Generate a summary for a code file using Ollama."""
        # Check cache first
        if self.cache:
            cache_key = self.cache.generate_key(
                code, "ollama", self.config.model, "summarize_code", language=language
            )
            cached_summary = await self.cache.get(cache_key)
            if cached_summary:
                return SummarizationResult(
                    summary=cached_summary,
                    model_used=self.config.model,
                    provider="ollama",
                    cached=True,
                )

        # Create the prompt (Ollama uses a single prompt, not messages)
        # Use getattr with fallback to prevent AttributeError
        system_prompt = getattr(
            self,
            "SYSTEM_PROMPT_CODE_SUMMARY",
            "You are a helpful assistant that creates concise, informative code summaries.",
        )
        user_prompt = self._create_code_summary_prompt(code, language, context)
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        try:
            # Make API call with retry
            response = await self._retry_with_backoff(self._make_api_call, full_prompt, max_length)

            # Extract summary
            summary = response["response"].strip()

            # Ollama provides token counts
            prompt_eval_count = response.get("prompt_eval_count", 0)
            eval_count = response.get("eval_count", 0)
            tokens_used = prompt_eval_count + eval_count

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
                provider="ollama",
                cached=False,
                metadata={
                    "input_tokens": prompt_eval_count,
                    "output_tokens": eval_count,
                    "eval_duration": response.get("eval_duration"),
                    "load_duration": response.get("load_duration"),
                },
            )

        except Exception as e:
            return SummarizationResult(
                summary="", error=str(e), model_used=self.config.model, provider="ollama"
            )

    async def summarize_function(
        self,
        function_code: str,
        function_name: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> SummarizationResult:
        """Generate a summary for a specific function using Ollama."""
        # Check cache first
        if self.cache:
            cache_key = self.cache.generate_key(
                function_code,
                "ollama",
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
                    provider="ollama",
                    cached=True,
                )

        # Create the prompt
        # Use getattr with fallback to prevent AttributeError
        system_prompt = getattr(
            self,
            "SYSTEM_PROMPT_FUNCTION_SUMMARY",
            "You are a helpful assistant that creates concise function summaries.",
        )
        user_prompt = self._create_function_summary_prompt(
            function_code, function_name, language, context
        )
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        try:
            # Make API call with retry
            response = await self._retry_with_backoff(
                self._make_api_call,
                full_prompt,
                200,  # Shorter max tokens for function summaries
            )

            # Extract summary
            summary = response["response"].strip()

            prompt_eval_count = response.get("prompt_eval_count", 0)
            eval_count = response.get("eval_count", 0)
            tokens_used = prompt_eval_count + eval_count

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
                provider="ollama",
                cached=False,
                metadata={
                    "input_tokens": prompt_eval_count,
                    "output_tokens": eval_count,
                    "eval_duration": response.get("eval_duration"),
                },
            )

        except Exception as e:
            return SummarizationResult(
                summary="", error=str(e), model_used=self.config.model, provider="ollama"
            )

    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current Ollama model."""
        info = {
            "provider": "ollama",
            "model": self.config.model,
            "temperature": self.config.temperature,
            "api_base": self.config.api_base,
            "cost_per_1k_input": 0,
            "cost_per_1k_output": 0,
            "note": "Local model - no API costs",
        }

        # Try to get model details from Ollama
        try:
            session = await self._get_session()
            url = f"{self.config.api_base}/api/show"
            payload = {"name": self.config.model}

            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    model_data = await response.json()
                    info.update(
                        {
                            "parameters": model_data.get("parameters", ""),
                            "template": model_data.get("template", ""),
                            "details": model_data.get("details", {}),
                        }
                    )
        except (aiohttp.ClientError, asyncio.TimeoutError, KeyError, ValueError):
            # Log error but continue - model listing is not critical
            pass

        return info

    async def validate_connection(self) -> bool:
        """Validate that the Ollama provider is properly configured."""
        import logging

        logger = logging.getLogger(__name__)

        try:
            # Check if Ollama server is running
            session = await self._get_session()
            async with session.get(f"{self.config.api_base}/api/tags") as response:
                if response.status != 200:
                    logger.warning(f"Ollama server not responding at {self.config.api_base}")
                    return False

                # Check if the specified model exists
                data = await response.json()
                models = [m["name"] for m in data.get("models", [])]

                # If no models available
                if not models:
                    logger.warning(
                        "No models found in Ollama. Run 'ollama pull codellama' or similar."
                    )
                    return False

                # If no model specified, we've auto-discovered one
                if not self.config.model:
                    return True

                # Check if specified model is available
                model_available = (
                    self.config.model in models or f"{self.config.model}:latest" in models
                )

                if not model_available:
                    logger.warning(
                        f"Model '{self.config.model}' not found in Ollama. "
                        f"Available models: {', '.join(models[:5])}"
                        f"{' and more...' if len(models) > 5 else ''}"
                    )
                    # Try to suggest pulling the model
                    logger.info(f"To install the model, run: ollama pull {self.config.model}")
                    return False

                logger.info(f"Ollama provider validated with model: {self.config.model}")
                return True

        except aiohttp.ClientError as e:
            logger.error(f"Cannot connect to Ollama at {self.config.api_base}: {e}")
            logger.info("Make sure Ollama is running: 'ollama serve' or check https://ollama.ai")
            return False
        except Exception as e:
            logger.error(f"Ollama validation error: {e}")
            return False
