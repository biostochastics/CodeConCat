import fnmatch
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional

from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from tqdm import tqdm

from codeconcat.base_types import CodeConCatConfig, ParsedFileData
from codeconcat.language_map import GUESSLANG_AVAILABLE, ext_map, get_language_guesslang

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
    
    # Virtual environments - Comprehensive patterns
    # Match any venv directory or subdirectory
    "venv/",
    "venv/**",
    "**/venv/",
    "**/venv/**",
    "*venv/",
    "*venv/**",
    "**/*venv/",
    "**/*venv/**",  # More aggressive pattern to match any directory with 'venv' in the name
    
    # Common environment directory names
    ".venv/",
    ".venv/**",
    "**/.venv/",
    "**/.venv/**",
    "env/",
    "env/**",
    "**/env/",
    "**/env/**",
    "*env/",
    "*env/**",
    "**/*env/",
    "**/*env/**",
    
    # Specific virtual envs in this project
    "codeconcat_venv/",
    "codeconcat_venv/**",
    "**/codeconcat_venv/",
    "**/codeconcat_venv/**",
    "venv_py312/",
    "venv_py312/**",
    "**/venv_py312/",
    "**/venv_py312/**",
    
    # Exclude site-packages entirely
    "**/site-packages/",
    "**/site-packages/**",
    
    # Hidden files and directories
    "**/.*",       # All hidden files and directories
    "**/.*/",      # All hidden directories
    "**/.*/***",   # Contents of hidden directories
    
    # Test directories
    "tests/",      # Root level tests directory
    "**/tests/",   # Tests directory anywhere in tree
    "**/tests/**", # Contents of tests directories
    "**/test/",    # Test directory (singular)
    "**/test/**",  # Contents of test directories
    
    # Common large directories
    "**/libs/**",
    "**/vendor/**",
    "**/third_party/**"
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

    # Check if the file is binary (we only want text files)
    if is_binary_file(file_path):
        if config.verbose:
            logger.debug(f"Excluded binary file: {rel_path}")
        return None

    # If we passed all checks, the file should be included
    if config.verbose:
        logger.debug(f"Final decision: Include {rel_path} (Language: {language})")
    return language  # Return the determined language string


