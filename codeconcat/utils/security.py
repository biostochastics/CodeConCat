"""
Security Utilities for CodeConCat

This module provides security utilities including path validation,
input sanitization, and rate limiting.
"""

import hashlib
import logging
import os
import re
import secrets
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Union

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Base exception for security-related errors."""

    pass


class PathTraversalError(SecurityError):
    """Exception raised when path traversal is detected."""

    pass


class RateLimitError(SecurityError):
    """Exception raised when rate limit is exceeded."""

    pass


class PathValidator:
    """
    Validates file paths to prevent path traversal attacks.
    """

    # Dangerous path patterns
    DANGEROUS_PATTERNS = [
        r"\.\.",  # Parent directory
        r"~",  # Home directory
        r"\$",  # Environment variables
        r"%",  # Windows environment variables
        r"\x00",  # Null bytes
        r"[\<\>\|]",  # Shell redirection
        r"&",  # Command chaining
    ]

    @classmethod
    def validate_path(
        cls,
        base_path: Union[str, Path],
        requested_path: Union[str, Path],
        allow_symlinks: bool = False,
    ) -> Path:
        """
        Validate that a path is within the allowed directory.

        Args:
            base_path: The base directory that paths must be within
            requested_path: The path to validate
            allow_symlinks: Whether to allow symbolic links

        Returns:
            The validated absolute path

        Raises:
            PathTraversalError: If path traversal is detected
        """
        # Convert to Path objects
        base = Path(base_path).resolve()

        # Check for dangerous patterns in the string representation
        path_str = str(requested_path)
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, path_str):
                raise PathTraversalError(f"Dangerous pattern detected in path: {pattern}")

        # Resolve the requested path
        try:
            if os.path.isabs(requested_path):
                # Absolute path provided
                requested = Path(requested_path).resolve()
            else:
                # Relative path - join with base
                requested = (base / requested_path).resolve()
        except (OSError, RuntimeError) as e:
            raise PathTraversalError(f"Invalid path: {e}") from e

        # Check if path is within base directory
        try:
            requested.relative_to(base)
        except ValueError as e:
            raise PathTraversalError(
                f"Path traversal attempt: {requested} is outside {base}"
            ) from e

        # Check for symlinks if not allowed
        if not allow_symlinks and requested.is_symlink():
            raise PathTraversalError(f"Symbolic links not allowed: {requested}")

        return requested

    @classmethod
    def sanitize_filename(cls, filename: str, max_length: int = 255) -> str:
        """
        Sanitize a filename to remove dangerous characters.

        Args:
            filename: The filename to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized filename
        """
        # Remove path separators and null bytes
        sanitized = re.sub(r"[/\\:\x00]", "_", filename)

        # Remove other dangerous characters
        sanitized = re.sub(r'[<>"|?*]', "_", sanitized)

        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip(". ")

        # Remove leading dash (can be interpreted as option)
        sanitized = sanitized.lstrip("-")

        # Ensure not empty
        if not sanitized:
            sanitized = "unnamed"

        # Truncate to max length
        if len(sanitized) > max_length:
            # Keep extension if present
            parts = sanitized.rsplit(".", 1)
            if len(parts) == 2 and len(parts[1]) <= 10:
                # Has extension
                name_part = parts[0][: max_length - len(parts[1]) - 1]
                sanitized = f"{name_part}.{parts[1]}"
            else:
                sanitized = sanitized[:max_length]

        return sanitized


class InputSanitizer:
    """
    Sanitizes user input to prevent injection attacks.
    """

    @staticmethod
    def sanitize_command_arg(arg: str) -> str:
        """
        Sanitize a command line argument.

        Args:
            arg: The argument to sanitize

        Returns:
            Sanitized argument
        """
        # Remove shell metacharacters
        dangerous_chars = ";|&$<>`\\\"'"
        for char in dangerous_chars:
            arg = arg.replace(char, "")

        # Remove newlines and other control characters
        arg = re.sub(r"[\x00-\x1f\x7f]", "", arg)

        return arg

    @staticmethod
    def sanitize_url(url: str) -> Optional[str]:
        """
        Sanitize and validate a URL.

        Args:
            url: The URL to sanitize

        Returns:
            Sanitized URL or None if invalid
        """
        # Basic URL validation
        url_pattern = re.compile(
            r"^https?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
            r"localhost|"  # localhost
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )

        if not url_pattern.match(url):
            return None

        # Remove any Javascript or data URIs
        if url.lower().startswith(("javascript:", "data:", "vbscript:")):
            return None

        return url

    @staticmethod
    def sanitize_regex(pattern: str, max_length: int = 1000) -> str:
        """
        Sanitize a regex pattern to prevent ReDoS attacks.

        Args:
            pattern: The regex pattern to sanitize
            max_length: Maximum allowed pattern length

        Returns:
            Sanitized pattern
        """
        # Truncate if too long
        if len(pattern) > max_length:
            pattern = pattern[:max_length]

        # Check for dangerous patterns
        dangerous_patterns = [
            r"(\w+)+",  # Catastrophic backtracking
            r"(.*)+",  # Catastrophic backtracking
            r"(.+)+",  # Catastrophic backtracking
        ]

        for dangerous in dangerous_patterns:
            if dangerous in pattern:
                logger.warning(f"Potentially dangerous regex pattern detected: {dangerous}")
                # Replace with safer version
                pattern = pattern.replace(dangerous, dangerous[:-1])

        return pattern


class RateLimiter:
    """
    Rate limiter for API endpoints and operations.
    """

    def __init__(
        self, max_requests: int = 100, window_seconds: int = 60, burst_size: Optional[int] = None
    ):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            burst_size: Maximum burst size (defaults to max_requests)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.burst_size = burst_size or max_requests

        # Store request timestamps per identifier
        self.requests: Dict[str, deque] = defaultdict(lambda: deque())

        # Store burst tokens per identifier
        self.burst_tokens: Dict[str, int] = defaultdict(lambda: self.burst_size)
        self.last_refill: Dict[str, datetime] = {}

    def check_rate_limit(self, identifier: str, cost: int = 1) -> tuple[bool, Optional[float]]:
        """
        Check if request is within rate limit.

        Args:
            identifier: Unique identifier (e.g., IP, user ID)
            cost: Cost of this request (default 1)

        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        now = datetime.now()

        # Clean old requests
        self._clean_old_requests(identifier, now)

        # Refill burst tokens if needed
        self._refill_burst_tokens(identifier, now)

        # Check rate limit
        request_count = len(self.requests[identifier])

        if request_count + cost > self.max_requests:
            # Calculate retry after
            if self.requests[identifier]:
                oldest = self.requests[identifier][0]
                retry_after = (
                    oldest + timedelta(seconds=self.window_seconds) - now
                ).total_seconds()
                retry_after = max(0, retry_after)
            else:
                retry_after = 0

            return False, retry_after

        # Check burst limit
        if self.burst_tokens[identifier] < cost:
            return False, 1.0  # Try again in 1 second

        # Allow request
        for _ in range(cost):
            self.requests[identifier].append(now)
        self.burst_tokens[identifier] -= cost

        return True, None

    def _clean_old_requests(self, identifier: str, now: datetime):
        """Remove requests outside the time window."""
        cutoff = now - timedelta(seconds=self.window_seconds)

        while self.requests[identifier] and self.requests[identifier][0] < cutoff:
            self.requests[identifier].popleft()

    def _refill_burst_tokens(self, identifier: str, now: datetime):
        """Refill burst tokens over time."""
        if identifier not in self.last_refill:
            self.last_refill[identifier] = now
            return

        # Calculate tokens to refill
        time_passed = (now - self.last_refill[identifier]).total_seconds()
        tokens_to_add = int(time_passed * self.burst_size / self.window_seconds)

        if tokens_to_add > 0:
            self.burst_tokens[identifier] = min(
                self.burst_size, self.burst_tokens[identifier] + tokens_to_add
            )
            self.last_refill[identifier] = now

    def reset(self, identifier: Optional[str] = None):
        """
        Reset rate limit for an identifier or all identifiers.

        Args:
            identifier: Specific identifier to reset, or None for all
        """
        if identifier:
            self.requests[identifier].clear()
            self.burst_tokens[identifier] = self.burst_size
            if identifier in self.last_refill:
                del self.last_refill[identifier]
        else:
            self.requests.clear()
            self.burst_tokens.clear()
            self.last_refill.clear()


