# file: codeconcat/parser/language_parsers/tree_sitter_crystal_parser.py

"""
Enhanced Crystal parser using tree-sitter.

Extracts declarations, imports, type annotations, and Crystal-specific constructs
using the crystal-lang-tools/tree-sitter-crystal grammar.

Supports Crystal 1.0+ with features including:
- Type annotations in method signatures and variable declarations
- Macro system (macro definitions and expansions)
- C library bindings (lib blocks and FFI declarations)
- Generic types with constraints
- Union and nilable types
- Module and class inheritance
- Abstract methods and types
- Crystal documentation comments
"""

import logging

from tree_sitter import Node

from ...base_types import Declaration, ParseResult
from ...errors import LanguageParserError

# QueryCursor was removed in tree-sitter 0.24.0 - import it if available for backward compatibility
try:
    from tree_sitter import QueryCursor  # type: ignore[attr-defined]
except ImportError:
    QueryCursor = None  # type: ignore[assignment,misc]

from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Tree-sitter queries for Crystal syntax
# Conforms to BaseTreeSitterParser expectations:
# - Use @class/@module/@function (not @class_def/@module_def/@function_def)
# - Use @name for the name capture
# - Use @import_statement for imports
CRYSTAL_QUERIES = {
    "doc_comments": """
        ; Crystal documentation comments (# style)
        (comment) @comment
    """,
    "declarations": """
        ; Class definitions (non-generic)
        (class_def
            (constant) @name
        ) @class

        ; Class definitions (generic)
        (class_def
            (generic_type
                (constant) @name
            )
        ) @class

        ; Module definitions
        (module_def
            (constant) @name
        ) @module

        ; Struct definitions (non-generic)
        (struct_def
            (constant) @name
        ) @class

        ; Struct definitions (generic)
        (struct_def
            (generic_type
                (constant) @name
            )
        ) @class

        ; Lib definitions (C bindings) - mapped to module since they're namespace-like
        (lib_def
            (constant) @name
        ) @module

        ; Method definitions
        (method_def
            (identifier) @name
        ) @function

        ; Macro definitions
        (macro_def
            (identifier) @name
        ) @macro

        ; Type aliases - mapped to class since they define types
        (alias
            (constant) @name
        ) @class
    """,
    "imports": """
        ; Require statements
        (require) @import_statement

        ; Include statements
        (include) @import_statement

        ; Extend statements
        (extend) @import_statement
    """,
}


