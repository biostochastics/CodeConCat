# file: codeconcat/parser/language_parsers/tree_sitter_csharp_parser.py

import logging
import re
from typing import Dict, List, Set

try:
    import defusedxml.ElementTree as ET
except ImportError:
    # Fallback to standard ET with security warning
    import warnings
    import xml.etree.ElementTree as ET

    warnings.warn(
        "defusedxml not installed - XML parsing may be vulnerable to XXE attacks. "
        "Install with: pip install defusedxml",
        UserWarning,
        stacklevel=2,
    )

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
            type_parameters: (type_parameter_list
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
            (type_parameter_list)? @type_params
            parameter_list: (parameter_list)? @params
            body: (class_body)? @body
        ) @record

        ; Record struct declarations (C# 10+)
        (record_struct_declaration
            (attribute_list)? @attributes
            (modifier)* @modifiers
            name: (identifier) @name
            (type_parameter_list)? @type_params
            parameter_list: (parameter_list)? @params
            body: (struct_body)? @body
        ) @record_struct

        ; Interface declarations with generics
        (interface_declaration
            (attribute_list)? @attributes
            (modifier)* @modifiers
            name: (identifier) @name
            type_parameters: (type_parameter_list
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
            (type_parameter_list)? @type_params
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
            (type_parameter_list)? @type_params
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
            (type_parameter_list)? @type_params
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
                and elem.text.strip()
            ):
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
        doc_comment_map = {}  # end_line -> raw comment_text (list of lines)

        # --- Pass 1: Extract Doc Comments --- #
        try:
            doc_query = self.ts_language.query(queries.get("doc_comments", ""))
            doc_captures = doc_query.captures(root_node)
            last_comment_line = -2
            current_doc_block: List[str] = []

            # doc_captures is a dict: {capture_name: [list of nodes]}
            for _capture_name, nodes in doc_captures.items():
                for node in nodes:
                    # Strip leading '///' and optional space
                    comment_text = byte_content[node.start_byte : node.end_byte].decode(
                        "utf8", errors="replace"
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
                    # captures is a dict of {capture_name: [list of nodes]}
                    # Fixed capture unpacking pattern
                    for capture in captures.items():
                        if len(capture) == 2:
                            capture_name, nodes = capture
                        else:
                            continue
                        if capture_name in [
                            "import_path",
                            "static_import_path",
                            "aliased_namespace",
                            "global_import_path",
                        ]:
                            for node in nodes:
                                import_path = byte_content[node.start_byte : node.end_byte].decode(
                                    "utf8", errors="replace"
                                )
                                imports.add(import_path)

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
                        if "modifiers" in captures_dict:
                            modifier_nodes = captures_dict["modifiers"]
                            for mod_node in modifier_nodes:
                                modifier_text = byte_content[
                                    mod_node.start_byte : mod_node.end_byte
                                ].decode("utf8", errors="replace")
                                modifiers.add(modifier_text)

                        # Add declaration if we have the node (name is optional for some like top_level_statement)
                        if declaration_node:
                            name_text = None
                            if name_node:
                                name_text = byte_content[
                                    name_node.start_byte : name_node.end_byte
                                ].decode("utf8", errors="replace")
                            else:
                                name_text = (
                                    f"<{kind}>"  # Default name for declarations without names
                                )

                            # Check for docstring
                            docstring = doc_comment_map.get(declaration_node.start_point[0] - 1, "")
                            if docstring:
                                docstring = _clean_csharp_doc_comment(docstring)

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
                logger.warning(f"Failed to execute C# query '{query_name}': {e}", exc_info=True)

        # Declaration processing now happens inline

        declarations.sort(key=lambda d: d.start_line)
        sorted_imports = sorted(imports)

        logger.debug(
            f"Tree-sitter C# extracted {len(declarations)} declarations and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports
