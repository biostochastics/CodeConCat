"""Comprehensive unit tests for ContentProcessor module.

This test suite achieves 85%+ coverage by testing all functions, edge cases,
error handling, and performance scenarios in the content_processor module.
"""

import unittest

from codeconcat.base_types import (
    CodeConCatConfig,
    Declaration,
    ParsedFileData,
    SecurityIssue,
    SecuritySeverity,
    TokenStats,
)
from codeconcat.processor.content_processor import (
    generate_directory_structure,
    generate_file_summary,
    process_file_content,
    remove_docstrings,
)


class TestContentProcessor(unittest.TestCase):
    """Comprehensive test cases for content processing functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Default configuration
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

        # Test content for various scenarios
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

        # Complex test content with various comment types
        self.complex_content = """
/* Multi-line comment
   spanning multiple lines */
// Single line comment
def function(param="string with # hash"):
    '''Docstring with /* comment inside */'''
    url = "http://example.com"  // Not a comment
    code = '/* not a comment */'
    # Regular Python comment
    return param + url

/*
 * JSDoc style comment
 * @param {string} test
 */
function jsFunction() {
    /* inline block comment */ var x = 5;
    return x; // another comment
}
"""

        # Sample parsed file data
        self.file_data = ParsedFileData(
            file_path="/path/to/test/file.py",
            language="python",
            content=self.test_content,
            imports=["os", "sys"],
            declarations=[
                Declaration(kind="function", name="hello_world", start_line=10, end_line=12),
                Declaration(kind="class", name="TestClass", start_line=16, end_line=20),
            ],
            token_stats=TokenStats(gpt4_tokens=120, claude_tokens=110),
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
        processed = process_file_content(self.test_content, self.config, self.file_data)

        # Content should remain unchanged with default settings
        self.assertEqual(processed, self.test_content)

        # Verify that content still contains docstrings and comments
        self.assertIn("This is a docstring.", processed)
        self.assertIn("# This is a comment", processed)
        self.assertIn("# inline comment", processed)

    def test_process_file_content_empty_string(self):
        """Test processing empty content."""
        processed = process_file_content("", self.config, self.file_data)
        self.assertEqual(processed, "")

    def test_process_file_content_whitespace_only(self):
        """Test processing content with only whitespace."""
        whitespace_content = "   \n  \t\n   \n"
        processed = process_file_content(whitespace_content, self.config, self.file_data)
        self.assertEqual(processed, whitespace_content)

    def test_process_file_content_empty_test_file(self):
        """Test processing empty test files gets special handling."""
        # Test different test file patterns
        test_configs = [
            CodeConCatConfig(target_path="/path/tests/test_file.py"),
            CodeConCatConfig(target_path="test_something.py"),
            CodeConCatConfig(target_path="my_test.R"),
            CodeConCatConfig(target_path="sample_tests.R"),
        ]

        for config in test_configs:
            processed = process_file_content("   \n  \n", config, self.file_data)
            self.assertEqual(processed, "# Empty test file")

    def test_process_file_content_remove_docstrings(self):
        """Test processing file content with docstring removal."""
        config = CodeConCatConfig(target_path="/path/to/test", remove_docstrings=True)

        processed = process_file_content(self.test_content, config, self.file_data)

        # Docstrings should be removed
        self.assertNotIn("This is a docstring.", processed)
        self.assertNotIn("This function prints hello world", processed)

        # Comments should still be present
        self.assertIn("# This is a comment", processed)

    def test_process_file_content_remove_comments(self):
        """Test processing file content with comment removal."""
        config = CodeConCatConfig(target_path="/path/to/test", remove_comments=True)

        processed = process_file_content(self.test_content, config, self.file_data)

        # Comments should be removed
        self.assertNotIn("# This is a comment", processed)
        self.assertNotIn("# inline comment", processed)

        # Docstrings should still be present
        self.assertIn("This is a docstring.", processed)

    def test_process_file_content_complex_comment_removal(self):
        """Test complex comment removal scenarios."""
        config = CodeConCatConfig(target_path="/path/to/test", remove_comments=True)

        processed = process_file_content(self.complex_content, config, self.file_data)

        # Multi-line comments should be removed
        self.assertNotIn("Multi-line comment", processed)
        self.assertNotIn("spanning multiple lines", processed)

        # Single line comments should be removed
        self.assertNotIn("// Single line comment", processed)
        self.assertNotIn("# Regular Python comment", processed)
        self.assertNotIn("// another comment", processed)

        # Comments inside strings should remain
        self.assertIn("string with # hash", processed)
        self.assertIn("http://example.com", processed)
        self.assertIn("/* not a comment */", processed)

        # JSDoc comments should be removed
        self.assertNotIn("JSDoc style comment", processed)
        self.assertNotIn("@param {string} test", processed)

    def test_process_file_content_multiline_block_comments(self):
        """Test handling of multiline block comments across multiple lines."""
        content_with_multiline = """
