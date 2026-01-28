# file: codeconcat/parser/language_parsers/tree_sitter_cpp_parser.py

import logging
import re

from tree_sitter import Node, Query

# QueryCursor was removed in tree-sitter 0.24.0 - import it if available for backward compatibility
try:
    from tree_sitter import QueryCursor
except ImportError:
    QueryCursor = None  # type: ignore[assignment,misc]

from ...base_types import Declaration
from ..doc_comment_utils import clean_block_comments, clean_line_comments, normalize_whitespace
from ..utils import get_node_location
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Define Tree-sitter queries for C++
# Ref: https://github.com/tree-sitter/tree-sitter-cpp/blob/master/queries/tags.scm
# Note: C++ parsing is complex; these queries capture common constructs but may miss edge cases.
CPP_QUERIES = {
    "imports": """
        ; Include directives
        (preproc_include
            path: [(string_literal) (system_lib_string)] @import_path)
    """,
    "declarations": """
        ; Class definitions
        (class_specifier
            name: (type_identifier) @name
        ) @class

        ; Struct definitions
        (struct_specifier
            name: (type_identifier) @name
        ) @struct

        ; Union definitions
        (union_specifier
            name: (type_identifier) @name
        ) @union

        ; Enum definitions
        (enum_specifier
            name: (type_identifier) @name
        ) @enum

        ; Constructor definitions and declarations
        (function_definition
            declarator: (function_declarator
                declarator: (field_identifier) @name
            )
        ) @constructor (#match? @name "^[A-Z]")

        ; Constructor declarations (inside class body)
        (declaration
            (function_declarator
                (identifier) @name
            )
        ) @constructor (#match? @name "^[A-Z]")

        ; Destructor definitions and declarations
        (function_definition
            declarator: (function_declarator
                declarator: (destructor_name) @name
            )
        ) @destructor

        ; Destructor declarations (inside class body)
        (declaration
            (function_declarator
                (destructor_name) @name
            )
        ) @destructor

        ; Operator overload definitions and declarations
        (function_definition
            declarator: (function_declarator
                declarator: (operator_name) @name
            )
        ) @operator

        ; Operator declarations (inside class body)
        (field_declaration
            (function_declarator
                (operator_name) @name
            )
        ) @operator

        ; Function definitions
        (function_definition
            declarator: (function_declarator
                declarator: (identifier) @name
            )
        ) @function

        ; Function declarations (method prototypes in classes) - not constructors/destructors
        (field_declaration
            (function_declarator
                (field_identifier) @name
                (#not-match? @name "^[A-Z]")  ; Exclude constructors (capitalized names)
                (#not-match? @name "^~")      ; Exclude destructors
            )
        ) @function

        ; Function definitions with field identifier
        (function_definition
            declarator: (function_declarator
                declarator: (field_identifier) @name
            )
        ) @function_field

        ; Function definitions with qualified identifier
        (function_definition
            declarator: (function_declarator
                declarator: (qualified_identifier) @name
            )
        ) @function_qualified

        ; Namespace definitions
        (namespace_definition
            name: (namespace_identifier)? @name
        ) @namespace
    """,
    # Enhanced doc comment capture including Doxygen and regular comments
    "doc_comments": """
        ; Doxygen-style line comments
        (comment) @doxygen_comment (#match? @doxygen_comment "^///|^//!")

        ; Doxygen-style block comments
        (comment) @doxygen_block (#match? @doxygen_block "^/\\\\*\\\\*|^/\\\\*!")

        ; C++ style line comments
        (comment) @cpp_comment (#match? @cpp_comment "^//")

        ; C style block comments
        (comment) @c_comment (#match? @c_comment "^/\\*")
    """,
}


def _clean_cpp_doc_comment(comment_block: list[str]) -> str:
    """Cleans a block of Doxygen comment lines using shared doc_comment_utils.

    Handles both block-style comments (/** */, /*! */) and line-style comments
    (///, //!) consistently with other parsers.
    """
    if not comment_block:
        return ""

    # Detect if this is a block comment or line comment
    first_line = comment_block[0].strip()
    is_block = first_line.startswith(("/**", "/*!"))

    if is_block:
        # Use shared block comment cleaner for /** */ and /*! */
        # Support both standard /** and Doxygen /*!
        start_pattern = r"^/\*[*!]"
        cleaned = clean_block_comments(comment_block, start_pattern=start_pattern)
    else:
        # Use shared line comment cleaner for /// and //!
        # Match both /// and //! styles
        prefix_pattern = r"^///?\s*|^//!\s*"
        cleaned = clean_line_comments(comment_block, prefix_pattern=prefix_pattern)

    # Remove common Doxygen tags (@brief, @author, @param, @return, etc.)
    # These tags are metadata and not part of the actual documentation content
    doxygen_tags = [
        r"@brief\s+",
        r"@details\s+",
        r"@author\s+",
        r"@version\s+",
        r"@date\s+",
        r"@tparam\s+\w+\s+",
        r"@param\s+\w+\s+",
        r"@return\s+",
        r"@returns\s+",
        r"@throws?\s+",
        r"@exception\s+",
        r"@see\s+",
        r"@note\s+",
        r"@warning\s+",
        r"@deprecated\s+",
    ]

    for tag_pattern in doxygen_tags:
        cleaned = re.sub(tag_pattern, "", cleaned, flags=re.IGNORECASE)

    return cleaned.strip()


