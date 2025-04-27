import os
import logging
import traceback
from typing import List, Optional, Tuple, Callable, Set
from tqdm import tqdm
import functools

from codeconcat.base_types import (
    ParsedFileData,
    ParseResult,
    CodeConCatConfig,
)
from codeconcat.errors import (
    FileProcessingError,
    LanguageParserError,
    ParserError,
    UnsupportedLanguageError,
)

# Setup logger
logger = logging.getLogger(__name__)

# +++ Log after imports +++
logger.debug(
    "file_parser.py module loaded successfully (parsers will be imported lazily)."
)


def parse_code_files(
    files_to_parse: List[ParsedFileData], config: CodeConCatConfig
) -> Tuple[List[ParsedFileData], List[ParserError]]:
    """
    Parses multiple code files using pre-read content, collecting results and errors.

    Handles language determination, parsing, and optional processing steps based on
    the provided file data and configuration.

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
            if config.exclude_languages and language in config.exclude_languages:
                logger.debug(
                    f"[parse_code_files] Skipping {file_path} (lang: {language}) due to exclude_languages config"
                )
                continue

            # +++ Add log before getting parser +++
            logger.debug(
                f"[parse_code_files] Attempting to get parser for language: {language} for file {file_path}"
            )
            parse_func = get_language_parser(language)  # Pass language
            # +++ Add log after getting parser +++
            logger.debug(
                f"[parse_code_files] Successfully got parser: {getattr(parse_func, '__name__', str(parse_func))} for file {file_path}"
            )

            if not parse_func:
                raise UnsupportedLanguageError(
                    f"No parser implementation available for language: {language}",
                    file_path=file_path,
                )

            # +++ Log before calling parser +++
            logger.debug(
                f"[parse_code_files] Attempting to call parser: {getattr(parse_func, '__name__', str(parse_func))} for {file_path}"
            )
            # --- Call the parser and handle potential tuple return --- #
            parser_result: ParseResult = parse_func(file_path, content)

            # Assign results directly to the file_data object
            file_data.declarations = parser_result.declarations
            file_data.imports = parser_result.imports
            file_data.token_stats = parser_result.token_stats
            file_data.security_issues = parser_result.security_issues

            parsed_files_output.append(file_data)  # Add the updated file_data

        except LanguageParserError as e:
            logger.warning(
                f"[parse_code_files] Skipping file {file_path} due to parsing error: {e}"
            )
            errors.append(e)
        except UnsupportedLanguageError as e:
            logger.warning(f"[parse_code_files] Skipping file {file_path}: {e}")
            errors.append(e)
        except FileProcessingError as e:
            logger.warning(
                f"[parse_code_files] Skipping file {file_path} due to processing error: {e}"
            )
            errors.append(
                ParserError(str(e), file_path=e.file_path, original_exception=e)
            )
        except Exception as e:
            logger.error(
                f"[parse_code_files] Unexpected error processing {file_path}: {e}\n{traceback.format_exc()}"
            )
            errors.append(
                ParserError(
                    f"[parse_code_files] Unexpected error: {type(e).__name__} - {e}",
                    file_path=file_path,
                    original_exception=e,
                )
            )

    # +++ Add exit log +++
    logger.debug(
        f"[parse_code_files] Finished parse_code_files loop. Found {len(errors)} errors."
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


def get_language_parser(language: str) -> Optional[Callable]:
    """Get the appropriate parser function for a given language identifier (imports lazily).

    Attempts to dynamically import the parser module for the requested language
    to avoid loading all parsers unnecessarily.

    Args:
        language: The language identifier string (e.g., 'python', 'javascript').
                  Case-insensitive.

    Returns:
        The parser function (Callable) if found and successfully imported,
        otherwise None.
    """

    normalized_language = language.lower()
    logger.debug(
        f"[get_language_parser] Attempting lazy import for parser: {normalized_language}"
    )

    parser_func: Optional[Callable] = None

    try:
        if normalized_language == "python":
            from .language_parsers.python_parser import parse_python

            parser_func = parse_python
        elif normalized_language in ["javascript", "typescript"]:
            from .language_parsers.js_ts_parser import parse_javascript_or_typescript

            parser_func = parse_javascript_or_typescript
        elif normalized_language == "java":
            from .language_parsers.java_parser import parse_java

            parser_func = parse_java
        elif normalized_language == "go":
            from .language_parsers.go_parser import parse_go

            parser_func = parse_go
        elif normalized_language == "php":
            from .language_parsers.php_parser import parse_php

            parser_func = parse_php
        elif normalized_language == "c":
            from .language_parsers.c_parser import parse_c_code

            parser_func = parse_c_code
        elif normalized_language == "cpp":
            from .language_parsers.cpp_parser import parse_cpp_code

            parser_func = parse_cpp_code
        elif normalized_language == "csharp":
            from .language_parsers.csharp_parser import parse_csharp_code

            parser_func = parse_csharp_code
        elif normalized_language == "r":
            from .language_parsers.r_parser import parse_r

            parser_func = parse_r
        elif normalized_language == "rust":
            from .language_parsers.rust_parser import parse_rust

            parser_func = parse_rust
        elif normalized_language == "julia":
            from .language_parsers.julia_parser import parse_julia

            parser_func = parse_julia
        # Add other supported languages here if needed
        else:
            logger.debug(
                f"[get_language_parser] No specific parser function found for language: {language} ({normalized_language})"
            )
            return None
    except ImportError as e:
        logger.error(
            f"[get_language_parser] Failed to lazily import parser for {normalized_language}: {e}"
        )
        return None

    logger.debug(
        f"[get_language_parser] Successfully lazy-imported parser for {normalized_language}"
    )
    return parser_func


@functools.lru_cache(maxsize=None)
def determine_language(file_path: str) -> Optional[str]:
    """
    Determine the programming language of a file based on its extension.
    This function is cached to improve performance.

    Args:
        file_path: Path to the file

    Returns:
        Language identifier or None if unknown
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
