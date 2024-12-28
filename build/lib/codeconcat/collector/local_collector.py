"""
local_collector.py

Recursively collects files from the local filesystem, applying exclude patterns,
language filters, and concurrency for filtering.
"""

import os
import fnmatch
from typing import List
from concurrent.futures import ThreadPoolExecutor

from codeconcat.types import CodeConCatConfig

def collect_local_files(root_path: str, config: CodeConCatConfig) -> List[str]:
    """
    Walks the local filesystem, returning a list of files that pass the config filters.
    Concurrency is used for post-walk filtering.
    """
    all_files = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        if is_excluded_path(dirpath, config.exclude_paths):
            dirnames[:] = []
            continue

        for fname in filenames:
            all_files.append(os.path.join(dirpath, fname))

    with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        results = list(executor.map(
            lambda p: p if should_include_file(p, config) else None,
            all_files
        ))

    final_files = [r for r in results if r is not None]
    return final_files

def is_excluded_path(path_str: str, exclude_patterns: List[str]) -> bool:
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(path_str, pattern) or pattern in path_str:
            return True
    return False

def should_include_file(path_str: str, config: CodeConCatConfig) -> bool:
    if is_excluded_path(path_str, config.exclude_paths):
        return False

    ext = os.path.splitext(path_str)[1].lower().lstrip(".")
    language_label = ext_map(ext, config)

    if config.include_languages and language_label not in config.include_languages:
        return False

    if language_label in config.exclude_languages:
        return False

    return True

def ext_map(ext: str, config: CodeConCatConfig) -> str:
    # Check user overrides first
    if ext in config.custom_extension_map:
        return config.custom_extension_map[ext]

    builtin = {
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "r": "r",
        "jl": "julia",
        "cpp": "cpp",
        "hpp": "cpp",
        "cxx": "cpp",
        "c": "c",
        "h": "c",
        "md": "doc",
        "rst": "doc",
        "txt": "doc",
        "rmd": "doc",
    }
    return builtin.get(ext, ext)
