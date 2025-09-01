#!/usr/bin/env python3

"""

Unit tests for the base parser components in CodeConCat.

Tests the EnhancedBaseParser class to ensure shared functionality
works across all language parsers.
"""

import logging
import re

import pytest

from codeconcat.base_types import Declaration, ParseResult, ParserInterface
from codeconcat.parser.enable_debug import enable_all_parser_debug_logging
from codeconcat.parser.language_parsers.enhanced_base_parser import EnhancedBaseParser

# Enable debug logging for all parsers
enable_all_parser_debug_logging()

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class TestParser(EnhancedBaseParser):
    """Test implementation of EnhancedBaseParser for testing."""

    def __init__(self, language="test"):
        """Initialize with custom language."""
        super().__init__()
        self.language = language
        self.line_comment = "#"
        self.block_comment_start = "/*"
        self.block_comment_end = "*/"

        # Setup test patterns
        self.patterns = {
            "function": r"function\s+(\w+)",
            "class": r"class\s+(\w+)",
            "import": r"import\s+(\w+)",
            "method": r"method\s+(\w+)",
        }

    def parse(self, content: str, _file_path: str) -> ParseResult:
        """Override parse method for testing."""
        lines = content.splitlines()
        declarations = []
        imports = []

        # Find function declarations using pattern
        for i, line in enumerate(lines):
            if "function" in line:
                match = re.search(self.patterns["function"], line)
                if match:
                    name = match.group(1)
                    docstring = self.extract_docstring(lines, i, i + 5)
                    end_idx = self._find_block_end_improved(lines, i, "{", "}", False)
                    declarations.append(
                        Declaration(
                            name=name,
                            kind="function",
                            start_line=i,
                            end_line=end_idx,
                            docstring=docstring,
                        )
                    )

            # Find imports
            if "import" in line:
                match = re.search(self.patterns["import"], line)
                if match:
                    imports.append(match.group(1))

        # Create result - using only the parameters available in ParseResult
        result = ParseResult(declarations=declarations, imports=imports, engine_used="regex")
        return result


