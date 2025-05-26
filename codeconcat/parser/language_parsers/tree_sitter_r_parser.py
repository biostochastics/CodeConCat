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
        ; Standard library/require calls with unquoted package names
        (call
          function: (identifier) @func_name (#match? @func_name "^(library|require)$")
          arguments: (arguments . (identifier) @library_name)
        ) @library_call_unquoted

        ; Standard library/require calls with quoted package names
        (call
          function: (identifier) @func_name (#match? @func_name "^(library|require)$")
          arguments: (arguments . (string) @library_name)
        ) @library_call_quoted
        
        ; Catch imports with named parameter
        (call
          function: (identifier) @func_name (#match? @func_name "^(library|require)$")
          arguments: (arguments
            (named_argument
              name: (identifier) @param_name (#match? @param_name "^(package)$")
              value: [(identifier) (string)] @library_name
            )
          )
        ) @library_call_named
        
        ; Package::function notation (implicit dependency)
        (namespace_get
          namespace: (identifier) @namespace
          function: (_) @function
        ) @namespace_usage
    """,
    "declarations": """
        ; Function definition assignment: my_func <- function(...) { ... }
        (assignment
          operator: "<-"
          left: (identifier) @name
          right: (function_definition
            parameters: (formal_parameters)? @params
            body: (expression_list)? @body
          ) @func_body
        ) @function_assignment

        ; Function definition assignment: my_func = function(...) { ... }
        (assignment
          operator: "="
          left: (identifier) @name
          right: (function_definition
            parameters: (formal_parameters)? @params
            body: (expression_list)? @body
          ) @func_body
        ) @function_assignment_equals
        
        ; Piped function definition (magrittr): ... %>% function(...) { ... }
        (pipe
          left: (_) @pipe_left
          right: (function_definition
            parameters: (formal_parameters)? @pipe_func_params
            body: (expression_list)? @pipe_func_body
          ) @pipe_func
        ) @pipe_function
        
        ; Native pipe function definition (R 4.1+): ... |> function(...) { ... }
        (binary_operator
          operator: "|>"
          left: (_) @native_pipe_left
          right: (function_definition
            parameters: (formal_parameters)? @native_pipe_func_params
            body: (expression_list)? @native_pipe_func_body
          ) @native_pipe_func
        ) @native_pipe_function

        ; Variable assignment: my_var <- ...
        (assignment
          operator: "<-"
          left: (identifier) @name
        ) @variable_assignment

        ; Variable assignment: my_var = ... (excluding function definitions)
        (assignment
          operator: "="
          left: (identifier) @name
          right: [(identifier) (string) (number) (call) (binary_operator)]
        ) @variable_assignment_equals

        ; S3 method definition: function(x, ...) UseMethod("function")
        (assignment
          left: (identifier) @s3_generic_name
          right: (function_definition
            body: (expression_list
              (call
                function: (identifier) @usemethod (#eq? @usemethod "UseMethod")
                arguments: (arguments (string) @method_name)
              )
            )
          )
        ) @s3_generic
        
        ; S3 specific method: function.class <- function(...) { ... }
        (assignment
          left: [
            (identifier) @s3_method_name (#match? @s3_method_name "^[a-zA-Z0-9_]+\\.[a-zA-Z0-9_]+$")
          ]
          right: (function_definition)
        ) @s3_method

        ; S4 Class Definition: setClass("MyClass", ...)
        (call
          function: (identifier) @func_name (#eq? @func_name "setClass")
          arguments: (arguments 
            (string) @name
            (named_argument
              name: (identifier) @slot_param (#eq? @slot_param "slots")
              value: (_) @slot_definitions
            )?
            (named_argument
              name: (identifier) @contains_param (#eq? @contains_param "contains")
              value: (_) @parent_classes
            )?
          )
        ) @s4_class

        ; S4 Method Definition: setMethod("myMethod", ...)
        (call
          function: (identifier) @func_name (#eq? @func_name "setMethod")
          arguments: (arguments 
            (string) @name
            (named_argument
              name: (identifier) @signature_param (#eq? @signature_param "signature")
              value: (_) @method_signature
            )?
            (named_argument
              name: (identifier) @def_param (#eq? @def_param "definition")
              value: (_) @method_definition
            )?
          )
        ) @s4_method
        
        ; S4 Generic Definition: setGeneric("myGeneric", ...)
        (call
          function: (identifier) @func_name (#eq? @func_name "setGeneric")
          arguments: (arguments 
            (string) @name
            (named_argument
              name: (identifier) @def_param (#eq? @def_param "def")
              value: (_) @generic_definition
            )?
          )
        ) @s4_generic

        ; R6 Class Definition: MyClass <- R6Class("MyClass", ...)
        (assignment
           left: (identifier) @name
           right: (call 
             function: (identifier) @call_name (#eq? @call_name "R6Class")
             arguments: (arguments
               (string) @class_name
               (named_argument
                 name: (identifier) @inherit_param (#eq? @inherit_param "inherit")
                 value: (_) @parent_class
               )?
               (named_argument
                 name: (identifier) @public_param (#eq? @public_param "public")
                 value: (_) @public_methods
               )?
               (named_argument
                 name: (identifier) @private_param (#eq? @private_param "private")
                 value: (_) @private_methods
               )?
             )
           )
        ) @r6_class
        
        ; Reference class: setRefClass("MyClass", ...)
        (call
          function: (identifier) @func_name (#eq? @func_name "setRefClass")
          arguments: (arguments 
            (string) @name
            (named_argument
              name: (identifier) @fields_param (#eq? @fields_param "fields")
              value: (_) @class_fields
            )?
            (named_argument
              name: (identifier) @methods_param (#eq? @methods_param "methods")
              value: (_) @class_methods
            )?
            (named_argument
              name: (identifier) @contains_param (#eq? @contains_param "contains")
              value: (_) @parent_classes
            )?
          )
        ) @reference_class
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
    cleaned_lines = []
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
                    for capture in captures:
                        # Handle both 2-tuple and 3-tuple captures from different tree-sitter versions
                        if len(capture) == 2:
                            node, capture_name = capture
                        else:
                            node, capture_name, _ = capture
                        if capture_name == "library_name":
                            library_name = (
                                byte_content[node.start_byte : node.end_byte]
                                .decode("utf8", errors="ignore")
                                .strip("'\"")
                            )
                            imports.add(library_name)

                elif query_name == "declarations":
                    # Group captures by declaration node ID (typically the assignment or call node)
                    node_capture_map = {}
                    for capture in captures:
                        # Handle both 2-tuple and 3-tuple captures from different tree-sitter versions
                        if len(capture) == 2:
                            node, capture_name = capture
                        else:
                            node, capture_name, _ = capture
                        decl_node = node
                        # Find the top-level expression node (assignment, call)
                        while decl_node.parent and decl_node.type not in [
                            "assignment",
                            "call",
                            "program",  # program is root
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
                        # Use the @kind capture name from the query if present
                        if capture_name in [
                            "function_assignment",
                            "function_assignment_equals",
                            "variable_assignment",
                            "variable_assignment_equals",
                            "s4_class",
                            "s4_method",
                            "r6_class",
                        ]:
                            node_capture_map[decl_id]["kind"] = capture_name

                    # Process grouped captures
                    for decl_id, data in node_capture_map.items():
                        decl_node = data["node"]
                        node_captures = data["captures"]
                        kind = data["kind"]  # Derived from capture name

                        if not kind:
                            continue  # Skip if no kind was assigned

                        # Map capture kinds to Declaration kinds
                        kind_map = {
                            "function_assignment": "function",
                            "function_assignment_equals": "function",
                            "variable_assignment": "variable",
                            "variable_assignment_equals": "variable",
                            "s4_class": "class",
                            "s4_method": "method",
                            "r6_class": "class",
                        }
                        final_kind = kind_map.get(kind)
                        if not final_kind:
                            continue  # Skip if mapping fails

                        name_node = next((n for n, cname in node_captures if cname == "name"), None)
                        name = (
                            byte_content[name_node.start_byte : name_node.end_byte]
                            .decode("utf8", errors="ignore")
                            .strip("'\"")
                            if name_node
                            else "<unknown>"
                        )

                        if name == "<unknown>":
                            continue  # Skip unnamed declarations

                        start_line = decl_node.start_point[0]
                        end_line = decl_node.end_point[0]

                        # Store declaration info, avoiding duplicates if multiple captures point to the same node
                        if decl_id not in declaration_map:
                            declaration_map[decl_id] = {
                                "kind": final_kind,
                                "name": name,
                                "start_line": start_line,
                                "end_line": end_line,
                                "modifiers": set(),
                                "docstring": "",
                            }
                        else:
                            # Ensure the most specific kind (e.g., function over variable) is kept if overlaps occur
                            if (
                                final_kind == "function"
                                and declaration_map[decl_id]["kind"] == "variable"
                            ):
                                declaration_map[decl_id]["kind"] = "function"
                            declaration_map[decl_id]["end_line"] = max(
                                declaration_map[decl_id]["end_line"], end_line
                            )
                            if declaration_map[decl_id]["name"] == "<unknown>":
                                declaration_map[decl_id]["name"] = name

            except Exception as e:
                logger.warning(f"Failed to execute R query '{query_name}': {e}", exc_info=True)

        # --- Pass 3: Process declarations and associate comments --- #
        for decl_id, decl_info in declaration_map.items():
            if decl_info.get("name") and decl_info["name"] != "<unknown>":
                # Check for comments ending on the line before the declaration
                raw_doc_block = doc_comment_map.get(decl_info["start_line"] - 1, [])
                # Use Roxygen convention: comments starting with #' are often documentation
                is_roxygen = any(line.strip().startswith("#'") for line in raw_doc_block)
                cleaned_docstring = (
                    _clean_r_doc_comment(raw_doc_block) if is_roxygen else ""
                )  # Only use if looks like Roxygen

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
            f"Tree-sitter R extracted {len(declarations)} declarations and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports
