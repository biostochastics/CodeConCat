#!/usr/bin/env python3
"""Debug script to examine tree-sitter-elixir grammar structure."""

import tree_sitter_elixir as ts_elixir
from tree_sitter import Language, Parser


def print_tree(node, indent=0):
    """Print AST tree with indentation."""
    print(
        "  " * indent
        + f"{node.type} [{node.start_point[0]}:{node.start_point[1]}-{node.end_point[0]}:{node.end_point[1]}]"
    )
    if node.type in ["identifier", "atom", "alias", "operator"]:
        text = node.text.decode("utf8")
        print("  " * indent + f"  → text: {text}")
    for child in node.children:
        print_tree(child, indent + 1)


def main():
    """Examine tree-sitter-elixir grammar."""
    # Get language and create parser
    language = Language(ts_elixir.language())
    parser = Parser(language)

    # Test various Elixir constructs
    samples = {
        "module": b"""
defmodule MyApp.User do
  @moduledoc "User module"
  defstruct name: nil, age: 0
end
""",
        "import": b"""
import Ecto.Query
alias MyApp.User
require Logger
use GenServer
""",
        "function": b"""
def init(state) do
  {:ok, state}
end

def handle_call(:get, _from, state) do
  {:reply, state, state}
end
""",
        "pattern_match": b"""
def process({:ok, data}) do
  data
end

def process({:error, reason}) do
  {:error, reason}
end
""",
        "pipe": b"""
def transform(data) do
  data
  |> String.trim()
  |> String.downcase()
end
""",
        "macro": b"""
defmacro unless(condition, do: block) do
  quote do
    if !unquote(condition) do
      unquote(block)
    end
  end
end
""",
    }

    for name, code in samples.items():
        print(f"\n{'=' * 60}")
        print(f"Sample: {name}")
        print(f"{'=' * 60}")
        print(f"Code:\n{code.decode('utf8')}")
        print(f"\n{'AST:'}")
        print(f"{'-' * 60}")

        tree = parser.parse(code)
        print_tree(tree.root_node)
        print()


if __name__ == "__main__":
    main()