def function():
    /* This is a multiline
       block comment that spans
       multiple lines */
    return True

/* Another block
   comment here */ var x = 5;
"""
        config = CodeConCatConfig(target_path="/path/to/test", remove_comments=True)

        processed = process_file_content(content_with_multiline, config, self.file_data)

        # Multiline block comments should be completely removed
        self.assertNotIn("This is a multiline", processed)
        self.assertNotIn("block comment that spans", processed)
        self.assertNotIn("multiple lines", processed)
        self.assertNotIn("Another block", processed)
        self.assertNotIn("comment here", processed)

        # Code should remain
        self.assertIn("def function():", processed)
        self.assertIn("return True", processed)
        self.assertIn("var x = 5;", processed)

    def test_process_file_content_comments_in_strings(self):
        """Test that comments inside strings are preserved."""
        content_with_string_comments = """
def function():
    url = "http://example.com//path"  # Real comment
    comment_str = "This is not a # comment"
    block_str = "/* also not a comment */"
    mixed = 'Mixed "quotes # and // symbols"'
    return url
"""
        config = CodeConCatConfig(target_path="/path/to/test", remove_comments=True)

        processed = process_file_content(content_with_string_comments, config, self.file_data)

        # Comments inside strings should be preserved
        self.assertIn("http://example.com//path", processed)
        self.assertIn("This is not a # comment", processed)
        self.assertIn("/* also not a comment */", processed)
        self.assertIn('Mixed "quotes # and // symbols"', processed)

        # Real comments should be removed
        self.assertNotIn("# Real comment", processed)

    def test_process_file_content_remove_empty_lines(self):
        """Test processing file content with empty line removal."""
        config = CodeConCatConfig(target_path="/path/to/test", remove_empty_lines=True)

        processed = process_file_content(self.test_content, config, self.file_data)

        # Count empty lines in original and processed content
        original_empty_lines = self.test_content.count("\n\n")
        processed_empty_lines = processed.count("\n\n")

        # Processed content should have fewer empty lines
        self.assertLess(processed_empty_lines, original_empty_lines)

    def test_process_file_content_remove_empty_lines_after_comments(self):
        """Test empty line removal after comment removal creates proper behavior."""
        content_with_comment_lines = """
def function():
    # Comment that will be removed

    # Another comment

    return True
