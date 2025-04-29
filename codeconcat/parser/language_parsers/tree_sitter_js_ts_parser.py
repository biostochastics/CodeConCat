# file: codeconcat/parser/language_parsers/tree_sitter_js_ts_parser.py

import logging
from typing import Dict, List, Set

from tree_sitter import Node

from ...base_types import Declaration
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Define Tree-sitter queries for JavaScript/TypeScript
# Ref JS: https://github.com/tree-sitter/tree-sitter-javascript/blob/master/queries/tags.scm
# Ref TS: https://github.com/tree-sitter/tree-sitter-typescript/blob/master/typescript/queries/tags.scm
# Combining common constructs. More specific TS types could be added if needed.
JS_TS_QUERIES = {
    "imports": """
        ; Standard ESM imports
        (import_statement
            source: (string) @import_source
        ) @import_stmt
        
        ; Default imports (import Name from 'module')
        (import_statement
            (import_clause
                (identifier) @default_import
            )
            source: (string) @import_source_default
        ) @default_import_stmt
        
        ; Named imports (import { name } from 'module')
        (import_statement
             (import_clause 
                (named_imports 
                    (import_specifier 
                        name: (identifier) @named_import
                        alias: (identifier)? @import_alias
                    )+
                )
             )
             source: (string) @import_source_named
        ) @named_import_stmt
        
        ; Namespace imports (import * as name from 'module')
        (import_statement
            (import_clause
                (namespace_import 
                    (identifier) @namespace_name
                )
            )
            source: (string) @import_source_namespace
        ) @namespace_import_stmt

        ; Dynamic import expressions (import('module'))
        (call_expression
            function: (import)
            arguments: (arguments (string) @import_source_dynamic)
        ) @dynamic_import
        
        ; Type-only imports (import type { Type } from 'module')
        (import_statement
            import_kind: "type"
            (import_clause
                (named_imports
                    (import_specifier
                        name: (identifier) @type_import
                    )+
                )
            )
            source: (string) @type_import_source
        ) @type_import_stmt

        ; CommonJS require
        (call_expression
            function: (identifier) @require_func (#eq? @require_func "require")
            arguments: (arguments (string) @require_source)
        ) @require_stmt
        
        ; ES Module exports
        (export_statement
            source: (string)? @re_export_source
        ) @export_stmt
        
        ; Named exports (export { name })
        (export_statement
            (export_clause
                (export_specifier
                    name: (identifier) @export_name
                )+
            )
        ) @named_export_stmt
        
        ; Default exports (export default value)
        (export_statement
            default: "default"
            value: (_) @default_export_value
        ) @default_export_stmt
    """,
    "declarations": """
        ; Standard function declarations (possibly with async)
        (function_declaration
            "async"? @async
            name: (identifier) @name
            parameters: (formal_parameters) @params
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
        ) @arrow_function_const
        
        ; Arrow functions assigned to var variables
        (variable_declaration
            (variable_declarator
                name: (identifier) @name
                value: (arrow_function
                    "async"? @arrow_async
                    parameters: [(formal_parameters) (identifier)] @arrow_params
                    body: [(statement_block) (expression)] @arrow_body
                )
            )
        ) @arrow_function_var

        ; Class declarations with extends, implements and decorators
        (class_declaration
            decorator: (decorator
                expression: [(identifier) (call_expression)] @decorator_expr
            )* @class_decorator
            name: (identifier) @name
            extends: (class_heritage
                (extends_clause
                    value: [(identifier) (member_expression)] @extends_class
                )
            )?
            implements: (class_heritage
                (implements_clause
                    value: (type_list)? @implements_interfaces
                )
            )?
            body: (class_body) @body
        ) @class

        ; Class methods (instance methods, static methods, constructors)
        (method_definition
            decorator: (decorator
                expression: [(identifier) (call_expression)] @method_decorator_expr
            )* @method_decorator
            "static"? @static
            "async"? @async_method
            "*"? @generator_method
            name: [(property_identifier) (computed_property_name) (private_property_identifier)] @name
            parameters: (formal_parameters) @method_params
            body: (statement_block) @body
        ) @method
        
        ; Class fields and properties (with initializers)
        (public_field_definition
            decorator: (decorator)* @field_decorator
            "static"? @static_field
            "readonly"? @readonly_field
            name: [(property_identifier) (computed_property_name) (private_property_identifier)] @field_name
            type: (type_annotation)? @field_type
            value: (_)? @field_value
        ) @class_field

        ; Function expressions assigned to variables
        (lexical_declaration
            (variable_declarator
                name: (identifier) @name
                value: [(function) (generator_function)]
            )
        ) @function_expression_const

        ; Function expressions assigned to var variables
        (variable_declaration
            (variable_declarator
                name: (identifier) @name
                value: [(function) (generator_function)]
            )
        ) @function_expression_var
        
        ; Class expressions assigned to variables
        (lexical_declaration
            (variable_declarator
                name: (identifier) @name
                value: (class) @class_expr
            )
        ) @class_expression_const
        
        ; Class expressions assigned to var variables
        (variable_declaration
            (variable_declarator
                name: (identifier) @name
                value: (class) @class_expr
            )
        ) @class_expression_var
        
        ; Object methods and shorthand methods
        (object
            (method_definition
                "async"? @async_obj_method
                "*"? @generator_obj_method
                name: (property_identifier) @obj_method_name
                parameters: (formal_parameters) @obj_method_params
                body: (statement_block) @obj_method_body
            )
        ) @object_with_methods
        
        ; React functional components (indicated by common patterns)
        (lexical_declaration
            (variable_declarator
                name: (identifier) @component_name (#match? @component_name "^[A-Z]")
                value: [(arrow_function) (function)]
            )
        ) @react_component_const
        
        ; React functional components as variables
        (variable_declaration
            (variable_declarator
                name: (identifier) @component_name (#match? @component_name "^[A-Z]")
                value: [(arrow_function) (function)]
            )
        ) @react_component_var
        
        ; React class components
        (class_declaration
            name: (identifier) @component_class_name (#match? @component_class_name "^[A-Z]")
            extends: (class_heritage
                (extends_clause
                    value: [(member_expression) (identifier)] @component_extends
                    (#match? @component_extends "(Component|React\\.Component|PureComponent|React\\.PureComponent)$")
                )
            )
        ) @react_class_component

        ; TypeScript interface declarations
        (interface_declaration
            decorator: (decorator)* @interface_decorator
            name: (type_identifier) @name
            type_parameters: (type_parameters)? @interface_type_params
            extends: (extends_type_clause
                (type_list) @interface_extends
            )?
            body: (object_type) @body
        ) @interface

        ; TypeScript type alias declarations
        (type_alias_declaration
            decorator: (decorator)* @type_decorator
            name: (type_identifier) @name
            type_parameters: (type_parameters)? @type_params
            value: (_) @type_value
        ) @type_alias

        ; TypeScript enum declarations
        (enum_declaration
            decorator: (decorator)* @enum_decorator
            "const"? @const_enum
            name: (identifier) @name
            body: (enum_body
                (enum_assignment
                    name: (property_identifier) @enum_key
                    value: (_)? @enum_value
                )*
            ) @body
        ) @enum
        
        ; TypeScript namespace declarations
        (namespace_declaration
            name: [(identifier) (nested_identifier)] @namespace_name
            body: (statement_block) @namespace_body
        ) @namespace
        
        ; TypeScript module declarations
        (module_declaration
            name: [(string) (identifier)] @module_name
            body: (statement_block) @module_body
        ) @module

        ; TypeScript declare function
        (ambient_declaration
            (function_declaration
                name: (identifier) @name
                parameters: (formal_parameters) @ambient_func_params
                return_type: (type_annotation)? @ambient_func_return
            )
        ) @ambient_function

        ; TypeScript declare class
        (ambient_declaration
            (class_declaration
                name: (identifier) @name
                type_parameters: (type_parameters)? @ambient_class_type_params
                extends: (class_heritage)? @ambient_class_extends
                implements: (class_heritage)? @ambient_class_implements
                body: (class_body)? @ambient_class_body
            )
        ) @ambient_class
        
        ; TypeScript declare variable
        (ambient_declaration
            (variable_declaration
                (variable_declarator
                    name: (identifier) @ambient_var_name
                    type: (type_annotation) @ambient_var_type
                )
            )
        ) @ambient_variable
        
        ; TypeScript declare namespace
        (ambient_declaration
            (namespace_declaration
                name: [(identifier) (nested_identifier)] @ambient_namespace_name
                body: (statement_block) @ambient_namespace_body
            )
        ) @ambient_namespace
        
        ; TypeScript declare module
        (ambient_declaration
            (module_declaration
                name: [(string) (identifier)] @ambient_module_name
                body: (statement_block) @ambient_module_body
            )
        ) @ambient_module
    """,
    "doc_comments": """
        ; JSDoc format block comments
        (comment) @doc_comment (#match? @doc_comment "^\\/\\*\\*")
        
        ; TypeScript triple-slash reference directives
        (comment) @triple_slash_directive (#match? @triple_slash_directive "^\\/\\/\\/")
        
        ; Regular line comments
        (comment) @line_comment (#match? @line_comment "^\\/\\/")
        
        ; Regular block comments
        (comment) @block_comment
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
        return JS_TS_QUERIES

    def _run_queries(
        self, root_node: Node, byte_content: bytes
    ) -> tuple[List[Declaration], List[str]]:
        """Runs JS/TS-specific queries and extracts declarations and imports."""
        queries = self.get_queries()
        declarations = []
        imports: Set[str] = set()
        declaration_map = {}  # node_id -> declaration info
        doc_comment_map = {}  # end_line -> comment_text

        # --- Pass 1: Extract Doc Comments --- #
        try:
            doc_query = self.ts_language.query(queries.get("doc_comments", ""))
            doc_captures = doc_query.captures(root_node)
            for node, _ in doc_captures:
                comment_text = byte_content[node.start_byte : node.end_byte].decode(
                    "utf8", errors="ignore"
                )
                # Store comment keyed by its end line
                doc_comment_map[node.end_point[0]] = self._clean_jsdoc(comment_text)
        except Exception as e:
            logger.warning(f"Failed to execute JS/TS doc_comments query: {e}", exc_info=False)

        # --- Pass 2: Extract Imports and Declarations --- #
        for query_name, query_str in queries.items():
            if query_name == "doc_comments":
                continue

            try:
                query = self.ts_language.query(query_str)
                captures = query.captures(root_node)
                logger.debug(f"Running JS/TS query '{query_name}', found {len(captures)} captures.")

                if query_name == "imports":
                    import_sources = set()
                    for node, capture_name in captures:
                        if (
                            capture_name.startswith("import_source")
                            or capture_name == "require_source"
                        ):
                            # String nodes include quotes, remove them
                            import_path = (
                                byte_content[node.start_byte : node.end_byte]
                                .decode("utf8", errors="ignore")
                                .strip("\"'")
                            )
                            imports.add(import_path)

                elif query_name == "declarations":
                    current_decl_node_id = None
                    for node, capture_name in captures:
                        node_id = node.id

                        # Identify the main declaration node
                        if capture_name in [
                            "function",
                            "generator_function",
                            "class",
                            "method",
                            "variable_function_class",
                            "variable_function_class_var",
                            "interface",
                            "type_alias",
                            "enum",
                            "ambient_function",
                            "ambient_class",
                        ]:
                            current_decl_node_id = node_id
                            if node_id not in declaration_map:
                                # Determine kind based on capture or parent
                                kind = capture_name
                                if capture_name.startswith("variable"):
                                    value_node = next(
                                        (
                                            n
                                            for n, name in captures
                                            if n.id == node_id and name == "value"
                                        ),
                                        None,
                                    )
                                    kind = value_node.type if value_node else "variable"
                                elif capture_name.startswith("ambient"):
                                    kind = f"declare_{capture_name.split('_')[1]}"

                                declaration_map[node_id] = {
                                    "kind": kind,
                                    "node": node,
                                    "name": None,
                                    "start_line": node.start_point[0],
                                    "end_line": node.end_point[0],
                                    "modifiers": set(),  # Modifiers like 'export', 'async', 'static' can be captured if needed
                                    "docstring": "",
                                }
                            # Update end line potentially
                            declaration_map[node_id]["end_line"] = max(
                                declaration_map[node_id]["end_line"], node.end_point[0]
                            )

                        # Capture name
                        elif capture_name == "name" and current_decl_node_id in declaration_map:
                            # Check if name is already set (e.g. function assigned to var)
                            if declaration_map[current_decl_node_id]["name"] is None:
                                name_text = byte_content[node.start_byte : node.end_byte].decode(
                                    "utf8", errors="ignore"
                                )
                                declaration_map[current_decl_node_id]["name"] = name_text

            except Exception as e:
                logger.warning(f"Failed to execute JS/TS query '{query_name}': {e}", exc_info=True)

        # --- Pass 3: Process declarations and associate docstrings --- #
        for decl_info in declaration_map.values():
            if decl_info.get("name"):  # Only add declarations with names
                # Check if a doc comment ended on the line before this declaration started
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
            f"Tree-sitter {self.language} extracted {len(declarations)} declarations and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports

    def _clean_jsdoc(self, comment_text: str) -> str:
        """Cleans a JSDoc block comment, removing delimiters and leading asterisks."""
        lines = comment_text.split("\n")
        cleaned_lines = []
        in_tag = False
        current_tag = ""
        current_tag_content = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Handle first and last lines specifically
            if i == 0 and stripped.startswith("/**"):
                # Remove '/**'
                cleaned = stripped[3:].strip()
            elif i == len(lines) - 1 and stripped.endswith("*/"):
                # Remove '*/'
                cleaned = stripped[:-2].strip()
                if cleaned.startswith("*"):
                    cleaned = cleaned[1:].strip()
            elif stripped.startswith("*"):
                # Remove leading '* '
                cleaned = stripped[1:].strip()
            else:
                cleaned = stripped

            # Process JSDoc tags (@param, @returns, @type, etc.)
            if cleaned and cleaned.startswith("@"):
                # If we were processing a previous tag, add it to the output
                if in_tag and current_tag_content:
                    tag_text = "\n".join(current_tag_content).strip()
                    if tag_text:
                        cleaned_lines.append(f"{current_tag}: {tag_text}")

                # Start a new tag
                parts = cleaned.split(" ", 1)
                current_tag = parts[0]  # The tag itself (@param, @returns, etc)

                # If there's content on the same line as the tag
                if len(parts) > 1 and parts[1].strip():
                    # For @param tags, extract the parameter name
                    if current_tag == "@param" and "{" not in parts[1]:
                        param_parts = parts[1].split(" ", 1)
                        param_name = param_parts[0]
                        param_desc = param_parts[1] if len(param_parts) > 1 else ""
                        current_tag_content = [
                            f"{param_name} - {param_desc}" if param_desc else param_name
                        ]
                    else:
                        current_tag_content = [parts[1].strip()]
                else:
                    current_tag_content = []
                in_tag = True
            elif in_tag:
                # Continue with the current tag
                if cleaned:
                    current_tag_content.append(cleaned)
            elif cleaned:
                # Regular line (not part of a tag)
                cleaned_lines.append(cleaned)

        # Don't forget the last tag if there was one
        if in_tag and current_tag_content:
            tag_text = "\n".join(current_tag_content).strip()
            if tag_text:
                cleaned_lines.append(f"{current_tag}: {tag_text}")

        return "\n".join(cleaned_lines)
