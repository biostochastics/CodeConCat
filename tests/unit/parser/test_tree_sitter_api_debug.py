#!/usr/bin/env python3
"""Debug tree-sitter API to understand capture structure."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tree_sitter_language_pack import get_language, get_parser  # noqa: E402


# Test Python parser API
def test_capture_api():
    print("Testing tree-sitter capture API...")

    # Get Python language
    language = get_language("python")
    parser = get_parser("python")

    # Simple Python code
    code = """
def hello():
    return "world"

class MyClass:
    pass
"""

    # Parse the code
    tree = parser.parse(code.encode("utf-8"))
    root = tree.root_node

    # Test query with captures
    query_str = """
    (function_definition
        name: (identifier) @func_name
    ) @function

    (class_definition
        name: (identifier) @class_name
    ) @class
    """

    query = language.query(query_str)

    # Test captures() method
    print("\n1. Testing captures() method:")
    captures = query.captures(root)
    print(f"   Type of captures: {type(captures)}")
    print(f"   Length: {len(captures)}")

    if isinstance(captures, dict):
        print(f"   Capture keys: {list(captures.keys())}")
        for key, nodes in captures.items():
            print(
                f"   {key}: {type(nodes)} with {len(nodes) if hasattr(nodes, '__len__') else '?'} items"
            )
            if nodes and hasattr(nodes, "__getitem__"):
                first_node = nodes[0]
                print(f"      First item type: {type(first_node)}")
                if hasattr(first_node, "type"):
                    print(f"      First node.type: {first_node.type}")
    elif isinstance(captures, list) and captures:
        first_capture = captures[0]
        print(f"   First capture type: {type(first_capture)}")
        print(f"   First capture content: {first_capture}")

    # Test matches() method
    print("\n2. Testing matches() method:")
    matches = query.matches(root)
    print(f"   Type of matches: {type(matches)}")
    print(f"   Length: {len(matches)}")

    if matches:
        first_match = matches[0]
        print(f"   First match type: {type(first_match)}")
        print(
            f"   First match length: {len(first_match) if hasattr(first_match, '__len__') else 'N/A'}"
        )
        print(f"   First match content: {first_match}")

        if isinstance(first_match, tuple) and len(first_match) == 2:
            match_id, captures_dict = first_match
            print(f"   Match ID: {match_id}")
            print(f"   Captures dict type: {type(captures_dict)}")
            print(
                f"   Captures dict keys: {list(captures_dict.keys()) if isinstance(captures_dict, dict) else 'Not a dict'}"
            )

            if isinstance(captures_dict, dict):
                for key, value in captures_dict.items():
                    print(f"      {key}: {type(value)} = {value}")


if __name__ == "__main__":
    test_capture_api()
