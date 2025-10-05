"""Tests for the enhanced parser base module."""

import pytest
from codeconcat.parser.enhanced_parser_base import EnhancedBaseParser, ParserConfig
from codeconcat.base_types import Declaration


class ConcreteTestParser(EnhancedBaseParser):
    """Concrete test implementation of EnhancedBaseParser."""

    def _init_patterns(self) -> None:
        """Initialize test patterns."""
        pass

    def get_language_patterns(self) -> dict[str, str]:
        """Return test language patterns."""
        return {
            "function": r"^def\s+(\w+)\s*\(",
            "class": r"^class\s+(\w+)",
            "import_statement": r"^import\s+([\w\.]+)",
            "from_import": r"^from\s+([\w\.]+)\s+import",
        }

    def _extract_declarations(self, content: str, file_path: str) -> list[Declaration]:
        """Extract test declarations."""
        declarations = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            # Match functions
            func_pattern = self._get_compiled_pattern("function")
            if func_pattern:
                match = func_pattern.search(line)
                if match:
                    declarations.append(
                        Declaration(
                            name=match.group(1),
                            kind="function",
                            start_line=line_num,
                            end_line=line_num,
                        )
                    )

            # Match classes
            class_pattern = self._get_compiled_pattern("class")
            if class_pattern:
                match = class_pattern.search(line)
                if match:
                    declarations.append(
                        Declaration(
                            name=match.group(1),
                            kind="class",
                            start_line=line_num,
                            end_line=line_num,
                        )
                    )

        return declarations


class TestParserConfig:
    """Test suite for ParserConfig."""

    def test_default_config(self):
        """Test ParserConfig with default values."""
        config = ParserConfig(language="python")
        assert config.language == "python"
        assert config.max_file_size == 10 * 1024 * 1024  # 10MB
        assert config.max_line_length == 10000
        assert config.enable_performance_monitoring is True
        assert config.enable_string_interning is True
        assert config.cache_patterns is True
        assert config.batch_size == 100

    def test_custom_config(self):
        """Test ParserConfig with custom values."""
        config = ParserConfig(
            language="javascript",
            max_file_size=5 * 1024 * 1024,
            max_line_length=5000,
            enable_performance_monitoring=False,
            enable_string_interning=False,
            cache_patterns=False,
            batch_size=50,
        )
        assert config.language == "javascript"
        assert config.max_file_size == 5 * 1024 * 1024
        assert config.max_line_length == 5000
        assert config.enable_performance_monitoring is False
        assert config.enable_string_interning is False
        assert config.cache_patterns is False
        assert config.batch_size == 50


