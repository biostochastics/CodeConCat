# file: codeconcat/parser/language_parsers/base_parser.py

import re
from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Pattern, Set

from codeconcat.base_types import Declaration, ParseResult, ParserInterface

__all__ = ["BaseParser", "CodeSymbol", "ParserInterface"]


@dataclass
class CodeSymbol:
    """A class to represent a symbol in a codebase, such as a variable, function, or class.
    Parameters:
        - name (str): The name of the code symbol.
        - kind (str): The kind of the symbol (e.g., variable, function, class).
        - start_line (int): The line number where the symbol starts in the code.
        - end_line (int): The line number where the symbol ends in the code.
        - modifiers (Set[str]): A set of modifiers associated with the symbol (e.g., public, private).
        - parent (Optional[CodeSymbol]): The parent symbol, if this symbol is nested within another.
        - children (List[CodeSymbol]): A list of child symbols nested within this symbol.
        - docstring (Optional[str]): The associated docstring of the code symbol, if present.
    Processing Logic:
        - Represents hierarchical code structures where symbols can be nested within each other.
        - Captures the location of the symbols in the code for reference or analysis."""
    name: str
    kind: str
    start_line: int
    end_line: int
    modifiers: Set[str]
    parent: Optional["CodeSymbol"] = None
    children: List["CodeSymbol"] = field(default_factory=list)
    docstring: Optional[str] = None


class BaseParser(ParserInterface):
    """
    BaseParser defines a minimal interface and partial logic for line-based scanning
    and comment extraction. Subclasses typically override _setup_patterns() and parse().
    """

    def __init__(self, _file_path: str = ""):
        """Initialize the parser with default values."""
        self.symbols: List[CodeSymbol] = []
        self.current_symbol: Optional[CodeSymbol] = None
        self.symbol_stack: List[CodeSymbol] = []
        self.block_start = "{"  # Default block start
        self.block_end = "}"  # Default block end
        self.line_comment: str | None = None  # Default line comment
        self.block_comment_start: str | None = None  # Default block comment start
        self.block_comment_end: str | None = None  # Default block comment end
        self.patterns: Dict[str, Pattern[str]] = {}
        self.modifiers: Set[str] = set()
        # Use Unicode word character class \w to match Unicode identifiers
        self.identifier_pattern = re.compile(r"[\w\u0080-\uffff]+")

    @abstractmethod
    def parse(self, content: str, file_path: str) -> ParseResult:
        """Parse code content and return a ParseResult object.

        Subclasses must implement this method.

        Args:
            content: The code content as a string.
            file_path: The path to the file being parsed.

        Returns:
            A ParseResult object.
        """
        raise NotImplementedError("Subclasses must implement the parse method.")

    def _flatten_symbol(self, symbol: CodeSymbol) -> List[Declaration]:
        """Flatten a symbol and its children into a list of declarations."""
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
            if self.line_comment and line.startswith(self.line_comment):
                continue
            brace_count += line.count(self.block_start) - line.count(self.block_end)
            if brace_count <= 0:
                return i

        return len(lines) - 1

    def _create_pattern(self, base_pattern: str, modifiers: Optional[List[str]] = None) -> Pattern:
        if modifiers:
            modifier_pattern = f"(?:{'|'.join(modifiers)})\\s+"
            return re.compile(f"^\\s*(?:{modifier_pattern})?{base_pattern}")
        return re.compile(f"^\\s*{base_pattern}")

    def extract_docstring(self, lines: List[str], start: int, end: int) -> Optional[str]:
        """
        Example extraction for docstring-like text between triple quotes or similar.
        Subclasses can override or use as needed.
        """
        for i in range(start, min(end + 1, len(lines))):
            line = lines[i].strip()
            if line.startswith('"""') or line.startswith("'''"):
                doc_lines: list[str] = []
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
