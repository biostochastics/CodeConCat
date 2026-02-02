#!/usr/bin/env python3

"""
Test suite for language parser discovery in CodeConcat.

This module validates that all language parsers are discoverable and can be instantiated.
Comprehensive parser functionality tests are in the individual test_tree_sitter_*.py
and test_enhanced_*.py test files.
"""

import importlib

import pytest

from codeconcat.base_types import CodeConCatConfig


class TestParsers:
    """Test class for language parser discovery."""

    @pytest.fixture
    def config(self) -> CodeConCatConfig:
        """Fixture to provide a CodeConCatConfig instance."""
        return CodeConCatConfig(
            output_dir="out",
            disable_tree=True,  # Disable tree-sitter for consistent testing
        )

    def get_language_parser(self, language: str, _config: CodeConCatConfig):
        """Wrapper for get_language_parser to properly handle imports in test environment."""
        # Import here to avoid circular imports
        from codeconcat.parser.language_parsers import REGEX_PARSER_MAP

        # For our tests, we always use enhanced parsers
        use_enhanced = True

        # Handle enhanced parsers
        normalized_language = language.lower()

        if use_enhanced:
            # Check if there's an enhanced version available
            enhanced_name = f"{normalized_language}_enhanced"
            parser_class_name = REGEX_PARSER_MAP.get(enhanced_name)

            if parser_class_name:
                # Try loading the enhanced parser
                try:
                    # Use absolute import path for tests
                    module_name = (
                        f"codeconcat.parser.language_parsers.enhanced_{normalized_language}_parser"
                    )

                    # Special case for JavaScript/TypeScript
                    if normalized_language in ["javascript", "typescript"]:
                        module_name = "codeconcat.parser.language_parsers.enhanced_js_ts_parser"

                    module = importlib.import_module(module_name)
                    parser_class = getattr(module, parser_class_name)
                    return parser_class()
                except (ImportError, AttributeError) as e:
                    print(f"Could not load Enhanced Regex parser for {normalized_language}: {e}")

        # Fall back to standard regex parser
        parser_class_name = REGEX_PARSER_MAP.get(normalized_language)

        if parser_class_name:
            try:
                # Use absolute import path for tests
                module_name = f"codeconcat.parser.language_parsers.{normalized_language}_parser"

                # Special case for JavaScript/TypeScript
                if normalized_language in ["javascript", "typescript"]:
                    module_name = "codeconcat.parser.language_parsers.js_ts_parser"

                module = importlib.import_module(module_name)
                parser_class = getattr(module, parser_class_name)
                return parser_class()
            except (ImportError, AttributeError) as e:
                print(f"Could not load Standard Regex parser for {normalized_language}: {e}")

        return None

    def test_all_parsers_discoverable(self, config: CodeConCatConfig):
        """Test that all language parsers are discoverable."""
        languages = [
            "python",
            "javascript",
            "typescript",
            "go",
            "rust",
            "php",
            "r",
            "julia",
            "csharp",
        ]

        for language in languages:
            parser = self.get_language_parser(language, config)
            assert parser is not None, f"Could not get parser for {language}"

    @pytest.mark.parametrize(
        "language",
        ["python", "javascript", "typescript", "go", "rust", "php", "r", "julia", "csharp"],
    )
    def test_parser_has_required_methods(self, config: CodeConCatConfig, language: str):
        """Test that each parser has the required interface methods."""
        parser = self.get_language_parser(language, config)
        assert parser is not None, f"Could not get parser for {language}"

        # Check required methods
        assert hasattr(parser, "parse"), f"{language} parser missing 'parse' method"
        assert callable(getattr(parser, "parse")), f"{language} parser 'parse' is not callable"

    @pytest.mark.parametrize(
        "language",
        ["python", "javascript", "typescript", "go", "rust", "php", "r", "julia", "csharp"],
    )
    def test_parser_returns_parse_result(self, config: CodeConCatConfig, language: str):
        """Test that each parser returns a ParseResult from minimal input."""
        from codeconcat.base_types import ParseResult

        parser = self.get_language_parser(language, config)
        assert parser is not None, f"Could not get parser for {language}"

        # Parse empty content - should return a valid ParseResult
        result = parser.parse("", f"test.{language}")
        assert isinstance(result, ParseResult), (
            f"{language} parser did not return ParseResult, got {type(result)}"
        )


if __name__ == "__main__":
    # Run the tests
    pytest.main(["-v", __file__])
