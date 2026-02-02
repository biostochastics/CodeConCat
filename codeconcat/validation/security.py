"""Security-focused validation functions.

This module provides comprehensive security validation capabilities including:
- File integrity verification using cryptographic hashes
- Detection of suspicious content patterns and potential vulnerabilities
- Binary file detection and analysis
- Integrity manifest generation and verification for directory trees
- Integration with Semgrep for advanced security scanning

The module uses TTL caching for performance optimization and provides
protection against common security threats like SQL injection, path traversal,
and code injection attacks.
"""

import hashlib
import logging
import re
from pathlib import Path
from typing import Any

from cachetools import TTLCache  # type: ignore[import-untyped]

from ..errors import FileIntegrityError, ValidationError
from ..processor.attack_patterns import scan_content as scan_attack_patterns
from ..utils.path_security import PathTraversalError, validate_safe_path
from .semgrep_validator import semgrep_validator

logger = logging.getLogger(__name__)

# Regular expressions for detecting potentially dangerous content
DANGEROUS_PATTERNS = {
    "exec_patterns": re.compile(
        r"""
        \b(exec|eval|system|popen|subprocess\.call|subprocess\.Popen|os\.system|
        child_process\.exec|require\(\s*["']child_process["']\)|
        Runtime\.exec|Process\.start|os\.popen|ShellExecute|WScript\.Shell)\b
        """,
        re.VERBOSE,
    ),
    "sql_injection": re.compile(
        r"""
        (SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\s+
        .*?
        (FROM|INTO|TABLE|DATABASE)\s+
        """,
        re.VERBOSE | re.IGNORECASE,
    ),
    "path_traversal": re.compile(r"\.\./|\.\\|\x00|/etc/passwd"),
    "template_injection": re.compile(r"\{\{.+?\}\}|\$\{.+?\}|<%= .+? %>"),
    "secrets_pattern": re.compile(
        r"""
        (password|passwd|pwd|secret|api[-_]?key|access[-_]?key|auth[-_]?token|
        credential|secret[-_]?key|private[-_]?key)\s*[:=]\s*['"][^'"]{8,}['"]
        """,
        re.VERBOSE | re.IGNORECASE,
    ),
    "base64_pattern": re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),
}

# Common file signatures (magic numbers)
FILE_SIGNATURES = {
    # Executables
    b"\x4d\x5a": {"type": "executable", "description": "Windows PE/DOS executable"},
    b"\x7f\x45\x4c\x46": {"type": "executable", "description": "ELF executable (Linux/Unix)"},
    # Archives
    b"\x50\x4b\x03\x04": {"type": "archive", "description": "ZIP archive"},
    b"\x1f\x8b": {"type": "archive", "description": "GZIP archive"},
    b"\x42\x5a\x68": {"type": "archive", "description": "BZIP2 archive"},
    # Documents
    b"\x25\x50\x44\x46": {"type": "document", "description": "PDF document"},
    b"\xd0\xcf\x11\xe0": {"type": "document", "description": "MS Office document (OLE)"},
    b"\x50\x4b\x03\x04\x14\x00\x06\x00": {
        "type": "document",
        "description": "MS Office document (OOXML)",
    },
    # Images
    b"\xff\xd8\xff": {"type": "image", "description": "JPEG image"},
    b"\x89\x50\x4e\x47": {"type": "image", "description": "PNG image"},
    b"\x47\x49\x46\x38": {"type": "image", "description": "GIF image"},
}

# File hash cache with TTL to avoid recomputing hashes and prevent memory overflow
# Max 10,000 entries with 1-hour TTL
FILE_HASH_CACHE: TTLCache = TTLCache(maxsize=10000, ttl=3600)


