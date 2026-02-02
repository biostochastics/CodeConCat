# file: codeconcat/parser/language_parsers/base_parser.py

import re
from abc import abstractmethod
from dataclasses import dataclass, field
from re import Pattern
from typing import Optional

from codeconcat.base_types import Declaration, ParseResult, ParserInterface

__all__ = ["BaseParser", "CodeSymbol", "ParserInterface"]


@dataclass
class CodeSymbol:
    """Represents a symbol in a codebase, such as a variable, function, or class.

    Captures hierarchical code structures where symbols can be nested within each other,
    along with their location in the source code for reference or analysis.

    Attributes:
        name: The name of the code symbol.
        kind: The type of symbol (e.g., 'variable', 'function', 'class').
        start_line: The 1-indexed line number where the symbol starts.
        end_line: The 1-indexed line number where the symbol ends.
        modifiers: A set of modifiers (e.g., 'public', 'private', 'static').
        parent: The parent symbol if this symbol is nested, or None.
        children: Child symbols nested within this symbol.
        docstring: The associated documentation string, if present.
    """

    name: str
    kind: str
    start_line: int
    end_line: int
    modifiers: set[str]
    parent: Optional["CodeSymbol"] = None
    children: list["CodeSymbol"] = field(default_factory=list)
    docstring: str | None = None


