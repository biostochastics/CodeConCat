"""AI-powered summarization processor for CodeConcat."""

import asyncio
import logging
from pathlib import Path
from typing import Any

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
        self.ai_provider: AIProvider | None = None
        self.summary_writer = None
        self._initialize_provider()

        # Initialize summary writer if file persistence is enabled
        if getattr(self.config, "ai_save_summaries", False):
            from ..writer.summary_writer import SummaryWriter

            self.summary_writer = SummaryWriter(self.config)
            logger.info("Summary writer initialized for file persistence")

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
            "local_server": AIProviderType.LOCAL_SERVER,
            "vllm": AIProviderType.VLLM,
            "lmstudio": AIProviderType.LMSTUDIO,
            "llamacpp_server": AIProviderType.LLAMACPP_SERVER,
        }

        provider_type = provider_map.get(provider_type_str.lower())
        if not provider_type:
            logger.error(f"Unknown AI provider '{provider_type_str}'. Summarization disabled.")
            return

        # Build extra params for llama.cpp performance tuning
        extra_params: dict[str, int | str] = {}
        api_base = getattr(self.config, "ai_api_base", None)
        if api_base and isinstance(api_base, str) and not api_base.strip():
            api_base = None
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

        local_server_defaults = {
            AIProviderType.LOCAL_SERVER: ("local server", None),
            AIProviderType.VLLM: ("vLLM", "http://localhost:8000"),
            AIProviderType.LMSTUDIO: ("LM Studio", "http://localhost:1234"),
            AIProviderType.LLAMACPP_SERVER: ("llama.cpp server", "http://localhost:8080"),
        }

        if provider_type in local_server_defaults:
            server_label, default_base = local_server_defaults[provider_type]
            extra_params["server_kind"] = server_label
            if not api_base and default_base:
                api_base = default_base

        # Create provider config
        ai_config = AIProviderConfig(
            provider_type=provider_type,
            api_key=api_key,
            model=model or "",
            temperature=getattr(self.config, "ai_temperature", 0.3),
            max_tokens=getattr(self.config, "ai_max_tokens", 500),
            cache_enabled=getattr(self.config, "ai_cache_enabled", True),
            api_base=api_base,
            extra_params=extra_params,
        )

        try:
            self.ai_provider = get_ai_provider(ai_config)
            logger.info(
                f"Successfully initialized {provider_type_str} AI provider with model {model}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize AI provider '{provider_type_str}': {e}")
            logger.error(
                "AI summarization is disabled. Please check your API key and provider configuration."
            )
            logger.error(
                f"Tip: Use --ai-api-key or set {provider_type_str.upper()}_API_KEY environment variable"
            )
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

                # Track costs and metadata
                metadata = {
                    "tokens_used": file_summary.tokens_used,
                    "cost_estimate": file_summary.cost_estimate,
                    "model": file_summary.model_used,
                    "cached": file_summary.cached,
                }
                parsed_file.ai_metadata = metadata

                # Save individual summary to disk if enabled
                if self.summary_writer:
                    try:
                        saved_path = self.summary_writer.save_individual_summary(
                            parsed_file, file_summary.summary, metadata
                        )
                        if saved_path:
                            logger.debug(f"Saved summary to {saved_path}")
                    except Exception as e:
                        logger.warning(f"Failed to save summary to disk: {e}")
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

    async def process_batch(self, files: list[ParsedFileData]) -> list[ParsedFileData]:
        """Process multiple files in batch for efficiency.

        Args:
            files: List of parsed files

        Returns:
            List of files with summaries added (and optionally meta-overview)
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

        # Generate meta-overview if enabled
        ai_meta_enabled = getattr(self.config, "ai_meta_overview", False)
        if ai_meta_enabled:
            logger.info("Generating meta-overview...")
            meta_overview = await self.generate_meta_overview(processed_files)
            if meta_overview and processed_files:
                logger.info(f"Meta-overview generated successfully: {len(meta_overview)} chars")
                # Store the meta-overview in the first file's ai_metadata
                # This will be accessed by the writers
                if processed_files[0].ai_metadata is None:
                    processed_files[0].ai_metadata = {}
                processed_files[0].ai_metadata["meta_overview"] = meta_overview

                # Save meta-overview to disk if enabled
                if self.summary_writer:
                    try:
                        # Build tree structure for saving
                        tree_structure = self._build_tree_structure(processed_files)
                        context = self._collect_overview_context(processed_files)

                        # Get metadata from AI provider if available
                        meta_metadata = {
                            "files_count": len(processed_files),
                            "languages": context.get("languages", {}),
                            "total_loc": context.get("total_loc", 0),
                        }

                        saved_path = self.summary_writer.save_meta_overview(
                            meta_overview,
                            len(processed_files),
                            metadata=meta_metadata,
                            tree_structure=tree_structure,
                        )
                        if saved_path:
                            logger.info(f"Saved meta-overview to {saved_path}")
                    except Exception as e:
                        logger.warning(f"Failed to save meta-overview to disk: {e}")
            else:
                logger.warning("Meta-overview generation returned None or no files to store in")

        return processed_files

    def _build_tree_structure(self, files: list[ParsedFileData]) -> str:
        """Build a tree structure visualization from file paths.

        Args:
            files: List of parsed files

        Returns:
            String representation of the directory tree
        """
        from pathlib import Path

        # Extract unique directories and files
        paths = [Path(f.file_path) for f in files]

        # Build tree structure
        tree_dict: dict[str, Any] = {}
        for path in paths:
            parts = path.parts
            current = tree_dict
            for part in parts:
                if part not in current:
                    current[part] = {}
                current = current[part]

        # Render tree
        def render_tree(node, prefix=""):
            lines = []
            items = sorted(node.items())
            for i, (name, children) in enumerate(items):
                is_final = i == len(items) - 1
                connector = "└── " if is_final else "├── "
                lines.append(f"{prefix}{connector}{name}")
                if children:
                    extension = "    " if is_final else "│   "
                    lines.extend(render_tree(children, prefix + extension))
            return lines

        tree_lines = render_tree(tree_dict)
        return "\n".join(tree_lines)

    def _collect_overview_context(self, files: list[ParsedFileData]) -> dict[str, Any]:
        """Collect contextual information for meta-overview generation.

        Args:
            files: List of parsed files

        Returns:
            Dictionary with context information
        """
        from collections import Counter

        # Count languages
        languages = Counter([f.language for f in files if f.language])

        # Calculate total LOC
        total_loc = 0
        for f in files:
            if f.content:
                total_loc += len(f.content.splitlines())

        return {
            "total_files": len(files),
            "languages": dict(languages),
            "total_loc": total_loc,
        }

    async def generate_meta_overview(self, files: list[ParsedFileData]) -> str | None:
        """Generate a meta-overview from all file summaries with enhanced context.

        Args:
            files: List of files with AI summaries

        Returns:
            Meta-overview string or None if generation fails
        """
        if not self.ai_provider:
            logger.warning("Cannot generate meta-overview: AI provider not initialized")
            return None

        # Collect all file summaries
        file_summaries = {}
        for file_data in files:
            if hasattr(file_data, "ai_summary") and file_data.ai_summary:
                file_summaries[file_data.file_path] = file_data.ai_summary

        if not file_summaries:
            logger.info("No file summaries available for meta-overview generation")
            return None

        try:
            logger.info(f"Generating meta-overview from {len(file_summaries)} file summaries...")

            # Build tree structure
            tree_structure = self._build_tree_structure(files)
            logger.debug(f"Generated tree structure with {len(tree_structure)} characters")

            # Collect context
            context = self._collect_overview_context(files)
            logger.debug(f"Context: {context}")

            # Get custom prompt and max tokens from config
            custom_prompt = getattr(self.config, "ai_meta_overview_prompt", None)
            max_tokens = getattr(self.config, "ai_meta_overview_max_tokens", 2000)

            # Generate the meta-overview with enhanced context
            result = await self.ai_provider.generate_meta_overview(
                file_summaries,
                custom_prompt=custom_prompt,
                max_tokens=max_tokens,
                tree_structure=tree_structure,
                context=context,
            )

            if result and not result.error:
                logger.info(f"✓ Generated meta-overview: {len(result.summary)} chars")
                return result.summary
            elif result and result.error:
                logger.warning(f"Failed to generate meta-overview: {result.error}")
                return None

        except Exception as e:
            logger.error(f"Exception while generating meta-overview: {e}")
            import traceback

            logger.debug(traceback.format_exc())

        return None

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
        min_lines = getattr(self.config, "ai_min_file_lines", 5)
        content = parsed_file.content
        if content:
            line_count = len(content.splitlines())
            if line_count < min_lines:
                logger.info(
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
    ) -> SummarizationResult | None:
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

    def get_statistics(self) -> dict[str, Any]:
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


def create_summarization_processor(config: CodeConCatConfig) -> SummarizationProcessor | None:
    """Factory function to create a summarization processor.

    Args:
        config: Global configuration

    Returns:
        SummarizationProcessor instance or None if disabled
    """
    if not getattr(config, "enable_ai_summary", False):
        return None

    return SummarizationProcessor(config)
