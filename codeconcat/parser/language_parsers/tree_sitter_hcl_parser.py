# file: codeconcat/parser/language_parsers/tree_sitter_hcl_parser.py

"""
Enhanced HCL2/Terraform parser using tree-sitter.

Extracts declarations and configuration from HCL2/Terraform files using the
MichaHoffmann/tree-sitter-hcl grammar.

Supports HCL2/Terraform with features including:
- Resource block declarations (aws_instance, google_compute_instance, etc.)
- Module definitions with source/inputs/outputs
- Provider configurations
- Variable, data, output, and locals blocks
- Variable interpolation (${var.name})
- Attribute assignments
"""

import logging
from typing import Dict, List

from codeconcat.base_types import Declaration

from .base_tree_sitter_parser import BaseTreeSitterParser

try:
    from tree_sitter import Node
except ImportError:
    Node = None  # type: ignore

logger = logging.getLogger(__name__)

# Tree-sitter queries for HCL2/Terraform syntax
HCL_QUERIES = {
    "declarations": """
        ; Resource blocks: resource "type" "name" { ... }
        ; Capture only the second string_lit (the resource name)
        (block
            (identifier) @block_type
            (string_lit)
            (string_lit) @name
            (#eq? @block_type "resource")
        ) @function

        ; Module blocks: module "name" { ... }
        (block
            (identifier) @block_type
            (string_lit) @name
            (#eq? @block_type "module")
        ) @module

        ; Provider blocks: provider "name" { ... }
        (block
            (identifier) @block_type
            (string_lit) @name
            (#eq? @block_type "provider")
        ) @class

        ; Variable blocks: variable "name" { ... }
        (block
            (identifier) @block_type
            (string_lit) @name
            (#eq? @block_type "variable")
        ) @property

        ; Data blocks: data "type" "name" { ... }
        ; Capture only the second string_lit (the data resource name)
        (block
            (identifier) @block_type
            (string_lit)
            (string_lit) @name
            (#eq? @block_type "data")
        ) @function

        ; Output blocks: output "name" { ... }
        (block
            (identifier) @block_type
            (string_lit) @name
            (#eq? @block_type "output")
        ) @property

        ; Locals blocks: locals { ... }
        (block
            (identifier) @name
            (#eq? @name "locals")
        ) @object
    """,
    "imports": """
        ; Terraform blocks (terraform { required_providers { ... } })
        (block
            (identifier) @name
            (#eq? @name "terraform")
        ) @import_statement
    """,
}


class TreeSitterHclParser(BaseTreeSitterParser):
    """
    Enhanced HCL2/Terraform parser using tree-sitter.

    Extracts resource blocks, module definitions, provider configurations,
    and other HCL2 constructs from Terraform configuration files.

    Supports Terraform 1.0+ and HCL2 syntax.

    Features:
        - Resource block declarations with type and name
        - Module definitions
        - Provider configurations
        - Variable, data, output, locals blocks
        - Variable interpolation tracking
        - Terraform configuration blocks

    Grammar: https://github.com/MichaHoffmann/tree-sitter-hcl
    Version: 1.2.x

    Complexity:
        - Initialization: O(1)
        - Parsing: O(n) where n is source length
        - Query execution: O(m) where m is match count
    """

    def __init__(self):
        """Initialize the HCL2 parser with the tree-sitter-hcl grammar."""
        super().__init__("hcl")
        logger.debug("TreeSitterHclParser initialized")

    def get_queries(self) -> Dict[str, str]:
        """Returns Tree-sitter query patterns for HCL2/Terraform.

        Returns:
            Dictionary mapping query names to S-expression query strings.
            Keys: 'declarations', 'imports'

        Complexity: O(1) - Returns static dictionary
        """
        return HCL_QUERIES

    def _run_queries(
        self, root_node: "Node", byte_content: bytes
    ) -> tuple[List[Declaration], List[str]]:
        """Runs queries and post-processes HCL-specific name extraction.

        Overrides base class to strip quotes from HCL string_lit nodes,
        since resource/module/provider names are string literals in HCL2.

        Args:
            root_node: The root AST node
            byte_content: The source code as bytes

        Returns:
            Tuple of (declarations list, imports list)
        """
        # Call parent implementation
        declarations, imports = super()._run_queries(root_node, byte_content)

        # Post-process: strip quotes from HCL string literal names
        # HCL blocks use string_lit for names: resource "aws_instance" "web"
        for decl in declarations:
            if decl.name.startswith('"') and decl.name.endswith('"'):
                decl.name = decl.name.strip('"')
            elif decl.name.startswith("'") and decl.name.endswith("'"):
                decl.name = decl.name.strip("'")

        return declarations, imports
