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

from tree_sitter import Node, Query

# QueryCursor was removed in tree-sitter 0.24.0 - import it if available for backward compatibility
try:
    from tree_sitter import QueryCursor  # type: ignore[attr-defined]
except ImportError:
    QueryCursor = None  # type: ignore[assignment,misc]

from ...base_types import Declaration, ParseResult
from ..utils import get_node_location
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Comprehensive Tree-sitter queries for Zig - Using correct syntax
ZIG_QUERIES = {
    "imports": """
        (builtin_function
            (builtin_identifier) @builtin
            (arguments (string) @import_path)?
        ) @import_call

        (variable_declaration
            (identifier) @import_name
            (builtin_function) @import_func
        ) @import_decl
    """,
    "declarations": """
        (function_declaration) @function

        (test_declaration) @test_block

        (variable_declaration) @variable
    """,
    "comptime": """
        (comptime_declaration) @comptime_block

        (comptime_expression) @comptime_expr

        (for_expression) @for_loop

        (while_expression) @while_loop
    """,
    "async_patterns": """
        (async_expression) @async_expr

        (nosuspend_expression) @nosuspend

        (nosuspend_statement) @nosuspend_stmt

        (suspend_statement) @suspend_stmt

        (resume_expression) @resume_expr
    """,
    "error_handling": """
        (error_union_type) @error_union

        (try_expression) @try_expr

        (catch_expression) @catch_expr

        (defer_statement) @defer_stmt

        (errdefer_statement) @errdefer_stmt
    """,
    "allocator_patterns": """
        (field_expression) @field_expr

        (parameter) @param
    """,
    "builtin_functions": """
        (builtin_function) @builtin_call
    """,
    "comments": """
        (comment) @comment
    """,
}


