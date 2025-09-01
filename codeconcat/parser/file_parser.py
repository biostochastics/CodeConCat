import functools
import logging
import os
import unicodedata
from typing import List, Optional, Set, Tuple

from tqdm import tqdm

from ..base_types import CodeConCatConfig, ParsedFileData, ParserInterface
from ..errors import ParserError, UnsupportedLanguageError
from ..processor.security_processor import SecurityProcessor
from ..processor.token_counter import get_token_stats
from ..utils.feature_flags import is_enabled

# Setup logger
logger = logging.getLogger(__name__)

# +++ Log after imports +++
logger.debug("file_parser.py module loaded successfully (parsers will be imported lazily).")


def parse_code_files(
    files_to_parse: List[ParsedFileData], config: CodeConCatConfig
) -> Tuple[List[ParsedFileData], List[ParserError]]:
    """
    Parses multiple code files using pre-read content, collecting results and errors.

    Handles language determination, parsing, and optional processing steps based on
    the provided file data and configuration. Includes unicode normalization,
    error recovery with fallback chains, and security scanning integration.

    Args:
        files_to_parse: A list of ParsedFileData objects, each containing the
                        file path, pre-read content, and determined language.
        config: The CodeConCatConfig object containing global settings like
                progress bar visibility, language includes/excludes, etc.

    Returns:
        A tuple containing:
        - A list of ParsedFileData objects that were successfully parsed,
          updated with the ParseResult (declarations and errors).
        - A list of ParserError objects encountered during processing for
          files that couldn't be parsed (e.g., missing content, unknown language).

    Complexity:
        O(n*m) where n is number of files and m is average file size

    Flow:
        Called by: main.py during processing pipeline
        Calls: normalize_unicode_content(), get_language_parser(),
               parse_with_error_recovery(), SecurityProcessor.scan_content()

    Features:
        - Unicode normalization (BOM removal, NFC normalization)
        - Error recovery with parser fallback chain
        - Security scanning when enabled
        - Token counting for AI context sizing
    """
    # +++ Log at function start +++
    logger.debug(f"Entering parse_code_files with {len(files_to_parse)} files.")

    parsed_files_output: List[ParsedFileData] = []
    errors: List[ParserError] = []

    progress_iterator = tqdm(
        files_to_parse,
        desc="Parsing files",
        unit="file",
        total=len(files_to_parse),
        disable=config.disable_progress_bar,  # Use config flag
    )

    for file_data in progress_iterator:
        file_path = file_data.file_path
        content = file_data.content
        language = file_data.language  # Use language determined by collector

        # +++ Add entry log +++
        logger.debug(
            f"[parse_code_files] Processing file in loop: {file_path} (Language: {language})"
        )

        try:
            # Basic validation - skip if essential data is missing
            if not file_path or content is None:
                errors.append(
                    ParserError(
                        "Missing file path or content in input data",
                        file_path=file_path,
                    )
                )
                continue

            # Language validation (already determined by collector, but re-check)
            if not language or language == "unknown":
                ext = os.path.splitext(file_path)[1].lower()
                # Check if it's an extension we *should* know but don't have a parser for
                if ext and ext in get_all_known_extensions():
                    errors.append(
                        UnsupportedLanguageError(
                            f"No parser available for known extension '{ext}' of '{file_path}' (lang: {language})",
                            file_path=file_path,
                        )
                    )
                else:
                    # If language is unknown and not a known code extension, likely not a code file
                    logger.debug(
                        f"[parse_code_files] Skipping file {file_path} with unknown/unsupported language: {language}"
                    )
                continue  # Skip this file

            # Check include/exclude languages from config (redundant if collector already did this, but safe)
            if config.include_languages and language not in config.include_languages:
                logger.debug(
                    f"[parse_code_files] Skipping {file_path} (lang: {language}) due to include_languages config"
                )
                continue

            # Special handling for documentation files (Markdown, RST, etc.)
            if language == "documentation":
                logger.debug(f"[parse_code_files] Processing documentation file: {file_path}")

                # For documentation files, we don't need to parse them - just use the content directly
                # Create a minimal ParseResult with the whole file as documentation
                from ..base_types import ParseResult

                parse_result = ParseResult()
                parse_result.file_path = file_path
                parse_result.language = "documentation"

                # Use the whole file content as the module_docstring
                parse_result.module_docstring = content

                # Update the file_data with the parse result
                file_data.parse_result = parse_result
                parsed_files_output.append(file_data)
                continue

            # Special handling for configuration files (YAML, TOML, INI, etc.)
            if language == "config":
                logger.debug(f"[parse_code_files] Processing configuration file: {file_path}")

                # For config files, we don't need to parse them - just use the content directly
                # Create a minimal ParseResult with the whole file as configuration
                from ..base_types import ParseResult

                parse_result = ParseResult()
                parse_result.file_path = file_path
                parse_result.language = "config"

                # Add the file title to the module name
                file_basename = os.path.basename(file_path)
                parse_result.module_name = f"Configuration: {file_basename}"

                # Use the whole file content as the module_docstring
                parse_result.module_docstring = content

                # Update the file_data with the parse result
                file_data.parse_result = parse_result
                parsed_files_output.append(file_data)
                continue
            if config.exclude_languages and language in config.exclude_languages:
                logger.debug(
                    f"[parse_code_files] Skipping {file_path} (lang: {language}) due to exclude_languages config"
                )
                continue

            # Unicode normalization before parsing
            if is_enabled("enable_unicode_handler"):
                content = normalize_unicode_content(content, file_path)

            # +++ Add log before getting parser +++
            logger.debug(
                f"[parse_code_files] Attempting to get parser for language: {language} for file {file_path}"
            )
            # Pass config to get_language_parser
            parser_instance = get_language_parser(language, config)
            # +++ Add log after getting parser +++
            if parser_instance:
                logger.debug(
                    f"[parse_code_files] Successfully got parser: {type(parser_instance).__name__} for file {file_path}"
                )
                # Add check right before calling parse
                if hasattr(parser_instance, "parser"):
                    logger.debug(
                        f"[parse_code_files Pre-Parse Check] Parser for {file_path}. parser.parser is None? {parser_instance.parser is None}"
                    )
                else:
                    logger.debug(
                        f"[parse_code_files Pre-Parse Check] Parser for {file_path} has no 'parser' attribute."
                    )
            else:
                logger.warning(
                    f"[parse_code_files] No parser instance returned for language '{language}', skipping file {file_path}"
                )
                # Raise error if no parser found and language was detected
                raise UnsupportedLanguageError(
                    f"No parser implementation available for language: {language}",
                    file_path=file_path,
                    language=language,
                )

            # +++ Log before calling parser +++
            logger.debug(
                f"[parse_code_files] Attempting to call parser: {type(parser_instance).__name__} for {file_path}"
            )
            # --- Call the parser with error recovery if enabled --- #
            logger.debug(
                f"[parse_code_files] Calling {type(parser_instance).__name__}.parse() for {file_path}"
            )

            if is_enabled("enable_error_recovery"):
                parse_result = parse_with_error_recovery(
                    parser_instance, content, file_path, language
                )
            else:
                parse_result = parser_instance.parse(content, file_path)

            logger.debug(
                f"[parse_code_files] Finished parsing {file_path}. Engine: {parse_result.engine_used}, Error: {parse_result.error}"
            )

            # --- Update file_data with parse results --- #
            file_data.parse_result = parse_result
            file_data.declarations = parse_result.declarations
            file_data.imports = parse_result.imports

            if parse_result.error:
                # Log the parsing error but continue processing (security/tokens)
                logger.warning(
                    f"[parse_code_files] Parser returned error for {file_path}: {parse_result.error}"
                )
                errors.append(ParserError(parse_result.error, file_path=file_path))

            # Reset security issues before potential scan
            file_data.security_issues = []

            # --- Perform Security Scan (if enabled) --- #
            if config.enable_security_scanning:
                logger.debug(f"[parse_code_files] Starting security scan for {file_path}")
                try:
                    # Call scan_content, passing the mask_output_content flag
                    issues, masked_content = SecurityProcessor.scan_content(
                        content=file_data.content,  # Use current content
                        file_path=file_path,
                        config=config,
                        mask_output_content=config.mask_output_content,
                    )
                    file_data.security_issues = issues
                    logger.debug(
                        f"[parse_code_files] Security scan for {file_path} found {len(issues)} issues."
                    )

                    # Update content if masking was performed and successful
                    if masked_content is not None:
                        logger.debug(
                            f"[parse_code_files] Updating content for {file_path} with masked version."
                        )
                        file_data.content = masked_content
                    elif config.mask_output_content:
                        # Log if masking was requested but no masked content was returned (e.g., no secrets found)
                        logger.debug(
                            f"[parse_code_files] Masking enabled for {file_path}, but no secrets found or masked."
                        )

                except (OSError, ValueError, TypeError, AttributeError) as security_exc:
                    logger.warning(
                        f"[parse_code_files] Security scan failed for {file_path}: {security_exc}",
                        exc_info=True,  # Include traceback in log
                    )
                    # Keep original content if scanning/masking failed
                    errors.append(
                        ParserError(f"Security scan failed: {security_exc}", file_path=file_path)
                    )
            # ---------------------------------------------- #

            # --- Calculate Token Stats (after potential masking) --- #
            try:
                if file_data.content:
                    file_data.token_stats = get_token_stats(file_data.content)
            except (ValueError, KeyError, AttributeError) as token_exc:
                logger.warning(
                    f"[parse_code_files] Could not calculate token stats for {file_path}: {token_exc}"
                )
            # ------------------------------------------------------ #

            # Add the successfully processed file_data to the output list
            parsed_files_output.append(file_data)

            # +++ Add log indicating successful processing for this file +++
            logger.debug(
                f"[parse_code_files] Successfully processed and added {file_path} to output."
            )

        except UnsupportedLanguageError as lang_err:
            # Log specifically for unsupported languages, might not be a fatal error
            logger.warning(f"[parse_code_files] {lang_err}")
            errors.append(lang_err)  # Append to errors list
        except (OSError, ValueError, TypeError, AttributeError) as e:
            # Catch other potential errors during parsing loop iteration
            # +++ Add log for general exception +++
            logger.error(
                f"[parse_code_files] Unhandled exception processing {file_path}: {e}",
                exc_info=True,  # Include traceback
            )
            errors.append(ParserError(str(e), file_path=file_path))

    # +++ Log at function end +++
    logger.debug(
        f"Exiting parse_code_files. Successfully parsed: {len(parsed_files_output)}, Errors: {len(errors)}"
    )
    return parsed_files_output, errors


