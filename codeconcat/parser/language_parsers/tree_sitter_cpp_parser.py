# file: codeconcat/parser/language_parsers/tree_sitter_cpp_parser.py

import logging
import re
from typing import Dict, List, Optional, Tuple

from tree_sitter import Node

from ...base_types import Declaration
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Define Tree-sitter queries for C++
# Ref: https://github.com/tree-sitter/tree-sitter-cpp/blob/master/queries/tags.scm
# Note: C++ parsing is complex; these queries capture common constructs but may miss edge cases.
CPP_QUERIES = {
    "imports": """
        ; Standard #include directives
        (preproc_include
            path: [(string_literal) (system_lib_string)] @import_path)
        
        ; Include with macro expansion
        (preproc_include 
            path: (identifier) @macro_import)
    """,
    "declarations": """
        ; Namespace definitions with improved body capture
        (namespace_definition
            name: (identifier) @name
            body: (declaration_list)? @body
        ) @namespace
        
        ; Anonymous namespace
        (namespace_definition
            body: (declaration_list)? @body
        ) @anonymous_namespace
        
        ; Nested namespace (C++17)
        (namespace_definition
            name: (nested_namespace_specifier) @nested_name
            body: (declaration_list)? @body
        ) @nested_namespace
        
        ; Template class definitions
        (template_declaration
            parameters: (template_parameter_list) @template_params
            declaration: (class_specifier
                name: (type_identifier) @name
                body: (field_declaration_list)? @body
            ) @template_class_body
        ) @template_class
        
        ; Regular class definitions with access specifiers
        (class_specifier
            name: [(type_identifier) (template_type)] @name
            bases: (base_class_clause)? @inheritance
            body: (field_declaration_list
                (access_specifier)? @access_specifier
            )? @body
        ) @class
        
        ; Template struct definitions
        (template_declaration
            parameters: (template_parameter_list) @template_params
            declaration: (struct_specifier
                name: (type_identifier) @name
                body: (field_declaration_list)? @body
            ) @template_struct_body
        ) @template_struct
        
        ; Regular struct definitions
        (struct_specifier
            name: [(type_identifier) (template_type)] @name
            bases: (base_class_clause)? @inheritance
            body: (field_declaration_list)? @body
        ) @struct
        
        ; Union definitions
        (union_specifier
            name: [(type_identifier) (template_type)] @name
            body: (field_declaration_list)? @body
        ) @union
        
        ; Scoped and unscoped enums with underlying type
        (enum_specifier
            name: (type_identifier) @name
            underlying_type: (enum_base_clause)? @underlying_type
            body: (enumerator_list
                (enumerator
                    name: (identifier) @enum_value_name
                    value: (_)? @enum_value
                )* 
            )? @body
        ) @enum
        
        ; Anonymous enum
        (enum_specifier
            body: (enumerator_list)? @body
        ) @anonymous_enum

        ; Regular function definitions with storage class and type info
        (function_definition
            type: (_)? @return_type
            declarator: (function_declarator
                declarator: (identifier) @name
                parameters: (parameter_list) @params
            )
            body: (compound_statement) @body
        ) @function
        
        ; Regular method definitions (class member functions)
        (function_definition
            type: (_)? @return_type
            declarator: (function_declarator
                declarator: (field_identifier) @name
                parameters: (parameter_list) @params
            )
            body: (compound_statement) @body
        ) @method
        
        ; Constructor definitions
        (function_definition
            declarator: (function_declarator
                declarator: (identifier) @name
                parameters: (parameter_list) @params
            )
            body: (compound_statement) @body
        ) @constructor
        
        ; Destructor definitions
        (function_definition
            declarator: (function_declarator
                declarator: (destructor_name) @name
                parameters: (parameter_list) @params
            )
            body: (compound_statement) @body
        ) @destructor
        
        ; Operator overload definitions
        (function_definition
            type: (_)? @return_type
            declarator: (function_declarator
                declarator: (operator_name) @name
                parameters: (parameter_list) @params
            )
            body: (compound_statement) @body
        ) @operator_overload
        
        ; Template function definitions
        (template_declaration
            parameters: (template_parameter_list) @template_params
            declaration: (function_definition
                type: (_)? @return_type
                declarator: (function_declarator
                    declarator: [(identifier) (field_identifier)] @name
                    parameters: (parameter_list) @params
                )
                body: (compound_statement) @body
            ) @template_func_body
        ) @template_function
        
        ; Function declaration (prototype) with parameters and modifiers
        (declaration
            type: (_) @type
            declarator: (function_declarator
                declarator: [(identifier) (field_identifier)] @name
                parameters: (parameter_list) @params
            )
            default_value: (_)? @default_value
        ) @function_declaration
        
        ; Operator overload declaration (prototype)
        (declaration
            type: (_) @type
            declarator: (function_declarator
                declarator: (operator_name) @name
                parameters: (parameter_list) @params
            )
        ) @operator_declaration
        
        ; Constructor/destructor declaration (prototype)
        (declaration
            declarator: (function_declarator
                declarator: [(identifier) (destructor_name)] @name
                parameters: (parameter_list) @params
            )
        ) @constructor_declaration

        ; Global variable declarations with initializers and modifiers
        (declaration
           storage_class: (_)? @storage_class
           type: (_) @type
           declarator: (init_declarator 
               declarator: (identifier) @name
               value: (_)? @init_value
           )
        ) @variable
        
        ; Static constexpr variables
        (declaration
           storage_class: (_)? @storage_class (#match? @storage_class "static|constexpr")
           type: (_) @type
           declarator: (init_declarator declarator: (identifier) @name)
        ) @static_variable
        
        ; Class member variables with access specifiers and default values
        (field_declaration
           type: (_) @type
           declarator: (field_identifier) @name
           default_value: (_)? @default_value
        ) @field
        
        ; Using declarations (importing symbols from namespaces)
        (using_declaration
             declarator: [(identifier) (qualified_identifier)] @name
        ) @using_symbol
        
        ; Using directives (entire namespace imports)
        (using_directive
             namespace: [(identifier) (qualified_identifier)] @namespace_name
        ) @using_namespace
        
        ; Namespace aliases
        (namespace_alias_definition
             name: (identifier) @name
             value: [(identifier) (qualified_identifier)] @aliased_namespace
        ) @namespace_alias
        
        ; Typedefs with more complete type information
        (type_definition
            type: (_) @original_type
            declarator: (type_identifier) @name
        ) @typedef
        
        ; Template alias (using X = Y<T>)
        (alias_declaration
            name: (type_identifier) @name
            type: (_) @aliased_type
        ) @type_alias
        
        ; Friend declarations in classes
        (friend_declaration
            type: (_)? @friend_type
            declarator: (_)? @friend_name
        ) @friend
    """,
    # Enhanced doc comment capture including Doxygen and regular comments
    "doc_comments": """
        ; Doxygen-style line comments
        (comment) @doxygen_comment (#match? @doxygen_comment "^///|^//\\!")
        
        ; Doxygen-style block comments
        (comment) @doxygen_block (#match? @doxygen_block "^/\\*\\*|^/\\*\\!")
        
        ; C++ style line comments
        (comment) @cpp_comment (#match? @cpp_comment "^//")
        
        ; C style block comments
        (comment) @c_comment (#match? @c_comment "^/\\*")
    """
}

