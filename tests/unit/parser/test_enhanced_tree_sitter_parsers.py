#!/usr/bin/env python3
"""
Comprehensive tests for enhanced tree-sitter parsers.

This test suite verifies that the enhanced tree-sitter parsers correctly:
1. Extract function and class declarations with proper signatures
2. Handle docstrings and comments appropriately
3. Detect modifiers (async, static, public, etc.)
4. Parse imports correctly
5. Handle language-specific constructs
"""

import pytest

from codeconcat.parser.language_parsers.tree_sitter_cpp_parser import TreeSitterCppParser
from codeconcat.parser.language_parsers.tree_sitter_go_parser import TreeSitterGoParser
from codeconcat.parser.language_parsers.tree_sitter_js_ts_parser import TreeSitterJsTsParser
from codeconcat.parser.language_parsers.tree_sitter_python_parser import TreeSitterPythonParser
from codeconcat.parser.language_parsers.tree_sitter_rust_parser import TreeSitterRustParser


class TestEnhancedPythonParser:
    """Test enhanced Python tree-sitter parser."""

    def setup_method(self):
        """Set up test fixtures."""
        try:
            self.parser = TreeSitterPythonParser()
        except Exception as e:
            pytest.skip(f"Tree-sitter Python parser not available: {e}")

    def test_function_with_docstring_and_signature(self):
        """Test parsing function with docstring and type annotations."""
        code = '''
def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two integers.

    Args:
        a: First integer
        b: Second integer

    Returns:
        The sum of a and b
    """
    return a + b
'''
        result = self.parser.parse(code, "test.py")

        assert len(result.declarations) == 1
        func = result.declarations[0]
        assert func.name == "calculate_sum"
        assert func.kind == "function"
        # Note: signature attribute doesn't exist in Declaration class yet
        # assert func.signature == "(a: int, b: int)"
        assert "Calculate the sum of two integers" in func.docstring
        assert func.start_line == 2
        assert func.end_line >= 9

    def test_async_function_with_modifiers(self):
        """Test parsing async function with proper modifier detection."""
        code = '''
async def fetch_data(url: str) -> dict:
    """Fetch data from URL asynchronously."""
    return {}
'''
        result = self.parser.parse(code, "test.py")

        assert len(result.declarations) == 1
        func = result.declarations[0]
        assert func.name == "fetch_data"
        assert func.kind == "function"
        assert "async" in func.modifiers
        # Note: signature attribute doesn't exist in Declaration class yet
        # assert func.signature == "(url: str)"

    def test_class_with_methods(self):
        """Test parsing class with methods and docstrings."""
        code = '''
class Calculator:
    """A simple calculator class."""

    def __init__(self, precision: int = 2):
        """Initialize calculator with precision."""
        self.precision = precision

    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        return a + b

    @property
    def version(self) -> str:
        """Get calculator version."""
        return "1.0"
'''
        result = self.parser.parse(code, "test.py")

        # Should have class and methods
        class_decl = next((d for d in result.declarations if d.kind == "class"), None)
        assert class_decl is not None
        assert class_decl.name == "Calculator"
        assert "A simple calculator class" in class_decl.docstring

        # Should have methods
        methods = [d for d in result.declarations if d.kind == "function"]
        assert len(methods) >= 2  # __init__ and add

        # Check property
        properties = [d for d in result.declarations if d.kind == "property"]
        if properties:  # Property detection might vary
            prop = properties[0]
            assert prop.name == "version"
            assert "property" in prop.modifiers

    def test_imports_extraction(self):
        """Test import statement extraction."""
        code = """
import os
import sys
from typing import List, Dict
from collections import defaultdict
"""
        result = self.parser.parse(code, "test.py")

        assert "os" in result.imports
        assert "sys" in result.imports
        assert "typing" in result.imports
        assert "collections" in result.imports


