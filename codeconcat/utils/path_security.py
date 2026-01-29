"""
Path security utilities for CodeConCat.

Provides secure path validation to prevent path traversal attacks
and other path-related security vulnerabilities.

This module implements defense-in-depth path validation using:
- Canonical path resolution (realpath)
- Strict boundary enforcement
- Symlink escape detection
- Cross-platform path normalization
"""

import os
import re
import unicodedata
from pathlib import Path
from urllib.parse import unquote


class PathTraversalError(Exception):
    """Raised when path traversal attack is detected."""

    pass


def validate_safe_path(
    path: str | Path,
    base_path: str | Path | None = None,
    allow_symlinks: bool = False,
) -> Path:
    """
    Validate that a path is safe to use, preventing path traversal attacks.

    This function provides defense-in-depth security by:
    1. Resolving paths to their canonical form (following symlinks)
    2. Enforcing boundary checks against the base path
    3. Detecting and blocking symlink escapes
    4. Normalizing path separators across platforms

    Args:
        path: Path to validate (string or Path object)
        base_path: Base directory to enforce as boundary. If None, uses cwd.
                   All resolved paths must remain within this directory.
        allow_symlinks: Whether to allow symlinks. Default False for security.

    Returns:
        Validated Path object, guaranteed to be within base_path boundary

    Raises:
        PathTraversalError: If path traversal is detected or path escapes boundary
        ValueError: If path is invalid or contains null bytes

    Example:
        >>> # Safe usage
        >>> validate_safe_path("/project/src/file.py", base_path="/project")
        PosixPath('/project/src/file.py')

        >>> # Blocked traversal
        >>> validate_safe_path("../../../etc/passwd", base_path="/project")
        PathTraversalError: Path traversal detected

    Security:
        - Uses os.path.realpath() for canonicalization (not just resolve())
        - Enforces strict boundary checks using commonpath comparison
        - Rejects paths containing null bytes
        - Optionally blocks symlinks to prevent TOCTOU attacks
    """
    # Input validation
    if not path:
        raise ValueError("Path cannot be empty")

    # Convert to string for validation
    path_str = str(path)

    # Block null bytes (path traversal primitive)
    if "\x00" in path_str:
        raise PathTraversalError("Path contains null bytes")

    # URL decode multiple times to handle double/triple encoding
    decoded = path_str
    for _ in range(3):  # Handle up to triple encoding
        prev = decoded
        decoded = unquote(decoded)
        if prev == decoded:
            break  # No more decoding needed

    # Normalize Unicode characters to handle homoglyph attacks
    normalized = unicodedata.normalize("NFKC", decoded)

    # Check for backslash traversal patterns (Windows-style on Unix)
    # If path contains backslashes and parent references, it's suspicious
    if "..\\" in normalized:
        # This is a clear traversal attempt using Windows-style separators
        raise PathTraversalError("Path escapes base directory")

    # Check for definitely malicious patterns (encoded/obfuscated traversal)
    # We allow plain ".." since it might resolve safely, but block encoded/obfuscated versions
    # Use regex lookarounds to avoid false positives with legitimate hex strings
    malicious_patterns_regex = [
        (r"(?<![0-9a-fA-F])%2e%2e(?![0-9a-fA-F])", "URL encoded .."),  # URL encoded ..
        (r"(?<![0-9a-fA-F])%252e(?![0-9a-fA-F])", "Double encoded"),  # Double encoded
        (r"%00", "Null byte"),  # Null byte
        (r"%01", "Control character"),  # Control character
        (r"\.\.\;", "Semicolon trick"),  # Semicolon tricks
    ]

    # Check in the normalized and decoded versions for malicious patterns
    for check_str in [normalized.lower(), decoded.lower()]:
        for pattern_regex, pattern_desc in malicious_patterns_regex:
            if re.search(pattern_regex, check_str, re.IGNORECASE):
                raise PathTraversalError(f"Malicious pattern detected: {pattern_desc}")

    # Use the normalized path for further processing
    path_str = normalized

    # Check if path tries to escape immediately (starts with ..)
    # This is always suspicious since we're supposed to stay within base
    if path_str.startswith(".."):
        # Double-check by resolving - it might be okay if base is not root
        # We'll let the later resolution handle this case
        pass

    # Check for Windows drive letter attacks (e.g., C:/, D:\)
    # Only apply this check on non-Windows hosts to avoid false positives on Windows
    # Valid drive letter pattern: single letter followed by colon
    if os.name != "nt" and len(path_str) >= 2 and path_str[1] == ":" and path_str[0].isalpha():
        raise PathTraversalError(f"Absolute Windows path not allowed: {path_str}")

    # Check for UNC path attacks (e.g., \\server\share or //server/share)
    if path_str.startswith("\\\\") or path_str.startswith("//"):
        raise PathTraversalError(f"UNC path not allowed: {path_str}")

    # Check for excessively long paths (potential attack)
    if len(path_str) > 4096:  # Most filesystems limit to 4096
        raise PathTraversalError(f"Path too long: {len(path_str)} bytes")

    # Convert to Path objects using the normalized string
    path_obj = Path(path_str)

    # Determine base path
    if base_path is None:
        base_obj = Path.cwd()
    else:
        base_obj = Path(base_path) if isinstance(base_path, str) else base_path

    # Resolve both paths to canonical form
    # Use os.path.realpath for security (handles symlinks properly)
    try:
        resolved_base = Path(os.path.realpath(base_obj))

        # Handle absolute paths differently - don't combine with base
        if path_obj.is_absolute():
            # For absolute paths, resolve them directly
            resolved_path = Path(os.path.realpath(path_obj))
        else:
            # For relative paths, combine with base then resolve
            resolved_path = Path(os.path.realpath(base_obj / path_obj))
    except (OSError, RuntimeError) as e:
        raise PathTraversalError(f"Path resolution failed: {e}") from e

    # Symlink detection (if disallowed)
    if not allow_symlinks:
        # Check each component of the path for symlinks
        try:
            # For absolute paths, check the path directly
            if path_obj.is_absolute():
                test_path = path_obj
                if test_path.exists() and test_path.is_symlink():
                    raise PathTraversalError(f"Symlinks not allowed in path: {test_path}")
            else:
                # For relative paths, check each component when combined with base
                test_path = base_obj
                for part in path_obj.parts:
                    if not part or part == "/":  # Skip empty parts or root
                        continue
                    test_path = test_path / part
                    if test_path.exists() and test_path.is_symlink():
                        raise PathTraversalError(f"Symlinks not allowed in path: {test_path}")
                    # Also check if it would escape via symlink
                    if test_path.exists():
                        real_test = Path(os.path.realpath(test_path))
                        real_base = Path(os.path.realpath(base_obj))
                        # Use os.path.commonpath for robust comparison (handles separators correctly)
                        # Compare normalized string forms to avoid path object/case-sensitivity mismatches
                        try:
                            common = os.path.commonpath([str(real_base), str(real_test)])
                            if os.path.normcase(common) != os.path.normcase(str(real_base)):
                                raise PathTraversalError(
                                    f"Symlink escapes base directory: {test_path}"
                                )
                        except ValueError:
                            # Different drives on Windows
                            raise PathTraversalError(
                                f"Symlink on different drive than base: {test_path}"
                            ) from None
        except (OSError, RuntimeError) as e:
            # If we can't check, fail closed for security
            if "symlink" not in str(e).lower():
                raise PathTraversalError(f"Path validation error: {e}") from e

    # Boundary enforcement: verify resolved path is within base directory
    try:
        # Use os.path.commonpath to check if paths share a common prefix
        # Compare normalized string forms to avoid case-sensitivity issues
        common = os.path.commonpath([str(resolved_base), str(resolved_path)])
        if os.path.normcase(common) != os.path.normcase(str(resolved_base)):
            raise PathTraversalError(f"Path escapes base directory: {path} -> {resolved_path}")
    except ValueError as e:
        # commonpath raises ValueError if paths are on different drives (Windows)
        raise PathTraversalError(f"Path on different drive than base: {path}") from e

    # Additional check: verify string prefix (defense-in-depth)
    # Use case-normalized comparison for cross-platform compatibility
    if not os.path.normcase(str(resolved_path)).startswith(os.path.normcase(str(resolved_base))):
        raise PathTraversalError(f"Path escapes base directory: {path}")

    return resolved_path
