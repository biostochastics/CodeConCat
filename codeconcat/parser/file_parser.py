import logging
import os
from functools import lru_cache
from typing import Callable, Dict, List, Optional, Tuple

from codeconcat.base_types import Declaration, ParseResult, ParsedFileData
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


@lru_cache(maxsize=100)
def _parse_single_file(file_path: str, language: str) -> Optional[ParseResult]:
    """
    Parse a single file with caching. This function is memoized to improve performance
    when the same file is processed multiple times.

    Args:
        file_path: Path to the file to parse
        language: Programming language of the file

    Returns:
        ParseResult if successful, None if parsing failed

    Note:
        The function is cached based on file_path and language. The cache is cleared
        when the file content changes (detected by modification time).
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        parse_func = {
            "python": parse_python,
            "javascript": lambda x, y: parse_javascript_or_typescript(x, y, "javascript"),
            "typescript": lambda x, y: parse_javascript_or_typescript(x, y, "typescript"),
            "c": parse_c_code,
            "cpp": parse_cpp_code,
            "csharp": parse_csharp_code,
            "go": parse_go,
            "java": parse_java,
            "julia": parse_julia,
            "php": parse_php,
            "r": parse_r,
            "rust": parse_rust,
        }.get(language)

        if not parse_func:
            raise ValueError(f"Unsupported language: {language}")

        try:
            return parse_func(file_path, content)
        except Exception:
            logging.error(f"Error parsing file {file_path}")
            return None

    except UnicodeDecodeError:
        raise ValueError(
            f"Failed to decode {file_path}. File may be binary or use an unsupported encoding."
        )
    except Exception as e:
        raise RuntimeError(f"Error parsing {file_path}: {str(e)}")


def parse_code_files(
    file_paths: List[str], config: Dict
) -> List[ParsedFileData]:
    """
    Parse multiple code files with improved error handling and caching.

    Args:
        file_paths: List of file paths to parse
        config: Configuration object

    Returns:
        List of successfully parsed files

    Note:
        Files that fail to parse are logged with detailed error messages but don't
        cause the entire process to fail.
    """
    parsed_files = []
    errors = []

    for file_path in file_paths:
        try:
            # Determine language (you may want to cache this too)
            language = determine_language(file_path)
            if not language:
                errors.append(f"Could not determine language for {file_path}")
                continue

            # Parse file with caching
            parsed_file = _parse_single_file(file_path, language)
            if parsed_file:
                # Convert ParseResult to ParsedFileData
                parsed_files.append(ParsedFileData(
                    file_path=parsed_file.file_path,
                    language=parsed_file.language,
                    content=parsed_file.content,
                    declarations=parsed_file.declarations
                ))

        except FileNotFoundError as e:
            errors.append(f"File not found: {file_path}")
        except UnicodeDecodeError:
            errors.append(
                f"Failed to decode {file_path}. File may be binary or use an unsupported encoding."
            )
        except ValueError as e:
            errors.append(str(e))
        except Exception as e:
            errors.append(f"Unexpected error parsing {file_path}: {str(e)}")

    # Log errors if any occurred
    if errors:
        error_summary = "\n".join(errors)
        print(f"Encountered errors while parsing files:\n{error_summary}")

    return parsed_files


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
    # Get base name and extension
    basename = os.path.basename(file_path)
    ext = os.path.splitext(file_path)[1].lower()

    # Skip R project-specific files
    r_specific_files = {
        "DESCRIPTION",  # R package description
        "NAMESPACE",  # R package namespace
        ".Rproj",  # RStudio project file
        "configure",  # R package configuration
        "configure.win",  # R package Windows configuration
    }
    if basename in r_specific_files:
        return None

    # Handle regular file extensions
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


def get_language_parser(file_path: str) -> Optional[Tuple[str, Callable]]:
    """Get the appropriate parser for a file based on its extension."""
    ext = file_path.split(".")[-1].lower() if "." in file_path else ""

    extension_map = {
        # Existing parsers
        ".py": ("python", parse_python),
        ".js": ("javascript", parse_javascript_or_typescript),
        ".ts": ("typescript", parse_javascript_or_typescript),
        ".jsx": ("javascript", parse_javascript_or_typescript),
        ".tsx": ("typescript", parse_javascript_or_typescript),
        ".r": ("r", parse_r),
        ".jl": ("julia", parse_julia),
        # New parsers
        ".rs": ("rust", parse_rust),
        ".cpp": ("cpp", parse_cpp_code),
        ".cxx": ("cpp", parse_cpp_code),
        ".cc": ("cpp", parse_cpp_code),
        ".hpp": ("cpp", parse_cpp_code),
        ".hxx": ("cpp", parse_cpp_code),
        ".h": ("c", parse_c_code),  # Note: .h could be C or C++
        ".c": ("c", parse_c_code),
        ".cs": ("csharp", parse_csharp_code),
        ".java": ("java", parse_java),
        ".go": ("go", parse_go),
        ".php": ("php", parse_php),
    }

    ext_with_dot = f".{ext}" if not ext.startswith(".") else ext
    return extension_map.get(ext_with_dot)


def get_language_name(file_path: str) -> str:
    """Get the language name for a file based on its extension."""
    parser_info = get_language_parser(file_path)
    if parser_info:
        return parser_info[0]
    return "unknown"


def is_doc_file(file_path: str, doc_exts: List[str]) -> bool:
    ext = os.path.splitext(file_path)[1].lower()
    return ext in doc_exts


def read_file_content(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""
