# file: codeconcat/parser/language_parsers/tree_sitter_go_parser.py

import logging
from typing import Dict, List, Set

from tree_sitter import Node, Query

# QueryCursor was removed in tree-sitter 0.24.0 - import it if available for backward compatibility
try:
    from tree_sitter import QueryCursor
except ImportError:
    QueryCursor = None  # type: ignore[assignment,misc]

from ...base_types import Declaration
from ..doc_comment_utils import clean_line_comments, normalize_whitespace
from ..utils import get_node_location
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Define Tree-sitter queries for Go
# Ref: https://github.com/tree-sitter/tree-sitter-go/blob/master/queries/tags.scm

# Define valid declaration capture types for better maintainability
DECLARATION_CAPTURE_TYPES = frozenset(
    {
        "function",
        "method",
        "struct_type",
        "interface_type",
        "type_alias",
        "constant",
        "variable",
    }
)

GO_QUERIES = {
    "imports": """
        ; Import declarations
        (import_spec
            path: (interpreted_string_literal) @import_path
        )
    """,
    "declarations": """
        ; Function declarations
        (function_declaration
            name: (identifier) @name
        ) @function

        ; Method declarations
        (method_declaration
            name: (field_identifier) @name
        ) @method

        ; Type spec for structs and interfaces
        (type_spec
            name: (type_identifier) @name
            type: (struct_type)
        ) @struct_type

        (type_spec
            name: (type_identifier) @name
            type: (interface_type)
        ) @interface_type

        ; Variable declarations (including multiline blocks)
        (var_declaration
            (var_spec
                name: (identifier) @name
            )
        ) @variable

        ; Constant declarations (including multiline blocks)
        (const_declaration
            (const_spec
                name: (identifier) @name
            )
        ) @constant
    """,
    "doc_comments": """
        ; Line comments (potential doc comments)
        (comment) @line_comment (#match? @line_comment "^//")

        ; Doc comments (specifically those starting with `//`)
        (comment) @doc_comment (#match? @doc_comment "^// ")

        ; Godoc comments (specifically those starting with `///`)
        (comment) @godoc_comment (#match? @godoc_comment "^///")

        ; Package comments (at the top of a file)
        (package_clause
            (package_identifier) @package_name
        )
    """,
}


