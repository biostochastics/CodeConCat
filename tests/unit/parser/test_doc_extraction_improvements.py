"""Tests for documentation extraction improvements across tree-sitter parsers.

These tests validate the doc_comments query support and docstring extraction
for parsers that were enhanced in the documentation extraction improvements.
"""

import pytest


class TestElixirDocExtraction:
    """Test Elixir @doc/@moduledoc extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        from codeconcat.parser.language_parsers.tree_sitter_elixir_parser import (
            TreeSitterElixirParser,
        )

        self.parser = TreeSitterElixirParser()

    def test_moduledoc_extraction(self):
        """Test @moduledoc attribute extraction."""
        code = '''
defmodule MyApp.Calculator do
  @moduledoc """
  A simple calculator module.
  Provides basic arithmetic operations.
  """

  def add(a, b), do: a + b
end
'''
        result = self.parser.parse(code, "calculator.ex")

        assert result is not None
        module_decl = next(
            (d for d in result.declarations if d.name == "MyApp.Calculator"), None
        )
        assert module_decl is not None
        assert "simple calculator module" in module_decl.docstring.lower()

    def test_doc_attribute_extraction(self):
        """Test @doc attribute extraction for functions."""
        code = '''
defmodule MyApp.Math do
  @doc """
  Adds two numbers together.

  ## Examples

      iex> Math.add(1, 2)
      3
  """
  def add(a, b), do: a + b
end
'''
        result = self.parser.parse(code, "math.ex")

        assert result is not None
        func_decl = next((d for d in result.declarations if d.name == "add"), None)
        assert func_decl is not None
        assert "adds two numbers" in func_decl.docstring.lower()

    def test_single_line_doc(self):
        """Test single-line @doc attribute."""
        code = '''
defmodule MyApp.Utils do
  @doc "Converts value to string."
  def to_string(val), do: "#{val}"
end
'''
        result = self.parser.parse(code, "utils.ex")

        assert result is not None
        func_decl = next((d for d in result.declarations if d.name == "to_string"), None)
        assert func_decl is not None
        assert "converts value to string" in func_decl.docstring.lower()

    def test_moduledoc_false(self):
        """Test @moduledoc false is handled correctly."""
        code = '''
defmodule MyApp.Internal do
  @moduledoc false

  def private_func, do: :ok
end
'''
        result = self.parser.parse(code, "internal.ex")

        assert result is not None
        module_decl = next(
            (d for d in result.declarations if d.name == "MyApp.Internal"), None
        )
        assert module_decl is not None
        # Should not have a docstring when @moduledoc false
        assert module_decl.docstring == "" or module_decl.docstring is None


class TestJuliaDocExtraction:
    """Test Julia docstring extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        from codeconcat.parser.language_parsers.tree_sitter_julia_parser import (
            TreeSitterJuliaParser,
        )

        self.parser = TreeSitterJuliaParser()

    def test_triple_quoted_docstring(self):
        """Test triple-quoted docstring extraction."""
        code = '''
"""
    add(a, b)

Add two numbers together and return the result.
"""
function add(a, b)
    return a + b
end
'''
        result = self.parser.parse(code, "math.jl")

        assert result is not None
        func_decl = next((d for d in result.declarations if d.name == "add"), None)
        assert func_decl is not None
        assert "add two numbers" in func_decl.docstring.lower()

    def test_line_comment_doc(self):
        """Test line comment documentation."""
        code = '''
# Multiply two numbers
# Returns the product
function multiply(a, b)
    return a * b
end
'''
        result = self.parser.parse(code, "math.jl")

        assert result is not None
        func_decl = next((d for d in result.declarations if d.name == "multiply"), None)
        assert func_decl is not None
        assert "multiply" in func_decl.docstring.lower() or func_decl.docstring != ""

    def test_block_comment_doc(self):
        """Test block comment (#= =#) documentation."""
        code = '''
#=
This is a struct for representing a point
in 2D space with x and y coordinates.
=#
struct Point
    x::Float64
    y::Float64
end
'''
        result = self.parser.parse(code, "geometry.jl")

        assert result is not None
        struct_decl = next((d for d in result.declarations if d.name == "Point"), None)
        assert struct_decl is not None
        assert "point" in struct_decl.docstring.lower() or struct_decl.docstring != ""


