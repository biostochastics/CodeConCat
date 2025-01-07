import os
from typing import List, Optional, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor

from codeconcat.base_types import CodeConCatConfig, ParsedFileData
from codeconcat.parser.language_parsers.python_parser import parse_python
from codeconcat.parser.language_parsers.js_ts_parser import parse_javascript_or_typescript
from codeconcat.parser.language_parsers.r_parser import parse_r
from codeconcat.parser.language_parsers.julia_parser import parse_julia
from codeconcat.parser.language_parsers.rust_parser import parse_rust_code
from codeconcat.parser.language_parsers.cpp_parser import parse_cpp_code
from codeconcat.parser.language_parsers.c_parser import parse_c_code
from codeconcat.parser.language_parsers.csharp_parser import parse_csharp_code
from codeconcat.parser.language_parsers.java_parser import parse_java
from codeconcat.parser.language_parsers.go_parser import parse_go
from codeconcat.parser.language_parsers.php_parser import parse_php


def parse_code_files(file_paths: List[str], config: CodeConCatConfig) -> List[ParsedFileData]:
    code_paths = [fp for fp in file_paths if not is_doc_file(fp, config.doc_extensions)]

    with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        results = list(executor.map(lambda fp: parse_single_file(fp, config), code_paths))
    return results


def parse_single_file(file_path: str, config: CodeConCatConfig) -> ParsedFileData:
    ext = os.path.splitext(file_path)[1].lower().lstrip(".")
    content = read_file_content(file_path)

    parser_info = get_language_parser(file_path)
    if parser_info:
        language, parser_func = parser_info
        if parser_func == parse_javascript_or_typescript:
            return parser_func(file_path, content, language)
        return parser_func(file_path, content)
    else:
        return ParsedFileData(file_path=file_path, language=get_language_name(file_path), content=content)


def get_language_parser(file_path: str) -> Optional[Tuple[str, Callable]]:
    """Get the appropriate parser for a file based on its extension."""
    ext = file_path.split('.')[-1].lower() if '.' in file_path else ''
    
    extension_map = {
        # Existing parsers
        '.py': ("python", parse_python),
        '.js': ("javascript", parse_javascript_or_typescript),
        '.ts': ("typescript", parse_javascript_or_typescript),
        '.jsx': ("javascript", parse_javascript_or_typescript),
        '.tsx': ("typescript", parse_javascript_or_typescript),
        '.r': ("r", parse_r),
        '.jl': ("julia", parse_julia),
        
        # New parsers
        '.rs': ("rust", parse_rust_code),
        '.cpp': ("cpp", parse_cpp_code),
        '.cxx': ("cpp", parse_cpp_code),
        '.cc': ("cpp", parse_cpp_code),
        '.hpp': ("cpp", parse_cpp_code),
        '.hxx': ("cpp", parse_cpp_code),
        '.h': ("c", parse_c_code),  # Note: .h could be C or C++
        '.c': ("c", parse_c_code),
        '.cs': ("csharp", parse_csharp_code),
        '.java': ("java", parse_java),
        '.go': ("go", parse_go),
        '.php': ("php", parse_php),
    }
    
    ext_with_dot = f".{ext}" if not ext.startswith('.') else ext
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
