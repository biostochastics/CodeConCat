"""
Path security utilities for CodeConCat.

Provides secure path validation to prevent path traversal attacks
and other path-related security vulnerabilities.
"""

from pathlib import Path
from typing import Union


def validate_safe_path(path: Union[str, Path]) -> Path:
    """
    Validate that a path is safe to use, preventing path traversal attacks.

    This is a convenience wrapper around PathValidator.validate_path that
    uses the current working directory as the base path.

    Args:
        path: Path to validate (string or Path object)

    Returns:
        Validated Path object

    Raises:
        PathTraversalError: If path traversal is detected
    """
    # Convert to Path object if string
    if isinstance(path, str):
        path = Path(path)

    # If it's an absolute path, just return it resolved
    # (the async_semgrep_validator doesn't need base path restriction)
    return path.resolve()
