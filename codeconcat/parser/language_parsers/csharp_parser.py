"""C# code parser for CodeConcat."""

import re
from typing import List, Tuple

def parse_csharp_code(content: str) -> List[Tuple[str, int, int]]:
    """Parse C# code to identify classes, methods, properties, and other constructs.
    
    Returns:
        List of tuples (symbol_name, start_line, end_line)
    """
    symbols = []
    lines = content.split('\n')
    
    # Patterns for C# constructs
    patterns = {
        'class': r'^\s*(?:public|private|protected|internal)?\s*(?:static|abstract|sealed)?\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        'interface': r'^\s*(?:public|private|protected|internal)?\s*interface\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        'method': r'^\s*(?:public|private|protected|internal)?\s*(?:static|virtual|abstract|override)?\s*(?:async\s+)?(?:[a-zA-Z_][a-zA-Z0-9_<>]*\s+)+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)',
        'property': r'^\s*(?:public|private|protected|internal)?\s*(?:static|virtual|abstract|override)?\s*(?:[a-zA-Z_][a-zA-Z0-9_<>]*\s+)+([a-zA-Z_][a-zA-Z0-9_]*)\s*{\s*(?:get|set)',
        'enum': r'^\s*(?:public|private|protected|internal)?\s*enum\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        'struct': r'^\s*(?:public|private|protected|internal)?\s*struct\s+([a-zA-Z_][a-zA-Z0-9_]*)',
        'delegate': r'^\s*(?:public|private|protected|internal)?\s*delegate\s+(?:[a-zA-Z_][a-zA-Z0-9_<>]*\s+)+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
        'event': r'^\s*(?:public|private|protected|internal)?\s*event\s+(?:[a-zA-Z_][a-zA-Z0-9_<>]*\s+)+([a-zA-Z_][a-zA-Z0-9_]*)',
        'namespace': r'^\s*namespace\s+([a-zA-Z_][a-zA-Z0-9_.]*)',
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
            
        # Skip attributes
        if line.strip().startswith('['):
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
                    # Handle auto-properties and one-line definitions
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
