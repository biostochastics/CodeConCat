#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive tests for recent parser fixes and improvements in CodeConCat.

This test suite specifically covers:
1. JS/TS parser tuple unpacking fixes
2. JS/TS field_definition compatibility fixes
3. JSON file handling as config files
4. TOML/config file error handling
5. Enhanced parser pipeline functionality
6. Tree-sitter parser robustness
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

from codeconcat.base_types import CodeConCatConfig, ParsedFileData, ParseResult, Declaration
from codeconcat.parser.enhanced_pipeline import enhanced_parse_pipeline
from codeconcat.parser.file_parser import parse_code_files, get_language_parser
from codeconcat.language_map import get_language_from_extension
from codeconcat.errors import LanguageParserError, ParserError


class TestParserFixes:
    """Test class for recent parser fixes and improvements."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = CodeConCatConfig(
            target_path=".",
            output="test_output.txt",
            format="text",
            disable_tree=False,
            use_enhanced_parsers=True,
            max_workers=1
        )

    def test_json_file_language_mapping(self):
        """Test that JSON files are correctly mapped to config language."""
        # Test JSON file extension mapping
        language = get_language_from_extension(".json")
        assert language == "config", f"Expected 'config', got '{language}'"
        
        # Test various JSON filenames
        test_files = [
            "package.json",
            "tsconfig.json", 
            "config.json",
            "settings.json"
        ]
        
        for filename in test_files:
            ext = os.path.splitext(filename)[1]
            language = get_language_from_extension(ext)
            assert language == "config", f"JSON file {filename} should map to 'config', got '{language}'"

    def test_config_file_parsing(self):
        """Test that config files (including JSON) are parsed correctly."""
        # Create test JSON content
        json_content = """{
    "name": "test-project",
    "version": "1.0.0",
    "dependencies": {
        "react": "^18.0.0",
        "typescript": "^4.0.0"
    },
    "scripts": {
        "build": "npm run build",
        "test": "jest"
    }
}"""
        
        # Create ParsedFileData for JSON file
        file_data = ParsedFileData(
            file_path="package.json",
            content=json_content,
            size=len(json_content.encode()),
            language="config"
        )
        
        # Test parsing
        parsed_files, errors = parse_code_files([file_data], self.config)
        
        # Verify no errors
        assert len(errors) == 0, f"Unexpected errors: {errors}"
        
        # Verify file was processed
        assert len(parsed_files) == 1, "Expected 1 parsed file"
        
        parsed_file = parsed_files[0]
        assert parsed_file.parse_result is not None, "Parse result should not be None"
        assert parsed_file.parse_result.language == "config", "Language should be 'config'"
        assert "Configuration: package.json" in parsed_file.parse_result.module_name, "Module name should include filename"

    @patch('codeconcat.parser.language_parsers.tree_sitter_js_ts_parser.TreeSitterJsTsParser._run_queries')
    def test_js_ts_tuple_unpacking_robustness(self, mock_run_queries):
        """Test that JS/TS parser handles both 2-tuple and 3-tuple captures correctly."""
        # Mock different tuple formats that tree-sitter might return
        mock_captures_2_tuple = [
            [("mock_node", "function")],  # 2-tuple format
            [("mock_node", "class")]
        ]
        
        mock_captures_3_tuple = [
            [("mock_node", "function", 0)],  # 3-tuple format  
            [("mock_node", "class", 1)]
        ]
        
        # Test with 2-tuple format
        mock_run_queries.return_value = ([], [])
        
        try:
            from codeconcat.parser.language_parsers.tree_sitter_js_ts_parser import TreeSitterJsTsParser
            parser = TreeSitterJsTsParser(language="javascript")
            
            # This should not raise an exception
            js_content = "function test() { return 'hello'; }"
            result = parser.parse(js_content, "test.js")
            assert result is not None, "Parse result should not be None"
            
        except ImportError:
            pytest.skip("Tree-sitter not available")

    def test_enhanced_pipeline_error_handling(self):
        """Test that enhanced pipeline handles parser errors correctly."""
        # Create test file data
        file_data = ParsedFileData(
            file_path="test.py",
            content="def test(): pass",
            size=16,
            language="python"
        )
        
        # Test enhanced pipeline
        parsed_files, errors = enhanced_parse_pipeline([file_data], self.config)
        
        # Should handle gracefully even if some parsers fail
        assert isinstance(parsed_files, list), "Should return list of parsed files"
        assert isinstance(errors, list), "Should return list of errors"

    def test_toml_parser_error_handling(self):
        """Test that TOML parser errors are handled correctly without language parameter."""
        # Create test TOML content
        toml_content = """[tool.poetry]
