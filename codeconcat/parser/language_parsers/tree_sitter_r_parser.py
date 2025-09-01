# file: codeconcat/parser/language_parsers/tree_sitter_r_parser.py

import logging
import re
from typing import Dict, List, Set

from tree_sitter import Node

from ...base_types import Declaration
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Define Tree-sitter queries for R
# Ref: https://github.com/tree-sitter/tree-sitter-r/blob/master/queries/tags.scm
R_QUERIES = {
    "imports": """
        ; Standard library/require calls
        (call
          function: (identifier) @func_name (#match? @func_name "^(library|require)$")
          arguments: (arguments (identifier) @library_name)
        ) @library_call

        ; Standard library/require calls with strings
        (call
          function: (identifier) @func_name (#match? @func_name "^(library|require)$")
          arguments: (arguments (string) @library_name)
        ) @library_call_string
    """,
    "declarations": """
        ; Function definition assignment
        (left_assignment
          (identifier) @name
          (function_definition)
        ) @function
    """,
    # Capture R comments and Roxygen documentation
    "doc_comments": """
        ; Standard comments
        (comment) @comment

        ; Roxygen comments (starting with #')
        (comment) @roxygen_comment (#match? @roxygen_comment "^#'")
    """,
}

# Patterns to clean R comments
R_LINE_COMMENT_PATTERN = re.compile(r"^#+\s?'?\s?")  # Handles #, ##, #', etc.
R_ROXYGEN_PATTERN = re.compile(r"^#'\s?")


def _clean_r_doc_comment(comment_block: List[str]) -> str:
    """Cleans a block of R comment lines."""
    cleaned_lines: list[str] = []
    is_roxygen = any(line.strip().startswith("#'") for line in comment_block)

    for line in comment_block:
        # Use the right pattern depending on comment type
        if is_roxygen:
            line = R_ROXYGEN_PATTERN.sub("", line)
        else:
            line = R_LINE_COMMENT_PATTERN.sub("", line)
        cleaned_lines.append(line.strip())
    return "\n".join(filter(None, cleaned_lines))


class TreeSitterRParser(BaseTreeSitterParser):
    """Tree-sitter based parser for the R language."""

    def __init__(self):
        """Initializes the R Tree-sitter parser."""
        super().__init__(language_name="r")

    def get_queries(self) -> Dict[str, str]:
        """Returns the predefined Tree-sitter queries for R."""
        return R_QUERIES

    def _run_queries(
        self, root_node: Node, byte_content: bytes
    ) -> tuple[List[Declaration], List[str]]:
        """Runs R-specific queries and extracts declarations and imports."""
        queries = self.get_queries()
        declarations = []
        imports: Set[str] = set()
        doc_comment_map = {}  # end_line -> List[str]

        # --- Pass 1: Extract Comments (potential docstrings) --- #
        try:
            doc_query = self.ts_language.query(queries.get("doc_comments", ""))
            doc_captures = doc_query.captures(root_node)
            last_comment_line = -2
            current_doc_block: List[str] = []

            # doc_captures is a dict: {capture_name: [list of nodes]}
            for _capture_name, nodes in doc_captures.items():
                for node in nodes:
                    comment_text = byte_content[node.start_byte : node.end_byte].decode(
                        "utf8", errors="replace"
                    )
                    current_start_line = node.start_point[0]
                    # R comments are always line comments
                    if current_start_line == last_comment_line + 1:
                        current_doc_block.append(comment_text)
                    else:
                        if current_doc_block:
                            doc_comment_map[last_comment_line] = current_doc_block
                        current_doc_block = [comment_text]
                    last_comment_line = current_start_line

            # Store the last block if it exists
            if current_doc_block:
                doc_comment_map[last_comment_line] = current_doc_block

        except Exception as e:
            logger.warning(f"Failed to execute R doc_comments query: {e}", exc_info=True)

        # --- Pass 2: Extract Imports and Declarations --- #
        for query_name, query_str in queries.items():
            if query_name == "doc_comments":
                continue

            try:
                query = self.ts_language.query(query_str)
                captures = query.captures(root_node)
                logger.debug(f"Running R query '{query_name}', found {len(captures)} captures.")

                if query_name == "imports":
                    # captures is a dict of {capture_name: [list of nodes]}
                    # Fixed capture unpacking pattern
                    for capture in captures.items():
                        if len(capture) == 2:
                            capture_name, nodes = capture
                        else:
                            continue
                        if capture_name == "library_name":
                            for node in nodes:
                                library_name = (
                                    byte_content[node.start_byte : node.end_byte]
                                    .decode("utf8", errors="replace")
                                    .strip("'\"")
                                )
                                imports.add(library_name)

                elif query_name == "declarations":
                    # Use matches for better structure
                    matches = query.matches(root_node)
                    for _match_id, captures_dict in matches:
                        declaration_node = None
                        name_node = None
                        kind = None
                        modifiers: set[str] = set()

                        # Check for function declarations
                        if "function" in captures_dict:
                            nodes = captures_dict["function"]
                            if nodes and len(nodes) > 0:
                                declaration_node = nodes[0]
                                kind = "function"

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

                            # Check for docstring (Roxygen comments)
                            raw_doc_block = doc_comment_map.get(
                                declaration_node.start_point[0] - 1, []
                            )
                            # Use Roxygen convention: comments starting with #' are often documentation
                            is_roxygen = any(
                                line.strip().startswith("#'") for line in raw_doc_block
                            )
                            docstring = (
                                _clean_r_doc_comment(raw_doc_block) if is_roxygen else ""
                            )  # Only use if looks like Roxygen

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
                logger.warning(f"Failed to execute R query '{query_name}': {e}", exc_info=True)

        # Declaration processing now happens inline

        declarations.sort(key=lambda d: d.start_line)
        sorted_imports = sorted(imports)

        logger.debug(
            f"Tree-sitter R extracted {len(declarations)} declarations and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports
