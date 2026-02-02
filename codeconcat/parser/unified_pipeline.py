#!/usr/bin/env python3
"""
Unified parsing pipeline for CodeConcat.

This module consolidates the functionality of file_parser.py and enhanced_pipeline.py
into a single, clean, and extensible parsing pipeline with progressive fallback support.

Features:
- Progressive parser fallback (Tree-sitter → Enhanced Regex → Standard Regex)
- Security scanning integration
- Token counting support
- Unicode normalization
- Comprehensive error handling and reporting
- Plugin-based architecture for extensibility
"""

import functools
import logging
import os
import traceback
import unicodedata
from concurrent.futures import ProcessPoolExecutor, TimeoutError, as_completed
from pathlib import Path
from typing import Any, Protocol

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    track,
)

from ..base_types import (
    CodeConCatConfig,
    Declaration,
    DiffMetadata,
    EnhancedParserInterface,
    ParsedFileData,
    ParseResult,
    SecurityIssue,
    SecuritySeverity,
    TokenStats,
)
from ..errors import (
    FileProcessingError,
    ParserError,
    UnsupportedLanguageError,
)
from ..parser.shared import MergeStrategy, ResultMerger
from ..processor.security_processor import SecurityProcessor
from ..processor.token_counter import get_token_stats
from ..utils.feature_flags import is_enabled
from ..validation.unsupported_reporter import get_reporter as get_unsupported_reporter

logger = logging.getLogger(__name__)


class ProgressCallback(Protocol):
    """Protocol for progress callbacks."""

    def __call__(self, current: int, total: int, message: str = "") -> None:
        """Update progress."""
        ...


# Allowed language identifiers for security validation
ALLOWED_LANGUAGES = {
    "python",
    "javascript",
    "typescript",
    "java",
    "cpp",
    "c",
    "csharp",
    "go",
    "rust",
    "php",
    "ruby",
    "swift",
    "kotlin",
    "scala",
    "r",
    "bash",
    "shell",
    "julia",
    "perl",
    "powershell",
    "sql",
    "graphql",
    "solidity",
    "html",
    "css",
    "xml",
    "yaml",
    "json",
    "toml",
    "ini",
    "markdown",
    "rst",
    "tex",
    "documentation",
    "config",
    "unknown",
    "glsl",
    "hlsl",
    "metal",
    "wat",
    "wasm",
}


def _reconstruct_declaration(data: dict | Declaration) -> Declaration:
    """Reconstruct a Declaration object from a dictionary.

    Handles nested children declarations recursively. If the input is already
    a Declaration object, it is returned unchanged.

    Args:
        data: Dictionary representation of Declaration or existing Declaration object.
            Expected keys: kind, name, start_line, end_line, modifiers (optional),
            docstring (optional), signature (optional), children (optional).

    Returns:
        Declaration object reconstructed from the dictionary data.

    Raises:
        KeyError: If required keys (kind, name, start_line, end_line) are missing.
        TypeError: If data is neither a dict nor a Declaration.
    """
    if isinstance(data, Declaration):
        return data

    # Recursively reconstruct children
    children = [_reconstruct_declaration(child) for child in data.get("children", [])]

    # Handle modifiers - could be list from JSON serialization
    modifiers = data.get("modifiers", set())
    if isinstance(modifiers, list):
        modifiers = set(modifiers)

    return Declaration(
        kind=data["kind"],
        name=data["name"],
        start_line=data["start_line"],
        end_line=data["end_line"],
        modifiers=modifiers,
        docstring=data.get("docstring", ""),
        signature=data.get("signature", ""),
        children=children,
        ai_summary=data.get("ai_summary"),
    )


def _reconstruct_parsed_file_data(result_dict: dict) -> ParsedFileData:
    """Reconstruct ParsedFileData from a dictionary with proper nested object reconstruction.

    This is needed because dataclasses.asdict() in parallel processing converts
    nested dataclass objects (Declaration, TokenStats, SecurityIssue, DiffMetadata)
    to plain dictionaries. This function properly reconstructs them.

    Args:
        result_dict: Dictionary from dataclasses.asdict(ParsedFileData)

    Returns:
        ParsedFileData with properly reconstructed nested objects
    """
    # Reconstruct declarations
    declarations = [_reconstruct_declaration(d) for d in result_dict.get("declarations", [])]

    # Reconstruct token_stats
    token_stats = None
    if result_dict.get("token_stats"):
        ts_data = result_dict["token_stats"]
        if isinstance(ts_data, dict):
            token_stats = TokenStats(
                gpt4_tokens=ts_data["gpt4_tokens"],
                claude_tokens=ts_data["claude_tokens"],
            )
        else:
            token_stats = ts_data

    # Reconstruct security_issues
    security_issues = []
    for issue in result_dict.get("security_issues", []):
        if isinstance(issue, dict):
            # Handle severity - could be string or SecuritySeverity enum
            severity = issue["severity"]
            if isinstance(severity, str):
                normalized = severity.strip().upper()
                try:
                    severity = SecuritySeverity[normalized]
                except KeyError:
                    try:
                        severity = SecuritySeverity(int(severity))
                    except (ValueError, TypeError):
                        severity = SecuritySeverity.INFO
            security_issues.append(
                SecurityIssue(
                    rule_id=issue["rule_id"],
                    description=issue["description"],
                    file_path=issue["file_path"],
                    line_number=issue["line_number"],
                    severity=severity,
                    context=issue.get("context", ""),
                )
            )
        else:
            security_issues.append(issue)

    # Reconstruct diff_metadata
    diff_metadata = None
    if result_dict.get("diff_metadata"):
        dm_data = result_dict["diff_metadata"]
        if isinstance(dm_data, dict):
            diff_metadata = DiffMetadata(
                from_ref=dm_data["from_ref"],
                to_ref=dm_data["to_ref"],
                change_type=dm_data["change_type"],
                additions=dm_data["additions"],
                deletions=dm_data["deletions"],
                binary=dm_data["binary"],
                old_path=dm_data.get("old_path"),
                similarity=dm_data.get("similarity"),
            )
        else:
            diff_metadata = dm_data

    # Reconstruct parse_result if it's a dict from multiprocess serialization
    parse_result = result_dict.get("parse_result")
    if isinstance(parse_result, dict):
        parse_result = ParseResult(
            declarations=declarations,
            imports=parse_result.get("imports", []),
            missed_features=parse_result.get("missed_features", []),
            security_issues=parse_result.get("security_issues", []),
            error=parse_result.get("error"),
            engine_used=parse_result.get("engine_used", "regex"),
            parser_quality=parse_result.get("parser_quality", "unknown"),
            file_path=parse_result.get("file_path"),
            language=parse_result.get("language"),
            content=parse_result.get("content"),
            module_docstring=parse_result.get("module_docstring"),
            module_name=parse_result.get("module_name"),
            degraded=parse_result.get("degraded", False),
            confidence_score=parse_result.get("confidence_score"),
            parser_type=parse_result.get("parser_type"),
        )

    return ParsedFileData(
        file_path=result_dict["file_path"],
        content=result_dict.get("content"),
        language=result_dict.get("language"),
        declarations=declarations,
        imports=result_dict.get("imports", []),
        token_stats=token_stats,
        security_issues=security_issues,
        parse_result=parse_result,
        ai_summary=result_dict.get("ai_summary"),
        ai_metadata=result_dict.get("ai_metadata"),
        diff_content=result_dict.get("diff_content"),
        diff_metadata=diff_metadata,
    )


