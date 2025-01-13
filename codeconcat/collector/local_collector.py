import fnmatch
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from typing import List

from codeconcat.base_types import CodeConCatConfig, ParsedFileData

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


def collect_local_files(root_path: str, config: CodeConCatConfig):
    """Collect files from local filesystem."""

    logger.debug(f"[CodeConCat] Collecting files from: {root_path}")

    # Ensure root path exists
    if not os.path.exists(root_path):
        raise FileNotFoundError(f"Path does not exist: {root_path}")

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
                futures.append(executor.submit(process_file, file_path, config))

        # Collect results, filtering out None values
        results = [f.result() for f in futures if f.result()]

    if not results:
        logger.warning("[CodeConCat] No files found matching the criteria")
    else:
        logger.info(f"[CodeConCat] Collected {len(results)} files")

    return results


def process_file(file_path: str, config: CodeConCatConfig):
    """Process a single file, reading its content if it should be included."""
    try:
        if not should_include_file(file_path, config):
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


def should_include_file(path_str: str, config: CodeConCatConfig) -> bool:
    """Determine if a file should be included based on patterns and configuration."""
    # Get file extension
    ext = os.path.splitext(path_str)[1].lower()

    # Check if file is binary
    if is_binary_file(path_str):
        return False

    # Get file type
    file_type = ext_map(ext, config)

    # Skip non-code files
    if file_type == "non-code":
        return False

    # Handle documentation files
    is_doc = file_type == "markdown"
    if is_doc and not config.extract_docs:
        return False

    # Check if file matches any include patterns
    if config.include_paths:
        included = any(matches_pattern(path_str, pattern) for pattern in config.include_paths)
        if not included:
            return False

    # Check if file matches any exclude patterns
    if config.exclude_paths:
        excluded = any(matches_pattern(path_str, pattern) for pattern in config.exclude_paths)
        if excluded:
            return False

    # Check if file type matches language filters
    if config.include_languages and file_type not in config.include_languages:
        return False
    if config.exclude_languages and file_type in config.exclude_languages:
        return False

    return True


def matches_pattern(path_str: str, pattern: str) -> bool:
    """Match a path against a glob pattern, handling both relative and absolute paths."""
    # Normalize path separators and remove leading/trailing slashes
    path_str = path_str.replace(os.sep, "/").strip("/").lower()  # Case-insensitive matching
    pattern = pattern.replace(os.sep, "/").strip("/").lower()

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
    # Remove leading dot if present
    ext = ext.lstrip(".").lower()

    # Check custom mappings first - try both with and without dot
    if ext in config.custom_extension_map:
        return config.custom_extension_map[ext]
    if f".{ext}" in config.custom_extension_map:
        return config.custom_extension_map[f".{ext}"]

    # Non-code files that should be excluded
    non_code_exts = {
        # Images
        "svg", "png", "jpg", "jpeg", "gif", "ico", "webp",
        # Fonts
        "woff", "woff2", "ttf", "eot", "otf",
        # Documents
        "pdf", "doc", "docx", "xls", "xlsx",
        # Archives
        "zip", "tar", "gz", "tgz", "7z", "rar",
        # Build artifacts
        "map", "min.js", "min.css", "bundle.js", "bundle.css",
        "chunk.js", "chunk.css", "nft.json", "rsc", "meta",
        "pyc", "pyo", "pyd",  # Python bytecode files
        # Other assets
        "mp3", "mp4", "wav", "avi", "mov"
    }

    if ext in non_code_exts:
        return "non-code"

    # Code files
    code_exts = {
        # Python
        "py": "python",
        "pyi": "python",
        "pyx": "python",
        # JavaScript/TypeScript
        "js": "javascript",
        "jsx": "javascript",
        "ts": "typescript",
        "tsx": "typescript",
        "mjs": "javascript",
        # Web
        "html": "html",
        "htm": "html",
        "css": "css",
        "scss": "css",
        "sass": "css",
        "less": "css",
        # Other languages
        "r": "r",
        "jl": "julia",
        "cpp": "cpp",
        "hpp": "cpp",
        "cxx": "cpp",
        "c": "c",
        "h": "c",
        "go": "go",
        "rs": "rust",
        "java": "java",
        "kt": "kotlin",
        "scala": "scala",
        "php": "php",
        "rb": "ruby",
        "pl": "perl",
        "sh": "shell",
        "bash": "shell",
        "zsh": "shell",
        # Documentation
        "md": "markdown",
        "rst": "markdown",
        "txt": "text",
        "rmd": "markdown",
        "adoc": "markdown",
        # Config
        "json": "json",
        "toml": "toml",
        "yaml": "yaml",
        "yml": "yaml",
        "ini": "ini",
        "cfg": "ini"
    }

    return code_exts.get(ext, "text")  # Default to text for unknown extensions


def is_binary_file(file_path: str) -> bool:
    """Check if a file is likely to be binary."""
    # First check if the file exists
    if not os.path.exists(file_path):
        return False

    # Check if it's a known binary extension
    binary_exts = {
        # Compiled files
        ".pyc", ".pyo", ".pyd",  # Python
        ".so", ".dylib", ".dll",  # Shared libraries
        ".exe", ".bin",          # Executables
        # Media files
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico",  # Images
        ".mp3", ".wav", ".ogg", ".m4a",                   # Audio
        ".mp4", ".avi", ".mov", ".mkv",                   # Video
        # Archives
        ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
        # Other
        ".pdf", ".doc", ".docx", ".xls", ".xlsx",
        ".db", ".sqlite", ".sqlite3"                      # Databases
    }
    
    ext = os.path.splitext(file_path)[1].lower()
    if ext in binary_exts:
        return True

    # For other files, try to read as text
    try:
        with open(file_path, "tr", encoding="utf-8") as check_file:
            # Read first few KB to check for binary content
            chunk = check_file.read(1024)
            return False
    except (UnicodeDecodeError, IOError):
        return True
