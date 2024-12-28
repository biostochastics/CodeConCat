import re
from codeconcat.types import ParsedFileData, Declaration

def parse_julia(file_path: str, content: str) -> ParsedFileData:
    lines = content.splitlines()
    declarations = []

    func_pattern = re.compile(r'^\s*function\s+(\w+)\s*\(')
    struct_pattern = re.compile(r'^\s*(mutable\s+)?struct\s+(\w+)')

    for i, line in enumerate(lines):
        fm = func_pattern.match(line)
        if fm:
            declarations.append(Declaration("function", fm.group(1), i+1, i+1))

        sm = struct_pattern.match(line)
        if sm:
            declarations.append(Declaration("struct", sm.group(2), i+1, i+1))

    return ParsedFileData(file_path=file_path, language="julia", content=content, declarations=declarations)