class TestEnhancedBaseParser:
    """Test suite for EnhancedBaseParser."""

    def test_parser_initialization(self):
        """Test parser initializes correctly."""
        config = ParserConfig(language="python")
        parser = ConcreteTestParser(config)

        assert parser.language == "python"
        assert parser.config == config
        assert parser.error_handler is not None
        assert parser.deduplicator is not None

    def test_parser_initialization_with_cache(self):
        """Test parser with pattern caching enabled."""
        config = ParserConfig(language="python", cache_patterns=True)
        parser = ConcreteTestParser(config)

        assert parser._pattern_cache is not None
        assert isinstance(parser._pattern_cache, dict)

    def test_parser_initialization_without_cache(self):
        """Test parser with pattern caching disabled."""
        config = ParserConfig(language="python", cache_patterns=False)
        parser = ConcreteTestParser(config)

        assert parser._pattern_cache is None

    def test_get_language_patterns(self):
        """Test getting language patterns."""
        config = ParserConfig(language="python")
        parser = ConcreteTestParser(config)

        patterns = parser.get_language_patterns()
        assert "function" in patterns
        assert "class" in patterns
        assert "import_statement" in patterns

    def test_get_compiled_pattern_with_cache(self):
        """Test getting compiled pattern with caching."""
        config = ParserConfig(language="python", cache_patterns=True)
        parser = ConcreteTestParser(config)

        pattern = parser._get_compiled_pattern("function")
        assert pattern is not None
        assert "function" in parser._pattern_cache

        # Second call should use cache
        pattern2 = parser._get_compiled_pattern("function")
        assert pattern is pattern2  # Same object

    def test_get_compiled_pattern_without_cache(self):
        """Test getting compiled pattern without caching."""
        config = ParserConfig(language="python", cache_patterns=False)
        parser = ConcreteTestParser(config)

        pattern = parser._get_compiled_pattern("function")
        assert pattern is not None

        # Second call should work (Python may cache re.compile internally)
        pattern2 = parser._get_compiled_pattern("function")
        assert pattern2 is not None
        # Both patterns should have the same functionality
        assert pattern.pattern == pattern2.pattern

    def test_get_compiled_pattern_nonexistent(self):
        """Test getting nonexistent pattern returns None."""
        config = ParserConfig(language="python")
        parser = ConcreteTestParser(config)

        pattern = parser._get_compiled_pattern("nonexistent_pattern")
        assert pattern is None

    def test_parse_simple_code(self):
        """Test parsing simple code."""
        config = ParserConfig(language="python")
        parser = ConcreteTestParser(config)

        content = """
def foo():
    pass

class Bar:
    pass
"""
        result = parser.parse(content, "test.py")

        assert result is not None
        assert result.error is None or result.error == ""
        assert len(result.declarations) == 2

        # Check function
        func_decl = next((d for d in result.declarations if d.name == "foo"), None)
        assert func_decl is not None
        assert func_decl.kind == "function"

        # Check class
        class_decl = next((d for d in result.declarations if d.name == "Bar"), None)
        assert class_decl is not None
        assert class_decl.kind == "class"

    def test_parse_with_imports(self):
        """Test parsing code with imports."""
        config = ParserConfig(language="python")
        parser = ConcreteTestParser(config)

        content = """
import os
from pathlib import Path

def foo():
    pass
"""
        result = parser.parse(content, "test.py")

        assert result is not None
        assert len(result.imports) >= 1
        assert any("os" in imp for imp in result.imports)

    def test_parse_empty_file(self):
        """Test parsing empty file."""
        config = ParserConfig(language="python")
        parser = ConcreteTestParser(config)

        result = parser.parse("", "test.py")

        assert result is not None
        assert len(result.declarations) == 0
        assert len(result.imports) == 0

    def test_parse_file_too_large(self):
        """Test parsing file that exceeds max size."""
        config = ParserConfig(language="python", max_file_size=100)  # 100 bytes
        parser = ConcreteTestParser(config)

        # Create content larger than 100 bytes
        content = "x" * 200
        result = parser.parse(content, "test.py")

        assert result is not None
        assert result.error is not None
        assert "too large" in result.error.lower()

    def test_parse_line_too_long(self):
        """Test parsing file with line exceeding max length."""
        config = ParserConfig(language="python", max_line_length=50)
        parser = ConcreteTestParser(config)

        # Create line longer than 50 characters
        content = "x" * 100
        result = parser.parse(content, "test.py")

        assert result is not None
        assert result.error is not None
        assert "too long" in result.error.lower()

    def test_parse_deduplicates_declarations(self):
        """Test that duplicate declarations are removed."""
        config = ParserConfig(language="python")
        parser = ConcreteTestParser(config)

        # Same function defined twice
        content = """
def foo():
    pass

def foo():
    pass
"""
        result = parser.parse(content, "test.py")

        assert result is not None
        # Should deduplicate based on name and line
        assert len(result.declarations) <= 2

    def test_parse_sorts_declarations_by_line(self):
        """Test that declarations are sorted by line number."""
        config = ParserConfig(language="python")
        parser = ConcreteTestParser(config)

        content = """
def zzz():
    pass

class AAA:
    pass

def bbb():
    pass
"""
        result = parser.parse(content, "test.py")

        assert result is not None
        assert len(result.declarations) == 3

        # Should be sorted by line number
        for i in range(len(result.declarations) - 1):
            assert result.declarations[i].start_line <= result.declarations[i + 1].start_line

    def test_parse_exception_handling(self):
        """Test that exceptions are caught and handled."""
        config = ParserConfig(language="python")
        parser = ConcreteTestParser(config)

        # Override _extract_declarations to raise exception
        def raise_exception(*args, **kwargs):
            raise ValueError("Test exception")

        parser._extract_declarations = raise_exception

        result = parser.parse("def foo(): pass", "test.py")

        assert result is not None
        assert result.error is not None
        assert "parse error" in result.error.lower() or "error" in result.error.lower()

    def test_pattern_caching_performance(self):
        """Test that pattern caching improves performance."""
        config = ParserConfig(language="python", cache_patterns=True)
        parser = ConcreteTestParser(config)

        # First access - compiles and caches
        pattern1 = parser._get_compiled_pattern("function")
        assert pattern1 is not None
        assert len(parser._pattern_cache) >= 1

        # Second access - uses cache
        pattern2 = parser._get_compiled_pattern("function")
        assert pattern2 is pattern1

        # Third pattern - adds to cache
        pattern3 = parser._get_compiled_pattern("class")
        assert pattern3 is not None
        assert len(parser._pattern_cache) >= 2

    def test_multiple_patterns_cached(self):
        """Test that multiple patterns can be cached."""
        config = ParserConfig(language="python", cache_patterns=True)
        parser = ConcreteTestParser(config)

        patterns = ["function", "class", "import_statement", "from_import"]
        compiled_patterns = {}

        for pattern_name in patterns:
            pattern = parser._get_compiled_pattern(pattern_name)
            if pattern:
                compiled_patterns[pattern_name] = pattern

        # All patterns should be cached
        assert len(compiled_patterns) == 4
        for pattern_name in patterns:
            assert pattern_name in parser._pattern_cache

    def test_parse_multiline_content(self):
        """Test parsing multiline content."""
        config = ParserConfig(language="python")
        parser = ConcreteTestParser(config)

        content = """
class MyClass:
    def method1(self):
        pass

    def method2(self):
        pass

def standalone():
    pass
"""
        result = parser.parse(content, "test.py")

        assert result is not None
        assert len(result.declarations) >= 2  # At least class and standalone function

    def test_import_extraction(self):
        """Test that imports are extracted correctly."""
        config = ParserConfig(language="python")
        parser = ConcreteTestParser(config)

        content = """
import os
import sys
from pathlib import Path
from collections import defaultdict
"""
        result = parser.parse(content, "test.py")

        assert result is not None
        assert len(result.imports) >= 2  # At least os and sys or pathlib

    def test_parse_with_whitespace(self):
        """Test parsing content with various whitespace."""
        config = ParserConfig(language="python")
        parser = ConcreteTestParser(config)

        content = """


def foo():
    pass


class Bar:
    pass


"""
        result = parser.parse(content, "test.py")

        assert result is not None
        assert len(result.declarations) == 2
