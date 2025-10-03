#!/usr/bin/env python3
"""Debug why init function is missing from declarations."""

import sys

sys.path.insert(0, "/Users/biostochastics/Development/GitHub/codeconcat")

import tree_sitter_zig as ts_zig
from tree_sitter import Language, Parser

zig_language = Language(ts_zig.language())
parser = Parser(zig_language)

code = """
pub const Vector = struct {
    x: f32,
    y: f32,

    pub fn init(x_val: f32, y_val: f32) Vector {
        return .{ .x = x_val, .y = y_val };
    }

    pub fn dot(self: Vector, other: Vector) f32 {
        return self.x * other.x + self.y * other.y;
    }

    pub fn length(self: Vector) f32 {
        return @sqrt(self.dot(self));
    }
};
"""

tree = parser.parse(bytes(code, "utf8"))


def find_nodes(node, node_type, results=None):
    if results is None:
        results = []
    if node.type == node_type:
        results.append(node)
    for child in node.children:
        find_nodes(child, node_type, results)
    return results


func_nodes = find_nodes(tree.root_node, "function_declaration")
print(f"Found {len(func_nodes)} function_declaration nodes\n")

for i, func_node in enumerate(func_nodes):
    print(f"=== Function {i + 1} ===")
    print(f"Position: {func_node.start_point} to {func_node.end_point}")

    # Show all children
    print(f"Children ({len(func_node.children)}):")
    for j, child in enumerate(func_node.children):
        text = code[child.start_byte : child.end_byte][:40].replace("\n", "\\n")
        print(f"  {j}: {child.type:20s} '{text}'")

    # Try to find identifier
    name = None
    for child in func_node.children:
        if child.type == "identifier":
            name = code[child.start_byte : child.end_byte]
            print(f"FOUND NAME: '{name}'")
            break

    if not name:
        print("WARNING: No identifier found!")

    print()
