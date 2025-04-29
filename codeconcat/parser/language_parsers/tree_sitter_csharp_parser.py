# file: codeconcat/parser/language_parsers/tree_sitter_csharp_parser.py

import logging
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Set

from tree_sitter import Node

from ...base_types import Declaration
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Define Tree-sitter queries for C#
# Ref: https://github.com/tree-sitter/tree-sitter-csharp/blob/master/queries/tags.scm
CSHARP_QUERIES = {
    "imports": """
        ; Standard using directives
        (using_directive
            name: (identifier) @import_path)
        (using_directive
            name: (qualified_name) @import_path)
        
        ; Static using directives
        (using_directive
            (using_static_directive)
            name: (qualified_name) @static_import_path)
        
        ; Using aliases
        (using_directive
            (name_equals
                name: (identifier) @alias_name)
            name: (qualified_name) @aliased_namespace)
        
        ; Global using directives (C# 10+)
        (using_directive
            (global_modifier)
            name: [(identifier) (qualified_name)] @global_import_path)
    """,
    "declarations": """
        ; Namespace declarations with nested types capture
        (namespace_declaration
            name: [(identifier) (qualified_name)] @name
            body: (block) @body
        ) @namespace
        
        ; File-scoped namespace (C# 10+)
        (file_scoped_namespace_declaration
            name: [(identifier) (qualified_name)] @name
        ) @file_namespace

        ; Class declarations with access modifiers, base classes, interfaces, and attributes
        (class_declaration
            (attribute_list)? @attributes
            (modifier)* @modifiers 
            name: (identifier) @name
            type_parameter_list: (type_parameter_list
                (type_parameter)+ @type_params
            )?
            base_list: (base_list)? @inheritance
            body: (class_body) @body
        ) @class
        
        ; Record declarations (C# 9.0+)
        (record_declaration
            (attribute_list)? @attributes
            (modifier)* @modifiers
            name: (identifier) @name
            type_parameter_list: (type_parameter_list)? @type_params
            parameter_list: (parameter_list)? @params
            body: (class_body)? @body
        ) @record
        
        ; Record struct declarations (C# 10+)
        (record_struct_declaration
            (attribute_list)? @attributes
            (modifier)* @modifiers
            name: (identifier) @name
            type_parameter_list: (type_parameter_list)? @type_params
            parameter_list: (parameter_list)? @params
            body: (struct_body)? @body
        ) @record_struct

        ; Interface declarations with generics
        (interface_declaration
            (attribute_list)? @attributes
            (modifier)* @modifiers
            name: (identifier) @name
            type_parameter_list: (type_parameter_list
                (type_parameter)+ @type_params
            )?
            base_list: (base_list)? @inheritance
            body: (interface_body) @body
        ) @interface

        ; Struct declarations with modifiers
        (struct_declaration
            (attribute_list)? @attributes
            (modifier)* @modifiers
            name: (identifier) @name
            type_parameter_list: (type_parameter_list)? @type_params
            base_list: (base_list)? @inheritance
            body: (struct_body) @body
        ) @struct

        ; Enum declarations with underlying type
        (enum_declaration
            (attribute_list)? @attributes
            (modifier)* @modifiers
            name: (identifier) @name
            base_list: (base_list)? @underlying_type
            body: (enum_body
                (enum_member_declaration
                    name: (identifier) @enum_value_name
                    (equals_value_clause)? @enum_value
                )* 
            ) @body
        ) @enum

        ; Method declarations with return type, parameters, constraints, and async/virtual modifiers
        (method_declaration
            (attribute_list)? @attributes
            (modifier)* @modifiers
            return_type: (_) @return_type
            name: (identifier) @name
            type_parameter_list: (type_parameter_list)? @type_params
            parameter_list: (parameter_list
                (parameter)* @params
            )
            constraint_clause: (type_parameter_constraints_clause)* @constraints
            body: [(block) (arrow_expression_clause)]? @body
        ) @method

        ; Constructor declarations with initializers and parameters
        (constructor_declaration
            (attribute_list)? @attributes
            (modifier)* @modifiers
            name: (identifier) @name
            parameter_list: (parameter_list
                (parameter)* @params
            )
            constructor_initializer: (constructor_initializer)? @initializer
            body: (block) @body
        ) @constructor
        
        ; Destructor declarations
        (destructor_declaration
            (attribute_list)? @attributes
            name: (identifier) @name
            parameter_list: (parameter_list)? @params
            body: (block) @body
        ) @destructor

        ; Property declarations with auto, expression-bodied and explicit accessors
        (property_declaration
            (attribute_list)? @attributes
            (modifier)* @modifiers
            type: (_) @type
            name: (identifier) @name
            accessor_list: (accessor_list)? @accessors
            (arrow_expression_clause)? @expression_body
            (equals_value_clause)? @initializer
        ) @property
        
        ; Indexer property declaration
        (indexer_declaration
            (attribute_list)? @attributes
            (modifier)* @modifiers
            type: (_) @type
            (this)
            parameter_list: (parameter_list) @params
            accessor_list: (accessor_list)? @accessors
            (arrow_expression_clause)? @expression_body
        ) @indexer

        ; Field declarations with modifiers and initializers
        (field_declaration
            (attribute_list)? @attributes
            (modifier)* @modifiers
            (variable_declaration
                type: (_) @type
                (variable_declarator
                    name: (identifier) @name
                    (equals_value_clause)? @initializer
                ))
        ) @field
        
        ; Constant field declarations
        (field_declaration
            (modifier)* @modifiers (#match? @modifiers "const")
            (variable_declaration
                type: (_) @type
                (variable_declarator
                    name: (identifier) @name
                    (equals_value_clause) @value
                ))
        ) @constant

        ; Delegate declarations with return type and parameters
        (delegate_declaration
            (attribute_list)? @attributes
            (modifier)* @modifiers
            return_type: (_) @return_type
            name: (identifier) @name
            type_parameter_list: (type_parameter_list)? @type_params
            parameter_list: (parameter_list
                (parameter)* @params
            )
            constraint_clause: (type_parameter_constraints_clause)* @constraints
        ) @delegate
        
        ; Event field declarations
        (event_field_declaration
            (attribute_list)? @attributes
            (modifier)* @modifiers
            type: (_) @type
            (variable_declaration
                (variable_declarator
                    name: (identifier) @name
                    (equals_value_clause)? @initializer
                ))
        ) @event
        
        ; Event declaration with accessors
        (event_declaration
            (attribute_list)? @attributes
            (modifier)* @modifiers
            type: (_) @type
            name: (identifier) @name
            accessor_list: (accessor_list) @accessors
        ) @event_accessor
        
        ; Operator declarations
        (operator_declaration
            (attribute_list)? @attributes
            (modifier)* @modifiers
            return_type: (_) @return_type
            name: (operator_value) @name
            parameter_list: (parameter_list) @params
            body: [(block) (arrow_expression_clause)] @body
        ) @operator
        
        ; Conversion operator declarations
        (conversion_operator_declaration
            (attribute_list)? @attributes
            (modifier)* @modifiers
            (implicit_or_explicit_keyword) @conversion_type
            return_type: (_) @return_type
            parameter_list: (parameter_list) @params
            body: [(block) (arrow_expression_clause)] @body
        ) @conversion_operator
        
        ; Top-level statements (C# 9.0+)
        (global_statement) @top_level_statement
    """,
    "doc_comments": """
        ; XML documentation comments
        (comment) @xml_doc (#match? @xml_doc "^///")
        
        ; Regular comments
        (comment) @comment
    """,
}