def collect_local_files(
    root_path: str, config: CodeConCatConfig
) -> List[ParsedFileData]:
    """Walks a directory tree or processes a single file, identifies, reads, and collects data for code files.

    This function orchestrates the file collection process:
    1. Checks if `root_path` is a file or directory.
    2. If it's a file, checks if it should be included and processes it directly.
    3. If it's a directory, walks the directory structure starting from `root_path`.
    4. Determines if files/directories should be included based on:
       - .gitignore rules (if present).
       - Default exclusion patterns (e.g., node_modules, .git).
       - User-defined include/exclude patterns from the config.
       - Whether the file is binary.
    5. Determines the language of included files using `determine_language`.
    6. Reads the content of included text files using a ThreadPoolExecutor for efficiency (only for directories).
    7. Returns a list of ParsedFileData objects, ready for the parsing stage.

    Args:
        root_path: The absolute path to the root directory or file to process.
        config: The CodeConCatConfig object containing user settings and derived specs.

    Returns:
        A list of ParsedFileData objects, each containing the file path,
        determined language, and file content for files that passed all checks.
        Files that are skipped (binary, excluded, etc.) are not included.
    """
    logger.info(f"[CodeConCat] Collecting files from target: {root_path}")
    parsed_files_data: List[ParsedFileData] = []

    # --- Compile PathSpec objects --- #
    # (These are needed for both file and directory cases)
    gitignore_spec = get_gitignore_spec(root_path if os.path.isdir(root_path) else os.path.dirname(root_path)) if config.use_gitignore else None
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
            gitignore_spec, # May not be strictly needed but passed for consistency
            default_exclude_spec,
            config_exclude_spec,
            config_include_spec,
        )
        if language:
            try:
                # Process the single file directly
                result = process_file(root_path, config, language)
                if result:
                    parsed_files_data.append(result)
                    logger.info(f"Successfully processed single file: {root_path}")
                else:
                    logger.warning(f"Processing single file '{root_path}' returned no data.")
            except Exception as exc:
                logger.error(
                    f"[CodeConCat] Error processing single file {root_path}: {exc}"
                )
        else:
            # Log exclusion reason if verbose
            if config.verbose:
                _log_exclusion_reason(
                    root_path,
                    config,
                    gitignore_spec,
                    default_exclude_spec,
                    config_exclude_spec,
                    config_include_spec,
                )
            else:
                 logger.info(f"Single file '{root_path}' excluded based on criteria.")

        return parsed_files_data # Return immediately after processing the single file

    # --- Handle case where root_path is a directory --- #
    elif os.path.isdir(root_path):
        logger.info(f"[CodeConCat] Scanning directory: {root_path}")
        all_files = []
        # Use os.walk to recursively find all files
        for dirpath, dirnames, filenames in os.walk(root_path, topdown=True):
                    # Filter dirnames based on exclusion rules (efficiency)
            # Create paths relative to root_path for matching
            relative_dirpath = os.path.relpath(dirpath, root_path) 
            
            # Save original dirnames for logging
            original_dirnames = dirnames.copy()
            
            # Enhanced list of directories to always skip
            # These are checked first for performance before more complex pattern matching
            skip_dirs = [
                # Common cache and build directories
                '__pycache__', '.git', 'node_modules', '.pytest_cache', 'build', 'dist',
                # IDE and editor directories
                '.idea', '.vscode',
                # Virtual environments - by exact name
                'venv', '.venv', 'env', 'codeconcat_venv', 'venv_py312',
                # Common lib directories that are typically large
                'site-packages', 'libs', 'vendor', 'third_party'
            ]
            
            # Filter directories by name first (fast check)
            filtered_dirs = []
            for d in dirnames:
                # Skip if in the explicit skip list
                if d in skip_dirs:
                    continue
                    
                # Skip if starts with dot or ends with common patterns
                if d.startswith('.') or 'venv' in d.lower() or 'env' in d.lower():
                    continue
                    
                # Skip directories that match common virtual environment patterns
                if any(pattern in d.lower() for pattern in ['env', 'venv', 'virtualenv', 'pyenv']):
                    continue
                    
                # For remaining directories, check complex pattern exclusions
                if not is_excluded(
                    os.path.join(relative_dirpath, d) + "/", # Add '/' for directory match
                    gitignore_spec,
                    default_exclude_spec,
                    config_exclude_spec,
                    None,  # Don't check include_spec for directories - we'll check the files within them
                    config,
                    is_dir=True
                ):
                    filtered_dirs.append(d)
                    
            # Update dirnames in-place with our filtered list
            dirnames[:] = filtered_dirs
            # Log pruned directories if verbose
            if config.verbose:
                pruned_dirs = set(original_dirnames) - set(dirnames)
                for pruned in pruned_dirs:
                     logger.debug(f"Pruning excluded directory: {os.path.join(dirpath, pruned)}")

            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                # Basic check: is it a symbolic link? Skip links for now.
                if not os.path.islink(file_path):
                    # Check if the file itself should be included before adding
                    # Pass compiled specs here
                    if should_include_file(
                        file_path,
                        config,
                        gitignore_spec,
                        default_exclude_spec,
                        config_exclude_spec,
                        config_include_spec,
                    ):
                        all_files.append(os.path.abspath(file_path))
                    # Log exclusion if verbose
                    elif config.verbose:
                         _log_exclusion_reason(
                            file_path,
                            config,
                            gitignore_spec,
                            default_exclude_spec,
                            config_exclude_spec,
                            config_include_spec,
                        )


        logger.info(
            f"[CodeConCat] Found {len(all_files)} files matching inclusion criteria. Processing..."
        )

        if not all_files:
            logger.warning("No files found to process in the specified directory after filtering.")
            return [] # Return empty list if no files are left

        # Use ThreadPoolExecutor for parallel processing
        # This part is only for directory scanning
        parsed_files_data = [] # Initialize list for directory results
        max_workers = (
            config.max_workers
            if config.max_workers and config.max_workers > 0
            else min(32, (os.cpu_count() or 1) + 4)
        )
        if (
            config.verbose or max_workers != config.max_workers
        ):  # Log if verbose or if value was adjusted
            logger.info(f"Using {max_workers} workers for parallel processing.")

        # Set a timeout for each file processing task
        timeout_seconds = 30  # Timeout after 30 seconds per file
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Determine language *before* submitting to executor to avoid redundant checks
            future_to_file_lang = {}
            for file_path in all_files:
                # Skip any files that are too large (early filter to prevent hangs)
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > 20 * 1024 * 1024:  # Skip files larger than 20MB
                        logger.warning(f"Skipping large file ({file_size/1024/1024:.2f}MB): {file_path}")
                        continue
                except Exception as e:
                    logger.error(f"Error checking file size: {file_path}: {e}")
                
                # We already filtered in the walk, but let's re-determine language for process_file
                from codeconcat.language_map import ext_map, get_language_guesslang
                lang = should_include_file(file_path, config)
                if lang: # Should always be true if it made it to all_files
                    future = executor.submit(process_file, file_path, config, lang)
                    future_to_file_lang[future] = (file_path, lang)
                else:
                    # This case should ideally not happen due to pre-filtering
                    logger.warning(f"File {file_path} passed pre-filter but failed language determination.")

            # Import the timeout utilities
            import concurrent.futures
            from concurrent.futures import TimeoutError
            
            # Process results as they complete with timeouts
            completed = 0
            total = len(future_to_file_lang)
            
            # Create progress bar
            with tqdm(
                total=total,
                desc="Processing files",
                unit="file",
                disable=config.disable_progress_bar,
            ) as progress_bar:
                # Process each future with a timeout
                for future in concurrent.futures.as_completed(future_to_file_lang):
                    file_path, language = future_to_file_lang[future]
                    try:
                        # Apply timeout to prevent hanging on any single file
                        result = future.result(timeout=timeout_seconds)
                        if result:
                            parsed_files_data.append(result)
                        # else: File processing returned None
                    except TimeoutError:
                        logger.warning(f"[CodeConCat] Timeout processing file {file_path} after {timeout_seconds}s")
                    except Exception as exc:
                        logger.error(f"[CodeConCat] Error processing file {file_path} in worker: {exc}")
                    finally:
                        # Always update progress regardless of success or failure
                        completed += 1
                        progress_bar.update(1)
                        
                        # Periodically log progress
                        if completed % 50 == 0 or completed == total:
                            logger.info(f"Processed {completed}/{total} files ({completed/total*100:.1f}%)")
        return parsed_files_data # Return results from directory scan

    # --- Handle case where root_path is neither file nor directory --- #
    else:
        logger.error(f"Target path '{root_path}' is not a valid file or directory.")
        return [] # Return empty list for invalid path


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


