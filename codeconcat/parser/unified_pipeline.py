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
from pathlib import Path
from typing import Any, List, Optional, Tuple

from rich.progress import track

from ..base_types import CodeConCatConfig, EnhancedParserInterface, ParsedFileData, ParseResult
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
}


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


def _try_tree_sitter_parser(language: str) -> Optional[Any]:
    """Try to load a tree-sitter parser for the language.

    Args:
        language: Language identifier

    Returns:
        Tree-sitter parser instance or None
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

        parser_class = getattr(module, class_name, None)
        if parser_class:
            return parser_class()

    except (ImportError, AttributeError, ValueError, TypeError) as e:
        logger.debug(f"Tree-sitter parser not available for {language}: {e}")

    return None


def _try_enhanced_regex_parser(language: str, use_enhanced: bool = True) -> Optional[Any]:
    """Try to load an enhanced regex parser for the language.

    Args:
        language: Language identifier
        use_enhanced: Whether to use enhanced parsers

    Returns:
        Enhanced parser instance or None
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


def _try_standard_regex_parser(language: str) -> Optional[Any]:
    """Try to load a standard regex parser for the language.

    Args:
        language: Language identifier

    Returns:
        Standard parser instance or None
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


class UnifiedPipeline:
    """Unified parsing pipeline with plugin-based architecture."""

    def __init__(self, config: CodeConCatConfig):
        """Initialize the unified pipeline with configuration.

        Args:
            config: CodeConcat configuration object
        """
        self.config = config
        self.unsupported_reporter = get_unsupported_reporter()

    def parse(
        self, files_to_parse: List[ParsedFileData]
    ) -> Tuple[List[ParsedFileData], List[ParserError]]:
        """
        Main parsing pipeline entry point with progressive fallbacks.

        This pipeline attempts parsing in the following order:
        1. Tree-sitter (if enabled)
        2. Enhanced regex parsers
        3. Standard regex parsers (fallback)

        It accumulates partial results and provides detailed error information.

        Args:
            files_to_parse: List of ParsedFileData objects to process

        Returns:
            Tuple of (parsed_files, errors) where:
            - parsed_files is a list of ParsedFileData with parsing results
            - errors is a list of ParserError objects for failed files
        """
        logger.info(f"Starting unified parsing pipeline for {len(files_to_parse)} files")

        parsed_files_output: List[ParsedFileData] = []
        errors: List[ParserError] = []

        # Use progress tracking if enabled
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

    def _process_file(self, file_data: ParsedFileData) -> Optional[ParsedFileData]:
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
    ) -> Optional[ParseResult]:
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
        all_results: List[ParseResult] = []

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

                    if not parse_result.error:
                        logger.debug(
                            f"{parser_name} parsing successful for {file_path}: "
                            f"{len(parse_result.declarations)} declarations"
                        )

                        if enable_result_merging:
                            # Collect result for merging
                            all_results.append(parse_result)
                        else:
                            # Legacy behavior: return first successful result
                            return parse_result

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
        items: List[Any], description: str = "Processing", disable_progress: bool = False
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
    language: str, config: CodeConCatConfig, parser_type: Optional[str] = None
) -> Optional[Any]:
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


@functools.lru_cache(maxsize=None)
def determine_language(file_path: str) -> Optional[str]:
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
        - LRU cache for performance (unlimited size)
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
    files_to_parse: List[ParsedFileData], config: CodeConCatConfig
) -> Tuple[List[ParsedFileData], List[ParserError]]:
    """
    Parse multiple code files using the unified pipeline.

    This is the main entry point that replaces both parse_code_files() from
    file_parser.py and enhanced_parse_pipeline() from enhanced_pipeline.py.

    Args:
        files_to_parse: List of ParsedFileData objects to process
        config: Configuration object

    Returns:
        Tuple of (parsed_files, errors)
    """
    pipeline = UnifiedPipeline(config)
    return pipeline.parse(files_to_parse)


# Alias for enhanced_parse_pipeline for backward compatibility
enhanced_parse_pipeline = parse_code_files