def _is_valid_language_input(language: str) -> bool:
    """Validate language input for security.

    Prevents directory traversal and code injection attacks.

    Args:
        language: Language identifier to validate

    Returns:
        True if the language is safe to use
    """
    if not language:
        return False

    # Check for suspicious patterns
    suspicious_patterns = [
        "../",
        "..\\",  # Directory traversal
        "/",
        "\\",  # Path separators
        ";",
        "|",
        "&",
        "`",
        "$",  # Command injection
        "import",
        "exec",
        "eval",
        "__",  # Python code injection
        "\x00",
        "\n",
        "\r",
        "\t",  # Special characters
    ]

    for pattern in suspicious_patterns:
        if pattern in language:
            logger.warning(f"Suspicious pattern detected in language: {language}")
            return False

    # Only allow known safe languages
    return language.lower() in ALLOWED_LANGUAGES


@functools.lru_cache(maxsize=64)
def _try_tree_sitter_parser(language: str) -> Any | None:
    """Try to load a tree-sitter parser for the language.

    PERFORMANCE: Results are cached per language to avoid repeated module imports
    and parser instantiation.

    Args:
        language: Language identifier

    Returns:
        Tree-sitter parser instance or None (cached)
    """
    try:
        # Map language to tree-sitter parser module name
        parser_map = {
            "python": "tree_sitter_python_parser",
            "javascript": "tree_sitter_js_ts_parser",
            "typescript": "tree_sitter_js_ts_parser",
            "java": "tree_sitter_java_parser",
            "cpp": "tree_sitter_cpp_parser",
            "c": "tree_sitter_cpp_parser",
            "csharp": "tree_sitter_csharp_parser",
            "go": "tree_sitter_go_parser",
            "rust": "tree_sitter_rust_parser",
            "php": "tree_sitter_php_parser",
            "swift": "tree_sitter_swift_parser",
            "r": "tree_sitter_r_parser",
            "julia": "tree_sitter_julia_parser",
            "bash": "tree_sitter_bash_parser",
            "shell": "tree_sitter_bash_parser",
            "kotlin": "tree_sitter_kotlin_parser",
            "dart": "tree_sitter_dart_parser",
            "sql": "tree_sitter_sql_parser",
            "graphql": "tree_sitter_graphql_parser",
            "ruby": "tree_sitter_ruby_parser",
            "solidity": "tree_sitter_solidity_parser",
            "glsl": "tree_sitter_glsl_parser",
            "hlsl": "tree_sitter_hlsl_parser",
            "wat": "tree_sitter_wat_parser",
            "wasm": "tree_sitter_wat_parser",
        }

        module_name = parser_map.get(language.lower())
        if not module_name:
            return None

        # Import the parser module
        module_path = f"codeconcat.parser.language_parsers.{module_name}"
        import importlib

        module = importlib.import_module(module_path)

        # Get the parser class (following naming convention)
        class_name = (
            "TreeSitter" + "".join(word.capitalize() for word in language.split("_")) + "Parser"
        )
        if language in ["javascript", "typescript"]:
            class_name = "TreeSitterJsTsParser"
        elif language == "c":
            class_name = "TreeSitterCppParser"
        elif language in ["bash", "shell"]:
            class_name = "TreeSitterBashParser"
        elif language == "kotlin":
            class_name = "TreeSitterKotlinParser"
        elif language == "dart":
            class_name = "TreeSitterDartParser"
        elif language == "sql":
            class_name = "TreeSitterSqlParser"
        elif language == "graphql":
            class_name = "TreeSitterGraphqlParser"
        elif language == "ruby":
            class_name = "TreeSitterRubyParser"
        elif language == "solidity":
            class_name = "TreeSitterSolidityParser"
        elif language == "glsl":
            class_name = "TreeSitterGlslParser"
        elif language == "hlsl":
            class_name = "TreeSitterHlslParser"

        parser_class = getattr(module, class_name, None)
        if parser_class:
            return parser_class()

    except (ImportError, AttributeError, ValueError, TypeError) as e:
        logger.debug(f"Tree-sitter parser not available for {language}: {e}")

    return None


