# file: codeconcat/parser/language_parsers/tree_sitter_r_parser.py

import logging
import re
from typing import Dict, List, Set

from tree_sitter import Node, Query, QueryCursor

from ...base_types import Declaration
from ..doc_comment_utils import clean_line_comments, normalize_whitespace
from ..utils import get_node_location
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Define Tree-sitter queries for R
# Ref: https://github.com/tree-sitter/tree-sitter-r/blob/master/queries/tags.scm
R_QUERIES = {
    "imports": """
        ; Standard library/require calls with identifier
        (call
          function: (identifier) @func_name (#match? @func_name "^(library|require)$")
          arguments: (arguments (identifier) @library_name)
        ) @library_call

        ; Standard library/require calls with strings
        (call
          function: (identifier) @func_name (#match? @func_name "^(library|require)$")
          arguments: (arguments (string) @library_name)
        ) @library_call_string

        ; Source calls for importing R files
        (call
          function: (identifier) @func_name (#eq? @func_name "source")
          arguments: (arguments (string) @source_file)
        ) @source_call

        ; Namespace operator usage (package::function or package:::function)
        (namespace_operator
          lhs: (identifier) @package_name
          rhs: (identifier) @function_name
        ) @namespace_call
    """,
    "declarations": """
        ; Function definitions using <- with identifier name (most common)
        (binary_operator
          lhs: (identifier) @name
          operator: "<-"
          rhs: (function_definition) @func_body
        ) @function

        ; Function definitions using = with identifier name
        (binary_operator
          lhs: (identifier) @name
          operator: "="
          rhs: (function_definition) @func_body
        ) @function_equals

        ; Function definitions using <- with string name (e.g., "my_func" <- function())
        (binary_operator
          lhs: (string) @name
          operator: "<-"
          rhs: (function_definition) @func_body
        ) @function_string

        ; Function definitions using = with string name
        (binary_operator
          lhs: (string) @name
          operator: "="
          rhs: (function_definition) @func_body
        ) @function_string_equals

        ; Global constants (UPPERCASE naming convention)
        (binary_operator
          lhs: (identifier) @const_name
          operator: "<-"
          rhs: (_) @const_value
        ) @constant (#match? @const_name "^[A-Z][A-Z0-9_]*$")

        ; Global constants using = operator
        (binary_operator
          lhs: (identifier) @const_name
          operator: "="
          rhs: (_) @const_value
        ) @constant_equals (#match? @const_name "^[A-Z][A-Z0-9_]*$")

        ; S3 method definitions (generic.class naming convention) with <-
        (binary_operator
          lhs: (identifier) @s3_name
          operator: "<-"
          rhs: (function_definition) @s3_body
        ) @s3_method (#match? @s3_name "^[^.]+\\.[^.]+$")

        ; S3 method definitions with = operator
        (binary_operator
          lhs: (identifier) @s3_name
          operator: "="
          rhs: (function_definition) @s3_body
        ) @s3_method_eq (#match? @s3_name "^[^.]+\\.[^.]+$")

        ; S3 generic via UseMethod() calls inside function definitions (direct call)
        (binary_operator
          lhs: (identifier) @s3_generic_name
          operator: "<-"
          rhs: (function_definition
            (call
              (identifier) @use_method (#eq? @use_method "UseMethod")
            )
          ) @s3_generic_body
        ) @s3_generic_arrow

        ; S3 generic with = operator (direct call)
        (binary_operator
          lhs: (identifier) @s3_generic_name_eq
          operator: "="
          rhs: (function_definition
            (call
              (identifier) @use_method_eq (#eq? @use_method_eq "UseMethod")
            )
          ) @s3_generic_body_eq
        ) @s3_generic_equals

        ; S3 generic with UseMethod in braced expression
        (binary_operator
          lhs: (identifier) @s3_generic_name_braced
          operator: "<-"
          rhs: (function_definition
            (braced_expression
              (call
                (identifier) @use_method_braced (#eq? @use_method_braced "UseMethod")
              )
            )
          ) @s3_generic_body_braced
        ) @s3_generic_braced

        ; S3 generic with = and braced expression
        (binary_operator
          lhs: (identifier) @s3_generic_name_eq_braced
          operator: "="
          rhs: (function_definition
            (braced_expression
              (call
                (identifier) @use_method_eq_braced (#eq? @use_method_eq_braced "UseMethod")
              )
            )
          ) @s3_generic_body_eq_braced
        ) @s3_generic_eq_braced

        ; S4 class definition (setClass calls)
        (call
          (identifier) @func_name (#eq? @func_name "setClass")
          (arguments
            (argument (string) @s4_class_name)
          )
        ) @s4_class

        ; S4 class definition with namespace (methods::setClass)
        (call
          (namespace_operator
            (identifier) @namespace
            (identifier) @func_name (#eq? @func_name "setClass")
          )
          (arguments
            (argument (string) @s4_class_name_ns)
          )
        ) @s4_class_ns

        ; S4 method definition (setMethod calls)
        (call
          (identifier) @func_name (#eq? @func_name "setMethod")
          (arguments
            (argument (string) @s4_method_name)
          )
        ) @s4_method

        ; S4 method with namespace
        (call
          (namespace_operator
            (identifier) @namespace
            (identifier) @func_name (#eq? @func_name "setMethod")
          )
          (arguments
            (argument (string) @s4_method_name_ns)
          )
        ) @s4_method_ns

        ; S4 generic definition (setGeneric calls)
        (call
          (identifier) @func_name (#eq? @func_name "setGeneric")
          (arguments
            (argument (string) @s4_generic_name)
          )
        ) @s4_generic_def

        ; S4 generic with namespace
        (call
          (namespace_operator
            (identifier) @namespace
            (identifier) @func_name (#eq? @func_name "setGeneric")
          )
          (arguments
            (argument (string) @s4_generic_name_ns)
          )
        ) @s4_generic_ns
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
def _clean_r_doc_comment(comment_block: List[str]) -> str:
    """Cleans R doc comments using shared doc_comment_utils.

    Handles both Roxygen comments (#') and regular comments (#) consistently
    with other parsers.
    """
    if not comment_block:
        return ""

    # Detect if this is a Roxygen comment block (#') or regular comment (#)
    is_roxygen = any(line.strip().startswith("#'") for line in comment_block)

    if is_roxygen:
        # Use shared line comment cleaner for Roxygen #' style
        prefix_pattern = r"^#'\s*"
        return clean_line_comments(comment_block, prefix_pattern=prefix_pattern)
    else:
        # Use shared line comment cleaner for regular # style
        prefix_pattern = r"^#+\s*"
        return clean_line_comments(comment_block, prefix_pattern=prefix_pattern)


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
            # Use modern Query() constructor and QueryCursor
            doc_query = Query(self.ts_language, queries.get("doc_comments", ""))
            doc_cursor = QueryCursor(doc_query)
            doc_captures = doc_cursor.captures(root_node)
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
                # Use modern Query() constructor and QueryCursor
                query = Query(self.ts_language, query_str)

                if query_name == "imports":
                    # Use captures for imports
                    cursor = QueryCursor(query)
                    captures = cursor.captures(root_node)
                    logger.debug(f"Running R query '{query_name}', found {len(captures)} captures.")

                    # captures is a dict of {capture_name: [list of nodes]}
                    for capture_name, nodes in captures.items():
                        if capture_name in ["library_name", "source_file", "package_name"]:
                            for node in nodes:
                                import_name = (
                                    byte_content[node.start_byte : node.end_byte]
                                    .decode("utf8", errors="replace")
                                    .strip("'\"")
                                )
                                imports.add(import_name)

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

                        # Check for S3 generic declarations FIRST (UseMethod calls)
                        # These are more specific than regular functions and should be detected first
                        s3_generic_types = [
                            "s3_generic_arrow",
                            "s3_generic_equals",
                            "s3_generic_braced",
                            "s3_generic_eq_braced",
                        ]
                        for s3_gen_type in s3_generic_types:
                            if s3_gen_type in captures_dict:
                                s3_gen_nodes = captures_dict[s3_gen_type]
                                if s3_gen_nodes and len(s3_gen_nodes) > 0:
                                    declaration_node = s3_gen_nodes[0]
                                    kind = "s3_generic"
                                    modifiers.add("s3")
                                    break

                        # Check for S3 method declarations (generic.class pattern)
                        if not kind:
                            s3_types = ["s3_method", "s3_method_eq"]
                            for s3_type in s3_types:
                                if s3_type in captures_dict:
                                    nodes = captures_dict[s3_type]
                                    if nodes and len(nodes) > 0:
                                        declaration_node = nodes[0]
                                        kind = "s3_method"
                                        modifiers.add("s3")
                                        break

                        # Check for S4 class declarations
                        if not kind:
                            s4_class_types = ["s4_class", "s4_class_ns"]
                            for s4_class_type in s4_class_types:
                                if s4_class_type in captures_dict:
                                    nodes = captures_dict[s4_class_type]
                                    if nodes and len(nodes) > 0:
                                        declaration_node = nodes[0]
                                        kind = "s4_class"
                                        modifiers.add("s4")
                                        break

                        # Check for S4 method declarations
                        if not kind:
                            s4_method_types = ["s4_method", "s4_method_ns"]
                            for s4_method_type in s4_method_types:
                                if s4_method_type in captures_dict:
                                    nodes = captures_dict[s4_method_type]
                                    if nodes and len(nodes) > 0:
                                        declaration_node = nodes[0]
                                        kind = "s4_method"
                                        modifiers.add("s4")
                                        break

                        # Check for S4 generic declarations
                        if not kind:
                            s4_generic_types = ["s4_generic_def", "s4_generic_ns"]
                            for s4_generic_type in s4_generic_types:
                                if s4_generic_type in captures_dict:
                                    nodes = captures_dict[s4_generic_type]
                                    if nodes and len(nodes) > 0:
                                        declaration_node = nodes[0]
                                        kind = "s4_generic"
                                        modifiers.add("s4")
                                        break

                        # Check for regular function declarations (catch-all for functions)
                        if not kind:
                            func_types = [
                                "function",
                                "function_equals",
                                "function_string",
                                "function_string_equals",
                            ]
                            for func_type in func_types:
                                if func_type in captures_dict:
                                    nodes = captures_dict[func_type]
                                    if nodes and len(nodes) > 0:
                                        declaration_node = nodes[0]
                                        kind = "function"
                                        break

                        # Check for constant declarations
                        if not kind:
                            const_types = ["constant", "constant_equals"]
                            for const_type in const_types:
                                if const_type in captures_dict:
                                    nodes = captures_dict[const_type]
                                    if nodes and len(nodes) > 0:
                                        declaration_node = nodes[0]
                                        kind = "constant"
                                        modifiers.add("const")
                                        break

                        # Get the name node (from various capture types)
                        name_capture_types = [
                            "name",
                            "const_name",
                            "s3_name",
                            "generic_name",
                            "s3_generic_name",
                            "s3_generic_name_eq",
                            "s3_generic_name_braced",
                            "s3_generic_name_eq_braced",
                            "s4_class_name",
                            "s4_class_name_ns",
                            "s4_method_name",
                            "s4_method_name_ns",
                            "s4_generic_name",
                            "s4_generic_name_ns",
                        ]
                        for capture_type in name_capture_types:
                            if capture_type in captures_dict:
                                name_nodes = captures_dict[capture_type]
                                if name_nodes and len(name_nodes) > 0:
                                    name_node = name_nodes[0]
                                    break

                        # Extract signature for functions
                        if declaration_node and kind == "function":
                            signature = self._extract_r_signature(declaration_node, byte_content)

                        # Add declaration if we have both node and name
                        if declaration_node and name_node:
                            name_text = byte_content[
                                name_node.start_byte : name_node.end_byte
                            ].decode("utf8", errors="replace")

                            # Clean string names (remove quotes)
                            # Remove leading/trailing quotes (single or double)
                            if (
                                (name_text.startswith('"') or name_text.startswith("'"))
                                and len(name_text) >= 2
                                and name_text[0] == name_text[-1]
                            ):
                                name_text = name_text[1:-1]  # Remove quotes

                            # Validate kind-specific naming patterns
                            # (tree-sitter predicates aren't auto-evaluated in Python)
                            if kind == "constant" and not re.match(r"^[A-Z][A-Z0-9_]*$", name_text):
                                # Constants must be UPPERCASE with underscores
                                continue  # Skip this declaration
                            elif kind == "s3_method" and not re.match(r"^[^.]+\.[^.]+$", name_text):
                                # S3 methods must have generic.class pattern (contain a dot)
                                continue  # Skip this declaration

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
                logger.warning(f"Failed to execute R query '{query_name}': {e}", exc_info=True)

        # Declaration processing now happens inline

        declarations.sort(key=lambda d: d.start_line)
        sorted_imports = sorted(imports)

        logger.debug(
            f"Tree-sitter R extracted {len(declarations)} declarations and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports

    def _extract_r_signature(self, func_node: Node, byte_content: bytes) -> str:
        """Extract function signature from function definition node.

        Extracts the complete signature including name, parameters, and assignment operator.

        Args:
            func_node: Function definition assignment node
            byte_content: Source code as bytes

        Returns:
            Function signature string (e.g., "calculate <- function(x, y)")
        """
        try:
            # R function definitions are in the form: name <- function(params)
            # Extract from the start of assignment to the end of parameter list
            sig_end_byte = func_node.end_byte

            # Look for the function body (brace or expression)
            for child in func_node.children:
                if child.type == "function_definition":
                    # Navigate to the function definition's body
                    for func_child in child.children:
                        if func_child.type in ["braced_expression", "brace_list"]:
                            sig_end_byte = func_child.start_byte
                            break
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
            logger.debug(f"Failed to extract R function signature: {e}")
            return ""