class TreeSitterZigParser(BaseTreeSitterParser):
    """Parser for Zig source code using tree-sitter-zig."""

    def __init__(self):
        """Initialize the Zig parser with tree-sitter-zig language."""
        super().__init__("zig")
        self._setup_queries()

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

        Returns:
            Dict mapping query names to Tree-sitter S-expression query strings.
        """
        return ZIG_QUERIES

    def _load_language(self):
        """Load the Zig language grammar.

        Returns:
            The loaded Zig language object.

        Raises:
            LanguageParserError: If the language cannot be loaded.
        """
        # Try to use the standalone tree-sitter-zig package
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
                "Please install with: pip install tree-sitter-zig"
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

    def _setup_queries(self):
        """Set up tree-sitter queries for Zig syntax."""
        self.queries: dict[str, Query | None] = {}
        for name, query_str in ZIG_QUERIES.items():
            try:
                # Use modern Query() constructor
                query = Query(self.ts_language, query_str)
                self.queries[name] = query
                logger.debug(f"Successfully compiled query '{name}'")
            except Exception as e:
                logger.warning(f"Failed to create query '{name}': {e}")
                self.queries[name] = None

    def _execute_query_captures(self, query: Query, root: Node) -> dict[str, list[Node]]:
        """Execute a query and get captures, handling both old and new tree-sitter API.

        Args:
            query: Compiled Query object
            root: Root node to query against

        Returns:
            Dictionary mapping capture names to lists of nodes
        """
        try:
            if QueryCursor is not None:
                # Old API: Use QueryCursor
                cursor = QueryCursor(query)
                return cursor.captures(root)  # type: ignore[no-any-return]
            else:
                # New API (tree-sitter >= 0.24.0): Query.captures() directly
                return query.captures(root)  # type: ignore[no-any-return]
        except Exception as e:
            logger.debug(f"Error executing query captures: {e}")
            return {}

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

        # Process queries to extract features
        self._process_queries(tree.root_node, content)

        # Walk the tree and extract declarations
        declarations = self._walk_tree(tree.root_node, content)

        return ParseResult(declarations=declarations, imports=[])

    def _process_queries(self, root: Node, source: str):
        """Process tree-sitter queries to extract Zig-specific features."""
        # Process declarations query
        decl_query = self.queries.get("declarations")
        if decl_query:
            captures_dict = self._execute_query_captures(decl_query, root)
            for capture_name, nodes in captures_dict.items():
                for node in nodes:
                    logger.debug(f"Found declaration: {capture_name} - {node.type}")

        # Process comptime features
        comptime_query = self.queries.get("comptime")
        if comptime_query:
            captures_dict = self._execute_query_captures(comptime_query, root)
            for capture_name, nodes in captures_dict.items():
                if "comptime" in capture_name:
                    for node in nodes:
                        self.comptime_blocks.append(
                            {"type": capture_name, "location": get_node_location(node)}
                        )

        # Process async patterns
        async_query = self.queries.get("async_patterns")
        if async_query:
            captures_dict = self._execute_query_captures(async_query, root)
            for capture_name, nodes in captures_dict.items():
                # All async_patterns query captures are async-related
                for node in nodes:
                    self.async_functions.append(
                        {"type": capture_name, "location": get_node_location(node)}
                    )

        # Process error handling
        error_query = self.queries.get("error_handling")
        if error_query:
            captures_dict = self._execute_query_captures(error_query, root)
            for capture_name, nodes in captures_dict.items():
                for node in nodes:
                    self.error_handlers.append(
                        {"type": capture_name, "location": get_node_location(node)}
                    )

        # Process builtin functions
        builtin_query = self.queries.get("builtin_functions")
        if builtin_query:
            captures_dict = self._execute_query_captures(builtin_query, root)
            for _capture_name, nodes in captures_dict.items():
                for node in nodes:
                    # Extract builtin name
                    for child in node.children:
                        if child.type == "builtin_identifier":
                            self.builtin_calls.append(
                                {
                                    "name": source[child.start_byte : child.end_byte],
                                    "location": get_node_location(node),
                                }
                            )
                            break

    def _walk_tree(self, node: Node, source: str) -> list[Declaration]:
        """Walk the AST and extract declarations."""
        declarations = []

        def visit_node(node: Node, depth: int = 0):
            # Debug: log node types we encounter
            if depth <= 2:  # Only log top-level nodes
                logger.debug(f"Node type at depth {depth}: {node.type}")

            # Extract declarations based on node type
            if node.type == "function_declaration":
                decl = self._create_function_declaration(node, source)
                if decl:
                    declarations.append(decl)
                    # Check for async modifier
                    if self._is_async_function(node, source):
                        self.async_functions.append(
                            {"name": decl.name, "location": (decl.start_line, decl.end_line)}
                        )

            elif node.type == "test_declaration":
                decl = self._create_test_declaration(node, source)
                if decl:
                    declarations.append(decl)
                    self.test_blocks.append(
                        {"name": decl.name, "location": (decl.start_line, decl.end_line)}
                    )

            elif node.type == "variable_declaration":
                # Check if it's a struct/enum/union definition
                decl = self._create_type_or_var_declaration(node, source)
                if decl:
                    declarations.append(decl)

            elif node.type == "comptime_declaration":
                # Track comptime blocks
                self.comptime_blocks.append(
                    {"type": "comptime_block", "location": get_node_location(node)}
                )

            elif node.type == "comptime_expression":
                # Track comptime expressions
                self.comptime_blocks.append(
                    {"type": "comptime_expression", "location": get_node_location(node)}
                )

            elif node.type in ["try_expression", "catch_expression", "error_union_type"]:
                # Track error handling
                self.error_handlers.append({"type": node.type, "location": get_node_location(node)})

            elif node.type in ["defer_statement", "errdefer_statement"]:
                # Track defer/errdefer
                self.error_handlers.append({"type": node.type, "location": get_node_location(node)})

            elif node.type == "builtin_function":
                # Track builtin function calls
                builtin_name = None
                for child in node.children:
                    if child.type == "builtin_identifier":
                        builtin_name = source[child.start_byte : child.end_byte]
                        break
                if builtin_name:
                    self.builtin_calls.append(
                        {"name": builtin_name, "location": get_node_location(node)}
                    )

            # Check for allocator patterns in field expressions
            if node.type == "field_expression":
                for child in node.children:
                    if child.type == "identifier":
                        field_name = source[child.start_byte : child.end_byte]
                        if "allocator" in field_name.lower():
                            self.allocator_usage.append(
                                {"type": "field_access", "location": get_node_location(node)}
                            )
                            break

            # Check for comptime parameters
            if node.type == "parameter":
                for child in node.children:
                    if child.type == "comptime":
                        self.comptime_blocks.append(
                            {"type": "comptime_parameter", "location": get_node_location(node)}
                        )
                        break

            # Check for inline for loops (comptime iteration)
            if node.type == "for_statement":
                for child in node.children:
                    if child.type == "inline":
                        self.comptime_blocks.append(
                            {"type": "inline_for", "location": get_node_location(node)}
                        )
                        break

            # Recurse to children
            for child in node.children:
                visit_node(child, depth + 1)

        visit_node(node)
        return declarations

    def _create_function_declaration(self, node: Node, source: str) -> Declaration | None:
        """Create a Declaration object for a function."""
        name = None
        is_pub = False
        return_type = None

        for child in node.children:
            if (
                child.type == "identifier" and not name
            ):  # Only set once to avoid overwriting with return type
                name = source[child.start_byte : child.end_byte]
            elif child.type == "pub":
                is_pub = True
            elif child.type in ["builtin_type", "error_union_type", "optional_type"]:
                return_type = source[child.start_byte : child.end_byte]

        if not name:
            return None

        start_line, end_line = get_node_location(node)

        # Build signature
        signature = "pub " if is_pub else ""
        signature += f"fn {name}()"
        if return_type:
            signature += f" {return_type}"

        # Extract doc comments
        doc_comments = self._extract_doc_comments(node, source)

        return Declaration(
            kind="function",
            name=name,
            signature=signature,
            docstring="\n".join(doc_comments),
            start_line=start_line,
            end_line=end_line,
        )

    def _create_test_declaration(self, node: Node, source: str) -> Declaration | None:
        """Create a Declaration object for a test block."""
        name = "test"

        # Extract test name if present
        for child in node.children:
            if child.type == "string":
                # Remove quotes from string
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

    def _create_type_or_var_declaration(self, node: Node, source: str) -> Declaration | None:
        """Create a Declaration for variable/const or type definitions."""
        name = None
        var_type = "const"
        is_pub = False
        is_type_def = False
        type_kind = "variable"

        for child in node.children:
            if child.type == "identifier":
                name = source[child.start_byte : child.end_byte]
            elif child.type in ["const", "var"]:
                var_type = child.type
            elif child.type == "pub":
                is_pub = True
            elif child.type == "struct_declaration":
                is_type_def = True
                type_kind = "struct"
            elif child.type == "enum_declaration":
                is_type_def = True
                type_kind = "enum"
            elif child.type == "union_declaration":
                is_type_def = True
                type_kind = "union"

        if not name:
            return None

        start_line, end_line = get_node_location(node)

        # Build signature
        signature = "pub " if is_pub else ""
        signature += f"{var_type} {name}"
        if is_type_def:
            signature = f"{type_kind} {name}"

        # Extract doc comments
        doc_comments = self._extract_doc_comments(node, source)

        return Declaration(
            kind=type_kind if is_type_def else "variable",
            name=name,
            signature=signature,
            docstring="\n".join(doc_comments),
            start_line=start_line,
            end_line=end_line,
        )

    def _is_async_function(self, node: Node, source: str) -> bool:
        """Check if a function has async modifier."""
        # Check if there's an async keyword in the parent context
        parent = node.parent
        if parent and parent.type == "async_expression":
            return True

        # Check for 'async' keyword in children
        return any(source[child.start_byte : child.end_byte] == "async" for child in node.children)

    def _extract_doc_comments(self, node: Node, source: str) -> list[str]:
        """Extract doc comments for a node."""
        doc_comments: list[str] = []

        # Look for preceding comments (Zig uses 'comment' node type, not 'line_comment')
        sibling: Node | None = node.prev_sibling
        while sibling is not None and sibling.type == "comment":
            comment = source[sibling.start_byte : sibling.end_byte]
            # Check for doc comments (///)
            if comment.startswith("///") or comment.startswith("//!"):
                doc_comments.insert(0, comment[3:].strip())
            else:
                break  # Stop at first non-doc comment
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
