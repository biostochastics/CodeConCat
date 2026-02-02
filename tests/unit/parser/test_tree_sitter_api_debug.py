#!/usr/bin/env python3
"""Debug tree-sitter API to understand capture structure.

This test verifies tree-sitter query API behavior across different versions.
- tree-sitter < 0.24.0: Uses QueryCursor for queries
- tree-sitter >= 0.24.0: Uses Query.captures() and Query.matches() directly
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

# Query class import - guard for potential API differences across tree-sitter versions
try:
    from tree_sitter import Query  # noqa: E402
except ImportError:
    Query = None  # type: ignore[assignment,misc]

# QueryCursor was removed in tree-sitter 0.24.0 - import it if available for backward compatibility
try:
    from tree_sitter import QueryCursor  # noqa: E402
except ImportError:
    QueryCursor = None  # type: ignore[assignment,misc]

from tree_sitter_language_pack import get_language, get_parser  # noqa: E402


# Test Python parser API
@pytest.mark.skipif(
    Query is None or QueryCursor is None,
    reason="Query or QueryCursor not available in this tree-sitter version",
)
def test_capture_api():
    """Test the NEW QueryCursor API for tree-sitter queries."""
    print("Testing tree-sitter NEW QueryCursor API...")

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

    # Use NEW API: Query() constructor instead of language.query()
    query = Query(language, query_str)

    # Test NEW captures() method using QueryCursor
    print("\n1. Testing NEW QueryCursor.captures() method:")
    cursor = QueryCursor(query)
    captures = cursor.captures(root)
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

    # Test NEW matches() method using QueryCursor
    print("\n2. Testing NEW QueryCursor.matches() method:")
    cursor2 = QueryCursor(query)
    matches = cursor2.matches(root)
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

    print("\n✅ All API tests completed successfully!")


if __name__ == "__main__":
    test_capture_api()
