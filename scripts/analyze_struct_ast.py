#!/usr/bin/env python3
"""Analyze the AST structure of Zig structs with methods."""

import sys

sys.path.insert(0, "/Users/biostochastics/Development/GitHub/codeconcat")

import tree_sitter_zig as ts_zig
from tree_sitter import Language, Parser

# Create parser
zig_language = Language(ts_zig.language())
parser = Parser(zig_language)

# Test struct with methods
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
};
"""

tree = parser.parse(bytes(code, "utf8"))


def print_ast(node, depth=0, max_depth=10):
    """Print AST structure."""
    if depth > max_depth:
        return

    indent = "  " * depth
    text_sample = code[node.start_byte : node.end_byte][:50].replace("\n", "\\n")
    print(
        f"{indent}{node.type} [{node.start_point[0]}:{node.start_point[1]}-{node.end_point[0]}:{node.end_point[1]}] '{text_sample}'"
    )

    for child in node.children:
        print_ast(child, depth + 1, max_depth)


print("=== Full AST Structure ===")
print_ast(tree.root_node, max_depth=8)

print("\n=== Finding struct_declaration nodes ===")


def find_nodes(node, node_type, results=None):
    if results is None:
        results = []
    if node.type == node_type:
        results.append(node)
    for child in node.children:
        find_nodes(child, node_type, results)
    return results


struct_nodes = find_nodes(tree.root_node, "struct_declaration")
print(f"Found {len(struct_nodes)} struct_declaration nodes")

for struct_node in struct_nodes:
    print("\nstruct_declaration children:")
    for i, child in enumerate(struct_node.children):
        text = code[child.start_byte : child.end_byte][:40].replace("\n", "\\n")
        print(f"  {i}: {child.type} - '{text}'")

print("\n=== Finding function_declaration nodes ===")
func_nodes = find_nodes(tree.root_node, "function_declaration")
print(f"Found {len(func_nodes)} function_declaration nodes")

for i, func_node in enumerate(func_nodes):
    # Get function name
    for child in func_node.children:
        if child.type == "identifier":
            func_name = code[child.start_byte : child.end_byte]
            print(f"  Function {i + 1}: {func_name}")
            # Check parent path
            parent = func_node.parent
            path = []
            while parent:
                path.append(parent.type)
                parent = parent.parent
            print(f"    Parent path: {' <- '.join(path[:5])}")
            break
