# file: codeconcat/parser/language_parsers/enhanced_base_parser.py

"""
Enhanced base parser with more shared functionality across language parsers.

This module extends the BaseParser and provides standard patterns and methods
that can be used by all language parsers to reduce duplication and improve
consistency in parsing across different languages.
"""

import re
from typing import Dict, List, Optional, Pattern, Tuple

from codeconcat.base_types import ParseResult
from codeconcat.parser.language_parsers.base_parser import BaseParser
from codeconcat.parser.language_parsers.pattern_library import CommentPatterns, DocstringPatterns


class EnhancedBaseParser(BaseParser):
    """
    Enhanced base parser with more shared functionality.

    This parser extends BaseParser with:
    - Standard regex patterns for common code constructs
    - Improved docstring extraction
    - Helper methods for parsing common structures
    - Better error handling and progressive enhancement
    """

    def __init__(self, file_path: str = ""):
        """Initialize the enhanced parser with standard patterns."""
        super().__init__(file_path)
        self.language = "generic"  # Override in subclasses
        self._setup_standard_patterns()

    def _setup_standard_patterns(self):
        """Setup standard patterns that many languages share."""
        # Set up comment patterns based on language
        self.line_comment = CommentPatterns.SINGLE_LINE.get(self.language)

        if self.language in CommentPatterns.BLOCK_COMMENT:
            self.block_comment_start, self.block_comment_end = CommentPatterns.BLOCK_COMMENT[
                self.language
            ]

        # Common patterns (override in subclasses as needed)
        # Initialize with empty dict, subclasses will populate
        self.patterns: Dict[str, Pattern[str]] = {}

        # Common modifiers recognized by this parser
        self.modifiers = set()  # Set in subclasses

    def parse(self, _content: str, file_path: str) -> ParseResult:
        """
        Parse code content and return a ParseResult object.

        Args:
            content: The code content as a string.
            file_path: The path to the file being parsed.

        Returns:
            A ParseResult object.
        """
        # This method should be overridden by subclasses
        # Providing a basic implementation that just returns an empty parse result
        return ParseResult(
            file_path=file_path,
            declarations=[],
            imports=[],
            error=None,
        )

    def extract_docstring(self, lines: List[str], start: int, end: int) -> Optional[str]:
        """
        Enhanced docstring extraction that works across languages.

        Args:
            lines: List of code lines.
            start: Start line index.
            end: End line index.

        Returns:
            Extracted docstring if found, None otherwise.
        """
        # Try language-specific docstring extraction
        if self.language == "python":
            return DocstringPatterns.extract_python_docstring(lines, start, end)

        # Generic multi-line comment extraction
        if self.block_comment_start and self.block_comment_end:
            # Join the relevant lines into a single string
            text = "\n".join(lines[start : end + 1])
            # Look for block comments
            start_idx = text.find(self.block_comment_start)
            if start_idx >= 0:
                end_idx = text.find(
                    self.block_comment_end, start_idx + len(self.block_comment_start)
                )
                if end_idx >= 0:
                    docstring = text[start_idx + len(self.block_comment_start) : end_idx].strip()
                    return docstring

        # Try single-line comment docstrings
        if self.line_comment:
            docstring_lines = []
            for i in range(start, min(end + 1, len(lines))):
                line = lines[i].strip()
                if line.startswith(self.line_comment):
                    docstring_lines.append(line[len(self.line_comment) :].strip())
                elif docstring_lines and not line:
                    # Allow empty lines in docstrings
                    docstring_lines.append("")
                elif docstring_lines:
                    # End of docstring
                    break

            if docstring_lines:
                return "\n".join(docstring_lines)

        # Fallback to BaseParser's implementation
        return super().extract_docstring(lines, start, end)

    def _find_pattern_in_content(
        self,
        pattern_name: str,
        lines: List[str],
        start_line: int = 0,
        end_line: Optional[int] = None,
    ) -> List[Tuple[int, re.Match]]:
        """
        Find all matches for a named pattern in the content.

        Args:
            pattern_name: Name of the pattern in self.patterns.
            lines: List of code lines.
            start_line: Line to start searching from.
            end_line: Line to end searching at (inclusive).

        Returns:
            List of tuples with (line_number, match_object).
        """
        pattern = self.patterns.get(pattern_name)
        if not pattern:
            return []

        matches = []
        end_line = end_line or len(lines)

        for i in range(start_line, min(end_line, len(lines))):
            line = lines[i]
            match = pattern.match(line)
            if match:
                matches.append((i, match))

        return matches

    def _find_block_end_improved(
        self,
        lines: List[str],
        start: int,
        open_char: str = "{",
        close_char: str = "}",
        indent_based: bool = False,
    ) -> int:
        """
        Find the end of a code block with improved handling of nested structures.

        Args:
            lines: List of code lines.
            start: Start line index.
            open_char: Character that opens a block (e.g., '{').
            close_char: Character that closes a block (e.g., '}').
            indent_based: Whether to use indentation instead of braces (e.g., Python).

        Returns:
            Line index of the end of the block.
        """
        if indent_based:
            return self._find_block_end_by_indent(lines, start)

        return self._find_block_end_by_braces(lines, start, open_char, close_char)

    def _find_block_end_by_braces(
        self, lines: List[str], start: int, open_char: str = "{", close_char: str = "}"
    ) -> int:
        """
        Find the end of a code block using brace counting.

        Args:
            lines: List of code lines.
            start: Start line index.
            open_char: Character that opens a block (e.g., '{').
            close_char: Character that closes a block (e.g., '}').

        Returns:
            Line index of the end of the block.
        """
        line = lines[start]
        if open_char not in line:
            return start

        brace_count = line.count(open_char) - line.count(close_char)
        if brace_count <= 0:
            return start

        for i in range(start + 1, len(lines)):
            line = lines[i]

            # Skip comment lines
            if self.line_comment and line.strip().startswith(self.line_comment):
                continue

            # Handle multi-line string literals and comments
            # (simplified - a real implementation would need more sophisticated handling)

            brace_count += line.count(open_char) - line.count(close_char)
            if brace_count <= 0:
                return i

        return len(lines) - 1

    def _find_block_end_by_indent(self, lines: List[str], start: int) -> int:
        """
        Find the end of a code block using indentation (e.g., Python).

        Args:
            lines: List of code lines.
            start: Start line index.

        Returns:
            Line index of the end of the block.
        """
        if start >= len(lines):
            return start

        # Get the indentation of the block start line
        start_line = lines[start]
        start_indent = len(start_line) - len(start_line.lstrip())

        # Check if there's a colon at the end of the line
        if not start_line.rstrip().endswith(":"):
            return start

        # Find the first non-empty line with same or less indentation
        for i in range(start + 1, len(lines)):
            line = lines[i].rstrip()
            if not line:  # Skip empty lines
                continue

            indent = len(lines[i]) - len(lines[i].lstrip())
            if indent <= start_indent:
                return i - 1

        return len(lines) - 1

    def get_capabilities(self) -> Dict[str, bool]:
        """
        Return the capabilities of this parser.

        Returns:
            Dictionary of capability names to boolean values.
        """
        return {
            "can_parse_functions": self.patterns.get("function") is not None,
            "can_parse_classes": self.patterns.get("class") is not None,
            "can_parse_imports": self.patterns.get("import") is not None,
            "can_extract_docstrings": True,  # We have generic docstring extraction
        }

    def validate(self) -> bool:
        """
        Validate that the parser is properly configured.

        Returns:
            True if the parser is properly configured, False otherwise.
        """
        # At minimum, the parser should have a language set
        return bool(self.language and self.language != "generic")

    def _count_total_declarations(self, declarations: List) -> int:
        """Count the total number of declarations including all nested ones.

        Args:
            declarations: List of Declaration objects

        Returns:
            Total count including nested declarations

        Complexity: O(n) where n is total number of declarations in tree
        """
        total = len(declarations)
        for decl in declarations:
            if hasattr(decl, "children") and decl.children:
                total += self._count_total_declarations(decl.children)
        return total

    def _calculate_max_nesting_depth(self, declarations: List, current_depth: int = 1) -> int:
        """Calculate the maximum nesting depth in the declaration tree.

        Args:
            declarations: List of Declaration objects
            current_depth: Current recursion depth (default: 1)

        Returns:
            Maximum nesting depth found

        Complexity: O(n) where n is total number of declarations in tree
        """
        if not declarations:
            return current_depth - 1

        max_depth = current_depth
        for decl in declarations:
            if hasattr(decl, "children") and decl.children:
                child_depth = self._calculate_max_nesting_depth(decl.children, current_depth + 1)
                max_depth = max(max_depth, child_depth)

        return max_depth

    def _extract_modifiers(self, line: str) -> set[str]:
        """Extract modifiers from a code line based on language-specific patterns.

        Args:
            line: The code line to analyze

        Returns:
            Set of modifier strings found in the line

        Complexity: O(m*k) where m is number of modifiers and k is line length
        """
        found_modifiers: set[str] = set()
        if not self.modifiers:
            return found_modifiers

        # Check each registered modifier
        for modifier in self.modifiers:
            # Use word boundary matching to avoid false positives
            if f" {modifier} " in f" {line} " or line.strip().startswith(f"{modifier} "):
                found_modifiers.add(modifier)

        return found_modifiers
