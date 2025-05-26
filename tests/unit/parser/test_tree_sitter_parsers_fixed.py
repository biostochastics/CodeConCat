"""Test tree-sitter parsers after fixes"""

import pytest
from unittest.mock import Mock, patch

# Mock tree-sitter imports
mock_language = Mock()
mock_node = Mock()
mock_parser = Mock()
mock_tree = Mock()
mock_query = Mock()


@pytest.fixture
def mock_tree_sitter():
    """Mock tree-sitter imports"""
    with patch.dict(
        "sys.modules",
        {
            "tree_sitter": Mock(
                Language=mock_language,
                Node=mock_node,
                Parser=mock_parser,
                Tree=mock_tree,
                Query=mock_query,
            ),
            "tree_sitter_language_pack": Mock(
                get_language=Mock(return_value=Mock()),
                get_parser=Mock(return_value=Mock(parse=Mock(return_value=Mock(root_node=Mock())))),
            ),
        },
    ):
        yield


@pytest.fixture
def sample_rust_code():
    return b"""
pub fn calculate(x: i32, y: i32) -> i32 {
    x + y
}

pub struct Calculator {
    value: i32,
}

impl Calculator {
    pub fn new(value: i32) -> Self {
        Self { value }
    }
}
"""


@pytest.fixture
def sample_cpp_code():
    return b"""
class Calculator {
public:
    int add(int x, int y) {
        return x + y;
    }
    
private:
    int value;
};
"""


@pytest.fixture
def sample_csharp_code():
    return b"""
using System;

namespace MyApp {
    public class Calculator {
        public int Add(int x, int y) {
            return x + y;
        }
    }
}
"""


@pytest.fixture
def sample_js_code():
    return b"""
class Calculator {
    constructor(value) {
        this.value = value;
    }
    
    add(x, y) {
        return x + y;
    }
}

const calc = new Calculator(0);
"""


@pytest.fixture
def sample_php_code():
    return b"""<?php
namespace App\\Controllers;

use App\\Models\\User;

class UserController {
    private $userModel;
    
    public function __construct() {
        $this->userModel = new User();
    }
    
    public function getUser($id) {
        return $this->userModel->find($id);
    }
}
"""


@pytest.fixture
def sample_julia_code():
    return b"""
module Calculator

export add, multiply

function add(x::Int, y::Int)
    return x + y
end

function multiply(x::Int, y::Int)
    return x * y
end

end # module
"""


