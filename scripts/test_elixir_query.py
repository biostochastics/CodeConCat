#!/usr/bin/env python3
"""Test Elixir query extraction."""

from codeconcat.parser.language_parsers.tree_sitter_elixir_parser import TreeSitterElixirParser

# Create parser
parser = TreeSitterElixirParser()

# Test code
code = """
defmodule MyApp.User do
  def init(state) do
    {:ok, state}
  end

  def transform(data) do
    data
    |> String.trim()
    |> String.downcase()
  end
end
"""

print("Parsing Elixir code...")
result = parser.parse(code)

print(f"\nResults:")
print(f"  Declarations: {len(result.declarations)}")
for decl in result.declarations:
    print(f"    - {decl.kind}: {decl.name}")

print(f"  Imports: {len(result.imports)}")
for imp in result.imports:
    print(f"    - {imp}")

print(f"\nMetrics:")
print(f"  GenServer callbacks: {parser.genserver_callback_count}")
print(f"  LiveView callbacks: {parser.liveview_callback_count}")
print(f"  Pattern matches: {parser.pattern_match_count}")
print(f"  Pipe operations: {parser.pipe_operation_count}")
print(f"  Behaviors: {parser.behavior_count}")
print(f"  Macros: {parser.macro_count}")
