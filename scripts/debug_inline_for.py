#!/usr/bin/env python3
"""Debug inline for and comptime parameter detection."""

import sys

sys.path.insert(0, "/Users/biostochastics/Development/GitHub/codeconcat")

import tree_sitter_zig as ts_zig
from tree_sitter import Language, Parser

zig_language = Language(ts_zig.language())
parser = Parser(zig_language)

code = """
pub fn generateArray(comptime size: usize) [size]u8 {
    var array: [size]u8 = undefined;
    inline for (&array, 0..) |*item, i| {
        item.* = @intCast(i);
    }
    return array;
}
"""

tree = parser.parse(bytes(code, "utf8"))


def find_nodes(node, node_type, results=None, path=""):
    if results is None:
        results = []
    if node.type == node_type:
        results.append((node, path))
    for i, child in enumerate(node.children):
        find_nodes(child, node_type, results, f"{path}/{node.type}[{i}]")
    return results


# Search for comptime-related nodes
for search_type in [
    "comptime",
    "comptime_expression",
    "comptime_declaration",
    "for_statement",
    "inline",
]:
    found = find_nodes(tree.root_node, search_type)
    if found:
        print(f"\n=== Found {len(found)} '{search_type}' nodes ===")
        for node, path in found:
            text = code[node.start_byte : node.end_byte][:50].replace("\n", "\\n")
            print(f"  Path: {path}")
            print(f"  Text: '{text}'")

# Show parameter structure
print("\n=== Function parameters ===")
func_decls = find_nodes(tree.root_node, "function_declaration")
for func_node, _ in func_decls:
    for child in func_node.children:
        if child.type == "parameters":
            print(f"Parameters node has {len(child.children)} children:")
            for i, param_child in enumerate(child.children):
                if param_child.type == "parameter":
                    print(f"  Parameter {i}:")
                    for j, p in enumerate(param_child.children):
                        text = code[p.start_byte : p.end_byte]
                        print(f"    {j}: {p.type:20s} '{text}'")

# Show for loop structure
print("\n=== For loops ===")
for_loops = find_nodes(tree.root_node, "for_statement")
print(f"Found {len(for_loops)} for_statement nodes")
for for_node, _path in for_loops:
    print(f"\nFor loop children ({len(for_node.children)}):")
    for i, child in enumerate(for_node.children):
        text = code[child.start_byte : child.end_byte][:40].replace("\n", "\\n")
        print(f"  {i}: {child.type:20s} '{text}'")
