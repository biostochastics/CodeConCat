import os
from typing import List
from concurrent.futures import ThreadPoolExecutor

from codeconcat.types import CodeConCatConfig, ParsedDocData


def extract_docs(file_paths: List[str], config: CodeConCatConfig) -> List[ParsedDocData]:
    doc_paths = [fp for fp in file_paths if is_doc_file(fp, config.doc_extensions)]

    with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        results = list(executor.map(lambda fp: parse_doc_file(fp), doc_paths))
    return results


def is_doc_file(file_path: str, doc_exts: List[str]) -> bool:
    ext = os.path.splitext(file_path)[1].lower()
    return ext in doc_exts


def parse_doc_file(file_path: str) -> ParsedDocData:
    ext = os.path.splitext(file_path)[1].lower()
    content = read_doc_content(file_path)
    doc_type = ext.lstrip(".")
    return ParsedDocData(file_path=file_path, doc_type=doc_type, content=content)


def read_doc_content(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""
