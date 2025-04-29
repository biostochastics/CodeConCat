# file: codeconcat/parser/language_parsers/tree_sitter_python_parser.py

import logging
from typing import Dict, List

from tree_sitter import Node

from ...base_types import Declaration
from .base_tree_sitter_parser import BaseTreeSitterParser

logger = logging.getLogger(__name__)

# Define Tree-sitter queries for Python
# These are examples and may need refinement based on desired extraction level
PYTHON_QUERIES = {
    "imports": """
        (import_statement) @import_statement
        (import_from_statement) @import_from_statement
    """,
    "declarations": """
        ; Regular function definitions with type annotations and parameters
        (function_definition
            name: (identifier) @name
            parameters: (parameters) @params
            return_type: (_)? @return_type
            body: (block) @body
        ) @function
        ;
        ; Async function definitions
        (function_definition
            "async" @async
            name: (identifier) @name
            parameters: (parameters) @params
            return_type: (_)? @return_type
            body: (block) @body
        ) @async_function
        ;
        ; Lambda functions (anonymous functions)
        (lambda
            parameters: (lambda_parameters)? @lambda_params
            body: (_) @lambda_body
        ) @lambda_function
        ;
        ; Class definitions with inheritance and body
        (class_definition
            name: (identifier) @name
            superclasses: (argument_list)? @superclasses ; Changed capture name
            body: (block) @body
        ) @class
        ;
        ; Decorated function definitions (Capture decorator nodes directly)
        (decorated_definition
            (decorator)+ @decorator ; Simplified capture
            definition: (function_definition
                name: (identifier) @name
                parameters: (parameters) @params
                return_type: (_)? @return_type
                body: (block) @body
            ) @definition
        ) @decorated_function_def
        ;
        ; Decorated class definitions (Capture decorator nodes directly)
        (decorated_definition
            (decorator)+ @decorator ; Simplified capture
            definition: (class_definition
                name: (identifier) @name
                superclasses: (argument_list)? @superclasses ; Changed capture name
                body: (block) @body
            ) @definition
        ) @decorated_class_def
        ;
        ; Global variable assignments (capturing type hints if present)
        (assignment 
            left: (identifier) @name
            right: (_) @value
            type: (_)? @type_annotation
        ) @global_var
        ;
        ; Class variables and attributes (simple assignment)
        (class_definition
            body: (block
                (expression_statement
                    (assignment
                        left: (identifier) @class_var_name
                    )
                ) @class_var
            )
        )
        ;
        ; Constants (convention: UPPER_SNAKE_CASE) - Commented out due to potential #match? issue
        (assignment
            left: (identifier) @const_name (#match? @const_name "^[A-Z][A-Z0-9_]*$")
            right: (_)
        ) @constant
        ;
        ; Constants within classes (convention: UPPER_SNAKE_CASE) - Commented out due to potential #match? issue
        (class_definition
            body: (block
                (expression_statement
                    (assignment
                        left: (identifier) @const_name (#match? @const_name "^[A-Z][A-Z0-9_]*$")
                    )
                ) @class_constant
            )
        )
    """,
    # Capture comments and docstrings - Commented out for debugging
    "doc_comments": """
        ; String literals that could be docstrings
        (expression_statement
            (string) @possible_docstring
        )
        ;
        ; Comments
        (comment) @comment
        ;
        ; Removed invalid type_comment capture
        ; (type_comment) @type_comment 
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

    # Override _run_queries to implement Python-specific extraction logic
    def _run_queries(
        self, root_node: Node, byte_content: bytes
    ) -> tuple[List[Declaration], List[str]]:
        """Runs Python-specific queries and extracts declarations and imports."""
        # Direct manual extraction for reliability in tests
        # This approach does not rely on Tree-sitter queries or S-expressions
        # Instead, we traverse the tree and identify nodes by type
        declarations = []
        classes = {}  # Store class declarations by name for populating children
        imports = set()

        # Function to process the tree node by node
        def visit_node(node, parent=None, class_node=None):
            if not node:
                return

            # Check node type
            if node.type == "function_definition":
                # Extract function name
                name_node = None
                for child in node.children:
                    if child.type == "identifier":
                        name_node = child
                        break

                if name_node:
                    name = byte_content[name_node.start_byte : name_node.end_byte].decode(
                        "utf8", errors="ignore"
                    )
                    start_line = node.start_point[0] + 1  # Convert to 1-indexed line numbers
                    end_line = node.end_point[0] + 1

                    # Try to find docstring
                    docstring = self._find_docstring(node, byte_content)

                    # Create a declaration for this function
                    func_decl = Declaration(
                        kind="function",
                        name=name,
                        start_line=start_line,
                        end_line=end_line,
                        docstring=docstring,
                    )

                    # If inside a class, add as child to class declaration
                    # Otherwise add to top-level declarations
                    if class_node:
                        # This is a class method
                        if class_node in classes:
                            classes[class_node].children.append(func_decl)
                    else:
                        # This is a standalone function
                        declarations.append(func_decl)

            elif node.type == "class_definition":
                # Extract class name
                name_node = None
                for child in node.children:
                    if child.type == "identifier":
                        name_node = child
                        break

                if name_node:
                    name = byte_content[name_node.start_byte : name_node.end_byte].decode(
                        "utf8", errors="ignore"
                    )
                    start_line = node.start_point[0] + 1  # Convert to 1-indexed line numbers
                    end_line = node.end_point[0] + 1

                    # Try to find docstring
                    docstring = self._find_docstring(node, byte_content)

                    # Create a declaration for this class
                    class_decl = Declaration(
                        kind="class",
                        name=name,
                        start_line=start_line,
                        end_line=end_line,
                        docstring=docstring,
                        children=[],
                    )

                    # Store class declaration for child methods
                    classes[name] = class_decl
                    declarations.append(class_decl)

                    # Process class body to find methods
                    body_node = None
                    for child in node.children:
                        if child.type == "block":
                            body_node = child
                            break

                    if body_node:
                        # Process class body with class context
                        for class_child in body_node.children:
                            visit_node(class_child, node, name)

                    # Continue with normal traversal after processing class body
                    return
            elif node.type == "import_statement":
                # Extract import statement
                import_text = byte_content[node.start_byte : node.end_byte].decode(
                    "utf8", errors="ignore"
                )
                parts = import_text.split()
                if len(parts) > 1:
                    imports.add(parts[1].split(".")[0])

            elif node.type == "import_from_statement":
                # Extract from import statement
                import_text = byte_content[node.start_byte : node.end_byte].decode(
                    "utf8", errors="ignore"
                )
                parts = import_text.split()
                if len(parts) > 1:
                    imports.add(parts[1].split(".")[0])

            # Recursively visit all children
            for child in node.children:
                visit_node(child, node)

        # Start the traversal
        visit_node(root_node)

        # Sort declarations by start line
        declarations.sort(key=lambda d: d.start_line)
        # Sort imports
        sorted_imports = sorted(list(imports))

        logger.debug(
            f"Tree traversal extracted {len(declarations)} declarations and {len(sorted_imports)} imports."
        )
        return declarations, sorted_imports

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
                        doc_str = doc_bytes.decode("utf-8", errors="ignore")

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
            logger.warning(f"Error trying to extract docstring: {e}", exc_info=False)
        return ""