@functools.lru_cache(maxsize=64)
def _try_enhanced_regex_parser(language: str, use_enhanced: bool = True) -> Any | None:
    """Try to load an enhanced regex parser for the language.

    PERFORMANCE: Results are cached per (language, use_enhanced) to avoid repeated
    module imports and parser instantiation.

    Args:
        language: Language identifier
        use_enhanced: Whether to use enhanced parsers

    Returns:
        Enhanced parser instance or None (cached)
    """
    if not use_enhanced:
        return None

    try:
        # Map language to enhanced parser module name
        parser_map = {
            "python": "enhanced_python_parser",
            "javascript": "enhanced_js_ts_parser",
            "typescript": "enhanced_js_ts_parser",
            "go": "enhanced_go_parser",
            "rust": "enhanced_rust_parser",
            "csharp": "enhanced_csharp_parser",
            "php": "enhanced_php_parser",
            "r": "enhanced_r_parser",
            "julia": "enhanced_julia_parser",
        }

        module_name = parser_map.get(language.lower())
        if not module_name:
            return None

        # Import the parser module
        module_path = f"codeconcat.parser.language_parsers.{module_name}"
        import importlib

        module = importlib.import_module(module_path)

        # Get the parser class
        class_name = (
            "Enhanced" + "".join(word.capitalize() for word in language.split("_")) + "Parser"
        )
        if language in ["javascript", "typescript"]:
            class_name = "EnhancedJSTypeScriptParser"

        parser_class = getattr(module, class_name, None)
        if parser_class:
            return parser_class()

    except (ImportError, AttributeError, ValueError, TypeError, KeyError) as e:
        logger.debug(f"Enhanced parser not available for {language}: {e}")

    return None


@functools.lru_cache(maxsize=64)
def _try_standard_regex_parser(language: str) -> Any | None:
    """Try to load a standard regex parser for the language.

    PERFORMANCE: Results are cached per language to avoid repeated module imports
    and parser instantiation.

    Args:
        language: Language identifier

    Returns:
        Standard parser instance or None (cached)
    """
    try:
        # Map language to standard parser module name
        parser_map = {
            "python": "python_parser",
            "javascript": "js_ts_parser",
            "typescript": "js_ts_parser",
            "java": "java_parser",
            "cpp": "cpp_parser",
            "c": "c_parser",
            "csharp": "csharp_parser",
            "go": "go_parser",
            "rust": "rust_parser",
            "php": "php_parser",
            "ruby": "ruby_parser",
            "swift": "swift_parser",
            "r": "r_parser",
            "julia": "julia_parser",
        }

        module_name = parser_map.get(language.lower())
        if not module_name:
            return None

        # Import the parser module
        module_path = f"codeconcat.parser.language_parsers.{module_name}"
        import importlib

        module = importlib.import_module(module_path)

        # Get the parser class
        class_name = "".join(word.capitalize() for word in language.split("_")) + "Parser"
        if language in ["javascript", "typescript"]:
            class_name = "JsTsParser"
        elif language == "cpp":
            class_name = "CppParser"
        elif language == "csharp":
            class_name = "CSharpParser"

        parser_class = getattr(module, class_name, None)
        if parser_class:
            return parser_class()

    except (ImportError, AttributeError, ValueError, TypeError, KeyError) as e:
        logger.debug(f"Standard parser not available for {language}: {e}")

    return None


# Module-level worker function for parallel processing (must be picklable)
def _process_file_worker(file_data_dict: dict, config_dict: dict) -> tuple[dict | None, str | None]:
    """Process a single file in a worker process.

    This function is called by ProcessPoolExecutor workers. It creates a minimal
    pipeline instance to process a single file and returns serializable results.

    SECURITY: Validates config using Pydantic's model_validate() and adds explicit
    type/sanity checks for file_data_dict to prevent injection attacks.

    Args:
        file_data_dict: Dictionary representation of ParsedFileData
        config_dict: Dictionary representation of CodeConCatConfig

    Returns:
        Tuple of (result_dict, error_message) where:
        - result_dict is a dictionary with parsed file data, or None on error
        - error_message is an error string, or None on success
    """
    import dataclasses

    try:
        # Reconstruct config from validated Pydantic model
        config = CodeConCatConfig.model_validate(config_dict)

        # Validate file_data_dict with explicit type/sanity checks
        # This prevents injection attacks through malformed input
        if not isinstance(file_data_dict, dict):
            raise ValueError("file_data_dict must be a dictionary")

        # Validate required string fields
        file_path = file_data_dict.get("file_path")
        if not isinstance(file_path, str) or not file_path:
            raise ValueError("file_path must be a non-empty string")

        # Validate optional fields have expected types
        content = file_data_dict.get("content")
        if content is not None and not isinstance(content, str):
            raise ValueError("content must be a string or None")

        language = file_data_dict.get("language")
        if language is not None and not isinstance(language, str):
            raise ValueError("language must be a string or None")

        # Reconstruct file_data using validated dict
        file_data = ParsedFileData(**file_data_dict)

        # Create a minimal pipeline instance
        pipeline = UnifiedPipeline(config)

        # Process the file
        result = pipeline._process_file(file_data)

        if result:
            # Clear unpicklable tree_sitter Node before serialization
            if result.parse_result and hasattr(result.parse_result, "ast_root"):
                result.parse_result.ast_root = None

            # Convert result to dictionary using dataclasses.asdict for recursive conversion
            if dataclasses.is_dataclass(result) and not isinstance(result, type):
                result_dict = dataclasses.asdict(result)
            elif hasattr(result, "model_dump"):
                result_dict = result.model_dump()
            else:
                result_dict = dict(result.__dict__)

            return result_dict, None
        return None, None

    except Exception as e:
        return None, f"Error processing {file_data_dict.get('file_path', 'unknown')}: {str(e)}"


