#!/usr/bin/env python3
"""Test tree-sitter query syntax for Zig with new API."""

import tree_sitter_zig as ts_zig
from tree_sitter import Language, Parser, Query

# Create a parser
zig_language = Language(ts_zig.language())
parser = Parser(zig_language)

# Test simple code
code = '''
pub fn add(a: i32, b: i32) i32 {
    return a + b;
}
'''

tree = parser.parse(bytes(code, "utf8"))

# Test query with new API
query_str = "(function_declaration) @function"
query = zig_language.query(query_str)

# Get captures using the new API
captures = query.captures(tree.root_node)

print(f"Found {len(captures)} captures")
for node, name in captures:
    print(f"  {name}: {node.type} - {code[node.start_byte:node.end_byte][:30]}...")

# Test more complex queries
test_queries = [
    "(function_declaration (identifier) @name)",
    "(builtin_function) @builtin",
    "(test_declaration) @test",
    "(variable_declaration) @var",
    "(error_union_type) @error_union",
]

print("\n\nTesting various queries:")
for q_str in test_queries:
    try:
        q = zig_language.query(q_str)
        print(f"✓ Query valid: {q_str[:50]}")
    except Exception as e:
        print(f"✗ Query failed: {q_str[:50]} - {e}")
