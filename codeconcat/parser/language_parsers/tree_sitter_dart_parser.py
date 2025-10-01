# file: codeconcat/parser/language_parsers/tree_sitter_dart_parser.py

"""
Enhanced Dart parser using tree-sitter.

Extracts declarations, imports, and Dart-specific constructs using the
UserNobody14/tree-sitter-dart grammar.

Supports Dart 3.x with features including:
- Function and method declarations with signatures
- Class, mixin, enum, and extension definitions
- Import, export, library, and part directives with prefixes
- Null safety annotations (?, !, late, required)
- Extension methods
- Mixins
- Async/await patterns
- Flutter widget tree patterns (StatefulWidget, StatelessWidget, State)
- State management patterns (initState, dispose, build methods)
- Documentation comment extraction
- Comprehensive modifier support (static, const, final, late, etc.)
"""

import logging
from typing import Dict, List, Set

from tree_sitter import Node, Query

# QueryCursor was removed in tree-sitter 0.24.0 - import it if available for backward compatibility
try:
    from tree_sitter import QueryCursor
except ImportError:
    QueryCursor = None  # type: ignore[assignment,misc]

from ...base_types import Declaration
from ..doc_comment_utils import clean_block_comments, clean_line_comments, normalize_whitespace
from ..utils import get_node_location
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Tree-sitter queries for Dart syntax
DART_QUERIES = {
    "imports": """
        ; Import specifications (actual import statements)
        (import_specification) @import_statement
    """,
    "declarations": """
        ; Class declarations
        (class_definition
            (identifier) @name
        ) @class

        ; Enum declarations
        (enum_declaration
            (identifier) @name
        ) @enum

        ; Extension declarations
        (extension_declaration
            (identifier) @name
        ) @extension

        ; Mixin declarations
        (mixin_declaration
            (identifier) @name
        ) @mixin

        ; Function signatures (includes top-level functions and methods)
        (function_signature
            (identifier) @name
        ) @function

        ; Getter signatures
        (getter_signature
            (identifier) @name
        ) @getter

        ; Setter signatures
        (setter_signature
            (identifier) @name
        ) @setter

        ; Constructor signatures
        (constructor_signature
            (identifier) @name
        ) @constructor

        ; Factory constructor signatures
        (factory_constructor_signature
            (identifier) @name
        ) @factory
    """,
    "doc_comments": """
        ; Dart documentation comments (/// or /** */)
        (documentation_comment) @doc_comment
        (comment) @comment
    """,
}


