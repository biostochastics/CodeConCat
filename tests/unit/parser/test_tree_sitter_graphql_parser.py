# tests/unit/parser/test_tree_sitter_graphql_parser.py

import pytest

from codeconcat.parser.language_parsers.tree_sitter_graphql_parser import (
    GRAPHQL_QUERIES,
    TreeSitterGraphqlParser,
)


class TestTreeSitterGraphqlParser:
    """Unit tests for TreeSitterGraphqlParser."""

    def test_graphql_grammar_loads(self):
        """Test that the GraphQL grammar loads successfully."""
        parser = TreeSitterGraphqlParser()
        assert parser is not None
        assert parser.language_name == "graphql"
        assert parser.ts_language is not None
        assert parser.parser is not None

    def test_parser_initialization(self):
        """Test parser initialization and configuration."""
        parser = TreeSitterGraphqlParser()

        # Check language availability
        assert parser.check_language_availability() is True

        # Check queries are available
        queries = parser.get_queries()
        assert isinstance(queries, dict)
        assert "type_definitions" in queries
        assert "operations" in queries
        assert "fragments" in queries
        assert "field_definitions" in queries
        assert "directives" in queries

    def test_graphql_queries_structure(self):
        """Test that GRAPHQL_QUERIES has correct structure."""
        assert isinstance(GRAPHQL_QUERIES, dict)
        assert len(GRAPHQL_QUERIES) == 5

        # Each query should be a non-empty string
        for query_name, query_str in GRAPHQL_QUERIES.items():
            assert isinstance(query_str, str)
            assert len(query_str.strip()) > 0

    def test_parse_empty_schema(self):
        """Test parsing an empty GraphQL schema."""
        parser = TreeSitterGraphqlParser()
        content = ""
        result = parser.parse(content, "test.graphql")

        assert result is not None
        assert result.declarations == []
        assert result.imports == []

    def test_parse_minimal_schema(self):
        """Test parsing a minimal GraphQL schema."""
        parser = TreeSitterGraphqlParser()
        content = """
type Query {
  hello: String
}
"""
        result = parser.parse(content, "test.graphql")

        assert result is not None
        assert result.error is None or result.error == ""
        assert result.ast_root is not None
        assert result.ast_root.type == "source_file"

    def test_parse_minimal_operation(self):
        """Test parsing a minimal GraphQL operation."""
        parser = TreeSitterGraphqlParser()
        content = """
query GetData {
  hello
}
"""
        result = parser.parse(content, "test.graphql")

        assert result is not None
        assert result.error is None or result.error == ""
        assert result.ast_root is not None
        assert result.ast_root.type == "source_file"

    def test_parse_handles_syntax_errors_gracefully(self):
        """Test that parser handles malformed GraphQL gracefully."""
        parser = TreeSitterGraphqlParser()
        content = """
type Query {
  hello: String
  # Missing closing brace
"""
        result = parser.parse(content, "test.graphql")

        # Should still return a result, possibly with error flag
        assert result is not None
        assert result.ast_root is not None

    def test_parser_caching_initialization(self):
        """Test that caching variables are initialized."""
        parser = TreeSitterGraphqlParser()

        # Check cache variables exist
        assert hasattr(parser, '_current_tree')
        assert hasattr(parser, '_cached_types')
        assert hasattr(parser, '_cached_operations')
        assert hasattr(parser, '_cached_fragments')
        assert hasattr(parser, '_type_relationships_cache')
        assert hasattr(parser, '_cached_directives')

        # Check they're initially None
        assert parser._current_tree is None
        assert parser._cached_types is None
        assert parser._cached_operations is None
        assert parser._cached_fragments is None
        assert parser._type_relationships_cache is None
        assert parser._cached_directives is None
