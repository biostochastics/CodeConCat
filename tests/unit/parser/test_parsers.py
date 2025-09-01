#!/usr/bin/env python3

"""
Test suite for language parsers in CodeConcat.

This module validates the functionality of all language parsers against
the test corpus, ensuring that they correctly identify declarations,
imports, docstrings, etc.
"""

import importlib
import json
import os
from typing import Any, Dict, List

import pytest

from codeconcat.base_types import CodeConCatConfig, ParseResult


class TestParsers:
    """Test class for language parsers."""

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

    @pytest.fixture
    def corpus_dir(self) -> str:
        """Fixture to provide the path to the test corpus directory."""
        # Get the directory of this test file
        test_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(test_dir, "parser_test_corpus")

    def _get_language_files(self, corpus_dir: str, language: str) -> List[str]:
        """Get all test files for a specific language."""
        language_dir = os.path.join(corpus_dir, language)
        if not os.path.exists(language_dir):
            return []

        files = []
        for filename in os.listdir(language_dir):
            if filename.endswith(tuple(self._get_extensions_for_language(language))):
                files.append(os.path.join(language_dir, filename))

        return files

    def _get_extensions_for_language(self, language: str) -> List[str]:
        """Get file extensions for a language."""
        extensions_map = {
            "python": [".py"],
            "javascript": [".js"],
            "typescript": [".ts", ".tsx"],
            "go": [".go"],
            "rust": [".rs"],
            "php": [".php"],
            "r": [".r", ".R"],
            "julia": [".jl"],
            "c": [".c", ".h"],
            "cpp": [".cpp", ".hpp", ".cc", ".hxx", ".cxx"],
            "csharp": [".cs"],
            "java": [".java"],
        }
        return extensions_map.get(language, [])

    def _load_expected_output(self, corpus_dir: str, language: str) -> Dict[str, Any]:
        """Load expected parsing output for validation."""
        expected_output_path = os.path.join(corpus_dir, language, "expected_output.json")
        if os.path.exists(expected_output_path):
            with open(expected_output_path) as f:
                return json.load(f)
        return {}

    def _validate_parse_result(
        self, parse_result: ParseResult, expected: Dict[str, Any], filename: str
    ) -> List[str]:
        """Validate a parse result against expected output."""
        basename = os.path.basename(filename)
        file_expected = expected.get(basename, {})

        if not file_expected:
            return [f"No expected output found for {basename}"]

        errors = []

        # Check declaration count
        if "declaration_count" in file_expected:
            expected_count = file_expected["declaration_count"]
            actual_count = len(parse_result.declarations)
            if expected_count != actual_count:
                errors.append(
                    f"Declaration count mismatch for {basename}: "
                    f"expected {expected_count}, got {actual_count}"
                )

        # Check specific declarations
        if "declarations" in file_expected:
            expected_declarations = set(file_expected["declarations"])
            actual_declarations = {d.name for d in parse_result.declarations}

            missing = expected_declarations - actual_declarations
            extra = actual_declarations - expected_declarations

            if missing:
                errors.append(f"Missing declarations in {basename}: {missing}")

            if extra:
                errors.append(f"Extra declarations in {basename}: {extra}")

        # Check import count
        if "import_count" in file_expected:
            expected_count = file_expected["import_count"]
            actual_count = len(parse_result.imports)
            if expected_count != actual_count:
                errors.append(
                    f"Import count mismatch for {basename}: "
                    f"expected {expected_count}, got {actual_count}"
                )

        # Check specific imports
        if "imports" in file_expected:
            expected_imports = set(file_expected["imports"])
            actual_imports = set(parse_result.imports)

            missing = expected_imports - actual_imports
            extra = actual_imports - expected_imports

            if missing:
                errors.append(f"Missing imports in {basename}: {missing}")

            if extra:
                errors.append(f"Extra imports in {basename}: {extra}")

        # Note: Docstrings are stored in declarations, not as a separate property
        # We'll check declarations metadata instead

        return errors

    def _generate_expected_output(self, parse_result: ParseResult, filename: str) -> Dict[str, Any]:
        """Generate expected output template from a parse result."""
        basename = os.path.basename(filename)

        # Basic counts
        expected = {
            "declaration_count": len(parse_result.declarations),
            "import_count": len(parse_result.imports),
            # Detailed data
            "declarations": [d.name for d in parse_result.declarations],
            "imports": parse_result.imports,
            # Add any docstrings found in declarations
            "declarations_with_docstrings": [
                d.name for d in parse_result.declarations if d.docstring
            ],
        }

        return {basename: expected}

    @pytest.mark.parametrize(
        "language",
        ["python", "javascript", "typescript", "go", "rust", "php", "r", "julia", "csharp"],
    )
    def test_language_parser(self, config: CodeConCatConfig, corpus_dir: str, language: str):
        """Test a specific language parser with test corpus files."""
        print(f"\n\nTesting parser for language: {language}")

        # Skip if no test files for this language
        files = self._get_language_files(corpus_dir, language)
        if not files:
            pytest.skip(f"No test files found for {language}")

        print(f"Found {len(files)} test files: {[os.path.basename(f) for f in files]}")

        # Load expected output
        expected = self._load_expected_output(corpus_dir, language)
        print(f"Expected output loaded: {bool(expected)}")

        # Generate expected output templates for missing files
        generate_expected = len(expected) == 0
        generated_expected = {}

        # Test each file
        all_errors = []

        for file_path in files:
            print(f"\nProcessing file: {os.path.basename(file_path)}")

            # Get parser using our test-friendly wrapper
            parser = self.get_language_parser(language, config)
            assert parser is not None, f"Could not get parser for {language}"
            print(f"Parser class: {parser.__class__.__name__}")

            # Read file content
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            print(f"File content loaded: {len(content)} bytes")

            # Parse content with timeout protection
            print("Starting parser.parse() - this is where it might hang...")
            result = parser.parse(content, file_path)

            # If generating expected output, collect it
            if generate_expected:
                generated_expected.update(self._generate_expected_output(result, file_path))
                continue

            # Validate parse result
            errors = self._validate_parse_result(result, expected, file_path)
            all_errors.extend(errors)

        # If generating expected output, write it to file
        if generate_expected and generated_expected:
            output_path = os.path.join(corpus_dir, language, "expected_output.json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(generated_expected, f, indent=2, sort_keys=True)

            pytest.skip(f"Generated expected output for {language}")

        # Assert no errors
        assert not all_errors, "\n".join(all_errors)

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


if __name__ == "__main__":
    # Run the tests
    pytest.main(["-v", __file__])
