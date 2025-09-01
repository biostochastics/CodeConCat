# file: codeconcat/parser/language_parsers/tree_sitter_julia_parser.py

import logging
import re
from typing import Dict, List, Set

from tree_sitter import Node

from ...base_types import Declaration
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Define Tree-sitter queries for Julia
# Ref: https://github.com/tree-sitter/tree-sitter-julia/blob/master/queries/tags.scm
JULIA_QUERIES = {
    "imports": """
        ; Simple import/using statements
        (import_statement
          (identifier) @import_path
        ) @import

        ; Import with selected identifiers
        (import_statement
          (selected_import
            (identifier) @import_path
          )
        ) @import_selected

        ; Module statements
        (module_statement
          (identifier) @import_path
        ) @module_statement
    """,
    "declarations": """
        ; Module definitions
        (module_definition
            name: (identifier) @name
        ) @module

        ; Function definitions with simple identifier
        (function_definition
            (signature (identifier) @name)
            body: (block_expression) @body
        ) @function

        ; Function definitions with call expression
        (function_definition
            (signature (call_expression
                (identifier) @name
            ))
        ) @function_call

        ; Macro definitions
        (macro_definition
            (signature (call_expression
                (identifier) @name
            ))
        ) @macro

        ; Struct definitions
        (struct_definition
            name: (identifier) @name
        ) @struct

        ; Abstract type definitions
        (abstract_definition
            name: (identifier) @name
        ) @abstract_type
    """,
    # Capture Julia docstrings (triple-quoted strings before declarations) and line_comments
    "doc_line_comments": """
        ; Regular line_comments
        (line_comment) @line_comment

        ; Julia docstrings - triple-quoted strings that appear before declarations
        (string_literal) @docstring
    """,
}

# Patterns to clean Julia line_comments
JULIA_LINE_COMMENT_PATTERN = re.compile(r"^#\s?")
JULIA_BLOCK_COMMENT_START_PATTERN = re.compile(r"^#=\s?")
JULIA_BLOCK_COMMENT_END_PATTERN = re.compile(r"\s*=#$")


def _clean_julia_doc_line_comment(line_comment_block_expression: List[str]) -> str:
    """Cleans a block_expression of Julia line_comment lines."""
    cleaned_lines: list[str] = []
    is_block_expression = (
        line_comment_block_expression[0].startswith("#=")
        if line_comment_block_expression
        else False
    )

    for i, line in enumerate(line_comment_block_expression):
        original_line = line  # Keep original for block_expression end check
        if is_block_expression:
            if i == 0:
                line = JULIA_BLOCK_COMMENT_START_PATTERN.sub("", line)
            # No standard line prefix like '*' for block_expression line_comments
            if original_line.strip().endswith("=#"):
                line = JULIA_BLOCK_COMMENT_END_PATTERN.sub("", line)
        else:  # Line line_comment
            line = JULIA_LINE_COMMENT_PATTERN.sub("", line)

        cleaned_lines.append(line.strip())

    return "\n".join(filter(None, cleaned_lines))