class UnifiedPipeline:
    """Unified parsing pipeline with plugin-based architecture."""

    def __init__(self, config: CodeConCatConfig, progress_callback: ProgressCallback | None = None):
        """Initialize the unified pipeline with configuration.

        Args:
            config: CodeConcat configuration object
            progress_callback: Optional callback for progress updates
        """
        self.config = config
        self.unsupported_reporter = get_unsupported_reporter()
        self.progress_callback = progress_callback

    def parse(
        self, files_to_parse: list[ParsedFileData]
    ) -> tuple[list[ParsedFileData], list[ParserError]]:
        """
        Main parsing pipeline entry point with progressive fallbacks.

        This pipeline attempts parsing in the following order:
        1. Tree-sitter (if enabled)
        2. Enhanced regex parsers
        3. Standard regex parsers (fallback)

        It accumulates partial results and provides detailed error information.

        PERFORMANCE: Uses ProcessPoolExecutor for parallel parsing when there are
        4+ files. Sequential processing is used for small batches to avoid
        multiprocessing overhead.

        Args:
            files_to_parse: List of ParsedFileData objects to process

        Returns:
            Tuple of (parsed_files, errors) where:
            - parsed_files is a list of ParsedFileData with parsing results
            - errors is a list of ParserError objects for failed files
        """
        logger.info(f"Starting unified parsing pipeline for {len(files_to_parse)} files")

        # Use sequential processing for small batches (< 50 files)
        # PERFORMANCE: Increased from 4 to 50 because multiprocessing startup overhead
        # (500-1000ms per worker) plus config serialization makes parallel processing
        # slower than sequential for small-to-medium codebases
        min_parallel_files = 50
        if len(files_to_parse) < min_parallel_files:
            return self._parse_sequential(files_to_parse)

        # Use parallel processing for larger batches
        return self._parse_parallel(files_to_parse)

    def _parse_sequential(
        self, files_to_parse: list[ParsedFileData]
    ) -> tuple[list[ParsedFileData], list[ParserError]]:
        """Parse files sequentially (for small batches).

        Args:
            files_to_parse: List of ParsedFileData objects to process

        Returns:
            Tuple of (parsed_files, errors)
        """
        parsed_files_output: list[ParsedFileData] = []
        errors: list[ParserError] = []

        total_files = len(files_to_parse)

        # Use external progress callback if provided (from CLI dashboard)
        # Otherwise fall back to Rich track() for standalone usage
        if self.progress_callback:
            # Use external callback - iterate directly and update progress
            for idx, file_data in enumerate(files_to_parse):
                try:
                    result = self._process_file(file_data)
                    if result:
                        parsed_files_output.append(result)
                except Exception as e:
                    logger.error(
                        f"Unexpected error processing {file_data.file_path}: {str(e)}",
                        exc_info=True,
                    )
                    errors.append(
                        FileProcessingError(  # type: ignore[arg-type]
                            f"Unexpected error: {str(e)}\n{traceback.format_exc()}",
                            file_path=file_data.file_path,
                        )
                    )
                # Update external progress callback
                self.progress_callback(idx + 1, total_files)
        else:
            # Use Rich track() for standalone usage
            progress_iterator = self._process_with_progress(
                files_to_parse, "Parsing files", self.config.disable_progress_bar
            )

            for file_data in progress_iterator:
                try:
                    result = self._process_file(file_data)
                    if result:
                        parsed_files_output.append(result)
                except Exception as e:
                    logger.error(
                        f"Unexpected error processing {file_data.file_path}: {str(e)}",
                        exc_info=True,
                    )
                    errors.append(
                        FileProcessingError(  # type: ignore[arg-type]
                            f"Unexpected error: {str(e)}\n{traceback.format_exc()}",
                            file_path=file_data.file_path,
                        )
                    )

        logger.info(
            f"Unified parsing pipeline completed: {len(parsed_files_output)} succeeded, "
            f"{len(errors)} failed"
        )

        return parsed_files_output, errors

    def _parse_parallel(
        self, files_to_parse: list[ParsedFileData]
    ) -> tuple[list[ParsedFileData], list[ParserError]]:
        """Parse files in parallel using ProcessPoolExecutor.

        PERFORMANCE: CPU-bound parsing work benefits from multiprocessing
        which avoids Python's GIL limitations.

        Args:
            files_to_parse: List of ParsedFileData objects to process

        Returns:
            Tuple of (parsed_files, errors)
        """
        # Determine number of workers
        max_workers = (
            self.config.max_workers
            if hasattr(self.config, "max_workers")
            and self.config.max_workers
            and self.config.max_workers > 0
            else min(os.cpu_count() or 1, 8)  # Cap at 8 workers for parsing
        )
        logger.info(f"Using {max_workers} workers for parallel parsing")

        # Per-file timeout to prevent hanging on problematic files
        timeout_seconds = 60

        # Convert config to dict for serialization
        config_dict = (
            self.config.model_dump() if hasattr(self.config, "model_dump") else self.config.__dict__
        )

        # Lists to collect results
        parsed_files_output: list[ParsedFileData] = []
        errors: list[ParserError] = []

        try:
            # Submit all files to the executor
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {}
                for file_data in files_to_parse:
                    # Convert file_data to dict for serialization
                    file_data_dict = (
                        file_data.model_dump()
                        if hasattr(file_data, "model_dump")
                        else file_data.__dict__
                    )
                    future = executor.submit(_process_file_worker, file_data_dict, config_dict)
                    future_to_file[future] = file_data

                # Process results as they complete with progress tracking
                completed = 0
                total = len(future_to_file)

                # Helper function to process completed futures
                def process_future(future, file_data):
                    nonlocal completed
                    try:
                        result_dict, error_msg = future.result(timeout=timeout_seconds)

                        if error_msg:
                            logger.error(error_msg)
                            errors.append(
                                FileProcessingError(  # type: ignore[arg-type]
                                    error_msg,
                                    file_path=file_data.file_path,
                                )
                            )
                        elif result_dict:
                            # Reconstruct ParsedFileData from dict with proper nested object reconstruction
                            # This handles Declaration, TokenStats, SecurityIssue, DiffMetadata
                            parsed_file = _reconstruct_parsed_file_data(result_dict)
                            parsed_files_output.append(parsed_file)

                    except TimeoutError:
                        logger.warning(
                            f"Timeout parsing {file_data.file_path} after {timeout_seconds}s"
                        )
                        errors.append(
                            FileProcessingError(  # type: ignore[arg-type]
                                f"Parsing timeout after {timeout_seconds}s",
                                file_path=file_data.file_path,
                            )
                        )
                    except Exception as e:
                        logger.error(
                            f"Error processing {file_data.file_path} in worker: {e}",
                            exc_info=True,
                        )
                        errors.append(
                            FileProcessingError(  # type: ignore[arg-type]
                                f"Worker error: {str(e)}",
                                file_path=file_data.file_path,
                            )
                        )
                    finally:
                        completed += 1
                        # Periodic progress logging
                        if completed % 50 == 0 or completed == total:
                            logger.info(
                                f"Parsed {completed}/{total} files ({completed / total * 100:.1f}%)"
                            )

                # Use external progress callback if provided (from CLI dashboard)
                if self.progress_callback:
                    for future in as_completed(future_to_file):
                        file_data = future_to_file[future]
                        process_future(future, file_data)
                        # Update external progress callback
                        self.progress_callback(completed, total)
                else:
                    # Use Rich Progress for standalone usage
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[bold blue]Parsing files"),
                        BarColumn(),
                        TaskProgressColumn(),
                        "[progress.percentage]{task.percentage:>3.0f}%",
                        disable=self.config.disable_progress_bar,
                    ) as progress:
                        task = progress.add_task("Parsing", total=total)

                        for future in as_completed(future_to_file):
                            file_data = future_to_file[future]
                            process_future(future, file_data)
                            progress.update(task, advance=1)

        except Exception:
            # Log error and ensure cleanup
            logger.exception("Error during parallel parsing, cleaning up pending futures")
            raise

        logger.info(
            f"Unified parsing pipeline completed: {len(parsed_files_output)} succeeded, "
            f"{len(errors)} failed"
        )

        return parsed_files_output, errors

    def _process_file(self, file_data: ParsedFileData) -> ParsedFileData | None:
        """Process a single file through the parsing pipeline.

        Args:
            file_data: ParsedFileData object to process

        Returns:
            Processed ParsedFileData or None if skipped
        """
        file_path = file_data.file_path
        content = file_data.content
        language = file_data.language

        logger.debug(f"Processing file: {file_path} (Language: {language})")

        # Validate input data
        if not file_path or content is None:
            raise ParserError("Missing file path or content in input data", file_path=file_path)

        # Skip unsupported languages
        if not language or language == "unknown":
            logger.debug(f"Skipping file with unknown language: {file_path}")
            self.unsupported_reporter.add_skipped_file(
                Path(file_path),
                "Unknown or unsupported language",
                "unknown_language" if language == "unknown" else "unsupported_language",
            )
            return None

        # Apply language filters
        if not self._should_process_language(language, file_path):
            return None

        # Handle special file types (documentation, config)
        if language in ["documentation", "config"]:
            return self._handle_special_file(file_data, language)

        # Unicode normalization if enabled
        if is_enabled("enable_unicode_handler"):
            file_data.content = normalize_unicode_content(content, file_path)
            content = file_data.content

        # Try parsing with progressive fallbacks
        parse_result = self._parse_with_fallbacks(content, file_path, language)

        if parse_result:
            # Update file_data with parse results
            file_data.parse_result = parse_result
            file_data.declarations = parse_result.declarations
            file_data.imports = parse_result.imports

            # Apply post-processing steps
            self._apply_post_processing(file_data)

            return file_data

        # No parser was able to handle this file
        error_msg = f"No parser available for {file_path} (language: {language})"
        self.unsupported_reporter.add_skipped_file(
            Path(file_path),
            f"No parser available for language '{language}'",
            "unsupported_language",
        )
        raise UnsupportedLanguageError(error_msg, file_path=file_path)

    def _should_process_language(self, language: str, file_path: str) -> bool:
        """Check if the language should be processed based on configuration.

        Args:
            language: Programming language identifier
            file_path: Path to the file

        Returns:
            True if the language should be processed, False otherwise
        """
        # Check include list
        if self.config.include_languages and language not in self.config.include_languages:
            logger.debug(f"Skipping {file_path} - language '{language}' not in include list")
            self.unsupported_reporter.add_skipped_file(
                Path(file_path), f"Language '{language}' not in include list", "excluded_pattern"
            )
            return False

        # Check exclude list
        if self.config.exclude_languages and language in self.config.exclude_languages:
            logger.debug(f"Skipping {file_path} - language '{language}' in exclude list")
            self.unsupported_reporter.add_skipped_file(
                Path(file_path), f"Language '{language}' in exclude list", "excluded_pattern"
            )
            return False

        return True

    def _handle_special_file(self, file_data: ParsedFileData, language: str) -> ParsedFileData:
        """Handle special file types like documentation and configuration files.

        Args:
            file_data: ParsedFileData object
            language: Special language type ("documentation" or "config")

        Returns:
            Processed ParsedFileData
        """
        logger.debug(f"Processing {language} file: {file_data.file_path}")

        parse_result = ParseResult()
        parse_result.file_path = file_data.file_path
        parse_result.language = language

        if language == "config":
            file_basename = os.path.basename(file_data.file_path)
            parse_result.module_name = f"Configuration: {file_basename}"

        # Use the whole file content as the module_docstring
        parse_result.module_docstring = file_data.content

        file_data.parse_result = parse_result
        return file_data

    def _parse_with_fallbacks(
        self, content: str, file_path: str, language: str
    ) -> ParseResult | None:
        """Parse content with progressive fallback chain.

        Args:
            content: File content to parse
            file_path: Path to the file
            language: Programming language identifier

        Returns:
            ParseResult or None if all parsers fail
        """
        # Check if result merging is enabled (default: True for improved results)
        enable_result_merging = getattr(self.config, "enable_result_merging", True)
        merge_strategy_name = getattr(self.config, "merge_strategy", "confidence")

        # PERFORMANCE: Early termination when primary parser (tree-sitter) succeeds
        # Default: True - skip additional parsers when tree-sitter produces good results
        # Set to False to always run all parsers for maximum coverage (slower)
        early_termination = getattr(self.config, "parser_early_termination", True)

        # Minimum declarations threshold for early termination
        # If tree-sitter finds at least this many declarations, skip other parsers
        # PERFORMANCE: Increased from 1 to 5 to reduce redundant parser runs while
        # still ensuring adequate coverage for files with few declarations
        early_termination_threshold = getattr(self.config, "parser_early_termination_threshold", 5)

        # Convert strategy name to enum
        strategy_map = {
            "confidence": MergeStrategy.CONFIDENCE_WEIGHTED,
            "union": MergeStrategy.FEATURE_UNION,
            "fast_fail": MergeStrategy.FAST_FAIL,
            "best_of_breed": MergeStrategy.BEST_OF_BREED,
        }
        merge_strategy = strategy_map.get(merge_strategy_name, MergeStrategy.CONFIDENCE_WEIGHTED)

        # Define the fallback chain
        fallback_chain = []

        if not self.config.disable_tree:
            fallback_chain.append(("tree_sitter", "Tree-sitter"))

        # Check if enhanced parsers are explicitly enabled or use as default
        use_enhanced = getattr(self.config, "use_enhanced_parsers", True)
        if use_enhanced:
            fallback_chain.append(("enhanced", "Enhanced regex"))

        fallback_chain.append(("standard", "Standard regex"))

        # Collect results from all parsers if merging is enabled
        all_results: list[ParseResult] = []

        # Try each parser in the fallback chain
        for parser_type, parser_name in fallback_chain:
            logger.debug(f"Attempting {parser_name} parser for {file_path}")

            try:
                parser = get_language_parser(language, self.config, parser_type=parser_type)
                if not parser:
                    continue

                # Validate enhanced parsers if they implement the interface
                if isinstance(parser, EnhancedParserInterface):
                    if not parser.validate():
                        logger.warning(f"{parser_name} parser for {language} failed validation")
                        continue

                    capabilities = parser.get_capabilities()
                    logger.debug(f"{parser_name} parser capabilities: {capabilities}")

                # Try parsing
                if is_enabled("enable_error_recovery") and hasattr(parser, "parse_simple"):
                    parse_result = self._parse_with_error_recovery(
                        parser, content, file_path, language
                    )
                else:
                    parse_result = parser.parse(content, file_path)

                if parse_result:
                    # Set parser metadata for merging
                    if not parse_result.parser_type:
                        parse_result.parser_type = parser_type
                    if not parse_result.engine_used:
                        parse_result.engine_used = parser_name

                    num_declarations = len(parse_result.declarations)
                    has_useful_content = num_declarations > 0 or len(parse_result.imports) > 0

                    if not parse_result.error:
                        # Successful parse (no errors)
                        logger.debug(
                            f"{parser_name} parsing successful for {file_path}: "
                            f"{num_declarations} declarations"
                        )

                        if enable_result_merging:
                            # Collect result for merging
                            all_results.append(parse_result)

                            # PERFORMANCE: Early termination for tree-sitter with good results
                            # Skip remaining parsers if tree-sitter produced sufficient declarations
                            # NOTE: Only early-terminate on CLEAN parses (no errors)
                            if (
                                early_termination
                                and parser_type == "tree_sitter"
                                and num_declarations >= early_termination_threshold
                            ):
                                logger.debug(
                                    f"Early termination: tree-sitter found {num_declarations} "
                                    f"declarations (threshold: {early_termination_threshold}), "
                                    f"skipping remaining parsers for {file_path}"
                                )
                                break  # Exit the parser loop early
                        else:
                            # Legacy behavior: return first successful result
                            return parse_result

                    elif has_useful_content and enable_result_merging:
                        # Partial parse with errors but some useful content extracted
                        # Include for merging but do NOT early-terminate - always run
                        # fallback parsers to potentially capture what tree-sitter missed
                        # (e.g., modern Swift syntax like nonisolated(unsafe))
                        logger.debug(
                            f"{parser_name} partial parse for {file_path}: "
                            f"{num_declarations} declarations extracted despite errors, "
                            f"continuing to fallback parsers for merging"
                        )
                        all_results.append(parse_result)
                        # Continue to next parser (no early termination for partial results)

            except Exception as e:
                logger.warning(
                    f"{parser_name} parsing failed for {file_path}: {str(e)}", exc_info=True
                )
                continue

        # Merge results if we collected any
        if all_results:
            if len(all_results) == 1:
                return all_results[0]

            logger.info(
                f"Merging {len(all_results)} parse results for {file_path} "
                f"using {merge_strategy.value} strategy"
            )
            merged_result = ResultMerger.merge_parse_results(
                all_results, strategy=merge_strategy, language=language
            )
            return merged_result

        return None

    def _parse_with_error_recovery(
        self, parser_instance: Any, content: str, file_path: str, language: str
    ) -> ParseResult:
        """Parse with error recovery using simplified parsing fallback.

        Args:
            parser_instance: Parser instance
            content: Content to parse
            file_path: Path to the file
            language: Programming language identifier

        Returns:
            ParseResult with possible degraded mode
        """
        # Try primary parser
        try:
            parse_result = parser_instance.parse(content, file_path)
            if parse_result and not parse_result.error:
                return parse_result  # type: ignore[no-any-return]
        except Exception as e:
            logger.warning(f"Primary parser failed for {file_path}: {e}")

        # Try simplified parsing if available
        if hasattr(parser_instance, "parse_simple"):
            try:
                logger.debug(f"Attempting simplified parsing for {file_path}")
                parse_result = parser_instance.parse_simple(content, file_path)
                if parse_result:
                    parse_result.degraded = True
                    return parse_result  # type: ignore[no-any-return]
            except Exception as e:
                logger.warning(f"Simplified parser failed for {file_path}: {e}")

        # Fallback to plain text
        logger.warning(f"All parsers failed for {file_path}, using plain text fallback")
        parse_result = ParseResult()
        parse_result.file_path = file_path
        parse_result.language = language
        parse_result.module_docstring = content
        parse_result.error = "Parser failed, treating as plain text"
        parse_result.degraded = True

        return parse_result

    def _apply_post_processing(self, file_data: ParsedFileData) -> None:
        """Apply post-processing steps like security scanning and token counting.

        Args:
            file_data: ParsedFileData object to post-process
        """
        # Security scanning
        if self.config.enable_security_scanning:
            self._apply_security_scanning(file_data)

        # Token counting
        try:
            if file_data.content:
                file_data.token_stats = get_token_stats(file_data.content)
        except Exception as e:
            logger.warning(f"Could not calculate token stats for {file_data.file_path}: {e}")

    def _apply_security_scanning(self, file_data: ParsedFileData) -> None:
        """Apply security scanning to the file data.

        Args:
            file_data: ParsedFileData object to scan
        """
        logger.debug(f"Starting security scan for {file_data.file_path}")

        try:
            # Reset security issues before scan
            file_data.security_issues = []

            # Call scan_content with mask_output_content flag
            issues, masked_content = SecurityProcessor.scan_content(
                content=file_data.content or "",
                file_path=file_data.file_path,
                config=self.config,
                mask_output_content=self.config.mask_output_content,
            )

            file_data.security_issues = issues
            logger.debug(f"Security scan for {file_data.file_path} found {len(issues)} issues.")

            # Update content if masking was performed
            if masked_content is not None:
                logger.debug(f"Updating content for {file_data.file_path} with masked version.")
                file_data.content = masked_content
            elif self.config.mask_output_content:
                logger.debug(f"Masking enabled for {file_data.file_path}, but no secrets found.")

        except Exception as e:
            logger.warning(f"Security scan failed for {file_data.file_path}: {e}", exc_info=True)

    @staticmethod
    def _process_with_progress(
        items: list[Any], description: str = "Processing", disable_progress: bool = False
    ) -> Any:
        """Wrap a list with Rich progress reporting.

        Args:
            items: The list of items to process
            description: Description for the progress bar
            disable_progress: Whether to disable the progress bar

        Returns:
            A Rich track iterator for the input items
        """
        return track(items, description=description, disable=disable_progress, total=len(items))