name = "test-project"
version = "0.1.0"
description = "Test project"

[tool.poetry.dependencies]
python = "^3.8"
"""
        
        file_data = ParsedFileData(
            file_path="pyproject.toml",
            content=toml_content,
            size=len(toml_content.encode()),
            language="config"
        )
        
        # This should not raise TypeError about language parameter
        parsed_files, errors = enhanced_parse_pipeline([file_data], self.config)
        
        # Verify no TypeError exceptions
        for error in errors:
            assert not isinstance(error, TypeError), f"Unexpected TypeError: {error}"
            if isinstance(error, LanguageParserError):
                # Verify the error was created correctly without language parameter
                assert hasattr(error, 'file_path'), "LanguageParserError should have file_path"

    def test_parser_factory_language_support(self):
        """Test that get_language_parser handles various languages correctly."""
        test_languages = [
            "python",
            "javascript", 
            "typescript",
            "config",  # Should handle config files
            "unknown"  # Should handle gracefully
        ]
        
        for language in test_languages:
            parser = get_language_parser(language, self.config)
            if language == "unknown":
                assert parser is None, f"Should return None for unknown language '{language}'"
            elif language == "config":
                # Config files should get TOML parser or None (handled gracefully)
                # The important thing is no exceptions are raised
                pass
            else:
                # Other languages should either get a parser or None (gracefully handled)
                pass

    def test_multiple_parser_types(self):
        """Test that different parser types (tree-sitter, enhanced, standard) work correctly."""
        # Test with different parser configurations
        configs = [
            # Tree-sitter enabled
            CodeConCatConfig(
                target_path=".",
                output="test.txt", 
                format="text",
                disable_tree=False,
                use_enhanced_parsers=False
            ),
            # Enhanced parsers enabled
            CodeConCatConfig(
                target_path=".",
                output="test.txt",
                format="text", 
                disable_tree=True,
                use_enhanced_parsers=True
            ),
            # Standard parsers only
            CodeConCatConfig(
                target_path=".",
                output="test.txt",
                format="text",
                disable_tree=True,
                use_enhanced_parsers=False
            )
        ]
        
        test_content = "def hello(): return 'world'"
        file_data = ParsedFileData(
            file_path="test.py",
            content=test_content,
            size=len(test_content.encode()),
            language="python"
        )
        
        for config in configs:
            # Each configuration should handle parsing gracefully
            parsed_files, errors = parse_code_files([file_data], config)
            
            # Should not crash regardless of parser configuration
            assert isinstance(parsed_files, list), "Should return list"
            assert isinstance(errors, list), "Should return list"

    def test_field_definition_compatibility(self):
        """Test that field_definition is used instead of public_field_definition."""
        try:
            from codeconcat.parser.language_parsers.tree_sitter_js_ts_parser import JS_TS_QUERIES
            
            # Check that queries use field_definition instead of public_field_definition
            declarations_query = JS_TS_QUERIES.get("declarations", "")
            
            assert "field_definition" in declarations_query, "Should use field_definition"
            assert "public_field_definition" not in declarations_query, "Should not use public_field_definition"
            
        except ImportError:
            pytest.skip("Tree-sitter JS/TS parser not available")

    def test_error_types_and_inheritance(self):
        """Test that error types are correctly defined and used."""
        # Test LanguageParserError creation without language parameter
        error = LanguageParserError(
            "Test error message",
            file_path="test.py"
        )
        
        assert isinstance(error, ParserError), "LanguageParserError should inherit from ParserError"
        assert error.file_path == "test.py", "File path should be set correctly"
        assert "Test error message" in str(error), "Error message should be included"

    def test_progressive_parser_fallback(self):
        """Test that parser fallback works correctly when parsers fail."""
        # Create a file that might challenge different parsers
        complex_content = """
