# file: codeconcat/parser/language_parsers/tree_sitter_js_ts_parser.py

import logging
from typing import Dict, List, Set

from tree_sitter import Node

from ...base_types import Declaration
from ..doc_comment_utils import clean_block_comments, clean_jsdoc_tags
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Define Tree-sitter queries for JavaScript/TypeScript
# Ref JS: https://github.com/tree-sitter/tree-sitter-javascript/blob/master/queries/tags.scm
# Ref TS: https://github.com/tree-sitter/tree-sitter-typescript/blob/master/typescript/queries/tags.scm
# Combining common constructs. More specific TS types could be added if needed.
JS_TS_QUERIES = {
    "imports": """
        ; Standard ESM imports - simplified to capture source
        (import_statement
            source: (string) @import_source
        ) @import_stmt

        ; CommonJS require statements
        (call_expression
            function: (identifier) @require_func (#eq? @require_func "require")
            arguments: (arguments (string) @require_source)
        ) @require_stmt

        ; Dynamic imports
        (call_expression
            function: (import)
            arguments: (arguments (string) @dynamic_import_source)
        ) @dynamic_import
    """,
    "declarations": """
        ; Function declarations
        (function_declaration
            "async"? @async_modifier
            name: (identifier) @name
            parameters: (formal_parameters) @params
            return_type: (type_annotation)? @return_type
            body: (statement_block) @body
        ) @function

        ; Generator function declarations
        (generator_function_declaration
            name: (identifier) @name
            parameters: (formal_parameters) @params
            body: (statement_block) @body
        ) @generator_function

        ; Arrow functions assigned to variables
        (lexical_declaration
            (variable_declarator
                name: (identifier) @name
                value: (arrow_function
                    "async"? @arrow_async
                    parameters: [(formal_parameters) (identifier)] @arrow_params
                    body: [(statement_block) (expression)] @arrow_body
                )
            )
        ) @arrow_function

        ; Function expressions assigned to variables
        (lexical_declaration
            (variable_declarator
                name: (identifier) @name
                value: (function_expression
                    parameters: (formal_parameters) @func_params
                    body: (statement_block) @func_body
                )
            )
        ) @function_expression

        ; Class declarations
        (class_declaration
            name: (identifier) @name
            superclass: (class_heritage)? @extends
            body: (class_body) @body
        ) @class

        ; Class methods
        (method_definition
            "static"? @static_modifier
            "async"? @async_modifier
            "*"? @generator_modifier
            name: [(property_identifier) (computed_property_name) (private_property_identifier)] @name
            parameters: (formal_parameters) @params
            body: (statement_block) @body
        ) @method

        ; Class fields
        (field_definition
            "static"? @static_field
            name: [(property_identifier) (private_property_identifier)] @field_name
            type: (type_annotation)? @field_type
            value: (_)? @field_value
        ) @class_field

        ; TypeScript interface declarations
        (interface_declaration
            name: (type_identifier) @name
            type_parameters: (type_parameters)? @type_params
            extends: (extends_type_clause)? @extends
            body: (object_type) @body
        ) @interface

        ; TypeScript type alias declarations
        (type_alias_declaration
            name: (type_identifier) @name
            type_parameters: (type_parameters)? @type_params
            value: (_) @type_value
        ) @type_alias

        ; TypeScript enum declarations
        (enum_declaration
            "const"? @const_modifier
            name: (identifier) @name
            body: (enum_body) @body
        ) @enum

        ; TypeScript namespace declarations
        (namespace_declaration
            name: [(identifier) (nested_identifier)] @name
            body: (statement_block) @body
        ) @namespace

        ; Variable declarations (const, let, var)
        (lexical_declaration
            (variable_declarator
                name: (identifier) @name
                type: (type_annotation)? @var_type
                value: (_)? @var_value
            )
        ) @variable
    """,
    "doc_comments": """
    ; Capturing all comments for diagnostic purposes
    (comment) @doc_comment
""",
}


