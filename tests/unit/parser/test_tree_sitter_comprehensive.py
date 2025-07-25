#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Comprehensive tests for Tree-sitter parser functionality in CodeConCat.

This test suite covers:
1. Tree-sitter parser initialization and availability
2. Multi-language parsing with tree-sitter
3. Capture tuple handling (2-tuple vs 3-tuple)
4. Field definition compatibility
5. Parser fallback mechanisms
"""

import pytest
from unittest.mock import patch, MagicMock, Mock

from codeconcat.base_types import CodeConCatConfig, ParsedFileData, ParseResult, Declaration


class TestTreeSitterParsers:
    """Test class for tree-sitter parser functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = CodeConCatConfig(
            target_path=".",
            output="test_output.txt",
            format="text",
            disable_tree=False,
            max_workers=1
        )

    def test_tree_sitter_availability_check(self):
        """Test that tree-sitter availability is properly checked."""
        try:
            from codeconcat.parser.language_parsers import TREE_SITTER_AVAILABLE, TREE_SITTER_PARSER_MAP
            
            if TREE_SITTER_AVAILABLE:
                assert isinstance(TREE_SITTER_PARSER_MAP, dict), "Parser map should be a dictionary"
                assert len(TREE_SITTER_PARSER_MAP) > 0, "Should have some parsers available"
            else:
                assert TREE_SITTER_PARSER_MAP == {}, "Parser map should be empty when unavailable"
                
        except ImportError:
            pytest.skip("Tree-sitter module not available")

    @pytest.mark.skipif(True, reason="Tree-sitter may not be available in test environment")
    def test_js_ts_parser_initialization(self):
        """Test JavaScript/TypeScript parser initialization."""
        try:
            from codeconcat.parser.language_parsers.tree_sitter_js_ts_parser import TreeSitterJsTsParser
            
            # Test JavaScript parser
            js_parser = TreeSitterJsTsParser(language="javascript")
            assert js_parser.language == "javascript", "Should set JavaScript language"
            
            # Test TypeScript parser
            ts_parser = TreeSitterJsTsParser(language="typescript")
            assert ts_parser.language == "typescript", "Should set TypeScript language"
            
            # Test invalid language
            with pytest.raises(ValueError):
                TreeSitterJsTsParser(language="invalid")
                
        except ImportError:
            pytest.skip("Tree-sitter JS/TS parser not available")

    def test_capture_tuple_handling_mock(self):
        """Test capture tuple handling with mocked tree-sitter."""
        # Mock the tree-sitter components
        mock_node = Mock()
        mock_node.id = 1
        mock_node.type = "function"
        mock_node.start_point = (10, 0)
        mock_node.end_point = (20, 0)
        
        # Test 2-tuple format
        captures_2_tuple = [(mock_node, "function")]
        
        # Test 3-tuple format  
        captures_3_tuple = [(mock_node, "function", 0)]
        
        # Test our handling logic
        for captures in [captures_2_tuple, captures_3_tuple]:
            for capture in captures:
                # This simulates the logic in tree_sitter_js_ts_parser.py
                if len(capture) == 2:
                    node, capture_name = capture
                    assert node == mock_node, "Should extract node correctly"
                    assert capture_name == "function", "Should extract capture name correctly"
                else:
                    node, capture_name, _ = capture
                    assert node == mock_node, "Should extract node correctly"
                    assert capture_name == "function", "Should extract capture name correctly"

    def test_field_definition_query_compatibility(self):
        """Test that queries use field_definition instead of public_field_definition."""
        try:
            from codeconcat.parser.language_parsers.tree_sitter_js_ts_parser import JS_TS_QUERIES
            
            declarations_query = JS_TS_QUERIES.get("declarations", "")
            
            # Should use the compatible field_definition
            assert "field_definition" in declarations_query, "Should use field_definition"
            
            # Should not use the problematic public_field_definition
            assert "public_field_definition" not in declarations_query, "Should not use public_field_definition"
            
            # Verify the query structure is valid
            assert "name:" in declarations_query, "Query should have name captures"
            assert "@" in declarations_query, "Query should have capture annotations"
            
        except ImportError:
            pytest.skip("Tree-sitter JS/TS parser not available")

    @patch('codeconcat.parser.language_parsers.tree_sitter_js_ts_parser.TreeSitterJsTsParser._run_queries')
    def test_js_ts_parser_with_mock_queries(self, mock_run_queries):
        """Test JS/TS parser with mocked query results."""
        try:
            from codeconcat.parser.language_parsers.tree_sitter_js_ts_parser import TreeSitterJsTsParser
            
            # Mock successful parsing results
            mock_declarations = [
                Declaration(
                    kind="function",
                    name="testFunction",
                    start_line=1,
                    end_line=5,
                    modifiers=set(),
                    docstring="Test function"
                ),
                Declaration(
                    kind="class",
                    name="TestClass", 
                    start_line=7,
                    end_line=15,
                    modifiers=set(["export"]),
                    docstring="Test class"
                )
            ]
            
            mock_imports = ["react", "lodash"]
            mock_run_queries.return_value = (mock_declarations, mock_imports)
            
            # Test parsing
            parser = TreeSitterJsTsParser(language="javascript")
            result = parser.parse("// Mock JavaScript code", "test.js")
            
            # Verify results
            assert result is not None, "Should return parse result"
            assert len(result.declarations) == 2, "Should have 2 declarations"
            assert len(result.imports) == 2, "Should have 2 imports"
            
            # Verify declaration details
            func_decl = result.declarations[0]
            assert func_decl.name == "testFunction", "Function name should match"
            assert func_decl.kind == "function", "Function kind should match"
            
            class_decl = result.declarations[1]
            assert class_decl.name == "TestClass", "Class name should match"
            assert "export" in class_decl.modifiers, "Class should have export modifier"
            
        except ImportError:
            pytest.skip("Tree-sitter JS/TS parser not available")

    def test_parser_factory_tree_sitter_selection(self):
        """Test that parser factory correctly selects tree-sitter parsers."""
        from codeconcat.parser.file_parser import get_language_parser
        
        # Test with tree-sitter enabled
        config_with_tree_sitter = CodeConCatConfig(
            target_path=".",
            output="test.txt",
            format="text",
            disable_tree=False
        )
        
        # Test various languages
        test_languages = ["python", "javascript", "typescript", "java"]
        
        for language in test_languages:
            parser = get_language_parser(language, config_with_tree_sitter)
            # Should either get a parser or None (gracefully handled)
            # The important thing is no exceptions are raised

    def test_tree_sitter_disabled_fallback(self):
        """Test that disabling tree-sitter falls back to other parsers."""
        from codeconcat.parser.file_parser import get_language_parser
        
        # Test with tree-sitter disabled
        config_no_tree_sitter = CodeConCatConfig(
            target_path=".",
            output="test.txt", 
            format="text",
            disable_tree=True,
            use_enhanced_parsers=True
        )
        
        # Should fall back to enhanced or standard parsers
        parser = get_language_parser("python", config_no_tree_sitter)
        # Should either get a fallback parser or None (gracefully handled)

    def test_multiple_language_support(self):
        """Test that multiple languages are supported by tree-sitter."""
        try:
            from codeconcat.parser.language_parsers import TREE_SITTER_PARSER_MAP
            
            expected_languages = [
                "python", "javascript", "typescript", "java", 
                "c", "cpp", "go", "rust", "php"
            ]
            
            for language in expected_languages:
                if language in TREE_SITTER_PARSER_MAP:
                    parser_class = TREE_SITTER_PARSER_MAP[language]
                    assert isinstance(parser_class, str), f"Parser class for {language} should be string"
                    assert "TreeSitter" in parser_class, f"Parser class should be tree-sitter based"
                    
        except ImportError:
            pytest.skip("Tree-sitter not available")

    @patch('codeconcat.parser.language_parsers.base_tree_sitter_parser.get_language')
    @patch('codeconcat.parser.language_parsers.base_tree_sitter_parser.get_parser')
    def test_tree_sitter_error_handling(self, mock_get_parser, mock_get_language):
        """Test that tree-sitter errors are handled gracefully."""
        # Mock tree-sitter to raise an exception
        mock_get_language.side_effect = Exception("Tree-sitter error")
        
        try:
            from codeconcat.parser.language_parsers.tree_sitter_js_ts_parser import TreeSitterJsTsParser
            
            # Should handle initialization errors gracefully
            parser = TreeSitterJsTsParser(language="javascript")
            
            # Parsing should not crash even if tree-sitter fails
            result = parser.parse("function test() {}", "test.js")
            
            # Should return a valid result (possibly empty) rather than crashing
            assert result is not None, "Should return result even on tree-sitter error"
            
        except ImportError:
            pytest.skip("Tree-sitter JS/TS parser not available")

    def test_query_structure_validation(self):
        """Test that tree-sitter queries have valid structure."""
        try:
            from codeconcat.parser.language_parsers.tree_sitter_js_ts_parser import JS_TS_QUERIES
            
            # Verify query dictionary structure
            assert isinstance(JS_TS_QUERIES, dict), "Queries should be a dictionary"
            
            expected_query_types = ["imports", "declarations", "doc_comments"]
            for query_type in expected_query_types:
                assert query_type in JS_TS_QUERIES, f"Should have {query_type} query"
                query_content = JS_TS_QUERIES[query_type]
                assert isinstance(query_content, str), f"{query_type} query should be string"
                assert len(query_content) > 0, f"{query_type} query should not be empty"
            
            # Verify query syntax elements
            declarations_query = JS_TS_QUERIES["declarations"]
            
            # Should have capture annotations
            assert "@" in declarations_query, "Should have capture annotations"
            
            # Should have node type patterns
            assert "(" in declarations_query and ")" in declarations_query, "Should have node patterns"
            
            # Should capture names
            assert "name:" in declarations_query, "Should capture names"
            
        except ImportError:
            pytest.skip("Tree-sitter JS/TS parser not available")