class SecurityValidator:
    """Security validator for code content and files.

    This class provides methods for validating file security, detecting suspicious
    patterns, computing and verifying file hashes, and managing integrity manifests.
    It includes integration with external security scanners like Semgrep and uses
    pattern matching to detect common security threats.

    Attributes:
        DANGEROUS_PATTERNS: Dictionary of regex patterns for detecting security threats
        FILE_SIGNATURES: Dictionary of binary file signatures (magic numbers)
        FILE_HASH_CACHE: TTL cache for storing computed file hashes (10k entries, 1hr TTL)

    Example:
        >>> validator = SecurityValidator()
        >>> hash_value = validator.compute_file_hash("/path/to/file.py")
        >>> validator.verify_file_integrity("/path/to/file.py", hash_value)
        >>> findings = validator.check_for_suspicious_content("/path/to/file.py")
    """

    @staticmethod
    def compute_file_hash(
        file_path: str | Path,
        algorithm: str = "sha256",
        use_cache: bool = True,
        max_file_size: int = 100 * 1024 * 1024,  # 100MB default limit
    ) -> str:
        """
        Compute the hash of a file using the specified algorithm.

        Args:
            file_path: Path to the file
            algorithm: Hash algorithm to use (default: sha256)
                Supported: md5, sha1, sha224, sha256, sha384, sha512
            use_cache: Whether to use cached hash if available (default: True)
            max_file_size: Maximum file size to hash in bytes (default: 100MB)

        Returns:
            The file hash as a hexadecimal string

        Raises:
            ValidationError: If the file cannot be read, too large, or algorithm invalid

        Complexity:
            O(n) where n is the file size, with O(1) cache lookup when cached

        Note:
            Uses chunked reading (64KB chunks) to handle large files efficiently
            Enforces file size limit to prevent memory exhaustion
        """
        path = Path(file_path)

        # Check file size before processing to prevent memory exhaustion
        try:
            file_size = path.stat().st_size
            if file_size > max_file_size:
                raise ValidationError(
                    f"File {path} too large ({file_size} bytes > {max_file_size} bytes limit)"
                )
        except OSError as e:
            raise ValidationError(f"Cannot access file {path}", original_exception=e) from e

        # Include mtime in cache key to detect file changes with same size
        mtime = path.stat().st_mtime_ns  # Use nanosecond precision for better accuracy
        cache_key = f"{path.resolve()}:{algorithm}:{file_size}:{mtime}"

        # Return cached hash if available and cache is enabled
        if use_cache and cache_key in FILE_HASH_CACHE:
            return FILE_HASH_CACHE[cache_key]  # type: ignore[no-any-return]

        try:
            hash_func = getattr(hashlib, algorithm)
        except AttributeError as e:
            raise ValidationError(f"Invalid hash algorithm: {algorithm}") from e

        try:
            hasher = hash_func()
            bytes_read = 0
            with open(path, "rb") as f:
                # Read and update hash in larger chunks for better performance
                # but limit total bytes read as a safety measure
                while bytes_read < max_file_size:
                    chunk = f.read(65536)  # 64KB chunks for better I/O performance
                    if not chunk:
                        break
                    hasher.update(chunk)
                    bytes_read += len(chunk)

            file_hash = hasher.hexdigest()
            if use_cache:
                FILE_HASH_CACHE[cache_key] = file_hash
            return file_hash  # type: ignore[no-any-return]
        except Exception as e:
            raise ValidationError(f"Failed to compute hash for {path}", original_exception=e) from e

    @staticmethod
    def verify_file_integrity(
        file_path: str | Path, expected_hash: str, algorithm: str = "sha256"
    ) -> bool:
        """
        Verify the integrity of a file by comparing its hash with the expected value.

        Args:
            file_path: Path to the file
            expected_hash: Expected hash value (case-insensitive)
            algorithm: Hash algorithm to use (default: sha256)

        Returns:
            True if the file hash matches the expected value

        Raises:
            FileIntegrityError: If the hash doesn't match (includes both hashes)
            ValidationError: If hash computation fails

        See Also:
            compute_file_hash: For computing file hashes
            detect_tampering: For checking if a file has been modified
        """
        # Don't use cache for integrity checks to ensure fresh hash computation
        actual_hash = SecurityValidator.compute_file_hash(file_path, algorithm, use_cache=False)

        if actual_hash.lower() != expected_hash.lower():
            raise FileIntegrityError(
                f"File integrity check failed for {file_path}",
                expected_hash=expected_hash,
                actual_hash=actual_hash,
            )

        logger.debug(f"File integrity verified for {file_path}")
        return True

    @staticmethod
    def sanitize_content(content: str, patterns: dict[str, re.Pattern] | None = None) -> str:
        """
        Sanitize content by removing or replacing potentially dangerous patterns.

        Args:
            content: The content to sanitize
            patterns: Optional dictionary of patterns to sanitize (defaults to DANGEROUS_PATTERNS)

        Returns:
            The sanitized content with dangerous patterns replaced or redacted

        Complexity:
            O(n*p) where n is content length and p is number of patterns

        Note:
            - Secrets are redacted with "[REDACTED]" placeholder
            - Other dangerous patterns are replaced with warning comments
            - Original structure is preserved where possible
        """
        if patterns is None:
            patterns = DANGEROUS_PATTERNS

        sanitized = content
        for name, pattern in patterns.items():
            if pattern.search(sanitized):
                logger.warning(f"Potentially dangerous pattern '{name}' detected and removed")
                if name == "secrets_pattern":
                    # Security: Completely remove secrets - never expose them
                    def redact_secret(match):
                        text = match.group()
                        # Find the delimiter and reconstruct with placeholder
                        for delimiter in [":", "="]:
                            if delimiter in text:
                                parts = text.split(delimiter, 1)
                                return parts[0] + delimiter + ' "[REDACTED]"'
                        return "[REDACTED]"

                    sanitized = pattern.sub(redact_secret, sanitized)
                else:
                    # Security: Completely remove dangerous patterns
                    # NEVER embed the original content - it defeats the purpose
                    sanitized = pattern.sub("[REDACTED: POTENTIALLY DANGEROUS CONTENT]", sanitized)

        return sanitized

    @staticmethod
    def check_for_suspicious_content(
        file_path: str | Path, use_semgrep: bool = False
    ) -> list[dict[str, Any]]:
        """
        Check a file for suspicious content patterns.

        Performs multi-layered security analysis:
        1. Binary file detection and signature analysis
        2. Pattern matching for dangerous code patterns
        3. Semgrep scanning (if enabled)
        4. Language-specific attack pattern detection

        Args:
            file_path: Path to the file
            use_semgrep: Whether to use Semgrep for additional scanning

        Returns:
            List of detected suspicious patterns, each containing:
                - type: "pattern" or "semgrep"
                - name: Pattern or rule name
                - severity: "LOW", "MEDIUM", or "HIGH"
                - message: Description of the finding
                - path: File path
                - line: Line number (if applicable)

        Raises:
            ValidationError: If the file cannot be read

        Complexity:
            O(n) for file reading, O(n*p) for pattern matching where p is pattern count
        """
        try:
            path = Path(file_path)
            findings = []

            # First check if it's a binary file to avoid text processing on binary data
            if SecurityValidator.is_binary_file(path):
                with open(path, "rb") as f:
                    # Check the file signature (magic number)
                    header = f.read(16)  # Most signatures are within first 16 bytes

                    # Check against known executable signatures
                    for signature, info in FILE_SIGNATURES.items():
                        if header.startswith(signature) and info["type"] == "executable":
                            findings.append(
                                {
                                    "type": "pattern",
                                    "name": "executable_file",
                                    "severity": "HIGH",
                                    "message": "Executable file detected",
                                    "path": str(path),
                                }
                            )
                            # Executables are high risk, no need for further checks
                            return findings

                findings.append(
                    {
                        "type": "pattern",
                        "name": "binary_file",
                        "severity": "MEDIUM",
                        "message": "Binary file detected",
                        "path": str(path),
                    }
                )
                return findings

            # For text files, read and scan for patterns
            with open(path, errors="replace") as f:
                content = f.read()

            pattern_findings = []
            for name, pattern in DANGEROUS_PATTERNS.items():
                if pattern.search(content):
                    pattern_findings.append(name)
                    findings.append(
                        {
                            "type": "pattern",
                            "name": name,
                            "severity": "MEDIUM" if "secrets" in name else "HIGH",
                            "message": f"Suspicious pattern detected: {name}",
                            "path": str(path),
                        }
                    )

            # Log at debug level instead of warning
            if pattern_findings:
                logger.debug("Suspicious patterns in %s: %s", path, ", ".join(pattern_findings))

            # Use semgrep if available and requested
            if use_semgrep and semgrep_validator.is_available():
                try:
                    logger.debug(f"Running semgrep scan on {path}")
                    semgrep_findings = semgrep_validator.scan_file(path)
                    if semgrep_findings:
                        findings.extend(semgrep_findings)
                        logger.warning(f"Semgrep found {len(semgrep_findings)} issues in {path}")
                except Exception as e:
                    logger.warning(f"Semgrep scan failed for {path}: {e}")

            # Use comprehensive attack patterns for language-specific vulnerabilities
            # Map file extensions to programming languages
            extension_map = {
                ".py": "python",
                ".js": "javascript",
                ".jsx": "javascript",
                ".ts": "typescript",
                ".tsx": "typescript",
                ".c": "c",
                ".cpp": "cpp",
                ".cc": "cpp",
                ".cxx": "cpp",
                ".h": "c",
                ".hpp": "cpp",
                ".cs": "csharp",
                ".go": "go",
                ".php": "php",
                ".r": "r",
                ".R": "r",
                ".jl": "julia",
                ".rs": "rust",
                ".java": "java",
            }

            suffix = path.suffix.lower()
            language = extension_map.get(suffix)

            if language:
                try:
                    attack_findings = scan_attack_patterns(content, language)
                    for finding in attack_findings:
                        findings.append(
                            {
                                "type": "pattern",
                                "name": finding["name"],
                                "severity": finding["severity"],
                                "message": finding["message"],
                                "path": str(path),
                                "line": finding.get("line", 0),
                                "cwe_id": finding.get("cwe_id", ""),
                            }
                        )
                except Exception as e:
                    logger.warning(f"Attack pattern scan failed for {path}: {e}")

            return findings

        except Exception as e:
            raise ValidationError(
                f"Failed to check file for suspicious content: {path}", original_exception=e
            ) from e

    @staticmethod
    def detect_tampering(
        file_path: str | Path, original_hash: str, algorithm: str = "sha256"
    ) -> bool:
        """
        Detect if a file has been tampered with by comparing its current hash with the original.

        Args:
            file_path: Path to the file
            original_hash: Original hash value to compare against
            algorithm: Hash algorithm to use (default: sha256)

        Returns:
            True if tampering is detected (hashes don't match), False otherwise

        Raises:
            ValidationError: If hash computation fails

        Note:
            Always computes fresh hash (use_cache=False) to ensure current state

        See Also:
            verify_file_integrity: For strict integrity checking that raises on mismatch
        """
        current_hash = SecurityValidator.compute_file_hash(file_path, algorithm, use_cache=False)
        is_tampered = current_hash.lower() != original_hash.lower()

        if is_tampered:
            logger.warning(f"Possible file tampering detected for {file_path}")

        return is_tampered

    @staticmethod
    def is_binary_file(file_path: str | Path) -> bool:
        """
        Check if a file is binary.

        Uses multiple heuristics:
        1. File extension check against known text formats
        2. Null byte detection
        3. UTF-8 decoding test

        Args:
            file_path: Path to the file

        Returns:
            True if the file appears to be binary, False otherwise

        Complexity:
            O(1) for extension check, O(n) for content check where n = min(file_size, 8192)

        Note:
            Returns True on any file access error (fail-safe approach)
        """
        try:
            path = Path(file_path)

            # Always check content first to avoid bypass via renamed files
            # Read a chunk of the file for content analysis
            with open(path, "rb") as f:
                chunk = f.read(8192)

            # Files with null bytes are usually binary
            if b"\x00" in chunk:
                return True

            # Try to decode as UTF-8, with Latin-1 fallback for legacy encodings
            try:
                chunk.decode("utf-8")
                return False  # Successfully decoded as UTF-8 text
            except UnicodeDecodeError:
                # Try Latin-1 (ISO-8859-1) which accepts any byte sequence
                # but check for high density of control characters
                try:
                    decoded = chunk.decode("latin-1")
                    # Count non-printable control characters (except common whitespace)
                    control_chars = sum(1 for c in decoded if ord(c) < 32 and c not in "\t\n\r")
                    # If more than 10% control characters, likely binary
                    # Appears to be Latin-1 text if condition is False
                    return len(decoded) > 0 and control_chars / len(decoded) > 0.1
                except (UnicodeDecodeError, ValueError) as e:
                    # Latin-1 should accept any byte sequence, but log if it fails
                    logger.debug(f"Latin-1 decode failed for {file_path}: {e}")
                    return True  # Failed to decode, assume binary

        except OSError as e:
            # File access error - log and assume binary for safety
            logger.warning(f"Cannot read file for binary detection: {file_path}: {e}")
            return True

    @staticmethod
    def generate_integrity_manifest(
        directory: str | Path, recursive: bool = True
    ) -> dict[str, str]:
        """
        Generate an integrity manifest for all files in a directory.

        The manifest is a dictionary mapping relative file paths to their SHA-256 hashes.
        This can be used later to verify that files haven't been tampered with.

        Args:
            directory: Path to the directory
            recursive: If True, include files in subdirectories (default: True)

        Returns:
            Dictionary mapping relative file paths (POSIX format) to their SHA-256 hashes

        Raises:
            ValidationError: If the directory cannot be read or is not a directory

        Complexity:
            O(n*m) where n is number of files and m is average file size

        Example:
            >>> manifest = SecurityValidator.generate_integrity_manifest("/project")
            >>> # Save manifest for later verification
            >>> with open("manifest.json", "w") as f:
            ...     json.dump(manifest, f)

        See Also:
            verify_integrity_manifest: For verifying files against a manifest
        """
        try:
            base_path = Path(directory).resolve()
            manifest = {}

            if not base_path.is_dir():
                raise ValidationError(f"Not a directory: {directory}")

            if recursive:
                # Security: Don't follow symlinks to prevent escape
                files = [
                    p
                    for p in base_path.glob("**/*")
                    if p.is_file()
                    and not p.is_symlink()
                    and validate_safe_path(p, base_path=base_path, allow_symlinks=False)
                ]
            else:
                files = [
                    p
                    for p in base_path.iterdir()
                    if p.is_file()
                    and not p.is_symlink()
                    and validate_safe_path(p, base_path=base_path, allow_symlinks=False)
                ]

            for file_path in files:
                try:
                    rel_path = file_path.relative_to(base_path).as_posix()
                    hash_value = SecurityValidator.compute_file_hash(file_path)
                    manifest[rel_path] = hash_value
                except (PathTraversalError, ValueError) as e:
                    logger.warning(
                        f"Skipping file due to path validation failure: {file_path} - {e}"
                    )
                    continue

            return manifest

        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(
                f"Failed to generate integrity manifest for {directory}", original_exception=e
            ) from e

    @staticmethod
    def verify_integrity_manifest(
        directory: str | Path, manifest: dict[str, str]
    ) -> dict[str, dict[str, bool | str]]:
        """
        Verify file integrity using a previously generated manifest.

        Args:
            directory: Base directory containing the files
            manifest: Dictionary mapping relative file paths to their expected hashes

        Returns:
            Dictionary mapping file paths to verification results:
            {
                "file_path": {
                    "verified": True/False,
                    "expected_hash": "...",
                    "actual_hash": "...",
                    "reason": "..." (if verification failed)
                }
            }

        Complexity:
            O(n*m) where n is number of files and m is average file size

        Note:
            - Always computes fresh hashes (use_cache=False)
            - Hash comparison is case-insensitive
            - Includes detailed failure reasons (file not found, hash mismatch, errors)

        Example:
            >>> results = SecurityValidator.verify_integrity_manifest("/project", manifest)
            >>> for path, result in results.items():
            ...     if not result["verified"]:
            ...         print(f"Failed: {path} - {result['reason']}")
        """
        base_path = Path(directory).resolve()
        results = {}
        manifest_files: set[Path] = set()

        # Validate manifest entries and compute hashes
        for rel_path, expected_hash in manifest.items():
            result = {
                "verified": False,
                "expected_hash": expected_hash,
                "actual_hash": "",
                "reason": "",
                "unexpected": False,
            }

            try:
                # Security: Validate path to prevent traversal
                # This blocks patterns like "../etc/passwd"
                try:
                    validated_path = validate_safe_path(
                        rel_path, base_path=base_path, allow_symlinks=False
                    )
                    manifest_files.add(validated_path)
                except PathTraversalError as e:
                    result["reason"] = f"Path traversal detected: {e}"
                    results[rel_path] = result
                    logger.warning(f"Blocked path traversal attempt in manifest: {rel_path}")
                    continue

                if not validated_path.exists():
                    result["reason"] = "File not found"
                else:
                    actual_hash = SecurityValidator.compute_file_hash(
                        validated_path, use_cache=False
                    )
                    result["actual_hash"] = actual_hash

                    if actual_hash.lower() == expected_hash.lower():
                        result["verified"] = True
                    else:
                        result["reason"] = "Hash mismatch"

            except Exception as e:
                result["reason"] = f"Error: {str(e)}"

            results[rel_path] = result

        # Bidirectional verification: Detect unexpected files not in manifest
        # This catches supply-chain attacks where new files are added
        try:
            for file_path in base_path.glob("**/*"):
                # Security: Skip symlinks to prevent directory escape attacks
                if file_path.is_symlink():
                    logger.debug(f"Skipping symlink during verification: {file_path}")
                    continue

                # Security: Validate path is within base_path before processing
                try:
                    validated_path = validate_safe_path(
                        file_path, base_path=base_path, allow_symlinks=False
                    )
                except PathTraversalError:
                    logger.warning(f"Skipping file with invalid path: {file_path}")
                    continue

                if validated_path.is_file() and validated_path not in manifest_files:
                    rel_path_str = validated_path.relative_to(base_path).as_posix()
                    results[rel_path_str] = {
                        "verified": False,
                        "expected_hash": "",
                        "actual_hash": SecurityValidator.compute_file_hash(
                            validated_path, use_cache=False
                        ),
                        "reason": "File not in manifest (unexpected file)",
                        "unexpected": True,
                    }
                    logger.warning(f"Unexpected file detected: {rel_path_str}")
        except Exception as e:
            logger.error(f"Error during bidirectional verification: {e}")

        return results  # type: ignore[return-value]


# Create a singleton instance
security_validator = SecurityValidator()
