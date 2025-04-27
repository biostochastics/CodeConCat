import fnmatch
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Optional, List

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
    ".cache/",
    "**/.cache/",
    "**/.cache/**",
    "tmp/",
    "**/tmp/",
    "**/tmp/**",
    # Test Coverage
    "coverage/",
    "**/coverage/",
    "**/coverage/**",
    # Environment Files
    ".env",
    "**/.env",
    ".env.*",
    "**/.env.*",
    # Python specific
    "__pycache__/",
    "**/__pycache__/",
    "**/__pycache__/**",
    "*.pyc",
    "**/*.pyc",
    "*.pyo",
    "**/*.pyo",
    "*.pyd",
    "**/*.pyd",
    "*.egg-info/",
    "**/*.egg-info/",
    "**/*.egg-info/**",
    # Virtual environments - Simplified patterns
    "codeconcat_venv/**",
    "**/codeconcat_venv/**",
    "venv/**",
    "**/venv/**",
    ".venv/**",
    "**/.venv/**",
    "env/**",
    "**/env/**",
    "*env/**",
    "**/*env/**",  # Covers names like 'myenv', 'test_env' and subdirs
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
            patterns = [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]

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


def should_include_file(
    file_path: str,
    config: CodeConCatConfig,
    gitignore_spec: Optional[PathSpec] = None,
    default_exclude_spec: Optional[PathSpec] = None,
    config_exclude_spec: Optional[PathSpec] = None,
    config_include_spec: Optional[PathSpec] = None,
) -> Optional[str]:  # Return Optional[str] (language or None)
    """Determine if a file should be included based on various criteria.

    Args:
        file_path (str): The absolute path to the file.
        config (CodeConCatConfig): The configuration object.
        gitignore_spec (Optional[PathSpec]): The compiled gitignore patterns.
        default_exclude_spec (Optional[PathSpec]): The compiled default exclude patterns.
        config_exclude_spec (Optional[PathSpec]): The compiled config exclude patterns.
        config_include_spec (Optional[PathSpec]): The compiled config include patterns.

    Returns:
        Optional[str]: The determined language string if the file should be included, otherwise None.
    """
    # Ensure target_path exists for relative path calculation
    base_path = (
        config.target_path
        if config.target_path and os.path.isdir(config.target_path)
        else "."
    )
    try:
        rel_path = os.path.relpath(file_path, base_path)
    except ValueError as e:
        # Handle cases where file_path might not be under base_path (e.g., if target_path is a file)
        logger.warning(
            f"Could not determine relative path for {file_path} based on {base_path}: {e}. Using absolute path for matching."
        )
        # Use the full path for matching in this edge case. Pathspec handles it.
        rel_path = file_path

    norm_path = Path(rel_path).as_posix()  # Normalize path for matching
    if config.verbose:
        logger.debug(
            f"Checking file: {rel_path} (Normalized: {norm_path}, Full: {file_path})"
        )

    # --- Path Filtering --- #

    # 1. Check .gitignore (if spec exists and enabled)
    if config.use_gitignore and gitignore_spec and gitignore_spec.match_file(norm_path):
        if config.verbose:
            logger.debug(f"Excluded by .gitignore: {rel_path}")
        return None

    # 2. Check default excludes (if spec exists and enabled)
    if (
        config.use_default_excludes
        and default_exclude_spec
        and default_exclude_spec.match_file(norm_path)
    ):
        if config.verbose:
            logger.debug(f"Excluded by default excludes: {rel_path}")
        return None

    # 3. Check explicit excludes from config (if spec exists)
    if config_exclude_spec and config_exclude_spec.match_file(norm_path):
        if config.verbose:
            logger.debug(f"Excluded by config exclude_paths: {rel_path}")
        return None

    # 4. Check explicit includes from config (if spec exists)
    # If include paths are defined, the file MUST match one of them.
    if config_include_spec:
        if not config_include_spec.match_file(norm_path):
            if config.verbose:
                logger.debug(
                    f"Skipped: '{rel_path}' does not match any include_paths pattern."
                )
            return None
        else:
            if config.verbose:
                logger.debug(f"Included by config include_paths: {rel_path}")
            # Pass: Continue to language checks
    # else: # No include_paths means include all by default (subject to excludes)
    #     if config.verbose: logger.debug(f"Included by default (no include_paths specified): {rel_path}")

    # --- Language Determination and Filtering --- #
    language: Optional[str] = None
    # Try guesslang first if available and enabled (check config? maybe not needed here)
    if GUESSLANG_AVAILABLE:
        try:
            # Read content specifically for guesslang if not already read
            # TODO: Optimize - can we avoid reading twice?
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content_for_guess = f.read(5000)  # Read a chunk for detection
            language = get_language_guesslang(content_for_guess)
            if language:
                if config.verbose:
                    logger.debug(
                        f"Language detected by guesslang as '{language}' for {rel_path}"
                    )
        except Exception as e:
            if config.verbose:
                logger.debug(f"guesslang check failed for {rel_path}: {e}")
            language = None  # Ensure language is None if guesslang fails

    # Fallback to extension map if guesslang fails, is unavailable, or returns None/Unknown
    if not language or language.lower() == "unknown":
        filename = os.path.basename(file_path)
        # Use extension WITH the dot for lookup
        ext_with_dot = os.path.splitext(file_path)[1].lower()
        language = ext_map.get(filename.lower(), ext_map.get(ext_with_dot))
        if language:
            if config.verbose:
                logger.debug(
                    f"Using language '{language}' for {rel_path} based on extension/filename."
                )
        else:
            if config.verbose:
                logger.debug(
                    f"Could not determine language for {rel_path} using extension/filename."
                )
            # If include_paths was specified and matched, but language is unknown, maybe warn?
            # For now, if language is unknown, we don't include unless forced by config?
            # If we got here because include_paths matched, maybe default to 'unknown' language?
            # Let's return None for now if language is undetermined.
            return None

    # Ensure we have a language string
    if not language:
        if config.verbose:
            logger.debug(f"Final language determination failed for {rel_path}")
        return None

    # 5. Check include_languages from config
    if config.include_languages and language not in config.include_languages:
        if config.verbose:
            logger.debug(
                f"Excluded by include_languages: {rel_path} (lang: {language} not in {config.include_languages})"
            )
        return None

    # 6. Check exclude_languages from config
    if config.exclude_languages and language in config.exclude_languages:
        if config.verbose:
            logger.debug(
                f"Excluded by exclude_languages: {rel_path} (lang: {language} in {config.exclude_languages})"
            )
        return None

    # If we passed all checks, the file should be included
    if config.verbose:
        logger.debug(f"Final decision: Include {rel_path} (Language: {language})")
    return language  # Return the determined language string


