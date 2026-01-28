"""WebAssembly Text (WAT) parser using tree-sitter.

This parser extracts declarations, imports, and structure from WebAssembly Text format files.
WAT is the human-readable text representation of WebAssembly modules.

Supports:
- Module declarations
- Function definitions with types
- Import and export statements
- Memory, table, and global definitions
- Type definitions
- Data and element segments
"""

import logging

# QueryCursor was removed in tree-sitter 0.24.0 - import it if available for backward compatibility
try:
    from tree_sitter import QueryCursor  # type: ignore[attr-defined]
except ImportError:
    QueryCursor = None  # type: ignore[assignment,misc]

from ...base_types import Declaration, ParseResult
from ..utils import get_node_location
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Tree-sitter queries for WebAssembly Text format
WAT_QUERIES = {
    "imports": """
        ; Import statements
        (module_field_import) @import_statement
    """,
    "exports": """
        ; Export statements
        (module_field_export
            (name (string) @export_name)
        ) @export_statement
    """,
    "declarations": """
        ; Module declaration
        (module) @module

        ; Function definitions
        (module_field_func
            (identifier)? @func_name
        ) @function

        ; Type definitions
        (module_field_type
            (identifier)? @type_name
        ) @type_def

        ; Table definitions
        (module_field_table
            (identifier)? @table_name
        ) @table_def

        ; Global definitions
        (module_field_global
            (identifier)? @global_name
        ) @global_def
    """,
}


