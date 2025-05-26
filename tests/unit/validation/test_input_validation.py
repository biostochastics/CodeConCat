"""
Unit tests for the input validation module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from codeconcat.validation import validator, InputValidator
from codeconcat.errors import ValidationError


class TestInputValidator:
    """Test suite for the InputValidator class."""

    def test_validate_file_path_valid(self, tmp_path):
        """Test validating a valid file path."""
        # Create a temporary file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        # Test with string path
        result = validator.validate_file_path(str(test_file))
        assert isinstance(result, Path)
        assert result == test_file.resolve()

        # Test with Path object
        result = validator.validate_file_path(test_file)
        assert isinstance(result, Path)
        assert result == test_file.resolve()

    def test_validate_file_path_nonexistent(self, tmp_path):
        """Test validating a non-existent file path."""
        non_existent = tmp_path / "nonexistent.txt"

        # Should not raise when check_exists=False
        result = validator.validate_file_path(non_existent, check_exists=False)
        assert isinstance(result, Path)

        # Should raise when check_exists=True
        with pytest.raises(ValidationError):
            validator.validate_file_path(non_existent, check_exists=True)

    def test_validate_file_size_valid(self, tmp_path):
        """Test validating file size within limits."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        # Should not raise
        assert validator.validate_file_size(test_file, max_size=1000) is True

    def test_validate_file_size_too_large(self, tmp_path):
        """Test validating a file that's too large."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("x" * 1000)  # 1000 bytes

        with pytest.raises(ValidationError) as excinfo:
            validator.validate_file_size(test_file, max_size=100)
        assert "too large" in str(excinfo.value).lower()

    def test_validate_file_extension_allowed(self, tmp_path):
        """Test validating allowed file extensions."""
        test_file = tmp_path / "test.py"
        test_file.touch()

        # Should not raise
        assert validator.validate_file_extension(test_file, {".py", ".txt"}) is True

    def test_validate_file_extension_not_allowed(self, tmp_path):
        """Test validating disallowed file extensions."""
        test_file = tmp_path / "test.py"
        test_file.touch()

        with pytest.raises(ValidationError) as excinfo:
            validator.validate_file_extension(test_file, {".txt", ".md"})
        assert "not allowed" in str(excinfo.value).lower()

    def test_validate_file_extension_malicious(self, tmp_path):
        """Test validating potentially malicious file extensions."""
        test_file = tmp_path / "test.exe"
        test_file.touch()

        with pytest.raises(ValidationError) as excinfo:
            validator.validate_file_extension(test_file)
        assert "potentially malicious" in str(excinfo.value).lower()

    def test_validate_file_content_text(self, tmp_path):
        """Test validating text file content."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is a text file")

        # Should not raise
        assert validator.validate_file_content(test_file) is True

    @patch("builtins.open", new_callable=mock_open, read_data=b"\x00\x01\x02\x03")
    def test_validate_file_content_binary(self, mock_file, tmp_path):
        """Test validating binary file content."""
        test_file = tmp_path / "test.bin"
        test_file.touch()

        with pytest.raises(ValidationError) as excinfo:
            validator.validate_file_content(test_file)
        assert "binary file detected" in str(excinfo.value).lower()

    def test_validate_directory_path_valid(self, tmp_path):
        """Test validating a valid directory path."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        # Should not raise
        result = validator.validate_directory_path(test_dir)
        assert isinstance(result, Path)
        assert result == test_dir.resolve()

    def test_validate_directory_path_file(self, tmp_path):
        """Test validating a file path when a directory is expected."""
        test_file = tmp_path / "test.txt"
        test_file.touch()

        with pytest.raises(ValidationError) as excinfo:
            validator.validate_directory_path(test_file)
        assert "not a directory" in str(excinfo.value).lower()

    @pytest.mark.parametrize(
        "url,allowed,should_raise",
        [
            ("https://github.com/user/repo", None, False),
            ("https://github.com/user/repo", {"github.com"}, False),
            ("https://api.github.com/user/repo", {"github.com"}, True),
            ("git@github.com:user/repo.git", {"github.com"}, False),
            ("git@gitlab.com:user/repo.git", {"github.com"}, True),
        ],
    )
    def test_validate_url(self, url, allowed, should_raise):
        """Test URL validation with various inputs."""
        if should_raise:
            with pytest.raises(ValidationError):
                validator.validate_url(url, allowed_domains=allowed)
        else:
            result = validator.validate_url(url, allowed_domains=allowed)
            assert isinstance(result, str)
            assert result.startswith(("https://", "git@"))

    def test_validate_config_valid(self):
        """Test validating a valid config dictionary."""
        config = {"key1": "value1", "key2": 42}
        assert validator.validate_config(config) is True

        # With required fields
        assert validator.validate_config(config, ["key1"]) is True

    def test_validate_config_invalid(self):
        """Test validating an invalid config dictionary."""
        # Not a dictionary
        with pytest.raises(ValidationError):
            validator.validate_config("not a dict")

        # Missing required field
        with pytest.raises(ValidationError):
            validator.validate_config({"key1": "value"}, ["missing_key"])

    def test_is_binary_file_text(self, tmp_path):
        """Test _is_binary_file with a text file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("This is a text file")

        assert InputValidator._is_binary_file(test_file) is False

    def test_is_binary_file_binary(self, tmp_path):
        """Test _is_binary_file with a binary file."""
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"\x00\x01\x02\x03")

        assert InputValidator._is_binary_file(test_file) is True
