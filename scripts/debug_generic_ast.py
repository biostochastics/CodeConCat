#!/usr/bin/env python3
"""Debug generic class AST structure."""

from codeconcat.parser.language_parsers.tree_sitter_crystal_parser import TreeSitterCrystalParser

parser = TreeSitterCrystalParser()

code = """
class Container(T)
  def initialize
  end
end
"""

tree = parser.parser.parse(bytes(code, "utf8"))


def print_tree(node, indent=0, max_depth=6):
    if indent > max_depth:
        return
    print("  " * indent + f"{node.type}")
    if node.type in ["identifier", "constant"]:
        try:
            text = node.text.decode("utf8")
            print("  " * indent + f"  → {text}")
        except:  # noqa: E722
            pass
    for child in node.children:
        print_tree(child, indent + 1, max_depth)


print_tree(tree.root_node)
