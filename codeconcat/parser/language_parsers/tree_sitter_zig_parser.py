# file: codeconcat/parser/language_parsers/tree_sitter_zig_parser.py

"""
Zig parser using Tree-sitter for accurate AST-based parsing.

This parser provides comprehensive support for Zig language features:
- Comptime evaluation blocks and expressions
- Async/await functions and coroutines
- Error union types and error handling (try/catch)
- Allocator usage patterns
- Test blocks and unit testing
- Inline assembly
- Compile-time reflection
- Generic functions and types
- Error sets and error propagation
"""

import logging
from typing import Any

from tree_sitter import Node

from ...base_types import Declaration, ParseResult
from ..utils import get_node_location
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)


class TreeSitterZigParser(BaseTreeSitterParser):
    """Parser for Zig source code using tree-sitter-zig."""

    def __init__(self):
        """Initialize the Zig parser with tree-sitter-zig language."""
        super().__init__("zig")

        # Track Zig-specific features
        self.comptime_blocks: list[dict[str, Any]] = []
        self.async_functions: list[dict[str, Any]] = []
        self.error_handlers: list[dict[str, Any]] = []
        self.allocator_usage: list[dict[str, Any]] = []
        self.test_blocks: list[dict[str, Any]] = []
        self.builtin_calls: list[dict[str, Any]] = []

    def get_queries(self) -> dict[str, str]:
        """
        Returns a dictionary of Tree-sitter queries for Zig.

        Note: The tree-sitter-zig grammar from tree_sitter_language_pack uses
        non-standard node types (Decl, FnProto, VarDecl, etc.) that don't work
        with standard queries. We use tree traversal instead.

        Returns:
            Empty dict - we use tree traversal for this grammar.
        """
        return {}

    def _load_language(self):
        """Load the Zig language grammar.

        Returns:
            The loaded Zig language object.

        Raises:
            LanguageParserError: If the language cannot be loaded.
        """
        # Try tree_sitter_language_pack first (preferred)
        try:
            from tree_sitter_language_pack import get_language

            return get_language("zig")
        except ImportError:
            pass

        # Try the standalone tree-sitter-zig package
        try:
            import tree_sitter_zig as ts_zig
            from tree_sitter import Language

            # Get the language pointer and create a Language object
            lang_ptr = ts_zig.language()
            return Language(lang_ptr)
        except ImportError as e:
            from ...errors import LanguageParserError

            raise LanguageParserError(
                f"Failed to load Zig language grammar: {e}. "
                "Please install with: pip install tree-sitter-language-pack or tree-sitter-zig"
            ) from e

    def _create_parser(self):
        """Create parser using the standalone tree-sitter-zig grammar.

        Returns:
            Parser instance configured for Zig

        Raises:
            LanguageParserError: If parser creation fails
        """
        try:
            from tree_sitter import Parser

            parser = Parser()
            parser.language = self.ts_language
            return parser
        except Exception as e:
            from ...errors import LanguageParserError

            raise LanguageParserError(f"Failed to create Zig parser: {e}") from e

    def parse(self, content: str, file_path: str = "") -> ParseResult:  # noqa: ARG002
        """
        Parse Zig source code and extract declarations with special features.

        Args:
            content: Zig source code as string
            file_path: Optional path to the file being parsed (unused for Zig)

        Returns:
            ParseResult containing declarations
        """
        # First, use base parser to get tree
        tree = self.parser.parse(bytes(content, "utf8"))

        if not tree or not tree.root_node:
            logger.error("Failed to parse Zig content")
            return ParseResult(declarations=[], imports=[])

        # Reset feature tracking
        self.comptime_blocks = []
        self.async_functions = []
        self.error_handlers = []
        self.allocator_usage = []
        self.test_blocks = []
        self.builtin_calls = []

        # Walk the tree and extract declarations
        declarations = self._walk_tree(tree.root_node, content)

        return ParseResult(declarations=declarations, imports=[])

    def _walk_tree(self, node: Node, source: str) -> list[Declaration]:
        """Walk the AST and extract declarations.

        The tree-sitter-zig grammar from tree_sitter_language_pack uses
        these node types:
        - Decl: General declaration (contains FnProto, VarDecl, etc.)
        - FnProto: Function prototype
        - VarDecl: Variable/const declaration
        - TestDecl: Test block
        - ComptimeDecl: Comptime block
        - IDENTIFIER: Identifier tokens
        - Block: Code blocks
        """
        declarations: list[Declaration] = []

        def visit_node(node: Node, depth: int = 0, is_pub: bool = False):
            # Debug: log node types we encounter
            if depth <= 2:  # Only log top-level nodes
                logger.debug(f"Node type at depth {depth}: {node.type}")

            # Track pub modifier for declarations
            current_is_pub = is_pub
            if node.type == "pub":
                current_is_pub = True

            # Handle general Decl node - look inside for specific declaration types
            if node.type == "Decl":
                # Check children for the actual declaration type
                for child in node.children:
                    if child.type == "FnProto":
                        decl = self._create_function_declaration(node, child, source, is_pub)
                        if decl:
                            declarations.append(decl)
                    elif child.type == "VarDecl":
                        decl = self._create_var_declaration(node, child, source, is_pub)
                        if decl:
                            declarations.append(decl)

            elif node.type == "TestDecl":
                decl = self._create_test_declaration(node, source)
                if decl:
                    declarations.append(decl)
                    self.test_blocks.append(
                        {"name": decl.name, "location": (decl.start_line, decl.end_line)}
                    )

            elif node.type == "ComptimeDecl":
                # Track comptime blocks
                self.comptime_blocks.append(
                    {"type": "comptime_block", "location": get_node_location(node)}
                )

            # Track builtin calls (like @import)
            elif node.type == "BUILTINIDENTIFIER":
                builtin_name = source[node.start_byte : node.end_byte]
                self.builtin_calls.append(
                    {"name": builtin_name, "location": get_node_location(node)}
                )

            # Track async keyword (may appear in ERROR nodes due to grammar limitations)
            elif node.type == "async":
                self.async_functions.append({"type": "async", "location": get_node_location(node)})

            # Track error handling keywords
            elif node.type in ["try", "catch", "defer", "errdefer"]:
                self.error_handlers.append({"type": node.type, "location": get_node_location(node)})

            # Track allocator patterns by looking for "allocator" identifiers
            elif node.type == "IDENTIFIER":
                ident_text = source[node.start_byte : node.end_byte]
                if "allocator" in ident_text.lower():
                    self.allocator_usage.append(
                        {"type": "allocator_ref", "location": get_node_location(node)}
                    )

            # Track inline keyword for comptime iteration
            elif node.type == "inline":
                self.comptime_blocks.append({"type": "inline", "location": get_node_location(node)})

            # Track suspend/resume for async
            elif node.type in ["suspend", "resume"]:
                self.async_functions.append(
                    {"type": node.type, "location": get_node_location(node)}
                )

            # Recurse to children, passing pub modifier state
            for child in node.children:
                visit_node(child, depth + 1, current_is_pub)

        visit_node(node)
        return declarations

    def _create_function_declaration(
        self, decl_node: Node, fn_proto: Node, source: str, is_pub: bool
    ) -> Declaration | None:
        """Create a Declaration object for a function.

        Args:
            decl_node: The Decl parent node (for line numbers)
            fn_proto: The FnProto child node
            source: Source code
            is_pub: Whether the function is public

        Returns:
            Declaration object or None if name not found
        """
        name = None
        params = []
        return_type = None

        for child in fn_proto.children:
            if child.type == "IDENTIFIER" and not name:
                name = source[child.start_byte : child.end_byte]
            elif child.type == "ParamDeclList":
                # Extract parameter info
                for param_child in child.children:
                    if param_child.type == "ParamDecl":
                        param_text = source[param_child.start_byte : param_child.end_byte]
                        params.append(param_text.strip())
            elif child.type == "ErrorUnionExpr" or child.type == "SuffixExpr":
                # Return type
                return_type = source[child.start_byte : child.end_byte].strip()

        if not name:
            return None

        start_line, end_line = get_node_location(decl_node)

        # Build signature
        signature = "pub " if is_pub else ""
        param_str = ", ".join(p for p in params if p and p not in ["(", ")", ","])
        signature += f"fn {name}({param_str})"
        if return_type:
            signature += f" {return_type}"

        # Extract doc comments
        doc_comments = self._extract_doc_comments(decl_node, source)

        return Declaration(
            kind="function",
            name=name,
            signature=signature,
            docstring="\n".join(doc_comments),
            start_line=start_line,
            end_line=end_line,
        )

    def _create_var_declaration(
        self, decl_node: Node, var_decl: Node, source: str, is_pub: bool
    ) -> Declaration | None:
        """Create a Declaration for variable/const or type definitions.

        Args:
            decl_node: The Decl parent node (for line numbers)
            var_decl: The VarDecl child node
            source: Source code
            is_pub: Whether the declaration is public

        Returns:
            Declaration object or None if name not found
        """
        name = None
        var_type = "const"
        is_type_def = False
        type_kind = "variable"

        for child in var_decl.children:
            if child.type == "IDENTIFIER":
                name = source[child.start_byte : child.end_byte]
            elif child.type == "const":
                var_type = "const"
            elif child.type == "var":
                var_type = "var"
            elif child.type == "ErrorUnionExpr":
                # Check if this is a type definition (struct, enum, union)
                for sub in child.children:
                    if sub.type == "SuffixExpr":
                        for inner in sub.children:
                            if inner.type == "ContainerDecl":
                                # Determine container type (check for packed/extern variants)
                                container_text = source[inner.start_byte : inner.end_byte]
                                if "struct" in container_text.split("{")[0]:
                                    is_type_def = True
                                    type_kind = "struct"
                                elif "enum" in container_text.split("{")[0]:
                                    is_type_def = True
                                    type_kind = "enum"
                                elif "union" in container_text.split("{")[0]:
                                    is_type_def = True
                                    type_kind = "union"

        if not name:
            return None

        start_line, end_line = get_node_location(decl_node)

        # Build signature
        signature = "pub " if is_pub else ""
        if is_type_def:
            signature += f"{type_kind} {name}"
        else:
            signature += f"{var_type} {name}"

        # Extract doc comments
        doc_comments = self._extract_doc_comments(decl_node, source)

        return Declaration(
            kind=type_kind if is_type_def else "variable",
            name=name,
            signature=signature,
            docstring="\n".join(doc_comments),
            start_line=start_line,
            end_line=end_line,
        )

    def _create_test_declaration(self, node: Node, source: str) -> Declaration | None:
        """Create a Declaration object for a test block."""
        name = "test"

        # Extract test name if present (in STRINGLITERALSINGLE node)
        for child in node.children:
            if child.type == "STRINGLITERALSINGLE":
                # Get the string content (including quotes)
                test_name = source[child.start_byte : child.end_byte]
                name = f"test {test_name}"
                break

        start_line, end_line = get_node_location(node)

        return Declaration(
            kind="test",
            name=name,
            signature=name,
            docstring="",
            start_line=start_line,
            end_line=end_line,
        )

    def _extract_doc_comments(self, node: Node, source: str) -> list[str]:
        """Extract doc comments for a node."""
        doc_comments: list[str] = []

        # Look for preceding comment nodes
        sibling: Node | None = node.prev_sibling
        while sibling is not None:
            # Check for doc comment or line comment types
            if sibling.type in ["doc_comment", "line_comment", "LINECOMMENT"]:
                comment = source[sibling.start_byte : sibling.end_byte]
                # Check for doc comments (///)
                if comment.startswith("///") or comment.startswith("//!"):
                    doc_comments.insert(0, comment[3:].strip())
                else:
                    break  # Stop at first non-doc comment
            elif sibling.type not in ["pub"]:  # Skip past pub modifier
                break
            sibling = sibling.prev_sibling

        return doc_comments

    def get_language_features(self) -> dict[str, Any]:
        """
        Get Zig-specific language features detected in the parsed code.

        Returns:
            Dictionary containing Zig feature information
        """
        return {
            "comptime_blocks": len(self.comptime_blocks),
            "async_functions": len(self.async_functions),
            "error_handlers": len(self.error_handlers),
            "allocator_usage": len(self.allocator_usage),
            "test_blocks": len(self.test_blocks),
            "builtin_calls": len(self.builtin_calls),
            "has_comptime": len(self.comptime_blocks) > 0,
            "has_async": len(self.async_functions) > 0,
            "has_tests": len(self.test_blocks) > 0,
            "uses_allocators": len(self.allocator_usage) > 0,
        }
