"""Tree-sitter based Swift parser for CodeConCat."""

import logging
from typing import Dict, List

from tree_sitter import Node

from ...base_types import Declaration
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Tree-sitter queries for Swift
SWIFT_QUERIES = {
    "imports": """
        ; Import declarations
        (import_declaration) @import
    """,
    "declarations": """
        ; Class declarations
        (class_declaration
            name: (type_identifier) @name
        ) @class

        ; Structure declarations
        (struct_declaration
            name: (type_identifier) @name
        ) @struct

        ; Enum declarations
        (enum_declaration
            name: (type_identifier) @name
        ) @enum

        ; Protocol declarations
        (protocol_declaration
            name: (type_identifier) @name
        ) @protocol

        ; Actor declarations (Swift 5.5+)
        (actor_declaration
            name: (type_identifier) @name
        ) @actor

        ; Extension declarations
        (extension_declaration
            name: (type_identifier) @name
        ) @extension

        ; Function declarations
        (function_declaration
            name: (simple_identifier) @name
        ) @function

        ; Method declarations
        (function_declaration
            name: (simple_identifier) @name
        ) @method

        ; Initializer declarations
        (initializer_declaration) @initializer

        ; Deinitializer declarations
        (deinitializer_declaration) @deinitializer

        ; Property declarations
        (property_declaration
            name: (pattern) @name
        ) @property

        ; Subscript declarations
        (subscript_declaration) @subscript

        ; Operator declarations
        (operator_declaration
            name: (custom_operator) @name
        ) @operator

        ; Typealias declarations
        (typealias_declaration
            name: (type_identifier) @name
        ) @typealias

        ; Associated type declarations
        (associatedtype_declaration
            name: (type_identifier) @name
        ) @associatedtype

        ; Global variable/constant declarations
        (property_declaration
            name: (pattern (simple_identifier) @name)
        ) @global_var
    """,
    "doc_comments": """
        ; Documentation comments (///)
        (comment) @doc_comment (#match? @doc_comment "^///")

        ; Block documentation comments (/** */)
        (multiline_comment) @doc_block (#match? @doc_block "^/\\\\*\\\\*")

        ; Regular comments
        (comment) @comment
        (multiline_comment) @multiline_comment
    """,
}