def determine_language(file_path: str, config: CodeConCatConfig) -> Optional[str]:
    """Determine the language of a file based on extension or content.
    
    This function extracts the language detection logic from should_include_file
    to make it accessible for other functions.
    
    Args:
        file_path: Path to the file to determine language for
        config: Configuration object
        
    Returns:
        The language as a string if detected, None otherwise
    """
    from codeconcat.language_map import ext_map, get_language_guesslang
    
    # Try using guesslang if available and enabled
    language = None
    if GUESSLANG_AVAILABLE and config.parser_engine == "tree_sitter":
        try:
            language = get_language_guesslang(file_path)
            if language and language.lower() != "unknown" and config.verbose:
                logger.debug(f"Using language '{language}' for {file_path} based on content analysis.")
        except Exception as e:
            if config.verbose:
                logger.debug(f"guesslang check failed for {file_path}: {e}")
            language = None  # Ensure language is None if guesslang fails

    # Fallback to extension map if guesslang fails, is unavailable, or returns None/Unknown
    if not language or language.lower() == "unknown":
        filename = os.path.basename(file_path)
        # Use extension WITH the dot for lookup
        ext_with_dot = os.path.splitext(file_path)[1].lower()
        language = ext_map.get(filename.lower(), ext_map.get(ext_with_dot))
        if language and config.verbose:
            logger.debug(f"Using language '{language}' for {file_path} based on extension/filename.")
        elif config.verbose:
            logger.debug(f"Could not determine language for {file_path} using extension/filename.")
            
    return language


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
        # Images
        "png", "jpg", "jpeg", "gif", "ico", "webp", "bmp", "tiff", "tif", "svg",
        # Fonts
        "woff", "woff2", "ttf", "eot", "otf",
        # Documents
        "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
        # Archives
        "zip", "tar", "gz", "tgz", "7z", "rar", "bz2", "xz",
        # Audio/Video
        "mp3", "mp4", "wav", "avi", "mov", "flac", "ogg", "mkv", "wmv", "mpg", "mpeg",
        # Other binary formats
        "exe", "dll", "so", "dylib", "bin", "dat", "db", "sqlite", "pyc", "pyo", "pyd",
        # Python package files
        "whl", "egg", 
        # JS/Node.js packaging
        "tsbuildinfo", "min.js", "bundle.js",
    }
    ext = os.path.splitext(file_path)[1].lstrip(".").lower()
    if ext in binary_exts:
        logger.debug(f"[is_binary_file] Extension match for binary: {file_path} (ext: {ext})")
        return True
        
    # Path-based checks for known binary files or large text files we want to skip
    file_name = os.path.basename(file_path).lower()
    path_lower = file_path.lower()
    
    # Skip lock files, minified files, and known large generated files
    skip_patterns = [
        "lock.json", "package-lock", "yarn.lock", "pnpm-lock", 
        ".min.js", ".bundle.js", "vendor.js", "polyfill", 
        "compiled", "generated", "build/", "dist/"
    ]
    if any(pattern in path_lower for pattern in skip_patterns):
        logger.debug(f"[is_binary_file] Path pattern match for binary/skip: {file_path}")
        return True
    
    # Check file size before opening - skip very large files
    try:
        file_size = os.path.getsize(file_path)
        # Skip files larger than 5MB
        if file_size > 5 * 1024 * 1024:  
            logger.debug(f"[is_binary_file] File too large (>{file_size/1024/1024:.2f}MB): {file_path}")
            return True
    except Exception as e:
        logger.error(f"[is_binary_file] Error checking file size for {file_path}: {str(e)}")
    
    try:
        # First, quick check with binary read for null bytes
        with open(file_path, "rb") as f:
            # Read just the first few KB to detect binary content
            sample = f.read(4096)
            if b'\0' in sample:  # Null bytes are a good indicator of binary content
                logger.debug(f"[is_binary_file] Binary content detected in: {file_path}")
                return True
                
            # Additional binary indicators
            # Check for high concentration of non-ASCII characters
            non_ascii_count = sum(1 for b in sample if b > 127)
            if non_ascii_count > len(sample) * 0.3:  # More than 30% non-ASCII
                logger.debug(f"[is_binary_file] High non-ASCII content in: {file_path}")
                return True
            
        # If passes binary checks, verify as text with a readline
        with open(file_path, "r", encoding="utf-8", errors="replace") as check_file:
            check_file.readline()
            return False
    except UnicodeDecodeError:
        logger.debug(f"[is_binary_file] UnicodeDecodeError for: {file_path} (Likely binary)")
        return True
    except Exception as e:
        logger.error(f"[is_binary_file] Error checking file {file_path}: {str(e)}")
        return False  # Assume not binary on error

