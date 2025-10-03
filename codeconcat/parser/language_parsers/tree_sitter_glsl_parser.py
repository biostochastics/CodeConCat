# file: codeconcat/parser/language_parsers/tree_sitter_glsl_parser.py

"""
Enhanced GLSL parser using tree-sitter.

Extracts declarations, uniforms, and GLSL-specific constructs using the
official tree-sitter-grammars/tree-sitter-glsl grammar.

Supports GLSL ES and Desktop GLSL with features including:
- Uniforms, attributes, varyings, in/out variables
- Texture samplers and image types
- Uniform and shader storage blocks
- Layout qualifiers and bindings
- Vertex, fragment, geometry, and compute shader support
- Preprocessor directives (#define, #version, #extension)
- Built-in variables and functions
- GLSL documentation comments
"""

import logging
from typing import Dict, List, Optional, Set

from tree_sitter import Node

from ...base_types import Declaration, ParseResult
from ...errors import LanguageParserError

# QueryCursor was removed in tree-sitter 0.24.0 - import it if available for backward compatibility
try:
    from tree_sitter import QueryCursor
except ImportError:
    QueryCursor = None  # type: ignore[assignment,misc]

from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Simpler approach: Use direct tree traversal instead of complex queries for keyword nodes
# Tree-sitter queries for GLSL syntax
GLSL_QUERIES = {
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


class TreeSitterGlslParser(BaseTreeSitterParser):
    """GLSL parser using tree-sitter.

    This parser extracts GLSL-specific constructs including uniforms, samplers,
    in/out variables, and compute shader specifications.

    Attributes:
        language_name: Set to "glsl"
        shader_stage: Detected shader stage (vertex/fragment/geometry/compute)
        _uniforms: Cached uniform variables
        _io_variables: Cached input/output variables
        _samplers: Cached sampler and image declarations
    """

    def __init__(self):
        """Initialize the GLSL parser."""
        # Try to use the new tree-sitter-glsl package
        try:
            from tree_sitter_glsl import language

            self._language = language()
            super().__init__("glsl")
        except ImportError:
            # Fall back to base initialization
            super().__init__("glsl")

        self.shader_stage: Optional[str] = None
        self._uniforms: List[Declaration] = []
        self._io_variables: List[Declaration] = []
        self._samplers: List[Declaration] = []
        self._buffers: List[Declaration] = []

    def get_queries(self) -> Dict[str, str]:
        """Returns Tree-sitter queries for GLSL.

        Returns:
            Dictionary of query names to query strings
        """
        return GLSL_QUERIES

    def _load_language(self):
        """Load the GLSL language grammar.

        Returns:
            The loaded GLSL language object.

        Raises:
            LanguageParserError: If the language cannot be loaded.
        """
        # Try to use the standalone tree-sitter-glsl package
        try:
            import tree_sitter_glsl
            from tree_sitter import Language

            # Get the language pointer and create a Language object
            lang_ptr = tree_sitter_glsl.language()
            return Language(lang_ptr)
        except ImportError:
            pass

        # Fall back to tree_sitter_languages if available
        try:
            from tree_sitter_languages import get_language

            return get_language("glsl")
        except ImportError:
            raise LanguageParserError(
                "Failed to load GLSL language. Install tree-sitter-glsl package."
            ) from None

    def parse(self, source_code: str, file_path: str = "unknown") -> ParseResult:  # noqa: ARG002
        """Parse GLSL source code and extract declarations.

        Args:
            source_code: The GLSL source code to parse.
            file_path: The path to the source file.

        Returns:
            ParseResult containing declarations and imports.
        """
        # Parse the source code
        tree = self.parser.parse(bytes(source_code, "utf8"))
        root_node = tree.root_node

        # Reset caches
        self._uniforms = []
        self._io_variables = []
        self._samplers = []
        self._buffers = []

        # Extract all declarations
        declarations: List[Declaration] = []
        imports: List[str] = []

        # Shared processed_nodes set to avoid duplicates across all extractions
        processed_nodes: Set = set()

        # Extract uniforms
        self._extract_uniforms(root_node, source_code, declarations, processed_nodes)

        # Extract I/O variables
        self._extract_io_variables(root_node, source_code, declarations, processed_nodes)

        # Extract samplers and images
        self._extract_samplers(root_node, source_code, declarations)

        # Extract buffers (SSBOs)
        self._extract_buffers(root_node, source_code, declarations, processed_nodes)

        # Extract functions
        self._extract_functions(root_node, source_code, declarations)

        # Extract structs
        self._extract_structs(root_node, source_code, declarations)

        # Extract preprocessor directives
        self._extract_preprocessor(root_node, source_code, imports)

        # Detect shader stage
        self._detect_shader_stage(source_code)

        return ParseResult(declarations=declarations, imports=imports)

    def _extract_uniforms(
        self,
        root_node: Node,
        source_code: str,
        declarations: List[Declaration],
        processed_nodes: Set,
    ) -> None:
        """Extract uniform variables from declarations."""
        self._traverse_declarations(
            root_node, source_code, declarations, "uniform", "uniform", processed_nodes
        )

    def _extract_io_variables(
        self,
        root_node: Node,
        source_code: str,
        declarations: List[Declaration],
        processed_nodes: Set,
    ) -> None:
        """Extract input/output variables."""
        self._traverse_declarations(
            root_node, source_code, declarations, "in", "in_variable", processed_nodes
        )
        self._traverse_declarations(
            root_node, source_code, declarations, "out", "out_variable", processed_nodes
        )

    def _extract_samplers(
        self, root_node: Node, source_code: str, declarations: List[Declaration]
    ) -> None:
        """Extract sampler and image declarations."""
        # Samplers are typically uniform declarations with sampler/image types
        # We'll extract them during uniform traversal and reclassify based on type
        pass  # Handled in traverse_declarations

    def _extract_buffers(
        self,
        root_node: Node,
        source_code: str,
        declarations: List[Declaration],
        processed_nodes: Set,
    ) -> None:
        """Extract shader storage buffer objects (SSBOs)."""
        self._traverse_declarations(
            root_node, source_code, declarations, "buffer", "storage_buffer", processed_nodes
        )

    def _traverse_declarations(
        self,
        node: Node,
        source_code: str,
        declarations: List[Declaration],
        keyword: str,
        kind: str,
        processed_nodes: Optional[Set] = None,
    ) -> None:
        """Recursively traverse the tree to find declarations with a specific keyword.

        Args:
            node: Current AST node
            source_code: Source code string
            declarations: List to append declarations to
            keyword: Keyword to look for (uniform, in, out, buffer)
            kind: Declaration kind to use
            processed_nodes: Set of processed node ranges to avoid duplicates
        """
        if processed_nodes is None:
            processed_nodes = set()

        if node.type == "declaration":
            # Create node key for duplicate detection
            node_key = (node.start_byte, node.end_byte)

            if node_key in processed_nodes:
                return

            # Check if this declaration has the keyword we're looking for
            has_keyword = False
            identifier_name = None
            type_name = None
            has_field_declaration_list = False
            block_name = None

            for child in node.children:
                if child.type == keyword and not child.is_named:
                    has_keyword = True
                # Use helper to extract identifier from various node types
                elif child.type in ("identifier", "array_declarator", "init_declarator"):
                    extracted = self._extract_identifier_from_node(child, source_code)
                    if extracted and not identifier_name:
                        identifier_name = extracted
                # Use helper to extract type
                elif child.type in ("type_identifier", "primitive_type", "template_type"):
                    extracted_type = self._extract_type_from_node(child, source_code)
                    if extracted_type and not type_name:
                        type_name = extracted_type
                # Check for block declarations (uniform blocks, buffer blocks)
                elif child.type == "field_declaration_list":
                    has_field_declaration_list = True

            # Special handling for block declarations (uniform X { ... } instance;)
            if has_keyword and has_field_declaration_list:
                # Extract block name (type) and instance name
                identifiers = []
                for child in node.children:
                    if child.type == "identifier":
                        identifiers.append(self._get_node_text(child, source_code))

                if len(identifiers) >= 2:
                    block_name = identifiers[0]  # Block type name
                    identifier_name = identifiers[1]  # Instance name
                elif len(identifiers) == 1:
                    # Unnamed block (e.g., uniform LightData { ... };)
                    identifier_name = identifiers[0]

                # Classify as block
                actual_kind = "uniform_block" if keyword == "uniform" else "storage_buffer"

                decl = Declaration(
                    name=identifier_name or block_name or "anonymous_block",
                    kind=actual_kind,
                    signature=self._get_node_text(node, source_code).strip(),
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                )
                declarations.append(decl)
                processed_nodes.add(node_key)  # Mark as processed

            elif has_keyword and identifier_name:
                # Regular declaration (not a block)
                # Check if it's a sampler/image type for reclassification
                actual_kind = kind
                if type_name:
                    if "sampler" in type_name.lower():
                        actual_kind = "sampler"
                    elif "image" in type_name.lower():
                        actual_kind = "image"

                decl = Declaration(
                    name=identifier_name,
                    kind=actual_kind,
                    signature=self._get_node_text(node, source_code).strip(),
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                )
                declarations.append(decl)
                processed_nodes.add(node_key)  # Mark as processed

                if kind == "uniform":
                    self._uniforms.append(decl)
                elif kind == "in_variable" or kind == "out_variable":
                    self._io_variables.append(decl)
                elif kind == "storage_buffer":
                    self._buffers.append(decl)

        # Recurse into children, passing processed_nodes set
        for child in node.children:
            self._traverse_declarations(
                child, source_code, declarations, keyword, kind, processed_nodes
            )

    def _extract_functions(
        self, root_node: Node, source_code: str, declarations: List[Declaration]
    ) -> None:
        """Extract function definitions and declarations."""
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
                # Handle both old and new API formats
                if hasattr(match, "captures"):
                    captures_dict = {name: node for node, name in match.captures}
                elif isinstance(match, tuple) and len(match) == 2:
                    pattern_index, captures_dict = match
                else:
                    continue

                # Get function name
                name_nodes = captures_dict.get("name", [])
                if not name_nodes:
                    continue

                name_node = name_nodes[0] if isinstance(name_nodes, list) else name_nodes
                name = self._get_node_text(name_node, source_code)

                # Get the full function node
                func_nodes = captures_dict.get("func_def", [])
                if not func_nodes:
                    continue

                func_node = func_nodes[0] if isinstance(func_nodes, list) else func_nodes

                # Check if this is the main function (entry point)
                kind = "entry_point" if name == "main" else "function"

                decl = Declaration(
                    name=name,
                    kind=kind,
                    signature=self._get_node_text(func_node, source_code).split("{")[0].strip(),
                    start_line=func_node.start_point[0] + 1,
                    end_line=func_node.end_point[0] + 1,
                )
                declarations.append(decl)

        except Exception as e:
            logger.debug(f"Error extracting GLSL functions: {e}")

    def _extract_structs(
        self, root_node: Node, source_code: str, declarations: List[Declaration]
    ) -> None:
        """Extract struct definitions."""
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
                # Handle both old and new API formats
                if hasattr(match, "captures"):
                    captures_dict = {name: node for node, name in match.captures}
                elif isinstance(match, tuple) and len(match) == 2:
                    pattern_index, captures_dict = match
                else:
                    continue

                # Get struct name
                name_nodes = captures_dict.get("name", [])
                if not name_nodes:
                    continue

                name_node = name_nodes[0] if isinstance(name_nodes, list) else name_nodes
                name = self._get_node_text(name_node, source_code)

                # Get the full struct node
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
            logger.debug(f"Error extracting GLSL structs: {e}")

    def _extract_preprocessor(self, root_node: Node, source_code: str, imports: List[str]) -> None:
        """Extract preprocessor directives, particularly #include statements."""

        def traverse(node: Node) -> None:
            if node.type == "preproc_include":
                # Extract the included path from the preprocessor directive
                text = self._get_node_text(node, source_code).strip()
                # Parse #include "path" or #include <path>
                if '"' in text:
                    # #include "path"
                    start = text.index('"') + 1
                    end = text.rindex('"')
                    path = text[start:end]
                    imports.append(path)
                elif "<" in text and ">" in text:
                    # #include <path>
                    start = text.index("<") + 1
                    end = text.rindex(">")
                    path = text[start:end]
                    imports.append(path)

            # Recurse into children
            for child in node.children:
                traverse(child)

        traverse(root_node)

    def _detect_shader_stage(self, source_code: str) -> None:
        """Detect the shader stage from compute layout or heuristics.

        Checks for:
        - layout(local_size_x...) for compute shaders
        - main function with specific output variables for vertex/fragment
        """
        # Check for compute shader layout
        source_lower = source_code.lower()
        if (
            "local_size_x" in source_lower
            or "local_size_y" in source_lower
            or "local_size_z" in source_lower
        ):
            self.shader_stage = "compute"
            return

        # Check for geometry shader keywords
        if "geometry" in source_lower or "emitvertex" in source_lower:
            self.shader_stage = "geometry"
            return

        # Check for gl_FragColor or fragment-specific built-ins
        if "gl_fragcolor" in source_lower or "gl_fragdata" in source_lower:
            self.shader_stage = "fragment"
            return

        # Check for gl_Position (vertex shader)
        if "gl_position" in source_lower:
            self.shader_stage = "vertex"
            return

        self.shader_stage = "unknown"

    def _extract_identifier_from_node(self, node: Node, source_code: str) -> Optional[str]:
        """Recursively extract identifier from node, handling nested structures.

        Handles:
        - identifier nodes directly
        - array_declarator nodes (identifier is nested inside)
        - init_declarator nodes (identifier is nested inside)
        """
        if node.type == "identifier":
            return self._get_node_text(node, source_code)
        elif node.type == "array_declarator":
            # Identifier is first child in array_declarator
            for child in node.children:
                if child.type == "identifier":
                    return self._get_node_text(child, source_code)
        elif node.type == "init_declarator":
            # Identifier is first child in init_declarator
            for child in node.children:
                if child.type == "identifier":
                    return self._get_node_text(child, source_code)
        return None

    def _extract_type_from_node(self, node: Node, source_code: str) -> Optional[str]:
        """Extract type name from various type node structures.

        Handles:
        - type_identifier nodes
        - primitive_type nodes
        - template_type nodes (extracts base type)
        """
        if node.type == "type_identifier" or node.type == "primitive_type":
            return self._get_node_text(node, source_code)
        elif node.type == "template_type":
            # Get the base type identifier
            for child in node.children:
                if child.type == "type_identifier":
                    return self._get_node_text(child, source_code)
        return None

    def _get_node_text(self, node: Node, source_code: str) -> str:
        """Extract text from a node."""
        return source_code[node.start_byte : node.end_byte]
