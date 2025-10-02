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
from typing import Dict, List, Set

# QueryCursor was removed in tree-sitter 0.24.0 - import it if available for backward compatibility
try:
    from tree_sitter import QueryCursor
except ImportError:
    QueryCursor = None  # type: ignore[assignment,misc]

from ...base_types import Declaration
from ..utils import get_node_location
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Tree-sitter queries for Solidity language constructs
SOLIDITY_QUERIES = {
    "imports": """
        ; Import directives
        (import_directive
            source: (_) @import_source
        ) @import_statement

        ; Import with aliases
        (import_directive
            (_import_clause) @import_clause
        ) @import_with_clause
    """,
    "declarations": """
        ; Contract declarations with inheritance
        (contract_declaration
            name: (identifier) @name
            (inheritance_specifier
                (user_defined_type_name) @parent_contract
            )? @inheritance
            body: (contract_body) @body
        ) @contract

        ; Interface declarations
        (interface_declaration
            name: (identifier) @name
            body: (_) @body
        ) @interface

        ; Library declarations
        (library_declaration
            name: (identifier) @name
            body: (_) @body
        ) @library

        ; Function definitions with modifiers
        (function_definition
            name: (identifier)? @name
            (modifier_invocation
                name: (identifier) @modifier_name
            )* @modifiers
            parameters: (parameter_list) @params
            return_type: (return_type_definition)? @returns
            body: (function_body)? @body
        ) @function

        ; Constructor definitions
        (constructor_definition
            (modifier_invocation)* @modifiers
            parameters: (parameter_list) @params
            body: (function_body) @body
        ) @constructor

        ; Fallback function
        (fallback_function_definition
            parameters: (parameter_list)? @params
            (modifier_invocation)* @modifiers
            body: (function_body) @body
        ) @fallback

        ; Receive function
        (receive_function_definition
            (modifier_invocation)* @modifiers
            body: (function_body) @body
        ) @receive

        ; Modifier definitions
        (modifier_definition
            name: (identifier) @name
            parameters: (parameter_list)? @params
            body: (function_body) @body
        ) @modifier_def

        ; Event definitions
        (event_definition
            name: (identifier) @name
            parameters: (event_parameter_list) @params
        ) @event

        ; State variable declarations
        (state_variable_declaration
            type: (_) @type
            name: (identifier) @name
            value: (_)? @initial_value
        ) @state_var

        ; Struct definitions
        (struct_declaration
            name: (identifier) @name
            body: (struct_body) @members
        ) @struct

        ; Enum definitions
        (enum_declaration
            name: (identifier) @name
            body: (enum_body) @values
        ) @enum

        ; Error definitions (Solidity 0.8.4+)
        (error_declaration
            name: (identifier) @name
            parameters: (error_parameter_list)? @params
        ) @error
    """,
    "syntactic_patterns": """
        ; Assembly blocks - flag for manual review
        (assembly_statement
            body: (assembly_body) @assembly_content
        ) @assembly_block

        ; Delegatecall usage - potential security concern
        (member_access_expression
            object: (identifier) @object
            property: (property_identifier) @property
            (#eq? @property "delegatecall")
        ) @delegatecall_usage

        ; Selfdestruct calls - critical security concern
        (call_expression
            function: (identifier) @function_name
            (#eq? @function_name "selfdestruct")
        ) @selfdestruct_call

        ; Suicide calls (deprecated but still found in older contracts)
        (call_expression
            function: (identifier) @function_name
            (#eq? @function_name "suicide")
        ) @suicide_call

        ; External calls - flag for reentrancy review
        (call_expression
            function: (member_access_expression
                property: (property_identifier) @call_type
                (#match? @call_type "^(call|send|transfer)$")
            )
        ) @external_call

        ; Emit statements
        (emit_statement
            name: (identifier) @event_name
            arguments: (call_arguments) @args
        ) @event_emission

        ; Using statements for libraries
        (using_directive
            library: (_) @library_name
            type: (_) @target_type
        ) @using_statement

        ; Payable functions and modifiers
        (function_definition
            (payable) @payable_marker
        ) @payable_function

        ; View/Pure function modifiers
        (function_definition
            [(view) (pure)] @state_mutability
        ) @state_restricted_function
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
        self._pattern_warnings: Set[str] = set()

    def get_queries(self) -> Dict[str, str]:
        """Return Solidity-specific tree-sitter queries.

        Returns:
            Dictionary mapping query names to query strings
        """
        return SOLIDITY_QUERIES

    def parse(self, content: str) -> "ParseResult":
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
                imports = self._run_query(imports_query, tree.root_node, content)
                result.imports.extend(self._process_imports(imports))

            # Extract declarations
            declarations_query = self._get_compiled_query("declarations")
            if declarations_query:
                declarations = self._run_query(declarations_query, tree.root_node, content)
                result.declarations.extend(self._process_declarations(declarations, content))

            # Extract syntactic patterns for security review
            patterns_query = self._get_compiled_query("syntactic_patterns")
            if patterns_query:
                patterns = self._run_query(patterns_query, tree.root_node, content)
                self._process_patterns(patterns, content, result)

            # Add pattern warnings as metadata
            if self._pattern_warnings:
                result.metadata = result.metadata or {}
                result.metadata["security_patterns"] = list(self._pattern_warnings)
                logger.info(f"Found {len(self._pattern_warnings)} syntactic patterns for review")

        except Exception as e:
            logger.error(f"Error parsing Solidity content: {e}")
            result.error = f"Parse error: {str(e)}"

        return result

    def _process_imports(self, captures: List[tuple]) -> List[str]:
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
                if not any(imp in full_import for imp in imports):
                    # Extract just the path if we haven't captured it yet
                    if "from" in full_import:
                        parts = full_import.split("from")
                        if len(parts) > 1:
                            path = parts[1].strip().strip(";").strip("\"'")
                            imports.append(path)

        return imports

    def _process_declarations(self, captures: List[tuple], content: str) -> List[Declaration]:
        """Process declaration captures into Declaration objects.

        Args:
            captures: List of captured nodes from declarations query
            content: Original source code

        Returns:
            List of Declaration objects
        """
        declarations = []
        current_decl = None

        for node, name in captures:
            if name in [
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
                # Start new declaration
                if current_decl:
                    declarations.append(current_decl)

                decl_type = self._map_declaration_type(name)
                location = get_node_location(node)
                current_decl = Declaration(
                    name="",  # Will be filled by name capture
                    type=decl_type,
                    location=location,
                    metadata={},
                )

            elif name == "name" and current_decl:
                # Set declaration name
                current_decl.name = node.text.decode("utf-8").strip()

            elif name == "parent_contract" and current_decl:
                # Add inheritance info
                parent = node.text.decode("utf-8").strip()
                if "inherits" not in current_decl.metadata:
                    current_decl.metadata["inherits"] = []
                current_decl.metadata["inherits"].append(parent)

            elif name == "modifier_name" and current_decl:
                # Add modifier info
                modifier = node.text.decode("utf-8").strip()
                if "modifiers" not in current_decl.metadata:
                    current_decl.metadata["modifiers"] = []
                current_decl.metadata["modifiers"].append(modifier)

            elif name == "type" and current_decl and current_decl.type == "variable":
                # Add type info for state variables
                current_decl.metadata["var_type"] = node.text.decode("utf-8").strip()

            elif name == "payable_marker" and current_decl:
                current_decl.metadata["payable"] = True

            elif name == "state_mutability" and current_decl:
                current_decl.metadata["state_mutability"] = node.text.decode("utf-8").strip()

        # Add final declaration
        if current_decl:
            declarations.append(current_decl)

        return declarations

    def _process_patterns(self, captures: List[tuple], content: str, result: "ParseResult"):
        """Process syntactic patterns that may be of security interest.

        Args:
            captures: List of captured nodes from patterns query
            content: Original source code
            result: ParseResult to add warnings to
        """
        pattern_counts = {}

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
                location = get_node_location(node)
                if name == "selfdestruct_call":
                    self._pattern_warnings.add(
                        f"CRITICAL: selfdestruct usage at line {location.line_start}"
                    )
                elif name == "suicide_call":
                    self._pattern_warnings.add(
                        f"CRITICAL: deprecated suicide usage at line {location.line_start}"
                    )
                elif name == "delegatecall_usage":
                    self._pattern_warnings.add(
                        f"WARNING: delegatecall usage at line {location.line_start} - review for security"
                    )
                elif name == "assembly_block":
                    self._pattern_warnings.add(
                        f"INFO: Assembly block at line {location.line_start} - requires careful review"
                    )
                elif name == "external_call":
                    # Less verbose for external calls as they're common
                    if "external_calls" not in result.metadata:
                        result.metadata = result.metadata or {}
                        result.metadata["external_calls"] = []
                    result.metadata["external_calls"].append(location.line_start)

        # Add summary of patterns found
        if pattern_counts:
            result.metadata = result.metadata or {}
            result.metadata["pattern_counts"] = pattern_counts

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
