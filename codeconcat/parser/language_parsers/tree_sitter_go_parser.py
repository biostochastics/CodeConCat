# file: codeconcat/parser/language_parsers/tree_sitter_go_parser.py

import logging
from typing import Dict, List, Set

from tree_sitter import Node

from ...base_types import Declaration
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
        """Runs Go-specific queries and extracts declarations and imports."""
        queries = self.get_queries()
        declarations: List[Declaration] = []
        imports: Set[str] = set()
        # Dictionary mapping end line numbers to accumulated doc comment text
        doc_comment_map: Dict[int, str] = {}  # end_line -> comment_text

        # --- Pass 1: Extract Doc Comments --- #
        # Go doc comments are consecutive line comments preceding a declaration
        try:
            doc_query = self.ts_language.query(queries.get("doc_comments", ""))
            doc_captures = doc_query.captures(root_node)
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
                            # Map the completed block to its end line
                            doc_comment_map[last_comment_line] = "\n".join(current_doc_block)
                        # Start new block
                        current_doc_block = [comment_text[2:].strip()]

                    last_comment_line = current_line

            # Store the last block if it exists
            if current_doc_block:
                doc_comment_map[last_comment_line] = "\n".join(current_doc_block)

        except Exception as e:
            logger.warning(f"Failed to execute Go doc_comments query: {e}", exc_info=True)

        # --- Pass 2: Extract Imports and Declarations --- #
        for query_name, query_str in queries.items():
            if query_name == "doc_comments":
                continue

            try:
                query = self.ts_language.query(query_str)
                captures = query.captures(root_node)
                logger.debug(f"Running Go query '{query_name}', found {len(captures)} captures.")

                if query_name == "imports":
                    # captures is a dict of {capture_name: [list of nodes]}
                    # Fixed capture unpacking pattern
                    for capture in captures.items():
                        if len(capture) == 2:
                            capture_name, nodes = capture
                        else:
                            continue
                        if capture_name == "import_path":
                            for node in nodes:
                                # String nodes include quotes, remove them
                                import_path = (
                                    byte_content[node.start_byte : node.end_byte]
                                    .decode("utf8", errors="replace")
                                    .strip('"')
                                )
                                imports.add(import_path)

                elif query_name == "declarations":
                    # Use matches for better structure
                    matches = query.matches(root_node)
                    for _match_id, captures_dict in matches:
                        declaration_node = None
                        name_node = None
                        kind = None
                        modifiers: set[str] = set()

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

                        # Add declaration if we have both
                        if declaration_node and name_node:
                            name_text = byte_content[
                                name_node.start_byte : name_node.end_byte
                            ].decode("utf8", errors="replace")

                            # Check for docstring
                            docstring = doc_comment_map.get(declaration_node.start_point[0] - 1, "")

                            # Use utility function for accurate line numbers
                            start_line, end_line = get_node_location(declaration_node)

                            declarations.append(
                                Declaration(
                                    kind=kind or "unknown",
                                    name=name_text,
                                    start_line=start_line,
                                    end_line=end_line,
                                    docstring=docstring,
                                    modifiers=modifiers,
                                )
                            )

            except Exception as e:
                logger.warning(f"Failed to execute Go query '{query_name}': {e}", exc_info=True)

        # Declaration processing now happens inline

        declarations.sort(key=lambda d: d.start_line)
        sorted_imports = sorted(imports)

        logger.debug(
            f"Tree-sitter Go extracted {len(declarations)} declarations and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports

    # No specific _clean_doc method needed for Go as comments are line-based
