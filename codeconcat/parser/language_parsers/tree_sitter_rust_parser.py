# file: codeconcat/parser/language_parsers/tree_sitter_rust_parser.py

import logging
import re
from typing import Dict, List, Set

from tree_sitter import Node

from ...base_types import Declaration
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Define Tree-sitter queries for Rust
# Ref: https://github.com/tree-sitter/tree-sitter-rust/blob/master/queries/tags.scm
RUST_QUERIES = {
    "imports": """
        (use_declaration
            argument: (_) @import_path
        ) @use_statement

        (extern_crate_declaration
            name: (identifier) @import_path
        ) @extern_crate
    """,
    "declarations": """
        (function_item
            visibility: (visibility_modifier)? @visibility
            name: (identifier) @name
            parameters: (parameters)? @params
            return_type: (_)? @return_type
            body: (block)? @body
        ) @function

        (struct_item
            visibility: (visibility_modifier)? @visibility
            name: (type_identifier) @name
            type_parameters: (type_parameters)? @type_params
            fields: (_)? @fields
        ) @struct

        (enum_item
            visibility: (visibility_modifier)? @visibility
            name: (type_identifier) @name
            type_parameters: (type_parameters)? @type_params
            variants: (_)? @variants
        ) @enum

        (trait_item
            visibility: (visibility_modifier)? @visibility
            name: (type_identifier) @name
            type_parameters: (type_parameters)? @type_params
            supertraits: (_)? @supertraits
            body: (_)? @body
        ) @trait
        
        ; Enhanced impl item query to better capture trait implementations
        (impl_item
            type_parameters: (type_parameters)? @type_params
            trait: [
                (type_identifier) @trait_name
                (scoped_identifier 
                    path: (_) @trait_path 
                    name: (type_identifier) @trait_name)
            ]?
            type: [
                (type_identifier) @impl_type
                (scoped_type_identifier
                    path: (_) @type_path
                    name: (type_identifier) @impl_type)
            ]
            body: (declaration_list)? @body
        ) @impl

        (mod_item
            visibility: (visibility_modifier)? @visibility
            name: (identifier) @name
            body: (_)? @body
        ) @module

        (const_item
            visibility: (visibility_modifier)? @visibility
            name: (identifier) @name
            type: (_)? @type
            value: (_)? @value
        ) @constant

        (static_item
            visibility: (visibility_modifier)? @visibility
            name: (identifier) @name
            type: (_)? @type
            value: (_)? @value
        ) @static

        (type_item
            visibility: (visibility_modifier)? @visibility
            name: (type_identifier) @name
            type_parameters: (type_parameters)? @type_params
            type: (_)? @type
        ) @type_alias

        (macro_definition
            name: (identifier) @name
        ) @macro_definition

        ; Better detection of methods within impl blocks
        (impl_item
            body: (declaration_list
                  (function_item
                    visibility: (visibility_modifier)? @method_visibility
                    name: (identifier) @method_name
                    parameters: (parameters)? @method_params
                    return_type: (_)? @method_return_type
                    body: (block)? @method_body
                  ) @method
                 )
        )

        ; Better detection of associated types
        (impl_item
            body: (declaration_list
                  (type_item
                    visibility: (visibility_modifier)? @assoc_type_visibility
                    name: (type_identifier) @assoc_type_name
                    type_parameters: (type_parameters)? @assoc_type_params
                    type: (_)? @assoc_type_value
                  ) @assoc_type
                 )
        )

        ; Better detection of associated constants
        (impl_item
            body: (declaration_list
                  (const_item
                    visibility: (visibility_modifier)? @assoc_const_visibility
                    name: (identifier) @assoc_const_name
                    type: (_)? @assoc_const_type
                    value: (_)? @assoc_const_value
                  ) @assoc_const
                 )
        )
    """,
    # Enhance doc comment detection - capture both line and block doc comments
    "doc_comments": """
        (line_comment) @doc_comment (#match? @doc_comment "^///|^//!")
        (block_comment) @doc_comment (#match? @doc_comment "^/\\*\\*|^/\\*!")
    """,
}

