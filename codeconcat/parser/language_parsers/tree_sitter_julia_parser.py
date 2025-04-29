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
        (using_statement
          (module_expression module: (identifier) @import_path)
        ) @using_module

        (using_statement
          (module_expression module: (scoped_identifier) @import_path)
        ) @using_scoped_module

        (import_statement
           (module_expression module: (identifier) @import_path)
        ) @import_module

        (import_statement
           (module_expression module: (scoped_identifier) @import_path)
        ) @import_scoped_module

        ; Import statements with specific symbols
        (import_statement
          argument: (identifier) @import_module
          symbols: (import_symbols . (symbol) @imported_symbol)
        ) @import_with_symbols
        
        (using_statement
          argument: (identifier) @import_module
          symbols: (import_symbols . (symbol) @imported_symbol)
        ) @using_with_symbols
        
        ; Specific imports like `import Pkg: add` or `using Pkg: add`
        (import_statement
          (symbol) @imported_symbol
        ) @import_symbol
        (using_statement
          (symbol) @imported_symbol
        ) @using_symbol
    """,
    "declarations": """
        (module_definition
            name: (identifier) @name
            body: (block) @body
        ) @module

        (baremodule_definition
            name: (identifier) @name
            body: (block) @body
        ) @baremodule

        ; Standard function definitions
        (function_definition
            name: [                 ; Multiple ways to define function names in Julia
                (identifier) @name
                (field_expression
                    object: (_) @object
                    field: (identifier) @field_name)
                (operator) @name    ; For operator overloading
            ]
            parameters: (parameter_list)? @params
            body: (block) @body
        ) @function
        
        ; Short-form function definitions: f(x) = expr
        (assignment
            left: (call_expression
                function: (identifier) @name
                arguments: (argument_list) @params)
            right: (_) @body_expr
        ) @short_function
        
        ; Anonymous functions: x -> expr
        (function_expression
            parameters: (parameter_list)? @anon_params
            body: (_) @anon_body
        ) @anonymous_function

        ; Macro definitions with better parameter capture
        (macro_definition
            name: (macro_identifier) @name
            parameters: (parameter_list)? @params
            body: (block) @body
        ) @macro

        ; Struct definitions with better type parameter capture and field detection
        (struct_definition
            mutable: (_)? @mutable
            name: (identifier) @name
            parameters: (type_parameter_list)? @type_params
            supertypes: (supertype_clause)? @supertype
            body: (field_declaration_list)? @fields
        ) @struct

        ; Abstract type definitions with better inheritance tracking
        (abstract_type_definition
            name: (identifier) @name
            parameters: (type_parameter_list)? @type_params
            supertypes: (supertype_clause)? @supertype
        ) @abstract_type

        ; Primitive type definitions with size and parameter capture
        (primitive_type_definition
            name: (identifier) @name
            size: (integer_literal)? @size
            parameters: (type_parameter_list)? @type_params
            supertypes: (supertype_clause)? @supertype
        ) @primitive_type

        (global_declaration
           (assignment left: (identifier) @name)
        ) @global_variable

        (constant_declaration
           (assignment left: (identifier) @name)
        ) @constant

    """,
    # Capture Julia docstrings (triple-quoted strings before declarations) and comments
    "doc_comments": """
        ; Regular comments
        (comment) @comment
        
        ; Julia docstrings - triple-quoted strings that appear before declarations
        (string_literal) @docstring
    """,
}

# Patterns to clean Julia comments
JULIA_LINE_COMMENT_PATTERN = re.compile(r"^#\s?")
JULIA_BLOCK_COMMENT_START_PATTERN = re.compile(r"^#=\s?")
JULIA_BLOCK_COMMENT_END_PATTERN = re.compile(r"\s*=#$")


def _clean_julia_doc_comment(comment_block: List[str]) -> str:
    """Cleans a block of Julia comment lines."""
    cleaned_lines = []
    is_block = comment_block[0].startswith("#=") if comment_block else False

    for i, line in enumerate(comment_block):
        original_line = line  # Keep original for block end check
        if is_block:
            if i == 0:
                line = JULIA_BLOCK_COMMENT_START_PATTERN.sub("", line)
            # No standard line prefix like '*' for block comments
            if original_line.strip().endswith("=#"):
                line = JULIA_BLOCK_COMMENT_END_PATTERN.sub("", line)
        else:  # Line comment
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
        declaration_map = {}  # node_id -> declaration info
        doc_comment_map = {}  # end_line -> List[str]

        # --- Pass 1: Extract Comments (potential docstrings) --- #
        try:
            doc_query = self.ts_language.query(queries.get("doc_comments", ""))
            doc_captures = doc_query.captures(root_node)
            last_comment_line = -2
            current_doc_block: List[str] = []

            for node, _ in doc_captures:
                comment_text = byte_content[node.start_byte : node.end_byte].decode(
                    "utf8", errors="ignore"
                )
                current_start_line = node.start_point[0]
                current_end_line = node.end_point[0]
                is_block = comment_text.startswith("#=")

                if is_block:
                    if current_doc_block:
                        doc_comment_map[last_comment_line] = current_doc_block
                    doc_comment_map[current_end_line] = comment_text.splitlines()
                    current_doc_block = []
                    last_comment_line = current_end_line
                else:  # Line comment
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
            logger.warning(f"Failed to execute Julia doc_comments query: {e}", exc_info=True)

        # --- Pass 2: Extract Imports and Declarations --- #
        for query_name, query_str in queries.items():
            if query_name == "doc_comments":
                continue

            try:
                query = self.ts_language.query(query_str)
                captures = query.captures(root_node)
                logger.debug(f"Running Julia query '{query_name}', found {len(captures)} captures.")

                if query_name == "imports":
                    for node, capture_name in captures:
                        if capture_name in ["import_path", "imported_symbol"]:
                            import_path = byte_content[node.start_byte : node.end_byte].decode(
                                "utf8", errors="ignore"
                            )
                            # Handle scoped identifiers like Pkg.Operations
                            import_path = import_path.replace(".", "::")  # Normalize to :: maybe?
                            imports.add(import_path)

                elif query_name == "declarations":
                    # Group captures by declaration node ID
                    node_capture_map = {}
                    for node, capture_name in captures:
                        decl_node = node
                        while decl_node.parent and decl_node.type not in [
                            "module_definition",
                            "baremodule_definition",
                            "function_definition",
                            "macro_definition",
                            "struct_definition",
                            "abstract_type_definition",
                            "primitive_type_definition",
                            "global_declaration",
                            "constant_declaration",
                            "source_file",  # Top level
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
                        if capture_name in [
                            "module",
                            "baremodule",
                            "function",
                            "macro",
                            "struct",
                            "abstract_type",
                            "primitive_type",
                            "global_variable",
                            "constant",
                        ]:
                            node_capture_map[decl_id]["kind"] = capture_name

                    # Process grouped captures
                    for decl_id, data in node_capture_map.items():
                        decl_node = data["node"]
                        node_captures = data["captures"]
                        kind = data["kind"] or decl_node.type

                        kind_map = {
                            "module_definition": "module",
                            "baremodule_definition": "module",
                            "function_definition": "function",
                            "macro_definition": "macro",
                            "struct_definition": "struct",
                            "abstract_type_definition": "abstract_type",
                            "primitive_type_definition": "primitive_type",
                            "global_declaration": "global_variable",
                            "constant_declaration": "constant",
                        }
                        kind = kind_map.get(kind, kind)

                        if kind not in [
                            "module",
                            "function",
                            "macro",
                            "struct",
                            "abstract_type",
                            "primitive_type",
                            "global_variable",
                            "constant",
                        ]:
                            continue  # Skip unclassified nodes

                        name_node = next((n for n, cname in node_captures if cname == "name"), None)
                        name = (
                            byte_content[name_node.start_byte : name_node.end_byte].decode(
                                "utf8", errors="ignore"
                            )
                            if name_node
                            else "<unknown>"
                        )

                        if name == "<unknown>":
                            continue  # Skip anonymous/unnamed

                        start_line = decl_node.start_point[0]
                        end_line = decl_node.end_point[0]

                        # Basic module path tracking (needs improvement for nesting)
                        # full_name = "::".join(current_module_path + [name])
                        full_name = name  # Keep simple for now

                        if decl_id not in declaration_map:
                            declaration_map[decl_id] = {
                                "kind": kind,
                                "name": full_name,
                                "start_line": start_line,
                                "end_line": end_line,
                                "modifiers": set(),  # TODO: Extract modifiers if applicable
                                "docstring": "",
                            }
                        else:
                            declaration_map[decl_id]["end_line"] = max(
                                declaration_map[decl_id]["end_line"], end_line
                            )
                            if declaration_map[decl_id]["name"] == "<unknown>":
                                declaration_map[decl_id]["name"] = full_name

            except Exception as e:
                logger.warning(f"Failed to execute Julia query '{query_name}': {e}", exc_info=True)

        # --- Pass 3: Process declarations and associate comments --- #
        for decl_id, decl_info in declaration_map.items():
            if decl_info.get("name") and decl_info["name"] != "<unknown>":
                # Check for comments ending on the line before the declaration
                raw_doc_block = doc_comment_map.get(decl_info["start_line"] - 1, [])
                cleaned_docstring = _clean_julia_doc_comment(raw_doc_block) if raw_doc_block else ""

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
            f"Tree-sitter Julia extracted {len(declarations)} declarations and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports
