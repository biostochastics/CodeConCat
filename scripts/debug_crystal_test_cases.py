#!/usr/bin/env python3
"""Debug specific test case failures."""

from codeconcat.parser.language_parsers.tree_sitter_crystal_parser import TreeSitterCrystalParser

parser = TreeSitterCrystalParser()

# Test case: struct
struct_code = """
struct Point
  property x : Float64
  property y : Float64

  def initialize(@x : Float64, @y : Float64)
  end

  def distance : Float64
    Math.sqrt(x ** 2 + y ** 2)
  end
end
"""

print("=" * 60)
print("STRUCT TEST")
print("=" * 60)
result = parser.parse(struct_code)
print(f"Declarations found: {len(result.declarations)}")
for d in result.declarations:
    print(f"  - {d.kind}: {d.name}")
print()

# Test case: macro
macro_code = """
macro define_method(name, content)
  def {{name.id}}
    {{content}}
  end
end

macro getter(*names)
  {% for name in names %}
    def {{name.id}}
      @{{name.id}}
    end
  {% end %}
end
"""

print("=" * 60)
print("MACRO TEST")
print("=" * 60)
result = parser.parse(macro_code)
print(f"Declarations found: {len(result.declarations)}")
for d in result.declarations:
    print(f"  - {d.kind}: {d.name}")
print(f"Macro count: {parser.macro_count}")
print()

# Test case: lib (C bindings)
lib_code = """
@[Link("m")]
lib LibMath
  fun sqrt(x : Float64) : Float64
  fun pow(base : Float64, exp : Float64) : Float64
end
"""

print("=" * 60)
print("LIB/C BINDINGS TEST")
print("=" * 60)
result = parser.parse(lib_code)
print(f"Declarations found: {len(result.declarations)}")
for d in result.declarations:
    print(f"  - {d.kind}: {d.name}")
print(f"C binding count: {parser.c_binding_count}")
print()

# Test case: imports (require, include, extend)
import_code = """
require "http/client"
require "./models/user"
require "../lib/validator"

module MyModule
  include Enumerable(String)
  extend ClassMethods
end
"""

print("=" * 60)
print("IMPORTS TEST")
print("=" * 60)
result = parser.parse(import_code)
print(f"Imports found: {len(result.imports)}")
for imp in result.imports:
    print(f"  - {imp}")
print("Expected: >= 5 (3 requires + 1 include + 1 extend)")
print()

# Test case: type alias
alias_code = """
alias UserId = Int32
alias UserMap = Hash(UserId, User)
alias Callback = Proc(String, Int32, Nil)
alias Result = {success: Bool, data: String?}
"""

print("=" * 60)
print("TYPE ALIAS TEST")
print("=" * 60)
result = parser.parse(alias_code)
print(f"Declarations found: {len(result.declarations)}")
for d in result.declarations:
    print(f"  - {d.kind}: {d.name}")
print()

# Test AST for struct
print("=" * 60)
print("STRUCT AST STRUCTURE")
print("=" * 60)
tree = parser.parser.parse(bytes(struct_code, "utf8"))


def print_tree(node, indent=0, max_depth=4):
    if indent > max_depth:
        return
    print("  " * indent + f"{node.type}")
    if node.type in ["identifier", "constant", "property"]:
        try:
            text = node.text.decode("utf8")
            print("  " * indent + f"  → {text}")
        except:  # noqa: E722
            pass
    for child in node.children:
        print_tree(child, indent + 1, max_depth)


print_tree(tree.root_node)
