# file: codeconcat/parser/language_parsers/tree_sitter_graphql_parser.py

"""
GraphQL parser using tree-sitter.

Extracts schema definitions and operations from GraphQL files using the
bkegley/tree-sitter-graphql grammar.

Supports GraphQL Schema Definition Language (SDL) and operations with features including:
- Type definitions (object, interface, union, enum, scalar, input)
- Operation definitions (query, mutation, subscription)
- Fragment definitions
- Directive definitions and usage
- Type relationship mapping
- Field argument extraction
- Resolver requirement identification
"""

import logging
from typing import Any

from ..utils import get_node_location
from .base_tree_sitter_parser import BaseTreeSitterParser

try:
    from tree_sitter import Node
except ImportError:
    Node = None  # type: ignore

# QueryCursor was removed in tree-sitter 0.24.0 - import it if available for backward compatibility
try:
    from tree_sitter import QueryCursor
except ImportError:
    QueryCursor = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)

# Tree-sitter queries for GraphQL syntax
GRAPHQL_QUERIES = {
    "type_definitions": """
        ; Object types
        (object_type_definition
            (name) @name
        ) @class

        ; Interface types
        (interface_type_definition
            (name) @name
        ) @interface

        ; Union types
        (union_type_definition
            (name) @name
        ) @enum

        ; Enum types
        (enum_type_definition
            (name) @name
        ) @enum

        ; Scalar types
        (scalar_type_definition
            (name) @name
        ) @property

        ; Input object types
        (input_object_type_definition
            (name) @name
        ) @class
    """,
    "operations": """
        ; Queries, Mutations, Subscriptions
        (operation_definition
            (operation_type) @op_type
            (name)? @name
        ) @function
    """,
    "fragments": """
        ; Named fragments
        (fragment_definition
            (fragment_name (name) @frag_name)
            (type_condition (named_type (name) @type_cond))
        ) @function
    """,
    "field_definitions": """
        ; Field definitions in type definitions
        (field_definition
            (name) @field_name
            (type) @field_type
        ) @field_def
    """,
    "directives": """
        ; Directive definitions
        (directive_definition
            (name) @directive_name
        ) @class

        ; Directive usage
        (directive
            (name) @directive_name
        ) @directive
    """,
}


