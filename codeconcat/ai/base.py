"""Base classes and interfaces for AI providers."""

import asyncio
import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, ClassVar, Dict, Optional


class AIProviderType(Enum):
    """Supported AI provider types."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    LLAMACPP = "llamacpp"
    LOCAL_SERVER = "local_server"  # OpenAI-compatible local servers (vLLM, TGI, LocalAI)


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
    # Using ClassVar to ensure these are class-level constants
    SYSTEM_PROMPT_CODE_SUMMARY: ClassVar[str] = (
        """You are an expert software architect and technical documentation specialist with deep knowledge of software design patterns, algorithms, and best practices across multiple programming languages. Your role is to analyze code and produce high-quality, actionable summaries that help developers quickly understand codebases. Focus on clarity, technical accuracy, and practical insights."""
    )

    SYSTEM_PROMPT_FUNCTION_SUMMARY: ClassVar[str] = (
        """You are a senior software engineer specializing in code documentation. Your expertise includes identifying function contracts, understanding complex algorithms, and explaining code behavior concisely. Create summaries that are technically precise yet accessible, highlighting the 'what', 'how', and 'why' of each function."""
    )

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

    async def generate_meta_overview(
        self,
        file_summaries: Dict[str, str],
        custom_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        tree_structure: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> SummarizationResult:
        """Generate a meta-overview from multiple file summaries with enhanced context.

        Args:
            file_summaries: Dictionary mapping file paths to their summaries
            custom_prompt: Optional custom prompt to override default
            max_tokens: Maximum tokens for the overview
            tree_structure: Optional tree structure visualization of the codebase
            context: Optional context dict (languages, file count, total LOC, etc.)

        Returns:
            SummarizationResult with the generated meta-overview
        """
        # Default implementation using the existing summarize_code method
        # Individual providers can override for optimized implementations

        # Use the enhanced prompt generator
        final_prompt = self._create_meta_overview_prompt(
            file_summaries,
            tree_structure=tree_structure,
            context=context,
            custom_prompt=custom_prompt,
        )

        # Use the existing summarize_code method with special context
        overview_context = {"type": "meta_overview", "file_count": len(file_summaries)}
        if context:
            overview_context.update(context)

        return await self.summarize_code(
            final_prompt,
            "overview",
            overview_context,
            max_length=max_tokens or 2000,
        )

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
            try:
                await self._session.close()
                # Give aiohttp time to finish connection cleanup
                await asyncio.sleep(0.1)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                # Ignore cleanup errors - session is being torn down anyway
                pass

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

    def _escape_triple_backticks(self, code: str) -> str:
        """Escape triple backticks in code to prevent markdown/prompt injection.

        Replaces ``` with escaped version to prevent breaking markdown code blocks.
        This prevents both accidental formatting issues and potential prompt injection attacks.
        """
        # Replace triple backticks with escaped version
        # Using zero-width space (\u200b) to break the sequence while maintaining visual appearance
        return code.replace("```", "`\u200b`\u200b`")

    def _truncate_code_if_needed(self, code: str, max_chars: int = 50000) -> tuple[str, bool]:
        """Truncate code if it exceeds model's context window limit.

        Args:
            code: The source code to potentially truncate
            max_chars: Maximum number of characters allowed (can be overridden)

        Returns:
            Tuple of (processed_code, was_truncated)
        """
        # Try to get model-specific context window
        from .models_config import get_model_config

        model_config = get_model_config(self.config.model)
        if model_config:
            # Calculate max chars based on context window
            # Reserve 20% for prompt template and response
            available_tokens = int(model_config.context_window * 0.8)
            # Conservative estimate: 1 token ≈ 4 characters for code
            model_max_chars = available_tokens * 4
            # Use the smaller of model limit or provided max_chars
            max_chars = min(max_chars, model_max_chars)

        if len(code) <= max_chars:
            return code, False

        # Truncate and add a note
        truncated_code = code[:max_chars]
        # Try to truncate at a line boundary for cleaner output
        last_newline = truncated_code.rfind("\n")
        if last_newline > max_chars * 0.9:  # If we have a newline in the last 10%
            truncated_code = truncated_code[:last_newline]

        truncated_code += "\n\n# [CODE TRUNCATED - Exceeded model context window]"
        return truncated_code, True

    def _create_code_summary_prompt(
        self, code: str, language: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a prompt for code summarization using enhanced CO-STAR framework with few-shot examples."""
        file_path = context.get("file_path", "unknown") if context else "unknown"

        # Extract additional context if available
        num_functions = context.get("num_functions", 0) if context else 0
        num_classes = context.get("num_classes", 0) if context else 0
        imports = context.get("imports", []) if context else []
        # Escape imports to prevent injection
        imports_str = ", ".join(imports[:5]) if imports else "none"
        imports_str = self._escape_triple_backticks(imports_str)

        # Truncate code based on model's context window
        code, was_truncated = self._truncate_code_if_needed(code)
        # Escape triple backticks to prevent markdown breaking and prompt injection
        code = self._escape_triple_backticks(code)

        truncation_note = " (Note: Code was truncated due to length)" if was_truncated else ""

        # Language-specific analysis hints
        language_hints = {
            "python": "Pay attention to decorators, type hints, async/await patterns, class inheritance, and data science libraries (pandas, numpy, scikit-learn).",
            "javascript": "Note React/Vue components, promises/async, ES6+ features, and module patterns.",
            "typescript": "Focus on type definitions, interfaces, generics, and type safety patterns.",
            "java": "Consider annotations, interfaces, inheritance hierarchies, and design patterns.",
            "go": "Highlight goroutines, channels, interfaces, and error handling patterns.",
            "rust": "Note ownership, borrowing, traits, lifetimes, and error handling with Result/Option.",
            "cpp": "Consider templates, memory management, STL usage, and object-oriented patterns.",
            "c": "Focus on memory management, pointer usage, and system-level operations.",
            "r": "Focus on data manipulation (tidyverse/dplyr), statistical analysis, visualization (ggplot2), vectorized operations, and package dependencies. Note S3/S4 classes, functional programming patterns, and data science workflows.",
            "julia": "Note multiple dispatch, type annotations, metaprogramming, performance optimizations, and scientific computing patterns.",
            "swift": "Consider optionals, protocols, extensions, value types vs reference types, and iOS/macOS frameworks.",
            "kotlin": "Focus on null safety, coroutines, extension functions, data classes, and Android patterns.",
            "scala": "Highlight functional programming, pattern matching, implicits, traits, and actor model.",
            "ruby": "Note metaprogramming, DSLs, blocks/procs/lambdas, Rails patterns, and dynamic features.",
            "php": "Consider frameworks (Laravel/Symfony), PSR standards, type declarations, and web patterns.",
            "csharp": "Focus on LINQ, async/await, properties, events, and .NET ecosystem.",
            "elixir": "Highlight actor model, pattern matching, OTP, supervisors, and fault tolerance.",
            "haskell": "Note pure functions, monads, type classes, lazy evaluation, and category theory concepts.",
            "clojure": "Focus on immutability, LISP syntax, macros, STM, and functional patterns.",
            "perl": "Consider regular expressions, CPAN modules, references, and text processing.",
            "lua": "Note metatables, coroutines, table structures, and embedding patterns.",
            "dart": "Focus on Flutter widgets, async patterns, null safety, and mobile development.",
            "matlab": "Highlight matrix operations, vectorization, toolboxes, and scientific computing.",
            "fortran": "Consider numerical computation, array operations, modules, and HPC patterns.",
            "cobol": "Note COBOL divisions, file handling, business logic, and mainframe patterns.",
        }

        lang_hint = language_hints.get(
            language.lower(), "Focus on language-specific idioms and patterns."
        )

        # Few-shot example for consistency
        few_shot_example = """
Example Output Format:
```
This module implements a REST API client for interacting with the GitHub API, providing async methods for repository management, issue tracking, and pull request operations. The implementation uses aiohttp for non-blocking HTTP requests and implements automatic retry logic with exponential backoff for resilience.