# Import parser helper functions from file_parser to maintain compatibility
def get_language_parser(
    language: str, config: CodeConCatConfig, parser_type: str | None = None
) -> Any | None:
    """Get the appropriate parser instance based on language and type.

    This function provides backward compatibility for code that directly
    calls get_language_parser.

    Args:
        language: The language identifier
        config: Configuration object
        parser_type: Optional parser type ("tree_sitter", "enhanced", "standard")

    Returns:
        Parser instance or None
    """
    # Validate language input for security
    if not _is_valid_language_input(language):
        logger.warning(f"Invalid language input rejected: {language}")
        return None

    # Map old parser types to current implementations
    if parser_type == "tree_sitter":
        parser = _try_tree_sitter_parser(language)
    elif parser_type == "enhanced":
        parser = _try_enhanced_regex_parser(language, config.use_enhanced_parsers)
    elif parser_type == "standard":
        parser = _try_standard_regex_parser(language)
    else:
        # Try progressive fallback
        parser = _try_tree_sitter_parser(language)
        if not parser:
            parser = _try_enhanced_regex_parser(language, config.use_enhanced_parsers)
        if not parser:
            parser = _try_standard_regex_parser(language)

    return parser


@functools.lru_cache(maxsize=1024)  # Bounded cache to prevent memory leaks
def determine_language(file_path: str) -> str | None:
    """
    Determine the programming language of a file based on its extension.
    This function is cached to improve performance.

    Args:
        file_path: Path to the file

    Returns:
        Language identifier or None if unknown

    Complexity: O(1) - Dictionary lookups with LRU cache

    Flow:
        Called by: Collectors when processing files
        Calls: Extension mapping dictionaries

    Language Detection Priority:
        1. R-specific files (returns None to skip)
        2. Documentation files (.md, .rst)
        3. Configuration files (.yml, .toml, .ini)
        4. Standard programming languages by extension

    Features:
        - LRU cache for performance (bounded to 1024 entries)
        - Case-insensitive extension matching
        - Special handling for R package files
        - Groups config and docs into special categories

    Supported Languages:
        python, javascript, typescript, r, julia, rust, cpp, c,
        csharp, java, go, php, and special categories (documentation, config)
    """
    basename = os.path.basename(file_path)
    ext = os.path.splitext(file_path)[1].lower()

    r_specific_files = {
        "DESCRIPTION",  # R package description
        "NAMESPACE",  # R package namespace
        ".Rproj",  # RStudio project file
        "configure",  # R package configuration
        "configure.win",  # R package Windows configuration
    }
    if basename in r_specific_files:
        return None

    # Documentation file types are handled specially with a "documentation" language identifier
    documentation_extensions = {
        ".md": "documentation",  # Markdown
        ".rst": "documentation",  # reStructuredText
    }
    if ext in documentation_extensions:
        logger.debug(f"Identified {file_path} as documentation file")
        return documentation_extensions[ext]

    # Configuration file types are handled specially with a "config" language identifier
    config_extensions = {
        ".yml": "config",  # YAML
        ".yaml": "config",  # YAML
        ".toml": "config",  # TOML
        ".ini": "config",  # INI
        ".cfg": "config",  # Config
        ".conf": "config",  # Config
    }
    if ext in config_extensions:
        logger.debug(f"Identified {file_path} as configuration file")
        return config_extensions[ext]

    language_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".r": "r",
        ".jl": "julia",
        ".rs": "rust",
        ".cpp": "cpp",
        ".cxx": "cpp",
        ".cc": "cpp",
        ".hpp": "cpp",
        ".hxx": "cpp",
        ".h": "c",
        ".c": "c",
        ".cs": "csharp",
        ".java": "java",
        ".go": "go",
        ".php": "php",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
        ".ksh": "bash",
        ".fish": "bash",
        ".kt": "kotlin",
        ".kts": "kotlin",
        ".dart": "dart",
        ".sql": "sql",
        ".psql": "sql",
        ".mysql": "sql",
        ".sqlite": "sql",
    }
    return language_map.get(ext)


