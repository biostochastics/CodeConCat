# tests/unit/parser/test_tree_sitter_graphql_extraction.py

import pytest

from codeconcat.parser.language_parsers.tree_sitter_graphql_parser import (
    TreeSitterGraphqlParser,
)


class TestGraphqlTypeExtraction:
    """Unit tests for GraphQL type definition extraction."""

    def test_extract_object_type(self):
        """Test extraction of object type definitions."""
        parser = TreeSitterGraphqlParser()
        content = b"""
type User {
  id: ID!
  name: String!
  email: String
  posts: [Post!]!
}
"""
        types = parser.extract_type_definitions(content)

        assert len(types) == 1
        user_type = types[0]
        assert user_type["name"] == "User"
        assert user_type["kind"] == "object"
        assert user_type["line_number"] == 2
        assert "fields" in user_type
        assert len(user_type["fields"]) == 4

        # Check field details
        id_field = user_type["fields"][0]
        assert id_field["name"] == "id"
        assert id_field["type"] == "ID!"

        posts_field = user_type["fields"][3]
        assert posts_field["name"] == "posts"
        assert posts_field["type"] == "[Post!]!"

    def test_extract_interface_type(self):
        """Test extraction of interface type definitions."""
        parser = TreeSitterGraphqlParser()
        content = b"""
interface Node {
  id: ID!
}

interface Timestamped {
  createdAt: DateTime!
  updatedAt: DateTime!
}
"""
        types = parser.extract_type_definitions(content)

        assert len(types) == 2
        node_interface = types[0]
        assert node_interface["name"] == "Node"
        assert node_interface["kind"] == "interface"
        assert len(node_interface["fields"]) == 1

        timestamped_interface = types[1]
        assert timestamped_interface["name"] == "Timestamped"
        assert timestamped_interface["kind"] == "interface"
        assert len(timestamped_interface["fields"]) == 2

    def test_extract_union_type(self):
        """Test extraction of union type definitions."""
        parser = TreeSitterGraphqlParser()
        content = b"""
union SearchResult = User | Post | Comment
"""
        types = parser.extract_type_definitions(content)

        assert len(types) == 1
        union_type = types[0]
        assert union_type["name"] == "SearchResult"
        assert union_type["kind"] == "union"
        assert "types" in union_type
        assert union_type["types"] == ["User", "Post", "Comment"]

    def test_extract_enum_type(self):
        """Test extraction of enum type definitions."""
        parser = TreeSitterGraphqlParser()
        content = b"""
enum Role {
  ADMIN
  USER
  GUEST
}
"""
        types = parser.extract_type_definitions(content)

        assert len(types) == 1
        enum_type = types[0]
        assert enum_type["name"] == "Role"
        assert enum_type["kind"] == "enum"
        assert "values" in enum_type
        assert enum_type["values"] == ["ADMIN", "USER", "GUEST"]

    def test_extract_scalar_type(self):
        """Test extraction of scalar type definitions."""
        parser = TreeSitterGraphqlParser()
        content = b"""
scalar DateTime
scalar JSON
"""
        types = parser.extract_type_definitions(content)

        assert len(types) == 2
        assert types[0]["name"] == "DateTime"
        assert types[0]["kind"] == "scalar"
        assert types[1]["name"] == "JSON"
        assert types[1]["kind"] == "scalar"

    def test_extract_input_type(self):
        """Test extraction of input object type definitions."""
        parser = TreeSitterGraphqlParser()
        content = b"""
input CreateUserInput {
  name: String!
  email: String!
  age: Int
}
"""
        types = parser.extract_type_definitions(content)

        assert len(types) == 1
        input_type = types[0]
        assert input_type["name"] == "CreateUserInput"
        assert input_type["kind"] == "input"
        assert "fields" in input_type
        assert len(input_type["fields"]) == 3

    def test_extract_field_with_arguments(self):
        """Test extraction of fields with arguments."""
        parser = TreeSitterGraphqlParser()
        content = b"""
type Query {
  user(id: ID!): User
  posts(limit: Int, offset: Int): [Post!]!
  search(query: String!, type: SearchType): [SearchResult!]
}
"""
        types = parser.extract_type_definitions(content)

        assert len(types) == 1
        query_type = types[0]
        assert len(query_type["fields"]) == 3

        # Check field with single argument
        user_field = query_type["fields"][0]
        assert user_field["name"] == "user"
        assert len(user_field["arguments"]) == 1
        assert user_field["arguments"][0]["name"] == "id"
        assert user_field["arguments"][0]["type"] == "ID!"

        # Check field with multiple arguments
        posts_field = query_type["fields"][1]
        assert posts_field["name"] == "posts"
        assert len(posts_field["arguments"]) == 2
        assert posts_field["arguments"][0]["name"] == "limit"
        assert posts_field["arguments"][0]["type"] == "Int"
        assert posts_field["arguments"][1]["name"] == "offset"
        assert posts_field["arguments"][1]["type"] == "Int"

    def test_extract_mixed_types(self):
        """Test extraction of multiple type kinds in one schema."""
        parser = TreeSitterGraphqlParser()
        content = b"""
scalar DateTime

enum Status {
  ACTIVE
  INACTIVE
}

interface Node {
  id: ID!
}

type User implements Node {
  id: ID!
  name: String!
  status: Status!
}

input UserFilter {
  status: Status
}

union Content = User | Post
"""
        types = parser.extract_type_definitions(content)

        assert len(types) == 6

        # Count by kind
        kinds = [t["kind"] for t in types]
        assert kinds.count("scalar") == 1
        assert kinds.count("enum") == 1
        assert kinds.count("interface") == 1
        assert kinds.count("object") == 1
        assert kinds.count("input") == 1
        assert kinds.count("union") == 1

    def test_type_extraction_caching(self):
        """Test that type extraction results are cached."""
        parser = TreeSitterGraphqlParser()
        content = b"""
type User {
  id: ID!
  name: String!
}
"""
        # First call should parse and cache
        types1 = parser.extract_type_definitions(content)
        assert len(types1) == 1

        # Second call should return cached result
        types2 = parser.extract_type_definitions(content)
        assert types2 is types1  # Same object reference