# Patterns to clean Doxygen comments
DOC_COMMENT_START_PATTERN = re.compile(r"^(/\*\*<?|/\*!<?|///<?|//!?)\s?")
# Additional patterns for matching Doxygen comment formats
DOC_COMMENT_LINE_PREFIX_PATTERN = re.compile(r"^\s*\*\s?")
DOC_COMMENT_END_PATTERN = re.compile(r"\s*\*/$")

def _clean_cpp_doc_comment(comment_block: List[str]) -> str:
    """Cleans a block of Doxygen comment lines."""
    cleaned_lines = []
    is_block = comment_block[0].startswith(("/**", "/*!")) if comment_block else False

    for i, line in enumerate(comment_block):
        original_line = line # Keep original for block end check
        if i == 0:
            line = DOC_COMMENT_START_PATTERN.sub('', line)
        if is_block:
             line = DOC_COMMENT_LINE_PREFIX_PATTERN.sub('', line)
        # Check original line for block comment end marker
        if is_block and original_line.endswith("*/"):
            line = DOC_COMMENT_END_PATTERN.sub('', line)

        cleaned_lines.append(line.strip())
    # Join lines, filtering empty ones that might result from cleaning
    return "\n".join(filter(None, cleaned_lines))

class TreeSitterCppParser(BaseTreeSitterParser):
    """Tree-sitter based parser for the C/C++ language."""

    def __init__(self):
        """Initializes the C++ Tree-sitter parser."""
        # Use 'cpp' grammar for both C and C++
        super().__init__(language_name="cpp")

    def get_queries(self) -> Dict[str, str]:
        """Returns the predefined Tree-sitter queries for C++."""
        return CPP_QUERIES

    def _run_queries(self, root_node: Node, byte_content: bytes) -> tuple[List[Declaration], List[str]]:
        """Runs C++-specific queries and extracts declarations and imports."""
        queries = self.get_queries()
        declarations = []
        imports: List[str] = []
        declaration_map = {} # node_id -> declaration info
        doc_comment_map = {} # end_line -> raw comment_text (list of lines)
        node_parent_map = {child.id: root_node.id for child in root_node.children} # Precompute parent IDs
        for child in root_node.children:
            for grandchild in child.children:
                 node_parent_map[grandchild.id] = child.id
                 # Add more levels if needed, or make recursive


        # --- Pass 1: Extract Doc Comments --- #
        try:
            doc_query = self.ts_language.query(queries.get("doc_comments", ""))
            doc_captures = doc_query.captures(root_node)
            last_comment_line = -2
            current_doc_block: List[str] = []

            for node, _ in doc_captures:
                comment_text = byte_content[node.start_byte:node.end_byte].decode("utf8", errors="ignore")
                current_start_line = node.start_point[0]
                current_end_line = node.end_point[0]
                is_block_comment = comment_text.startswith(("/**", "/*!"))

                if is_block_comment:
                     # Store previous block if it exists and is different
                     if current_doc_block:
                         doc_comment_map[last_comment_line] = current_doc_block
                     # Store the new block comment immediately, keyed by its end line
                     doc_comment_map[current_end_line] = comment_text.splitlines()
                     current_doc_block = [] # Reset tracker
                     last_comment_line = current_end_line # Update last line seen
                elif comment_text.startswith(("///", "//!")):
                     # If it continues a line comment block
                     if current_start_line == last_comment_line + 1:
                         current_doc_block.append(comment_text)
                     else:
                         # Store previous block if any
                         if current_doc_block:
                            doc_comment_map[last_comment_line] = current_doc_block
                         # Start new line comment block
                         current_doc_block = [comment_text]
                     last_comment_line = current_start_line
                else:
                     # Non-doc comment encountered, store pending block
                     if current_doc_block:
                         doc_comment_map[last_comment_line] = current_doc_block
                     current_doc_block = []
                     last_comment_line = current_end_line # Update last line seen

            # Store the last block if it exists
            if current_doc_block:
                doc_comment_map[last_comment_line] = current_doc_block

        except Exception as e:
            logger.warning(f"Failed to execute C++ doc_comments query: {e}", exc_info=False)

        # --- Pass 2: Extract Imports and Declarations --- #
        for query_name, query_str in queries.items():
            if query_name == "doc_comments": continue

            try:
                query = self.ts_language.query(query_str)
                captures = query.captures(root_node)
                logger.debug(f"Running C++ query '{query_name}', found {len(captures)} captures.")

                if query_name == "imports":
                    for node, capture_name in captures:
                        if capture_name == "import_path":
                            # Includes <...> or "..."
                            import_path = byte_content[node.start_byte:node.end_byte].decode("utf8", errors="ignore").strip('<>"')
                            if import_path not in imports:  # Maintain uniqueness behavior
                                imports.append(import_path)

                elif query_name == "declarations":
                    # Map captures to their main declaration node ID
                    node_capture_map = {}
                    for node, capture_name in captures:
                        # Heuristic: Find the ancestor node that corresponds to the @declaration capture name
                        # This is tricky because captures can be nested.
                        current_node = node
                        decl_node = None
                        while current_node:
                             # Use the capture name on the node itself for primary identification
                             node_type_capture = next((name for n, name in captures if n.id == current_node.id), None)
                             if node_type_capture in ["namespace", "class", "struct", "union", "enum", "function", "function_declaration", "variable", "field", "using_symbol", "namespace_alias", "typedef"]:
                                 decl_node = current_node
                                 break
                             parent_id = node_parent_map.get(current_node.id)
                             if parent_id is None: break
                             # Need a way to get parent node object from ID - tree-sitter doesn't provide this directly!
                             # This part is flawed without parent node access.
                             # Let's simplify: use the node where the @kind capture occurred.
                             decl_node = node # Default to the captured node if kind matched
                             break # Stop search
                        # Fallback if loop didn't find ancestor
                        if decl_node is None and capture_name in ["namespace", "class", "struct", "union", "enum", "function", "function_declaration", "variable", "field", "using_symbol", "namespace_alias", "typedef"]:
                           decl_node = node

                        if decl_node:
                            decl_id = decl_node.id
                            if decl_id not in node_capture_map:
                                node_capture_map[decl_id] = {'node': decl_node, 'captures': []}
                            node_capture_map[decl_id]['captures'].append((node, capture_name))


                    # Process the grouped captures
                    for decl_id, data in node_capture_map.items():
                        decl_node = data['node']
                        node_captures = data['captures']

                        # Determine kind from the main node's capture name if possible
                        kind = next((name for n, name in node_captures if n.id == decl_id and name in ["namespace", "class", "struct", "union", "enum", "function", "function_declaration", "variable", "field", "using_symbol", "namespace_alias", "typedef"]), None)
                        if not kind: continue # Skip if we couldn't determine kind

                        # Extract name
                        name_node = next((n for n, name in node_captures if name == "name"), None)
                        name_text = byte_content[name_node.start_byte:name_node.end_byte].decode("utf8", errors="ignore") if name_node else "<unknown>"

                        # Handle potential template arguments in names (basic strip)
                        name_text = re.sub(r'<.*>', '', name_text)

                        # Function declarations might not have a body
                        start_line = decl_node.start_point[0]
                        end_line = decl_node.end_point[0]

                        if decl_id not in declaration_map:
                             declaration_map[decl_id] = {
                                'kind': kind,
                                'node': decl_node,
                                'name': name_text,
                                'start_line': start_line,
                                'end_line': end_line,
                                'modifiers': [], # TODO: Extract modifiers (using list instead of set for Python 3.12+ compatibility)
                                'docstring': ""
                            }
                        else:
                            # Update end line if needed (e.g., subsequent capture extends range)
                            declaration_map[decl_id]['end_line'] = max(declaration_map[decl_id]['end_line'], end_line)
                            # Ensure name is captured if missed initially
                            if declaration_map[decl_id]['name'] == "<unknown>" and name_text != "<unknown>":
                                 declaration_map[decl_id]['name'] = name_text

            except Exception as e:
                logger.warning(f"Failed to execute C++ query '{query_name}': {e}", exc_info=True)

        # --- Pass 3: Process declarations and associate docstrings --- #
        for decl_info in declaration_map.values():
            if decl_info.get('name') and decl_info['name'] != "<unknown>":
                # Check for doc comments ending on the line before the declaration
                raw_doc_block = doc_comment_map.get(decl_info['start_line'] - 1, [])
                cleaned_docstring = _clean_cpp_doc_comment(raw_doc_block) if raw_doc_block else ""

                declarations.append(Declaration(
                    kind=decl_info['kind'],
                    name=decl_info['name'],
                    start_line=decl_info['start_line'],
                    end_line=decl_info['end_line'],
                    docstring=cleaned_docstring,
                    modifiers=decl_info['modifiers']
                ))

        declarations.sort(key=lambda d: d.start_line)
        sorted_imports = sorted(list(imports))

        logger.debug(f"Tree-sitter C++ extracted {len(declarations)} declarations and {len(sorted_imports)} imports.")
        return declarations, sorted_imports