def collect_local_files(
    root_path: str, config: CodeConCatConfig
) -> List[ParsedFileData]:
    """Walks a directory tree, identifies, reads, and collects data for code files.

    This function orchestrates the file collection process:
    1. Walks the directory structure starting from `root_path`.
    2. Determines if files/directories should be included based on:
       - .gitignore rules (if present).
       - Default exclusion patterns (e.g., node_modules, .git).
       - User-defined include/exclude patterns from the config.
       - Whether the file is binary.
    3. Determines the language of included files using `determine_language`.
    4. Reads the content of included text files using a ThreadPoolExecutor for efficiency.
    5. Returns a list of ParsedFileData objects, ready for the parsing stage.

    Args:
        root_path: The absolute path to the root directory to start scanning.
        config: The CodeConCatConfig object containing user settings and derived specs.

    Returns:
        A list of ParsedFileData objects, each containing the file path,
        determined language, and file content for files that passed all checks.
        Files that are skipped (binary, excluded, etc.) are not included.
    """
    logger.info(f"[CodeConCat] Collecting files from: {root_path}")
    parsed_files_data = []

    # --- Compile PathSpec objects --- #
    gitignore_spec = get_gitignore_spec(root_path) if config.use_gitignore else None
    default_exclude_spec = (
        PathSpec.from_lines(GitWildMatchPattern, DEFAULT_EXCLUDES)
        if config.use_default_excludes
        else None
    )
    # Handle None case for config paths
    config_exclude_patterns = config.exclude_paths or []
    config_include_patterns = config.include_paths or []
    # Compile only if patterns exist
    config_exclude_spec = (
        PathSpec.from_lines(GitWildMatchPattern, config_exclude_patterns)
        if config_exclude_patterns
        else None
    )
    config_include_spec = (
        PathSpec.from_lines(GitWildMatchPattern, config_include_patterns)
        if config_include_patterns
        else None
    )
    # --- End Compile PathSpec objects --- #

    # --- Handle case where root_path is a file --- #
    if os.path.isfile(root_path):
        if config.verbose:
            logger.debug(f"Target path is a file: {root_path}")
        # Pass compiled specs
        language = should_include_file(
            root_path,
            config,
            gitignore_spec,
            default_exclude_spec,
            config_exclude_spec,
            config_include_spec,
        )
        if language:
            try:
                result = process_file(root_path, config, language)
                if result:
                    parsed_files_data.append(result)
            except Exception as exc:
                logger.error(
                    f"[CodeConCat] Error processing single file {root_path}: {exc}"
                )
        else:
            logger.debug(f"Single file '{root_path}' excluded based on criteria.")

    # --- Handle case where root_path is a directory --- #
    logger.info(f"[CodeConCat] Scanning directory: {root_path}")
    all_files = []
    # Use os.walk to recursively find all files
    for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
        # TODO: Consider pruning dirnames based on specs for efficiency
        # dirnames[:] = [d for d in dirnames if not should_exclude_dir(...)]

        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            # Basic check: is it a symbolic link? Skip links for now.
            # Consider adding config option to follow links if needed.
            if not os.path.islink(file_path):
                all_files.append(os.path.abspath(file_path))

    logger.info(
        f"[CodeConCat] Found {len(all_files)} potential files. Filtering and processing..."
    )

    # Use ThreadPoolExecutor for parallel processing
    parsed_files_data = []
    max_workers = (
        config.max_workers
        if config.max_workers and config.max_workers > 0
        else min(32, (os.cpu_count() or 1) + 4)
    )
    if (
        config.verbose or max_workers != config.max_workers
    ):  # Log if verbose or if value was adjusted
        logger.info(f"Using {max_workers} workers for parallel processing.")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {}
        for file_path in all_files:
            # Pass the compiled specs to should_include_file
            language = should_include_file(
                file_path,
                config,
                gitignore_spec,
                default_exclude_spec,
                config_exclude_spec,
                config_include_spec,
            )
            if language:  # If language is returned, file should be included
                # Submit process_file with the determined language
                future = executor.submit(process_file, file_path, config, language)
                future_to_file[future] = file_path
            # else: file is excluded, do nothing

        # Collect results as they complete
        # Use tqdm for progress bar if enabled
        iterable = as_completed(future_to_file)
        if not config.disable_progress_bar:
            iterable = tqdm(
                iterable,
                total=len(future_to_file),
                desc="Collecting files",
                unit="file",
            )

        for future in iterable:
            file_path = future_to_file[future]
            try:
                result = future.result()
                if result:
                    parsed_files_data.append(result)
            except Exception as exc:
                logger.error(f"[CodeConCat] Error processing {file_path}: {exc}")
    return parsed_files_data