def get_all_known_extensions() -> Set[str]:
    """Returns a set of all file extensions CodeConCat knows how to potentially parse.

    This is based on the keys in the language_map used internally and helps
    distinguish between files that are skipped because they are unknown vs.
    files skipped because a parser isn't implemented yet for a known type.

    Returns:
        A set of lowercase file extensions (including the leading dot) for
        which a parser is theoretically available (though might not be implemented).
    """
    return {
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".r",
        ".jl",
        ".rs",
        ".cpp",
        ".cxx",
        ".cc",
        ".hpp",
        ".hxx",
        ".h",
        ".c",
        ".cs",
        ".java",
        ".go",
        ".php",
    }


def get_language_parser(
    language: str, config: CodeConCatConfig, parser_type: Optional[str] = None
) -> Optional[ParserInterface]:
    """
    Get the appropriate parser instance based on language, config, and explicit parser type.

    Attempts to dynamically import the parser module for the requested language,
    instantiate the parser class, and return the instance.

    Args:
        language: The language identifier (e.g., "python", "javascript").
        config: The CodeConCatConfig object.
        parser_type: Optional explicit parser type to use: "tree_sitter", "enhanced", or "standard".
                     If None, will try in order based on config settings.

    Returns:
        An instance implementing the ParserInterface if found and successfully imported,
        otherwise None.
    """
    # Import parser maps from language_parsers module

    normalized_language = language.lower()
    logger.debug(
        f"[get_language_parser] Requesting parser for: {normalized_language}, type: {parser_type or 'auto'}"
    )

    parser_instance: Optional[ParserInterface] = None
    attempted_tree_sitter = False
    use_enhanced = False

    # Check if we should use enhanced parsers
    if hasattr(config, "use_enhanced_parsers") and config.use_enhanced_parsers:
        use_enhanced = True
        logger.debug(f"Using enhanced parsers where available for {normalized_language}")

    # If explicit parser_type is specified, only try that type
    if parser_type == "tree_sitter":
        return _try_tree_sitter_parser(normalized_language)
    elif parser_type == "enhanced":
        return _try_enhanced_regex_parser(normalized_language, use_enhanced=True)
    elif parser_type == "standard":
        return _try_standard_regex_parser(normalized_language)

    # --- Try Tree-sitter first if requested --- #
    if not config.disable_tree:
        attempted_tree_sitter = True
        try:
            parser_instance = _try_tree_sitter_parser(normalized_language)
            if parser_instance:
                return parser_instance
        except (ImportError, AttributeError, TypeError, ValueError) as e:
            logger.error(f"Error trying Tree-sitter parser for {language}: {e}", exc_info=True)

    # --- Try Enhanced Regex if available --- #
    if use_enhanced:
        try:
            logger.debug(f"Falling back to Enhanced Regex parser for {normalized_language}")
            parser_instance = _try_enhanced_regex_parser(normalized_language, use_enhanced=True)
            if parser_instance:
                return parser_instance
        except (ImportError, AttributeError, TypeError, ValueError) as e:
            logger.error(f"Error trying Enhanced Regex parser for {language}: {e}", exc_info=True)

    # --- Try Standard Regex parser as final fallback --- #
    try:
        logger.debug(f"Falling back to Standard Regex parser for {normalized_language}")
        parser_instance = _try_standard_regex_parser(normalized_language)
        if parser_instance:
            return parser_instance
    except (ImportError, AttributeError, TypeError, ValueError) as e:
        logger.error(f"Error trying Standard Regex parser for {language}: {e}", exc_info=True)

    # Should not be reached if logic is correct, but acts as a final fallback
    if attempted_tree_sitter:
        logger.error(
            f"Failed to load Tree-sitter parser for {language} and fallback to regex failed or was disabled."
        )
    else:
        logger.error(f"Failed to load Regex parser for {language}.")
    return None


