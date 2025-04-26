import fnmatch
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from tqdm import tqdm

from codeconcat.base_types import CodeConCatConfig, ParsedFileData
from codeconcat.language_map import get_language_guesslang, GUESSLANG_AVAILABLE, ext_map

logger = logging.getLogger(__name__)
# Do not set up handlers or formatters here; let the CLI configure logging.
DEFAULT_EXCLUDES = [
    # Version Control
    ".git/",  # Match the .git directory itself
    ".git/**",  # Match contents of .git directory
    "**/.git/",  # Match .git directory anywhere in tree
    "**/.git/**",  # Match contents of .git directory anywhere in tree
    ".gitignore",
    "**/.gitignore",
    # R Specific
    ".Rcheck/",
    "**/.Rcheck/",
    "**/.Rcheck/**",
    ".Rhistory",
    "**/.Rhistory",
    ".RData",
    "**/.RData",
    # OS and Editor Files
    ".DS_Store",
    "**/.DS_Store",
    "Thumbs.db",
    "**/*.swp",
    "**/*.swo",
    ".idea/**",
    ".vscode/**",
    # Configuration Files
    "*.yml",
    "./*.yml",
    "**/*.yml",
    "*.yaml",
    "./*.yaml",
    "**/*.yaml",
    ".codeconcat.yml",
    # Build and Dependencies
    "node_modules/",
    "**/node_modules/",
    "**/node_modules/**",
    "build/",
    "**/build/",
    "**/build/**",
    "dist/",
    "**/dist/",
    "**/dist/**",
    # Next.js specific
    ".next/",
    "**/.next/",
    "**/.next/**",
    "**/static/chunks/**",
    "**/server/chunks/**",
    "**/BUILD_ID",
    "**/trace",
    "**/*.map",
    "**/webpack-*.js",
    "**/manifest*.js",
    "**/server-reference-manifest.js",
    "**/middleware-manifest.js",
    "**/client-reference-manifest.js",
    "**/webpack-runtime.js",
    "**/server-reference-manifest.js",
    "**/middleware-build-manifest.js",
    "**/middleware-react-loadable-manifest.js",
    "**/server-reference-manifest.js",
    "**/interception-route-rewrite-manifest.js",
    "**/next-font-manifest.js",
    "**/polyfills-*.js",
    "**/main-*.js",
    "**/framework-*.js",
    # Package Files
    "package-lock.json",
    "**/package-lock.json",
    "yarn.lock",
    "**/yarn.lock",
    "pnpm-lock.yaml",
    "**/pnpm-lock.yaml",
    # Cache and Temporary Files
    ".cache/", "**/.cache/", "**/.cache/**",
    "tmp/", "**/tmp/", "**/tmp/**",
    # Test Coverage
    "coverage/", "**/coverage/", "**/coverage/**",
    # Environment Files
    ".env", "**/.env", ".env.*", "**/.env.*",
    # Python specific
    "__pycache__/", "**/__pycache__/", "**/__pycache__/**",
    "*.pyc", "**/*.pyc",
    "*.pyo", "**/*.pyo",
    "*.pyd", "**/*.pyd",
    "*.egg-info/", "**/*.egg-info/", "**/*.egg-info/**",
    # Virtual environments - Simplified patterns
    "codeconcat_venv/**", "**/codeconcat_venv/**",
    "venv/**", "**/venv/**",
    ".venv/**", "**/.venv/**",
    "env/**", "**/env/**",
    "*env/**", "**/*env/**", # Covers names like 'myenv', 'test_env' and subdirs
    "**/.*",  # Ignore all files/directories starting with a dot
]


def get_gitignore_spec(root_path: str) -> PathSpec:
    """
    Read .gitignore file and create a PathSpec for matching.

    Args:
        root_path: Root directory to search for .gitignore

    Returns:
        PathSpec object for matching paths against .gitignore patterns
    """
    gitignore_path = os.path.join(root_path, ".gitignore")
    patterns = []

    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            patterns = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    # Add common patterns that should always be ignored
    patterns.extend(
        [
            "**/__pycache__/**",
            "**/*.pyc",
            "**/.git/**",
            "**/node_modules/**",
            "**/.pytest_cache/**",
            "**/.coverage",
            "**/build/**",
            "**/dist/**",
            "**/*.egg-info/**",
        ]
    )

    return PathSpec.from_lines(GitWildMatchPattern, patterns)


