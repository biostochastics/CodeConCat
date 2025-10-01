# tests/integration/test_graphql_integration.py

"""Integration tests for GraphQL parser through unified pipeline."""

import tempfile
from pathlib import Path

import pytest

from codeconcat.base_types import CodeConCatConfig, ParsedFileData
from codeconcat.parser.unified_pipeline import parse_code_files


class TestGraphqlIntegration:
    """Integration tests for GraphQL parser."""

    def test_graphql_schema_parsing(self):
        """Test parsing a complete GraphQL schema through the pipeline."""
        schema_content = """
# GraphQL Schema for a Blog Platform

scalar DateTime

enum Role {
  ADMIN
  AUTHOR
  READER
}

interface Node {
  id: ID!
  createdAt: DateTime!
}

type User implements Node {
  id: ID!
  createdAt: DateTime!
  name: String!
  email: String!
  role: Role!
  posts: [Post!]!
  comments: [Comment!]!
}

type Post implements Node {
  id: ID!
  createdAt: DateTime!
  title: String!
  content: String!
  published: Boolean!
  author: User!
  comments: [Comment!]!
  tags: [String!]!
}

type Comment implements Node {
  id: ID!
  createdAt: DateTime!
  content: String!
  author: User!
  post: Post!
}

type Query {
  user(id: ID!): User
  post(id: ID!): Post
  posts(limit: Int, offset: Int): [Post!]!
  search(query: String!): [SearchResult!]!
}

input CreatePostInput {
  title: String!
  content: String!
  tags: [String!]
}

type Mutation {
  createPost(input: CreatePostInput!): Post!
  deletePost(id: ID!): Boolean!
}

union SearchResult = User | Post | Comment

directive @auth(requires: Role = ADMIN) on FIELD_DEFINITION | OBJECT
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".graphql", delete=False) as f:
            f.write(schema_content)
            schema_file = f.name

        try:
            # Parse through unified pipeline
            config = CodeConCatConfig(no_progress=True)

            # Create ParsedFileData object
            with open(schema_file) as f:
                content = f.read()
            file_data = ParsedFileData(
                file_path=schema_file, content=content, language="graphql"
            )

            parsed_files, errors = parse_code_files([file_data], config)

            # Verify parsing succeeded
            assert len(errors) == 0
            assert len(parsed_files) == 1
            result = parsed_files[0]
            assert result is not None
            assert result.parse_result is not None
            assert result.parse_result.error is None or result.parse_result.error == ""
            assert result.parse_result.ast_root is not None

            # Verify language and parser
            assert result.language == "graphql"
            assert result.parse_result.parser_type == "tree_sitter"

        finally:
            Path(schema_file).unlink()

    def test_graphql_operations_parsing(self):
        """Test parsing GraphQL operations."""
        operations_content = """
query GetUser($id: ID!) {
  user(id: $id) {
    id
    name
    email
    posts {
      id
      title
    }
  }
}

mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    id
    title
    author {
      name
    }
  }
}

fragment UserFields on User {
  id
  name
  email
  role
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".gql", delete=False) as f:
            f.write(operations_content)
            ops_file = f.name

        try:
            config = CodeConCatConfig(no_progress=True)

            # Create ParsedFileData object
            with open(ops_file) as f:
                content = f.read()
            file_data = ParsedFileData(
                file_path=ops_file, content=content, language="graphql"
            )

            parsed_files, errors = parse_code_files([file_data], config)

            assert len(errors) == 0
            assert len(parsed_files) == 1
            result = parsed_files[0]
            assert result is not None
            assert result.parse_result is not None
            assert result.parse_result.error is None or result.parse_result.error == ""
            assert result.parse_result.ast_root is not None

        finally:
            Path(ops_file).unlink()

    def test_graphql_file_extension_recognition(self):
        """Test that both .graphql and .gql extensions are recognized."""
        schema = "type Query { hello: String }"

        # Test .graphql extension
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".graphql", delete=False
        ) as f:
            f.write(schema)
            graphql_file = f.name

        # Test .gql extension
        with tempfile.NamedTemporaryFile(mode="w", suffix=".gql", delete=False) as f:
            f.write(schema)
            gql_file = f.name

        try:
            config = CodeConCatConfig(no_progress=True)

            # Parse .graphql file
            with open(graphql_file) as f:
                content1 = f.read()
            file_data1 = ParsedFileData(
                file_path=graphql_file, content=content1, language="graphql"
            )
            parsed_files1, errors1 = parse_code_files([file_data1], config)
            assert len(errors1) == 0
            assert len(parsed_files1) == 1
            result1 = parsed_files1[0]
            assert result1 is not None
            assert result1.language == "graphql"
            assert result1.parse_result.parser_type == "tree_sitter"

            # Parse .gql file
            with open(gql_file) as f:
                content2 = f.read()
            file_data2 = ParsedFileData(
                file_path=gql_file, content=content2, language="graphql"
            )
            parsed_files2, errors2 = parse_code_files([file_data2], config)
            assert len(errors2) == 0
            assert len(parsed_files2) == 1
            result2 = parsed_files2[0]
            assert result2 is not None
            assert result2.language == "graphql"
            assert result2.parse_result.parser_type == "tree_sitter"

        finally:
            Path(graphql_file).unlink()
            Path(gql_file).unlink()

    def test_graphql_complex_schema(self):
        """Test parsing a complex real-world schema."""
        complex_schema = """
directive @deprecated(reason: String = "No longer supported") on FIELD_DEFINITION | ENUM_VALUE

scalar Upload
scalar JSON

interface Timestamped {
  createdAt: DateTime!
  updatedAt: DateTime!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type UserEdge {
  node: User!
  cursor: String!
}

enum OrderDirection {
  ASC
  DESC
}

input UserOrder {
  field: String!
  direction: OrderDirection!
}

type User implements Node & Timestamped {
  id: ID!
  createdAt: DateTime!
  updatedAt: DateTime!
  username: String!
  email: String!
  profile: Profile
  posts(
    first: Int
    after: String
    orderBy: UserOrder
  ): PostConnection!
}

type Profile {
  bio: String
  avatar: String
  website: String
}

type Post implements Node & Timestamped {
  id: ID!
  createdAt: DateTime!
  updatedAt: DateTime!
  title: String!
  content: String!
  author: User!
  categories: [Category!]!
}

type Category {
  id: ID!
  name: String!
  posts: [Post!]!
}

type Query {
  users(
    first: Int
    after: String
    orderBy: UserOrder
  ): UserConnection!

  user(id: ID, username: String): User
  post(id: ID!): Post
}

type Mutation {
  updateProfile(bio: String, avatar: Upload): Profile!
  createPost(title: String!, content: String!): Post!
}

type Subscription {
  postAdded: Post!
}
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".graphql", delete=False) as f:
            f.write(complex_schema)
            schema_file = f.name

        try:
            config = CodeConCatConfig(no_progress=True)

            # Create ParsedFileData object
            with open(schema_file) as f:
                content = f.read()
            file_data = ParsedFileData(
                file_path=schema_file, content=content, language="graphql"
            )

            parsed_files, errors = parse_code_files([file_data], config)

            assert len(errors) == 0
            assert len(parsed_files) == 1
            result = parsed_files[0]
            assert result is not None
            assert result.parse_result is not None
            assert result.parse_result.error is None or result.parse_result.error == ""
            assert result.parse_result.ast_root is not None

        finally:
            Path(schema_file).unlink()
