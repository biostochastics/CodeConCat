"""Tree-sitter based parser for Bash/Shell scripts."""

import logging
from typing import Any, Dict, List, Optional

from tree_sitter import Node, Parser
from tree_sitter_language_pack import get_language

from ...base_types import Declaration
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)


class TreeSitterBashParser(BaseTreeSitterParser):
    """Tree-sitter based parser for Bash and shell scripts."""

    def __init__(self) -> None:
        """Initialize the Bash parser."""
        # Use tree-sitter-language-pack to get the bash language
        self.language_name = "bash"
        self.ts_language = get_language("bash")
        self.parser = Parser(self.ts_language)
        self._query_cache: Dict[tuple, Optional[Any]] = {}

    def get_queries(self) -> Dict[str, str]:
        """Get the tree-sitter queries for Bash.

        Returns queries for:
        - Functions (function declarations)
        - Variables (variable assignments)
        - Aliases (alias declarations)
        - Source/includes (source and . commands)
        """
        return {
            "functions": """
                (function_definition
                  name: (word) @function.name) @function

                (function_definition
                  body: (_) @function.body)
            """,
            "variables": """
                (variable_assignment
                  name: (variable_name) @variable.name) @variable

                (declaration_command
                  (variable_assignment
                    name: (variable_name) @variable.name))
            """,
            "aliases": """
                (command
                  name: (command_name (word) @alias.cmd (#eq? @alias.cmd "alias"))
                  argument: (concatenation) @alias.definition)

                (command
                  name: (command_name (word) @alias.cmd (#eq? @alias.cmd "alias"))
                  argument: (word) @alias.definition)
            """,
            "imports": """
                (command
                  name: (command_name (word) @source.cmd (#match? @source.cmd "^(source|\\.)$"))
                  argument: (_) @source.path)
            """,
        }

    def parse(self, content: str, file_path: str) -> Any:
        """Parse Bash/shell script content.

        Args:
            content: The shell script content to parse
            file_path: Path to the shell script file (unused but required by interface)

        Returns:
            Parsing result with declarations and imports
        """
        _ = file_path  # Explicitly mark as unused
        byte_content = content.encode("utf8")
        tree = self.parser.parse(byte_content)
        root_node = tree.root_node

        declarations: List[Declaration] = []
        imports: List[str] = []

        # Extract functions
        self._extract_functions(root_node, byte_content, declarations)

        # Extract variables
        self._extract_variables(root_node, byte_content, declarations)

        # Extract source/includes
        self._extract_imports(root_node, byte_content, imports)

        # Extract aliases (treated as functions for simplicity)
        self._extract_aliases(root_node, byte_content, declarations)

        return self._create_parse_result(declarations, imports)

    def _extract_functions(self, node: Node, byte_content: bytes, declarations: List[Declaration]):
        """Extract function declarations from the AST."""
        if node.type == "function_definition":
            # Find the function name
            for child in node.children:
                if child.type == "word":
                    func_name = byte_content[child.start_byte : child.end_byte].decode(
                        "utf8", errors="replace"
                    )
                    declarations.append(
                        Declaration(
                            kind="function",
                            name=func_name,
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                        )
                    )
                    break

        # Recursively check children
        for child in node.children:
            self._extract_functions(child, byte_content, declarations)

    def _extract_variables(self, node: Node, byte_content: bytes, declarations: List[Declaration]):
        """Extract variable declarations from the AST."""
        if node.type == "variable_assignment":
            # Find the variable name
            for child in node.children:
                if child.type == "variable_name":
                    var_name = byte_content[child.start_byte : child.end_byte].decode(
                        "utf8", errors="replace"
                    )
                    declarations.append(
                        Declaration(
                            kind="variable",
                            name=var_name,
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                        )
                    )
                    break
        elif node.type == "declaration_command":
            # Handle export, local, readonly, etc.
            for child in node.children:
                if child.type == "variable_assignment":
                    self._extract_variables(child, byte_content, declarations)

        # Recursively check children
        for child in node.children:
            self._extract_variables(child, byte_content, declarations)

    def _extract_imports(self, node: Node, byte_content: bytes, imports: List[str]):
        """Extract source/include statements from the AST."""
        if node.type == "command":
            # Check if it's a source or . command
            cmd_name = None
            cmd_arg = None

            for child in node.children:
                if child.type == "command_name":
                    for subchild in child.children:
                        if subchild.type == "word":
                            cmd_name = byte_content[subchild.start_byte : subchild.end_byte].decode(
                                "utf8", errors="replace"
                            )
                            break
                elif cmd_name in ["source", "."] and child.type in [
                    "word",
                    "string",
                    "raw_string",
                    "concatenation",
                ]:
                    # Extract the sourced file path
                    cmd_arg = byte_content[child.start_byte : child.end_byte].decode(
                        "utf8", errors="replace"
                    )
                    # Remove quotes if present
                    cmd_arg = cmd_arg.strip("\"'")
                    imports.append(cmd_arg)
                    break

        # Recursively check children
        for child in node.children:
            self._extract_imports(child, byte_content, imports)

    def _extract_aliases(self, node: Node, byte_content: bytes, declarations: List[Declaration]):
        """Extract alias declarations from the AST."""
        if node.type == "command":
            # Check if it's an alias command
            is_alias = False

            for child in node.children:
                if child.type == "command_name":
                    for subchild in child.children:
                        if subchild.type == "word":
                            cmd_name = byte_content[subchild.start_byte : subchild.end_byte].decode(
                                "utf8", errors="replace"
                            )
                            if cmd_name == "alias":
                                is_alias = True
                            break
                elif is_alias and child.type in ["word", "concatenation"]:
                    # Extract alias definition
                    alias_def = byte_content[child.start_byte : child.end_byte].decode(
                        "utf8", errors="replace"
                    )
                    # Try to parse alias name from definition (format: name=value)
                    if "=" in alias_def:
                        alias_name = alias_def.split("=")[0].strip()
                        declarations.append(
                            Declaration(
                                kind="alias",
                                name=alias_name,
                                start_line=node.start_point[0] + 1,
                                end_line=node.end_point[0] + 1,
                            )
                        )
                    break

        # Recursively check children
        for child in node.children:
            self._extract_aliases(child, byte_content, declarations)

    def _create_parse_result(self, declarations: List[Declaration], imports: List[str]) -> Any:
        """Create a parse result object."""
        from ...base_types import ParseResult

        return ParseResult(
            declarations=declarations, imports=imports, error=None, engine_used="tree-sitter"
        )
