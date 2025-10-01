# file: codeconcat/parser/language_parsers/tree_sitter_csharp_parser.py

import logging
import re
from typing import Dict, List, Set

try:
    import defusedxml.ElementTree as ET  # noqa: F401
except ImportError:
    # Fallback to standard ET with security warning
    import warnings

    warnings.warn(
        "defusedxml not installed - XML parsing may be vulnerable to XXE attacks. "
        "Install with: pip install defusedxml",
        UserWarning,
        stacklevel=2,
    )

from tree_sitter import Node, Query, QueryCursor

from ...base_types import Declaration
from ..doc_comment_utils import clean_xml_doc_comments, normalize_whitespace
from ..utils import get_node_location
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Define Tree-sitter queries for C#
# Simplified queries matching actual tree-sitter-csharp grammar structure
CSHARP_QUERIES = {
    "imports": """
        ; Using directives (standard and global)
        (using_directive
            (identifier) @import_path)
        (using_directive
            (qualified_name) @import_path)
    """,
    "declarations": """
        ; Namespace declarations
        (namespace_declaration
            [(identifier) (qualified_name)] @name
        ) @namespace

        ; File-scoped namespace (C# 10+)
        (file_scoped_namespace_declaration
            (identifier) @name
        ) @file_namespace

        ; Class declarations
        (class_declaration
            (modifier)* @modifiers
            (identifier) @name
        ) @class

        ; Record declarations (C# 9.0+)
        (record_declaration
            (modifier)* @modifiers
            (identifier) @name
        ) @record

        ; Interface declarations
        (interface_declaration
            (modifier)* @modifiers
            (identifier) @name
        ) @interface

        ; Struct declarations
        (struct_declaration
            (modifier)* @modifiers
            (identifier) @name
        ) @struct

        ; Enum declarations
        (enum_declaration
            (modifier)* @modifiers
            (identifier) @name
        ) @enum

        ; Method declarations
        (method_declaration
            (modifier)* @modifiers
            (identifier) @name
        ) @method

        ; Constructor declarations
        (constructor_declaration
            (modifier)* @modifiers
            (identifier) @name
        ) @constructor

        ; Destructor declarations
        (destructor_declaration
            (identifier) @name
        ) @destructor

        ; Property declarations
        (property_declaration
            (modifier)* @modifiers
            (identifier) @name
        ) @property

        ; Field declarations
        (field_declaration
            (modifier)* @modifiers
            (variable_declaration
                (variable_declarator
                    (identifier) @name
                ))
        ) @field

        ; Delegate declarations
        (delegate_declaration
            (modifier)* @modifiers
            (identifier) @name
        ) @delegate

        ; Event field declarations
        (event_field_declaration
            (modifier)* @modifiers
            (variable_declaration
                (variable_declarator
                    (identifier) @name
                ))
        ) @event

        ; Operator declarations
        (operator_declaration
            (modifier)* @modifiers
        ) @operator
    """,
    "doc_comments": """
        ; XML documentation comments
        (comment) @xml_doc (#match? @xml_doc "^///")

        ; Regular comments
        (comment) @comment
    """,
}


# Helper to clean XML doc comments
def _clean_csharp_doc_comment(xml_content: str) -> str:
    """Cleans C# XML documentation using shared doc_comment_utils.

    This method leverages the shared utilities for consistent
    XML doc comment cleaning with security (defusedxml).
    """
    if not xml_content:
        return ""
    return clean_xml_doc_comments(xml_content, extract_tags=True)


