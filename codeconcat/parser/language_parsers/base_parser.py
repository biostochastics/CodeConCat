"""Base parser class for language-specific parsers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Pattern, Tuple, Set
import re

@dataclass
class CodeSymbol:
    """Represents a code symbol (function, class, etc.)."""
    name: str
    kind: str
    start_line: int
    end_line: int
    modifiers: Set[str]
    parent: Optional['CodeSymbol'] = None
    children: List['CodeSymbol'] = None
    docstring: Optional[str] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []

class BaseParser(ABC):
    """Base class for all language parsers."""
    
    def __init__(self):
        self.symbols: List[CodeSymbol] = []
        self.current_symbol: Optional[CodeSymbol] = None
        self.symbol_stack: List[CodeSymbol] = []
        self._setup_patterns()

    @abstractmethod
    def _setup_patterns(self):
        """Set up regex patterns for the specific language."""
        self.patterns: Dict[str, Pattern] = {}
        self.modifiers: Set[str] = set()
        self.block_start: str = '{'
        self.block_end: str = '}'
        self.line_comment: str = '//'
        self.block_comment_start: str = '/*'
        self.block_comment_end: str = '*/'

    def parse(self, content: str) -> List[Tuple[str, int, int]]:
        """Parse code content and return symbols."""
        self.symbols = []
        self.current_symbol = None
        self.symbol_stack = []
        
        lines = content.split('\n')
        in_comment = False
        brace_count = 0
        comment_buffer = []
        
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            
            # Handle comments
            if self.block_comment_start in line and not in_comment:
                in_comment = True
                comment_start = line.index(self.block_comment_start)
                comment_buffer.append(line[comment_start + 2:])
                continue
                
            if in_comment:
                if self.block_comment_end in line:
                    in_comment = False
                    comment_end = line.index(self.block_comment_end)
                    comment_buffer.append(line[:comment_end])
                    if self.current_symbol and not self.current_symbol.docstring:
                        self.current_symbol.docstring = '\n'.join(comment_buffer).strip()
                    comment_buffer = []
                else:
                    comment_buffer.append(line)
                continue
                
            if stripped_line.startswith(self.line_comment):
                continue
                
            # Track braces for block detection
            if not self.current_symbol:
                # Look for new symbol definitions
                for kind, pattern in self.patterns.items():
                    match = pattern.match(line)
                    if match:
                        name = match.group('name')
                        modifiers = set(m.strip() for m in match.group('modifiers').split()) \
                                  if 'modifiers' in match.groupdict() else set()
                        
                        symbol = CodeSymbol(
                            name=name,
                            kind=kind,
                            start_line=i,
                            end_line=i,
                            modifiers=modifiers & self.modifiers
                        )
                        
                        if self.symbol_stack:
                            symbol.parent = self.symbol_stack[-1]
                            self.symbol_stack[-1].children.append(symbol)
                            
                        self.current_symbol = symbol
                        self.symbol_stack.append(symbol)
                        break
                        
            # Track block boundaries
            brace_count += line.count(self.block_start) - line.count(self.block_end)
            
            # Handle end of block
            if self.current_symbol and brace_count == 0:
                if self.block_end in line or ';' in line:
                    self.current_symbol.end_line = i
                    self.symbols.append(self.current_symbol)
                    self.symbol_stack.pop()
                    self.current_symbol = self.symbol_stack[-1] if self.symbol_stack else None
        
        # Convert to the expected tuple format for backward compatibility
        return [(s.name, s.start_line, s.end_line) for s in self.symbols]

    def _create_pattern(self, base_pattern: str, modifiers: Optional[List[str]] = None) -> Pattern:
        """Create a regex pattern with optional modifiers."""
        if modifiers:
            modifier_pattern = f"(?:(?:{' |'.join(modifiers)})\\s+)*"
            return re.compile(f"^\\s*{modifier_pattern}?{base_pattern}")
        return re.compile(f"^\\s*{base_pattern}")

    @staticmethod
    def extract_docstring(lines: List[str], start: int, end: int) -> Optional[str]:
        """Extract docstring from code lines."""
        for i in range(start, min(end + 1, len(lines))):
            line = lines[i].strip()
            if line.startswith('"""') or line.startswith("'''"):
                doc_lines = []
                quote = line[:3]
                if line.endswith(quote) and len(line) > 3:
                    return line[3:-3].strip()
                doc_lines.append(line[3:])
                for j in range(i + 1, end + 1):
                    line = lines[j].strip()
                    if line.endswith(quote):
                        doc_lines.append(line[:-3])
                        return '\n'.join(doc_lines).strip()
                    doc_lines.append(line)
        return None
