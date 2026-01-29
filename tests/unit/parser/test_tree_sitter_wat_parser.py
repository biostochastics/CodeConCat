"""Unit tests for TreeSitterWatParser (WebAssembly Text format parser)."""

import pytest

from codeconcat.parser.error_handling import ParserInitializationError
from codeconcat.parser.language_parsers.tree_sitter_wat_parser import TreeSitterWatParser


@pytest.fixture
def wat_parser():
    """Create a WAT parser, skipping if grammar unavailable."""
    try:
        return TreeSitterWatParser()
    except ParserInitializationError as e:
        # WAT grammar may not be available in CI environments
        # where it needs to be built from source (requires git clone)
        pytest.skip(f"WAT parser unavailable: {e}")


class TestTreeSitterWatParser:
    """Test cases for WAT parser functionality."""

    def test_parser_initialization(self, wat_parser):
        """Test that the WAT parser initializes correctly."""
        parser = wat_parser
        assert parser is not None
        assert parser.parser is not None
        assert parser.ts_language is not None

    def test_parse_simple_module(self, wat_parser):
        """Test parsing a simple WAT module."""
        parser = wat_parser
        wat_code = """
(module
  (func $add (param i32 i32) (result i32)
    local.get 0
    local.get 1
    i32.add
  )
)
"""
        result = parser.parse(wat_code)
        assert result is not None
        assert result.error is None
        assert len(result.declarations) > 0

        # Should find the module and function
        kinds = [d.kind for d in result.declarations]
        assert "module" in kinds
        assert "function" in kinds

        # Check function declaration
        func_decls = [d for d in result.declarations if d.kind == "function"]
        assert len(func_decls) == 1
        assert func_decls[0].name == "add"
        assert func_decls[0].signature is not None
        assert "i32" in func_decls[0].signature

    def test_parse_imports(self, wat_parser):
        """Test parsing import statements."""
        parser = wat_parser
        wat_code = """
(module
  (import "env" "memory" (memory 1))
  (import "env" "print" (func $print (param i32)))
  (import "wasi_snapshot_preview1" "fd_write" (func $fd_write (param i32 i32 i32 i32) (result i32)))
)
"""
        result = parser.parse(wat_code)
        assert result is not None
        assert len(result.imports) == 3
        assert "env.memory" in result.imports
        assert "env.print" in result.imports
        assert "wasi_snapshot_preview1.fd_write" in result.imports

    def test_parse_exports(self, wat_parser):
        """Test parsing export statements."""
        parser = wat_parser
        wat_code = """
(module
  (func $add (param i32 i32) (result i32)
    local.get 0
    local.get 1
    i32.add
  )
  (export "add" (func $add))
  (export "memory" (memory 0))
)
"""
        result = parser.parse(wat_code)
        assert result is not None

        # Exports are stored as declarations with kind "export"
        export_decls = [d for d in result.declarations if d.kind == "export"]
        assert len(export_decls) == 2
        export_names = [d.name for d in export_decls]
        assert "add" in export_names
        assert "memory" in export_names

    def test_parse_function_with_params_and_results(self, wat_parser):
        """Test parsing functions with parameters and result types."""
        parser = wat_parser
        wat_code = """
(module
  (func $compute (param i32 f32) (result i64)
    i64.const 42
  )
)
"""
        result = parser.parse(wat_code)
        assert result is not None

        func_decls = [d for d in result.declarations if d.kind == "function"]
        assert len(func_decls) == 1
        func = func_decls[0]
        assert func.name == "compute"
        assert func.signature is not None
        assert "i32" in func.signature
        assert "f32" in func.signature
        assert "i64" in func.signature

    def test_parse_type_definitions(self, wat_parser):
        """Test parsing type definitions."""
        parser = wat_parser
        wat_code = """
(module
  (type $callback (func (param i32) (result i32)))
  (type $printer (func (param i32)))
)
"""
        result = parser.parse(wat_code)
        assert result is not None

        type_decls = [d for d in result.declarations if d.kind == "type"]
        assert len(type_decls) == 2
        type_names = [d.name for d in type_decls]
        assert "callback" in type_names
        assert "printer" in type_names

    def test_parse_table_definitions(self, wat_parser):
        """Test parsing table definitions."""
        parser = wat_parser
        wat_code = """
(module
  (table $indirect 10 funcref)
  (table 5 10 externref)
)
"""
        result = parser.parse(wat_code)
        assert result is not None

        table_decls = [d for d in result.declarations if d.kind == "table"]
        assert len(table_decls) >= 1
        # Verify both named and anonymous tables
        named_tables = [d for d in table_decls if d.name != "(table)"]
        assert len(named_tables) >= 1
        assert named_tables[0].name == "indirect"
        # Also verify anonymous table
        anonymous_tables = [d for d in table_decls if d.name == "(table)"]
        assert len(anonymous_tables) >= 1

    def test_parse_global_definitions(self, wat_parser):
        """Test parsing global variable definitions."""
        parser = wat_parser
        wat_code = """
(module
  (global $counter (mut i32) (i32.const 0))
  (global $pi f32 (f32.const 3.14159))
)
"""
        result = parser.parse(wat_code)
        assert result is not None

        global_decls = [d for d in result.declarations if d.kind == "global"]
        assert len(global_decls) == 2
        global_names = [d.name for d in global_decls]
        assert "counter" in global_names
        assert "pi" in global_names

    def test_parse_anonymous_functions(self, wat_parser):
        """Test parsing functions without explicit names."""
        parser = wat_parser
        wat_code = """
(module
  (func (param i32) (result i32)
    local.get 0
  )
)
"""
        result = parser.parse(wat_code)
        assert result is not None

        func_decls = [d for d in result.declarations if d.kind == "function"]
        assert len(func_decls) == 1
        # Anonymous functions get a default name
        assert func_decls[0].name == "(function)"

    def test_parse_complex_module(self, wat_parser):
        """Test parsing a complex module with multiple features."""
        parser = wat_parser
        wat_code = """
(module
  (import "env" "log" (func $log (param i32)))
  (type $binop (func (param i32 i32) (result i32)))
  (memory 1)
  (table 10 funcref)
  (global $g (mut i32) (i32.const 0))

  (func $add (type $binop)
    local.get 0
    local.get 1
    i32.add
  )

  (func $main (export "main")
    i32.const 5
    call $log
  )

  (export "add" (func $add))
)
"""
        result = parser.parse(wat_code)
        assert result is not None
        assert result.error is None

        # Check imports
        assert len(result.imports) == 1
        assert "env.log" in result.imports

        # Check declarations
        assert len(result.declarations) > 0

        # Check we found various declaration types
        kinds = {d.kind for d in result.declarations}
        assert "module" in kinds
        assert "type" in kinds
        assert "function" in kinds
        assert "global" in kinds
        assert "export" in kinds

        # Check specific functions
        func_decls = [d for d in result.declarations if d.kind == "function"]
        func_names = [d.name for d in func_decls]
        assert "add" in func_names
        assert "main" in func_names

    def test_parse_empty_module(self, wat_parser):
        """Test parsing an empty module."""
        parser = wat_parser
        wat_code = "(module)"

        result = parser.parse(wat_code)
        assert result is not None
        assert result.error is None

        # Should at least find the module declaration
        module_decls = [d for d in result.declarations if d.kind == "module"]
        assert len(module_decls) == 1

    def test_parse_malformed_wat(self, wat_parser):
        """Test parsing malformed WAT code."""
        parser = wat_parser
        wat_code = "(module (func $broken"

        result = parser.parse(wat_code)
        assert result is not None
        # Parser should handle gracefully, may or may not have error
        # Mainly checking it doesn't crash

    def test_parse_multiline_function(self, wat_parser):
        """Test parsing a function with complex body."""
        parser = wat_parser
        wat_code = """
(module
  (func $factorial (param $n i32) (result i32)
    (local $result i32)
    (local $i i32)
    i32.const 1
    local.set $result
    i32.const 1
    local.set $i
    (block $break
      (loop $continue
        local.get $i
        local.get $n
        i32.gt_u
        br_if $break
        local.get $result
        local.get $i
        i32.mul
        local.set $result
        local.get $i
        i32.const 1
        i32.add
        local.set $i
        br $continue
      )
    )
    local.get $result
  )
)
"""
        result = parser.parse(wat_code)
        assert result is not None
        assert result.error is None

        func_decls = [d for d in result.declarations if d.kind == "function"]
        assert len(func_decls) == 1
        assert func_decls[0].name == "factorial"
        # Check that line numbers are captured
        assert func_decls[0].start_line > 0
        assert func_decls[0].end_line > func_decls[0].start_line

    def test_line_numbers(self, wat_parser):
        """Test that line numbers are correctly captured."""
        parser = wat_parser
        wat_code = """(module
  (func $first
    nop
  )
  (func $second
    nop
  )
)"""
        result = parser.parse(wat_code)
        assert result is not None

        # Check that declarations have valid line numbers
        for decl in result.declarations:
            assert decl.start_line >= 0
            assert decl.end_line >= decl.start_line

    def test_parse_wasi_program(self, wat_parser):
        """Test parsing a WASI program with typical imports."""
        parser = wat_parser
        wat_code = """
(module
  (import "wasi_snapshot_preview1" "fd_write"
    (func $fd_write (param i32 i32 i32 i32) (result i32)))
  (import "wasi_snapshot_preview1" "proc_exit"
    (func $proc_exit (param i32)))

  (memory 1)
  (export "memory" (memory 0))

  (func $_start (export "_start")
    i32.const 0
    call $proc_exit
  )
)
"""
        result = parser.parse(wat_code)
        assert result is not None
        assert result.error is None

        # Check WASI imports
        assert len(result.imports) == 2
        assert "wasi_snapshot_preview1.fd_write" in result.imports
        assert "wasi_snapshot_preview1.proc_exit" in result.imports

        # Check function
        func_decls = [d for d in result.declarations if d.kind == "function"]
        assert any(d.name == "_start" for d in func_decls)
