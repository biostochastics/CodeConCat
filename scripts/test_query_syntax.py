#!/usr/bin/env python3
"""Test query syntax to identify the issue."""

import tree_sitter_zig as ts_zig
from tree_sitter import Language, Parser, Query

# Create a parser
zig_language = Language(ts_zig.language())

# Test each query individually
queries_to_test = {
    "simple_function": "(function_declaration) @function",
    "test_decl": "(test_declaration) @test",
    "variable": "(variable_declaration) @variable",
    "builtin": "(builtin_function) @builtin",
    "error_union": "(error_union_type) @error",
    "try_expr": "(try_expression) @try",
    "comptime_decl": "(comptime_declaration) @comptime",
    "comptime_expr": "(comptime_expression) @comptime",
    "async_expr": "(async_expression) @async",
}

for name, query_str in queries_to_test.items():
    try:
        query = Query(zig_language, query_str)
        print(f"✓ {name}: OK")
    except Exception as e:
        print(f"✗ {name}: {e}")
