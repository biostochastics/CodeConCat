#!/usr/bin/env python3

"""
Parser Performance and Enhancement Testing Script

This script performs direct comparisons between basic and enhanced parsers
to validate enhancements in nested declaration handling, parent-child relationships,
and overall parsing quality.
"""

import logging
import sys
import time
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from codeconcat.base_types import Declaration  # noqa: E402
from codeconcat.parser.language_parsers.enhanced_js_ts_parser import (  # noqa: E402
    EnhancedJSTypeScriptParser,
)
from codeconcat.parser.language_parsers.enhanced_julia_parser import (  # noqa: E402
    EnhancedJuliaParser,
)
from codeconcat.parser.language_parsers.enhanced_python_parser import (  # noqa: E402
    EnhancedPythonParser,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Sample code for testing
PYTHON_SAMPLE = '''"""
Module level docstring.
"""
import os
import sys
from typing import List, Dict

class TestClass:
    """Test class docstring."""

    def __init__(self, value):
        """Constructor."""
        self.value = value

    def method_with_nested(self):
        """Method with nested function."""
        def nested_function():
            """Nested function docstring."""
            return self.value * 2

        return nested_function()

def top_level_function():
    """Top-level function docstring."""

    class NestedClass:
        """Nested class docstring."""
        def nested_method(self):
            """Nested method docstring."""
            return "nested result"

    return NestedClass().nested_method()
'''

JS_SAMPLE = """/**
 * Module level comment
 */
import { useState } from 'react';

class TestClass {
    /**
     * Constructor comment
     */
    constructor(value) {
        this.value = value;
    }

    /**
     * Method with nested function
     */
    methodWithNested() {
        /**
         * Nested function comment
         */
        function nestedFunction() {
            return this.value * 2;
        }

        return nestedFunction.call(this);
    }
}

/**
 * Top-level function
 */
function topLevelFunction() {
    /**
     * Nested class
     */
    class NestedClass {
        nestedMethod() {
            return "nested result";
        }
    }

    return new NestedClass().nestedMethod();
}
"""

JULIA_SAMPLE = '''"""
Module level docstring.
"""
module TestModule

using Test

struct TestStruct
    name::String
    value::Int
end

"""
Function with nested function.
"""
function outer_function(param)
    """
    Nested function docstring.
    """
    function inner_function(x)
        return x * 2
    end

    return inner_function(param)
end

"""
Nested module.
"""
module NestedModule
    """
    Function in nested module.
    """
    function nested_function()
        return "nested result"
    end
end

end # module TestModule
'''


def print_declaration_tree(declarations: list[Declaration], indent: int = 0):
    """Print a tree of declarations with proper indentation to show hierarchy."""
    for decl in declarations:
        print(
            f"{'  ' * indent}|- {decl.kind}: {decl.name} (lines {decl.start_line}-{decl.end_line})"
        )
        if decl.children:
            print_declaration_tree(decl.children, indent + 1)


def count_declarations(declarations: list[Declaration]) -> int:
    """Count total declarations including nested ones."""
    total = len(declarations)
    for decl in declarations:
        total += count_declarations(decl.children)
    return total


def measure_nesting_depth(declarations: list[Declaration], current_depth: int = 0) -> int:
    """Calculate the maximum nesting depth of declarations."""
    if not declarations:
        return current_depth

    depths = [current_depth]
    for decl in declarations:
        depths.append(measure_nesting_depth(decl.children, current_depth + 1))

    return max(depths)


def test_python_parser():
    """Test the Python parser with the sample code."""
    print("\n===== PYTHON PARSER TEST =====")

    parser = EnhancedPythonParser()

    start_time = time.time()
    result = parser.parse(PYTHON_SAMPLE, "test.py")
    parse_time = (time.time() - start_time) * 1000

    print(f"Parse time: {parse_time:.2f} ms")
    print(f"Total declarations: {count_declarations(result.declarations)}")
    print(f"Maximum nesting depth: {measure_nesting_depth(result.declarations)}")
    print(f"Imports detected: {len(result.imports)}")
    print("\nDeclaration Tree:")
    print_declaration_tree(result.declarations)

    # Validate enhanced features
    # 1. Check for nested function detection
    nested_found = False
    for decl in result.declarations:
        if decl.kind == "class" and decl.name == "TestClass":
            for method in decl.children:
                if (
                    method.name == "method_with_nested"
                    and method.children
                    and method.children[0].name == "nested_function"
                ):
                    nested_found = True
                    break

    if nested_found:
        print("\n✅ Enhanced parser correctly found nested function!")
    else:
        print("\n❌ Enhanced parser failed to find nested function!")

    # 2. Check for nested class detection
    nested_class_found = False
    for decl in result.declarations:
        if (
            decl.kind == "function"
            and decl.name == "top_level_function"
            and decl.children
            and decl.children[0].name == "NestedClass"
        ):
            nested_class_found = True
            break

    if nested_class_found:
        print("✅ Enhanced parser correctly found nested class!")
    else:
        print("❌ Enhanced parser failed to find nested class!")


def test_javascript_parser():
    """Test the JavaScript parser with the sample code."""
    print("\n===== JAVASCRIPT PARSER TEST =====")

    parser = EnhancedJSTypeScriptParser()

    start_time = time.time()
    result = parser.parse(JS_SAMPLE, "test.js")
    parse_time = (time.time() - start_time) * 1000

    print(f"Parse time: {parse_time:.2f} ms")
    print(f"Total declarations: {count_declarations(result.declarations)}")
    print(f"Maximum nesting depth: {measure_nesting_depth(result.declarations)}")
    print(f"Imports detected: {len(result.imports)}")
    print("\nDeclaration Tree:")
    print_declaration_tree(result.declarations)

    # Validate enhanced features
    # 1. Check for nested function detection
    nested_found = False
    for decl in result.declarations:
        if decl.kind == "class" and decl.name == "TestClass":
            for method in decl.children:
                if (
                    method.name == "methodWithNested"
                    and method.children
                    and method.children[0].name == "nestedFunction"
                ):
                    nested_found = True
                    break

    if nested_found:
        print("\n✅ Enhanced parser correctly found nested function!")
    else:
        print("\n❌ Enhanced parser failed to find nested function!")

    # 2. Check for nested class detection
    nested_class_found = False
    for decl in result.declarations:
        if (
            decl.kind == "function"
            and decl.name == "topLevelFunction"
            and decl.children
            and decl.children[0].name == "NestedClass"
        ):
            nested_class_found = True
            break

    if nested_class_found:
        print("✅ Enhanced parser correctly found nested class!")
    else:
        print("❌ Enhanced parser failed to find nested class!")


def test_julia_parser():
    """Test the Julia parser with the sample code."""
    print("\n===== JULIA PARSER TEST =====")

    parser = EnhancedJuliaParser()

    start_time = time.time()
    result = parser.parse(JULIA_SAMPLE, "test.jl")
    parse_time = (time.time() - start_time) * 1000

    print(f"Parse time: {parse_time:.2f} ms")
    print(f"Total declarations: {count_declarations(result.declarations)}")
    print(f"Maximum nesting depth: {measure_nesting_depth(result.declarations)}")
    print(f"Imports detected: {len(result.imports)}")
    print("\nDeclaration Tree:")
    print_declaration_tree(result.declarations)

    # Validate enhanced features
    # 1. Check for nested function detection
    nested_found = False
    for decl in result.declarations:
        if decl.kind == "module" and decl.name == "TestModule":
            for func in decl.children:
                if (
                    func.kind == "function"
                    and func.name == "outer_function"
                    and func.children
                    and func.children[0].name == "inner_function"
                ):
                    nested_found = True
                    break

    if nested_found:
        print("\n✅ Enhanced parser correctly found nested function!")
    else:
        print("\n❌ Enhanced parser failed to find nested function!")

    # 2. Check for nested module detection
    nested_module_found = False
    for decl in result.declarations:
        if decl.kind == "module" and decl.name == "TestModule":
            for child in decl.children:
                if child.kind == "module" and child.name == "NestedModule":
                    nested_module_found = True
                    break

    if nested_module_found:
        print("✅ Enhanced parser correctly found nested module!")
    else:
        print("❌ Enhanced parser failed to find nested module!")


def main():
    """Run all parser tests."""
    test_python_parser()
    test_javascript_parser()
    test_julia_parser()


if __name__ == "__main__":
    main()
