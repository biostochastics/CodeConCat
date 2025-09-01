#!/usr/bin/env python3

"""
Unit tests for the annotator module.

Tests the functionality of the annotator to transform parsed data into annotated data.
"""

import pytest

from codeconcat.base_types import AnnotatedFileData, CodeConCatConfig, Declaration, ParsedFileData
from codeconcat.transformer.annotator import annotate


class TestAnnotator:
    """Test class for the annotator module."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = CodeConCatConfig(
            target_path="/test/path",
            include_paths=["**/*.py"],
            exclude_paths=["venv"],
            disable_symbols=False,
        )

    def test_annotate_with_functions(self):
        """Test annotating data with functions."""
        # Create parsed file data with functions
        declarations = [
            Declaration(name="func1", kind="function", start_line=1, end_line=2),
            Declaration(name="func2", kind="function", start_line=4, end_line=5),
        ]

        parsed_data = ParsedFileData(
            file_path="test.py",
            language="python",
            content="def func1():\n    pass\n\ndef func2(x):\n    return x * 2",
            declarations=declarations,
            imports=[],
            token_stats={},
            security_issues=[],
        )

        # Call the annotate function
        result = annotate(parsed_data, self.config)

        # Check the result
        assert isinstance(result, AnnotatedFileData)
        assert result.file_path == "test.py"
        assert result.language == "python"
        assert "## File: test.py" in result.annotated_content
        assert "### Functions" in result.annotated_content
        assert "- func1" in result.annotated_content
        assert "- func2" in result.annotated_content
        assert "```python" in result.annotated_content
        assert "Contains 2 functions" in result.summary
        assert "has_functions" in result.tags
        assert "python" in result.tags

    def test_annotate_with_classes(self):
        """Test annotating data with classes."""
        # Create parsed file data with classes
        declarations = [Declaration(name="TestClass", kind="class", start_line=1, end_line=3)]

        parsed_data = ParsedFileData(
            file_path="class_test.py",
            language="python",
            content="class TestClass:\n    def method(self):\n        pass",
            declarations=declarations,
            imports=[],
            token_stats={},
            security_issues=[],
        )

        # Call the annotate function
        result = annotate(parsed_data, self.config)

        # Check the result
        assert "### Classes" in result.annotated_content
        assert "- TestClass" in result.annotated_content
        assert "Contains 1 classes" in result.summary
        assert "has_classes" in result.tags

    def test_annotate_with_structs(self):
        """Test annotating data with structs."""
        # Create parsed file data with structs
        declarations = [Declaration(name="Point", kind="struct", start_line=1, end_line=4)]

        parsed_data = ParsedFileData(
            file_path="structs.c",
            language="c",
            content="struct Point {\n    int x;\n    int y;\n};",
            declarations=declarations,
            imports=[],
            token_stats={},
            security_issues=[],
        )

        # Call the annotate function
        result = annotate(parsed_data, self.config)

        # Check the result
        assert "### Structs" in result.annotated_content
        assert "- Point" in result.annotated_content
        assert "Contains 1 structs" in result.summary
        assert "has_structs" in result.tags

    def test_annotate_with_symbols(self):
        """Test annotating data with symbols."""
        # Create parsed file data with symbols
        declarations = [
            Declaration(name="MAX_VALUE", kind="symbol", start_line=1, end_line=1),
            Declaration(name="MIN_VALUE", kind="symbol", start_line=2, end_line=2),
        ]

        parsed_data = ParsedFileData(
            file_path="constants.js",
            language="javascript",
            content="const MAX_VALUE = 100;\nconst MIN_VALUE = 0;",
            declarations=declarations,
            imports=[],
            token_stats={},
            security_issues=[],
        )

        # Call the annotate function
        result = annotate(parsed_data, self.config)

        # Check the result
        assert "### Symbols" in result.annotated_content
        assert "- MAX_VALUE" in result.annotated_content
        assert "- MIN_VALUE" in result.annotated_content
        assert "Contains 2 symbols" in result.summary
        assert "has_symbols" in result.tags

    def test_annotate_with_disabled_symbols(self):
        """Test annotating with symbols disabled."""
        # Configure to disable symbols
        config_with_disabled_symbols = CodeConCatConfig(
            target_path="/test/path", disable_symbols=True
        )

        # Create parsed file data with symbols
        declarations = [Declaration(name="MAX_VALUE", kind="symbol", start_line=1, end_line=1)]

        parsed_data = ParsedFileData(
            file_path="constants.js",
            language="javascript",
            content="const MAX_VALUE = 100;",
            declarations=declarations,
            imports=[],
            token_stats={},
            security_issues=[],
        )

        # Call the annotate function
        result = annotate(parsed_data, config_with_disabled_symbols)

        # Check the result - should not include symbols
        assert "### Symbols" not in result.annotated_content
        assert "- MAX_VALUE" not in result.annotated_content
        assert "No declarations found" in result.summary
        assert "has_symbols" not in result.tags

    def test_annotate_with_mixed_declarations(self):
        """Test annotating with a mix of declaration types."""
        # Create parsed file data with mixed declarations
        declarations = [
            Declaration(name="User", kind="class", start_line=1, end_line=1),
            Declaration(name="createUser", kind="function", start_line=2, end_line=2),
            Declaration(name="DEFAULT_USER", kind="symbol", start_line=3, end_line=3),
        ]

        parsed_data = ParsedFileData(
            file_path="user.js",
            language="javascript",
            content="class User {};\nfunction createUser() {}\nconst DEFAULT_USER = 'guest';",
            declarations=declarations,
            imports=[],
            token_stats={},
            security_issues=[],
        )

        # Call the annotate function
        result = annotate(parsed_data, self.config)

        # Check the result
        assert "### Classes" in result.annotated_content
        assert "### Functions" in result.annotated_content
        assert "### Symbols" in result.annotated_content
        assert "Contains 1 functions, 1 classes, 1 symbols" in result.summary
        assert "has_functions" in result.tags
        assert "has_classes" in result.tags
        assert "has_symbols" in result.tags

    def test_annotate_no_declarations(self):
        """Test annotating a file with no declarations."""
        # Create parsed file data with no declarations
        parsed_data = ParsedFileData(
            file_path="empty.py",
            language="python",
            content="# Just a comment\n",
            declarations=[],
            imports=[],
            token_stats={},
            security_issues=[],
        )

        # Call the annotate function
        result = annotate(parsed_data, self.config)

        # Check the result
        assert "## File: empty.py" in result.annotated_content
        assert "No declarations found" in result.summary
        assert "python" in result.tags  # Should still tag the language


if __name__ == "__main__":
    pytest.main(["-v", __file__])
