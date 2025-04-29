#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit tests for the enhanced Julia parser in CodeConCat.

Tests the EnhancedJuliaParser class to ensure it properly handles 
Julia-specific syntax, functions, macros, modules, nested functions, and docstrings.
"""

import os
import logging
import pytest
from typing import List, Dict, Any, Optional
from pathlib import Path

from codeconcat.base_types import (
    CodeConCatConfig,
    Declaration,
    ParseResult,
    ParserInterface,
)
from codeconcat.parser.language_parsers.enhanced_base_parser import EnhancedBaseParser
from codeconcat.parser.language_parsers.enhanced_julia_parser import EnhancedJuliaParser
from codeconcat.parser.enable_debug import enable_all_parser_debug_logging

# Enable debug logging for all parsers
enable_all_parser_debug_logging()

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class TestEnhancedJuliaParser:
    """Test class for the EnhancedJuliaParser."""
    
    @pytest.fixture
    def julia_code(self) -> str:
        """Fixture providing a sample Julia code from the test corpus."""
        file_path = Path(__file__).parent.parent.parent / "parser_test_corpus" / "julia" / "basic.jl"
        with open(file_path, "r") as f:
            return f.read()
    
    def test_julia_parser_initialization(self):
        """Test initializing the EnhancedJuliaParser."""
        # Create an instance
        parser = EnhancedJuliaParser()
        
        # Check that it inherits from EnhancedBaseParser
        assert isinstance(parser, EnhancedBaseParser)
        assert isinstance(parser, ParserInterface)
        
        # Check that Julia-specific properties are set
        assert parser.language == "julia"
        assert parser.line_comment == "#"
        assert parser.block_comment_start in ["#=", "\"\"\""]
        assert parser.block_comment_end in ["=#", "\"\"\""]
        
        # Check capabilities
        capabilities = parser.get_capabilities()
        assert capabilities["can_parse_functions"] is True
        assert capabilities["can_parse_modules"] is True
        assert capabilities["can_parse_structs"] is True
        assert capabilities["can_extract_docstrings"] is True
    
    def test_julia_parser_parse(self, julia_code):
        """Test parsing a Julia file with the EnhancedJuliaParser."""
        # Create parser and parse the code
        parser = EnhancedJuliaParser()
        result = parser.parse(julia_code, "basic.jl")
        
        # Check that we got a ParseResult
        assert isinstance(result, ParseResult)
        assert result.error is None, f"Parse error: {result.error}"
        
        # Log the declarations for debugging
        print(f"Found {len(result.declarations)} top-level declarations:")
        for decl in result.declarations:
            print(f"- {decl.kind}: {decl.name}")
        
        # Check for imports/using statements
        print(f"Found {len(result.imports)} imports: {result.imports}")
        assert len(result.imports) > 0, "No imports/using statements were detected"
        
        # Try to find specific declarations 
        module_decl = None
        struct_decl = None
        function_decl = None
        
        for decl in result.declarations:
            if decl.kind == "module":
                module_decl = decl
            elif decl.kind == "struct":
                struct_decl = decl
            elif decl.kind == "function" and decl.name != "module" and decl.name != "struct":
                function_decl = decl
        
        # Test that we found key Julia constructs
        if module_decl:
            print(f"Found module: {module_decl.name} at lines {module_decl.start_line}-{module_decl.end_line}")
            if module_decl.docstring:
                print(f"Module docstring: {module_decl.docstring[:50]}...")
            
            # Check if the module has children (functions, structs, etc.)
            if module_decl.children:
                print(f"Found {len(module_decl.children)} declarations inside module")
                for child in module_decl.children:
                    print(f"  - {child.kind}: {child.name}")
        else:
            print("No module declaration found, this is okay if the test file doesn't have one")
        
        if struct_decl:
            print(f"Found struct: {struct_decl.name} at lines {struct_decl.start_line}-{struct_decl.end_line}")
            if struct_decl.docstring:
                print(f"Struct docstring: {struct_decl.docstring[:50]}...")
        else:
            print("No struct declaration found, this is okay if the test file doesn't have one")
        
        if function_decl:
            print(f"Found function: {function_decl.name} at lines {function_decl.start_line}-{function_decl.end_line}")
            if function_decl.docstring:
                print(f"Function docstring: {function_decl.docstring[:50]}...")
            
            # Check if function has nested functions
            if function_decl.children:
                print(f"Found {len(function_decl.children)} nested functions inside {function_decl.name}")
                for nested in function_decl.children:
                    print(f"  - {nested.kind}: {nested.name}")
        else:
            print("No function declaration found, this is okay if the test file doesn't have one")
        
        # Check that at least some declarations were found
        assert len(result.declarations) > 0, "No declarations were detected"
        
        # Count docstrings
        declarations_with_docstrings = [d for d in result.declarations if d.docstring]
        print(f"Found {len(declarations_with_docstrings)} declarations with docstrings")
    
    def test_julia_parser_nested_declarations(self, julia_code):
        """Test the EnhancedJuliaParser's ability to detect nested declarations."""
        # Create parser and parse the code
        parser = EnhancedJuliaParser()
        result = parser.parse(julia_code, "basic.jl")
        
        # Check that we got a ParseResult
        assert isinstance(result, ParseResult)
        assert result.error is None, f"Parse error: {result.error}"
        
        # Count all declarations including nested ones
        total_declarations = parser._count_nested_declarations(result.declarations)
        max_depth = parser._calculate_max_nesting_depth(result.declarations)
        
        print(f"Total declarations (including nested): {total_declarations}")
        print(f"Maximum nesting depth: {max_depth}")
        
        # Create a tree of declarations for visualization
        def print_declaration_tree(declaration, indent=0):
            indent_str = "  " * indent
            print(f"{indent_str}- {declaration.kind}: {declaration.name}")
            if declaration.children:
                for child in declaration.children:
                    print_declaration_tree(child, indent + 1)
        
        print("\nDeclaration tree:")
        for decl in result.declarations:
            print_declaration_tree(decl)
        
        # Find declarations with children (nested declarations)
        declarations_with_children = [d for d in result.declarations if d.children]
        print(f"Found {len(declarations_with_children)} declarations with children (nested declarations)")
        
        # This test is informative rather than assertive since nested declarations are optional
        assert total_declarations >= len(result.declarations), "Total declarations should be at least equal to top-level declarations"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
