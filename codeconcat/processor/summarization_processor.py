"""AI-powered summarization processor for CodeConcat."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..ai import AIProvider, AIProviderConfig, SummarizationResult, get_ai_provider
from ..ai.base import AIProviderType
from ..base_types import CodeConCatConfig, ParsedFileData

logger = logging.getLogger(__name__)


class SummarizationProcessor:
    """Processor that adds AI-generated summaries to code files and functions."""

    def __init__(self, config: CodeConCatConfig):
        """Initialize the summarization processor.

        Args:
            config: Global configuration object
        """
        self.config = config
        self.ai_provider: Optional[AIProvider] = None
        self._initialize_provider()

    def _initialize_provider(self):
        """Initialize the AI provider based on configuration."""
        if not getattr(self.config, "enable_ai_summary", False):
            logger.info("AI summary not enabled in config")
            return

        # Get provider settings from config
        provider_type_str = getattr(self.config, "ai_provider", "openai")
        api_key = getattr(self.config, "ai_api_key", None)
        model = getattr(self.config, "ai_model", None)

        logger.info(f"Initializing AI provider: {provider_type_str} with model {model}")
        logger.debug(f"API key present: {bool(api_key)}")

        # Map string to enum
        provider_map = {
            "openai": AIProviderType.OPENAI,
            "anthropic": AIProviderType.ANTHROPIC,
            "openrouter": AIProviderType.OPENROUTER,
            "ollama": AIProviderType.OLLAMA,
            "llamacpp": AIProviderType.LLAMACPP,
        }

        provider_type = provider_map.get(provider_type_str.lower())
        if not provider_type:
            logger.error(f"Unknown AI provider '{provider_type_str}'. Summarization disabled.")
            return

        # Build extra params for llama.cpp performance tuning
        extra_params = {}
        if provider_type == AIProviderType.LLAMACPP:
            if (
                hasattr(self.config, "llama_gpu_layers")
                and self.config.llama_gpu_layers is not None
            ):
                extra_params["llama_gpu_layers"] = self.config.llama_gpu_layers
            if (
                hasattr(self.config, "llama_context_size")
                and self.config.llama_context_size is not None
            ):
                extra_params["llama_context_size"] = self.config.llama_context_size
            if hasattr(self.config, "llama_threads") and self.config.llama_threads is not None:
                extra_params["llama_threads"] = self.config.llama_threads
            if (
                hasattr(self.config, "llama_batch_size")
                and self.config.llama_batch_size is not None
            ):
                extra_params["llama_batch_size"] = self.config.llama_batch_size

        # Create provider config
        ai_config = AIProviderConfig(
            provider_type=provider_type,
            api_key=api_key,
            model=model or "",
            temperature=getattr(self.config, "ai_temperature", 0.3),
            max_tokens=getattr(self.config, "ai_max_tokens", 500),
            cache_enabled=getattr(self.config, "ai_cache_enabled", True),
            extra_params=extra_params,
        )

        try:
            self.ai_provider = get_ai_provider(ai_config)
            logger.info(f"Successfully initialized {provider_type_str} AI provider")
        except Exception as e:
            logger.error(f"Failed to initialize AI provider: {e}. Summarization disabled.")
            self.ai_provider = None

    async def process_file(self, parsed_file: ParsedFileData) -> ParsedFileData:
        """Process a single file and add AI summaries.

        Args:
            parsed_file: The parsed file data

        Returns:
            ParsedFileData with AI summaries added
        """
        if not self.ai_provider:
            logger.warning(f"Cannot summarize {parsed_file.file_path}: AI provider not initialized")
            return parsed_file

        # Skip if summarization is disabled or file is too small
        if not self._should_summarize_file(parsed_file):
            return parsed_file

        try:
            logger.info(f"Generating AI summary for {parsed_file.file_path}...")
            # Generate file-level summary
            file_summary = await self._generate_file_summary(parsed_file)
            if file_summary and not file_summary.error:
                parsed_file.ai_summary = file_summary.summary
                logger.info(
                    f"✓ Generated summary for {parsed_file.file_path}: {len(file_summary.summary)} chars"
                )

                # Track costs if available
                if hasattr(parsed_file, "ai_metadata"):
                    parsed_file.ai_metadata = {
                        "tokens_used": file_summary.tokens_used,
                        "cost_estimate": file_summary.cost_estimate,
                        "model": file_summary.model_used,
                        "cached": file_summary.cached,
                    }
            elif file_summary and file_summary.error:
                logger.warning(
                    f"Failed to generate summary for {parsed_file.file_path}: {file_summary.error}"
                )

            # Generate function-level summaries if enabled
            if getattr(self.config, "ai_summarize_functions", False):
                await self._add_function_summaries(parsed_file)

        except Exception as e:
            logger.error(f"Exception while generating summary for {parsed_file.file_path}: {e}")
            import traceback

            logger.debug(traceback.format_exc())

        return parsed_file

    async def process_batch(self, files: List[ParsedFileData]) -> List[ParsedFileData]:
        """Process multiple files in batch for efficiency.

        Args:
            files: List of parsed files

        Returns:
            List of files with summaries added
        """
        if not self.ai_provider:
            return files

        # Process files concurrently with a semaphore to limit concurrent requests
        max_concurrent = getattr(self.config, "ai_max_concurrent", 5)
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(file_data):
            """Process a file with semaphore-controlled concurrency.

            Args:
                file_data: The parsed file data to process

            Returns:
                ParsedFileData with AI summaries added
            """
            async with semaphore:
                return await self.process_file(file_data)

        tasks = [process_with_semaphore(f) for f in files]
        processed_files = await asyncio.gather(*tasks)

        return processed_files

    def _should_summarize_file(self, parsed_file: ParsedFileData) -> bool:
        """Determine if a file should be summarized.

        Args:
            parsed_file: The parsed file data

        Returns:
            True if the file should be summarized
        """
        # Skip if already has a summary
        if hasattr(parsed_file, "ai_summary") and parsed_file.ai_summary:
            logger.debug(f"Skipping {parsed_file.file_path}: already has summary")
            return False

        # Check file size threshold
        min_lines = getattr(self.config, "ai_min_file_lines", 20)
        content = parsed_file.content
        if content:
            line_count = len(content.splitlines())
            if line_count < min_lines:
                logger.debug(
                    f"Skipping {parsed_file.file_path}: {line_count} lines < {min_lines} minimum"
                )
                return False

        # Check language inclusion/exclusion
        included_languages = getattr(self.config, "ai_include_languages", None)
        excluded_languages = getattr(self.config, "ai_exclude_languages", [])

        if included_languages and parsed_file.language not in included_languages:
            logger.debug(
                f"Skipping {parsed_file.file_path}: language {parsed_file.language} not in include list"
            )
            return False

        if parsed_file.language in excluded_languages:
            logger.debug(
                f"Skipping {parsed_file.file_path}: language {parsed_file.language} in exclude list"
            )
            return False

        # Check file path patterns
        excluded_patterns = getattr(self.config, "ai_exclude_patterns", [])
        if excluded_patterns:
            file_path = Path(parsed_file.file_path)
            for pattern in excluded_patterns:
                if file_path.match(pattern):
                    logger.debug(
                        f"Skipping {parsed_file.file_path}: matches excluded pattern '{pattern}'"
                    )
                    return False

        logger.debug(f"Will summarize {parsed_file.file_path}")
        return True

    async def _generate_file_summary(
        self, parsed_file: ParsedFileData
    ) -> Optional[SummarizationResult]:
        """Generate a summary for an entire file.

        Args:
            parsed_file: The parsed file data

        Returns:
            SummarizationResult or None if failed
        """
        # Check if this is a diff and prepare appropriate context
        is_diff = hasattr(parsed_file, "diff_metadata") and parsed_file.diff_metadata

        if is_diff and parsed_file.diff_metadata:
            # For diffs, use diff-specific context and content
            diff_metadata = parsed_file.diff_metadata
            context = {
                "file_path": parsed_file.file_path,
                "change_type": diff_metadata.change_type,
                "additions": diff_metadata.additions,
                "deletions": diff_metadata.deletions,
                "from_ref": diff_metadata.from_ref,
                "to_ref": diff_metadata.to_ref,
            }

            # Add old path if it's a rename
            if diff_metadata.old_path:
                context["old_path"] = diff_metadata.old_path

            # Use diff content if available, otherwise fall back to regular content
            content = getattr(parsed_file, "diff_content", None) or parsed_file.content

            # Create a specialized prompt for diff summarization
            diff_prompt = self._create_diff_summary_prompt(parsed_file, content or "")

            # Override the content with the specialized prompt
            content = diff_prompt

        else:
            # Regular file summary context
            context = {
                "file_path": parsed_file.file_path,
                "imports": parsed_file.imports[:10] if parsed_file.imports else [],  # Limit imports
                "num_functions": sum(1 for d in parsed_file.declarations if d.kind == "function"),
                "num_classes": sum(1 for d in parsed_file.declarations if d.kind == "class"),
            }

            # Use annotated content if available and comments were removed, otherwise use original
            content = getattr(parsed_file, "annotated_content", None) or parsed_file.content

        # Truncate content if too large
        max_chars = getattr(self.config, "ai_max_content_chars", 50000)
        if content and len(content) > max_chars:
            content = content[:max_chars] + "\n... (content truncated)"

        if not content:
            return SummarizationResult(summary="", error="No content to summarize")

        if not self.ai_provider:
            return SummarizationResult(summary="", error="AI provider not initialized")

        return await self.ai_provider.summarize_code(
            str(content), parsed_file.language or "unknown", context
        )

    def _create_diff_summary_prompt(self, parsed_file: ParsedFileData, diff_content: str) -> str:
        """Create a specialized prompt for diff summarization.

        Constructs an intelligent prompt that guides the AI to provide meaningful
        summaries of code changes, focusing on the impact, purpose, and technical
        details of modifications between Git references.

        Args:
            parsed_file: The parsed file data containing diff metadata
            diff_content: The actual diff content to summarize

        Returns:
            A formatted prompt string that combines diff content with contextual
            instructions for effective summarization.
        """
        meta = parsed_file.diff_metadata
        if not meta:
            # Shouldn't happen but handle gracefully
            return diff_content

        prompt_parts = [
            f"Analyze the following code changes between Git refs '{meta.from_ref}' and '{meta.to_ref}':",
            f"\nFile: {parsed_file.file_path}",
            f"Change Type: {meta.change_type}",
            f"Lines: +{meta.additions} / -{meta.deletions}",
        ]

        if meta.old_path:
            prompt_parts.append(f"Renamed from: {meta.old_path}")

        prompt_parts.extend(
            [
                "\n=== DIFF CONTENT ===\n",
                diff_content,
                "\n=== END DIFF ===\n",
                "\nProvide a concise summary that covers:",
                "1. The purpose and impact of these changes",
                "2. Key modifications to functionality or behavior",
                "3. Any notable patterns, refactoring, or architectural changes",
                "4. Potential risks or areas that may need additional review",
                "\nFocus on the 'why' and 'what changed' rather than line-by-line descriptions.",
                "Keep the summary under 3-4 sentences for clarity.",
            ]
        )

        return "\n".join(prompt_parts)

    async def _add_function_summaries(self, parsed_file: ParsedFileData):
        """Add summaries to individual functions in a file.

        Args:
            parsed_file: The parsed file data
        """
        # Filter for functions and methods
        functions = [d for d in parsed_file.declarations if d.kind in ("function", "method")]

        # Limit number of functions to summarize
        max_functions = getattr(self.config, "ai_max_functions_per_file", 10)
        min_function_lines = getattr(self.config, "ai_min_function_lines", 10)

        # Sort by complexity/size and take top N
        functions = sorted(
            functions, key=lambda f: f.end_line - f.start_line if f.end_line else 0, reverse=True
        )[:max_functions]

        # Generate summaries for selected functions
        for func in functions:
            # Skip small functions
            if func.end_line and (func.end_line - func.start_line) < min_function_lines:
                continue

            try:
                # Extract function code
                content = parsed_file.content
                if not content:
                    continue

                lines = content.splitlines()
                if func.end_line:
                    func_lines = lines[func.start_line - 1 : func.end_line]
                else:
                    func_lines = lines[func.start_line - 1 : func.start_line + 20]  # Fallback

                function_code = "\n".join(func_lines)

                # Generate summary
                if not self.ai_provider:
                    continue

                result = await self.ai_provider.summarize_function(
                    function_code,
                    func.name,
                    parsed_file.language or "unknown",
                    {"file_path": parsed_file.file_path},
                )

                if result and not result.error:
                    func.ai_summary = result.summary

            except Exception as e:
                logger.warning(f"Failed to summarize function {func.name}: {e}")

    async def cleanup(self):
        """Clean up resources."""
        if self.ai_provider:
            await self.ai_provider.close()

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the summarization process.

        Returns:
            Dictionary with statistics
        """
        stats = {
            "enabled": self.ai_provider is not None,
            "provider": getattr(self.config, "ai_provider", "none"),
            "model": getattr(self.config, "ai_model", "none"),
        }

        if self.ai_provider and hasattr(self.ai_provider, "cache"):
            cache_stats = self.ai_provider.cache.get_stats()
            stats["cache"] = cache_stats

        return stats


def create_summarization_processor(config: CodeConCatConfig) -> Optional[SummarizationProcessor]:
    """Factory function to create a summarization processor.

    Args:
        config: Global configuration

    Returns:
        SummarizationProcessor instance or None if disabled
    """
    if not getattr(config, "enable_ai_summary", False):
        return None

    return SummarizationProcessor(config)
