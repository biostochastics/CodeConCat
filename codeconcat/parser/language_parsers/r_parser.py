import re
from codeconcat.types import ParsedFileData, Declaration

def parse_r(file_path: str, content: str) -> ParsedFileData:
    lines = content.splitlines()
    declarations = []
    
    # Patterns for R code
    func_pattern = re.compile(r'^\s*(\w+)\s*<-\s*function\s*\(.*\)\s*\{?')
    symbol_pattern = re.compile(r'^\s*([A-Z][A-Z0-9_]*)\s*<?-\s*.*$')  # Constants like MAX_VALUE
    var_pattern = re.compile(r'^\s*([a-z][a-z0-9_]*)\s*<?-\s*(?!.*function)')  # Variables, excluding functions

    for i, line in enumerate(lines):
        # Check for function definitions
        fmatch = func_pattern.match(line)
        if fmatch:
            declarations.append(Declaration("function", fmatch.group(1), i+1, i+1))
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

    return ParsedFileData(file_path=file_path, language="r", content=content, declarations=declarations)