class TestGraphqlDirectiveExtraction:
    """Unit tests for GraphQL directive extraction."""

    def test_extract_directive_definition(self):
        """Test extraction of directive definitions."""
        parser = TreeSitterGraphqlParser()
        content = b"""
directive @auth(requires: Role = ADMIN) on FIELD_DEFINITION | OBJECT

directive @deprecated(
  reason: String = "No longer supported"
) on FIELD_DEFINITION | ENUM_VALUE
"""
        result = parser.extract_directives(content)

        assert "definitions" in result
        assert "usages" in result
        assert len(result["definitions"]) == 2

        # Check first directive
        auth_directive = result["definitions"][0]
        assert auth_directive["name"] == "auth"
        assert len(auth_directive["arguments"]) == 1
        assert auth_directive["arguments"][0]["name"] == "requires"
        assert "FIELD_DEFINITION" in auth_directive["locations"]
        assert "OBJECT" in auth_directive["locations"]

        # Check second directive
        deprecated_directive = result["definitions"][1]
        assert deprecated_directive["name"] == "deprecated"
        assert len(deprecated_directive["arguments"]) == 1
        assert deprecated_directive["arguments"][0]["name"] == "reason"

    def test_extract_directive_usage(self):
        """Test extraction of directive usage in schema."""
        parser = TreeSitterGraphqlParser()
        content = b"""
type User @auth(requires: ADMIN) {
  id: ID!
  email: String! @deprecated(reason: "Use contactEmail")
  contactEmail: String!
}
"""
        result = parser.extract_directives(content)

        assert len(result["usages"]) == 2

        # Check usages
        usage_names = [u["name"] for u in result["usages"]]
        assert "auth" in usage_names
        assert "deprecated" in usage_names

    def test_directive_extraction_caching(self):
        """Test that directive extraction results are cached."""
        parser = TreeSitterGraphqlParser()
        content = b"""
directive @example on FIELD_DEFINITION

type Query {
  test: String @example
}
"""
        # First call should parse and cache
        result1 = parser.extract_directives(content)
        assert len(result1["definitions"]) == 1

        # Second call should return cached result
        result2 = parser.extract_directives(content)
        assert result2 is result1  # Same object reference


class TestGraphqlComplexSchemas:
    """Integration tests with complex GraphQL schemas."""

    def test_github_style_schema(self):
        """Test with a GitHub-style GraphQL schema."""
        parser = TreeSitterGraphqlParser()
        content = b"""
scalar DateTime

enum IssueState {
  OPEN
  CLOSED
}

interface Node {
  id: ID!
}

type User implements Node {
  id: ID!
  login: String!
  email: String
  createdAt: DateTime!
}

type Issue implements Node {
  id: ID!
  title: String!
  body: String
  state: IssueState!
  author: User!
  createdAt: DateTime!
}

type Query {
  user(login: String!): User
  issue(number: Int!): Issue
  search(query: String!, type: SearchType!): [SearchResult!]!
}

input CreateIssueInput {
  title: String!
  body: String
}

type Mutation {
  createIssue(input: CreateIssueInput!): Issue!
}

union SearchResult = User | Issue
"""
        types = parser.extract_type_definitions(content)

        # Should extract all type definitions
        assert len(types) == 9

        # Check specific types exist
        type_names = [t["name"] for t in types]
        assert "DateTime" in type_names
        assert "IssueState" in type_names
        assert "Node" in type_names
        assert "User" in type_names
        assert "Issue" in type_names
        assert "Query" in type_names
        assert "CreateIssueInput" in type_names
        assert "Mutation" in type_names
        assert "SearchResult" in type_names

        # Verify User type has correct structure
        user_type = next(t for t in types if t["name"] == "User")
        assert user_type["kind"] == "object"
        assert len(user_type["fields"]) == 4

        # Verify Query type has fields with arguments
        query_type = next(t for t in types if t["name"] == "Query")
        user_query = query_type["fields"][0]
        assert user_query["name"] == "user"
        assert len(user_query["arguments"]) == 1

    def test_empty_schema(self):
        """Test handling of empty schema."""
        parser = TreeSitterGraphqlParser()
        content = b""

        types = parser.extract_type_definitions(content)
        assert types == []

        directives = parser.extract_directives(content)
        assert directives["definitions"] == []
        assert directives["usages"] == []

    def test_schema_with_comments(self):
        """Test extraction from schema with comments."""
        parser = TreeSitterGraphqlParser()
        content = b'''
# User type definition
type User {
  # Unique identifier
  id: ID!
  # User's display name
  name: String!
}
'''
        types = parser.extract_type_definitions(content)

        assert len(types) == 1
        user_type = types[0]
        assert user_type["name"] == "User"
        assert len(user_type["fields"]) == 2
