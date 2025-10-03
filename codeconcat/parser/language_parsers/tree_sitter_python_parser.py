# file: codeconcat/parser/language_parsers/tree_sitter_python_parser.py

import logging
from typing import Dict, List

from tree_sitter import Node

# QueryCursor was removed in tree-sitter 0.24.0 - import it if available for backward compatibility
try:
    from tree_sitter import QueryCursor
except ImportError:
    QueryCursor = None  # type: ignore[assignment,misc]

from ...base_types import Declaration
from ..doc_comment_utils import normalize_whitespace
from ..utils import get_node_location
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Enhanced Tree-sitter queries for Python with comprehensive coverage
PYTHON_QUERIES = {
    "imports": """
        ; Standard import statements
        (import_statement
            name: (dotted_name) @import_name
        ) @import_statement

        ; Import from statements
        (import_from_statement
            module_name: (dotted_name)? @module_name
            name: [(dotted_name) (aliased_import) (wildcard_import)] @import_name
        ) @import_from_statement
    """,
    "declarations": """
        ; Function definitions (including async)
        (function_definition
            "async"? @async_modifier
            name: (identifier) @name
            parameters: (parameters) @params
            return_type: (type)? @return_type
            body: (block) @body
        ) @function

        ; Class definitions
        (class_definition
            name: (identifier) @name
            superclasses: (argument_list)? @superclasses
            body: (block) @body
        ) @class

        ; Decorated definitions (functions and classes)
        (decorated_definition
            (decorator)+ @decorators
            definition: [
                (function_definition
                    "async"? @async_modifier
                    name: (identifier) @name
                    parameters: (parameters) @params
                    return_type: (type)? @return_type
                    body: (block) @body
                ) @function_def
                (class_definition
                    name: (identifier) @name
                    superclasses: (argument_list)? @superclasses
                    body: (block) @body
                ) @class_def
            ]
        ) @decorated_definition

        ; Global variable assignments with type annotations
        (assignment
            left: (identifier) @name
            type: (type)? @type_annotation
            right: (_) @value
        ) @assignment

        ; Note: annotated_assignment node type doesn't exist in current grammar
        ; Type annotations are handled by the assignment query above

        ; Constants (UPPER_CASE convention)
        (assignment
            left: (identifier) @const_name
            right: (_) @const_value
        ) @constant (#match? @const_name "^[A-Z][A-Z0-9_]*$")

        ; Property definitions using @property decorator
        (decorated_definition
            (decorator
                (identifier) @decorator_name
                (#eq? @decorator_name "property")
            )
            definition: (function_definition
                name: (identifier) @property_name
            )
        ) @property
    """,
    "doc_comments": """
        ; Docstring detection - first string in function/class body
        [
            (function_definition body: (block (expression_statement (string) @docstring)))
            (class_definition body: (block (expression_statement (string) @docstring)))
        ]

        ; Comments
        (comment) @comment
    """,
}


