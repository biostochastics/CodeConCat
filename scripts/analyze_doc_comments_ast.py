#!/usr/bin/env python3
"""Analyze how doc comments appear in the Zig AST."""

import sys

sys.path.insert(0, "/Users/biostochastics/Development/GitHub/codeconcat")

import tree_sitter_zig as ts_zig
from tree_sitter import Language, Parser

zig_language = Language(ts_zig.language())
parser = Parser(zig_language)

code = """
/// This is a simple addition function.
/// It adds two numbers together.
pub fn add(a: i32, b: i32) i32 {
    return a + b;
}

//! Module-level documentation

/// A 3D vector structure.
pub const Vector3 = struct {
    x: f32,
    y: f32,
};
"""

tree = parser.parse(bytes(code, "utf8"))


def print_ast(node, depth=0, max_depth=6):
    indent = "  " * depth
    text_sample = code[node.start_byte : node.end_byte][:60].replace("\n", "\\n")
    print(f"{indent}{node.type} [{node.start_point[0]}:{node.start_point[1]}] '{text_sample}'")

    for child in node.children:
        print_ast(child, depth + 1, max_depth)


print("=== Full AST ===")
print_ast(tree.root_node)

print("\n=== Finding comment nodes ===")


def find_nodes(node, node_type, results=None):
    if results is None:
        results = []
    if node.type == node_type:
        results.append(node)
    for child in node.children:
        find_nodes(child, node_type, results)
    return results


comments = find_nodes(tree.root_node, "comment")
print(f"Found {len(comments)} comment nodes\n")

for i, comment in enumerate(comments):
    text = code[comment.start_byte : comment.end_byte]
    print(f"Comment {i + 1}: '{text}'")
    print(f"  Position: line {comment.start_point[0] + 1}, col {comment.start_point[1]}")
    print(f"  Next sibling: {comment.next_sibling.type if comment.next_sibling else None}")
    print(f"  Prev sibling: {comment.prev_sibling.type if comment.prev_sibling else None}")
    print(f"  Parent: {comment.parent.type if comment.parent else None}")
    print()

print("\n=== Finding function nodes and their relationships to comments ===")
funcs = find_nodes(tree.root_node, "function_declaration")
for func in funcs:
    # Get function name
    func_name = None
    for child in func.children:
        if child.type == "identifier":
            func_name = code[child.start_byte : child.end_byte]
            break

    print(f"Function: {func_name}")
    print(f"  Position: line {func.start_point[0] + 1}")
    print(f"  Prev sibling: {func.prev_sibling.type if func.prev_sibling else None}")

    # Check if prev sibling is comment
    if func.prev_sibling and func.prev_sibling.type == "comment":
        comment_text = code[func.prev_sibling.start_byte : func.prev_sibling.end_byte]
        print(f"  Doc comment: '{comment_text}'")

    # Check parent's children for nearby comments
    parent = func.parent
    if parent:
        func_index = list(parent.children).index(func)
        print(f"  Index in parent: {func_index}")
        if func_index > 0:
            prev = parent.children[func_index - 1]
            print(f"  Previous sibling in parent: {prev.type}")
            if prev.type == "comment":
                print(f"    Comment text: '{code[prev.start_byte : prev.end_byte]}'")
