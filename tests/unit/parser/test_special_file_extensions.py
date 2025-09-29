#!/usr/bin/env python3

"""
Test suite for special file extension handling in CodeConCat.

This module validates that markdown, RST, and configuration files
are correctly identified and not parsed as code.
"""

import pytest

from codeconcat.parser.unified_pipeline import determine_language


class TestSpecialFileExtensions:
    """Test class for special file extension handling."""

    @pytest.mark.parametrize(
        "file_extension,expected_language",
        [
            # Documentation files
            (".md", "documentation"),
            (".rst", "documentation"),
            # Config files
            (".yml", "config"),
            (".yaml", "config"),
            (".toml", "config"),
            (".ini", "config"),
            (".cfg", "config"),
            (".conf", "config"),
            # Regular code files for comparison
            (".py", "python"),
            (".js", "javascript"),
            (".cpp", "cpp"),
        ],
    )
    def test_file_extension_detection(self, file_extension, expected_language):
        """Test that file extensions are correctly mapped to languages."""
        # Create a test file path with the extension
        file_path = f"/path/to/testfile{file_extension}"

        # Get the detected language
        detected_language = determine_language(file_path)

        # Assert correct language detection
        assert detected_language == expected_language, (
            f"File with extension '{file_extension}' should be detected as '{expected_language}' "
            f"but was detected as '{detected_language}'"
        )


if __name__ == "__main__":
    # Run the tests
    pytest.main(["-v", __file__])
