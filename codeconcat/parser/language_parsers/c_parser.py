"""C code parser for CodeConcat."""

import re
from typing import List, Tuple

def parse_c_code(content: str) -> List[Tuple[str, int, int]]:
    """Parse C code to identify functions, structs, unions, and enums.
    
    Returns:
        List of tuples (symbol_name, start_line, end_line)
    """
    symbols = []
    lines = content.split('\n')
    
    # Patterns for C constructs
    patterns = {
        'function': r'^\s*(?:static\s+)?(?:inline\s+)?(?:[a-zA-Z_][a-zA-Z0-9_]*\s+)+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^;]*$',
        'struct': r'^\s*struct\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        'union': r'^\s*union\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        'enum': r'^\s*enum\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        'typedef': r'^\s*typedef\s+(?:struct|union|enum)?\s*(?:[a-zA-Z_][a-zA-Z0-9_]*\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*;',
        'define': r'^\s*#define\s+([A-Z_][A-Z0-9_]*)',
    }
    
    in_block = False
    block_start = 0
    block_name = ""
    brace_count = 0
    in_comment = False
    in_macro = False
    
    for i, line in enumerate(lines):
        # Handle multi-line comments
        if '/*' in line:
            in_comment = True
        if '*/' in line:
            in_comment = False
            continue
        if in_comment or line.strip().startswith('//'):
            continue
            
        # Handle multi-line macros
        if line.strip().endswith('\\'):
            in_macro = True
            continue
        if in_macro:
            if not line.strip().endswith('\\'):
                in_macro = False
            continue
            
        # Skip preprocessor directives except #define
        if line.strip().startswith('#') and not line.strip().startswith('#define'):
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
                    if construct in ['typedef', 'define'] or (brace_count == 0 and ';' in line):
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