# @lru_cache(maxsize=1024) # Cache results for performance -- REMOVED due to unhashable config
def should_include_file(
    file_path: str, config: CodeConCatConfig, gitignore_spec: Optional[PathSpec] = None
) -> Optional[str]: # Return Optional[str] (language or None)
    """Determine if a file should be included based on various criteria.

    Args:
        file_path (str): The absolute path to the file.
        config (CodeConCatConfig): The configuration object.
        gitignore_spec (Optional[PathSpec]): The compiled gitignore patterns.

    Returns:
        Optional[str]: The determined language string if the file should be included, otherwise None.
    """
    rel_path = os.path.relpath(file_path, config.target_path or ".")
    norm_path = Path(rel_path).as_posix() # Normalize path for matching
    logger.debug(f"Checking file: {rel_path} (Full: {file_path})")

    # 1. Check .gitignore
    if gitignore_spec and gitignore_spec.match_file(norm_path):
        logger.debug(f"Excluded by .gitignore: {rel_path}")
        return None

    # 2. Check default excludes (always applied)
    matching_default_exclude = match_path_against_patterns(norm_path, DEFAULT_EXCLUDES)
    if matching_default_exclude:
        logger.debug(f"Excluded by default excludes pattern '{matching_default_exclude}' matching path '{norm_path}'")
        return None

    # 3. Check explicit excludes from config
    if config.exclude_paths and match_path_against_patterns(norm_path, config.exclude_paths):
        logger.debug(f"Excluded by config exclude_paths: {rel_path}")
        return None

    # 4. Check explicit includes from config
    # If include_paths is defined, a file *must* match at least one pattern
    if config.include_paths:
        if not match_path_against_patterns(norm_path, config.include_paths):
            logger.debug(
                f"Skipped: '{rel_path}' does not match any include_paths pattern {config.include_paths}"
            )
            return None
        else:
             logger.debug(f"Included by include_paths: {rel_path}")
             # Continue to language checks even if included by path
    # else: # No include_paths means include all by default (subject to excludes)
    #     logger.debug(f"Included by default (no include_paths specified): {rel_path}")

    # --- Language Determination and Filtering ---
    language: Optional[str] = None
    # Try guesslang first if available and enabled (check config? maybe not needed here)
    if GUESSLANG_AVAILABLE:
        try:
            # Read content specifically for guesslang if not already read
            # TODO: Optimize - can we avoid reading twice?
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content_for_guess = f.read(5000) # Read a chunk for detection
            language = get_language_guesslang(content_for_guess)
            if language:
                logger.debug(f"Language detected by guesslang as '{language}' for {rel_path}")
        except Exception as e:
            logger.debug(f"guesslang check failed for {rel_path}: {e}")
            language = None # Ensure language is None if guesslang fails

    # Fallback to extension map if guesslang fails, is unavailable, or returns None/Unknown
    if not language or language.lower() == 'unknown':
        filename = os.path.basename(file_path)
        # Use extension WITH the dot for lookup
        ext_with_dot = os.path.splitext(file_path)[1].lower()
        language = ext_map.get(filename.lower(), ext_map.get(ext_with_dot))
        if language:
            logger.debug(f"Using language '{language}' for {rel_path} based on extension/filename.")
        else:
             logger.debug(f"Could not determine language for {rel_path} using extension/filename.")
             # If include_paths was specified and matched, but language is unknown, maybe warn?
             # For now, if language is unknown, we don't include unless forced by config?
             # If we got here because include_paths matched, maybe default to 'unknown' language?
             # Let's return None for now if language is undetermined.
             return None

    # Ensure we have a language string
    if not language:
        logger.debug(f"Final language determination failed for {rel_path}")
        return None

    # 5. Check include_languages from config
    if config.include_languages and language not in config.include_languages:
        logger.debug(
            f"Excluded by include_languages: {rel_path} (lang: {language} not in {config.include_languages})"
        )
        return None

    # 6. Check exclude_languages from config
    if config.exclude_languages and language in config.exclude_languages:
        logger.debug(
            f"Excluded by exclude_languages: {rel_path} (lang: {language} in {config.exclude_languages})"
        )
        return None

    # If we passed all checks, the file should be included
    logger.debug(f"Final decision: Include {rel_path} (Language: {language})")
    return language # Return the determined language string


def collect_local_files(root_path: str, config: CodeConCatConfig, show_progress: bool = False):
    """Collect and read files from the local file system based on configuration."""
    logger.info(f"[CodeConCat] Collecting files from: {root_path}")
    all_files = [] # Collect all potential file paths first
    for root, dirs, files in os.walk(root_path, topdown=True):
        # Filter directories based on ignore patterns
        # TODO: Implement should_skip_dir logic similar to generate_folder_tree
        # dirs[:] = [d for d in dirs if not should_skip_dir(os.path.join(root, d), config)]

        for file in files:
            all_files.append(os.path.join(root, file))

    parsed_files_data = []
    gitignore_spec = get_gitignore_spec(root_path)

    # Determine the number of workers
    max_workers = config.max_workers if config.max_workers else os.cpu_count()
    logger.debug(f"Using {max_workers} workers for file processing.")

    # Process files in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit tasks: Check should_include_file first
        future_to_file = {}
        for file_path in all_files:
            # Directly call should_include_file here
            language = should_include_file(file_path, config, gitignore_spec)
            if language: # If language is returned, file should be included
                # Submit process_file with the determined language
                future = executor.submit(process_file, file_path, config, language)
                future_to_file[future] = file_path
            # else: file is excluded, do nothing

        # Collect results as they complete
        # Use tqdm for progress bar if enabled
        iterable = as_completed(future_to_file)
        if show_progress:
            iterable = tqdm(iterable, total=len(future_to_file), desc="Collecting files", unit="file")

        for future in iterable:
            file_path = future_to_file[future]
            try:
                result = future.result()
                if result:
                    parsed_files_data.append(result)
            except Exception as exc:
                logger.error(f"[CodeConCat] Error processing {file_path}: {exc}")

    if not parsed_files_data:
        logger.warning("[CodeConCat] No files found matching the criteria")

    return parsed_files_data


