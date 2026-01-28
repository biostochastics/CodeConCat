# file: codeconcat/parser/language_parsers/tree_sitter_solidity_parser.py

"""
Solidity smart contract parser using Tree-sitter for syntactic analysis.

This parser provides comprehensive parsing of Solidity smart contracts including:
- Contract, interface, and library declarations with inheritance
- Function and modifier definitions
- State variables and events
- Import statements
- Assembly blocks

Security Note: This parser performs syntactic pattern flagging only. It identifies
patterns of interest for manual security review but does NOT perform semantic
security analysis. For comprehensive vulnerability detection, integrate with
dedicated tools like Slither or Mythril.

Based on JoranHonig/tree-sitter-solidity grammar.
"""

import logging

# QueryCursor was removed in tree-sitter 0.24.0 - import it if available for backward compatibility
try:
    from tree_sitter import QueryCursor
except ImportError:
    QueryCursor = None  # type: ignore[assignment,misc]

from ...base_types import Declaration, ParseResult
from ..utils import get_node_location
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Tree-sitter queries for Solidity language constructs
SOLIDITY_QUERIES = {
    "imports": """
        ; Import directives
        (import_directive) @import_statement
    """,
    "declarations": """
        ; Contract declarations (simple capture)
        (contract_declaration) @contract

        ; Function definitions
        (function_definition) @function

        ; State variable declarations
        (state_variable_declaration) @state_var

        ; Event definitions
        (event_definition) @event

        ; Modifier definitions
        (modifier_definition) @modifier_def

        ; Constructor definitions
        (constructor_definition) @constructor

        ; Struct definitions
        (struct_declaration) @struct

        ; Enum definitions
        (enum_declaration) @enum

        ; Interface declarations
        (interface_declaration) @interface

        ; Library declarations
        (library_declaration) @library

        ; Error definitions
        (error_declaration) @error
    """,
    "syntactic_patterns": """
        ; Using statements for libraries
        (using_directive) @using_statement
    """,
}


