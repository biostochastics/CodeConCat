# tests/unit/parser/test_tree_sitter_zig_parser.py

"""
Comprehensive tests for TreeSitterZigParser covering:
- Basic parsing functionality
- Comptime blocks and expressions
- Async/await patterns
- Error handling (try/catch/error unions)
- Allocator usage patterns
- Test block detection
- Builtin functions
"""

import pytest
from unittest.mock import Mock, patch

from codeconcat.parser.language_parsers.tree_sitter_zig_parser import TreeSitterZigParser


class TestTreeSitterZigParser:
    """Test suite for Zig parser functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = TreeSitterZigParser()

    def test_parser_initialization(self):
        """Test that the parser initializes correctly."""
        assert self.parser is not None
        assert self.parser.language_name == "zig"
        assert hasattr(self.parser, 'comptime_blocks')
        assert hasattr(self.parser, 'async_functions')
        assert hasattr(self.parser, 'error_handlers')
        assert hasattr(self.parser, 'allocator_usage')
        assert hasattr(self.parser, 'test_blocks')

    def test_parse_simple_function(self):
        """Test parsing a simple Zig function."""
        code = '''
pub fn add(a: i32, b: i32) i32 {
    return a + b;
}
'''
        declarations = self.parser.parse(code)

        assert len(declarations) == 1
        func = declarations[0]
        assert func.kind == "function"
        assert func.name == "add"
        assert "i32" in func.signature

    def test_parse_async_function(self):
        """Test parsing async functions."""
        code = '''
pub async fn fetchData(url: []const u8) !Response {
    const response = await httpClient.get(url);
    return response;
}
'''
        declarations = self.parser.parse(code)

        assert len(declarations) >= 1
        func = declarations[0]
        assert func.kind == "function"
        assert func.name == "fetchData"

        # Check async features detected
        features = self.parser.get_language_features()
        assert features["has_async"] == True

    def test_parse_comptime_blocks(self):
        """Test parsing comptime blocks and expressions."""
        code = '''
const std = @import("std");

pub fn genericArray(comptime T: type, comptime size: usize) type {
    return struct {
        items: [size]T,

        comptime {
            if (size == 0) {
                @compileError("Array size must be greater than 0");
            }
        }

        pub fn init() @This() {
            return .{ .items = [_]T{0} ** size };
        }
    };
}

test "comptime evaluation" {
    const Array10 = genericArray(i32, 10);
    comptime {
        const size = 10;
        std.debug.assert(size > 0);
    }
}
'''
        declarations = self.parser.parse(code)

        # Should find function and test
        assert len(declarations) >= 2

        # Check comptime features detected
        features = self.parser.get_language_features()
        assert features["has_comptime"] == True
        assert features["comptime_blocks"] > 0

    def test_parse_error_handling(self):
        """Test parsing error unions and error handling patterns."""
        code = '''
const FileError = error{
    NotFound,
    PermissionDenied,
    OutOfMemory,
};

pub fn readFile(path: []const u8) ![]u8 {
    const file = try std.fs.openFileAbsolute(path, .{});
    defer file.close();

    const content = file.readToEndAlloc(allocator, 1024 * 1024) catch |err| {
        std.log.err("Failed to read file: {}", .{err});
        return err;
    };

    return content;
}

pub fn safeReadFile(path: []const u8) []u8 {
    return readFile(path) catch |err| switch (err) {
        error.NotFound => return "File not found",
        error.PermissionDenied => return "Permission denied",
        else => return "Unknown error",
    };
}
'''
        declarations = self.parser.parse(code)

        # Should find both functions
        func_names = [d.name for d in declarations if d.kind == "function"]
        assert "readFile" in func_names
        assert "safeReadFile" in func_names

        # Check error handling features detected
        features = self.parser.get_language_features()
        assert features["error_handlers"] > 0

    def test_parse_allocator_patterns(self):
        """Test detection of allocator usage patterns."""
        code = '''
const std = @import("std");

pub fn createBuffer(allocator: std.mem.Allocator, size: usize) ![]u8 {
    const buffer = try allocator.alloc(u8, size);
    errdefer allocator.free(buffer);

    // Initialize buffer
    for (buffer) |*byte| {
        byte.* = 0;
    }

    return buffer;
}

pub fn processWithArena(data: []const u8) !void {
    var arena = std.heap.ArenaAllocator.init(std.heap.page_allocator);
    defer arena.deinit();

    const allocator = arena.allocator();
    const copy = try allocator.dupe(u8, data);

    // Process data...
}
'''
        declarations = self.parser.parse(code)

        # Should find both functions
        assert len(declarations) >= 2

        # Check allocator usage detected
        features = self.parser.get_language_features()
        assert features["uses_allocators"] == True
        assert features["allocator_usage"] > 0

    def test_parse_test_blocks(self):
        """Test parsing of test blocks."""
        code = '''
const std = @import("std");
const testing = std.testing;

test "basic addition" {
    try testing.expectEqual(@as(i32, 42), add(40, 2));
}

test "string operations" {
    const str = "hello";
    try testing.expect(str.len == 5);
}

test {
    // Anonymous test
    try testing.expect(true);
}
'''
        declarations = self.parser.parse(code)

        # Should find all test blocks
        test_decls = [d for d in declarations if d.kind == "test"]
        assert len(test_decls) >= 3

        # Check test features detected
        features = self.parser.get_language_features()
        assert features["has_tests"] == True
        assert features["test_blocks"] >= 3

    def test_parse_struct_with_methods(self):
        """Test parsing structs with methods."""
        code = '''
pub const Vector = struct {
    x: f32,
    y: f32,
    z: f32,

    pub fn init(x: f32, y: f32, z: f32) Vector {
        return .{ .x = x, .y = y, .z = z };
    }

    pub fn dot(self: Vector, other: Vector) f32 {
        return self.x * other.x + self.y * other.y + self.z * other.z;
    }

    pub fn length(self: Vector) f32 {
        return @sqrt(self.dot(self));
    }
};
'''
        declarations = self.parser.parse(code)

        # Should find struct and its methods
        assert any(d.name == "Vector" and d.kind == "struct" for d in declarations)

        # Methods inside struct should also be detected
        method_names = [d.name for d in declarations if d.kind == "function"]
        assert "init" in method_names
        assert "dot" in method_names
        assert "length" in method_names

    def test_parse_union_and_enum(self):
        """Test parsing unions and enums."""
        code = '''
pub const TokenType = enum {
    identifier,
    number,
    string,
    keyword,
    operator,
};

pub const Value = union(enum) {
    int: i64,
    float: f64,
    string: []const u8,
    boolean: bool,
    nil: void,

    pub fn isNumber(self: Value) bool {
        return switch (self) {
            .int, .float => true,
            else => false,
        };
    }
};
'''
        declarations = self.parser.parse(code)

        # Should find enum and union
        type_names = [d.name for d in declarations if d.kind in ["enum", "union"]]
        assert "TokenType" in type_names
        assert "Value" in type_names

    def test_parse_builtin_functions(self):
        """Test detection of builtin function calls."""
        code = '''
const std = @import("std");
const builtin = @import("builtin");

pub fn typeInfo(comptime T: type) void {
    const info = @typeInfo(T);
    const name = @typeName(T);
    const size = @sizeOf(T);
    const alignment = @alignOf(T);

    if (@TypeOf(info) != std.builtin.Type) {
        @compileError("Invalid type info");
    }
}

pub fn panicHandler(msg: []const u8) noreturn {
    @panic(msg);
}
'''
        declarations = self.parser.parse(code)

        # Check builtin calls detected
        features = self.parser.get_language_features()
        assert features["builtin_calls"] > 0

    def test_parse_inline_assembly(self):
        """Test parsing inline assembly blocks."""
        code = '''
pub fn enableInterrupts() void {
    asm volatile ("sti");
}

pub fn disableInterrupts() void {
    asm volatile ("cli");
}

pub fn cpuid(leaf: u32) u32 {
    return asm volatile (
        "cpuid"
        : [_] "={eax}" (-> u32),
        : [_] "{eax}" (leaf),
        : "ebx", "ecx", "edx"
    );
}
'''
        declarations = self.parser.parse(code)

        # Should find functions with inline assembly
        func_names = [d.name for d in declarations if d.kind == "function"]
        assert "enableInterrupts" in func_names
        assert "disableInterrupts" in func_names
        assert "cpuid" in func_names

    def test_parse_generic_functions(self):
        """Test parsing generic functions with type parameters."""
        code = '''
pub fn swap(comptime T: type, a: *T, b: *T) void {
    const temp = a.*;
    a.* = b.*;
    b.* = temp;
}

pub fn ArrayList(comptime T: type) type {
    return struct {
        items: []T,
        capacity: usize,
        allocator: std.mem.Allocator,

        pub fn init(allocator: std.mem.Allocator) @This() {
            return .{
                .items = &[_]T{},
                .capacity = 0,
                .allocator = allocator,
            };
        }

        pub fn append(self: *@This(), item: T) !void {
            // Implementation
        }
    };
}
'''
        declarations = self.parser.parse(code)

        # Should find generic functions
        func_names = [d.name for d in declarations if d.kind == "function"]
        assert "swap" in func_names
        assert "ArrayList" in func_names

    def test_parse_defer_and_errdefer(self):
        """Test parsing defer and errdefer statements."""
        code = '''
const std = @import("std");

pub fn processFile(path: []const u8) !void {
    const file = try std.fs.openFileAbsolute(path, .{});
    defer file.close();

    const allocator = std.heap.page_allocator;
    const buffer = try allocator.alloc(u8, 1024);
    defer allocator.free(buffer);
    errdefer std.log.err("Failed to process file", .{});

    // Process file content
    _ = try file.read(buffer);
}
'''
        declarations = self.parser.parse(code)

        # Should find function with defer/errdefer
        assert any(d.name == "processFile" for d in declarations)

        # Check error handling features
        features = self.parser.get_language_features()
        assert features["error_handlers"] > 0

    def test_parse_doc_comments(self):
        """Test extraction of doc comments."""
        code = '''
/// Adds two numbers together.
/// This is a simple addition function.
pub fn add(a: i32, b: i32) i32 {
    return a + b;
}

//! Module-level documentation
//! This module provides math utilities.

/// A 3D vector structure.
/// Used for geometric calculations.
pub const Vector3 = struct {
    x: f32,
    y: f32,
    z: f32,
};
'''
        declarations = self.parser.parse(code)

        # Check for doc comments
        func = next((d for d in declarations if d.name == "add"), None)
        assert func is not None
        assert len(func.docstring) > 0

        struct = next((d for d in declarations if d.name == "Vector3"), None)
        assert struct is not None

    def test_parse_packed_struct(self):
        """Test parsing packed structs."""
        code = '''
pub const Flags = packed struct {
    carry: bool,
    zero: bool,
    negative: bool,
    overflow: bool,
    _reserved: u4 = 0,
};

pub const Color = packed struct {
    r: u8,
    g: u8,
    b: u8,
    a: u8,

    pub fn fromRgb(r: u8, g: u8, b: u8) Color {
        return .{ .r = r, .g = g, .b = b, .a = 255 };
    }
};
'''
        declarations = self.parser.parse(code)

        # Should find packed structs
        struct_names = [d.name for d in declarations if d.kind == "struct"]
        assert "Flags" in struct_names
        assert "Color" in struct_names

    def test_parse_extern_declarations(self):
        """Test parsing extern declarations."""
        code = '''
pub extern "c" fn printf(format: [*:0]const u8, ...) c_int;
pub extern "c" fn malloc(size: usize) ?*anyopaque;
pub extern "c" fn free(ptr: ?*anyopaque) void;

extern "kernel32" fn GetCurrentProcessId() callconv(std.os.windows.WINAPI) u32;
'''
        declarations = self.parser.parse(code)

        # Should find extern functions
        func_names = [d.name for d in declarations if d.kind == "function"]
        assert "printf" in func_names
        assert "malloc" in func_names
        assert "free" in func_names

    def test_parse_inline_for(self):
        """Test parsing inline for loops (comptime iteration)."""
        code = '''
const std = @import("std");

pub fn tupleSum(tuple: anytype) i32 {
    var sum: i32 = 0;
    inline for (tuple) |item| {
        sum += @intCast(item);
    }
    return sum;
}

pub fn generateArray(comptime size: usize) [size]u8 {
    var array: [size]u8 = undefined;
    inline for (&array, 0..) |*item, i| {
        item.* = @intCast(i);
    }
    return array;
}
'''
        declarations = self.parser.parse(code)

        # Check comptime features for inline loops
        features = self.parser.get_language_features()
        assert features["has_comptime"] == True

    def test_parse_suspend_resume(self):
        """Test parsing suspend and resume expressions."""
        code = '''
const std = @import("std");

var frame: anyframe = undefined;

pub fn asyncFunction() void {
    suspend {
        frame = @frame();
    }
    // Do async work
}

pub fn resumeFunction() void {
    resume frame;
}

pub fn nosuspendFunction() void {
    nosuspend {
        // Code that should not suspend
        performCriticalOperation();
    }
}
'''
        declarations = self.parser.parse(code)

        # Check async features detected
        features = self.parser.get_language_features()
        assert features["has_async"] == True

    def test_parse_complex_error_union(self):
        """Test parsing complex error union types."""
        code = '''
const FileError = error{
    NotFound,
    PermissionDenied,
};

const NetworkError = error{
    Timeout,
    ConnectionRefused,
};

pub fn fetchFileFromNetwork(url: []const u8) (FileError || NetworkError)![]u8 {
    // Implementation
    return error.NotFound;
}

pub fn handleResult(result: anyerror!i32) void {
    const value = result catch |err| {
        std.log.err("Error: {}", .{err});
        return;
    };
    std.log.info("Value: {}", .{value});
}
'''
        declarations = self.parser.parse(code)

        # Check error handling features
        features = self.parser.get_language_features()
        assert features["error_handlers"] > 0

    def test_empty_file(self):
        """Test parsing an empty file."""
        code = ""
        declarations = self.parser.parse(code)
        assert declarations == []

    def test_malformed_code(self):
        """Test parsing malformed code."""
        code = '''
pub fn broken(a: i32, b: {
    // Missing closing brace and return type
'''
        # Should not crash, just return what it can parse
        declarations = self.parser.parse(code)
        # May or may not find the broken function depending on recovery

    def test_get_language_features(self):
        """Test the get_language_features method."""
        code = '''
const std = @import("std");

pub async fn asyncFunc() !void {
    comptime {
        const x = 10;
    }
    const allocator = std.heap.page_allocator;
    const data = try allocator.alloc(u8, 100);
    defer allocator.free(data);
}

test "feature test" {
    try std.testing.expect(true);
}
'''
        self.parser.parse(code)
        features = self.parser.get_language_features()

        assert "comptime_blocks" in features
        assert "async_functions" in features
        assert "error_handlers" in features
        assert "allocator_usage" in features
        assert "test_blocks" in features
        assert "has_comptime" in features
        assert "has_async" in features
        assert "has_tests" in features
        assert "uses_allocators" in features
