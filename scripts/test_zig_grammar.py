#!/usr/bin/env python3
"""Test script to understand the tree-sitter-zig grammar node types."""

import tree_sitter_zig as ts_zig
from tree_sitter import Language, Parser

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
root = tree.root_node

def print_tree(node, indent=0):
    """Recursively print the AST tree."""
    print(" " * indent + f"{node.type} [{node.start_point}:{node.end_point}]")
    for child in node.children:
        print_tree(child, indent + 2)

print("AST for simple function:")
print_tree(root)

# Test more complex features
code2 = '''
const std = @import("std");

comptime {
    const x = 10;
}

pub async fn fetchData() !void {
    try doSomething();
}

test "example test" {
    const allocator = std.heap.page_allocator;
}
'''

tree2 = parser.parse(bytes(code2, "utf8"))
root2 = tree2.root_node

print("\n\nAST for complex code:")
print_tree(root2)

# Get all node types
def collect_node_types(node, types=None):
    if types is None:
        types = set()
    types.add(node.type)
    for child in node.children:
        collect_node_types(child, types)
    return types

types = collect_node_types(root2)
print("\n\nAll node types found:")
for t in sorted(types):
    print(f"  {t}")