# Function to process a single file (called by the executor)
def process_file(
    file_path: str, config: CodeConCatConfig, language: str
) -> Optional[ParsedFileData]:
    """Process a single file, reading its content. Assumes file should be included.
    Args:
        file_path (str): Absolute path to the file.
        config (CodeConCatConfig): Configuration object.
        language (str): The language determined by should_include_file.
    Returns:
        Optional[ParsedFileData]: Data object if successful, None otherwise.
    """
    try:
        # Log before binary check
        logger.debug(f"[process_file] Checking if binary: {file_path}")
        is_bin = is_binary_file(file_path)
        # Log after binary check
        logger.debug(f"[process_file] Binary check result for {file_path}: {is_bin}")
        if is_bin:
            # is_binary_file now logs internally
            return None

        # Log before open
        logger.debug(f"[process_file] Attempting to open for read: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            # Log after open, before read
            logger.debug(f"[process_file] Opened {file_path}, attempting read.")
            content = f.read()
            # Log after read
            logger.debug(f"[process_file] Read successful for: {file_path}")

        # Language is now passed as an argument, no need to look it up here
        # ext = os.path.splitext(file_path)[1].lstrip(".")
        # filename = os.path.basename(file_path)
        # Use dictionary access on the imported ext_map
        # language = ext_map.get(filename.lower(), ext_map.get(ext.lower()))

        logger.debug(f"[CodeConCat] Processed file: {file_path} ({language})")
        return ParsedFileData(
            file_path=file_path,
            language=language,  # Use the passed language
            content=content,
            declarations=[],  # We'll fill this in during parsing phase
        )
    except UnicodeDecodeError:
        logger.debug(f"[CodeConCat] Skipping non-text file: {file_path}")
        return None
    except Exception as e:
        logger.error(f"[CodeConCat] Error processing {file_path}: {str(e)}")
        return None


def should_skip_dir(
    dirpath: str, config: CodeConCatConfig
) -> bool:  # Accept config object
    """Check if a directory should be skipped based on exclude patterns.

    Compares the directory path against the combined list of default excludes
    and user-configured excludes. Uses `matches_pattern` for matching.

    Args:
        dirpath: The absolute path to the directory being considered.
        config: The CodeConCatConfig object containing exclude_paths and target_path.

    Returns:
        True if the directory matches any exclude pattern, False otherwise.
    """
    all_excludes = DEFAULT_EXCLUDES + (
        config.exclude_paths or []
    )  # Access excludes from config
    logger.debug(f"Checking directory: {dirpath} against patterns: {all_excludes}")

    # Convert to relative path for matching
    if os.path.isabs(dirpath):
        try:
            rel_path = os.path.relpath(
                dirpath, config.target_path
            )  # Use config.target_path
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
        logger.debug(f"[is_binary_file] Attempting to open: {file_path}")
        with open(file_path, "r", encoding="utf-8", errors="replace") as check_file:
            logger.debug(f"[is_binary_file] Opened {file_path}, attempting readline.")
            check_file.readline()
            logger.debug(f"[is_binary_file] Readline successful for: {file_path}")
            return False
    except UnicodeDecodeError:
        logger.debug(
            f"[is_binary_file] UnicodeDecodeError for: {file_path} (Likely binary)"
        )
        return True
    except Exception as e:
        logger.error(f"[is_binary_file] Error checking file {file_path}: {str(e)}")
        return False  # Assume not binary on error? Or True? Let's default to False.