# Function to process a single file (called by the executor)
def process_file(file_path: str, config: CodeConCatConfig, language: str) -> Optional[ParsedFileData]:
    """Process a single file, reading its content. Assumes file should be included.
    Args:
        file_path (str): Absolute path to the file.
        config (CodeConCatConfig): Configuration object.
        language (str): The language determined by should_include_file.
    Returns:
        Optional[ParsedFileData]: Data object if successful, None otherwise.
    """
    try:
        # should_include_file check is done before submitting the task
        # if not language: # This check is redundant now
        #     return None

        if is_binary_file(file_path):
            logger.debug(f"[CodeConCat] Skipping binary file: {file_path}")
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Language is now passed as an argument, no need to look it up here
        # ext = os.path.splitext(file_path)[1].lstrip(".")
        # filename = os.path.basename(file_path)
        # Use dictionary access on the imported ext_map
        # language = ext_map.get(filename.lower(), ext_map.get(ext.lower()))

        logger.debug(f"[CodeConCat] Processed file: {file_path} ({language})")
        return ParsedFileData(
            file_path=file_path,
            language=language, # Use the passed language
            content=content,
            declarations=[],  # We'll fill this in during parsing phase
        )
    except UnicodeDecodeError:
        logger.debug(f"[CodeConCat] Skipping non-text file: {file_path}")
        return None
    except Exception as e:
        logger.error(f"[CodeConCat] Error processing {file_path}: {str(e)}")
        return None


def should_skip_dir(dirpath: str, config: CodeConCatConfig) -> bool:  # Accept config object
    """Check if a directory should be skipped based on exclude patterns."""
    all_excludes = DEFAULT_EXCLUDES + (config.exclude_paths or [])  # Access excludes from config
    logger.debug(f"Checking directory: {dirpath} against patterns: {all_excludes}")

    # Convert to relative path for matching
    if os.path.isabs(dirpath):
        try:
            rel_path = os.path.relpath(dirpath, config.target_path)  # Use config.target_path
        except ValueError:
            # Handle cases where dirpath is not under target_path (e.g., different drive on Windows)
            rel_path = dirpath
    else:
        rel_path = dirpath
    rel_path = rel_path.replace(os.sep, "/").strip("/")

    for pattern in all_excludes:
        if matches_pattern(rel_path, pattern):
            logger.debug(f"Excluding directory {rel_path} due to pattern {pattern}")
            return True
    return False


import string

_cache = {}


def matches_pattern(path_str: str, pattern: str) -> bool:
    """Match a path against a glob pattern using fnmatch.translate for correctness, with caching."""
    norm_path = path_str.replace(os.sep, "/")
    norm_pattern = pattern.replace(os.sep, "/")
    if norm_pattern not in _cache:
        _cache[norm_pattern] = re.compile(fnmatch.translate(norm_pattern))
    return bool(_cache[norm_pattern].match(norm_path))


def is_binary_file(file_path: str) -> bool:
    """Check if a file is likely to be binary."""
    # Fast path: check by extension
    binary_exts = {
        "png",
        "jpg",
        "jpeg",
        "gif",
        "ico",
        "webp",
        "woff",
        "woff2",
        "ttf",
        "eot",
        "otf",
        "pdf",
        "doc",
        "docx",
        "xls",
        "xlsx",
        "zip",
        "tar",
        "gz",
        "tgz",
        "7z",
        "rar",
        "mp3",
        "mp4",
        "wav",
        "avi",
        "mov",
    }
    ext = os.path.splitext(file_path)[1].lstrip(".").lower()
    if ext in binary_exts:
        return True
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as check_file:
            check_file.readline()
            return False
    except UnicodeDecodeError:
        return True


def match_path_against_patterns(path: str, patterns: List[str]) -> Optional[str]:
    """Check if a path matches any of the given patterns.

    Args:
        path (str): The path string to check.
        patterns (List[str]): A list of pattern strings.

    Returns:
        Optional[str]: The first pattern that matches the path, or None if no pattern matches.
    """
    for pattern in patterns:
        if matches_pattern(path, pattern):
            return pattern # Return the pattern that matched
    return None # Return None if no match