class SecureHash:
    """
    Secure hashing utilities.
    """

    @staticmethod
    def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
        """
        Hash a password using PBKDF2.

        Args:
            password: Password to hash
            salt: Optional salt (generated if not provided)

        Returns:
            Tuple of (hash, salt) as hex strings
        """
        if salt is None:
            salt = secrets.token_bytes(32)

        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)  # iterations

        return key.hex(), salt.hex()

    @staticmethod
    def verify_password(password: str, hash_hex: str, salt_hex: str) -> bool:
        """
        Verify a password against a hash.

        Args:
            password: Password to verify
            hash_hex: Hash as hex string
            salt_hex: Salt as hex string

        Returns:
            True if password matches
        """
        salt = bytes.fromhex(salt_hex)
        computed_hash, _ = SecureHash.hash_password(password, salt)

        # Use constant-time comparison
        return secrets.compare_digest(computed_hash, hash_hex)

    @staticmethod
    def generate_token(length: int = 32) -> str:
        """
        Generate a secure random token.

        Args:
            length: Token length in bytes

        Returns:
            Token as hex string
        """
        return secrets.token_hex(length)


# Global rate limiter instance
_global_rate_limiter = RateLimiter()


def check_rate_limit(identifier: str, cost: int = 1) -> tuple[bool, Optional[float]]:
    """Check global rate limit."""
    return _global_rate_limiter.check_rate_limit(identifier, cost)


def validate_path(base_path: Union[str, Path], requested_path: Union[str, Path]) -> Path:
    """Validate a path against traversal attacks."""
    return PathValidator.validate_path(base_path, requested_path)


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename."""
    return PathValidator.sanitize_filename(filename)
