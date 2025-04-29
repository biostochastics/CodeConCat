#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script to validate the enhanced Rust parser's nested declaration detection.

This script tests the EnhancedRustParser on a file with complex nested declarations
and prints out the parser results showing all declarations with their nesting.
"""

import os
import sys
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

# Add the project root to sys.path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the enhanced Rust parser directly
from codeconcat.parser.language_parsers.enhanced_rust_parser import EnhancedRustParser

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
    """Run the test on the nested structures Rust file."""
    parser = EnhancedRustParser()
    test_file = project_root / "tests" / "parser_test_corpus" / "rust" / "nested_structures.rs"
    
    with open(test_file, 'r') as f:
        content = f.read()
    
    result = parser.parse(content, str(test_file))
    
    print("\n\n=== RUST PARSER RESULTS ===")
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
    
    # Check if nested functions were found in at least one struct method
    nested_functions_found = False
    
    def check_for_nested_functions(declarations):
        nonlocal nested_functions_found
        for decl in declarations:
            if decl.kind in ("struct", "impl"):
                for child in decl.children:
                    if child.kind == "function" and child.children:
                        for grandchild in child.children:
                            if grandchild.kind == "function":
                                nested_functions_found = True
                                return
            if decl.children:
                check_for_nested_functions(decl.children)
    
    check_for_nested_functions(result.declarations)
    
    if nested_functions_found:
        print("\nSUCCESS: Nested functions were correctly detected!")
        return 0
    else:
        print("\nERROR: Failed to detect nested functions!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
