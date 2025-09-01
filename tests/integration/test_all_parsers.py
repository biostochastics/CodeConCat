#!/usr/bin/env python3
"""Test all Tree-sitter parsers after fixing the API usage."""

import sys
from pathlib import Path

# Add codeconcat to path
sys.path.insert(0, str(Path(__file__).parent))

from codeconcat.parser.language_parsers.tree_sitter_cpp_parser import (  # noqa: E402
    TreeSitterCppParser,
)
from codeconcat.parser.language_parsers.tree_sitter_csharp_parser import (  # noqa: E402
    TreeSitterCSharpParser,
)
from codeconcat.parser.language_parsers.tree_sitter_go_parser import (  # noqa: E402
    TreeSitterGoParser,
)
from codeconcat.parser.language_parsers.tree_sitter_java_parser import (  # noqa: E402
    TreeSitterJavaParser,
)
from codeconcat.parser.language_parsers.tree_sitter_js_ts_parser import (  # noqa: E402
    TreeSitterJsTsParser,
)
from codeconcat.parser.language_parsers.tree_sitter_julia_parser import (  # noqa: E402
    TreeSitterJuliaParser,
)
from codeconcat.parser.language_parsers.tree_sitter_php_parser import (  # noqa: E402
    TreeSitterPhpParser,
)
from codeconcat.parser.language_parsers.tree_sitter_python_parser import (  # noqa: E402
    TreeSitterPythonParser,
)
from codeconcat.parser.language_parsers.tree_sitter_rust_parser import (  # noqa: E402
    TreeSitterRustParser,
)

# Note: R parser import commented out - tree-sitter-r package not available
# from codeconcat.parser.language_parsers.tree_sitter_r_parser import TreeSitterRParser

# Test code samples for each language
TEST_SAMPLES = {
    "python": '''
import os
import sys
from typing import List

class MyClass:
    """A sample class."""
    def method(self, x: int) -> int:
        """Method docstring."""
        return x * 2

def my_function(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
''',
    "go": """
package main

import (
    "fmt"
    "strings"
)

// MyStruct is a sample structure
type MyStruct struct {
    Name string
    Age  int
}

// Hello returns a greeting
func Hello(name string) string {
    return fmt.Sprintf("Hello, %s", name)
}
""",
    "cpp": """
#include <iostream>
#include <vector>

/// A sample class
class MyClass {
public:
    /// Constructor
    MyClass(int value) : value_(value) {}

    /// Get the value
    int getValue() const { return value_; }

private:
    int value_;
};

/// Main function
int main() {
    return 0;
}
""",
    "rust": """
use std::fmt;
use std::io;

/// A sample struct
struct Person {
    name: String,
    age: u32,
}

/// Implementation for Person
impl Person {
    /// Create a new person
    pub fn new(name: String, age: u32) -> Self {
        Person { name, age }
    }
}

/// Main function
fn main() {
    println!("Hello, world!");
}
""",
    "csharp": """
using System;
using System.Collections.Generic;

namespace MyNamespace
{
    /// <summary>
    /// A sample class
    /// </summary>
    public class MyClass
    {
        /// <summary>
        /// A property
        /// </summary>
        public string Name { get; set; }

        /// <summary>
        /// A method
        /// </summary>
        public void DoSomething()
        {
            Console.WriteLine("Hello");
        }
    }
}
""",
    "java": """
import java.util.*;
import java.io.*;

/**
 * A sample class
 */
public class MyClass {
    /**
     * A field
     */
    private String name;

    /**
     * Constructor
     */
    public MyClass(String name) {
        this.name = name;
    }

    /**
     * A method
     */
    public String getName() {
        return name;
    }
}
""",
    "php": """
<?php
namespace MyNamespace;

use DateTime;
use Exception;

/**
 * A sample class
 */
class MyClass {
    /**
     * @var string
     */
    private $name;

    /**
     * Constructor
     * @param string $name
     */
    public function __construct($name) {
        $this->name = $name;
    }

    /**
     * Get name
     * @return string
     */
    public function getName() {
        return $this->name;
    }
}
""",
    "javascript": """
import React from 'react';
import { useState } from 'react';

/**
 * A sample component
 */
function MyComponent(props) {
    const [count, setCount] = useState(0);

    /**
     * Handle click
     */
    const handleClick = () => {
        setCount(count + 1);
    };

    return <div>{count}</div>;
}

export default MyComponent;
""",
    "typescript": """
import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';

/**
 * A sample class
 */
export class MyService {
    /**
     * Constructor
     */
    constructor(private http: HttpClient) {}

    /**
     * Fetch data
     */
    async getData(): Promise<any> {
        return this.http.get('/api/data').toPromise();
    }
}
""",
    "julia": '''
using LinearAlgebra
using Statistics

"""
A sample struct
"""
struct Point
    x::Float64
    y::Float64
end

"""
Calculate distance between two points
"""
function distance(p1::Point, p2::Point)
    return sqrt((p1.x - p2.x)^2 + (p1.y - p2.y)^2)
end
''',
    "r": """
library(ggplot2)
library(dplyr)

#' Calculate mean and standard deviation
#' @param x A numeric vector
#' @return A list with mean and sd
calculate_stats <- function(x) {
    list(
        mean = mean(x),
        sd = sd(x)
    )
}

#' Plot data
#' @param data A data frame
plot_data <- function(data) {
    ggplot(data, aes(x = x, y = y)) +
        geom_point()
}
""",
}


