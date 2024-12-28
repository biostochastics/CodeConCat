"""
js_ts_parser.py

Naive approach for detecting 'function <name>' and 'class <name>'
in JS/TS. Could be extended to arrow functions, exports, etc.
"""

import re
from codeconcat.types import ParsedFileData, Declaration

func_pattern = re.compile(r'^\s*(?:export\s+)?function\s+(\w+)\s*\(')
class_pattern = re.compile(r'^\s*(?:export\s+)?class\s+(\w+)\s*[\{\(]?')

def parse_javascript_or_typescript(file_path: str, content: str, language: str) -> ParsedFileData:
    lines = content.splitlines()
    declarations = []

    for i, line in enumerate(lines):
        fm = func_pattern.match(line)
        if fm:
            declarations.append(Declaration("function", fm.group(1), i+1, i+1))
        cm = class_pattern.match(line)
        if cm:
            declarations.append(Declaration("class", cm.group(1), i+1, i+1))

    return ParsedFileData(
        file_path=file_path,
        language=language,
        content=content,
        declarations=declarations
    )
