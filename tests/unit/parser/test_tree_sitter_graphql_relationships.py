# tests/unit/parser/test_tree_sitter_graphql_relationships.py

import pytest

from codeconcat.parser.language_parsers.tree_sitter_graphql_parser import (
    TreeSitterGraphqlParser,
)


class TestGraphqlTypeRelationships:
    """Unit tests for GraphQL type relationship extraction."""

    def test_simple_type_relationships(self):
        """Test extraction of basic type relationships."""
        parser = TreeSitterGraphqlParser()
        content = b"""
type User {
  id: ID!
  name: String!
  posts: [Post!]!
}

type Post {
  id: ID!
  title: String!
  author: User!
}
"""
        relationships = parser.extract_type_relationships(content)

        assert "User" in relationships
        assert "Post" in relationships["User"]
        assert "User" in relationships["Post"]

    def test_interface_relationships(self):
        """Test relationships with interface types."""
        parser = TreeSitterGraphqlParser()
        content = b"""
interface Node {
  id: ID!
}

type User implements Node {
  id: ID!
  name: String!
  manager: User
}
"""
        relationships = parser.extract_type_relationships(content)

        assert "User" in relationships
        assert relationships["User"] == ["User"]  # Self-reference

    def test_union_type_relationships(self):
        """Test relationships with union types."""
        parser = TreeSitterGraphqlParser()
        content = b"""
type User {
  id: ID!
}

type Post {
  id: ID!
}

union SearchResult = User | Post
"""
        relationships = parser.extract_type_relationships(content)

        assert "SearchResult" in relationships
        assert set(relationships["SearchResult"]) == {"User", "Post"}

    def test_input_type_relationships(self):
        """Test relationships with input types."""
        parser = TreeSitterGraphqlParser()
        content = b"""
input UserFilter {
  role: Role
}

enum Role {
  ADMIN
  USER
}

type Query {
  users(filter: UserFilter): [User!]!
}

type User {
  id: ID!
}
"""
        relationships = parser.extract_type_relationships(content)

        assert "UserFilter" in relationships
        assert "Role" in relationships["UserFilter"]
        assert "Query" in relationships
        assert set(relationships["Query"]) == {"User", "UserFilter"}

    def test_argument_type_relationships(self):
        """Test that argument types are included in relationships."""
        parser = TreeSitterGraphqlParser()
        content = b"""
input CreateUserInput {
  name: String!
}

type Mutation {
  createUser(input: CreateUserInput!): User!
}

type User {
  id: ID!
}
"""
        relationships = parser.extract_type_relationships(content)

        assert "Mutation" in relationships
        assert "CreateUserInput" in relationships["Mutation"]
        assert "User" in relationships["Mutation"]

    def test_builtin_types_excluded(self):
        """Test that built-in types are not included in relationships."""
        parser = TreeSitterGraphqlParser()
        content = b"""
type User {
  id: ID!
  name: String!
  age: Int
  score: Float
  active: Boolean
}
"""
        relationships = parser.extract_type_relationships(content)

        assert "User" in relationships
        assert relationships["User"] == []  # No custom type references

    def test_relationship_caching(self):
        """Test that relationship extraction is cached."""
        parser = TreeSitterGraphqlParser()
        content = b"""
type User {
  posts: [Post!]!
}

type Post {
  author: User!
}
"""
        # First call
        rel1 = parser.extract_type_relationships(content)

        # Second call should return cached result
        rel2 = parser.extract_type_relationships(content)
        assert rel2 is rel1  # Same object reference