def check_parser(name, parser_class, code, language=None):
    """Check a single parser."""
    print(f"\n{'='*60}")
    print(f"Testing {name} Parser")
    print(f"{'='*60}")

    try:
        # Initialize parser
        parser = parser_class(language) if language else parser_class()

        # Parse code - pass a dummy file path since parse() requires it
        result = parser.parse(code, file_path=f"test.{language if language else name.lower()}")

        # Check results
        print("✓ Parser initialized successfully")
        print("✓ Parsing completed without errors")

        if result.declarations:
            print(f"✓ Found {len(result.declarations)} declarations:")
            for decl in result.declarations:
                print(f"  - {decl.kind}: {decl.name}")
                if decl.docstring:
                    print("    (has docstring)")
        else:
            print("⚠ No declarations found")

        if result.imports:
            print(f"✓ Found {len(result.imports)} imports:")
            for imp in result.imports:
                print(f"  - {imp}")
        else:
            print("⚠ No imports found")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_all_tree_sitter_parsers():
    """Test all tree-sitter parsers."""
    print("Testing All Tree-sitter Parsers After API Fix")
    print("=" * 60)

    results = []

    # Test each parser
    test_cases = [
        ("Python", TreeSitterPythonParser, TEST_SAMPLES["python"]),
        ("Go", TreeSitterGoParser, TEST_SAMPLES["go"]),
        ("C++", TreeSitterCppParser, TEST_SAMPLES["cpp"]),
        ("Rust", TreeSitterRustParser, TEST_SAMPLES["rust"]),
        ("C#", TreeSitterCSharpParser, TEST_SAMPLES["csharp"]),
        ("Java", TreeSitterJavaParser, TEST_SAMPLES["java"]),
        ("PHP", TreeSitterPhpParser, TEST_SAMPLES["php"]),
        ("JavaScript", TreeSitterJsTsParser, TEST_SAMPLES["javascript"], "javascript"),
        ("TypeScript", TreeSitterJsTsParser, TEST_SAMPLES["typescript"], "typescript"),
        ("Julia", TreeSitterJuliaParser, TEST_SAMPLES["julia"]),
        # R parser test skipped - tree-sitter-r package not available
        # ("R", TreeSitterRParser, TEST_SAMPLES['r']),
    ]

    for test_case in test_cases:
        success = check_parser(*test_case)
        results.append((test_case[0], success))

    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"{name:15} {status}")

    print(f"\nTotal: {passed}/{total} parsers passed")

    if passed == total:
        print("\n🎉 All parsers are working correctly!")
    else:
        print(f"\n⚠️ {total - passed} parser(s) need attention")

    # Assert that all parsers passed
    assert passed == total, f"{total - passed} parser(s) failed"


# if __name__ == "__main__":
#     test_all_tree_sitter_parsers()
