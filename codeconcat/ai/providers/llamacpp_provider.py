"""Llama.cpp provider implementation for local model inference."""

import asyncio
import os
from pathlib import Path
from typing import Any, Dict, Optional

from ..base import AIProvider, AIProviderConfig, SummarizationResult
from ..cache import SummaryCache


class LlamaCppProvider(AIProvider):
    """Llama.cpp provider for local LLM inference."""

    def __init__(self, config: AIProviderConfig):
        """Initialize Llama.cpp provider."""
        super().__init__(config)

        # Set defaults for Llama.cpp
        if not config.model:
            # Look for model in common locations
            model_paths = [
                os.getenv("LLAMA_MODEL_PATH"),
                "./models/llama-2-7b-chat.gguf",
                "~/models/llama-2-7b-chat.gguf",
                "./llama-2-7b-chat.gguf",
            ]
            for path in model_paths:
                if path and Path(path).expanduser().exists():
                    config.model = str(Path(path).expanduser())
                    break

            if not config.model:
                raise ValueError(
                    "No model file found. Set LLAMA_MODEL_PATH env var or "
                    "specify model path in config"
                )

        # Llama.cpp specific settings
        self.n_ctx = config.extra_params.get("n_ctx", 2048)
        self.n_threads = config.extra_params.get("n_threads", 4)
        self.n_gpu_layers = config.extra_params.get("n_gpu_layers", 0)
        self.seed = config.extra_params.get("seed", -1)

        # Local models have no API costs
        config.cost_per_1k_input_tokens = 0
        config.cost_per_1k_output_tokens = 0

        self.cache = SummaryCache() if config.cache_enabled else None
        self._llm = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the Llama.cpp model."""
        try:
            from llama_cpp import Llama
        except ImportError as err:
            raise ImportError(
                "llama-cpp-python is not installed. Install it with: pip install llama-cpp-python"
            ) from err

        if not Path(self.config.model).exists():
            raise FileNotFoundError(f"Model file not found: {self.config.model}")

        try:
            self._llm = Llama(
                model_path=self.config.model,
                n_ctx=self.n_ctx,
                n_threads=self.n_threads,
                n_gpu_layers=self.n_gpu_layers,
                seed=self.seed,
                verbose=False,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}") from e

    async def _generate(self, prompt: str, max_tokens: Optional[int] = None) -> str:
        """Generate text using the local model."""
        if not self._llm:
            raise RuntimeError("Model not initialized")

        # Run generation in executor to avoid blocking
        loop = asyncio.get_event_loop()

        def _sync_generate():
            response = self._llm(
                prompt,
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=self.config.temperature,
                echo=False,
                stop=["</s>", "\n\n"],
            )
            return response["choices"][0]["text"].strip()

        return await loop.run_in_executor(None, _sync_generate)

    async def summarize_code(
        self,
        code: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
        max_length: Optional[int] = None,
    ) -> SummarizationResult:
        """Generate a summary for a code file using local Llama model."""
        # Check cache first
        if self.cache:
            cache_key = self.cache.generate_key(
                code, "llamacpp", self.config.model, "summarize_code", language=language
            )
            cached_summary = await self.cache.get(cache_key)
            if cached_summary:
                return SummarizationResult(
                    summary=cached_summary,
                    model_used=Path(self.config.model).name,
                    provider="llamacpp",
                    cached=True,
                )

        # Create the prompt with Llama format
        base_prompt = self._create_code_summary_prompt(code, language, context)

        # Format for Llama chat model
        # Use getattr with fallback to prevent AttributeError
        system_prompt = getattr(
            self,
            "SYSTEM_PROMPT_CODE_SUMMARY",
            "You are a helpful assistant that creates concise, informative code summaries.",
        )
        prompt = f"""<s>[INST] <<SYS>>
{system_prompt}
<</SYS>>

