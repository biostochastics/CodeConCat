# file: codeconcat/parser/language_parsers/tree_sitter_java_parser.py

import logging
from typing import Dict, List, Set

from tree_sitter import Node

from ...base_types import Declaration
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Define Tree-sitter queries for Java
# Ref: https://github.com/tree-sitter/tree-sitter-java/blob/master/src/node-types.json
# Ref: https://github.com/tree-sitter/tree-sitter-java/blob/master/queries/tags.scm
JAVA_QUERIES = {
    "imports": """
        ; Standard imports
        (import_declaration
            name: (_) @import
            static: "static"? @static_import
        )
        
        ; Wildcard imports (import x.y.*)
        (import_declaration
            name: (scoped_identifier
                scope: (_) @wildcard_import_scope
                name: (asterisk) @wildcard
            )
        ) @wildcard_import
        
        ; Static wildcard imports (import static x.y.*)
        (import_declaration
            static: "static" @static
            name: (scoped_identifier
                scope: (_) @static_wildcard_scope
                name: (asterisk) @static_wildcard
            )
        ) @static_wildcard_import
        
        ; Package declaration (track base package)
        (package_declaration
            name: (_) @package
        )
    """,
    "declarations": """
        ; Class declarations with generic type parameters and annotations
        (class_declaration
            (modifiers
                (annotation)* @class_annotation
                (marker_annotation)* @class_marker_annotation
                (_)* @modifier
            )?
            name: (identifier) @name
            type_parameters: (type_parameters)? @type_params
            superclass: (superclass
                (type_arguments)? @superclass_type_args
                (type_identifier)? @superclass_name
                (generic_type)? @superclass_generic
            )?
            interfaces: (super_interfaces
                (type_list
                    [(type_identifier) (generic_type)]+ @interface
                )
            )?
            body: (class_body) @body
        ) @class
        
        ; Record declarations (Java 14+)
        (record_declaration
            (modifiers
                (annotation)* @record_annotation
                (marker_annotation)* @record_marker_annotation
                (_)* @modifier
            )?
            name: (identifier) @name
            parameters: (formal_parameters
                (formal_parameter
                    name: (identifier) @record_param_name
                    type: (_) @record_param_type
                )*
            ) @record_params
            body: (class_body) @body
        ) @record

        ; Interface declarations with extends and generics
        (interface_declaration
            (modifiers
                (annotation)* @interface_annotation
                (marker_annotation)* @interface_marker_annotation
                (_)* @modifier
            )?
            name: (identifier) @name
            type_parameters: (type_parameters)? @type_params
            interfaces: (extends_interfaces
                (type_list
                    [(type_identifier) (generic_type)]+ @extended_interface
                )
            )?
            body: (interface_body) @body
        ) @interface

        ; Enum declarations with implementations
        (enum_declaration
            (modifiers
                (annotation)* @enum_annotation
                (marker_annotation)* @enum_marker_annotation
                (_)* @modifier
            )?
            name: (identifier) @name
            interfaces: (super_interfaces
                (type_list
                    [(type_identifier) (generic_type)]+ @enum_interface
                )
            )?
            body: (enum_body
                (enum_constant_list
                    (enum_constant
                        name: (identifier) @enum_value
                        arguments: (argument_list)? @enum_value_args
                        body: (class_body)? @enum_value_body
                    )*
                )?
            ) @body
        ) @enum

        ; Method declarations with type parameters, annotations and throws
        (method_declaration
            (modifiers
                (annotation)* @method_annotation
                (marker_annotation)* @method_marker_annotation
                (_)* @modifier
            )?
            type_parameters: (type_parameters)? @method_type_params
            type: (_) @return_type
            name: (identifier) @name
            parameters: (formal_parameters
                (formal_parameter
                    name: (identifier) @param_name
                    type: (_) @param_type
                    (dimensions)? @param_array_dims
                    (variable_declarator_id
                        dimensions: (dimensions)? @var_dims
                    )?
                )*
                (spread_parameter
                    name: (identifier) @vararg_name
                    type: (_) @vararg_type
                )?
            ) @params
            dimensions: (dimensions)? @method_array_dims
            throws: (throws)? @throws
            body: [(block) (";")]? @body
        ) @method

        ; Constructor declarations with type parameters and constructor calls
        (constructor_declaration
            (modifiers
                (annotation)* @constructor_annotation
                (marker_annotation)* @constructor_marker_annotation
                (_)* @modifier
            )?
            type_parameters: (type_parameters)? @constructor_type_params
            name: (identifier) @name
            parameters: (formal_parameters
                (formal_parameter
                    name: (identifier) @param_name
                    type: (_) @param_type
                )*
                (spread_parameter)? @varargs
            ) @params
            throws: (throws)? @throws
            body: (constructor_body
                (explicit_constructor_invocation)? @super_call
                (block) @body_block
            ) @body
        ) @constructor
        
        ; Field declarations with multiple variables
        (field_declaration
            (modifiers
                (annotation)* @field_annotation
                (marker_annotation)* @field_marker_annotation
                (_)* @modifier
            )?
            type: (_) @field_type
            declarator: (variable_declarator
                name: (identifier) @field_name
                value: (_)? @field_initializer
                dimensions: (dimensions)? @field_dims
            )+
        ) @field

        ; Annotation Type Declaration
        (annotation_type_declaration
            (modifiers
                (annotation)* @anno_type_annotation
                (marker_annotation)* @anno_type_marker_annotation
                (_)* @modifier
            )?
            name: (identifier) @name
            body: (annotation_type_body
                (annotation_type_element_declaration
                    name: (identifier) @anno_element_name
                    type: (_) @anno_element_type
                    dimensions: (dimensions)? @anno_element_dims
                    default_value: (_)? @anno_element_default
                )*
            ) @body
        ) @annotation_type
        
        ; Lambda expressions (method and class levels)
        (lambda_expression
            parameters: [(formal_parameters) (identifier)] @lambda_params
            body: [(block) (expression)] @lambda_body
        ) @lambda
        
        ; Method reference expressions (Class::method)
        (method_reference
            object: (_) @method_ref_object
            method: (identifier) @method_ref_name
        ) @method_reference
    """,
    # Query for extracting doc comments
    "doc_comments": """
        ; Javadoc block comments (/**...*/)
        (block_comment) @javadoc_comment (#match? @javadoc_comment "^/\\*\\*")
        
        ; Regular block comments (/*...*/)
        (block_comment) @block_comment
        
        ; Line comments (//...)
        (line_comment) @line_comment
    """,
}


