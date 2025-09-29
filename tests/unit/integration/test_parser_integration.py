#!/usr/bin/env python3

"""
Integration tests for CodeConCat parsers with other components.

These tests verify the interaction between language parsers and other
CodeConCat components, such as file collection, declaration processing,
and output generation.
"""

import logging
from pathlib import Path

import pytest

from codeconcat.base_types import CodeConCatConfig, ParseResult, ParserInterface
from codeconcat.parser.enable_debug import enable_all_parser_debug_logging
from codeconcat.parser.unified_pipeline import get_language_parser

# Enable debug logging for all parsers
enable_all_parser_debug_logging()

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class TestParserIntegration:
    """Test class for parser integration with other components."""

    @pytest.fixture
    def sample_python_file(self, tmp_path) -> Path:
        """Create a sample Python file for testing."""
        file_path = tmp_path / "sample.py"
        with open(file_path, "w") as f:
            f.write(
                '''"""Sample Python module for integration testing."""

import os
import sys
from typing import List, Dict, Optional

class TestClass:
    """A test class for demonstration."""

    def __init__(self, name: str):
        """Initialize with a name."""
        self.name = name

    def greet(self) -> str:
        """Return a greeting."""
        return f"Hello, {self.name}!"

def main():
    """Main function."""
    test = TestClass("World")
    print(test.greet())

if __name__ == "__main__":
    main()
'''
            )
        return file_path

    @pytest.fixture
    def sample_js_file(self, tmp_path) -> Path:
        """Create a sample JavaScript file for testing."""
        file_path = tmp_path / "sample.js"
        with open(file_path, "w") as f:
            f.write(
                """/**
 * Sample JavaScript file for integration testing.
 */

import { Component } from 'some-library';

/**
 * A test class for demonstration.
 */
class TestClass {
  /**
   * Initialize with a name.
   */
  constructor(name) {
    this.name = name;
  }

  /**
   * Return a greeting.
   */
  greet() {
    return `Hello, ${this.name}!`;
  }
}

/**
 * Main function.
 */
function main() {
  const test = new TestClass("World");
  console.log(test.greet());
}

// Run the main function
main();
"""
            )
        return file_path

    def test_get_language_parser_integration(self):
        """Test integration with the parser factory function."""
        # Create a configuration with enhanced parsers enabled
        config = CodeConCatConfig()
        config.use_enhanced_parsers = True

        # Get parsers for different languages
        python_parser = get_language_parser("python", config, parser_type="enhanced")
        javascript_parser = get_language_parser("javascript", config, parser_type="enhanced")
        typescript_parser = get_language_parser("typescript", config, parser_type="enhanced")

        # Check that we got valid parsers
        assert python_parser is not None, "Failed to get Python parser"
        assert javascript_parser is not None, "Failed to get JavaScript parser"
        assert typescript_parser is not None, "Failed to get TypeScript parser"

        # Check that they implement the ParserInterface
        assert isinstance(python_parser, ParserInterface)
        assert isinstance(javascript_parser, ParserInterface)
        assert isinstance(typescript_parser, ParserInterface)

        # Verify language-specific capabilities
        python_caps = python_parser.get_capabilities()
        js_caps = javascript_parser.get_capabilities()

        assert python_caps["can_parse_functions"] is True
        assert python_caps["can_parse_classes"] is True
        assert js_caps["can_parse_functions"] is True
        assert js_caps["can_parse_classes"] is True

        # Test error handling for invalid language
        invalid_parser = get_language_parser("nonexistent", config, parser_type="enhanced")
        assert invalid_parser is None, "Should return None for invalid language"

    def test_parser_with_file_integration(self, sample_python_file):
        """Test integration between parser and file processing."""
        # Create a configuration with enhanced parsers enabled
        config = CodeConCatConfig()
        config.use_enhanced_parsers = True

        # Get parser for Python
        parser = get_language_parser("python", config, parser_type="enhanced")
        assert parser is not None, "Failed to get Python parser"

        # Parse the sample file
        with open(sample_python_file) as f:
            content = f.read()

        parse_result = parser.parse(content, str(sample_python_file))
        assert isinstance(parse_result, ParseResult), "Parser should return a ParseResult"
        assert len(parse_result.declarations) > 0, "Parser should find declarations"

        # Verify declarations were properly parsed
        class_decl = next((d for d in parse_result.declarations if d.kind == "class"), None)
        assert class_decl is not None, "TestClass should be detected"
        assert class_decl.name == "TestClass", "Class name should be correctly parsed"
        assert "demonstration" in class_decl.docstring, "Class docstring should be extracted"

        # Verify methods within class were parsed
        greet_method = next((m for m in class_decl.children if m.name == "greet"), None)
        assert greet_method is not None, "greet method should be detected"
        assert "Return a greeting" in greet_method.docstring, "Method docstring should be extracted"

        # Verify imports were detected
        assert "os" in parse_result.imports, "os import should be detected"
        assert "sys" in parse_result.imports, "sys import should be detected"
        assert "typing" in parse_result.imports, "typing import should be detected"

        # Print summary of parsed elements
        print(f"\nParsed {len(parse_result.declarations)} declarations from Python file")
        print(f"Found {len(parse_result.imports)} imports")
        print(f"TestClass has {len(class_decl.children)} methods")

    def test_parser_integration_with_multiple_files(self, sample_python_file, sample_js_file):
        """Test parsing multiple files with different languages."""
        # Create a configuration with enhanced parsers enabled
        config = CodeConCatConfig()
        config.use_enhanced_parsers = True

        # Get parsers
        python_parser = get_language_parser("python", config, parser_type="enhanced")
        js_parser = get_language_parser("javascript", config, parser_type="enhanced")

        assert python_parser is not None, "Failed to get Python parser"
        assert js_parser is not None, "Failed to get JavaScript parser"

        # Parse the Python file
        with open(sample_python_file) as f:
            python_content = f.read()

        python_result = python_parser.parse(python_content, str(sample_python_file))
        assert isinstance(python_result, ParseResult)
        assert len(python_result.declarations) > 0

        # Parse the JavaScript file
        with open(sample_js_file) as f:
            js_content = f.read()

        js_result = js_parser.parse(js_content, str(sample_js_file))
        assert isinstance(js_result, ParseResult)
        assert len(js_result.declarations) > 0

        # Compare declarations from both languages
        python_class = next((d for d in python_result.declarations if d.kind == "class"), None)
        js_class = next((d for d in js_result.declarations if d.kind == "class"), None)

        assert python_class is not None, "Python class should be detected"
        assert js_class is not None, "JavaScript class should be detected"

        # Both should have the same name (TestClass)
        assert python_class.name == js_class.name, "Class names should match between files"

        # Both should have a greet method
        python_greet = next((m for m in python_class.children if m.name == "greet"), None)
        js_greet = next((m for m in js_class.children if m.name == "greet"), None)

        assert python_greet is not None, "Python greet method should be detected"
        assert js_greet is not None, "JavaScript greet method should be detected"

        # Verify imports were detected in both languages
        print(f"\nPython imports: {python_result.imports}")
        print(f"JavaScript imports: {js_result.imports}")

        # Print summary
        print(f"\nParsed {len(python_result.declarations)} declarations from Python file")
        print(f"Parsed {len(js_result.declarations)} declarations from JavaScript file")
        print(f"Python TestClass has {len(python_class.children)} methods")
        print(f"JavaScript TestClass has {len(js_class.children)} methods")


if __name__ == "__main__":
    pytest.main(["-v", __file__])
