# file: codeconcat/parser/language_parsers/c_parser.py

import re
from typing import List, Optional, Set
from codeconcat.base_types import Declaration, ParsedFileData
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol

def parse_c_code(file_path: str, content: str) -> Optional[ParsedFileData]:
    parser = CParser()
    declarations = parser.parse(content)
    return ParsedFileData(
        file_path=file_path,
        language="c",
        content=content,
        declarations=declarations
    )

class CParser(BaseParser):
    def _setup_patterns(self):
        """
        We define capturing groups: 'name' for declarations.
        """
        # Basic patterns for function, struct, union, enum, typedef, define
        storage = r"(?:static|extern)?\s*"
        inline = r"(?:inline)?\s*"
        type_pattern = r"(?:[a-zA-Z_][\w*\s]+)+"

        self.patterns = {
            "function": re.compile(
                rf"^[^#/]*{storage}{inline}"
                rf"{type_pattern}\s+"
                rf"(?P<name>[a-zA-Z_]\w*)\s*\([^;{{]*"
            ),
            "struct": re.compile(
                rf"^[^#/]*struct\s+(?P<name>[a-zA-Z_]\w*)"
            ),
            "union": re.compile(
                rf"^[^#/]*union\s+(?P<name>[a-zA-Z_]\w*)"
            ),
            "enum": re.compile(
                rf"^[^#/]*enum\s+(?P<name>[a-zA-Z_]\w*)"
            ),
            "typedef": re.compile(
                r"^[^#/]*typedef\s+"
                r"(?:struct|union|enum)?\s*"
                r"(?:[a-zA-Z_][\w*\s]+)*"
                r"(?:\(\s*\*\s*)?"
                r"(?P<name>[a-zA-Z_]\w*)"
                r"(?:\s*\))?"
                r"\s*(?:\([^)]*\))?\s*;"
            ),
            "define": re.compile(
                r"^[^#/]*#define\s+(?P<name>[A-Z_][A-Z0-9_]*)"
            ),
        }

        # For braces
        self.block_start = "{"
        self.block_end = "}"
        self.line_comment = "//"
        self.block_comment_start = "/*"
        self.block_comment_end = "*/"

    def parse(self, content: str) -> List[Declaration]:
        lines = content.split("\n")
        symbols: List[CodeSymbol] = []
        line_count = len(lines)
        i = 0

        while i < line_count:
            line = lines[i].strip()
            if not line or line.startswith("//"):
                i += 1
                continue

            # Attempt matches
            for kind, pattern in self.patterns.items():
                match = pattern.match(line)
                if match:
                    name = match.group("name")
                    # We find potential block ends
                    block_end = i
                    if kind in ["function", "struct", "union", "enum"]:
                        block_end = self._find_block_end(lines, i)

                    symbol = CodeSymbol(
                        name=name,
                        kind=kind,
                        start_line=i,
                        end_line=block_end,
                        modifiers=set(),
                    )
                    symbols.append(symbol)
                    i = block_end  # skip to block_end
                    break
            i += 1

        # Convert to Declaration
        declarations = []
        for sym in symbols:
            declarations.append(Declaration(
                kind=sym.kind,
                name=sym.name,
                start_line=sym.start_line + 1,
                end_line=sym.end_line + 1,
                modifiers=sym.modifiers
            ))
        return declarations

    def _find_block_end(self, lines: List[str], start: int) -> int:
        """
        Naive approach: if we see '{', we try to find matching '}'.
        If not found, return start.
        """
        line = lines[start]
        if "{" not in line:
            return start
        brace_count = line.count("{") - line.count("}")
        if brace_count <= 0:
            return start

        for i in range(start + 1, len(lines)):
            l2 = lines[i]
            # skip line comments
            if l2.strip().startswith("//"):
                continue
            brace_count += l2.count("{") - l2.count("}")
            if brace_count <= 0:
                return i
        return len(lines) - 1