def normalize_unicode_content(content: str, file_path: str) -> str:
    """
    Normalize unicode content for consistent parsing across different encodings.

    This function performs comprehensive unicode normalization to prevent parsing
    errors due to encoding issues. It handles:
    - BOM (Byte Order Mark) removal for UTF-8/UTF-16/UTF-32
    - Line ending normalization (CRLF -> LF)
    - Zero-width character removal (U+200B, U+200C, U+200D, U+2060, U+FEFF)
    - Unicode normalization to NFC form for consistent representation
    - Non-breaking space replacement with regular spaces

    Args:
        content: The content to normalize
        file_path: Path to the file (for logging purposes)

    Returns:
        Normalized content string safe for parsing

    Complexity:
        O(n) where n is the length of the content string

    Flow:
        Called by: parse_code_files() when processing each file
        Calls: unicodedata.normalize()

    Note:
        Returns original content on error to ensure parsing can continue
    """
    try:
        # Remove BOM if present
        if content.startswith("\ufeff"):
            content = content[1:]
            logger.debug(f"Removed BOM from {file_path}")

        # Normalize line endings to Unix style
        content = content.replace("\r\n", "\n").replace("\r", "\n")

        # Handle zero-width characters
        zero_width_chars = ["\u200b", "\u200c", "\u200d", "\u2060", "\ufeff"]
        for char in zero_width_chars:
            if char in content:
                content = content.replace(char, "")
                logger.debug(f"Removed zero-width characters from {file_path}")

        # Normalize unicode to NFC form
        content = unicodedata.normalize("NFC", content)

        # Replace non-breaking spaces with regular spaces
        content = content.replace("\xa0", " ")

        return content

    except Exception as e:
        logger.warning(f"Unicode normalization failed for {file_path}: {e}")
        return content


# Main entry point function for backward compatibility
def parse_code_files(
    files_to_parse: list[ParsedFileData],
    config: CodeConCatConfig,
    progress_callback: ProgressCallback | None = None,
) -> tuple[list[ParsedFileData], list[ParserError]]:
    """
    Parse multiple code files using the unified pipeline.

    This is the main entry point that replaces both parse_code_files() from
    file_parser.py and enhanced_parse_pipeline() from enhanced_pipeline.py.

    Args:
        files_to_parse: List of ParsedFileData objects to process
        config: Configuration object
        progress_callback: Optional callback for progress updates (current, total)

    Returns:
        Tuple of (parsed_files, errors)
    """
    pipeline = UnifiedPipeline(config, progress_callback=progress_callback)
    return pipeline.parse(files_to_parse)


# Alias for enhanced_parse_pipeline for backward compatibility
enhanced_parse_pipeline = parse_code_files