class TreeSitterJuliaParser(BaseTreeSitterParser):
    """Tree-sitter based parser for the Julia language."""

    def __init__(self):
        """Initializes the Julia Tree-sitter parser."""
        super().__init__(language_name="julia")

    def get_queries(self) -> Dict[str, str]:
        """Returns the predefined Tree-sitter queries for Julia."""
        return JULIA_QUERIES

    def _run_queries(
        self, root_node: Node, byte_content: bytes
    ) -> tuple[List[Declaration], List[str]]:
        """Runs Julia-specific queries and extracts declarations and imports."""
        queries = self.get_queries()
        declarations = []
        imports: Set[str] = set()
        doc_line_comment_map = {}  # end_line -> List[str]

        # --- Pass 1: Extract Comments (potential docstrings) --- #
        try:
            doc_query = self.ts_language.query(queries.get("doc_line_comments", ""))
            doc_captures = doc_query.captures(root_node)
            last_line_comment_line = -2
            current_doc_block_expression: List[str] = []

            # doc_captures is a dict: {capture_name: [list of nodes]}
            for _capture_name, nodes in doc_captures.items():
                for node in nodes:
                    line_comment_text = byte_content[node.start_byte : node.end_byte].decode(
                        "utf8", errors="replace"
                    )
                    current_start_line = node.start_point[0]
                    current_end_line = node.end_point[0]
                    is_block_expression = line_comment_text.startswith("#=")

                    if is_block_expression:
                        if current_doc_block_expression:
                            doc_line_comment_map[last_line_comment_line] = (
                                current_doc_block_expression
                            )
                        doc_line_comment_map[current_end_line] = line_comment_text.splitlines()
                        current_doc_block_expression = []
                        last_line_comment_line = current_end_line
                    else:  # Line line_comment
                        if current_start_line == last_line_comment_line + 1:
                            current_doc_block_expression.append(line_comment_text)
                        else:
                            if current_doc_block_expression:
                                doc_line_comment_map[last_line_comment_line] = (
                                    current_doc_block_expression
                                )
                            current_doc_block_expression = [line_comment_text]
                        last_line_comment_line = current_start_line

            # Store the last block_expression if it exists
            if current_doc_block_expression:
                doc_line_comment_map[last_line_comment_line] = current_doc_block_expression

        except Exception as e:
            logger.warning(f"Failed to execute Julia doc_line_comments query: {e}", exc_info=True)

        # --- Pass 2: Extract Imports and Declarations --- #
        for query_name, query_str in queries.items():
            if query_name == "doc_line_comments":
                continue

            try:
                query = self.ts_language.query(query_str)
                captures = query.captures(root_node)
                logger.debug(f"Running Julia query '{query_name}', found {len(captures)} captures.")

                if query_name == "imports":
                    # captures is a dict: {capture_name: [list of nodes]}
                    # Fixed capture unpacking pattern
                    for capture in captures.items():
                        if len(capture) == 2:
                            capture_name, nodes = capture
                        else:
                            continue
                        if capture_name in ["import_path", "imported_symbol"]:
                            for node in nodes:
                                import_path = byte_content[node.start_byte : node.end_byte].decode(
                                    "utf8", errors="replace"
                                )
                                # Handle scoped identifiers like Pkg.Operations
                                import_path = import_path.replace(
                                    ".", "::"
                                )  # Normalize to :: maybe?
                                imports.add(import_path)

                elif query_name == "declarations":
                    # Use matches for better structure
                    matches = query.matches(root_node)
                    for _match_id, captures_dict in matches:
                        declaration_node = None
                        name_node = None
                        kind = None
                        modifiers: set[str] = set()

                        # Check for various declaration types
                        decl_types = ["module", "function", "macro", "struct", "abstract_type"]

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

                        # Add declaration if we have both node and name
                        if declaration_node and name_node:
                            name_text = byte_content[
                                name_node.start_byte : name_node.end_byte
                            ].decode("utf8", errors="replace")

                            # Handle macro names that start with @
                            if kind == "macro" and not name_text.startswith("@"):
                                name_text = "@" + name_text

                            # Check for docstring
                            docstring_lines = doc_line_comment_map.get(
                                declaration_node.start_point[0] - 1, []
                            )
                            if docstring_lines:
                                docstring = _clean_julia_doc_line_comment(docstring_lines)
                            else:
                                docstring = ""

                            declarations.append(
                                Declaration(
                                    kind=kind or "unknown",
                                    name=name_text,
                                    start_line=declaration_node.start_point[0] + 1,
                                    end_line=declaration_node.end_point[0] + 1,
                                    docstring=docstring,
                                    modifiers=modifiers,
                                )
                            )

            except Exception as e:
                logger.warning(f"Failed to execute Julia query '{query_name}': {e}", exc_info=True)

        # Declaration processing now happens inline

        declarations.sort(key=lambda d: d.start_line)
        sorted_imports = sorted(imports)

        logger.debug(
            f"Tree-sitter Julia extracted {len(declarations)} declarations and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports
