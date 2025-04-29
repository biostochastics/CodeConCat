# file: codeconcat/parser/language_parsers/tree_sitter_php_parser.py

import logging
import re
from typing import Dict, List, Set

from tree_sitter import Node

from ...base_types import Declaration
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Define Tree-sitter queries for PHP
# Ref: https://github.com/tree-sitter/tree-sitter-php/blob/master/queries/tags.scm
PHP_QUERIES = {
    "imports": """
        ; Basic use statement (class import)
        (use_declaration
          (namespace_use_clause path: (name) @import_path)
        ) @use_statement
        
        ; Function imports with 'use function'
        (use_declaration
          kind: "function"
          (namespace_use_clause path: (name) @function_import_path)
        ) @function_use_statement
        
        ; Constant imports with 'use const'
        (use_declaration
          kind: "const"
          (namespace_use_clause path: (name) @const_import_path)
        ) @const_use_statement

        ; Group use statements - namespace part
        (namespace_use_declaration
            (namespace_name) @group_import_prefix
        ) @use_statement_group
        
        ; Group use statements - individual items
        (namespace_use_declaration
            (namespace_use_group
                (namespace_use_clause
                    path: (name) @group_import_item
                )
            )
        )
        
        ; Function use statements with aliases
        (use_declaration
          (namespace_use_clause 
            path: (name) @import_path
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
            name: (name)? @name
        ) @namespace

        ; Class declarations with modifiers, extends and implements
        (class_declaration
            (attribute_list
                (attribute
                    name: (name) @class_attr_name
                    arguments: (arguments)? @class_attr_args
                )
            )* @class_attributes
            modifier: ["abstract" "final"]? @class_modifier
            name: (name) @name
            extends: (base_clause
                (name) @extends_name
            )?
            implements: (class_interface_clause
                (name_list)? @implements_list
            )?
            body: (declaration_list) @body
        ) @class
        
        ; Anonymous class declarations
        (anonymous_class_declaration
            (attribute_list)? @anon_class_attr
            extends: (base_clause
                (name) @anon_extends_name
            )?
            implements: (class_interface_clause
                (name_list)? @anon_implements_list
            )?
        ) @anonymous_class

        ; Interface declarations
        (interface_declaration
            (attribute_list
                (attribute
                    name: (name) @interface_attr_name
                    arguments: (arguments)? @interface_attr_args
                )
            )* @interface_attributes
            name: (name) @name
            extends: (base_clause
                (name_list) @interface_extends
            )?
            body: (declaration_list) @body
        ) @interface

        ; Trait declarations
        (trait_declaration
            (attribute_list
                (attribute
                    name: (name) @trait_attr_name
                    arguments: (arguments)? @trait_attr_args
                )
            )* @trait_attributes
            name: (name) @name
            body: (declaration_list) @body
        ) @trait

        ; Function definitions with return types, parameters and modifiers
        (function_definition
            (attribute_list
                (attribute
                    name: (name) @func_attr_name
                    arguments: (arguments)? @func_attr_args
                )
            )* @function_attributes
            name: (name) @name
            parameters: (formal_parameters
                (simple_parameter
                    type: (_)? @param_type
                    name: (variable_name) @param_name
                    default_value: (_)? @param_default
                )* @params
            )
            return_type: (return_type)? @return_type
            body: (compound_statement) @body
        ) @function
        
        ; Method declarations with modifiers, return types and parameters
        (method_declaration
            (attribute_list
                (attribute
                    name: (name) @method_attr_name
                    arguments: (arguments)? @method_attr_args
                )
            )* @method_attributes
            modifiers: [
                "public" "protected" "private"
                "static" "abstract" "final"
            ]* @modifiers
            name: (name) @name
            parameters: (formal_parameters
                (simple_parameter
                    type: (_)? @param_type
                    name: (variable_name) @param_name
                    default_value: (_)? @param_default
                )* @params
            )
            return_type: (return_type)? @return_type
            body: (compound_statement)? @body
        ) @method
        
        ; Constructor method with property promotion (PHP 8+)
        (method_declaration
            modifiers: [
                "public" "protected" "private"
                "final"
            ]* @constructor_modifiers
            name: (name) @constructor_name (#eq? @constructor_name "__construct")
            parameters: (formal_parameters
                (property_promotion_parameter
                    modifiers: [
                        "public" "protected" "private"
                    ]* @prop_promotion_modifiers
                    type: (_)? @prop_promotion_type
                    name: (variable_name) @prop_promotion_name
                    default_value: (_)? @prop_promotion_default
                )* @promoted_params
            )
            body: (compound_statement) @constructor_body
        ) @constructor_with_promotion

        ; Constants (global scope)
        (const_declaration
            (const_element 
                name: (name) @name
                value: (_) @const_value
            )
        ) @constant

        ; Class Constants with visibility modifiers
        (class_const_declaration
            modifiers: [
                "public" "protected" "private"
                "final"
            ]* @const_modifiers
            (const_element 
                name: (name) @name
                value: (_) @class_const_value
            )
        ) @class_constant

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
        (comment) @doc_comment (#match? @doc_comment "^/\\*\\*")
        
        ; Single line annotations (less common but used in some codebases)
        (comment) @line_annotation (#match? @line_annotation "^//\\s*@")
        
        ; File-level docblock
        (program . (comment) @file_doc_comment (#match? @file_doc_comment "^/\\*\\*"))
    """,
}

