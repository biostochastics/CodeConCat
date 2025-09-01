#!/usr/bin/env python3
"""Test script to verify the Python Tree-sitter parser fix."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from codeconcat.parser.language_parsers.tree_sitter_python_parser import (  # noqa: E402
    TreeSitterPythonParser,
)

# Sample Python code to parse
test_code = '''
"""Module docstring."""

import os
import sys
from typing import List, Dict

class MyClass:
    """A sample class with docstring."""

    def __init__(self, name: str):
        """Initialize the class."""
        self.name = name

    def greet(self) -> str:
        """Return a greeting."""
        return f"Hello, {self.name}!"

def my_function(x: int, y: int) -> int:
    """Add two numbers."""
    return x + y

async def async_function():
    """An async function."""
    pass

# Constants
MY_CONSTANT = 42
ANOTHER_CONST = "hello"

# Variables
my_variable = 100
my_typed_var: str = "test"
'''


def test_parser():
    """Test the Python parser."""
    parser = TreeSitterPythonParser()

    # Parse the test code
    print("Parsing Python code...")
    result = parser.parse(test_code, "test.py")
    declarations, imports = result.declarations, result.imports

    print(f"\nFound {len(imports)} imports:")
    for imp in sorted(imports):
        print(f"  - {imp}")

    print(f"\nFound {len(declarations)} declarations:")
    for decl in declarations:
        print(f"  - {decl.kind}: {decl.name} (lines {decl.start_line}-{decl.end_line})")
        # Note: signature attribute doesn't exist in Declaration class yet
        # if decl.signature:
        #     print(f"    Signature: {decl.signature}")
        if decl.docstring:
            print(f"    Docstring: {decl.docstring[:50]}...")
        if decl.modifiers:
            print(f"    Modifiers: {', '.join(decl.modifiers)}")

    # Verify results
    print("\n=== Verification ===")
    assert len(imports) > 0, "No imports found!"
    assert len(declarations) > 0, "No declarations found!"

    # Check specific items
    import_names = set(imports)
    assert "os" in import_names, "Missing 'os' import"
    assert "sys" in import_names, "Missing 'sys' import"
    assert "typing" in import_names, "Missing 'typing' import"

    decl_names = {d.name for d in declarations}
    assert "MyClass" in decl_names, "Missing 'MyClass' class"
    assert "__init__" in decl_names, "Missing '__init__' method"
    assert "greet" in decl_names, "Missing 'greet' method"
    assert "my_function" in decl_names, "Missing 'my_function' function"
    assert "async_function" in decl_names, "Missing 'async_function' function"
    assert "MY_CONSTANT" in decl_names, "Missing 'MY_CONSTANT' constant"
    assert "my_variable" in decl_names, "Missing 'my_variable' variable"

    # Check async modifier
    async_decl = next((d for d in declarations if d.name == "async_function"), None)
    if async_decl and async_decl.modifiers:
        assert "async" in async_decl.modifiers, "Missing 'async' modifier"

    print("✅ All tests passed!")
    return True


if __name__ == "__main__":
    try:
        test_parser()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
