#!/usr/bin/env python3
"""Quick check of HLSL grammar structure."""

import tree_sitter_hlsl
from tree_sitter import Language, Parser


def print_tree(node, source_code, indent=0):
    node_text = source_code[node.start_byte : node.end_byte]
    if len(node_text) > 50:
        node_text = node_text[:50] + "..."
    node_text = node_text.replace("\n", "\\n")
    print("  " * indent + f"{node.type} (named: {node.is_named}) = '{node_text}'")
    for child in node.children:
        if indent < 3:  # Limit depth
            print_tree(child, source_code, indent + 1)


# Load language
lang_ptr = tree_sitter_hlsl.language()
language = Language(lang_ptr)
parser = Parser(language)

# Test cbuffer
code = """
cbuffer MatrixBuffer : register(b0)
{
    float4x4 worldMatrix;
};
"""

print("CBUFFER TEST:")
tree = parser.parse(bytes(code, "utf8"))
print_tree(tree.root_node, code)

# Test texture
code2 = """Texture2D diffuseTexture : register(t0);"""
print("\n\nTEXTURE TEST:")
tree2 = parser.parse(bytes(code2, "utf8"))
print_tree(tree2.root_node, code2)