def _try_tree_sitter_parser(language: str) -> Optional[ParserInterface]:
    """
    Try to load a Tree-sitter parser for the given language.

    Args:
        language: The normalized language identifier.

    Returns:
        A parser instance if successful, None otherwise.
    """
    import importlib

    from codeconcat.parser.language_parsers import TREE_SITTER_PARSER_MAP

    logger.debug(f"Attempting to load Tree-sitter parser for {language}")
    parser_class_name = TREE_SITTER_PARSER_MAP.get(language)

    if not parser_class_name:
        logger.debug(f"No Tree-sitter parser defined for {language}")
        return None

    try:
        module_name = f"codeconcat.parser.language_parsers.tree_sitter_{language}_parser"

        # Special cases for JS/TS and C/C++
        if language in ["javascript", "typescript"]:
            module_name = "codeconcat.parser.language_parsers.tree_sitter_js_ts_parser"
        elif language in ["c", "cpp"]:
            module_name = "codeconcat.parser.language_parsers.tree_sitter_cpp_parser"

        module = importlib.import_module(module_name)
        parser_class = getattr(module, parser_class_name)
        parser_instance: ParserInterface = parser_class()
        logger.debug(f"Successfully loaded Tree-sitter parser for {language}")
        return parser_instance
    except (ImportError, AttributeError) as e:
        logger.warning(f"Could not load Tree-sitter parser for {language}: {e}")
        return None
    except (TypeError, ValueError, RuntimeError, MemoryError) as e:
        logger.error(f"Error initializing Tree-sitter parser for {language}: {e}", exc_info=True)
        return None