# Patterns to clean Rust doc comments
RUST_DOC_COMMENT_LINE_PATTERN = re.compile(r"^///?\s?|^//!\s?")
RUST_DOC_COMMENT_BLOCK_START_PATTERN = re.compile(r"^/\*\*\s?")
RUST_DOC_COMMENT_BLOCK_LINE_PREFIX_PATTERN = re.compile(r"^\s*\*\s?")
RUST_DOC_COMMENT_BLOCK_END_PATTERN = re.compile(r"\s*\*/$")


def _clean_rust_doc_comment(comment_block: List[str]) -> str:
    """Cleans a block of Rust doc comment lines."""
    cleaned_lines = []
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
        declaration_map = {}  # node_id -> declaration info
        doc_comment_map = {}  # end_line -> {'text': List[str], 'inner': bool}

        # --- Pass 1: Extract Doc Comments --- #
        try:
            doc_query = self.ts_language.query(queries.get("doc_comments", ""))
            doc_captures = doc_query.captures(root_node)
            last_comment_line = -2
            current_doc_block: List[str] = []
            current_block_inner = False

            for node, _ in doc_captures:
                comment_text = byte_content[node.start_byte : node.end_byte].decode(
                    "utf8", errors="ignore"
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
            logger.warning(f"Failed to execute Rust doc_comments query: {e}", exc_info=False)

        # --- Pass 2: Extract Imports and Declarations --- #
        for query_name, query_str in queries.items():
            if query_name == "doc_comments":
                continue

            try:
                query = self.ts_language.query(query_str)
                captures = query.captures(root_node)
                logger.debug(f"Running Rust query '{query_name}', found {len(captures)} captures.")

                if query_name == "imports":
                    for node, capture_name in captures:
                        if capture_name == "import_path":
                            import_path = byte_content[node.start_byte : node.end_byte].decode(
                                "utf8", errors="ignore"
                            )
                            # Clean up paths like 'crate::foo' or 'super::bar'
                            imports.add(import_path)

                elif query_name == "declarations":
                    # Group captures by the main declaration node ID
                    node_capture_map = {}
                    for node, capture_name in captures:
                        # Find the ancestor that is the actual declaration item
                        decl_node = node
                        while decl_node.parent and decl_node.type not in [
                            "function_item",
                            "struct_item",
                            "enum_item",
                            "trait_item",
                            "impl_item",
                            "mod_item",
                            "const_item",
                            "static_item",
                            "type_item",
                            "macro_definition",
                            "source_file",
                        ]:
                            decl_node = decl_node.parent
                        if not decl_node:
                            decl_node = node  # Fallback

                        decl_id = decl_node.id
                        if decl_id not in node_capture_map:
                            node_capture_map[decl_id] = {
                                "node": decl_node,
                                "captures": [],
                                "kind": None,
                            }
                        node_capture_map[decl_id]["captures"].append((node, capture_name))
                        # Capture primary kind if available
                        if capture_name in [
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
                        ]:
                            node_capture_map[decl_id]["kind"] = capture_name

                    # Process grouped captures
                    for decl_id, data in node_capture_map.items():
                        decl_node = data["node"]
                        node_captures = data["captures"]
                        kind = data["kind"] or decl_node.type  # Fallback to node type

                        # Map TS types / capture names to our kinds
                        kind_map = {
                            "function_item": "function",
                            "struct_item": "struct",
                            "enum_item": "enum",
                            "trait_item": "trait",
                            "impl_item": "impl",
                            "mod_item": "module",
                            "const_item": "constant",
                            "static_item": "static",
                            "type_item": "type_alias",
                            "macro_definition": "macro",
                            "method": "method",  # Use specific capture name
                            "assoc_type": "associated_type",
                            "assoc_const": "associated_constant",
                        }
                        kind = kind_map.get(kind, kind)  # Use mapped kind or original capture name

                        if kind not in [
                            "function",
                            "struct",
                            "enum",
                            "trait",
                            "impl",
                            "module",
                            "constant",
                            "static",
                            "type_alias",
                            "macro",
                            "method",
                            "associated_type",
                            "associated_constant",
                        ]:
                            continue  # Skip nodes we don't classify

                        # --- Extract Name --- #
                        name = "<unknown>"
                        if kind == "impl":
                            # Name for impl block is complex: trait for type
                            trait_node = next(
                                (n for n, cname in node_captures if cname == "trait_name"), None
                            )
                            type_node = next(
                                (n for n, cname in node_captures if cname == "impl_type"), None
                            )
                            trait_name = (
                                byte_content[trait_node.start_byte : trait_node.end_byte].decode(
                                    "utf8", errors="ignore"
                                )
                                if trait_node
                                else None
                            )
                            type_name = (
                                byte_content[type_node.start_byte : type_node.end_byte].decode(
                                    "utf8", errors="ignore"
                                )
                                if type_node
                                else "<unknown>"
                            )
                            name = f"{trait_name} for {type_name}" if trait_name else type_name
                        elif kind == "method":
                            name_node = next(
                                (n for n, cname in node_captures if cname == "method_name"), None
                            )
                            if name_node:
                                name = byte_content[
                                    name_node.start_byte : name_node.end_byte
                                ].decode("utf8", errors="ignore")
                        elif kind == "associated_type":
                            name_node = next(
                                (n for n, cname in node_captures if cname == "assoc_type_name"),
                                None,
                            )
                            if name_node:
                                name = byte_content[
                                    name_node.start_byte : name_node.end_byte
                                ].decode("utf8", errors="ignore")
                        elif kind == "associated_constant":
                            name_node = next(
                                (n for n, cname in node_captures if cname == "assoc_const_name"),
                                None,
                            )
                            if name_node:
                                name = byte_content[
                                    name_node.start_byte : name_node.end_byte
                                ].decode("utf8", errors="ignore")
                        else:
                            # General case: capture named 'name'
                            name_node = next(
                                (n for n, cname in node_captures if cname == "name"), None
                            )
                            if name_node:
                                name = byte_content[
                                    name_node.start_byte : name_node.end_byte
                                ].decode("utf8", errors="ignore")

                        if name == "<unknown>":
                            continue  # Skip if name extraction failed

                        start_line = decl_node.start_point[0]
                        end_line = decl_node.end_point[0]

                        # Basic module path tracking (doesn't handle complex nesting well)
                        # if kind == 'module': current_mod_path.append(name)
                        # full_name = "::".join(current_mod_path + [name]) if current_mod_path else name
                        # This needs a proper stack based on node depth
                        full_name = name  # Keep it simple for now

                        if decl_id not in declaration_map:
                            declaration_map[decl_id] = {
                                "kind": kind,
                                "name": full_name,
                                "start_line": start_line,
                                "end_line": end_line,
                                "modifiers": set(),  # TODO: Extract pub, async, unsafe, etc.
                                "docstring": "",
                            }
                        else:
                            declaration_map[decl_id]["end_line"] = max(
                                declaration_map[decl_id]["end_line"], end_line
                            )
                            if declaration_map[decl_id]["name"] == "<unknown>":
                                declaration_map[decl_id]["name"] = full_name

            except Exception as e:
                logger.warning(f"Failed to execute Rust query '{query_name}': {e}", exc_info=True)

        # --- Pass 3: Process declarations and associate docstrings --- #
        for decl_id, decl_info in declaration_map.items():
            if decl_info.get("name") and decl_info["name"] != "<unknown>":
                # Find associated doc comment
                doc_info = doc_comment_map.get(decl_info["start_line"] - 1)
                cleaned_docstring = ""
                if doc_info and not doc_info["inner"]:  # Outer doc comment before decl
                    cleaned_docstring = _clean_rust_doc_comment(doc_info["text"])
                # TODO: Handle inner doc comments (associated with parent, e.g., module)

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
        sorted_imports = sorted(list(imports))

        logger.debug(
            f"Tree-sitter Rust extracted {len(declarations)} declarations and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports
