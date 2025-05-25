"""
Input validation module for CodeConCat.

This module provides functions to validate various types of input data
used throughout the CodeConCat application, including file paths, content,
configuration, and API inputs.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union, BinaryIO
import re
import os
import mimetypes
from urllib.parse import urlparse
import logging

from ..errors import ValidationError

logger = logging.getLogger(__name__)

# Maximum file size for validation (100MB)
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB in bytes

# Common file extensions that could be malicious
POTENTIALLY_MALICIOUS_EXTENSIONS = {
    # Executables
    '.exe', '.msi', '.bat', '.cmd', '.ps1', '.sh', '.bin', '.dll', '.so', '.dylib',
    # Archives that could contain malicious content
    '.zip', '.tar', '.gz', '.bz2', '.xz', '.7z',
    # Documents with macros
    '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    # Other potentially dangerous types
    '.js', '.jse', '.vbs', '.vbe', '.wsf', '.wsh', '.ps1', '.psm1', '.psd1',
    # Hidden files on Unix-like systems
    '~', '.swp', '.swo', '.swn', '.swm', '.swl', '.swk', '.swj', '.swn', '.swp',
}

# Common binary file signatures (magic numbers)
BINARY_SIGNATURES = [
    (b'\x7fELF', 'ELF executable'),
    (b'MZ', 'Windows PE executable'),
    (b'\x89PNG', 'PNG image'),
    (b'\xff\xd8\xff', 'JPEG image'),
    (b'GIF87a', 'GIF image'),
    (b'GIF89a', 'GIF image'),
    (b'%PDF', 'PDF document'),
    (b'PK\x03\x04', 'ZIP archive'),
]

class InputValidator:
    """A class to handle input validation for CodeConCat."""

    @staticmethod
    def validate_file_path(file_path: Union[str, Path], check_exists: bool = True, base_dir: Optional[Path] = None) -> Path:
        """
        Validate a file path.

        Args:
            file_path: The file path to validate.
            check_exists: If True, checks if the file exists.
            base_dir: The base directory to check for path traversal against. Defaults to CWD.

        Returns:
            Path: The validated Path object.

        Raises:
            ValidationError: If the path is invalid, doesn't exist (when check_exists=True),
                             or is a traversal attempt.
        """
        if not file_path:
            raise ValidationError("File path cannot be empty")

        try:
            path = Path(file_path).resolve()
        except Exception as e:
            # logger.debug(f"Path resolution failed for '{file_path}': {e}", exc_info=True)
            raise ValidationError(f"Invalid file path: {file_path}") from e

        if check_exists and not path.exists():
            raise ValidationError(f"File does not exist: {path} (from original: {file_path})")

        # Check for path traversal attempts only if base_dir is provided
        if base_dir:
            logger.debug(f"[validate_file_path] Original base_dir for '{file_path}': {base_dir}")
            effective_base_dir = base_dir.resolve()
            logger.debug(f"[validate_file_path] Effective base_dir for '{file_path}': {effective_base_dir}")
            try:
                path.relative_to(effective_base_dir)
            except ValueError:
                logger.debug(f"Path traversal check failed: path='{path}', effective_base_dir='{effective_base_dir}'")
                raise ValidationError(f"Path traversal attempt detected for '{file_path}' (resolved to '{path}') relative to base '{effective_base_dir}'")

        return path

    @staticmethod
    def validate_file_size(file_path: Union[str, Path], max_size: int = MAX_FILE_SIZE, base_dir: Optional[Path] = None) -> bool:
        """
        Check if a file's size is within the allowed limit.

        Args:
            file_path: Path to the file
            max_size: Maximum allowed file size in bytes
            base_dir: Optional base directory for path validation

        Returns:
            bool: True if file size is within limits

        Raises:
            ValidationError: If file is too large
        """
        path = InputValidator.validate_file_path(file_path, base_dir=base_dir)
        file_size = path.stat().st_size

        if file_size > max_size:
            raise ValidationError(
                f"File {file_path} is too large ({file_size} bytes > {max_size} bytes)"
            )
        return True

    @staticmethod
    def validate_file_extension(file_path: Union[str, Path], allowed_extensions: Optional[Set[str]] = None, base_dir: Optional[Path] = None) -> bool:
        """
        Validate a file's extension against a set of allowed extensions.

        Args:
            file_path: Path to the file
            allowed_extensions: Set of allowed file extensions (with leading .), or None to only check for malicious

        Returns:
            bool: True if the file extension is allowed

        Raises:
            ValidationError: If the file extension is not allowed or is potentially malicious
        """
        path = InputValidator.validate_file_path(file_path, base_dir=base_dir)
        ext = path.suffix.lower()

        # Check for potentially malicious extensions
        if ext in POTENTIALLY_MALICIOUS_EXTENSIONS:
            raise ValidationError(f"Potentially malicious file type detected: {ext}")

        # If specific extensions are required, check against them
        if allowed_extensions is not None and ext not in allowed_extensions:
            raise ValidationError(f"File type {ext} is not allowed. Allowed types: {', '.join(allowed_extensions)}")

        return True

    @staticmethod
    def validate_file_content(file_path: Union[str, Path], check_binary: bool = True, base_dir: Optional[Path] = None) -> bool:
        """
        Validate the content of a file.

        Args:
            file_path: Path to the file
            check_binary: If True, checks if the file appears to be binary

        Returns:
            bool: True if the file content is valid

        Raises:
            ValidationError: If the file content is invalid or appears to be binary (when check_binary=True)
        """
        path = InputValidator.validate_file_path(file_path, base_dir=base_dir)

        # Skip binary check for certain file types
        if check_binary and InputValidator._is_binary_file(path):
            raise ValidationError(f"Binary file detected: {file_path}")

        return True

    @staticmethod
    def validate_directory_path(directory_path: Union[str, Path], check_exists: bool = True, base_dir: Optional[Path] = None) -> Path:
        """
        Validate a directory path.

        Args:
            directory_path: The directory path to validate
            check_exists: If True, checks if the directory exists

        Returns:
            Path: The validated Path object

        Raises:
            ValidationError: If the path is invalid, doesn't exist (when check_exists=True),
                            or is not a directory
        """
        path = InputValidator.validate_file_path(directory_path, check_exists=check_exists, base_dir=base_dir)

        if check_exists and not path.is_dir():
            raise ValidationError(f"Path is not a directory: {directory_path}")

        return path

    @staticmethod
    def validate_url(url: str, allowed_domains: Optional[Set[str]] = None) -> str:
        """
        Validate a URL.

        Args:
            url: The URL to validate
            allowed_domains: Set of allowed domains (e.g., {'github.com', 'gitlab.com'})

        Returns:
            str: The validated URL

        Raises:
            ValidationError: If the URL is invalid or not from an allowed domain
        """
        if not url:
            raise ValidationError("URL cannot be empty")


        # Check URL scheme
        if not url.startswith(('http://', 'https://', 'git@')):
            # Try to add https:// if no scheme is provided
            if '://' not in url and not url.startswith('git@'):
                url = f'https://{url}'
            else:
                raise ValidationError("Invalid URL scheme. Only http://, https://, and git@ are supported.")

        # Parse the URL
        try:
            parsed = urlparse(url)
            if not parsed.netloc and not url.startswith('git@'):
                raise ValidationError("Invalid URL: No network location")

            # For git@ URLs, extract the domain
            if url.startswith('git@'):
                domain = url.split('@')[1].split(':')[0]
            else:
                domain = parsed.netloc

            # Remove port if present
            domain = domain.split(':')[0]


            # Check against allowed domains if specified
            if allowed_domains and domain not in allowed_domains:
                raise ValidationError(f"Domain not allowed: {domain}")

            return url

        except (ValueError, IndexError, AttributeError) as e:
            raise ValidationError(f"Invalid URL: {url}") from e

    @staticmethod
    def validate_config(config: Dict[str, Any], required_fields: Optional[List[str]] = None) -> bool:
        """
        Validate a configuration dictionary.

        Args:
            config: The configuration dictionary to validate
            required_fields: List of required field names

        Returns:
            bool: True if the configuration is valid

        Raises:
            ValidationError: If the configuration is invalid
        """
        if not isinstance(config, dict):
            raise ValidationError("Configuration must be a dictionary")

        if required_fields:
            missing = [field for field in required_fields if field not in config]
            if missing:
                raise ValidationError(f"Missing required configuration fields: {', '.join(missing)}")

        return True

    @staticmethod
    def _is_binary_file(file_path: Path) -> bool:
        """
        Check if a file appears to be binary.

        Args:
            file_path: Path to the file

        Returns:
            bool: True if the file appears to be binary
        """
        # Check file extension first (faster than reading content)
        text_extensions = {
            # Source code
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
            '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.dart', '.sh', '.bash',
            '.zsh', '.fish', '.ps1', '.bat', '.cmd',
            # Config files
            '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.env',
            # Web files
            '.html', '.htm', '.css', '.scss', '.sass', '.less',
            # Data files
            '.csv', '.tsv', '.xml', '.svg',
            # Documentation
            '.md', '.markdown', '.rst', '.txt', '.text'
        }

        # If the file has a known text extension, it's probably text
        if file_path.suffix.lower() in text_extensions:
            return False

        # If the file has no extension, check its content
        try:
            with open(file_path, 'rb') as f:
                # Read first 8KB to check for binary content
                chunk = f.read(8192)
                # Check for null bytes (common in binary files)
                if b'\x00' in chunk:
                    return True
                # Check for common binary file signatures
                for signature, _ in BINARY_SIGNATURES:
                    if chunk.startswith(signature):
                        return True
                # Try to decode as text
                try:
                    chunk.decode('utf-8')
                except UnicodeDecodeError:
                    return True
        except (IOError, OSError):
            return True

        return False

# Create a singleton instance for convenience
validator = InputValidator()