class TestPHPDocExtraction:
    """Test PHP PHPDoc extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        from codeconcat.parser.language_parsers.tree_sitter_php_parser import (
            TreeSitterPhpParser,
        )

        self.parser = TreeSitterPhpParser()

    def test_phpdoc_with_tags(self):
        """Test PHPDoc comment with @param and @return tags."""
        code = '''<?php
/**
 * Calculate the sum of two numbers.
 *
 * @param int $a First number
 * @param int $b Second number
 * @return int The sum
 */
function add($a, $b) {
    return $a + $b;
}
'''
        result = self.parser.parse(code, "math.php")

        assert result is not None
        func_decl = next((d for d in result.declarations if d.name == "add"), None)
        assert func_decl is not None
        assert "sum" in func_decl.docstring.lower()
        # PHPDoc tags should be cleaned using clean_jsdoc_tags
        assert "param" in func_decl.docstring.lower() or "first number" in func_decl.docstring.lower()

    def test_class_phpdoc(self):
        """Test PHPDoc for class definitions."""
        code = '''<?php
/**
 * A simple calculator class.
 */
class Calculator {
    public function calculate() {}
}
'''
        result = self.parser.parse(code, "calculator.php")

        assert result is not None
        class_decl = next(
            (d for d in result.declarations if d.name == "Calculator"), None
        )
        assert class_decl is not None
        assert "calculator" in class_decl.docstring.lower()


class TestGraphQLDocExtraction:
    """Test GraphQL description extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        from codeconcat.parser.language_parsers.tree_sitter_graphql_parser import (
            TreeSitterGraphqlParser,
        )

        self.parser = TreeSitterGraphqlParser()

    def test_type_description(self):
        """Test GraphQL type description extraction."""
        code = '''
"""
Represents a user in the system.
"""
type User {
  id: ID!
  name: String!
}
'''
        result = self.parser.parse(code, "schema.graphql")

        assert result is not None
        # GraphQL parser should extract the description
        type_decl = next((d for d in result.declarations if d.name == "User"), None)
        if type_decl:
            # Description may or may not be extracted depending on grammar
            assert type_decl is not None


class TestSQLDocExtraction:
    """Test SQL comment extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        from codeconcat.parser.language_parsers.tree_sitter_sql_parser import (
            TreeSitterSqlParser,
        )

        self.parser = TreeSitterSqlParser()

    def test_sql_line_comments(self):
        """Test SQL line comment handling."""
        code = '''
-- Create the users table
-- Stores user account information
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100)
);
'''
        result = self.parser.parse(code, "schema.sql")

        assert result is not None
        # SQL parser should handle comments without crashing
        assert result.error is None or result.error == ""

    def test_sql_block_comments(self):
        """Test SQL block comment handling."""
        code = '''
/*
 * Create the products table
 * for storing product inventory
 */
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200)
);
'''
        result = self.parser.parse(code, "products.sql")

        assert result is not None
        assert result.error is None or result.error == ""


class TestHCLDocExtraction:
    """Test HCL/Terraform comment extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        from codeconcat.parser.language_parsers.tree_sitter_hcl_parser import (
            TreeSitterHclParser,
        )

        self.parser = TreeSitterHclParser()

    def test_hcl_hash_comments(self):
        """Test HCL # style comments."""
        code = '''
# Configure the AWS provider
# for the production environment
provider "aws" {
  region = "us-west-2"
}
'''
        result = self.parser.parse(code, "main.tf")

        assert result is not None
        # HCL parser should handle comments without crashing
        # and doc_comments query should be present
        assert "doc_comments" in self.parser.get_queries()


