"""Unit tests for the SecurityValidator class."""

import re
from unittest.mock import patch

import pytest

from codeconcat.errors import FileIntegrityError, ValidationError
from codeconcat.validation.security import security_validator


class TestSecurityValidator:
    """Test suite for the SecurityValidator class."""

    def test_compute_file_hash(self, tmp_path):
        """Test computing a file hash."""
        # Create a test file with known content
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, world!")

        # Known SHA256 hash for "Hello, world!"
        expected_hash = "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"

        # Compute the hash
        actual_hash = security_validator.compute_file_hash(test_file)
        assert actual_hash == expected_hash

    def test_compute_file_hash_invalid_algorithm(self, tmp_path):
        """Test computing a file hash with an invalid algorithm."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, world!")

        with pytest.raises(ValidationError) as excinfo:
            security_validator.compute_file_hash(test_file, algorithm="invalid_algorithm")

        assert "Invalid hash algorithm" in str(excinfo.value)

    def test_compute_file_hash_nonexistent_file(self):
        """Test computing a hash for a nonexistent file."""
        with pytest.raises(ValidationError) as excinfo:
            security_validator.compute_file_hash("/nonexistent/file.txt")

        # Updated to match the new error message from security improvements
        assert "Cannot access file" in str(excinfo.value)

    def test_verify_file_integrity_valid(self, tmp_path):
        """Test verifying file integrity with matching hash."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, world!")

        # Known SHA256 hash for "Hello, world!"
        expected_hash = "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"

        # This should not raise an exception
        security_validator.verify_file_integrity(test_file, expected_hash)

    def test_verify_file_integrity_invalid(self, tmp_path):
        """Test verifying file integrity with non-matching hash."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, world!")

        incorrect_hash = "0000000000000000000000000000000000000000000000000000000000000000"

        with pytest.raises(FileIntegrityError) as excinfo:
            security_validator.verify_file_integrity(test_file, incorrect_hash)

        # Check that the error has the expected and actual hash attributes
        assert excinfo.value.expected_hash == incorrect_hash
        assert excinfo.value.actual_hash != incorrect_hash
        assert len(excinfo.value.actual_hash) == 64  # SHA256 hash length

    def test_sanitize_content(self):
        """Test sanitizing content by replacing patterns."""
        content = "SELECT * FROM users WHERE username = 'admin'"

        # Create a custom pattern
        patterns = {"sql_injection": re.compile(r"SELECT\s+\*\s+FROM\s+users", re.IGNORECASE)}

        sanitized = security_validator.sanitize_content(content, patterns)
        # According to the implementation, it should replace with a warning comment
        assert (
            sanitized
            == "/* POTENTIALLY DANGEROUS CONTENT REMOVED: SELECT * FROM users */ WHERE username = 'admin'"
        )

        # Test secret pattern handling specifically for the named 'secrets_pattern'
        # This uses the special lambda sub: m.group().split("=")[0] + "= \"[REDACTED]\""
        secret_content = 'CUSTOM_API_TOKEN = "super_secret_value_at_least_8_chars_long"'
        secret_patterns = {
            # This pattern name triggers the special redaction logic.
            # The regex needs to match 'KEY = "VALUE"' where VALUE is at least 8 chars.
            "secrets_pattern": re.compile(
                r"(CUSTOM_API_TOKEN)\s*[:=]\s*['\"]([^'\"]{8,})['\"]", re.IGNORECASE
            )
        }

        sanitized_secret = security_validator.sanitize_content(secret_content, secret_patterns)
        assert sanitized_secret == 'CUSTOM_API_TOKEN = "[REDACTED]"'
        assert "super_secret_value_at_least_8_chars_long" not in sanitized_secret

    def test_sanitize_content_with_colon_delimiter(self):
        """Test that secrets redaction handles both colon and equals delimiters."""
        # Test colon delimiter
        content_colon = 'api_key: "my_super_secret_api_key_value"'
        patterns = {
            "secrets_pattern": re.compile(
                r"(api_key)\s*[:=]\s*['\"]([^'\"]{8,})['\"]", re.IGNORECASE
            )
        }

        sanitized = security_validator.sanitize_content(content_colon, patterns)
        assert sanitized == 'api_key: "[REDACTED]"'
        assert "my_super_secret_api_key_value" not in sanitized

        # Test equals delimiter
        content_equals = 'api_key = "my_super_secret_api_key_value"'
        sanitized = security_validator.sanitize_content(content_equals, patterns)
        assert sanitized == 'api_key = "[REDACTED]"'
        assert "my_super_secret_api_key_value" not in sanitized

    def test_binary_file_detection_with_renamed_extension(self, tmp_path):
        """Test that binary file detection works even with renamed text extensions."""
        # Create a binary file with a text extension
        binary_file = tmp_path / "malicious.txt"
        # Write binary content with null bytes
        binary_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")

        # Should detect as binary despite .txt extension
        assert security_validator.is_binary_file(binary_file) is True

        # Create a real text file for comparison
        text_file = tmp_path / "normal.txt"
        text_file.write_text("This is normal text content")
        assert security_validator.is_binary_file(text_file) is False

    def test_binary_file_detection_unicode_decode(self, tmp_path):
        """Test that binary file detection properly handles non-UTF8 content."""
        # Create a file with invalid UTF-8 bytes
        invalid_utf8_file = tmp_path / "invalid.py"
        invalid_utf8_file.write_bytes(b"#!/usr/bin/python\n\xff\xfe\xfd\xfc")

        # Should detect as binary due to invalid UTF-8
        assert security_validator.is_binary_file(invalid_utf8_file) is True

    def test_sql_injection_case_insensitive(self):
        """Test that SQL injection detection is case-insensitive."""
        from codeconcat.validation.security import DANGEROUS_PATTERNS

        sql_pattern = DANGEROUS_PATTERNS["sql_injection"]

        # Test uppercase
        assert sql_pattern.search("SELECT * FROM users") is not None
        # Test lowercase
        assert sql_pattern.search("select * from users") is not None
        # Test mixed case
        assert sql_pattern.search("SeLeCt * FrOm users") is not None
        # Test with other SQL commands
        assert sql_pattern.search("insert into table") is not None
        assert sql_pattern.search("DELETE FROM database") is not None
        assert sql_pattern.search("drop table users") is not None

    def test_r_language_extension_normalization(self, tmp_path):
        """Test that R language files are correctly identified regardless of case."""
        # Create R files with different extension cases
        r_file_lower = tmp_path / "analysis.r"
        r_file_upper = tmp_path / "analysis.R"

        r_code = """
        library(ggplot2)
        data <- read.csv("data.csv")
        plot(data$x, data$y)
        """

        r_file_lower.write_text(r_code)
        r_file_upper.write_text(r_code)

        # Both should be identified as R language files in suspicious content checks
        findings_lower = security_validator.check_for_suspicious_content(r_file_lower)
        findings_upper = security_validator.check_for_suspicious_content(r_file_upper)

        # The extension map lookup should work for both
        # This is a simple check that no errors occur when processing R files
        assert isinstance(findings_lower, list)
        assert isinstance(findings_upper, list)

    def test_file_integrity_cache_with_mtime(self, tmp_path):
        """Test that file integrity cache includes mtime to detect changes."""
        import time

        test_file = tmp_path / "test.txt"
        test_file.write_text("Original content")

        # Compute hash first time
        hash1 = security_validator.compute_file_hash(test_file)

        # Wait a tiny bit and modify the file with same size content
        time.sleep(0.01)
        test_file.write_text("Changed  content")  # Same length, different content

        # Compute hash again - should be different due to mtime in cache key
        hash2 = security_validator.compute_file_hash(test_file)

        # Hashes should be different since content changed
        assert hash1 != hash2

    @patch("codeconcat.validation.semgrep_validator.semgrep_validator.scan_file")
    def test_check_for_suspicious_content_with_semgrep(self, mock_scan_file, tmp_path):
        """Test checking for suspicious content with Semgrep enabled."""
        test_file = tmp_path / "test.py"
        test_file.write_text('import os\nos.system("echo test")')

        # Mock Semgrep findings
        mock_scan_file.return_value = [
            {
                "type": "semgrep",
                "rule_id": "python.lang.security.dangerous-system-call",
                "message": "Dangerous system call",
                "severity": "ERROR",
                "line": 2,
            }
        ]

        # Make sure the file exists before testing
        assert test_file.exists()

        findings = security_validator.check_for_suspicious_content(test_file, use_semgrep=True)

        # Should have findings (both regex patterns and Semgrep)
        assert findings is not None
        assert len(findings) > 0

        # Check for both pattern and Semgrep findings
        exec_found = False
        semgrep_found = False

        for finding in findings:
            if finding.get("type") == "pattern" and finding.get("name") == "exec_patterns":
                exec_found = True
            if finding.get("type") == "semgrep":
                semgrep_found = True

        assert exec_found, "Missing regex pattern finding for exec_patterns"
        assert semgrep_found, "Missing Semgrep finding"

    def test_check_for_suspicious_content_without_semgrep(self, tmp_path):
        """Test checking for suspicious content without Semgrep."""
        test_file = tmp_path / "test.py"
        test_file.write_text('import os\nos.system("echo test")')

        # Make sure the file exists before testing
        assert test_file.exists()

        findings = security_validator.check_for_suspicious_content(test_file, use_semgrep=False)

        # Verify we got the exec_patterns finding
        assert findings is not None
        assert len(findings) > 0

        # Check specifically for the exec_patterns finding
        exec_found = False
        for finding in findings:
            if finding.get("type") == "pattern" and finding.get("name") == "exec_patterns":
                exec_found = True
                break

        assert exec_found, "Missing regex pattern finding for exec_patterns"

    def test_is_binary_file_text(self, tmp_path):
        """Test checking if a text file is binary (should be False)."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, world!")

        assert security_validator.is_binary_file(test_file) is False

    def test_is_binary_file_binary(self, tmp_path):
        """Test checking if a binary file is binary (should be True)."""
        test_file = tmp_path / "test.bin"

        # Write some binary data
        with open(test_file, "wb") as f:
            f.write(b"\x00\x01\x02\x03\x04\xff\xfe\xfd")

        assert security_validator.is_binary_file(test_file) is True

    def test_generate_integrity_manifest(self, tmp_path):
        """Test generating an integrity manifest for a directory."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        # Create a few files
        file1 = test_dir / "file1.txt"
        file1.write_text("File 1 content")

        file2 = test_dir / "file2.txt"
        file2.write_text("File 2 content")

        # Create a subdirectory with a file
        subdir = test_dir / "subdir"
        subdir.mkdir()
        file3 = subdir / "file3.txt"
        file3.write_text("File 3 content")

        # Generate manifest
        manifest = security_validator.generate_integrity_manifest(test_dir)

        # Check manifest contents
        assert "file1.txt" in manifest
        assert "file2.txt" in manifest
        assert "subdir/file3.txt" in manifest
        assert len(manifest) == 3

        # Verify hashes are correct format (64 hex characters for SHA-256)
        for _file_path, hash_value in manifest.items():
            assert len(hash_value) == 64
            assert all(c in "0123456789abcdef" for c in hash_value)

    def test_verify_integrity_manifest(self, tmp_path):
        """Test verifying integrity using a manifest."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        # Create a few files
        file1 = test_dir / "file1.txt"
        file1.write_text("File 1 content")

        file2 = test_dir / "file2.txt"
        file2.write_text("File 2 content")

        # Generate manifest
        manifest = security_validator.generate_integrity_manifest(test_dir)

        # First verify all files pass integrity check
        results = security_validator.verify_integrity_manifest(test_dir, manifest)
        assert results["file1.txt"]["verified"] is True
        assert results["file2.txt"]["verified"] is True

        # Modify one file
        file1.write_text("Modified content")

        # Verify manifest again
        results = security_validator.verify_integrity_manifest(test_dir, manifest)

        # Check results
        assert results["file1.txt"]["verified"] is False
        assert results["file2.txt"]["verified"] is True
        assert results["file1.txt"]["reason"] == "Hash mismatch"

    def test_detect_tampering(self, tmp_path):
        """Test detection of file tampering."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Original content")

        # Calculate original hash
        original_hash = security_validator.compute_file_hash(test_file)

        # No tampering yet, should not detect anything
        result = security_validator.detect_tampering(test_file, original_hash)
        assert result is False

        # Now modify the file
        test_file.write_text("Modified content")

        # Should detect tampering
        result = security_validator.detect_tampering(test_file, original_hash)
        assert result is True