class TreeSitterCSharpParser(BaseTreeSitterParser):
    """Tree-sitter based parser for the C# language."""

    def __init__(self):
        """Initializes the C# Tree-sitter parser."""
        super().__init__(language_name="csharp")

    def get_queries(self) -> Dict[str, str]:
        """Returns the predefined Tree-sitter queries for C#."""
        return CSHARP_QUERIES

    def _run_queries(
        self, root_node: Node, byte_content: bytes
    ) -> tuple[List[Declaration], List[str]]:
        """Runs C#-specific queries and extracts declarations and imports."""
        queries = self.get_queries()
        imports: Set[str] = set()
        doc_comment_map = {}  # end_line -> raw comment_text (list of lines)

        # --- Pass 1: Extract Doc Comments --- #
        try:
            # Use modern Query() constructor and QueryCursor
            doc_query = Query(self.ts_language, queries.get("doc_comments", ""))
            doc_cursor = QueryCursor(doc_query)
            doc_captures = doc_cursor.captures(root_node)
            last_comment_line = -2
            current_doc_block: List[str] = []

            # Collect all comment nodes and sort by line number
            # Use a set to deduplicate (same node can match multiple captures)
            seen_node_ids = set()
            all_comment_nodes = []
            for _capture_name, nodes in doc_captures.items():
                for node in nodes:
                    if node.id not in seen_node_ids:
                        seen_node_ids.add(node.id)
                        all_comment_nodes.append(node)

            # Sort by line number
            all_comment_nodes.sort(key=lambda n: n.start_point[0])

            # Process comments in order
            for node in all_comment_nodes:
                # Strip leading '///' and optional space
                comment_text = byte_content[node.start_byte : node.end_byte].decode(
                    "utf8", errors="replace"
                )
                cleaned_line = re.sub(r"^///\s?", "", comment_text).strip()
                current_line = node.start_point[0]

                if current_line == last_comment_line + 1:
                    current_doc_block.append(cleaned_line)
                else:
                    if current_doc_block:
                        doc_comment_map[last_comment_line] = "\n".join(current_doc_block)
                    current_doc_block = [cleaned_line]

                last_comment_line = current_line

            if current_doc_block:
                doc_comment_map[last_comment_line] = "\n".join(current_doc_block)

        except Exception as e:
            logger.warning(f"Failed to execute C# doc_comments query: {e}", exc_info=True)

        # --- Pass 2: Extract Imports --- #
        try:
            import_query = Query(self.ts_language, queries.get("imports", ""))
            cursor = QueryCursor(import_query)
            captures = cursor.captures(root_node)
            logger.debug(f"Running C# imports query, found {len(captures)} captures.")

            # captures is a dict of {capture_name: [list of nodes]}
            for capture_name, nodes in captures.items():
                if capture_name in [
                    "import_path",
                    "static_import_path",
                    "aliased_namespace",
                    "global_import_path",
                ]:
                    for node in nodes:
                        import_path = byte_content[node.start_byte : node.end_byte].decode(
                            "utf8", errors="replace"
                        )
                        imports.add(import_path)
        except Exception as e:
            logger.warning(f"Failed to execute C# imports query: {e}", exc_info=True)

        # --- Pass 3: Extract Declarations Recursively --- #
        declarations = self._extract_declarations_recursive(
            root_node, byte_content, doc_comment_map
        )

        declarations.sort(key=lambda d: d.start_line)
        sorted_imports = sorted(imports)

        logger.debug(
            f"Tree-sitter C# extracted {len(declarations)} declarations and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports

    def _extract_declarations_recursive(
        self, parent_node: Node, byte_content: bytes, doc_comment_map: dict
    ) -> List[Declaration]:
        """Recursively extract declarations and build parent-child hierarchy.

        Args:
            parent_node: Node to search for declarations (compilation_unit, declaration_list, etc.)
            byte_content: Source code as bytes
            doc_comment_map: Map of line numbers to doc comments

        Returns:
            List of declarations found directly in parent_node
        """
        declarations = []

        # Types that can contain nested declarations
        container_types = {
            "namespace_declaration",
            "file_scoped_namespace_declaration",
            "class_declaration",
            "record_declaration",
            "struct_declaration",
            "interface_declaration",
            "enum_declaration",
        }

        # Map of node type to declaration kind
        type_to_kind = {
            "namespace_declaration": "namespace",
            "file_scoped_namespace_declaration": "file_namespace",
            "class_declaration": "class",
            "record_declaration": "record",
            "interface_declaration": "interface",
            "struct_declaration": "struct",
            "enum_declaration": "enum",
            "method_declaration": "method",
            "constructor_declaration": "constructor",
            "destructor_declaration": "destructor",
            "property_declaration": "property",
            "field_declaration": "field",
            "delegate_declaration": "delegate",
            "event_field_declaration": "event",
            "operator_declaration": "operator",
        }

        # Process direct children
        for child in parent_node.children:
            if not child.is_named:
                continue

            # Check if this is a declaration we care about
            if child.type in type_to_kind:
                kind = type_to_kind[child.type]
                name = self._extract_name(child, byte_content)
                modifiers = self._extract_modifiers(child, byte_content)
                signature = ""

                # Extract signature for methods, constructors, operators
                if kind in ["method", "constructor", "operator"]:
                    signature = self._extract_csharp_signature(child, byte_content)

                # Check for docstring
                docstring = doc_comment_map.get(child.start_point[0] - 1, "")
                if docstring:
                    docstring = _clean_csharp_doc_comment(docstring)

                start_line, end_line = get_node_location(child)

                # Create declaration
                decl = Declaration(
                    kind=kind,
                    name=name or f"<{kind}>",
                    start_line=start_line,
                    end_line=end_line,
                    docstring=docstring,
                    signature=signature,
                    modifiers=modifiers,
                )

                # Recursively process children if this is a container
                if child.type in container_types:
                    # Find declaration_list child
                    for decl_list_child in child.children:
                        if decl_list_child.type == "declaration_list":
                            decl.children = self._extract_declarations_recursive(
                                decl_list_child, byte_content, doc_comment_map
                            )
                            break

                declarations.append(decl)

            # Also recurse into declaration_list nodes directly
            elif child.type == "declaration_list":
                declarations.extend(
                    self._extract_declarations_recursive(child, byte_content, doc_comment_map)
                )

        return declarations

    def _extract_name(self, node: Node, byte_content: bytes) -> str | None:
        """Extract the name identifier from a declaration node."""
        # Direct identifier (classes, methods, etc.)
        for child in node.children:
            if child.type in ["identifier", "qualified_name"]:
                return byte_content[child.start_byte : child.end_byte].decode(
                    "utf8", errors="replace"
                )

        # For fields and events: variable_declaration -> variable_declarator -> identifier
        for child in node.children:
            if child.type == "variable_declaration":
                for var_child in child.children:
                    if var_child.type == "variable_declarator":
                        for decl_child in var_child.children:
                            if decl_child.type == "identifier":
                                return byte_content[
                                    decl_child.start_byte : decl_child.end_byte
                                ].decode("utf8", errors="replace")
        return None

    def _extract_modifiers(self, node: Node, byte_content: bytes) -> set[str]:
        """Extract modifiers from a declaration node."""
        modifiers = set()
        for child in node.children:
            if child.type == "modifier":
                modifier_text = byte_content[child.start_byte : child.end_byte].decode(
                    "utf8", errors="replace"
                )
                modifiers.add(modifier_text)
        return modifiers

    def _extract_csharp_signature(self, method_node: Node, byte_content: bytes) -> str:
        """Extract method/constructor/operator signature from declaration node.

        Extracts the complete signature including modifiers, return type, name,
        parameters, and constraints.

        Args:
            method_node: Method, constructor, or operator declaration node
            byte_content: Source code as bytes

        Returns:
            Method signature string (e.g., "public async Task<T> GetAsync<T>(int id) where T : class")
        """
        try:
            # Find the method body to determine signature end
            sig_end_byte = method_node.end_byte

            # Look for the opening brace, arrow expression, or semicolon to determine signature end
            for child in method_node.children:
                if child.type in ["block", "arrow_expression_clause", ";"]:
                    sig_end_byte = child.start_byte
                    break

            # Extract signature from start to body
            signature = (
                byte_content[method_node.start_byte : sig_end_byte]
                .decode("utf-8", errors="replace")
                .strip()
            )

            # Normalize whitespace
            signature = normalize_whitespace(signature)

            return signature
        except Exception as e:
            logger.debug(f"Failed to extract C# method signature: {e}")
            return ""