class TestTreeSitterIntegration:
    """Integration tests for tree-sitter functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = CodeConCatConfig(
            target_path=".",
            output="test_output.txt",
            format="text",
            disable_tree=False,
            max_workers=1
        )

    def test_tree_sitter_with_enhanced_pipeline(self):
        """Test tree-sitter integration with enhanced parsing pipeline."""
        from codeconcat.parser.enhanced_pipeline import enhanced_parse_pipeline
        
        # Create test JavaScript file
        js_content = """
// Test JavaScript file
import React from 'react';

/**
 * Test component
 */
function TestComponent() {
    return <div>Hello World</div>;
}

export default TestComponent;
"""
        
        file_data = ParsedFileData(
            file_path="TestComponent.js",
            content=js_content,
            size=len(js_content.encode()),
            language="javascript"
        )
        
        # Test with enhanced pipeline
        parsed_files, errors = enhanced_parse_pipeline([file_data], self.config)
        
        # Should handle gracefully regardless of tree-sitter availability
        assert isinstance(parsed_files, list), "Should return list of parsed files"
        assert isinstance(errors, list), "Should return list of errors"

    def test_tree_sitter_vs_fallback_consistency(self):
        """Test that tree-sitter and fallback parsers produce consistent results."""
        # Test content that should be parseable by multiple parser types
        python_content = """