{base_prompt} [/INST]"""

        try:
            # Generate summary
            summary = await self._generate(prompt, max_length)

            # Estimate tokens (rough approximation for local models)
            input_tokens = self._estimate_tokens(prompt)
            output_tokens = self._estimate_tokens(summary)
            tokens_used = input_tokens + output_tokens

            # Cache the result
            if self.cache and cache_key:
                await self.cache.set(
                    cache_key,
                    summary,
                    {"tokens": tokens_used, "model": Path(self.config.model).name},
                )

            return SummarizationResult(
                summary=summary,
                tokens_used=tokens_used,
                cost_estimate=0.0,  # Local models have no cost
                model_used=Path(self.config.model).name,
                provider="llamacpp",
                cached=False,
                metadata={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "context_size": self.n_ctx,
                },
            )

        except Exception as e:
            return SummarizationResult(
                summary="",
                error=str(e),
                model_used=Path(self.config.model).name,
                provider="llamacpp",
            )

    async def summarize_function(
        self,
        function_code: str,
        function_name: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> SummarizationResult:
        """Generate a summary for a specific function using local Llama model."""
        # Check cache first
        if self.cache:
            cache_key = self.cache.generate_key(
                function_code,
                "llamacpp",
                self.config.model,
                "summarize_function",
                function_name=function_name,
                language=language,
            )
            cached_summary = await self.cache.get(cache_key)
            if cached_summary:
                return SummarizationResult(
                    summary=cached_summary,
                    model_used=Path(self.config.model).name,
                    provider="llamacpp",
                    cached=True,
                )

        # Create the prompt
        base_prompt = self._create_function_summary_prompt(
            function_code, function_name, language, context
        )

        # Format for Llama chat model
        # Use getattr with fallback to prevent AttributeError
        system_prompt = getattr(
            self,
            "SYSTEM_PROMPT_FUNCTION_SUMMARY",
            "You are a helpful assistant that creates concise function summaries.",
        )
        prompt = f"""<s>[INST] <<SYS>>
{system_prompt}
<</SYS>>

{base_prompt} [/INST]"""

        try:
            # Generate summary
            summary = await self._generate(prompt, 200)

            # Estimate tokens
            input_tokens = self._estimate_tokens(prompt)
            output_tokens = self._estimate_tokens(summary)
            tokens_used = input_tokens + output_tokens

            # Cache the result
            if self.cache and cache_key:
                await self.cache.set(
                    cache_key,
                    summary,
                    {"tokens": tokens_used, "model": Path(self.config.model).name},
                )

            return SummarizationResult(
                summary=summary,
                tokens_used=tokens_used,
                cost_estimate=0.0,
                model_used=Path(self.config.model).name,
                provider="llamacpp",
                cached=False,
                metadata={"input_tokens": input_tokens, "output_tokens": output_tokens},
            )

        except Exception as e:
            return SummarizationResult(
                summary="",
                error=str(e),
                model_used=Path(self.config.model).name,
                provider="llamacpp",
            )

    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current local model."""
        model_name = Path(self.config.model).name if self.config.model else "unknown"

        info = {
            "provider": "llamacpp",
            "model": model_name,
            "model_path": self.config.model,
            "context_window": self.n_ctx,
            "temperature": self.config.temperature,
            "n_threads": self.n_threads,
            "n_gpu_layers": self.n_gpu_layers,
            "cost_per_1k_input": 0.0,
            "cost_per_1k_output": 0.0,
            "is_local": True,
        }

        if self._llm:
            info["model_loaded"] = True
            info["model_type"] = "GGUF"
        else:
            info["model_loaded"] = False

        return info

    async def validate_connection(self) -> bool:
        """Validate that the Llama.cpp provider is properly configured."""
        if not self.config.model:
            return False

        if not Path(self.config.model).exists():
            return False

        if not self._llm:
            return False

        try:
            # Try a minimal generation
            test_result = await self._generate("Hello", max_tokens=1)
            return len(test_result) > 0
        except Exception:
            return False

    async def close(self):
        """Clean up resources."""
        # Llama.cpp doesn't need explicit cleanup, but we'll clear the reference
        self._llm = None
        await super().close()
