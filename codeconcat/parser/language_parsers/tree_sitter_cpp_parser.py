# file: codeconcat/parser/language_parsers/tree_sitter_cpp_parser.py

import logging
import re
from typing import Dict, List, Set

from tree_sitter import Node

from ...base_types import Declaration
from ..utils import get_node_location
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Define Tree-sitter queries for C++
# Ref: https://github.com/tree-sitter/tree-sitter-cpp/blob/master/queries/tags.scm
# Note: C++ parsing is complex; these queries capture common constructs but may miss edge cases.
CPP_QUERIES = {
    "imports": """
        ; Include directives
        (preproc_include
            path: [(string_literal) (system_lib_string)] @import_path)
    """,
    "declarations": """
        ; Class definitions
        (class_specifier
            name: (type_identifier) @name
        ) @class

        ; Struct definitions
        (struct_specifier
            name: (type_identifier) @name
        ) @struct

        ; Union definitions
        (union_specifier
            name: (type_identifier) @name
        ) @union

        ; Enum definitions
        (enum_specifier
            name: (type_identifier) @name
        ) @enum

        ; Function definitions
        (function_definition
            declarator: (function_declarator
                declarator: (identifier) @name
            )
        ) @function

        ; Function definitions with field identifier
        (function_definition
            declarator: (function_declarator
                declarator: (field_identifier) @name
            )
        ) @function_field

        ; Function definitions with qualified identifier
        (function_definition
            declarator: (function_declarator
                declarator: (qualified_identifier) @name
            )
        ) @function_qualified

        ; Namespace definitions
        (namespace_definition
            name: (namespace_identifier)? @name
        ) @namespace
    """,
    # Enhanced doc comment capture including Doxygen and regular comments
    "doc_comments": """
        ; Doxygen-style line comments
        (comment) @doxygen_comment (#match? @doxygen_comment "^///|^//!")

        ; Doxygen-style block comments
        (comment) @doxygen_block (#match? @doxygen_block "^/\\\\*\\\\*|^/\\\\*!")

        ; C++ style line comments
        (comment) @cpp_comment (#match? @cpp_comment "^//")

        ; C style block comments
        (comment) @c_comment (#match? @c_comment "^/\\*")
    """,
}

# Patterns to clean Doxygen comments
DOC_COMMENT_START_PATTERN = re.compile(r"^(/\*\*<?|/\*!<?|///<?|//!?)\s?")
# Additional patterns for matching Doxygen comment formats
DOC_COMMENT_LINE_PREFIX_PATTERN = re.compile(r"^\s*\*\s?")
DOC_COMMENT_END_PATTERN = re.compile(r"\s*\*/$")


def _clean_cpp_doc_comment(comment_block: List[str]) -> str:
    """Cleans a block of Doxygen comment lines."""
    cleaned_lines: list[str] = []
    is_block = comment_block[0].startswith(("/**", "/*!")) if comment_block else False

    for i, line in enumerate(comment_block):
        original_line = line  # Keep original for block end check
        if i == 0:
            line = DOC_COMMENT_START_PATTERN.sub("", line)
        if is_block:
            line = DOC_COMMENT_LINE_PREFIX_PATTERN.sub("", line)
        # Check original line for block comment end marker
        if is_block and original_line.endswith("*/"):
            line = DOC_COMMENT_END_PATTERN.sub("", line)

        cleaned_lines.append(line.strip())
    # Join lines, filtering empty ones that might result from cleaning
    return "\n".join(filter(None, cleaned_lines))


