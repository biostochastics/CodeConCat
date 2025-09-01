#!/usr/bin/env python3

"""
Integration tests for special file types in CodeConCat.

These tests verify that documentation files (Markdown/RST) and
configuration files (YAML/TOML) are properly handled throughout
the entire processing pipeline.
"""

import pytest

from codeconcat.parser.file_parser import determine_language


class TestSpecialFileTypeLanguageDetection:
    """Test class for special file type language detection."""

    @pytest.mark.parametrize(
        "filename,expected_language",
        [
            # Documentation files
            ("README.md", "documentation"),
            ("docs.rst", "documentation"),
            # Config files
            ("config.yml", "config"),
            ("settings.yaml", "config"),
            ("pyproject.toml", "config"),
            ("config.ini", "config"),
            ("settings.cfg", "config"),
            ("nginx.conf", "config"),
            # Regular code files for comparison
            ("main.py", "python"),
            ("app.js", "javascript"),
            ("utils.cpp", "cpp"),
        ],
    )
    def test_realistic_filenames(self, filename, expected_language):
        """Test file extension detection with realistic filenames."""
        # Get the detected language
        detected_language = determine_language(filename)

        # Assert correct language detection
        assert detected_language == expected_language, (
            f"File '{filename}' should be detected as '{expected_language}' "
            f"but was detected as '{detected_language}'"
        )


if __name__ == "__main__":
    # Run the tests
    pytest.main(["-v", __file__])