def is_excluded(
    path: str,
    gitignore_spec: Optional[PathSpec],
    default_exclude_spec: Optional[PathSpec],
    config_exclude_spec: Optional[PathSpec],
    config_include_spec: Optional[PathSpec],
    config: CodeConCatConfig, # Add config here
    is_dir: bool = False,
) -> bool:
    """Check if a path should be excluded based on various criteria.

    Args:
        path (str): The path to check.
        gitignore_spec (Optional[PathSpec]): The compiled gitignore patterns.
        default_exclude_spec (Optional[PathSpec]): The compiled default exclude patterns.
        config_exclude_spec (Optional[PathSpec]): The compiled config exclude patterns.
        config_include_spec (Optional[PathSpec]): The compiled config include patterns.
        config (CodeConCatConfig): The configuration object.
        is_dir (bool): Whether the path is a directory. Defaults to False.

    Returns:
        bool: True if the path should be excluded, False otherwise.
    """
    # Check .gitignore (if spec exists and enabled)
    if gitignore_spec and gitignore_spec.match_file(path):
        return True

    # Check default excludes (if spec exists and enabled)
    if default_exclude_spec and default_exclude_spec.match_file(path):
        return True

    # Check explicit excludes from config (if spec exists)
    if config_exclude_spec and config_exclude_spec.match_file(path):
        return True

    # If include paths are defined, the file MUST match one of them.
    if config_include_spec and not config_include_spec.match_file(path):
        return True

    # If it's a directory, check if it should be excluded
    if is_dir and should_skip_dir(path, config):
        return True

    return False

def _log_exclusion_reason(
    file_path: str,
    config: CodeConCatConfig,
    gitignore_spec: Optional[PathSpec],
    default_exclude_spec: Optional[PathSpec],
    config_exclude_spec: Optional[PathSpec],
    config_include_spec: Optional[PathSpec],
) -> None:
    """Log the reason for excluding a file.

    Args:
        file_path (str): The path to the file.
        config (CodeConCatConfig): The configuration object.
        gitignore_spec (Optional[PathSpec]): The compiled gitignore patterns.
        default_exclude_spec (Optional[PathSpec]): The compiled default exclude patterns.
        config_exclude_spec (Optional[PathSpec]): The compiled config exclude patterns.
        config_include_spec (Optional[PathSpec]): The compiled config include patterns.
    """
    # Check .gitignore (if spec exists and enabled)
    if config.use_gitignore and gitignore_spec and gitignore_spec.match_file(file_path):
        logger.debug(f"Excluded by .gitignore: {file_path}")
        return

    # Check default excludes (if spec exists and enabled)
    if (
        config.use_default_excludes
        and default_exclude_spec
        and default_exclude_spec.match_file(file_path)
    ):
        logger.debug(f"Excluded by default excludes: {file_path}")
        return

    # Check explicit excludes from config (if spec exists)
    if config_exclude_spec and config_exclude_spec.match_file(file_path):
        logger.debug(f"Excluded by config exclude_paths: {file_path}")
        return

    # If include paths are defined, the file MUST match one of them.
    if config_include_spec and not config_include_spec.match_file(file_path):
        logger.debug(
            f"Skipped: '{file_path}' does not match any include_paths pattern."
        )
        return

    # If we got here, it's likely due to language filtering
    logger.debug(f"Excluded by language filtering: {file_path}")
