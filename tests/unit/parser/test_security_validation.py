"""Test security validation in parser module loading."""

from unittest.mock import patch

import pytest

from codeconcat.parser.file_parser import (
    _try_enhanced_regex_parser,
    _try_standard_regex_parser,
    _try_tree_sitter_parser,
)


class TestSecurityValidation:
    """Test that parser module loading validates language inputs."""

    def test_enhanced_parser_rejects_malicious_language(self):
        """Test that enhanced parser rejects potentially malicious language inputs."""
        # Test various malicious inputs
        malicious_inputs = [
            "../../../etc/passwd",
            "os.system('ls')",
            "__import__('os').system('ls')",
            "python;os",
            "python/../../../",
            "../../secret_module",
            "python\x00malicious",
            "python|malicious",
            "python&malicious",
            "python`malicious`",
            "python$(malicious)",
        ]

        for malicious_input in malicious_inputs:
            result = _try_enhanced_regex_parser(malicious_input, use_enhanced=True)
            assert result is None, f"Should reject malicious input: {malicious_input}"

    def test_standard_parser_rejects_malicious_language(self):
        """Test that standard parser rejects potentially malicious language inputs."""
        malicious_inputs = [
            "../../../etc/passwd",
            "os.system('ls')",
            "__import__('os').system('ls')",
            "python;os",
            "python/../../../",
            "../../secret_module",
        ]

        for malicious_input in malicious_inputs:
            result = _try_standard_regex_parser(malicious_input)
            assert result is None, f"Should reject malicious input: {malicious_input}"

    def test_tree_sitter_parser_rejects_malicious_language(self):
        """Test that tree-sitter parser rejects potentially malicious language inputs."""
        malicious_inputs = [
            "../../../etc/passwd",
            "os.system('ls')",
            "__import__('os').system('ls')",
            "python;os",
            "python/../../../",
            "../../secret_module",
        ]

        for malicious_input in malicious_inputs:
            result = _try_tree_sitter_parser(malicious_input)
            assert result is None, f"Should reject malicious input: {malicious_input}"

    def test_parsers_accept_valid_languages(self):
        """Test that parsers accept valid language identifiers."""
        valid_languages = ["python", "javascript", "typescript", "rust", "go", "java"]

        for language in valid_languages:
            # These might return None if the parser isn't available,
            # but they shouldn't raise security exceptions
            try:
                _try_enhanced_regex_parser(language, use_enhanced=True)
                _try_standard_regex_parser(language)
                _try_tree_sitter_parser(language)
            except Exception as e:
                # Should not raise any exceptions for valid languages
                pytest.fail(f"Valid language '{language}' raised exception: {e}")

    def test_enhanced_parser_doesnt_import_arbitrary_module(self):
        """Test that enhanced parser doesn't attempt to import arbitrary modules."""
        with patch("importlib.import_module") as mock_import:
            # Try to load a malicious "language"
            result = _try_enhanced_regex_parser("../../malicious", use_enhanced=True)

            # Should not have attempted to import anything
            mock_import.assert_not_called()
            assert result is None

    def test_standard_parser_doesnt_import_arbitrary_module(self):
        """Test that standard parser doesn't attempt to import arbitrary modules."""
        with patch("importlib.import_module") as mock_import:
            # Try to load a malicious "language"
            result = _try_standard_regex_parser("../../malicious")

            # Should not have attempted to import anything
            mock_import.assert_not_called()
            assert result is None

    def test_tree_sitter_parser_doesnt_import_arbitrary_module(self):
        """Test that tree-sitter parser doesn't attempt to import arbitrary modules."""
        with patch("importlib.import_module") as mock_import:
            # Try to load a malicious "language"
            result = _try_tree_sitter_parser("../../malicious")

            # Should not have attempted to import anything
            mock_import.assert_not_called()
            assert result is None

    def test_case_sensitive_language_validation(self):
        """Test that language validation is case-sensitive."""
        # These should be rejected as they're not in the allowed list exactly
        invalid_cases = ["PYTHON", "Python", "JAVASCRIPT", "JavaScript"]

        for invalid_case in invalid_cases:
            result_enhanced = _try_enhanced_regex_parser(invalid_case, use_enhanced=True)
            result_standard = _try_standard_regex_parser(invalid_case)
            result_tree_sitter = _try_tree_sitter_parser(invalid_case)

            assert result_enhanced is None, f"Should reject case variant: {invalid_case}"
            assert result_standard is None, f"Should reject case variant: {invalid_case}"
            assert result_tree_sitter is None, f"Should reject case variant: {invalid_case}"