class TreeSitterJsTsParser(BaseTreeSitterParser):
    """Tree-sitter based parser for JavaScript and TypeScript languages."""

    def __init__(self, language="javascript"):  # Default to JS, override for TS
        """Initializes the JS/TS Tree-sitter parser."""
        if language not in ["javascript", "typescript"]:
            raise ValueError("Language must be 'javascript' or 'typescript'")
        super().__init__(language_name=language)
        self.language = language

    def get_queries(self) -> Dict[str, str]:
        """Returns the predefined Tree-sitter queries for JS/TS."""
        # For JavaScript, we need to filter out TypeScript-specific syntax
        if self.language == "javascript":
            # Create a copy and modify declarations to remove TypeScript-specific items
            js_queries = {
                "imports": JS_TS_QUERIES["imports"],
                "doc_comments": JS_TS_QUERIES["doc_comments"],
            }
            # Simplified JavaScript declarations without TypeScript features
            js_queries["declarations"] = """
        ; Standard function declarations
        (function_declaration
            "async"? @async_modifier
            name: (identifier) @name
        ) @function

        ; Generator function declarations
        (generator_function_declaration
            name: (identifier) @name
        ) @generator_function

        ; Arrow functions assigned to variables
        (lexical_declaration
            (variable_declarator
                name: (identifier) @name
                value: (arrow_function)
            )
        ) @arrow_function_const

        ; Arrow functions assigned to var variables
        (variable_declaration
            (variable_declarator
                name: (identifier) @name
                value: (arrow_function)
            )
        ) @arrow_function_var

        ; Class declarations
        (class_declaration
            name: (identifier) @name
        ) @class

        ; Class methods
        (method_definition
            "static"? @static_modifier
            "async"? @async_modifier
            name: (property_identifier) @name
        ) @method

        ; Function expressions assigned to variables
        (lexical_declaration
            (variable_declarator
                name: (identifier) @name
                value: (function_expression)
            )
        ) @function_expression_const

        ; Function expressions assigned to var variables
        (variable_declaration
            (variable_declarator
                name: (identifier) @name
                value: (function_expression)
            )
        ) @function_expression_var
            """
            return js_queries
        return JS_TS_QUERIES

    def _run_queries(
        self, root_node: Node, byte_content: bytes
    ) -> tuple[List[Declaration], List[str]]:
        """Runs JS/TS-specific queries and extracts declarations and imports."""
        queries = self.get_queries()
        declarations = []
        imports: Set[str] = set()
        doc_comment_map = {}  # end_line -> comment_text

        # --- Pass 1: Extract Doc Comments --- #
        try:
            doc_query = self.ts_language.query(queries.get("doc_comments", ""))
            doc_captures = doc_query.captures(root_node)
            # doc_captures is a dict: {capture_name: [list of nodes]}
            for _capture_name, nodes in doc_captures.items():
                for node in nodes:
                    comment_text = byte_content[node.start_byte : node.end_byte].decode(
                        "utf8", errors="replace"
                    )
                    # Store comment keyed by its end line
                    doc_comment_map[node.end_point[0]] = self._clean_jsdoc(comment_text)
        except Exception as e:
            logger.warning(f"Failed to execute JS/TS doc_comments query: {e}", exc_info=True)

        # --- Pass 2: Extract Imports and Declarations --- #
        for query_name, query_str in queries.items():
            if query_name == "doc_comments":
                continue

            try:
                query = self.ts_language.query(query_str)
                captures = query.captures(root_node)
                logger.debug(f"Running JS/TS query '{query_name}', found {len(captures)} captures.")

                if query_name == "imports":
                    # captures is a dict of {capture_name: [list of nodes]}
                    # Fixed capture unpacking pattern
                    for capture in captures.items():
                        if len(capture) == 2:
                            capture_name, nodes = capture
                        else:
                            continue
                        if (
                            capture_name.startswith("import_source")
                            or capture_name == "require_source"
                            or capture_name == "dynamic_import_source"
                        ):
                            for node in nodes:
                                # String nodes include quotes, remove them
                                import_path = (
                                    byte_content[node.start_byte : node.end_byte]
                                    .decode("utf8", errors="replace")
                                    .strip("\"'")
                                )
                                imports.add(import_path)

                elif query_name == "declarations":
                    logger.debug("Processing declarations query...")
                    # Use matches for better structure with declarations
                    matches = query.matches(root_node)
                    logger.debug(f"Got {len(matches)} matches")
                    for match_id, captures_dict in matches:
                        logger.debug(
                            f"Match {match_id}, captures_dict keys: {captures_dict.keys()}"
                        )
                        declaration_node = None
                        name_node = None
                        kind = None
                        modifiers = set()

                        # Check for various declaration types in the captures
                        declaration_types = [
                            "function",
                            "generator_function",
                            "class",
                            "method",
                            "arrow_function",
                            "function_expression",
                            "class_expression",
                            "interface",
                            "type_alias",
                            "enum",
                            "ambient_function",
                            "ambient_class",
                        ]

                        for decl_type in declaration_types:
                            if decl_type in captures_dict:
                                nodes = captures_dict[decl_type]
                                if nodes and len(nodes) > 0:
                                    declaration_node = nodes[0]
                                    kind = decl_type
                                    break

                        # Get the name node if present
                        if "name" in captures_dict:
                            name_nodes = captures_dict["name"]
                            if name_nodes and len(name_nodes) > 0:
                                name_node = name_nodes[0]

                        # Check for modifiers
                        if "async_modifier" in captures_dict:
                            nodes = captures_dict["async_modifier"]
                            logger.debug(
                                f"async_modifier found: {nodes}, len={len(nodes) if nodes else 0}"
                            )
                            if nodes and len(nodes) > 0:
                                modifiers.add("async")
                                logger.debug("Added async to modifiers")
                        if "static_modifier" in captures_dict:
                            nodes = captures_dict["static_modifier"]
                            if nodes and len(nodes) > 0:
                                modifiers.add("static")
                        if "generator_modifier" in captures_dict:
                            nodes = captures_dict["generator_modifier"]
                            if nodes and len(nodes) > 0:
                                modifiers.add("generator")

                        # Add declaration if we have both node and name
                        if declaration_node and name_node:
                            name_text = byte_content[
                                name_node.start_byte : name_node.end_byte
                            ].decode("utf8", errors="replace")

                            # Check for docstring
                            docstring = doc_comment_map.get(declaration_node.start_point[0] - 1, "")

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
                logger.warning(f"Failed to execute JS/TS query '{query_name}': {e}", exc_info=True)

        # Declaration map no longer needed - processing happens inline

        declarations.sort(key=lambda d: d.start_line)
        sorted_imports = sorted(imports)

        logger.debug(
            f"Tree-sitter {self.language} extracted {len(declarations)} declarations and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports

    def _clean_jsdoc(self, comment_text: str) -> str:
        """Cleans a JSDoc block comment using shared doc_comment_utils.

        This method now leverages the shared utilities for consistent
        comment cleaning across all parsers.
        """
        lines = comment_text.split("\n")
        # First, clean the block comment structure (/** */ and leading *)
        cleaned = clean_block_comments(lines, preserve_structure=True)
        # Then process JSDoc tags (@param, @returns, etc.)
        return clean_jsdoc_tags(cleaned)
