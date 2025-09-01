# file: codeconcat/parser/language_parsers/tree_sitter_java_parser.py

import logging
from typing import Dict, List, Set

from tree_sitter import Node

from ...base_types import Declaration
from ..utils import get_node_location
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
        )

        ; Wildcard imports (import x.y.*)
        (import_declaration
            name: (scoped_identifier
                scope: (_) @wildcard_import_scope
                name: (asterisk) @wildcard
            )
        ) @wildcard_import

        ; Static imports
        (import_declaration
            "static"
            name: (_) @static_import
        ) @static_import_stmt

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
                (enum_constant
                    name: (identifier) @enum_value
                    arguments: (argument_list)? @enum_value_args
                    body: (class_body)? @enum_value_body
                )*
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
        (block_comment) @javadoc_comment

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
        doc_comment_map = {}  # end_line -> comment_text

        # --- Pass 1: Extract Doc Comments and map by end line --- #
        # We do this first to easily associate comments with the declaration below them
        try:
            doc_query = self.ts_language.query(queries.get("doc_comments", ""))
            doc_captures = doc_query.captures(root_node)
            # doc_captures is a dict: {capture_name: [list of nodes]}
            for _capture_name, nodes in doc_captures.items():
                for node in nodes:
                    comment_text = byte_content[node.start_byte : node.end_byte].decode(
                        "utf8", errors="replace"
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
                    # captures is a dict of {capture_name: [list of nodes]}
                    # Fixed capture unpacking pattern
                    for capture in captures.items():
                        if len(capture) == 2:
                            capture_name, nodes = capture
                        else:
                            continue
                        if capture_name in ["import_statement", "import_path", "import"]:
                            for node in nodes:
                                import_text = byte_content[node.start_byte : node.end_byte].decode(
                                    "utf8", errors="replace"
                                )
                                imports.add(import_text)

                elif query_name == "declarations":
                    # Use matches for better structure
                    matches = query.matches(root_node)
                    for _match_id, captures_dict in matches:
                        declaration_node = None
                        name_node = None
                        kind = None
                        modifiers = set()

                        # Check for various declaration types
                        decl_types = [
                            "class",
                            "interface",
                            "enum",
                            "method",
                            "constructor",
                            "annotation_type",
                            "record",
                            "field",
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
                        if "modifier" in captures_dict:
                            modifier_nodes = captures_dict["modifier"]
                            for mod_node in modifier_nodes:
                                modifier_text = byte_content[
                                    mod_node.start_byte : mod_node.end_byte
                                ].decode("utf8", errors="replace")
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
                                    modifiers.add(modifier_text)

                        # Add declaration if we have both node and name
                        if declaration_node and name_node:
                            name_text = byte_content[
                                name_node.start_byte : name_node.end_byte
                            ].decode("utf8", errors="replace")

                            # Check for docstring
                            docstring = doc_comment_map.get(declaration_node.start_point[0] - 1, "")

                            # Use utility function for accurate line numbers
                            start_line, end_line = get_node_location(declaration_node)

                            declarations.append(
                                Declaration(
                                    kind=kind or "unknown",
                                    name=name_text,
                                    start_line=start_line,
                                    end_line=end_line,
                                    docstring=docstring,
                                    modifiers=modifiers,
                                )
                            )

            except Exception as e:
                logger.warning(f"Failed to execute Java query '{query_name}': {e}", exc_info=True)

        # Declaration processing now happens inline

        # Sort declarations by start line
        declarations.sort(key=lambda d: d.start_line)
        # Sort imports alphabetically
        sorted_imports = sorted(imports)

        logger.debug(
            f"Tree-sitter Java extracted {len(declarations)} declarations and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports

    def _clean_javadoc(self, comment_text: str) -> str:
        """Cleans a Javadoc block comment, removing delimiters and leading asterisks."""
        lines = comment_text.split("\n")
        cleaned_lines: list[str] = []
        in_tag = False
        current_tag = ""
        current_tag_content: list[str] = []

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
