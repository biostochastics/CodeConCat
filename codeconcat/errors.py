# Define custom exceptions for CodeConCat

class CodeConcatError(Exception):
    """Base class for CodeConCat errors."""
    pass

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
    def __init__(self, message: str, file_path: str = None, line_number: int = None, original_exception: Exception = None):
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
     pass
