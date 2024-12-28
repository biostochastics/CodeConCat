import re
from codeconcat.types import ParsedFileData, Declaration

def parse_r(file_path: str, content: str) -> ParsedFileData:
    lines = content.splitlines()
    declarations = []
    func_pattern = re.compile(r'^\s*(\w+)\s*<-\s*function\s*\(.*\)\s*\{?')

    for i, line in enumerate(lines):
        match = func_pattern.match(line)
        if match:
            declarations.append(Declaration("function", match.group(1), i+1, i+1))

    return ParsedFileData(file_path=file_path, language="r", content=content, declarations=declarations)
