# tests/unit/parser/test_tree_sitter_graphql_operations.py

import pytest

from codeconcat.parser.language_parsers.tree_sitter_graphql_parser import (
    TreeSitterGraphqlParser,
)


class TestGraphqlOperationExtraction:
    """Unit tests for GraphQL operation extraction."""

    def test_extract_named_query(self):
        """Test extraction of named query operation."""
        parser = TreeSitterGraphqlParser()
        content = b"""
query GetUser {
  user(id: "123") {
    id
    name
  }
}
"""
        operations = parser.extract_operations(content)

        assert len(operations) == 1
        op = operations[0]
        assert op["type"] == "query"
        assert op["name"] == "GetUser"
        assert op["line_number"] == 2
        assert "user(id:" in op["definition"]

    def test_extract_anonymous_query(self):
        """Test extraction of anonymous query operation."""
        parser = TreeSitterGraphqlParser()
        content = b"""
{
  user {
    id
    name
  }
}
"""
        operations = parser.extract_operations(content)

        assert len(operations) == 1
        op = operations[0]
        assert op["type"] == "query"
        assert op["name"] is None  # Anonymous
        assert "user" in op["definition"]

    def test_extract_mutation(self):
        """Test extraction of mutation operation."""
        parser = TreeSitterGraphqlParser()
        content = b"""
mutation CreateUser {
  createUser(input: {name: "Alice"}) {
    id
    name
  }
}
"""
        operations = parser.extract_operations(content)

        assert len(operations) == 1
        op = operations[0]
        assert op["type"] == "mutation"
        assert op["name"] == "CreateUser"

    def test_extract_subscription(self):
        """Test extraction of subscription operation."""
        parser = TreeSitterGraphqlParser()
        content = b"""
subscription OnUserCreated {
  userCreated {
    id
    name
  }
}
"""
        operations = parser.extract_operations(content)

        assert len(operations) == 1
        op = operations[0]
        assert op["type"] == "subscription"
        assert op["name"] == "OnUserCreated"

    def test_extract_operation_with_variables(self):
        """Test extraction of operation with variable definitions."""
        parser = TreeSitterGraphqlParser()
        content = b"""
query GetUser($id: ID!, $includeEmail: Boolean) {
  user(id: $id) {
    id
    name
    email @include(if: $includeEmail)
  }
}
"""
        operations = parser.extract_operations(content)

        assert len(operations) == 1
        op = operations[0]
        assert op["name"] == "GetUser"
        assert len(op["variables"]) == 2

        # Check first variable
        assert op["variables"][0]["name"] == "id"
        assert op["variables"][0]["type"] == "ID!"

        # Check second variable
        assert op["variables"][1]["name"] == "includeEmail"
        assert op["variables"][1]["type"] == "Boolean"

    def test_extract_multiple_operations(self):
        """Test extraction of multiple operations in one document."""
        parser = TreeSitterGraphqlParser()
        content = b"""
query GetUser {
  user { id }
}

mutation UpdateUser {
  updateUser { id }
}

subscription WatchUser {
  userUpdated { id }
}
"""
        operations = parser.extract_operations(content)

        assert len(operations) == 3
        assert operations[0]["type"] == "query"
        assert operations[1]["type"] == "mutation"
        assert operations[2]["type"] == "subscription"

    def test_operation_extraction_caching(self):
        """Test that operation extraction results are cached."""
        parser = TreeSitterGraphqlParser()
        content = b"""
query Test {
  user { id }
}
"""
        # First call should parse and cache
        ops1 = parser.extract_operations(content)
        assert len(ops1) == 1

        # Second call should return cached result
        ops2 = parser.extract_operations(content)
        assert ops2 is ops1  # Same object reference


class TestGraphqlFragmentExtraction:
    """Unit tests for GraphQL fragment extraction."""

    def test_extract_simple_fragment(self):
        """Test extraction of simple fragment definition."""
        parser = TreeSitterGraphqlParser()
        content = b"""
fragment UserFields on User {
  id
  name
  email
}
"""
        fragments = parser.extract_fragments(content)

        assert len(fragments) == 1
        frag = fragments[0]
        assert frag["name"] == "UserFields"
        assert frag["type_condition"] == "User"
        assert frag["line_number"] == 2
        assert "id" in frag["definition"]

    def test_extract_nested_fragment(self):
        """Test extraction of fragment with nested fields."""
        parser = TreeSitterGraphqlParser()
        content = b"""
fragment UserProfile on User {
  id
  name
  posts {
    id
    title
  }
}
"""
        fragments = parser.extract_fragments(content)

        assert len(fragments) == 1
        frag = fragments[0]
        assert frag["name"] == "UserProfile"
        assert frag["type_condition"] == "User"
        assert "posts" in frag["definition"]

    def test_extract_multiple_fragments(self):
        """Test extraction of multiple fragment definitions."""
        parser = TreeSitterGraphqlParser()
        content = b"""
fragment UserFields on User {
  id
  name
}

fragment PostFields on Post {
  id
  title
  author {
    ...UserFields
  }
}
"""
        fragments = parser.extract_fragments(content)

        assert len(fragments) == 2
        assert fragments[0]["name"] == "UserFields"
        assert fragments[0]["type_condition"] == "User"
        assert fragments[1]["name"] == "PostFields"
        assert fragments[1]["type_condition"] == "Post"

    def test_fragment_extraction_caching(self):
        """Test that fragment extraction results are cached."""
        parser = TreeSitterGraphqlParser()
        content = b"""
fragment Test on User {
  id
}
"""
        # First call should parse and cache
        frags1 = parser.extract_fragments(content)
        assert len(frags1) == 1

        # Second call should return cached result
        frags2 = parser.extract_fragments(content)
        assert frags2 is frags1  # Same object reference


class TestGraphqlMixedDocuments:
    """Integration tests with mixed GraphQL documents."""

    def test_operations_and_fragments(self):
        """Test extraction from document with both operations and fragments."""
        parser = TreeSitterGraphqlParser()
        content = b"""
fragment UserFields on User {
  id
  name
  email
}

query GetUsers {
  users {
    ...UserFields
  }
}

mutation CreateUser($input: CreateUserInput!) {
  createUser(input: $input) {
    ...UserFields
  }
}
"""
        operations = parser.extract_operations(content)
        fragments = parser.extract_fragments(content)

        assert len(operations) == 2
        assert len(fragments) == 1

        # Check operations
        assert operations[0]["type"] == "query"
        assert operations[0]["name"] == "GetUsers"
        assert operations[1]["type"] == "mutation"
        assert operations[1]["name"] == "CreateUser"
        assert len(operations[1]["variables"]) == 1

        # Check fragment
        assert fragments[0]["name"] == "UserFields"
        assert fragments[0]["type_condition"] == "User"

    def test_empty_operations_document(self):
        """Test handling of document with no operations."""
        parser = TreeSitterGraphqlParser()
        content = b""

        operations = parser.extract_operations(content)
        assert operations == []

    def test_empty_fragments_document(self):
        """Test handling of document with no fragments."""
        parser = TreeSitterGraphqlParser()
        content = b""

        fragments = parser.extract_fragments(content)
        assert fragments == []