class TreeSitterGraphqlParser(BaseTreeSitterParser):
    """
    GraphQL parser using tree-sitter.

    Extracts type definitions, operations, fragments, directives, and type relationships
    from GraphQL schema files and operation documents.

    Supports both Schema Definition Language (SDL) and executable documents
    (queries, mutations, subscriptions).

    Features:
        - Type definitions (object, interface, union, enum, scalar, input)
        - Operation definitions (query, mutation, subscription)
        - Fragment definitions
        - Directive definitions and usage
        - Type relationship mapping
        - Field argument extraction
        - Resolver requirement identification

    Grammar: https://github.com/bkegley/tree-sitter-graphql
    Version: Available in tree-sitter-language-pack

    Complexity:
        - Initialization: O(1)
        - Parsing: O(n) where n is source length
        - Query execution: O(m) where m is match count
    """

    def __init__(self):
        """Initialize the GraphQL parser with the tree-sitter-graphql grammar."""
        super().__init__("graphql")
        logger.debug("TreeSitterGraphqlParser initialized")

        # Cache for parsed tree (reused across extraction methods)
        self._current_tree = None

        # Caches for extracted metadata
        self._cached_types: list[dict[Any, Any]] | None = None
        self._cached_operations: list[dict[Any, Any]] | None = None
        self._cached_fragments: list[dict[Any, Any]] | None = None
        self._type_relationships_cache: dict[str, list[str]] | None = None
        self._cached_directives: dict[str, list[dict[Any, Any]]] | None = None

    def get_queries(self) -> dict[str, str]:
        """Returns Tree-sitter query patterns for GraphQL.

        Returns:
            Dictionary mapping query names to S-expression query strings.
            Keys: 'type_definitions', 'operations', 'fragments',
                  'field_definitions', 'directives'

        Complexity: O(1) - Returns static dictionary
        """
        return GRAPHQL_QUERIES

    def extract_type_definitions(self, byte_content: bytes) -> list[dict[Any, Any]]:
        """Extract all GraphQL type definitions from SDL.

        Extracts object types, interface types, union types, enum types,
        scalar types, and input object types from GraphQL schema files.

        Args:
            byte_content: GraphQL schema source as bytes

        Returns:
            List of type definition dictionaries with keys:
                - name: Type name
                - kind: Type kind (object/interface/union/enum/scalar/input)
                - line_number: Starting line number (1-indexed)
                - definition: Source code snippet
                - fields: List of field definitions (for object/interface/input types)
                - values: List of enum values (for enum types)
                - types: List of union member types (for union types)

        Complexity: O(n) where n is number of type definitions
        """
        if self._cached_types is not None:
            return self._cached_types

        # Parse if not already done
        if self._current_tree is None:
            self._current_tree = self.parser.parse(byte_content)

        type_defs = []
        root_node = self._current_tree.root_node

        # Map node types to GraphQL kinds
        kind_map = {
            "object_type_definition": "object",
            "interface_type_definition": "interface",
            "union_type_definition": "union",
            "enum_type_definition": "enum",
            "scalar_type_definition": "scalar",
            "input_object_type_definition": "input",
        }

        # Navigate through AST layers: source_file → document → definition → type_system_definition → type_definition
        for doc_node in root_node.children:
            if doc_node.type == "document":
                for def_node in doc_node.children:
                    if def_node.type == "definition":
                        # Check for type_system_definition layer
                        for sys_def_node in def_node.children:
                            if sys_def_node.type == "type_system_definition":
                                # Check for type_definition layer
                                for type_def_node in sys_def_node.children:
                                    if type_def_node.type == "type_definition":
                                        # Finally, find the actual type kind
                                        for type_kind_node in type_def_node.children:
                                            if type_kind_node.type in kind_map:
                                                type_def = self._extract_type_definition(
                                                    type_kind_node,
                                                    kind_map[type_kind_node.type],
                                                    byte_content,
                                                )
                                                if type_def:
                                                    type_defs.append(type_def)

        self._cached_types = type_defs
        return type_defs

    def _extract_type_definition(self, node: "Node", kind: str, byte_content: bytes) -> dict | None:
        """Extract details from a single type definition node.

        Args:
            node: Tree-sitter node representing a type definition
            kind: Type kind (object/interface/union/enum/scalar/input)
            byte_content: Source content as bytes

        Returns:
            Dictionary with type definition details, or None if extraction fails

        Complexity: O(f) where f is number of fields/values in the type
        """
        try:
            # Extract type name
            name_node = None
            for child in node.children:
                if child.type == "name":
                    name_node = child
                    break

            if not name_node:
                return None

            name = byte_content[name_node.start_byte : name_node.end_byte].decode("utf-8")
            start_line, end_line = get_node_location(name_node)
            line_number = start_line
            definition = byte_content[node.start_byte : node.end_byte].decode("utf-8")

            type_def = {
                "name": name,
                "kind": kind,
                "line_number": line_number,
                "definition": definition.strip(),
            }

            # Extract fields for object/interface/input types
            if kind in ("object", "interface", "input"):
                type_def["fields"] = self._extract_fields(node, byte_content)

            # Extract enum values
            elif kind == "enum":
                type_def["values"] = self._extract_enum_values(node, byte_content)

            # Extract union member types
            elif kind == "union":
                type_def["types"] = self._extract_union_types(node, byte_content)

            return type_def

        except Exception as e:
            logger.warning(f"Failed to extract type definition: {e}")
            return None

    def _extract_fields(self, type_node: "Node", byte_content: bytes) -> list[dict]:
        """Extract field definitions from object/interface/input types.

        Args:
            type_node: Type definition node
            byte_content: Source content as bytes

        Returns:
            List of field dictionaries with name, type, arguments

        Complexity: O(f) where f is number of fields
        """
        fields = []

        for child in type_node.children:
            # Object and interface types use fields_definition
            if child.type == "fields_definition":
                for field_def_node in child.children:
                    if field_def_node.type == "field_definition":
                        field = self._extract_field_definition(field_def_node, byte_content)
                        if field:
                            fields.append(field)

            # Input types use input_fields_definition with input_value_definition
            elif child.type == "input_fields_definition":
                for input_val_node in child.children:
                    if input_val_node.type == "input_value_definition":
                        field = self._extract_input_value_as_field(input_val_node, byte_content)
                        if field:
                            fields.append(field)

        return fields

    def _extract_input_value_as_field(
        self, input_val_node: "Node", byte_content: bytes
    ) -> dict | None:
        """Extract input value definition as a field.

        Args:
            input_val_node: Input value definition node
            byte_content: Source content as bytes

        Returns:
            Dictionary with field name and type

        Complexity: O(1)
        """
        try:
            field_name = None
            field_type = None

            for child in input_val_node.children:
                if child.type == "name":
                    field_name = byte_content[child.start_byte : child.end_byte].decode("utf-8")
                elif child.type == "type":
                    field_type = self._extract_type_name(child, byte_content)

            if not field_name or not field_type:
                return None

            return {"name": field_name, "type": field_type, "arguments": []}

        except Exception as e:
            logger.warning(f"Failed to extract input value definition: {e}")
            return None

    def _extract_field_definition(self, field_node: "Node", byte_content: bytes) -> dict | None:
        """Extract details from a single field definition.

        Args:
            field_node: Field definition node
            byte_content: Source content as bytes

        Returns:
            Dictionary with field name, type, and arguments

        Complexity: O(a) where a is number of arguments
        """
        try:
            field_name = None
            field_type = None
            arguments = []

            for child in field_node.children:
                if child.type == "name":
                    field_name = byte_content[child.start_byte : child.end_byte].decode("utf-8")
                elif child.type == "type":
                    field_type = self._extract_type_name(child, byte_content)
                elif child.type == "arguments_definition":
                    arguments = self._extract_arguments(child, byte_content)

            if not field_name or not field_type:
                return None

            return {"name": field_name, "type": field_type, "arguments": arguments}

        except Exception as e:
            logger.warning(f"Failed to extract field definition: {e}")
            return None

    def _extract_type_name(self, type_node: "Node", byte_content: bytes) -> str:
        """Extract type name from a type node, handling lists and non-null.

        Args:
            type_node: Type node
            byte_content: Source content as bytes

        Returns:
            Type name string (e.g., "String", "[User]!", "User!")

        Complexity: O(1)
        """
        return byte_content[type_node.start_byte : type_node.end_byte].decode("utf-8")

    def _extract_arguments(self, args_node: "Node", byte_content: bytes) -> list[dict]:
        """Extract argument definitions from a field or directive.

        Args:
            args_node: Arguments definition node
            byte_content: Source content as bytes

        Returns:
            List of argument dictionaries with name and type

        Complexity: O(a) where a is number of arguments
        """
        arguments = []

        for child in args_node.children:
            if child.type == "input_value_definition":
                arg_name = None
                arg_type = None

                for arg_child in child.children:
                    if arg_child.type == "name":
                        arg_name = byte_content[arg_child.start_byte : arg_child.end_byte].decode(
                            "utf-8"
                        )
                    elif arg_child.type == "type":
                        arg_type = self._extract_type_name(arg_child, byte_content)

                if arg_name and arg_type:
                    arguments.append({"name": arg_name, "type": arg_type})

        return arguments

    def _extract_enum_values(self, enum_node: "Node", byte_content: bytes) -> list[str]:
        """Extract enum value names from an enum type definition.

        Args:
            enum_node: Enum type definition node
            byte_content: Source content as bytes

        Returns:
            List of enum value names

        Complexity: O(v) where v is number of enum values
        """
        values = []

        for child in enum_node.children:
            if child.type == "enum_values_definition":
                for value_def in child.children:
                    if value_def.type == "enum_value_definition":
                        for value_child in value_def.children:
                            if value_child.type == "enum_value":
                                value_name = byte_content[
                                    value_child.start_byte : value_child.end_byte
                                ].decode("utf-8")
                                values.append(value_name)

        return values

    def _extract_union_types(self, union_node: "Node", byte_content: bytes) -> list[str]:
        """Extract member type names from a union type definition.

        Union member types are nested recursively in the AST, so we need
        to traverse all levels to collect all member type names.

        Args:
            union_node: Union type definition node
            byte_content: Source content as bytes

        Returns:
            List of union member type names

        Complexity: O(t) where t is number of union types
        """
        types: list[str] = []

        for child in union_node.children:
            if child.type == "union_member_types":
                # Recursively extract all types from nested union_member_types
                self._extract_union_types_recursive(child, byte_content, types)

        return types

    def _extract_union_types_recursive(
        self, node: "Node", byte_content: bytes, types: list[str]
    ) -> None:
        """Recursively extract union member types from nested structure.

        Args:
            node: Current union_member_types node
            byte_content: Source content as bytes
            types: Accumulated list of type names

        Complexity: O(n) where n is depth of nesting
        """
        for child in node.children:
            if child.type == "named_type":
                # Extract the type name
                for name_node in child.children:
                    if name_node.type == "name":
                        type_name = byte_content[name_node.start_byte : name_node.end_byte].decode(
                            "utf-8"
                        )
                        types.append(type_name)
            elif child.type == "union_member_types":
                # Recursively process nested union_member_types
                self._extract_union_types_recursive(child, byte_content, types)

    def extract_directives(self, byte_content: bytes) -> dict[str, list[dict[Any, Any]]]:
        """Extract directive definitions and usage from GraphQL schema.

        Args:
            byte_content: GraphQL schema source as bytes

        Returns:
            Dictionary with two keys:
                - definitions: List of directive definition dictionaries
                - usages: List of directive usage locations

        Complexity: O(d) where d is number of directives
        """
        if self._cached_directives is not None:
            return self._cached_directives

        # Parse if not already done
        if self._current_tree is None:
            self._current_tree = self.parser.parse(byte_content)

        directive_defs: list[dict[Any, Any]] = []
        directive_usages: list[dict[Any, Any]] = []

        self._extract_directives_recursive(
            self._current_tree.root_node, byte_content, directive_defs, directive_usages
        )

        result = {"definitions": directive_defs, "usages": directive_usages}
        self._cached_directives = result
        return result

    def _extract_directives_recursive(
        self,
        node: "Node",
        byte_content: bytes,
        definitions: list[dict],
        usages: list[dict],
    ) -> None:
        """Recursively extract directives from AST.

        Args:
            node: Current AST node
            byte_content: Source content as bytes
            definitions: Accumulated directive definitions
            usages: Accumulated directive usages

        Complexity: O(n) where n is number of nodes in AST
        """
        # Check if this node is a directive definition
        if node.type == "directive_definition":
            directive_def = self._extract_directive_definition(node, byte_content)
            if directive_def:
                definitions.append(directive_def)

        # Check if this node is a directive usage
        elif node.type == "directive":
            directive_usage = self._extract_directive_usage(node, byte_content)
            if directive_usage:
                usages.append(directive_usage)

        # Recurse through children
        for child in node.children:
            self._extract_directives_recursive(child, byte_content, definitions, usages)

    def _extract_directive_definition(self, node: "Node", byte_content: bytes) -> dict | None:
        """Extract details from a directive definition.

        Args:
            node: Directive definition node
            byte_content: Source content as bytes

        Returns:
            Dictionary with directive name, arguments, and locations

        Complexity: O(l) where l is number of locations
        """
        try:
            directive_name = None
            arguments = []
            locations: list[str] = []

            for child in node.children:
                if child.type == "name":
                    directive_name = byte_content[child.start_byte : child.end_byte].decode("utf-8")
                elif child.type == "arguments_definition":
                    arguments = self._extract_arguments(child, byte_content)
                elif child.type == "directive_locations":
                    # Recursively extract all locations from nested structure
                    self._extract_directive_locations_recursive(child, byte_content, locations)

            if not directive_name:
                return None

            start_line, end_line = get_node_location(node)
            return {
                "name": directive_name,
                "arguments": arguments,
                "locations": locations,
                "line_number": start_line,
            }

        except Exception as e:
            logger.warning(f"Failed to extract directive definition: {e}")
            return None

    def _extract_directive_locations_recursive(
        self, node: "Node", byte_content: bytes, locations: list[str]
    ) -> None:
        """Recursively extract directive locations from nested structure.

        Directive locations are nested recursively like union types.

        Args:
            node: Current directive_locations node
            byte_content: Source content as bytes
            locations: Accumulated list of location names

        Complexity: O(n) where n is depth of nesting
        """
        for child in node.children:
            if child.type == "directive_location":
                # Navigate through nested structure to get the actual location name
                for loc_child in child.children:
                    if loc_child.type in (
                        "type_system_directive_location",
                        "executable_directive_location",
                    ):
                        # Extract the location name (e.g., FIELD_DEFINITION, OBJECT)
                        for name_child in loc_child.children:
                            loc_name = byte_content[
                                name_child.start_byte : name_child.end_byte
                            ].decode("utf-8")
                            if loc_name not in ("|", " ", "\n"):
                                locations.append(loc_name)
            elif child.type == "directive_locations":
                # Recursively process nested directive_locations
                self._extract_directive_locations_recursive(child, byte_content, locations)

    def _extract_directive_usage(self, node: "Node", byte_content: bytes) -> dict | None:
        """Extract details from a directive usage.

        Args:
            node: Directive usage node
            byte_content: Source content as bytes

        Returns:
            Dictionary with directive name and line number

        Complexity: O(1)
        """
        try:
            directive_name = None

            for child in node.children:
                if child.type == "name":
                    directive_name = byte_content[child.start_byte : child.end_byte].decode("utf-8")
                    break

            if not directive_name:
                return None

            start_line, end_line = get_node_location(node)
            return {
                "name": directive_name,
                "line_number": start_line,
            }

        except Exception as e:
            logger.warning(f"Failed to extract directive usage: {e}")
            return None

    def extract_operations(self, byte_content: bytes) -> list[dict[Any, Any]]:
        """Extract GraphQL operations (query, mutation, subscription).

        Args:
            byte_content: GraphQL operation source as bytes

        Returns:
            List of operation dictionaries with keys:
                - type: Operation type (query/mutation/subscription)
                - name: Operation name (or None for anonymous)
                - line_number: Starting line number
                - definition: Source code snippet
                - variables: List of variable definitions (if any)

        Complexity: O(o) where o is number of operations
        """
        if self._cached_operations is not None:
            return self._cached_operations

        # Parse if not already done
        if self._current_tree is None:
            self._current_tree = self.parser.parse(byte_content)

        operations = []

        # Navigate through AST: source_file → document → definition → executable_definition → operation_definition
        for doc_node in self._current_tree.root_node.children:
            if doc_node.type == "document":
                for def_node in doc_node.children:
                    if def_node.type == "definition":
                        for exec_def_node in def_node.children:
                            if exec_def_node.type == "executable_definition":
                                for op_def_node in exec_def_node.children:
                                    if op_def_node.type == "operation_definition":
                                        operation = self._extract_operation_definition(
                                            op_def_node, byte_content
                                        )
                                        if operation:
                                            operations.append(operation)

        self._cached_operations = operations
        return operations

    def _extract_operation_definition(self, op_node: "Node", byte_content: bytes) -> dict | None:
        """Extract details from an operation definition.

        Args:
            op_node: Operation definition node
            byte_content: Source content as bytes

        Returns:
            Dictionary with operation type, name, and variables

        Complexity: O(v) where v is number of variables
        """
        try:
            op_type = None
            op_name = None
            variables = []

            for child in op_node.children:
                if child.type == "operation_type":
                    op_type = byte_content[child.start_byte : child.end_byte].decode("utf-8")
                elif child.type == "name":
                    op_name = byte_content[child.start_byte : child.end_byte].decode("utf-8")
                elif child.type == "variable_definitions":
                    variables = self._extract_variables(child, byte_content)

            # Default to 'query' if no operation type specified (shorthand syntax)
            if not op_type:
                op_type = "query"

            definition = byte_content[op_node.start_byte : op_node.end_byte].decode("utf-8")

            start_line, end_line = get_node_location(op_node)
            return {
                "type": op_type,
                "name": op_name,  # Can be None for anonymous operations
                "line_number": start_line,
                "definition": definition.strip(),
                "variables": variables,
            }

        except Exception as e:
            logger.warning(f"Failed to extract operation definition: {e}")
            return None

    def _extract_variables(self, vars_node: "Node", byte_content: bytes) -> list[dict]:
        """Extract variable definitions from an operation.

        Args:
            vars_node: Variable definitions node
            byte_content: Source content as bytes

        Returns:
            List of variable dictionaries with name and type

        Complexity: O(v) where v is number of variables
        """
        variables = []

        for child in vars_node.children:
            if child.type == "variable_definition":
                var_name = None
                var_type = None

                for var_child in child.children:
                    if var_child.type == "variable":
                        # Variable starts with $
                        for name_child in var_child.children:
                            if name_child.type == "name":
                                var_name = byte_content[
                                    name_child.start_byte : name_child.end_byte
                                ].decode("utf-8")
                    elif var_child.type == "type":
                        var_type = self._extract_type_name(var_child, byte_content)

                if var_name and var_type:
                    variables.append({"name": var_name, "type": var_type})

        return variables

    def extract_fragments(self, byte_content: bytes) -> list[dict[Any, Any]]:
        """Extract fragment definitions from GraphQL documents.

        Args:
            byte_content: GraphQL source as bytes

        Returns:
            List of fragment dictionaries with keys:
                - name: Fragment name
                - type_condition: Type the fragment applies to
                - line_number: Starting line number
                - definition: Source code snippet

        Complexity: O(f) where f is number of fragments
        """
        if self._cached_fragments is not None:
            return self._cached_fragments

        # Parse if not already done
        if self._current_tree is None:
            self._current_tree = self.parser.parse(byte_content)

        fragments = []

        # Navigate through AST: source_file → document → definition → executable_definition → fragment_definition
        for doc_node in self._current_tree.root_node.children:
            if doc_node.type == "document":
                for def_node in doc_node.children:
                    if def_node.type == "definition":
                        for exec_def_node in def_node.children:
                            if exec_def_node.type == "executable_definition":
                                for frag_def_node in exec_def_node.children:
                                    if frag_def_node.type == "fragment_definition":
                                        fragment = self._extract_fragment_definition(
                                            frag_def_node, byte_content
                                        )
                                        if fragment:
                                            fragments.append(fragment)

        self._cached_fragments = fragments
        return fragments

    def _extract_fragment_definition(self, frag_node: "Node", byte_content: bytes) -> dict | None:
        """Extract details from a fragment definition.

        Args:
            frag_node: Fragment definition node
            byte_content: Source content as bytes

        Returns:
            Dictionary with fragment name and type condition

        Complexity: O(1)
        """
        try:
            frag_name = None
            type_condition = None

            for child in frag_node.children:
                if child.type == "fragment_name":
                    for name_child in child.children:
                        if name_child.type == "name":
                            frag_name = byte_content[
                                name_child.start_byte : name_child.end_byte
                            ].decode("utf-8")
                elif child.type == "type_condition":
                    # Navigate through type_condition → named_type → name
                    for tc_child in child.children:
                        if tc_child.type == "named_type":
                            for type_child in tc_child.children:
                                if type_child.type == "name":
                                    type_condition = byte_content[
                                        type_child.start_byte : type_child.end_byte
                                    ].decode("utf-8")

            if not frag_name or not type_condition:
                return None

            definition = byte_content[frag_node.start_byte : frag_node.end_byte].decode("utf-8")

            start_line, end_line = get_node_location(frag_node)
            return {
                "name": frag_name,
                "type_condition": type_condition,
                "line_number": start_line,
                "definition": definition.strip(),
            }

        except Exception as e:
            logger.warning(f"Failed to extract fragment definition: {e}")
            return None

    def extract_type_relationships(self, byte_content: bytes) -> dict[str, list[str]]:
        """Extract type-to-type relationships from schema.

        Analyzes which types reference other types through their fields.
        Useful for understanding schema dependencies and structure.

        Args:
            byte_content: GraphQL schema source as bytes

        Returns:
            Dictionary mapping type names to lists of referenced type names.
            Example: {"User": ["Post", "Comment"], "Post": ["User"]}

        Complexity: O(t * f) where t is types and f is fields per type
        """
        if self._type_relationships_cache is not None:
            return self._type_relationships_cache

        # Get all type definitions
        types = self.extract_type_definitions(byte_content)

        relationships = {}

        for type_def in types:
            type_name = type_def["name"]
            referenced_types = set()

            # Only object, interface, and input types have fields
            if type_def["kind"] in ("object", "interface", "input"):
                for field in type_def.get("fields", []):
                    field_type = field["type"]
                    # Extract base type name (strip !, [])
                    base_type = self._extract_base_type_name(field_type)
                    if base_type and not self._is_builtin_type(base_type):
                        referenced_types.add(base_type)

                    # Also check argument types
                    for arg in field.get("arguments", []):
                        arg_type = arg["type"]
                        base_arg_type = self._extract_base_type_name(arg_type)
                        if base_arg_type and not self._is_builtin_type(base_arg_type):
                            referenced_types.add(base_arg_type)

            # Union types reference member types
            elif type_def["kind"] == "union":
                for member_type in type_def.get("types", []):
                    referenced_types.add(member_type)

            relationships[type_name] = sorted(referenced_types)

        self._type_relationships_cache = relationships
        return relationships

    def _extract_base_type_name(self, type_str: str) -> str | None:
        """Extract base type name from a GraphQL type string.

        Strips list wrappers ([]) and non-null markers (!) to get the base type.

        Args:
            type_str: GraphQL type string (e.g., "[User!]!", "String", "ID!")

        Returns:
            Base type name (e.g., "User", "String", "ID")

        Complexity: O(n) where n is length of type string
        """
        if not type_str:
            return None

        # Remove all [ ] ! characters
        base_type = type_str.replace("[", "").replace("]", "").replace("!", "").strip()
        return base_type if base_type else None

    def _is_builtin_type(self, type_name: str) -> bool:
        """Check if a type is a GraphQL built-in type.

        Args:
            type_name: Type name to check

        Returns:
            True if the type is a built-in scalar or introspection type

        Complexity: O(1)
        """
        builtin_types = {
            "Int",
            "Float",
            "String",
            "Boolean",
            "ID",
            "__Schema",
            "__Type",
            "__Field",
            "__InputValue",
            "__EnumValue",
            "__Directive",
            "__DirectiveLocation",
            "__TypeKind",
        }
        return type_name in builtin_types

    def extract_resolver_requirements(self, byte_content: bytes) -> dict[str, list[dict]]:
        """Identify fields that require custom resolvers.

        Fields returning object types (not scalars/enums) typically need resolvers
        on a GraphQL server. This method identifies those fields.

        Args:
            byte_content: GraphQL schema source as bytes

        Returns:
            Dictionary mapping type names to lists of fields requiring resolvers.
            Each field dict contains: name, type, complexity_hint

        Complexity: O(t * f) where t is types and f is fields per type
        """
        types = self.extract_type_definitions(byte_content)

        # First, categorize all types
        scalar_types = {"Int", "Float", "String", "Boolean", "ID"}
        enum_types = set()
        object_types = set()

        for type_def in types:
            if type_def["kind"] == "enum":
                enum_types.add(type_def["name"])
            elif type_def["kind"] in ("object", "interface"):
                object_types.add(type_def["name"])
            elif type_def["kind"] == "scalar":
                scalar_types.add(type_def["name"])

        # Now identify fields that return object types (need resolvers)
        resolver_requirements = {}

        for type_def in types:
            if type_def["kind"] in ("object", "interface"):
                type_name = type_def["name"]
                fields_needing_resolvers = []

                for field in type_def.get("fields", []):
                    field_type = field["type"]
                    base_type = self._extract_base_type_name(field_type)

                    # Field needs resolver if it returns an object type
                    if base_type in object_types:
                        complexity_hint = "simple"

                        # Higher complexity if field has arguments
                        if field.get("arguments"):
                            complexity_hint = "moderate"

                        # Even higher if it's a list of objects
                        if "[" in field_type:
                            complexity_hint = (
                                "high" if complexity_hint == "moderate" else "moderate"
                            )

                        fields_needing_resolvers.append(
                            {
                                "name": field["name"],
                                "type": field_type,
                                "complexity_hint": complexity_hint,
                            }
                        )

                if fields_needing_resolvers:
                    resolver_requirements[type_name] = fields_needing_resolvers

        return resolver_requirements

    def get_metadata(self, byte_content: bytes) -> dict:
        """Extract comprehensive GraphQL metadata in a unified interface.

        This is the primary method for accessing all GraphQL parser functionality.
        Returns a dictionary with all extracted schema information.

        Args:
            byte_content: GraphQL source as bytes

        Returns:
            Dictionary containing:
                - types: List of type definitions
                - operations: List of operations (queries/mutations/subscriptions)
                - fragments: List of fragment definitions
                - directives: Dict with definitions and usages
                - relationships: Type-to-type reference mapping
                - resolver_requirements: Fields requiring custom resolvers
                - statistics: Counts and summary information

        Complexity: O(n) where n is total nodes in schema
        """
        # Extract all components
        types = self.extract_type_definitions(byte_content)
        operations = self.extract_operations(byte_content)
        fragments = self.extract_fragments(byte_content)
        directives = self.extract_directives(byte_content)
        relationships = self.extract_type_relationships(byte_content)
        resolver_reqs = self.extract_resolver_requirements(byte_content)

        # Calculate statistics
        type_counts: dict[str, int] = {}
        for type_def in types:
            kind = type_def["kind"]
            type_counts[kind] = type_counts.get(kind, 0) + 1

        operation_counts: dict[str, int] = {}
        for op in operations:
            op_type = op["type"]
            operation_counts[op_type] = operation_counts.get(op_type, 0) + 1

        total_fields_needing_resolvers = sum(len(fields) for fields in resolver_reqs.values())

        statistics = {
            "total_types": len(types),
            "types_by_kind": type_counts,
            "total_operations": len(operations),
            "operations_by_type": operation_counts,
            "total_fragments": len(fragments),
            "total_directive_definitions": len(directives.get("definitions", [])),
            "total_directive_usages": len(directives.get("usages", [])),
            "types_with_relationships": len([r for r in relationships.values() if r]),
            "total_resolver_requirements": total_fields_needing_resolvers,
        }

        return {
            "types": types,
            "operations": operations,
            "fragments": fragments,
            "directives": directives,
            "relationships": relationships,
            "resolver_requirements": resolver_reqs,
            "statistics": statistics,
        }

    # Convenience methods for common queries

    def get_type_by_name(self, byte_content: bytes, type_name: str) -> dict | None:
        """Get a specific type definition by name.

        Args:
            byte_content: GraphQL schema source as bytes
            type_name: Name of the type to find

        Returns:
            Type definition dictionary or None if not found

        Complexity: O(t) where t is number of types
        """
        types = self.extract_type_definitions(byte_content)
        for type_def in types:
            if type_def["name"] == type_name:
                return type_def
        return None

    def get_types_by_kind(self, byte_content: bytes, kind: str) -> list[dict]:
        """Get all types of a specific kind.

        Args:
            byte_content: GraphQL schema source as bytes
            kind: Type kind (object/interface/union/enum/scalar/input)

        Returns:
            List of type definitions matching the kind

        Complexity: O(t) where t is number of types
        """
        types = self.extract_type_definitions(byte_content)
        return [t for t in types if t["kind"] == kind]

    def get_operation_by_name(self, byte_content: bytes, operation_name: str) -> dict | None:
        """Get a specific operation by name.

        Args:
            byte_content: GraphQL operation source as bytes
            operation_name: Name of the operation to find

        Returns:
            Operation dictionary or None if not found

        Complexity: O(o) where o is number of operations
        """
        operations = self.extract_operations(byte_content)
        for op in operations:
            if op["name"] == operation_name:
                return op
        return None

    def get_fragment_by_name(self, byte_content: bytes, fragment_name: str) -> dict | None:
        """Get a specific fragment by name.

        Args:
            byte_content: GraphQL source as bytes
            fragment_name: Name of the fragment to find

        Returns:
            Fragment dictionary or None if not found

        Complexity: O(f) where f is number of fragments
        """
        fragments = self.extract_fragments(byte_content)
        for frag in fragments:
            if frag["name"] == fragment_name:
                return frag
        return None

    def get_types_implementing_interface(
        self, _byte_content: bytes, _interface_name: str
    ) -> list[dict]:
        """Get all types that implement a specific interface.

        Note: This requires parsing the implements clause which is not yet
        implemented in the current extraction logic. Returns empty list for now.

        Args:
            byte_content: GraphQL schema source as bytes
            interface_name: Name of the interface

        Returns:
            List of type definitions implementing the interface

        Complexity: O(t) where t is number of types
        """
        # TODO: Implement interface implementation detection
        # This requires extracting the "implements" clause from type definitions
        return []

    def get_types_referencing_type(self, byte_content: bytes, target_type: str) -> list[str]:
        """Get all types that reference a specific type.

        Args:
            byte_content: GraphQL schema source as bytes
            target_type: Name of the type being referenced

        Returns:
            List of type names that reference the target type

        Complexity: O(t) where t is number of types
        """
        relationships = self.extract_type_relationships(byte_content)
        referencing_types = []

        for type_name, referenced_types in relationships.items():
            if target_type in referenced_types:
                referencing_types.append(type_name)

        return referencing_types