class TreeSitterCppParser(BaseTreeSitterParser):
    """Tree-sitter based parser for the C/C++ language."""

    def __init__(self):
        """Initializes the C++ Tree-sitter parser."""
        # Use 'cpp' grammar for both C and C++
        super().__init__(language_name="cpp")

    def get_queries(self) -> dict[str, str]:
        """Returns the predefined Tree-sitter queries for C++."""
        return CPP_QUERIES

    def _run_queries(
        self, root_node: Node, byte_content: bytes
    ) -> tuple[list[Declaration], list[str]]:
        """Runs C++-specific queries and extracts declarations and imports."""
        queries = self.get_queries()
        declarations = []
        imports: set[str] = set()
        doc_comment_map = {}  # end_line -> raw comment_text (list of lines)

        # --- Pass 1: Extract Doc Comments --- #
        try:
            # Use modern Query() constructor and QueryCursor
            doc_query = Query(self.ts_language, queries.get("doc_comments", ""))
            doc_captures = self._execute_query_with_cursor(doc_query, root_node)
            last_comment_line = -2
            current_doc_block: list[str] = []

            # doc_captures is a dict: {capture_name: [list of nodes]}
            for _capture_name, nodes in doc_captures.items():
                for node in nodes:
                    comment_text = byte_content[node.start_byte : node.end_byte].decode(
                        "utf8", errors="replace"
                    )
                    current_start_line = node.start_point[0]
                    current_end_line = node.end_point[0]
                    is_block_comment = comment_text.startswith(("/**", "/*!"))

                    if is_block_comment:
                        # Store previous block if it exists and is different
                        if current_doc_block:
                            doc_comment_map[last_comment_line] = current_doc_block
                        # Store the new block comment immediately, keyed by its end line
                        doc_comment_map[current_end_line] = comment_text.splitlines()
                        current_doc_block = []  # Reset tracker
                        last_comment_line = current_end_line  # Update last line seen
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
                    last_comment_line = current_end_line  # Update last line seen

            # Store the last block if it exists
            if current_doc_block:
                doc_comment_map[last_comment_line] = current_doc_block

        except Exception as e:
            logger.warning(f"Failed to execute C++ doc_comments query: {e}", exc_info=True)

        # --- Pass 2: Extract Imports and Declarations --- #
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
                        f"Running C++ query '{query_name}', found {len(captures)} captures."
                    )

                    # captures is a dict: {capture_name: [list of nodes]}
                    for capture_name, nodes in captures.items():
                        if capture_name == "import_path":
                            for node in nodes:
                                # Includes <...> or "..."
                                import_path = (
                                    byte_content[node.start_byte : node.end_byte]
                                    .decode("utf8", errors="replace")
                                    .strip('<>"')
                                )
                                imports.add(import_path)

                elif query_name == "declarations":
                    # Use matches for better structure with declarations
                    matches = self._execute_query_matches(query, root_node)
                    for _match_id, captures_dict in matches:
                        declaration_node = None
                        name_node = None
                        kind = None
                        modifiers: set[str] = set()
                        signature = ""

                        # Check for various declaration types
                        decl_types = [
                            "constructor",
                            "destructor",
                            "operator",
                            "class",
                            "struct",
                            "union",
                            "enum",
                            "function",
                            "namespace",
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

                        # Extract modifiers from the declaration node
                        if declaration_node:
                            modifiers = self._extract_cpp_modifiers(declaration_node, byte_content)

                            # For class members, also look for access specifier in parent context
                            if kind in ["constructor", "destructor", "operator"]:
                                access_modifier = self._find_access_specifier(
                                    declaration_node, byte_content
                                )
                                if access_modifier:
                                    modifiers.add(access_modifier)

                        # Extract signature for functions, constructors, destructors, and operators
                        if declaration_node and kind in [
                            "function",
                            "constructor",
                            "destructor",
                            "operator",
                        ]:
                            signature = self._extract_cpp_signature(declaration_node, byte_content)

                        # Add declaration if we have both node and name
                        if declaration_node and name_node:
                            name_text = byte_content[
                                name_node.start_byte : name_node.end_byte
                            ].decode("utf8", errors="replace")

                            # Check for docstring
                            # For template classes/functions, the doc comment may be several lines before
                            # the actual declaration (before the template<> line)
                            raw_doc_block = []
                            for lookback in range(1, 4):  # Look back up to 3 lines
                                raw_doc_block = doc_comment_map.get(
                                    declaration_node.start_point[0] - lookback, []
                                )
                                if raw_doc_block:
                                    break

                            docstring = (
                                _clean_cpp_doc_comment(raw_doc_block) if raw_doc_block else ""
                            )

                            # Use utility function for accurate line numbers
                            start_line, end_line = get_node_location(declaration_node)

                            declarations.append(
                                Declaration(
                                    kind=kind or "unknown",
                                    name=name_text,
                                    start_line=start_line,
                                    end_line=end_line,
                                    docstring=docstring,
                                    signature=signature,
                                    modifiers=modifiers,
                                )
                            )

            except Exception as e:
                logger.warning(f"Failed to execute C++ query '{query_name}': {e}", exc_info=True)

        # Declaration processing now happens inline during Pass 2

        declarations.sort(key=lambda d: d.start_line)
        sorted_imports = sorted(imports)

        logger.debug(
            f"Tree-sitter C++ extracted {len(declarations)} declarations and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports

    def _find_access_specifier(self, declaration_node: Node, byte_content: bytes) -> str:
        """Find the active access specifier for a class member.

        In C++, access specifiers (public:, private:, protected:) apply to all
        subsequent members until the next access specifier. This method uses an
        optimized approach to find the active access specifier.

        Args:
            declaration_node: Declaration node inside a class
            byte_content: Source code as bytes

        Returns:
            Access specifier string ("public", "private", or "protected"), or empty string
        """
        try:
            # Navigate up to find the field_declaration_list (class body)
            parent = declaration_node.parent
            while parent and parent.type != "field_declaration_list":
                parent = parent.parent

            if not parent:
                return ""

            # Find the index of our declaration in the parent's children
            decl_index = -1
            for i, child in enumerate(parent.children):
                if child == declaration_node:
                    decl_index = i
                    break

            if decl_index == -1:
                return ""

            # OPTIMIZATION: Cache access specifiers to avoid repeated text extraction
            # Traverse backwards more efficiently - check only relevant nodes
            last_access_specifier = ""
            for i in range(decl_index - 1, -1, -1):
                child = parent.children[i]

                # Skip non-relevant nodes quickly
                if child.type not in [
                    "access_specifier",
                    "field_declaration",
                    "method_definition",
                    "function_definition",
                ]:
                    continue

                if child.type == "access_specifier":
                    # Extract the access specifier text (public, private, protected)
                    access_text = (
                        byte_content[child.start_byte : child.end_byte]
                        .decode("utf-8", errors="replace")
                        .strip()
                    )
                    # Remove the trailing colon if present
                    last_access_specifier = access_text.rstrip(":")
                    break  # Found the most recent access specifier

            return last_access_specifier

        except Exception as e:
            logger.debug(f"Failed to find access specifier: {e}")
            return ""

    def _extract_cpp_modifiers(self, declaration_node: Node, byte_content: bytes) -> set[str]:
        """Extract modifiers from C++ declaration node.

        Extracts access specifiers (public, private, protected), storage class specifiers
        (static, extern, inline, virtual, const, etc.) from the declaration.

        Args:
            declaration_node: Declaration node from tree-sitter
            byte_content: Source code as bytes

        Returns:
            Set of modifier strings (e.g., {"public", "static", "const"})
        """
        modifiers: set[str] = set()

        try:
            # OPTIMIZATION: Use direct text extraction for common modifiers
            # instead of recursive traversal for better performance
            node_text = byte_content[
                declaration_node.start_byte : declaration_node.end_byte
            ].decode("utf-8", errors="replace")

            # Common C++ modifiers - check with regex word boundaries for accuracy
            common_modifiers = [
                "static",
                "extern",
                "inline",
                "virtual",
                "const",
                "volatile",
                "override",
                "final",
            ]
            for modifier in common_modifiers:
                # Use word-boundary search to detect modifiers correctly
                # This avoids false positives like 'constexpr' matching 'const'
                # and correctly handles 'const&', 'const;', etc.
                if re.search(rf"\b{re.escape(modifier)}\b", node_text):
                    modifiers.add(modifier)

            # For more complex cases, use targeted node inspection
            # Check for function declarator with trailing qualifiers
            for child in declaration_node.children:
                if child.type == "function_declarator":
                    # Check for trailing const/volatile/noexcept
                    for sub_child in child.children:
                        if sub_child.type == "type_qualifier":
                            qualifier = (
                                byte_content[sub_child.start_byte : sub_child.end_byte]
                                .decode("utf-8", errors="replace")
                                .strip()
                            )
                            if qualifier and qualifier not in [":", ";"]:
                                modifiers.add(qualifier)
                        elif sub_child.type == "noexcept_specifier":
                            modifiers.add("noexcept")

        except Exception as e:
            logger.debug(f"Failed to extract C++ modifiers: {e}")

        return modifiers

    def _extract_cpp_signature(self, func_node: Node, byte_content: bytes) -> str:
        """Extract function signature from function definition node.

        Extracts the complete signature including return type, name, parameters,
        and qualifiers (const, noexcept, etc.).

        Args:
            func_node: Function definition node
            byte_content: Source code as bytes

        Returns:
            Function signature string (e.g., "int calculate(double x, double y) const")
        """
        try:
            # Find the function body to determine signature end
            sig_end_byte = func_node.end_byte

            # Look for the opening brace or semicolon to determine signature end
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
            logger.debug(f"Failed to extract C++ function signature: {e}")
            return ""
