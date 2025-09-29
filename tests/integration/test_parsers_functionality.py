#!/usr/bin/env python3
"""
Parser functionality test script for CodeConCat.
Tests each parser with real code samples to verify correct extraction.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tempfile  # noqa: E402
from pathlib import Path  # noqa: E402

from codeconcat.base_types import CodeConCatConfig, ParsedFileData  # noqa: E402
from codeconcat.parser.unified_pipeline import parse_code_files  # noqa: E402

# Test samples for each language
TEST_SAMPLES = {
    "python": {
        "filename": "test.py",
        "content": '''
"""Module docstring for testing."""

import os
import sys
from typing import List, Optional

class TestClass:
    """Test class with methods."""

    def __init__(self, name: str):
        """Initialize the test class."""
        self.name = name

    def method_one(self) -> str:
        """First method."""
        return self.name

    @staticmethod
    def static_method(value: int) -> int:
        """Static method example."""
        return value * 2

def test_function(param1: str, param2: int = 10) -> Optional[str]:
    """
    Test function with type hints.

    Args:
        param1: First parameter
        param2: Second parameter with default

    Returns:
        Optional string result
    """
    if param2 > 5:
        return param1
    return None

async def async_function():
    """Async function example."""
    pass
''',
        "expected": {
            "classes": ["TestClass"],
            # Note: Tree-sitter may extract methods as functions
            "functions": [
                "test_function",
                "async_function",
                "__init__",
                "method_one",
                "static_method",
            ],
            "imports": ["os", "sys", "List", "Optional", "typing"],
        },
    },
    "javascript": {
        "filename": "test.js",
        "content": """
// JavaScript test file
import React from 'react';
import { useState, useEffect } from 'react';
const lodash = require('lodash');

/**
 * Test class with JSDoc
 */
class TestClass {
    constructor(name) {
        this.name = name;
    }

    getName() {
        return this.name;
    }

    static staticMethod() {
        return 42;
    }
}

// Regular function
function testFunction(param1, param2 = 10) {
    return param1 + param2;
}

// Arrow function
const arrowFunction = (x, y) => x + y;

// Async function
async function fetchData(url) {
    const response = await fetch(url);
    return response.json();
}

// React component
const MyComponent = ({ title }) => {
    const [count, setCount] = useState(0);

    useEffect(() => {
        console.log('Effect ran');
    }, [count]);

    return <div>{title}: {count}</div>;
};

export default MyComponent;
""",
        "expected": {
            "classes": ["TestClass"],
            # Note: Arrow functions and React components may not all be detected
            "functions": ["testFunction", "fetchData"],
            "imports": ["react", "lodash"],  # Detects as lowercase 'react'
        },
    },
    "go": {
        "filename": "test.go",
        "content": """
package main

import (
    "fmt"
    "net/http"
    "encoding/json"
)

// User struct represents a user
type User struct {
    ID       int    `json:"id"`
    Name     string `json:"name"`
    Email    string `json:"email"`
}

// UserService interface
type UserService interface {
    GetUser(id int) (*User, error)
    CreateUser(user *User) error
}

// userServiceImpl implements UserService
type userServiceImpl struct {
    db Database
}

// GetUser retrieves a user by ID
func (s *userServiceImpl) GetUser(id int) (*User, error) {
    // Implementation here
    return nil, nil
}

// CreateUser creates a new user
func (s *userServiceImpl) CreateUser(user *User) error {
    // Implementation here
    return nil
}

// HandleRequest handles HTTP requests
func HandleRequest(w http.ResponseWriter, r *http.Request) {
    fmt.Fprintf(w, "Hello, World!")
}

func main() {
    fmt.Println("Starting server...")
    http.HandleFunc("/", HandleRequest)
    http.ListenAndServe(":8080", nil)
}
""",
        "expected": {
            "structs": ["User", "userServiceImpl"],
            "interfaces": ["UserService"],
            # Note: Methods GetUser/CreateUser may not be extracted separately from structs in Go
            "functions": ["HandleRequest", "main"],
            "imports": ["fmt", "net/http", "encoding/json"],
        },
    },
    "rust": {
        "filename": "test.rs",
        "content": """
use std::collections::HashMap;
use std::io::{self, Read};

/// A test struct
#[derive(Debug, Clone)]
pub struct TestStruct {
    name: String,
    value: i32,
}

impl TestStruct {
    /// Create a new TestStruct
    pub fn new(name: String, value: i32) -> Self {
        TestStruct { name, value }
    }

    /// Get the name
    pub fn get_name(&self) -> &str {
        &self.name
    }
}

/// A test trait
trait TestTrait {
    fn do_something(&self) -> String;
}

impl TestTrait for TestStruct {
    fn do_something(&self) -> String {
        format!("{}: {}", self.name, self.value)
    }
}

/// Main function
fn main() {
    let test = TestStruct::new("Test".to_string(), 42);
    println!("{:?}", test);
}

