# file: codeconcat/parser/language_parsers/base_parser.py

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Pattern, Set, Tuple

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

    def __init__(self):
        self.symbols: List[CodeSymbol] = []
        self.current_symbol: Optional[CodeSymbol] = None
        self.symbol_stack: List[CodeSymbol] = []
        self._setup_patterns()

    @abstractmethod
    def _setup_patterns(self):
        self.patterns: Dict[str, Pattern] = {}
        self.modifiers: Set[str] = set()
        self.block_start: str = "{"
        self.block_end: str = "}"
        self.line_comment: str = "//"
        self.block_comment_start: str = "/*"
        self.block_comment_end: str = "*/"

    def parse(self, content: str) -> List[Tuple[str, int, int]]:
        """
        A default naive parse that tries to identify code symbols via line-based scanning.
        Subclasses often override parse() with a more language-specific approach.
        """
        self.symbols = []
        self.current_symbol = None
        self.symbol_stack = []

        lines = content.split("\n")
        in_comment = False
        comment_buffer = []

        brace_count = 0  # naive brace count

        for i, line in enumerate(lines):
            stripped_line = line.strip()

            # Handle block comments
            if self.block_comment_start in line and not in_comment:
                in_comment = True
                comment_start = line.index(self.block_comment_start)
                comment_buffer.append(line[comment_start + len(self.block_comment_start):])
                continue

            if in_comment:
                if self.block_comment_end in line:
                    in_comment = False
                    comment_end = line.index(self.block_comment_end)
                    comment_buffer.append(line[:comment_end])
                    # Optionally, store docstrings if needed
                    comment_buffer = []
                else:
                    comment_buffer.append(line)
                continue

            # Skip line comments
            if stripped_line.startswith(self.line_comment):
                continue

            # Basic brace tracking
            brace_count += line.count(self.block_start) - line.count(self.block_end)

            # Attempt naive matching
            if not self.current_symbol:
                for kind, pattern in self.patterns.items():
                    match = pattern.match(line)
                    if match:
                        # Typically, we look for match.group("name"), but must confirm
                        if "name" in match.groupdict():
                            name = match.group("name") or ""
                        else:
                            continue

                        # Possibly gather modifiers
                        mods = set()
                        if "modifiers" in match.groupdict() and match.group("modifiers"):
                            raw_mods = match.group("modifiers").split()
                            mods = {m.strip() for m in raw_mods if m.strip()}

                        symbol = CodeSymbol(
                            name=name,
                            kind=kind,
                            start_line=i,
                            end_line=i,
                            modifiers=mods & self.modifiers,
                        )
                        if self.symbol_stack:
                            symbol.parent = self.symbol_stack[-1]
                            self.symbol_stack[-1].children.append(symbol)

                        self.current_symbol = symbol
                        self.symbol_stack.append(symbol)
                        break

            if self.current_symbol and brace_count == 0:
                if (self.block_end in line) or (";" in line):
                    self.current_symbol.end_line = i
                    self.symbols.append(self.current_symbol)
                    if self.symbol_stack:
                        self.symbol_stack.pop()
                    self.current_symbol = self.symbol_stack[-1] if self.symbol_stack else None

        return [(s.name, s.start_line, s.end_line) for s in self.symbols]

    def _create_pattern(self, base_pattern: str, modifiers: Optional[List[str]] = None) -> Pattern:
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