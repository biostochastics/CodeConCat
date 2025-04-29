# file: codeconcat/parser/language_parsers/tree_sitter_go_parser.py

import logging
from typing import Dict, List, Set, Any

from tree_sitter import Node

from ...base_types import Declaration
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Define Tree-sitter queries for Go
# Ref: https://github.com/tree-sitter/tree-sitter-go/blob/master/queries/tags.scm

# Define valid declaration capture types for better maintainability
DECLARATION_CAPTURE_TYPES = frozenset(
    {
        "function",
        "method",
        "type_struct_interface",
        "type_alias",
        "constant",
        "variable",
    }
)

GO_QUERIES = {
    "imports": """
        ; Standard imports
        (import_declaration
            (import_spec_list
                (import_spec 
                    path: (interpreted_string_literal) @import_path
                )))

        ; Single imports
        (import_declaration
             (import_spec 
                path: (interpreted_string_literal) @import_path
             ))
             
        ; Named imports (import alias "package")
        (import_declaration
            (import_spec_list
                (import_spec 
                    name: (identifier) @import_alias
                    path: (interpreted_string_literal) @import_path
                )))
                
        ; Single named import
        (import_declaration
             (import_spec 
                name: (identifier) @import_alias
                path: (interpreted_string_literal) @import_path
             ))
    """,
    "declarations": """
        ; Function declarations with parameters and return types
        (function_declaration
            name: (identifier) @name
            parameters: (parameter_list) @params
            result: [                  ; Return types
                (parameter_list) @return_params
                (type_identifier) @return_type
                (pointer_type) @return_type
                (qualified_type) @return_type
                (array_type) @return_type
            ]?
            body: (block) @body
        ) @function
        
        ; Generic function declarations (Go 1.18+)
        (function_declaration
            type_parameters: (type_parameter_list) @type_params
            name: (identifier) @name
            parameters: (parameter_list) @params
            result: (_)? @return_type
            body: (block) @body
        ) @generic_function

        ; Method declarations with receiver types and parameters
        (method_declaration
            receiver: (parameter_list
                (parameter_declaration
                    name: (_)? @receiver_name
                    type: (_) @receiver_type
                )
            ) @receiver
            name: (field_identifier) @name
            parameters: (parameter_list) @params
            result: (_)? @return_type
            body: (block) @body
        ) @method
        
        ; Generic method declarations (Go 1.18+)
        (method_declaration
            type_parameters: (type_parameter_list) @type_params
            receiver: (parameter_list) @receiver
            name: (field_identifier) @name
            parameters: (parameter_list) @params
            result: (_)? @return_type
            body: (block) @body
        ) @generic_method

        ; Struct type declarations with fields
        (type_declaration
            (type_spec
                name: (type_identifier) @name
                type: (struct_type
                    (field_declaration_list
                        (field_declaration
                            name: (field_identifier) @field_name
                            type: (_) @field_type
                            tag: (raw_string_literal)? @field_tag
                        )* 
                    )?
                ) @struct_body
            )
        ) @struct_type
        
        ; Generic struct type declarations (Go 1.18+)
        (type_declaration
            (type_spec
                name: (type_identifier) @name
                type_parameters: (type_parameter_list) @type_params
                type: (struct_type) @struct_body
            )
        ) @generic_struct_type
        
        ; Embedded fields in structs (anonymous fields)
        (type_declaration
            (type_spec
                type: (struct_type
                    (field_declaration_list
                        (field_declaration
                            name: (_)? @embedded_name
                            type: (_) @embedded_type
                        )
                    )
                )
            )
        ) @struct_with_embedded

        ; Interface declarations with methods
        (type_declaration
            (type_spec
                name: (type_identifier) @name
                type: (interface_type
                    (method_spec_list
                        (method_spec
                            name: (field_identifier) @interface_method_name
                            parameters: (parameter_list) @interface_method_params
                            result: (_)? @interface_method_return
                        )* 
                    )?
                ) @interface_body
            )
        ) @interface_type
        
        ; Generic interface declarations (Go 1.18+)
        (type_declaration
            (type_spec
                name: (type_identifier) @name
                type_parameters: (type_parameter_list) @type_params
                type: (interface_type) @interface_body
            )
        ) @generic_interface_type
        
        ; Embedded interfaces
        (type_declaration
            (type_spec
                type: (interface_type
                    (method_spec_list
                        (_) @embedded_interface
                    )
                )
            )
        ) @interface_with_embedded

        ; Type aliases with more detail
        (type_declaration
            (type_spec
                name: (type_identifier) @name
                type: (_) @aliased_type
            )
        ) @type_alias

        ; Constants with values and iota
        (const_declaration
            (const_spec
                name: (identifier) @name
                type: (_)? @const_type
                value: (_)? @const_value
            )
        ) @constant
        
        ; Multiple constants in a single declaration
        (const_declaration
            (const_spec_list
                (const_spec
                    name: (identifier) @const_name
                    type: (_)? @const_type
                    value: (_)? @const_value
                )+
            )
        ) @const_group

        ; Variables with types and initializers
        (var_declaration
            (var_spec
                name: (identifier) @name
                type: (_)? @var_type
                value: (_)? @var_value
            )
        ) @variable
        
        ; Multiple variables in a single declaration
        (var_declaration
            (var_spec_list
                (var_spec
                    name: (identifier) @var_name
                    type: (_)? @var_type
                    value: (_)? @var_value
                )+
            )
        ) @var_group
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

    def _find_type_node(self, captures, node_id):
        """Helper to find a type node by its ID in the captures list.

        Args:
            captures: List of (node, name) tuples from query captures
            node_id: ID of the node to match

        Returns:
            The matching node with name 'type', or None if not found
        """
        for node, name in captures:
            if node.id == node_id and name == "type":
                return node
        return None

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
        # Dictionary mapping node IDs to declaration information
        declaration_map: Dict[int, Dict[str, Any]] = {}  # node_id -> declaration info
        # Dictionary mapping end line numbers to accumulated doc comment text
        doc_comment_map: Dict[int, str] = {}  # end_line -> comment_text

        # --- Pass 1: Extract Doc Comments --- #
        # Go doc comments are consecutive line comments preceding a declaration
        try:
            doc_query = self.ts_language.query(queries.get("doc_comments", ""))
            doc_captures = doc_query.captures(root_node)
            last_comment_line = -2
            current_doc_block: List[str] = []

            for node, _ in doc_captures:
                comment_text = (
                    byte_content[node.start_byte : node.end_byte]
                    .decode("utf8", errors="ignore")
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
                    for node, capture_name in captures:
                        if capture_name == "import_path":
                            # String nodes include quotes, remove them
                            import_path = (
                                byte_content[node.start_byte : node.end_byte]
                                .decode("utf8", errors="ignore")
                                .strip('"')
                            )
                            imports.add(import_path)

                elif query_name == "declarations":
                    current_decl_node_id = None
                    for node, capture_name in captures:
                        node_id = node.id

                        # Identify the main declaration node
                        if capture_name in DECLARATION_CAPTURE_TYPES:
                            current_decl_node_id = (
                                node.parent.id
                            )  # Use parent ID for mapping spec to declaration
                            parent_node = node.parent
                            if current_decl_node_id not in declaration_map:
                                # Determine specific kind if needed (e.g., struct vs interface)
                                kind = capture_name
                                if kind == "type_struct_interface":
                                    # Helper function to find type node by ID
                                    type_node = self._find_type_node(captures, node_id)
                                    kind = type_node.type if type_node else "type"

                                declaration_map[current_decl_node_id] = {
                                    "kind": kind,
                                    "node": parent_node,  # Store parent declaration node
                                    "name": None,
                                    "start_line": parent_node.start_point[0],
                                    "end_line": parent_node.end_point[0],
                                    "modifiers": set(),
                                    "docstring": "",
                                }
                            # Update end line if needed
                            declaration_map[current_decl_node_id]["end_line"] = max(
                                declaration_map[current_decl_node_id]["end_line"],
                                parent_node.end_point[0],
                            )

                        # Capture name
                        elif capture_name == "name" and current_decl_node_id in declaration_map:
                            # Check if name is already set
                            if declaration_map[current_decl_node_id]["name"] is None:
                                name_text = byte_content[node.start_byte : node.end_byte].decode(
                                    "utf8", errors="ignore"
                                )
                                declaration_map[current_decl_node_id]["name"] = name_text

            except Exception as e:
                logger.warning(f"Failed to execute Go query '{query_name}': {e}", exc_info=True)

        # --- Pass 3: Process declarations and associate docstrings --- #
        for decl_info in declaration_map.values():
            if decl_info.get("name"):
                # Check if a doc comment block ended on the line before this declaration started
                docstring = doc_comment_map.get(decl_info["start_line"] - 1, "")

                declarations.append(
                    Declaration(
                        kind=decl_info["kind"],
                        name=decl_info["name"],
                        start_line=decl_info["start_line"],
                        end_line=decl_info["end_line"],
                        docstring=docstring,
                        modifiers=decl_info["modifiers"],
                    )
                )

        declarations.sort(key=lambda d: d.start_line)
        sorted_imports = sorted(list(imports))

        logger.debug(
            f"Tree-sitter Go extracted {len(declarations)} declarations and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports

    # No specific _clean_doc method needed for Go as comments are line-based
