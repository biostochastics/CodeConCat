"""Unit tests for doc_comment_utils module.

Tests the shared documentation comment cleaning utilities used by tree-sitter parsers.
"""

from codeconcat.parser.doc_comment_utils import (
    clean_block_comments,
    clean_jsdoc_tags,
    clean_line_comments,
    clean_xml_doc_comments,
    normalize_whitespace,
)


class TestCleanLineComments:
    """Test clean_line_comments function."""

    def test_basic_line_comments(self):
        """Test basic line comment cleaning."""
        lines = ["// This is", "// a comment"]
        result = clean_line_comments(lines, r"^//\s*")
        assert result == "This is a comment"

    def test_triple_slash_comments(self):
        """Test triple-slash documentation comments (Rust, C#)."""
        lines = ["/// This is", "/// a doc comment"]
        result = clean_line_comments(lines, r"^///\s*")
        assert result == "This is a doc comment"

    def test_hash_comments(self):
        """Test hash-based comments (Python, Julia, R)."""
        lines = ["# This is", "# a comment"]
        result = clean_line_comments(lines, r"^#\s*")
        assert result == "This is a comment"

    def test_roxygen_comments(self):
        """Test Roxygen comments (R)."""
        lines = ["#' Roxygen comment", "#' Second line"]
        result = clean_line_comments(lines, r"^#'\s*")
        assert result == "Roxygen comment Second line"

    def test_empty_lines_filtered(self):
        """Test that empty lines are filtered out."""
        lines = ["// First line", "//", "// Third line"]
        result = clean_line_comments(lines, r"^//\s*")
        assert result == "First line Third line"

    def test_preserve_newlines(self):
        """Test preserving line breaks when join_lines=False."""
        lines = ["// First line", "// Second line"]
        result = clean_line_comments(lines, r"^//\s*", join_lines=False)
        assert result == "First line\nSecond line"

    def test_no_strip_whitespace(self):
        """Test disabling whitespace stripping."""
        lines = ["//  Indented  ", "//  content  "]
        result = clean_line_comments(lines, r"^//", strip_whitespace=False)
        assert "  Indented  " in result

    def test_empty_input(self):
        """Test with empty input."""
        assert clean_line_comments([]) == ""


class TestCleanBlockComments:
    """Test clean_block_comments function."""

    def test_basic_javadoc(self):
        """Test basic Javadoc comment cleaning."""
        lines = ["/**", " * This is a", " * doc comment", " */"]
        result = clean_block_comments(lines)
        assert result == "This is a doc comment"

    def test_doxygen_comments(self):
        """Test Doxygen-style comments with /*!."""
        lines = ["/*!", " * Doxygen comment", " */"]
        result = clean_block_comments(lines, start_pattern=r"^/\*!")
        assert result == "Doxygen comment"

    def test_preserve_structure(self):
        """Test preserving line structure."""
        lines = ["/**", " * Line 1", " * Line 2", " */"]
        result = clean_block_comments(lines, preserve_structure=True)
        assert result == "Line 1\nLine 2"

    def test_without_asterisks(self):
        """Test block comment without leading asterisks."""
        lines = ["/**", "Simple comment", "*/"]
        result = clean_block_comments(lines)
        assert result == "Simple comment"

    def test_single_line_block(self):
        """Test single-line block comment."""
        lines = ["/** Single line comment */"]
        result = clean_block_comments(lines)
        assert result == "Single line comment"

    def test_empty_lines_filtered(self):
        """Test that empty lines are filtered out."""
        lines = ["/**", " * First", " *", " * Third", " */"]
        result = clean_block_comments(lines)
        assert result == "First Third"

    def test_empty_input(self):
        """Test with empty input."""
        assert clean_block_comments([]) == ""


class TestCleanXmlDocComments:
    """Test clean_xml_doc_comments function."""

    def test_simple_summary(self):
        """Test extracting simple summary tag."""
        xml = "<summary>This is a summary</summary>"
        result = clean_xml_doc_comments(xml)
        assert result == "This is a summary"

    def test_summary_with_param(self):
        """Test extracting summary and param tags."""
        xml = '<summary>Summary text</summary><param name="x">Parameter description</param>'
        result = clean_xml_doc_comments(xml, extract_tags=True)
        assert "Summary text" in result
        assert "Param x: Parameter description" in result

    def test_returns_tag(self):
        """Test extracting returns tag."""
        xml = "<summary>Method</summary><returns>Return value</returns>"
        result = clean_xml_doc_comments(xml, extract_tags=True)
        assert "Returns: Return value" in result

    def test_exception_tag(self):
        """Test extracting exception tag."""
        xml = '<summary>Method</summary><exception cref="ArgumentException">Throws when invalid</exception>'
        result = clean_xml_doc_comments(xml, extract_tags=True)
        assert "Throws ArgumentException: Throws when invalid" in result

    def test_remarks_tag(self):
        """Test extracting remarks tag."""
        xml = "<summary>Method</summary><remarks>Additional remarks</remarks>"
        result = clean_xml_doc_comments(xml, extract_tags=True)
        assert "Remarks: Additional remarks" in result

    def test_extract_all_text(self):
        """Test extracting all text without tag formatting."""
        xml = "<summary>Summary</summary><param name='x'>Param</param>"
        result = clean_xml_doc_comments(xml, extract_tags=False)
        # Should contain both texts without formatting
        assert "Summary" in result
        assert "Param" in result

    def test_invalid_xml_fallback(self):
        """Test graceful handling of invalid XML."""
        xml = "<summary>Unclosed tag"
        result = clean_xml_doc_comments(xml)
        # Should return something (fallback to regex cleaning)
        assert "Unclosed tag" in result

    def test_empty_input(self):
        """Test with empty input."""
        assert clean_xml_doc_comments("") == ""
        assert clean_xml_doc_comments("   ") == ""


