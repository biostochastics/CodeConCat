# file: codeconcat/parser/language_parsers/go_parser.py

import re
from typing import List, Optional

from codeconcat.base_types import Declaration, ParsedFileData
from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol


def parse_go(file_path: str, content: str) -> Optional[ParsedFileData]:
    parser = GoParser()
    declarations = parser.parse_file(content)
    return ParsedFileData(
        file_path=file_path, language="go", content=content, declarations=declarations
    )


class GoParser(BaseParser):
    def __init__(self):
        super().__init__()
        self._setup_patterns()

    def _setup_patterns(self):
        """Set up patterns for Go code declarations."""
        self.patterns = {}

        # Go uses curly braces
        self.block_start = "{"
        self.block_end = "}"
        self.line_comment = "//"
        self.block_comment_start = "/*"
        self.block_comment_end = "*/"

        # Function pattern (both regular and method)
        func_pattern = r"^\s*func\s+(?:\([^)]+\)\s+)?(?P<n>[a-zA-Z_][a-zA-Z0-9_]*)\s*\("
        self.patterns["function"] = re.compile(func_pattern)

        # Interface pattern
        interface_pattern = r"^\s*type\s+(?P<n>[a-zA-Z_][a-zA-Z0-9_]*)\s+interface\s*"
        self.patterns["interface"] = re.compile(interface_pattern)

        # Struct pattern
        struct_pattern = r"^\s*type\s+(?P<n>[a-zA-Z_][a-zA-Z0-9_]*)\s+struct\s*"
        self.patterns["struct"] = re.compile(struct_pattern)

        # Const pattern (both single and block)
        const_pattern = r"^\s*(?:const\s+(?P<n>[a-zA-Z_][a-zA-Z0-9_]*)|const\s+\(\s*(?P<n2>[a-zA-Z_][a-zA-Z0-9_]*))"
        self.patterns["const"] = re.compile(const_pattern)

        # Var pattern (both single and block)
        var_pattern = (
            r"^\s*(?:var\s+(?P<n>[a-zA-Z_][a-zA-Z0-9_]*)|var\s+\(\s*(?P<n2>[a-zA-Z_][a-zA-Z0-9_]*))"
        )
        self.patterns["var"] = re.compile(var_pattern)

    def parse_file(self, content: str) -> List[Declaration]:
        """Parse Go file content and return list of declarations."""
        return self.parse(content)

    def parse(self, content: str) -> List[Declaration]:
        """Parse Go code content and return list of declarations."""
        declarations = []
        lines = content.split("\n")
        in_comment = False
        comment_buffer = []
        in_const_block = False
        in_var_block = False

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines and comments
            if not line or line.startswith("//"):
                i += 1
                continue

            # Handle block comments
            if "/*" in line and not in_comment:
                in_comment = True
                i += 1
                continue
            elif in_comment:
                if "*/" in line:
                    in_comment = False
                i += 1
                continue

            # Handle const blocks
            if line.startswith("const ("):
                in_const_block = True
                i += 1
                continue
            elif in_const_block:
                if line == ")":
                    in_const_block = False
                    i += 1
                    continue
                else:
                    # Parse constant declaration inside block
                    name = line.split("=")[0].strip()
                    if name and name.isidentifier():
                        declarations.append(
                            Declaration(
                                kind="const",
                                name=name,
                                start_line=i + 1,
                                end_line=i + 1,
                                modifiers=set(),
                                docstring="",
                            )
                        )
                    i += 1
                    continue

            # Handle var blocks
            if line.startswith("var ("):
                in_var_block = True
                i += 1
                continue
            elif in_var_block:
                if line == ")":
                    in_var_block = False
                    i += 1
                    continue
                else:
                    # Parse variable declaration inside block
                    name = line.split("=")[0].strip().split()[0]
                    if name and name.isidentifier():
                        declarations.append(
                            Declaration(
                                kind="var",
                                name=name,
                                start_line=i + 1,
                                end_line=i + 1,
                                modifiers=set(),
                                docstring="",
                            )
                        )
                    i += 1
                    continue

            # Try to match patterns
            for kind, pattern in self.patterns.items():
                match = pattern.match(line)
                if match:
                    name = match.group("n")
                    if not name:
                        continue

                    # Find block end for block-based declarations
                    end_line = i
                    if kind in ("function", "interface", "struct"):
                        brace_count = 0
                        found_opening = False

                        # Find the end of the block by counting braces
                        j = i
                        while j < len(lines):
                            curr_line = lines[j].strip()

                            if "{" in curr_line:
                                found_opening = True
                                brace_count += curr_line.count("{")
                            if "}" in curr_line:
                                brace_count -= curr_line.count("}")

                            if found_opening and brace_count == 0:
                                end_line = j
                                break
                            j += 1

                    # Extract docstring if present
                    docstring = None
                    if end_line > i:
                        docstring = self.extract_docstring(lines, i, end_line)

                    declarations.append(
                        Declaration(
                            kind=kind,
                            name=name,
                            start_line=i + 1,
                            end_line=end_line + 1,
                            modifiers=set(),
                            docstring=docstring or "",
                        )
                    )
                    i = end_line + 1
                    break
            else:
                i += 1

        return declarations

    def _find_block_end(self, lines: List[str], start: int) -> int:
        """Find the end of a Go code block."""
        brace_count = 0
        i = start

        # Find the opening brace
        while i < len(lines):
            line = lines[i]
            if "{" in line:
                brace_count += 1
                break
            i += 1

        # Find the matching closing brace
        while i < len(lines):
            line = lines[i]
            brace_count += line.count("{")
            brace_count -= line.count("}")

            if brace_count == 0:
                return i + 1

            i += 1

        return len(lines)
