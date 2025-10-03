# file: codeconcat/parser/language_parsers/tree_sitter_php_parser.py

import logging
from typing import Dict, List, Set

from tree_sitter import Node, Query

# QueryCursor was removed in tree-sitter 0.24.0 - import it if available for backward compatibility
try:
    from tree_sitter import QueryCursor
except ImportError:
    QueryCursor = None  # type: ignore[assignment,misc]

from ...base_types import Declaration
from ..doc_comment_utils import clean_block_comments, normalize_whitespace
from ..utils import get_node_location
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Define Tree-sitter queries for PHP
# Ref: https://github.com/tree-sitter/tree-sitter-php/blob/master/queries/tags.scm
PHP_QUERIES = {
    "imports": """
        ; Basic use statement (class import)
        (use_declaration
          (namespace_use_clause name: (name) @import_path)
        ) @use_statement

        ; Function imports with 'use function'
        (use_declaration
          "function"
          (namespace_use_clause name: (name) @function_import_path)
        ) @function_use_statement

        ; Constant imports with 'use const'
        (use_declaration
          "const"
          (namespace_use_clause name: (name) @const_import_path)
        ) @const_use_statement

        ; Group use statements - namespace part
        (namespace_use_declaration
            (namespace_name) @group_import_prefix
        ) @use_statement_group

        ; Group use statements - individual items
        (namespace_use_declaration
            (namespace_use_group
                (namespace_use_clause
                    name: (name) @group_import_item
                )
            )
        )

        ; Function use statements with aliases
        (use_declaration
          (namespace_use_clause
            name: (name) @import_path
            alias: (name) @import_alias
          )
        ) @use_statement_with_alias

        ; require/include statements
        (call_expression
          function: (name) @func_name (#match? @func_name "^(require|require_once|include|include_once)$")
          arguments: (arguments (string) @import_path)
        ) @require_include

        ; autoload registration (common pattern)
        (call_expression
          function: (name) @register_func (#eq? @register_func "spl_autoload_register")
        ) @autoload_registration
    """,
    "declarations": """
        ; Namespace definitions
        (namespace_definition
            name: (namespace_name) @name
        ) @namespace

        ; Class declarations
        (class_declaration
            name: (name) @name
        ) @class

        ; Interface declarations
        (interface_declaration
            name: (name) @name
        ) @interface

        ; Trait declarations
        (trait_declaration
            name: (name) @name
        ) @trait

        ; Function definitions
        (function_definition
            name: (name) @name
        ) @function

        ; Method declarations
        (method_declaration
            name: (name) @name
        ) @method

        ; Const declarations
        (const_declaration
            (const_element
                name: (name) @name
                value: (_) @const_value
            )
        ) @const

        ; Properties with type declarations and nullability
        (property_declaration
            (attribute_list
                (attribute
                    name: (name) @prop_attr_name
                    arguments: (arguments)? @prop_attr_args
                )
            )* @property_attributes
            modifiers: [
                "public" "protected" "private"
                "static" "readonly"
            ]* @property_modifiers
            type: (_)? @property_type
            (property_element
                name: (variable_name) @name
                default_value: (_)? @property_default
            )
        ) @property

        ; Enum declarations (PHP 8.1+)
        (enum_declaration
            (attribute_list
                (attribute
                    name: (name) @enum_attr_name
                    arguments: (arguments)? @enum_attr_args
                )
            )* @enum_attributes
            name: (name) @name
            implements: (class_interface_clause
                (name_list)? @enum_implements_list
            )?
            (enum_case
                name: (name) @enum_case_name
                value: (_)? @enum_case_value
            )* @enum_cases
            body: (declaration_list) @enum_body
        ) @enum

        ; Global variables (less common)
        (global_declaration
            (variable_name) @name
        ) @global_variable
    """,
    # Capture PHPDoc style comments /** ... */ and line comments with // starting with @
    "doc_comments": """
        ; PHPDoc block comments
        (comment) @doc_comment (#match? @doc_comment "^/\\\\*\\\\*")

        ; Single line annotations (less common but used in some codebases)
        (comment) @line_annotation (#match? @line_annotation "^//\\\\s*@")

        ; File-level docblock
        (program . (comment) @file_doc_comment (#match? @file_doc_comment "^/\\\\*\\\\*"))
    """,
}


# Patterns to clean PHPDoc comments
def _clean_php_doc_comment(comment_block: List[str]) -> str:
    """Cleans a block of PHPDoc comment lines using shared doc_comment_utils.

    PHPDoc uses the same /** */ format as Javadoc and JSDoc, so we can
    use the shared block comment cleaner.
    """
    if not comment_block:
        return ""
    # Use shared block comment cleaner for /** */ style
    return clean_block_comments(comment_block)