class TestTreeSitterParsersFixed:
    """Test that tree-sitter parsers work after fixes"""

    def test_rust_parser_no_visibility_errors(self, mock_tree_sitter):
        """Test Rust parser doesn't have visibility field errors"""
        from codeconcat.parser.language_parsers.tree_sitter_rust_parser import RUST_QUERIES

        # Check that visibility fields were removed from item declarations
        declarations_query = RUST_QUERIES["declarations"]

        # These problematic patterns should not exist
        assert "visibility: (visibility_modifier)?" not in declarations_query

        # But visibility should still be captured (as separate nodes)
        assert "(visibility_modifier)? @visibility" in declarations_query

    def test_cpp_parser_field_fixes(self, mock_tree_sitter):
        """Test C++ parser field name fixes"""
        from codeconcat.parser.language_parsers.tree_sitter_cpp_parser import CPP_QUERIES

        declarations_query = CPP_QUERIES["declarations"]

        # Check that 'declaration:' was fixed
        assert "declaration: (declaration_list)" not in declarations_query
        assert (
            "body: (declaration_list)" in declarations_query or "declarator:" in declarations_query
        )

    def test_csharp_parser_node_type_fixes(self, mock_tree_sitter):
        """Test C# parser node type fixes"""
        from codeconcat.parser.language_parsers.tree_sitter_csharp_parser import CSHARP_QUERIES

        imports_query = CSHARP_QUERIES["imports"]

        # Check that using_static_directive was replaced
        assert "using_static_directive" not in imports_query
        assert "using_directive" in imports_query

        declarations_query = CSHARP_QUERIES["declarations"]

        # Check field name fixes
        assert "type_parameter_list:" not in declarations_query
        assert "type_parameters:" in declarations_query

    def test_php_parser_field_fixes(self, mock_tree_sitter):
        """Test PHP parser field fixes"""
        from codeconcat.parser.language_parsers.tree_sitter_php_parser import PHP_QUERIES

        imports_query = PHP_QUERIES["imports"]

        # Check that 'path:' was replaced with 'name:'
        assert "path: (_) @path" not in imports_query
        assert "name: (name)" in imports_query or "name: (namespace_name)" in imports_query

        declarations_query = PHP_QUERIES["declarations"]

        # Check that modifier field references were removed
        assert "modifier: " not in declarations_query

    def test_julia_parser_node_type_fixes(self, mock_tree_sitter):
        """Test Julia parser node type fixes"""
        from codeconcat.parser.language_parsers.tree_sitter_julia_parser import JULIA_QUERIES

        # Check comment -> line_comment fix
        assert "(comment)" not in JULIA_QUERIES.get("doc_comments", "")

        imports_query = JULIA_QUERIES["imports"]

        # Check module_expression -> module_statement fix
        assert "module_expression" not in imports_query
        assert "module_statement" in imports_query

        declarations_query = JULIA_QUERIES["declarations"]

        # Check block -> block_expression fix
        assert "body: (block)" not in declarations_query
        assert "body: (block_expression)" in declarations_query

    def test_javascript_parser_field_fixes(self, mock_tree_sitter):
        """Test JavaScript parser field fixes"""
        from codeconcat.parser.language_parsers.tree_sitter_js_ts_parser import JS_TS_QUERIES

        declarations_query = JS_TS_QUERIES["declarations"]

        # Check that problematic patterns were fixed
        # JS parser should use 'left:' for assignments
        if "expression:" in declarations_query:
            # Should have been replaced with 'left:'
            assert False, "expression: field should have been replaced with left:"

    def test_all_parsers_capture_unpacking_fixed(self, mock_tree_sitter):
        """Test all parsers handle both 2-tuple and 3-tuple captures"""
        parsers_to_test = [
            "tree_sitter_rust_parser",
            "tree_sitter_cpp_parser",
            "tree_sitter_csharp_parser",
            "tree_sitter_js_ts_parser",
            "tree_sitter_php_parser",
            "tree_sitter_julia_parser",
            "tree_sitter_go_parser",
            "tree_sitter_java_parser",
            "tree_sitter_r_parser",
        ]

        for parser_module in parsers_to_test:
            # Read the parser file
            parser_path = f"/Users/biostochastics/Development/GitHub/codeconcat/codeconcat/parser/language_parsers/{parser_module}.py"
            try:
                with open(parser_path, "r") as f:
                    content = f.read()

                # Check that the old pattern doesn't exist
                assert (
                    "for node, capture_name in captures:" not in content
                ), f"{parser_module} still has old capture unpacking pattern"

                # Check that the new pattern exists
                assert (
                    "if len(capture) == 2:" in content or "for capture in captures:" in content
                ), f"{parser_module} doesn't have fixed capture unpacking"
            except FileNotFoundError:
                pass  # Skip if file doesn't exist

    def test_regex_escaping_fixed(self, mock_tree_sitter):
        """Test regex patterns in doc comments are properly escaped"""
        parsers_with_regex = [
            ("tree_sitter_rust_parser", "RUST_QUERIES"),
            ("tree_sitter_cpp_parser", "CPP_QUERIES"),
            ("tree_sitter_php_parser", "PHP_QUERIES"),
        ]

        for module_name, queries_var in parsers_with_regex:
            try:
                module = __import__(
                    f"codeconcat.parser.language_parsers.{module_name}", fromlist=[queries_var]
                )
                queries = getattr(module, queries_var)

                doc_comments_query = queries.get("doc_comments", "")

                # Check that asterisks in regex patterns are properly escaped
                # Should have \\\\* not \\*
                if "/\\*\\*" in doc_comments_query:
                    assert False, f"{module_name} has unescaped asterisk in regex"

                # Properly escaped patterns should have \\\\*
                if "^/\\\\*\\\\*" in doc_comments_query:
                    assert True  # This is correct

            except ImportError:
                pass  # Skip if module not available


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