class TreeSitterDartParser(BaseTreeSitterParser):
    """
    Enhanced Dart parser using tree-sitter.

    Extracts declarations, imports, and Dart-specific constructs with full
    support for Dart documentation comments, modifiers, and signatures.

    Supports Dart 3.x and Flutter patterns.

    Features:
        - Function/method declarations with complete signatures
        - Class/mixin/enum/extension definitions with modifiers
        - Import, export, library, and part directives
        - Extension methods
        - Null safety annotations (?, !, late, required)
        - Mixins and mixin applications
        - Async/await patterns
        - Flutter widget patterns (StatefulWidget, State)
        - State management lifecycle methods
        - Documentation comment extraction
        - Comprehensive modifier support (static, const, final, late, async, etc.)

    Grammar: https://github.com/UserNobody14/tree-sitter-dart
    Version: Compatible with Dart 3.x

    Complexity:
        - Initialization: O(1)
        - Parsing: O(n) where n is source length
        - Query execution: O(m) where m is match count
    """

    def __init__(self):
        """Initialize the Dart parser with the tree-sitter-dart grammar."""
        super().__init__("dart")
        logger.debug("TreeSitterDartParser initialized")

    def get_queries(self) -> Dict[str, str]:
        """Returns Tree-sitter query patterns for Dart.

        Returns:
            Dictionary mapping query names to S-expression query strings.
            Keys: 'declarations', 'imports', 'doc_comments'

        Complexity: O(1) - Returns static dictionary
        """
        return DART_QUERIES

    def _run_queries(
        self, root_node: Node, byte_content: bytes
    ) -> tuple[List[Declaration], List[str]]:
        """Runs Dart-specific queries and extracts declarations and imports.

        Performs multi-pass extraction:
        1. Extract documentation comments and build location map
        2. Extract imports
        3. Extract declarations with modifiers, signatures, and doc comments

        Args:
            root_node: Root node of the parsed tree
            byte_content: Source code as bytes

        Returns:
            Tuple of (declarations list, imports list)
        """
        queries = self.get_queries()
        declarations = []
        imports: Set[str] = set()
        doc_map = {}  # line_before_declaration -> doc_text

        # --- Pass 1: Extract Documentation Comments --- #
        try:
            doc_query = Query(self.ts_language, queries.get("doc_comments", ""))
            doc_cursor = QueryCursor(doc_query)
            doc_captures = doc_cursor.captures(root_node)
            # doc_captures is a dict: {capture_name: [list of nodes]}
            for capture_name, nodes in doc_captures.items():
                if capture_name in ["doc_comment", "comment"]:
                    for node in nodes:
                        comment_text = byte_content[node.start_byte : node.end_byte].decode(
                            "utf-8", errors="replace"
                        )
                        # Only process doc comments (/// or /** */)
                        if comment_text.startswith("///") or comment_text.startswith("/**"):
                            # Store doc comment by the line it ends on (line before declaration)
                            end_line = node.end_point[0]
                            doc_map[end_line] = self._clean_dart_doc(comment_text)
        except Exception as e:
            logger.warning(f"Failed to extract Dart documentation comments: {e}", exc_info=True)

        # --- Pass 2: Extract Imports and Declarations --- #
        for query_name, query_str in queries.items():
            if query_name == "doc_comments":
                continue

            try:
                query = Query(self.ts_language, query_str)

                if query_name == "imports":
                    # Use captures for imports
                    cursor = QueryCursor(query)
                    captures = cursor.captures(root_node)
                    logger.debug(
                        f"Running Dart query '{query_name}', found {len(captures)} captures."
                    )

                    # captures is a dict of {capture_name: [list of nodes]}
                    for capture_name, nodes in captures.items():
                        if capture_name == "import_statement":
                            for node in nodes:
                                import_text = byte_content[node.start_byte : node.end_byte].decode(
                                    "utf-8", errors="replace"
                                )
                                # Extract import URI from the statement
                                # Format: import 'package:foo/bar.dart'; or import 'dart:async';
                                import_uri = self._extract_dart_import_uri(import_text)
                                if import_uri:
                                    imports.add(import_uri)

                elif query_name == "declarations":
                    # Use matches for better structure with declarations
                    cursor = QueryCursor(query)
                    matches = cursor.matches(root_node)

                    for _match_id, captures_dict in matches:
                        declaration_node = None
                        name = None
                        kind = None
                        modifiers = set()
                        signature = ""

                        # Determine declaration type
                        if "function" in captures_dict:
                            func_nodes = captures_dict["function"]
                            declaration_node = (
                                func_nodes[0] if isinstance(func_nodes, list) else func_nodes
                            )
                            kind = "function"

                            # Extract function name
                            if "name" in captures_dict:
                                name_nodes = captures_dict["name"]
                                name_node = (
                                    name_nodes[0] if isinstance(name_nodes, list) else name_nodes
                                )
                                name = byte_content[
                                    name_node.start_byte : name_node.end_byte
                                ].decode("utf-8", errors="replace")

                            # Build function signature
                            signature = self._extract_dart_signature(declaration_node, byte_content)

                            # Extract modifiers
                            modifiers = self._extract_dart_modifiers(declaration_node, byte_content)

                        elif "getter" in captures_dict:
                            getter_nodes = captures_dict["getter"]
                            declaration_node = (
                                getter_nodes[0] if isinstance(getter_nodes, list) else getter_nodes
                            )
                            kind = "getter"

                            if "name" in captures_dict:
                                name_nodes = captures_dict["name"]
                                name_node = (
                                    name_nodes[0] if isinstance(name_nodes, list) else name_nodes
                                )
                                name = byte_content[
                                    name_node.start_byte : name_node.end_byte
                                ].decode("utf-8", errors="replace")

                            signature = self._extract_dart_signature(declaration_node, byte_content)
                            modifiers = self._extract_dart_modifiers(declaration_node, byte_content)

                        elif "setter" in captures_dict:
                            setter_nodes = captures_dict["setter"]
                            declaration_node = (
                                setter_nodes[0] if isinstance(setter_nodes, list) else setter_nodes
                            )
                            kind = "setter"

                            if "name" in captures_dict:
                                name_nodes = captures_dict["name"]
                                name_node = (
                                    name_nodes[0] if isinstance(name_nodes, list) else name_nodes
                                )
                                name = byte_content[
                                    name_node.start_byte : name_node.end_byte
                                ].decode("utf-8", errors="replace")

                            signature = self._extract_dart_signature(declaration_node, byte_content)
                            modifiers = self._extract_dart_modifiers(declaration_node, byte_content)

                        elif "constructor" in captures_dict:
                            cons_nodes = captures_dict["constructor"]
                            declaration_node = (
                                cons_nodes[0] if isinstance(cons_nodes, list) else cons_nodes
                            )
                            kind = "constructor"

                            if "name" in captures_dict:
                                name_nodes = captures_dict["name"]
                                name_node = (
                                    name_nodes[0] if isinstance(name_nodes, list) else name_nodes
                                )
                                name = byte_content[
                                    name_node.start_byte : name_node.end_byte
                                ].decode("utf-8", errors="replace")

                            signature = self._extract_dart_signature(declaration_node, byte_content)

                        elif "factory" in captures_dict:
                            factory_nodes = captures_dict["factory"]
                            declaration_node = (
                                factory_nodes[0]
                                if isinstance(factory_nodes, list)
                                else factory_nodes
                            )
                            kind = "factory"
                            modifiers.add("factory")

                            if "name" in captures_dict:
                                name_nodes = captures_dict["name"]
                                name_node = (
                                    name_nodes[0] if isinstance(name_nodes, list) else name_nodes
                                )
                                name = byte_content[
                                    name_node.start_byte : name_node.end_byte
                                ].decode("utf-8", errors="replace")

                            signature = self._extract_dart_signature(declaration_node, byte_content)

                        elif "class" in captures_dict:
                            class_nodes = captures_dict["class"]
                            declaration_node = (
                                class_nodes[0] if isinstance(class_nodes, list) else class_nodes
                            )
                            kind = "class"

                            if "name" in captures_dict:
                                name_nodes = captures_dict["name"]
                                name_node = (
                                    name_nodes[0] if isinstance(name_nodes, list) else name_nodes
                                )
                                name = byte_content[
                                    name_node.start_byte : name_node.end_byte
                                ].decode("utf-8", errors="replace")

                            modifiers = self._extract_dart_modifiers(declaration_node, byte_content)

                        elif "enum" in captures_dict:
                            enum_nodes = captures_dict["enum"]
                            declaration_node = (
                                enum_nodes[0] if isinstance(enum_nodes, list) else enum_nodes
                            )
                            kind = "enum"

                            if "name" in captures_dict:
                                name_nodes = captures_dict["name"]
                                name_node = (
                                    name_nodes[0] if isinstance(name_nodes, list) else name_nodes
                                )
                                name = byte_content[
                                    name_node.start_byte : name_node.end_byte
                                ].decode("utf-8", errors="replace")

                        elif "mixin" in captures_dict:
                            mixin_nodes = captures_dict["mixin"]
                            declaration_node = (
                                mixin_nodes[0] if isinstance(mixin_nodes, list) else mixin_nodes
                            )
                            kind = "mixin"

                            if "name" in captures_dict:
                                name_nodes = captures_dict["name"]
                                name_node = (
                                    name_nodes[0] if isinstance(name_nodes, list) else name_nodes
                                )
                                name = byte_content[
                                    name_node.start_byte : name_node.end_byte
                                ].decode("utf-8", errors="replace")

                        elif "extension" in captures_dict:
                            ext_nodes = captures_dict["extension"]
                            declaration_node = (
                                ext_nodes[0] if isinstance(ext_nodes, list) else ext_nodes
                            )
                            kind = "extension"

                            if "name" in captures_dict:
                                name_nodes = captures_dict["name"]
                                name_node = (
                                    name_nodes[0] if isinstance(name_nodes, list) else name_nodes
                                )
                                name = byte_content[
                                    name_node.start_byte : name_node.end_byte
                                ].decode("utf-8", errors="replace")

                        # Add declaration if we have both node and name
                        if declaration_node and name:
                            start_line, end_line = get_node_location(declaration_node)

                            # Find associated documentation (look for comment on line before declaration)
                            doc_string = ""
                            for check_line in range(start_line - 1, max(0, start_line - 10), -1):
                                if check_line in doc_map:
                                    doc_string = doc_map[check_line]
                                    break

                            declarations.append(
                                Declaration(
                                    kind=kind or "unknown",
                                    name=name,
                                    start_line=start_line,
                                    end_line=end_line,
                                    docstring=doc_string,
                                    signature=signature,
                                    modifiers=modifiers,
                                )
                            )

            except Exception as e:
                logger.warning(f"Failed to execute Dart query '{query_name}': {e}", exc_info=True)

        # Sort declarations by start line
        declarations.sort(key=lambda d: d.start_line)
        sorted_imports = sorted(imports)

        logger.debug(
            f"Tree-sitter Dart extracted {len(declarations)} declarations "
            f"and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports

    def _extract_dart_signature(self, node: Node, byte_content: bytes) -> str:
        """Extract signature from declaration node.

        Extracts the complete signature including name, parameters, and return type.

        Args:
            node: Declaration node
            byte_content: Source code as bytes

        Returns:
            Signature string
        """
        try:
            # For most Dart declarations, extract from start to the opening brace or semicolon
            sig_end_byte = node.end_byte

            # Look for the opening brace or semicolon to determine signature end
            for child in node.children:
                if child.type in ["function_body", "{", ";"]:
                    sig_end_byte = child.start_byte
                    break

            # Extract signature from start to body
            signature = (
                byte_content[node.start_byte : sig_end_byte]
                .decode("utf-8", errors="replace")
                .strip()
            )

            # Normalize whitespace
            signature = normalize_whitespace(signature)

            return signature
        except Exception as e:
            logger.debug(f"Failed to extract Dart signature: {e}")
            return ""

    def _extract_dart_modifiers(self, node: Node, byte_content: bytes) -> Set[str]:
        """Extract modifiers from a declaration node.

        Extracts Dart modifiers such as:
        - Visibility: private (identified by leading _)
        - Mutability: const, final, late, var
        - Function: async, sync, static, external, abstract
        - Class: abstract, base, interface, final, sealed, mixin

        Args:
            node: Declaration node from tree-sitter
            byte_content: Source code as bytes

        Returns:
            Set of modifier strings
        """
        modifiers = set()

        try:
            # Look for modifier keywords in the node text
            node_text = byte_content[node.start_byte : node.end_byte].decode(
                "utf-8", errors="replace"
            )

            # Common Dart modifiers
            dart_modifiers = [
                "static",
                "const",
                "final",
                "late",
                "var",
                "async",
                "sync",
                "external",
                "abstract",
                "base",
                "interface",
                "sealed",
                "mixin",
                "required",
                "covariant",
                "factory",
            ]

            for modifier in dart_modifiers:
                # Use word boundaries to avoid false matches
                if f" {modifier} " in f" {node_text} " or node_text.startswith(f"{modifier} "):
                    modifiers.add(modifier)

            # Check for private (leading underscore in name)
            if "_" in node_text:
                # Look for identifier starting with underscore
                for child in node.children:
                    if child.type == "identifier":
                        id_text = byte_content[child.start_byte : child.end_byte].decode(
                            "utf-8", errors="replace"
                        )
                        if id_text.startswith("_"):
                            modifiers.add("private")
                            break

        except Exception as e:
            logger.debug(f"Failed to extract Dart modifiers: {e}")

        return modifiers

    def _extract_dart_import_uri(self, import_statement: str) -> str:
        """Extract URI from Dart import statement.

        Args:
            import_statement: Full import statement text

        Returns:
            Import URI (e.g., 'dart:async', 'package:flutter/material.dart')
        """
        try:
            # Extract the quoted URI
            # Format: import 'uri' [as prefix] [show/hide];
            import_statement = import_statement.strip()

            # Find the URI between quotes
            start_quote = import_statement.find("'")
            if start_quote == -1:
                start_quote = import_statement.find('"')

            if start_quote != -1:
                # Find the closing quote
                end_quote = import_statement.find("'", start_quote + 1)
                if end_quote == -1:
                    end_quote = import_statement.find('"', start_quote + 1)

                if end_quote != -1:
                    uri = import_statement[start_quote + 1 : end_quote]
                    return uri

        except Exception as e:
            logger.debug(f"Failed to extract Dart import URI: {e}")

        return ""

    def _clean_dart_doc(self, doc_text: str) -> str:
        """Clean Dart documentation comment text using shared utilities.

        Dart supports both /// line comments and /** block comments.

        Args:
            doc_text: Raw documentation comment text

        Returns:
            Cleaned documentation string
        """
        if not doc_text:
            return ""

        # Detect if this is a block comment or line comment
        is_block = doc_text.strip().startswith("/**")

        if is_block:
            # Use shared block comment cleaner for /** */ style
            lines = doc_text.split("\n")
            return clean_block_comments(lines, preserve_structure=False)
        else:
            # Use shared line comment cleaner for /// style
            lines = doc_text.split("\n")
            # Match /// style
            prefix_pattern = r"^///\s*"
            return clean_line_comments(lines, prefix_pattern=prefix_pattern)