class TestNormalizeWhitespace:
    """Test normalize_whitespace function."""

    def test_collapse_spaces(self):
        """Test collapsing multiple spaces."""
        text = "This  has   multiple    spaces"
        result = normalize_whitespace(text)
        assert result == "This has multiple spaces"

    def test_collapse_newlines(self):
        """Test collapsing multiple newlines."""
        text = "Line1\n\n\nLine2"
        result = normalize_whitespace(text, collapse_newlines=True)
        assert result == "Line1\nLine2"

    def test_preserve_newlines(self):
        """Test preserving newlines when requested."""
        text = "Line1\n\n\nLine2"
        result = normalize_whitespace(text, collapse_newlines=False)
        # Should still have multiple newlines
        assert "\n\n" in result

    def test_strip_whitespace(self):
        """Test stripping leading/trailing whitespace."""
        text = "  Content  "
        result = normalize_whitespace(text)
        assert result == "Content"

    def test_empty_input(self):
        """Test with empty input."""
        assert normalize_whitespace("") == ""


class TestCleanJsdocTags:
    """Test clean_jsdoc_tags function."""

    def test_param_tag_with_type(self):
        """Test cleaning @param tag with type."""
        text = "@param {string} name - The name parameter"
        result = clean_jsdoc_tags(text)
        assert result == "Param name (string): The name parameter"

    def test_param_tag_without_type(self):
        """Test cleaning @param tag without type."""
        text = "@param name - The name parameter"
        result = clean_jsdoc_tags(text)
        assert result == "Param name: The name parameter"

    def test_returns_tag_with_type(self):
        """Test cleaning @returns tag with type."""
        text = "@returns {boolean} True if valid"
        result = clean_jsdoc_tags(text)
        assert result == "Returns (boolean): True if valid"

    def test_return_tag_variant(self):
        """Test @return variant of @returns."""
        text = "@return {string} The result"
        result = clean_jsdoc_tags(text)
        assert result == "Returns (string): The result"

    def test_throws_tag(self):
        """Test cleaning @throws tag."""
        text = "@throws {Error} When validation fails"
        result = clean_jsdoc_tags(text)
        assert result == "Throws Error: When validation fails"

    def test_exception_tag(self):
        """Test @exception variant of @throws."""
        text = "@exception {TypeError} Invalid type"
        result = clean_jsdoc_tags(text)
        assert result == "Throws TypeError: Invalid type"

    def test_other_tags(self):
        """Test other common tags."""
        text = "@deprecated Use newMethod instead"
        result = clean_jsdoc_tags(text)
        assert result == "Deprecated: Use newMethod instead"

    def test_multiple_tags(self):
        """Test multiple tags in one block."""
        text = """@param {string} name - The name
@returns {boolean} True if valid"""
        result = clean_jsdoc_tags(text)
        assert "Param name (string): The name" in result
        assert "Returns (boolean): True if valid" in result

    def test_non_tag_lines_preserved(self):
        """Test that non-tag lines are preserved."""
        text = """This is a description
@param x - Parameter
More description"""
        result = clean_jsdoc_tags(text)
        assert "This is a description" in result
        assert "More description" in result

    def test_empty_input(self):
        """Test with empty input."""
        assert clean_jsdoc_tags("") == ""


class TestIntegration:
    """Integration tests combining multiple utilities."""

    def test_python_docstring_cleaning(self):
        """Test cleaning Python-style docstrings."""
        lines = ['"""', "This is a docstring", "with multiple lines", '"""']
        # First clean as block comment
        result = clean_block_comments(
            lines, start_pattern=r'^"""', line_pattern=r"^", end_pattern=r'"""$'
        )
        assert result == "This is a docstring with multiple lines"

    def test_go_doc_comments(self):
        """Test cleaning Go-style documentation comments."""
        lines = ["// Package foo provides utilities.", "// It has multiple features."]
        result = clean_line_comments(lines, r"^//\s*")
        assert result == "Package foo provides utilities. It has multiple features."

    def test_rust_doc_comments(self):
        """Test cleaning Rust-style documentation comments."""
        lines = ["/// This function does something.", "/// It returns a value."]
        result = clean_line_comments(lines, r"^///\s*")
        assert result == "This function does something. It returns a value."

    def test_jsdoc_complete_example(self):
        """Test complete JSDoc cleaning workflow."""
        lines = [
            "/**",
            " * Calculate the sum of two numbers",
            " * @param {number} a - First number",
            " * @param {number} b - Second number",
            " * @returns {number} The sum",
            " */",
        ]
        # Clean block comment while preserving structure for tag processing
        cleaned = clean_block_comments(lines, preserve_structure=True)
        # Then clean JSDoc tags
        result = clean_jsdoc_tags(cleaned)
        assert "Calculate the sum of two numbers" in result
        assert "Param a (number): First number" in result
        assert "Param b (number): Second number" in result
        assert "Returns (number): The sum" in result

    def test_csharp_xml_complete_example(self):
        """Test complete C# XML doc cleaning workflow."""
        xml = """<summary>
        Gets or sets the user name
        </summary>
        <param name="value">The new name</param>
        <returns>The user name</returns>
        """
        result = clean_xml_doc_comments(xml, extract_tags=True)
        result = normalize_whitespace(result)
        assert "Gets or sets the user name" in result
        assert "Param value: The new name" in result
        assert "Returns: The user name" in result
