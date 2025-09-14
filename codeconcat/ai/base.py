"""Base classes and interfaces for AI providers."""

import asyncio
import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Dict, Optional


class AIProviderType(Enum):
    """Supported AI provider types."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    LLAMACPP = "llamacpp"


@dataclass
class AIProviderConfig:
    """Configuration for an AI provider."""

    provider_type: AIProviderType
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model: str = ""
    temperature: float = 0.3
    max_tokens: int = 500
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    cache_enabled: bool = True
    cache_ttl: int = 3600  # 1 hour
    cost_per_1k_input_tokens: float = 0.0
    cost_per_1k_output_tokens: float = 0.0
    custom_headers: Dict[str, str] = field(default_factory=dict)
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SummarizationResult:
    """Result from an AI summarization request."""

    summary: str
    tokens_used: int = 0
    cost_estimate: float = 0.0
    model_used: str = ""
    provider: str = ""
    cached: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    # Centralized system prompts for consistency across all providers
    SYSTEM_PROMPT_CODE_SUMMARY = """You are an expert software architect and technical documentation specialist with deep knowledge of software design patterns, algorithms, and best practices across multiple programming languages. Your role is to analyze code and produce high-quality, actionable summaries that help developers quickly understand codebases. Focus on clarity, technical accuracy, and practical insights."""

    SYSTEM_PROMPT_FUNCTION_SUMMARY = """You are a senior software engineer specializing in code documentation. Your expertise includes identifying function contracts, understanding complex algorithms, and explaining code behavior concisely. Create summaries that are technically precise yet accessible, highlighting the 'what', 'how', and 'why' of each function."""

    def __init__(self, config: AIProviderConfig):
        """Initialize the AI provider with configuration."""
        self.config = config
        self._session = None

    @abstractmethod
    async def summarize_code(
        self,
        code: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
        max_length: Optional[int] = None,
    ) -> SummarizationResult:
        """Generate a summary for a code file.

        Args:
            code: The source code to summarize
            language: Programming language of the code
            context: Additional context (file path, project info, etc.)
            max_length: Maximum length of summary in tokens

        Returns:
            SummarizationResult with the generated summary
        """
        pass

    @abstractmethod
    async def summarize_function(
        self,
        function_code: str,
        function_name: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> SummarizationResult:
        """Generate a summary for a specific function.

        Args:
            function_code: The function source code
            function_name: Name of the function
            language: Programming language
            context: Additional context

        Returns:
            SummarizationResult with the generated summary
        """
        pass

    @abstractmethod
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model.

        Returns:
            Dictionary with model details (name, context window, costs, etc.)
        """
        pass

    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validate that the provider is properly configured and can connect.

        Returns:
            True if connection is valid, False otherwise
        """
        pass

    async def close(self):
        """Clean up resources (e.g., close HTTP sessions)."""
        if self._session:
            await self._session.close()

    def _generate_cache_key(self, content: str, **kwargs) -> str:
        """Generate a cache key for the given content and parameters."""
        cache_data = {
            "content": content,
            "model": self.config.model,
            "provider": self.config.provider_type.value,
            **kwargs,
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()

    async def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute a function with exponential backoff retry logic."""
        last_exception = None

        for attempt in range(self.config.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.config.max_retries - 1:
                    delay = self.config.retry_delay * (2**attempt)
                    await asyncio.sleep(delay)
                continue

        if last_exception is not None:
            raise last_exception
        raise RuntimeError("Unexpected retry error")

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        # Rough estimate: 1 token ≈ 4 characters for code
        return len(text) // 4

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost based on token usage."""
        input_cost = (input_tokens / 1000) * self.config.cost_per_1k_input_tokens
        output_cost = (output_tokens / 1000) * self.config.cost_per_1k_output_tokens
        return input_cost + output_cost

    def _create_code_summary_prompt(
        self, code: str, language: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a prompt for code summarization using CO-STAR framework."""
        file_path = context.get("file_path", "unknown") if context else "unknown"

        # Extract additional context if available
        num_functions = context.get("num_functions", 0) if context else 0
        num_classes = context.get("num_classes", 0) if context else 0
        imports = context.get("imports", []) if context else []
        imports_str = ", ".join(imports[:5]) if imports else "none"

        prompt = f"""### Role
You are an expert software engineer specializing in {language} code documentation and analysis.

### Context
File: {file_path}
Language: {language}
Structure: {num_classes} classes, {num_functions} functions
Key imports: {imports_str}

### Objective
Analyze and summarize the following {language} code, creating a comprehensive yet concise summary.

### Task
Provide a structured summary that covers:
1. **Primary Purpose**: What problem does this code solve? (1 sentence)
2. **Core Components**: Main classes/functions and their responsibilities
3. **Key Patterns**: Important design patterns, algorithms, or architectural decisions
4. **Dependencies**: Critical external libraries or modules used
5. **Technical Highlights**: Notable implementation details or complexity

### Style
Technical but accessible to intermediate developers. Use precise terminology while maintaining clarity.

### Format
Provide a 2-3 paragraph summary structured as:
- First paragraph: Overall purpose and functionality
- Second paragraph: Key implementation details and design choices
- Third paragraph (if needed): Important dependencies or integration points

### Code
```{language}
{code}
```

### Summary"""

        return prompt

    def _create_function_summary_prompt(
        self,
        function_code: str,
        function_name: str,
        language: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a prompt for function summarization using structured format."""
        file_path = context.get("file_path", "unknown") if context else "unknown"

        # Try to extract complexity hints from the code
        lines_of_code = len(function_code.splitlines())
        complexity_hint = (
            "simple" if lines_of_code < 10 else "moderate" if lines_of_code < 30 else "complex"
        )

        prompt = f"""### Role
You are a senior software engineer documenting {language} code for a technical team.

### Context
Function: {function_name}
From file: {file_path}
Language: {language}
Complexity: {complexity_hint} (~{lines_of_code} lines)

### Objective
Create a precise, informative summary of this function's behavior and implementation.

### Task
Analyze the function and provide:
1. **Purpose**: What problem it solves or functionality it provides
2. **Signature**: Key parameters and return value with types if evident
3. **Behavior**: Core logic, including any algorithms or patterns used
4. **Side Effects**: State mutations, I/O operations, or external interactions
5. **Error Handling**: How it handles edge cases or errors (if applicable)

### Format
Provide a concise 1-2 sentence summary that captures:
- Primary functionality and purpose
- Key technical details (algorithm, pattern, or approach used)
- Important considerations (side effects, performance, constraints)

Use this structure: "[Action verb] [what it does] by [how it does it], [any important notes]."

### Function Code
```{language}
{function_code}
```

### Summary"""

        return prompt


def with_retry(max_retries: int = 3, delay: float = 1.0):
    """Decorator for adding retry logic to async methods."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (2**attempt))
                    continue
            if last_exception is not None:
                raise last_exception
            raise RuntimeError("Unexpected retry error")

        return wrapper

    return decorator
