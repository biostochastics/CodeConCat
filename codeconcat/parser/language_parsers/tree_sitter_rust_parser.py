# file: codeconcat/parser/language_parsers/tree_sitter_rust_parser.py

import logging
import re
from typing import Dict, List, Set

from tree_sitter import Node

from ...base_types import Declaration
from ..utils import get_node_location
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Enhanced Tree-sitter queries for Rust with comprehensive coverage
RUST_QUERIES = {
    "imports": """
        ; Use declarations
        (use_declaration
            argument: (_) @import_path
        ) @use_statement

        ; External crate declarations
        (extern_crate_declaration
            name: (identifier) @crate_name
        ) @extern_crate

        ; Mod declarations (module imports)
        (mod_item
            name: (identifier) @mod_name
        ) @mod_declaration
    """,
    "declarations": """
        ; Function items with full signature capture
        (function_item
            (visibility_modifier)? @visibility
            (function_modifiers
                "async"? @async_modifier
                "unsafe"? @unsafe_modifier
                "const"? @const_modifier
                "extern"? @extern_modifier
            )? @modifiers
            name: (identifier) @name
            parameters: (parameters) @params
            return_type: (_)? @return_type
            body: (block)? @body
        ) @function

        ; Method definitions within impl blocks
        (impl_item
            type: (_) @impl_type
            body: (declaration_list)
        ) @impl_block

        ; Struct definitions
        (struct_item
            name: (type_identifier) @name
            body: [
                (field_declaration_list) @struct_fields
                (ordered_field_declaration_list) @tuple_fields
            ]?
        ) @struct

        ; Enum definitions
        (enum_item
            name: (type_identifier) @name
            body: (enum_variant_list) @enum_variants
        ) @enum

        ; Trait definitions
        (trait_item
            "unsafe"? @unsafe_trait
            name: (type_identifier) @name
            body: (declaration_list) @trait_body
        ) @trait

        ; Type alias definitions
        (type_item
            name: (type_identifier) @name
            type: (_) @type_definition
        ) @type_alias

        ; Constant definitions
        (const_item
            name: (identifier) @name
            type: (_) @const_type
            value: (_) @const_value
        ) @constant

        ; Static definitions
        (static_item
            name: (identifier) @name
            type: (_) @static_type
            value: (_) @static_value
        ) @static

        ; Macro definitions
        (macro_definition
            name: (identifier) @name
            parameters: (macro_rule)* @macro_rules
        ) @macro

        ; Module definitions
        (mod_item
            name: (identifier) @name
            body: (declaration_list)? @mod_body
        ) @module
    """,
    "doc_comments": """
        ; Outer doc comments (///)
        (line_comment) @outer_doc_comment (#match? @outer_doc_comment "^///")

        ; Inner doc comments (//!)
        (line_comment) @inner_doc_comment (#match? @inner_doc_comment "^//!")

        ; Outer block doc comments (/** */)
        (block_comment) @outer_block_doc (#match? @outer_block_doc "^/\\\\*\\\\*")

        ; Inner block doc comments (/*! */)
        (block_comment) @inner_block_doc (#match? @inner_block_doc "^/\\*!")
    """,
}

# Patterns to clean Rust doc comments
RUST_DOC_COMMENT_LINE_PATTERN = re.compile(r"^///?\s?|^//!\s?")
RUST_DOC_COMMENT_BLOCK_START_PATTERN = re.compile(r"^/\*\*\s?")
RUST_DOC_COMMENT_BLOCK_LINE_PREFIX_PATTERN = re.compile(r"^\s*\*\s?")
RUST_DOC_COMMENT_BLOCK_END_PATTERN = re.compile(r"\s*\*/$")


def _clean_rust_doc_comment(comment_block: List[str]) -> str:
    """Cleans a block of Rust doc comment lines."""
    cleaned_lines: list[str] = []
    is_block = comment_block[0].startswith("/**") if comment_block else False
    (
        comment_block[0].startswith(("//!", "/*!")) if comment_block else False
    )  # //! applies to parent

    for i, line in enumerate(comment_block):
        original_line = line  # Keep original for block end check
        if is_block:
            if i == 0:
                line = RUST_DOC_COMMENT_BLOCK_START_PATTERN.sub("", line)
            line = RUST_DOC_COMMENT_BLOCK_LINE_PREFIX_PATTERN.sub("", line)
            if original_line.strip().endswith("*/"):
                line = RUST_DOC_COMMENT_BLOCK_END_PATTERN.sub("", line)
        else:  # Line comment
            line = RUST_DOC_COMMENT_LINE_PATTERN.sub("", line)

        cleaned_lines.append(line.strip())

    return "\n".join(filter(None, cleaned_lines))