class TreeSitterGoParser(BaseTreeSitterParser):
    """Tree-sitter based parser for the Go language."""

    def __init__(self):
        """Initializes the Go Tree-sitter parser."""
        super().__init__(language_name="go")

    # Removed obsolete _find_type_node method

    def get_queries(self) -> Dict[str, str]:
        """Returns the predefined Tree-sitter queries for Go."""
        return GO_QUERIES

    def _run_queries(
        self, root_node: Node, byte_content: bytes
    ) -> tuple[List[Declaration], List[str]]:
        """Runs Go-specific queries and extracts declarations and imports.

        Performs multi-pass extraction:
        1. Extract doc comments (// style) and build location map
        2. Extract imports (full package paths)
        3. Extract declarations with signatures and doc comments

        Args:
            root_node: Root node of the parsed tree
            byte_content: Source code as bytes

        Returns:
            Tuple of (declarations list, imports list)
        """
        queries = self.get_queries()
        declarations: List[Declaration] = []
        imports: Set[str] = set()
        # Dictionary mapping end line numbers to accumulated doc comment text
        doc_comment_map: Dict[int, str] = {}  # end_line -> comment_text

        # --- Pass 1: Extract Doc Comments --- #
        # Go doc comments are consecutive line comments preceding a declaration
        try:
            doc_query = Query(self.ts_language, queries.get("doc_comments", ""))
            doc_captures = self._execute_query_with_cursor(doc_query, root_node)

            last_comment_line = -2
            current_doc_block: List[str] = []

            # doc_captures is a dict: {capture_name: [list of nodes]}
            for _capture_name, nodes in doc_captures.items():
                for node in nodes:
                    comment_text = (
                        byte_content[node.start_byte : node.end_byte]
                        .decode("utf8", errors="replace")
                        .strip()
                    )
                    current_line = node.start_point[0]

                    # Check if this comment continues the previous block
                    if current_line == last_comment_line + 1:
                        current_doc_block.append(comment_text[2:].strip())  # Remove // and strip
                    else:
                        # Start a new block if the previous one wasn't empty
                        if current_doc_block:
                            # Clean the completed block using shared utilities
                            cleaned_block = clean_line_comments(
                                current_doc_block, prefix_pattern=""
                            )
                            # Map the completed block to its end line
                            doc_comment_map[last_comment_line] = cleaned_block
                        # Start new block
                        current_doc_block = [comment_text[2:].strip()]

                    last_comment_line = current_line

            # Store the last block if it exists
            if current_doc_block:
                cleaned_block = clean_line_comments(current_doc_block, prefix_pattern="")
                doc_comment_map[last_comment_line] = cleaned_block

        except Exception as e:
            logger.warning(f"Failed to execute Go doc_comments query: {e}", exc_info=True)

        # --- Pass 2: Extract Imports and Declarations --- #
        for query_name, query_str in queries.items():
            if query_name == "doc_comments":
                continue

            try:
                query = Query(self.ts_language, query_str)

                if query_name == "imports":
                    # Use captures for imports
                    captures = self._execute_query_with_cursor(query, root_node)
                    logger.debug(
                        f"Running Go query '{query_name}', found {len(captures)} captures."
                    )

                    # captures is a dict of {capture_name: [list of nodes]}
                    for capture_name, nodes in captures.items():
                        if capture_name == "import_path":
                            for node in nodes:
                                # String nodes include quotes, remove them
                                import_path = (
                                    byte_content[node.start_byte : node.end_byte]
                                    .decode("utf8", errors="replace")
                                    .strip('"')
                                )
                                # Store full import path
                                imports.add(import_path)

                elif query_name == "declarations":
                    # Use matches for better structure with declarations
                    matches = self._execute_query_matches(query, root_node)

                    for _match_id, captures_dict in matches:
                        declaration_node = None
                        name_node = None
                        kind = None
                        modifiers: set[str] = set()
                        signature = ""

                        # Check for declaration types
                        for decl_type in DECLARATION_CAPTURE_TYPES:
                            if decl_type in captures_dict:
                                nodes = captures_dict[decl_type]
                                if nodes and len(nodes) > 0:
                                    declaration_node = nodes[0]
                                    kind = decl_type
                                    if kind == "struct_type":
                                        kind = "struct"
                                    elif kind == "interface_type":
                                        kind = "interface"
                                    break

                        # Get the name node
                        if "name" in captures_dict:
                            name_nodes = captures_dict["name"]
                            if name_nodes and len(name_nodes) > 0:
                                name_node = name_nodes[0]

                        # Extract signature for functions and methods
                        if declaration_node and kind in ["function", "method"]:
                            signature = self._extract_go_signature(declaration_node, byte_content)

                        # Add declaration if we have both node and name
                        if declaration_node and name_node:
                            name_text = byte_content[
                                name_node.start_byte : name_node.end_byte
                            ].decode("utf8", errors="replace")

                            # Find associated doc comment (look for comment on line before declaration)
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
                logger.warning(f"Failed to execute Go query '{query_name}': {e}", exc_info=True)

        # Sort declarations by start line
        declarations.sort(key=lambda d: d.start_line)
        sorted_imports = sorted(imports)

        logger.debug(
            f"Tree-sitter Go extracted {len(declarations)} declarations and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports

    def _extract_go_signature(self, func_node: Node, byte_content: bytes) -> str:
        """Extract function/method signature from function or method declaration node.

        Extracts the complete signature including name, parameters, and return type.

        Args:
            func_node: Function or method declaration node
            byte_content: Source code as bytes

        Returns:
            Function signature string (e.g., "func (r *Receiver) Name(param Type) ReturnType")
        """
        try:
            # Find the function body to determine signature end
            sig_end_byte = func_node.end_byte

            # Look for the opening brace to determine signature end
            for child in func_node.children:
                if child.type == "block":
                    sig_end_byte = child.start_byte
                    break

            # Extract signature from start to body
            signature = (
                byte_content[func_node.start_byte : sig_end_byte]
                .decode("utf-8", errors="replace")
                .strip()
            )

            # Normalize whitespace
            signature = normalize_whitespace(signature)

            return signature
        except Exception as e:
            logger.debug(f"Failed to extract Go function signature: {e}")
            return ""
