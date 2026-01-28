# Define custom exceptions for CodeConCat

from typing import Any


class CodeConcatError(Exception):
    """Base class for CodeConCat errors.

    This base class uses a flexible constructor that accepts additional
    keyword arguments, allowing derived classes to add specific fields
    while maintaining LSP compliance.
    """

    def __init__(self, message: str, **kwargs):
        """Initialize the error with a message and optional additional fields.

        Args:
            message: The error message
            **kwargs: Additional fields specific to derived classes
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
        message: Explanation of the validation error
        field: The name of the field that failed validation (optional)
        value: The invalid value that caused the error (optional)
        original_exception: The original exception that caused this error (optional)
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
            message: The error message
            field: The name of the field that failed validation
            value: The invalid value
            original_exception: The original exception if any
            **kwargs: Additional fields
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
    """Errors related to configuration loading or validation."""

    pass


class FileProcessingError(CodeConcatError):
    """Errors during file collection or initial processing."""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        original_exception: Exception | None = None,
        **kwargs,
    ):
        """Initialize a file processing error.

        Args:
            message: The error message
            file_path: Path to the file that caused the error
            original_exception: The original exception if any
            **kwargs: Additional fields
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
    """Base class for parsing errors."""

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
            message: The error message
            file_path: Path to the file being parsed
            line_number: Line number where the error occurred
            original_exception: The original exception if any
            **kwargs: Additional fields
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
    """Errors specific to a language parser."""

    pass


class UnsupportedLanguageError(ParserError):
    """Language determined but no parser available."""

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
            message: The error message
            file_path: Path to the file
            language: The unsupported language
            line_number: Line number if applicable
            original_exception: The original exception if any
            **kwargs: Additional fields
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
    """Base class for security-related validation errors."""

    pass


class PatternMatchError(SecurityValidationError):
    """Raised when dangerous patterns are detected in content."""

    def __init__(
        self,
        message: str,
        pattern_name: str | None = None,
        severity: str | None = None,
        **kwargs,
    ):
        """Initialize a pattern match error."""
        super().__init__(message, pattern_name=pattern_name, severity=severity, **kwargs)


class SemgrepValidationError(SecurityValidationError):
    """Raised when Semgrep validation fails or finds issues."""

    def __init__(self, message: str, findings: list[dict] | None = None, **kwargs):
        """Initialize a Semgrep validation error."""
        super().__init__(message, findings=findings or [], **kwargs)


class FileIntegrityError(SecurityValidationError):
    """Raised when file integrity checks fail (hash mismatch, tampering detected)."""

    def __init__(
        self,
        message: str,
        expected_hash: str | None = None,
        actual_hash: str | None = None,
        **kwargs,
    ):
        """Initialize a file integrity error."""
        super().__init__(message, expected_hash=expected_hash, actual_hash=actual_hash, **kwargs)
