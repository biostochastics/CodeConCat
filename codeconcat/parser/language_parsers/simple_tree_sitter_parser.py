"""
Simplified tree-sitter parser that directly examines AST nodes
instead of using complex queries.
"""

import logging

from tree_sitter import Node

from ...base_types import Declaration
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)


class SimpleTreeSitterParser(BaseTreeSitterParser):
    """Simplified tree-sitter parser that directly walks the AST."""

    def __init__(self, language_name: str, node_types: dict[str, list[str]]):
        """Initialize with language and node type mappings.

        Args:
            language_name: Name of the programming language
            node_types: Dictionary mapping declaration types to node type names
                e.g., {"function": ["function_declaration", "method_declaration"]}
        """
        super().__init__(language_name=language_name)
        self.node_types = node_types

    def get_queries(self) -> dict[str, str]:
        """Return empty queries as we don't use them in simple mode."""
        return {}

    def _extract_node_name(self, node: Node, byte_content: bytes) -> str | None:
        """Extract the name from a declaration node."""
        # Common patterns for finding names in AST nodes
        for child in node.named_children:
            if "identifier" in child.type or "name" in child.type:
                return byte_content[child.start_byte : child.end_byte].decode(
                    "utf8", errors="replace"
                )
        return None

    def _extract_imports(self, node: Node, byte_content: bytes, imports: set[str]):
        """Extract import statements from the AST."""
        if "import" in node.type:
            # Extract the import path/module
            for child in node.named_children:
                if "string" in child.type or "identifier" in child.type:
                    import_text = byte_content[child.start_byte : child.end_byte].decode(
                        "utf8", errors="replace"
                    )
                    # Clean up quotes if present
                    import_text = import_text.strip("\"'`")
                    imports.add(import_text)
                    break

        # Recursively check children
        for child in node.children:
            self._extract_imports(child, byte_content, imports)

    def _extract_declarations(
        self, node: Node, byte_content: bytes, declarations: list[Declaration], depth: int = 0
    ):
        """Recursively extract declarations from the AST."""
        # Check if this node matches any of our declaration types
        for decl_type, node_type_list in self.node_types.items():
            if node.type in node_type_list:
                name = self._extract_node_name(node, byte_content)
                if name:
                    declarations.append(
                        Declaration(
                            kind=decl_type,
                            name=name,
                            start_line=node.start_point[0] + 1,
                            end_line=node.end_point[0] + 1,
                        )
                    )
                # Don't recurse into declaration bodies
                return

        # Recursively check children
        for child in node.named_children:
            self._extract_declarations(child, byte_content, declarations, depth + 1)

    def parse(self, content: str, _file_path: str):
        """Parse content and extract declarations."""
        byte_content = content.encode("utf8")

        # Parse with tree-sitter
        tree = self.parser.parse(byte_content)
        root_node = tree.root_node

        # Extract imports and declarations by walking the tree
        imports: set[str] = set()
        declarations: list[Declaration] = []

        self._extract_imports(root_node, byte_content, imports)
        self._extract_declarations(root_node, byte_content, declarations)

        # Sort results
        declarations.sort(key=lambda d: d.start_line)
        sorted_imports = sorted(imports)

        from ...base_types import ParseResult

        return ParseResult(
            declarations=declarations,
            imports=sorted_imports,
            error=None if not root_node.has_error else "Parse error detected",
            engine_used="tree_sitter",
            parser_quality="full" if not root_node.has_error else "partial",
            missed_features=[] if not root_node.has_error else ["error_recovery"],
        )
