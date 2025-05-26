"""Tests for custom error classes."""

from codeconcat.errors import (
    ValidationError,
    FileProcessingError,
    ConfigurationError,
    ParserError,
    CodeConcatError,
)


class TestErrorClasses:
    """Test custom error classes."""

    def test_validation_error(self):
        """Test ValidationError creation and message."""
        error = ValidationError("Invalid input provided")
        assert str(error) == "Invalid input provided"
        assert isinstance(error, Exception)

    def test_file_processing_error(self):
        """Test FileProcessingError creation and message."""
        error = FileProcessingError("Failed to process file.txt")
        assert str(error) == "Failed to process file.txt"
        assert isinstance(error, Exception)

    def test_configuration_error(self):
        """Test ConfigurationError creation and message."""
        error = ConfigurationError("Invalid configuration option")
        assert str(error) == "Invalid configuration option"
        assert isinstance(error, Exception)

    def test_parser_error(self):
        """Test ParserError creation and message."""
        error = ParserError("Failed to parse syntax", file_path="test.py", line_number=10)
        assert "Failed to parse syntax" in str(error)
        assert "test.py" in str(error)
        assert "10" in str(error)
        assert isinstance(error, Exception)

    def test_base_error(self):
        """Test CodeConcatError base class."""
        error = CodeConcatError("Base error message")
        assert str(error) == "Base error message"
        assert isinstance(error, Exception)

    def test_error_inheritance(self):
        """Test that all errors inherit from Exception."""
        errors = [
            ValidationError("test"),
            FileProcessingError("test"),
            ConfigurationError("test"),
            ParserError("test"),
            CodeConcatError("test"),
        ]

        for error in errors:
            assert isinstance(error, Exception)

    def test_error_with_context(self):
        """Test errors with additional context."""
        try:
            raise ValidationError("Invalid file") from ValueError("Bad value")
        except ValidationError as e:
            assert str(e) == "Invalid file"
            assert e.__cause__ is not None
            assert isinstance(e.__cause__, ValueError)

    def test_error_repr(self):
        """Test error representation."""
        error = ValidationError("Test message")
        assert repr(error) == "ValidationError('Test message')"

        error = FileProcessingError("File not found: test.py")
        assert repr(error) == "FileProcessingError('File not found: test.py')"
