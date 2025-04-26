import logging

logger = logging.getLogger(__name__)
import os
from functools import lru_cache
from typing import Callable, Dict, List, Optional, Tuple
import inspect

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
    files_to_parse: List[ParsedFileData], config: CodeConCatConfig
) -> Tuple[List[ParsedFileData], List[ParserError]]:
    """
    Parses multiple code files using pre-read content, collecting results and errors.
    Handles language determination, parsing, and optional processing steps based on ParsedFileData.
    """
    parsed_files_output: List[ParsedFileData] = []
    errors: List[ParserError] = []

    for file_data in files_to_parse:
        file_path = file_data.file_path
        content = file_data.content
        language = file_data.language  # Use language determined by collector

        try:
            # Basic validation - skip if essential data is missing
            if not file_path or content is None:
                errors.append(
                    ParserError("Missing file path or content in input data", file_path=file_path)
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
                    logger.debug(f"Skipping file {file_path} with unknown/unsupported language: {language}")
                continue # Skip this file

            # Check include/exclude languages from config (redundant if collector already did this, but safe)
            if config.include_languages and language not in config.include_languages:
                logger.debug(f"Skipping {file_path} (lang: {language}) due to include_languages config")
                continue
            if config.exclude_languages and language in config.exclude_languages:
                logger.debug(f"Skipping {file_path} (lang: {language}) due to exclude_languages config")
                continue

            # --- File Opening Removed - Content is already provided --- 
            # with open(file_path, "r", encoding="utf-8", errors="strict") as f:
            #     content = f.read()

            parse_func = get_language_parser(language) # Pass language

            if not parse_func:
                 raise UnsupportedLanguageError(
                     f"Parser function mapping not found for language '{language}' of file '{file_path}'",
                     file_path=file_path,
                 )

            # Determine the actual parsing function, handling JS/TS variations
            if language in ["javascript", "typescript"]:
                 # Ensure the parser function accepts the language hint if needed
                 sig = inspect.signature(parse_func)
                 if 'language' in sig.parameters:
                     actual_parse_func = lambda fp, c: parse_func(fp, c, language=language)
                 else:
                     actual_parse_func = parse_func
            else:
                actual_parse_func = parse_func

            # Perform the parsing using the provided content
            parse_result: ParseResult = actual_parse_func(file_path, content)

            # --- Optional Processing (Token Counting, Security Scan) ---
            token_stats: Optional[TokenStats] = None
            if config.enable_token_counting:
                from codeconcat.processor.token_counter import get_token_stats
                try:
                    token_stats = get_token_stats(content)
                except Exception as e:
                    logger.warning(f"Token counting failed for {file_path}: {e}")

            security_issues: List[SecurityIssue] = []
            if config.enable_security_scanning:
                from codeconcat.processor.security_processor import SecurityProcessor
                try:
                    security_issues = SecurityProcessor.scan_content(content, file_path, config)
                except Exception as e:
                    logger.warning(f"Security scanning failed for {file_path}: {e}")

            # Append successfully parsed data
            parsed_files_output.append(
                ParsedFileData(
                    file_path=parse_result.file_path,
                    language=parse_result.language,
                    content=parse_result.content, # Store original content
                    declarations=parse_result.declarations,
                    token_stats=token_stats,
                    security_issues=security_issues,
                )
            )

        # --- Exception Handling --- (Moved FileNotFoundError outside, as file isn't opened here)
        # except FileNotFoundError as e: # No longer applicable here
        #     logger.warning(f"Skipping file {file_path}: File not found.")
        #     errors.append(FileProcessingError(str(e), file_path=file_path, original_exception=e))
        except UnicodeDecodeError as e: # Should not happen if collector reads correctly
            logger.warning(f"Skipping file {file_path} due to unexpected decode error in pre-read content: {e}")
            errors.append(
                ParserError(f"Unicode decode error in content: {e}", file_path=file_path, original_exception=e)
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
            import traceback
            logger.error(f"Unexpected error processing {file_path}: {e}\n{traceback.format_exc()}")
            errors.append(
                ParserError(
                    f"Unexpected error: {type(e).__name__} - {e}",
                    file_path=file_path,
                    original_exception=e,
                )
            )

    if errors:
        logger.info(f"Finished parsing {len(files_to_parse)} inputs. Encountered {len(errors)} errors.")

    return parsed_files_output, errors


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


def get_language_parser(language: str) -> Optional[Callable]:
    """Get the appropriate parser function for a given language identifier."""
    # Map language identifiers (strings) to parser functions
    language_to_parser_map: Dict[str, Callable] = {
        "python": parse_python,
        "javascript": parse_javascript_or_typescript,
        "typescript": parse_javascript_or_typescript,
        "r": parse_r,
        "julia": parse_julia,
        "rust": parse_rust,
        "cpp": parse_cpp_code,
        "c": parse_c_code,
        "csharp": parse_csharp_code,
        "java": parse_java,
        "go": parse_go,
        "php": parse_php,
        # Add other supported languages and their parser functions here
        # "html": parse_html, # Example
        # "css": parse_css,   # Example
    }

    # Normalize language string (lowercase, maybe remove hyphens/underscores?)
    # For now, just lowercase seems consistent with language_map.py
    normalized_language = language.lower()

    parser_func = language_to_parser_map.get(normalized_language)

    if parser_func is None:
        logger.debug(f"No specific parser function found for language: {language} ({normalized_language})")
        return None

    return parser_func
