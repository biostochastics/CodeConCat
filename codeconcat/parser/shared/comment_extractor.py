"""Unified comment and docstring extraction for all language parsers.

This module eliminates ~600 lines of duplicated comment extraction logic
across 10+ enhanced parsers by providing a single, language-agnostic interface.
"""

import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class CommentExtractor:
    """Unified comment/docstring extraction for all languages.

    Provides language-agnostic methods for extracting documentation comments
    that appear before declarations (functions, classes, methods, etc.).

    Eliminates duplication by centralizing the logic that was previously
    scattered across enhanced_python_parser, enhanced_go_parser, enhanced_rust_parser,
    enhanced_php_parser, enhanced_julia_parser, and 5+ other parsers.
    """

    # Language-specific comment patterns
    LINE_COMMENT_PATTERNS = {
        "python": "#",
        "javascript": "//",
        "typescript": "//",
        "go": "//",
        "rust": "//",
        "cpp": "//",
        "c": "//",
        "csharp": "//",
        "java": "//",
        "php": "//",
        "julia": "#",
        "r": "#",
        "bash": "#",
        "shell": "#",
    }

    BLOCK_COMMENT_PATTERNS = {
        "python": ('"""', '"""'),  # Also supports triple single quotes
        "javascript": ("/*", "*/"),
        "typescript": ("/*", "*/"),
        "go": ("/*", "*/"),
        "rust": ("/*", "*/"),
        "cpp": ("/*", "*/"),
        "c": ("/*", "*/"),
        "csharp": ("/*", "*/"),
        "java": ("/*", "*/"),
        "php": ("/*", "*/"),
        "julia": ("#=", "=#"),
        "r": None,  # R doesn't have block comments
        "bash": None,
        "shell": None,
    }

    @staticmethod
    def extract_pre_declaration_comments(
        lines: List[str],
        declaration_line: int,
        language: str,
        max_lookback: int = 10,
    ) -> Optional[str]:
        (
            """Extract comments immediately before a declaration.

        This method searches backwards from the declaration line to find
        associated documentation comments. It handles:
        - Line comments (e.g., //, #)
        - Block comments (e.g., /* */, """
            """)
        - Multiple consecutive comment lines
        - Empty lines between comments and declarations

        Args:
            lines: List of code lines
            declaration_line: Line number of the declaration (0-indexed)
            language: Programming language identifier
            max_lookback: Maximum number of lines to search backwards (default: 10)

        Returns:
            Extracted comment text or None if no comments found

        Complexity: O(max_lookback) - constant time bounded by max_lookback

        Example:
            >>> lines = ["# This is a doc comment", "def foo():", "    pass"]
            >>> CommentExtractor.extract_pre_declaration_comments(lines, 1, "python")
            "This is a doc comment"
        """
        )
        if declaration_line <= 0 or declaration_line >= len(lines):
            return None

        # Get language-specific comment markers
        line_comment = CommentExtractor.LINE_COMMENT_PATTERNS.get(language.lower())
        block_comment = CommentExtractor.BLOCK_COMMENT_PATTERNS.get(language.lower())

        if not line_comment and not block_comment:
            logger.debug(f"No comment patterns defined for language: {language}")
            return None

        comment_lines: List[str] = []
        search_start = max(0, declaration_line - max_lookback)

        # Search backwards from declaration
        for i in range(declaration_line - 1, search_start - 1, -1):
            if i < 0 or i >= len(lines):
                break

            line = lines[i].strip()

            # Skip empty lines
            if not line:
                # Allow empty lines within comment blocks
                if comment_lines:
                    comment_lines.insert(0, "")
                continue

            # Check for line comments
            if line_comment and line.startswith(line_comment):
                # Remove comment marker and strip whitespace
                comment_text = line[len(line_comment) :].strip()
                comment_lines.insert(0, comment_text)
                continue

            # Check for block comment end (when searching backwards)
            if block_comment and line.endswith(block_comment[1]):
                # Found end of block comment, search for start
                block_lines = CommentExtractor._extract_block_comment_backwards(
                    lines, i, block_comment
                )
                if block_lines:
                    comment_lines = block_lines + comment_lines
                break

            # Hit a non-comment line
            if comment_lines:
                # We already have comments, so stop here
                break

        # Clean up and join comment lines
        if comment_lines:
            # Remove leading/trailing empty lines
            while comment_lines and not comment_lines[0]:
                comment_lines.pop(0)
            while comment_lines and not comment_lines[-1]:
                comment_lines.pop()

            if comment_lines:
                return "\n".join(comment_lines)

        return None

    @staticmethod
    def _extract_block_comment_backwards(
        lines: List[str], end_line: int, markers: Tuple[str, str]
    ) -> List[str]:
        """Extract block comment by searching backwards from end marker.

        Args:
            lines: List of code lines
            end_line: Line containing the end marker
            markers: Tuple of (start_marker, end_marker)

        Returns:
            List of comment text lines (without markers)
        """
        start_marker, end_marker = markers
        comment_lines: List[str] = []

        # Extract content from end line (might have content before end marker)
        end_line_text = lines[end_line]
        end_marker_pos = end_line_text.find(end_marker)
        if end_marker_pos > 0:
            # Get text before end marker
            before_end = end_line_text[:end_marker_pos].strip()
            # Check if start marker is also on this line (single-line block comment)
            start_marker_pos = before_end.find(start_marker)
            if start_marker_pos >= 0:
                # Single-line block comment
                comment_text = before_end[start_marker_pos + len(start_marker) :].strip()
                return [comment_text] if comment_text else []
            elif before_end:
                comment_lines.insert(0, before_end)

        # Search backwards for start marker
        for i in range(end_line - 1, max(0, end_line - 50), -1):
            line = lines[i]
            if start_marker in line:
                # Found start marker
                start_pos = line.find(start_marker)
                # Get content after start marker
                after_start = line[start_pos + len(start_marker) :].strip()
                if after_start:
                    comment_lines.insert(0, after_start)
                break
            else:
                # Part of the block comment
                comment_lines.insert(0, line.strip())

        return comment_lines

    @staticmethod
    def extract_inline_docstring(
        lines: List[str], start_line: int, end_line: int, language: str
    ) -> Optional[str]:
        """Extract docstring from within a declaration body.

        This is particularly useful for Python's triple-quoted docstrings
        that appear as the first statement in a function/class.

        Args:
            lines: List of code lines
            start_line: Start line of the declaration body
            end_line: End line of the declaration body
            language: Programming language identifier

        Returns:
            Extracted docstring or None
        """
        if language.lower() == "python":
            return CommentExtractor._extract_python_inline_docstring(lines, start_line, end_line)

        # For other languages, try block comment extraction
        block_comment = CommentExtractor.BLOCK_COMMENT_PATTERNS.get(language.lower())
        if not block_comment:
            return None

        # Search for block comment at the beginning of the body
        for i in range(start_line, min(end_line + 1, len(lines))):
            line = lines[i].strip()
            if not line:
                continue

            if line.startswith(block_comment[0]):
                # Found potential docstring
                result = CommentExtractor._extract_block_comment_forward(lines, i, block_comment)
                return "\n".join(result) if result else None

            # Hit a non-comment line
            break

        return None

    @staticmethod
    def _extract_python_inline_docstring(
        lines: List[str], start_line: int, end_line: int
    ) -> Optional[str]:
        """Extract Python's triple-quoted docstrings."""
        # Look for triple quotes at the start of the block
        for i in range(start_line, min(end_line + 1, len(lines))):
            line = lines[i].strip()
            if not line:
                continue

            # Check for triple quotes (single or double)
            if line.startswith('"""') or line.startswith("'''"):
                quote_type = '"""' if line.startswith('"""') else "'''"
                docstring_lines = []

                # Check if single-line docstring
                if line.count(quote_type) >= 2:
                    # Single-line docstring
                    content = line.strip(quote_type).strip()
                    return content if content else None

                # Multi-line docstring
                docstring_lines.append(line[3:].strip())  # Remove opening quotes

                # Search for closing quotes
                for j in range(i + 1, min(end_line + 1, len(lines))):
                    doc_line = lines[j].strip()
                    if quote_type in doc_line:
                        # Found closing quotes
                        closing_pos = doc_line.find(quote_type)
                        if closing_pos > 0:
                            docstring_lines.append(doc_line[:closing_pos].strip())
                        break
                    else:
                        docstring_lines.append(doc_line)

                # Clean up and return
                while docstring_lines and not docstring_lines[0]:
                    docstring_lines.pop(0)
                while docstring_lines and not docstring_lines[-1]:
                    docstring_lines.pop()

                return "\n".join(docstring_lines) if docstring_lines else None

            # Hit a non-comment line
            break

        return None

    @staticmethod
    def _extract_block_comment_forward(
        lines: List[str], start_line: int, markers: Tuple[str, str]
    ) -> List[str]:
        """Extract block comment by searching forward from start marker."""
        start_marker, end_marker = markers
        comment_lines: List[str] = []

        # Extract content from start line
        start_line_text = lines[start_line]
        start_pos = start_line_text.find(start_marker)
        after_start = start_line_text[start_pos + len(start_marker) :].strip()

        # Check if single-line block comment
        if end_marker in after_start:
            end_pos = after_start.find(end_marker)
            content = after_start[:end_pos].strip()
            return [content] if content else []

        if after_start:
            comment_lines.append(after_start)

        # Search forward for end marker
        for i in range(start_line + 1, min(start_line + 50, len(lines))):
            line = lines[i]
            if end_marker in line:
                # Found end marker
                end_pos = line.find(end_marker)
                before_end = line[:end_pos].strip()
                if before_end:
                    comment_lines.append(before_end)
                break
            else:
                comment_lines.append(line.strip())

        return comment_lines
