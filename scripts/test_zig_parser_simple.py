#!/usr/bin/env python3
"""Simple test to verify the Zig parser works correctly."""

import sys
sys.path.insert(0, '/Users/biostochastics/Development/GitHub/codeconcat')

from codeconcat.parser.language_parsers.tree_sitter_zig_parser import TreeSitterZigParser

# Create parser
parser = TreeSitterZigParser()

# Test simple function
code = '''
pub fn add(a: i32, b: i32) i32 {
    return a + b;
}
'''

print("Testing simple function parsing...")
declarations = parser.parse(code)
print(f"Found {len(declarations)} declarations")

for decl in declarations:
    print(f"  - {decl.kind}: {decl.name} - {decl.signature}")

# Test with more features
code2 = '''
const std = @import("std");

pub fn main() !void {
    const allocator = std.heap.page_allocator;

    comptime {
        const x = 10;
    }

    try doSomething();
}

test "example" {
    const x = 5;
}
'''

print("\n\nTesting complex code...")
declarations2 = parser.parse(code2)
print(f"Found {len(declarations2)} declarations")

for decl in declarations2:
    print(f"  - {decl.kind}: {decl.name}")

features = parser.get_language_features()
print(f"\nFeatures detected:")
for k, v in features.items():
    if isinstance(v, bool) and v:
        print(f"  {k}: {v}")
    elif isinstance(v, int) and v > 0:
        print(f"  {k}: {v}")