class TreeSitterCrystalParser(BaseTreeSitterParser):
    """Parser for Crystal using tree-sitter-crystal grammar."""

    def __init__(self) -> None:
        """Initialize the Crystal parser."""
        super().__init__("crystal")
        # Language-specific tracking (not part of ParseResult)
        self._macros: set[str] = set()
        self._c_bindings: dict[str, list[str]] = {}
        self._generic_types: set[str] = set()
        self._union_types: list[str] = []
        self._nilable_types: list[str] = []

    def _load_language(self):
        """Load the Crystal language from our custom tree_sitter_crystal module.

        This override is necessary because the Crystal grammar is built locally
        rather than being available in tree-sitter-language-pack.

        Returns:
            Language: The loaded Tree-sitter language object

        Raises:
            LanguageParserError: If the language cannot be loaded
        """
        try:
            # Import our local tree_sitter_crystal module
            from tree_sitter import Language

            from . import tree_sitter_crystal

            # Get the language capsule
            language_capsule = tree_sitter_crystal.language()

            # Wrap it in a Language object
            language = Language(language_capsule)
            logger.debug("Successfully loaded Crystal language from local module")
            return language
        except Exception as e:
            logger.error(f"Failed to load Crystal language: {e}")
            raise LanguageParserError(
                f"Could not load Tree-sitter language for Crystal. Error: {e}"
            ) from e

    def _create_parser(self):
        """Create a Tree-sitter parser configured for Crystal.

        This override is necessary to use our locally-loaded language
        rather than relying on tree-sitter-language-pack.

        Returns:
            Parser: A configured Tree-sitter parser instance

        Raises:
            LanguageParserError: If parser creation fails
        """
        try:
            from tree_sitter import Parser

            parser = Parser()
            parser.language = self.ts_language
            logger.debug("Successfully created Crystal parser")
            return parser
        except Exception as e:
            logger.error(f"Failed to create Crystal parser: {e}")
            raise LanguageParserError(
                f"Could not create Tree-sitter parser for Crystal. Error: {e}"
            ) from e

    def get_queries(self) -> dict[str, str]:
        """Get the tree-sitter queries for Crystal."""
        return CRYSTAL_QUERIES

    def parse(self, content: str, file_path: str | None = None) -> ParseResult:
        """
        Parse Crystal source code and extract structured information.

        Args:
            content: The source code to parse
            file_path: Optional file path for better error messages

        Returns:
            ParseResult containing declarations and imports
        """
        # Reset Crystal-specific tracking
        self._macros.clear()
        self._c_bindings.clear()
        self._generic_types.clear()
        self._union_types.clear()
        self._nilable_types.clear()

        # Use base class to parse and extract declarations/imports
        result = super().parse(content, file_path or "")

        # Post-process declarations to add Crystal-specific tracking
        if result.ast_root:
            self._track_language_features(result.ast_root, result.declarations, content)

        return result

    def _track_language_features(
        self, root_node: Node, declarations: list[Declaration], content: str
    ) -> None:
        """
        Analyze the AST to track Crystal-specific language features.

        This runs after base class extraction to add language-specific metrics.
        """
        content_bytes = content.encode("utf-8")

        # Track macros in declarations
        for decl in declarations:
            if decl.kind == "function":
                # Check if this was extracted from a macro definition
                # by examining the source node
                pass

        # Walk AST to find type annotations, C bindings, generics
        self._walk_ast_for_features(root_node, content_bytes)

    def _walk_ast_for_features(self, node: Node, content_bytes: bytes) -> None:
        """Walk the AST to track language-specific features."""
        # Track type annotations
        if node.type == "type_annotation":
            # Extract the type annotation
            type_text = content_bytes[node.start_byte : node.end_byte].decode(
                "utf-8", errors="replace"
            )
            # Check for union types (Type1 | Type2)
            if "|" in type_text:
                self._union_types.append(type_text)
            # Check for nilable types (Type?)
            if type_text.endswith("?"):
                self._nilable_types.append(type_text)

        # Track macro definitions
        if node.type == "macro_def":
            for child in node.children:
                if child.type == "identifier":
                    macro_name = content_bytes[child.start_byte : child.end_byte].decode(
                        "utf-8", errors="replace"
                    )
                    self._macros.add(macro_name)
                    break

        # Track C bindings (lib blocks)
        if node.type == "lib_def":
            for child in node.children:
                if child.type == "constant":
                    lib_name = content_bytes[child.start_byte : child.end_byte].decode(
                        "utf-8", errors="replace"
                    )
                    self._c_bindings[lib_name] = []
                    # Extract functions within this lib block (child.parent is node)
                    self._extract_lib_functions(node, content_bytes, lib_name)
                    break

        # Track generic types
        if node.type == "type_parameter_list":
            parent = node.parent
            if parent and parent.type in ["class_def", "module_def", "struct_def"]:
                # This class/module/struct is generic
                for sibling in parent.children:
                    if sibling.type == "constant":
                        type_name = content_bytes[sibling.start_byte : sibling.end_byte].decode(
                            "utf-8", errors="replace"
                        )
                        self._generic_types.add(type_name)
                        break

        # Recursively walk children
        for child in node.children:
            self._walk_ast_for_features(child, content_bytes)

    def _extract_lib_functions(self, lib_node: Node, content_bytes: bytes, lib_name: str) -> None:
        """Extract function declarations from a lib block."""
        for node in lib_node.children:
            if node.type == "fun_def":
                # Extract function name
                for child in node.children:
                    if child.type == "identifier":
                        fun_name = content_bytes[child.start_byte : child.end_byte].decode(
                            "utf-8", errors="replace"
                        )
                        if lib_name in self._c_bindings:
                            self._c_bindings[lib_name].append(fun_name)
                        break

    # Public accessors for language-specific metrics (for testing)
    @property
    def macro_count(self) -> int:
        """Get count of macros found."""
        return len(self._macros)

    @property
    def c_binding_count(self) -> int:
        """Get count of C library bindings found."""
        return len(self._c_bindings)

    @property
    def generic_type_count(self) -> int:
        """Get count of generic types found."""
        return len(self._generic_types)

    @property
    def union_type_count(self) -> int:
        """Get count of union types found."""
        return len(self._union_types)

    @property
    def nilable_type_count(self) -> int:
        """Get count of nilable types found."""
        return len(self._nilable_types)
