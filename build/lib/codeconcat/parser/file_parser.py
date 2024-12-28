import os
from typing import List
from concurrent.futures import ThreadPoolExecutor

from codeconcat.types import CodeConCatConfig, ParsedFileData
from codeconcat.parser.language_parsers.python_parser import parse_python
from codeconcat.parser.language_parsers.js_ts_parser import parse_javascript_or_typescript
from codeconcat.parser.language_parsers.r_parser import parse_r
from codeconcat.parser.language_parsers.julia_parser import parse_julia


def parse_code_files(file_paths: List[str], config: CodeConCatConfig) -> List[ParsedFileData]:
    code_paths = [fp for fp in file_paths if not is_doc_file(fp, config.doc_extensions)]

    with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        results = list(executor.map(lambda fp: parse_single_file(fp, config), code_paths))
    return results


def parse_single_file(file_path: str, config: CodeConCatConfig) -> ParsedFileData:
    ext = os.path.splitext(file_path)[1].lower().lstrip(".")
    content = read_file_content(file_path)

    if ext == "py":
        return parse_python(file_path, content)
    elif ext == "js":
        return parse_javascript_or_typescript(file_path, content, language="javascript")
    elif ext == "ts":
        return parse_javascript_or_typescript(file_path, content, language="typescript")
    elif ext == "r":
        return parse_r(file_path, content)
    elif ext == "jl":
        return parse_julia(file_path, content)
    else:
        return ParsedFileData(file_path=file_path, language=ext, content=content)


def is_doc_file(file_path: str, doc_exts: List[str]) -> bool:
    ext = os.path.splitext(file_path)[1].lower()
    return ext in doc_exts


def read_file_content(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""