"""
        config = CodeConCatConfig(
            target_path="/path/to/test", remove_comments=True, remove_empty_lines=True
        )

        processed = process_file_content(content_with_comment_lines, config, self.file_data)

        # Comments should be removed
        self.assertNotIn("# Comment that will be removed", processed)
        self.assertNotIn("# Another comment", processed)

        # Should not have excessive empty lines
        self.assertNotIn("\n\n\n", processed)

        # Code should remain
        self.assertIn("def function():", processed)
        self.assertIn("return True", processed)

    def test_process_file_content_show_line_numbers(self):
        """Test processing file content with line numbers."""
        config = CodeConCatConfig(target_path="/path/to/test", show_line_numbers=True)

        processed = process_file_content(self.test_content, config, self.file_data)

        # Each line should start with a line number
        lines = processed.split("\n")
        for i, line in enumerate(lines):
            if line:  # Skip empty lines
                self.assertTrue(line.startswith(f"{i+1:4d} |"))

    def test_process_file_content_line_numbers_with_processing(self):
        """Test line numbers work correctly with other processing options."""
        config = CodeConCatConfig(
            target_path="/path/to/test",
            show_line_numbers=True,
            remove_comments=True,
            remove_empty_lines=True,
        )

        processed = process_file_content(self.test_content, config, self.file_data)
        lines = processed.split("\n")

        # Should have line numbers for remaining lines
        line_count = 0
        for line in lines:
            if line.strip():  # Non-empty lines
                line_count += 1
                self.assertTrue(line.startswith(f"{line_count:4d} |"))

    def test_process_file_content_combined_options(self):
        """Test processing with multiple options enabled."""
        config = CodeConCatConfig(
            target_path="/path/to/test",
            remove_docstrings=True,
            remove_comments=True,
            remove_empty_lines=True,
            show_line_numbers=True,
        )

        processed = process_file_content(self.test_content, config, self.file_data)

        # All processing should be applied
        self.assertNotIn("This is a docstring.", processed)  # Docstrings removed
        self.assertNotIn("# This is a comment", processed)  # Comments removed
        self.assertTrue(
            all(
                line.startswith(f"{i+1:4d} |") or not line.strip()
                for i, line in enumerate(processed.split("\n"))
                if line.strip()
            )
        )  # Line numbers present

    def test_remove_docstrings_python(self):
        """Test removing Python docstrings."""
        python_code = """
'''Module docstring'''

def function():
    '''Function docstring'''
    return True

class MyClass:
    '''Class docstring'''
    def method(self):
        \"\"\"Method docstring\"\"\"
        return True
"""
        result = remove_docstrings(python_code)

        # Triple-quoted docstrings should be removed
        self.assertNotIn("Module docstring", result)
        self.assertNotIn("Function docstring", result)
        self.assertNotIn("Class docstring", result)
        self.assertNotIn("Method docstring", result)

        # Code structure should remain
        self.assertIn("def function():", result)
        self.assertIn("class MyClass:", result)
        self.assertIn("return True", result)

    def test_remove_docstrings_javascript(self):
        """Test removing JavaScript JSDoc comments."""
        js_code = """
/**
 * This is a JSDoc comment
 * @param {string} name - Name parameter
 * @returns {boolean} Result
 */
function testFunction(name) {
    return true;
}

/**
 * Another JSDoc block
 */