def _try_enhanced_regex_parser(
    language: str, use_enhanced: bool = True
) -> Optional[ParserInterface]:
    """
    Try to load an enhanced regex parser for the given language.

    Enhanced parsers use sophisticated regex patterns tailored to each
    language's specific syntax, providing better accuracy than generic
    regex parsers while being lighter than tree-sitter parsers.

    Args:
        language: The normalized language identifier.
        use_enhanced: Whether to try enhanced parsers (default True).

    Returns:
        A parser instance if successful, None otherwise.

    Complexity: O(1) - Module import and instantiation

    Flow:
        Called by: get_language_parser() as secondary parser option
        Calls: Language-specific enhanced parser classes via importlib

    Supported Languages:
        Via REGEX_PARSER_MAP with '_enhanced' suffix:
        python, javascript, typescript, and others

    Error Handling:
        - ImportError: Parser module not available (returns None)
        - AttributeError: Parser class missing (returns None)
        - TypeError/ValueError: Invalid parser state (returns None)
        - RuntimeError/MemoryError: Parser initialization failures (returns None)
        - All errors logged with context for debugging
    """
    import importlib

    from codeconcat.parser.language_parsers import REGEX_PARSER_MAP

    if not use_enhanced:
        logger.debug(f"Enhanced parsers disabled, skipping for {language}")
        return None

    logger.debug(f"Attempting to load Enhanced Regex parser for {language}")
    enhanced_name = f"{language}_enhanced"
    parser_class_name = REGEX_PARSER_MAP.get(enhanced_name)

    if not parser_class_name:
        logger.debug(f"No Enhanced Regex parser defined for {language}")
        return None

    try:
        module_name = f"codeconcat.parser.language_parsers.enhanced_{language}_parser"

        # Special case for JavaScript/TypeScript
        if language in ["javascript", "typescript"]:
            module_name = "codeconcat.parser.language_parsers.enhanced_js_ts_parser"

        module = importlib.import_module(module_name)
        parser_class = getattr(module, parser_class_name)
        parser_instance: ParserInterface = parser_class()
        logger.debug(f"Successfully loaded Enhanced Regex parser for {language}")
        return parser_instance
    except (ImportError, AttributeError) as e:
        logger.warning(f"Could not load Enhanced Regex parser for {language}: {e}")
        return None
    except (TypeError, ValueError, RuntimeError, MemoryError) as e:
        logger.error(f"Error initializing Enhanced Regex parser for {language}: {e}", exc_info=True)
        return None


