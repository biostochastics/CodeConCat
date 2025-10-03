#!/usr/bin/env python3
"""Explore actual AST structure of Zig to understand correct node types."""

import tree_sitter_zig as ts_zig
from tree_sitter import Language, Parser

# Create a parser
zig_language = Language(ts_zig.language())
parser = Parser(zig_language)

# Test simple function
code1 = """
pub fn add(a: i32, b: i32) i32 {
    return a + b;
}
"""

tree = parser.parse(bytes(code1, "utf8"))


def print_tree(node, depth=0, max_depth=5):
    """Recursively print the AST tree."""
    if depth > max_depth:
        return

    indent = "  " * depth
    text_sample = node.text[:50] if node.text else b""
    print(f"{indent}{node.type}: {text_sample}")

    for child in node.children:
        print_tree(child, depth + 1, max_depth)


print("=== Simple Function AST ===")
print_tree(tree.root_node)

# Test struct
code2 = """
pub const Vector = struct {
    x: f32,
    y: f32,

    pub fn init(x: f32, y: f32) Vector {
        return .{ .x = x, .y = y };
    }
};
"""

tree = parser.parse(bytes(code2, "utf8"))
print("\n\n=== Struct with Method AST ===")
print_tree(tree.root_node)

# Test various declarations
code3 = """
const std = @import("std");

test "example" {
    const x = 5;
}

pub fn main() !void {
    try doSomething();
}
"""

tree = parser.parse(bytes(code3, "utf8"))
print("\n\n=== Mixed Declarations AST ===")
print_tree(tree.root_node, max_depth=4)


# Find all unique node types
def collect_node_types(node, types_set):
    """Collect all unique node types in the tree."""
    types_set.add(node.type)
    for child in node.children:
        collect_node_types(child, types_set)


all_types = set()
collect_node_types(tree.root_node, all_types)

print("\n\n=== All Node Types Found ===")
for t in sorted(all_types):
    print(f"  - {t}")
