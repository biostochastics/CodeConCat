"""
python_parser.py

Naive regex approach to top-level 'def' and 'class' detection in Python files.
For advanced usage, consider AST-based parsing.
"""

import re
from codeconcat.types import ParsedFileData, Declaration

def parse_python(file_path: str, content: str) -> ParsedFileData:
    lines = content.splitlines()
    declarations = []

    func_pattern = re.compile(r'^\s*def\s+(\w+)\s*\(')
    class_pattern = re.compile(r'^\s*class\s+(\w+)\s*[\(:]?')

    for i, line in enumerate(lines):
        fmatch = func_pattern.match(line)
        if fmatch:
            declarations.append(Declaration("function", fmatch.group(1), i+1, i+1))

        cmatch = class_pattern.match(line)
        if cmatch:
            declarations.append(Declaration("class", cmatch.group(1), i+1, i+1))

    return ParsedFileData(
        file_path=file_path,
        language="python",
        content=content,
        declarations=declarations
    )