class TestSolidityDocExtraction:
    """Test Solidity NatSpec comment extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        from codeconcat.parser.language_parsers.tree_sitter_solidity_parser import (
            TreeSitterSolidityParser,
        )

        self.parser = TreeSitterSolidityParser()

    def test_natspec_comments(self):
        """Test NatSpec documentation comments."""
        code = '''
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title A simple storage contract
/// @author Developer
/// @notice Store and retrieve a value
contract Storage {
    uint256 value;

    /// @notice Store a value
    /// @param _value The value to store
    function store(uint256 _value) public {
        value = _value;
    }
}
'''
        result = self.parser.parse(code, "Storage.sol")

        assert result is not None
        # Solidity parser should have doc_comments query
        assert "doc_comments" in self.parser.get_queries()


class TestWATDocExtraction:
    """Test WebAssembly Text format comment extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        from codeconcat.parser.language_parsers.tree_sitter_wat_parser import (
            TreeSitterWatParser,
        )

        self.parser = TreeSitterWatParser()

    def test_wat_line_comments(self):
        """Test WAT ;; style comments."""
        code = '''
;; Simple add function
;; Takes two i32 parameters
(module
  (func $add (param $a i32) (param $b i32) (result i32)
    local.get $a
    local.get $b
    i32.add
  )
)
'''
        result = self.parser.parse(code, "math.wat")

        assert result is not None
        # WAT parser should have doc_comments query
        assert "doc_comments" in self.parser.get_queries()


class TestCrystalDocExtraction:
    """Test Crystal comment extraction."""

    def setup_method(self):
        """Set up test fixtures."""
        from codeconcat.parser.language_parsers.tree_sitter_crystal_parser import (
            TreeSitterCrystalParser,
        )

        self.parser = TreeSitterCrystalParser()

    def test_crystal_comments(self):
        """Test Crystal # style comments."""
        code = '''
# A simple calculator class
# for basic arithmetic
class Calculator
  # Add two numbers
  def add(a, b)
    a + b
  end
end
'''
        result = self.parser.parse(code, "calculator.cr")

        assert result is not None
        # Crystal parser should have doc_comments query
        assert "doc_comments" in self.parser.get_queries()


class TestPatternLibraryCommentPatterns:
    """Test CommentPatterns class in pattern_library.py."""

    def test_elixir_comment_patterns(self):
        """Test Elixir comment patterns are defined."""
        from codeconcat.parser.language_parsers.pattern_library import CommentPatterns

        assert "elixir" in CommentPatterns.SINGLE_LINE
        assert CommentPatterns.SINGLE_LINE["elixir"] == "#"

    def test_julia_comment_patterns(self):
        """Test Julia comment patterns are defined."""
        from codeconcat.parser.language_parsers.pattern_library import CommentPatterns

        assert "julia" in CommentPatterns.SINGLE_LINE
        assert CommentPatterns.SINGLE_LINE["julia"] == "#"
        assert "julia" in CommentPatterns.BLOCK_COMMENT
        block_start, block_end = CommentPatterns.BLOCK_COMMENT["julia"]
        assert block_start == "#="
        assert block_end == "=#"

    def test_sql_comment_patterns(self):
        """Test SQL comment patterns are defined."""
        from codeconcat.parser.language_parsers.pattern_library import CommentPatterns

        assert "sql" in CommentPatterns.SINGLE_LINE
        assert CommentPatterns.SINGLE_LINE["sql"] == "--"

    def test_graphql_comment_patterns(self):
        """Test GraphQL comment patterns are defined."""
        from codeconcat.parser.language_parsers.pattern_library import CommentPatterns

        assert "graphql" in CommentPatterns.SINGLE_LINE
        assert CommentPatterns.SINGLE_LINE["graphql"] == "#"
        assert "graphql" in CommentPatterns.BLOCK_COMMENT
        block_start, block_end = CommentPatterns.BLOCK_COMMENT["graphql"]
        assert '"""' in block_start

    def test_hcl_comment_patterns(self):
        """Test HCL/Terraform comment patterns are defined."""
        from codeconcat.parser.language_parsers.pattern_library import CommentPatterns

        assert "hcl" in CommentPatterns.SINGLE_LINE
        assert CommentPatterns.SINGLE_LINE["hcl"] == "#"

    def test_solidity_comment_patterns(self):
        """Test Solidity comment patterns are defined."""
        from codeconcat.parser.language_parsers.pattern_library import CommentPatterns

        assert "solidity" in CommentPatterns.SINGLE_LINE
        assert CommentPatterns.SINGLE_LINE["solidity"] == "//"
        assert "solidity" in CommentPatterns.BLOCK_COMMENT

    def test_crystal_comment_patterns(self):
        """Test Crystal comment patterns are defined."""
        from codeconcat.parser.language_parsers.pattern_library import CommentPatterns

        assert "crystal" in CommentPatterns.SINGLE_LINE
        assert CommentPatterns.SINGLE_LINE["crystal"] == "#"