# Helper to clean XML doc comments
def _clean_csharp_doc_comment(xml_content: str) -> str:
    """Extracts text content from C# XML documentation comments."""
    try:
        # Wrap the content in a root tag to make it valid XML
        # Replace generic type params like `T` with `_T_` to avoid XML parsing errors
        # This is a heuristic and might not cover all cases.
        cleaned_content = re.sub(r"`(\d+)", r"", xml_content)  # Remove arity indicators
        cleaned_content = re.sub(
            r"<([a-zA-Z_][a-zA-Z0-9_]*)>", r"&lt;\1&gt;", cleaned_content
        )  # Escape simple generics
        # Attempt to wrap
        wrapped_xml = f"<root>{cleaned_content}</root>"
        root = ET.fromstring(wrapped_xml)
        # Extract text, joining paragraphs
        text_parts = []
        for elem in root.iter():
            if elem.tag == "param" and "name" in elem.attrib:
                text_parts.append(
                    f"@param {elem.attrib['name']}: {elem.text.strip() if elem.text else ''}"
                )
            elif elem.tag == "typeparam" and "name" in elem.attrib:
                text_parts.append(
                    f"@typeparam {elem.attrib['name']}: {elem.text.strip() if elem.text else ''}"
                )
            elif elem.tag == "returns":
                text_parts.append(f"@returns: {elem.text.strip() if elem.text else ''}")
            elif elem.tag == "summary":
                text_parts.append(elem.text.strip() if elem.text else "")
            elif (
                elem.tag
                not in ["root", "param", "typeparam", "returns", "summary", "see", "exception"]
                and elem.text
            ):
                # Add other text content, but maybe indent or format based on tag?
                # For now, just append stripped text if it exists
                if elem.text.strip():
                    text_parts.append(elem.text.strip())

        # Filter empty parts and join
        return "\n".join(filter(None, text_parts))
    except ET.ParseError as e:
        logger.debug(f"Failed to parse XML doc comment: {e}. Content: {xml_content[:100]}...")
        # Fallback: return the raw content without ///
        return xml_content.strip()
    except Exception as e:
        logger.warning(f"Unexpected error cleaning C# doc comment: {e}")
        return xml_content.strip()