class TreeSitterSwiftParser(BaseTreeSitterParser):
    """Tree-sitter based parser for Swift code."""

    def __init__(self):
        """Initialize the Swift parser."""
        super().__init__("swift")
        self.queries_dict = SWIFT_QUERIES
        self._compiled_queries = {}

    def get_queries(self) -> Dict[str, str]:
        """Get the query strings for Swift parsing.

        Returns:
            Dictionary of query names to query strings
        """
        return SWIFT_QUERIES

    def _get_compiled_query(self, query_name: str):
        """Get a compiled query from cache or compile it.

        This method uses the parent class's caching mechanism.
        """
        query_str = self.queries_dict.get(query_name)
        if not query_str:
            return None

        # Use parent class's compile method with caching
        cache_key = (self.language_name, query_name, query_str)
        return self._compile_query_cached(cache_key)

    def extract_imports(self, tree: Node, byte_content: bytes) -> List[str]:
        """Extract import statements from Swift code.

        Args:
            tree: The tree-sitter parse tree

        Returns:
            List of imported module names
        """
        imports: List[str] = []
        import_query = self._get_compiled_query("imports")

        if not import_query:
            return imports

        try:
            captures = import_query.captures(tree.root_node)

            for node, capture_name in captures:
                if capture_name == "import":
                    # Extract the full import statement text
                    import_text = byte_content[node.start_byte : node.end_byte].decode(
                        "utf-8", errors="replace"
                    )
                    # Remove 'import' keyword and extract module name
                    if import_text.startswith("import "):
                        module_name = import_text[7:].strip()
                        # Handle import attributes like @testable
                        if module_name.startswith("@"):
                            parts = module_name.split(None, 1)
                            if len(parts) > 1:
                                module_name = parts[1]
                        imports.append(module_name)

        except Exception as e:
            logger.warning(f"Error extracting imports: {e}")

        return imports

    def extract_declarations(self, tree: Node, byte_content: bytes) -> List[Declaration]:
        """Extract declarations from Swift code.

        Args:
            tree: The tree-sitter parse tree

        Returns:
            List of Declaration objects
        """
        declarations: List[Declaration] = []
        decl_query = self._get_compiled_query("declarations")

        if not decl_query:
            return declarations

        try:
            captures = decl_query.captures(tree.root_node)

            # Group captures by their parent nodes to avoid duplicates
            processed_nodes = set()

            for node, capture_name in captures:
                # Skip if we've already processed this node
                if id(node) in processed_nodes:
                    continue

                # Extract declaration based on type
                if capture_name in ["class", "struct", "enum", "protocol", "actor", "extension"]:
                    processed_nodes.add(id(node))
                    name_node = self._find_name_node(node)
                    if name_node:
                        declarations.append(
                            Declaration(
                                kind=capture_name,
                                name=byte_content[name_node.start_byte : name_node.end_byte].decode(
                                    "utf-8", errors="replace"
                                ),
                                start_line=node.start_point[0] + 1,
                                end_line=node.end_point[0] + 1,
                                docstring=self._extract_docstring_for_node(
                                    node, tree, byte_content
                                ),
                                modifiers=self._extract_modifiers(node, byte_content),
                            )
                        )

                elif capture_name == "function":
                    processed_nodes.add(id(node))
                    name_node = self._find_name_node(node)
                    if name_node:
                        func_name = byte_content[name_node.start_byte : name_node.end_byte].decode(
                            "utf-8", errors="replace"
                        )
                        # Check if it's async/throws
                        modifiers = self._extract_function_modifiers(node, byte_content)
                        declarations.append(
                            Declaration(
                                kind="function",
                                name=func_name,
                                start_line=node.start_point[0] + 1,
                                end_line=node.end_point[0] + 1,
                                docstring=self._extract_docstring_for_node(
                                    node, tree, byte_content
                                ),
                                modifiers=modifiers,
                                signature=self._extract_function_signature(node, byte_content),
                            )
                        )

                elif capture_name == "initializer":
                    processed_nodes.add(id(node))
                    declarations.append(
                        Declaration(
                            kind="initializer",
                            name="init",
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            docstring=self._extract_docstring_for_node(node, tree, byte_content),
                            modifiers=self._extract_modifiers(node, byte_content),
                        )
                    )

                elif capture_name == "deinitializer":
                    processed_nodes.add(id(node))
                    declarations.append(
                        Declaration(
                            kind="deinitializer",
                            name="deinit",
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            docstring=self._extract_docstring_for_node(node, tree, byte_content),
                            modifiers=set(),
                        )
                    )

                elif capture_name == "property":
                    processed_nodes.add(id(node))
                    name_node = self._find_property_name(node)
                    if name_node:
                        prop_name = byte_content[name_node.start_byte : name_node.end_byte].decode(
                            "utf-8", errors="replace"
                        )
                        modifiers = self._extract_property_modifiers(node, byte_content)
                        declarations.append(
                            Declaration(
                                kind="property",
                                name=prop_name,
                                start_line=node.start_point[0] + 1,
                                end_line=node.end_point[0] + 1,
                                docstring=self._extract_docstring_for_node(
                                    node, tree, byte_content
                                ),
                                modifiers=modifiers,
                            )
                        )

                elif capture_name == "subscript":
                    processed_nodes.add(id(node))
                    declarations.append(
                        Declaration(
                            kind="subscript",
                            name="subscript",
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                            docstring=self._extract_docstring_for_node(node, tree, byte_content),
                            modifiers=self._extract_modifiers(node, byte_content),
                        )
                    )

                elif capture_name == "operator":
                    processed_nodes.add(id(node))
                    name_node = self._find_child_by_type(node, "custom_operator")
                    if name_node:
                        declarations.append(
                            Declaration(
                                kind="operator",
                                name=byte_content[name_node.start_byte : name_node.end_byte].decode(
                                    "utf-8", errors="replace"
                                ),
                                start_line=node.start_point[0] + 1,
                                end_line=node.end_point[0] + 1,
                                docstring="",
                                modifiers=self._extract_operator_modifiers(node, byte_content),
                            )
                        )

                elif capture_name == "typealias":
                    processed_nodes.add(id(node))
                    name_node = self._find_name_node(node)
                    if name_node:
                        declarations.append(
                            Declaration(
                                kind="typealias",
                                name=byte_content[name_node.start_byte : name_node.end_byte].decode(
                                    "utf-8", errors="replace"
                                ),
                                start_line=node.start_point[0] + 1,
                                end_line=node.end_point[0] + 1,
                                docstring=self._extract_docstring_for_node(
                                    node, tree, byte_content
                                ),
                                modifiers=set(),
                            )
                        )

        except Exception as e:
            logger.warning(f"Error extracting declarations: {e}")

        return declarations

    def _find_name_node(self, node: Node) -> Node:
        """Find the name identifier node within a declaration."""
        # Check if node has a 'name' field first (most efficient)
        name_field = node.child_by_field_name("name")
        if name_field:
            return name_field

        # Otherwise look for type_identifier or simple_identifier
        for child in node.children:
            if child.type in ["type_identifier", "simple_identifier"]:
                return child
        return None

    def _find_property_name(self, node: Node) -> Node:
        """Find the property name within a property declaration."""
        # Look for pattern containing the identifier
        pattern = node.child_by_field_name("name")
        if pattern:
            # Navigate through pattern to find the actual identifier
            for child in pattern.children:
                if child.type == "simple_identifier":
                    return child
            # If pattern is directly the identifier
            if pattern.type == "simple_identifier":
                return pattern
        return None

    def _find_child_by_type(self, node: Node, child_type: str) -> Node:
        """Find a child node by type."""
        for child in node.children:
            if child.type == child_type:
                return child
        return None

    def _extract_modifiers(self, node: Node, byte_content: bytes) -> set:
        """Extract access modifiers and other modifiers from a declaration."""
        modifiers = set()

        # Cache for decoded modifier text to avoid repeated decoding
        modifier_types_to_decode = {
            "visibility_modifier",
            "mutation_modifier",
            "property_modifier",
            "inheritance_modifier",
        }

        # Simple modifiers that can be added directly by type
        simple_modifiers = {
            "public",
            "private",
            "internal",
            "fileprivate",
            "open",
            "static",
            "class",
            "final",
            "override",
        }

        # Look for modifier nodes
        for child in node.children:
            if child.type == "modifiers":
                for modifier in child.children:
                    if modifier.type in modifier_types_to_decode:
                        # Decode only once per modifier
                        modifier_text = byte_content[
                            modifier.start_byte : modifier.end_byte
                        ].decode("utf-8", errors="replace")
                        modifiers.add(modifier_text)
            elif child.type in simple_modifiers:
                modifiers.add(child.type)

        return modifiers

    def _extract_function_modifiers(self, node: Node, byte_content: bytes) -> set:
        """Extract function-specific modifiers."""
        modifiers = self._extract_modifiers(node, byte_content)

        # Check for async/throws/rethrows
        for child in node.children:
            if child.type in ["async", "throws", "rethrows"]:
                modifiers.add(child.type)
            elif byte_content[child.start_byte : child.end_byte].decode(
                "utf-8", errors="replace"
            ) in ["async", "throws", "rethrows"]:
                modifiers.add(
                    byte_content[child.start_byte : child.end_byte].decode(
                        "utf-8", errors="replace"
                    )
                )

        modifiers.add("function")
        return modifiers

    def _extract_property_modifiers(self, node: Node, byte_content: bytes) -> set:
        """Extract property-specific modifiers."""
        modifiers = self._extract_modifiers(node, byte_content)

        # Check for var/let
        for child in node.children:
            if child.type in ["let", "var"]:
                modifiers.add(child.type)
            elif byte_content[child.start_byte : child.end_byte].decode(
                "utf-8", errors="replace"
            ) in ["let", "var"]:
                modifiers.add(
                    byte_content[child.start_byte : child.end_byte].decode(
                        "utf-8", errors="replace"
                    )
                )

        # Check if it's computed (has a body)
        if node.child_by_field_name("body"):
            modifiers.add("computed")

        modifiers.add("property")
        return modifiers

    def _extract_operator_modifiers(self, node: Node, byte_content: bytes) -> set:
        """Extract operator-specific modifiers."""
        modifiers = {"operator"}

        # Check for prefix/infix/postfix
        for child in node.children:
            if child.type in ["prefix", "infix", "postfix"]:
                modifiers.add(child.type)
            elif byte_content[child.start_byte : child.end_byte].decode(
                "utf-8", errors="replace"
            ) in ["prefix", "infix", "postfix"]:
                modifiers.add(
                    byte_content[child.start_byte : child.end_byte].decode(
                        "utf-8", errors="replace"
                    )
                )

        return modifiers

    def _extract_function_signature(self, node: Node, byte_content: bytes) -> str:
        """Extract the function signature."""
        # Get the text from function start to the opening brace
        text = byte_content[node.start_byte : node.end_byte].decode("utf-8", errors="replace")
        if "{" in text:
            return text[: text.index("{")].strip()
        return text.strip()

    def _extract_docstring_for_node(self, node: Node, tree: Node, byte_content: bytes) -> str:
        """Extract documentation comments for a specific node."""
        doc_lines: List[str] = []

        # Look for comments immediately before the node
        line_before = node.start_point[0]

        # Get all comments from the file
        doc_query = self._get_compiled_query("doc_comments")
        if doc_query:
            captures = doc_query.captures(tree.root_node)

            for comment_node, _capture_name in captures:
                comment_line = comment_node.end_point[0]

                # Check if this comment is right before our node
                if comment_line == line_before - 1 or comment_line == line_before:
                    comment_text = byte_content[
                        comment_node.start_byte : comment_node.end_byte
                    ].decode("utf-8", errors="replace")

                    # Process documentation comments
                    if comment_text.startswith("///"):
                        doc_lines.append(comment_text[3:].strip())
                    elif comment_text.startswith("/**") and comment_text.endswith("*/"):
                        # Extract multi-line doc comment content
                        content = comment_text[3:-2].strip()
                        for line in content.split("\n"):
                            line = line.strip()
                            if line.startswith("*"):
                                line = line[1:].strip()
                            if line:
                                doc_lines.append(line)

        return "\n".join(doc_lines)