class TreeSitterCppParser(BaseTreeSitterParser):
    """Tree-sitter based parser for the C/C++ language."""

    def __init__(self):
        """Initializes the C++ Tree-sitter parser."""
        # Use 'cpp' grammar for both C and C++
        super().__init__(language_name="cpp")

    def get_queries(self) -> Dict[str, str]:
        """Returns the predefined Tree-sitter queries for C++."""
        return CPP_QUERIES

    def _run_queries(
        self, root_node: Node, byte_content: bytes
    ) -> tuple[List[Declaration], List[str]]:
        """Runs C++-specific queries and extracts declarations and imports."""
        queries = self.get_queries()
        declarations = []
        imports: Set[str] = set()
        declaration_map: dict[int, dict] = {}  # node_id -> declaration info
        doc_comment_map = {}  # end_line -> raw comment_text (list of lines)
        node_parent_map = {
            child.id: root_node.id for child in root_node.children
        }  # Precompute parent IDs
        for child in root_node.children:
            for grandchild in child.children:
                node_parent_map[grandchild.id] = child.id
                # Add more levels if needed, or make recursive

        # --- Pass 1: Extract Doc Comments --- #
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
                    current_end_line = node.end_point[0]
                    is_block_comment = comment_text.startswith(("/**", "/*!"))

                    if is_block_comment:
                        # Store previous block if it exists and is different
                        if current_doc_block:
                            doc_comment_map[last_comment_line] = current_doc_block
                        # Store the new block comment immediately, keyed by its end line
                        doc_comment_map[current_end_line] = comment_text.splitlines()
                        current_doc_block = []  # Reset tracker
                        last_comment_line = current_end_line  # Update last line seen
                    elif comment_text.startswith(("///", "//!")):
                        # If it continues a line comment block
                        if current_start_line == last_comment_line + 1:
                            current_doc_block.append(comment_text)
                        else:
                            # Store previous block if any
                            if current_doc_block:
                                doc_comment_map[last_comment_line] = current_doc_block
                            # Start new line comment block
                            current_doc_block = [comment_text]
                        last_comment_line = current_start_line
                else:
                    # Non-doc comment encountered, store pending block
                    if current_doc_block:
                        doc_comment_map[last_comment_line] = current_doc_block
                    current_doc_block = []
                    last_comment_line = current_end_line  # Update last line seen

            # Store the last block if it exists
            if current_doc_block:
                doc_comment_map[last_comment_line] = current_doc_block

        except Exception as e:
            logger.warning(f"Failed to execute C++ doc_comments query: {e}", exc_info=True)

        # --- Pass 2: Extract Imports and Declarations --- #
        for query_name, query_str in queries.items():
            if query_name == "doc_comments":
                continue

            try:
                query = self.ts_language.query(query_str)
                captures = query.captures(root_node)
                logger.debug(f"Running C++ query '{query_name}', found {len(captures)} captures.")

                if query_name == "imports":
                    # captures is a dict: {capture_name: [list of nodes]}
                    # Fixed capture unpacking pattern
                    for capture in captures.items():
                        if len(capture) == 2:
                            capture_name, nodes = capture
                        else:
                            continue
                        if capture_name == "import_path":
                            for node in nodes:
                                # Includes <...> or "..."
                                import_path = (
                                    byte_content[node.start_byte : node.end_byte]
                                    .decode("utf8", errors="replace")
                                    .strip('<>"')
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

                        # Check for various declaration types
                        decl_types = ["class", "struct", "union", "enum", "function", "namespace"]

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

                            # Check for docstring
                            raw_doc_block = doc_comment_map.get(
                                declaration_node.start_point[0] - 1, []
                            )
                            docstring = (
                                _clean_cpp_doc_comment(raw_doc_block) if raw_doc_block else ""
                            )

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
                logger.warning(f"Failed to execute C++ query '{query_name}': {e}", exc_info=True)

        # --- Pass 3: Process declarations and associate docstrings --- #
        for decl_info in declaration_map.values():
            if decl_info.get("name") and decl_info["name"] != "<unknown>":
                # Check for doc comments ending on the line before the declaration
                raw_doc_block = doc_comment_map.get(decl_info["start_line"] - 1, [])
                cleaned_docstring = _clean_cpp_doc_comment(raw_doc_block) if raw_doc_block else ""

                declarations.append(
                    Declaration(
                        kind=decl_info["kind"],
                        name=decl_info["name"],
                        start_line=decl_info["start_line"],
                        end_line=decl_info["end_line"],
                        docstring=cleaned_docstring,
                        modifiers=decl_info["modifiers"],
                    )
                )

        declarations.sort(key=lambda d: d.start_line)
        sorted_imports = sorted(imports)

        logger.debug(
            f"Tree-sitter C++ extracted {len(declarations)} declarations and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports
