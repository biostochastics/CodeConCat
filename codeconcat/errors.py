# Define custom exceptions for CodeConCat

from typing import Any


class CodeConcatError(Exception):
    """Base class for CodeConCat errors."""

    pass


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
        field: str = None,
        value: Any = None,
        original_exception: Exception = None,
    ):
        self.message = message
        self.field = field
        self.value = value
        self.original_exception = original_exception
        super().__init__(message)

    def __str__(self) -> str:
        parts = [self.message]
        if self.field:
            parts.append(f"Field: {self.field}")
        if self.value is not None:
            parts.append(f"Value: {self.value!r}")
        if self.original_exception:
            parts.append(f"Original error: {str(self.original_exception)}")
        return " | ".join(parts)


class ConfigurationError(CodeConcatError):
    """Errors related to configuration loading or validation."""

    pass


class FileProcessingError(CodeConcatError):
    """Errors during file collection or initial processing."""

    def __init__(self, message: str, file_path: str = None, original_exception: Exception = None):
        super().__init__(message)
        self.file_path = file_path
        self.original_exception = original_exception

    def __str__(self):
        base = super().__str__()
        if self.file_path:
            return f"{base} (File: {self.file_path})"
        return base


class ParserError(FileProcessingError):
    """Base class for parsing errors."""

    def __init__(
        self,
        message: str,
        file_path: str = None,
        line_number: int = None,
        original_exception: Exception = None,
    ):
        super().__init__(message, file_path=file_path, original_exception=original_exception)
        self.line_number = line_number

    def __str__(self):
        base = super().__str__()
        if self.line_number is not None:
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
        file_path: str = None,
        language: str = None,
        line_number: int = None,
        original_exception: Exception = None,
    ):
        super().__init__(
            message,
            file_path=file_path,
            line_number=line_number,
            original_exception=original_exception,
        )
        self.language = language

    def __str__(self):
        base = super().__str__()
        if self.language is not None:
            return f"{base} (Language: {self.language})"
        return base
