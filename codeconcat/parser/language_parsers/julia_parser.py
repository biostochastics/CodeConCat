"""Julia code parser for CodeConcat."""

import re
from typing import List, Dict, Pattern
from codeconcat.types import ParsedFileData, Declaration
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol

class JuliaParser(BaseParser):
    """Julia language parser."""
    
    def _setup_patterns(self):
        """Set up Julia-specific patterns."""
        self.patterns = {
            'function': re.compile(
                r'^(?P<modifiers>(?:export\s+)?)'  # Optional export
                r'function\s+(?P<func_name>[a-zA-Z_][a-zA-Z0-9_]*)'  # Function name
                r'\s*\((?P<parameters>[^)]*)\)'  # Parameters
                r'(?:\s*::\s*(?P<return_type>[^{;]+))?'  # Optional return type
            ),
            'struct': re.compile(
                r'^(?P<modifiers>(?:export\s+)?(?:mutable\s+)?)'  # Modifiers
                r'struct\s+(?P<struct_name>[a-zA-Z_][a-zA-Z0-9_]*)'  # Struct name
                r'(?:\s*<:\s*(?P<supertype>[^{]+))?'  # Optional supertype
            ),
            'abstract': re.compile(
                r'^(?P<modifiers>(?:export\s+)?)'  # Optional export
                r'abstract\s+type\s+(?P<type_name>[a-zA-Z_][a-zA-Z0-9_]*)'  # Type name
                r'(?:\s*<:\s*(?P<supertype>[^{]+))?'  # Optional supertype
            ),
            'module': re.compile(
                r'^(?P<modifiers>(?:export\s+)?)'  # Optional export
                r'module\s+(?P<module_name>[a-zA-Z_][a-zA-Z0-9_]*)'  # Module name
            ),
            'const': re.compile(
                r'^(?P<modifiers>(?:export\s+)?)'  # Optional export
                r'const\s+(?P<const_name>[A-Z][A-Z0-9_]*)'  # Constant name
                r'(?:\s*::\s*(?P<type>[^=]+))?'  # Optional type annotation
                r'\s*='  # Assignment
            ),
            'macro': re.compile(
                r'^(?P<modifiers>(?:export\s+)?)'  # Optional export
                r'macro\s+(?P<macro_name>[a-zA-Z_][a-zA-Z0-9_]*)'  # Macro name
                r'\s*\((?P<parameters>[^)]*)\)'  # Parameters
            ),
            'variable': re.compile(
                r'^(?P<var_name>[a-z][a-z0-9_]*)'  # Variable name
                r'(?:\s*::\s*(?P<type>[^=]+))?'  # Optional type annotation
                r'\s*=\s*(?!.*(?:function|struct|mutable|module|macro))'  # Assignment, not a definition
            )
        }
        
        self.modifiers = {'export', 'mutable'}
        self.block_start = 'begin'
        self.block_end = 'end'
        self.line_comment = '#'
        self.block_comment_start = '#='
        self.block_comment_end = '=#'
        
    def parse(self, content: str) -> List[Declaration]:
        """Parse Julia code content."""
        lines = content.split('\n')
        symbols = []
        brace_count = 0
        in_comment = False
        current_module = None
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
                
            # Handle block comments
            if line.startswith('#='):
                in_comment = True
                if '=#' in line[2:]:
                    in_comment = False
                i += 1
                continue
                
            if in_comment:
                if '=#' in line:
                    in_comment = False
                i += 1
                continue
                
            # Skip line comments
            if line.startswith('#'):
                i += 1
                continue
                
            # Look for declarations
            for kind, pattern in self.patterns.items():
                match = pattern.match(line)
                if match:
                    name = match.group(f'{kind}_name')
                    modifiers = set()
                    if 'modifiers' in match.groupdict() and match.group('modifiers'):
                        modifiers = {m.strip() for m in match.group('modifiers').split()}
                    
                    # Create symbol
                    symbol = CodeSymbol(
                        name=name,
                        kind=kind,
                        start_line=i,
                        end_line=i,
                        modifiers=modifiers,
                        parent=current_module
                    )
                    
                    # Handle block-level constructs
                    if kind in ('function', 'struct', 'abstract', 'module', 'macro'):
                        j = i + 1
                        block_level = 1
                        while j < len(lines) and block_level > 0:
                            if 'begin' in lines[j] or kind in lines[j]:
                                block_level += 1
                            if 'end' in lines[j]:
                                block_level -= 1
                            j += 1
                        symbol.end_line = j - 1
                        i = j - 1
                        
                        # Update current module context
                        if kind == 'module':
                            current_module = symbol
                    
                    symbols.append(symbol)
                    break
            
            i += 1
        
        # Convert to Declarations for backward compatibility
        return [
            Declaration(
                symbol.kind,
                symbol.name,
                symbol.start_line + 1,
                symbol.end_line + 1
            ) for symbol in symbols
        ]

def parse_julia(file_path: str, content: str) -> ParsedFileData:
    """Parse Julia code and return ParsedFileData."""
    parser = JuliaParser()
    declarations = parser.parse(content)
    return ParsedFileData(
        file_path=file_path,
        language="julia",
        content=content,
        declarations=declarations
    )
