import fnmatch
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from typing import List
from pathlib import Path
from codeconcat.base_types import CodeConCatConfig, ParsedFileData
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# Create a console handler and set the level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# Create a formatter and add it to the handler
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(ch)

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


def should_include_file(
    file_path: str, config: CodeConCatConfig, gitignore_spec: PathSpec = None
) -> bool:
    """
    Check if a file should be included based on configuration and .gitignore.

    Args:
        file_path: Path to the file
        config: Configuration object
        gitignore_spec: PathSpec object for .gitignore matching

    Returns:
        bool: True if file should be included, False otherwise
    """
    # Get relative path for .gitignore matching
    rel_path = os.path.relpath(file_path, config.target_path)

    # Check .gitignore first
    if gitignore_spec and gitignore_spec.match_file(rel_path):
        return False

    # Then check configuration patterns
    if config.exclude_paths:
        for pattern in config.exclude_paths:
            # Check if any part of the path matches the pattern
            path_parts = Path(rel_path).parts
            if any(fnmatch.fnmatch(os.path.join(*path_parts[:i+1]), pattern) 
                  for i in range(len(path_parts))):
                return False

    if config.include_paths:
        return any(fnmatch.fnmatch(rel_path, pattern) for pattern in config.include_paths)

    return True


def collect_local_files(root_path: str, config: CodeConCatConfig):
    """Collect files from local filesystem."""

    logger.debug(f"[CodeConCat] Collecting files from: {root_path}")

    # Ensure root path exists
    if not os.path.exists(root_path):
        raise FileNotFoundError(f"Path does not exist: {root_path}")

    gitignore_spec = get_gitignore_spec(root_path)

    # Collect files using thread pool
    with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        futures = []

        for dirpath, dirnames, filenames in os.walk(root_path):
            # Skip directories that match exclude patterns
            if should_skip_dir(dirpath, config.exclude_paths):
                dirnames.clear()  # Clear dirnames to skip subdirectories
                continue

            # Process files in parallel
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                futures.append(executor.submit(process_file, file_path, config, gitignore_spec))

        # Collect results, filtering out None values
        results = [f.result() for f in futures if f.result()]

    if not results:
        logger.warning("[CodeConCat] No files found matching the criteria")
    else:
        logger.info(f"[CodeConCat] Collected {len(results)} files")

    return results


def process_file(file_path: str, config: CodeConCatConfig, gitignore_spec: PathSpec):
    """Process a single file, reading its content if it should be included."""
    try:
        if not should_include_file(file_path, config, gitignore_spec):
            return None

        if is_binary_file(file_path):
            logger.debug(f"[CodeConCat] Skipping binary file: {file_path}")
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        ext = os.path.splitext(file_path)[1].lstrip(".")
        language = ext_map(ext, config)

        logger.debug(f"[CodeConCat] Processed file: {file_path} ({language})")
        return ParsedFileData(
            file_path=file_path,
            language=language,
            content=content,
            declarations=[],  # We'll fill this in during parsing phase
        )

    except UnicodeDecodeError:
        logger.debug(f"[CodeConCat] Skipping non-text file: {file_path}")
        return None
    except Exception as e:
        logger.error(f"[CodeConCat] Error processing {file_path}: {str(e)}")
        return None


def should_skip_dir(dirpath: str, user_excludes: List[str]) -> bool:
    """Check if a directory should be skipped based on exclude patterns."""
    all_excludes = DEFAULT_EXCLUDES + (user_excludes or [])
    logger.debug(f"Checking directory: {dirpath} against patterns: {all_excludes}")

    # Convert to relative path for matching
    if os.path.isabs(dirpath):
        try:
            rel_path = os.path.relpath(dirpath, os.getcwd())
        except ValueError:
            rel_path = dirpath
    else:
        rel_path = dirpath

    # Normalize path separators and remove leading/trailing slashes
    rel_path = rel_path.replace(os.sep, "/").strip("/")

    # Check if the directory itself matches any exclude pattern
    for pattern in all_excludes:
        if matches_pattern(rel_path, pattern):
            logger.debug(f"Excluding directory {rel_path} due to pattern {pattern}")
            return True

    # Also check each parent directory
    path_parts = [p for p in rel_path.split("/") if p]
    current_path = ""
    for part in path_parts:
        if current_path:
            current_path += "/"
        current_path += part

        for pattern in all_excludes:
            # Try both with and without trailing slash
            if matches_pattern(current_path, pattern) or matches_pattern(
                current_path + "/", pattern
            ):
                logger.debug(
                    f"Excluding directory {rel_path} due to parent {current_path} matching pattern {pattern}"
                )
                return True

    return False


