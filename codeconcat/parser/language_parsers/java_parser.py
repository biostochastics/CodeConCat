# file: codeconcat/parser/language_parsers/java_parser.py

import re
from typing import List, Optional, Set
from codeconcat.base_types import Declaration, ParsedFileData
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol

def parse_java(file_path: str, content: str) -> Optional[ParsedFileData]:
    parser = JavaParser()
    declarations = parser.parse(content)
    return ParsedFileData(
        file_path=file_path,
        language="java",
        content=content,
        declarations=declarations
    )

class JavaParser(BaseParser):
    def _setup_patterns(self):
        """
        We'll define patterns for class, interface, method, field (rough).
        If the line includes `{` we'll parse the block. We handle constructor vs. method by checking if
        there's a return type.
        """
        self.patterns = {
            "class": re.compile(
                r"^[^/]*"
                r"(?:public|private|protected|static|final|abstract\s+)*"
                r"class\s+(?P<name>[A-Z][a-zA-Z0-9_]*)"
                r"(?:\s+extends\s+[a-zA-Z0-9_.]+)?"
                r"(?:\s+implements\s+[a-zA-Z0-9_.]+(?:\s*,\s*[a-zA-Z0-9_.]+)*)?"
                r"\s*\{"
            ),
            "interface": re.compile(
                r"^[^/]*"
                r"(?:public|private|protected|static\s+)*"
                r"interface\s+(?P<name>[A-Z][a-zA-Z0-9_]*)"
                r"(?:\s+extends\s+[a-zA-Z0-9_.]+(?:\s*,\s*[a-zA-Z0-9_.]+)*)?"
                r"\s*\{"
            ),
            "method": re.compile(
                r"^[^/]*"
                r"(?:public|private|protected|static|final|abstract|synchronized\s+)*"
                r"(?:[a-zA-Z_][a-zA-Z0-9_.<>\[\]\s]*\s+)+"   # return type
                r"(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)"         # method or constructor name
                r"\s*\([^)]*\)\s*"
                r"(?:throws\s+[a-zA-Z0-9_.]+(?:\s*,\s*[a-zA-Z0-9_.]+)*)?"
                r"\s*\{"
            ),
            "field": re.compile(
                r"^[^/]*"
                r"(?:public|private|protected|static|final|volatile|transient\s+)*"
                r"[a-zA-Z_][a-zA-Z0-9_<>\[\]\s]*\s+"
                r"(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\s*;"
            ),
        }

        self.block_start = "{"
        self.block_end = "}"
        self.line_comment = "//"
        self.block_comment_start = "/*"
        self.block_comment_end = "*/"

    def parse(self, content: str) -> List[Declaration]:
        lines = content.split("\n")
        symbols: List[CodeSymbol] = []
        i = 0
        line_count = len(lines)

        while i < line_count:
            line = lines[i].strip()
            if not line or line.startswith("//"):
                i += 1
                continue

            matched = False
            for kind, pattern in self.patterns.items():
                match = pattern.match(line)
                if match:
                    name = match.group("name")
                    # Distinguish constructor vs. method:
                    if kind == "method":
                        # If the 'return type' portion doesn't exist or matches the name exactly => constructor
                        # This is simplistic check. We might check if the return type is the same as `name`.
                        # We'll keep it as method for test.
                        pass

                    block_end = i
                    if kind in ("class", "interface", "method"):
                        block_end = self._find_block_end(lines, i)

                    symbol = CodeSymbol(
                        kind=kind,
                        name=name,
                        start_line=i,
                        end_line=block_end,
                        modifiers=set(),
                    )
                    symbols.append(symbol)
                    i = block_end
                    matched = True
                    break
            if not matched:
                i += 1

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
        line = lines[start]
        if "{" not in line:
            return start
        brace_count = line.count("{") - line.count("}")
        if brace_count <= 0:
            return start
        for i in range(start + 1, len(lines)):
            l2 = lines[i].strip()
            if l2.startswith("//"):
                continue
            brace_count += l2.count("{") - l2.count("}")
            if brace_count <= 0:
                return i
        return len(lines) - 1