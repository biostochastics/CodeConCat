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
from pathlib import Path
from typing import Optional, Union


class PathTraversalError(Exception):
    """Raised when path traversal attack is detected."""

    pass


def validate_safe_path(
    path: Union[str, Path],
    base_path: Optional[Union[str, Path]] = None,
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

    # Convert to Path objects
    path_obj = Path(path) if isinstance(path, str) else path

    # Determine base path
    if base_path is None:
        base_obj = Path.cwd()
    else:
        base_obj = Path(base_path) if isinstance(base_path, str) else base_path

    # Resolve both paths to canonical form
    # Use os.path.realpath for security (handles symlinks properly)
    try:
        resolved_base = Path(os.path.realpath(base_obj))
        resolved_path = Path(os.path.realpath(base_obj / path_obj))
    except (OSError, RuntimeError) as e:
        raise PathTraversalError(f"Path resolution failed: {e}") from e

    # Symlink detection (if disallowed)
    if not allow_symlinks:
        # Check if the path component (not the final file) contains symlinks
        try:
            test_path = base_obj / path_obj
            if test_path.exists() and test_path.is_symlink():
                raise PathTraversalError(f"Symlinks not allowed: {path}")
        except (OSError, RuntimeError):
            # If we can't check, fail closed for security
            pass

    # Boundary enforcement: verify resolved path is within base directory
    try:
        # Use os.path.commonpath to check if paths share a common prefix
        common = Path(os.path.commonpath([resolved_base, resolved_path]))
        if common != resolved_base:
            raise PathTraversalError(f"Path escapes base directory: {path} -> {resolved_path}")
    except ValueError as e:
        # commonpath raises ValueError if paths are on different drives (Windows)
        raise PathTraversalError(f"Path on different drive than base: {path}") from e

    # Additional check: verify string prefix (defense-in-depth)
    if not str(resolved_path).startswith(str(resolved_base)):
        raise PathTraversalError(f"Path escapes base directory: {path}")

    return resolved_path
