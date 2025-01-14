# file: codeconcat/parser/language_parsers/julia_parser.py

import re
from typing import List, Optional, Set
from codeconcat.base_types import Declaration, ParsedFileData
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol

def parse_julia(file_path: str, content: str) -> Optional[ParsedFileData]:
    parser = JuliaParser()
    declarations = parser.parse(content)
    return ParsedFileData(
        file_path=file_path,
        language="julia",
        content=content,
        declarations=declarations
    )

class JuliaParser(BaseParser):
    def _setup_patterns(self):
        """
        We'll define simpler patterns. Note we must handle single-line vs. multi-line function definitions
        like:
          function name(...) ...
        or
          name(x) = x+1
        """
        # We'll unify to 'name' group
        self.patterns = {
            "function": re.compile(
                r"^[^#]*"
                r"(?:function\s+(?P<name>[a-zA-Z_]\w*))|"
                r"^(?P<name2>[a-zA-Z_]\w*)\s*\([^)]*\)\s*=\s*"
            ),
            "struct": re.compile(
                r"^[^#]*(?:mutable\s+)?struct\s+(?P<name>[A-Z][a-zA-Z0-9_]*)"
            ),
            "abstract": re.compile(
                r"^[^#]*abstract\s+type\s+(?P<name>[A-Z][a-zA-Z0-9_]*)"
            ),
            "module": re.compile(
                r"^[^#]*module\s+(?P<name>[A-Z][a-zA-Z0-9_]*)"
            ),
            "macro": re.compile(
                r"^[^#]*macro\s+(?P<name>[a-zA-Z_]\w*)"
            ),
        }

        self.block_start = "begin"  # not always used, but a placeholder
        self.block_end = "end"
        self.line_comment = "#"
        self.block_comment_start = "#="
        self.block_comment_end = "=#"

    def parse(self, content: str) -> List[Declaration]:
        lines = content.split("\n")
        symbols: List[CodeSymbol] = []
        i = 0
        line_count = len(lines)

        while i < line_count:
            line = lines[i]
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                i += 1
                continue

            matched = False
            for kind, pattern in self.patterns.items():
                m = pattern.match(stripped)
                if m:
                    # unify name
                    name = m.groupdict().get("name") or m.groupdict().get("name2")
                    if not name:
                        continue
                    symbol = CodeSymbol(
                        name=name,
                        kind=kind,
                        start_line=i,
                        end_line=i,
                        modifiers=set(),
                    )
                    symbols.append(symbol)
                    matched = True
                    break
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