class TreeSitterRustParser(BaseTreeSitterParser):
    """Tree-sitter based parser for the Rust language."""

    def __init__(self):
        """Initializes the Rust Tree-sitter parser."""
        super().__init__(language_name="rust")

    def get_queries(self) -> Dict[str, str]:
        """Returns the predefined Tree-sitter queries for Rust."""
        return RUST_QUERIES

    def _run_queries(
        self, root_node: Node, byte_content: bytes
    ) -> tuple[List[Declaration], List[str]]:
        """Runs Rust-specific queries and extracts declarations and imports."""
        queries = self.get_queries()
        declarations = []
        imports: Set[str] = set()
        doc_comment_map = {}  # end_line -> {'text': List[str], 'inner': bool}

        # --- Pass 1: Extract Doc Comments --- #
        try:
            doc_query = self.ts_language.query(queries.get("doc_comments", ""))
            doc_captures = doc_query.captures(root_node)
            last_comment_line = -2
            current_doc_block: List[str] = []
            current_block_inner = False

            # doc_captures is a dict: {capture_name: [list of nodes]}
            for _capture_name, nodes in doc_captures.items():
                for node in nodes:
                    comment_text = byte_content[node.start_byte : node.end_byte].decode(
                        "utf8", errors="replace"
                    )
                    current_start_line = node.start_point[0]
                    current_end_line = node.end_point[0]
                    is_block = comment_text.startswith("/**")
                    is_inner = comment_text.startswith(("//!", "/*!"))  # Treat /*! same as //!

                    if is_block:
                        if current_doc_block:
                            doc_comment_map[last_comment_line] = {
                                "text": current_doc_block,
                                "inner": current_block_inner,
                            }
                        doc_comment_map[current_end_line] = {
                            "text": comment_text.splitlines(),
                            "inner": is_inner,
                        }
                        current_doc_block = []
                        last_comment_line = current_end_line
                    else:  # Line comment
                        if (
                            current_start_line == last_comment_line + 1
                            and is_inner == current_block_inner
                        ):
                            current_doc_block.append(comment_text)
                        else:
                            if current_doc_block:
                                doc_comment_map[last_comment_line] = {
                                    "text": current_doc_block,
                                    "inner": current_block_inner,
                                }
                        current_doc_block = [comment_text]
                        current_block_inner = is_inner
                    last_comment_line = current_start_line

            # Store the last block if it exists
            if current_doc_block:
                doc_comment_map[last_comment_line] = {
                    "text": current_doc_block,
                    "inner": current_block_inner,
                }

        except Exception as e:
            logger.warning(f"Failed to execute Rust doc_comments query: {e}", exc_info=True)

        # --- Pass 2: Extract Imports and Declarations --- #
        for query_name, query_str in queries.items():
            if query_name == "doc_comments":
                continue

            try:
                query = self.ts_language.query(query_str)
                captures = query.captures(root_node)
                logger.debug(f"Running Rust query '{query_name}', found {len(captures)} captures.")

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
                                import_path = byte_content[node.start_byte : node.end_byte].decode(
                                    "utf8", errors="replace"
                                )
                                # Clean up paths like 'crate::foo' or 'super::bar'
                                imports.add(import_path)

                elif query_name == "declarations":
                    # Use matches for better structure
                    matches = query.matches(root_node)
                    for _match_id, captures_dict in matches:
                        declaration_node = None
                        name_node = None
                        kind = None
                        modifiers = set()

                        # Check for various declaration types
                        decl_types = [
                            "function",
                            "struct",
                            "enum",
                            "trait",
                            "impl",
                            "module",
                            "constant",
                            "static",
                            "type_alias",
                            "macro_definition",
                            "method",
                            "assoc_type",
                            "assoc_const",
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

                        # Check for modifiers
                        if "pub_modifier" in captures_dict or "visibility" in captures_dict:
                            modifiers.add("pub")
                        if "async_modifier" in captures_dict or "method_async" in captures_dict:
                            modifiers.add("async")
                        if "unsafe_modifier" in captures_dict:
                            modifiers.add("unsafe")

                        # Map capture names to standard kinds
                        kind_map = {
                            "assoc_type": "associated_type",
                            "assoc_const": "associated_constant",
                        }
                        if kind:
                            kind = kind_map.get(kind, kind)

                        # Add declaration if we have both node and name
                        if declaration_node and name_node and kind:
                            name_text = byte_content[
                                name_node.start_byte : name_node.end_byte
                            ].decode("utf8", errors="replace")

                            # Check for docstring
                            doc_data = doc_comment_map.get(declaration_node.start_point[0] - 1, "")
                            # Convert docstring to string format
                            if isinstance(doc_data, dict) and "text" in doc_data:
                                text_data = doc_data["text"]
                                if isinstance(text_data, (list, tuple)):
                                    docstring = "\n".join(str(line) for line in text_data).strip()
                                    # Clean up Rust doc comment markers
                                    docstring = self._clean_rust_docstring(docstring)
                                else:
                                    docstring = str(text_data).strip()
                            else:
                                docstring = str(doc_data) if doc_data else ""

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
                logger.warning(f"Failed to execute Rust query '{query_name}': {e}", exc_info=True)

        # Declaration processing now happens inline

        declarations.sort(key=lambda d: d.start_line)
        sorted_imports = sorted(imports)

        logger.debug(
            f"Tree-sitter Rust extracted {len(declarations)} declarations and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports

    def _clean_rust_docstring(self, docstring_text: str) -> str:
        """Clean Rust docstring by removing comment markers and normalizing."""
        if not docstring_text:
            return ""

        lines = docstring_text.split("\n")
        cleaned_lines: list[str] = []

        for line in lines:
            # Remove Rust doc comment markers
            cleaned_line = RUST_DOC_COMMENT_LINE_PATTERN.sub("", line).strip()
            if cleaned_line or cleaned_lines:  # Keep non-empty lines and preserve structure
                cleaned_lines.append(cleaned_line)

        return "\n".join(cleaned_lines).strip()
