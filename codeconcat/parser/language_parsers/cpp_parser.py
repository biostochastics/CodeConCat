"""C++ code parser for CodeConcat."""

import re
from typing import List, Tuple

def parse_cpp_code(content: str) -> List[Tuple[str, int, int]]:
    """Parse C++ code to identify classes, functions, namespaces, and templates.
    
    Returns:
        List of tuples (symbol_name, start_line, end_line)
    """
    symbols = []
    lines = content.split('\n')
    
    # Patterns for C++ constructs
    patterns = {
        'class': r'^\s*(?:template\s*<[^>]*>\s*)?(?:class|struct)\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        'function': r'^\s*(?:template\s*<[^>]*>\s*)?(?:[a-zA-Z_][a-zA-Z0-9_:]*\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*(?:const)?\s*(?:noexcept)?\s*(?:override)?\s*(?:final)?\s*(?:=\s*(?:default|delete))?\s*(?:{\s*)?$',
        'namespace': r'^\s*namespace\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        'enum': r'^\s*enum(?:\s+class)?\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        'typedef': r'^\s*typedef\s+[^;]+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*;',
        'using': r'^\s*using\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=',
    }
    
    in_block = False
    block_start = 0
    block_name = ""
    brace_count = 0
    in_comment = False
    
    for i, line in enumerate(lines):
        # Handle multi-line comments
        if '/*' in line:
            in_comment = True
        if '*/' in line:
            in_comment = False
            continue
        if in_comment or line.strip().startswith('//'):
            continue
            
        # Skip preprocessor directives
        if line.strip().startswith('#'):
            continue
            
        # Track braces and blocks
        if not in_block:
            for construct, pattern in patterns.items():
                match = re.match(pattern, line)
                if match:
                    block_name = match.group(1)
                    block_start = i
                    in_block = True
                    brace_count = line.count('{') - line.count('}')
                    # Handle one-line definitions
                    if brace_count == 0 and ';' in line:
                        symbols.append((block_name, i, i))
                        in_block = False
                    break
        else:
            brace_count += line.count('{') - line.count('}')
            
        # Check if block ends
        if in_block and brace_count == 0 and ('}' in line or ';' in line):
            symbols.append((block_name, block_start, i))
            in_block = False
            
    return symbols