class BaseParser(ParserInterface):
    """
    BaseParser defines a minimal interface and partial logic for line-based scanning
    and comment extraction. Subclasses typically override _setup_patterns() and parse().
    """

    def __init__(self, _file_path: str = ""):
        """Initialize the parser with default values.

        Args:
            _file_path: Optional file path (unused, for interface compatibility).
        """
        self.symbols: list[CodeSymbol] = []
        self.current_symbol: CodeSymbol | None = None
        self.symbol_stack: list[CodeSymbol] = []
        self.block_start: str | None = "{"  # Default block start
        self.block_end: str | None = "}"  # Default block end
        self.line_comment: str | None = None  # Default line comment
        self.block_comment_start: str | None = None  # Default block comment start
        self.block_comment_end: str | None = None  # Default block comment end
        self.patterns: dict[str, Pattern[str]] = {}
        self.modifiers: set[str] = set()
        # Match Unicode identifiers (Python 3 \w matches Unicode by default)
        self.identifier_pattern = re.compile(r"\w+")

    def _reset(self) -> None:
        """Reset parser state for a fresh parse.

        Call this at the beginning of parse() to ensure clean state when
        reusing a parser instance for multiple files.
        """
        self.symbols = []
        self.current_symbol = None
        self.symbol_stack = []

    @abstractmethod
    def parse(self, content: str, file_path: str) -> ParseResult:
        """Parse code content and return a ParseResult object.

        Subclasses must implement this method. Implementations should call
        self._reset() at the start to ensure clean state.

        Args:
            content: The code content as a string.
            file_path: The path to the file being parsed.

        Returns:
            A ParseResult object.
        """
        ...

    def _flatten_symbol(self, symbol: CodeSymbol) -> list[Declaration]:
        """Flatten a symbol and its children into a list of declarations.

        Recursively converts a CodeSymbol tree into a flat list of Declaration objects.

        Args:
            symbol: The root CodeSymbol to flatten.

        Returns:
            A list of Declaration objects including the symbol and all nested children.
        """
        declarations = [
            Declaration(
                kind=symbol.kind,
                name=symbol.name,
                start_line=symbol.start_line,
                end_line=symbol.end_line,
                docstring=symbol.docstring or "",
                modifiers=symbol.modifiers,
            )
        ]
        for child in symbol.children:
            declarations.extend(self._flatten_symbol(child))
        return declarations

    def _count_braces_outside_strings(self, line: str) -> int:
        """Count net braces (open - close) excluding those inside string literals.

        Scans the line character by character, tracking string context to avoid
        counting braces that appear within quoted strings.

        Args:
            line: A single line of source code.

        Returns:
            The net brace count (block_start occurrences minus block_end occurrences)
            for braces outside of string literals.
        """
        if self.block_start is None or self.block_end is None:
            return 0

        count = 0
        in_string: str | None = None
        escape_next = False
        i = 0

        while i < len(line):
            char = line[i]

            if escape_next:
                escape_next = False
                i += 1
                continue

            if char == "\\":
                escape_next = True
                i += 1
                continue

            # Check for string delimiters
            if in_string is None:
                # Check for triple quotes first
                if line[i : i + 3] in ('"""', "'''"):
                    in_string = line[i : i + 3]
                    i += 3
                    continue
                elif char in ('"', "'"):
                    in_string = char
                    i += 1
                    continue
                # Check for line comment
                if self.line_comment and line[i:].startswith(self.line_comment):
                    break  # Rest of line is comment
            else:
                # Check for end of string
                if in_string in ('"""', "'''") and line[i : i + 3] == in_string:
                    in_string = None
                    i += 3
                    continue
                elif len(in_string) == 1 and char == in_string:
                    in_string = None
                    i += 1
                    continue

            # Count braces only when not in string
            if in_string is None:
                if char == self.block_start:
                    count += 1
                elif char == self.block_end:
                    count -= 1

            i += 1

        return count

    def _find_block_end(self, lines: list[str], start: int) -> int:
        """Find the end of a code block by matching braces.

        Scans from the starting line and tracks brace nesting to find where
        the block closes. Skips braces inside strings and comment lines.

        Args:
            lines: List of source code lines.
            start: The 0-indexed line number where the block starts.

        Returns:
            The 0-indexed line number where the block ends, or the start line
            if no block opener is found, or len(lines)-1 if block never closes.
        """
        if self.block_start is None or self.block_end is None:
            return start

        line = lines[start]
        if self.block_start not in line:
            return start

        brace_count = self._count_braces_outside_strings(line)
        if brace_count <= 0:
            return start

        for i in range(start + 1, len(lines)):
            line = lines[i].strip()
            if self.line_comment and line.startswith(self.line_comment):
                continue
            brace_count += self._count_braces_outside_strings(line)
            if brace_count <= 0:
                return i

        return len(lines) - 1

    def _create_pattern(
        self, base_pattern: str, modifiers: list[str] | None = None
    ) -> Pattern[str]:
        """Create a compiled regex pattern with optional modifier prefix.

        Builds a regex that matches lines starting with optional whitespace,
        followed by an optional modifier keyword, then the base pattern.

        Args:
            base_pattern: The core regex pattern to match (without anchors).
            modifiers: Optional list of modifier keywords (e.g., ['public', 'private']).

        Returns:
            A compiled regex Pattern object.

        Example:
            >>> parser._create_pattern(r'def\\s+(\\w+)', ['async', 'static'])
            # Matches: "  async def foo" or "static def bar" or "def baz"
        """
        if modifiers:
            escaped_modifiers = [re.escape(m) for m in modifiers]
            modifier_pattern = f"(?:{'|'.join(escaped_modifiers)})\\s+"
            return re.compile(f"^\\s*(?:{modifier_pattern})?{base_pattern}")
        return re.compile(f"^\\s*{base_pattern}")

    def extract_docstring(self, lines: list[str], start: int, end: int) -> str | None:
        """Extract a docstring from triple-quoted text within a line range.

        Searches for Python-style triple-quoted strings (single or double) and extracts
        the content between them. Handles both single-line and multi-line docstrings.

        Args:
            lines: List of source code lines.
            start: The 0-indexed start line to begin searching.
            end: The 0-indexed end line (inclusive) to stop searching.

        Returns:
            The extracted docstring content with surrounding quotes removed,
            or None if no docstring is found in the range.
        """
        for i in range(start, min(end + 1, len(lines))):
            line = lines[i].strip()
            if line.startswith('"""') or line.startswith("'''"):
                doc_lines: list[str] = []
                quote = line[:3]
                if line.endswith(quote) and len(line) > 3:
                    return line[3:-3].strip()
                doc_lines.append(line[3:])
                for j in range(i + 1, min(end + 1, len(lines))):
                    line2 = lines[j].strip()
                    if line2.endswith(quote):
                        doc_lines.append(line2[:-3])
                        return "\n".join(doc_lines).strip()
                    doc_lines.append(line2)
        return None
