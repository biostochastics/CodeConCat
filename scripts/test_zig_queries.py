#!/usr/bin/env python3
"""Test tree-sitter query syntax for Zig."""

import tree_sitter_zig as ts_zig
from tree_sitter import Language, Parser, Query

# Create a parser
zig_language = Language(ts_zig.language())
parser = Parser(zig_language)

# Test simple query
code = '''
pub fn add(a: i32, b: i32) i32 {
    return a + b;
}
'''

tree = parser.parse(bytes(code, "utf8"))

# Test various query formats
test_queries = [
    # Simple node type query
    "(function_declaration) @function",

    # With child
    "(function_declaration (identifier) @name) @function",

    # Field query
    "(function_declaration name: (identifier) @name)",

    # Multiple patterns
    """
    (function_declaration) @function
    (test_declaration) @test
    """,
]

for i, query_str in enumerate(test_queries):
    try:
        query = Query(zig_language, query_str)
        captures = query.captures(tree.root_node)
        print(f"Query {i+1} SUCCESS: {len(captures)} captures")
        for capture in captures[:3]:  # Show first 3 captures
            node, name = capture
            print(f"  - {name}: {node.type}")
    except Exception as e:
        print(f"Query {i+1} FAILED: {e}")

# Test what works for function finding
simple_query = "(function_declaration) @function"
query = Query(zig_language, simple_query)
captures = query.captures(tree.root_node)
print(f"\n\nSimple function query found {len(captures)} functions")

# Check builtin functions
code2 = '''const std = @import("std");'''
tree2 = parser.parse(bytes(code2, "utf8"))

builtin_query = "(builtin_function) @builtin"
query2 = Query(zig_language, builtin_query)
captures2 = query2.captures(tree2.root_node)
print(f"Builtin query found {len(captures2)} builtins")
