# file: codeconcat/parser/language_parsers/tree_sitter_java_parser.py

import logging
from typing import Dict, List, Set

from tree_sitter import Node, Query

# QueryCursor was removed in tree-sitter 0.24.0 - import it if available for backward compatibility
try:
    from tree_sitter import QueryCursor
except ImportError:
    QueryCursor = None  # type: ignore[assignment,misc]

from ...base_types import Declaration
from ..doc_comment_utils import clean_block_comments, clean_jsdoc_tags, normalize_whitespace
from ..utils import get_node_location
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Define Tree-sitter queries for Java
# Ref: https://github.com/tree-sitter/tree-sitter-java/blob/master/src/node-types.json
# Ref: https://github.com/tree-sitter/tree-sitter-java/blob/master/queries/tags.scm
JAVA_QUERIES = {
    "imports": """
        ; Standard imports - capture the entire import path
        (import_declaration
            (_) @import
        ) @import_stmt

        ; Package declaration (track base package)
        (package_declaration
            (_) @package
        ) @package_stmt
    """,
    "declarations": """
        ; Class declarations with annotations and modifiers
        (class_declaration
            (modifiers)? @modifiers
            (identifier) @name
            (type_parameters)? @type_params
            (superclass)? @superclass
            (super_interfaces)? @interfaces
            (class_body) @body
        ) @class

        ; Record declarations (Java 14+)
        (record_declaration
            (modifiers)? @modifiers
            (identifier) @name
            (formal_parameters) @record_params
            (class_body)? @body
        ) @record

        ; Interface declarations
        (interface_declaration
            (modifiers)? @modifiers
            (identifier) @name
            (type_parameters)? @type_params
            (extends_interfaces)? @extends
            (interface_body) @body
        ) @interface

        ; Enum declarations
        (enum_declaration
            (modifiers)? @modifiers
            (identifier) @name
            (super_interfaces)? @interfaces
            (enum_body) @body
        ) @enum

        ; Method declarations
        (method_declaration
            (modifiers)? @modifiers
            (type_parameters)? @method_type_params
            (_) @return_type
            (identifier) @name
            (formal_parameters) @params
            (throws)? @throws
            [(block) (";")]? @body
        ) @method

        ; Constructor declarations
        (constructor_declaration
            (modifiers)? @modifiers
            (type_parameters)? @constructor_type_params
            (identifier) @name
            (formal_parameters) @params
            (throws)? @throws
            (constructor_body) @body
        ) @constructor

        ; Field declarations
        (field_declaration
            (modifiers)? @modifiers
            (_) @field_type
            (variable_declarator
                (identifier) @name
            )
        ) @field

        ; Annotation type declarations
        (annotation_type_declaration
            (modifiers)? @modifiers
            (identifier) @name
            (annotation_type_body) @body
        ) @annotation_type
    """,
    # Query for extracting doc comments
    "doc_comments": """
        ; Javadoc block comments (/**...*/)
        (block_comment) @javadoc_comment

        ; Regular block comments (/*...*/)
        (block_comment) @block_comment

        ; Line comments (//...)
        (line_comment) @line_comment
    """,
}


