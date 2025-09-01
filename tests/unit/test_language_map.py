"""Tests for language mapping functionality."""

from unittest.mock import patch

from codeconcat.language_map import GUESSLANG_AVAILABLE, ext_map, get_language_guesslang


class TestLanguageMap:
    """Test language mapping functions."""

    def test_ext_map_contains_common_extensions(self):
        """Test that ext_map contains common programming language extensions."""
        common_extensions = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".go": "go",
            ".rs": "rust",
            ".php": "php",
            ".rb": "ruby",
            ".cs": "csharp",
            ".r": "r",
            ".R": "r",
        }

        for ext, expected_lang in common_extensions.items():
            assert ext in ext_map
            assert ext_map[ext] == expected_lang

    def test_ext_map_lookup_known(self):
        """Test looking up known extensions in ext_map."""
        assert ext_map.get(".py") == "python"
        assert ext_map.get(".js") == "javascript"
        assert ext_map.get(".java") == "java"

    def test_ext_map_lookup_unknown(self):
        """Test looking up unknown extensions in ext_map."""
        assert ext_map.get(".unknown") is None
        assert ext_map.get(".xyz") is None
        assert ext_map.get("") is None

    def test_ext_map_case_handling(self):
        """Test that extension lookup handles case properly."""
        # Most extensions are lowercase
        assert ext_map.get(".py") == "python"
        # Some special cases like .R exist
        assert ".r" in ext_map or ".R" in ext_map

    def test_ext_map_completeness(self):
        """Test that ext_map has reasonable coverage."""
        # Should have at least 20 different extensions
        assert len(ext_map) >= 20

        # All values should be non-empty strings
        for ext, lang in ext_map.items():
            assert isinstance(ext, str)
            assert isinstance(lang, str)
            # Most keys start with '.', but some special filenames don't
            if ext not in ["dockerfile", "makefile", "cmakelists.txt"]:
                assert ext.startswith(".")
            assert len(lang) > 0

    @patch("codeconcat.language_map.GUESSLANG_AVAILABLE", True)
    @patch("codeconcat.language_map.guesslang_instance")
    def test_get_language_guesslang_available(self, mock_instance):
        """Test language guessing when guesslang is available."""
        # Mock the guesslang instance
        mock_instance.language_name.return_value = "Python"

        result = get_language_guesslang("def hello():\n    print('Hello')")

        assert result == "python"
        mock_instance.language_name.assert_called_once()

    @patch("codeconcat.language_map.GUESSLANG_AVAILABLE", False)
    def test_get_language_guesslang_not_available(self):
        """Test language guessing when guesslang is not available."""
        result = get_language_guesslang("def hello():\n    print('Hello')")

        assert result is None

    def test_guesslang_available_is_boolean(self):
        """Test that GUESSLANG_AVAILABLE is a boolean."""
        assert isinstance(GUESSLANG_AVAILABLE, bool)
