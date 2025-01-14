"""Python code parser for CodeConcat."""

import re
from typing import List, Optional

from codeconcat.base_types import Declaration, ParsedFileData
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol


def parse_python(file_path: str, content: str) -> ParsedFileData:
    """Parse Python code and return ParsedFileData."""
    parser = PythonParser()
    declarations = parser.parse(content)
    return ParsedFileData(
        file_path=file_path, language="python", content=content, declarations=declarations
    )


class PythonParser(BaseParser):
    """Python language parser."""

    def __init__(self):
        super().__init__()
        self._setup_patterns()

    def _setup_patterns(self):
        """
        Enhanced patterns for Python:
        - We define one pattern for 'class' and 'function' that can handle decorators,
          but we rely on the logic in parse() to gather multiple lines if needed.
        """
        # Common pattern for names
        name = r"[a-zA-Z_][a-zA-Z0-9_]*"
        
        self.patterns = {
            "class": re.compile(
                r"^class\s+(?P<n>" + name + r")"  # Class name
                r"(?:\s*\([^)]*\))?"  # Optional parent class
                r"\s*:"  # Class definition end
            ),
            "function": re.compile(
                r"^(?:async\s+)?def\s+(?P<n>" + name + r")"  # Function name with optional async
                r"\s*\([^)]*\)?"  # Function parameters, optional closing parenthesis
                r"\s*(?:->[^:]+)?"  # Optional return type
                r"\s*:?"  # Optional colon (for multi-line definitions)
            ),
            "variable": re.compile(
                r"^(?P<n>[a-z_][a-zA-Z0-9_]*)\s*"  # Variable name
                r"(?::\s*[^=\s]+)?"  # Optional type annotation
                r"\s*=\s*[^=]"  # Assignment but not comparison
            ),
            "constant": re.compile(
                r"^(?P<n>[A-Z][A-Z0-9_]*)\s*"  # Constant name
                r"(?::\s*[^=\s]+)?"  # Optional type annotation
                r"\s*=\s*[^=]"  # Assignment but not comparison
            ),
            "decorator": re.compile(
                r"^@(?P<n>[a-zA-Z_][\w.]*)(?:\s*\([^)]*\))?"  # Decorator with optional args
            )
        }
        
        # Python doesn't always rely on '{' or '}', so we use the base logic for line by line
        self.block_start = ":"
        self.block_end = None
        self.line_comment = "#"
        self.block_comment_start = '"""'
        self.block_comment_end = '"""'
        
        # Our recognized modifiers (for demonstration)
        self.modifiers = {
            "@classmethod",
            "@staticmethod",
            "@property",
            "@abstractmethod",
        }

    def parse(self, content: str) -> List[Declaration]:
        """Parse Python code with improved decorator and docstring handling."""
        lines = content.split("\n")
        self.symbols = []
        self.current_symbol = None
        self.symbol_stack = []
        
        # States for multi-line handling
        pending_decorators = []
        current_def_lines = []
        in_multiline_decorator = False
        in_function_def = False
        function_start_line = 0
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                i += 1
                continue
                
            # Handle multi-line decorators
            if stripped.startswith("@"):
                pending_decorators.append(stripped)
                if "(" in stripped and ")" not in stripped:
                    in_multiline_decorator = True
                i += 1
                continue
                
            if in_multiline_decorator:
                pending_decorators[-1] += " " + stripped
                if ")" in stripped:
                    in_multiline_decorator = False
                i += 1
                continue
                
            # Calculate current indentation
            indent = len(line) - len(stripped)
            
            # Pop symbol stack while current indent is less than or equal to previous levels
            while self.symbol_stack and indent <= (len(lines[self.symbol_stack[-1].start_line - 1]) - len(lines[self.symbol_stack[-1].start_line - 1].lstrip())):
                self.symbol_stack.pop()
                
            # Handle multi-line function definitions
            if in_function_def:
                current_def_lines.append(line)
                if stripped.endswith(":"):
                    # Process the complete function definition
                    combined_def = " ".join(l.strip() for l in current_def_lines)
                    # Try to match the complete function definition
                    match = self.patterns["function"].match(combined_def)
                    if not match:
                        # Try matching just the first line
                        first_line = current_def_lines[0].strip()
                        match = self.patterns["function"].match(first_line)
                    
                    if match:
                        name = match.group("n")
                        end_line = self._find_block_end(lines, i, indent)
                        if end_line <= i:
                            end_line = i + 1
                            
                        # Extract docstring
                        docstring = self.extract_docstring(lines, i + 1, end_line)
                        
                        # Create symbol
                        symbol = CodeSymbol(
                            name=name,
                            kind="function",
                            start_line=function_start_line + 1,
                            end_line=end_line + 1,
                            modifiers=set(pending_decorators),
                            docstring=docstring,
                            parent=self.symbol_stack[-1] if self.symbol_stack else None,
                            children=[]
                        )
                        
                        # Add to parent's children if we have a parent
                        if self.symbol_stack and symbol.parent:
                            symbol.parent.children.append(symbol)
                        else:
                            self.symbols.append(symbol)
                            
                        # Push onto stack for nested functions
                        self.symbol_stack.append(symbol)
                        
                    # Reset states
                    in_function_def = False
                    current_def_lines = []
                    pending_decorators = []
                i += 1
                continue
            
            # Try matching patterns
            matched = False
            for kind, pattern in self.patterns.items():
                match = pattern.match(stripped)
                if not match:
                    continue

                name = match.group("n")
                    
                if kind == "function":
                    # Check if this is a multi-line function definition
                    if "(" in stripped and ")" not in stripped or not stripped.endswith(":"):
                        in_function_def = True
                        current_def_lines = [line]
                        function_start_line = i
                        matched = True
                        break
                    else:
                        end_line = self._find_block_end(lines, i, indent)
                        if end_line <= i:
                            end_line = i + 1
                            
                        # Extract docstring
                        docstring = self.extract_docstring(lines, i + 1, end_line)
                        
                        symbol = CodeSymbol(
                            name=name,
                            kind="function",
                            start_line=i + 1,
                            end_line=end_line + 1,
                            modifiers=set(pending_decorators),
                            docstring=docstring,
                            parent=self.symbol_stack[-1] if self.symbol_stack else None,
                            children=[]
                        )
                        
                        # Add to parent's children if we have a parent
                        if self.symbol_stack and symbol.parent:
                            symbol.parent.children.append(symbol)
                        else:
                            self.symbols.append(symbol)
                            
                        # Push onto stack for nested functions
                        self.symbol_stack.append(symbol)
                        
                        # Reset states
                        pending_decorators = []
                        matched = True
                        i += 1
                        break
                elif kind == "class":
                    end_line = self._find_block_end(lines, i, indent)
                    if end_line <= i:
                        end_line = i + 1
                            
                    # Extract docstring
                    docstring = self.extract_docstring(lines, i + 1, end_line)
                    
                    symbol = CodeSymbol(
                        name=name,
                        kind=kind,
                        start_line=i + 1,
                        end_line=end_line + 1,
                        modifiers=set(pending_decorators),
                        docstring=docstring,
                        parent=self.symbol_stack[-1] if self.symbol_stack else None,
                        children=[]
                    )
                    
                else:  # variable or constant
                    symbol = CodeSymbol(
                        name=name,
                        kind=kind,
                        start_line=i + 1,
                        end_line=i + 1,
                        modifiers=set(),
                        parent=self.symbol_stack[-1] if self.symbol_stack else None,
                        children=[]
                    )
                    
                # Add to parent's children if we have a parent
                if self.symbol_stack and symbol.parent:
                    symbol.parent.children.append(symbol)
                else:
                    self.symbols.append(symbol)
                    
                # Push onto stack for nested definitions
                if kind in ("class", "function"):
                    self.symbol_stack.append(symbol)
                    
                # Reset states
                pending_decorators = []
                matched = True
                i += 1
                break
                    
            if not matched and not in_function_def:
                pending_decorators = []
                i += 1
                
        # Convert symbols to declarations, including nested symbols
        def convert_symbols(symbols: List[CodeSymbol]) -> List[Declaration]:
            declarations = []
            for symbol in symbols:
                declarations.append(Declaration(
                    kind=symbol.kind,
                    name=symbol.name,
                    start_line=symbol.start_line,
                    end_line=symbol.end_line,
                    modifiers=symbol.modifiers,
                    docstring=symbol.docstring
                ))
                if symbol.children:
                    declarations.extend(convert_symbols(symbol.children))
            return declarations
            
        return convert_symbols(self.symbols)

    def _find_block_end(self, lines: List[str], start: int, base_indent: int) -> int:
        """Find the end of a Python code block based on indentation."""
        i = start + 1
        max_lines = len(lines)
        
        # Handle edge case where we're at the end of the file
        if i >= max_lines:
            return start
        
        # Skip empty lines at the start
        while i < max_lines and not lines[i].strip():
            i += 1
            
        # If we hit the end of the file, return the last non-empty line
        if i >= max_lines:
            return max_lines - 1
            
        # Get the indentation of the first non-empty line
        first_line = lines[i]
        block_indent = len(first_line) - len(first_line.lstrip())
        
        # If the first line isn't indented more than the base, this is an empty block
        if block_indent <= base_indent:
            return start
            
        while i < max_lines:
            line = lines[i].rstrip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
                
            # Calculate indentation of current line
            indent = len(line) - len(line.lstrip())
            
            # If we find a line with same or less indentation, we've found the end
            if indent <= base_indent:
                return i - 1
                
            i += 1
            
        # If we reach the end of the file, return the last line
        return max_lines - 1