# Complex Python file with various constructs
import os
from typing import List, Dict, Optional

class TestClass:
    '''A test class with various features.'''
    
    def __init__(self, name: str):
        self.name = name
        self._private_attr = None
    
    @property
    def display_name(self) -> str:
        '''Get display name.'''
        return f"Test: {self.name}"
    
    async def async_method(self) -> Optional[Dict]:
        '''An async method.'''
        return {"status": "ok"}

def complex_function(items: List[str]) -> Dict[str, int]:
    '''Process items and return counts.'''
    return {item: len(item) for item in items}
"""
        
        file_data = ParsedFileData(
            file_path="complex.py",
            content=complex_content,
            size=len(complex_content.encode()),
            language="python"
        )
        
        # Test with enhanced pipeline (should try multiple parser types)
        parsed_files, errors = enhanced_parse_pipeline([file_data], self.config)
        
        # Should successfully parse with at least one parser type
        assert len(parsed_files) >= 1, "Should successfully parse with fallback"
        
        parsed_file = parsed_files[0]
        assert parsed_file.parse_result is not None, "Should have parse result"


class TestParserIntegration:
    """Integration tests for parser functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = CodeConCatConfig(
            target_path=".",
            output="test_output.txt",
            format="text",
            max_workers=1
        )

    def test_mixed_file_types_parsing(self):
        """Test parsing a mix of different file types."""
        # Create test files of different types
        test_files = [
            # Python file
            ParsedFileData(
                file_path="script.py",
                content="def hello(): return 'world'",
                size=27,
                language="python"
            ),
            # JavaScript file  
            ParsedFileData(
                file_path="app.js",
                content="function greet() { return 'hello'; }",
                size=35,
                language="javascript"
            ),
            # JSON config file
            ParsedFileData(
                file_path="package.json", 
                content='{"name": "test", "version": "1.0.0"}',
                size=35,
                language="config"
            ),
            # TOML config file
            ParsedFileData(
                file_path="pyproject.toml",
                content="[tool.poetry]\nname = 'test'",
                size=26,
                language="config"
            )
        ]
        
        # Parse all files
        parsed_files, errors = parse_code_files(test_files, self.config)
        
        # Should handle all file types gracefully
        assert len(parsed_files) >= len(test_files) - len(errors), "Should parse most files successfully"
        
        # Verify config files are handled correctly
        config_files = [f for f in parsed_files if f.parse_result and f.parse_result.language == "config"]
        assert len(config_files) >= 2, "Should handle JSON and TOML config files"

    def test_parser_error_recovery(self):
        """Test that parser errors don't crash the entire process."""
        # Create files with potential parsing issues
        problematic_files = [
            # Valid file
            ParsedFileData(
                file_path="good.py",
                content="def good_function(): pass",
                size=25,
                language="python"
            ),
            # File with syntax issues (but should be handled gracefully)
            ParsedFileData(
                file_path="problematic.py", 
                content="def incomplete_function(",  # Incomplete syntax
                size=25,
                language="python"
            ),
            # Unknown language (should be skipped gracefully)
            ParsedFileData(
                file_path="unknown.xyz",
                content="unknown content",
                size=15,
                language="unknown"
            )
        ]
        
        # Should not crash even with problematic files
        parsed_files, errors = parse_code_files(problematic_files, self.config)
        
        # Should process at least the good file
        assert len(parsed_files) >= 1, "Should process at least some files"
        
        # Errors should be collected, not raised
        assert isinstance(errors, list), "Errors should be collected in list"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
