#!/usr/bin/env python3
"""Test the exact Query and QueryCursor API behavior for Zig."""

import tree_sitter_zig as ts_zig
from tree_sitter import Language, Parser, Query

# Try to import QueryCursor
try:
    from tree_sitter import QueryCursor
    print("✓ QueryCursor is available")
except ImportError:
    QueryCursor = None
    print("✗ QueryCursor is NOT available (tree-sitter >= 0.24.0)")

# Create a parser
zig_language = Language(ts_zig.language())
parser = Parser(zig_language)

# Test code with various declarations
code = '''
pub fn add(a: i32, b: i32) i32 {
    return a + b;
}

test "example" {
    const x = 5;
}

pub const Vector = struct {
    x: f32,
    y: f32,
};

const MyEnum = enum {
    one,
    two,
};

const MyUnion = union(enum) {
    int: i32,
    float: f32,
};
'''

tree = parser.parse(bytes(code, "utf8"))

# Test Query constructor
query_str = """
(function_declaration) @function
(test_declaration) @test
(variable_declaration) @variable
"""

print("\n=== Testing Query Constructor ===")
try:
    query = Query(zig_language, query_str)
    print(f"✓ Query created successfully: {query}")
except Exception as e:
    print(f"✗ Query creation failed: {e}")
    import sys
    sys.exit(1)

# Test QueryCursor if available
if QueryCursor is not None:
    print("\n=== Testing QueryCursor.captures() ===")
    try:
        cursor = QueryCursor(query)
        captures = cursor.captures(tree.root_node)
        print(f"✓ captures() returned: {type(captures)}")
        print(f"  Number of items: {len(captures)}")

        # Show structure
        for capture_name, nodes in captures.items():
            print(f"\n  Capture '{capture_name}':")
            for node in nodes[:2]:  # Show first 2
                text_sample = node.text[:50] if node.text else b''
                print(f"    - {node.type}: {text_sample}")
    except Exception as e:
        print(f"✗ QueryCursor.captures() failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print("\n=== QueryCursor not available, testing alternative ===")
    # In newer tree-sitter, we might need to use matches() directly
    try:
        matches = query.matches(tree.root_node)
        print(f"✓ query.matches() returned: {type(matches)}")
        match_list = list(matches)
        print(f"  Number of matches: {len(match_list)}")

        if match_list:
            first_match = match_list[0]
            print(f"  First match type: {type(first_match)}")
            print(f"  First match: {first_match}")
    except Exception as e:
        print(f"✗ query.matches() failed: {e}")
        import traceback
        traceback.print_exc()

# Check actual node types for struct, enum, union
print("\n\n=== Verifying struct/enum/union node types ===")
def find_node_by_name(node, name):
    """Find a variable declaration by name."""
    if node.type == "variable_declaration":
        for child in node.children:
            if child.type == "identifier" and child.text.decode('utf8') == name:
                return node
    for child in node.children:
        result = find_node_by_name(child, name)
        if result:
            return result
    return None

vector_node = find_node_by_name(tree.root_node, "Vector")
if vector_node:
    print(f"\nVector declaration node types:")
    for child in vector_node.children:
        print(f"  - {child.type}")

enum_node = find_node_by_name(tree.root_node, "MyEnum")
if enum_node:
    print(f"\nMyEnum declaration node types:")
    for child in enum_node.children:
        print(f"  - {child.type}")

union_node = find_node_by_name(tree.root_node, "MyUnion")
if union_node:
    print(f"\nMyUnion declaration node types:")
    for child in union_node.children:
        print(f"  - {child.type}")