class TreeSitterWatParser(BaseTreeSitterParser):
    """Tree-sitter based parser for WebAssembly Text format.

    This parser extracts structure and declarations from WAT files,
    providing insights into WebAssembly module organization, functions,
    imports/exports, and memory layout.
    """

    def __init__(self):
        """Initialize the WAT parser with the tree-sitter-wasm grammar."""
        super().__init__("wat")

    def _load_language(self):
        """Load the WAT language from our custom tree_sitter_wat module.

        This override is necessary because the WAT grammar is built locally
        rather than being available in tree-sitter-language-pack.

        Returns:
            Language: The loaded Tree-sitter language object

        Raises:
            LanguageParserError: If the language cannot be loaded
        """
        from ...errors import LanguageParserError

        try:
            # Import our local tree_sitter_wat module
            from tree_sitter import Language

            from . import tree_sitter_wat

            # Get the language capsule
            language_capsule = tree_sitter_wat.language()

            # Wrap it in a Language object
            language = Language(language_capsule)
            logger.debug("Successfully loaded WAT language from local module")
            return language
        except Exception as e:
            logger.error(f"Failed to load WAT language: {e}")
            raise LanguageParserError(
                f"Could not load Tree-sitter language for WAT. Error: {e}"
            ) from e

    def _create_parser(self):
        """Create a Tree-sitter parser configured for WAT.

        This override is necessary to use our locally-loaded language
        rather than relying on tree-sitter-language-pack.

        Returns:
            Parser: Configured Tree-sitter parser for WAT

        Raises:
            LanguageParserError: If the parser cannot be created
        """
        from tree_sitter import Parser

        from ...errors import LanguageParserError

        try:
            parser = Parser()
            parser.language = self.ts_language
            logger.debug("Successfully created WAT parser")
            return parser
        except Exception as e:
            logger.error(f"Failed to create WAT parser: {e}")
            raise LanguageParserError(f"Failed to create parser for WAT: {e}") from e

    def get_queries(self) -> dict[str, str]:
        """Return WAT-specific tree-sitter queries.

        Returns:
            Dictionary mapping query names to query strings.
        """
        return WAT_QUERIES

    def parse(self, content: str, file_path: str = "") -> ParseResult:  # noqa: ARG002
        """Parse WAT source code and extract declarations.

        Args:
            content: WebAssembly Text format source code to parse.
            file_path: Optional path to the file being parsed (unused for WAT).

        Returns:
            ParseResult containing extracted declarations, imports, and exports.
        """
        from ...base_types import ParseResult

        result = ParseResult()

        try:
            # Parse the content using tree-sitter
            tree = self.parser.parse(bytes(content, "utf8"))

            # Extract imports
            imports_query = self._get_compiled_query("imports")
            if imports_query:
                captures = self._execute_query_with_cursor(imports_query, tree.root_node)
                result.imports.extend(self._process_imports(captures))

            # Extract exports
            exports_query = self._get_compiled_query("exports")
            if exports_query:
                captures = self._execute_query_with_cursor(exports_query, tree.root_node)
                self._process_exports(captures, result)

            # Extract declarations
            declarations_query = self._get_compiled_query("declarations")
            if declarations_query:
                captures = self._execute_query_with_cursor(declarations_query, tree.root_node)
                result.declarations.extend(self._process_declarations(captures, content))

        except Exception as e:
            logger.error(f"Error parsing WAT content: {e}")
            result.error = f"Parse error: {str(e)}"

        return result

    def _extract_import_from_node(self, node) -> str | None:
        """Extract import string from an import statement node.

        Args:
            node: The import_statement node.

        Returns:
            Import string in format "module.name" or None if extraction fails.
        """
        # Each import statement has two "name" children with string values
        name_nodes = [child for child in node.children if child.type == "name"]
        if len(name_nodes) < 2:
            return None

        # First name is module, second is import name
        module_text = None
        import_text = None

        # Extract string from first name node
        for child in name_nodes[0].children:
            if child.type == "string":
                module_text = child.text.decode("utf-8").strip('"')
                break

        # Extract string from second name node
        for child in name_nodes[1].children:
            if child.type == "string":
                import_text = child.text.decode("utf-8").strip('"')
                break

        if module_text and import_text:
            return f"{module_text}.{import_text}"
        return None

    def _process_imports(self, captures: dict | list) -> list[str]:
        """Process import statement captures.

        Args:
            captures: Captured nodes from import query.

        Returns:
            List of import strings in format "module.name".
        """
        imports = []

        # Handle both dict format (new API) and list format (old API)
        if isinstance(captures, dict):
            # Dict format from new tree-sitter API
            if "import_statement" in captures:
                for node in captures["import_statement"]:
                    import_str = self._extract_import_from_node(node)
                    if import_str:
                        imports.append(import_str)
        else:
            # List format from old tree-sitter API
            for node, capture_name in captures:
                if capture_name == "import_statement":
                    import_str = self._extract_import_from_node(node)
                    if import_str:
                        imports.append(import_str)

        return imports

    def _process_exports(self, captures: dict | list, result: ParseResult):
        """Process export statement captures.

        Args:
            captures: Captured nodes from export query.
            result: ParseResult to add exports to.
        """
        # Handle both dict format (new API) and list format (old API)
        if isinstance(captures, dict):
            # Dict format from new tree-sitter API
            if "export_statement" in captures:
                for export_node in captures["export_statement"]:
                    # Extract export name and line numbers from the statement node
                    export_name = None

                    # Find the name node within the export statement
                    for child in export_node.children:
                        if child.type == "name":
                            for name_child in child.children:
                                if name_child.type == "string":
                                    export_name = name_child.text.decode("utf-8").strip('"')
                                    break
                            break

                    if export_name:
                        start_line, end_line = get_node_location(export_node)
                        declaration = Declaration(
                            name=export_name,
                            kind="export",
                            start_line=start_line,
                            end_line=end_line,
                        )
                        result.declarations.append(declaration)
        else:
            # List format from old tree-sitter API
            for node, capture_name in captures:
                if capture_name == "export_statement":
                    # Extract export name and line numbers from the statement node
                    export_name = None

                    # Find the name node within the export statement
                    for child in node.children:
                        if child.type == "name":
                            for name_child in child.children:
                                if name_child.type == "string":
                                    export_name = name_child.text.decode("utf-8").strip('"')
                                    break
                            break

                    if export_name:
                        start_line, end_line = get_node_location(node)
                        declaration = Declaration(
                            name=export_name,
                            kind="export",
                            start_line=start_line,
                            end_line=end_line,
                        )
                        result.declarations.append(declaration)

    def _process_declarations(self, captures: dict | list, content: str) -> list[Declaration]:  # noqa: ARG002
        """Process declaration captures into Declaration objects.

        Args:
            captures: Captured nodes from declarations query.
            content: Original source code.

        Returns:
            List of Declaration objects.
        """
        declarations = []

        # Handle both dict format (new API) and list format (old API)
        if isinstance(captures, dict):
            # Dict format from new tree-sitter API
            for capture_name, nodes in captures.items():
                for node in nodes:
                    decl = self._create_declaration(node, capture_name)
                    if decl:
                        declarations.append(decl)
        else:
            # List format from old tree-sitter API
            for node, capture_name in captures:
                decl = self._create_declaration(node, capture_name)
                if decl:
                    declarations.append(decl)

        return declarations

    def _create_declaration(self, node, capture_name: str) -> Declaration | None:
        """Create a Declaration object from a captured node.

        Args:
            node: The captured tree-sitter node.
            capture_name: The name of the capture.

        Returns:
            Declaration object or None if not applicable.
        """
        # Map capture names to declaration kinds
        kind_mapping = {
            "module": "module",
            "function": "function",
            "type_def": "type",
            "table_def": "table",
            "global_def": "global",
            "func_name": None,  # Skip name captures
            "type_name": None,
            "table_name": None,
            "global_name": None,
        }

        kind = kind_mapping.get(capture_name)
        if kind is None:
            return None

        # Extract name from the node if available
        decl_name = ""
        for child in node.children:
            if child.type == "identifier":
                decl_name = child.text.decode("utf-8").strip("$")
                break

        # If no name found, generate a default based on type
        if not decl_name:
            decl_name = "(module)" if capture_name == "module" else f"({kind})"

        start_line, end_line = get_node_location(node)

        declaration = Declaration(
            name=decl_name,
            kind=kind,
            start_line=start_line,
            end_line=end_line,
        )

        # Add signatures for functions if possible
        if capture_name == "function":
            # Try to extract parameter and result types
            param_types = []
            result_types = []

            for child in node.children:
                if child.type == "func_type_params":
                    # Extract parameter types from func_type_params
                    for param_node in child.children:
                        if param_node.type in ["func_type_params_many", "func_type_params_one"]:
                            for value_type in param_node.children:
                                if value_type.type == "value_type":
                                    # Extract the actual type text (e.g., "i32")
                                    type_text = value_type.text.decode("utf-8").strip()
                                    if type_text:
                                        param_types.append(type_text)
                elif child.type == "func_type_results":
                    # Extract result types from func_type_results
                    for result_child in child.children:
                        if result_child.type == "value_type":
                            type_text = result_child.text.decode("utf-8").strip()
                            if type_text:
                                result_types.append(type_text)

            if param_types or result_types:
                params = " ".join(param_types) if param_types else ""
                results = " -> " + " ".join(result_types) if result_types else ""
                declaration.signature = f"(func {decl_name} {params}{results})"

        return declaration
