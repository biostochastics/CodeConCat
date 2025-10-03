#!/usr/bin/env python3
"""
Test script to understand how to query keyword nodes in GLSL.
"""

from tree_sitter import Language, Parser, Query
import tree_sitter_glsl


def main():
    # Load the language
    lang_ptr = tree_sitter_glsl.language()
    language = Language(lang_ptr)

    # Create parser
    parser = Parser(language)

    # Test uniform declaration
    code = """uniform mat4 model;"""

    tree = parser.parse(bytes(code, "utf8"))
    root = tree.root_node

    # Print tree structure with node types
    def print_node(node, indent=0):
        print("  " * indent + f"{node.type} (named: {node.is_named})")
        for child in node.children:
            print_node(child, indent + 1)

    print("AST for: uniform mat4 model;")
    print_node(root)

    # Try different query patterns
    queries_to_test = [
        # Attempt 1: Match declaration with uniform keyword
        '(declaration) @decl',
        # Attempt 2: Try to match uniform as field
        '(declaration (type_identifier) @type)',
        # Attempt 3: Pattern that should work
        '''
        (declaration
            (type_identifier) @type
            (identifier) @name
        ) @decl
        '''
    ]

    for i, query_str in enumerate(queries_to_test, 1):
        print(f"\nTest Query {i}:")
        print(query_str)
        try:
            query = Query(language, query_str)
            print("Query compiled successfully!")

            # Try to execute query - need to check API
            print("Query object methods:", [m for m in dir(query) if not m.startswith('_')])
        except Exception as e:
            print(f"Query failed: {e}")


if __name__ == "__main__":
    main()
