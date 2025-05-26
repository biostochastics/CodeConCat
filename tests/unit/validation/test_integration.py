"""Unit tests for the validation integration module."""

import pytest
from unittest.mock import patch, MagicMock

from codeconcat.validation.integration import (
    validate_input_files,
    validate_config_values,
    sanitize_output,
    verify_file_signatures,
)
from codeconcat.base_types import ParsedFileData
from codeconcat.errors import ValidationError, ConfigurationError


class TestValidationIntegration:
    """Test suite for validation integration functions."""

    def test_validate_input_files(self, tmp_path):
        """Test validating a list of input files."""
        # Create test files
        file1 = tmp_path / "file1.py"
        file1.write_text("def test(): pass")

        file2 = tmp_path / "file2.py"
        file2.write_text("def test(): pass")

        # Create ParsedFileData objects
        files = [
            ParsedFileData(file_path=str(file1), content="def test(): pass", language="python"),
            ParsedFileData(file_path=str(file2), content="def test(): pass", language="python"),
        ]

        # Create test config
        config = MagicMock()
        config.strict_validation = False
        config.max_file_size = 1024 * 1024  # 1MB
        config.target_path = str(tmp_path)  # Set target_path to the test directory

        # Validate files
        validated = validate_input_files(files, config)

        # All files should pass validation
        assert len(validated) == 2
        assert validated[0].file_path == str(file1)
        assert validated[1].file_path == str(file2)

    def test_validate_input_files_with_suspicious_content(self, tmp_path):
        """Test validating files with suspicious content."""
        # Create a file with suspicious content
        suspicious_file = tmp_path / "suspicious.py"
        suspicious_file.write_text(
            """
        def hack():
            exec("import os; os.system('rm -rf /')")
        """
        )

        # Create ParsedFileData objects
        files = [
            ParsedFileData(
                file_path=str(suspicious_file),
                content=suspicious_file.read_text(),
                language="python",
            ),
        ]

        # Create test config with strict validation
        config = MagicMock()
        config.strict_validation = True
        config.strict_security = True
        config.target_path = str(tmp_path)  # Set target_path to the test directory
        config.enable_security_scanning = True
        config.enable_semgrep = False
        config.max_file_size = 1024 * 1024  # 1MB

        # Should filter out the suspicious file
        with pytest.raises(ValidationError):
            validate_input_files(files, config)

        # With strict_security=False, it should warn but still include the file
        config.strict_security = False
        validated = validate_input_files(files, config)
        assert len(validated) == 1

    def test_validate_config_values_valid(self):
        """Test validating valid configuration values."""
        config = {
            "format": "markdown",
            "output": "output.md",
            "include_paths": ["src/**/*.py"],
            "exclude_paths": ["tests/**"],
            "max_workers": 4,
            "disable_ai_context": False,
        }

        # Should not raise an exception
        assert validate_config_values(config) is True

    def test_validate_config_values_invalid(self):
        """Test validating invalid configuration values."""
        # Missing required field 'output'
        config = {
            "format": "markdown",
            "include_paths": ["src/**/*.py"],
        }

        with pytest.raises(ConfigurationError) as excinfo:
            validate_config_values(config)

        assert "configuration validation failed" in str(excinfo.value).lower()

    def test_sanitize_output(self):
        """Test sanitizing output content."""
        content = """
        # This is a test file
        
        API_KEY = "1234567890abcdef1234567890abcdef"
        
        def dangerous_function():
            exec(user_input)
        """

        sanitized = sanitize_output(content)

        # Check that sensitive data was sanitized
        assert "API_KEY" in sanitized
        assert "1234567890abcdef" not in sanitized
        assert "[REDACTED]" in sanitized
        assert "/* POTENTIALLY DANGEROUS CONTENT REMOVED: exec" in sanitized

    def test_verify_file_signatures(self, tmp_path):
        """Test verifying file signatures."""
        # Create test files
        text_file = tmp_path / "text.py"
        text_file.write_text("def test(): pass")

        # Create binary file
        binary_file = tmp_path / "binary.bin"
        with open(binary_file, "wb") as f:
            f.write(b"\x00\x01\x02\x03")

        # Create ParsedFileData objects
        files = [
            ParsedFileData(file_path=str(text_file), content="def test(): pass", language="python"),
            ParsedFileData(
                file_path=str(binary_file), content=b"\x00\x01\x02\x03", language="binary"
            ),
        ]

        # Verify file signatures
        with patch(
            "codeconcat.validation.security.SecurityValidator.is_binary_file"
        ) as mock_is_binary:
            # Mock the is_binary_file function to return expected values
            mock_is_binary.side_effect = lambda path: "binary" in str(path)

            signatures = verify_file_signatures(files)

            assert signatures[str(text_file)] == "text"
            assert signatures[str(binary_file)] == "binary"

    def test_verify_file_signatures_invalid(self, tmp_path):
        """Test verifying invalid file signatures."""
        # Create a file with a Python extension but containing binary data
        binary_py_file = tmp_path / "binary.py"
        with open(binary_py_file, "wb") as f:
            f.write(b"\x00\x01\x02\x03")

        # Create ParsedFileData objects
        files = [
            ParsedFileData(
                file_path=str(binary_py_file), content=b"\x00\x01\x02\x03", language="python"
            ),
        ]

        # Verify file signatures - should raise ValidationError
        with patch(
            "codeconcat.validation.security.SecurityValidator.is_binary_file", return_value=True
        ):
            with pytest.raises(ValidationError) as excinfo:
                verify_file_signatures(files)

            assert "binary" in str(excinfo.value).lower()
