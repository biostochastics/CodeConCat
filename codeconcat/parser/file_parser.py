import logging

logger = logging.getLogger(__name__)
import os
from functools import lru_cache
from typing import Callable, Dict, List, Optional, Tuple

from codeconcat.base_types import (
    CodeConCatConfig,
    Declaration,
    ParseResult,
    ParsedFileData,
    TokenStats,
    SecurityIssue,
)
from codeconcat.errors import (
    FileProcessingError,
    ParserError,
    UnsupportedLanguageError,
    LanguageParserError,
)

from .language_parsers.c_parser import parse_c_code
from .language_parsers.cpp_parser import parse_cpp_code
from .language_parsers.csharp_parser import parse_csharp_code
from .language_parsers.go_parser import parse_go
from .language_parsers.java_parser import parse_java
from .language_parsers.js_ts_parser import parse_javascript_or_typescript
from .language_parsers.julia_parser import parse_julia
from .language_parsers.php_parser import parse_php
from .language_parsers.python_parser import parse_python
from .language_parsers.r_parser import parse_r
from .language_parsers.rust_parser import parse_rust


logger = logging.getLogger(__name__)


def parse_code_files(
    file_paths: List[str], config: CodeConCatConfig
) -> Tuple[List[ParsedFileData], List[ParserError]]:
    """
    Parses multiple code files, collecting both results and errors.
    Handles file opening, language determination, parsing, and optional processing steps.
    """
    parsed_files: List[ParsedFileData] = []
    errors: List[ParserError] = []

    for file_path in file_paths:
        language = None
        try:
            language = determine_language(file_path)
            if not language or language == "unknown":
                ext = os.path.splitext(file_path)[1].lower()
                if ext and ext in get_all_known_extensions():
                    errors.append(
                        UnsupportedLanguageError(
                            f"No parser available for determined language of '{file_path}'",
                            file_path=file_path,
                        )
                    )
                continue

            if config.include_languages and language not in config.include_languages:
                continue
            if config.exclude_languages and language in config.exclude_languages:
                continue

            with open(file_path, "r", encoding="utf-8", errors="strict") as f:
                content = f.read()

            parser_info = get_language_parser(file_path)
            if not parser_info:
                raise UnsupportedLanguageError(
                    f"Parser function mapping not found for language '{language}' of file '{file_path}'",
                    file_path=file_path,
                )
            parse_func = parser_info[1]
            if language in ["javascript", "typescript"]:
                actual_parse_func = lambda fp, c: parse_func(fp, c, language=language)
            else:
                actual_parse_func = parse_func

            parse_result: ParseResult = actual_parse_func(file_path, content)

            token_stats: Optional[TokenStats] = None
            if config.enable_token_counting:
                # Import moved here to break circular dependency
                from codeconcat.processor.token_counter import get_token_stats

                try:
                    token_stats = get_token_stats(content)
                except Exception as e:
                    logger.warning(f"Token counting failed for {file_path}: {e}")

            security_issues: List[SecurityIssue] = []
            if config.enable_security_scanning:
                # Import moved here to break circular dependency
                from codeconcat.processor.security_processor import SecurityProcessor

                try:
                    security_issues = SecurityProcessor.scan_content(content, file_path, config)
                except Exception as e:
                    logger.warning(f"Security scanning failed for {file_path}: {e}")

            parsed_files.append(
                ParsedFileData(
                    file_path=parse_result.file_path,
                    language=parse_result.language,
                    content=parse_result.content,
                    declarations=parse_result.declarations,
                    token_stats=token_stats,
                    security_issues=security_issues,
                )
            )

        except FileNotFoundError as e:
            logger.warning(f"Skipping file {file_path}: File not found.")
            errors.append(FileProcessingError(str(e), file_path=file_path, original_exception=e))
        except UnicodeDecodeError as e:
            logger.warning(f"Skipping file {file_path} due to decode error: {e}")
            errors.append(
                ParserError(f"Unicode decode error: {e}", file_path=file_path, original_exception=e)
            )
        except LanguageParserError as e:
            logger.warning(f"Skipping file {file_path} due to parsing error: {e}")
            errors.append(e)
        except UnsupportedLanguageError as e:
            logger.warning(f"Skipping file {file_path}: {e}")
            errors.append(e)
        except FileProcessingError as e:
            logger.warning(f"Skipping file {file_path} due to processing error: {e}")
            errors.append(ParserError(str(e), file_path=e.file_path, original_exception=e))
        except Exception as e:
            logger.error(f"Unexpected error processing {file_path}: {e}", exc_info=True)
            errors.append(
                ParserError(
                    f"Unexpected error: {type(e).__name__} - {e}",
                    file_path=file_path,
                    original_exception=e,
                )
            )

    if errors:
        logger.info(f"Finished parsing. Encountered {len(errors)} errors.")

    return parsed_files, errors


@lru_cache(maxsize=100)
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


def get_all_known_extensions() -> set:
    """Returns a set of all file extensions CodeConCat knows how to potentially parse."""
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


def get_language_parser(file_path: str) -> Optional[Tuple[str, Callable]]:
    """Get the appropriate parser for a file based on its extension."""
    ext = file_path.split(".")[-1].lower() if "." in file_path else ""

    extension_map = {
        ".py": ("python", parse_python),
        ".js": ("javascript", parse_javascript_or_typescript),
        ".ts": ("typescript", parse_javascript_or_typescript),
        ".jsx": ("javascript", parse_javascript_or_typescript),
        ".tsx": ("typescript", parse_javascript_or_typescript),
        ".r": ("r", parse_r),
        ".jl": ("julia", parse_julia),
        ".rs": ("rust", parse_rust),
        ".cpp": ("cpp", parse_cpp_code),
        ".cxx": ("cpp", parse_cpp_code),
        ".cc": ("cpp", parse_cpp_code),
        ".hpp": ("cpp", parse_cpp_code),
        ".hxx": ("cpp", parse_cpp_code),
        ".h": ("c", parse_c_code),
        ".c": ("c", parse_c_code),
        ".cs": ("csharp", parse_csharp_code),
        ".java": ("java", parse_java),
        ".go": ("go", parse_go),
        ".php": ("php", parse_php),
    }

    ext_with_dot = f".{ext}" if not ext.startswith(".") else ext
    return extension_map.get(ext_with_dot)
