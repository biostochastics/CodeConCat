#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script to validate the enhanced Julia parser's nested function detection.

This script tests the EnhancedJuliaParser on a file with complex nested functions
and prints out the parser results showing all declarations with their nesting.
"""

import os
import sys
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

# Add the project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the enhanced Julia parser directly
from codeconcat.parser.language_parsers.enhanced_julia_parser import EnhancedJuliaParser

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def print_declarations(declarations, indent=0):
    """Print declarations with proper indentation to show nesting."""
    for decl in declarations:
        print(f"{' ' * indent}[{decl.kind}] {decl.name} (lines {decl.start_line}-{decl.end_line})")
        if decl.children:
            print_declarations(decl.children, indent + 4)

def main():
    """Run the test on the nested functions Julia file."""
    parser = EnhancedJuliaParser()
    test_file = project_root / "tests" / "parser_test_corpus" / "julia" / "nested_functions.jl"
    
    with open(test_file, 'r') as f:
        content = f.read()
    
    result = parser.parse(content, str(test_file))
    
    print("\n\n=== JULIA PARSER RESULTS ===")
    print(f"Total top-level declarations: {len(result.declarations)}")
    
    # Count all declarations including nested ones
    total_declarations = parser._count_nested_declarations(result.declarations)
    max_depth = parser._calculate_max_nesting_depth(result.declarations)
    
    print(f"Total declarations (including nested): {total_declarations}")
    print(f"Maximum nesting depth: {max_depth}")
    print(f"Number of imports: {len(result.imports)}")
    print("\nDeclaration tree:")
    print_declarations(result.declarations)
    
    if result.error:
        print(f"\nERROR: {result.error}")
        return 1
    
    # Check if nested functions were found
    nested_functions_found = False
    total_functions = 0
    
    def count_functions(declarations):
        nonlocal total_functions
        for d in declarations:
            if d.kind == "function":
                total_functions += 1
            if d.children:
                count_functions(d.children)
    
    # Count all function declarations
    count_functions(result.declarations)
    
    # The total number of functions should be more than the top-level ones
    if total_functions > len([d for d in result.declarations if d.kind == "function"]):
        nested_functions_found = True
    
    if nested_functions_found:
        print("\nSUCCESS: Nested functions were correctly detected!")
        return 0
    else:
        print("\nERROR: Failed to detect nested functions!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