class TreeSitterJavaParser(BaseTreeSitterParser):
    """Tree-sitter based parser for the Java language."""

    def __init__(self):
        """Initializes the Java Tree-sitter parser."""
        super().__init__(language_name="java")

    def get_queries(self) -> Dict[str, str]:
        """Returns the predefined Tree-sitter queries for Java."""
        return JAVA_QUERIES

    def _run_queries(
        self, root_node: Node, byte_content: bytes
    ) -> tuple[List[Declaration], List[str]]:
        """Runs Java-specific queries and extracts declarations and imports."""
        queries = self.get_queries()
        declarations = []
        imports: Set[str] = set()
        declaration_map = {}  # node_id -> declaration info
        doc_comment_map = {}  # end_line -> comment_text

        # --- Pass 1: Extract Doc Comments and map by end line --- #
        # We do this first to easily associate comments with the declaration below them
        try:
            doc_query = self.ts_language.query(queries.get("doc_comments", ""))
            doc_captures = doc_query.captures(root_node)
            for node, _ in doc_captures:
                comment_text = byte_content[node.start_byte : node.end_byte].decode(
                    "utf8", errors="ignore"
                )
                if comment_text.startswith("/**") and comment_text.endswith("*/"):
                    # Store Javadoc comments keyed by their end line
                    doc_comment_map[node.end_point[0]] = self._clean_javadoc(comment_text)
        except Exception as e:
            logger.warning(f"Failed to execute Java doc_comments query: {e}", exc_info=True)

        # --- Pass 2: Extract Imports and Declarations --- #
        for query_name, query_str in queries.items():
            if query_name == "doc_comments":
                continue  # Already processed

            try:
                query = self.ts_language.query(query_str)
                captures = query.captures(root_node)
                logger.debug(f"Running Java query '{query_name}', found {len(captures)} captures.")

                if query_name == "imports":
                    for node, _ in captures:
                        import_text = byte_content[node.start_byte : node.end_byte].decode(
                            "utf8", errors="ignore"
                        )
                        imports.add(import_text)

                elif query_name == "declarations":
                    current_decl_node_id = None
                    for capture in captures:
                        # Handle both 2-tuple and 3-tuple captures from different tree-sitter versions
                        if len(capture) == 2:
                            node, capture_name = capture
                        else:
                            node, capture_name, _ = capture
                        node_id = node.id

                        # Identify the main declaration node
                        if capture_name in [
                            "class",
                            "interface",
                            "enum",
                            "method",
                            "constructor",
                            "annotation",
                        ]:
                            current_decl_node_id = node_id
                            if node_id not in declaration_map:
                                declaration_map[node_id] = {
                                    "kind": capture_name,
                                    "node": node,
                                    "name": None,
                                    "start_line": node.start_point[0],
                                    "end_line": node.end_point[0],
                                    "modifiers": set(),
                                    "docstring": "",  # Initialize docstring
                                }
                            # Update end line potentially
                            declaration_map[node_id]["end_line"] = max(
                                declaration_map[node_id]["end_line"], node.end_point[0]
                            )

                        # Capture name
                        elif capture_name == "name" and current_decl_node_id in declaration_map:
                            name_text = byte_content[node.start_byte : node.end_byte].decode(
                                "utf8", errors="ignore"
                            )
                            declaration_map[current_decl_node_id]["name"] = name_text

                        # Capture modifiers
                        elif capture_name == "modifier" and current_decl_node_id in declaration_map:
                            modifier_text = byte_content[node.start_byte : node.end_byte].decode(
                                "utf8", errors="ignore"
                            )
                            # Filter common modifiers (can be expanded)
                            if modifier_text in [
                                "public",
                                "private",
                                "protected",
                                "static",
                                "final",
                                "abstract",
                                "synchronized",
                                "native",
                                "strictfp",
                            ]:
                                declaration_map[current_decl_node_id]["modifiers"].add(
                                    modifier_text
                                )

            except Exception as e:
                logger.warning(f"Failed to execute Java query '{query_name}': {e}", exc_info=True)

        # --- Pass 3: Process captured declarations and associate docstrings --- #
        for decl_info in declaration_map.values():
            if decl_info.get("name"):  # Ensure name was captured
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

        # Sort declarations by start line
        declarations.sort(key=lambda d: d.start_line)
        # Sort imports alphabetically
        sorted_imports = sorted(list(imports))

        logger.debug(
            f"Tree-sitter Java extracted {len(declarations)} declarations and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports

    def _clean_javadoc(self, comment_text: str) -> str:
        """Cleans a Javadoc block comment, removing delimiters and leading asterisks."""
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

            # Look for Javadoc tags (@param, @return, etc)
            if cleaned and cleaned.startswith("@"):
                # If we were processing a previous tag, add it to the output
                if in_tag and current_tag_content:
                    tag_text = "\n".join(current_tag_content).strip()
                    if tag_text:
                        cleaned_lines.append(f"{current_tag}: {tag_text}")

                # Start a new tag
                parts = cleaned.split(" ", 1)
                current_tag = parts[0]  # The tag itself (@param, @return, etc)
                # If there's content on the same line as the tag
                if len(parts) > 1 and parts[1].strip():
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