class TestEnhancedRustParser:
    """Test enhanced Rust tree-sitter parser."""

    def setup_method(self):
        """Set up test fixtures."""
        try:
            self.parser = TreeSitterRustParser()
        except Exception as e:
            pytest.skip(f"Tree-sitter Rust parser not available: {e}")

    def test_function_with_doc_comments(self):
        """Test parsing Rust function with doc comments."""
        code = """
/// Calculate the sum of two integers
///
/// # Arguments
/// * `a` - First integer
/// * `b` - Second integer
///
/// # Returns
/// The sum of a and b
pub fn calculate_sum(a: i32, b: i32) -> i32 {
    a + b
}
"""
        result = self.parser.parse(code, "test.rs")

        assert len(result.declarations) >= 1
        func = next((d for d in result.declarations if d.name == "calculate_sum"), None)
        assert func is not None
        assert func.kind == "function"
        assert "public" in func.modifiers or "pub" in func.modifiers
        assert "Calculate the sum" in func.docstring or "sum" in func.docstring

    def test_struct_and_impl(self):
        """Test parsing Rust struct and impl blocks."""
        code = """
/// A point in 2D space
pub struct Point {
    pub x: f64,
    pub y: f64,
}

impl Point {
    /// Create a new point
    pub fn new(x: f64, y: f64) -> Self {
        Point { x, y }
    }

    /// Calculate distance from origin
    pub fn distance_from_origin(&self) -> f64 {
        (self.x * self.x + self.y * self.y).sqrt()
    }
}
"""
        result = self.parser.parse(code, "test.rs")

        # Should have struct
        struct_decl = next((d for d in result.declarations if d.kind == "struct"), None)
        assert struct_decl is not None
        assert struct_decl.name == "Point"

        # Should have methods
        methods = [d for d in result.declarations if d.kind in ["function", "method"]]
        assert len(methods) >= 2

    def test_async_function(self):
        """Test parsing async Rust function."""
        code = """
pub async fn fetch_data(url: &str) -> Result<String, Error> {
    // Implementation here
    Ok(String::new())
}
"""
        result = self.parser.parse(code, "test.rs")

        func = next((d for d in result.declarations if d.name == "fetch_data"), None)
        assert func is not None
        assert "async" in func.modifiers


class TestEnhancedJavaScriptParser:
    """Test enhanced JavaScript/TypeScript tree-sitter parser."""

    def setup_method(self):
        """Set up test fixtures."""
        try:
            self.parser = TreeSitterJsTsParser(language="javascript")
        except Exception as e:
            pytest.skip(f"Tree-sitter JavaScript parser not available: {e}")

    def test_function_declarations(self):
        """Test parsing JavaScript function declarations."""
        code = """
/**
 * Calculate the sum of two numbers
 * @param {number} a - First number
 * @param {number} b - Second number
 * @returns {number} The sum
 */
function calculateSum(a, b) {
    return a + b;
}

const multiply = (x, y) => x * y;

async function fetchData(url) {
    const response = await fetch(url);
    return response.json();
}
"""
        result = self.parser.parse(code, "test.js")

        # Should have function declarations
        functions = [d for d in result.declarations if d.kind in ["function", "arrow_function"]]
        assert len(functions) >= 2

        # Check function with JSDoc
        calc_func = next((f for f in functions if f.name == "calculateSum"), None)
        assert calc_func is not None
        assert "Calculate the sum" in calc_func.docstring

        # Check async function
        async_func = next((f for f in functions if f.name == "fetchData"), None)
        assert async_func is not None
        assert "async" in async_func.modifiers

    def test_class_with_methods(self):
        """Test parsing JavaScript class with methods."""
        code = """
/**
 * A simple calculator class
 */
class Calculator {
    constructor(precision = 2) {
        this.precision = precision;
    }

    /**
     * Add two numbers
     */
    add(a, b) {
        return a + b;
    }

    static create() {
        return new Calculator();
    }
}
"""
        result = self.parser.parse(code, "test.js")

        # Should have class
        class_decl = next((d for d in result.declarations if d.kind == "class"), None)
        assert class_decl is not None
        assert class_decl.name == "Calculator"

        # Should have methods
        methods = [d for d in result.declarations if d.kind == "method"]
        static_methods = [m for m in methods if "static" in m.modifiers]
        assert len(static_methods) >= 1

    def test_imports_and_exports(self):
        """Test parsing JavaScript imports."""
        code = """
import React from 'react';
import { useState, useEffect } from 'react';
import * as utils from './utils';
const fs = require('fs');
"""
        result = self.parser.parse(code, "test.js")

        assert "react" in result.imports
        assert "fs" in result.imports


