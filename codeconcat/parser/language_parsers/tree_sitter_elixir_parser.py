# file: codeconcat/parser/language_parsers/tree_sitter_elixir_parser.py

"""
Enhanced Elixir parser using tree-sitter.

Extracts declarations, imports, and Elixir-specific constructs using the
official elixir-lang/tree-sitter-elixir grammar.

Supports Elixir 1.12+ with features including:
- GenServer and LiveView callback detection
- Pattern matching in function clauses and case statements
- Pipe operator (|>) flow analysis
- Macro definitions and usage (defmacro, quote, unquote)
- Supervisor tree structures
- Protocol implementations
- Module attributes and behaviors
- Phoenix framework patterns
"""

import logging

from tree_sitter import Node, Query

from ...base_types import Declaration, ParseResult
from ..doc_comment_utils import normalize_whitespace

# QueryCursor was removed in tree-sitter 0.24.0 - import it if available for backward compatibility
try:
    from tree_sitter import QueryCursor  # type: ignore[attr-defined]
except ImportError:
    QueryCursor = None  # type: ignore[assignment,misc]

from ..utils import get_node_location
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Tree-sitter queries for Elixir syntax
# Conforms to BaseTreeSitterParser expectations:
# - Use @module/@function (not @module_def/@function_def)
# - Use @name for the name capture
# - Use @import_statement for imports
ELIXIR_QUERIES = {
    "declarations": """
        ; Module definitions
        (call
            (identifier) @def_keyword
            (#eq? @def_keyword "defmodule")
            (arguments
                (alias) @name
            )
        ) @module

        ; Function definitions with arguments (def, defp) - e.g., def hello(name)
        (call
            (identifier) @def_keyword
            (#match? @def_keyword "^(def|defp)$")
            (arguments
                (call
                    (identifier) @name
                )
            )
        ) @function

        ; Function definitions without arguments (def, defp) - e.g., def goodbye
        (call
            (identifier) @def_keyword
            (#match? @def_keyword "^(def|defp)$")
            (arguments
                (identifier) @name
            )
        ) @function

        ; Macro definitions with arguments (defmacro, defmacrop)
        (call
            (identifier) @def_keyword
            (#match? @def_keyword "^(defmacro|defmacrop)$")
            (arguments
                (call
                    (identifier) @name
                )
            )
        ) @function

        ; Macro definitions without arguments (defmacro, defmacrop)
        (call
            (identifier) @def_keyword
            (#match? @def_keyword "^(defmacro|defmacrop)$")
            (arguments
                (identifier) @name
            )
        ) @function
    """,
    "imports": """
        ; Import, alias, require, use statements
        (call
            (identifier) @import_type
            (#match? @import_type "^(import|alias|require|use)$")
        ) @import_statement
    """,
    "doc_comments": """
        ; @moduledoc attribute with string content
        (unary_operator
            "@"
            (call
                (identifier) @attr_name
                (#eq? @attr_name "moduledoc")
                (arguments
                    (string) @moduledoc_content
                )
            )
        ) @moduledoc_attr

        ; @doc attribute with string content
        (unary_operator
            "@"
            (call
                (identifier) @attr_name
                (#eq? @attr_name "doc")
                (arguments
                    (string) @doc_content
                )
            )
        ) @doc_attr
    """,
}