# Patterns to clean PHPDoc comments
PHP_DOC_COMMENT_START_PATTERN = re.compile(r"^/\*\*\s?")
PHP_DOC_COMMENT_LINE_PREFIX_PATTERN = re.compile(r"^\s*\*\s?")
PHP_DOC_COMMENT_END_PATTERN = re.compile(r"\s*\*/$")


def _clean_php_doc_comment(comment_block: List[str]) -> str:
    """Cleans a block of PHPDoc comment lines."""
    cleaned_lines = []
    for i, line in enumerate(comment_block):
        original_line = line  # Keep original for block end check
        if i == 0:
            line = PHP_DOC_COMMENT_START_PATTERN.sub("", line)
        line = PHP_DOC_COMMENT_LINE_PREFIX_PATTERN.sub("", line)
        # Check original line for block comment end marker
        if original_line.strip().endswith("*/"):
            line = PHP_DOC_COMMENT_END_PATTERN.sub("", line)

        cleaned_lines.append(line.strip())
    # Join lines, filtering empty ones
    return "\n".join(filter(None, cleaned_lines))


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
        declaration_map = {}  # node_id -> declaration info
        doc_comment_map = {}  # end_line -> raw comment_text (list of lines)

        # Keep track of modifiers for declarations
        current_namespace = ""

        # --- Pass 1: Extract Doc Comments --- #
        try:
            doc_query = self.ts_language.query(queries.get("doc_comments", ""))
            doc_captures = doc_query.captures(root_node)

            for node, _ in doc_captures:
                comment_text = byte_content[node.start_byte : node.end_byte].decode(
                    "utf8", errors="ignore"
                )
                # PHPDoc comments are always block comments /** ... */
                if comment_text.startswith("/**"):
                    doc_comment_map[node.end_point[0]] = comment_text.splitlines()

        except Exception as e:
            logger.warning(f"Failed to execute PHP doc_comments query: {e}", exc_info=False)

        # --- Pass 2: Extract Imports and Declarations --- #
        current_namespace = ""
        for query_name, query_str in queries.items():
            if query_name == "doc_comments":
                continue

            try:
                query = self.ts_language.query(query_str)
                captures = query.captures(root_node)
                logger.debug(f"Running PHP query '{query_name}', found {len(captures)} captures.")

                if query_name == "imports":
                    for node, capture_name in captures:
                        if capture_name == "import_path":
                            import_path = (
                                byte_content[node.start_byte : node.end_byte]
                                .decode("utf8", errors="ignore")
                                .strip("'\"")
                            )
                            # Handle group use statements (multiple paths possible)
                            if node.parent and node.parent.type == "namespace_use_clause":
                                # Part of a group use statement like 'use N\{C1, C2}'
                                # Find the common prefix
                                group_node = node.parent
                                while group_node and group_node.type != "namespace_use_declaration":
                                    group_node = group_node.parent
                                if group_node:
                                    prefix_node = next(
                                        (
                                            n
                                            for n, name in query.captures(group_node)
                                            if name == "import_path"
                                        ),
                                        None,
                                    )
                                    if prefix_node:
                                        prefix = byte_content[
                                            prefix_node.start_byte : prefix_node.end_byte
                                        ].decode("utf8", errors="ignore")
                                        import_path = f"{prefix}\\{import_path}"

                            imports.add(import_path)

                elif query_name == "declarations":
                    # Group captures by the main declaration node ID
                    node_capture_map = {}
                    for node, capture_name in captures:
                        # Heuristic: Use the node associated with the @declaration_kind capture
                        decl_node = node  # Start with the captured node
                        # Find the ancestor that represents the whole declaration
                        # (e.g., class_declaration, function_definition)
                        while decl_node.parent and decl_node.type not in [
                            "namespace_definition",
                            "class_declaration",
                            "interface_declaration",
                            "trait_declaration",
                            "function_definition",
                            "const_declaration",
                            "class_const_declaration",
                            "property_declaration",
                            "program",
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
                            "namespace",
                            "class",
                            "interface",
                            "trait",
                            "function",
                            "constant",
                            "class_constant",
                            "property",
                        ]:
                            # Prioritize explicit kind capture if available
                            node_capture_map[decl_id]["kind"] = capture_name

                    # Process grouped captures
                    for decl_id, data in node_capture_map.items():
                        decl_node = data["node"]
                        node_captures = data["captures"]
                        kind = data["kind"] or decl_node.type  # Fallback to node type

                        # Normalize kinds from the Tree-sitter node types
                        if kind == "class_declaration":
                            kind = "class"
                        elif kind == "anonymous_class_declaration":
                            kind = "anonymous_class"
                        elif kind == "interface_declaration":
                            kind = "interface"
                        elif kind == "trait_declaration":
                            kind = "trait"
                        elif kind == "function_definition":
                            kind = "function"
                        elif kind == "method_declaration":
                            kind = "method"
                        elif kind == "constructor_with_promotion":
                            kind = "constructor"
                        elif kind == "const_declaration":
                            kind = "constant"
                        elif kind == "class_const_declaration":
                            kind = "class_constant"
                        elif kind == "property_declaration":
                            kind = "property"
                        elif kind == "namespace_definition":
                            kind = "namespace"
                        elif kind == "enum_declaration":
                            kind = "enum"
                        elif kind == "global_declaration":
                            kind = "global_variable"
                        # Keep existing kind if already mapped

                        if kind not in [
                            "namespace",
                            "class",
                            "anonymous_class",
                            "interface",
                            "trait",
                            "function",
                            "method",
                            "constructor",
                            "constant",
                            "class_constant",
                            "property",
                            "enum",
                            "global_variable",
                        ]:
                            continue  # Skip nodes we don't classify as declarations

                        # Extract name from relevant captured nodes
                        name_node = next((n for n, name in node_captures if name == "name"), None)
                        name_text = (
                            byte_content[name_node.start_byte : name_node.end_byte].decode(
                                "utf8", errors="ignore"
                            )
                            if name_node
                            else "<anonymous>"
                        )
                        name_text = name_text.lstrip("$")  # Remove leading $ from property names

                        start_line = decl_node.start_point[0]
                        end_line = decl_node.end_point[0]

                        # Extract modifiers into a set
                        modifiers = set()
                        # Look for common modifier captures
                        modifier_nodes = [
                            (n, cname)
                            for n, cname in node_captures
                            if cname
                            in [
                                "modifiers",
                                "class_modifier",
                                "property_modifiers",
                                "const_modifiers",
                                "constructor_modifiers",
                                "prop_promotion_modifiers",
                            ]
                        ]

                        for mod_node, _ in modifier_nodes:
                            mod_text = byte_content[mod_node.start_byte : mod_node.end_byte].decode(
                                "utf8", errors="ignore"
                            )
                            modifiers.add(mod_text)

                        # Check for attributes (PHP 8+)
                        attr_nodes = [
                            (n, cname)
                            for n, cname in node_captures
                            if cname
                            in [
                                "class_attributes",
                                "method_attributes",
                                "function_attributes",
                                "interface_attributes",
                                "trait_attributes",
                                "property_attributes",
                                "enum_attributes",
                            ]
                        ]

                        has_attributes = len(attr_nodes) > 0
                        if has_attributes:
                            modifiers.add("attribute")

                        # Look for return types
                        return_type_node = next(
                            (n for n, cname in node_captures if cname == "return_type"), None
                        )
                        has_return_type = return_type_node is not None
                        if has_return_type:
                            modifiers.add("typed")

                        # Update current namespace
                        if kind == "namespace":
                            current_namespace = name_text if name_text != "<anonymous>" else ""
                            # Create a declaration for the namespace
                            declaration_map[decl_id] = {
                                "kind": kind,
                                "name": name_text,
                                "start_line": start_line,
                                "end_line": end_line,
                                "modifiers": modifiers,
                                "docstring": "",
                            }
                            continue  # Don't add other specific properties for namespaces

                        # Prepend namespace if exists
                        full_name = (
                            f"{current_namespace}\\{name_text}"
                            if current_namespace and name_text != "<anonymous>"
                            else name_text
                        )

                        if decl_id not in declaration_map:
                            declaration_map[decl_id] = {
                                "kind": kind,
                                "name": full_name,
                                "start_line": start_line,
                                "end_line": end_line,
                                "modifiers": modifiers,
                                "docstring": "",
                            }
                        else:
                            # Update end line, modifiers, or potentially missed name
                            declaration_map[decl_id]["end_line"] = max(
                                declaration_map[decl_id]["end_line"], end_line
                            )
                            declaration_map[decl_id]["modifiers"].update(modifiers)
                            if (
                                declaration_map[decl_id]["name"] == "<anonymous>"
                                and full_name != "<anonymous>"
                            ):
                                declaration_map[decl_id]["name"] = full_name

            except Exception as e:
                logger.warning(f"Failed to execute PHP query '{query_name}': {e}", exc_info=True)

        # --- Pass 3: Process declarations and associate docstrings --- #
        for decl_info in declaration_map.values():
            if decl_info.get("name") and decl_info["name"] != "<anonymous>":
                # Check for doc comments ending on the line before the declaration
                raw_doc_block = doc_comment_map.get(decl_info["start_line"] - 1, [])
                cleaned_docstring = _clean_php_doc_comment(raw_doc_block) if raw_doc_block else ""

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
            f"Tree-sitter PHP extracted {len(declarations)} declarations and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports
