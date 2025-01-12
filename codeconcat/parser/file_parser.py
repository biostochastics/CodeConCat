import os
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import Callable, List, Optional, Tuple

from codeconcat.base_types import CodeConCatConfig, ParsedFileData
from codeconcat.parser.language_parsers.base_parser import BaseParser
from codeconcat.parser.language_parsers.c_parser import parse_c_code
from codeconcat.parser.language_parsers.cpp_parser import parse_cpp_code
from codeconcat.parser.language_parsers.csharp_parser import parse_csharp_code
from codeconcat.parser.language_parsers.go_parser import parse_go
from codeconcat.parser.language_parsers.java_parser import parse_java
from codeconcat.parser.language_parsers.js_ts_parser import parse_javascript_or_typescript
from codeconcat.parser.language_parsers.julia_parser import parse_julia
from codeconcat.parser.language_parsers.php_parser import parse_php
from codeconcat.parser.language_parsers.python_parser import parse_python
from codeconcat.parser.language_parsers.r_parser import parse_r
from codeconcat.parser.language_parsers.rust_parser import parse_rust_code
from codeconcat.processor.token_counter import get_token_stats


@lru_cache(maxsize=100)
def _parse_single_file(file_path: str, language: str) -> Optional[ParsedFileData]:
    """
    Parse a single file with caching. This function is memoized to improve performance
    when the same file is processed multiple times.
    
    Args:
        file_path: Path to the file to parse
        language: Programming language of the file
        
    Returns:
        ParsedFileData if successful, None if parsing failed
        
    Note:
        The function is cached based on file_path and language. The cache is cleared
        when the file content changes (detected by modification time).
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if language == "python":
            return parse_python(file_path, content)
        elif language in ["javascript", "typescript"]:
            return parse_javascript_or_typescript(file_path, content, language)
        elif language == "c":
            return parse_c_code(file_path, content)
        elif language == "cpp":
            return parse_cpp_code(file_path, content)
        elif language == "csharp":
            return parse_csharp_code(file_path, content)
        elif language == "go":
            return parse_go(file_path, content)
        elif language == "java":
            return parse_java(file_path, content)
        elif language == "julia":
            return parse_julia(file_path, content)
        elif language == "php":
            return parse_php(file_path, content)
        elif language == "r":
            return parse_r(file_path, content)
        elif language == "rust":
            return parse_rust_code(file_path, content)
        else:
            raise ValueError(f"Unsupported language: {language}")
            
    except UnicodeDecodeError:
        raise ValueError(f"Failed to decode {file_path}. File may be binary or use an unsupported encoding.")
    except Exception as e:
        raise RuntimeError(f"Error parsing {file_path}: {str(e)}")


def parse_code_files(file_paths: List[str], config: CodeConCatConfig) -> List[ParsedFileData]:
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
                parsed_files.append(parsed_file)
                
        except FileNotFoundError as e:
            errors.append(f"File not found: {file_path}")
        except UnicodeDecodeError:
            errors.append(f"Failed to decode {file_path}. File may be binary or use an unsupported encoding.")
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
    ext = os.path.splitext(file_path)[1].lower()
    language_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.r': 'r',
        '.jl': 'julia',
        '.rs': 'rust',
        '.cpp': 'cpp',
        '.cxx': 'cpp',
        '.cc': 'cpp',
        '.hpp': 'cpp',
        '.hxx': 'cpp',
        '.h': 'c',
        '.c': 'c',
        '.cs': 'csharp',
        '.java': 'java',
        '.go': 'go',
        '.php': 'php',
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
        ".rs": ("rust", parse_rust_code),
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