def _try_standard_regex_parser(language: str) -> Optional[ParserInterface]:
    """
    Try to load a standard regex parser for the given language.

    Args:
        language: The normalized language identifier.

    Returns:
        A parser instance if successful, None otherwise.
    """
    import importlib

    from codeconcat.parser.language_parsers import REGEX_PARSER_MAP

    logger.debug(f"Attempting to load Standard Regex parser for {language}")
    parser_class_name = REGEX_PARSER_MAP.get(language)

    if not parser_class_name:
        logger.debug(f"No Standard Regex parser defined for {language}")
        return None

    try:
        module_name = f"codeconcat.parser.language_parsers.{language}_parser"

        # Special cases for JS/TS and C/C++
        if language in ["javascript", "typescript"]:
            module_name = "codeconcat.parser.language_parsers.js_ts_parser"
        elif language in ["c", "cpp"]:
            module_name = "codeconcat.parser.language_parsers.cpp_parser"

        module = importlib.import_module(module_name)
        parser_class = getattr(module, parser_class_name)
        parser_instance: ParserInterface = parser_class()
        logger.debug(f"Successfully loaded Standard Regex parser for {language}")
        return parser_instance
    except (ImportError, AttributeError) as e:
        logger.warning(f"Could not load Standard Regex parser for {language}: {e}")
        return None
    except (TypeError, ValueError, RuntimeError, MemoryError) as e:
        logger.error(f"Error initializing Standard Regex parser for {language}: {e}", exc_info=True)
        return None


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
    except (UnicodeError, ValueError, TypeError, AttributeError) as e:
        logger.warning(f"Error normalizing unicode for {file_path}: {e}")
        return content  # Return original on error


def parse_with_error_recovery(parser_instance, content: str, file_path: str, language: str):
    """
    Parse with error recovery using a fallback chain of parsers.

    Implements a graceful degradation strategy when the primary parser fails:
    1. Try primary parser (usually tree-sitter)
    2. If fails, try simplified parsing (if parser supports it)
    3. As last resort, create plain text fallback with basic structure

    This ensures that some useful output is always produced, even for
    malformed or partially corrupted source files.

    Args:
        parser_instance: The primary parser to use (implements ParserInterface)
        content: Content to parse
        file_path: Path to the file being parsed
        language: Programming language identifier

    Returns:
        ParseResult object with declarations and any errors

    Complexity:
        O(n) for successful parse, O(2n) worst case with fallback

    Flow:
        Called by: parse_code_files() when parsing individual files
        Calls: parser_instance.parse(), parser_instance.parse_simple()

    Note:
        Always returns a ParseResult, never raises exceptions
    """
    from ..base_types import ParseResult

    # Try primary parser
    try:
        parse_result = parser_instance.parse(content, file_path)
        if parse_result and not parse_result.error:
            return parse_result
    except (AttributeError, ValueError, TypeError, RuntimeError) as e:
        logger.warning(f"Primary parser failed for {file_path}: {e}")

    # Try simplified parsing if available
    if hasattr(parser_instance, "parse_simple"):
        try:
            logger.debug(f"Attempting simplified parsing for {file_path}")
            parse_result = parser_instance.parse_simple(content, file_path)
            if parse_result:
                parse_result.degraded = True
                return parse_result
        except (AttributeError, ValueError, TypeError, RuntimeError) as e:
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