class TreeSitterCSharpParser(BaseTreeSitterParser):
    """Tree-sitter based parser for the C# language."""

    def __init__(self):
        """Initializes the C# Tree-sitter parser."""
        super().__init__(language_name="csharp")

    def get_queries(self) -> Dict[str, str]:
        """Returns the predefined Tree-sitter queries for C#."""
        return CSHARP_QUERIES

    def _run_queries(
        self, root_node: Node, byte_content: bytes
    ) -> tuple[List[Declaration], List[str]]:
        """Runs C#-specific queries and extracts declarations and imports."""
        queries = self.get_queries()
        declarations = []
        imports: Set[str] = set()
        declaration_map = {}  # node_id -> declaration info
        doc_comment_map = {}  # end_line -> raw comment_text (list of lines)

        # --- Pass 1: Extract Doc Comments --- #
        try:
            doc_query = self.ts_language.query(queries.get("doc_comments", ""))
            doc_captures = doc_query.captures(root_node)
            last_comment_line = -2
            current_doc_block: List[str] = []

            for node, _ in doc_captures:
                # Strip leading '///' and optional space
                comment_text = byte_content[node.start_byte : node.end_byte].decode(
                    "utf8", errors="ignore"
                )
                cleaned_line = re.sub(r"^///\s?", "", comment_text).strip()
                current_line = node.start_point[0]

                if current_line == last_comment_line + 1:
                    current_doc_block.append(cleaned_line)
                else:
                    if current_doc_block:
                        doc_comment_map[last_comment_line] = "\n".join(current_doc_block)
                    current_doc_block = [cleaned_line]

                last_comment_line = current_line

            if current_doc_block:
                doc_comment_map[last_comment_line] = "\n".join(current_doc_block)

        except Exception as e:
            logger.warning(f"Failed to execute C# doc_comments query: {e}", exc_info=True)

        # --- Pass 2: Extract Imports and Declarations --- #
        for query_name, query_str in queries.items():
            if query_name == "doc_comments":
                continue

            try:
                query = self.ts_language.query(query_str)
                captures = query.captures(root_node)
                logger.debug(f"Running C# query '{query_name}', found {len(captures)} captures.")

                if query_name == "imports":
                    for node, capture_name in captures:
                        # Capture all import paths regardless of specific capture name
                        import_path = byte_content[node.start_byte : node.end_byte].decode(
                            "utf8", errors="ignore"
                        )
                        # Clean up potential alias definitions for simplicity
                        if "@" in capture_name:  # Heuristic for alias parts
                            continue
                        if capture_name in [
                            "import_path",
                            "static_import_path",
                            "aliased_namespace",
                            "global_import_path",
                        ]:
                            imports.add(import_path)

                elif query_name == "declarations":
                    current_decl_node_id = None
                    current_decl_info = None
                    for node, capture_name in captures:
                        # Identify the main declaration node using the @kind capture
                        if capture_name in [
                            "namespace",
                            "file_namespace",
                            "class",
                            "record",
                            "record_struct",
                            "interface",
                            "struct",
                            "enum",
                            "method",
                            "constructor",
                            "destructor",
                            "property",
                            "indexer",
                            "field",
                            "constant",
                            "delegate",
                            "event",
                            "event_accessor",
                            "operator",
                            "conversion_operator",
                            "top_level_statement",
                        ]:
                            current_decl_node_id = node.id
                            if current_decl_node_id not in declaration_map:
                                declaration_map[current_decl_node_id] = {
                                    "kind": capture_name,
                                    "node": node,
                                    "name": None,
                                    "start_line": node.start_point[0],
                                    "end_line": node.end_point[0],
                                    "modifiers": set(),
                                    "docstring": "",
                                }
                            current_decl_info = declaration_map[current_decl_node_id]
                            # Update end line if needed (e.g., nested captures extend range)
                            current_decl_info["end_line"] = max(
                                current_decl_info["end_line"], node.end_point[0]
                            )

                        # Capture details associated with the current declaration node ID
                        elif current_decl_info:
                            if capture_name == "name":
                                # Only capture the first 'name' encountered for a declaration node
                                if current_decl_info["name"] is None:
                                    name_text = byte_content[
                                        node.start_byte : node.end_byte
                                    ].decode("utf8", errors="ignore")
                                    current_decl_info["name"] = name_text
                            elif capture_name == "modifiers":
                                modifier_text = byte_content[
                                    node.start_byte : node.end_byte
                                ].decode("utf8", errors="ignore")
                                current_decl_info["modifiers"].add(modifier_text)
                            # Add other captures like 'params', 'return_type', etc. if needed later
                            # Update end line based on any sub-capture
                            current_decl_info["end_line"] = max(
                                current_decl_info["end_line"], node.end_point[0]
                            )

            except Exception as e:
                logger.warning(f"Failed to execute C# query '{query_name}': {e}", exc_info=True)

        # --- Pass 3: Process declarations and associate docstrings --- #
        for decl_info in declaration_map.values():
            # Use a default name if none was captured (e.g., top-level statements)
            decl_name = decl_info.get("name") or f"<{decl_info['kind']}>"

            # Check for doc comments ending on the line before the declaration
            raw_docstring = doc_comment_map.get(decl_info["start_line"] - 1, "")
            cleaned_docstring = _clean_csharp_doc_comment(raw_docstring) if raw_docstring else ""

            declarations.append(
                Declaration(
                    kind=decl_info["kind"],
                    name=decl_name,
                    start_line=decl_info["start_line"],
                    end_line=decl_info["end_line"],
                    docstring=cleaned_docstring,
                    modifiers=decl_info["modifiers"],  # Store captured modifiers
                )
            )

        declarations.sort(key=lambda d: d.start_line)
        sorted_imports = sorted(list(imports))

        logger.debug(
            f"Tree-sitter C# extracted {len(declarations)} declarations and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports
