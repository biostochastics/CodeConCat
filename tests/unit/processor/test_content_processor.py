"""Unit tests for ContentProcessor module."""

import unittest
from codeconcat.base_types import (
    CodeConCatConfig,
    ParsedFileData,
    TokenStats,
    SecurityIssue,
    SecuritySeverity,
    Declaration,  # Import Declaration
)
from codeconcat.processor.content_processor import (
    process_file_content,
    remove_docstrings,
    generate_file_summary,
    generate_directory_structure,
)


class TestContentProcessor(unittest.TestCase):
    """Test cases for content processing functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = CodeConCatConfig(
            target_path="/path/to/test",
            remove_comments=False,
            remove_docstrings=False,
            remove_empty_lines=False,
            show_line_numbers=False,
            include_imports_in_summary=True,
            include_declarations_in_summary=True,
            include_tokens_in_summary=True,
            include_security_in_summary=True,
        )

        self.test_content = """#!/usr/bin/env python3
'''
This is a docstring.
It spans multiple lines.
'''

import os
import sys

# This is a comment
def hello_world():
    '''This function prints hello world'''
    print("Hello, World!")  # inline comment

# Empty line follows

class TestClass:
    '''Test class docstring'''
    def method(self):
        '''Method docstring'''
        return True
"""

        self.file_data = ParsedFileData(
            file_path="/path/to/test/file.py",
            language="python",
            content=self.test_content,
            imports=["os", "sys"],
            declarations=[
                Declaration(  # Use Declaration object
                    kind="function", name="hello_world", start_line=10, end_line=12
                ),
                Declaration(  # Use Declaration object
                    kind="class", name="TestClass", start_line=16, end_line=20
                ),
            ],
            token_stats=TokenStats(
                gpt3_tokens=100,
                gpt4_tokens=120,
                davinci_tokens=90,
                claude_tokens=110,
            ),
            security_issues=[
                SecurityIssue(
                    rule_id="test_rule",
                    description="Test security issue",
                    file_path="/path/to/test/file.py",
                    line_number=12,
                    severity=SecuritySeverity.HIGH,
                )
            ],
        )

    def test_process_file_content_default(self):
        """Test processing file content with default settings."""
        processed = process_file_content(self.test_content, self.config)

        # Content should remain unchanged with default settings
        self.assertEqual(processed, self.test_content)

        # Verify that content still contains docstrings and comments
        self.assertIn("This is a docstring.", processed)
        self.assertIn("# This is a comment", processed)
        self.assertIn("# inline comment", processed)

    def test_process_file_content_remove_docstrings(self):
        """Test processing file content with docstring removal."""
        config = CodeConCatConfig(
            target_path="/path/to/test",
            remove_docstrings=True,
        )

        processed = process_file_content(self.test_content, config)

        # Docstrings should be removed
        self.assertNotIn("This is a docstring.", processed)
        self.assertNotIn("This function prints hello world", processed)

        # Comments should still be present
        self.assertIn("# This is a comment", processed)

    def test_process_file_content_remove_comments(self):
        """Test processing file content with comment removal."""
        config = CodeConCatConfig(
            target_path="/path/to/test",
            remove_comments=True,
        )

        processed = process_file_content(self.test_content, config)

        # Comments should be removed
        self.assertNotIn("# This is a comment", processed)
        self.assertNotIn("# inline comment", processed)

        # Docstrings should still be present (they're not treated as comments)
        self.assertIn("This is a docstring.", processed)
        self.assertIn("This function prints hello world", processed)

    def test_process_file_content_remove_empty_lines(self):
        """Test processing file content with empty line removal."""
        config = CodeConCatConfig(
            target_path="/path/to/test",
            remove_empty_lines=True,
        )

        processed = process_file_content(self.test_content, config)

        # Count empty lines in original and processed content
        original_empty_lines = self.test_content.count("\n\n")
        processed_empty_lines = processed.count("\n\n")

        # Processed content should have fewer empty lines
        self.assertLess(processed_empty_lines, original_empty_lines)

    def test_process_file_content_show_line_numbers(self):
        """Test processing file content with line numbers."""
        config = CodeConCatConfig(
            target_path="/path/to/test",
            show_line_numbers=True,
        )

        processed = process_file_content(self.test_content, config)

        # Each line should start with a line number
        lines = processed.split("\n")
        for i, line in enumerate(lines):
            if line:  # Skip empty lines
                self.assertTrue(line.startswith(f"{i+1:4d} |"))

    def test_remove_docstrings(self):
        """Test removing docstrings from code."""
        code_content = """
'''Module docstring'''

def function():
    '''Function docstring'''
    return True

class MyClass:
    '''Class docstring'''
    def method(self):
        '''Method docstring'''
        return True

# JSDoc style
/**
 * This is a JSDoc comment
 * @param {string} name - Name parameter
 */

// C# XML style
/// <summary>
/// This is an XML doc comment
/// </summary>

// Rust style
/// This is a Rust doc comment

# R style
#' This is an R roxygen2 comment
"""
        result = remove_docstrings(code_content)

        # Triple-quoted docstrings should be removed
        self.assertNotIn("Module docstring", result)
        self.assertNotIn("Function docstring", result)
        self.assertNotIn("Class docstring", result)
        self.assertNotIn("Method docstring", result)

        # JSDoc comments should be removed
        self.assertNotIn("* This is a JSDoc comment", result)

        # C# XML comments should be removed
        self.assertNotIn("/// This is an XML doc comment", result)

        # Rust doc comments should be removed
        self.assertNotIn("/// This is a Rust doc comment", result)

        # R roxygen2 comments should be removed
        self.assertNotIn("#' This is an R roxygen2 comment", result)

    def test_generate_file_summary(self):
        """Test generating file summary."""
        summary = generate_file_summary(self.file_data, self.config)

        # Check that the summary contains the file name and language
        self.assertIn("**File:** `file.py`", summary)
        self.assertIn("**Language:** `python`", summary)

        # Check that imports are included
        self.assertIn("**Imports (2):** `os, sys`", summary)

        # Check that declarations are included
        self.assertIn("**Declarations:**", summary)
        # Assert Class first due to alphabetical sort by kind
        self.assertIn("**Class (1):** `TestClass`", summary)
        self.assertIn("**Function (1):** `hello_world`", summary)

        # Check that token stats are included
        self.assertIn("**Token Counts:**", summary)
        self.assertIn("GPT-3: `100`", summary)
        self.assertIn("GPT-4: `120`", summary)
        self.assertIn("DaVinci: `90`", summary)
        self.assertIn("Claude: `110`", summary)

        # Check that security issues are included
        self.assertIn("**Security Issues:**", summary)
        self.assertIn("Line 12", summary)
        self.assertIn("Test security issue", summary)

    def test_generate_directory_structure(self):
        """Test generating directory structure."""
        file_paths = [
            "project/src/main.py",
            "project/src/utils/helpers.py",
            "project/tests/test_main.py",
            "project/README.md",
        ]

        structure = generate_directory_structure(file_paths)

        # Check that the structure contains all expected files
        self.assertIn("project", structure)
        self.assertIn("src", structure)
        self.assertIn("tests", structure)
        self.assertIn("main.py", structure)
        self.assertIn("helpers.py", structure)
        self.assertIn("test_main.py", structure)
        self.assertIn("README.md", structure)

        # Check that the structure has the expected tree format
        self.assertIn("└── project", structure)
        self.assertIn("├── src", structure)
        self.assertIn("│   └── utils", structure)
        self.assertIn("└── helpers.py", structure)


if __name__ == "__main__":
    unittest.main()