class TreeSitterJavaParser(BaseTreeSitterParser):
    """Tree-sitter based parser for the Java language."""

    def __init__(self):
        """Initializes the Java Tree-sitter parser."""
        super().__init__(language_name="java")

    def get_queries(self) -> Dict[str, str]:
        """Returns the predefined Tree-sitter queries for Java."""
        return JAVA_QUERIES

    def _run_queries(
        self, root_node: Node, byte_content: bytes
    ) -> tuple[List[Declaration], List[str]]:
        """Runs Java-specific queries and extracts declarations and imports.

        Performs multi-pass extraction:
        1. Extract Javadoc comments (/** */) and build location map
        2. Extract imports (full package paths)
        3. Extract declarations with signatures and doc comments

        Args:
            root_node: Root node of the parsed tree
            byte_content: Source code as bytes

        Returns:
            Tuple of (declarations list, imports list)
        """
        queries = self.get_queries()
        declarations = []
        imports: Set[str] = set()
        doc_comment_map = {}  # end_line -> comment_text

        # --- Pass 1: Extract Doc Comments and map by end line --- #
        # We do this first to easily associate comments with the declaration below them
        try:
            doc_query = Query(self.ts_language, queries.get("doc_comments", ""))
            doc_captures = self._execute_query_with_cursor(doc_query, root_node)

            # doc_captures is a dict: {capture_name: [list of nodes]}
            for _capture_name, nodes in doc_captures.items():
                for node in nodes:
                    comment_text = byte_content[node.start_byte : node.end_byte].decode(
                        "utf8", errors="replace"
                    )
                    if comment_text.startswith("/**") and comment_text.endswith("*/"):
                        # Store Javadoc comments keyed by their end line
                        doc_comment_map[node.end_point[0]] = self._clean_javadoc(comment_text)
        except Exception as e:
            logger.warning(f"Failed to execute Java doc_comments query: {e}", exc_info=True)

        # --- Pass 2: Extract Imports and Declarations --- #
        for query_name, query_str in queries.items():
            if query_name == "doc_comments":
                continue  # Already processed

            try:
                query = Query(self.ts_language, query_str)

                if query_name == "imports":
                    # Use captures for imports
                    captures = self._execute_query_with_cursor(query, root_node)
                    logger.debug(
                        f"Running Java query '{query_name}', found {len(captures)} captures."
                    )

                    # captures is a dict of {capture_name: [list of nodes]}
                    for capture_name, nodes in captures.items():
                        if capture_name in ["import_statement", "import_path", "import"]:
                            for node in nodes:
                                import_text = byte_content[node.start_byte : node.end_byte].decode(
                                    "utf8", errors="replace"
                                )
                                # Store full import path
                                imports.add(import_text)

                elif query_name == "declarations":
                    # Use matches for better structure with declarations
                    matches = self._execute_query_matches(query, root_node)

                    for _match_id, captures_dict in matches:
                        declaration_node = None
                        name_node = None
                        kind = None
                        modifiers = set()
                        signature = ""

                        # Check for various declaration types
                        decl_types = [
                            "class",
                            "interface",
                            "enum",
                            "method",
                            "constructor",
                            "annotation_type",
                            "record",
                            "field",
                        ]

                        for decl_type in decl_types:
                            if decl_type in captures_dict:
                                nodes = captures_dict[decl_type]
                                if nodes and len(nodes) > 0:
                                    declaration_node = nodes[0]
                                    kind = decl_type
                                    break

                        # Get the name node
                        if "name" in captures_dict:
                            name_nodes = captures_dict["name"]
                            if name_nodes and len(name_nodes) > 0:
                                name_node = name_nodes[0]

                        # Get modifiers - extract from modifiers node
                        if "modifiers" in captures_dict:
                            modifiers_nodes = captures_dict["modifiers"]
                            if modifiers_nodes and len(modifiers_nodes) > 0:
                                modifiers_node = modifiers_nodes[0]
                                # Parse modifiers node children to extract keyword modifiers
                                for child in modifiers_node.children:
                                    if child.type in [
                                        "public",
                                        "private",
                                        "protected",
                                        "static",
                                        "final",
                                        "abstract",
                                        "synchronized",
                                        "native",
                                        "strictfp",
                                    ]:
                                        modifiers.add(child.type)

                        # Extract signature for methods and constructors
                        if declaration_node and kind in ["method", "constructor"]:
                            signature = self._extract_java_signature(declaration_node, byte_content)

                        # Add declaration if we have both node and name
                        if declaration_node and name_node:
                            name_text = byte_content[
                                name_node.start_byte : name_node.end_byte
                            ].decode("utf8", errors="replace")

                            # Find associated Javadoc (look for comment on line before declaration)
                            start_line, end_line = get_node_location(declaration_node)
                            docstring = ""
                            for check_line in range(start_line - 1, max(0, start_line - 20), -1):
                                if check_line in doc_comment_map:
                                    docstring = doc_comment_map[check_line]
                                    break

                            declarations.append(
                                Declaration(
                                    kind=kind or "unknown",
                                    name=name_text,
                                    start_line=start_line,
                                    end_line=end_line,
                                    docstring=docstring,
                                    signature=signature,
                                    modifiers=modifiers,
                                )
                            )

            except Exception as e:
                logger.warning(f"Failed to execute Java query '{query_name}': {e}", exc_info=True)

        # Sort declarations by start line
        declarations.sort(key=lambda d: d.start_line)
        # Sort imports alphabetically
        sorted_imports = sorted(imports)

        logger.debug(
            f"Tree-sitter Java extracted {len(declarations)} declarations and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports

    def _extract_java_signature(self, method_node: Node, byte_content: bytes) -> str:
        """Extract method/constructor signature from method or constructor declaration node.

        Extracts the complete signature including modifiers, type parameters, return type,
        name, parameters, and throws clause.

        Args:
            method_node: Method or constructor declaration node
            byte_content: Source code as bytes

        Returns:
            Method signature string (e.g., "public <T> T getName(String param) throws IOException")
        """
        try:
            # Find the method body to determine signature end
            sig_end_byte = method_node.end_byte

            # Look for the opening brace or semicolon to determine signature end
            for child in method_node.children:
                if child.type in ["block", "constructor_body", ";"]:
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
            logger.debug(f"Failed to extract Java method signature: {e}")
            return ""

    def _clean_javadoc(self, comment_text: str) -> str:
        """Cleans a Javadoc block comment using shared doc_comment_utils.

        This method now leverages the shared utilities for consistent
        comment cleaning across all parsers.
        """
        lines = comment_text.split("\n")
        # First, clean the block comment structure (/** */ and leading *)
        cleaned = clean_block_comments(lines, preserve_structure=True)
        # Then process Javadoc tags (@param, @return, @throws, etc.)
        return clean_jsdoc_tags(cleaned)
