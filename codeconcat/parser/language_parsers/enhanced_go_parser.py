# file: codeconcat/parser/language_parsers/enhanced_go_parser.py

"""
Enhanced Go parser for CodeConcat.

This module provides an improved Go parser using the EnhancedBaseParser
with Go-specific patterns and functionality.
"""

import logging
import re
from typing import Dict, List, Set, Tuple

from codeconcat.base_types import Declaration, ParseResult
from codeconcat.parser.language_parsers.enhanced_base_parser import EnhancedBaseParser

logger = logging.getLogger(__name__)


class EnhancedGoParser(EnhancedBaseParser):
    """Go language parser using improved regex patterns and shared functionality."""

    def __init__(self):
        """Initialize the enhanced Go parser."""
        super().__init__()
        self.language = "go"
        self._setup_go_patterns()

    def _setup_standard_patterns(self):
        """Setup standard patterns for Go."""
        super()._setup_standard_patterns()

        # Go specific comment patterns
        self.line_comment = "//"
        self.block_comment_start = "/*"
        self.block_comment_end = "*/"

        # Go uses braces for blocks
        self.block_start = "{"
        self.block_end = "}"

        # Initialize patterns dict (will be populated in _setup_go_patterns)
        self.patterns = {}

        # Initialize recognized Go modifiers
        self.modifiers = {
            "func",
            "type",
            "struct",
            "interface",
            "const",
            "var",
            "package",
            "import",
            "map",
            "chan",
            "defer",
            "go",
            "select",
            "export",
            "public",
            "private",
        }

    def _setup_go_patterns(self):
        """Setup Go-specific patterns."""
        # Function declarations
        self.patterns["function"] = re.compile(
            r"^\s*func\s+(?:\([^)]*\)\s+)?(?P<name>\w+)\s*\([^)]*\)", re.MULTILINE
        )

        # Method declarations (with receiver)
        self.patterns["method"] = re.compile(
            r"^\s*func\s+\(\s*\w+\s+\*?\s*\w+\s*\)\s+(?P<name>\w+)\s*\(", re.MULTILINE
        )

        # Struct declarations
        self.patterns["struct"] = re.compile(
            r"^\s*type\s+(?P<name>\w+)\s+struct\s*\{", re.MULTILINE
        )

        # Interface declarations
        self.patterns["interface"] = re.compile(
            r"^\s*type\s+(?P<name>\w+)\s+interface\s*\{", re.MULTILINE
        )

        # Type declarations (non-struct/interface)
        self.patterns["type"] = re.compile(
            r"^\s*type\s+(?P<name>\w+)\s+(?!struct|interface)\w+", re.MULTILINE
        )

        # Constant declarations
        self.patterns["const"] = re.compile(
            r"^\s*(?:const|var)\s+(?P<name>\w+)(?:\s+[\w\[\]{}*<>.]+)?\s*=", re.MULTILINE
        )

        # Import declarations
        self.patterns["import"] = re.compile(r"^\s*import\s+(?:\"([^\"]+)\"|[\(\s])", re.MULTILINE)

    def parse(self, content: str, file_path: str) -> ParseResult:
        """Parse Go code and return a ParseResult object."""
        try:
            logger.debug(f"Starting EnhancedGoParser.parse for file: {file_path}")

            declarations = []
            imports = []
            classes = []  # Go struct types
            functions = []
            docstrings = {}
            errors = []

            lines = content.split("\n")
            i = 0

            # Find package name
            for line in lines:
                if line.strip().startswith("package "):
                    line.strip()[8:].strip()
                    break

            while i < len(lines):
                line = lines[i].strip()

                # Skip empty lines and comments
                if not line or line.startswith("//"):
                    i += 1
                    continue

                # Skip block comments
                if line.startswith("/*"):
                    while i < len(lines) and "*/" not in lines[i]:
                        i += 1
                    i += 1
                    continue

                # Process imports
                processed, new_index = self._process_imports(line, imports, i, lines)
                if processed:
                    # Update i to the position returned by _process_imports
                    i = new_index
                    continue

                # Try each pattern
                for kind, pattern in self.patterns.items():
                    if kind == "import":  # Already handled separately
                        continue

                    match = pattern.match(line)
                    if match:
                        # Extract name
                        try:
                            name = match.group("name")
                            if not name:
                                i += 1
                                continue
                        except (IndexError, KeyError):
                            i += 1
                            continue

                        start_line = i
                        end_line = i
                        docstring_text = ""

                        # Extract modifiers
                        modifiers = self._extract_modifiers(line)

                        # For braced declarations, find the end of the block
                        if "{" in line:
                            end_line = self._find_block_end_improved(
                                lines, i, open_char="{", close_char="}"
                            )

                        # Look for a doc comment before this declaration
                        j = start_line - 1
                        doc_lines = []
                        while j >= 0 and j >= start_line - 5:  # Look at most 5 lines back
                            prev_line = lines[j].strip()
                            if not prev_line or prev_line.isspace():
                                j -= 1
                                continue

                            if prev_line.startswith("//"):
                                doc_lines.insert(0, prev_line[2:].strip())
                                j -= 1
                            else:
                                break

                        if doc_lines:
                            docstring_text = "\n".join(doc_lines)

                        # Convert kind for consistent naming
                        normalized_kind = kind
                        if kind == "struct" or kind == "interface":
                            normalized_kind = "type"
                            # Add to classes list
                            classes.append(name)
                        elif kind in ["function", "method"]:
                            normalized_kind = "function"
                            # Add to functions list
                            functions.append(name)

                        # Create declaration
                        declaration = Declaration(
                            kind=normalized_kind,
                            name=name,
                            start_line=start_line,
                            end_line=end_line,
                            docstring=docstring_text,
                            modifiers=modifiers,
                        )

                        # Store docstring in the docstrings dict
                        if docstring_text:
                            docstrings[f"{normalized_kind}.{name}"] = docstring_text

                        declarations.append(declaration)
                        logger.debug(f"Found declaration: {normalized_kind} {name}")

                        # Move past the block
                        i = end_line + 1
                        break
                else:
                    # No pattern matched
                    i += 1

            imports = list(set(imports))  # Remove duplicates

            logger.debug(
                f"Finished EnhancedGoParser.parse for file: {file_path}. "
                f"Found {len(declarations)} declarations, {len(imports)} unique imports."
            )

            return ParseResult(
                declarations=declarations,
                imports=imports,
                engine_used="regex",
            )

        except Exception as e:
            logger.error(f"Error parsing Go file {file_path}: {e}", exc_info=True)
            error_msg = f"Failed to parse Go file ({type(e).__name__}): {e}"
            errors.append(error_msg)

            # Return partially parsed content with error
            return ParseResult(
                declarations=[],
                imports=[],
                error=error_msg,
                engine_used="regex",
            )

    def _process_imports(
        self, line: str, imports: List[str], i: int, lines: List[str]
    ) -> Tuple[bool, int]:
        """
        Process Go import statements and add them to the imports list.

        Args:
            line: Current line of code to process.
            imports: List to add imports to.
            i: Current line index.
            lines: All lines of code.

        Returns:
            Tuple of (was_processed, new_index) where:
            - was_processed: True if line was an import statement
            - new_index: Updated index position after processing imports
        """
        # Handle single import
        if line.startswith("import ") and '"' in line:
            start_idx = line.find('"')
            end_idx = line.find('"', start_idx + 1)
            if start_idx != -1 and end_idx != -1:
                import_path = line[start_idx + 1 : end_idx]
                # Extract the last component as the module name
                if "/" in import_path:
                    module_name = import_path.split("/")[-1]
                else:
                    module_name = import_path
                imports.append(module_name)
                return True, i

        # Handle import block
        if line == "import (" or line.startswith("import ("):
            j = i + 1 if line == "import (" else i
            while j < len(lines):
                import_line = lines[j].strip()
                if import_line == ")":
                    # Return the updated index position - after the closing parenthesis
                    return True, j + 1

                if import_line and not import_line.startswith("//"):
                    # Parse each import inside the block
                    if '"' in import_line:
                        start_idx = import_line.find('"')
                        end_idx = import_line.find('"', start_idx + 1)
                        if start_idx != -1 and end_idx != -1:
                            import_path = import_line[start_idx + 1 : end_idx]
                            # Extract the last component or check for alias
                            parts = import_line.split()
                            if len(parts) > 1 and parts[0] not in ["_", "."]:
                                # Has alias like: alias "path/to/package"
                                module_name = parts[0]
                            elif "/" in import_path:
                                module_name = import_path.split("/")[-1]
                            else:
                                module_name = import_path
                            imports.append(module_name)
                j += 1

        return False, i

    def _extract_modifiers(self, line: str) -> Set[str]:
        """
        Extract modifiers from a declaration line.

        Args:
            line: Line containing a declaration.

        Returns:
            Set of modifiers found in the line.
        """
        found_modifiers = set()
        for mod in self.modifiers:
            # Use word boundaries to match whole words only
            if re.search(rf"\b{re.escape(mod)}\b", line):
                found_modifiers.add(mod)
        return found_modifiers

    def get_capabilities(self) -> Dict[str, bool]:
        """Return the capabilities of this parser."""
        return {
            "can_parse_functions": True,
            "can_parse_classes": False,  # Go has structs/interfaces, not classes
            "can_parse_types": True,
            "can_parse_structs": True,
            "can_parse_interfaces": True,
            "can_parse_imports": True,
            "can_extract_docstrings": True,
        }
