#!/usr/bin/env python3
"""Debug generic types test."""

from codeconcat.parser.language_parsers.tree_sitter_crystal_parser import TreeSitterCrystalParser

parser = TreeSitterCrystalParser()

# Generic types test
code = """
class Container(T)
  @value : T

  def initialize(@value : T)
  end

  def get : T
    @value
  end
end

class Result(T, E)
  @value : T | E

  def initialize(@value : T | E)
  end

  def ok? : Bool
    @value.is_a?(T)
  end
end
"""

result = parser.parse(code)
print(f"Declarations found: {len(result.declarations)}")
for d in result.declarations:
    print(f"  - {d.kind}: {d.name}")

print(f"\nContainer found: {any(d.name == 'Container' for d in result.declarations)}")
print(f"Result found: {any(d.name == 'Result' for d in result.declarations)}")

# Union types test
code2 = """
def process(value : String | Int32 | Nil) : String?
  case value
  when String
    value.upcase
  when Int32
    value.to_s
  else
    nil
  end
end

class Config
  @host : String?
  @port : Int32 | Nil
  @options : Hash(String, String | Int32)?

  def initialize
    @host = nil
    @port = nil
    @options = nil
  end
end
"""

result2 = parser.parse(code2)
print(f"\n\nUnion types test:")
print(f"Declarations found: {len(result2.declarations)}")
for d in result2.declarations:
    print(f"  - {d.kind}: {d.name}")
print(f"\nExpected >= 4 declarations")
