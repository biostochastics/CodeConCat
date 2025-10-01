# file: codeconcat/parser/language_parsers/tree_sitter_kotlin_parser.py

"""
Enhanced Kotlin parser using tree-sitter.

Extracts declarations, imports, and Kotlin-specific constructs using the
fwcd/tree-sitter-kotlin grammar.

Supports Kotlin 1.9+ with features including:
- Function and method declarations with signatures
- Class, interface, and object definitions
- Import statements with aliases
- Coroutines and suspend functions
- Extension functions
- Sealed classes, data classes, and value classes
- KDoc documentation extraction
- Companion objects
- Modifiers (suspend, inline, infix, operator, etc.)
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
from ..doc_comment_utils import clean_block_comments, normalize_whitespace
from ..utils import get_node_location
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Tree-sitter queries for Kotlin syntax
KOTLIN_QUERIES = {
    "imports": """
        ; Import statements
        (import_header
            (identifier) @import_path
        ) @import_statement

        ; Import with alias
        (import_header
            (identifier) @import_path_aliased
            (import_alias
                (type_identifier) @import_alias
            )
        ) @import_statement_aliased
    """,
    "declarations": """
        ; Function declarations
        ; Structure: fun <name> <params> [: <return_type>] <body>
        (function_declaration
            (modifiers)? @modifiers
            (simple_identifier) @name
            (function_value_parameters)? @params
        ) @function

        ; Class and Interface declarations
        ; Structure: [class|interface] <name> [<primary_constructor>] [<class_body>]
        ; Note: Interfaces also use class_declaration node type
        (class_declaration
            (modifiers)? @modifiers
            (type_identifier) @name
            (primary_constructor)? @primary_constructor
            (class_body)? @class_body
        ) @class

        ; Object declarations (singletons and companion objects)
        ; Structure: object <name> [<class_body>]
        (object_declaration
            (modifiers)? @modifiers
            (type_identifier) @name
        ) @object

        ; Companion objects
        (companion_object
            (modifiers)? @modifiers
            (type_identifier)? @companion_name
        ) @companion

        ; Property declarations (top-level and class-level)
        ; Structure: [val|var] <name> [: <type>] [= <init>]
        (property_declaration
            (modifiers)? @modifiers
            (variable_declaration
                (simple_identifier) @name
            )
        ) @property
    """,
    "doc_comments": """
        ; KDoc comments (/** ... */)
        (multiline_comment) @kdoc (#match? @kdoc "^/\\\\*\\\\*")
    """,
}


class TreeSitterKotlinParser(BaseTreeSitterParser):
    """
    Enhanced Kotlin parser using tree-sitter.

    Extracts declarations, imports, and Kotlin-specific constructs with full
    support for KDoc documentation, modifiers, and signatures.

    Supports Kotlin 1.9 and above.

    Features:
        - Function/method declarations with complete signatures
        - Class/interface/object definitions with modifiers
        - Import statements with alias support
        - Extension functions
        - Data classes, sealed classes, value classes
        - Companion objects
        - Property declarations
        - KDoc documentation extraction
        - Comprehensive modifier support (suspend, inline, infix, operator, etc.)

    Grammar: https://github.com/fwcd/tree-sitter-kotlin
    Version: 0.3.x

    Complexity:
        - Initialization: O(1)
        - Parsing: O(n) where n is source length
        - Query execution: O(m) where m is match count
    """

    def __init__(self):
        """Initialize the Kotlin parser with the tree-sitter-kotlin grammar."""
        super().__init__("kotlin")
        logger.debug("TreeSitterKotlinParser initialized")

    def get_queries(self) -> Dict[str, str]:
        """Returns Tree-sitter query patterns for Kotlin.

        Returns:
            Dictionary mapping query names to S-expression query strings.
            Keys: 'declarations', 'imports', 'doc_comments'

        Complexity: O(1) - Returns static dictionary
        """
        return KOTLIN_QUERIES

    def _run_queries(
        self, root_node: Node, byte_content: bytes
    ) -> tuple[List[Declaration], List[str]]:
        """Runs Kotlin-specific queries and extracts declarations and imports.

        Performs multi-pass extraction:
        1. Extract KDoc comments and build location map
        2. Extract imports with alias support
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
        kdoc_map = {}  # line_before_declaration -> kdoc_text

        # --- Pass 1: Extract KDoc Comments --- #
        try:
            doc_query = Query(self.ts_language, queries.get("doc_comments", ""))
            doc_cursor = QueryCursor(doc_query)
            doc_captures = doc_cursor.captures(root_node)
            # doc_captures is a dict: {capture_name: [list of nodes]}
            for capture_name, nodes in doc_captures.items():
                if capture_name == "kdoc":
                    for node in nodes:
                        comment_text = byte_content[node.start_byte : node.end_byte].decode(
                            "utf-8", errors="replace"
                        )
                        # Store KDoc by the line it ends on (line before declaration)
                        end_line = node.end_point[0]
                        kdoc_map[end_line] = self._clean_kdoc(comment_text)
        except Exception as e:
            logger.warning(f"Failed to extract Kotlin KDoc comments: {e}", exc_info=True)

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
                        f"Running Kotlin query '{query_name}', found {len(captures)} captures."
                    )

                    # captures is a dict of {capture_name: [list of nodes]}
                    for capture_name, nodes in captures.items():
                        if capture_name in ["import_path", "import_path_aliased"]:
                            for node in nodes:
                                import_text = byte_content[node.start_byte : node.end_byte].decode(
                                    "utf-8", errors="replace"
                                )
                                # Store the full import path
                                imports.add(import_text)

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
                            signature = self._extract_function_signature(
                                declaration_node, byte_content
                            )

                            # Extract modifiers from the function
                            if "modifiers" in captures_dict:
                                mod_nodes = captures_dict["modifiers"]
                                if mod_nodes:
                                    mod_node = (
                                        mod_nodes[0] if isinstance(mod_nodes, list) else mod_nodes
                                    )
                                    modifiers = self._extract_modifiers(mod_node, byte_content)

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

                            # Extract modifiers
                            if "modifiers" in captures_dict:
                                mod_nodes = captures_dict["modifiers"]
                                if mod_nodes:
                                    mod_node = (
                                        mod_nodes[0] if isinstance(mod_nodes, list) else mod_nodes
                                    )
                                    modifiers = self._extract_modifiers(mod_node, byte_content)

                        elif "object" in captures_dict:
                            obj_nodes = captures_dict["object"]
                            declaration_node = (
                                obj_nodes[0] if isinstance(obj_nodes, list) else obj_nodes
                            )
                            kind = "object"

                            if "name" in captures_dict:
                                name_nodes = captures_dict["name"]
                                name_node = (
                                    name_nodes[0] if isinstance(name_nodes, list) else name_nodes
                                )
                                name = byte_content[
                                    name_node.start_byte : name_node.end_byte
                                ].decode("utf-8", errors="replace")

                        elif "companion" in captures_dict:
                            comp_nodes = captures_dict["companion"]
                            declaration_node = (
                                comp_nodes[0] if isinstance(comp_nodes, list) else comp_nodes
                            )
                            kind = "object"
                            modifiers.add("companion")

                            # Companion objects may have optional name
                            if (
                                "companion_name" in captures_dict
                                and captures_dict["companion_name"]
                            ):
                                name_nodes = captures_dict["companion_name"]
                                name_node = (
                                    name_nodes[0] if isinstance(name_nodes, list) else name_nodes
                                )
                                name = byte_content[
                                    name_node.start_byte : name_node.end_byte
                                ].decode("utf-8", errors="replace")
                            else:
                                name = "Companion"

                        elif "property" in captures_dict:
                            prop_nodes = captures_dict["property"]
                            declaration_node = (
                                prop_nodes[0] if isinstance(prop_nodes, list) else prop_nodes
                            )
                            kind = "property"

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

                            # Find associated KDoc (look for comment on line before declaration)
                            kdoc = ""
                            for check_line in range(start_line - 1, max(0, start_line - 10), -1):
                                if check_line in kdoc_map:
                                    kdoc = kdoc_map[check_line]
                                    break

                            declarations.append(
                                Declaration(
                                    kind=kind or "unknown",
                                    name=name,
                                    start_line=start_line,
                                    end_line=end_line,
                                    docstring=kdoc,
                                    signature=signature,
                                    modifiers=modifiers,
                                )
                            )

            except Exception as e:
                logger.warning(f"Failed to execute Kotlin query '{query_name}': {e}", exc_info=True)

        # Sort declarations by start line
        declarations.sort(key=lambda d: d.start_line)
        sorted_imports = sorted(imports)

        logger.debug(
            f"Tree-sitter Kotlin extracted {len(declarations)} declarations "
            f"and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports

    def _extract_function_signature(self, func_node: Node, byte_content: bytes) -> str:
        """Extract function signature from function declaration node.

        Extracts the complete signature including name, parameters, and return type.

        Args:
            func_node: Function declaration node
            byte_content: Source code as bytes

        Returns:
            Function signature string (e.g., "fun greet(name: String): String")
        """
        try:
            # Find the function body or end of signature
            sig_end_byte = func_node.end_byte

            # Look for the opening brace or assignment operator to determine signature end
            for child in func_node.children:
                if child.type in ["function_body", "="]:
                    sig_end_byte = child.start_byte
                    break

            # Extract signature from start to body/assignment
            signature = (
                byte_content[func_node.start_byte : sig_end_byte]
                .decode("utf-8", errors="replace")
                .strip()
            )

            # Normalize whitespace
            signature = normalize_whitespace(signature)

            return signature
        except Exception as e:
            logger.debug(f"Failed to extract function signature: {e}")
            return ""

    def _extract_modifiers(self, modifiers_node: Node, byte_content: bytes) -> Set[str]:
        """Extract modifiers from a modifiers node.

        Extracts Kotlin modifiers such as:
        - Visibility: public, private, protected, internal
        - Inheritance: open, final, abstract, sealed
        - Function: suspend, inline, infix, operator, tailrec
        - Class: data, enum, annotation, inner, value

        Args:
            modifiers_node: Modifiers node from tree-sitter
            byte_content: Source code as bytes

        Returns:
            Set of modifier strings
        """
        modifiers = set()

        try:
            # Iterate through all children of the modifiers node
            for child in modifiers_node.children:
                if child.type in [
                    "visibility_modifier",
                    "inheritance_modifier",
                    "function_modifier",
                    "class_modifier",
                    "member_modifier",
                    "parameter_modifier",
                ]:
                    modifier_text = (
                        byte_content[child.start_byte : child.end_byte]
                        .decode("utf-8", errors="replace")
                        .strip()
                    )

                    if modifier_text:
                        modifiers.add(modifier_text)
        except Exception as e:
            logger.debug(f"Failed to extract modifiers: {e}")

        return modifiers

    def _clean_kdoc(self, kdoc_text: str) -> str:
        """Clean KDoc comment text using shared utilities.

        KDoc uses JavaDoc-style /** ... */ comments. This method uses the
        shared clean_block_comments utility for consistency.

        Args:
            kdoc_text: Raw KDoc comment text

        Returns:
            Cleaned documentation string
        """
        if not kdoc_text:
            return ""

        lines = kdoc_text.split("\n")
        # Use shared block comment cleaner for /** */ style
        return clean_block_comments(lines, preserve_structure=False)
