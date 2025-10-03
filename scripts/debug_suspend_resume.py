#!/usr/bin/env python3
"""Debug suspend/resume AST structure."""

import sys

sys.path.insert(0, "/Users/biostochastics/Development/GitHub/codeconcat")

import tree_sitter_zig as ts_zig
from tree_sitter import Language, Parser

zig_language = Language(ts_zig.language())
parser = Parser(zig_language)

code = """
const std = @import("std");

var frame: anyframe = undefined;

pub fn asyncFunction() void {
    suspend {
        frame = @frame();
    }
    // Do async work
}

pub fn resumeFunction() void {
    resume frame;
}

pub fn nosuspendFunction() void {
    nosuspend {
        // Code that should not suspend
        performCriticalOperation();
    }
}
"""

tree = parser.parse(bytes(code, "utf8"))


# Search for all unique node types
def collect_node_types(node, types=None):
    if types is None:
        types = set()
    types.add(node.type)
    for child in node.children:
        collect_node_types(child, types)
    return types


types = collect_node_types(tree.root_node)
relevant = [
    t
    for t in sorted(types)
    if any(kw in t.lower() for kw in ["suspend", "resume", "async", "await", "frame"])
]

print("=== Relevant node types ===")
for t in relevant:
    print(f"  {t}")

# Search for keywords as text
print("\n=== Keywords found in code ===")
keywords = ["suspend", "resume", "nosuspend", "@frame", "anyframe"]
for keyword in keywords:
    if keyword in code:
        print(f"  '{keyword}' - YES")
    else:
        print(f"  '{keyword}' - NO")


# Show function structures
def find_nodes(node, node_type, results=None):
    if results is None:
        results = []
    if node.type == node_type:
        results.append(node)
    for child in node.children:
        find_nodes(child, node_type, results)
    return results


print("\n=== Function children ===")
for func_node in find_nodes(tree.root_node, "function_declaration"):
    name = None
    for child in func_node.children:
        if child.type == "identifier":
            name = code[child.start_byte : child.end_byte]
            break
    if name:
        print(f"\nFunction: {name}")
        for i, child in enumerate(func_node.children):
            text = code[child.start_byte : child.end_byte][:30].replace("\n", "\\n")
            print(f"  {i}: {child.type:20s} '{text}'")
