# Define custom exceptions for CodeConCat

from typing import Any


class CodeConcatError(Exception):
    """Base class for CodeConCat errors.

    This base class uses a flexible constructor that accepts additional
    keyword arguments, allowing derived classes to add specific fields
    while maintaining Liskov Substitution Principle compliance.

    Attributes:
        message: The error message describing the issue.
        **kwargs: Additional fields specific to derived classes.

    Example:
        >>> raise CodeConcatError("Configuration failed", config_file=".codeconcat.yml")
    """

    def __init__(self, message: str, **kwargs):
        """Initialize the error with a message and optional additional fields.

        Args:
            message: The error message describing the issue.
            **kwargs: Additional fields specific to derived classes.
                Common fields include: file_path, field, value, setting_name.
        """
        super().__init__(message)
        self.message = message
        self._additional_fields = kwargs

        # Store commonly used fields as attributes
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self) -> str:
        """Return a string representation of the error."""
        return self.message


class ValidationError(CodeConcatError):
    """Raised when input validation fails.

    This error is raised when input data fails validation checks, such as invalid
    file paths, unsupported file types, or malformed configurations.

    Attributes:
        message: Explanation of the validation error.
        field: The name of the field that failed validation (optional).
        value: The invalid value that caused the error (optional).
        original_exception: The original exception that caused this error (optional).

    Example:
        >>> raise ValidationError(
        ...     "Invalid output format",
        ...     field="format",
        ...     value="invalid_format"
        ... )
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any = None,
        original_exception: Exception | None = None,
        **kwargs,
    ):
        """Initialize a validation error.

        Args:
            message: The error message describing the validation failure.
            field: The name of the field that failed validation.
            value: The invalid value that caused the error.
            original_exception: The original exception if any.
            **kwargs: Additional fields for derived classes.
        """
        super().__init__(
            message, field=field, value=value, original_exception=original_exception, **kwargs
        )

    def __str__(self) -> str:
        """Return a detailed string representation of the validation error."""
        parts = [self.message]
        if hasattr(self, "field") and self.field:
            parts.append(f"Field: {self.field}")
        if hasattr(self, "value") and self.value is not None:
            parts.append(f"Value: {self.value!r}")
        if hasattr(self, "original_exception") and self.original_exception:
            parts.append(f"Original error: {str(self.original_exception)}")
        return " | ".join(parts)


class ConfigurationError(CodeConcatError):
    """Errors related to configuration loading or validation.

    This exception is raised when configuration files are malformed,
    required settings are missing, or configuration values are invalid.

    Attributes:
        config_file: Path to the configuration file that caused the error (optional).
        setting_name: Name of the specific setting that failed (optional).

    Example:
        >>> raise ConfigurationError(
        ...     "Invalid output format",
        ...     config_file=".codeconcat.yml",
        ...     setting_name="format"
        ... )
    """

    def __init__(
        self,
        message: str,
        config_file: str | None = None,
        setting_name: str | None = None,
        **kwargs,
    ):
        """Initialize a configuration error.

        Args:
            message: The error message describing the configuration issue.
            config_file: Path to the configuration file (optional).
            setting_name: Name of the problematic setting (optional).
            **kwargs: Additional fields for derived classes.
        """
        super().__init__(message, config_file=config_file, setting_name=setting_name, **kwargs)

    def __str__(self) -> str:
        """Return a string representation with config details if available."""
        base = super().__str__()
        parts = [base]
        if hasattr(self, "config_file") and self.config_file:
            parts.append(f"Config file: {self.config_file}")
        if hasattr(self, "setting_name") and self.setting_name:
            parts.append(f"Setting: {self.setting_name}")
        return " | ".join(parts)


class FileProcessingError(CodeConcatError):
    """Errors during file collection or initial processing.

    This exception is raised when files cannot be read, parsed, or processed
    due to I/O errors, encoding issues, or other file-related problems.

    Attributes:
        file_path: Path to the file that caused the error (optional).
        original_exception: The original exception that caused this error (optional).

    Example:
        >>> raise FileProcessingError(
        ...     "Could not read file",
        ...     file_path="/path/to/file.py"
        ... )
    """

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        original_exception: Exception | None = None,
        **kwargs,
    ):
        """Initialize a file processing error.

        Args:
            message: The error message describing the processing failure.
            file_path: Path to the file that caused the error.
            original_exception: The original exception if any.
            **kwargs: Additional fields for derived classes.
        """
        super().__init__(
            message, file_path=file_path, original_exception=original_exception, **kwargs
        )

    def __str__(self) -> str:
        """Return a string representation with file path if available."""
        base = super().__str__()
        if hasattr(self, "file_path") and self.file_path:
            return f"{base} (File: {self.file_path})"
        return base


class ParserError(FileProcessingError):
    """Base class for parsing errors.

    This exception is raised when code parsing fails due to syntax errors,
    unsupported language features, or parser configuration issues.

    Attributes:
        file_path: Path to the file being parsed (optional).
        line_number: Line number where the parsing error occurred (optional).
        original_exception: The original exception that caused this error (optional).

    Example:
        >>> raise ParserError(
        ...     "Could not parse Python syntax",
        ...     file_path="/path/to/file.py",
        ...     line_number=42
        ... )
    """

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        line_number: int | None = None,
        original_exception: Exception | None = None,
        **kwargs,
    ):
        """Initialize a parser error.

        Args:
            message: The error message describing the parsing failure.
            file_path: Path to the file being parsed.
            line_number: Line number where the error occurred.
            original_exception: The original exception if any.
            **kwargs: Additional fields for derived classes.
        """
        super().__init__(
            message,
            file_path=file_path,
            original_exception=original_exception,
            line_number=line_number,
            **kwargs,
        )

    def __str__(self) -> str:
        """Return a string representation with line number if available."""
        base = super().__str__()
        if hasattr(self, "line_number") and self.line_number is not None:
            return f"{base} (Line: {self.line_number})"
        return base


class LanguageParserError(ParserError):
    """Errors specific to a language parser.

    This exception is raised when a language-specific parser encounters
    an error, such as unsupported syntax or parser configuration issues.

    Attributes:
        file_path: Path to the file being parsed (inherited).
        line_number: Line number where the error occurred (inherited).
        language: The programming language that caused the error.

    Example:
        >>> raise LanguageParserError(
        ...     "Unsupported Rust syntax pattern",
        ...     file_path="/path/to/file.rs",
        ...     language="rust"
        ... )
    """

    pass


class UnsupportedLanguageError(ParserError):
    """Language determined but no parser available.

    This exception is raised when a file's language can be identified
    but no suitable parser exists for processing.

    Attributes:
        file_path: Path to the file (inherited).
        language: The unsupported programming language identifier.
        line_number: Line number if applicable (inherited).

    Example:
        >>> raise UnsupportedLanguageError(
        ...     "No parser available for ABC language",
        ...     file_path="/path/to/file.abc",
        ...     language="abc"
        ... )
    """

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        language: str | None = None,
        line_number: int | None = None,
        original_exception: Exception | None = None,
        **kwargs,
    ):
        """Initialize an unsupported language error.

        Args:
            message: The error message describing the issue.
            file_path: Path to the file.
            language: The unsupported language identifier.
            line_number: Line number if applicable.
            original_exception: The original exception if any.
            **kwargs: Additional fields for derived classes.
        """
        super().__init__(
            message,
            file_path=file_path,
            line_number=line_number,
            original_exception=original_exception,
            language=language,
            **kwargs,
        )

    def __str__(self) -> str:
        """Return a string representation with language if available."""
        base = super().__str__()
        if hasattr(self, "language") and self.language is not None:
            return f"{base} (Language: {self.language})"
        return base


# Security-specific validation errors
class SecurityValidationError(ValidationError):
    """Base class for security-related validation errors.

    This exception is raised when security checks detect potential threats,
    such as dangerous code patterns, suspicious content, or policy violations.

    Attributes:
        field: The configuration field that triggered the error (inherited).
        value: The invalid value that caused the error (inherited).

    Example:
        >>> raise SecurityValidationError(
        ...     "Suspicious code pattern detected",
        ...     field="custom_patterns",
        ...     severity="HIGH"
        ... )
    """

    pass


class PatternMatchError(SecurityValidationError):
    """Raised when dangerous patterns are detected in content.

    This exception indicates that a security pattern matched content in
    the scanned files, potentially indicating a security concern.

    Attributes:
        pattern_name: The name of the matched security pattern (optional).
        severity: The severity level of the detected pattern (optional).

    Example:
        >>> raise PatternMatchError(
        ...     "Potential API key detected",
        ...     pattern_name="api_key_detection",
        ...     severity="HIGH"
        ... )
    """

    def __init__(
        self,
        message: str,
        pattern_name: str | None = None,
        severity: str | None = None,
        **kwargs,
    ):
        """Initialize a pattern match error.

        Args:
            message: The error message describing the pattern match.
            pattern_name: The name of the matched security pattern.
            severity: The severity level (e.g., "HIGH", "MEDIUM").
            **kwargs: Additional fields for derived classes.
        """
        super().__init__(message, pattern_name=pattern_name, severity=severity, **kwargs)


class SemgrepValidationError(SecurityValidationError):
    """Raised when Semgrep validation fails or finds issues.

    This exception is raised when Semgrep security scanning detects
    potential security issues or fails to execute properly.

    Attributes:
        findings: List of security findings from Semgrep (optional).

    Example:
        >>> raise SemgrepValidationError(
        ...     "Semgrep detected potential SQL injection",
        ...     findings=[{"rule": "sql-injection", "severity": "HIGH"}]
        ... )
    """

    def __init__(self, message: str, findings: list[dict] | None = None, **kwargs):
        """Initialize a Semgrep validation error.

        Args:
            message: The error message describing the validation issue.
            findings: List of security findings from Semgrep scan.
            **kwargs: Additional fields for derived classes.
        """
        super().__init__(message, findings=findings or [], **kwargs)


class FileIntegrityError(SecurityValidationError):
    """Raised when file integrity checks fail.

    This exception is raised when file hash verification fails,
    indicating potential tampering or corruption.

    Attributes:
        expected_hash: The expected file hash (optional).
        actual_hash: The actual file hash computed (optional).

    Example:
        >>> raise FileIntegrityError(
        ...     "File hash mismatch detected",
        ...     expected_hash="sha256:abc123...",
        ...     actual_hash="sha256:def456..."
        ... )
    """

    def __init__(
        self,
        message: str,
        expected_hash: str | None = None,
        actual_hash: str | None = None,
        **kwargs,
    ):
        """Initialize a file integrity error.

        Args:
            message: The error message describing the integrity failure.
            expected_hash: The expected hash value.
            actual_hash: The actual computed hash value.
            **kwargs: Additional fields for derived classes.
        """
        super().__init__(message, expected_hash=expected_hash, actual_hash=actual_hash, **kwargs)
