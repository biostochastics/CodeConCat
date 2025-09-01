# file: codeconcat/parser/language_parsers/enhanced_c_family_parser.py

"""
Enhanced C-family parser base class for CodeConcat.

This module provides a base parser for C-family languages (C, C++, C#, Java)
that shares common functionality while allowing language-specific customization.
"""

import logging
import re
from typing import Dict, List, Optional, Set

from codeconcat.base_types import Declaration, ParseResult
from codeconcat.parser.language_parsers.enhanced_base_parser import EnhancedBaseParser
from codeconcat.parser.language_parsers.pattern_library import (
    C_FAMILY_MODIFIERS,
    ClassPatterns,
    FunctionPatterns,
)

logger = logging.getLogger(__name__)


class EnhancedCFamilyParser(EnhancedBaseParser):
    """Base parser for C-family languages with improved regex patterns and shared functionality."""

    def __init__(self):
        """Initialize the enhanced C-family parser."""
        super().__init__()
        self.language = "c_family"  # Will be overridden by subclasses
        self._setup_c_family_patterns()

    def _setup_standard_patterns(self):
        """Setup standard patterns for C-family languages."""
        super()._setup_standard_patterns()

        # C-family languages use braces for blocks
        self.block_start = "{"
        self.block_end = "}"

        # Initialize patterns dict (will be populated in _setup_c_family_patterns)
        self.patterns = {}

        # Initialize recognized modifiers from pattern library
        self.modifiers = set(C_FAMILY_MODIFIERS)

    def _setup_c_family_patterns(self):
        """Setup patterns for C-family languages."""
        # Functions and classes
        self.patterns["function"] = FunctionPatterns.C_STYLE
        self.patterns["class"] = ClassPatterns.C_STYLE

        # Additional patterns - can be extended by subclasses
        self.patterns["namespace"] = re.compile(
            r"^\s*namespace\s+(?P<name>[\w:]+)(?:\s*\{)?", re.MULTILINE
        )

    def parse(self, content: str, file_path: str) -> ParseResult:
        """Parse C-family code and return a ParseResult object."""
        try:
            logger.debug(f"Starting {self.__class__.__name__}.parse for file: {file_path}")

            declarations: list[Declaration] = []
            imports: list[str] = []
            errors: list[str] = []

            lines = content.split("\n")

            # Process the entire file content recursively
            self._process_block(lines, 0, len(lines) - 1, declarations, imports, errors)

            # Remove duplicates from imports
            imports = list(set(imports))

            logger.debug(
                f"Finished {self.__class__.__name__}.parse for file: {file_path}. "
                f"Found {len(declarations)} declarations, {len(imports)} unique imports."
            )

            return ParseResult(
                declarations=declarations,
                imports=imports,
                engine_used="regex",
            )

        except Exception as e:
            logger.error(f"Error parsing {self.language} file {file_path}: {e}", exc_info=True)
            error_msg = f"Failed to parse {self.language} file ({type(e).__name__}): {e}"
            errors.append(error_msg)

            # Return partially parsed content with error
            return ParseResult(
                declarations=[],
                imports=[],
                error=error_msg,
                engine_used="regex",
            )

    def _process_block(
        self,
        lines: List[str],
        start: int,
        end: int,
        declarations: List[Declaration],
        imports: List[str],
        errors: List[str],
        parent_declaration: Optional[Declaration] = None,
    ) -> int:
        """
        Process a C-family code block and extract declarations and imports.

        Args:
            lines: List of code lines.
            start: Start line index.
            end: End line index (inclusive).
            declarations: List to add declarations to.
            imports: List to add imports to.
            errors: List to add errors to.
            parent_declaration: Parent declaration if processing a nested block.

        Returns:
            Next line index to process.
        """
        i = start

        while i <= end:
            if i >= len(lines):  # Safety check
                break

            line = lines[i].strip()

            # Skip empty lines and comments
            if not line or (self.line_comment and line.startswith(self.line_comment)):
                i += 1
                continue

            # Skip block comments
            if self.block_comment_start and line.startswith(self.block_comment_start):
                while i < len(lines) and (
                    self.block_comment_end and self.block_comment_end not in lines[i]
                ):
                    i += 1
                i += 1  # Skip the closing comment line
                continue

            # Process imports (to be implemented by subclasses)
            if hasattr(self, "_process_imports") and self._process_imports(line, imports):
                i += 1
                continue

            # Try each pattern for declarations
            for kind, pattern in self.patterns.items():
                if not pattern:
                    continue

                match = pattern.match(line)
                if match:
                    # Extract name - handle different group names in patterns
                    name = None
                    for group_name in ["name", "n"]:
                        try:
                            name = match.group(group_name)
                            if name:
                                break
                        except (IndexError, KeyError):
                            continue

                    if not name:
                        i += 1
                        continue

                    start_line = i
                    end_line = i
                    docstring_text = ""

                    # For declarations with blocks, find the end
                    if "{" in line:
                        end_line = self._find_block_end_improved(
                            lines, i, open_char="{", close_char="}"
                        )
                    else:
                        # Check if opening brace is on the next few lines
                        for j in range(i + 1, min(i + 5, len(lines))):
                            if j >= len(lines):
                                break
                            if "{" in lines[j]:
                                end_line = self._find_block_end_improved(
                                    lines, j, open_char="{", close_char="}"
                                )
                                break
                        else:
                            # For declarations without braces, find the semicolon
                            j = i
                            while j < len(lines) and ";" not in lines[j]:
                                j += 1
                            if j < len(lines):
                                end_line = j

                    # Extract docstring if available
                    docstring_text = self.extract_docstring(lines, start_line, end_line) or ""

                    # Extract modifiers like public, static, etc.
                    modifiers = self._extract_modifiers(line)

                    # Create declaration
                    declaration = Declaration(
                        kind=kind,
                        name=name,
                        start_line=start_line,
                        end_line=end_line,
                        docstring=docstring_text,
                        modifiers=modifiers,
                    )

                    # Add declaration to parent or top-level list
                    if parent_declaration:
                        if parent_declaration.children is None:
                            parent_declaration.children = []
                        parent_declaration.children.append(declaration)
                        logger.debug(f"Found nested declaration: {kind} {name}")
                    else:
                        declarations.append(declaration)
                        logger.debug(f"Found declaration: {kind} {name}")

                    # Process nested blocks (only for container types like class, struct, namespace)
                    if (
                        kind in ["class", "struct", "namespace", "function"]
                        and end_line > start_line
                    ):
                        nested_declarations: list[Declaration] = []  # Create new list for children
                        # Recursively process the block for nested declarations
                        self._process_block(
                            lines,
                            start_line + 1,
                            end_line - 1,
                            nested_declarations,
                            imports,
                            errors,
                            declaration,
                        )
                        declaration.children = nested_declarations  # Assign children

                    # Move past the block
                    i = end_line + 1
                    break
            else:
                # No pattern matched
                i += 1

        return i

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

    def extract_docstring(self, lines: List[str], start: int, end: int) -> Optional[str]:
        """
        Extract C-family docstring from lines.

        Args:
            lines: List of code lines.
            start: Start line index.
            end: End line index.

        Returns:
            Extracted docstring if found, None otherwise.
        """
        # Skip empty lines at the beginning
        while start <= end and not lines[start].strip():
            start += 1

        if start > end:
            return None

        # Try to find a block comment
        if self.block_comment_start and self.block_comment_end:
            comment_lines = []
            in_comment = False

            for i in range(start, min(end + 1, len(lines))):
                line = lines[i].strip()

                if not in_comment and line.startswith(self.block_comment_start):
                    # Start of a block comment
                    in_comment = True
                    if line.endswith(self.block_comment_end) and len(line) > len(
                        self.block_comment_start
                    ) + len(self.block_comment_end):
                        # Single-line comment
                        return line[
                            len(self.block_comment_start) : -len(self.block_comment_end)
                        ].strip()

                    comment_lines.append(line[len(self.block_comment_start) :].strip())
                    continue

                if in_comment:
                    if line.endswith(self.block_comment_end):
                        # End of block comment
                        comment_lines.append(line[: -len(self.block_comment_end)].strip())
                        return "\n".join(comment_lines).strip()
                    else:
                        comment_lines.append(line)

        # Try to find line comments
        if self.line_comment:
            comment_lines = []
            for i in range(start, min(end + 1, len(lines))):
                line = lines[i].strip()
                if line.startswith(self.line_comment):
                    comment_lines.append(line[len(self.line_comment) :].strip())
                elif comment_lines and not line:
                    # Allow empty lines
                    continue
                elif comment_lines:
                    # End of comment block
                    break
                else:
                    # No comments found yet, and this line is not a comment
                    break

            if comment_lines:
                return "\n".join(comment_lines)

        return None

    def get_capabilities(self) -> Dict[str, bool]:
        """Return the capabilities of this parser."""
        return {
            "can_parse_functions": True,
            "can_parse_classes": True,
            "can_parse_imports": False,  # Set by subclasses
            "can_extract_docstrings": True,
        }
