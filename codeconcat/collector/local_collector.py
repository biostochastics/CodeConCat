import os
import fnmatch
from typing import List
from concurrent.futures import ThreadPoolExecutor
import logging

from codeconcat.types import CodeConCatConfig

# Set up logging
logging.basicConfig(level=logging.DEBUG)

DEFAULT_EXCLUDES = [
    # Version Control
    ".git/",  # Match the .git directory itself
    ".git/**",  # Match contents of .git directory
    "**/.git/",  # Match .git directory anywhere in tree
    "**/.git/**",  # Match contents of .git directory anywhere in tree
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
    "__pycache__/**",
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
    "docs/_build/**",
    "**/docs/_build/**",
    "**/*.doctree",
    "**/searchindex.js",
    "**/objects.inv",
    "**/_static/**",
    "**/_sources/**",
    "**/CACHEDIR.TAG",
    "**/.buildinfo",
    "**/.buildinfo.bak",
    "**/genindex.html",
    "**/py-modindex.html",
    "**/search.html",
    "**/environment.pickle",
    "**/doctrees/**",
    "**/html/**",
    "**/fonts/**",
    "**/css/**",
    "**/js/**",
    
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
    "**/*.a",
    "**/*.AC",
    "**/*.AC0",
    "**/*.INF",
    "**/*.dat",
    "**/*.out",
    "**/*.in",
    "**/*.pdb",
    
    # Test Files
    "tests/**/__pycache__/**",
    "**/test_*.py[c,o]",
    "**/.pytest_cache/**",
    "**/pytest_cache/**",
    
    # Output Files
    "**/code_concat_output.md",
    
    # Specific Files
    "**/ANTECHAMBER_*.AC",
    "**/ANTECHAMBER_*.AC0",
    "**/ATOMTYPE.INF",
    "**/sqm.out",
    "**/leap.log",
    "**/timer.dat",
    "**/sqm.in",
    "**/build_polymer.in",
    "**/sqm.pdb"
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
    all_excludes = DEFAULT_EXCLUDES + (user_excludes or [])
    logging.debug(f"Checking directory: {dirpath} against patterns: {all_excludes}")
    
    # Convert to relative path for matching
    if os.path.isabs(dirpath):
        try:
            rel_path = os.path.relpath(dirpath, os.getcwd())
        except ValueError:
            rel_path = dirpath
    else:
        rel_path = dirpath
        
    # Check each exclude pattern
    for pattern in all_excludes:
        if matches_pattern(rel_path, pattern):
            logging.debug(f"Excluding directory {rel_path} due to pattern {pattern}")
            return True
    
    return False


def should_include_file(path_str: str, config: CodeConCatConfig) -> bool:
    """Determine if a file should be included based on patterns and configuration."""
    # Get all exclude patterns
    all_excludes = DEFAULT_EXCLUDES + (config.exclude_paths or [])
    logging.debug(f"Checking file: {path_str} against patterns: {all_excludes}")
    
    # Convert to relative path for matching
    if os.path.isabs(path_str):
        try:
            rel_path = os.path.relpath(path_str, os.getcwd())
        except ValueError:
            rel_path = path_str
    else:
        rel_path = path_str
        
    # Normalize path separators
    rel_path = rel_path.replace(os.sep, '/')
    
    # Check exclusions first
    for pattern in all_excludes:
        if matches_pattern(rel_path, pattern):
            logging.debug(f"Excluding file {rel_path} due to pattern {pattern}")
            return False
            
    # If we have includes, file must match at least one
    if config.include_languages:
        ext = os.path.splitext(path_str)[1].lower().lstrip(".")
        language_label = ext_map(ext, config)
        return language_label in config.include_languages
        
    return True


def matches_pattern(path_str: str, pattern: str) -> bool:
    """Match a path against a glob pattern, handling both relative and absolute paths."""
    # Convert absolute paths to relative for matching
    if os.path.isabs(path_str):
        try:
            path_str = os.path.relpath(path_str, os.getcwd())
        except ValueError:
            # If paths are on different drives, keep absolute path
            pass

    # Normalize path separators for consistent matching
    path_str = path_str.replace(os.sep, '/')
    pattern = pattern.replace(os.sep, '/')
    
    # Handle directory patterns
    if pattern.endswith('/**'):
        # For directory wildcard patterns, check if the path starts with the directory part
        dir_pattern = pattern[:-3]  # Remove '/**'
        return path_str == dir_pattern or path_str.startswith(dir_pattern + '/')
    elif os.path.isdir(path_str) and not path_str.endswith('/'):
        # For directories, ensure they end with / for matching
        path_str += '/'
        if not pattern.endswith('/'):
            pattern += '/'
    
    # Handle both glob patterns and direct matches
    return fnmatch.fnmatch(path_str, pattern)


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
