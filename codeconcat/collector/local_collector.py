import os
import fnmatch
from typing import List
from concurrent.futures import ThreadPoolExecutor

from codeconcat.types import CodeConCatConfig

DEFAULT_EXCLUDES = [
    # Version Control
    ".git",
    ".git/**",
    "**/.git/**",
    ".gitignore",
    "**/.gitignore",
    
    # OS and Editor Files
    ".DS_Store",
    "**/.DS_Store",
    "Thumbs.db",
    "**/*.swp",
    "**/*.swo",
    ".idea/**",
    ".vscode/**",
    
    # Build and Compilation
    "__pycache__",
    "**/__pycache__/**",
    "*.pyc",
    "**/*.pyc",
    "*.pyo",
    "**/*.pyo",
    "*.pyd",
    "*.so",
    "*.dll",
    "*.dylib",
    "*.class",
    "*.exe",
    "*.bin",
    "build/**",
    "dist/**",
    "*.egg-info/**",
    "**/build/**",
    "**/dist/**",
    "**/*.egg-info/**",
    
    # Dependencies
    "node_modules/**",
    "**/node_modules/**",
    "venv/**",
    "**/.env/**",
    
    # Documentation Build
    "_build/**",
    "**/_build/**",
    "**/*.doctree",
    "**/searchindex.js",
    "**/objects.inv",
    "**/_static/**",
    "**/_sources/**",
    "**/CACHEDIR.TAG",
    
    # Caches and Temporary
    ".pytest_cache/**",
    "**/.pytest_cache/**",
    ".mypy_cache/**",
    ".ruff_cache/**",
    ".coverage",
    "coverage/**",
    "**/*.log",
    "**/*.tmp",
    "**/*.temp",
    
    # Binary and Data Files
    "**/*.pkl",
    "**/*.h5",
    "**/*.parquet",
    "**/*.o",
    "**/*.a"
]


def collect_local_files(root_path: str, config: CodeConCatConfig) -> List[str]:
    all_files = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        if should_skip_dir(dirpath, config.exclude_paths):
            dirnames[:] = []
            continue

        for fname in filenames:
            full_path = os.path.join(dirpath, fname)
            all_files.append(full_path)

    with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        results = list(executor.map(
            lambda p: p if should_include_file(p, config) else None,
            all_files
        ))
    final_files = [r for r in results if r is not None]
    return final_files


def should_skip_dir(dirpath: str, user_excludes: List[str]) -> bool:
    """Check if a directory should be skipped based on exclude patterns."""
    rel_path = os.path.relpath(dirpath, os.getcwd())
    combined = user_excludes + DEFAULT_EXCLUDES
    
    for pattern in combined:
        if pattern.endswith('/**'):
            dir_pattern = pattern[:-3]  # Remove '/**'
            if matches_pattern(rel_path, dir_pattern):
                return True
        elif matches_pattern(rel_path, pattern):
            return True
    return False


def should_include_file(path_str: str, config: CodeConCatConfig) -> bool:
    combined_excludes = config.exclude_paths + DEFAULT_EXCLUDES
    if any(matches_pattern(path_str, pat) for pat in combined_excludes):
        return False

    # Skip binary files
    if is_binary_file(path_str):
        return False

    ext = os.path.splitext(path_str)[1].lower().lstrip(".")
    language_label = ext_map(ext, config)

    if config.include_languages and language_label not in config.include_languages:
        return False
    if language_label in config.exclude_languages:
        return False

    return True


def matches_pattern(path_str: str, pattern: str) -> bool:
    return fnmatch.fnmatch(path_str, pattern) or pattern in path_str


def ext_map(ext: str, config: CodeConCatConfig) -> str:
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


def is_binary_file(file_path: str) -> bool:
    """Check if a file is likely to be binary."""
    try:
        with open(file_path, 'tr') as check_file:
            check_file.readline()
            return False
    except UnicodeDecodeError:
        return True
