"""Tree-sitter based Swift parser for CodeConCat."""

import logging
from typing import Dict, List, Optional

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

# Tree-sitter queries for Swift
# Note: In tree-sitter-swift, structs/classes/enums/actors all use class_declaration
# We distinguish them by checking for the keyword child node
# ruff: noqa
# fmt: off
SWIFT_QUERIES = {
    "imports": """
        (import_declaration) @import
    """,
    "declarations": """
        ; Class/struct/enum/actor declarations with names
        (class_declaration
            name: (type_identifier) @name
        ) @class

        ; Extension declarations (extends existing types)
        (class_declaration
            (_)* @extension_children
        ) @class

        (protocol_declaration
            name: (type_identifier) @name
        ) @protocol

        (function_declaration
            name: (simple_identifier) @name
        ) @function

        (init_declaration) @initializer

        (property_declaration
            (pattern (simple_identifier) @name)
        ) @property

        (enum_entry
            (simple_identifier) @case_name
        ) @enum_case

        (typealias_declaration
            name: (type_identifier) @name
        ) @typealias

        (associatedtype_declaration
            name: (type_identifier) @name
        ) @associatedtype
    """,
    "doc_comments": """
        (comment) @doc_comment (#match? @doc_comment "^///")
        (multiline_comment) @doc_block (#match? @doc_block "^/[*][*]")
        (comment) @comment
        (multiline_comment) @multiline_comment
    """,
}
# fmt: on
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

    def _run_queries(
        self, root_node: Node, byte_content: bytes
    ) -> tuple[List[Declaration], List[str]]:
        """Runs Swift-specific queries and extracts declarations and imports."""
        declarations = self.extract_declarations(root_node, byte_content)
        imports = self.extract_imports(root_node, byte_content)
        return declarations, imports

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
            captures = self._execute_query_with_cursor(import_query, tree)

            # captures is a dict: {capture_name: [list of nodes]}
            if "import" in captures:
                for node in captures["import"]:
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

    def _extract_doc_comments(self, tree: Node, byte_content: bytes) -> Dict[int, str]:
        """Extract all doc comments once and build a map for efficient lookup.

        This is a performance optimization - instead of running the doc comment query
        for each declaration (O(N * M)), we run it once and build a map (O(N + M)).

        Returns:
            Dict[int, str]: Map of line_number -> doc_comment_text
        """
        doc_comment_map: Dict[int, str] = {}  # line_number -> doc_comment_text
        doc_query = self._get_compiled_query("doc_comments")

        if not doc_query:
            return doc_comment_map

        try:
            captures = self._execute_query_with_cursor(doc_query, tree)

            # Track consecutive doc comment blocks
            current_doc_block: List[str] = []
            last_comment_end_line = -2

            # Collect all comment nodes and deduplicate
            seen_positions = set()
            all_comment_nodes = []

            for capture_name, nodes in captures.items():
                for node in nodes:
                    pos = (node.start_byte, node.end_byte)
                    if pos not in seen_positions:
                        seen_positions.add(pos)
                        all_comment_nodes.append(node)

            # Sort by start line for proper consecutive block detection
            all_comment_nodes.sort(key=lambda n: n.start_point[0])

            # Process comments in line order
            for comment_node in all_comment_nodes:
                comment_text = byte_content[comment_node.start_byte : comment_node.end_byte].decode(
                    "utf-8", errors="replace"
                )

                comment_start_line = comment_node.start_point[0]
                comment_end_line = comment_node.end_point[0]
                is_block = comment_text.startswith("/**")

                if is_block:
                    # Block comments are standalone - store and reset
                    if current_doc_block:
                        doc_comment_map[last_comment_end_line] = "\\n".join(current_doc_block)

                    # Clean and store block comment
                    block_lines = comment_text.splitlines()
                    cleaned = clean_block_comments(block_lines)
                    doc_comment_map[comment_end_line] = cleaned
                    current_doc_block = []
                    last_comment_end_line = comment_end_line
                else:
                    # Line comment (///) - collect consecutive lines
                    if comment_start_line == last_comment_end_line + 1:
                        # Continue current block
                        current_doc_block.append(comment_text)
                    else:
                        # Store previous block if exists
                        if current_doc_block:
                            cleaned = clean_line_comments(
                                current_doc_block, prefix_pattern=r"^///\\s*"
                            )
                            doc_comment_map[last_comment_end_line] = cleaned
                        # Start new block
                        current_doc_block = [comment_text]

                    last_comment_end_line = comment_start_line

            # Store the last block if it exists
            if current_doc_block:
                cleaned = clean_line_comments(current_doc_block, prefix_pattern=r"^///\\s*")
                doc_comment_map[last_comment_end_line] = cleaned

        except Exception as e:
            logger.warning(f"Failed to extract Swift doc comments: {e}", exc_info=True)

        return doc_comment_map

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

        # Extract all doc comments once for efficient lookup (performance optimization)
        doc_comment_map = self._extract_doc_comments(tree, byte_content)

        try:
            captures = self._execute_query_with_cursor(decl_query, tree)

            # captures is a dict: {capture_name: [list of nodes]}
            # Group captures by their parent nodes to avoid duplicates
            processed_nodes = set()

            # Iterate through all capture names and their associated nodes
            for capture_name, nodes in captures.items():
                for node in nodes:
                    # Skip if we've already processed this node
                    if id(node) in processed_nodes:
                        continue

                    # Extract declaration based on type
                    if capture_name == "class":
                        # In tree-sitter-swift, class_declaration is used for class/struct/enum/actor/extension
                        # We need to check the keyword child to determine the actual kind
                        processed_nodes.add(id(node))
                        actual_kind = self._get_class_declaration_kind(node, byte_content)

                        # Extensions use user_type instead of name field
                        name_node = self._find_name_node(node)
                        if not name_node and actual_kind == "extension":
                            # For extensions, find the type_identifier in user_type
                            user_type = node.child_by_field_name("type")
                            if not user_type:
                                # Try finding user_type node manually
                                for child in node.children:
                                    if child.type == "user_type":
                                        user_type = child
                                        break
                            if user_type:
                                # Get type_identifier from user_type
                                for child in user_type.children:
                                    if child.type == "type_identifier":
                                        name_node = child
                                        break

                        if name_node:
                            # Combine modifiers and attributes
                            modifiers = self._extract_modifiers(node, byte_content)
                            attributes = self._extract_attributes(node, byte_content)
                            all_modifiers = modifiers | attributes

                            start_line, end_line = get_node_location(node)
                            declarations.append(
                                Declaration(
                                    kind=actual_kind,
                                    name=byte_content[
                                        name_node.start_byte : name_node.end_byte
                                    ].decode("utf-8", errors="replace"),
                                    start_line=start_line,
                                    end_line=end_line,
                                    docstring=doc_comment_map.get(node.start_point[0] - 1, ""),
                                    modifiers=all_modifiers,
                                )
                            )

                    elif capture_name == "protocol":
                        processed_nodes.add(id(node))
                        name_node = self._find_name_node(node)
                        if name_node:
                            # Combine modifiers and attributes
                            modifiers = self._extract_modifiers(node, byte_content)
                            attributes = self._extract_attributes(node, byte_content)
                            all_modifiers = modifiers | attributes

                            start_line, end_line = get_node_location(node)
                            declarations.append(
                                Declaration(
                                    kind="protocol",
                                    name=byte_content[
                                        name_node.start_byte : name_node.end_byte
                                    ].decode("utf-8", errors="replace"),
                                    start_line=start_line,
                                    end_line=end_line,
                                    docstring=doc_comment_map.get(node.start_point[0] - 1, ""),
                                    modifiers=all_modifiers,
                                )
                            )

                    elif capture_name == "function":
                        processed_nodes.add(id(node))
                        name_node = self._find_name_node(node)
                        if name_node:
                            func_name = byte_content[
                                name_node.start_byte : name_node.end_byte
                            ].decode("utf-8", errors="replace")
                            # Merge function-specific modifiers with attributes
                            modifiers = self._extract_function_modifiers(node, byte_content)
                            attributes = self._extract_attributes(node, byte_content)
                            all_modifiers = modifiers | attributes

                            start_line, end_line = get_node_location(node)
                            declarations.append(
                                Declaration(
                                    kind="function",
                                    name=func_name,
                                    start_line=start_line,
                                    end_line=end_line,
                                    docstring=doc_comment_map.get(node.start_point[0] - 1, ""),
                                    modifiers=all_modifiers,
                                    signature=self._extract_function_signature(node, byte_content),
                                )
                            )

                    elif capture_name == "initializer":
                        processed_nodes.add(id(node))
                        # Combine modifiers and attributes
                        modifiers = self._extract_modifiers(node, byte_content)
                        attributes = self._extract_attributes(node, byte_content)
                        all_modifiers = modifiers | attributes

                        start_line, end_line = get_node_location(node)
                        declarations.append(
                            Declaration(
                                kind="initializer",
                                name="init",
                                start_line=start_line,
                                end_line=end_line,
                                docstring=doc_comment_map.get(node.start_point[0] - 1, ""),
                                modifiers=all_modifiers,
                            )
                        )

                    elif capture_name == "property":
                        processed_nodes.add(id(node))
                        name_node = self._find_property_name(node)
                        if name_node:
                            prop_name = byte_content[
                                name_node.start_byte : name_node.end_byte
                            ].decode("utf-8", errors="replace")
                            # Merge property-specific modifiers with attributes (critical for @State, @Published)
                            modifiers = self._extract_property_modifiers(node, byte_content)
                            attributes = self._extract_attributes(node, byte_content)
                            all_modifiers = modifiers | attributes

                            start_line, end_line = get_node_location(node)
                            declarations.append(
                                Declaration(
                                    kind="property",
                                    name=prop_name,
                                    start_line=start_line,
                                    end_line=end_line,
                                    docstring=doc_comment_map.get(node.start_point[0] - 1, ""),
                                    modifiers=all_modifiers,
                                )
                            )

                    elif capture_name == "typealias":
                        processed_nodes.add(id(node))
                        name_node = self._find_name_node(node)
                        if name_node:
                            start_line, end_line = get_node_location(node)
                            declarations.append(
                                Declaration(
                                    kind="typealias",
                                    name=byte_content[
                                        name_node.start_byte : name_node.end_byte
                                    ].decode("utf-8", errors="replace"),
                                    start_line=start_line,
                                    end_line=end_line,
                                    docstring=doc_comment_map.get(node.start_point[0] - 1, ""),
                                    modifiers=self._extract_attributes(node, byte_content),
                                )
                            )

                    elif capture_name == "enum_case":
                        # Extract individual enum cases from enum_entry nodes
                        # Note: Multiple cases can be on one line (e.g., case a, b, c)
                        processed_nodes.add(id(node))
                        # Collect ALL simple_identifier children (for multi-case declarations)
                        case_name_nodes = []
                        for child in node.children:
                            if child.type == "simple_identifier":
                                case_name_nodes.append(child)

                        # Create a declaration for each case name found
                        for case_name_node in case_name_nodes:
                            case_name = byte_content[
                                case_name_node.start_byte : case_name_node.end_byte
                            ].decode("utf-8", errors="replace")
                            start_line, end_line = get_node_location(node)
                            declarations.append(
                                Declaration(
                                    kind="enum_case",
                                    name=case_name,
                                    start_line=start_line,
                                    end_line=end_line,
                                    docstring=doc_comment_map.get(node.start_point[0] - 1, ""),
                                    modifiers=set(),
                                )
                            )

                    elif capture_name == "associatedtype":
                        processed_nodes.add(id(node))
                        name_node = self._find_name_node(node)
                        if name_node:
                            start_line, end_line = get_node_location(node)
                            declarations.append(
                                Declaration(
                                    kind="associatedtype",
                                    name=byte_content[
                                        name_node.start_byte : name_node.end_byte
                                    ].decode("utf-8", errors="replace"),
                                    start_line=start_line,
                                    end_line=end_line,
                                    docstring=doc_comment_map.get(node.start_point[0] - 1, ""),
                                    modifiers=self._extract_attributes(node, byte_content),
                                )
                            )

        except Exception as e:
            logger.warning(f"Error extracting declarations: {e}")

        return declarations

    def _find_name_node(self, node: Node) -> Optional[Node]:
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

    def _find_property_name(self, node: Node) -> Optional[Node]:
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

    def _find_child_by_type(self, node: Node, child_type: str) -> Optional[Node]:
        """Find a child node by type."""
        for child in node.children:
            if child.type == child_type:
                return child
        return None

    def _get_class_declaration_kind(self, node: Node, byte_content: bytes) -> str:
        """Determine the actual kind of a class_declaration node.

        In tree-sitter-swift, class/struct/enum/actor/extension all use class_declaration.
        We distinguish them by checking for the keyword child node.

        Args:
            node: A class_declaration node
            byte_content: Source code as bytes

        Returns:
            One of: "class", "struct", "enum", "actor", "extension" (defaults to "class")
        """
        # Check for keyword child nodes
        for child in node.children:
            child_type: str = child.type
            if child_type in ["struct", "enum", "actor", "extension"]:
                return child_type
            elif child_type == "class":
                return "class"

        # Default to class if no keyword found
        return "class"

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

    def _extract_attributes(self, node: Node, byte_content: bytes) -> set:
        """Extract Swift attributes (property wrappers, concurrency, etc.) from a declaration.

        Extracts attributes like @State, @Published, @MainActor, @available, etc.
        and returns them as a set to be merged with modifiers.

        Args:
            node: Declaration node that may contain attributes
            byte_content: Source code as bytes

        Returns:
            Set of attribute strings (e.g., {"@State", "@MainActor"})
        """
        attributes = set()

        # Look for attribute child nodes (can be direct children or inside modifiers node)
        for child in node.children:
            if child.type == "attribute":
                # Extract full attribute text including arguments
                attr_text = (
                    byte_content[child.start_byte : child.end_byte]
                    .decode("utf-8", errors="replace")
                    .strip()
                )
                # Ensure it starts with @ (should always be true for attributes)
                if attr_text and not attr_text.startswith("@"):
                    attr_text = f"@{attr_text}"
                attributes.add(attr_text)
            elif child.type == "modifiers":
                # Attributes can also be inside the modifiers node
                for modifier_child in child.children:
                    if modifier_child.type == "attribute":
                        attr_text = (
                            byte_content[modifier_child.start_byte : modifier_child.end_byte]
                            .decode("utf-8", errors="replace")
                            .strip()
                        )
                        if attr_text and not attr_text.startswith("@"):
                            attr_text = f"@{attr_text}"
                        attributes.add(attr_text)

        return attributes

    def _extract_function_modifiers(self, node: Node, byte_content: bytes) -> set:
        """Extract function-specific modifiers."""
        modifiers = self._extract_modifiers(node, byte_content)

        # Check for async/throws/rethrows
        for child in node.children:
            if child.type in ["async", "throws", "rethrows"]:
                modifiers.add(child.type)
            else:
                # Decode once and check
                child_text = byte_content[child.start_byte : child.end_byte].decode(
                    "utf-8", errors="replace"
                )
                if child_text in ["async", "throws", "rethrows"]:
                    modifiers.add(child_text)

        modifiers.add("function")
        return modifiers

    def _extract_property_modifiers(self, node: Node, byte_content: bytes) -> set:
        """Extract property-specific modifiers."""
        modifiers = self._extract_modifiers(node, byte_content)

        # Check for var/let
        for child in node.children:
            if child.type in ["let", "var"]:
                modifiers.add(child.type)
            else:
                # Decode once and check
                child_text = byte_content[child.start_byte : child.end_byte].decode(
                    "utf-8", errors="replace"
                )
                if child_text in ["let", "var"]:
                    modifiers.add(child_text)

        # Check if it's computed (has a computed_property child node)
        for child in node.children:
            if child.type == "computed_property":
                modifiers.add("computed")
                break

        modifiers.add("property")
        return modifiers

    def _extract_operator_modifiers(self, node: Node, byte_content: bytes) -> set:
        """Extract operator-specific modifiers."""
        modifiers = {"operator"}

        # Check for prefix/infix/postfix
        for child in node.children:
            if child.type in ["prefix", "infix", "postfix"]:
                modifiers.add(child.type)
            else:
                # Decode once and check
                child_text = byte_content[child.start_byte : child.end_byte].decode(
                    "utf-8", errors="replace"
                )
                if child_text in ["prefix", "infix", "postfix"]:
                    modifiers.add(child_text)

        return modifiers

    def _extract_function_signature(self, node: Node, byte_content: bytes) -> str:
        """Extract the complete function signature including generics and where clauses.

        Uses body node detection to preserve generic constraints and where clauses.
        Falls back to opening brace detection if body node is not found.

        Args:
            node: Function or initializer declaration node
            byte_content: Source code as bytes

        Returns:
            Function signature string (e.g., "func foo<T>(x: T) -> T where T: Equatable")
        """
        try:
            # Find the function body to determine signature end
            sig_end_byte = node.end_byte
            body_node = node.child_by_field_name("body")

            if body_node:
                # Use body start as signature end (preserves generics and where clauses)
                sig_end_byte = body_node.start_byte
            else:
                # Fallback: look for opening brace manually
                for child in node.children:
                    if child.type in ["code_block", "computed_property"]:
                        sig_end_byte = child.start_byte
                        break

            # Extract signature from start to body
            signature = (
                byte_content[node.start_byte : sig_end_byte]
                .decode("utf-8", errors="replace")
                .strip()
            )

            # Normalize whitespace using shared utility
            signature = normalize_whitespace(signature)

            return signature
        except Exception as e:
            logger.debug(f"Failed to extract Swift function signature: {e}")
            # Fallback to naive extraction
            text = byte_content[node.start_byte : node.end_byte].decode("utf-8", errors="replace")
            if "{" in text:
                return text[: text.index("{")].strip()
            return text.strip()

    def _extract_docstring_for_node(self, node: Node, tree: Node, byte_content: bytes) -> str:
        """Extract documentation comments for a specific node using shared doc_comment_utils.

        Supports both Swift line comments (///) and block comments (/** */).
        Uses shared utilities for consistent doc comment cleaning across all parsers.
        """
        # Look for comments immediately before the node
        node_start_line = node.start_point[0]

        # Get all comments from the file
        doc_query = self._get_compiled_query("doc_comments")
        if not doc_query:
            return ""

        try:
            captures = self._execute_query_with_cursor(doc_query, tree)

            # Collect consecutive doc comment lines that appear before the node
            doc_comment_lines: List[str] = []
            last_comment_end_line = -2  # Track line continuity for /// comments

            # captures is a dict: {capture_name: [list of nodes]}
            for capture_name, nodes in captures.items():
                for comment_node in nodes:
                    comment_start_line = comment_node.start_point[0]
                    comment_end_line = comment_node.end_point[0]

                    # Check if this comment is in the lines immediately before our node
                    # Allow for consecutive /// lines by checking line continuity
                    if comment_end_line < node_start_line:
                        comment_text = byte_content[
                            comment_node.start_byte : comment_node.end_byte
                        ].decode("utf-8", errors="replace")

                        # Handle /// line comments - collect consecutive lines
                        if comment_text.startswith("///"):
                            # Check if this continues a previous doc comment block
                            if comment_start_line == last_comment_end_line + 1:
                                # Continue current block
                                doc_comment_lines.append(comment_text)
                            elif comment_end_line == node_start_line - 1:
                                # Start new block (first line before node)
                                doc_comment_lines = [comment_text]
                            last_comment_end_line = comment_end_line

                        # Handle /** */ block comments
                        elif comment_text.startswith("/**"):
                            # Block comment must be immediately before the node
                            if comment_end_line == node_start_line - 1:
                                doc_comment_lines = comment_text.splitlines()
                                break  # Block comments are single entities

            # Clean the collected doc comments using shared utilities
            if doc_comment_lines:
                first_line = doc_comment_lines[0].strip()
                if first_line.startswith("///"):
                    # Use shared line comment cleaner for /// style
                    return clean_line_comments(doc_comment_lines, prefix_pattern=r"^///\s*")
                elif first_line.startswith("/**"):
                    # Use shared block comment cleaner for /** */ style
                    return clean_block_comments(doc_comment_lines)

        except Exception as e:
            logger.debug(f"Failed to extract Swift documentation comment: {e}")

        return ""
