#!/usr/bin/env python3
"""Test more Zig grammar features to understand node types."""

import tree_sitter_zig as ts_zig
from tree_sitter import Language, Parser

# Create a parser
zig_language = Language(ts_zig.language())
parser = Parser(zig_language)

# Test struct and methods
code1 = '''
pub const Vector = struct {
    x: f32,
    y: f32,

    pub fn init(x: f32, y: f32) Vector {
        return .{ .x = x, .y = y };
    }
};

const MyEnum = enum {
    one,
    two,
    three,
};

const MyUnion = union(enum) {
    int: i32,
    float: f32,
};
'''

tree = parser.parse(bytes(code1, "utf8"))
print("Struct/Enum/Union AST:")
for child in tree.root_node.children:
    if child.type != '\n':
        print(f"  {child.type}: {child.text[:50]}")

# Test error handling
code2 = '''
fn mayFail() !void {
    return error.OutOfMemory;
}

fn handleError() void {
    mayFail() catch |err| {
        std.log.err("Error: {}", .{err});
    };

    const result = try mayFail();

    defer cleanup();
    errdefer rollback();
}
'''

tree = parser.parse(bytes(code2, "utf8"))
print("\n\nError handling AST nodes:")
for child in tree.root_node.children:
    if child.type == 'function_declaration':
        print(f"  Function: {child.children[2].text if len(child.children) > 2 else 'unnamed'}")
        # Look for error handling nodes
        def find_error_nodes(node, indent=4):
            if node.type in ['try_expression', 'catch_expression', 'defer_statement', 'errdefer_statement', 'error_union_type']:
                print(" " * indent + f"{node.type}")
            for c in node.children:
                find_error_nodes(c, indent)
        find_error_nodes(child)

# Test async patterns
code3 = '''
async fn fetchData() !void {
    const frame = @frame();
    suspend {}
    resume frame;
}

nosuspend {
    doWork();
}
'''

tree = parser.parse(bytes(code3, "utf8"))
print("\n\nAsync/Suspend/Resume nodes:")

def find_async_nodes(node, indent=0):
    if 'async' in node.type or 'suspend' in node.type or 'resume' in node.type or 'nosuspend' in node.type or 'frame' in str(node.text):
        print(" " * indent + f"{node.type}: {node.text[:40]}")
    for c in node.children:
        find_async_nodes(c, indent + 2)

find_async_nodes(tree.root_node)

# Test inline and comptime
code4 = '''
inline for (items) |item| {
    process(item);
}

inline while (i < 10) : (i += 1) {
    doWork();
}

comptime {
    var x = 10;
}
'''

tree = parser.parse(bytes(code4, "utf8"))
print("\n\nInline/Comptime nodes:")

def find_special_nodes(node, indent=0):
    if 'inline' in node.type or 'comptime' in node.type or node.type in ['for_expression', 'while_expression']:
        print(" " * indent + f"{node.type}: {node.text[:60] if node.text else 'no text'}")
    for c in node.children:
        find_special_nodes(c, indent + 2)

find_special_nodes(tree.root_node)