class TreeSitterPythonParser(BaseTreeSitterParser):
    """Tree-sitter based parser for Python language."""

    def __init__(self):
        """Initializes the Python Tree-sitter parser."""
        super().__init__(language_name="python")

    def get_queries(self) -> Dict[str, str]:
        """Returns the predefined Tree-sitter queries for Python."""
        return PYTHON_QUERIES

    def _run_queries(
        self, root_node: Node, byte_content: bytes
    ) -> tuple[List[Declaration], List[str]]:
        """Runs Python-specific queries and extracts declarations and imports."""
        declarations = []
        imports = set()
        docstring_map = {}  # node_id -> docstring

        # --- Pass 1: Extract Docstrings --- #
        try:
            doc_query = self._get_compiled_query("doc_comments")
            if doc_query:
                cursor = QueryCursor(doc_query)
                doc_captures = cursor.captures(root_node)
                # doc_captures is a dict: {capture_name: [list of nodes]}
                for capture_name, nodes in doc_captures.items():
                    if capture_name == "docstring":
                        for node in nodes:
                            # Find the parent function or class
                            parent = node.parent
                            while parent and parent.type not in [
                                "function_definition",
                                "class_definition",
                                "decorated_definition",
                            ]:
                                parent = parent.parent

                            if parent:
                                docstring_text = byte_content[
                                    node.start_byte : node.end_byte
                                ].decode("utf-8", errors="replace")
                                # Clean docstring (remove quotes)
                                cleaned_docstring = self._clean_docstring(docstring_text)
                                docstring_map[parent.id] = cleaned_docstring
        except Exception as e:
            logger.warning(f"Failed to extract Python docstrings: {e}", exc_info=True)

        # --- Pass 2: Extract Imports --- #
        try:
            import_query = self._get_compiled_query("imports")
            if import_query:
                cursor = QueryCursor(import_query)
                import_captures = cursor.captures(root_node)
                # import_captures is a dict: {capture_name: [list of nodes]}
                for capture_name, nodes in import_captures.items():
                    if capture_name in ["import_name", "module_name"]:
                        for node in nodes:
                            import_text = byte_content[node.start_byte : node.end_byte].decode(
                                "utf-8", errors="replace"
                            )
                            # Extract base module name
                            base_module = import_text.split(".")[0]
                            imports.add(base_module)
        except Exception as e:
            logger.warning(f"Failed to extract Python imports: {e}", exc_info=True)

        # --- Pass 3: Extract Declarations --- #
        try:
            decl_query = self._get_compiled_query("declarations")
            if decl_query:
                cursor = QueryCursor(decl_query)
                matches = cursor.matches(root_node)

                # matches is a list of tuples: (match_id, dict of capture_name -> nodes)
                for _match_id, captures_dict in matches:
                    # Determine declaration type and extract information
                    declaration_node = None
                    name = None
                    kind = None
                    modifiers = set()

                    # Find the main declaration node and name
                    if "function" in captures_dict:
                        # captures_dict values can be a single node or list of nodes
                        func_val = captures_dict["function"]
                        declaration_node = func_val[0] if isinstance(func_val, list) else func_val
                        kind = "function"
                        name_val = captures_dict.get("name")
                        if name_val:
                            name_node = name_val[0] if isinstance(name_val, list) else name_val
                            name = byte_content[name_node.start_byte : name_node.end_byte].decode(
                                "utf-8", errors="replace"
                            )

                        # Check for async modifier
                        if "async_modifier" in captures_dict and captures_dict["async_modifier"]:
                            modifiers.add("async")

                    elif "class" in captures_dict:
                        class_val = captures_dict["class"]
                        declaration_node = (
                            class_val[0] if isinstance(class_val, list) else class_val
                        )
                        kind = "class"
                        name_val = captures_dict.get("name")
                        if name_val:
                            name_node = name_val[0] if isinstance(name_val, list) else name_val
                            name = byte_content[name_node.start_byte : name_node.end_byte].decode(
                                "utf-8", errors="replace"
                            )

                    elif "decorated_definition" in captures_dict:
                        decor_val = captures_dict["decorated_definition"]
                        declaration_node = (
                            decor_val[0] if isinstance(decor_val, list) else decor_val
                        )
                        # Determine if it's a decorated function or class
                        if "function_def" in captures_dict and captures_dict["function_def"]:
                            kind = "function"
                            modifiers.add("decorated")
                        elif "class_def" in captures_dict and captures_dict["class_def"]:
                            kind = "class"
                            modifiers.add("decorated")

                        name_val = captures_dict.get("name")
                        if name_val:
                            name_node = name_val[0] if isinstance(name_val, list) else name_val
                            name = byte_content[name_node.start_byte : name_node.end_byte].decode(
                                "utf-8", errors="replace"
                            )

                    elif "property" in captures_dict:
                        prop_val = captures_dict["property"]
                        declaration_node = prop_val[0] if isinstance(prop_val, list) else prop_val
                        kind = "property"
                        name_val = captures_dict.get("property_name")
                        if name_val:
                            name_node = name_val[0] if isinstance(name_val, list) else name_val
                            name = byte_content[name_node.start_byte : name_node.end_byte].decode(
                                "utf-8", errors="replace"
                            )
                        modifiers.add("property")

                    elif "assignment" in captures_dict:
                        assign_val = captures_dict.get("assignment")
                        if assign_val:
                            declaration_node = (
                                assign_val[0] if isinstance(assign_val, list) else assign_val
                            )
                            kind = "variable"
                            name_val = captures_dict.get("name")
                            if name_val:
                                name_node = name_val[0] if isinstance(name_val, list) else name_val
                                name = byte_content[
                                    name_node.start_byte : name_node.end_byte
                                ].decode("utf-8", errors="replace")

                    elif "constant" in captures_dict:
                        const_val = captures_dict["constant"]
                        declaration_node = (
                            const_val[0] if isinstance(const_val, list) else const_val
                        )
                        kind = "constant"
                        name_val = captures_dict.get("const_name")
                        if name_val:
                            name_node = name_val[0] if isinstance(name_val, list) else name_val
                            name = byte_content[name_node.start_byte : name_node.end_byte].decode(
                                "utf-8", errors="replace"
                            )
                        modifiers.add("const")

                    if declaration_node and name:
                        start_line, end_line = get_node_location(declaration_node)

                        # Extract signature for functions and methods
                        signature = ""
                        if kind in ["function", "method", "property"]:
                            # Get the signature (name + parameters + return type if present)
                            # We'll extract from the start of the declaration to the colon
                            sig_start = declaration_node.start_byte
                            # Find the colon that ends the signature
                            sig_end_node = None
                            for child in declaration_node.children:
                                if child.type == ":":
                                    sig_end_node = child
                                    break

                            if sig_end_node:
                                sig_end = sig_end_node.end_byte
                                signature = (
                                    byte_content[sig_start:sig_end]
                                    .decode("utf-8", errors="replace")
                                    .strip()
                                )
                                # Clean up the signature - remove 'def' keyword
                                if signature.startswith("def "):
                                    signature = signature[4:].strip()
                                elif signature.startswith("async def "):
                                    signature = signature[10:].strip()

                        # Get docstring
                        docstring = docstring_map.get(declaration_node.id, "")

                        declarations.append(
                            Declaration(
                                kind=kind or "unknown",
                                name=name,
                                start_line=start_line,
                                end_line=end_line,
                                docstring=docstring,
                                signature=signature,
                                modifiers=modifiers,
                            )
                        )

        except Exception as e:
            logger.warning(f"Failed to extract Python declarations: {e}", exc_info=True)

        # Sort declarations by start line
        declarations.sort(key=lambda d: d.start_line)
        sorted_imports = sorted(imports)

        logger.debug(
            f"Tree-sitter Python extracted {len(declarations)} declarations and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports

    def _clean_docstring(self, docstring_text: str) -> str:
        """Clean Python docstring by removing quotes and normalizing whitespace.

        Uses shared doc_comment_utils for consistent whitespace normalization.
        """
        # Remove triple quotes or single quotes
        cleaned = docstring_text.strip()
        for quote in ['"""', "'''", '"', "'"]:
            if cleaned.startswith(quote) and cleaned.endswith(quote):
                cleaned = cleaned[len(quote) : -len(quote)]
                break

        # Normalize whitespace using shared utility
        # Python docstrings should preserve line breaks for readability
        return normalize_whitespace(cleaned, collapse_newlines=False)

    def _find_docstring(self, node: Node, byte_content: bytes) -> str:
        """Attempts to find a docstring within a function/class body node."""
        try:
            # Look for the 'body' node captured by the query (e.g., block)
            body_node = None
            for child in node.children:
                # Heuristic: find the block node which usually contains the body
                # This relies on query structure / TS grammar
                if child.type == "block":
                    body_node = child
                    break

            if body_node and body_node.children:
                first_child = body_node.children[0]
                # Check if the first statement is an expression statement containing a string
                if first_child.type == "expression_statement" and first_child.children:
                    string_node = first_child.children[0]
                    if string_node.type in ["string", "string_content"]:
                        doc_bytes = byte_content[string_node.start_byte : string_node.end_byte]
                        # Remove quotes (triple or single)
                        doc_str = doc_bytes.decode("utf-8", errors="replace")

                        # Handle potential f-strings, raw strings, etc.
                        prefix_chars = ["r", "u", "f", "b"]
                        for prefix in prefix_chars:
                            if doc_str.startswith(prefix):
                                doc_str = doc_str[1:]

                        # Remove quotes
                        for quote in ['"""', "'''", '"', "'"]:
                            if doc_str.startswith(quote) and doc_str.endswith(quote):
                                return doc_str[len(quote) : -len(quote)].strip()
                        return doc_str.strip()  # Fallback if quotes aren't standard
        except Exception as e:
            logger.warning(f"Error trying to extract docstring: {e}", exc_info=True)
        return ""
