# file: codeconcat/parser/language_parsers/tree_sitter_hlsl_parser.py

"""
HLSL parser using tree-sitter with direct tree traversal.

Supports HLSL shader constructs including:
- Constant buffers (cbuffer/tbuffer)
- Textures and samplers
- Structured buffers
- Functions and structs
- Semantics and register bindings
"""

import logging
from typing import Dict, List, Optional

from tree_sitter import Node

from ...base_types import Declaration, ParseResult
from ...errors import LanguageParserError

try:
    from tree_sitter import QueryCursor
except ImportError:
    QueryCursor = None

from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Simple queries for functions and structs
HLSL_QUERIES = {
    "functions": """
        (function_definition
            (function_declarator
                (identifier) @name
            )
        ) @func_def
    """,
    "structs": """
        (struct_specifier
            (type_identifier) @name
        ) @struct_def
    """,
}


class TreeSitterHlslParser(BaseTreeSitterParser):
    """HLSL parser using tree-sitter."""

    def __init__(self):
        """Initialize the HLSL parser."""
        super().__init__("hlsl")
        self.shader_stage: Optional[str] = None

    def get_queries(self) -> Dict[str, str]:
        """Returns Tree-sitter queries for HLSL."""
        return HLSL_QUERIES

    def _load_language(self):
        """Load the HLSL language grammar."""
        try:
            import tree_sitter_hlsl
            from tree_sitter import Language

            lang_ptr = tree_sitter_hlsl.language()
            return Language(lang_ptr)
        except ImportError:
            pass

        try:
            from tree_sitter_languages import get_language

            return get_language("hlsl")
        except ImportError:
            raise LanguageParserError(
                "Failed to load HLSL language. Install tree-sitter-hlsl package."
            ) from None

    def parse(self, source_code: str, file_path: str = "unknown") -> ParseResult:  # noqa: ARG002
        """Parse HLSL source code and extract declarations."""
        tree = self.parser.parse(bytes(source_code, "utf8"))
        root_node = tree.root_node

        declarations: List[Declaration] = []
        imports: List[str] = []

        # Extract declarations using tree traversal
        self._traverse_hlsl_declarations(root_node, source_code, declarations)

        # Extract functions and structs using queries
        self._extract_functions(root_node, source_code, declarations)
        self._extract_structs(root_node, source_code, declarations)

        return ParseResult(declarations=declarations, imports=imports)

    def _traverse_hlsl_declarations(
        self, node: Node, source_code: str, declarations: List[Declaration]
    ) -> None:
        """Traverse tree to find HLSL-specific declarations."""
        if node.type == "type_definition":
            # Handle typedef declarations
            type_identifiers = []
            for child in node.children:
                if child.type == "type_identifier":
                    type_identifiers.append(self._get_node_text(child, source_code))

            # The last type_identifier is the typedef name
            if type_identifiers:
                typedef_name = type_identifiers[-1]
                decl = Declaration(
                    name=typedef_name,
                    kind="typedef",
                    signature=self._get_node_text(node, source_code).strip(),
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                )
                declarations.append(decl)

        elif node.type == "declaration":
            type_name = None
            identifier_name = None
            has_storage_qualifier = False
            is_const = False
            is_groupshared = False

            for child in node.children:
                if child.type == "type_identifier":
                    type_name = self._get_node_text(child, source_code)
                elif child.type == "template_type":
                    # Extract type from template_type node (e.g., RWTexture2D<float4>)
                    for template_child in child.children:
                        if template_child.type == "type_identifier":
                            type_name = self._get_node_text(template_child, source_code)
                            break
                elif child.type == "identifier":
                    identifier_name = self._get_node_text(child, source_code)
                elif child.type == "primitive_type":
                    # Handle primitive types (float, int, etc.)
                    type_name = self._get_node_text(child, source_code)
                elif child.type == "init_declarator":
                    # Extract identifier from init_declarator (e.g., PI = 3.14)
                    for init_child in child.children:
                        if init_child.type == "identifier":
                            identifier_name = self._get_node_text(init_child, source_code)
                            break
                elif child.type == "array_declarator":
                    # Extract identifier from array_declarator (e.g., data[256])
                    for array_child in child.children:
                        if array_child.type == "identifier":
                            identifier_name = self._get_node_text(array_child, source_code)
                            break
                elif child.type == "storage_class_specifier":
                    has_storage_qualifier = True
                elif child.type == "type_qualifier":
                    is_const = "const" in self._get_node_text(child, source_code).lower()
                elif child.type == "qualifiers":
                    qualifier_text = self._get_node_text(child, source_code).lower()
                    is_groupshared = "groupshared" in qualifier_text

            if type_name and identifier_name:
                # Classify based on type or storage qualifiers
                kind = self._classify_hlsl_type(type_name)

                # If no specific type classification, check for global variables
                if not kind:
                    if has_storage_qualifier and is_const:
                        kind = "global_constant"
                    elif is_groupshared:
                        kind = "global_shared"
                    else:
                        # Generic global variable
                        kind = "global_variable"

                if kind:
                    decl = Declaration(
                        name=identifier_name,
                        kind=kind,
                        signature=self._get_node_text(node, source_code).strip(),
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                    )
                    declarations.append(decl)

        # Recurse
        for child in node.children:
            self._traverse_hlsl_declarations(child, source_code, declarations)

    def _classify_hlsl_type(self, type_name: str) -> Optional[str]:
        """Classify HLSL type into declaration kind."""
        type_lower = type_name.lower()

        if type_name == "cbuffer":
            return "cbuffer"
        elif type_name == "tbuffer":
            return "tbuffer"
        elif "rwtexture" in type_lower:
            # Check RW textures before regular textures
            return "rw_texture"
        elif "texture" in type_lower:
            return "texture"
        elif "sampler" in type_lower:
            return "sampler"
        elif "buffer" in type_lower:
            return "buffer"
        else:
            return None

    def _extract_functions(
        self, root_node: Node, source_code: str, declarations: List[Declaration]
    ) -> None:
        """Extract function definitions using queries."""
        query = self._get_compiled_query("functions")
        if not query:
            return

        try:
            if QueryCursor is not None:
                cursor = QueryCursor(query)
                matches = cursor.matches(root_node)
            else:
                matches = query.matches(root_node)

            for match in matches:
                if hasattr(match, "captures"):
                    captures_dict = {name: node for node, name in match.captures}
                elif isinstance(match, tuple) and len(match) == 2:
                    _, captures_dict = match
                else:
                    continue

                name_nodes = captures_dict.get("name", [])
                if not name_nodes:
                    continue

                name_node = name_nodes[0] if isinstance(name_nodes, list) else name_nodes
                name = self._get_node_text(name_node, source_code)

                func_nodes = captures_dict.get("func_def", [])
                if not func_nodes:
                    continue

                func_node = func_nodes[0] if isinstance(func_nodes, list) else func_nodes

                # Detect shader stage by function name conventions
                kind = "function"
                if name.endswith("Main") or name.lower() in ["vsmain", "psmain", "csmain"]:
                    kind = self._detect_shader_stage_from_name(name)

                    # Set shader_stage based on entry point kind
                    if kind == "compute_entry_point" and not self.shader_stage:
                        self.shader_stage = "compute"
                    elif kind == "vertex_entry_point" and not self.shader_stage:
                        self.shader_stage = "vertex"
                    elif kind == "pixel_entry_point" and not self.shader_stage:
                        self.shader_stage = "pixel"

                decl = Declaration(
                    name=name,
                    kind=kind,
                    signature=self._get_node_text(func_node, source_code).split("{")[0].strip(),
                    start_line=func_node.start_point[0] + 1,
                    end_line=func_node.end_point[0] + 1,
                )
                declarations.append(decl)

        except Exception as e:
            logger.debug(f"Error extracting HLSL functions: {e}")

    def _extract_structs(
        self, root_node: Node, source_code: str, declarations: List[Declaration]
    ) -> None:
        """Extract struct definitions using queries."""
        query = self._get_compiled_query("structs")
        if not query:
            return

        try:
            if QueryCursor is not None:
                cursor = QueryCursor(query)
                matches = cursor.matches(root_node)
            else:
                matches = query.matches(root_node)

            for match in matches:
                if hasattr(match, "captures"):
                    captures_dict = {name: node for node, name in match.captures}
                elif isinstance(match, tuple) and len(match) == 2:
                    _, captures_dict = match
                else:
                    continue

                name_nodes = captures_dict.get("name", [])
                if not name_nodes:
                    continue

                name_node = name_nodes[0] if isinstance(name_nodes, list) else name_nodes
                name = self._get_node_text(name_node, source_code)

                struct_nodes = captures_dict.get("struct_def", [])
                if not struct_nodes:
                    continue

                struct_node = struct_nodes[0] if isinstance(struct_nodes, list) else struct_nodes

                decl = Declaration(
                    name=name,
                    kind="struct",
                    signature=self._get_node_text(struct_node, source_code).split("{")[0]
                    + " { ... }",
                    start_line=struct_node.start_point[0] + 1,
                    end_line=struct_node.end_point[0] + 1,
                )
                declarations.append(decl)

        except Exception as e:
            logger.debug(f"Error extracting HLSL structs: {e}")

    def _detect_shader_stage_from_name(self, name: str) -> str:
        """Detect shader stage from function name."""
        name_lower = name.lower()
        if "vs" in name_lower or "vertex" in name_lower:
            return "vertex_entry_point"
        elif "ps" in name_lower or "pixel" in name_lower:
            return "pixel_entry_point"
        elif "cs" in name_lower or "compute" in name_lower:
            return "compute_entry_point"
        else:
            return "function"

    def _get_node_text(self, node: Node, source_code: str) -> str:
        """Extract text from a node."""
        return source_code[node.start_byte : node.end_byte]