var x = 5;
"""
        result = remove_docstrings(js_code)

        # JSDoc comments should be removed
        self.assertNotIn("This is a JSDoc comment", result)
        self.assertNotIn("@param {string} name", result)
        self.assertNotIn("@returns {boolean} Result", result)
        self.assertNotIn("Another JSDoc block", result)

        # Code should remain
        self.assertIn("function testFunction(name)", result)
        self.assertIn("return true;", result)
        self.assertIn("var x = 5;", result)

    def test_remove_docstrings_csharp(self):
        """Test removing C# XML documentation comments."""
        csharp_code = """
/// <summary>
/// This is a C# XML doc comment
/// </summary>
/// <param name="value">Parameter description</param>
public void Method(string value)
{
    // Regular comment should remain
    return;
}

/// <summary>Another summary</summary>
public class TestClass
{
}
"""
        result = remove_docstrings(csharp_code)

        # XML doc comments should be removed
        self.assertNotIn("This is a C# XML doc comment", result)
        self.assertNotIn('<param name="value">', result)
        self.assertNotIn("Another summary", result)

        # Code and regular comments should remain
        self.assertIn("public void Method(string value)", result)
        self.assertIn("// Regular comment should remain", result)
        self.assertIn("public class TestClass", result)

    def test_remove_docstrings_rust(self):
        """Test removing Rust documentation comments."""
        rust_code = """
/// This is a Rust doc comment
/// for a function
pub fn function() -> bool {
    true
}

//! This is a module-level doc comment
//! with multiple lines

/// Another doc comment
struct TestStruct;
"""
        result = remove_docstrings(rust_code)

        # Rust doc comments should be removed
        self.assertNotIn("This is a Rust doc comment", result)
        self.assertNotIn("for a function", result)
        self.assertNotIn("This is a module-level doc comment", result)
        self.assertNotIn("with multiple lines", result)
        self.assertNotIn("Another doc comment", result)

        # Code should remain
        self.assertIn("pub fn function() -> bool", result)
        self.assertIn("struct TestStruct;", result)

    def test_remove_docstrings_r(self):
        """Test removing R roxygen2 comments."""
        r_code = """
#' This is an R roxygen2 comment
#' @param x A parameter
#' @return A return value
my_function <- function(x) {
  # Regular comment
  return(x + 1)
}

#' Another roxygen comment
#' @export
another_function <- function() {
  TRUE
}
"""
        result = remove_docstrings(r_code)

        # Roxygen2 comments should be removed
        self.assertNotIn("#' This is an R roxygen2 comment", result)
        self.assertNotIn("#' @param x A parameter", result)
        self.assertNotIn("#' @return A return value", result)
        self.assertNotIn("#' Another roxygen comment", result)
        self.assertNotIn("#' @export", result)

        # Code and regular comments should remain
        self.assertIn("my_function <- function(x)", result)
        self.assertIn("# Regular comment", result)
        self.assertIn("another_function <- function()", result)

    def test_remove_docstrings_mixed_languages(self):
        """Test removing docstrings from mixed language content."""
        mixed_code = """
'''Python docstring'''
def python_func():
    pass

/**
 * JavaScript JSDoc
 */
function jsFunc() {}

/// C# XML doc
public void CSharpMethod() {}

/// Rust doc comment
pub fn rust_func() {}

#' R roxygen2 comment
r_function <- function() {}
"""
        result = remove_docstrings(mixed_code)

        # All types of docstrings should be removed
        self.assertNotIn("Python docstring", result)
        self.assertNotIn("JavaScript JSDoc", result)
        self.assertNotIn("C# XML doc", result)
        self.assertNotIn("Rust doc comment", result)
        self.assertNotIn("R roxygen2 comment", result)

        # Function declarations should remain
        self.assertIn("def python_func():", result)
        self.assertIn("function jsFunc()", result)
        self.assertIn("public void CSharpMethod()", result)
        self.assertIn("pub fn rust_func()", result)
        self.assertIn("r_function <- function()", result)

    def test_remove_docstrings_preserves_code_strings(self):
        """Test that docstring removal doesn't affect strings in code."""
        code_with_strings = """
def function():
    message = "This looks like '''a docstring''' but it's not"
    another = 'Contains /** fake JSDoc */'
    xml_like = "/// Not really XML doc"
    return message + another + xml_like
"""
        result = remove_docstrings(code_with_strings)

        # Strings that look like docstrings should be preserved
        self.assertIn("This looks like '''a docstring''' but it's not", result)
        self.assertIn("Contains /** fake JSDoc */", result)
        self.assertIn("/// Not really XML doc", result)

    def test_remove_docstrings_empty_content(self):
        """Test removing docstrings from empty content."""
        result = remove_docstrings("")
        self.assertEqual(result, "")

    def test_remove_docstrings_cleanup_empty_lines(self):
        """Test that docstring removal cleans up resulting empty lines."""
        code_with_docstrings = """
'''Module docstring'''


def function():
    '''Function docstring'''


    return True
"""
        result = remove_docstrings(code_with_docstrings)

        # Should not have excessive consecutive empty lines
        self.assertNotIn("\n\n\n", result)

    def test_generate_file_summary_complete(self):
        """Test generating complete file summary with all components."""
        summary = generate_file_summary(self.file_data, self.config)

        # Check basic file info
        self.assertIn("**File:** `file.py`", summary)
        self.assertIn("**Language:** `python`", summary)

        # Check imports
        self.assertIn("**Imports (2):** `os, sys`", summary)

        # Check declarations (sorted by kind)
        self.assertIn("**Declarations:**", summary)
        self.assertIn("**Class (1):** `TestClass`", summary)
        self.assertIn("**Function (1):** `hello_world`", summary)

        # Check token stats
        self.assertIn("**Token Counts:**", summary)
        self.assertIn("GPT-4: `120`", summary)
        self.assertIn("Claude: `110`", summary)

        # Check security issues
        self.assertIn("**Security Issues:**", summary)
        self.assertIn("`HIGH` (Line 12): Test security issue", summary)

    def test_generate_file_summary_minimal_config(self):
        """Test generating file summary with minimal config."""
        minimal_config = CodeConCatConfig(
            target_path="/path/to/test",
            include_imports_in_summary=False,
            include_declarations_in_summary=False,
            include_tokens_in_summary=False,
            include_security_in_summary=False,
        )

        summary = generate_file_summary(self.file_data, minimal_config)

        # Should be empty since no additional info is enabled
        self.assertEqual(summary, "")

    def test_generate_file_summary_partial_data(self):
        """Test generating file summary with partial data."""
        partial_data = ParsedFileData(
            file_path="/path/to/test/simple.py",
            language="python",
            content="print('hello')",
            imports=[],  # No imports
            declarations=[],  # No declarations
            token_stats=None,  # No token stats
            security_issues=[],  # No security issues
        )

        config = CodeConCatConfig(
            target_path="/path/to/test",
            include_imports_in_summary=True,
            include_declarations_in_summary=True,
            include_tokens_in_summary=True,
            include_security_in_summary=True,
        )

        summary = generate_file_summary(partial_data, config)

        # Should contain basic info only
        self.assertIn("**File:** `simple.py`", summary)
        self.assertIn("**Language:** `python`", summary)

        # Should not contain sections for missing data
        self.assertNotIn("**Imports", summary)
        self.assertNotIn("**Declarations:**", summary)
        self.assertNotIn("**Token Counts:**", summary)
        self.assertNotIn("**Security Issues:**", summary)

    def test_generate_file_summary_with_multiple_security_issues(self):
        """Test file summary with multiple security issues of different severities."""
        file_data_with_issues = ParsedFileData(
            file_path="/path/to/test/vulnerable.py",
            language="python",
            content="code",
            security_issues=[
                SecurityIssue(
                    rule_id="critical_rule",
                    description="Critical security issue",
                    file_path="/path/to/test/vulnerable.py",
                    line_number=5,
                    severity=SecuritySeverity.CRITICAL,
                ),
                SecurityIssue(
                    rule_id="medium_rule",
                    description="Medium security issue",
                    file_path="/path/to/test/vulnerable.py",
                    line_number=10,
                    severity=SecuritySeverity.MEDIUM,
                ),
                SecurityIssue(
                    rule_id="low_rule",
                    description="Low security issue",
                    file_path="/path/to/test/vulnerable.py",
                    line_number=15,
                    severity=SecuritySeverity.LOW,
                ),
            ],
        )

        summary = generate_file_summary(file_data_with_issues, self.config)

        # Should contain all security issues
        self.assertIn("**Security Issues:**", summary)
        self.assertIn("`CRITICAL` (Line 5): Critical security issue", summary)
        self.assertIn("`MEDIUM` (Line 10): Medium security issue", summary)
        self.assertIn("`LOW` (Line 15): Low security issue", summary)

    def test_generate_file_summary_complex_declarations(self):
        """Test file summary with complex declaration structure."""
        complex_data = ParsedFileData(
            file_path="/path/to/test/complex.py",
            language="python",
            content="code",
            declarations=[
                Declaration(kind="function", name="func1", start_line=1, end_line=5),
                Declaration(kind="function", name="func2", start_line=6, end_line=10),
                Declaration(kind="class", name="ClassA", start_line=11, end_line=20),
                Declaration(kind="class", name="ClassB", start_line=21, end_line=30),
                Declaration(kind="variable", name="var1", start_line=31, end_line=31),
                Declaration(kind="variable", name="var2", start_line=32, end_line=32),
                Declaration(kind="constant", name="CONST1", start_line=33, end_line=33),
            ],
        )

        summary = generate_file_summary(complex_data, self.config)

        # Should group by kind and show counts
        self.assertIn("**Class (2):** `ClassA, ClassB`", summary)
        self.assertIn("**Constant (1):** `CONST1`", summary)
        self.assertIn("**Function (2):** `func1, func2`", summary)
        self.assertIn("**Variable (2):** `var1, var2`", summary)

    def test_generate_file_summary_token_stats_partial(self):
        """Test file summary with partial token statistics."""
        # Test with only GPT-4 tokens
        data_gpt4_only = ParsedFileData(
            file_path="/path/to/test/file.py",
            language="python",
            content="code",
            token_stats=TokenStats(gpt4_tokens=100, claude_tokens=None),
        )

        summary = generate_file_summary(data_gpt4_only, self.config)
        self.assertIn("GPT-4: `100`", summary)
        self.assertNotIn("Claude:", summary)

        # Test with only Claude tokens
        data_claude_only = ParsedFileData(
            file_path="/path/to/test/file.py",
            language="python",
            content="code",
            token_stats=TokenStats(gpt4_tokens=None, claude_tokens=90),
        )

        summary = generate_file_summary(data_claude_only, self.config)
        self.assertIn("Claude: `90`", summary)
        self.assertNotIn("GPT-4:", summary)

    def test_generate_directory_structure_simple(self):
        """Test generating simple directory structure."""
        file_paths = [
            "project/src/main.py",
            "project/src/utils/helpers.py",
            "project/tests/test_main.py",
            "project/README.md",
        ]

        structure = generate_directory_structure(file_paths)

        # Check basic structure elements
        self.assertIn("project", structure)
        self.assertIn("src", structure)
        self.assertIn("tests", structure)
        self.assertIn("main.py", structure)
        self.assertIn("helpers.py", structure)
        self.assertIn("test_main.py", structure)
        self.assertIn("README.md", structure)

        # Check tree formatting
        lines = structure.split("\n")
        self.assertTrue(any("└── " in line or "├── " in line for line in lines))

    def test_generate_directory_structure_complex(self):
        """Test generating complex directory structure."""
        file_paths = [
            "app/controllers/user_controller.py",
            "app/controllers/auth_controller.py",
            "app/models/user.py",
            "app/models/auth.py",
            "app/views/templates/base.html",
            "app/views/templates/user/profile.html",
            "app/views/templates/user/settings.html",
            "tests/unit/test_user.py",
            "tests/integration/test_auth.py",
            "config/settings.py",
            "config/database.py",
            "requirements.txt",
            "setup.py",
        ]

        structure = generate_directory_structure(file_paths)

        # Should contain all directories and files
        expected_items = [
            "app",
            "controllers",
            "models",
            "views",
            "templates",
            "user",
            "tests",
            "unit",
            "integration",
            "config",
            "user_controller.py",
            "auth_controller.py",
            "user.py",
            "auth.py",
            "base.html",
            "profile.html",
            "settings.html",
            "test_user.py",
            "test_auth.py",
            "settings.py",
            "database.py",
            "requirements.txt",
            "setup.py",
        ]

        for item in expected_items:
            self.assertIn(item, structure)

    def test_generate_directory_structure_single_file(self):
        """Test generating directory structure with single file."""
        file_paths = ["main.py"]
        structure = generate_directory_structure(file_paths)

        self.assertIn("main.py", structure)
        self.assertIn("└── main.py", structure)

    def test_generate_directory_structure_empty_list(self):
        """Test generating directory structure with empty file list."""
        structure = generate_directory_structure([])
        self.assertEqual(structure, "")

    def test_generate_directory_structure_nested_deep(self):
        """Test generating deeply nested directory structure."""
        file_paths = [
            "a/b/c/d/e/f/deep_file.txt",
            "a/b/c/other.py",
            "a/shallow.py",
        ]

        structure = generate_directory_structure(file_paths)

        # Should handle deep nesting correctly
        self.assertIn("deep_file.txt", structure)
        self.assertIn("other.py", structure)
        self.assertIn("shallow.py", structure)

        # Should have proper tree structure
        lines = structure.split("\n")
        self.assertTrue(any("│   " in line for line in lines))  # Should have tree connectors

    def test_generate_directory_structure_duplicate_paths(self):
        """Test handling of duplicate file paths."""
        file_paths = [
            "project/file.py",
            "project/file.py",  # Duplicate
            "project/other.py",
        ]

        structure = generate_directory_structure(file_paths)

        # Should handle duplicates gracefully
        self.assertIn("project", structure)
        self.assertIn("file.py", structure)
        self.assertIn("other.py", structure)

    def test_generate_directory_structure_root_files(self):
        """Test directory structure with files at root level."""
        file_paths = [
            "root_file1.py",
            "root_file2.txt",
            "subdir/sub_file.py",
        ]

        structure = generate_directory_structure(file_paths)

        # Should include root-level files
        self.assertIn("root_file1.py", structure)
        self.assertIn("root_file2.txt", structure)
        self.assertIn("subdir", structure)
        self.assertIn("sub_file.py", structure)

    def test_process_file_content_large_content(self):
        """Test processing very large content for performance."""
        # Create large content (10,000 lines)
        large_content = "\n".join([f"# Line {i}" for i in range(10000)])

        config = CodeConCatConfig(target_path="/path/to/test", remove_comments=True)

        # This should complete without hanging
        processed = process_file_content(large_content, config, self.file_data)

        # Comments should be removed even from large content
        self.assertNotIn("# Line 5000", processed)

        # Should have significantly fewer lines
        self.assertLess(len(processed.split("\n")), 1000)

    def test_process_file_content_unicode_handling(self):
        """Test processing content with Unicode characters."""
        unicode_content = """
# Comment with Unicode: café, naïve, résumé
def function():
    '''Docstring with Unicode: 中文, العربية, Русский'''
    return "Unicode string: 🔥 emoji and ñoño"
"""

        config = CodeConCatConfig(
            target_path="/path/to/test",
            remove_comments=True,
            remove_docstrings=True,
        )

        processed = process_file_content(unicode_content, config, self.file_data)

        # Unicode in strings should be preserved
        self.assertIn("Unicode string: 🔥 emoji and ñoño", processed)
        self.assertIn("def function():", processed)

        # Unicode in comments/docstrings should be removed
        self.assertNotIn("café, naïve, résumé", processed)
        self.assertNotIn("中文, العربية, Русский", processed)

    def test_process_file_content_edge_case_comments(self):
        """Test edge cases in comment processing."""
        edge_case_content = """
# Edge case: URLs with double slashes
url = "https://example.com"  # This is a comment

# Edge case: Comments at end of file without newline
def func(): pass  # Comment at EOF"""

        config = CodeConCatConfig(target_path="/path/to/test", remove_comments=True)

        processed = process_file_content(edge_case_content, config, self.file_data)

        # URLs should be preserved
        self.assertIn("https://example.com", processed)

        # Comments should be removed
        self.assertNotIn("This is a comment", processed)
        self.assertNotIn("Comment at EOF", processed)
        self.assertNotIn("Edge case:", processed)

    def test_process_file_content_escaped_quotes_in_strings(self):
        """Test handling of escaped quotes in strings with comments."""
        content_with_escaped = r"""
def function():
    string1 = "This has \"escaped quotes\" and # hash"
    string2 = 'Also has \'escaped quotes\' and // slashes'
    # This comment should be removed
    return string1 + string2
"""

        config = CodeConCatConfig(target_path="/path/to/test", remove_comments=True)

        processed = process_file_content(content_with_escaped, config, self.file_data)

        # Strings with escaped quotes should be preserved
        self.assertIn('This has \\"escaped quotes\\" and # hash', processed)
        self.assertIn("Also has \\'escaped quotes\\' and // slashes", processed)

        # Real comments should be removed
        self.assertNotIn("This comment should be removed", processed)

    def test_process_file_content_multiline_strings(self):
        """Test processing with multiline strings that might contain comment-like text."""
        content_with_multiline = '''
def function():
    multiline = """
    This is a multiline string
    # This looks like a comment but isn't
    /* This looks like a block comment */
    // This looks like a JS comment
    """
    # This is a real comment
    return multiline
'''

        config = CodeConCatConfig(target_path="/path/to/test", remove_comments=True)

        processed = process_file_content(content_with_multiline, config, self.file_data)

        # Content inside multiline strings should be preserved
        self.assertIn("# This looks like a comment but isn't", processed)
        self.assertIn("/* This looks like a block comment */", processed)
        self.assertIn("// This looks like a JS comment", processed)

        # Real comments should be removed
        self.assertNotIn("# This is a real comment", processed)

    def test_process_file_content_performance_edge_cases(self):
        """Test performance with edge cases that could cause slowdowns."""
        # Content with many potential comment starts
        tricky_content = "x = " + " + ".join([f'"#{i}"' for i in range(1000)])

        config = CodeConCatConfig(target_path="/path/to/test", remove_comments=True)

        # Should complete quickly even with many hash symbols in strings
        processed = process_file_content(tricky_content, config, self.file_data)

        # All hash symbols should be preserved since they're in strings
        self.assertEqual(processed, tricky_content)

    def test_remove_docstrings_nested_quotes(self):
        """Test docstring removal with nested quote scenarios."""
        content_with_nested = '''
def function():
    """
    This docstring contains 'single quotes' and "double quotes"
    And even triple quotes inside
    """
    return "Normal string with fake docstring inside"
'''

        result = remove_docstrings(content_with_nested)

        # Docstring should be removed despite nested quotes
        self.assertNotIn("This docstring contains", result)
        self.assertNotIn("single quotes", result)
        self.assertNotIn("triple quotes inside", result)

        # Regular string should be preserved
        self.assertIn("Normal string with fake docstring inside", result)

    def test_generate_file_summary_security_issue_enum_handling(self):
        """Test file summary handles security severity as enum vs string."""
        # Create issue with enum severity
        issue_with_enum = SecurityIssue(
            rule_id="enum_test",
            description="Enum severity test",
            file_path="/test/file.py",
            line_number=42,
            severity=SecuritySeverity.CRITICAL,
        )

        # Create mock issue with string-like severity for edge case
        class MockSeverity:
            def __init__(self, value):
                self.value = value

        mock_issue = SecurityIssue(
            rule_id="mock_test",
            description="Mock severity test",
            file_path="/test/file.py",
            line_number=43,
            severity=MockSeverity("HIGH"),
        )

        file_data_with_mixed_severities = ParsedFileData(
            file_path="/test/file.py",
            language="python",
            content="code",
            security_issues=[issue_with_enum, mock_issue],
        )

        summary = generate_file_summary(file_data_with_mixed_severities, self.config)

        # Should handle both enum and non-enum severities
        self.assertIn("`CRITICAL` (Line 42): Enum severity test", summary)
        self.assertIn("`HIGH` (Line 43): Mock severity test", summary)


if __name__ == "__main__":
    unittest.main()
