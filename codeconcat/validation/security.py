"""Security-focused validation functions."""

import hashlib
import logging
import re
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..errors import ValidationError
from .semgrep_validator import semgrep_validator
from ..processor.attack_patterns import scan_content as scan_attack_patterns

logger = logging.getLogger(__name__)

# Regular expressions for detecting potentially dangerous content
DANGEROUS_PATTERNS = {
    "exec_patterns": re.compile(
        r"""
        (exec|eval|system|popen|subprocess\.call|subprocess\.Popen|os\.system|
        child_process\.exec|require\(\s*["']child_process["']\)|
        Runtime\.exec|Process\.start|os\.popen|ShellExecute|WScript\.Shell)
        """,
        re.VERBOSE,
    ),
    "sql_injection": re.compile(
        r"""
        (SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\s+
        .*?
        (FROM|INTO|TABLE|DATABASE)\s+
        """,
        re.VERBOSE,
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

# File hash cache to avoid recomputing hashes
FILE_HASH_CACHE: Dict[str, str] = {}
FILE_HASH_CACHE_LOCK = threading.Lock()


class SecurityValidator:
    """Security validator for code content and files."""

    @staticmethod
    def compute_file_hash(
        file_path: Union[str, Path], algorithm: str = "sha256", use_cache: bool = True
    ) -> str:
        """
        Compute the hash of a file using the specified algorithm.

        Args:
            file_path: Path to the file
            algorithm: Hash algorithm to use (default: sha256)
            use_cache: Whether to use cached hash if available (default: True)

        Returns:
            The file hash as a hexadecimal string

        Raises:
            ValidationError: If the file cannot be read or the algorithm is invalid
        """
        path = Path(file_path)
        cache_key = f"{path.resolve()}:{algorithm}"

        # Return cached hash if available and cache is enabled
        if use_cache:
            with FILE_HASH_CACHE_LOCK:
                if cache_key in FILE_HASH_CACHE:
                    return FILE_HASH_CACHE[cache_key]

        try:
            hash_func = getattr(hashlib, algorithm)
        except AttributeError:
            raise ValidationError(f"Invalid hash algorithm: {algorithm}")

        try:
            hasher = hash_func()
            with open(path, "rb") as f:
                # Read and update hash in chunks to avoid loading large files into memory
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)

            file_hash = hasher.hexdigest()
            if use_cache:
                with FILE_HASH_CACHE_LOCK:
                    FILE_HASH_CACHE[cache_key] = file_hash
            return file_hash
        except Exception as e:
            raise ValidationError(f"Failed to compute hash for {path}", original_exception=e)

    @staticmethod
    def verify_file_integrity(
        file_path: Union[str, Path], expected_hash: str, algorithm: str = "sha256"
    ) -> bool:
        """
        Verify the integrity of a file by comparing its hash with the expected value.

        Args:
            file_path: Path to the file
            expected_hash: Expected hash value
            algorithm: Hash algorithm to use (default: sha256)

        Returns:
            True if the file hash matches the expected value

        Raises:
            ValidationError: If the hash doesn't match or computation fails
        """
        actual_hash = SecurityValidator.compute_file_hash(file_path, algorithm)

        if actual_hash.lower() != expected_hash.lower():
            raise ValidationError(
                f"File integrity check failed for {file_path}. "
                f"Expected hash: {expected_hash}, actual hash: {actual_hash}"
            )

        logger.debug(f"File integrity verified for {file_path}")
        return True

    @staticmethod
    def sanitize_content(content: str, patterns: Optional[Dict[str, re.Pattern]] = None) -> str:
        """
        Sanitize content by removing or replacing potentially dangerous patterns.

        Args:
            content: The content to sanitize
            patterns: Optional dictionary of patterns to sanitize

        Returns:
            The sanitized content
        """
        if patterns is None:
            patterns = DANGEROUS_PATTERNS

        sanitized = content
        for name, pattern in patterns.items():
            if pattern.search(sanitized):
                logger.warning(f"Potentially dangerous pattern '{name}' detected")
                if name == "secrets_pattern":
                    # Redact secrets but keep the structure
                    sanitized = pattern.sub(
                        lambda m: m.group().split("=")[0] + '= "[REDACTED]"', sanitized
                    )
                else:
                    # For other patterns, add warning comment
                    sanitized = pattern.sub(
                        r"/* POTENTIALLY DANGEROUS CONTENT REMOVED: \g<0> */", sanitized
                    )

        return sanitized

    @staticmethod
    def check_for_suspicious_content(
        file_path: Union[str, Path], use_semgrep: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Check a file for suspicious content patterns.

        Args:
            file_path: Path to the file

        Returns:
            List of detected suspicious patterns

        Raises:
            ValidationError: If the file cannot be read
        """
        try:
            path = Path(file_path)
            findings = []

            # First check if it's a binary file
            if SecurityValidator.is_binary_file(path):
                with open(path, "rb") as f:
                    # Check the file signature
                    header = f.read(16)  # Read first 16 bytes

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
            with open(path, "r", errors="replace") as f:
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

            if pattern_findings:
                logger.warning(
                    f"Suspicious content detected in {path}: {', '.join(pattern_findings)}"
                )

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

            # Use comprehensive attack patterns
            # Detect language from file extension
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
            )

    @staticmethod
    def detect_tampering(
        file_path: Union[str, Path], original_hash: str, algorithm: str = "sha256"
    ) -> bool:
        """
        Detect if a file has been tampered with by comparing its current hash with the original.

        Args:
            file_path: Path to the file
            original_hash: Original hash value
            algorithm: Hash algorithm to use (default: sha256)

        Returns:
            True if tampering is detected, False otherwise

        Raises:
            ValidationError: If hash computation fails
        """
        current_hash = SecurityValidator.compute_file_hash(file_path, algorithm, use_cache=False)
        is_tampered = current_hash.lower() != original_hash.lower()

        if is_tampered:
            logger.warning(f"Possible file tampering detected for {file_path}")

        return is_tampered

    @staticmethod
    def is_binary_file(file_path: Union[str, Path]) -> bool:
        """
        Check if a file is binary.

        Args:
            file_path: Path to the file

        Returns:
            True if the file appears to be binary, False otherwise
        """
        try:
            path = Path(file_path)

            # Check extension first
            suffix = path.suffix.lower()

            # Common text file extensions
            text_extensions = {
                ".txt",
                ".md",
                ".py",
                ".js",
                ".ts",
                ".html",
                ".css",
                ".json",
                ".xml",
                ".yaml",
                ".yml",
                ".toml",
                ".ini",
                ".c",
                ".cpp",
                ".h",
                ".hpp",
                ".java",
                ".cs",
                ".go",
                ".rb",
                ".php",
                ".rs",
                ".sh",
                ".bat",
                ".ps1",
            }

            if suffix in text_extensions:
                return False

            # Check content
            with open(path, "rb") as f:
                chunk = f.read(8192)

            # Files with null bytes are usually binary
            if b"\x00" in chunk:
                return True

            # Try to decode as UTF-8
            try:
                chunk.decode("utf-8")
                return False  # Successfully decoded as text
            except UnicodeDecodeError:
                return True  # Failed to decode as text

        except Exception:
            # If we can't determine, assume it's binary to be safe
            return True

    @staticmethod
    def generate_integrity_manifest(
        directory: Union[str, Path], recursive: bool = True
    ) -> Dict[str, str]:
        """
        Generate an integrity manifest for all files in a directory.

        The manifest is a dictionary mapping relative file paths to their SHA-256 hashes.
        This can be used later to verify that files haven't been tampered with.

        Args:
            directory: Path to the directory
            recursive: If True, include files in subdirectories

        Returns:
            Dictionary mapping relative file paths to their hashes

        Raises:
            ValidationError: If the directory cannot be read
        """
        try:
            base_path = Path(directory).resolve()
            manifest = {}

            if not base_path.is_dir():
                raise ValidationError(f"Not a directory: {directory}")

            if recursive:
                files = [p for p in base_path.glob("**/*") if p.is_file()]
            else:
                files = [p for p in base_path.iterdir() if p.is_file()]

            for file_path in files:
                rel_path = file_path.relative_to(base_path).as_posix()
                hash_value = SecurityValidator.compute_file_hash(file_path)
                manifest[rel_path] = hash_value

            return manifest

        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(
                f"Failed to generate integrity manifest for {directory}", original_exception=e
            )

    @staticmethod
    def verify_integrity_manifest(
        directory: Union[str, Path], manifest: Dict[str, str]
    ) -> Dict[str, Dict[str, Union[bool, str]]]:
        """
        Verify file integrity using a previously generated manifest.

        Args:
            directory: Base directory containing the files
            manifest: Dictionary mapping relative file paths to their hashes

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
        """
        base_path = Path(directory).resolve()
        results = {}

        for rel_path, expected_hash in manifest.items():
            file_path = base_path / rel_path
            result = {
                "verified": False,
                "expected_hash": expected_hash,
                "actual_hash": "",
                "reason": "",
            }

            try:
                if not file_path.exists():
                    result["reason"] = "File not found"
                else:
                    actual_hash = SecurityValidator.compute_file_hash(file_path, use_cache=False)
                    result["actual_hash"] = actual_hash

                    if actual_hash.lower() == expected_hash.lower():
                        result["verified"] = True
                    else:
                        result["reason"] = "Hash mismatch"

            except Exception as e:
                result["reason"] = f"Error: {str(e)}"

            results[rel_path] = result

        return results


# Create a singleton instance
security_validator = SecurityValidator()