class TestBaseParser:
    """Test class for the BaseParser component."""

    @pytest.fixture
    def mixed_code_sample(self) -> str:
        """Fixture providing a sample mixed-language code for testing base parser functions."""
        return """// This file has mixed language syntax to test parser flexibility

/*
 * Block comment at the top
 * with multiple lines
 */

# Python-style comment
# Another comment

function testFunction() {
    /* Function docstring */
    const x = 10;
    return x * 2;
}

class TestClass {
    /* Class docstring
     * with multiple lines
     */

    method test() {
        return "test";
    }
}

# A line with both braces { } in it

import module1
import module2

// Nested blocks test
function nestedFunction() {
    if (true) {
        for (let i = 0; i < 10; i++) {
            // Deeply nested
            if (i % 2 === 0) {
                console.log(i);
            }
        }
    }
}

// Indentation based blocks (Python-like)
def python_function():
    # Python-style docstring
    \"\"\"
    This is a Python docstring
    with multiple lines
    \"\"\"
    if True:
        print("Nested block")
        if False:
            print("Deeper nesting")
            for i in range(10):
                print(i)
"""

    @pytest.fixture
    def parser(self) -> TestParser:
        """Fixture providing a test parser instance."""
        return TestParser()

    @pytest.fixture
    def python_parser(self) -> TestParser:
        """Fixture providing a Python test parser instance."""
        parser = TestParser("python")
        parser.line_comment = "#"
        parser.block_comment_start = '"""'
        parser.block_comment_end = '"""'
        parser.block_start = ":"
        parser.block_end = None  # Python uses indentation
        return parser

    def test_base_parser_initialization(self):
        """Test initializing the EnhancedBaseParser."""
        parser = EnhancedBaseParser()

        # Check that basic properties are set
        assert parser.language == "generic"
        assert isinstance(parser.patterns, dict)
        assert isinstance(parser, ParserInterface)

        # Check that the parser has capabilities
        capabilities = parser.get_capabilities()
        assert isinstance(capabilities, dict)
        assert "can_extract_docstrings" in capabilities

    def test_parser_validation(self, parser):
        """Test parser validation."""
        # Test parser should be valid since it has a non-generic language
        assert parser.validate() is True

        # Generic parser should not be valid
        generic_parser = EnhancedBaseParser()
        assert generic_parser.validate() is False

    def test_get_capabilities(self, parser):
        """Test getting parser capabilities."""
        capabilities = parser.get_capabilities()

        # Our test parser has all patterns defined
        assert capabilities["can_parse_functions"] is True
        assert capabilities["can_parse_classes"] is True
        assert capabilities["can_parse_imports"] is True
        assert capabilities["can_extract_docstrings"] is True

        # Test with missing patterns
        parser.patterns["function"] = None
        capabilities = parser.get_capabilities()
        assert capabilities["can_parse_functions"] is False

    def test_extract_docstring(self, parser, mixed_code_sample):
        """Test docstring extraction across different styles."""
        lines = mixed_code_sample.splitlines()

        # Test block comment extraction
        block_docstring = parser.extract_docstring(lines, 2, 5)
        assert block_docstring is not None
        assert "Block comment at the top" in block_docstring

        # Test function docstring
        function_docstring = parser.extract_docstring(lines, 10, 13)
        assert function_docstring is not None
        assert "Function docstring" in function_docstring

        # Test class docstring
        class_docstring = parser.extract_docstring(lines, 16, 20)
        assert class_docstring is not None
        assert "Class docstring" in class_docstring
        assert "multiple lines" in class_docstring

    def test_python_docstring_extraction(self, python_parser, mixed_code_sample):
        """Test Python-specific docstring extraction."""
        lines = mixed_code_sample.splitlines()

        # Python parser should find Python triple-quote docstrings
        python_docstring = python_parser.extract_docstring(lines, 44, 50)
        assert python_docstring is not None
        assert "This is a Python docstring" in python_docstring
        assert "multiple lines" in python_docstring

    def test_find_block_end_by_braces(self, parser, mixed_code_sample):
        """Test finding the end of brace-based blocks."""
        lines = mixed_code_sample.splitlines()

        # Find the function line
        function_start = None
        for i, line in enumerate(lines):
            if "function testFunction()" in line:
                function_start = i
                break
        assert function_start is not None, "Test function not found in sample code"

        function_end = parser._find_block_end_by_braces(lines, function_start, "{", "}")
        assert function_end >= function_start, "Block end should be at or after start"

        # Find the nested function line
        nested_function_start = None
        for i, line in enumerate(lines):
            if "function nestedFunction()" in line:
                nested_function_start = i
                break
        assert nested_function_start is not None, "Nested function not found in sample code"

        nested_function_end = parser._find_block_end_by_braces(
            lines, nested_function_start, "{", "}"
        )
        assert nested_function_end >= nested_function_start, "Block end should be at or after start"
        assert nested_function_end < len(lines), "Block end should be within the file"

    def test_find_block_end_by_indent(self, python_parser, mixed_code_sample):
        """Test finding the end of indent-based blocks (Python-style)."""
        lines = mixed_code_sample.splitlines()

        # Find the Python function line
        python_function_start = None
        for i, line in enumerate(lines):
            if "def python_function():" in line:
                python_function_start = i
                break
        assert python_function_start is not None, "Python function not found in sample code"

        python_function_end = python_parser._find_block_end_by_indent(lines, python_function_start)
        assert python_function_end >= python_function_start, "Block end should be at or after start"
        assert python_function_end < len(lines), "Block end should be within the file"

    def test_find_block_end_improved(self, parser, python_parser, mixed_code_sample):
        """Test the improved block end detection that handles both braces and indentation."""
        lines = mixed_code_sample.splitlines()

        # Find the function line
        function_start = None
        for i, line in enumerate(lines):
            if "function testFunction()" in line:
                function_start = i
                break
        assert function_start is not None, "Test function not found in sample code"

        # Test brace-based function with improved method
        function_end = parser._find_block_end_improved(lines, function_start, "{", "}", False)
        assert function_end >= function_start, "Block end should be at or after start"

        # Find Python function line
        python_function_start = None
        for i, line in enumerate(lines):
            if "def python_function():" in line:
                python_function_start = i
                break
        assert python_function_start is not None, "Python function not found in sample code"

        # Test indentation-based function with improved method
        python_function_end = python_parser._find_block_end_improved(
            lines, python_function_start, "{", "}", True
        )
        assert python_function_end >= python_function_start, "Block end should be at or after start"

        # For both blocks, check that the parser correctly determined the end
        assert function_end < len(lines), "Block end should be within the file"
        assert python_function_end < len(lines), "Block end should be within the file"

    def test_parse_basic(self, parser, mixed_code_sample):
        """Test basic parsing functionality."""
        result = parser.parse(mixed_code_sample, "test.txt")

        # Check that we got a valid ParseResult
        assert isinstance(result, ParseResult)

        # Check that functions were found
        assert len(result.declarations) > 0

        # Test function should be found with its docstring
        test_function = next((d for d in result.declarations if d.name == "testFunction"), None)
        assert test_function is not None
        if test_function.docstring:
            assert "Function docstring" in test_function.docstring

        # Check imports
        assert len(result.imports) > 0
        assert "module1" in result.imports
        assert "module2" in result.imports


if __name__ == "__main__":
    pytest.main(["-v", __file__])