/// Helper function
pub fn helper_function(input: &str) -> Result<String, io::Error> {
    Ok(input.to_uppercase())
}
""",
        "expected": {
            "structs": ["TestStruct"],
            "traits": ["TestTrait"],
            "functions": ["new", "get_name", "do_something", "main", "helper_function"],
            # Note: Rust imports may be parsed as full paths
            "imports": ["std::collections::HashMap", "std::io::{self, Read}"],
        },
    },
}


def check_parser(language: str, sample: dict):
    """Check a specific language parser."""
    print(f"\n{'=' * 60}")
    print(f"Testing {language.upper()} parser")
    print(f"{'=' * 60}")

    # Create temporary file
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / sample["filename"]
        filepath.write_text(sample["content"])

        # Create ParsedFileData
        file_data = ParsedFileData(
            file_path=str(filepath), content=sample["content"], language=language
        )

        # Create config for tree-sitter parsing
        config = CodeConCatConfig(
            parser_engine="tree_sitter",
            disable_tree=False,
            use_enhanced_parsers=True,
            disable_progress_bar=True,
        )

        # Parse the file
        try:
            results, parse_errors = parse_code_files([file_data], config)

            if not results:
                print("❌ No parsing results returned")
                return False

            result = results[0]

            # Check for errors
            if hasattr(result, "error") and result.error:
                print(f"❌ Parser error: {result.error}")
                # Try with enhanced parser
                print("  Retrying with enhanced parser...")
                config.parser_engine = "regex"
                config.use_enhanced_parsers = True
                results, parse_errors = parse_code_files([file_data], config)
                if results:
                    result = results[0]
                else:
                    return False

            # Extract found items from declarations
            found_classes = []
            found_functions = []
            found_imports = []
            found_structs = []
            found_interfaces = []
            found_traits = []
            found_methods = []

            # Extract from declarations field
            if hasattr(result, "declarations") and result.declarations:
                for decl in result.declarations:
                    if decl.kind == "class":
                        found_classes.append(decl.name)
                        # Extract methods from class children
                        for child in decl.children:
                            if child.kind in ["method", "function"]:
                                found_methods.append(child.name)
                    elif decl.kind == "function":
                        found_functions.append(decl.name)
                    elif decl.kind == "struct":
                        found_structs.append(decl.name)
                        # Extract methods from struct impl blocks
                        for child in decl.children:
                            if child.kind in ["method", "function"]:
                                found_methods.append(child.name)
                    elif decl.kind == "interface":
                        found_interfaces.append(decl.name)
                    elif decl.kind == "trait":
                        found_traits.append(decl.name)
                    elif decl.kind == "type" and language == "go":
                        # In Go, types can be structs or interfaces
                        if "struct" in decl.signature.lower():
                            found_structs.append(decl.name)
                        elif "interface" in decl.signature.lower():
                            found_interfaces.append(decl.name)

            # Extract imports
            if hasattr(result, "imports") and result.imports:
                # Imports might be strings or objects with name attribute
                for imp in result.imports:
                    if isinstance(imp, str):
                        found_imports.append(imp)
                    elif hasattr(imp, "name"):
                        found_imports.append(imp.name)
                    else:
                        found_imports.append(str(imp))

            # Print results
            print("\n📊 Parsing Results:")
            print(f"  Classes: {found_classes}")
            print(f"  Functions: {found_functions}")
            if found_methods:
                print(f"  Methods: {found_methods}")
            print(f"  Imports: {found_imports}")

            if language == "go":
                print(f"  Structs: {found_structs}")
                print(f"  Interfaces: {found_interfaces}")
            elif language == "rust":
                print(f"  Structs: {found_structs}")
                print(f"  Traits: {found_traits}")

            # Validate results
            expected = sample["expected"]
            success = True

            def check_items(found, expected_key, label):
                nonlocal success
                if expected_key in expected:
                    expected_items = expected[expected_key]
                    missing = set(expected_items) - set(found)
                    if missing:
                        print(f"\n  ⚠️  Missing {label}: {missing}")
                        success = False
                    else:
                        print(f"  ✅ All {label} found")

            check_items(found_classes, "classes", "classes")
            check_items(found_functions, "functions", "functions")
            if "methods" in expected:
                check_items(found_methods, "methods", "methods")
            check_items(found_imports, "imports", "imports")

            if language == "go":
                check_items(found_structs, "structs", "structs")
                check_items(found_interfaces, "interfaces", "interfaces")
            elif language == "rust":
                check_items(found_structs, "structs", "structs")
                check_items(found_traits, "traits", "traits")

            return success

        except Exception as e:
            print(f"❌ Exception during parsing: {e}")
            import traceback

            traceback.print_exc()
            return False


def main():
    """Run all parser tests."""
    print("🔍 CodeConCat Parser Functionality Test")
    print("=" * 60)

    results = {}

    for language, sample in TEST_SAMPLES.items():
        results[language] = check_parser(language, sample)

    # Summary
    print(f"\n{'=' * 60}")
    print("📈 TEST SUMMARY")
    print(f"{'=' * 60}")

    for language, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {language.upper():15} {status}")

    total = len(results)
    passed = sum(1 for s in results.values() if s)

    print(f"\n  Total: {passed}/{total} parsers passed")

    if passed == total:
        print("\n🎉 All parsers working correctly!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} parser(s) need attention")
        return 1


if __name__ == "__main__":
    sys.exit(main())