class TreeSitterPhpParser(BaseTreeSitterParser):
    """Tree-sitter based parser for the PHP language."""

    def __init__(self):
        """Initializes the PHP Tree-sitter parser."""
        super().__init__(language_name="php")

    def get_queries(self) -> Dict[str, str]:
        """Returns the predefined Tree-sitter queries for PHP."""
        return PHP_QUERIES

    def _run_queries(
        self, root_node: Node, byte_content: bytes
    ) -> tuple[List[Declaration], List[str]]:
        """Runs PHP-specific queries and extracts declarations and imports."""
        queries = self.get_queries()
        declarations = []
        imports: Set[str] = set()
        doc_comment_map = {}  # end_line -> raw comment_text (list of lines)
        current_namespace = ""

        # --- Pass 1: Extract Doc Comments --- #
        try:
            # Use modern Query() constructor and QueryCursor
            doc_query = Query(self.ts_language, queries.get("doc_comments", ""))
            doc_captures = self._execute_query_with_cursor(doc_query, root_node)

            # doc_captures is a dict: {capture_name: [list of nodes]}
            for _capture_name, nodes in doc_captures.items():
                for node in nodes:
                    comment_text = byte_content[node.start_byte : node.end_byte].decode(
                        "utf8", errors="replace"
                    )
                    # PHPDoc comments are always block comments /** ... */
                    if comment_text.startswith("/**"):
                        doc_comment_map[node.end_point[0]] = comment_text.splitlines()

        except Exception as e:
            logger.warning(f"Failed to execute PHP doc_comments query: {e}", exc_info=True)

        # --- Pass 2: Extract Imports and Declarations --- #
        current_namespace = ""
        for query_name, query_str in queries.items():
            if query_name == "doc_comments":
                continue

            try:
                # Use modern Query() constructor and QueryCursor
                query = Query(self.ts_language, query_str)

                if query_name == "imports":
                    # Use captures for imports
                    captures = self._execute_query_with_cursor(query, root_node)
                    logger.debug(
                        f"Running PHP query '{query_name}', found {len(captures)} captures."
                    )

                    # captures is a dict of {capture_name: [list of nodes]}
                    for capture_name, nodes in captures.items():
                        if capture_name in [
                            "import_path",
                            "function_import_path",
                            "const_import_path",
                            "group_import_item",
                            "group_import_prefix",
                        ]:
                            for node in nodes:
                                import_path = (
                                    byte_content[node.start_byte : node.end_byte]
                                    .decode("utf8", errors="replace")
                                    .strip("'\"")
                                )
                                imports.add(import_path)

                elif query_name == "declarations":
                    # Use matches for better structure with declarations
                    matches = self._execute_query_matches(query, root_node)
                    for _match_id, captures_dict in matches:
                        declaration_node = None
                        name_node = None
                        kind = None
                        modifiers = set()
                        signature = ""

                        # Check for various declaration types
                        decl_types = [
                            "namespace",
                            "class",
                            "interface",
                            "trait",
                            "enum",
                            "function",
                            "method",
                            "property",
                            "class_constant",
                            "global_variable",
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

                        # Get modifiers
                        if "property_modifiers" in captures_dict:
                            for mod_node in captures_dict["property_modifiers"]:
                                modifier_text = byte_content[
                                    mod_node.start_byte : mod_node.end_byte
                                ].decode("utf8", errors="replace")
                                modifiers.add(modifier_text)

                        # Extract signature for functions and methods
                        if declaration_node and kind in ["function", "method"]:
                            signature = self._extract_php_signature(declaration_node, byte_content)

                        # Add declaration if we have both node and name
                        if declaration_node and name_node:
                            name_text = byte_content[
                                name_node.start_byte : name_node.end_byte
                            ].decode("utf8", errors="replace")

                            # Update current namespace if this is a namespace declaration
                            if kind == "namespace":
                                current_namespace = name_text

                            # For non-namespace declarations, prepend namespace if exists
                            if kind != "namespace" and current_namespace:
                                full_name = f"{current_namespace}\\{name_text}"
                            else:
                                full_name = name_text

                            # Check for docstring
                            docstring_lines = doc_comment_map.get(
                                declaration_node.start_point[0] - 1, []
                            )
                            docstring = (
                                _clean_php_doc_comment(docstring_lines) if docstring_lines else ""
                            )

                            start_line, end_line = get_node_location(declaration_node)
                            declarations.append(
                                Declaration(
                                    kind=kind or "unknown",
                                    name=full_name,
                                    start_line=start_line,
                                    end_line=end_line,
                                    docstring=docstring,
                                    signature=signature,
                                    modifiers=modifiers,
                                )
                            )

            except Exception as e:
                logger.warning(f"Failed to execute PHP query '{query_name}': {e}", exc_info=True)

        # Declaration processing now happens inline

        declarations.sort(key=lambda d: d.start_line)
        sorted_imports = sorted(imports)

        logger.debug(
            f"Tree-sitter PHP extracted {len(declarations)} declarations and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports

    def _extract_php_signature(self, func_node: Node, byte_content: bytes) -> str:
        """Extract function/method signature from function or method declaration node.

        Extracts the complete signature including name, parameters, return type,
        and modifiers.

        Args:
            func_node: Function or method declaration node
            byte_content: Source code as bytes

        Returns:
            Function signature string (e.g., "public function getName(int $id): ?string")
        """
        try:
            # Find the function body to determine signature end
            sig_end_byte = func_node.end_byte

            # Look for the opening brace or semicolon (for abstract methods)
            for child in func_node.children:
                if child.type in ["compound_statement", ";"]:
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
            logger.debug(f"Failed to extract PHP function signature: {e}")
            return ""