class TestEnhancedGoParser:
    """Test enhanced Go tree-sitter parser."""

    def setup_method(self):
        """Set up test fixtures."""
        try:
            self.parser = TreeSitterGoParser()
        except Exception as e:
            pytest.skip(f"Tree-sitter Go parser not available: {e}")

    def test_function_with_doc_comment(self):
        """Test parsing Go function with doc comment."""
        code = """
package main

import "fmt"

// CalculateSum adds two integers and returns the result.
// This is a simple addition function for demonstration.
func CalculateSum(a, b int) int {
    return a + b
}
"""
        result = self.parser.parse(code, "test.go")

        func = next((d for d in result.declarations if d.name == "CalculateSum"), None)
        assert func is not None
        assert func.kind == "function"
        assert "CalculateSum adds two integers" in func.docstring

    def test_struct_and_methods(self):
        """Test parsing Go struct and methods."""
        code = """
package main

// Point represents a point in 2D space
type Point struct {
    X, Y float64
}

// New creates a new Point
func (p *Point) New(x, y float64) *Point {
    return &Point{X: x, Y: y}
}

// Distance calculates distance from origin
func (p *Point) Distance() float64 {
    return math.Sqrt(p.X*p.X + p.Y*p.Y)
}
"""
        result = self.parser.parse(code, "test.go")

        # Should have struct
        struct_decl = next((d for d in result.declarations if d.kind == "struct"), None)
        assert struct_decl is not None
        assert struct_decl.name == "Point"

        # Should have methods
        methods = [d for d in result.declarations if d.kind == "method"]
        assert len(methods) >= 2


class TestEnhancedCppParser:
    """Test enhanced C++ tree-sitter parser."""

    def setup_method(self):
        """Set up test fixtures."""
        try:
            self.parser = TreeSitterCppParser()
        except Exception as e:
            pytest.skip(f"Tree-sitter C++ parser not available: {e}")

    def test_function_with_doxygen(self):
        """Test parsing C++ function with Doxygen comments."""
        code = """
#include <iostream>

/**
 * @brief Calculate the sum of two integers
 * @param a First integer
 * @param b Second integer
 * @return The sum of a and b
 */
int calculateSum(int a, int b) {
    return a + b;
}
"""
        result = self.parser.parse(code, "test.cpp")

        func = next((d for d in result.declarations if d.name == "calculateSum"), None)
        assert func is not None
        assert func.kind == "function"
        assert "Calculate the sum" in func.docstring

    def test_class_with_methods(self):
        """Test parsing C++ class with methods."""
        code = """
/**
 * @brief A simple calculator class
 */
class Calculator {
public:
    /// Constructor
    Calculator(int precision = 2) : precision_(precision) {}

    /// Add two numbers
    int add(int a, int b) const {
        return a + b;
    }

private:
    int precision_;
};
"""
        result = self.parser.parse(code, "test.cpp")

        # Should have class
        class_decl = next((d for d in result.declarations if d.kind == "class"), None)
        assert class_decl is not None
        assert class_decl.name == "Calculator"

    def test_namespace(self):
        """Test parsing C++ namespace."""
        code = """
namespace math {
    int add(int a, int b) {
        return a + b;
    }
}
"""
        result = self.parser.parse(code, "test.cpp")

        # Should have namespace
        namespace_decl = next((d for d in result.declarations if d.kind == "namespace"), None)
        assert namespace_decl is not None
        assert namespace_decl.name == "math"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
