import re
from codeconcat.types import ParsedFileData, Declaration

def parse_julia(file_path: str, content: str) -> ParsedFileData:
    lines = content.splitlines()
    declarations = []

    # Patterns for Julia code
    func_pattern = re.compile(r'^\s*function\s+(\w+)\s*\(')
    struct_pattern = re.compile(r'^\s*(mutable\s+)?struct\s+(\w+)')
    const_pattern = re.compile(r'^\s*const\s+([A-Z][A-Z0-9_]*)\s*=')  # Constants declared with const
    symbol_pattern = re.compile(r'^\s*([A-Z][A-Z0-9_]*)\s*=\s*.*$')  # Other uppercase symbols
    var_pattern = re.compile(r'^\s*([a-z][a-z0-9_]*)\s*=\s*(?!.*(?:function|struct|mutable))')  # Variables

    for i, line in enumerate(lines):
        # Check for functions
        fm = func_pattern.match(line)
        if fm:
            declarations.append(Declaration("function", fm.group(1), i+1, i+1))
            continue

        # Check for structs
        sm = struct_pattern.match(line)
        if sm:
            declarations.append(Declaration("struct", sm.group(2), i+1, i+1))
            continue

        # Check for const declarations
        cm = const_pattern.match(line)
        if cm:
            declarations.append(Declaration("symbol", cm.group(1), i+1, i+1))
            continue

        # Check for other constants (UPPER_CASE)
        um = symbol_pattern.match(line)
        if um:
            declarations.append(Declaration("symbol", um.group(1), i+1, i+1))
            continue

        # Check for variables (lower_case)
        vm = var_pattern.match(line)
        if vm:
            declarations.append(Declaration("symbol", vm.group(1), i+1, i+1))

    return ParsedFileData(file_path=file_path, language="julia", content=content, declarations=declarations)