The core architecture follows a repository pattern with `GitHubClient` as the main entry point, delegating to specialized handlers (`RepoHandler`, `IssueHandler`, `PRHandler`) for different API endpoints. Key features include OAuth2 authentication, rate limit handling via `RateLimiter` class, and comprehensive error handling with custom exception types. The client maintains connection pooling for performance and supports both pagination and webhook event processing.

Dependencies include aiohttp for async HTTP, pydantic for data validation, and tenacity for retry logic. The module integrates with the application's caching layer through the `CacheManager` interface and emits metrics via the `MetricsCollector` for monitoring API usage and performance.
```"""

        prompt = f"""### Role
You are an expert software architect analyzing {language} code with deep knowledge of design patterns, best practices, and language-specific idioms.

### Context
File: {file_path}
Language: {language}
Structure: {num_classes} classes, {num_functions} functions
Key imports: {imports_str}
Analysis Focus: {lang_hint}

### Objective
Create a high-quality technical summary that helps developers quickly understand this code's purpose, architecture, and implementation details.

### Task
Analyze the code and provide:
1. **Purpose & Functionality**: Core problem solved and main capabilities
2. **Architecture & Design**: Key components, patterns, and structural decisions
3. **Implementation Details**: Algorithms, data structures, and technical approaches
4. **Integration Points**: External dependencies, APIs, and interfaces
5. **Quality Indicators**: Performance considerations, error handling, testing approach

### Output Requirements
- 3 concise paragraphs (4-5 sentences each)
- First paragraph: WHAT the code does and WHY it exists
- Second paragraph: HOW it works (architecture, patterns, key algorithms)
- Third paragraph: INTEGRATION aspects (dependencies, interfaces, usage context)
- Use active voice and present tense
- Include specific class/function names when discussing key components
- Mention concrete technical details (algorithms used, design patterns, etc.)

### Style Guide
- Technical precision with clarity
- Avoid generic statements; be specific
- Use industry-standard terminology
- Balance between high-level overview and implementation details{truncation_note}

{few_shot_example}

### Code to Analyze
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
        """Create a prompt for function summarization using enhanced structured format with examples."""
        file_path = context.get("file_path", "unknown") if context else "unknown"

        # Escape function name to prevent injection
        function_name = self._escape_triple_backticks(function_name)

        # Truncate function code based on model's context window (with smaller default for functions)
        # Functions typically should be smaller than full files
        from .models_config import get_model_config

        model_config = get_model_config(self.config.model)
        if model_config:
            # For functions, use 10% of context window or 10k chars, whichever is smaller
            available_tokens = int(model_config.context_window * 0.1)
            model_max_chars = available_tokens * 4
            max_chars = min(10000, model_max_chars)
        else:
            max_chars = 10000

        function_code, was_truncated = self._truncate_code_if_needed(
            function_code, max_chars=max_chars
        )
        # Escape triple backticks to prevent markdown breaking and prompt injection
        function_code = self._escape_triple_backticks(function_code)

        # Try to extract complexity hints from the code
        lines_of_code = len(function_code.splitlines())
        complexity_hint = (
            "simple" if lines_of_code < 10 else "moderate" if lines_of_code < 30 else "complex"
        )

        # Detect common patterns for better analysis
        has_async = "async " in function_code or "await " in function_code
        has_generator = "yield " in function_code
        has_decorator = function_code.strip().startswith("@")

        pattern_hints = []
        if has_async:
            pattern_hints.append("async/await")
        if has_generator:
            pattern_hints.append("generator")
        if has_decorator:
            pattern_hints.append("decorated")

        pattern_str = f" ({', '.join(pattern_hints)})" if pattern_hints else ""

        truncation_note = " (Note: Function was truncated due to length)" if was_truncated else ""

        # Language-specific function analysis focus
        lang_function_hints = {
            "python": "Consider decorators, generators, type hints, exception handling, and data science operations (numpy vectorization, pandas operations).",
            "javascript": "Note callbacks, promises, arrow functions, and closure usage.",
            "typescript": "Focus on type signatures, generics, and type guards.",
            "java": "Consider method overloading, exceptions, and annotations.",
            "go": "Note error returns, defer statements, and goroutine usage.",
            "rust": "Focus on ownership, Result/Option returns, and trait implementations.",
            "cpp": "Consider templates, const-correctness, and exception specifications.",
            "c": "Focus on pointer operations, memory allocation, and return codes.",
            "r": "Note vectorized operations, apply family functions, tidyverse pipelines (%>%), statistical functions, data frame manipulations, and S3/S4 method dispatch.",
            "julia": "Consider multiple dispatch signatures, type parameters, macro usage, and performance annotations.",
            "swift": "Focus on optionals, guard statements, protocol conformance, and throws/rethrows.",
            "kotlin": "Note suspend functions, inline functions, extension functions, and null safety operators.",
            "scala": "Consider implicit parameters, partial functions, pattern matching, and for comprehensions.",
            "ruby": "Focus on blocks, yield statements, method_missing, and metaprogramming.",
            "php": "Note type declarations, nullable types, variadic functions, and generators.",
            "csharp": "Consider async/await, LINQ expressions, properties, and extension methods.",
            "elixir": "Focus on pattern matching, guard clauses, pipe operator, and GenServer callbacks.",
            "haskell": "Note type signatures, monadic operations, currying, and lazy evaluation.",
            "clojure": "Consider destructuring, multi-methods, transducers, and macro expansion.",
            "perl": "Focus on context (scalar/list), references, regular expressions, and special variables.",
            "lua": "Note varargs, metatables, coroutines, and multiple returns.",
            "dart": "Consider async/await, named parameters, cascade notation, and null safety.",
            "matlab": "Focus on matrix operations, function handles, varargin/varargout, and nested functions.",
            "fortran": "Note pure/elemental functions, intent specifications, and array operations.",
            "cobol": "Consider PERFORM statements, paragraph structure, and COPY statements.",
        }

        lang_hint = lang_function_hints.get(
            language.lower(), "Focus on function contract and implementation."
        )

        # Few-shot examples for consistency
        few_shot_examples = """
Example Summaries:

Simple function:
"Validates email addresses using regex pattern matching, returning True for valid RFC-compliant addresses and False otherwise, with special handling for internationalized domains."

Complex async function:
"Orchestrates parallel API calls to fetch user data from multiple services using asyncio.gather, implements circuit breaker pattern for fault tolerance, caches results with TTL expiration, and returns aggregated user profile with fallback to partial data on service failures."

Generator function:
"Yields Fibonacci sequence values up to specified limit using generator pattern for memory efficiency, supports both iteration count and value threshold termination, with optional memoization for repeated calls."
"""

        prompt = f"""### Role
You are a senior software engineer creating precise technical documentation for {language} functions.

### Context
Function: {function_name}{pattern_str}
From file: {file_path}
Language: {language}
Complexity: {complexity_hint} (~{lines_of_code} lines)
Analysis Focus: {lang_hint}

### Objective
Create a comprehensive yet concise summary that captures the function's complete behavior, implementation approach, and usage considerations.

### Analysis Guidelines
1. **Purpose & Contract**: What problem it solves, expected inputs/outputs
2. **Implementation Strategy**: Core algorithm, data structures, design patterns
3. **Behavioral Details**: Edge cases, error handling, state changes
4. **Performance Characteristics**: Time/space complexity, optimization techniques
5. **Integration Context**: Dependencies, side effects, concurrency considerations

### Output Format
Write 1-2 sentences (max 50 words) following this structure:
"[Action verb] [primary function] by/using [implementation approach], [key technical details], [important considerations/constraints]."

Key requirements:
- Use present tense and active voice
- Include specific technical terms (algorithm names, patterns, etc.)
- Mention concrete implementation details not obvious from the name
- Note any side effects, state mutations, or external dependencies
- Highlight error handling or edge cases if significant{truncation_note}

{few_shot_examples}

### Function Code to Analyze
```{language}
{function_code}
```

### Summary"""

        return prompt

    def _create_meta_overview_prompt(
        self,
        file_summaries: Dict[str, str],
        tree_structure: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        custom_prompt: Optional[str] = None,
    ) -> str:
        """Create an enhanced prompt for meta-overview generation with tree structure.

        Args:
            file_summaries: Dictionary mapping file paths to their summaries
            tree_structure: Optional tree structure visualization of the codebase
            context: Additional context (file count, languages, total LOC, etc.)
            custom_prompt: Optional custom prompt to use instead of default

        Returns:
            Formatted prompt string for meta-overview generation
        """
        # If custom prompt provided, use it with minimal enhancement
        if custom_prompt:
            combined_summaries = "\n\n".join(
                [f"**{path}**\n{summary}" for path, summary in file_summaries.items()]
            )
            return f"{custom_prompt}\n\n### File Summaries\n{combined_summaries}"

        # Extract context information
        total_files = len(file_summaries)
        languages = context.get("languages", {}) if context else {}
        total_loc = context.get("total_loc", 0) if context else 0

        # Build language distribution string
        lang_dist = ", ".join([f"{lang}: {count} files" for lang, count in languages.items()])
        if not lang_dist:
            lang_dist = "mixed"

        # Prepare combined summaries
        summary_sections = []
        for file_path, summary in file_summaries.items():
            # Escape to prevent injection
            file_path_safe = self._escape_triple_backticks(file_path)
            summary_safe = self._escape_triple_backticks(summary)
            summary_sections.append(f"**{file_path_safe}**\n{summary_safe}")

        combined_summaries = "\n\n".join(summary_sections)

        # Create comprehensive prompt
        prompt_parts = [
            "### Role",
            "You are a senior software architect conducting a comprehensive codebase analysis. Your expertise includes system design, architectural patterns, technology assessment, and identifying technical debt and improvement opportunities across large-scale projects.",
            "",
            "### Context",
            f"Project Overview: {total_files} files analyzed",
            f"Languages: {lang_dist}",
        ]

        if total_loc > 0:
            prompt_parts.append(f"Total Lines of Code: ~{total_loc:,}")

        # Add tree structure if provided
        if tree_structure:
            prompt_parts.extend(
                [
                    "",
                    "### Directory Structure",
                    "```",
                    tree_structure,
                    "```",
                ]
            )

        prompt_parts.extend(
            [
                "",
                "### Objective",
                "Synthesize the individual file summaries below into a comprehensive, high-level technical overview of the entire codebase. This meta-overview should provide strategic insights that go beyond individual file descriptions, identifying overarching patterns, architectural decisions, and system-wide characteristics.",
                "",
                "### Analysis Framework",
                "Structure your analysis into EXACTLY 7 distinct sections, following this precise format:",
                "",
                "**1. System Purpose & Domain**",
                "Start with: '[System Name] is a [type/category] system that [primary purpose]...'",
                "- What problem does this system solve?",
                "- Primary domain or business context",
                "- Intended users or consumers",
                "- Core capabilities and scope",
                "",
                "**2. Architectural Overview**",
                "Start with: 'Architecturally, the codebase is [pattern type] organized as [structure]...'",
                "- Overall architecture pattern (microservices, monolith, layered, event-driven, etc.)",
                "- Component organization and major subsystems",
                "- Key architectural boundaries and interfaces",
                "- Data flow and processing pipelines",
                "- Module/package structure and relationships",
                "",
                "**3. Technical Stack & Dependencies**",
                "Start with: 'The stack blends [categories of technologies]...'",
                "- Core technologies, frameworks, and libraries (with specific names and versions)",
                "- External services or API integrations",
                "- Notable technology choices or constraints",
                "- Build tools, package managers, and development workflow",
                "",
                "**4. Code Quality & Design Patterns**",
                "Start with: 'Design patterns are [prevalence] and [adjectives]...'",
                "- Prevalent design patterns (MVC, repository, factory, observer, etc.) with examples",
                "- Code structure and maintainability assessment",
                "- Coding conventions and consistency",
                "- Overall code quality and engineering practices",
                "- Testing coverage and strategies",
                "",
                "**5. Cross-Cutting Concerns**",
                "Start with: 'Cross-cutting concerns are [assessment]...'",
                "- Logging, monitoring, and observability approaches",
                "- Security measures and authentication mechanisms",
                "- Error handling and resilience patterns",
                "- Testing strategies (unit, integration, e2e)",
                "- Configuration and environment management",
                "- Performance optimization techniques",
                "",
                "**6. Architectural Risks & Technical Debt**",
                "Start with: 'There are [number/severity] architectural risks and areas of technical debt...'",
                "- Signs of technical debt or code smells (with specific examples)",
                "- Scalability concerns and bottlenecks",
                "- Areas that are over-engineered or under-engineered",
                "- Security vulnerabilities or risks",
                "- Maintenance challenges",
                "- Consistency issues or fragmentation",
                "",
                "**7. Strengths & Actionable Recommendations**",
                "Start with: 'Despite [challenges], the codebase exhibits [positive qualities]...'",
                "- Strongest aspects of the codebase",
                "- Notable capabilities or sophisticated implementations",
                "- Specific opportunities for improvement or refactoring",
                "- Actionable next steps for maintainers (prioritized list)",
                "- Quick wins vs strategic improvements",
                "",
                "### Output Requirements",
                "CRITICAL: Your response MUST follow this exact structure:",
                "- Write EXACTLY 7 numbered sections as specified above",
                "- Each section: 1 paragraph of 4-6 sentences",
                "- Start each section with the suggested opening phrase pattern",
                "- Use precise technical terminology with specific examples (file names, class names, function names)",
                "- Reference actual components when discussing architecture",
                "- Balance strategic insights with concrete technical details",
                "- Use present tense and active voice throughout",
                "- End with a bulleted list of 3-5 prioritized actionable recommendations",
                "",
                "### File Summaries",
                combined_summaries,
                "",
                "### Meta-Overview",
                "Begin your structured 7-section analysis:",
            ]
        )

        return "\n".join(prompt_parts)


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