class TestGraphqlResolverRequirements:
    """Unit tests for GraphQL resolver requirement identification."""

    def test_simple_resolver_requirements(self):
        """Test identification of basic resolver requirements."""
        parser = TreeSitterGraphqlParser()
        content = b"""
type User {
  id: ID!
  name: String!
  posts: [Post!]!
}

type Post {
  id: ID!
  title: String!
}
"""
        requirements = parser.extract_resolver_requirements(content)

        assert "User" in requirements
        assert len(requirements["User"]) == 1
        assert requirements["User"][0]["name"] == "posts"
        assert requirements["User"][0]["type"] == "[Post!]!"

    def test_scalar_fields_no_resolvers(self):
        """Test that scalar fields don't require resolvers."""
        parser = TreeSitterGraphqlParser()
        content = b"""
type User {
  id: ID!
  name: String!
  age: Int
  score: Float
  active: Boolean
}
"""
        requirements = parser.extract_resolver_requirements(content)

        # User type not in requirements (all scalar fields)
        assert "User" not in requirements

    def test_enum_fields_no_resolvers(self):
        """Test that enum fields don't require resolvers."""
        parser = TreeSitterGraphqlParser()
        content = b"""
enum Role {
  ADMIN
  USER
}

type User {
  id: ID!
  role: Role!
}
"""
        requirements = parser.extract_resolver_requirements(content)

        # User type not in requirements (role is enum, not object)
        assert "User" not in requirements

    def test_complexity_hints_simple(self):
        """Test complexity hints for simple object fields."""
        parser = TreeSitterGraphqlParser()
        content = b"""
type User {
  profile: Profile!
}

type Profile {
  bio: String
}
"""
        requirements = parser.extract_resolver_requirements(content)

        assert "User" in requirements
        assert requirements["User"][0]["complexity_hint"] == "simple"

    def test_complexity_hints_moderate_with_args(self):
        """Test complexity hints for fields with arguments."""
        parser = TreeSitterGraphqlParser()
        content = b"""
type User {
  posts(limit: Int): [Post!]!
}

type Post {
  title: String!
}
"""
        requirements = parser.extract_resolver_requirements(content)

        assert "User" in requirements
        # Has arguments, so should be at least moderate
        assert requirements["User"][0]["complexity_hint"] in ("moderate", "high")

    def test_complexity_hints_high_with_list_and_args(self):
        """Test complexity hints for list fields with arguments."""
        parser = TreeSitterGraphqlParser()
        content = b"""
type Query {
  users(filter: String, limit: Int): [User!]!
}

type User {
  id: ID!
}
"""
        requirements = parser.extract_resolver_requirements(content)

        assert "Query" in requirements
        # List with arguments should be high complexity
        assert requirements["Query"][0]["complexity_hint"] == "high"

    def test_interface_resolver_requirements(self):
        """Test resolver requirements for interface types."""
        parser = TreeSitterGraphqlParser()
        content = b"""
interface Node {
  id: ID!
  relatedNodes: [Node!]!
}

type User implements Node {
  id: ID!
  relatedNodes: [Node!]!
}
"""
        requirements = parser.extract_resolver_requirements(content)

        # Both Node and User should have resolver requirements
        assert "Node" in requirements
        assert "User" in requirements

    def test_multiple_resolver_fields(self):
        """Test type with multiple fields requiring resolvers."""
        parser = TreeSitterGraphqlParser()
        content = b"""
type User {
  id: ID!
  profile: Profile!
  posts: [Post!]!
  followers: [User!]!
}

type Profile {
  bio: String
}

type Post {
  title: String
}
"""
        requirements = parser.extract_resolver_requirements(content)

        assert "User" in requirements
        assert len(requirements["User"]) == 3  # profile, posts, followers
        field_names = {f["name"] for f in requirements["User"]}
        assert field_names == {"profile", "posts", "followers"}


class TestGraphqlComplexRelationships:
    """Integration tests for complex relationship scenarios."""

    def test_circular_relationships(self):
        """Test handling of circular type references."""
        parser = TreeSitterGraphqlParser()
        content = b"""
type User {
  id: ID!
  friends: [User!]!
  posts: [Post!]!
}

type Post {
  id: ID!
  author: User!
  comments: [Comment!]!
}

type Comment {
  id: ID!
  author: User!
  post: Post!
}
"""
        relationships = parser.extract_type_relationships(content)

        assert "User" in relationships["User"]  # Self-reference
        assert "Post" in relationships["User"]
        assert "User" in relationships["Post"]
        assert "Comment" in relationships["Post"]
        assert "User" in relationships["Comment"]
        assert "Post" in relationships["Comment"]

    def test_github_style_schema_relationships(self):
        """Test with a realistic GitHub-style schema."""
        parser = TreeSitterGraphqlParser()
        content = b"""
type User {
  id: ID!
  repositories: [Repository!]!
  issues: [Issue!]!
}

type Repository {
  id: ID!
  owner: User!
  issues: [Issue!]!
}

type Issue {
  id: ID!
  author: User!
  repository: Repository!
}
"""
        relationships = parser.extract_type_relationships(content)
        requirements = parser.extract_resolver_requirements(content)

        # Check relationships
        assert set(relationships["User"]) == {"Repository", "Issue"}
        assert set(relationships["Repository"]) == {"User", "Issue"}
        assert set(relationships["Issue"]) == {"User", "Repository"}

        # Check resolver requirements
        assert "User" in requirements
        assert "Repository" in requirements
        assert "Issue" in requirements