def matches_pattern(path_str: str, pattern: str) -> bool:
    """Match a path against a glob pattern, handling both relative and absolute paths."""
    # Normalize path separators and remove leading/trailing slashes
    path_str = path_str.replace(os.sep, "/").strip("/")
    pattern = pattern.replace(os.sep, "/").strip("/")

    # Handle special case of root directory
    if pattern == "":
        return path_str == ""

    # Convert glob pattern to regex
    pattern = pattern.replace(".", "\\.")  # Escape dots
    pattern = pattern.replace("**", "__DOUBLE_STAR__")  # Preserve **
    pattern = pattern.replace("*", "[^/]*")  # Single star doesn't cross directories
    pattern = pattern.replace("__DOUBLE_STAR__", ".*")  # ** can cross directories
    pattern = pattern.replace("?", "[^/]")  # ? matches single character

    # Handle directory patterns
    if pattern.endswith("/"):
        pattern = pattern + ".*"  # Match anything after directory

    # Handle pattern anchoring
    if pattern.startswith("/"):
        pattern = "^" + pattern[1:]  # Keep absolute path requirement
    elif pattern.startswith("**/"):
        pattern = ".*" + pattern[2:]  # Allow matching anywhere in path
    else:
        pattern = "^" + pattern  # Anchor to start by default

    if not pattern.endswith("$"):
        pattern += "$"  # Always anchor to end

    # Try to match
    try:
        return bool(re.match(pattern, path_str))
    except re.error as e:
        logger.warning(f"Invalid pattern {pattern}: {str(e)}")
        return False


def ext_map(ext: str, config: CodeConCatConfig) -> str:
    """Map file extensions to their corresponding language or type."""
    if ext in config.custom_extension_map:
        return config.custom_extension_map[ext]

    # Non-code files that should be excluded
    non_code_exts = {
        # Images
        "svg",
        "png",
        "jpg",
        "jpeg",
        "gif",
        "ico",
        "webp",
        # Fonts
        "woff",
        "woff2",
        "ttf",
        "eot",
        "otf",
        # Documents
        "pdf",
        "doc",
        "docx",
        "xls",
        "xlsx",
        # Archives
        "zip",
        "tar",
        "gz",
        "tgz",
        "7z",
        "rar",
        # Build artifacts
        "map",
        "min.js",
        "min.css",
        "bundle.js",
        "bundle.css",
        "chunk.js",
        "chunk.css",
        "nft.json",
        "rsc",
        "meta",
        # Other assets
        "mp3",
        "mp4",
        "wav",
        "avi",
        "mov",
    }

    if ext.lower() in non_code_exts:
        return "non-code"

    # Code files
    code_exts = {
        # Python
        "py": "python",
        "pyi": "python",
        # JavaScript/TypeScript
        "js": "javascript",
        "jsx": "javascript",
        "ts": "typescript",
        "tsx": "typescript",
        "mjs": "javascript",
        # Other languages
        "r": "r",
        "jl": "julia",
        "cpp": "cpp",
        "hpp": "cpp",
        "cxx": "cpp",
        "c": "c",
        "h": "c",
        # Documentation
        "md": "doc",
        "rst": "doc",
        "txt": "doc",
        "rmd": "doc",
    }

    return code_exts.get(ext.lower(), "unknown")


def is_binary_file(file_path: str) -> bool:
    """Check if a file is likely to be binary."""
    try:
        with open(file_path, "tr") as check_file:
            check_file.readline()
            return False
    except UnicodeDecodeError:
        return True
