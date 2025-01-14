# file: codeconcat/parser/language_parsers/php_parser.py

import re
from typing import List, Optional, Set
from codeconcat.base_types import Declaration, ParsedFileData
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol

def parse_php(file_path: str, content: str) -> Optional[ParsedFileData]:
    parser = PhpParser()
    declarations = parser.parse(content)
    return ParsedFileData(
        file_path=file_path,
        language="php",
        content=content,
        declarations=declarations
    )

class PhpParser(BaseParser):
    def _setup_patterns(self):
        """
        Using consistent '(?P<name>...)' for all top-level declarations:
        class, interface, trait, function, etc.
        """
        self.patterns = {
            "class": re.compile(
                r"^[^#/]*"
                r"(?:abstract\s+|final\s+)?"
                r"class\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)"
                r"(?:\s+extends\s+[a-zA-Z_][a-zA-Z0-9_]*)?"
                r"(?:\s+implements\s+[a-zA-Z_][a-zA-Z0-9_]*(?:\s*,\s*[a-zA-Z_][a-zA-Z0-9_]*)*)?"
                r"\s*\{"
            ),
            "interface": re.compile(
                r"^[^#/]*"
                r"interface\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)"
                r"(?:\s+extends\s+[a-zA-Z_][a-zA-Z0-9_]*(?:\s*,\s*[a-zA-Z_][a-zA-Z0-9_]*)*)?"
                r"\s*\{"
            ),
            "trait": re.compile(
                r"^[^#/]*"
                r"trait\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)"
                r"\s*\{"
            ),
            "function": re.compile(
                r"^[^#/]*"
                r"(?:public\s+|private\s+|protected\s+|static\s+|final\s+)*"
                r"function\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)"
                r"\s*\([^)]*\)"
                r"(?:\s*:\s*[a-zA-Z_][a-zA-Z0-9_|\\]*)?"
                r"\s*\{"
            ),
            "namespace": re.compile(
                r"^[^#/]*"
                r"namespace\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_\\]*)"
                r"\s*;?"
            ),
        }

        self.block_start = "{"
        self.block_end = "}"
        self.line_comment = "//"
        # In PHP often '#' or '//' can be comment, but we just keep '//' for demonstration
        self.block_comment_start = "/*"
        self.block_comment_end = "*/"

    def parse(self, content: str) -> List[Declaration]:
        lines = content.split("\n")
        symbols: List[CodeSymbol] = []
        i = 0
        line_count = len(lines)

        while i < line_count:
            line = lines[i].strip()
            if not line or line.startswith("//") or line.startswith("#"):
                i += 1
                continue

            matched = False
            for kind, pattern in self.patterns.items():
                match = pattern.match(line)
                if match:
                    name = match.group("name")
                    block_end = i
                    # class, interface, trait, function might have braces
                    if kind in ["class", "interface", "trait", "function"]:
                        block_end = self._find_block_end(lines, i)
                    # namespace might end with ; or be followed by a block
                    symbol = CodeSymbol(
                        kind=kind,
                        name=name,
                        start_line=i,
                        end_line=block_end,
                        modifiers=set()
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
                modifiers=sym.modifiers,
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
            l2 = lines[i]
            if l2.strip().startswith("//") or l2.strip().startswith("#"):
                continue
            brace_count += l2.count("{") - l2.count("}")
            if brace_count <= 0:
                return i
        return len(lines) - 1