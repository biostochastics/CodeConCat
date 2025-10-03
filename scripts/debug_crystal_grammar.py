#!/usr/bin/env python3
"""Debug Crystal grammar to understand AST structure."""

from codeconcat.parser.language_parsers.tree_sitter_crystal_parser import TreeSitterCrystalParser

# Create parser
parser = TreeSitterCrystalParser()

# Test samples
samples = {
    "class": """
class User
  def initialize(@name : String)
  end
end
""",
    "module": """
module MyModule
  def self.hello
    "world"
  end
end
""",
    "function": """
def greet(name : String) : String
  "Hello, #{name}!"
end
""",
    "macro": """
macro log(message)
  puts {{message}}
end
""",
    "require": """
require "json"
require "./my_file"
""",
}


def print_tree(node, indent=0, max_depth=8):
    """Print AST tree with indentation."""
    if indent > max_depth:
        return
    print(
        "  " * indent
        + f"{node.type} [{node.start_point[0]}:{node.start_point[1]}-{node.end_point[0]}:{node.end_point[1]}]"
    )
    if node.type in ["identifier", "constant", "string", "symbol"]:
        try:
            text = node.text.decode("utf8")
            print("  " * indent + f"  → text: {text}")
        except:  # noqa: E722
            pass
    for child in node.children:
        print_tree(child, indent + 1, max_depth)


for name, code in samples.items():
    print(f"\n{'=' * 60}")
    print(f"Sample: {name}")
    print(f"{'=' * 60}")
    print("Code:")
    print(code)
    print("\nAST:")

    # Parse to get AST
    tree = parser.parser.parse(bytes(code, "utf8"))
    print_tree(tree.root_node, max_depth=6)