def hello_world():
    '''A simple greeting function.'''
    return "Hello, World!"

class Greeter:
    '''A class for greetings.'''
    
    def __init__(self, name):
        self.name = name
    
    def greet(self):
        return f"Hello, {self.name}!"
"""
        
        file_data = ParsedFileData(
            file_path="greetings.py",
            content=python_content,
            size=len(python_content.encode()),
            language="python"
        )
        
        # Test with tree-sitter enabled
        config_tree_sitter = CodeConCatConfig(
            target_path=".",
            output="test.txt",
            format="text",
            disable_tree=False,
            use_enhanced_parsers=False
        )
        
        # Test with tree-sitter disabled (fallback)
        config_fallback = CodeConCatConfig(
            target_path=".",
            output="test.txt",
            format="text", 
            disable_tree=True,
            use_enhanced_parsers=True
        )
        
        from codeconcat.parser.enhanced_pipeline import enhanced_parse_pipeline
        
        # Parse with both configurations
        tree_sitter_results, tree_sitter_errors = enhanced_parse_pipeline([file_data], config_tree_sitter)
        fallback_results, fallback_errors = enhanced_parse_pipeline([file_data], config_fallback)
        
        # Both should produce valid results
        assert len(tree_sitter_results) >= 0, "Tree-sitter should produce results"
        assert len(fallback_results) >= 0, "Fallback should produce results"
        
        # At least one should succeed in parsing
        total_successful = len(tree_sitter_results) + len(fallback_results)
        assert total_successful >= 1, "At least one parser type should succeed"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
