# file: codeconcat/parser/language_parsers/base_parser.py

import re
from abc import ABC
from dataclasses import dataclass
from typing import Dict, List, Optional, Pattern, Set

from codeconcat.base_types import Declaration, ParseResult


@dataclass
class CodeSymbol:
    name: str
    kind: str
    start_line: int
    end_line: int
    modifiers: Set[str]
    parent: Optional["CodeSymbol"] = None
    children: List["CodeSymbol"] = None
    docstring: Optional[str] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []


class BaseParser(ABC):
    """
    BaseParser defines a minimal interface and partial logic for line-based scanning
    and comment extraction. Subclasses typically override _setup_patterns() and parse().
    """

    def __init__(self, file_path: str = ""):
        """Initialize the parser with default values."""
        self.symbols: List[CodeSymbol] = []
        self.current_symbol: Optional[CodeSymbol] = None
        self.symbol_stack: List[CodeSymbol] = []
        self.block_start = "{"  # Default block start
        self.block_end = "}"  # Default block end
        self.line_comment = None  # Default line comment
        self.block_comment_start = None  # Default block comment start
        self.block_comment_end = None  # Default block comment end
        self.patterns: Dict[str, Pattern] = {}
        self.modifiers: Set[str] = set()
        # Use Unicode word character class \w to match Unicode identifiers
        self.identifier_pattern = re.compile(r"[\w\u0080-\uffff]+")
        # Store the file path for use in ParseResult
        self.current_file_path = file_path

    def parse(self, content: str) -> ParseResult:
        """Parse code content and return list of declarations."""
        self.symbols = []
        self.current_symbol = None
        self.symbol_stack = []

        # Track seen declarations to avoid duplicates
        seen_declarations = set()  # (name, start_line, kind) tuples

        lines = content.split("\n")
        in_comment = False
        comment_buffer = []
        brace_count = 0

        for i, line in enumerate(lines):
            stripped_line = line.strip()

            # Handle block comments
            if self.block_comment_start in line and not in_comment:
                in_comment = True
                comment_start = line.index(self.block_comment_start)
                comment_buffer.append(
                    line[comment_start + len(self.block_comment_start) :]
                )
                continue

            if in_comment:
                if self.block_comment_end in line:
                    in_comment = False
                    comment_end = line.index(self.block_comment_end)
                    comment_buffer.append(line[:comment_end])
                    comment_buffer = []
                else:
                    comment_buffer.append(line)
                continue

            # Skip line comments
            if stripped_line.startswith(self.line_comment):
                continue

            # Basic brace tracking
            if self.block_start is not None and self.block_end is not None:
                brace_count += line.count(self.block_start) - line.count(self.block_end)

            # Try to match patterns
            for kind, pattern in self.patterns.items():
                match = pattern.match(stripped_line)
                if match:
                    name = match.group("n")  # Use "n" instead of "name"
                    if not name:
                        continue

                    # Check if we've seen this declaration before
                    declaration_key = (name, i, kind)
                    if declaration_key in seen_declarations:
                        continue
                    seen_declarations.add(declaration_key)

                    # Find block end for block-based declarations
                    end_line = i
                    if kind in (
                        "class",
                        "function",
                        "method",
                        "interface",
                        "struct",
                        "enum",
                    ):
                        end_line = self._find_block_end(lines, i)

                    # Extract docstring if present
                    docstring = None
                    if end_line > i:
                        docstring = self.extract_docstring(lines, i, end_line)

                    # Create new symbol
                    symbol = CodeSymbol(
                        name=name,
                        kind=kind,
                        start_line=i,
                        end_line=end_line,
                        modifiers=set(),
                        docstring=docstring,
                    )

                    # Handle symbol hierarchy
                    if self.current_symbol:
                        symbol.parent = self.current_symbol
                        self.current_symbol.children.append(symbol)
                    else:
                        self.symbols.append(symbol)

                    # Update current symbol for nested declarations
                    if kind in ("class", "interface", "struct"):
                        self.symbol_stack.append(self.current_symbol)
                        self.current_symbol = symbol

            # Handle end of block
            if self.current_symbol and brace_count == 0:
                self.current_symbol = (
                    self.symbol_stack.pop() if self.symbol_stack else None
                )

        # Convert symbols to tuples
        declarations = []
        for symbol in self.symbols:
            declarations.extend(self._flatten_symbol(symbol))
        return declarations

    def _flatten_symbol(self, symbol: CodeSymbol) -> List[Declaration]:
        """Flatten a symbol and its children into a list of declaration tuples."""
        declarations = [(symbol.name, symbol.start_line, symbol.end_line)]
        for child in symbol.children:
            declarations.extend(self._flatten_symbol(child))
        return declarations

    def _find_block_end(self, lines: List[str], start: int) -> int:
        """Find the end of a code block."""
        if self.block_start is None or self.block_end is None:
            return start

        line = lines[start]
        if self.block_start not in line:
            return start

        brace_count = line.count(self.block_start) - line.count(self.block_end)
        if brace_count <= 0:
            return start

        for i in range(start + 1, len(lines)):
            line = lines[i].strip()
            if line.startswith(self.line_comment):
                continue
            brace_count += line.count(self.block_start) - line.count(self.block_end)
            if brace_count <= 0:
                return i

        return len(lines) - 1

    def _create_pattern(
        self, base_pattern: str, modifiers: Optional[List[str]] = None
    ) -> Pattern:
        if modifiers:
            modifier_pattern = f"(?:{'|'.join(modifiers)})\\s+"
            return re.compile(f"^\\s*(?:{modifier_pattern})?{base_pattern}")
        return re.compile(f"^\\s*{base_pattern}")

    @staticmethod
    def extract_docstring(lines: List[str], start: int, end: int) -> Optional[str]:
        """
        Example extraction for docstring-like text between triple quotes or similar.
        Subclasses can override or use as needed.
        """
        for i in range(start, min(end + 1, len(lines))):
            line = lines[i].strip()
            if line.startswith('"""') or line.startswith("'''"):
                doc_lines = []
                quote = line[:3]
                if line.endswith(quote) and len(line) > 3:
                    return line[3:-3].strip()
                doc_lines.append(line[3:])
                for j in range(i + 1, end + 1):
                    line2 = lines[j].strip()
                    if line2.endswith(quote):
                        doc_lines.append(line2[:-3])
                        return "\n".join(doc_lines).strip()
                    doc_lines.append(line2)
        return None
