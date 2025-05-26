"""Tests for string utility functions."""

from codeconcat.processor.string_utils import is_inside_string


class TestIsInsideString:
    """Test is_inside_string function."""

    def test_not_in_string(self):
        """Test positions not inside strings."""
        line = "print('hello')"
        assert is_inside_string(line, 0) is False  # 'p' of print
        assert is_inside_string(line, 5) is False  # '('
        assert is_inside_string(line, 13) is False  # ')' at end

    def test_inside_single_quote_string(self):
        """Test positions inside single-quoted strings."""
        line = "print('hello world')"
        assert is_inside_string(line, 7) is True  # 'h' of hello
        assert is_inside_string(line, 8) is True  # 'e' of hello
        assert is_inside_string(line, 12) is True  # 'w' of world
        assert is_inside_string(line, 18) is True  # 'd' at end of world

    def test_inside_double_quote_string(self):
        """Test positions inside double-quoted strings."""
        line = 'print("hello world")'
        assert is_inside_string(line, 7) is True  # 'h' of hello
        assert is_inside_string(line, 12) is True  # 'w' of world
        assert is_inside_string(line, 18) is True  # 'd' at end

    def test_escaped_quotes(self):
        """Test handling of escaped quotes."""
        # Single quotes with escaped quote
        line = "print('it\\'s great')"
        assert is_inside_string(line, 10) is True  # The backslash
        assert is_inside_string(line, 11) is True  # The escaped quote
        assert is_inside_string(line, 12) is True  # 's' after escaped quote

        # Double quotes with escaped quote
        line = 'print("Say \\"Hi\\"")'
        assert is_inside_string(line, 11) is True  # The backslash
        assert is_inside_string(line, 12) is True  # The escaped quote
        assert is_inside_string(line, 13) is True  # 'H' after escaped quote

    def test_multiple_strings(self):
        """Test line with multiple strings."""
        line = "a = 'first' + 'second'"
        assert is_inside_string(line, 5) is True  # 'f' in first
        assert is_inside_string(line, 11) is False  # space between strings
        assert is_inside_string(line, 12) is False  # '+' operator
        assert is_inside_string(line, 15) is True  # 's' in second

    def test_mixed_quotes(self):
        """Test handling mixed quote types."""
        line = """print("He said 'hello'")"""
        assert is_inside_string(line, 7) is True  # Inside double quotes
        assert is_inside_string(line, 15) is True  # Single quote inside double
        assert is_inside_string(line, 20) is True  # Still inside double quotes

    def test_edge_cases(self):
        """Test edge cases."""
        # Empty string
        assert is_inside_string("", 0) is False

        # Position out of bounds
        assert is_inside_string("test", -1) is False
        assert is_inside_string("test", 10) is False

        # String at very start
        line = "'string' + other"
        assert is_inside_string(line, 0) is False  # Opening quote
        assert is_inside_string(line, 1) is True  # 's' inside string

    def test_complex_escapes(self):
        """Test complex escape sequences."""
        # Double backslash should not escape the quote
        line = "print('test\\\\n')"  # Contains \\n
        assert is_inside_string(line, 11) is True  # First backslash
        assert is_inside_string(line, 12) is True  # Second backslash
        assert is_inside_string(line, 13) is True  # 'n'

        # Escaped backslash at end
        line = "print('test\\\\')"
        assert is_inside_string(line, 11) is True  # First backslash
        assert is_inside_string(line, 12) is True  # Second backslash

    def test_unterminated_string(self):
        """Test behavior with unterminated strings."""
        line = "print('unterminated"
        assert is_inside_string(line, 10) is True  # Inside unterminated string
        assert is_inside_string(line, 15) is True  # Still inside
        assert is_inside_string(line, 18) is True  # At the end

    def test_triple_quotes_simple(self):
        """Test simple cases that look like triple quotes."""
        # Note: This function doesn't handle actual triple-quoted strings
        # as multi-line strings, just the characters on one line
        line = 'text = """hello"""'
        assert is_inside_string(line, 7) is False  # First quote starts string
        assert is_inside_string(line, 8) is True  # Second quote inside string
        assert is_inside_string(line, 10) is True  # Inside the string that starts at third quote
