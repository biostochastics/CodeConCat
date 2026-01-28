# file: codeconcat/utils/file_utils.py

"""
Centralized file utility functions for codeconcat.

This module provides common file operations including:
- Large file detection and handling
- File size validation
- Binary file detection helpers
"""

import logging
import os
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class FileSizeConfig:
    """
    Configuration for file size limits.

    Centralized configuration class for all file size limits used
    throughout codeconcat. Provides consistent size limits and
    convenient size unit constants.

    Attributes:
        DEFAULT_MAX_FILE_SIZE: 10MB limit for general file processing
        DEFAULT_MAX_COLLECTION_SIZE: 20MB limit for collection phase
        DEFAULT_MAX_BINARY_CHECK_SIZE: 10MB limit for binary detection
        KB, MB, GB: Size unit constants for calculations

    Usage:
        Used by check_file_size() and related functions to enforce
        consistent size limits across the codebase.
    """

    # Default size limits in bytes
    DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB for general processing
    DEFAULT_MAX_COLLECTION_SIZE = 20 * 1024 * 1024  # 20MB for collection phase
    DEFAULT_MAX_BINARY_CHECK_SIZE = 10 * 1024 * 1024  # 10MB for binary checking

    # Size units for convenience
    KB = 1024
    MB = 1024 * 1024
    GB = 1024 * 1024 * 1024


def check_file_size(
    file_path: str, max_size: Optional[int] = None, context: str = "processing"
) -> Tuple[bool, int]:
    """
    Check if a file exceeds the specified size limit.

    Core function for file size validation used throughout codeconcat
    to prevent processing of excessively large files that could cause
    memory issues or performance problems.

    Args:
        file_path: Path to the file to check
        max_size: Maximum allowed size in bytes (defaults to 10MB)
        context: Context string for logging (e.g., "collection", "parsing")

    Returns:
        Tuple of (is_within_limit, actual_size) where:
        - is_within_limit: True if file is within size limit, False otherwise
        - actual_size: Actual file size in bytes

    Raises:
        OSError: If file size cannot be determined

    Complexity: O(1) - Single filesystem stat call

    Flow:
        Called by: is_file_too_large_for_collection(), is_file_too_large_for_binary_check()
        Calls: os.path.getsize()

    Error Handling:
        - OSError/IOError: Logs error and re-raises for caller to handle
    """
    if max_size is None:
        max_size = FileSizeConfig.DEFAULT_MAX_FILE_SIZE

    try:
        file_size = os.path.getsize(file_path)

        if file_size > max_size:
            size_mb = file_size / FileSizeConfig.MB
            max_mb = max_size / FileSizeConfig.MB
            logger.debug(
                f"[{context}] File exceeds size limit: {file_path} "
                f"({size_mb:.2f}MB > {max_mb:.2f}MB)"
            )
            return False, file_size

        return True, file_size

    except OSError as e:
        logger.error(f"[{context}] Error checking file size for {file_path}: {e}")
        raise


def is_file_too_large_for_collection(file_path: str, max_size: Optional[int] = None) -> bool:
    """
    Check if a file is too large for the collection phase.

    Specialized check for the file collection phase with a higher
    size limit (20MB) to allow collection of larger codebases while
    still preventing memory exhaustion.

    Args:
        file_path: Path to the file to check
        max_size: Maximum size in bytes (defaults to 20MB)

    Returns:
        True if file is too large, False otherwise

    Complexity: O(1) - Single size check

    Flow:
        Called by: local_collector.py during file collection
        Calls: check_file_size()

    Error Handling:
        - OSError: Returns True (safe default) if size cannot be determined
        - Logs warning for skipped large files

    Security Notes:
        - Prevents memory exhaustion from large files
        - Safe default (True) when size cannot be determined
    """
    if max_size is None:
        max_size = FileSizeConfig.DEFAULT_MAX_COLLECTION_SIZE

    try:
        within_limit, size = check_file_size(file_path, max_size, "collection")
        if not within_limit:
            logger.warning(f"Skipping large file ({size / FileSizeConfig.MB:.2f}MB): {file_path}")
        return not within_limit
    except OSError:
        # If we can't determine size, assume it's too large to be safe
        return True


def is_file_too_large_for_binary_check(file_path: str, max_size: Optional[int] = None) -> bool:
    """
    Check if a file is too large for binary content checking.

    Determines if a file should skip binary detection to avoid
    reading large files unnecessarily. Uses a lower threshold (5MB)
    since binary detection only needs to read the first 8KB.

    Args:
        file_path: Path to the file to check
        max_size: Maximum size in bytes (defaults to 5MB)

    Returns:
        True if file is too large for binary checking, False otherwise

    Complexity: O(1) - Single size check

    Flow:
        Called by: local_collector.is_binary_file()
        Calls: check_file_size()

    Performance Notes:
        - Avoids reading large files for binary detection
        - Binary check only needs first 8KB, but large files are likely binary

    Error Handling:
        - OSError: Returns True (skip binary check) if size cannot be determined
    """
    if max_size is None:
        max_size = FileSizeConfig.DEFAULT_MAX_BINARY_CHECK_SIZE

    try:
        within_limit, size = check_file_size(file_path, max_size, "binary_check")
        if not within_limit:
            logger.debug(
                f"File too large for binary check (>{size / FileSizeConfig.MB:.2f}MB): {file_path}"
            )
        return not within_limit
    except OSError:
        # If we can't determine size, skip binary check
        return True


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Converts raw byte counts to human-friendly strings with
    appropriate units (B, KB, MB, GB).

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string like "1.23 MB"

    Complexity: O(1) - Simple arithmetic and comparisons

    Flow:
        Called by: get_file_size_info(), logging functions
        Calls: None (pure calculation)

    Examples:
        - 512 -> "512 B"
        - 1536 -> "1.50 KB"
        - 5242880 -> "5.00 MB"
        - 1073741824 -> "1.00 GB"
    """
    if size_bytes < FileSizeConfig.KB:
        return f"{size_bytes} B"
    elif size_bytes < FileSizeConfig.MB:
        return f"{size_bytes / FileSizeConfig.KB:.2f} KB"
    elif size_bytes < FileSizeConfig.GB:
        return f"{size_bytes / FileSizeConfig.MB:.2f} MB"
    else:
        return f"{size_bytes / FileSizeConfig.GB:.2f} GB"


def get_file_size_info(file_path: str) -> Optional[str]:
    """
    Get formatted file size information for logging.

    Convenience function that combines size retrieval and formatting
    for use in log messages and user output.

    Args:
        file_path: Path to the file

    Returns:
        Formatted string with file size, or None if error

    Complexity: O(1) - Single filesystem stat call

    Flow:
        Called by: Logging and reporting functions
        Calls: os.path.getsize(), format_file_size()

    Error Handling:
        - OSError/IOError: Returns None instead of raising
        - Safe for use in logging without try/catch

    Usage Example:
        size_info = get_file_size_info("/path/to/file.py")
        if size_info:
            logger.info(f"Processing file ({size_info}): {file_path}")
    """
    try:
        size = os.path.getsize(file_path)
        return format_file_size(size)
    except OSError:
        return None
