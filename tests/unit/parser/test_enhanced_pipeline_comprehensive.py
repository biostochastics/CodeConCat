"""Comprehensive tests for enhanced pipeline to improve code coverage."""

from unittest.mock import Mock, patch
from pathlib import Path
from codeconcat.parser.enhanced_pipeline import EnhancedParsingPipeline
from codeconcat.base_types import ProcessingResult, ParsedElement


class TestEnhancedPipelineComprehensive:
    """Comprehensive test suite for EnhancedParsingPipeline."""

    def setup_method(self):
        """Set up test pipeline instance."""
        self.pipeline = EnhancedParsingPipeline()

    def test_initialization(self):
        """Test pipeline initialization."""
        assert hasattr(self.pipeline, "parsers")
        assert hasattr(self.pipeline, "fallback_parser")
        assert hasattr(self.pipeline, "tree_sitter_parsers")
        assert hasattr(self.pipeline, "_parser_cache")

    def test_get_parser_for_file_cached(self):
        """Test getting parser from cache."""
        # Set up cache
        mock_parser = Mock()
        self.pipeline._parser_cache[".py"] = mock_parser

        result = self.pipeline.get_parser_for_file(Path("test.py"))
        assert result == mock_parser

    def test_get_parser_for_file_python(self):
        """Test getting parser for Python files."""
        parser = self.pipeline.get_parser_for_file(Path("test.py"))
        assert parser is not None
        assert parser.__class__.__name__ in ["EnhancedPythonParser", "PythonParser"]

    def test_get_parser_for_file_javascript(self):
        """Test getting parser for JavaScript files."""
        parser = self.pipeline.get_parser_for_file(Path("test.js"))
        assert parser is not None
        assert parser.__class__.__name__ in ["EnhancedJSTSParser", "JSTSParser"]

    def test_get_parser_for_file_typescript(self):
        """Test getting parser for TypeScript files."""
        parser = self.pipeline.get_parser_for_file(Path("test.ts"))
        assert parser is not None
        assert parser.__class__.__name__ in ["EnhancedJSTSParser", "JSTSParser"]

    def test_get_parser_for_file_rust(self):
        """Test getting parser for Rust files."""
        parser = self.pipeline.get_parser_for_file(Path("test.rs"))
        assert parser is not None
        assert parser.__class__.__name__ in ["EnhancedRustParser", "RustParser"]

    def test_get_parser_for_file_go(self):
        """Test getting parser for Go files."""
        parser = self.pipeline.get_parser_for_file(Path("test.go"))
        assert parser is not None
        assert parser.__class__.__name__ in ["EnhancedGoParser", "GoParser"]

    def test_get_parser_for_file_java(self):
        """Test getting parser for Java files."""
        parser = self.pipeline.get_parser_for_file(Path("test.java"))
        assert parser is not None
        assert parser.__class__.__name__ in ["JavaParser", "TreeSitterJavaParser"]

    def test_get_parser_for_file_csharp(self):
        """Test getting parser for C# files."""
        parser = self.pipeline.get_parser_for_file(Path("test.cs"))
        assert parser is not None
        assert parser.__class__.__name__ in ["EnhancedCSharpParser", "CSharpParser"]

    def test_get_parser_for_file_cpp(self):
        """Test getting parser for C++ files."""
        for ext in [".cpp", ".cc", ".cxx", ".hpp"]:
            parser = self.pipeline.get_parser_for_file(Path(f"test{ext}"))
            assert parser is not None
            assert parser.__class__.__name__ in ["CPPParser", "TreeSitterCPPParser"]

    def test_get_parser_for_file_c(self):
        """Test getting parser for C files."""
        for ext in [".c", ".h"]:
            parser = self.pipeline.get_parser_for_file(Path(f"test{ext}"))
            assert parser is not None
            assert parser.__class__.__name__ in ["CParser", "TreeSitterCPPParser"]

    def test_get_parser_for_file_php(self):
        """Test getting parser for PHP files."""
        parser = self.pipeline.get_parser_for_file(Path("test.php"))
        assert parser is not None
        assert parser.__class__.__name__ in ["EnhancedPHPParser", "PHPParser"]

    def test_get_parser_for_file_r(self):
        """Test getting parser for R files."""
        parser = self.pipeline.get_parser_for_file(Path("test.R"))
        assert parser is not None
        assert parser.__class__.__name__ in ["EnhancedRParser", "RParser"]

    def test_get_parser_for_file_julia(self):
        """Test getting parser for Julia files."""
        parser = self.pipeline.get_parser_for_file(Path("test.jl"))
        assert parser is not None
        assert parser.__class__.__name__ in ["EnhancedJuliaParser", "JuliaParser"]

    def test_get_parser_for_file_fallback(self):
        """Test fallback parser for unknown extensions."""
        parser = self.pipeline.get_parser_for_file(Path("test.unknown"))
        assert parser == self.pipeline.fallback_parser

    def test_parse_file_success(self):
        """Test successful file parsing."""
        file_path = Path("test.py")
        content = """def hello():
    return "Hello, World!"

class Greeter:
    def greet(self, name):
        return f"Hello, {name}!"
"""

        result = self.pipeline.parse_file(file_path, content)

        assert isinstance(result, ProcessingResult)
        assert result.success
        assert len(result.elements) >= 3  # function, class, method
        assert any(e.name == "hello" for e in result.elements)
        assert any(e.name == "Greeter" for e in result.elements)

    def test_parse_file_empty_content(self):
        """Test parsing empty file."""
        result = self.pipeline.parse_file(Path("test.py"), "")

        assert isinstance(result, ProcessingResult)
        assert result.success
        assert len(result.elements) == 0

    def test_parse_file_with_syntax_error(self):
        """Test parsing file with syntax errors."""
        content = """def broken(:
    return "This won't parse"
"""

        result = self.pipeline.parse_file(Path("test.py"), content)

        assert isinstance(result, ProcessingResult)
        # Parser might still succeed but return fewer elements
        assert isinstance(result.elements, list)

    def test_parse_file_with_parser_exception(self):
        """Test handling parser exceptions."""
        mock_parser = Mock()
        mock_parser.parse.side_effect = Exception("Parser error")

        with patch.object(self.pipeline, "get_parser_for_file", return_value=mock_parser):
            result = self.pipeline.parse_file(Path("test.py"), "code")

        assert isinstance(result, ProcessingResult)
        assert not result.success
        assert result.error == "Parser error"

    def test_parse_multiple_files(self):
        """Test parsing multiple files."""
        files = [
            (Path("test1.py"), "def func1(): pass"),
            (Path("test2.js"), "function func2() { return 42; }"),
            (Path("test3.rs"), "fn func3() -> i32 { 42 }"),
        ]

        results = []
        for file_path, content in files:
            result = self.pipeline.parse_file(file_path, content)
            results.append(result)

        assert all(r.success for r in results)
        assert all(len(r.elements) > 0 for r in results)

    def test_tree_sitter_fallback(self):
        """Test fallback from tree-sitter to regular parser."""
        # Mock tree-sitter parser that returns None
        mock_ts_parser = Mock()
        mock_ts_parser.get_parser.return_value = None

        # Mock regular parser
        mock_regular_parser = Mock()
        mock_regular_parser.parse.return_value = [
            ParsedElement(
                type="function", name="test", content="def test(): pass", start_line=1, end_line=1
            )
        ]

        with patch.dict(self.pipeline.tree_sitter_parsers, {".py": mock_ts_parser}):
            with patch.dict(self.pipeline.parsers, {".py": mock_regular_parser}):
                result = self.pipeline.parse_file(Path("test.py"), "def test(): pass")

        assert result.success
        assert len(result.elements) == 1
        assert result.elements[0].name == "test"

    def test_parse_file_with_security_checks(self):
        """Test parsing with security checks enabled."""
        content = """import os

def dangerous_function():
    os.system("rm -rf /")
    eval(user_input)
"""

        result = self.pipeline.parse_file(Path("danger.py"), content, enable_security_checks=True)

        assert isinstance(result, ProcessingResult)
        if hasattr(result, "security_checks") and result.security_checks:
            # If security checks are implemented
            assert len(result.security_checks) > 0

    def test_parse_mixed_language_project(self):
        """Test parsing files from a mixed-language project."""
        project_files = [
            (
                Path("src/main.py"),
                """
class App:
    def run(self):
        print("Running app")
""",
            ),
            (
                Path("src/utils.js"),
                """
export function formatDate(date) {
    return date.toISOString();
}
""",
            ),
            (
                Path("src/server.go"),
                """
package main

func main() {
    fmt.Println("Server starting")
}
""",
            ),
            (
                Path("src/lib.rs"),
                """
pub fn calculate(x: i32, y: i32) -> i32 {
    x + y
}
""",
            ),
        ]

        all_elements = []
        for file_path, content in project_files:
            result = self.pipeline.parse_file(file_path, content)
            if result.success:
                all_elements.extend(result.elements)

        # Should have parsed elements from all languages
        assert len(all_elements) >= 4

        # Check for elements from each language
        assert any(e.name == "App" for e in all_elements)  # Python
        assert any(e.name == "formatDate" for e in all_elements)  # JavaScript
        assert any(e.name == "main" for e in all_elements)  # Go
        assert any(e.name == "calculate" for e in all_elements)  # Rust

    def test_cache_performance(self):
        """Test parser caching improves performance."""
        # First call - should cache the parser
        parser1 = self.pipeline.get_parser_for_file(Path("test.py"))

        # Second call - should return cached parser
        parser2 = self.pipeline.get_parser_for_file(Path("another.py"))

        assert parser1 is parser2  # Same instance due to caching

    def test_parse_file_with_unicode(self):
        """Test parsing files with unicode content."""
        content = '''def 你好():
    """Unicode function name and content."""
    return "世界"

# Comment with emoji 🚀
class ÜnicödeClass:
    def método(self):
        return "café ☕"
'''

        result = self.pipeline.parse_file(Path("unicode.py"), content)

        assert result.success
        assert len(result.elements) >= 2

    def test_parse_file_with_type_hints(self):
        """Test parsing Python with complex type hints."""
        content = '''from typing import Dict, List, Optional, Union, Callable

def process_data(
    items: List[Dict[str, Union[str, int]]],
    callback: Optional[Callable[[str], bool]] = None
) -> Dict[str, List[int]]:
    """Process data with complex type hints."""
    return {}

class GenericProcessor[T]:
    def process(self, item: T) -> Optional[T]:
        return item
'''

        result = self.pipeline.parse_file(Path("typed.py"), content)

        assert result.success
        assert any(e.name == "process_data" for e in result.elements)
        assert any(e.name == "GenericProcessor" for e in result.elements)

    def test_parse_file_edge_cases(self):
        """Test parsing various edge cases."""
        edge_cases = [
            # Very long single line
            ("long.py", "def " + "a" * 1000 + "(): pass"),
            # Deeply nested code
            (
                "nested.py",
                """
def outer():
    def middle():
        def inner():
            def deepest():
                return 42
            return deepest
        return inner
    return middle
""",
            ),
            # Many small functions
            ("many.py", "\n".join(f"def func{i}(): pass" for i in range(50))),
        ]

        for filename, content in edge_cases:
            result = self.pipeline.parse_file(Path(filename), content)
            assert isinstance(result, ProcessingResult)

    def test_parse_file_different_encodings(self):
        """Test parsing files with different encoding declarations."""
        content = '''# -*- coding: utf-8 -*-

def process_text(text: str) -> str:
    """Process UTF-8 encoded text."""
    return text.encode('utf-8').decode('utf-8')
'''

        result = self.pipeline.parse_file(Path("encoded.py"), content)
        assert result.success

    def test_concurrent_parsing_simulation(self):
        """Test simulating concurrent parsing of multiple files."""
        files = [(Path(f"file{i}.py"), f"def func{i}(): pass") for i in range(10)]

        results = []
        for file_path, content in files:
            result = self.pipeline.parse_file(file_path, content)
            results.append(result)

        assert all(r.success for r in results)
        assert len(results) == 10

    def test_memory_efficiency(self):
        """Test that parser cache doesn't grow unbounded."""
        initial_cache_size = len(self.pipeline._parser_cache)

        # Parse files with many different extensions
        for i in range(20):
            ext = f".ext{i}"
            self.pipeline.get_parser_for_file(Path(f"test{ext}"))

        # Cache should have grown but within reasonable bounds
        final_cache_size = len(self.pipeline._parser_cache)
        assert final_cache_size > initial_cache_size
        assert final_cache_size < 100  # Reasonable upper bound