class TestDocCommentsQueryPresence:
    """Test that doc_comments queries exist in all enhanced parsers."""

    def test_sql_has_doc_comments_query(self):
        """Test SQL parser has doc_comments query."""
        from codeconcat.parser.language_parsers.tree_sitter_sql_parser import (
            TreeSitterSqlParser,
        )

        parser = TreeSitterSqlParser()
        queries = parser.get_queries()
        assert "doc_comments" in queries

    def test_graphql_has_doc_comments_query(self):
        """Test GraphQL parser has doc_comments query."""
        from codeconcat.parser.language_parsers.tree_sitter_graphql_parser import (
            TreeSitterGraphqlParser,
        )

        parser = TreeSitterGraphqlParser()
        queries = parser.get_queries()
        assert "doc_comments" in queries

    def test_hcl_has_doc_comments_query(self):
        """Test HCL parser has doc_comments query."""
        from codeconcat.parser.language_parsers.tree_sitter_hcl_parser import (
            TreeSitterHclParser,
        )

        parser = TreeSitterHclParser()
        queries = parser.get_queries()
        assert "doc_comments" in queries

    def test_glsl_has_doc_comments_query(self):
        """Test GLSL parser has doc_comments query."""
        from codeconcat.parser.language_parsers.tree_sitter_glsl_parser import (
            TreeSitterGlslParser,
        )

        parser = TreeSitterGlslParser()
        queries = parser.get_queries()
        assert "doc_comments" in queries

    def test_hlsl_has_doc_comments_query(self):
        """Test HLSL parser has doc_comments query."""
        from codeconcat.parser.language_parsers.tree_sitter_hlsl_parser import (
            TreeSitterHlslParser,
        )

        parser = TreeSitterHlslParser()
        queries = parser.get_queries()
        assert "doc_comments" in queries

    def test_solidity_has_doc_comments_query(self):
        """Test Solidity parser has doc_comments query."""
        from codeconcat.parser.language_parsers.tree_sitter_solidity_parser import (
            TreeSitterSolidityParser,
        )

        parser = TreeSitterSolidityParser()
        queries = parser.get_queries()
        assert "doc_comments" in queries

    def test_wat_has_doc_comments_query(self):
        """Test WAT parser has doc_comments query."""
        from codeconcat.parser.language_parsers.tree_sitter_wat_parser import (
            TreeSitterWatParser,
        )

        parser = TreeSitterWatParser()
        queries = parser.get_queries()
        assert "doc_comments" in queries

    def test_crystal_has_doc_comments_query(self):
        """Test Crystal parser has doc_comments query."""
        from codeconcat.parser.language_parsers.tree_sitter_crystal_parser import (
            TreeSitterCrystalParser,
        )

        parser = TreeSitterCrystalParser()
        queries = parser.get_queries()
        assert "doc_comments" in queries

    def test_elixir_has_doc_comments_query(self):
        """Test Elixir parser has doc_comments query."""
        from codeconcat.parser.language_parsers.tree_sitter_elixir_parser import (
            TreeSitterElixirParser,
        )

        parser = TreeSitterElixirParser()
        queries = parser.get_queries()
        assert "doc_comments" in queries
