# file: codeconcat/parser/language_parsers/go_parser.py

import re
from typing import List, Optional
from codeconcat.base_types import Declaration, ParsedFileData
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol

def parse_go(file_path: str, content: str) -> Optional[ParsedFileData]:
    parser = GoParser()
    declarations = parser.parse(content)
    return ParsedFileData(
        file_path=file_path,
        language="go",
        content=content,
        declarations=declarations
    )

class GoParser(BaseParser):
    def _setup_patterns(self):
        """
        We separate out interface vs. struct vs. type in general, to avoid double counting.
        """
        self.patterns = {
            "struct": re.compile(
                r"^[^/]*type\s+(?P<name>[A-Z][a-zA-Z0-9_]*)\s+struct\s*\{"
            ),
            "interface": re.compile(
                r"^[^/]*type\s+(?P<name>[A-Z][a-zA-Z0-9_]*)\s+interface\s*\{"
            ),
            "function": re.compile(
                r"^[^/]*func\s+(?:\([^)]+\)\s+)?(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)"
                r"(?:\s*\([^)]*\))?\s*\{"
            ),
            "const": re.compile(
                r"^[^/]*const\s+(?:\(\s*|(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\s*=)"
            ),
            "var": re.compile(
                r"^[^/]*var\s+(?:\(\s*|(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)\s*(?:=|\s+[^=\s]+))"
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
        in_const_block = False
        in_var_block = False
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                i += 1
                continue

            # handle multi-line const ( ) or var ( )
            if in_const_block or in_var_block:
                if ")" in stripped:
                    # block closed
                    in_const_block = False
                    in_var_block = False
                    i += 1
                    continue

                # lines inside const/var block
                if "=" in stripped:
                    # parse out the name
                    parts = stripped.split("=")
                    name_part = parts[0].strip()
                    # we only take the first token as name
                    name = name_part.split()[0]
                    kind = "const" if in_const_block else "var"
                    symbol = CodeSymbol(
                        name=name,
                        kind=kind,
                        start_line=i + 1,
                        end_line=i + 1,
                        modifiers=set(),
                    )
                    symbols.append(symbol)
                i += 1
                continue

            matched = False
            for kind, pattern in self.patterns.items():
                m = pattern.match(stripped)
                if m:
                    matched = True
                    if kind in ("const", "var"):
                        # If group 'name' is not found => multi-line block
                        name = m.groupdict().get("name", None)
                        if name is None:
                            # e.g. const (
                            if kind == "const":
                                in_const_block = True
                            else:
                                in_var_block = True
                        else:
                            # Single-line const/var
                            symbol = CodeSymbol(
                                name=name,
                                kind=kind,
                                start_line=i + 1,
                                end_line=i + 1,
                                modifiers=set(),
                            )
                            symbols.append(symbol)
                    else:
                        # struct, interface, function
                        name = m.group("name")
                        block_end = self._find_block_end(lines, i)
                        symbol = CodeSymbol(
                            name=name,
                            kind=kind,
                            start_line=i + 1,
                            end_line=block_end + 1,
                            modifiers=set(),
                        )
                        symbols.append(symbol)
                        i = block_end
                    break
            if not matched:
                # no pattern matched
                pass

            i += 1

        declarations = []
        for sym in symbols:
            declarations.append(Declaration(
                kind=sym.kind,
                name=sym.name,
                start_line=sym.start_line,
                end_line=sym.end_line,
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
            l2 = lines[i]
            if l2.strip().startswith("//"):
                continue
            brace_count += l2.count("{") - l2.count("}")
            if brace_count <= 0:
                return i
        return len(lines) - 1