import re
from codeconcat.types import ParsedFileData, Declaration

def parse_python(file_path: str, content: str) -> ParsedFileData:
    lines = content.splitlines()
    declarations = []

    func_pattern = re.compile(r'^\s*def\s+(\w+)\s*\(')
    class_pattern = re.compile(r'^\s*class\s+(\w+)\s*[\(:]?')
    symbol_pattern = re.compile(r'^\s*([A-Z][A-Z0-9_]*)\s*=\s*.*$')  # Constants
    var_pattern = re.compile(r'^\s*([a-z][a-z0-9_]*)\s*=\s*(?!.*(?:def|class)\s)')  # Variables, excluding function/class defs

    for i, line in enumerate(lines):
        fmatch = func_pattern.match(line)
        if fmatch:
            declarations.append(Declaration("function", fmatch.group(1), i+1, i+1))
            continue

        cmatch = class_pattern.match(line)
        if cmatch:
            declarations.append(Declaration("class", cmatch.group(1), i+1, i+1))
            continue

        # Check for constants (UPPER_CASE)
        smatch = symbol_pattern.match(line)
        if smatch:
            declarations.append(Declaration("symbol", smatch.group(1), i+1, i+1))
            continue

        # Check for variables (lower_case)
        vmatch = var_pattern.match(line)
        if vmatch:
            declarations.append(Declaration("symbol", vmatch.group(1), i+1, i+1))

    return ParsedFileData(file_path=file_path, language="python", content=content, declarations=declarations)
