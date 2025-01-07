"""Python code parser for CodeConcat."""

import re
from typing import List, Dict, Pattern
from codeconcat.types import ParsedFileData, Declaration
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol

class PythonParser(BaseParser):
    """Python language parser."""
    
    def _setup_patterns(self):
        """Set up Python-specific patterns."""
        self.patterns = {
            'class': re.compile(
                r'^(?P<modifiers>(?:@\w+\s+)*)'  # Decorators
                r'class\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)'  # Class name
                r'\s*(?:\([^)]*\))?\s*:'  # Optional parent class
            ),
            'function': re.compile(
                r'^(?P<modifiers>(?:@\w+\s+)*)'  # Decorators
                r'(?:async\s+)?def\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)'  # Function name
                r'\s*\([^)]*\)\s*(?:->[^:]+)?:'  # Args and optional return type
            ),
            'constant': re.compile(
                r'^(?P<name>[A-Z][A-Z0-9_]*)\s*='  # Constants (UPPER_CASE)
            ),
            'variable': re.compile(
                r'^(?P<name>[a-z][a-z0-9_]*)\s*='  # Variables (lower_case)
                r'(?!.*(?:def|class)\s)'  # Not part of function/class definition
            )
        }
        
        self.modifiers = {'@classmethod', '@staticmethod', '@property', '@abstractmethod'}
        self.block_start = ':'
        self.block_end = None  # Python uses indentation
        self.line_comment = '#'
        self.block_comment_start = '"""'
        self.block_comment_end = '"""'
        
    def parse(self, content: str) -> List[Declaration]:
        """Parse Python code content."""
        lines = content.split('\n')
        symbols = []
        indent_stack = [0]
        current_indent = 0
        pending_decorators = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith(self.line_comment):
                i += 1
                continue
            
            # Handle docstrings
            if stripped.startswith('"""') or stripped.startswith("'''"):
                doc_end = self._find_docstring_end(lines, i)
                if doc_end > i:
                    if self.current_symbol and not self.current_symbol.docstring:
                        self.current_symbol.docstring = '\n'.join(lines[i:doc_end+1])
                    i = doc_end + 1
                    continue
            
            # Collect decorators
            if stripped.startswith('@'):
                pending_decorators.append(stripped)
                i += 1
                continue
            
            # Calculate indentation
            current_indent = len(line) - len(stripped)
            
            # Handle dedents
            while current_indent < indent_stack[-1]:
                indent_stack.pop()
                if self.symbol_stack:
                    symbol = self.symbol_stack.pop()
                    symbol.end_line = i - 1
                    symbols.append(symbol)
            
            # Look for new definitions
            for kind, pattern in self.patterns.items():
                match = pattern.match(stripped)
                if match:
                    name = match.group('name')
                    modifiers = set(pending_decorators)
                    pending_decorators = []  # Clear pending decorators
                    
                    symbol = CodeSymbol(
                        name=name,
                        kind=kind,
                        start_line=i - len(modifiers),  # Account for decorators
                        end_line=i,
                        modifiers=modifiers,
                        parent=self.symbol_stack[-1] if self.symbol_stack else None
                    )
                    
                    if kind in ('class', 'function'):
                        indent_stack.append(current_indent)
                        self.symbol_stack.append(symbol)
                    else:
                        symbols.append(symbol)
                    break
            else:
                # If no pattern matched, clear pending decorators
                pending_decorators = []
            
            i += 1
        
        # Close any remaining open symbols
        while self.symbol_stack:
            symbol = self.symbol_stack.pop()
            symbol.end_line = len(lines) - 1
            symbols.append(symbol)
        
        # Convert to Declarations for backward compatibility
        return [
            Declaration(
                symbol.kind,
                symbol.name,
                symbol.start_line + 1,
                symbol.end_line + 1
            ) for symbol in symbols
        ]
    
    def _find_docstring_end(self, lines: List[str], start: int) -> int:
        """Find the end of a docstring."""
        quote = '"""' if lines[start].strip().startswith('"""') else "'''"
        for i in range(start + 1, len(lines)):
            if quote in lines[i]:
                return i
        return start

def parse_python(file_path: str, content: str) -> ParsedFileData:
    """Parse Python code and return ParsedFileData."""
    parser = PythonParser()
    declarations = parser.parse(content)
    return ParsedFileData(
        file_path=file_path,
        language="python",
        content=content,
        declarations=declarations
    )
