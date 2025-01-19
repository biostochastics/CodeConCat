# file: codeconcat/parser/language_parsers/julia_parser.py

import re
from typing import List, Optional, Set
from codeconcat.base_types import Declaration, ParsedFileData
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol

def parse_julia(file_path: str, content: str) -> Optional[ParsedFileData]:
    parser = JuliaParser()
    declarations = parser.parse_file(content)
    return ParsedFileData(
        file_path=file_path,
        language="julia",
        content=content,
        declarations=declarations
    )

class JuliaParser(BaseParser):
    def __init__(self):
        super().__init__()
        self._setup_patterns()

    def _setup_patterns(self):
        """Set up patterns for Julia code declarations."""
        self.patterns = {}
        
        # Julia uses 'end' as block end
        self.block_start = None
        self.block_end = None
        self.line_comment = "#"
        self.block_comment_start = "#="
        self.block_comment_end = "=#"

        # Function pattern (both long and short form)
        func_pattern = r"^\s*(?:function\s+)?(?P<n>[a-zA-Z_][a-zA-Z0-9_!]*)\s*\([^)]*\)(?:\s*where\s+\{[^}]*\})?\s*(?:=|$)"
        self.patterns["function"] = re.compile(func_pattern)

        # Struct pattern
        struct_pattern = r"^\s*(?:mutable\s+)?struct\s+(?P<n>[a-zA-Z_][a-zA-Z0-9_!]*)\s*(?:<:\s*[a-zA-Z_][a-zA-Z0-9_!]*\s*)?$"
        self.patterns["struct"] = re.compile(struct_pattern)

        # Abstract type pattern
        abstract_pattern = r"^\s*abstract\s+type\s+(?P<n>[a-zA-Z_][a-zA-Z0-9_!]*)\s*(?:<:\s*[a-zA-Z_][a-zA-Z0-9_!]*\s*)?$"
        self.patterns["abstract"] = re.compile(abstract_pattern)

        # Module pattern
        module_pattern = r"^\s*module\s+(?P<n>[a-zA-Z_][a-zA-Z0-9_!]*)\s*$"
        self.patterns["module"] = re.compile(module_pattern)

        # Macro pattern
        macro_pattern = r"^\s*macro\s+(?P<n>[a-zA-Z_][a-zA-Z0-9_!]*)\s*\([^)]*\)\s*$"
        self.patterns["macro"] = re.compile(macro_pattern)

        # Const pattern
        const_pattern = r"^\s*const\s+(?P<n>[a-zA-Z_][a-zA-Z0-9_!]*)\s*=\s*"
        self.patterns["const"] = re.compile(const_pattern)

    def parse_file(self, content: str) -> List[Declaration]:
        """Parse Julia file content and return list of declarations."""
        return self.parse(content)

    def parse(self, content: str) -> List[Declaration]:
        """Parse Julia code content and return list of declarations."""
        declarations = []
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                i += 1
                continue
                
            # Handle functions
            if line.startswith('function ') or ('(' in line and ')' in line and '=' in line):
                match = re.match(r'(?:function\s+)?(\w+)\s*\([^)]*\).*', line)
                if match:
                    name = match.group(1)
                    end_line = i
                    
                    # Find the end of the function
                    if line.startswith('function'):
                        j = i + 1
                        while j < len(lines):
                            curr_line = lines[j].strip()
                            if curr_line == 'end':
                                end_line = j
                                break
                            j += 1
                    
                    declarations.append(Declaration(
                        kind='function',
                        name=name,
                        start_line=i + 1,
                        end_line=end_line + 1,
                        modifiers=set(),
                        docstring=""
                    ))
                    i = end_line + 1
                    continue
            
            # Handle structs
            if line.startswith('struct ') or line.startswith('mutable struct '):
                match = re.match(r'(?:mutable\s+)?struct\s+(\w+)', line)
                if match:
                    name = match.group(1)
                    end_line = i
                    
                    # Find the end of the struct
                    j = i + 1
                    while j < len(lines):
                        curr_line = lines[j].strip()
                        if curr_line == 'end':
                            end_line = j
                            break
                        j += 1
                    
                    declarations.append(Declaration(
                        kind='struct',
                        name=name,
                        start_line=i + 1,
                        end_line=end_line + 1,
                        modifiers=set(),
                        docstring=""
                    ))
                    i = end_line + 1
                    continue
            
            # Handle abstract types
            if line.startswith('abstract type '):
                match = re.match(r'abstract\s+type\s+(\w+)(?:\s+<:\s+\w+)?', line)
                if match:
                    name = match.group(1)
                    end_line = i
                    
                    # Find the end if it's on a different line
                    if 'end' not in line:
                        j = i + 1
                        while j < len(lines):
                            curr_line = lines[j].strip()
                            if curr_line == 'end':
                                end_line = j
                                break
                            j += 1
                    
                    declarations.append(Declaration(
                        kind='abstract',
                        name=name,
                        start_line=i + 1,
                        end_line=end_line + 1,
                        modifiers=set(),
                        docstring=""
                    ))
                    i = end_line + 1
                    continue
            
            # Handle modules
            if line.startswith('module '):
                match = re.match(r'module\s+(\w+)', line)
                if match:
                    name = match.group(1)
                    module_start = i
                    module_end = i
                    
                    # Find the end of the module
                    j = i + 1
                    while j < len(lines):
                        curr_line = lines[j].strip()
                        if curr_line == 'end' or curr_line.startswith('end #'):
                            module_end = j
                            break
                        j += 1
                    
                    declarations.append(Declaration(
                        kind='module',
                        name=name,
                        start_line=i + 1,
                        end_line=module_end + 1,
                        modifiers=set(),
                        docstring=""
                    ))
                    
                    # Parse declarations within the module
                    module_content = '\n'.join(lines[module_start+1:module_end])
                    module_declarations = self.parse(module_content)
                    # Adjust line numbers for nested declarations
                    for decl in module_declarations:
                        decl.start_line += module_start + 1
                        decl.end_line += module_start + 1
                    declarations.extend(module_declarations)
                    
                    i = module_end + 1
                    continue
            
            # Handle macros and decorated functions
            if line.startswith('macro ') or line.startswith('@'):
                if line.startswith('macro '):
                    match = re.match(r'macro\s+(\w+)', line)
                    kind = 'macro'
                else:
                    match = re.match(r'@\w+\s+function\s+(\w+)', line)
                    kind = 'function'
                
                if match:
                    name = match.group(1)
                    end_line = i
                    
                    # Find the end of the macro/function
                    j = i + 1
                    while j < len(lines):
                        curr_line = lines[j].strip()
                        if curr_line == 'end':
                            end_line = j
                            break
                        j += 1
                    
                    declarations.append(Declaration(
                        kind=kind,
                        name=name,
                        start_line=i + 1,
                        end_line=end_line + 1,
                        modifiers=set(),
                        docstring=""
                    ))
                    i = end_line + 1
                    continue
            
            # Handle one-line function definitions
            if '=' in line and '(' in line and ')' in line:
                match = re.match(r'(\w+)\s*\([^)]*\)\s*=', line)
                if match:
                    name = match.group(1)
                    declarations.append(Declaration(
                        kind='function',
                        name=name,
                        start_line=i + 1,
                        end_line=i + 1,
                        modifiers=set(),
                        docstring=""
                    ))
                    i += 1
                    continue
            
            i += 1
            
        return declarations

    def _find_block_end(self, lines: List[str], start: int) -> int:
        """Find the 'end' keyword that matches the block start."""
        i = start
        block_count = 1  # We start after a block opener

        while i < len(lines):
            line = lines[i].strip()
            
            # Skip comments
            if line.startswith(self.line_comment) or line.startswith(self.block_comment_start):
                i += 1
                continue

            # Count block starters (function, struct, etc.)
            if any(word in line for word in ["function", "struct", "begin", "module", "macro", "if", "for", "while"]):
                block_count += 1

            # Count block enders
            if line == "end" or line.endswith(" end"):
                block_count -= 1
                if block_count == 0:
                    return i

            i += 1

        return len(lines) - 1  # If no matching end found, return last line