class TreeSitterSolidityParser(BaseTreeSitterParser):
    """Tree-sitter based parser for Solidity smart contracts.

    This parser provides syntactic analysis of Solidity code, extracting:
    - Smart contract structure and inheritance
    - Functions, modifiers, and events
    - State variables and constants
    - Import statements
    - Syntactic patterns of security interest (for manual review)

    Note: Security pattern detection is limited to syntactic patterns.
    For semantic security analysis, integrate with specialized tools.
    """

    def __init__(self):
        """Initialize the Solidity parser with the tree-sitter-solidity grammar."""
        super().__init__("solidity")
        self._pattern_warnings: set[str] = set()

    def get_queries(self) -> dict[str, str]:
        """Return Solidity-specific tree-sitter queries.

        Returns:
            Dictionary mapping query names to query strings
        """
        return SOLIDITY_QUERIES

    def parse(self, content: str, file_path: str = "") -> ParseResult:  # noqa: ARG002
        """Parse Solidity source code and extract declarations and patterns.

        Args:
            content: Solidity source code to parse

        Returns:
            ParseResult containing extracted declarations, imports, and flagged patterns
        """
        from ...base_types import ParseResult

        result = ParseResult()
        self._pattern_warnings.clear()

        try:
            # Parse the content using tree-sitter
            tree = self.parser.parse(bytes(content, "utf8"))

            # Extract imports
            imports_query = self._get_compiled_query("imports")
            if imports_query:
                captures_dict = self._execute_query_with_cursor(imports_query, tree.root_node)
                # Convert dict format to list of tuples
                imports = []
                for name, nodes in captures_dict.items():
                    for node in nodes:
                        imports.append((node, name))
                result.imports.extend(self._process_imports(imports))

            # Extract declarations
            declarations_query = self._get_compiled_query("declarations")
            if declarations_query:
                captures_dict = self._execute_query_with_cursor(declarations_query, tree.root_node)
                # Convert dict format to list of tuples
                declarations = []
                for name, nodes in captures_dict.items():
                    for node in nodes:
                        declarations.append((node, name))
                result.declarations.extend(self._process_declarations(declarations, content))

            # Extract syntactic patterns for security review
            patterns_query = self._get_compiled_query("syntactic_patterns")
            if patterns_query:
                captures_dict = self._execute_query_with_cursor(patterns_query, tree.root_node)
                # Convert dict format to list of tuples
                patterns = []
                for name, nodes in captures_dict.items():
                    for node in nodes:
                        patterns.append((node, name))
                self._process_patterns(patterns, content, result)

            # Log pattern warnings if any were found
            if self._pattern_warnings:
                logger.info(f"Found {len(self._pattern_warnings)} syntactic patterns for review")

        except Exception as e:
            logger.error(f"Error parsing Solidity content: {e}")
            result.error = f"Parse error: {str(e)}"

        return result

    def _process_imports(self, captures: list[tuple]) -> list[str]:
        """Process import statement captures.

        Args:
            captures: List of captured nodes from import query

        Returns:
            List of import strings
        """
        imports = []

        for node, name in captures:
            if name == "import_source":
                import_text = node.text.decode("utf-8").strip().strip("\"'")
                imports.append(import_text)
            elif name == "import_statement":
                # Full import statement for reference
                full_import = node.text.decode("utf-8").strip()
                if not any(imp in full_import for imp in imports) and "from" in full_import:
                    # Extract just the path if we haven't captured it yet
                    parts = full_import.split("from")
                    if len(parts) > 1:
                        path = parts[1].strip().strip(";").strip("\"'")
                        imports.append(path)

        return imports

    def _process_declarations(self, captures: list[tuple], content: str) -> list[Declaration]:  # noqa: ARG002
        """Process declaration captures into Declaration objects.

        Args:
            captures: List of captured nodes from declarations query
            content: Original source code

        Returns:
            List of Declaration objects
        """
        declarations = []

        for node, capture_name in captures:
            if capture_name in [
                "contract",
                "interface",
                "library",
                "function",
                "constructor",
                "fallback",
                "receive",
                "modifier_def",
                "event",
                "state_var",
                "struct",
                "enum",
                "error",
            ]:
                # Extract name from the node - look for identifier child
                decl_name = ""
                for child in node.children:
                    if child.type == "identifier":
                        decl_name = child.text.decode("utf-8").strip()
                        break

                # For state variables, the identifier might be deeper
                if capture_name == "state_var" and not decl_name:
                    # Look for identifier anywhere in the tree
                    for child in node.children:
                        if child.type == "identifier":
                            decl_name = child.text.decode("utf-8").strip()
                            break
                        # Check children of children for state variables
                        for grandchild in child.children:
                            if grandchild.type == "identifier":
                                decl_name = grandchild.text.decode("utf-8").strip()
                                break

                decl_type = self._map_declaration_type(capture_name)
                start_line, end_line = get_node_location(node)

                declaration = Declaration(
                    name=decl_name,
                    kind=decl_type,
                    start_line=start_line,
                    end_line=end_line,
                )

                # Add signature for functions
                if capture_name == "function" and decl_name:
                    declaration.signature = f"function {decl_name}()"
                elif capture_name == "contract":
                    declaration.signature = f"contract {decl_name}"

                declarations.append(declaration)

        return declarations

    def _process_patterns(self, captures: list[tuple], content: str, result: "ParseResult"):  # noqa: ARG002, F821
        """Process syntactic patterns that may be of security interest.

        Args:
            captures: List of captured nodes from patterns query
            content: Original source code
            result: ParseResult to add warnings to
        """
        pattern_counts: dict[str, int] = {}

        for node, name in captures:
            if name in [
                "assembly_block",
                "delegatecall_usage",
                "selfdestruct_call",
                "suicide_call",
                "external_call",
            ]:
                pattern_counts[name] = pattern_counts.get(name, 0) + 1

                # Add specific warnings for critical patterns
                start_line, end_line = get_node_location(node)
                if name == "selfdestruct_call":
                    self._pattern_warnings.add(f"CRITICAL: selfdestruct usage at line {start_line}")
                elif name == "suicide_call":
                    self._pattern_warnings.add(
                        f"CRITICAL: deprecated suicide usage at line {start_line}"
                    )
                elif name == "delegatecall_usage":
                    self._pattern_warnings.add(
                        f"WARNING: delegatecall usage at line {start_line} - review for security"
                    )
                elif name == "assembly_block":
                    self._pattern_warnings.add(
                        f"INFO: Assembly block at line {start_line} - requires careful review"
                    )
                elif name == "external_call":
                    # Track external calls as potential security issues
                    result.security_issues.append(
                        {"type": "external_call", "line": start_line, "severity": "info"}
                    )

        # Add pattern warnings as security issues
        for warning in self._pattern_warnings:
            result.security_issues.append({"type": "security_pattern", "message": warning})

    def _map_declaration_type(self, capture_name: str) -> str:
        """Map tree-sitter capture names to declaration types.

        Args:
            capture_name: Name from tree-sitter query capture

        Returns:
            Standardized declaration type
        """
        mapping = {
            "contract": "class",  # Map to class for compatibility
            "interface": "interface",
            "library": "library",
            "function": "function",
            "constructor": "constructor",
            "fallback": "function",
            "receive": "function",
            "modifier_def": "modifier",
            "event": "event",
            "state_var": "variable",
            "struct": "struct",
            "enum": "enum",
            "error": "error",
        }
        return mapping.get(capture_name, capture_name)
