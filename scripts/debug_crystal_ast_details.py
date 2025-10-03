#!/usr/bin/env python3
"""Debug AST structure for lib, include/extend, and alias."""

from codeconcat.parser.language_parsers.tree_sitter_crystal_parser import TreeSitterCrystalParser

parser = TreeSitterCrystalParser()


def print_tree(node, indent=0, max_depth=6):
    if indent > max_depth:
        return
    print("  " * indent + f"{node.type}")
    if node.type in ["identifier", "constant", "string"]:
        try:
            text = node.text.decode("utf8")
            print("  " * indent + f"  → {text}")
        except:  # noqa: E722
            pass
    for child in node.children:
        print_tree(child, indent + 1, max_depth)


# Test: lib block
print("=" * 60)
print("LIB BLOCK AST")
print("=" * 60)
lib_code = """
@[Link("m")]
lib LibMath
  fun sqrt(x : Float64) : Float64
  fun pow(base : Float64, exp : Float64) : Float64
end
"""
tree = parser.parser.parse(bytes(lib_code, "utf8"))
print_tree(tree.root_node, max_depth=7)
print()

# Test: include/extend
print("=" * 60)
print("INCLUDE/EXTEND AST")
print("=" * 60)
inc_code = """
module MyModule
  include Enumerable(String)
  extend ClassMethods
end
"""
tree = parser.parser.parse(bytes(inc_code, "utf8"))
print_tree(tree.root_node, max_depth=7)
print()

# Test: alias
print("=" * 60)
print("ALIAS AST")
print("=" * 60)
alias_code = """
alias UserId = Int32
alias UserMap = Hash(UserId, User)
"""
tree = parser.parser.parse(bytes(alias_code, "utf8"))
print_tree(tree.root_node, max_depth=7)