class TreeSitterElixirParser(BaseTreeSitterParser):
    """Parser for Elixir using tree-sitter-elixir grammar."""

    def __init__(self) -> None:
        """Initialize the Elixir parser."""
        super().__init__("elixir")
        # Language-specific tracking (not part of ParseResult)
        self._genserver_callbacks: set[str] = set()
        self._liveview_callbacks: set[str] = set()
        self._pattern_matches: int = 0
        self._pipe_operations: int = 0
        self._behaviors: set[str] = set()
        self._protocols: set[str] = set()
        self._macros: set[str] = set()
        self._supervisor_trees: int = 0

    def get_queries(self) -> dict[str, str]:
        """Get the tree-sitter queries for Elixir."""
        return ELIXIR_QUERIES

    def _run_queries(
        self, root_node: Node, byte_content: bytes
    ) -> tuple[list[Declaration], list[str]]:
        """Run Elixir-specific queries with @doc/@moduledoc extraction."""
        queries = self.get_queries()
        declarations: list[Declaration] = []
        imports: set[str] = set()
        doc_comment_map: dict[int, str] = {}  # end_line -> docstring text
        moduledoc_map: dict[int, str] = {}  # end_line -> moduledoc text

        # --- Pass 1: Extract @doc/@moduledoc attributes --- #
        try:
            doc_query_str = queries.get("doc_comments", "")
            if doc_query_str:
                doc_query = Query(self.ts_language, doc_query_str)
                doc_captures = self._execute_query_with_cursor(doc_query, root_node)

                # Process @moduledoc captures
                if "moduledoc_content" in doc_captures:
                    for node in doc_captures["moduledoc_content"]:
                        docstring = self._clean_elixir_string(node, byte_content)
                        if docstring:
                            # Use the parent's end line for association
                            parent = node.parent
                            while parent and parent.type != "unary_operator":
                                parent = parent.parent
                            if parent:
                                moduledoc_map[parent.end_point[0]] = docstring

                # Process @doc captures
                if "doc_content" in doc_captures:
                    for node in doc_captures["doc_content"]:
                        docstring = self._clean_elixir_string(node, byte_content)
                        if docstring:
                            # Use the parent's end line for association
                            parent = node.parent
                            while parent and parent.type != "unary_operator":
                                parent = parent.parent
                            if parent:
                                doc_comment_map[parent.end_point[0]] = docstring

        except Exception as e:
            logger.warning(f"Failed to execute Elixir doc_comments query: {e}", exc_info=True)

        # --- Pass 2: Extract imports --- #
        try:
            import_query_str = queries.get("imports", "")
            if import_query_str:
                import_query = Query(self.ts_language, import_query_str)
                import_captures = self._execute_query_with_cursor(import_query, root_node)

                if "import_statement" in import_captures:
                    for node in import_captures["import_statement"]:
                        import_text = byte_content[node.start_byte : node.end_byte].decode(
                            "utf-8", errors="replace"
                        )
                        imports.add(import_text.strip())

        except Exception as e:
            logger.warning(f"Failed to execute Elixir imports query: {e}", exc_info=True)

        # --- Pass 3: Extract declarations and associate docstrings --- #
        try:
            decl_query_str = queries.get("declarations", "")
            if decl_query_str:
                decl_query = Query(self.ts_language, decl_query_str)
                matches = self._execute_query_matches(decl_query, root_node)

                for _match_id, captures_dict in matches:
                    declaration_node = None
                    name_node = None
                    kind = None

                    # Check for module or function declaration
                    if "module" in captures_dict and captures_dict["module"]:
                        declaration_node = captures_dict["module"][0]
                        kind = "module"
                    elif "function" in captures_dict and captures_dict["function"]:
                        declaration_node = captures_dict["function"][0]
                        kind = "function"

                    # Get the name node
                    if "name" in captures_dict and captures_dict["name"]:
                        name_node = captures_dict["name"][0]

                    if declaration_node and name_node:
                        name_text = byte_content[name_node.start_byte : name_node.end_byte].decode(
                            "utf-8", errors="replace"
                        )

                        start_line, end_line = get_node_location(declaration_node)

                        # Look for associated docstring
                        docstring = ""
                        decl_start_line = declaration_node.start_point[0]

                        if kind == "module":
                            # For modules, find @moduledoc that appears after the defmodule
                            # and before any function definitions
                            for doc_end_line, doc_text in moduledoc_map.items():
                                # @moduledoc should be inside the module (after start)
                                if decl_start_line < doc_end_line < end_line:
                                    docstring = doc_text
                                    break
                        else:
                            # For functions, find @doc immediately before the def
                            for doc_end_line, doc_text in doc_comment_map.items():
                                # @doc should end right before the function starts
                                if doc_end_line == decl_start_line - 1:
                                    docstring = doc_text
                                    break

                        declarations.append(
                            Declaration(
                                kind=kind or "unknown",
                                name=name_text,
                                start_line=start_line,
                                end_line=end_line,
                                docstring=docstring,
                            )
                        )

        except Exception as e:
            logger.warning(f"Failed to execute Elixir declarations query: {e}", exc_info=True)

        declarations.sort(key=lambda d: d.start_line)
        sorted_imports = sorted(imports)

        logger.debug(
            f"Tree-sitter Elixir extracted {len(declarations)} declarations "
            f"and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports

    def _clean_elixir_string(self, string_node: Node, byte_content: bytes) -> str:
        """Extract and clean content from an Elixir string node.

        Args:
            string_node: A tree-sitter node of type 'string'.
            byte_content: The source code as bytes.

        Returns:
            Cleaned string content without quotes.
        """
        # Find quoted_content child which contains the actual string content
        for child in string_node.children:
            if child.type == "quoted_content":
                content = byte_content[child.start_byte : child.end_byte].decode(
                    "utf-8", errors="replace"
                )
                # Normalize whitespace
                return normalize_whitespace(content.strip())

        # Fallback: extract full string and strip quotes
        full_text = byte_content[string_node.start_byte : string_node.end_byte].decode(
            "utf-8", errors="replace"
        )
        # Remove triple quotes
        if full_text.startswith('"""') and full_text.endswith('"""'):
            content = full_text[3:-3]
        elif full_text.startswith('"') and full_text.endswith('"'):
            content = full_text[1:-1]
        else:
            content = full_text
        return normalize_whitespace(content.strip())

    def parse(self, content: str, file_path: str | None = None) -> ParseResult:
        """
        Parse Elixir source code and extract structured information.

        Args:
            content: The source code to parse
            file_path: Optional file path for better error messages

        Returns:
            ParseResult containing declarations and imports
        """
        # Reset Elixir-specific tracking
        self._genserver_callbacks.clear()
        self._liveview_callbacks.clear()
        self._pattern_matches = 0
        self._pipe_operations = 0
        self._behaviors.clear()
        self._protocols.clear()
        self._macros.clear()
        self._supervisor_trees = 0

        # Use base class to parse and extract declarations/imports
        result = super().parse(content, file_path or "")

        # Post-process declarations to add Elixir-specific tracking
        if result.ast_root:
            self._track_language_features(result.ast_root, result.declarations, content)

        return result

    def _track_language_features(
        self, root_node: Node, declarations: list[Declaration], content: str
    ) -> None:
        """
        Analyze the AST to track Elixir-specific language features.

        This runs after base class extraction to add language-specific metrics.
        """
        content_bytes = content.encode("utf-8")

        # Track GenServer, LiveView, Supervisor callbacks, and macros
        for decl in declarations:
            if decl.kind == "function":
                func_name = decl.name

                # Check if this is a macro by examining the signature/context
                # Since we don't have access to the original query metadata,
                # we'll count functions that match macro naming patterns
                # This is a heuristic since macros were extracted as @function

                # GenServer callbacks
                if func_name in [
                    "init",
                    "handle_call",
                    "handle_cast",
                    "handle_info",
                    "handle_continue",
                    "terminate",
                    "code_change",
                    "format_status",
                ]:
                    self._genserver_callbacks.add(func_name)

                # LiveView callbacks
                if func_name in [
                    "mount",
                    "render",
                    "handle_event",
                    "handle_params",
                ]:
                    self._liveview_callbacks.add(func_name)

                # Supervisor callbacks
                # Only count if NOT already counted as GenServer to avoid double-counting
                if (
                    func_name in ["init", "start_link", "child_spec"]
                    and func_name not in self._genserver_callbacks
                ):
                    self._supervisor_trees += 1

        # Walk AST to find macros, pipes, patterns, and behaviors
        self._walk_ast_for_features(root_node, content_bytes)

    def _walk_ast_for_features(self, node: Node, content_bytes: bytes) -> None:
        """Walk the AST to track language-specific features."""
        # Track macros (defmacro/defmacrop)
        if node.type == "call":
            # Check if this is a macro definition
            for child in node.children:
                if child.type == "identifier":
                    id_text = content_bytes[child.start_byte : child.end_byte].decode(
                        "utf-8", errors="replace"
                    )
                    if id_text in ["defmacro", "defmacrop"]:
                        # Find macro name
                        for arg_node in node.children:
                            if arg_node.type == "arguments":
                                for macro_call in arg_node.children:
                                    if macro_call.type == "call":
                                        for name_node in macro_call.children:
                                            if name_node.type == "identifier":
                                                macro_name = content_bytes[
                                                    name_node.start_byte : name_node.end_byte
                                                ].decode("utf-8", errors="replace")
                                                self._macros.add(macro_name)
                                                break
                        break
                    # Track use statements (behaviors)
                    elif id_text == "use":
                        # Find what's being used
                        for arg_node in node.children:
                            if arg_node.type == "arguments":
                                for alias_node in arg_node.children:
                                    if alias_node.type == "alias":
                                        behavior_name = content_bytes[
                                            alias_node.start_byte : alias_node.end_byte
                                        ].decode("utf-8", errors="replace")
                                        self._behaviors.add(behavior_name)
                        break
                    # Track protocol definitions and implementations
                    elif id_text in ["defprotocol", "defimpl"]:
                        for arg_node in node.children:
                            if arg_node.type == "arguments":
                                for proto_node in arg_node.children:
                                    if proto_node.type in ("alias", "identifier"):
                                        proto_name = content_bytes[
                                            proto_node.start_byte : proto_node.end_byte
                                        ].decode("utf-8", errors="replace")
                                        self._protocols.add(proto_name)
                        break

        # Track pipe operators
        if node.type == "binary_operator":
            # Check if this binary operator contains |>
            # The operator token appears in the source but not always as a named child
            node_text = content_bytes[node.start_byte : node.end_byte].decode(
                "utf-8", errors="replace"
            )
            if "|>" in node_text:
                # Verify it's actually a pipe by checking immediate context
                # Count each binary_operator node that contains |>
                # But we need to avoid double-counting nested pipes
                # Only count if this is the immediate parent of the |> operator
                for child in node.children:
                    child_text = content_bytes[child.start_byte : child.end_byte].decode(
                        "utf-8", errors="replace"
                    )
                    # Check if |> appears between children (not inside a child)
                    if child_text.strip() == "|>":
                        self._pipe_operations += 1
                        break
                else:
                    # If no child is exactly "|>", check if the gap between children contains it
                    # This handles the case where |> is an unnamed token
                    if len(node.children) >= 2:
                        # Get text between first and second child
                        first_child = node.children[0]
                        second_child = node.children[1]
                        between_start = first_child.end_byte
                        between_end = second_child.start_byte
                        between_text = content_bytes[between_start:between_end].decode(
                            "utf-8", errors="replace"
                        )
                        if "|>" in between_text:
                            self._pipe_operations += 1

        # Track pattern matching constructs
        if node.type in ["tuple", "map", "list"]:
            # Check if this is in a function parameter or case clause (pattern match context)
            parent = node.parent
            if parent and parent.type in ["arguments", "stab_clause"]:
                self._pattern_matches += 1

        # Recursively walk children
        for child in node.children:
            self._walk_ast_for_features(child, content_bytes)

    def _has_pattern_match(self, node: Node) -> bool:
        """Check if a node contains pattern matching constructs."""
        if not node:
            return False

        # Pattern matching indicators: tuples, maps, lists in function params
        pattern_types = {"tuple", "map", "list", "binary_operator"}

        # Check node and its children
        if node.type in pattern_types:
            return True

        return any(self._has_pattern_match(child) for child in node.children)

    # Public accessors for language-specific metrics (for testing)
    @property
    def genserver_callback_count(self) -> int:
        """Get count of GenServer callbacks found."""
        return len(self._genserver_callbacks)

    @property
    def liveview_callback_count(self) -> int:
        """Get count of LiveView callbacks found."""
        return len(self._liveview_callbacks)

    @property
    def pattern_match_count(self) -> int:
        """Get count of pattern matches found."""
        return self._pattern_matches

    @property
    def pipe_operation_count(self) -> int:
        """Get count of pipe operations found."""
        return self._pipe_operations

    @property
    def behavior_count(self) -> int:
        """Get count of behaviors (use statements) found."""
        return len(self._behaviors)

    @property
    def protocol_count(self) -> int:
        """Get count of protocols found."""
        return len(self._protocols)

    @property
    def macro_count(self) -> int:
        """Get count of macros found."""
        return len(self._macros)

    @property
    def supervisor_tree_count(self) -> int:
        """Get count of supervisor-related callbacks found."""
        return self._supervisor_trees
