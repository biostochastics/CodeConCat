# file: codeconcat/parser/language_parsers/tree_sitter_julia_parser.py

import logging
from typing import Dict, List, Set

from tree_sitter import Node, Query

# QueryCursor was removed in tree-sitter 0.24.0 - import it if available for backward compatibility
try:
    from tree_sitter import QueryCursor
except ImportError:
    QueryCursor = None  # type: ignore[assignment,misc]

from ...base_types import Declaration
from ..doc_comment_utils import clean_block_comments, clean_line_comments, normalize_whitespace
from ..utils import get_node_location
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
        (module_definition
          (identifier) @import_path
        ) @module_definition
    """,
    "declarations": """
        ; Module definitions
        (module_definition
            (identifier) @name
        ) @module

        ; Function definitions with call expression (non-parametric)
        (function_definition
            (signature (call_expression
                (identifier) @name
            ))
        ) @function

        ; Parametric functions (with where expression wrapping call_expression)
        (function_definition
            (signature (where_expression
                (call_expression
                    (identifier) @param_func_name
                )
            ))
        ) @parametric_function

        ; Macro definitions
        (macro_definition
            (signature (call_expression
                (identifier) @name
            ))
        ) @macro

        ; Struct definitions (non-parametric with simple identifier)
        (struct_definition
            (type_head (identifier) @name)
        ) @struct

        ; Parametric struct definitions (with type parameters)
        (struct_definition
            (type_head (parametrized_type_expression
                (identifier) @param_struct_name
            ))
        ) @parametric_struct

        ; Abstract type definitions (non-parametric)
        (abstract_definition
            (type_head (identifier) @name)
        ) @abstract_type

        ; Parametric abstract type definitions
        (abstract_definition
            (type_head (parametrized_type_expression
                (identifier) @param_abstract_name
            ))
        ) @parametric_abstract

        ; Short-form parametric functions (assignment style)
        (assignment
            (call_expression) @func_call
            (where_expression) @where_constraints
        ) @parametric_func_short
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
def _clean_julia_doc_line_comment(line_comment_block_expression: List[str]) -> str:
    """Cleans Julia doc comments using shared doc_comment_utils.

    Handles both block comments (#= =#) and line comments (#) consistently
    with other parsers.
    """
    if not line_comment_block_expression:
        return ""

    # Detect if this is a block comment or line comment
    first_line = line_comment_block_expression[0].strip()
    is_block_expression = first_line.startswith("#=")

    if is_block_expression:
        # Use shared block comment cleaner for #= =# style
        # Julia block comments use #= =# instead of /* */
        start_pattern = r"^#="
        end_pattern = r"=#$"
        line_pattern = r"^"  # No standard line prefix in Julia block comments
        return clean_block_comments(
            line_comment_block_expression,
            start_pattern=start_pattern,
            line_pattern=line_pattern,
            end_pattern=end_pattern,
        )
    else:
        # Use shared line comment cleaner for # style
        prefix_pattern = r"^#\s*"
        return clean_line_comments(line_comment_block_expression, prefix_pattern=prefix_pattern)


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
            # Use modern Query() constructor and QueryCursor
            doc_query = Query(self.ts_language, queries.get("doc_line_comments", ""))
            doc_cursor = QueryCursor(doc_query)
            doc_captures = doc_cursor.captures(root_node)
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
                            doc_line_comment_map[
                                last_line_comment_line
                            ] = current_doc_block_expression
                        doc_line_comment_map[current_end_line] = line_comment_text.splitlines()
                        current_doc_block_expression = []
                        last_line_comment_line = current_end_line
                    else:  # Line line_comment
                        if current_start_line == last_line_comment_line + 1:
                            current_doc_block_expression.append(line_comment_text)
                        else:
                            if current_doc_block_expression:
                                doc_line_comment_map[
                                    last_line_comment_line
                                ] = current_doc_block_expression
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
                # Use modern Query() constructor and QueryCursor
                query = Query(self.ts_language, query_str)

                if query_name == "imports":
                    # Use captures for imports
                    cursor = QueryCursor(query)
                    captures = cursor.captures(root_node)
                    logger.debug(
                        f"Running Julia query '{query_name}', found {len(captures)} captures."
                    )

                    # captures is a dict: {capture_name: [list of nodes]}
                    for capture_name, nodes in captures.items():
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
                    # Use matches for better structure with declarations
                    cursor = QueryCursor(query)
                    matches = cursor.matches(root_node)
                    for _match_id, captures_dict in matches:
                        declaration_node = None
                        name_node = None
                        kind = None
                        modifiers: set[str] = set()
                        signature = ""

                        # Check for various declaration types
                        decl_types = ["module", "function", "macro", "struct", "abstract_type"]

                        for decl_type in decl_types:
                            if decl_type in captures_dict:
                                nodes = captures_dict[decl_type]
                                if nodes and len(nodes) > 0:
                                    declaration_node = nodes[0]
                                    kind = decl_type
                                    break

                        # Check for parametric struct types
                        if "parametric_struct" in captures_dict:
                            param_nodes = captures_dict["parametric_struct"]
                            if param_nodes and len(param_nodes) > 0:
                                declaration_node = param_nodes[0]
                                kind = "struct"
                                modifiers.add("parametric")

                        # Check for parametric abstract types
                        if "parametric_abstract" in captures_dict:
                            param_nodes = captures_dict["parametric_abstract"]
                            if param_nodes and len(param_nodes) > 0:
                                declaration_node = param_nodes[0]
                                kind = "abstract_type"
                                modifiers.add("parametric")

                        # Check for parametric functions
                        if (
                            "parametric_function" in captures_dict
                            or "parametric_func_short" in captures_dict
                        ):
                            param_func_key = (
                                "parametric_function"
                                if "parametric_function" in captures_dict
                                else "parametric_func_short"
                            )
                            param_nodes = captures_dict[param_func_key]
                            if param_nodes and len(param_nodes) > 0:
                                declaration_node = param_nodes[0]
                                if (
                                    kind != "function"
                                ):  # Don't override if already detected as function
                                    kind = "function"
                                modifiers.add("parametric")

                        # Get the name node
                        if "name" in captures_dict:
                            name_nodes = captures_dict["name"]
                            if name_nodes and len(name_nodes) > 0:
                                name_node = name_nodes[0]
                        elif "param_struct_name" in captures_dict:
                            name_nodes = captures_dict["param_struct_name"]
                            if name_nodes and len(name_nodes) > 0:
                                name_node = name_nodes[0]
                        elif "param_abstract_name" in captures_dict:
                            name_nodes = captures_dict["param_abstract_name"]
                            if name_nodes and len(name_nodes) > 0:
                                name_node = name_nodes[0]
                        elif "param_func_name" in captures_dict:
                            name_nodes = captures_dict["param_func_name"]
                            if name_nodes and len(name_nodes) > 0:
                                name_node = name_nodes[0]

                        # Extract signature for functions and macros
                        if declaration_node and kind in ["function", "macro"]:
                            signature = self._extract_julia_signature(
                                declaration_node, byte_content
                            )

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

                            start_line, end_line = get_node_location(declaration_node)
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
                logger.warning(f"Failed to execute Julia query '{query_name}': {e}", exc_info=True)

        # Declaration processing now happens inline

        declarations.sort(key=lambda d: d.start_line)
        sorted_imports = sorted(imports)

        logger.debug(
            f"Tree-sitter Julia extracted {len(declarations)} declarations and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports

    def _extract_julia_signature(self, func_node: Node, byte_content: bytes) -> str:
        """Extract function/macro signature from function or macro definition node.

        Extracts the complete signature including name, parameters, and type annotations.

        Args:
            func_node: Function or macro definition node
            byte_content: Source code as bytes

        Returns:
            Function signature string (e.g., "function calculate(x::Float64, y::Float64)::Float64")
        """
        try:
            # Find the function body to determine signature end
            sig_end_byte = func_node.end_byte

            # Look for the body block to determine signature end
            for child in func_node.children:
                if child.type in ["block_expression", "block"]:
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
            logger.debug(f"Failed to extract Julia function signature: {e}")
            return ""
